"""
Image utility functions for Marketing Video Agent Factory.
"""

from colorthief import ColorThief
from typing import Dict


def extract_brand_colors(image_path: str) -> Dict:
    """
    Extract dominant colors from an image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with dominant color and color palette
    """
    try:
        color_thief = ColorThief(image_path)
        # Get dominant color
        dominant = color_thief.get_color(quality=1)
        # Get palette (top 6 colors)
        palette = color_thief.get_palette(color_count=6, quality=1)
        
        # Convert RGB tuples to hex
        def rgb_to_hex(rgb):
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        
        return {
            "dominant": rgb_to_hex(dominant),
            "palette": [rgb_to_hex(c) for c in palette]
        }
    except Exception as e:
        # Return default colors if extraction fails
        return {
            "dominant": "#000000",
            "palette": ["#000000", "#FFFFFF", "#CCCCCC"]
        }
