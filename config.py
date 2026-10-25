"""Environment-based application configuration."""

from dataclasses import dataclass
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    telegram_token: str
    telegram_proxy: str = ""
    github_token: str = ""
    github_username: str = ""
    llm_api_key: str = ""
    llm_model: str = "gemini-3.5-flash-lite"
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    owner_chat_id: Optional[int] = None
    database_path: str = "data/morning_bot.sqlite3"
    timezone: str = "Europe/Minsk"

    @classmethod
    def from_env(cls) -> "Config":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required; see .env.example")
        chat_id = os.getenv("OWNER_CHAT_ID", "").strip()
        return cls(
            telegram_token=token,
            telegram_proxy=os.getenv("TELEGRAM_PROXY", "").strip(),
            github_token=os.getenv("GITHUB_TOKEN", "").strip(),
            github_username=os.getenv("GITHUB_USERNAME", "").strip(),
            llm_api_key=os.getenv("LLM_API_KEY", "").strip(),
            llm_model=os.getenv("LLM_MODEL", "gemini-3.5-flash-lite").strip(),
            llm_base_url=os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai").rstrip("/"),
            owner_chat_id=int(chat_id) if chat_id else None,
            database_path=os.getenv("DATABASE_PATH", "data/morning_bot.sqlite3"),
            timezone=os.getenv("TIMEZONE", "Europe/Minsk").strip(),
        )
