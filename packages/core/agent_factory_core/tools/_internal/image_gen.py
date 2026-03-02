"""
Image Generation Tools using Gemini API.

Provides image generation, editing, and animation capabilities
with proper error handling and rate limiting.
"""

import os
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from google import genai
from google.genai import types
from PIL import Image
from colorthief import ColorThief
from dotenv import load_dotenv

load_dotenv()


class ImageGenerationError(Exception):
    """Custom exception for image generation errors."""
    pass


def _get_client():
    """Get Gemini client with validation."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ImageGenerationError(
            "API key not configured. Please set GOOGLE_API_KEY in your environment."
        )
    return genai.Client(api_key=api_key)


def _retry_with_backoff(func, max_retries: int = 3, base_delay: float = 2.0):
    """Execute function with exponential backoff retry."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            # Only skip retry for truly unrecoverable errors
            if "not found" in error_str and "model" in error_str:
                raise  # Model doesn't exist - no point retrying
            if "api" in error_str and "key" in error_str:
                raise  # Bad API key - no point retrying
            # Retry everything else (including INVALID_ARGUMENT which can be
            # transient rate-limits on Gemini free tier)
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"⚠️ Attempt {attempt + 1} failed ({str(e)[:100]}), retrying in {delay}s...")
                time.sleep(delay)
    raise last_error


def _format_error(error: Exception, context: str = "") -> dict:
    """Format error into user-friendly response."""
    error_str = str(error).lower()
    
    if "quota" in error_str or "rate" in error_str:
        message = "The image generation service is busy. Please wait a moment and try again."
    elif "safety" in error_str or "blocked" in error_str:
        message = "The image couldn't be generated due to content guidelines. Try adjusting your prompt."
    elif "api" in error_str and "key" in error_str:
        message = "There's an issue with the API configuration. Please contact support."
    elif "timeout" in error_str:
        message = "The image generation took too long. Try a simpler design."
    elif "not found" in error_str:
        message = "The requested model or resource wasn't found. Please try again."
    else:
        message = f"Image generation failed. {context}" if context else "Image generation failed. Please try again."
    
    return {
        "status": "error",
        "message": message,
        "technical_details": str(error)
    }


def extract_brand_colors(image_path: str) -> dict:
    """
    Extract dominant colors from a logo/image using ColorThief.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with dominant color and palette
    """
    try:
        if not os.path.exists(image_path):
            return {
                "status": "error",
                "message": f"Image not found: {image_path}",
                "dominant": "#3498db",
                "palette": ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]
            }
        
        color_thief = ColorThief(image_path)
        dominant = color_thief.get_color(quality=1)
        palette = color_thief.get_palette(color_count=6, quality=1)
        
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
        
        return {
            "status": "success",
            "dominant": rgb_to_hex(dominant),
            "palette": [rgb_to_hex(color) for color in palette]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Could not extract colors: {str(e)}",
            "dominant": "#3498db",
            "palette": ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]
        }


