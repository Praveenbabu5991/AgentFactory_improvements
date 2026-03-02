"""
Calendar and Event Planning Tools.

Provides festival/event information and content calendar suggestions.
Includes dynamic date calculations for variable holidays.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Optional
import time

from google import genai
from dotenv import load_dotenv

load_dotenv()


def _get_client():
    """Get Gemini client with validation."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("API key not configured. Please set GOOGLE_API_KEY.")
    return genai.Client(api_key=api_key)


def _retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Execute function with exponential backoff retry."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
    raise last_error


def _format_error(error: Exception) -> dict:
    """Format error into user-friendly response."""
    return {
        "status": "error", 
        "message": "Could not retrieve calendar information. Please try again.",
        "technical_details": str(error)
    }


def _get_nth_weekday(year: int, month: int, weekday: int, n: int) -> datetime:
    """
    Get the nth occurrence of a weekday in a month.
    weekday: 0=Monday, 6=Sunday
    n: 1=first, 2=second, etc. -1=last
    """
    if n > 0:
        # First day of month
        first_day = datetime(year, month, 1)
        # Days until first occurrence of weekday
        days_until = (weekday - first_day.weekday()) % 7
        first_occurrence = first_day + timedelta(days=days_until)
        # Add (n-1) weeks
        return first_occurrence + timedelta(weeks=n-1)
    else:
        # Last occurrence - start from last day of month
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        days_since = (last_day.weekday() - weekday) % 7
        return last_day - timedelta(days=days_since)


