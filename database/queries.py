"""CRUD helpers for the single-owner settings and saved cities."""

from .db import Database


async def get_settings(db: Database) -> dict:
    row = await (await db.conn.execute("SELECT * FROM settings WHERE id=1")).fetchone()
    return dict(row)


async def update_settings(db: Database, **values) -> None:
    allowed = {"chat_id", "active_city_id", "send_time", "language", "issue_threshold_days"}
    updates = {key: value for key, value in values.items() if key in allowed}
    if not updates:
        return
    assignments = ", ".join(f"{key}=?" for key in updates)
    await db.conn.execute(f"UPDATE settings SET {assignments} WHERE id=1", tuple(updates.values()))
    await db.conn.commit()


async def list_cities(db: Database) -> list[dict]:
    rows = await (await db.conn.execute("SELECT * FROM cities ORDER BY name COLLATE NOCASE")).fetchall()
    return [dict(row) for row in rows]


async def add_city(db: Database, name: str, latitude: float, longitude: float) -> int:
    cursor = await db.conn.execute(
        "INSERT INTO cities(name, latitude, longitude) VALUES(?,?,?) "
        "ON CONFLICT(name) DO UPDATE SET latitude=excluded.latitude, longitude=excluded.longitude",
        (name, latitude, longitude),
    )
    await db.conn.commit()
    row = await (await db.conn.execute("SELECT id FROM cities WHERE name=?", (name,))).fetchone()
    return int(row["id"])


async def delete_city(db: Database, city_id: int) -> None:
    await db.conn.execute("DELETE FROM cities WHERE id=?", (city_id,))
    await db.conn.execute("UPDATE settings SET active_city_id=NULL WHERE active_city_id=?", (city_id,))
    await db.conn.commit()
