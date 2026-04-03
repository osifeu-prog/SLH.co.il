import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from redis.asyncio import Redis
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.db.database import db
from app.services.bootstrap import ensure_user_exists, attach_referrer
from app.services.economy import get_balance
from app.services.profile import get_user_profile
from app.services.xp import LEVEL_THRESHOLDS
from app.handlers.claim import router as claim_router
from app.handlers.tasks import router as tasks_router
from app.handlers.invite import router as invite_router
from app.handlers.purchases import router as purchases_router
from app.handlers.withdrawals import router as withdrawals_router
from app.handlers.ton_admin import router as ton_admin_router
from app.handlers.task_verifications import router as task_verifications_router
from app.handlers.admin_console_v2 import router as admin_console_v2_router
from app.core.admin_guard import ADMIN_USER_ID, is_admin

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

WORKER_LOG = str(LOG_DIR / "worker.log")

fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
fh = RotatingFileHandler(WORKER_LOG, maxBytes=2_000_000, backupCount=10, encoding="utf-8")
sh = logging.StreamHandler(sys.stdout)
fh.setFormatter(fmt)
sh.setFormatter(fmt)

logging.getLogger().handlers.clear()
logging.getLogger().addHandler(fh)
logging.getLogger().addHandler(sh)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("slh.worker")

load_dotenv(ROOT / ".env", override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BOT_USERNAME = os.getenv("BOT_USERNAME", "TON_MNH_bot").strip()
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6380/0")
REDIS_STREAM = os.getenv("REDIS_STREAM", "slh:updates")
REDIS_BLOCK_MS = int(os.getenv("REDIS_BLOCK_MS", "5000"))

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN missing in .env")

logger.info("BOOT: ADMIN_USER_ID=%s", ADMIN_USER_ID)




def main_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="About")
    kb.button(text="Health")
    kb.button(text="Balance")
    kb.button(text="Tasks")
    kb.button(text="Invite Friend")
    kb.button(text="Store")
    kb.button(text="Buy")
    kb.button(text="Withdraw")
    kb.button(text="Withdrawals")
    kb.button(text="My Orders")
    kb.button(text="Claim 1.0 SLH")
    kb.button(text="Profile")
    kb.button(text="Leaderboard")
    kb.adjust(2, 2, 2, 2, 2, 2, 1)
    return kb.as_markup(resize_keyboard=True)


def admin_inline():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Tail Logs", callback_data="adm:tail")],
        [types.InlineKeyboardButton(text="Stats", callback_data="adm:stats")],
    ])


def tail_log(path: Path, n_lines: int = 120) -> str:
    try:
        if not path.exists():
            return f"{path.name} not found"
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-n_lines:]
        return "\n".join(lines)[-3500:]
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
            """
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
            """,
            user_id,
        )
    return int(row["rank"]) if row else None


