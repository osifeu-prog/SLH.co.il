from pathlib import Path
from textwrap import dedent

root = Path(".")

claim_path = root / "app" / "handlers" / "claim.py"
bootstrap_path = root / "app" / "services" / "bootstrap.py"

claim_text = dedent("""\
import logging

from aiogram import F, Router, types
from aiogram.filters import Command

from app.services.daily import claim_daily
from app.services.bootstrap import grant_referral_reward_for_user

router = Router()
logger = logging.getLogger("slh.worker")


def _cooldown_text(wait_seconds: int, streak: int) -> str:
    hours = wait_seconds // 3600
    minutes = (wait_seconds % 3600) // 60
    return (
        "Daily reward already claimed.\\n\\n"
        f"Current streak: {streak}\\n"
        f"Try again in about {hours}h {minutes}m."
    )


def _success_text(res: dict) -> str:
    reward = float(res["reward"])
    return (
        "Daily reward claimed.\\n\\n"
        f"Reward: {reward:.4f} SLH\\n"
        f"MNH: {int(res['mnh_units'])}\\n"
        f"Streak: {int(res['streak'])}\\n"
        f"XP gained: +{int(res['xp_gain'])}\\n"
        f"XP total: {int(res['xp_total'])}\\n"
        f"Level: {int(res['level'])}"
    )


@router.message(Command("daily"))
@router.message(F.text == "Claim 1.0 SLH")
@router.message(F.text == "Daily Reward")
async def claim(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    username = message.from_user.username if message.from_user else None
    logger.info("HANDLER: daily claim by %s", user_id)

    res = await claim_daily(user_id, username)

    if not res["ok"]:
        if res.get("error") == "already_claimed":
            return await message.answer(
                _cooldown_text(
                    int(res.get("wait_seconds", 0)),
                    int(res.get("streak", 0)),
                )
            )
        return await message.answer("Daily reward failed. Please try again.")

    referral_reward_granted = await grant_referral_reward_for_user(user_id)
    logger.info(
        "HANDLER: daily referral reward check by %s granted=%s",
        user_id,
        referral_reward_granted,
    )

    await message.answer(_success_text(res))
""")

bootstrap_text = dedent("""\
import json

from app.db.database import db
from app.services.xp import level_from_xp

REFERRAL_REWARD = 3.0
REFERRAL_XP = 15


async def ensure_user_exists(user_id: int, username: str | None) -> bool:
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            exists = await conn.fetchval(
                "SELECT 1 FROM users WHERE user_id = $1",
                user_id,
            )

            await conn.execute(
                \"""
                INSERT INTO users (user_id, username, role, balance, last_claim, joined_at)
                VALUES ($1, $2, 'user', 0, TIMESTAMP '1970-01-01 00:00:00', CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE
                SET username = COALESCE(EXCLUDED.username, users.username)
                \""",
                user_id,
                username,
            )

            await conn.execute(
                \"""
                INSERT INTO user_balances (user_id, available, locked)
                VALUES ($1, 0, 0)
                ON CONFLICT (user_id) DO NOTHING
                \""",
                user_id,
            )

            if not exists:
                await conn.execute(
                    \"""
                    INSERT INTO audit_log (user_id, event_type, payload_json)
                    VALUES ($1, $2, $3)
                    \""",
                    user_id,
                    "user.created",
                    '{"source":"start"}',
                )
                return True

            return False


async def attach_referrer(user_id: int, referrer_user_id: int | None) -> bool:
    if not referrer_user_id:
        return False
    if user_id == referrer_user_id:
        return False

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                \"""
                INSERT INTO user_balances (user_id, available, locked)
                VALUES ($1, 0, 0)
                ON CONFLICT (user_id) DO NOTHING
                \""",
                referrer_user_id,
            )

            inserted = await conn.fetchval(
                \"""
                INSERT INTO invites (inviter_user_id, invited_user_id, invite_code)
                VALUES ($1, $2, $3)
                ON CONFLICT (invited_user_id) DO NOTHING
                RETURNING id
                \""",
                referrer_user_id,
                user_id,
                str(referrer_user_id),
            )

            if not inserted:
                return False

            await conn.execute(
                \"""
                UPDATE users
                SET invited_count = COALESCE(invited_count, 0) + 1
                WHERE user_id = $1
                \""",
                referrer_user_id,
            )

            await conn.execute(
                \"""
                INSERT INTO audit_log (user_id, event_type, payload_json)
                VALUES ($1, $2, $3)
                \""",
                referrer_user_id,
                "invite.attached",
                '{"invited_user_id":%s}' % user_id,
            )

            return True


async def grant_referral_reward_for_user(user_id: int) -> bool:
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            invite = await conn.fetchrow(
                \"""
                SELECT id, inviter_user_id, invited_user_id, reward_granted
                FROM invites
                WHERE invited_user_id = $1
                FOR UPDATE
                \""",
                user_id,
            )

            if not invite:
                return False

            if invite["reward_granted"]:
                return False

            inviter_user_id = int(invite["inviter_user_id"])
            invite_id = int(invite["id"])

            await conn.execute(
                \"""
                INSERT INTO user_balances (user_id, available, locked)
                VALUES ($1, 0, 0)
                ON CONFLICT (user_id) DO NOTHING
                \""",
                inviter_user_id,
            )

            inviter_row = await conn.fetchrow(
                \"""
                SELECT COALESCE(xp_total, 0) AS xp_total
                FROM users
                WHERE user_id = $1
                FOR UPDATE
                \""",
                inviter_user_id,
            )

            current_xp = int(inviter_row["xp_total"] or 0) if inviter_row else 0
            new_xp = current_xp + int(REFERRAL_XP)
            new_level = level_from_xp(new_xp)

            updated = await conn.execute(
                \"""
                UPDATE invites
                SET reward_granted = TRUE
                WHERE id = $1
                  AND reward_granted = FALSE
                \""",
                invite_id,
            )

            if updated != "UPDATE 1":
                return False

            await conn.execute(
                \"""
                UPDATE user_balances
                SET available = available + $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $2
                \""",
                REFERRAL_REWARD,
                inviter_user_id,
            )

            await conn.execute(
                \"""
                UPDATE users
                SET balance = COALESCE(balance, 0) + $1,
                    xp_total = $2,
                    level = $3,
                    last_active_at = CURRENT_TIMESTAMP
                WHERE user_id = $4
                \""",
                REFERRAL_REWARD,
                new_xp,
                new_level,
                inviter_user_id,
            )

            await conn.execute(
                \"""
                INSERT INTO audit_log (user_id, event_type, payload_json)
                VALUES ($1, $2, $3)
                \""",
                inviter_user_id,
                "invite.reward_granted",
                '{"invited_user_id":%s,"amount":%s,"xp_delta":%s}' % (user_id, REFERRAL_REWARD, REFERRAL_XP),
            )

            payload_json = json.dumps(
                {
                    "invited_user_id": user_id,
                    "amount": REFERRAL_REWARD,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )

            await conn.execute(
                \"""
                INSERT INTO xp_events (user_id, event_type, xp_delta, payload_json)
                VALUES ($1, $2, $3, $4)
                \""",
                inviter_user_id,
                "xp.referral_reward",
                int(REFERRAL_XP),
                payload_json,
            )

    return True
""")

claim_path.write_text(claim_text, encoding="utf-8", newline="\n")
bootstrap_path.write_text(bootstrap_text, encoding="utf-8", newline="\n")

print("claim.py and bootstrap.py rewritten cleanly")