def generate_post_image(
    prompt: str,
    brand_name: str = "",
    brand_colors: str = "",
    style: str = "creative",
    logo_path: str = "",
    output_dir: str = "generated",
    industry: str = "",
    occasion: str = "",
    reference_images: str = "",
    company_overview: str = "",
    greeting_text: str = "",
    headline_text: str = "",
    subtext: str = "",
    cta_text: str = "",
    user_images: str = "",
    user_image_instructions: str = ""
) -> dict:
    """
    Generate a professional social media post image using Gemini.

    Args:
        prompt: Description of the image/visual concept
        brand_name: Name of the brand/company
        brand_colors: Comma-separated brand colors (hex codes)
        style: Visual style (creative, professional, playful, minimal, bold)
        logo_path: Path to logo image to incorporate
        output_dir: Directory to save generated images
        industry: Brand's industry/niche
        occasion: Special occasion/event theme
        reference_images: Comma-separated paths to reference images
        company_overview: Description of what the company does
        greeting_text: Event greeting (e.g., "Happy Valentine's Day!")
        headline_text: Main headline text for the image
        subtext: Supporting text/tagline
        cta_text: Call-to-action text
        user_images: Comma-separated paths to user-uploaded images to incorporate
        user_image_instructions: Instructions on how to use user images (e.g., "[BACKGROUND] path1, [PRODUCT_FOCUS] path2")

    Returns:
        Dictionary with image path and generation details
    """
    print(f"🎨 Generating image for: {brand_name or 'brand'}")
    print(f"   Style: {style}, Occasion: {occasion or 'general'}")
    
    try:
        client = _get_client()
        
        # Build color instructions - STRONGLY emphasize brand colors
        color_scheme = ""
        colors_list = []
        if brand_colors:
            colors_list = [c.strip() for c in brand_colors.split(",") if c.strip()]
            if colors_list:
                primary = colors_list[0]
                color_scheme = f"""
COLOR PALETTE (MUST USE THESE COLORS PROMINENTLY):
- PRIMARY COLOR: {primary} - Use this as the DOMINANT color in the image
- This color should be visible in backgrounds, overlays, accents, or lighting
"""
                if len(colors_list) > 1:
                    color_scheme += f"- SECONDARY COLORS: {', '.join(colors_list[1:4])} - Use as accents\n"
                color_scheme += f"- The overall color mood of the image should reflect {primary}\n"
        
        # Style descriptions
        style_map = {
            'creative': 'Artistic, imaginative, visually striking',
            'professional': 'Clean, corporate, polished',
            'playful': 'Fun, vibrant, energetic',
            'minimal': 'Simple, clean, focused',
            'bold': 'Strong, impactful, attention-grabbing'
        }
        style_desc = style_map.get(style, style_map['creative'])
        
        # Extract colors from reference images if provided
        ref_colors = []
        ref_context = ""
        has_refs = False
        
        if reference_images:
            ref_paths = [p.strip() for p in reference_images.split(",") if p.strip() and os.path.exists(p.strip())]
            if ref_paths:
                has_refs = True
                print(f"   📸 Using {len(ref_paths)} reference images")
                for rp in ref_paths[:3]:
                    try:
                        colors = extract_brand_colors(rp)
                        if colors.get("status") == "success":
                            ref_colors.append(colors.get("dominant"))
                            ref_colors.extend(colors.get("palette", [])[:2])
                    except:
                        pass
                
                ref_colors = list(dict.fromkeys(ref_colors))[:6]
                ref_context = f"""
REFERENCE IMAGES PROVIDED - Match this visual style:
- Extracted colors: {', '.join(ref_colors) if ref_colors else 'Match reference style'}
- Match the design style, composition, and mood from references
- Create an image that looks like it belongs in the same campaign"""
        
        # Build the generation prompt with strong color emphasis
        primary_color = colors_list[0] if colors_list else "#000000"
        
        # Build explicit text section - only the actual text, no labels
        text_elements = []
        if greeting_text:
            text_elements.append(f'At the TOP in large decorative text: "{greeting_text}"')
        if headline_text:
            text_elements.append(f'Main headline (prominent, eye-catching): "{headline_text}"')
        if subtext:
            text_elements.append(f'Supporting text (smaller): "{subtext}"')
        if cta_text:
            text_elements.append(f'Call-to-action (button or highlighted): "{cta_text}"')
        
        text_section = ""
        if text_elements:
            text_section = f"""
EXACT TEXT TO DISPLAY ON THE IMAGE:
{chr(10).join(f"• {t}" for t in text_elements)}

⚠️ CRITICAL TEXT RULES:
- Display ONLY the text inside the quotation marks above
- DO NOT write words like "HEADLINE", "GREETING", "SUBTEXT", "CTA", "TEXT" on the image
- The viewer should see "{greeting_text or headline_text}" NOT "HEADLINE: {headline_text}"
- Make all text legible with good contrast against background
- Use elegant typography that matches the {style} style
"""
        
        full_prompt = f"""Create a premium Instagram post image for {brand_name or 'a brand'}.

VISUAL CONCEPT: {prompt}

BRAND IDENTITY:
- Brand: {brand_name or 'Brand'}
- Industry: {industry or 'General'}
{f"- About: {company_overview}" if company_overview else ""}

{color_scheme}

VISUAL STYLE: {style_desc}
{f"OCCASION/THEME: {occasion}" if occasion else ""}

CRITICAL COLOR REQUIREMENT:
The image MUST prominently feature the brand's primary color ({primary_color}).
- Use {primary_color} in background gradient, overlay, or prominent elements
- The brand colors should be immediately recognizable
- Overall mood should reflect the brand identity

{text_section}

{ref_context if has_refs else f'''
VISUAL APPROACH - NO REFERENCE IMAGES PROVIDED:
Since no reference images are given, create a scene featuring REAL HUMANS:
- Include realistic, diverse people as customers/clients relevant to the {industry or 'business'} industry
- Show authentic human interaction with the brand's product/service
- People should look natural, engaged, and genuine (not stock photo-like)
- Match demographics to the target audience based on: {company_overview or 'the brand'}
- Examples: travelers enjoying destinations, professionals using tech, customers experiencing service
- The humans should feel like real customers, not models

IMPORTANT: Do NOT use generic stock photo poses. Show genuine human moments.
Premium, polished aesthetic suitable for brand social media.'''}

TECHNICAL SPECS:
- Aspect ratio: 4:5 (Instagram optimal)
- Ultra high resolution
- Sharp, readable text
- Brand colors prominent
{f"- Include {brand_name} logo: subtle, bottom-right corner" if logo_path else ""}

Create a scroll-stopping, magazine-quality image."""

        # Prepare content with images
        contents = [full_prompt]
        
        if logo_path and os.path.exists(logo_path):
            try:
                logo_image = Image.open(logo_path)
                contents.append(logo_image)
                print(f"   📷 Added logo: {logo_path}")
            except Exception as e:
                print(f"   ⚠️ Could not load logo: {e}")
        
        if reference_images:
            ref_paths = [p.strip() for p in reference_images.split(",") if p.strip()]
            for ref_path in ref_paths[:3]:  # Limit to 3 references
                if os.path.exists(ref_path):
                    try:
                        ref_image = Image.open(ref_path)
                        contents.append(ref_image)
                        print(f"   📷 Added reference: {ref_path}")
                    except Exception as e:
                        print(f"   ⚠️ Could not load reference {ref_path}: {e}")

        # Handle user-uploaded images to incorporate into the post
        if user_images:
            user_img_paths = [p.strip() for p in user_images.split(",") if p.strip()]
            user_img_count = 0
            for user_img_path in user_img_paths[:5]:  # Limit to 5 user images
                if os.path.exists(user_img_path):
                    try:
                        user_img = Image.open(user_img_path)
                        contents.append(user_img)
                        user_img_count += 1
                        print(f"   📸 Added user image: {user_img_path}")
                    except Exception as e:
                        print(f"   ⚠️ Could not load user image {user_img_path}: {e}")

            if user_img_count > 0:
                # Add instructions for how to use the user images
                user_img_prompt = f"""

USER PROVIDED IMAGES ({user_img_count} image(s)):
The user has uploaded {user_img_count} image(s) to be incorporated into this post.
"""
                if user_image_instructions:
                    # Parse structured instructions like "[BACKGROUND] path1, [PRODUCT_FOCUS] path2"
                    user_img_prompt += f"""
SPECIFIC USAGE INSTRUCTIONS:
{user_image_instructions}
"""
                else:
                    user_img_prompt += """
- Incorporate these images naturally into the design
- Maintain the quality and visibility of the uploaded images
- Blend them harmoniously with the brand colors and overall aesthetic
- Ensure they enhance rather than distract from the message
"""
                # Insert user image instructions into the prompt
                contents[0] = contents[0] + user_img_prompt

        # Small delay between successive API calls to avoid rate-limits
        time.sleep(1)

        # Generate image with retry
        model = os.getenv("IMAGE_MODEL", "gemini-3-pro-image-preview")

        def make_request():
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["image", "text"],
                )
            )
        
        response = _retry_with_backoff(make_request)
        
        # Save the generated image
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_id = str(uuid.uuid4())[:8]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"post_{timestamp}_{image_id}.png"
                image_path = output_path / filename
                
                with open(image_path, "wb") as f:
                    f.write(part.inline_data.data)
                
                print(f"   ✅ Image saved: {image_path}")
                
                return {
                    "status": "success",
                    "image_path": str(image_path),
                    "filename": filename,
                    "url": f"/generated/{filename}",
                    "prompt_used": prompt,
                    "style": style,
                    "model": model
                }
        
        return {
            "status": "error",
            "message": "No image was generated. Try adjusting your prompt."
        }
            
    except Exception as e:
        return _format_error(e, "Try simplifying your design request.")


