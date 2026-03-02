"""Video Studio agent factory."""

from __future__ import annotations

from typing import Any

from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from agent_factory_core.config.settings import ORCHESTRATOR_MODEL
from agent_factory_core.factory import create_studio_agent
from agent_factory_core.tools.response_formatter import format_response_for_user
from agent_factory_core.tools.web_search import (
    get_competitor_insights,
    search_trending_topics,
    search_web,
)

from video_studio.prompts.orchestrator import ROOT_AGENT_PROMPT
from video_studio.subagents import ALL_SUBAGENTS


def create_video_studio_agent(
    *,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    **kwargs: Any,
) -> CompiledStateGraph:
    """Create the video studio orchestrator agent.

    The orchestrator coordinates 4 specialist subagents for marketing
    video creation: video generation, animation, captions, and campaigns.
    """
    orchestrator_tools = [
        search_web,
        search_trending_topics,
        get_competitor_insights,
        format_response_for_user,
    ]

    return create_studio_agent(
        model=f"google_genai:{ORCHESTRATOR_MODEL}",
        tools=orchestrator_tools,
        subagents=ALL_SUBAGENTS,
        system_prompt=ROOT_AGENT_PROMPT,
        checkpointer=checkpointer,
        store=store,
        **kwargs,
    )
