from app.db.pool import pool

class UserService:

    @staticmethod
    async def create_or_update(user_id: int, username: str):
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (telegram_id, username)
                VALUES ($1, $2)
                ON CONFLICT (telegram_id)
                DO UPDATE SET username=$2
                """,
                user_id,
                username
            )

    @staticmethod
    async def get(user_id: int):
        async with pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id=$1",
                user_id
            )