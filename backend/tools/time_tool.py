import time
from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("TimeTool")

# Standard major city-to-IANA timezone map
CITY_TIMEZONE_MAP = {
    "london": "Europe/London",
    "uk": "Europe/London",
    "new york": "America/New_York",
    "nyc": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "california": "America/Los_Angeles",
    "san francisco": "America/Los_Angeles",
    "seattle": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "toronto": "America/Toronto",
    "vancouver": "America/Vancouver",
    "tokyo": "Asia/Tokyo",
    "japan": "Asia/Tokyo",
    "seoul": "Asia/Seoul",
    "korea": "Asia/Seoul",
    "beijing": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai",
    "china": "Asia/Shanghai",
    "singapore": "Asia/Singapore",
    "hong kong": "Asia/Hong_Kong",
    "dubai": "Asia/Dubai",
    "uae": "Asia/Dubai",
    "abu dhabi": "Asia/Dubai",
    "doha": "Asia/Qatar",
    "qatar": "Asia/Qatar",
    "riyadh": "Asia/Riyadh",
    "saudi": "Asia/Riyadh",
    "mumbai": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "bangalore": "Asia/Kolkata",
    "bengaluru": "Asia/Kolkata",
    "chennai": "Asia/Kolkata",
    "kolkata": "Asia/Kolkata",
    "hyderabad": "Asia/Kolkata",
    "coimbatore": "Asia/Kolkata",
    "india": "Asia/Kolkata",
    "paris": "Europe/Paris",
    "france": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "germany": "Europe/Berlin",
    "rome": "Europe/Rome",
    "italy": "Europe/Rome",
    "madrid": "Europe/Madrid",
    "spain": "Europe/Madrid",
    "amsterdam": "Europe/Amsterdam",
    "zurich": "Europe/Zurich",
    "switzerland": "Europe/Zurich",
    "sydney": "Australia/Sydney",
    "melbourne": "Australia/Melbourne",
    "australia": "Australia/Sydney",
    "auckland": "Pacific/Auckland",
    "new zealand": "Pacific/Auckland",
    "moscow": "Europe/Moscow",
    "russia": "Europe/Moscow",
    "sao paulo": "America/Sao_Paulo",
    "brazil": "America/Sao_Paulo",
    "buenos aires": "America/Argentina/Buenos_Aires",
    "cairo": "Africa/Cairo",
    "egypt": "Africa/Cairo",
    "johannesburg": "Africa/Johannesburg",
    "south africa": "Africa/Johannesburg"
}

# Reliable fallback UTC offsets (hours) for environments without tzdata
CITY_UTC_OFFSETS = {
    "london": 1,
    "uk": 1,
    "new york": -4,
    "nyc": -4,
    "los angeles": -7,
    "california": -7,
    "san francisco": -7,
    "seattle": -7,
    "chicago": -5,
    "toronto": -4,
    "vancouver": -7,
    "tokyo": 9,
    "japan": 9,
    "seoul": 9,
    "korea": 9,
    "beijing": 8,
    "shanghai": 8,
    "china": 8,
    "singapore": 8,
    "hong kong": 8,
    "dubai": 4,
    "uae": 4,
    "abu dhabi": 4,
    "doha": 3,
    "qatar": 3,
    "riyadh": 3,
    "saudi": 3,
    "mumbai": 5.5,
    "delhi": 5.5,
    "bangalore": 5.5,
    "bengaluru": 5.5,
    "chennai": 5.5,
    "kolkata": 5.5,
    "hyderabad": 5.5,
    "coimbatore": 5.5,
    "india": 5.5,
    "paris": 2,
    "france": 2,
    "berlin": 2,
    "germany": 2,
    "rome": 2,
    "italy": 2,
    "madrid": 2,
    "spain": 2,
    "amsterdam": 2,
    "zurich": 2,
    "switzerland": 2,
    "sydney": 10,
    "melbourne": 10,
    "australia": 10,
    "auckland": 12,
    "new zealand": 12,
    "moscow": 3,
    "russia": 3,
    "sao paulo": -3,
    "brazil": -3,
    "cairo": 3,
    "egypt": 3,
    "johannesburg": 2,
    "south africa": 2
}

class TimeTool:
    """Provides high-precision real system time and global timezone intelligence."""

    def get_current_time(self, city_or_region: Optional[str] = None) -> Dict[str, Any]:
        """Fetch the exact current real-time for local machine or target city."""
        now_local = datetime.now()
        local_tz_name = time.tzname[time.daylight] if time.daylight else time.tzname[0]
        
        target_city = None
        target_tz_str = None
        target_time = now_local

        if city_or_region:
            norm_city = city_or_region.strip().lower()
            # Match directly or substring
            for key, tz_name in CITY_TIMEZONE_MAP.items():
                if key == norm_city or key in norm_city or norm_city in key:
                    target_city = key.title()
                    target_tz_str = tz_name
                    break
            
            if target_city:
                resolved = False
                # 1. Try ZoneInfo
                try:
                    import zoneinfo
                    tz = zoneinfo.ZoneInfo(target_tz_str)
                    target_time = datetime.now(tz)
                    resolved = True
                except Exception:
                    pass

                # 2. Fallback to UTC offset
                if not resolved and norm_city:
                    matched_key = None
                    for key in CITY_UTC_OFFSETS:
                        if key == norm_city or key in norm_city or norm_city in key:
                            matched_key = key
                            break
                    if matched_key:
                        offset_hrs = CITY_UTC_OFFSETS[matched_key]
                        tz_offset = timezone(timedelta(hours=offset_hrs))
                        target_time = datetime.now(timezone.utc).astimezone(tz_offset)
                        resolved = True

                if not resolved:
                    target_city = None

        # Determine greeting
        hour = target_time.hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        # Format time strings
        time_12h = target_time.strftime("%I:%M %p").lstrip("0")
        time_24h = target_time.strftime("%H:%M:%S")
        day_of_week = target_time.strftime("%A")
        full_date = target_time.strftime("%B %d, %Y")
        
        if target_city:
            tz_display = target_tz_str.split("/")[-1].replace("_", " ") if target_tz_str else target_city
            spoken_text = (
                f"{greeting}, Sir. In {target_city}, it is currently {time_12h} on {day_of_week}, {full_date}."
            )
            card_title = f"TIME IN {target_city.upper()}"
        else:
            spoken_text = (
                f"{greeting}, Sir. The current time is {time_12h} on {day_of_week}, {full_date}."
            )
            card_title = "LOCAL SYSTEM TIME"

        return {
            "status": "success",
            "time_12h": time_12h,
            "time_24h": time_24h,
            "day": day_of_week,
            "date": full_date,
            "timestamp": target_time.isoformat(),
            "timezone": target_tz_str or local_tz_name,
            "city": target_city or "Local System",
            "spoken": spoken_text,
            "card_title": card_title
        }

time_tool = TimeTool()
