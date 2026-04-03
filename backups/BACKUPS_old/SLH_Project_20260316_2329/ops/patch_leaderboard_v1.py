from pathlib import Path

p = Path("worker.py")
s = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")

old_import = "from app.services.profile import get_user_profile\n"
new_import = "from app.services.profile import get_user_profile\nfrom app.services.xp import LEVEL_THRESHOLDS\n"
if "from app.services.xp import LEVEL_THRESHOLDS" not in s:
    if old_import not in s:
        raise SystemExit("import anchor not found")
    s = s.replace(old_import, new_import, 1)

old_kb = """def main_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="About")
    kb.button(text="Health")
    kb.button(text="Balance")
    kb.button(text="Tasks")
    kb.button(text="Invite Friend")
    kb.button(text="Withdraw")
    kb.button(text="Withdrawals")
    kb.button(text="Claim 1.0 SLH")
    kb.button(text="Profile")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup(resize_keyboard=True)
"""
new_kb = """def main_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="About")
    kb.button(text="Health")
    kb.button(text="Balance")
    kb.button(text="Tasks")
    kb.button(text="Invite Friend")
    kb.button(text="Withdraw")
    kb.button(text="Withdrawals")
    kb.button(text="Claim 1.0 SLH")
    kb.button(text="Profile")
    kb.button(text="Leaderboard")
    kb.adjust(2, 2, 2, 2, 2)
    return kb.as_markup(resize_keyboard=True)
"""
if old_kb not in s:
    raise SystemExit("main_kb block not found")
s = s.replace(old_kb, new_kb, 1)

anchor = """def tail_log(path: Path, n_lines: int = 120) -> str:
    try:
        if not path.exists():
            return f"{path.name} not found"
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-n_lines:]
        return "\\n".join(lines)[-3500:]
    except Exception as e:
        return f"tail error: {e!r}"


bot = Bot(BOT_TOKEN)
"""
insert_helpers = """def tail_log(path: Path, n_lines: int = 120) -> str:
    try:
        if not path.exists():
            return f"{path.name} not found"
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-n_lines:]
        return "\\n".join(lines)[-3500:]
    except Exception as e:
        return f"tail error: {e!r}"


def xp_to_next_level(xp_total: int) -> int:
    for _, min_xp in LEVEL_THRESHOLDS:
        if xp_total < min_xp:
            return max(0, min_xp - xp_total)
    return 0


async def fetch_user_rank(user_id: int) -> int | None:
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            \"""
            SELECT rank
            FROM (
                SELECT
                    user_id,
                    ROW_NUMBER() OVER (
                        ORDER BY
                            COALESCE(xp_total, 0) DESC,
                            COALESCE(level, 1) DESC,
                            COALESCE(invited_count, 0) DESC,
                            user_id ASC
                    ) AS rank
                FROM users
            ) ranked
            WHERE user_id = $1
            \""",
            user_id,
        )
    return int(row["rank"]) if row else None


async def render_leaderboard_text(limit: int = 10) -> str:
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            \"""
            SELECT
                user_id,
                username,
                invited_count,
                xp_total,
                level
            FROM users
            ORDER BY
                COALESCE(xp_total, 0) DESC,
                COALESCE(level, 1) DESC,
                COALESCE(invited_count, 0) DESC,
                user_id ASC
            LIMIT $1
            \""",
            limit,
        )

    if not rows:
        return "Leaderboard\\n\\nNo users yet."

    lines = ["Leaderboard", ""]
    for idx, row in enumerate(rows, start=1):
        username = row["username"] or "-"
        xp_total = int(row["xp_total"] or 0)
        level = int(row["level"] or 1)
        invites = int(row["invited_count"] or 0)
        lines.append(
            f"{idx}. {username} | XP {xp_total} | L{level} | Invites {invites}"
        )

    return "\\n".join(lines)


bot = Bot(BOT_TOKEN)
"""
if anchor not in s:
    raise SystemExit("helper anchor not found")