def generate_complete_post(
    prompt: str,
    brand_name: str = "",
    brand_colors: str = "",
    style: str = "creative",
    logo_path: str = "",
    output_dir: str = "generated",
    industry: str = "",
    occasion: str = "",
    reference_images: str = "",
    company_overview: str = "",
    greeting_text: str = "",
    headline_text: str = "",
    subtext: str = "",
    cta_text: str = "",
    user_images: str = "",
    user_image_instructions: str = "",
    brand_voice: str = "professional yet friendly",
    target_audience: str = "",
    emoji_level: str = "moderate",
    max_hashtags: int = 15
) -> dict:
    """
    Generate a complete social media post with image, caption, and hashtags.

    This is the primary tool for creating full posts in one call.

    Args:
        prompt: Visual concept/description for the image
        brand_name: Name of the brand/company
        brand_colors: Comma-separated brand colors (hex codes)
        style: Visual style (creative, professional, playful, minimal, bold)
        logo_path: Path to logo image to incorporate
        output_dir: Directory to save generated images
        industry: Brand's industry/niche
        occasion: Special occasion/event theme
        reference_images: Comma-separated paths to reference images
        company_overview: Description of what the company does
        greeting_text: Event greeting (e.g., "Happy Valentine's Day!")
        headline_text: Main headline text for the image
        subtext: Supporting text/tagline
        cta_text: Call-to-action text
        user_images: Comma-separated paths to user-uploaded images
        user_image_instructions: Instructions on how to use user images
        brand_voice: Brand's tone of voice for caption
        target_audience: Target audience description
        emoji_level: none, minimal, moderate, heavy
        max_hashtags: Maximum number of hashtags to generate

    Returns:
        Dictionary with image, caption, hashtags, and full post content
    """
    from agent_factory_core.tools._internal.content import write_caption, generate_hashtags

    print(f"🎯 Generating complete post for: {brand_name or 'brand'}")

    # Step 1: Generate the image
    image_result = generate_post_image(
        prompt=prompt,
        brand_name=brand_name,
        brand_colors=brand_colors,
        style=style,
        logo_path=logo_path,
        output_dir=output_dir,
        industry=industry,
        occasion=occasion,
        reference_images=reference_images,
        company_overview=company_overview,
        greeting_text=greeting_text,
        headline_text=headline_text,
        subtext=subtext,
        cta_text=cta_text,
        user_images=user_images,
        user_image_instructions=user_image_instructions
    )

    if image_result.get("status") != "success":
        return image_result

    # Step 2: Generate caption based on the image and context
    topic = prompt
    if occasion:
        topic = f"{occasion}: {prompt}"

    caption_result = write_caption(
        topic=topic,
        brand_voice=brand_voice,
        target_audience=target_audience or industry or "general",
        key_message=headline_text or subtext or "",
        occasion=occasion,
        tone="engaging",
        include_cta=bool(cta_text),
        emoji_level=emoji_level,
        company_overview=company_overview,
        brand_name=brand_name,
        image_description=prompt
    )

    # Step 3: Generate hashtags
    hashtag_result = generate_hashtags(
        topic=topic,
        niche=industry,
        brand_name=brand_name,
        trending_context=occasion,
        max_hashtags=max_hashtags
    )

    # Combine results
    result = {
        "status": "success",
        "image": image_result,
        "image_path": image_result.get("image_path"),
        "image_url": image_result.get("url"),
    }

    # Add caption
    if caption_result.get("status") == "success":
        result["caption"] = caption_result.get("caption")
        result["caption_length"] = caption_result.get("character_count")
    else:
        result["caption"] = f"✨ {headline_text or prompt}\n\n{cta_text or 'Check it out!'}"
        result["caption_error"] = caption_result.get("message")

    # Add hashtags
    if hashtag_result.get("status") == "success":
        result["hashtags"] = hashtag_result.get("hashtags")
        result["hashtag_string"] = hashtag_result.get("hashtag_string")
    else:
        result["hashtags"] = []
        result["hashtag_string"] = ""
        result["hashtag_error"] = hashtag_result.get("message")

    # Create full post text
    full_post = result["caption"]
    if result.get("hashtag_string"):
        full_post += f"\n\n.\n.\n.\n\n{result['hashtag_string']}"
    result["full_post"] = full_post

    print(f"   ✅ Complete post generated!")
    print(f"   📷 Image: {result.get('image_path')}")
    print(f"   📝 Caption: {len(result.get('caption', ''))} chars")
    print(f"   #️⃣ Hashtags: {len(result.get('hashtags', []))}")

    return result


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
    logo_path: str = "",
    output_dir: str = "generated",
    showcase_style: str = "lifestyle",
    headline_text: str = "",
    cta_text: str = "Shop Now"
) -> dict:
    """
    Generate a product showcase post featuring an uploaded product image.

    Creates a professional product post that incorporates the user's actual
    product image into a marketing-ready social media post.

    Args:
        product_image_path: Path to the uploaded product image
        product_name: Name of the product being showcased
        product_features: Key features/selling points (comma-separated)
        brand_name: Name of the brand/company
        brand_colors: Comma-separated brand colors (hex codes)
        industry: Brand's industry (fashion, tech, food, etc.)
        target_audience: Who the product is for
        launch_context: Context like "New Launch", "Summer Collection", "Limited Edition"
        price_point: Price or pricing tier ("$49", "Premium", etc.)
        style: Visual style (creative, professional, playful, minimal, bold)
        logo_path: Path to logo image
        output_dir: Directory to save generated images
        showcase_style: "lifestyle" (in-use), "studio" (clean shot), "flatlay" (top-down)
        headline_text: Main headline (defaults to product name)
        cta_text: Call-to-action text

    Returns:
        Dictionary with product post including image, caption, and hashtags
    """
    from agent_factory_core.tools._internal.content import write_caption, generate_hashtags

    print(f"🛍️ Generating product showcase for: {product_name}")
    print(f"   Product image: {product_image_path}")
    print(f"   Style: {showcase_style}, Brand: {brand_name}")

    # Resolve product image path - use CWD where generated/uploads dirs exist
    resolved_product_path = product_image_path
    if product_image_path.startswith(("/uploads/", "/generated/")):
        resolved_product_path = str(Path.cwd() / product_image_path.lstrip("/"))
    elif not os.path.isabs(product_image_path):
        resolved_product_path = str(Path.cwd() / product_image_path)

    if not os.path.exists(resolved_product_path):
        return {
            "status": "error",
            "message": f"Product image not found: {product_image_path}"
        }

    # Build showcase-specific prompts
    showcase_prompts = {
        "lifestyle": f"""Create a lifestyle marketing image featuring this product.
Show the product being used or worn by a person in a natural, aspirational setting.
The product should be the hero of the image, clearly visible and highlighted.
Professional photography quality with natural lighting.""",

        "studio": f"""Create a clean, professional studio product shot.
Feature this product on a clean background with professional lighting.
The product should be perfectly lit with subtle shadows for depth.
High-end commercial photography style, perfect for e-commerce.""",

        "flatlay": f"""Create a stylish flatlay (top-down) product arrangement.
Feature this product as the centerpiece with complementary props.
Clean, organized layout with aesthetic appeal.
Instagram-worthy flatlay photography style."""
    }

    base_prompt = showcase_prompts.get(showcase_style, showcase_prompts["lifestyle"])

    # Build the full prompt
    prompt_parts = [
        base_prompt,
        "",
        f"PRODUCT: {product_name}",
    ]

    if product_features:
        prompt_parts.append(f"KEY FEATURES: {product_features}")
    if industry:
        prompt_parts.append(f"INDUSTRY: {industry}")
    if launch_context:
        prompt_parts.append(f"CONTEXT: {launch_context}")

    prompt_parts.extend([
        "",
        "REQUIREMENTS:",
        "- The uploaded product must be the HERO of the image",
        "- Product should be clearly visible and recognizable",
        "- Maintain product accuracy - don't alter the actual product",
        "- Create an aspirational, marketing-ready image",
        "- High quality suitable for Instagram/social media",
    ])

    if brand_colors:
        prompt_parts.append(f"- Incorporate brand colors: {brand_colors}")

    full_prompt = "\n".join(prompt_parts)

    # Use the headline or product name
    display_headline = headline_text or product_name

    # Generate the image with product focus
    user_image_instructions = f"[PRODUCT_FOCUS] {product_image_path}"

    image_result = generate_post_image(
        prompt=full_prompt,
        brand_name=brand_name,
        brand_colors=brand_colors,
        style=style,
        logo_path=logo_path,
        output_dir=output_dir,
        industry=industry,
        occasion=launch_context,
        headline_text=display_headline,
        cta_text=cta_text,
        user_images=product_image_path,
        user_image_instructions=user_image_instructions
    )

    if image_result.get("status") != "success":
        return image_result

    # Generate product-focused caption
    caption_topic = f"Product launch: {product_name}"
    if launch_context:
        caption_topic = f"{launch_context}: {product_name}"

    key_message = product_name
    if product_features:
        features_list = [f.strip() for f in product_features.split(",")][:3]
        key_message = f"{product_name} - {', '.join(features_list)}"

    caption_result = write_caption(
        topic=caption_topic,
        brand_voice="enthusiastic and product-focused",
        target_audience=target_audience or "shoppers and brand enthusiasts",
        key_message=key_message,
        occasion=launch_context,
        tone="engaging",
        include_cta=True,
        emoji_level="moderate",
        company_overview=f"{brand_name} - {industry}" if brand_name else "",
        brand_name=brand_name,
        image_description=f"Product showcase of {product_name}"
    )

    # Add price point to caption if provided
    caption = caption_result.get("caption", f"Introducing {product_name}! {cta_text}")
    if price_point and caption_result.get("status") == "success":
        # Insert price before the CTA
        if cta_text.lower() in caption.lower():
            caption = caption.replace(cta_text, f"{price_point} | {cta_text}")

    # Generate product-focused hashtags
    hashtag_result = generate_hashtags(
        topic=f"{product_name} {industry} product launch",
        niche=industry,
        brand_name=brand_name,
        trending_context=launch_context or "new product",
        max_hashtags=15
    )

    # Combine results
    result = {
        "status": "success",
        "image": image_result,
        "image_path": image_result.get("image_path"),
        "image_url": image_result.get("url"),
        "product_name": product_name,
        "product_features": product_features,
        "showcase_style": showcase_style,
        "type": "product_showcase"
    }

    # Add caption
    if caption_result.get("status") == "success":
        result["caption"] = caption
        result["caption_length"] = len(caption)
    else:
        result["caption"] = f"✨ Introducing {product_name}!\n\n{product_features}\n\n{cta_text}"
        result["caption_error"] = caption_result.get("message")

    # Add hashtags
    if hashtag_result.get("status") == "success":
        result["hashtags"] = hashtag_result.get("hashtags")
        result["hashtag_string"] = hashtag_result.get("hashtag_string")
    else:
        result["hashtags"] = [f"#{brand_name.replace(' ', '')}" if brand_name else "#newproduct", "#shopnow"]
        result["hashtag_string"] = " ".join(result["hashtags"])
        result["hashtag_error"] = hashtag_result.get("message")

    # Create full post text
    full_post = result["caption"]
    if result.get("hashtag_string"):
        full_post += f"\n\n.\n.\n.\n\n{result['hashtag_string']}"
    result["full_post"] = full_post

    print(f"   ✅ Product showcase generated!")
    print(f"   🛍️ Product: {product_name}")
    print(f"   📷 Image: {result.get('image_path')}")
    print(f"   📝 Caption: {len(result.get('caption', ''))} chars")
    print(f"   #️⃣ Hashtags: {len(result.get('hashtags', []))}")

    return result


