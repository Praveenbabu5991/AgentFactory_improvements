"""@tool wrappers for Instagram tools."""

import json

from langchain_core.tools import tool

from agent_factory_core.tools._internal import instagram as _impl


@tool
def scrape_instagram_profile(profile_url: str) -> str:
    """Scrape an Instagram profile for brand analysis.

    Args:
        profile_url: Instagram profile URL or @username.
    """
    result = _impl.scrape_instagram_profile(profile_url)
    return json.dumps(result)


@tool
def get_profile_summary(username: str) -> str:
    """Get a summary analysis of an Instagram profile.

    Args:
        username: Instagram username or profile URL.
    """
    result = _impl.get_profile_summary(username)
    return result  # Already returns a string