s = s.replace(anchor, insert_helpers, 1)

old_profile_head = """async def render_profile_text(user_id: int) -> str:
    p = await get_user_profile(user_id)
    user = p["user"] or {}
    bal = p["balance"] or {}
    ref = p["referral"]
    daily = p["daily"] or {}

    available = float(bal.get("available", 0) or 0)
    locked = float(bal.get("locked", 0) or 0)
    available_mnh = int(round(available * 10000))
    xp_total = int(user.get("xp_total", 0) or 0)
    level = int(user.get("level", 1) or 1)
    streak = int(daily.get("streak", 0) or 0)

    lines = [
"""
new_profile_head = """async def render_profile_text(user_id: int) -> str:
    p = await get_user_profile(user_id)
    user = p["user"] or {}
    bal = p["balance"] or {}
    ref = p["referral"]
    daily = p["daily"] or {}

    available = float(bal.get("available", 0) or 0)
    locked = float(bal.get("locked", 0) or 0)
    available_mnh = int(round(available * 10000))
    xp_total = int(user.get("xp_total", 0) or 0)
    level = int(user.get("level", 1) or 1)
    streak = int(daily.get("streak", 0) or 0)
    rank = await fetch_user_rank(user_id)
    next_xp_gap = xp_to_next_level(xp_total)

    lines = [
"""
if old_profile_head not in s:
    raise SystemExit("profile head block not found")
s = s.replace(old_profile_head, new_profile_head, 1)

old_profile_lines = """        f"MNH: {available_mnh}",
        f"XP total: {xp_total}",
        f"Level: {level}",
        f"Daily streak: {streak}",
"""
new_profile_lines = """        f"MNH: {available_mnh}",
        f"XP total: {xp_total}",
        f"Level: {level}",
        f"Rank: #{rank}" if rank else "Rank: -",
        f"XP to next level: {next_xp_gap}",
        f"Daily streak: {streak}",
"""
if old_profile_lines not in s:
    raise SystemExit("profile lines block not found")
s = s.replace(old_profile_lines, new_profile_lines, 1)

profile_anchor = """@dp.message(Command("profile"))
async def profile_cmd(m: types.Message):
    uid = m.from_user.id if m.from_user else 0
    username = m.from_user.username if m.from_user else None
    await ensure_user_exists(uid, username)
    logger.info("HANDLER: /profile by %s", uid)
    await m.answer(await render_profile_text(uid))

@dp.message(Command("admin"))
"""
profile_insert = """@dp.message(Command("profile"))
async def profile_cmd(m: types.Message):
    uid = m.from_user.id if m.from_user else 0
    username = m.from_user.username if m.from_user else None
    await ensure_user_exists(uid, username)
    logger.info("HANDLER: /profile by %s", uid)
    await m.answer(await render_profile_text(uid))

@dp.message(F.text == "Leaderboard")
async def leaderboard_btn(m: types.Message):
    uid = m.from_user.id if m.from_user else 0
    username = m.from_user.username if m.from_user else None
    await ensure_user_exists(uid, username)
    logger.info("HANDLER: Leaderboard by %s", uid)
    await m.answer(await render_leaderboard_text(10))

@dp.message(Command("leaderboard"))
async def leaderboard_cmd(m: types.Message):
    uid = m.from_user.id if m.from_user else 0
    username = m.from_user.username if m.from_user else None
    await ensure_user_exists(uid, username)
    logger.info("HANDLER: /leaderboard by %s", uid)
    await m.answer(await render_leaderboard_text(10))

@dp.message(Command("admin"))
"""
if profile_anchor not in s:
    raise SystemExit("profile/admin anchor not found")
s = s.replace(profile_anchor, profile_insert, 1)

p.write_text(s, encoding="utf-8", newline="\n")
print("worker.py patched: leaderboard + profile rank")