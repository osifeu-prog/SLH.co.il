from app.db.database import db


async def ensure_user_balance(user_id: int) -> None:
    async with db.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_balances (user_id, available, locked)
            VALUES ($1, 0, 0)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id,
        )


async def add_balance(user_id: int, amount):
    amount = float(amount)
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO user_balances (user_id, available, locked)
                VALUES ($1, 0, 0)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id,
            )

            await conn.execute(
                """
                UPDATE user_balances
                SET available = available + $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $2
                """,
                amount,
                user_id,
            )

            await conn.execute(
                """
                UPDATE users
                SET balance = COALESCE(balance, 0) + $1
                WHERE user_id = $2
                """,
                amount,
                user_id,
            )


async def subtract_balance(user_id: int, amount):
    amount = float(amount)
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO user_balances (user_id, available, locked)
                VALUES ($1, 0, 0)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id,
            )

            await conn.execute(
                """
                UPDATE user_balances
                SET available = available - $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $2
                """,
                amount,
                user_id,
            )

            await conn.execute(
                """
                UPDATE users
                SET balance = COALESCE(balance, 0) - $1
                WHERE user_id = $2
                """,
                amount,
                user_id,
            )


async def get_balance(user_id: int):
    async with db.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_balances (user_id, available, locked)
            VALUES ($1, 0, 0)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id,
        )

        row = await conn.fetchrow(
            """
            SELECT available, locked
            FROM user_balances
            WHERE user_id = $1
            """,
            user_id,
        )

        if not row:
            return {"available": 0, "locked": 0}

        return {
            "available": float(row["available"]),
            "locked": float(row["locked"]),
        }