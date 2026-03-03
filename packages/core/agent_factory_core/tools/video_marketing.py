"""@tool wrappers for marketing video studio tools.

These are from marketing_video_agent_factory's video_gen.py and animation.py -
includes generate_video (unified), product video, motion graphics.
"""

import json

from langchain_core.tools import tool

from agent_factory_core.tools._internal import video_gen_marketing as _mkt_impl
from agent_factory_core.tools._internal import animation as _anim_impl


@tool
def generate_video(
    prompt: str,
    image_path: str = "",
    duration_seconds: int = 8,
    aspect_ratio: str = "9:16",
    negative_prompt: str = "",
    logo_path: str = "",
    brand_name: str = "",
    brand_colors: str = "",
    cta_text: str = "",
) -> str:
    """Generate a marketing video using Veo 3.1.

    The prompt determines the video type. Follow the 5-part Veo formula:
    [Camera + lens] + [Subject] + [Action] + [Setting + atmosphere] + [Style + Audio].

    IMPORTANT: Do NOT include text/titles/company name in the Veo prompt.
    Veo cannot render text correctly. Branding (logo, name, CTA) is added
    automatically as post-processing overlays via the branding parameters.

    Args:
        prompt: Detailed cinematic video description (50-175 words). Include
            camera work, subject, action, context, style, and audio description.
            End with "No text, no titles, no captions, no words, no watermarks."
        image_path: Optional source image for image-to-video generation.
        duration_seconds: Video duration (5-8).
        aspect_ratio: Video aspect ratio ("9:16" for reels, "16:9" for landscape).
        negative_prompt: Elements to exclude (e.g. "blurry, low quality, distorted").
        logo_path: Path to brand logo for watermark overlay (post-processing).
        brand_name: Company name for text overlay (post-processing).
        brand_colors: JSON list of hex colors (e.g. '["#FF6B35", "#2EC4B6"]').
        cta_text: Call-to-action text overlay (e.g. "Shop Now").
    """
    colors_list = []
    if brand_colors:
        try:
            colors_list = json.loads(brand_colors)
        except (json.JSONDecodeError, TypeError):
            colors_list = []

    result = _mkt_impl.generate_video(
        prompt=prompt, image_path=image_path,
        duration_seconds=duration_seconds, aspect_ratio=aspect_ratio,
        negative_prompt=negative_prompt, logo_path=logo_path,
        brand_name=brand_name, brand_colors=colors_list,
        cta_text=cta_text,
    )
    return json.dumps(result)


@tool
def generate_marketing_product_video(
    product_image_path: str,
    product_name: str,
    animation_style: str = "showcase",
    duration_seconds: int = 8,
    aspect_ratio: str = "9:16",
    brand_context: str = "",
    logo_path: str = "",
    cta_text: str = "",
    target_audience: str = "",
) -> str:
    """Create a marketing product showcase video from a product image.

    Args:
        product_image_path: ACTUAL file path to the product image.
        product_name: Name of the product.
        animation_style: Style (showcase/zoom/lifestyle/unboxing).
        duration_seconds: Video duration.
        aspect_ratio: Video aspect ratio.
        brand_context: JSON string with brand name, colors, tone, etc.
        logo_path: Path to brand logo.
        cta_text: Call-to-action text.
        target_audience: Target audience.
    """
    # Parse brand_context JSON string to dict for _internal function
    brand_ctx = None
    if brand_context:
        try:
            brand_ctx = json.loads(brand_context)
        except (json.JSONDecodeError, TypeError):
            brand_ctx = None

    result = _mkt_impl.generate_animated_product_video(
        product_image_path=product_image_path,
        product_name=product_name, animation_style=animation_style,
        duration_seconds=duration_seconds, aspect_ratio=aspect_ratio,
        brand_context=brand_ctx, logo_path=logo_path or None,
        cta_text=cta_text or None, target_audience=target_audience,
    )
    return json.dumps(result)


@tool
def generate_marketing_motion_graphics(
    message: str,
    style: str = "modern",
    duration_seconds: int = 8,
    aspect_ratio: str = "9:16",
    brand_context: str = "",
    target_audience: str = "",
) -> str:
    """Create marketing motion graphics video.

    Args:
        message: Main message or announcement.
        style: Motion graphics style.
        duration_seconds: Video duration.
        aspect_ratio: Video aspect ratio.
        brand_context: JSON string with brand name, colors, tone, etc.
        target_audience: Target audience.
    """
    brand_ctx = None
    if brand_context:
        try:
            brand_ctx = json.loads(brand_context)
        except (json.JSONDecodeError, TypeError):
            brand_ctx = None

    result = _mkt_impl.generate_motion_graphics_video(
        message=message, style=style,
        duration_seconds=duration_seconds, aspect_ratio=aspect_ratio,
        brand_context=brand_ctx, target_audience=target_audience,
    )
    return json.dumps(result)


@tool
def animate_marketing_image(
    image_path: str,
    motion_prompt: str = "",
    duration_seconds: int = 5,
    aspect_ratio: str = "9:16",
    with_audio: bool = True,
    negative_prompt: str = "",
) -> str:
    """Animate a static image into video for marketing use.

    Args:
        image_path: Path to the source image.
        motion_prompt: Desired motion/animation description.
        duration_seconds: Video duration (5-8).
        aspect_ratio: Video aspect ratio.
        with_audio: Enable audio.
        negative_prompt: What to avoid.
    """
    result = _anim_impl.animate_image(
        image_path=image_path, motion_prompt=motion_prompt,
        duration_seconds=duration_seconds, aspect_ratio=aspect_ratio,
        with_audio=with_audio, negative_prompt=negative_prompt,
    )
    return json.dumps(result)


@tool
def generate_marketing_video_from_text(
    prompt: str,
    duration_seconds: int = 5,
    aspect_ratio: str = "16:9",
    with_audio: bool = True,
    negative_prompt: str = "",
) -> str:
    """Generate a marketing video from text using Veo 3.1.

    Args:
        prompt: Detailed video description.
        duration_seconds: Video duration.
        aspect_ratio: Video aspect ratio.
        with_audio: Enable audio.
        negative_prompt: What to avoid.
    """
    result = _anim_impl.generate_video_from_text(
        prompt=prompt, duration_seconds=duration_seconds,
        aspect_ratio=aspect_ratio, with_audio=with_audio,
        negative_prompt=negative_prompt,
    )
    return json.dumps(result)
