"""SQLite schema and connection lifecycle."""

from pathlib import Path
from typing import Optional
import aiosqlite


SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    chat_id INTEGER,
    active_city_id INTEGER,
    send_time TEXT NOT NULL DEFAULT '08:00',
    language TEXT NOT NULL DEFAULT 'ru',
    issue_threshold_days INTEGER NOT NULL DEFAULT 7
);
CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
);
INSERT OR IGNORE INTO settings (id) VALUES (1);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        self.connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = await aiosqlite.connect(self.path)
        self.connection.row_factory = aiosqlite.Row
        await self.connection.executescript(SCHEMA)
        await self.connection.commit()

    async def close(self) -> None:
        if self.connection:
            await self.connection.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        if self.connection is None:
            raise RuntimeError("Database is not connected")
        return self.connection