def regenerate_post(
    original_image_path: str,
    edit_instruction: str,
    regenerate_caption: bool = False,
    regenerate_hashtags: bool = False,
    original_caption: str = "",
    original_context_json: str = "",
    output_dir: str = "generated"
) -> dict:
    """
    Regenerate/edit an existing post based on feedback.

    This tool handles:
    - Image edits (color changes, element modifications, style adjustments)
    - Caption regeneration with new tone/message
    - Hashtag refresh

    Args:
        original_image_path: Path to the original image to edit
        edit_instruction: What changes to make to the image
        regenerate_caption: Also regenerate the caption
        regenerate_hashtags: Also regenerate hashtags
        original_caption: The original caption (for context)
        original_context_json: JSON string with original context (brand_name, industry, occasion, etc.)
        output_dir: Directory to save edited images

    Returns:
        Dictionary with regenerated content
    """
    import json
    from agent_factory_core.tools._internal.content import improve_caption, generate_hashtags

    print(f"🔄 Regenerating post: {original_image_path}")
    print(f"   Changes: {edit_instruction[:50]}...")

    result = {"status": "success"}

    # Parse context from JSON string
    context = {}
    if original_context_json:
        try:
            context = json.loads(original_context_json)
        except json.JSONDecodeError:
            pass

    # Step 1: Edit the image
    image_result = edit_post_image(
        original_image_path=original_image_path,
        edit_instruction=edit_instruction,
        output_dir=output_dir
    )

    if image_result.get("status") == "success":
        result["image"] = image_result
        result["image_path"] = image_result.get("image_path")
        result["image_url"] = image_result.get("url")
    else:
        result["image_error"] = image_result.get("message")
        result["image_path"] = original_image_path

    # Step 2: Regenerate caption if requested
    if regenerate_caption and original_caption:
        caption_result = improve_caption(
            original_caption=original_caption,
            feedback=edit_instruction,
            preserve_tone=True
        )

        if caption_result.get("status") == "success":
            result["caption"] = caption_result.get("improved_caption")
            result["caption_regenerated"] = True
        else:
            result["caption"] = original_caption
            result["caption_error"] = caption_result.get("message")
    elif original_caption:
        result["caption"] = original_caption

    # Step 3: Regenerate hashtags if requested
    if regenerate_hashtags and context:
        hashtag_result = generate_hashtags(
            topic=context.get("prompt", edit_instruction),
            niche=context.get("industry", ""),
            brand_name=context.get("brand_name", ""),
            trending_context=context.get("occasion", ""),
            max_hashtags=context.get("max_hashtags", 15)
        )

        if hashtag_result.get("status") == "success":
            result["hashtags"] = hashtag_result.get("hashtags")
            result["hashtag_string"] = hashtag_result.get("hashtag_string")
            result["hashtags_regenerated"] = True

    # Create full post if we have both caption and hashtags
    if result.get("caption") and result.get("hashtag_string"):
        result["full_post"] = f"{result['caption']}\n\n.\n.\n.\n\n{result['hashtag_string']}"
    elif result.get("caption"):
        result["full_post"] = result["caption"]

    print(f"   ✅ Regeneration complete!")

    return result


