from app.db.database import db


async def get_withdrawal_for_execution(withdrawal_id: int) -> dict | None:
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, user_id, amount, wallet, status
            FROM withdrawals
            WHERE id = $1
            """,
            withdrawal_id,
        )
    return dict(row) if row else None