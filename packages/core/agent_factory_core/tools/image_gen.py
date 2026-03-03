"""@tool wrappers for image generation tools (Gemini)."""

import json
from typing import Optional

from langchain_core.tools import tool

from agent_factory_core.tools._internal import image_gen as _impl

# Per-request counter to enforce ONE image generation call per /chat/stream request.
# The LLM ignores prompt instructions to "stop after one generation", so we enforce here.
# reset_generation_counter() is called at the start of each /chat/stream request in app.py.
# This guards all image-generating tools: generate_post_image, generate_complete_post,
# generate_product_showcase. Internal calls (e.g. generate_complete_post calling
# generate_post_image internally) bypass the @tool wrapper, so they're unaffected.
_generation_call_count: int = 0
_generation_last_result: str = ""


def reset_generation_counter():
    """Reset the per-request generation counter. Called at the start of each /chat/stream request."""
    global _generation_call_count, _generation_last_result
    _generation_call_count = 0
    _generation_last_result = ""


def _check_and_block() -> str | None:
    """Return cached result if an image was already generated this request, else None."""
    if _generation_call_count >= 1 and _generation_last_result:
        print("   ⛔ BLOCKED: Image generation already called in this request. Returning previous result.")
        return _generation_last_result
    return None


def _record_result(output: str):
    """Record a successful generation so subsequent calls are blocked."""
    global _generation_call_count, _generation_last_result
    _generation_call_count += 1
    _generation_last_result = output


@tool
def generate_post_image(
    prompt: str,
    brand_name: str = "",
    brand_colors: str = "",
    style: str = "creative",
    logo_path: str = "",
    greeting_text: str = "",
    headline_text: str = "",
    subtext: str = "",
    cta_text: str = "",
    reference_images: str = "",
    user_images: str = "",
    user_image_instructions: str = "",
) -> str:
    """Generate a branded social media post image.

    Args:
        prompt: Visual scene description (WITHOUT text - text goes in separate params).
        brand_name: Company name.
        brand_colors: Comma-separated hex colors (e.g., "#FF6B35, #2C3E50").
        style: Visual style (creative/professional/playful/minimal/bold).
        logo_path: Path to brand logo file.
        greeting_text: Event greeting (e.g., "Happy Valentine's Day!").
        headline_text: Main headline text for the image.
        subtext: Supporting text.
        cta_text: Call-to-action text.
        reference_images: Comma-separated paths to reference style images.
        user_images: Comma-separated paths to user-uploaded images.
        user_image_instructions: How to use user images (e.g., "[PRODUCT_FOCUS] /path").
    """
    blocked = _check_and_block()
    if blocked:
        return blocked

    result = _impl.generate_post_image(
        prompt=prompt, brand_name=brand_name, brand_colors=brand_colors,
        style=style, logo_path=logo_path, greeting_text=greeting_text,
        headline_text=headline_text, subtext=subtext, cta_text=cta_text,
        reference_images=reference_images, user_images=user_images,
        user_image_instructions=user_image_instructions,
    )
    output = json.dumps(result)
    _record_result(output)
    return output


