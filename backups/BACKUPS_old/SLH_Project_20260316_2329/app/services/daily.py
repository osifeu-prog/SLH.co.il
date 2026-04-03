import json
from datetime import datetime, timedelta
from decimal import Decimal

from app.db.database import db
from app.services.xp import grant_xp


DAILY_REWARDS = [
    Decimal("0.1000"),
    Decimal("0.1200"),
    Decimal("0.1500"),
    Decimal("0.1800"),
    Decimal("0.2200"),
    Decimal("0.2700"),
    Decimal("0.3500"),
]

DAILY_XP = [5, 5, 5, 5, 5, 5, 15]

CLAIM_COOLDOWN = timedelta(hours=24)
STREAK_RESET_AFTER = timedelta(hours=48)


def _reward_for_streak(streak: int) -> Decimal:
    idx = max(1, min(streak, len(DAILY_REWARDS))) - 1
    return DAILY_REWARDS[idx]


def _xp_for_streak(streak: int) -> int:
    idx = max(1, min(streak, len(DAILY_XP))) - 1
    return DAILY_XP[idx]


async def claim_daily(user_id: int, username: str | None = None) -> dict:
    now = datetime.utcnow()

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO users (
                    user_id, username, role, balance, last_claim, joined_at
                )
                VALUES ($1, $2, 'user', 0, TIMESTAMP '1970-01-01 00:00:00', CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE
                SET username = COALESCE(EXCLUDED.username, users.username),
                    last_active_at = CURRENT_TIMESTAMP
                """,
                user_id,
                username,
            )

            await conn.execute(
                """
                INSERT INTO user_balances (user_id, available, locked)
                VALUES ($1, 0, 0)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id,
            )

            user_row = await conn.fetchrow(
                """
                SELECT last_claim
                FROM users
                WHERE user_id = $1
                FOR UPDATE
                """,
                user_id,
            )

            dc_row = await conn.fetchrow(
                """
                SELECT streak, last_claim_at, last_reward
                FROM daily_claims
                WHERE user_id = $1
                """,
                user_id,
            )

            last_claim = user_row["last_claim"] if user_row else None
            current_streak = int(dc_row["streak"] or 0) if dc_row and dc_row["streak"] is not None else 0

            if last_claim and last_claim > datetime(1970, 1, 1):
                since_last = now - last_claim

                if since_last < CLAIM_COOLDOWN:
                    wait_seconds = int((CLAIM_COOLDOWN - since_last).total_seconds())
                    return {
                        "ok": False,
                        "error": "already_claimed",
                        "wait_seconds": max(0, wait_seconds),
                        "streak": current_streak,
                    }

                if since_last >= STREAK_RESET_AFTER:
                    next_streak = 1
                else:
                    next_streak = min(current_streak + 1, len(DAILY_REWARDS)) if current_streak > 0 else 1
            else:
                next_streak = 1

            reward = _reward_for_streak(next_streak)
            xp_gain = _xp_for_streak(next_streak)

            await conn.execute(
                """
                UPDATE users
                SET last_claim = CURRENT_TIMESTAMP,
                    last_active_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
                """,
                user_id,
            )

            await conn.execute(
                """
                INSERT INTO daily_claims (user_id, streak, last_claim_at, last_reward, updated_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE
                SET streak = EXCLUDED.streak,
                    last_claim_at = EXCLUDED.last_claim_at,
                    last_reward = EXCLUDED.last_reward,
                    updated_at = EXCLUDED.updated_at
                """,
                user_id,
                next_streak,
                reward,
            )

            claim_row = await conn.fetchrow(
                """
                INSERT INTO claims (user_id, amount, claim_type, created_at)
                VALUES ($1, $2, 'daily', CURRENT_TIMESTAMP)
                RETURNING id
                """,
                user_id,
                reward,
            )

            finance_ref_key = f"claim:daily:{int(claim_row['id'])}:v3"
            finance_metadata = json.dumps(
                {
                    "kind": "daily_claim",
                    "claim_id": int(claim_row["id"]),
                    "streak": next_streak,
                    "reward": str(reward),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )

            await conn.fetchval(
                """
                SELECT finance_post_user_reward(
                    $1, $2, $3, $4, $5, $6, $7, $8
                )
                """,
                finance_ref_key,
                user_id,
                reward,
                "daily_claim_reward",
                "Daily claim reward posted via finance ledger",
                "claims",
                int(claim_row["id"]),
                finance_metadata,
            )

            audit_payload = json.dumps(
                {
                    "kind": "daily_claim",
                    "streak": next_streak,
                    "reward": str(reward),
                    "mnh_units": int(reward * Decimal("10000")),
                    "claim_id": int(claim_row["id"]),
                    "finance_ref_key": finance_ref_key,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )

            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json)
                VALUES ($1, $2, $3)
                """,
                user_id,
                "claim.daily.v3",
                audit_payload,
            )

    xp_info = await grant_xp(
        user_id,
        "xp.daily_claim",
        xp_gain,
        {
            "streak": next_streak,
            "reward": str(reward),
        },
    )

    return {
        "ok": True,
        "reward": reward,
        "streak": next_streak,
        "xp_gain": xp_gain,
        "xp_total": xp_info["xp_total"],
        "level": xp_info["level"],
        "mnh_units": int(reward * Decimal("10000")),
    }