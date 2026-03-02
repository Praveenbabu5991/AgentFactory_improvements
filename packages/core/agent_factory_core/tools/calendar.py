"""@tool wrappers for calendar and event planning tools."""

import json
from typing import Optional

from langchain_core.tools import tool

from agent_factory_core.tools._internal import calendar as _impl


@tool
def get_upcoming_events(
    days_ahead: int = 30,
    region: str = "global",
) -> str:
    """Get upcoming events, holidays, and observances for content planning.

    Args:
        days_ahead: Number of days to look ahead (1-90).
        region: Geographic region (global/US/India/UK/etc.).
    """
    result = _impl.get_upcoming_events(days_ahead=days_ahead, region=region)
    return json.dumps(result)


@tool
def get_festivals_and_events(
    month: str = "",
    region: str = "global",
    year: Optional[int] = None,
    include_themes: bool = True,
) -> str:
    """Get festivals and events for a specific month.

    Args:
        month: Month name (empty for current month).
        region: Geographic region filter.
        year: Year for date calculations.
        include_themes: Include content theme suggestions.
    """
    result = _impl.get_festivals_and_events(
        month=month, region=region, year=year, include_themes=include_themes,
    )
    return json.dumps(result)


@tool
def get_content_calendar_suggestions(
    brand_name: str,
    niche: str = "general",
    tone: str = "professional",
    target_audience: str = "general audience",
    planning_period: str = "month",
    posts_per_week: int = 5,
) -> str:
    """Generate a content calendar with post suggestions.

    Args:
        brand_name: Name of the brand.
        niche: Industry or niche.
        tone: Brand tone of voice.
        target_audience: Target audience description.
        planning_period: week, month, or quarter.
        posts_per_week: Target posts per week.
    """
    result = _impl.get_content_calendar_suggestions(
        brand_name=brand_name, niche=niche, tone=tone,
        target_audience=target_audience, planning_period=planning_period,
        posts_per_week=posts_per_week,
    )
    return json.dumps(result)


@tool
def suggest_best_posting_times(
    niche: str,
    target_audience: str = "",
    timezone: str = "IST",
) -> str:
    """Suggest optimal posting times for social media.

    Args:
        niche: Industry/niche.
        target_audience: Target audience description.
        timezone: Timezone for recommendations.
    """
    result = _impl.suggest_best_posting_times(
        niche=niche, target_audience=target_audience, timezone=timezone,
    )
    return json.dumps(result)
