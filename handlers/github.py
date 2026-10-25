"""GitHub summary, issues and streak commands."""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.exceptions import TelegramNetworkError

from database.queries import get_settings

router = Router()
logger = logging.getLogger(__name__)


async def safe_answer(message: Message, text: str) -> None:
    """Prevent a failed Telegram send from raising a second handler exception."""
    try:
        await message.answer(text)
    except TelegramNetworkError:
        logger.error("EVENT: telegram_reply_failed | check internet connection or TELEGRAM_PROXY")


@router.message(Command("resume"))
async def resume(message: Message, github_service):
    try:
        await message.answer(await github_service.resume())
    except Exception:
        logger.exception("EVENT: github_resume_failed")
        await message.answer("⚠️ Не удалось загрузить GitHub-профиль. Проверьте настройки токена и username.")


@router.message(Command("issues"))
async def issues(message: Message, db, github_service):
    try:
        settings = await get_settings(db)
        items = await github_service.unanswered_issues(settings["issue_threshold_days"])
        if not items:
            await message.answer("✅ Issues без ответа не найдены.")
            return
        lines = [f"📬 Issues без ответа (порог {settings['issue_threshold_days']} дн.):"]
        lines.extend(f"• [{item['repo']}] {item['title']} — {item['age_days']} дн.\n{item['url']}" for item in items[:20])
        await message.answer("\n".join(lines))
    except Exception:
        logger.exception("EVENT: github_issues_failed")
        await message.answer("⚠️ GitHub временно недоступен или не настроен.")


@router.message(Command("streak"))
async def streak(message: Message, github_graphql):
    try:
        count, has_today = await github_graphql.current_streak()
        tail = "Контрибуция сегодня уже есть ✅" if has_today else "Сегодня контрибуций пока нет — streak под угрозой ⚠️"
        reply = f"🔥 Текущий streak: {count} дн.\n{tail}"
    except Exception:
        logger.exception("EVENT: github_streak_failed")
        reply = "⚠️ Не удалось получить streak. Проверьте GitHub token и username."
    await safe_answer(message, reply)