async def render_leaderboard_text(limit: int = 10) -> str:
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
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
            """,
            limit,
        )

    if not rows:
        return "Leaderboard\n\nNo users yet."

    lines = ["Leaderboard", ""]
    for idx, row in enumerate(rows, start=1):
        username = row["username"] or "-"
        xp_total = int(row["xp_total"] or 0)
        level = int(row["level"] or 1)
        invites = int(row["invited_count"] or 0)
        lines.append(f"{idx}. {username} | XP {xp_total} | L{level} | Invites {invites}")
    return "\n".join(lines)


def render_about_text() -> str:
    return (
        "SLH Bot\n\n"
        "أ—â€؛أ—ع¯أ—ع؛ أ—ع¯أ—آ¤أ—آ©أ—آ¨ أ—إ“أ—آ أ—â€‌أ—إ“ أ—آ¤أ—آ¢أ—â€¢أ—إ“أ—â€¢أ—ع¾ أ—â€کأ—طŒأ—â„¢أ—طŒأ—â„¢أ—â€¢أ—ع¾ أ—â€کأ—â€چأ—آ¢أ—آ¨أ—â€؛أ—ع¾:\n"
        "- أ—آ¦أ—آ¤أ—â„¢أ—â„¢أ—â€‌ أ—â€کأ—â„¢أ—ع¾أ—آ¨أ—â€‌ أ—â€¢أ—â€کأ—آ¤أ—آ¨أ—â€¢أ—آ¤أ—â„¢أ—إ“\n"
        "- أ—â€چأ—آ©أ—â„¢أ—â€چأ—â€¢أ—ع¾ أ—â€¢أ—آ¦أ—â€کأ—â„¢أ—آ¨أ—ع¾ XP\n"
        "- أ—â€‌أ—â€“أ—â€چأ—آ أ—â€¢أ—ع¾ أ—â€¢أ—آ¨أ—â€؛أ—â„¢أ—آ©أ—â€¢أ—ع¾\n"
        "- أ—â€‌أ—â€“أ—â€چأ—آ أ—â€¢أ—ع¾ أ—â€چأ—آ©أ—â„¢أ—â€؛أ—â€‌\n"
        "- أ—آ§أ—â„¢أ—آ©أ—â€¢أ—آ¨ أ—â€‌أ—â€“أ—â€چأ—آ أ—â€‌ أ—إ“أ—â€”أ—â€کأ—آ¨أ—â„¢أ—â€Œ\n\n"
        "أ—â€‌أ—â€چأ—آ¢أ—آ¨أ—â€؛أ—ع¾ أ—آ أ—â€چأ—آ¦أ—ع¯أ—ع¾ أ—â€کأ—آ©أ—â„¢أ—آ¤أ—â€¢أ—آ¨ أ—â€چأ—ع¾أ—â€چأ—آ©أ—ع‘, أ—â€¢أ—â€‌أ—â€چأ—طŒأ—â€”أ—آ¨ أ—â€‌أ—â„¢أ—â€œأ—آ أ—â„¢ أ—آ¤أ—آ¢أ—â„¢أ—إ“."
    )


def render_health_text() -> str:
    return (
        "System Health\n\n"
        f"Bot username: @{BOT_USERNAME}\n"
        f"Redis stream: {REDIS_STREAM}\n"
        "Worker: online\n"
        "DB: connected\n"
        "Commerce: enabled by settings\n"
        "Manual payment flow: available\n"
        "Status: OK"
    )


bot = Bot(BOT_TOKEN)
dp = Dispatcher()

dp.include_router(claim_router)
dp.include_router(tasks_router)
dp.include_router(invite_router)
dp.include_router(purchases_router)
dp.include_router(withdrawals_router)
dp.include_router(ton_admin_router)
dp.include_router(task_verifications_router)
dp.include_router(admin_console_v2_router)


@dp.message(Command("start"))
async def start_cmd(m: types.Message, command: CommandObject | None = None):
    uid = m.from_user.id if m.from_user else 0
    username = m.from_user.username if m.from_user else None
    await ensure_user_exists(uid, username)

    ref_user_id = None
    raw_ref = ((command.args if command else None) or "").strip()

    if raw_ref:
        lines = [ln.strip() for ln in raw_ref.splitlines() if ln.strip()]
        blocked_texts = {
            "About",
            "Health",
            "Balance",
            "Profile",
            "Leaderboard",
            "Invite Friend",
            "Withdraw",
            "Withdrawals",
            "Tasks",
            "Claim 1.0 SLH",
            "Daily Reward",
            "Store",
            "Buy",
            "My Orders",
        }

        if len(lines) == 1:
            candidate = lines[0]
            if candidate not in blocked_texts and not candidate.startswith("/") and candidate.isdigit():
                try:
                    ref_user_id = int(candidate)
                except Exception:
                    ref_user_id = None

    if ref_user_id:
        await attach_referrer(uid, ref_user_id)
        logger.info("HANDLER: /start by %s args=%s", uid, ref_user_id)
    else:
        logger.info("HANDLER: /start by %s args=None", uid)

    await m.answer(
        "أ—â€کأ—آ¨أ—â€¢أ—ع‘ أ—â€‌أ—â€کأ—ع¯ أ—إ“-SLH.\n\nأ—â€کأ—â€”أ—آ¨ أ—آ¤أ—آ¢أ—â€¢أ—إ“أ—â€‌ أ—â€چأ—â€‌أ—ع¾أ—آ¤أ—آ¨أ—â„¢أ—ع© أ—إ“أ—â€چأ—ع©أ—â€‌ أ—â€؛أ—â€œأ—â„¢ أ—إ“أ—â€‌أ—ع¾أ—â€”أ—â„¢أ—إ“.",
        reply_markup=main_kb(),
    )

@dp.message(F.text == "About")
async def about_btn(m: types.Message):
    logger.info("HANDLER: About btn")
    await m.answer(render_about_text())


@dp.message(F.text == "Health")
async def health_btn(m: types.Message):
    logger.info("HANDLER: Health btn")
    await m.answer(render_health_text())


@dp.message(F.text == "Balance")
async def balance_btn(m: types.Message):
    uid = m.from_user.id if m.from_user else 0
    username = m.from_user.username if m.from_user else None
    await ensure_user_exists(uid, username)
    bal = await get_balance(uid)
    logger.info("HANDLER: Balance btn by %s", uid)
    await m.answer(
        f"Balance\n\nAvailable: {bal['available']:.8f} SLH\nLocked: {bal['locked']:.8f} SLH"
    )


@dp.message(Command("balance"))
async def balance_cmd(m: types.Message):
    uid = m.from_user.id if m.from_user else 0
    username = m.from_user.username if m.from_user else None
    await ensure_user_exists(uid, username)
    bal = await get_balance(uid)
    logger.info("HANDLER: /balance by %s", uid)
    await m.answer(
        f"Balance\n\nAvailable: {bal['available']:.8f} SLH\nLocked: {bal['locked']:.8f} SLH"
    )


async def render_profile_text(user_id: int) -> str:
    p = await get_user_profile(user_id)
    user = p["user"] or {}
    bal = p["balance"] or {}
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
        "Profile",
        "",
        f"User ID: {user.get('user_id', user_id)}",
        f"Username: {user.get('username') or '-'}",
        f"Role: {user.get('role') or 'user'}",
        f"Available: {available:.8f} SLH",
        f"Locked: {locked:.8f} SLH",
        f"MNH: {available_mnh}",
        f"XP total: {xp_total}",
        f"Level: {level}",
        f"Rank: #{rank}" if rank else "Rank: -",
        f"XP to next level: {next_xp_gap}",
        f"Daily streak: {streak}",
        f"Claims count: {p['claims_count']}",
        f"Invited count: {user.get('invited_count', 0)}",
        f"Joined at: {user.get('joined_at')}",
        f"Last claim: {user.get('last_claim')}",
    ]

    if user.get("last_active_at"):
        lines.append(f"Last active: {user.get('last_active_at')}")
    if p.get("referral"):
        lines.append(f"Referral link: {p['referral']}")

    return "\n".join(lines)


@dp.message(F.text == "Profile")
async def profile_btn(m: types.Message):
    uid = m.from_user.id if m.from_user else 0
    username = m.from_user.username if m.from_user else None
    await ensure_user_exists(uid, username)
    logger.info("HANDLER: Profile by %s", uid)
    await m.answer(await render_profile_text(uid))


@dp.message(Command("profile"))
async def profile_cmd(m: types.Message):
    uid = m.from_user.id if m.from_user else 0
    username = m.from_user.username if m.from_user else None
    await ensure_user_exists(uid, username)
    logger.info("HANDLER: /profile by %s", uid)
    await m.answer(await render_profile_text(uid))


@dp.message(F.text == "Leaderboard")
async def leaderboard_btn(m: types.Message):
    logger.info("HANDLER: Leaderboard by %s", m.from_user.id if m.from_user else 0)
    await m.answer(await render_leaderboard_text(10))


@dp.message(Command("leaderboard"))
async def leaderboard_cmd(m: types.Message):
    logger.info("HANDLER: /leaderboard by %s", m.from_user.id if m.from_user else 0)
    await m.answer(await render_leaderboard_text(10))


@dp.message(Command("admin"))
async def admin_cmd(m: types.Message):
    uid = m.from_user.id if m.from_user else 0
    if not is_admin(uid):
        await m.answer("Forbidden")
        return
    logger.info("HANDLER: /admin by %s", uid)
    await m.answer("Admin panel", reply_markup=admin_inline())


@dp.callback_query(F.data == "adm:tail")
async def adm_tail(cb: types.CallbackQuery):
    uid = cb.from_user.id if cb.from_user else 0
    if not is_admin(uid):
        await cb.answer("Forbidden", show_alert=True)
        return
    await cb.answer()
    if cb.message:
        await cb.message.answer(tail_log(Path(WORKER_LOG)))


@dp.callback_query(F.data == "adm:stats")
async def adm_stats(cb: types.CallbackQuery):
    uid = cb.from_user.id if cb.from_user else 0
    if not is_admin(uid):
        await cb.answer("Forbidden", show_alert=True)
        return
    await cb.answer()

    async with db.pool.acquire() as conn:
        users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        orders_count = await conn.fetchval("SELECT COUNT(*) FROM purchase_orders")
        pending_orders = await conn.fetchval(
            "SELECT COUNT(*) FROM purchase_orders WHERE status IN ('pending_payment', 'payment_submitted', 'paid')"
        )

    if cb.message:
        await cb.message.answer(
            "Stats\n\n"
            f"Users: {int(users_count or 0)}\n"
            f"Orders total: {int(orders_count or 0)}\n"
            f"Orders open: {int(pending_orders or 0)}"
        )


async def redis_listener():
    redis = Redis.from_url(REDIS_URL, decode_responses=True)
    logger.info("worker started | redis=%s | stream=%s", REDIS_URL, REDIS_STREAM)

    last_id = "$"
    try:
        while True:
            try:
                result = await redis.xread(
                    {REDIS_STREAM: last_id},
                    block=REDIS_BLOCK_MS,
                    count=10,
                )
                if not result:
                    continue

                for _, messages in result:
                    for msg_id, payload in messages:
                        last_id = msg_id
                        logger.info("REDIS EVENT %s %s", msg_id, json.dumps(payload, ensure_ascii=False))

                        raw = payload.get("update")
                        if not raw:
                            logger.warning("REDIS EVENT %s missing update field", msg_id)
                            continue

                        try:
                            data = json.loads(raw)
                            update = types.Update(**data)
                            await dp.feed_update(bot, update)
                        except Exception:
                            logger.exception("failed processing msg_id=%s", msg_id)

            except Exception as e:
                logger.exception("redis listener error: %r", e)
                await asyncio.sleep(2)
    finally:
        await redis.aclose()


async def on_startup():
    await db.connect()


async def on_shutdown():
    await db.disconnect()


async def main():
    await on_startup()
    try:
        await redis_listener()
    finally:
        await on_shutdown()


if __name__ == "__main__":
    asyncio.run(main())