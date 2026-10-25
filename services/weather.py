"""Open-Meteo forecast and geocoding client."""

import aiohttp
from typing import Optional


class WeatherService:
    BASE = "https://api.open-meteo.com/v1/forecast"
    GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"

    async def current(self, latitude: float, longitude: float) -> dict:
        params = {"latitude": latitude, "longitude": longitude, "current_weather": "true"}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE, params=params, timeout=15) as response:
                response.raise_for_status()
                payload = await response.json()
        current = payload.get("current_weather")
        if not current:
            raise RuntimeError("Open-Meteo returned no current_weather data")
        return current

    async def geocode(self, name: str) -> Optional[dict]:
        params = {"name": name, "count": 1, "language": "ru", "format": "json"}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.GEOCODE, params=params, timeout=15) as response:
                response.raise_for_status()
                payload = await response.json()
        result = (payload.get("results") or [None])[0]
        if not result:
            return None
        return {
            "name": result["name"],
            "latitude": float(result["latitude"]),
            "longitude": float(result["longitude"]),
        }


WEATHER_CODES = {
    0: "ясно", 1: "преимущественно ясно", 2: "переменная облачность", 3: "пасмурно",
    45: "туман", 48: "изморозь", 51: "лёгкая морось", 53: "морось", 55: "сильная морось",
    61: "небольшой дождь", 63: "дождь", 65: "сильный дождь", 71: "небольшой снег",
    73: "снег", 75: "сильный снег", 80: "ливень", 81: "сильный ливень", 82: "очень сильный ливень",
    95: "гроза", 96: "гроза с градом", 99: "сильная гроза с градом",
}
