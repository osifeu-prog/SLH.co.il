from pathlib import Path
import re

root = Path(".")
worker_path = root / "worker.py"
bootstrap_path = root / "app" / "services" / "bootstrap.py"
claim_path = root / "app" / "handlers" / "claim.py"

worker = worker_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
bootstrap = bootstrap_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
claim = claim_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")

# =========================
# worker.py - fix /start referral arg type
# =========================
old_worker = """    ref_code = None
    if command and command.args:
        ref_code = command.args.strip()

    if ref_code:
        await attach_referrer(uid, ref_code)

    logger.info("HANDLER: /start by %s args=%s", uid, ref_code)
"""
new_worker = """    ref_user_id = None
    raw_ref = None
    if command and command.args:
        raw_ref = command.args.strip()
        if raw_ref.isdigit():
            ref_user_id = int(raw_ref)
        else:
            logger.warning("HANDLER: /start invalid referral arg by %s raw=%r", uid, raw_ref)

    if ref_user_id:
        await attach_referrer(uid, ref_user_id)

    logger.info("HANDLER: /start by %s args=%s", uid, raw_ref)
"""
if old_worker not in worker:
    raise SystemExit("worker.py start referral block not found")
worker = worker.replace(old_worker, new_worker, 1)

# =========================
# bootstrap.py - imports/constants
# =========================
if "import json\n" not in bootstrap:
    bootstrap = "import json\n" + bootstrap

if "from app.services.xp import level_from_xp" not in bootstrap:
    bootstrap = bootstrap.replace(
        "from app.services.economy import add_balance\n",
        "from app.services.economy import add_balance\nfrom app.services.xp import level_from_xp\n",
    )

if "REFERRAL_XP = 15" not in bootstrap:
    bootstrap = bootstrap.replace(
        "REFERRAL_REWARD = 3.0\n",
        "REFERRAL_REWARD = 3.0\nREFERRAL_XP = 15\n",
    )

# =========================
# bootstrap.py - replace reward function
# =========================
pattern_bootstrap = r"async def grant_referral_reward_for_user\(user_id: int\) -> bool:\n[\s\S]*$"
replacement_bootstrap = """async def grant_referral_reward_for_user(user_id: int) -> bool:
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
"""
if not re.search(pattern_bootstrap, bootstrap):
    raise SystemExit("bootstrap.py reward function block not found")
bootstrap = re.sub(pattern_bootstrap, replacement_bootstrap, bootstrap, count=1)

# =========================
# claim.py - add import
# =========================
if "from app.services.bootstrap import grant_referral_reward_for_user" not in claim:
    claim = claim.replace(
        "from app.services.daily import claim_daily\n",
        "from app.services.daily import claim_daily\nfrom app.services.bootstrap import grant_referral_reward_for_user\n",
        1,
    )

# =========================
# claim.py - replace claim function
# =========================
pattern_claim = r"@router\.message\(Command\(\"daily\"\)\)\n@router\.message\(F\.text == \"Claim 1\.0 SLH\"\)\n@router\.message\(F\.text == \"Daily Reward\"\)\nasync def claim\(message: types\.Message\):\n[\s\S]*$"
replacement_claim = """@router.message(Command("daily"))
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
"""
if not re.search(pattern_claim, claim):
    raise SystemExit("claim.py claim function block not found")
claim = re.sub(pattern_claim, replacement_claim, claim, count=1)

worker_path.write_text(worker, encoding="utf-8", newline="\n")
bootstrap_path.write_text(bootstrap, encoding="utf-8", newline="\n")
claim_path.write_text(claim, encoding="utf-8", newline="\n")

print("patched worker.py, bootstrap.py, claim.py")