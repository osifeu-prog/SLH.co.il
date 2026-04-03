from pathlib import Path
import re

root = Path(".")
bootstrap_path = root / "app" / "services" / "bootstrap.py"
claim_path = root / "app" / "handlers" / "claim.py"

bootstrap = bootstrap_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
claim = claim_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")

# --- bootstrap.py: imports ---
if "import json" not in bootstrap:
    bootstrap = "import json\n" + bootstrap

if "from app.services.xp import level_from_xp" not in bootstrap:
    bootstrap = bootstrap.replace(
        "from app.services.economy import add_balance\n",
        "from app.services.economy import add_balance\nfrom app.services.xp import level_from_xp\n",
    )

# --- bootstrap.py: constants ---
if "REFERRAL_XP = 15" not in bootstrap:
    bootstrap = bootstrap.replace(
        "REFERRAL_REWARD = 3.0\n",
        "REFERRAL_REWARD = 3.0\nREFERRAL_XP = 15\n",
    )

# --- bootstrap.py: replace grant_referral_reward_for_user ---
pattern = r'async def grant_referral_reward_for_user\(user_id: int\) -> bool:\n(?:    .*\n|\n)*?$'
replacement = '''async def grant_referral_reward_for_user(user_id: int) -> bool:
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

            await conn.execute(
                """
                UPDATE user_balances
                SET available = available + $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $2
                """,
                REFERRAL_REWARD,
                inviter_user_id,
            )

            await conn.execute(
                """
                UPDATE users
                SET balance = COALESCE(balance, 0) + $1,
                    xp_total = $2,
                    level = $3,
                    last_active_at = CURRENT_TIMESTAMP
                WHERE user_id = $4
                """,
                REFERRAL_REWARD,
                new_xp,
                new_level,
                inviter_user_id,
            )

            await conn.execute(
                """
                UPDATE invites
                SET reward_granted = TRUE
                WHERE id = $1
                """,
                invite_id,
            )

            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json)
                VALUES ($1, $2, $3)
                """,
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
'''
m = re.search(pattern, bootstrap, flags=re.M)
if not m:
    raise SystemExit("grant_referral_reward_for_user function block not found")
bootstrap = bootstrap[:m.start()] + replacement

# --- claim.py: import grant_referral_reward_for_user ---
if "from app.services.bootstrap import grant_referral_reward_for_user" not in claim:
    claim = claim.replace(
        "from app.services.daily import claim_daily\n",
        "from app.services.daily import claim_daily\nfrom app.services.bootstrap import grant_referral_reward_for_user\n",
    )

# --- claim.py: call referral reward after successful daily claim ---
old = "    await message.answer(_success_text(res))\n"
new = '''    referral_reward_granted = await grant_referral_reward_for_user(user_id)
    logger.info(
        "HANDLER: daily referral reward check by %s granted=%s",
        user_id,
        referral_reward_granted,
    )

    await message.answer(_success_text(res))
'''
if old not in claim:
    raise SystemExit("claim success anchor not found")
claim = claim.replace(old, new, 1)

bootstrap_path.write_text(bootstrap, encoding="utf-8", newline="\n")
claim_path.write_text(claim, encoding="utf-8", newline="\n")

print("patched bootstrap.py and claim.py")