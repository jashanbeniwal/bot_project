import aiosqlite
import os

DB_PATH = os.environ.get("DATABASE_URL", "bot_data.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            settings TEXT DEFAULT '{}'
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            payload TEXT,
            status TEXT DEFAULT 'pending'
        )
        """)
        await db.commit()

async def get_or_create_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if row:
            return row[0]
        await db.execute("INSERT INTO users (user_id, settings) VALUES (?, ?)", (user_id, "{}"))
        await db.commit()
        return user_id

async def update_settings(user_id: int, settings_json: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET settings = ? WHERE user_id = ?", (settings_json, user_id))
        await db.commit()

async def read_settings(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT settings FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else "{}"
