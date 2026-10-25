"""Start command and ownership checks."""

import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database.queries import get_settings, update_settings

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start(message: Message, db, config):
    settings = await get_settings(db)
    if config.owner_chat_id and message.chat.id != config.owner_chat_id:
        await message.answer("Этот бот настроен для личного использования.")
        return
    if settings["chat_id"] and settings["chat_id"] != message.chat.id:
        await message.answer("Этот бот уже привязан к другому чату.")
        return
    await update_settings(db, chat_id=message.chat.id)
    logger.info("EVENT: start | chat_id=%s", message.chat.id)
    await message.answer("Привет! Я буду присылать утренний погодный совет и сводку GitHub. Настройки: /settings")