def edit_post_image(
    original_image_path: str,
    edit_instruction: str,
    output_dir: str = "generated"
) -> dict:
    """
    Edit an existing image based on instructions.
    
    Args:
        original_image_path: Path to the original image
        edit_instruction: What changes to make
        output_dir: Directory to save edited images
        
    Returns:
        Dictionary with new image path and edit details
    """
    print(f"✏️ Editing image: {original_image_path}")
    print(f"   Instruction: {edit_instruction[:50]}...")
    
    try:
        client = _get_client()
        
        if not os.path.exists(original_image_path):
            return {
                "status": "error",
                "message": f"Original image not found: {original_image_path}"
            }
        
        edit_prompt = f"""Edit this image with the following changes:
{edit_instruction}

Keep the overall quality and brand feel while making the requested modifications.
Maintain professional, high-quality output suitable for Instagram."""

        original_image = Image.open(original_image_path)
        model = os.getenv("EDIT_MODEL", os.getenv("IMAGE_MODEL", "gemini-3-pro-image-preview"))

        def make_request():
            return client.models.generate_content(
                model=model,
                contents=[edit_prompt, original_image],
                config=types.GenerateContentConfig(
                    response_modalities=["image", "text"],
                )
            )
        
        response = _retry_with_backoff(make_request)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_id = str(uuid.uuid4())[:8]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"edited_{timestamp}_{image_id}.png"
                image_path = output_path / filename
                
                with open(image_path, "wb") as f:
                    f.write(part.inline_data.data)
                
                print(f"   ✅ Edited image saved: {image_path}")
                
                return {
                    "status": "success",
                    "image_path": str(image_path),
                    "filename": filename,
                    "url": f"/generated/{filename}",
                    "edit_instruction": edit_instruction,
                    "original_image": original_image_path
                }
        
        return {
            "status": "error",
            "message": "Could not generate edited image. Try different edit instructions."
        }
            
    except Exception as e:
        return _format_error(e, "Try simpler edit instructions.")


