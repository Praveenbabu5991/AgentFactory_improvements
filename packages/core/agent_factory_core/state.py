"""State types for the Studio Agent platform."""

from __future__ import annotations

from typing import Any, TypedDict


class BrandContext(TypedDict, total=False):
    """Brand identity and configuration."""

    name: str
    industry: str
    overview: str
    tone: str
    logo_path: str
    colors: list[str]
    reference_images: list[str]
    user_images: list[dict[str, Any]]
    target_audience: str
    products_services: str
    style_reference_url: str
    # Marketing-video-specific (optional)
    marketing_goals: list[str]
    brand_messaging: str
    competitive_positioning: str


class MediaAsset(TypedDict, total=False):
    """A generated media asset (image or video)."""

    asset_id: str
    asset_type: str  # "image" or "video"
    path: str
    url: str
    thread_id: str
    created_at: str
    metadata: dict[str, Any]


class StudioAgentState(TypedDict, total=False):
    """Extended state for studio agents.

    The core LangGraph agent state (messages, todos, files) is managed by
    deepagents middleware automatically. This adds studio-specific fields.
    """

    brand: BrandContext
    media_assets: list[MediaAsset]
