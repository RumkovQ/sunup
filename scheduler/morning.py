"""Morning digest composition and scheduler registration."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.queries import get_settings, list_cities
from services.weather import WEATHER_CODES

logger = logging.getLogger(__name__)


async def send_morning_digest(bot, db, weather_service, llm_service, github_service, github_graphql):
    settings = await get_settings(db)
    chat_id = settings["chat_id"]
    if not chat_id:
        logger.info("EVENT: morning_skipped | no_chat_id")
        return
    sections = []
    try:
        cities = await list_cities(db)
        city = next((item for item in cities if item["id"] == settings["active_city_id"]), None)
        if city:
            current = await weather_service.current(city["latitude"], city["longitude"])
            condition = WEATHER_CODES.get(current.get("weathercode"), "неизвестные условия")
            advice = await llm_service.clothing_advice(current["temperature"], condition, settings["language"])
            sections.append(f"🌤 {city['name']}: {current['temperature']} °C, {condition}.\n{advice}")
        else:
            logger.warning("EVENT: weather_skipped | city_not_selected")
    except Exception:
        logger.exception("EVENT: weather_failed")

    try:
        issues = await github_service.unanswered_issues(settings["issue_threshold_days"])
        streak, has_today = await github_graphql.current_streak()
        if issues or not has_today:
            age = issues[0]["age_days"] if issues else 0
            lines = ["📬 GitHub:"]
            if issues:
                lines.append(f"• {len(issues)} issues ждут ответа (самому старому {age} дн.)")
            if not has_today:
                lines.append(f"• ⚠️ Streak под угрозой: сегодня ещё не было контрибуций (текущая серия: {streak} дн.)")
            sections.append("\n".join(lines))
        else:
            sections.append("📬 GitHub: ✅ Всё чисто, красавчик")
    except Exception:
        logger.exception("EVENT: github_digest_failed")
        sections.append("📬 GitHub: ⚠️ GitHub временно недоступен")

    text = "\n\n".join(sections) or "Утренний дайджест пока пуст: настройте город и GitHub."
    try:
        await bot.send_message(chat_id, text)
        logger.info("EVENT: morning_sent | WEATHER_OK | GITHUB_OK")
    except Exception:
        logger.exception("EVENT: telegram_send_failed | retry_in=60s")
        import asyncio
        await asyncio.sleep(60)
        try:
            await bot.send_message(chat_id, text)
            logger.info("EVENT: morning_sent | retry=success")
        except Exception:
            logger.exception("EVENT: telegram_retry_failed")


def configure_scheduler(scheduler: AsyncIOScheduler, bot, db, services, timezone: str):
    async def job():
        await send_morning_digest(bot, db, **services)

    async def refresh():
        settings = await get_settings(db)
        hour, minute = map(int, settings["send_time"].split(":"))
        scheduler.add_job(job, "cron", hour=hour, minute=minute, id="morning_digest", replace_existing=True)

    scheduler.configure(timezone=timezone)
    return refresh
