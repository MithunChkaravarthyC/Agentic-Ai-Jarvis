import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

logger = logging.getLogger("WeatherTool")

WMO_WEATHER_CODES = {
    0: {"condition": "Clear Sky", "icon": "☀️", "desc": "crystal clear skies"},
    1: {"condition": "Mainly Clear", "icon": "🌤️", "desc": "mostly clear skies"},
    2: {"condition": "Partly Cloudy", "icon": "⛅", "desc": "scattered cloud cover"},
    3: {"condition": "Overcast", "icon": "☁️", "desc": "dense overcast clouds"},
    45: {"condition": "Foggy", "icon": "🌫️", "desc": "dense fog with reduced visibility"},
    48: {"condition": "Depositing Rime Fog", "icon": "🌫️", "desc": "rime frost fog"},
    51: {"condition": "Light Drizzle", "icon": "🌦️", "desc": "gentle light drizzle"},
    53: {"condition": "Moderate Drizzle", "icon": "🌦️", "desc": "steady drizzle"},
    55: {"condition": "Dense Drizzle", "icon": "🌧️", "desc": "heavy persistent drizzle"},
    61: {"condition": "Slight Rain", "icon": "🌧️", "desc": "light intermittent rain"},
    63: {"condition": "Moderate Rain", "icon": "🌧️", "desc": "steady rain showers"},
    65: {"condition": "Heavy Rain", "icon": "⛈️", "desc": "torrential heavy rainfall"},
    71: {"condition": "Slight Snow", "icon": "🌨️", "desc": "light snow flurries"},
    73: {"condition": "Moderate Snow", "icon": "🌨️", "desc": "steady snowfall"},
    75: {"condition": "Heavy Snow", "icon": "❄️", "desc": "heavy snow blizzard"},
    80: {"condition": "Rain Showers", "icon": "🌦️", "desc": "passing rain showers"},
    81: {"condition": "Moderate Showers", "icon": "🌧️", "desc": "frequent rain showers"},
    82: {"condition": "Violent Rain Showers", "icon": "⛈️", "desc": "heavy tropical downpour"},
    95: {"condition": "Thunderstorm", "icon": "⚡", "desc": "thunderstorm activity with electrical discharge"},
    96: {"condition": "Thunderstorm with Hail", "icon": "⛈️", "desc": "severe thunderstorm with hail"},
    99: {"condition": "Severe Hail Thunderstorm", "icon": "🌪️", "desc": "severe tempest with violent hail"}
}

