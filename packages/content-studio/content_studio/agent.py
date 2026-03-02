"""Content Studio agent factory."""

from __future__ import annotations

from typing import Any

from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from agent_factory_core.config.settings import ORCHESTRATOR_MODEL
from agent_factory_core.factory import create_studio_agent
from agent_factory_core.tools.calendar import get_upcoming_events
from agent_factory_core.tools.instagram import get_profile_summary, scrape_instagram_profile
from agent_factory_core.tools.response_formatter import format_response_for_user
from agent_factory_core.tools.web_scraper import scrape_brand_from_url
from agent_factory_core.tools.web_search import search_web

from content_studio.prompts.orchestrator import ROOT_AGENT_PROMPT
from content_studio.subagents import ALL_SUBAGENTS


def create_content_studio_agent(
    *,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    **kwargs: Any,
) -> CompiledStateGraph:
    """Create the content studio orchestrator agent.

    The orchestrator coordinates 8 specialist subagents for social media
    content creation: ideas, briefs, images, captions, editing,
    animation, video, and campaigns.
    """
    # Root orchestrator tools (research + response formatting)
    orchestrator_tools = [
        scrape_instagram_profile,
        get_profile_summary,
        search_web,
        get_upcoming_events,
        scrape_brand_from_url,
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
