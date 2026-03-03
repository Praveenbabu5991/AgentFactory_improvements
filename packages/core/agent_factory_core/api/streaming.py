"""SSE streaming via LangGraph astream_events()."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import AsyncGenerator

from langgraph.graph.state import CompiledStateGraph


def _sanitize_unicode(text: str) -> str:
    """Remove invalid Unicode surrogates that cause serialization errors."""
    if not text:
        return text
    cleaned = re.sub(r"[\ud800-\udfff]", "", text)
    try:
        cleaned = cleaned.encode("utf-8", errors="replace").decode("utf-8")
    except UnicodeError:
        cleaned = "".join(c for c in text if ord(c) < 0x10000 or ord(c) <= 0x10FFFF)
    return cleaned


def _sse(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


def _log(msg: str):
    """Print with flush for immediate visibility."""
    print(msg, flush=True)


def _extract_error_detail(exc: Exception) -> str:
    """Extract a user-friendly error message from common API exceptions."""
    err = str(exc)
    # Google/Gemini API errors
    if "429" in err or "RESOURCE_EXHAUSTED" in err:
        return "Rate limit exceeded (429). The Gemini API free tier allows 20 requests/day per model. Please wait or use a different API key."
    if "403" in err or "PERMISSION_DENIED" in err:
        return "Permission denied (403). Check your API key permissions."
    if "400" in err or "INVALID_ARGUMENT" in err:
        return f"Invalid request (400): {err[:200]}"
    if "404" in err or "NOT_FOUND" in err:
        return f"Model not found (404): {err[:200]}"
    if "500" in err or "INTERNAL" in err:
        return "Gemini API internal error (500). Please try again."
    if "503" in err or "UNAVAILABLE" in err:
        return "Gemini API temporarily unavailable (503). Please try again in a moment."
    # Generic
    return f"Error: {err[:300]}"


async def stream_agent_response(
    agent: CompiledStateGraph,
    input_data: dict,
    config: dict,
    session_id: str,
) -> AsyncGenerator[str, None]:
    """Stream agent response as Server-Sent Events.

    Yields SSE events:
    - {"type": "session", "session_id": "..."}
    - {"type": "text", "content": "..."}
    - {"type": "tool_start", "tool": "...", "tool_call_id": "..."}
    - {"type": "tool_end", "tool": "...", "content": "..."}
    - {"type": "done"}
    - {"type": "error", "message": "..."}
    """
    yield _sse({"type": "session", "session_id": session_id})

    has_content = False  # Track if we sent any text or tool events
    last_error = None  # Capture last error from events

    try:
        async for event in agent.astream_events(input_data, config=config, version="v2"):
            kind = event.get("event", "")

            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    text = chunk.content
                    if isinstance(text, str) and text:
                        has_content = True
                        yield _sse({"type": "text", "content": _sanitize_unicode(text)})

            elif kind == "on_tool_start":
                tool_name = event.get("name", "")
                run_id = event.get("run_id", "")
                has_content = True
                yield _sse({"type": "tool_start", "tool": tool_name, "tool_call_id": run_id})

            elif kind == "on_tool_end":
                tool_name = event.get("name", "")
                output = event.get("data", {}).get("output", "")
                # Extract .content from ToolMessage objects
                if hasattr(output, "content"):
                    output = output.content
                if isinstance(output, str):
                    output = _sanitize_unicode(output)
                else:
                    output = str(output)
                # Don't truncate format_response_for_user — frontend needs full JSON
                max_len = 16000 if tool_name == "format_response_for_user" else 4000
                yield _sse({"type": "tool_end", "tool": tool_name, "content": output[:max_len]})

            # Capture errors/retries from LangGraph events
            elif kind in ("on_chain_error", "on_llm_error", "on_chat_model_error"):
                error = event.get("data", {})
                if isinstance(error, dict):
                    err_msg = error.get("error", error.get("message", str(error)))
                else:
                    err_msg = str(error)
                last_error = err_msg
                _log(f"   ❌ {kind}: {err_msg}")

    except Exception as e:
        error_str = str(e)
        _log(f"   ❌ SSE streaming error: {error_str}")
        # Extract useful details from common Gemini errors
        detail = _extract_error_detail(e)
        yield _sse({"type": "error", "message": detail})

    # If the agent completed without producing any text or tool events,
    # it likely means the model call failed silently (e.g., rate limit).
    if not has_content:
        detail = last_error or "No response from model"
        _log(f"   ⚠️ Empty response for session={session_id} — {detail}")
        yield _sse({
            "type": "error",
            "message": f"Sorry, the AI model didn't respond. Reason: {detail}"
        })

    yield _sse({"type": "done"})
