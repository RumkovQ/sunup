"""Settings menu callbacks and text-based city/time input."""

import logging
from typing import Optional
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.queries import add_city, delete_city, get_settings, list_cities, update_settings

router = Router()
logger = logging.getLogger(__name__)


class SettingInput(StatesGroup):
    city = State()
    time = State()
    threshold = State()


def settings_keyboard(cities: list[dict], active_id: Optional[int]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=("✅ " if c["id"] == active_id else "") + c["name"], callback_data=f"city:{c['id']}") for c in cities[i:i+2]] for i in range(0, len(cities), 2)]
    rows += [
        [InlineKeyboardButton(text="➕ Добавить город", callback_data="setting:addcity")],
        [InlineKeyboardButton(text="🗑 Удалить активный город", callback_data="setting:delcity")],
        [InlineKeyboardButton(text="⏰ Время отправки", callback_data="setting:time"), InlineKeyboardButton(text="📬 Порог issues", callback_data="setting:threshold")],
        [InlineKeyboardButton(text="Язык: RU", callback_data="lang:ru"), InlineKeyboardButton(text="EN", callback_data="lang:en"), InlineKeyboardButton(text="RU+EN", callback_data="lang:both")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def render_settings(message: Message, db):
    settings, cities = await get_settings(db), await list_cities(db)
    active = next((c["name"] for c in cities if c["id"] == settings["active_city_id"]), "не выбран")
    await message.answer(
        f"⚙️ Настройки\nГород: {active}\nВремя: {settings['send_time']}\nЯзык: {settings['language']}\nПорог issues: {settings['issue_threshold_days']} дн.",
        reply_markup=settings_keyboard(cities, settings["active_city_id"]),
    )


@router.message(Command("settings"))
async def settings_menu(message: Message, db):
    await render_settings(message, db)


@router.callback_query(F.data.startswith("city:"))
async def choose_city(callback: CallbackQuery, db):
    city_id = int(callback.data.split(":", 1)[1])
    await update_settings(db, active_city_id=city_id)
    await callback.answer("Город выбран")
    if callback.message:
        await render_settings(callback.message, db)


@router.callback_query(F.data == "setting:addcity")
async def ask_city(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingInput.city)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Напишите название города для поиска.")


@router.message(SettingInput.city)
async def add_city_from_text(message: Message, state: FSMContext, db, weather_service):
    try:
        city = await weather_service.geocode(message.text.strip())
        if not city:
            await message.answer("Не нашёл такой город. Попробуйте другое название.")
            return
        city_id = await add_city(db, city["name"], city["latitude"], city["longitude"])
        await update_settings(db, active_city_id=city_id)
        await message.answer(f"Город {city['name']} добавлен и выбран.")
        await render_settings(message, db)
        await state.clear()
    except Exception:
        logger.exception("EVENT: city_add_failed")
        await message.answer("Не удалось найти город через Open-Meteo. Попробуйте позже.")


@router.callback_query(F.data == "setting:delcity")
async def remove_active_city(callback: CallbackQuery, db):
    settings = await get_settings(db)
    if settings["active_city_id"] is not None:
        await delete_city(db, settings["active_city_id"])
    await callback.answer("Активный город удалён")
    if callback.message:
        await render_settings(callback.message, db)


@router.callback_query(F.data.in_({"setting:time", "setting:threshold"}))
async def ask_numeric_setting(callback: CallbackQuery, state: FSMContext):
    time_mode = callback.data == "setting:time"
    await state.set_state(SettingInput.time if time_mode else SettingInput.threshold)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Введите время в формате ЧЧ:ММ." if time_mode else "Введите порог в днях (целое число).")


@router.message(SettingInput.time)
async def set_time(message: Message, state: FSMContext, db, schedule_refresh):
    value = (message.text or "").strip()
    try:
        hour, minute = map(int, value.split(":"))
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError
    except ValueError:
        await message.answer("Нужно время в формате ЧЧ:ММ, например 08:15.")
        return
    await update_settings(db, send_time=f"{hour:02d}:{minute:02d}")
    await schedule_refresh()
    await state.clear()
    await message.answer(f"Время отправки установлено: {hour:02d}:{minute:02d}.")


@router.message(SettingInput.threshold)
async def set_threshold(message: Message, state: FSMContext, db):
    try:
        days = int((message.text or "").strip())
        if not 1 <= days <= 365:
            raise ValueError
    except ValueError:
        await message.answer("Введите целое число от 1 до 365.")
        return
    await update_settings(db, issue_threshold_days=days)
    await state.clear()
    await message.answer(f"Порог установлен: {days} дн.")


@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery, db):
    value = callback.data.split(":", 1)[1]
    await update_settings(db, language=value)
    await callback.answer("Язык обновлён")
    if callback.message:
        await render_settings(callback.message, db)
