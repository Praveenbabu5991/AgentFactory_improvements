"""@tool wrappers for content creation tools (captions, hashtags)."""

import json

from langchain_core.tools import tool

from agent_factory_core.tools._internal import content as _impl


@tool
def write_caption(
    topic: str,
    brand_name: str = "",
    brand_voice: str = "professional yet friendly",
    target_audience: str = "general",
    key_message: str = "",
    occasion: str = "",
    tone: str = "engaging",
    max_length: int = 500,
    include_cta: bool = True,
    emoji_level: str = "moderate",
    company_overview: str = "",
    image_description: str = "",
) -> str:
    """Write an engaging Instagram caption for a post.

    Args:
        topic: What the post is about.
        brand_name: Brand name to mention naturally.
        brand_voice: Brand voice style.
        target_audience: Who the caption should speak to.
        key_message: Core message to convey.
        occasion: Event or occasion context.
        tone: Caption tone (engaging/professional/playful).
        max_length: Maximum caption length in characters.
        include_cta: Whether to include a call-to-action.
        emoji_level: Emoji usage (none/minimal/moderate/heavy).
        company_overview: Brief brand description.
        image_description: Description of the image this caption is for.
    """
    result = _impl.write_caption(
        topic=topic, brand_voice=brand_voice,
        target_audience=target_audience, key_message=key_message,
        occasion=occasion, tone=tone, max_length=max_length,
        include_cta=include_cta, emoji_level=emoji_level,
        company_overview=company_overview, brand_name=brand_name,
        image_description=image_description,
    )
    return json.dumps(result)


@tool
def generate_hashtags(
    topic: str,
    niche: str = "",
    brand_name: str = "",
    trending_context: str = "",
    max_hashtags: int = 15,
) -> str:
    """Generate strategic hashtags for a social media post.

    Args:
        topic: Post topic for hashtag relevance.
        niche: Industry/niche for targeted hashtags.
        brand_name: Brand name for branded hashtag.
        trending_context: Any trending topics to incorporate.
        max_hashtags: Number of hashtags to generate (10-30).
    """
    result = _impl.generate_hashtags(
        topic=topic, niche=niche, brand_name=brand_name,
        trending_context=trending_context, max_hashtags=max_hashtags,
    )
    return json.dumps(result)


@tool
def improve_caption(
    original_caption: str,
    feedback: str,
    preserve_tone: bool = True,
) -> str:
    """Improve an existing caption based on feedback.

    Args:
        original_caption: The current caption text.
        feedback: What to change (e.g., "make it shorter", "more professional").
        preserve_tone: Whether to keep the same overall tone.
    """
    result = _impl.improve_caption(
        original_caption=original_caption,
        feedback=feedback,
        preserve_tone=preserve_tone,
    )
    return json.dumps(result)
