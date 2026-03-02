"""@tool wrappers for AI knowledge and trending topic tools."""

import json

from langchain_core.tools import tool

from agent_factory_core.tools._internal import web_search as _impl


@tool
def search_web(query: str, context: str = "") -> str:
    """Get AI-generated knowledge about a topic for content creation.

    NOTE: Uses LLM knowledge, not real-time web search.

    Args:
        query: Topic or question to research.
        context: Additional context for the query.
    """
    result = _impl.get_ai_knowledge(query=query, context=context)
    return json.dumps(result)


@tool
def search_trending_topics(
    niche: str,
    region: str = "global",
    platform: str = "instagram",
) -> str:
    """Get trending topic suggestions for a niche.

    NOTE: AI predictions based on patterns, not real-time trends.

    Args:
        niche: Industry or topic niche.
        region: Geographic region.
        platform: Social media platform.
    """
    result = _impl.search_trending_topics(
        niche=niche, region=region, platform=platform,
    )
    return json.dumps(result)


@tool
def get_competitor_insights(
    competitor_handles: str,
    platform: str = "instagram",
) -> str:
    """Get strategic insights about competing in a space.

    Args:
        competitor_handles: Comma-separated competitor account types/categories.
        platform: Social media platform.
    """
    result = _impl.get_competitor_insights(
        competitor_handles=competitor_handles, platform=platform,
    )
    return json.dumps(result)
