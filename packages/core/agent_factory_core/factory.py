"""Studio agent factory - wraps create_deep_agent() with domain defaults."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from deepagents import SubAgent, CompiledSubAgent, create_deep_agent
from deepagents.backends import StateBackend
from deepagents.backends.protocol import BackendFactory, BackendProtocol

from agent_factory_core.config.settings import DEFAULT_MODEL
from agent_factory_core.middleware.brand_context import BrandContextMiddleware
from agent_factory_core.middleware.media_tracker import MediaTrackerMiddleware

_DEFAULT_MODEL = f"google_genai:{DEFAULT_MODEL}"


def create_studio_agent(
    *,
    model: str | BaseChatModel = _DEFAULT_MODEL,
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    subagents: list[SubAgent | CompiledSubAgent] | None = None,
    system_prompt: str | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    backend: BackendProtocol | BackendFactory | None = None,
    middleware: Sequence[AgentMiddleware] | None = None,
    enable_brand_context: bool = True,
    enable_media_tracking: bool = True,
    **kwargs: Any,
) -> CompiledStateGraph:
    """Create a studio agent with brand context and media tracking.

    This wraps ``create_deep_agent()`` adding:
    - BrandContextMiddleware (injects brand into system prompt)
    - MediaTrackerMiddleware (catalogs generated assets)

    All deepagents middleware (planning, filesystem, subagents,
    summarization) is applied automatically by ``create_deep_agent()``.

    Args:
        model: LLM model identifier. Defaults to Gemini 2.5 Flash.
        tools: Tools the agent can use.
        subagents: SubAgent specs for the task tool.
        system_prompt: Domain-specific system prompt.
        checkpointer: Persistence backend (SQLite/Postgres).
        store: Cross-session store for brand profiles.
        backend: File storage backend.
        middleware: Additional middleware beyond the studio defaults.
        enable_brand_context: Inject brand context into prompts.
        enable_media_tracking: Track generated media assets.
        **kwargs: Passed through to ``create_deep_agent()``.

    Returns:
        A compiled LangGraph agent.
    """
    studio_middleware: list[AgentMiddleware] = []

    if enable_brand_context:
        studio_middleware.append(BrandContextMiddleware())
    if enable_media_tracking:
        studio_middleware.append(MediaTrackerMiddleware())
    if middleware:
        studio_middleware.extend(middleware)

    if backend is None:
        backend = StateBackend

    return create_deep_agent(
        model=model,
        tools=tools,
        subagents=subagents,
        system_prompt=system_prompt,
        middleware=studio_middleware,
        checkpointer=checkpointer,
        store=store,
        backend=backend,
        **kwargs,
    )
