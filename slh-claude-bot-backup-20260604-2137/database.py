import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL", "")
db_pool = None

async def init_db():
    global db_pool
    if DATABASE_URL:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
        # ×™×¦×™×¨×ª ×˜×‘×œ××•×ª ×× ×œ× ×§×™×™×ž×•×ª
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS premium_users (
                    user_id BIGINT PRIMARY KEY,
                    expires_at TIMESTAMP
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id BIGINT PRIMARY KEY,
                    points INTEGER DEFAULT 0
                )
            """)

