"""
Web Scraping Tools - Extract brand/company information from any URL.

Supports:
- Company websites
- Instagram profiles
- LinkedIn company pages
- Any web page with brand information
"""

import re
import httpx
from typing import Optional
from urllib.parse import urlparse


def scrape_brand_from_url(url: str) -> dict:
    """
    Scrape brand/company information from any URL.
    
    Supports:
    - Company websites (extracts about, colors, logo)
    - Instagram profiles
    - LinkedIn pages
    - Generic web pages
    
    Args:
        url: Any web URL to scrape for brand information
        
    Returns:
        Dictionary containing extracted brand information
    """
    if not url or not url.strip():
        return {
            "status": "error",
            "message": "No URL provided"
        }
    
    # Normalize URL
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    
    # Route to appropriate handler
    if 'instagram.com' in domain or 'instagr.am' in domain:
        return _scrape_instagram(url)
    elif 'linkedin.com' in domain:
        return _scrape_linkedin(url)
    else:
        return _scrape_website(url)


def _scrape_instagram(url: str) -> dict:
    """Extract brand info from Instagram profile."""
    # Extract username
    match = re.search(r'instagram\.com/([^/?\s]+)', url)
    username = match.group(1) if match else url.split('/')[-1]
    username = username.strip('/')
    
    return {
        "status": "success",
        "source": "instagram",
        "url": url,
        "brand_info": {
            "name": username.replace('_', ' ').replace('.', ' ').title(),
            "handle": f"@{username}",
            "platform": "Instagram",
            "profile_url": f"https://instagram.com/{username}"
        },
        "style_hints": {
            "platform_style": "Visual-first, square/portrait images",
            "recommended_tone": "Casual, authentic, engaging",
            "content_types": ["Reels", "Carousels", "Stories", "Static Posts"],
            "best_practices": [
                "Use high-quality visuals",
                "Engage in first hour",
                "Mix Reels and static content",
                "Use 10-15 relevant hashtags"
            ]
        },
        "usage_note": "For detailed Instagram analytics, integrate with Instagram Graph API"
    }


def _scrape_linkedin(url: str) -> dict:
    """Extract brand info from LinkedIn company page."""
    # Extract company name from URL
    match = re.search(r'linkedin\.com/company/([^/?\s]+)', url)
    company_slug = match.group(1) if match else 'company'
    company_name = company_slug.replace('-', ' ').replace('_', ' ').title()
    
    return {
        "status": "success",
        "source": "linkedin",
        "url": url,
        "brand_info": {
            "name": company_name,
            "platform": "LinkedIn",
            "profile_url": url
        },
        "style_hints": {
            "platform_style": "Professional, B2B focused",
            "recommended_tone": "Professional, thought leadership",
            "content_types": ["Articles", "Industry insights", "Company updates", "Job posts"],
            "best_practices": [
                "Share industry insights",
                "Use professional imagery",
                "Engage with comments",
                "Post during business hours"
            ]
        },
        "usage_note": "For detailed LinkedIn analytics, use LinkedIn Marketing API"
    }


def _scrape_website(url: str) -> dict:
    """
    Extract brand info from a company website.
    
    Attempts to fetch and parse the page for brand elements.
    """
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    brand_name = domain.split('.')[0].replace('-', ' ').replace('_', ' ').title()
    
    extracted_data = {
        "title": None,
        "description": None,
        "colors": [],
        "keywords": [],
        "images": []
    }
    
    try:
        # Try to fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ContentStudioBot/1.0)'
        }
        response = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
        
        if response.status_code == 200:
            html = response.text
            
            # Extract title
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
            if title_match:
                extracted_data["title"] = title_match.group(1).strip()
                # Use title as brand name if it's cleaner
                title_name = extracted_data["title"].split('|')[0].split('-')[0].strip()
                if title_name and len(title_name) < 50:
                    brand_name = title_name
            
            # Extract meta description
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if not desc_match:
                desc_match = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']description["\']', html, re.IGNORECASE)
            if desc_match:
                extracted_data["description"] = desc_match.group(1).strip()
            
            # Extract keywords
            kw_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if kw_match:
                extracted_data["keywords"] = [k.strip() for k in kw_match.group(1).split(',')][:10]
            
            # Extract colors from CSS (simplified)
            color_matches = re.findall(r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b', html)
            if color_matches:
                # Get unique colors, prioritize 6-char hex
                seen = set()
                for c in color_matches:
                    c = c.upper()
                    if len(c) == 6 and c not in seen:
                        seen.add(c)
                        extracted_data["colors"].append(f"#{c}")
                        if len(extracted_data["colors"]) >= 5:
                            break
            
            # Extract og:image
            og_image = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if og_image:
                extracted_data["images"].append(og_image.group(1))
                
    except Exception as e:
        # If scraping fails, return basic info from URL
        pass
    
    return {
        "status": "success",
        "source": "website",
        "url": url,
        "brand_info": {
            "name": brand_name,
            "domain": domain,
            "title": extracted_data["title"],
            "description": extracted_data["description"],
            "extracted_colors": extracted_data["colors"] if extracted_data["colors"] else None,
            "keywords": extracted_data["keywords"] if extracted_data["keywords"] else None,
            "logo_hint": extracted_data["images"][0] if extracted_data["images"] else None
        },
        "style_hints": {
            "recommended_tone": "Match your brand voice",
            "content_types": ["Product posts", "Behind-the-scenes", "Customer stories", "Tips & tutorials"],
            "best_practices": [
                "Maintain consistent brand colors",
                "Use logo watermark on images",
                "Reflect brand personality in captions",
                "Create content for your target audience"
            ]
        },
        "usage_note": "Basic extraction from website. Provide additional brand details for best results."
    }


def get_brand_context_from_url(url: str) -> str:
    """
    Get a formatted brand context string from URL for use in prompts.
    
    Args:
        url: Web URL to analyze
        
    Returns:
        Formatted string with brand context
    """
    data = scrape_brand_from_url(url)
    
    if data.get("status") != "success":
        return f"Could not extract brand info from {url}"
    
    brand = data.get("brand_info", {})
    style = data.get("style_hints", {})
    
    context = f"""
**Brand Reference from {data.get('source', 'web')}:**
- Name: {brand.get('name', 'Unknown')}
- Source: {data.get('url', url)}
"""
    
    if brand.get('description'):
        context += f"- About: {brand.get('description')[:200]}...\n"
    
    if brand.get('extracted_colors'):
        context += f"- Colors Found: {', '.join(brand.get('extracted_colors', []))}\n"
    
    if brand.get('keywords'):
        context += f"- Keywords: {', '.join(brand.get('keywords', [])[:5])}\n"
    
    context += f"""
**Style Guidance:**
- Tone: {style.get('recommended_tone', 'professional')}
- Content Types: {', '.join(style.get('content_types', [])[:3])}
"""
    
    return context.strip()