def _get_easter(year: int) -> datetime:
    """Calculate Easter Sunday for a given year (Western calendar)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime(year, month, day)


def _calculate_variable_dates(year: int) -> dict:
    """Calculate variable holiday dates for a given year."""
    easter = _get_easter(year)
    
    return {
        # US holidays
        "mlk_day": _get_nth_weekday(year, 1, 0, 3),  # 3rd Monday of January
        "presidents_day": _get_nth_weekday(year, 2, 0, 3),  # 3rd Monday of February
        "memorial_day": _get_nth_weekday(year, 5, 0, -1),  # Last Monday of May
        "labor_day": _get_nth_weekday(year, 9, 0, 1),  # 1st Monday of September
        "columbus_day": _get_nth_weekday(year, 10, 0, 2),  # 2nd Monday of October
        "thanksgiving": _get_nth_weekday(year, 11, 3, 4),  # 4th Thursday of November
        
        # Variable religious holidays
        "easter": easter,
        "good_friday": easter - timedelta(days=2),
        "ash_wednesday": easter - timedelta(days=46),
        
        # Mother's/Father's Day
        "mothers_day": _get_nth_weekday(year, 5, 6, 2),  # 2nd Sunday of May
        "fathers_day": _get_nth_weekday(year, 6, 6, 3),  # 3rd Sunday of June
    }


def get_festivals_and_events(
    month: str = "",
    region: str = "global",
    year: Optional[int] = None,
    include_themes: bool = True
) -> dict:
    """
    Get festivals and events for content planning.
    
    Args:
        month: Month name (empty for current month)
        region: Geographic region filter (global, US, India, UK, etc.)
        year: Year for date calculations (defaults to current year)
        include_themes: Include content theme suggestions
        
    Returns:
        Dictionary with events and themes
    """
    if year is None:
        year = datetime.now().year
    
    if not month:
        month = datetime.now().strftime("%B").lower()
    else:
        month = month.lower()
    
    # Map month names to numbers
    month_map = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12
    }
    month_num = month_map.get(month, datetime.now().month)
    
    # Get variable dates for the year
    var_dates = _calculate_variable_dates(year)
    
    # Comprehensive events database with fixed and variable dates
    all_events = {
        1: [  # January
            {"date": "01", "name": "New Year's Day", "type": "holiday", "region": "global", "themes": ["new beginnings", "goals", "fresh start", "resolutions"]},
            {"date": "14", "name": "Makar Sankranti", "type": "festival", "region": "India", "themes": ["harvest", "kites", "celebration", "tradition"]},
            {"date": "26", "name": "Republic Day", "type": "national", "region": "India", "themes": ["patriotism", "pride", "unity", "freedom"]},
            {"date": "26", "name": "Australia Day", "type": "national", "region": "Australia", "themes": ["celebration", "patriotism"]},
        ],
        2: [  # February
            {"date": "02", "name": "Groundhog Day", "type": "observance", "region": "US", "themes": ["winter", "prediction", "fun"]},
            {"date": "14", "name": "Valentine's Day", "type": "observance", "region": "global", "themes": ["love", "relationships", "gifts", "romance"]},
        ],
        3: [  # March
            {"date": "08", "name": "International Women's Day", "type": "awareness", "region": "global", "themes": ["empowerment", "equality", "women", "inspiration"]},
            {"date": "17", "name": "St. Patrick's Day", "type": "observance", "region": "global", "themes": ["luck", "green", "celebration", "Irish"]},
            {"date": "20", "name": "Spring Equinox", "type": "seasonal", "region": "global", "themes": ["spring", "renewal", "nature", "balance"]},
        ],
        4: [  # April
            {"date": "01", "name": "April Fools' Day", "type": "observance", "region": "global", "themes": ["humor", "pranks", "fun"]},
            {"date": "22", "name": "Earth Day", "type": "awareness", "region": "global", "themes": ["environment", "sustainability", "nature", "green"]},
        ],
        5: [  # May
            {"date": "01", "name": "May Day / Labor Day", "type": "holiday", "region": "global", "themes": ["workers", "rights", "spring"]},
            {"date": "05", "name": "Cinco de Mayo", "type": "observance", "region": "US", "themes": ["Mexican culture", "celebration", "food"]},
        ],
        6: [  # June
            {"date": "21", "name": "International Yoga Day", "type": "awareness", "region": "global", "themes": ["wellness", "health", "mindfulness", "fitness"]},
            {"date": "21", "name": "Summer Solstice", "type": "seasonal", "region": "global", "themes": ["summer", "longest day", "sun"]},
        ],
        7: [  # July
            {"date": "04", "name": "Independence Day", "type": "national", "region": "US", "themes": ["freedom", "patriotism", "celebration", "fireworks"]},
            {"date": "14", "name": "Bastille Day", "type": "national", "region": "France", "themes": ["freedom", "celebration"]},
        ],
        8: [  # August
            {"date": "15", "name": "Independence Day", "type": "national", "region": "India", "themes": ["freedom", "patriotism", "pride", "tricolor"]},
        ],
        9: [  # September
            {"date": "05", "name": "Teachers' Day", "type": "observance", "region": "India", "themes": ["education", "gratitude", "teachers", "learning"]},
            {"date": "21", "name": "International Day of Peace", "type": "awareness", "region": "global", "themes": ["peace", "unity", "harmony"]},
        ],
        10: [  # October
            {"date": "02", "name": "Gandhi Jayanti", "type": "national", "region": "India", "themes": ["peace", "non-violence", "inspiration"]},
            {"date": "31", "name": "Halloween", "type": "observance", "region": "global", "themes": ["costumes", "fun", "spooky", "creativity"]},
        ],
        11: [  # November
            {"date": "11", "name": "Veterans Day", "type": "national", "region": "US", "themes": ["honor", "gratitude", "service"]},
        ],
        12: [  # December
            {"date": "25", "name": "Christmas", "type": "holiday", "region": "global", "themes": ["gifts", "joy", "celebration", "family", "giving"]},
            {"date": "26", "name": "Boxing Day", "type": "holiday", "region": "UK", "themes": ["shopping", "sales", "giving"]},
            {"date": "31", "name": "New Year's Eve", "type": "holiday", "region": "global", "themes": ["celebration", "reflection", "party", "countdown"]},
        ]
    }
    
    # Add variable holidays to appropriate months
    if var_dates["mothers_day"].month == month_num:
        all_events.setdefault(month_num, []).append({
            "date": var_dates["mothers_day"].strftime("%d"),
            "name": "Mother's Day",
            "type": "observance",
            "region": "global",
            "themes": ["mothers", "gratitude", "family", "love"]
        })
    
    if var_dates["fathers_day"].month == month_num:
        all_events.setdefault(month_num, []).append({
            "date": var_dates["fathers_day"].strftime("%d"),
            "name": "Father's Day",
            "type": "observance",
            "region": "global",
            "themes": ["fathers", "gratitude", "family", "appreciation"]
        })
    
    if var_dates["thanksgiving"].month == month_num:
        all_events.setdefault(month_num, []).append({
            "date": var_dates["thanksgiving"].strftime("%d"),
            "name": "Thanksgiving",
            "type": "holiday",
            "region": "US",
            "themes": ["gratitude", "family", "feast", "thankfulness"]
        })
        # Black Friday is day after Thanksgiving
        black_friday = var_dates["thanksgiving"] + timedelta(days=1)
        if black_friday.month == month_num:
            all_events[month_num].append({
                "date": black_friday.strftime("%d"),
                "name": "Black Friday",
                "type": "commercial",
                "region": "global",
                "themes": ["sales", "shopping", "deals", "discounts"]
            })
    
    if var_dates["easter"].month == month_num:
        all_events.setdefault(month_num, []).append({
            "date": var_dates["easter"].strftime("%d"),
            "name": "Easter",
            "type": "holiday",
            "region": "global",
            "themes": ["spring", "celebration", "family", "renewal"]
        })
    
    # Get events for the requested month
    events = all_events.get(month_num, [])
    
    # Filter by region
    if region != "global":
        events = [e for e in events if e.get("region", "global") in [region, "global"]]
    
    # Sort by date
    events.sort(key=lambda x: int(x["date"]))
    
    result = {
        "status": "success",
        "month": month.title(),
        "year": year,
        "region": region,
        "events": events,
        "count": len(events)
    }
    
    if include_themes and events:
        all_themes = []
        for event in events:
            all_themes.extend(event.get("themes", []))
        result["content_themes"] = list(set(all_themes))
    
    return result


def get_upcoming_events(
    days_ahead: int = 30,
    region: str = "global"
) -> dict:
    """
    Get upcoming events within a specified number of days.
    
    Args:
        days_ahead: Number of days to look ahead
        region: Geographic region filter
        
    Returns:
        Dictionary with upcoming events
    """
    try:
        client = _get_client()
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)
        
        prompt = f"""List important events, holidays, and observances from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}.

