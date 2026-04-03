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
                """
                INSERT INTO users (user_id, username, role, balance, last_claim, joined_at)
                VALUES ($1, $2, 'user', 0, TIMESTAMP '1970-01-01 00:00:00', CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE
                SET username = COALESCE(EXCLUDED.username, users.username)
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

            if not exists:
                await conn.execute(
                    """
                    INSERT INTO audit_log (user_id, event_type, payload_json)
                    VALUES ($1, $2, $3)
                    """,
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
                """
                INSERT INTO user_balances (user_id, available, locked)
                VALUES ($1, 0, 0)
                ON CONFLICT (user_id) DO NOTHING
                """,
                referrer_user_id,
            )

            inserted = await conn.fetchval(
                """
                INSERT INTO invites (inviter_user_id, invited_user_id, invite_code)
                VALUES ($1, $2, $3)
                ON CONFLICT (invited_user_id) DO NOTHING
                RETURNING id
                """,
                referrer_user_id,
                user_id,
                str(referrer_user_id),
            )

            if not inserted:
                return False

            await conn.execute(
                """
                UPDATE users
                SET invited_count = COALESCE(invited_count, 0) + 1
                WHERE user_id = $1
                """,
                referrer_user_id,
            )

            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json)
                VALUES ($1, $2, $3)
                """,
                referrer_user_id,
                "invite.attached",
                '{"invited_user_id":%s}' % user_id,
            )

            return True


async def grant_referral_reward_for_user(user_id: int) -> bool:
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            invite = await conn.fetchrow(
                """
                SELECT id, inviter_user_id, invited_user_id, reward_granted
                FROM invites
                WHERE invited_user_id = $1
                FOR UPDATE
                """,
                user_id,
            )

            if not invite:
                return False

            if invite["reward_granted"]:
                return False

            inviter_user_id = int(invite["inviter_user_id"])
            invite_id = int(invite["id"])

            await conn.execute(
                """
                INSERT INTO user_balances (user_id, available, locked)
                VALUES ($1, 0, 0)
                ON CONFLICT (user_id) DO NOTHING
                """,
                inviter_user_id,
            )

            inviter_row = await conn.fetchrow(
                """
                SELECT COALESCE(xp_total, 0) AS xp_total
                FROM users
                WHERE user_id = $1
                FOR UPDATE
                """,
                inviter_user_id,
            )

            current_xp = int(inviter_row["xp_total"] or 0) if inviter_row else 0
            new_xp = current_xp + int(REFERRAL_XP)
            new_level = level_from_xp(new_xp)

            updated = await conn.execute(
                """
                UPDATE invites
                SET reward_granted = TRUE
                WHERE id = $1
                  AND reward_granted = FALSE
                """,
                invite_id,
            )

            if updated != "UPDATE 1":
                return False

            reward_metadata = json.dumps(
                {
                    "kind": "referral_reward",
                    "invite_id": invite_id,
                    "invited_user_id": user_id,
                    "amount": REFERRAL_REWARD,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )

            ref_key = f"invite:reward:{invite_id}:v2"

            await conn.fetchval(
                """
                SELECT finance_post_user_reward(
                    $1, $2, $3, $4, $5, $6, $7, $8
                )
                """,
                ref_key,
                inviter_user_id,
                REFERRAL_REWARD,
                "referral_reward",
                "Referral reward posted via finance ledger",
                "invites",
                invite_id,
                reward_metadata,
            )

            await conn.execute(
                """
                UPDATE users
                SET xp_total = $1,
                    level = $2,
                    last_active_at = CURRENT_TIMESTAMP
                WHERE user_id = $3
                """,
                new_xp,
                new_level,
                inviter_user_id,
            )

            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json)
                VALUES ($1, $2, $3)
                """,
                inviter_user_id,
                "invite.reward_granted",
                '{"invited_user_id":%s,"amount":%s,"xp_delta":%s,"finance_ref_key":"%s"}'
                % (user_id, REFERRAL_REWARD, REFERRAL_XP, ref_key),
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
                """
                INSERT INTO xp_events (user_id, event_type, xp_delta, payload_json)
                VALUES ($1, $2, $3, $4)
                """,
                inviter_user_id,
                "xp.referral_reward",
                int(REFERRAL_XP),
                payload_json,
            )

    return True