@tool
def generate_complete_post(
    prompt: str,
    brand_name: str = "",
    brand_colors: str = "",
    style: str = "creative",
    logo_path: str = "",
    industry: str = "",
    occasion: str = "",
    company_overview: str = "",
    greeting_text: str = "",
    headline_text: str = "",
    subtext: str = "",
    cta_text: str = "",
    reference_images: str = "",
    user_images: str = "",
    user_image_instructions: str = "",
    brand_voice: str = "",
    target_audience: str = "",
    emoji_level: str = "moderate",
    max_hashtags: int = 15,
) -> str:
    """Generate a complete post: image + caption + hashtags in ONE call.

    This is the primary tool for post generation.

    Args:
        prompt: Visual scene description.
        brand_name: Company name.
        brand_colors: Comma-separated hex colors.
        style: Visual style.
        logo_path: Path to brand logo.
        industry: Brand's industry.
        occasion: Event or occasion theme.
        company_overview: Brief brand description.
        greeting_text: Event greeting text for the image.
        headline_text: Main headline text for the image.
        subtext: Supporting text for the image.
        cta_text: Call-to-action text.
        reference_images: Reference style image paths.
        user_images: User-uploaded image paths.
        user_image_instructions: Usage instructions for user images.
        brand_voice: Brand voice for caption writing.
        target_audience: Who the caption should speak to.
        emoji_level: Emoji usage (none/minimal/moderate/heavy).
        max_hashtags: Number of hashtags to generate.
    """
    blocked = _check_and_block()
    if blocked:
        return blocked

    result = _impl.generate_complete_post(
        prompt=prompt, brand_name=brand_name, brand_colors=brand_colors,
        style=style, logo_path=logo_path, industry=industry,
        occasion=occasion, company_overview=company_overview,
        greeting_text=greeting_text, headline_text=headline_text,
        subtext=subtext, cta_text=cta_text,
        reference_images=reference_images, user_images=user_images,
        user_image_instructions=user_image_instructions,
        brand_voice=brand_voice, target_audience=target_audience,
        emoji_level=emoji_level, max_hashtags=max_hashtags,
    )
    output = json.dumps(result)
    _record_result(output)
    return output


@tool
def generate_product_showcase(
    product_image_path: str,
    product_name: str,
    product_features: str = "",
    brand_name: str = "",
    brand_colors: str = "",
    industry: str = "",
    target_audience: str = "",
    launch_context: str = "",
    price_point: str = "",
    style: str = "creative",
) -> str:
    """Generate a product showcase post from an uploaded product image.

    Args:
        product_image_path: Path to the product image file.
        product_name: Name of the product.
        product_features: Key features (comma-separated).
        brand_name: Company name.
        brand_colors: Brand color palette.
        industry: Industry/niche.
        target_audience: Who this product is for.
        launch_context: Launch type (new/seasonal/limited).
        price_point: Price or positioning.
        style: Visual style.
    """
    blocked = _check_and_block()
    if blocked:
        return blocked

    result = _impl.generate_product_showcase(
        product_image_path=product_image_path,
        product_name=product_name, product_features=product_features,
        brand_name=brand_name, brand_colors=brand_colors,
        industry=industry, target_audience=target_audience,
        launch_context=launch_context, price_point=price_point,
        style=style,
    )
    output = json.dumps(result)
    _record_result(output)
    return output


@tool
def edit_post_image(
    original_image_path: str,
    edit_instruction: str,
) -> str:
    """Edit/regenerate a post image based on feedback.

    Args:
        original_image_path: Path to the image to edit.
        edit_instruction: What to change (e.g., "make background darker").
    """
    result = _impl.edit_post_image(
        original_image_path=original_image_path,
        edit_instruction=edit_instruction,
    )
    return json.dumps(result)


@tool
def regenerate_post(
    original_image_path: str,
    edit_instruction: str,
    regenerate_caption: bool = False,
    regenerate_hashtags: bool = False,
    original_caption: str = "",
    original_context_json: str = "",
) -> str:
    """Regenerate a post with comprehensive changes (image + optional caption/hashtags).

    Args:
        original_image_path: Path to source image.
        edit_instruction: What to change in the image.
        regenerate_caption: Whether to also regenerate the caption.
        regenerate_hashtags: Whether to also regenerate hashtags.
        original_caption: Current caption text for context.
        original_context_json: JSON with brand_name, industry, occasion, etc.
    """
    result = _impl.regenerate_post(
        original_image_path=original_image_path,
        edit_instruction=edit_instruction,
        regenerate_caption=regenerate_caption,
        regenerate_hashtags=regenerate_hashtags,
        original_caption=original_caption,
        original_context_json=original_context_json,
    )
    return json.dumps(result)


@tool
def extract_brand_colors(image_path: str) -> str:
    """Extract dominant colors from a logo or image.

    Args:
        image_path: Path to the image file.
    """
    result = _impl.extract_brand_colors(image_path)
    return json.dumps(result)