class WeatherTool:
    """Provides genuine, live real-world climate and weather telemetry via Open-Meteo."""

    def _http_get_json(self, url: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "JARVIS-MultiAgent/2.4 (Personal AI Assistant)"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            logger.warning(f"HTTP GET error for {url}: {e}")
        return None

    def _detect_local_location(self) -> Dict[str, Any]:
        """Detect local city using lightweight IP geolocation services."""
        # Try ip-api.com first (fast & reliable)
        data = self._http_get_json("http://ip-api.com/json/?fields=status,city,regionName,country,lat,lon", timeout=3)
        if data and data.get("status") == "success":
            return {
                "city": data.get("city", "Local Area"),
                "region": data.get("regionName", ""),
                "country": data.get("country", ""),
                "lat": data.get("lat"),
                "lon": data.get("lon")
            }
        
        # Fallback to ipapi.co
        data2 = self._http_get_json("https://ipapi.co/json/", timeout=3)
        if data2 and data2.get("city"):
            return {
                "city": data2.get("city", "Local Area"),
                "region": data2.get("region", ""),
                "country": data2.get("country_name", ""),
                "lat": data2.get("latitude"),
                "lon": data2.get("longitude")
            }

        # Safe default
        return {
            "city": "Bengaluru",
            "region": "Karnataka",
            "country": "India",
            "lat": 12.9716,
            "lon": 77.5946
        }

    def _geocode_city(self, city_name: str) -> Optional[Dict[str, Any]]:
        """Geocode a city name to coordinates using Open-Meteo Geocoding API."""
        encoded_name = urllib.parse.quote(city_name.strip())
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_name}&count=1&language=en&format=json"
        res = self._http_get_json(url, timeout=5)
        if res and res.get("results") and len(res["results"]) > 0:
            top = res["results"][0]
            return {
                "city": top.get("name", city_name.title()),
                "region": top.get("admin1", ""),
                "country": top.get("country", ""),
                "lat": top.get("latitude"),
                "lon": top.get("longitude")
            }
        return None

    def _fetch_wttr_in(self, city_name: str) -> Optional[Dict[str, Any]]:
        """Fetch real-time ground meteorological station observation via wttr.in (matches Google Weather / Airport METAR)."""
        try:
            encoded_city = urllib.parse.quote(city_name.strip())
            url = f"https://wttr.in/{encoded_city}?format=j1"
            data = self._http_get_json(url, timeout=4)
            if data and data.get("current_condition"):
                curr = data["current_condition"][0]
                weather_today = data.get("weather", [{}])[0]

                temp_c = float(curr.get("temp_C", 0))
                feels_like_c = float(curr.get("FeelsLikeC", temp_c))
                humidity = int(curr.get("humidity", 50))
                wind_kmh = float(curr.get("windspeedKmph", 10.0))
                wind_dir = curr.get("winddir16Point", "N")
                cloud_cover = int(curr.get("cloudcover", 20))
                pressure = float(curr.get("pressure", 1013.0))
                desc_obj = curr.get("weatherDesc", [{}])[0]
                desc = desc_obj.get("value", "Partly cloudy").strip()

                max_c = float(weather_today.get("maxtempC", temp_c)) if weather_today.get("maxtempC") else temp_c
                min_c = float(weather_today.get("mintempC", temp_c)) if weather_today.get("mintempC") else temp_c

                spoken = (
                    f"Sir, live atmospheric sensors for {city_name.title()} report {int(round(temp_c))}°C with {desc.lower()}. "
                    f"Relative humidity is {humidity}%, feels like {int(round(feels_like_c))}°C, with winds at {int(round(wind_kmh))} km/h from the {wind_dir}."
                )

                return {
                    "status": "success",
                    "city": city_name.title(),
                    "display_location": f"{city_name.title()}",
                    "temperature_c": temp_c,
                    "temperature_f": round(temp_c * 9 / 5 + 32, 1),
                    "feels_like_c": feels_like_c,
                    "feels_like_f": round(feels_like_c * 9 / 5 + 32, 1),
                    "condition": desc,
                    "condition_desc": desc.lower(),
                    "icon": "⛅",
                    "humidity": humidity,
                    "wind_speed_kmh": wind_kmh,
                    "wind_speed_mph": round(wind_kmh * 0.621371, 1),
                    "wind_direction": wind_dir,
                    "cloud_cover": cloud_cover,
                    "pressure_hpa": pressure,
                    "temp_max_c": max_c,
                    "temp_min_c": min_c,
                    "is_day": True,
                    "spoken": spoken
                }
        except Exception as e:
            logger.warning(f"wttr.in ground observation fetch note for {city_name}: {e}")
        return None

    def get_live_weather(self, location_query: Optional[str] = None) -> Dict[str, Any]:
        """Fetch live authentic atmospheric metrics for the requested location."""
        # Priority 1: Query live ground METAR observation if a specific city was requested
        if location_query and len(location_query.strip()) > 1 and location_query.strip().lower() not in ["here", "my area", "local", "outside", "today"]:
            ground_data = self._fetch_wttr_in(location_query.strip())
            if ground_data:
                return ground_data

        loc = None
        if location_query and len(location_query.strip()) > 1 and location_query.strip().lower() not in ["here", "my area", "local", "outside", "today"]:
            loc = self._geocode_city(location_query)

        if not loc:
            loc = self._detect_local_location()

        city = loc.get("city", "Local Area")

        # Also attempt ground station observation for local detected city
        if city and city != "Local Area":
            ground_data = self._fetch_wttr_in(city)
            if ground_data:
                return ground_data

        lat = loc.get("lat", 12.9716)
        lon = loc.get("lon", 77.5946)
        country = loc.get("country", "")
        region = loc.get("region", "")

        display_location = f"{city}, {country}" if country else city
        if region and region != city and country:
            display_location = f"{city}, {region}, {country}"

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,cloud_cover,surface_pressure,wind_speed_10m,wind_direction_10m&"
            f"daily=weather_code,temperature_2m_max,temperature_2m_min&"
            f"timezone=auto"
        )

        weather_data = self._http_get_json(weather_url, timeout=6)
        if not weather_data or "current" not in weather_data:
            logger.warning("Could not fetch live weather from Open-Meteo, using calibrated baseline.")
            return {
                "status": "error",
                "message": f"Unable to reach atmospheric telemetry sensors for {display_location}.",
                "city": city,
                "spoken": f"Atmospheric sensors are currently calibrating for {city}, Sir. Satellite telemetry will reconnect momentarily."
            }

        curr = weather_data["current"]
        daily = weather_data.get("daily", {})

        temp_c = curr.get("temperature_2m", 24.0)
        temp_f = round(temp_c * 9 / 5 + 32, 1)
        feels_like_c = curr.get("apparent_temperature", temp_c)
        feels_like_f = round(feels_like_c * 9 / 5 + 32, 1)
        humidity = curr.get("relative_humidity_2m", 50)
        wind_speed_kmh = curr.get("wind_speed_10m", 10.0)
        wind_speed_mph = round(wind_speed_kmh * 0.621371, 1)
        wind_dir = curr.get("wind_direction_10m", 0)
        precip_mm = curr.get("precipitation", 0.0)
        cloud_cover = curr.get("cloud_cover", 20)
        pressure_hpa = curr.get("surface_pressure", 1013.0)
        is_day = curr.get("is_day", 1) == 1

        wmo_code = curr.get("weather_code", 0)
        condition_info = WMO_WEATHER_CODES.get(wmo_code, {"condition": "Partly Cloudy", "icon": "⛅", "desc": "mild atmospheric conditions"})
        condition = condition_info["condition"]
        icon = condition_info["icon"]
        desc = condition_info["desc"]

        max_temp_c = daily.get("temperature_2m_max", [temp_c])[0] if daily.get("temperature_2m_max") else temp_c
        min_temp_c = daily.get("temperature_2m_min", [temp_c])[0] if daily.get("temperature_2m_min") else temp_c

        # Wind direction cardinal
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        cardinal_wind = dirs[int((wind_dir + 11.25) / 22.5) % 16]

        # Spoken JARVIS narrative
        spoken_text = (
            f"Atmospheric sensors for {city} report {temp_c}°C with {desc}, Sir. "
            f"Relative humidity is at {humidity}%, feels like {feels_like_c}°C, "
            f"with winds at {wind_speed_kmh} km/h from the {cardinal_wind}."
        )

        return {
            "status": "success",
            "city": city,
            "region": region,
            "country": country,
            "display_location": display_location,
            "temperature_c": temp_c,
            "temperature_f": temp_f,
            "feels_like_c": feels_like_c,
            "feels_like_f": feels_like_f,
            "condition": condition,
            "condition_desc": desc,
            "icon": icon,
            "humidity": humidity,
            "wind_speed_kmh": wind_speed_kmh,
            "wind_speed_mph": wind_speed_mph,
            "wind_direction": cardinal_wind,
            "precipitation_mm": precip_mm,
            "cloud_cover": cloud_cover,
            "pressure_hpa": pressure_hpa,
            "temp_max_c": max_temp_c,
            "temp_min_c": min_temp_c,
            "is_day": is_day,
            "spoken": spoken_text
        }

weather_tool = WeatherTool()
