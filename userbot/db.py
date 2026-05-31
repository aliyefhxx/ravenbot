"""PostgreSQL bağlantısı və sxema"""
import asyncpg
from config import Config

_pool: asyncpg.Pool | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plugins (
  name TEXT PRIMARY KEY,
  code TEXT NOT NULL,
  installed_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS welcomes (
  chat_id BIGINT PRIMARY KEY,
  message TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS klones (
  user_id BIGINT PRIMARY KEY,
  original_first TEXT,
  original_last TEXT,
  original_bio TEXT,
  original_photo BYTEA,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS blocks (
  user_id BIGINT PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

async def init_db():
    global _pool
    if not Config.DATABASE_URL:
        return None
    _pool = await asyncpg.create_pool(Config.DATABASE_URL, min_size=1, max_size=5)
    async with _pool.acquire() as c:
        await c.execute(SCHEMA)
    return _pool

def pool() -> asyncpg.Pool:
    assert _pool is not None, "DB init edilməyib"
    return _pool

async def set_setting(key: str, value: str):
    async with pool().acquire() as c:
        await c.execute(
            "INSERT INTO settings(key,value) VALUES($1,$2) "
            "ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value", key, value
        )

async def get_setting(key: str, default: str | None = None) -> str | None:
    async with pool().acquire() as c:
        row = await c.fetchrow("SELECT value FROM settings WHERE key=$1", key)
        return row["value"] if row else default
