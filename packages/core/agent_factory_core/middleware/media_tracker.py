"""MediaTrackerMiddleware - auto-catalogs generated media assets."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, NotRequired
from uuid import uuid4

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ContextT,
    ResponseT,
)
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

# Tools whose results may contain generated media paths
TRACKED_TOOLS = frozenset({
    "generate_post_image",
    "generate_complete_post",
    "generate_product_showcase",
    "edit_post_image",
    "animate_image",
    "generate_video_from_text",
    "generate_video",
    "generate_animated_product_video",
    "generate_motion_graphics_video",
})


class MediaTrackerState(AgentState):
    """State schema for MediaTrackerMiddleware."""

    media_assets: NotRequired[list[dict[str, Any]]]


def _extract_asset(parsed: dict[str, Any], thread_id: str) -> dict[str, Any] | None:
    """Extract a MediaAsset dict from a parsed tool result."""
    if parsed.get("status") != "success":
        return None

    # Determine asset type and path
    asset_type = "image"
    path = parsed.get("image_path", "")
    if not path:
        path = parsed.get("video_path", "")
        asset_type = "video"
    if not path:
        path = parsed.get("path", "")
        if path and path.endswith(".mp4"):
            asset_type = "video"

    if not path:
        return None

    return {
        "asset_id": str(uuid4()),
        "asset_type": asset_type,
        "path": path,
        "url": path if path.startswith("/") else f"/{path}",
        "thread_id": thread_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "prompt_used": parsed.get("prompt_used", parsed.get("prompt", "")),
            "model": parsed.get("model", ""),
            "brand_name": parsed.get("brand_name", ""),
            "caption": parsed.get("caption", ""),
            "hashtags": parsed.get("hashtags", []),
            "video_type": parsed.get("type", ""),
            "duration": parsed.get("duration_seconds"),
            "version": 1,
        },
    }


class MediaTrackerMiddleware(AgentMiddleware[MediaTrackerState, ContextT, ResponseT]):
    """Intercepts tool results from media generation tools to catalog assets.

    When a tracked tool returns a successful result with a file path,
    a MediaAsset entry is appended to state.media_assets via Command.
    """

    state_schema = MediaTrackerState

    def _process_result(
        self,
        request: ToolCallRequest,
        result: ToolMessage | Command,
    ) -> ToolMessage | Command:
        tool_name = request.tool_call.get("name", "")
        if tool_name not in TRACKED_TOOLS:
            return result

        # Extract content from the result
        content = None
        if isinstance(result, ToolMessage):
            content = result.content
        elif isinstance(result, Command):
            # Command may contain messages with tool results
            msgs = result.update.get("messages", []) if isinstance(result.update, dict) else []
            for msg in msgs:
                if isinstance(msg, ToolMessage):
                    content = msg.content
                    break

        if content is None:
            return result

        # Parse the content
        try:
            if isinstance(content, str):
                parsed = json.loads(content)
            elif isinstance(content, dict):
                parsed = content
            else:
                return result
        except (json.JSONDecodeError, TypeError):
            return result

        # Get thread_id from runtime config
        thread_id = ""
        if hasattr(request, "runtime") and request.runtime:
            config = getattr(request.runtime, "config", {})
            if isinstance(config, dict):
                configurable = config.get("configurable", {})
                thread_id = configurable.get("thread_id", "")

        asset = _extract_asset(parsed, thread_id)
        if asset is None:
            return result

        logger.info(
            "Tracked %s asset: %s (%s)",
            asset["asset_type"], asset["path"], tool_name,
        )

        # Return Command with state update to append the asset
        if isinstance(result, ToolMessage):
            return Command(
                update={
                    "media_assets": [asset],
                    "messages": [result],
                },
            )
        # If already a Command, merge the asset into its update
        if isinstance(result, Command) and isinstance(result.update, dict):
            existing_assets = result.update.get("media_assets", [])
            result.update["media_assets"] = [*existing_assets, asset]
            return result

        return result

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        result = handler(request)
        return self._process_result(request, result)

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        result = await handler(request)
        return self._process_result(request, result)
