"""Application entry point."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import Config
from database.db import Database
from handlers import github, settings, start, weather
from scheduler.morning import configure_scheduler
from services.github_graphql import GitHubGraphQL
from services.github_rest import GitHubService
from services.llm import LLMService
from services.weather import WeatherService
from utils.logger import configure_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    configure_logging()
    config = Config.from_env()
    db = Database(config.database_path)
    await db.connect()
    telegram_session = AiohttpSession(proxy=config.telegram_proxy) if config.telegram_proxy else None
    bot = Bot(config.telegram_token, session=telegram_session)
    dp = Dispatcher(storage=MemoryStorage())
    services = {
        "weather_service": WeatherService(),
        "llm_service": LLMService(config.llm_api_key, config.llm_model, config.llm_base_url),
        "github_service": GitHubService(config.github_token, config.github_username),
        "github_graphql": GitHubGraphQL(config.github_token, config.github_username),
    }
    dp["db"] = db
    dp["config"] = config
    dp["schedule_refresh"] = None
    for name, service in services.items():
        dp[name] = service
    dp.include_routers(start.router, weather.router, github.router, settings.router)

    scheduler = AsyncIOScheduler(timezone=config.timezone)
    refresh = configure_scheduler(scheduler, bot, db, {
        "weather_service": services["weather_service"],
        "llm_service": services["llm_service"],
        "github_service": services["github_service"],
        "github_graphql": services["github_graphql"],
    }, config.timezone)
    dp["schedule_refresh"] = refresh
    await refresh()
    scheduler.start()
    logger.info("EVENT: bot_start")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
