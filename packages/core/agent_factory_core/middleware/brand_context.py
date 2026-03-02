"""BrandContextMiddleware - injects brand info into every LLM call's system prompt."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NotRequired

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ContextT,
    ModelRequest,
    ModelResponse,
    ResponseT,
)

from deepagents.middleware._utils import append_to_system_message

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


class BrandState(AgentState):
    """State schema for BrandContextMiddleware."""

    brand: NotRequired[dict[str, Any]]


class BrandContextMiddleware(AgentMiddleware[BrandState, ContextT, ResponseT]):
    """Reads brand context from state and appends it to the system prompt.

    This ensures every agent (root + subagents) sees the brand identity
    without the orchestrator needing to pass it explicitly each time.
    """

    state_schema = BrandState

    def _build_brand_section(self, brand: dict[str, Any]) -> str | None:
        if not brand or not brand.get("name"):
            return None

        lines = [
            "## Brand Context (use this for ALL content generation)",
            f"- Brand: {brand['name']} ({brand.get('industry', 'N/A')})",
            f"- Tone: {brand.get('tone', 'creative')}",
        ]

        colors = brand.get("colors", [])
        if colors:
            lines.append(f"- Colors: {', '.join(colors)}")

        for field, label in [
            ("overview", "Overview"),
            ("target_audience", "Target Audience"),
            ("products_services", "Products/Services"),
        ]:
            val = brand.get(field, "")
            if val:
                lines.append(f"- {label}: {val}")

        logo = brand.get("logo_path", "")
        lines.append(f"- Logo: {'Available at ' + logo if logo else 'Not uploaded'}")

        # User images for posts
        user_images = brand.get("user_images", [])
        if user_images:
            lines.append("")
            lines.append("USER_IMAGES_FOR_POST:")
            paths = []
            for img in user_images:
                intent = img.get("usage_intent", "AUTO").upper()
                path = img.get("path", "")
                lines.append(f"  - [{intent}] {path}")
                paths.append(path)
            lines.append(f"  USER_IMAGES_PATHS: {','.join(paths)}")

        # Marketing-specific fields
        goals = brand.get("marketing_goals", [])
        if goals:
            lines.append(f"- Marketing Goals: {', '.join(goals)}")
        messaging = brand.get("brand_messaging", "")
        if messaging:
            lines.append(f"- Key Messages: {messaging}")
        positioning = brand.get("competitive_positioning", "")
        if positioning:
            lines.append(f"- Positioning: {positioning}")

        return "\n".join(lines)

    def _modify_request(self, request: ModelRequest[ContextT]) -> ModelRequest[ContextT]:
        brand = request.state.get("brand", {})
        section = self._build_brand_section(brand)
        if section is None:
            return request
        new_system = append_to_system_message(request.system_message, section)
        return request.override(system_message=new_system)

    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT]:
        return handler(self._modify_request(request))

    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]],
    ) -> ModelResponse[ResponseT]:
        return await handler(self._modify_request(request))
