"""SSE streaming via LangGraph astream_events()."""

from __future__ import annotations

import json
import re
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

    try:
        async for event in agent.astream_events(input_data, config=config, version="v2"):
            kind = event.get("event", "")

            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    text = chunk.content
                    if isinstance(text, str) and text:
                        yield _sse({"type": "text", "content": _sanitize_unicode(text)})

            elif kind == "on_tool_start":
                tool_name = event.get("name", "")
                run_id = event.get("run_id", "")
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
                yield _sse({"type": "tool_end", "tool": tool_name, "content": output[:4000]})

    except Exception as e:
        yield _sse({"type": "error", "message": f"An error occurred: {e!s}"})

    yield _sse({"type": "done"})