def animate_image(
    image_path: str,
    motion_prompt: str,
    duration_seconds: int = 8,
    output_dir: str = "generated",
    aspect_ratio: str = "9:16",
    with_audio: bool = True,
    negative_prompt: str = ""
) -> dict:
    """
    Animate a static image to create a short video using Veo 3.1.

    Uses Google's Veo 3.1 model for high-quality image-to-video generation
    with optional audio generation.

    Args:
        image_path: Path to the static image to animate (can be web URL like /generated/file.png or full filesystem path)
        motion_prompt: Description of desired motion and scene
        duration_seconds: Length of video (5-8 seconds recommended)
        output_dir: Directory to save the generated video
        aspect_ratio: Video aspect ratio ("16:9", "9:16" for vertical)
        with_audio: Generate audio with the video (Veo 3.1 feature)
        negative_prompt: What to avoid in the video

    Returns:
        Dictionary with video path or error information
    """
    print(f"🎬 Animating image with Veo 3.1: {image_path}")
    print(f"   Motion: {motion_prompt[:50]}...")
    print(f"   Duration: {duration_seconds}s, Aspect: {aspect_ratio}, Audio: {with_audio}")

    try:
        client = _get_client()

        # Convert web URL path to filesystem path if needed
        resolved_path = image_path
        if image_path.startswith("/generated/"):
            resolved_path = str(Path.cwd() / image_path.lstrip("/"))
            print(f"   📁 Resolved path: {resolved_path}")
        elif not os.path.isabs(image_path):
            resolved_path = str(Path.cwd() / image_path)
            print(f"   📁 Resolved relative path: {resolved_path}")

        if not os.path.exists(resolved_path):
            return {
                "status": "error",
                "message": f"Image not found: {image_path} (resolved: {resolved_path})"
            }

        # Build the animation prompt
        full_prompt = f"""Create a smooth, professional video animation from this image.

MOTION DESCRIPTION: {motion_prompt}

GUIDELINES:
- Smooth, cinematic motion
- Keep brand elements (logo, text) stable and readable
- Professional quality suitable for Instagram Reels/Stories
"""
        if negative_prompt:
            full_prompt += f"\nAVOID: {negative_prompt}"

        # Use Veo 3.1 model from env or default
        video_model = os.getenv("VIDEO_MODEL", "veo-3.1-generate-preview")
        print(f"   Model: {video_model}")

        # Clamp duration to valid range (5-8 seconds)
        duration_seconds = max(5, min(8, duration_seconds))

        try:
            print("   📤 Starting video generation with Veo 3.1...")

            # Step 1: Load the source image and create an Image object for the API
            # Following reference: image=image.parts[0].as_image()
            # We use PIL to load, then upload via client to get a proper image object
            source_image = Image.open(resolved_path)
            if source_image.mode in ('RGBA', 'LA', 'P'):
                source_image = source_image.convert('RGB')

            # Save to bytes for upload
            import io
            img_byte_arr = io.BytesIO()
            source_image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()

            # Create image object the way the API expects it
            source_image_obj = types.Image(
                image_bytes=img_bytes,
                mime_type="image/jpeg"
            )

            # Step 2: Configure video generation
            video_config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                number_of_videos=1,
                duration_seconds=duration_seconds,
            )

            # Step 3: Generate video with image input
            operation = client.models.generate_videos(
                model=video_model,
                prompt=full_prompt,
                image=source_image_obj,
                config=video_config,
            )

            # Step 4: Poll for completion
            max_wait_time = 300  # 5 minutes max
            poll_interval = 10

            print("   ⏳ Waiting for video generation...")
            while not operation.done:
                time.sleep(poll_interval)
                operation = client.operations.get(operation)
                max_wait_time -= poll_interval
                print(f"   ⏳ Processing... (waiting...)")
                if max_wait_time <= 0:
                    return {
                        "status": "timeout",
                        "message": "Video generation is taking longer than expected. Please try again later.",
                        "source_image": image_path,
                        "motion_prompt": motion_prompt
                    }

            # Step 5: Get result
            result = operation.result
            if not result:
                return {
                    "status": "error",
                    "message": "Video generation completed but no result was returned.",
                    "source_image": image_path,
                    "motion_prompt": motion_prompt
                }

            generated_videos = result.generated_videos
            if not generated_videos:
                return {
                    "status": "error",
                    "message": "Video generation completed but no videos were generated.",
                    "source_image": image_path,
                    "motion_prompt": motion_prompt
                }

            # Step 6: Download and save the video
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            video = generated_videos[0]
            video_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"animated_{timestamp}_{video_id}.mp4"
            video_path = output_path / filename

            print(f"   📥 Downloading video: {video.video.uri}")
            client.files.download(file=video.video)
            video.video.save(str(video_path))
            print(f"   ✅ Video saved: {video_path}")

            return {
                "status": "success",
                "video_path": str(video_path),
                "filename": filename,
                "url": f"/generated/{filename}",
                "motion_prompt": motion_prompt,
                "duration_seconds": duration_seconds,
                "source_image": image_path,
                "aspect_ratio": aspect_ratio,
                "with_audio": with_audio,
                "model": video_model,
                "type": "video"
            }

        except Exception as model_error:
            error_str = str(model_error).lower()
            print(f"   ⚠️ Video generation error: {model_error}")

            if "not found" in error_str or "invalid" in error_str or "unavailable" in error_str or "not supported" in error_str or "permission" in error_str:
                return {
                    "status": "model_unavailable",
                    "message": f"Veo 3.1 video generation error: {str(model_error)[:200]}",
                    "source_image": image_path,
                    "motion_prompt": motion_prompt,
                }
            raise

    except Exception as e:
        return _format_error(e, "Video generation may not be available in your region.")


