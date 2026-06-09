import asyncpg
from app.core.config import settings

pool = None

async def init_db():
    global pool
    pool = await asyncpg.create_pool(settings.DATABASE_URL)

    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id BIGINT PRIMARY KEY,
            username TEXT,
            points INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)