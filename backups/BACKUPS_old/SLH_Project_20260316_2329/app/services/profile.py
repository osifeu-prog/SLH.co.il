from app.db.database import db


async def get_user_profile(user_id: int):
    async with db.pool.acquire() as conn:
        user_row = await conn.fetchrow(
            """
            SELECT
                user_id,
                username,
                role,
                balance,
                last_claim,
                invited_count,
                joined_at,
                xp_total,
                level,
                last_active_at
            FROM users
            WHERE user_id = $1
            """,
            user_id,
        )

        balance_row = await conn.fetchrow(
            """
            SELECT available, locked, updated_at
            FROM user_balances
            WHERE user_id = $1
            """,
            user_id,
        )

        referral_row = await conn.fetchrow(
            """
            SELECT inviter_user_id, invite_code, reward_granted, created_at
            FROM invites
            WHERE invited_user_id = $1
            """,
            user_id,
        )

        claims_count = await conn.fetchval(
            "SELECT COUNT(*) FROM claims WHERE user_id = $1",
            user_id,
        )

        daily_row = await conn.fetchrow(
            """
            SELECT streak, last_claim_at, last_reward, updated_at
            FROM daily_claims
            WHERE user_id = $1
            """,
            user_id,
        )

    return {
        "user": dict(user_row) if user_row else None,
        "balance": dict(balance_row) if balance_row else None,
        "referral": dict(referral_row) if referral_row else None,
        "daily": dict(daily_row) if daily_row else None,
        "claims_count": int(claims_count or 0),
    }