def generate_video_from_text(
    prompt: str,
    duration_seconds: int = 8,
    aspect_ratio: str = "9:16",
    output_dir: str = "generated",
    with_audio: bool = True,
    negative_prompt: str = ""
) -> dict:
    """
    Generate a video directly from text prompt using Veo 3.1.

    Creates a new video from scratch based on the text description.

    Args:
        prompt: Detailed description of the video to generate
        duration_seconds: Length of video (5-8 seconds)
        aspect_ratio: Video aspect ratio ("16:9", "9:16")
        output_dir: Directory to save the generated video
        with_audio: Generate audio with the video
        negative_prompt: What to avoid in the video

    Returns:
        Dictionary with video path or error information
    """
    print(f"🎬 Generating video from text with Veo 3.1")
    print(f"   Prompt: {prompt[:50]}...")
    print(f"   Duration: {duration_seconds}s, Aspect: {aspect_ratio}, Audio: {with_audio}")

    try:
        client = _get_client()

        video_model = os.getenv("VIDEO_MODEL", "veo-3.1-generate-preview")
        print(f"   Model: {video_model}")

        # Clamp duration to valid range (5-8 seconds)
        duration_seconds = max(5, min(8, duration_seconds))

        try:
            print("   📤 Starting video generation with Veo 3.1...")

            # Configure video generation
            video_config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                number_of_videos=1,
                duration_seconds=duration_seconds,
                person_generation="ALLOW_ADULT",
            )

            # Generate video from text prompt
            operation = client.models.generate_videos(
                model=video_model,
                prompt=prompt,
                config=video_config,
            )

            # Poll for completion
            max_wait_time = 300  # 5 minutes max

            print("   ⏳ Waiting for video generation...")
            while not operation.done:
                time.sleep(10)
                operation = client.operations.get(operation)
                max_wait_time -= 10
                print(f"   ⏳ Processing... (waiting...)")
                if max_wait_time <= 0:
                    return {
                        "status": "timeout",
                        "message": "Video generation is taking longer than expected.",
                        "prompt": prompt
                    }

            # Get result
            result = operation.result
            if not result:
                return {
                    "status": "error",
                    "message": "Video generation completed but no result was returned.",
                    "prompt": prompt
                }

            generated_videos = result.generated_videos
            if not generated_videos:
                return {
                    "status": "error",
                    "message": "Video generation completed but no videos were generated.",
                    "prompt": prompt
                }

            # Download and save the video
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            video = generated_videos[0]
            video_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"video_{timestamp}_{video_id}.mp4"
            video_path = output_path / filename

            print(f"   📥 Downloading video: {video.video.uri}")
            client.files.download(file=video.video)
            video.video.save(str(video_path))
            print(f"   ✅ Video saved: {video_path}")

            return {
                "status": "success",
                "video_path": str(video_path),
                "filename": filename,
                "url": f"/generated/{filename}",
                "prompt": prompt,
                "duration_seconds": duration_seconds,
                "aspect_ratio": aspect_ratio,
                "with_audio": with_audio,
                "model": video_model,
                "type": "video"
            }

        except Exception as model_error:
            error_str = str(model_error).lower()
            print(f"   ⚠️ Video generation error: {model_error}")

            if "not found" in error_str or "invalid" in error_str or "unavailable" in error_str:
                return {
                    "status": "model_unavailable",
                    "message": f"Veo 3.1 video generation error: {str(model_error)[:200]}",
                    "prompt": prompt,
                }
            raise

    except Exception as e:
        return _format_error(e, "Video generation may not be available in your region.")
