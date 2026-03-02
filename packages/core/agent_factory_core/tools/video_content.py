"""@tool wrappers for content-studio video tools (Veo 3.1).

These wrap functions from hylancer's image_gen.py (animate_image,
generate_video_from_text) and video_gen_content.py (product video,
motion graphics).
"""

import json

from langchain_core.tools import tool

from agent_factory_core.tools._internal import image_gen as _img_impl
from agent_factory_core.tools._internal import video_gen_content as _vid_impl


@tool
def animate_image(
    image_path: str,
    motion_prompt: str = "",
    duration_seconds: int = 8,
    aspect_ratio: str = "9:16",
    with_audio: bool = True,
    negative_prompt: str = "",
) -> str:
    """Animate a static image into a video using Veo 3.1.

    Args:
        image_path: Path to the source image.
        motion_prompt: Description of desired motion/animation style.
        duration_seconds: Video duration in seconds (5-8).
        aspect_ratio: Video aspect ratio ("16:9" or "9:16").
        with_audio: Enable ambient audio generation.
        negative_prompt: What to avoid in the video.
    """
    result = _img_impl.animate_image(
        image_path=image_path, motion_prompt=motion_prompt,
        duration_seconds=duration_seconds, aspect_ratio=aspect_ratio,
        with_audio=with_audio, negative_prompt=negative_prompt,
    )
    return json.dumps(result)


@tool
def generate_video_from_text(
    prompt: str,
    duration_seconds: int = 8,
    aspect_ratio: str = "9:16",
    with_audio: bool = True,
    negative_prompt: str = "",
) -> str:
    """Generate a video from a text description using Veo 3.1.

    Args:
        prompt: Detailed video description.
        duration_seconds: Video duration (5-8).
        aspect_ratio: Video aspect ratio.
        with_audio: Enable audio generation.
        negative_prompt: What to avoid.
    """
    result = _img_impl.generate_video_from_text(
        prompt=prompt, duration_seconds=duration_seconds,
        aspect_ratio=aspect_ratio, with_audio=with_audio,
        negative_prompt=negative_prompt,
    )
    return json.dumps(result)


@tool
def generate_animated_product_video(
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
    """Create an animated product showcase video from a product image.

    Args:
        product_image_path: ACTUAL file path to the product image.
        product_name: Name of the product.
        animation_style: Style (showcase/zoom/lifestyle/unboxing).
        duration_seconds: Video duration (5-8).
        aspect_ratio: Video aspect ratio.
        brand_context: JSON string with brand name, colors, tone, logo_path.
        logo_path: Path to brand logo for watermark.
        cta_text: Call-to-action text for end of video.
        target_audience: Target audience for marketing focus.
    """
    brand_ctx = None
    if brand_context:
        try:
            brand_ctx = json.loads(brand_context)
        except (json.JSONDecodeError, TypeError):
            brand_ctx = None

    result = _vid_impl.generate_animated_product_video(
        product_image_path=product_image_path,
        product_name=product_name, animation_style=animation_style,
        duration_seconds=duration_seconds, aspect_ratio=aspect_ratio,
        brand_context=brand_ctx, logo_path=logo_path or None,
        cta_text=cta_text or None, target_audience=target_audience,
    )
    return json.dumps(result)


@tool
def generate_motion_graphics_video(
    message: str,
    style: str = "modern",
    duration_seconds: int = 8,
    aspect_ratio: str = "9:16",
    brand_context: str = "",
    target_audience: str = "",
) -> str:
    """Create a branded motion graphics video from a text message.

    Args:
        message: Main message or announcement for the video.
        style: Motion graphics style (modern/minimal/bold/elegant/playful).
        duration_seconds: Video duration (5-8).
        aspect_ratio: Video aspect ratio.
        brand_context: JSON string with brand name, colors, tone.
        target_audience: Target audience for marketing focus.
    """
    brand_ctx = None
    if brand_context:
        try:
            brand_ctx = json.loads(brand_context)
        except (json.JSONDecodeError, TypeError):
            brand_ctx = None

    result = _vid_impl.generate_motion_graphics_video(
        message=message, style=style,
        duration_seconds=duration_seconds, aspect_ratio=aspect_ratio,
        brand_context=brand_ctx, target_audience=target_audience,
    )
    return json.dumps(result)