Region Focus: {region}

For each event, provide:
- Date (specific)
- Event Name
- Type (holiday/festival/awareness day/commercial)
- Content Opportunity (how brands can leverage it)

Include: Major holidays, awareness days, cultural events, seasonal themes, and commercial events.
Format as a clean, structured list."""

        def make_request():
            response = client.models.generate_content(
                model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
                contents=prompt
            )
            return response.text.strip()
        
        result = _retry_with_backoff(make_request)
        
        return {
            "status": "success",
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "region": region,
            "events": result
        }
    except Exception as e:
        return _format_error(e)


def get_content_calendar_suggestions(
    brand_name: str,
    niche: str = "general",
    tone: str = "professional",
    target_audience: str = "general audience",
    planning_period: str = "month",
    posts_per_week: int = 5
) -> dict:
    """
    Generate a content calendar with post suggestions.
    
    Args:
        brand_name: Name of the brand
        niche: Industry or niche
        tone: Brand tone of voice
        target_audience: Target audience description
        planning_period: week, month, or quarter
        posts_per_week: Target number of posts per week
        
    Returns:
        Dictionary with content calendar
    """
    try:
        client = _get_client()
        
        days_map = {"week": 7, "month": 30, "quarter": 90}
        days = days_map.get(planning_period, 30)
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        
        # Get events for context
        events_data = get_festivals_and_events(start_date.strftime("%B").lower())
        events_str = ", ".join([e["name"] for e in events_data.get("events", [])]) if events_data.get("events") else "No major events"
        
        prompt = f"""Create a practical Instagram content calendar for {brand_name}.

**Brand Details:**
- Industry/Niche: {niche}
- Tone: {tone}
- Target Audience: {target_audience}

**Planning Period:** {start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}
**Target:** {posts_per_week} posts per week

**Relevant Events This Period:** {events_str}

**Create a calendar with:**
1. Specific posting dates
2. Content type (Feed post, Reel idea, Story, Carousel)
3. Topic/Theme for each post
4. Brief caption hook idea
5. Recommended hashtag category

**Content Mix:**
- Educational (how-to, tips)
- Behind-the-scenes
- Engagement posts (questions, polls)
- Product/service highlights
- Event-based content

Format as a clean weekly calendar."""

        def make_request():
            response = client.models.generate_content(
                model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
                contents=prompt
            )
            return response.text.strip()
        
        result = _retry_with_backoff(make_request)
        
        return {
            "status": "success",
            "brand": brand_name,
            "period": planning_period,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "posts_per_week": posts_per_week,
            "calendar": result
        }
    except Exception as e:
        return _format_error(e)


def suggest_best_posting_times(
    niche: str,
    target_audience: str = "",
    timezone: str = "IST"
) -> dict:
    """
    Suggest optimal posting times for Instagram.
    
    Args:
        niche: Industry/niche
        target_audience: Target audience description
        timezone: Timezone for recommendations
        
    Returns:
        Dictionary with posting time recommendations
    """
    try:
        client = _get_client()
        
        prompt = f"""Recommend optimal Instagram posting times for:

**Niche:** {niche}
**Target Audience:** {target_audience or "General audience"}
**Timezone:** {timezone}

Provide:
1. Best days of the week to post
2. Optimal times for each recommended day
3. Times to avoid
4. Brief reasoning
5. Testing tips

Base on typical social media engagement patterns."""

        def make_request():
            response = client.models.generate_content(
                model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
                contents=prompt
            )
            return response.text.strip()
        
        result = _retry_with_backoff(make_request)
        
        return {
            "status": "success",
            "niche": niche,
            "timezone": timezone,
            "recommendations": result
        }
    except Exception as e:
        return _format_error(e)
