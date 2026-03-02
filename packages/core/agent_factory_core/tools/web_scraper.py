"""@tool wrappers for web scraping tools."""

import json

from langchain_core.tools import tool

from agent_factory_core.tools._internal import web_scraper as _impl


@tool
def scrape_brand_from_url(url: str) -> str:
    """Scrape brand information from a website URL.

    Extracts brand name, description, colors, and other identity elements.

    Args:
        url: Website URL or social media profile URL to scrape.
    """
    result = _impl.scrape_brand_from_url(url)
    return json.dumps(result)


@tool
def get_brand_context_from_url(url: str) -> str:
    """Extract detailed brand context from a URL for content creation.

    Args:
        url: Website URL to analyze.
    """
    result = _impl.get_brand_context_from_url(url)
    # Already returns a formatted string
    if isinstance(result, str):
        return result
    return json.dumps(result)
