import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        db_url = (os.getenv("DATABASE_URL", "") or os.getenv("DB_URL", "")).strip()
        if not db_url:
            host = os.getenv("DB_HOST", "127.0.0.1").strip()
            name = os.getenv("DB_NAME", "slh_db").strip()
            user = os.getenv("DB_USER", "postgres").strip()
            password = os.getenv("DB_PASS", "").strip()

            if password:
                db_url = f"postgresql://{user}:{password}@{host}:5432/{name}"
            else:
                db_url = f"postgresql://{user}@{host}:5432/{name}"

        self.pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=10)

        async with self.pool.acquire() as conn:
            await conn.execute("SELECT 1")

        print(f"DB connected: {db_url.split('@')[-1]}")


    async def disconnect(self):
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            print("DB disconnected")
db = Database()