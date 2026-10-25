"""Weather command."""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.queries import get_settings, list_cities
from services.weather import WEATHER_CODES

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("weather"))
async def weather(message: Message, db, weather_service, llm_service):
    settings = await get_settings(db)
    cities = await list_cities(db)
    city = next((item for item in cities if item["id"] == settings["active_city_id"]), None)
    if not city:
        await message.answer("Активный город не выбран. Откройте /settings и добавьте город.")
        return
    try:
        current = await weather_service.current(city["latitude"], city["longitude"])
        condition = WEATHER_CODES.get(current.get("weathercode"), "неизвестные условия")
        advice = await llm_service.clothing_advice(current["temperature"], condition, settings["language"])
        await message.answer(f"🌤 {city['name']}: {current['temperature']} °C, {condition}.\n{advice}")
    except Exception:
        logger.exception("EVENT: weather_failed")
        await message.answer("⚠️ Не удалось получить погоду. Попробуйте позже.")
