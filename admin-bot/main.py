"""
SLH SPARK SYSTEM â€” Super Admin Bot (@MY_SUPER_ADMIN_bot)
Central control panel: broadcast, airdrop, gift, users, payments, stats, studio.
Industry-grade: FSM flows, confirmation step, Railway DB, full audit logging.
"""
import os, sys, asyncio, logging, asyncpg, aiohttp
from datetime import datetime
from io import BytesIO
import math

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

sys.path.insert(0, "/app/shared")
from slh_payments import db as pay_db
from slh_payments.config import ADMIN_USER_ID, BOT_PRICING

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("slh.admin")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN missing")

RAILWAY_DB_URL = os.getenv("DATABASE_URL") or os.getenv("RAILWAY_DATABASE_URL")
AIRDROP_BOT_TOKEN = os.getenv("AIRDROP_BOT_TOKEN", "").strip()

# ── Control Center HTTP targets ─────────────────────────────────────
API_BASE             = os.getenv("SLH_API_BASE", "https://slh-api-production.up.railway.app")
SLH_ADMIN_API_KEY    = os.getenv("ADMIN_API_KEY", "slh_admin_2026_rotated_04_20")
SLH_BROADCAST_KEY    = os.getenv("ADMIN_BROADCAST_KEY", "slh-broadcast-2026-change-me")
GITHUB_API_REPO      = "https://api.github.com/repos/osifeu-prog/slh-api"
WEBSITE_OPS_BASE     = "https://slh-nft.com/ops"
OPS_VIEWER_BASE      = "https://slh-nft.com/ops-viewer.html?file="

bot = Bot(BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())

_db_pool: asyncpg.Pool | None = None

SKIP_IDS = {100001, 100002, 100003, 200001}

ECOSYSTEM_BOTS = {
    "academia": {"name": "SLH Academia",    "username": "SLH_Academia_bot",     "container": "slh-core-bot"},
    "guardian": {"name": "SLH Guardian",    "username": "Grdian_bot",            "container": "slh-guardian-bot"},
    "botshop":  {"name": "GATE BotShop",    "username": "Buy_My_Shop_bot",       "container": "slh-botshop"},
    "wallet":   {"name": "SLH Wallet",      "username": "SLH_Wallet_bot",        "container": "slh-wallet"},
    "factory":  {"name": "BOT Factory",     "username": "Osifs_Factory_bot",     "container": "slh-factory"},
    "community":{"name": "SLH Community",   "username": "SLH_community_bot",     "container": "slh-fun"},
}

TOKEN_EMOJIS = {"SLH": "ðŸ’Ž", "ZVK": "ðŸŸ¡", "MNH": "ðŸ”µ", "REP": "â­", "ZUZ": "ðŸ”´"}

# â”€â”€â”€ DB â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async def get_db() -> asyncpg.Pool:
    global _db_pool
    if _db_pool is None and RAILWAY_DB_URL:
        _db_pool = await asyncpg.create_pool(RAILWAY_DB_URL, min_size=1, max_size=5)
    return _db_pool

async def get_all_users():
    pool = await get_db()
    if not pool:
        return []
    rows = await pool.fetch(
        "SELECT telegram_id, first_name, username, is_registered "
        "FROM web_users WHERE telegram_id IS NOT NULL AND telegram_id > 0"
    )
    return [r for r in rows if r["telegram_id"] not in SKIP_IDS]

async def get_registered_users():
    return [u for u in await get_all_users() if u["is_registered"]]

async def credit_tokens(telegram_id: int, gifts: dict):
    pool = await get_db()
    if not pool:
        return
    for token, amount in gifts.items():
        await pool.execute("""
            INSERT INTO token_balances (user_id, token, balance, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (user_id, token) DO UPDATE
            SET balance = token_balances.balance + EXCLUDED.balance, updated_at = NOW()
        """, telegram_id, token, float(amount))

async def log_broadcast(total, sent, failed, preview, actor="admin_bot"):
    pool = await get_db()
    if not pool:
        return
    await pool.execute("""
        INSERT INTO broadcast_log
            (sent_at, target, total_targets, success_count, fail_count, message_preview, admin_actor)
        VALUES (NOW(), 'ALL_USERS', $1, $2, $3, $4, $5)
    """, total, sent, failed, preview[:200], actor)

# â”€â”€â”€ FSM States â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class BroadcastFlow(StatesGroup):
    target   = State()
    gift     = State()
    message  = State()
    confirm  = State()

class AirdropFlow(StatesGroup):
    target   = State()
    tokens   = State()
    confirm  = State()

class GiftFlow(StatesGroup):
    waiting  = State()

# â”€â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def is_admin(uid: int) -> bool:
    return uid == ADMIN_USER_ID

def target_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ðŸ‘¥ ×›×œ ×”×ž×©×ª×ž×©×™×",   callback_data="bc_target:all")],
        [InlineKeyboardButton(text="âœ… ×¨×©×•×ž×™× ×‘×œ×‘×“",   callback_data="bc_target:registered")],
        [InlineKeyboardButton(text="âŒ ×‘×™×˜×•×œ",          callback_data="bc_cancel")],
    ])

def gift_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ðŸŽ Airdrop ×™×•×ž×™ (0.12 SLH+8 ZVK+32 MNH+12 REP+100 ZUZ)", callback_data="bc_gift:daily")],
        [InlineKeyboardButton(text="ðŸ‡®ðŸ‡± ×™×•× ×¢×¦×ž××•×ª (78 ZVK + 78 REP)",                        callback_data="bc_gift:independence")],
        [InlineKeyboardButton(text="â­ REP ×‘×œ×‘×“ (+50)",                                       callback_data="bc_gift:rep50")],
        [InlineKeyboardButton(text="ðŸš« ×œ×œ× ×ž×ª× ×”",                                             callback_data="bc_gift:none")],
        [InlineKeyboardButton(text="âŒ ×‘×™×˜×•×œ",                                                 callback_data="bc_cancel")],
    ])

GIFT_PRESETS = {
    "daily":        {"SLH": 0.12, "ZVK": 8, "MNH": 32, "REP": 12, "ZUZ": 100},
    "independence": {"ZVK": 78, "REP": 78},
    "rep50":        {"REP": 50},
    "none":         {},
}

def gift_label(key: str) -> str:
    g = GIFT_PRESETS.get(key, {})
    if not g:
        return "×œ×œ× ×ž×ª× ×”"
    return " | ".join(f"{TOKEN_EMOJIS.get(t,'')}{t}+{v}" for t, v in g.items())

async def do_broadcast(users, message_text, gifts, actor="admin_bot"):
    if not AIRDROP_BOT_TOKEN:
        return 0, len(users), "AIRDROP_BOT_TOKEN missing"
    sent = failed = 0
    tg_api = f"https://api.telegram.org/bot{AIRDROP_BOT_TOKEN}"
    pool = await get_db()

    async with aiohttp.ClientSession() as session:
        for u in users:
            uid = u["telegram_id"]
            # Credit tokens first
            if pool and gifts:
                await credit_tokens(uid, gifts)
            # Send message
            try:
                async with session.post(
                    f"{tg_api}/sendMessage",
                    json={"chat_id": uid, "text": message_text, "parse_mode": "Markdown"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as r:
                    data = await r.json()
                    if data.get("ok"):
                        sent += 1
                    else:
                        failed += 1
            except Exception:
                failed += 1
            await asyncio.sleep(0.05)

    await log_broadcast(len(users), sent, failed, message_text[:200], actor)
    return sent, failed, None

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# /start
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@dp.message(Command("start"))
async def start_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        await m.answer("âŒ ×’×™×©×” ×œ××“×ž×™× ×™× ×‘×œ×‘×“.")
        return
    await m.answer(
        "```\n â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•—     â–ˆâ–ˆâ•—  â–ˆâ–ˆâ•—\n â–ˆâ–ˆâ•”â•â•â•â•â•â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ•‘  â–ˆâ–ˆâ•‘\n"
        " â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•‘\n â•šâ•â•â•â•â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ•”â•â•â•â•â–ˆâ–ˆâ•‘\n"
        " â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•‘  â–ˆâ–ˆâ•‘\n â•šâ•â•â•â•â•â•â•â•šâ•â•â•â•â•â•â•â•šâ•â•  â•šâ•â•\n```\n"
        "*SLH SPARK SYSTEM* â€” Mission Control ðŸš€\n\n"
        "ðŸ“£ *×©×™×“×•×¨×™×:*\n"
        "/broadcast â€” ×©×œ×— ×”×•×“×¢×” + ×ž×ª× ×” ×œ×›×•×œ×\n"
        "/airdrop   â€” ×—×œ×•×§×ª ×˜×•×§× ×™× ×ž×”×™×¨×”\n"
        "/gift      â€” ×ž×ª× ×” ×œ××“× ×¡×¤×¦×™×¤×™\n\n"
        "ðŸ“Š *× ×™×”×•×œ:*\n"
        "/dashboard â€” ×¡×§×™×¨×ª ×ž×¦×‘\n"
        "/payments  â€” ×ª×©×œ×•×ž×™× ×ž×ž×ª×™× ×™×\n"
        "/users     â€” ×¨×©×™×ž×ª ×ž×©×ª×ž×©×™×\n"
        "/stats     â€” ×¡×˜×˜×™×¡×˜×™×§×•×ª\n"
        "/bots      â€” ×¨×©×™×ž×ª ×‘×•×˜×™×\n"
        "/revenue   â€” ×“×•×— ×”×›× ×¡×•×ª\n\n"
        "ðŸŽ¨ *×›×œ×™×:*\n"
        "/studio    â€” Image Studio",
        parse_mode="Markdown",
    )

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# /broadcast â€” FSM flow: target â†’ gift â†’ message â†’ confirm â†’ send
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@dp.message(Command("broadcast"))
async def broadcast_start(m: types.Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    await state.clear()
    await state.set_state(BroadcastFlow.target)
    await m.answer("ðŸ“£ *×©×™×“×•×¨ ×—×“×©*\n\n×‘×—×¨ ×§×”×œ ×™×¢×“:", parse_mode="Markdown", reply_markup=target_kb())

@dp.callback_query(F.data.startswith("bc_target:"), BroadcastFlow.target)
async def bc_target(cb: types.CallbackQuery, state: FSMContext):
    target = cb.data.split(":")[1]
    await state.update_data(target=target)
    await state.set_state(BroadcastFlow.gift)
    label = "×›×œ ×”×ž×©×ª×ž×©×™×" if target == "all" else "×¨×©×•×ž×™× ×‘×œ×‘×“"
    await cb.message.edit_text(
        f"âœ… ×§×”×œ: *{label}*\n\n×‘×—×¨ ×ž×ª× ×” ×œ×¦×™×¨×•×£:",
        parse_mode="Markdown", reply_markup=gift_kb()
    )
    await cb.answer()

@dp.callback_query(F.data.startswith("bc_gift:"), BroadcastFlow.gift)
async def bc_gift(cb: types.CallbackQuery, state: FSMContext):
    gift_key = cb.data.split(":")[1]
    await state.update_data(gift_key=gift_key)
    await state.set_state(BroadcastFlow.message)
    await cb.message.edit_text(
        f"ðŸŽ ×ž×ª× ×”: *{gift_label(gift_key)}*\n\nâœï¸ ×›×¢×ª ×›×ª×•×‘ ××ª ×”×”×•×“×¢×”:",
        parse_mode="Markdown"
    )
    await cb.answer()

@dp.message(BroadcastFlow.message)
async def bc_message(m: types.Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    data = await state.get_data()
    target   = data["target"]
    gift_key = data["gift_key"]
    gifts    = GIFT_PRESETS[gift_key]

    users = await get_all_users() if target == "all" else await get_registered_users()

    await state.update_data(message=m.text, users_count=len(users))
    await state.set_state(BroadcastFlow.confirm)

    gift_str = gift_label(gift_key) if gifts else "×œ×œ× ×ž×ª× ×”"
    preview = m.text[:300] + ("..." if len(m.text) > 300 else "")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="âœ… ×©×œ×— ×¢×›×©×™×•",  callback_data="bc_confirm:yes")],
        [InlineKeyboardButton(text="âŒ ×‘×˜×œ",        callback_data="bc_confirm:no")],
    ])
    await m.answer(
        f"ðŸ“‹ *××™×©×•×¨ ×©×™×“×•×¨*\n\n"
        f"ðŸ‘¥ ×§×”×œ: {len(users)} ×ž×©×ª×ž×©×™×\n"
        f"ðŸŽ ×ž×ª× ×”: {gift_str}\n\n"
        f"ðŸ“ *×ª×¦×•×’×” ×ž×§×“×™×ž×”:*\n{preview}",
        parse_mode="Markdown", reply_markup=kb
    )

@dp.callback_query(F.data.startswith("bc_confirm:"), BroadcastFlow.confirm)
async def bc_confirm(cb: types.CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("âŒ")
        return
    if cb.data == "bc_confirm:no":
        await state.clear()
        await cb.message.edit_text("âŒ ×©×™×“×•×¨ ×‘×•×˜×œ.")
        return

    data    = await state.get_data()
    target  = data["target"]
    gift_key = data["gift_key"]
    message = data["message"]
    gifts   = GIFT_PRESETS[gift_key]
    users   = await get_all_users() if target == "all" else await get_registered_users()

    await cb.message.edit_text(f"â³ ×©×•×œ×— ×œ-{len(users)} ×ž×©×ª×ž×©×™×...")
    await cb.answer()

    # Build final message with gift info
    if gifts:
        gift_lines = "\n".join(f"â€¢ {TOKEN_EMOJIS.get(t,'')}{t}: +{v}" for t, v in gifts.items())
        full_msg = f"{message}\n\nðŸŽ *×ž×ª× ×” ×ž-SLH Spark:*\n{gift_lines}"
    else:
        full_msg = message

    sent, failed, err = await do_broadcast(users, full_msg, gifts, actor="admin_bot_broadcast")
    await state.clear()

    await cb.message.answer(
        f"âœ… *×©×™×“×•×¨ ×”×•×©×œ×!*\n\n"
        f"ðŸ‘¥ ×ž×©×ª×ž×©×™×: {len(users)}\n"
        f"ðŸ“¤ × ×©×œ×—: {sent}\n"
        f"âŒ × ×›×©×œ: {failed}" + (f"\nâš ï¸ {err}" if err else ""),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "bc_cancel")
async def bc_cancel(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("âŒ ×‘×•×˜×œ.")
    await cb.answer()

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# /airdrop â€” FSM: target â†’ preset gift â†’ confirm
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@dp.message(Command("airdrop"))
async def airdrop_start(m: types.Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    await state.clear()
    await state.set_state(AirdropFlow.target)
    await m.answer("ðŸ’° *Airdrop ×ž×”×™×¨*\n\n×‘×—×¨ ×§×”×œ:", parse_mode="Markdown", reply_markup=target_kb())

@dp.callback_query(F.data.startswith("bc_target:"), AirdropFlow.target)
async def airdrop_target(cb: types.CallbackQuery, state: FSMContext):
    target = cb.data.split(":")[1]
    await state.update_data(target=target)
    await state.set_state(AirdropFlow.tokens)
    await cb.message.edit_text(
        "ðŸ’° *×‘×—×¨ ×—×‘×™×œ×ª Airdrop:*",
        parse_mode="Markdown", reply_markup=gift_kb()
    )
    await cb.answer()

@dp.callback_query(F.data.startswith("bc_gift:"), AirdropFlow.tokens)
async def airdrop_tokens(cb: types.CallbackQuery, state: FSMContext):
    gift_key = cb.data.split(":")[1]
    gifts    = GIFT_PRESETS[gift_key]
    if not gifts:
        await cb.message.edit_text("âš ï¸ ×‘×—×¨×ª ×œ×œ× ×ž×ª× ×” â€” airdrop ×‘×•×˜×œ.")
        await state.clear()
        await cb.answer()
        return

    await state.update_data(gift_key=gift_key)
    data  = await state.get_data()
    users = await get_all_users() if data["target"] == "all" else await get_registered_users()

    await state.update_data(users_count=len(users))
    await state.set_state(AirdropFlow.confirm)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="âœ… ××©×¨ Airdrop", callback_data="ad_confirm:yes")],
        [InlineKeyboardButton(text="âŒ ×‘×˜×œ",          callback_data="ad_confirm:no")],
    ])
    await cb.message.edit_text(
        f"ðŸ’° *××™×©×•×¨ Airdrop*\n\n"
        f"ðŸ‘¥ ×ž×©×ª×ž×©×™×: {len(users)}\n"
        f"ðŸŽ {gift_label(gift_key)}\n\n"
        f"âš ï¸ ×¤×¢×•×œ×” ×–×• ×ª×›×ª×•×‘ ×œDB ×™×©×™×¨×•×ª.",
        parse_mode="Markdown", reply_markup=kb
    )
    await cb.answer()

@dp.callback_query(F.data.startswith("ad_confirm:"), AirdropFlow.confirm)
async def airdrop_confirm(cb: types.CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("âŒ")
        return
    if cb.data == "ad_confirm:no":
        await state.clear()
        await cb.message.edit_text("âŒ Airdrop ×‘×•×˜×œ.")
        return

    data     = await state.get_data()
    gift_key = data["gift_key"]
    target   = data["target"]
    gifts    = GIFT_PRESETS[gift_key]
    users    = await get_all_users() if target == "all" else await get_registered_users()

    await cb.message.edit_text(f"â³ ×ž×—×œ×§ ×œ-{len(users)} ×ž×©×ª×ž×©×™×...")
    await cb.answer()

    pool = await get_db()
    tx = 0
    for u in users:
        if pool:
            await credit_tokens(u["telegram_id"], gifts)
            tx += len(gifts)

    await log_broadcast(len(users), len(users), 0,
                        f"AIRDROP: {gift_label(gift_key)}", "admin_bot_airdrop")
    await state.clear()
    await cb.message.answer(
        f"âœ… *Airdrop ×”×•×©×œ×!*\n\n"
        f"ðŸ‘¥ ×ž×©×ª×ž×©×™×: {len(users)}\n"
        f"ðŸ’¾ ×¢×¡×§××•×ª: {tx}\n"
        f"ðŸŽ {gift_label(gift_key)}",
        parse_mode="Markdown"
    )

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# /gift <telegram_id|@username> <amount> <TOKEN>
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@dp.message(Command("gift"))
async def gift_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    parts = m.text.split()[1:]
    if len(parts) != 3:
        await m.answer("×©×™×ž×•×©: `/gift <telegram_id> <amount> <TOKEN>`\n×“×•×’×ž×”: `/gift 224223270 100 ZVK`",
                       parse_mode="Markdown")
        return
    try:
        uid    = int(parts[0])
        amount = float(parts[1])
        token  = parts[2].upper()
    except ValueError:
        await m.answer("âŒ ×¤×¨×ž×˜×¨×™× ×©×’×•×™×™×.")
        return

    pool = await get_db()
    if not pool:
        await m.answer("âŒ DB ×œ× ×–×ž×™×Ÿ.")
        return

    await credit_tokens(uid, {token: amount})
    bal = await pool.fetchval(
        "SELECT balance FROM token_balances WHERE user_id=$1 AND token=$2",
        uid, token
    )
    await m.answer(
        f"âœ… *×ž×ª× ×” × ×©×œ×—×”!*\n\n"
        f"ðŸ‘¤ ID: `{uid}`\n"
        f"ðŸŽ {TOKEN_EMOJIS.get(token,'')}{token}: +{amount}\n"
        f"ðŸ’° ×™×ª×¨×” ×—×“×©×”: {bal}",
        parse_mode="Markdown"
    )

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# /users â€” ×¨×©×™×ž×ª ×ž×©×ª×ž×©×™×
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@dp.message(Command("users"))
async def users_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    users = await get_all_users()
    reg   = [u for u in users if u["is_registered"]]
    lines = [f"ðŸ‘¥ *×ž×©×ª×ž×©×™× ({len(users)} ×¡×”\"×› | {len(reg)} ×¨×©×•×ž×™×)*\n"]
    for u in users:
        mark = "âœ…" if u["is_registered"] else "â³"
        name = u["first_name"] or u["username"] or "?"
        lines.append(f"{mark} {name} â€” `{u['telegram_id']}`")
    await m.answer("\n".join(lines), parse_mode="Markdown")

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# /dashboard, /payments, /stats, /bots, /revenue (unchanged core)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@dp.message(Command("dashboard"))
async def dashboard_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    stats = await pay_db.get_stats()
    pool  = await get_db()
    reg_count = 0
    if pool:
        reg_count = await pool.fetchval(
            "SELECT COUNT(*) FROM web_users WHERE is_registered=TRUE"
        ) or 0
    lines = [
        "ðŸ“Š *SLH SPARK DASHBOARD*\n",
        f"ðŸŒ ×¨×©×•×ž×™× ×‘××ª×¨: {reg_count}",
        f"ðŸ‘¥ ×ž×©×ª×ž×©×™× (legacy): {stats['total_users']}",
        f"âœ… ×ž××•×©×¨×™×: {stats['approved']}",
        f"â³ ×ž×ž×ª×™× ×™×: {stats['pending']}",
        f"ðŸ’° ×”×›× ×¡×•×ª: {stats['total_revenue']:.0f} â‚ª\n",
        "*×œ×¤×™ ×‘×•×˜:*",
    ]
    for row in stats["by_bot"]:
        lines.append(f"  â€¢ {row['bot_name']}: {row['cnt']} ×ž×©×ª×ž×©×™× | {float(row['revenue']):.0f} â‚ª")
    lines.append(f"\nâ° ×¢×“×›×•×Ÿ: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    await m.answer("\n".join(lines), parse_mode="Markdown")

@dp.message(Command("payments"))
async def payments_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    pending = await pay_db.get_pending_payments()
    if not pending:
        await m.answer("âœ… ××™×Ÿ ×ª×©×œ×•×ž×™× ×ž×ž×ª×™× ×™×!")
        return
    for p in pending[:10]:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="âœ… ××©×¨", callback_data=f"adm_approve:{p['id']}"),
            InlineKeyboardButton(text="âŒ ×“×—×”", callback_data=f"adm_reject:{p['id']}"),
        ]])
        text = (
            f"ðŸ’³ *×ª×©×œ×•× #{p['id']}*\n"
            f"×‘×•×˜: {p['bot_name']}\n"
            f"×ž×©×ª×ž×©: @{p['username'] or '?'} ({p['user_id']})\n"
            f"×¡×›×•×: {p['payment_amount']} {p['payment_currency']}\n"
            f"×ª××¨×™×š: {p['created_at'].strftime('%d/%m %H:%M') if p['created_at'] else '?'}"
        )
        if p.get("payment_proof_file_id"):
            try:
                await bot.send_photo(m.chat.id, p["payment_proof_file_id"],
                                     caption=text, parse_mode="Markdown", reply_markup=kb)
                continue
            except Exception:
                pass
        await m.answer(text + "\n(××™×Ÿ ×ª×ž×•× ×”)", parse_mode="Markdown", reply_markup=kb)
    if len(pending) > 10:
        await m.answer(f"×•×¢×•×“ {len(pending)-10} ×ª×©×œ×•×ž×™×...")

@dp.callback_query(F.data.startswith("adm_approve:"))
async def approve_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    pid    = int(cb.data.split(":")[1])
    result = await pay_db.approve_payment(pid, cb.from_user.id)
    if result:
        txt = f"âœ… ××•×©×¨ #{pid} | {result['bot_name']} | @{result.get('username','?')}"
        await (cb.message.edit_caption(caption=txt) if cb.message.photo
               else cb.message.edit_text(txt))
    await cb.answer("××•×©×¨!" if result else "×œ× × ×ž×¦×")

@dp.callback_query(F.data.startswith("adm_reject:"))
async def reject_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    pid    = int(cb.data.split(":")[1])
    result = await pay_db.reject_payment(pid, cb.from_user.id)
    if result:
        txt = f"âŒ × ×“×—×” #{pid} | @{result.get('username','?')}"
        await (cb.message.edit_caption(caption=txt) if cb.message.photo
               else cb.message.edit_text(txt))
    await cb.answer("× ×“×—×”")

@dp.message(Command("stats"))
async def stats_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    stats = await pay_db.get_stats()
    total_monthly = sum(BOT_PRICING[k].price_ils for k in BOT_PRICING)
    await m.answer(
        f"ðŸ“ˆ *×¡×˜×˜×™×¡×˜×™×§×•×ª*\n\n"
        f"×ž×©×ª×ž×©×™× ×¨×©×•×ž×™×: {stats['total_users']}\n"
        f"×ž×©×œ×ž×™×: {stats['approved']}\n"
        f"×ž×ž×ª×™× ×™×: {stats['pending']}\n"
        f"×”×›× ×¡×•×ª ×›×•×œ×œ: {stats['total_revenue']:.0f} â‚ª\n\n"
        f"×¤×•×˜× ×¦×™××œ/×ž×©×ª×ž×©: {total_monthly} â‚ª\n"
        f"×¤×•×˜× ×¦×™××œ/100 ×ž×©×ª×ž×©×™×: {total_monthly*100:,.0f} â‚ª",
        parse_mode="Markdown"
    )

@dp.message(Command("bots"))
async def bots_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    lines = ["ðŸ¤– *×¨×©×™×ž×ª ×‘×•×˜×™×*\n"]
    for key, info in ECOSYSTEM_BOTS.items():
        pricing = BOT_PRICING.get(key)
        price   = f"{pricing.price_ils}â‚ª" if pricing else "?"
        lines.append(f"â€¢ *{info['name']}* @{info['username']} | {price}")
    lines.append(f"\n×¡×”\"×› ×‘×•×˜×™× ×¤×¢×™×œ×™×: {len(ECOSYSTEM_BOTS)}")
    await m.answer("\n".join(lines), parse_mode="Markdown")

@dp.message(Command("revenue"))
async def revenue_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    stats = await pay_db.get_stats()
    lines = ["ðŸ’° *×“×•×— ×”×›× ×¡×•×ª*\n"]
    for row in stats["by_bot"]:
        lines.append(f"â€¢ {row['bot_name']}: {float(row['revenue']):.0f} â‚ª ({row['cnt']} ×ž×©×ª×ž×©×™×)")
    lines.append(f"\n*×¡×”\"×›: {stats['total_revenue']:.0f} â‚ª*")
    await m.answer("\n".join(lines), parse_mode="Markdown")

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Access requests callbacks (unchanged)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@dp.message(Command("requests"))
async def access_requests_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    pending = await pay_db.get_pending_access_requests()
    if not pending:
        await m.answer("âœ… ××™×Ÿ ×‘×§×©×•×ª ×’×™×©×” ×ž×ž×ª×™× ×•×ª!")
        return
    for p in pending[:10]:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="âœ… ××©×¨", callback_data=f"acc_ok:{p['id']}"),
            InlineKeyboardButton(text="âŒ ×“×—×”", callback_data=f"acc_no:{p['id']}"),
        ]])
        text = (
            f"ðŸ“‹ ×‘×§×©×ª ×’×™×©×” #{p['id']}\n"
            f"×ž×©×ª×ž×©: @{p.get('username') or '?'} ({p['user_id']})\n"
            f"×‘×•×˜: {p['bot_name']}\n"
            f"×¡×™×‘×”: {p.get('reason') or '-'}\n"
            f"×ª××¨×™×š: {str(p.get('created_at',''))[:16]}"
        )
        if p.get("receipt_file_id"):
            try:
                await bot.send_photo(m.chat.id, p["receipt_file_id"], caption=text, reply_markup=kb)
                continue
            except Exception:
                pass
        await m.answer(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("acc_ok:"))
async def approve_access_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    result = await pay_db.approve_access(int(cb.data.split(":")[1]))
    if result:
        try:
            await bot.send_message(result["user_id"],
                "âœ… ×‘×§×©×ª ×”×’×™×©×” ×©×œ×š ××•×©×¨×”!\n×›×œ ×”×¤×™×¦'×¨×™× ×–×ž×™× ×™× ×¢×‘×•×¨×š. ðŸš€")
        except Exception:
            pass
        await cb.message.edit_text(f"âœ… ××•×©×¨ | @{result.get('username','?')}")
    await cb.answer("âœ…")

@dp.callback_query(F.data.startswith("acc_no:"))
async def reject_access_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    result = await pay_db.reject_access(int(cb.data.split(":")[1]))
    if result:
        try:
            await bot.send_message(result["user_id"],
                "âŒ ×‘×§×©×ª ×”×’×™×©×” × ×“×—×ª×”.\n×œ×¤×¨×˜×™×: /premium")
        except Exception:
            pass
        await cb.message.edit_text(f"âŒ × ×“×—×” | @{result.get('username','?')}")
    await cb.answer("âŒ")

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Image Studio (unchanged logic, refactored strings)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
user_image_mode = {}

@dp.message(Command("studio"))
@dp.message(Command("resize"))
async def studio_menu(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ðŸ“· ×©×™× ×•×™ ×’×•×“×œ", callback_data="studio:resize_menu")],
        [InlineKeyboardButton(text="ðŸŽ¬ ×™×¦×™×¨×ª GIF",  callback_data="studio:gif_menu")],
    ])
    await m.answer("ðŸŽ¨ *SLH Image Studio*\n\n×‘×—×¨ ×ž×” ×œ×¢×©×•×ª:", parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data == "studio:resize_menu")
async def resize_menu(cb: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="640x360 (BotFather)",  callback_data="studio:set_resize:640x360")],
        [InlineKeyboardButton(text="320x320 (Bot Profile)", callback_data="studio:set_resize:320x320")],
        [InlineKeyboardButton(text="512x512 (Sticker)",     callback_data="studio:set_resize:512x512")],
        [InlineKeyboardButton(text="1280x720 (HD)",         callback_data="studio:set_resize:1280x720")],
        [InlineKeyboardButton(text="1080x1080 (Instagram)", callback_data="studio:set_resize:1080x1080")],
        [InlineKeyboardButton(text="ðŸ“· ×›×œ ×”×’×“×œ×™×",         callback_data="studio:set_resize:all")],
    ])
    await cb.message.answer("ðŸ“· *×©×™× ×•×™ ×’×•×“×œ*\n\n×‘×—×¨ ×’×•×“×œ, ××—×¨ ×›×š ×©×œ×— ×ª×ž×•× ×”:", parse_mode="Markdown", reply_markup=kb)
    await cb.answer()

@dp.callback_query(F.data == "studio:gif_menu")
async def gif_menu(cb: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ðŸŒ€ Zoom",    callback_data="studio:set_gif:zoom")],
        [InlineKeyboardButton(text="ðŸ’« Pulse",   callback_data="studio:set_gif:pulse")],
        [InlineKeyboardButton(text="ðŸŒŠ Wave",    callback_data="studio:set_gif:wave")],
        [InlineKeyboardButton(text="âœ¨ Sparkle", callback_data="studio:set_gif:sparkle")],
        [InlineKeyboardButton(text="ðŸ”„ Rotate",  callback_data="studio:set_gif:rotate")],
        [InlineKeyboardButton(text="ðŸŽ¬ ×›×œ ×”×× ×™×ž×¦×™×•×ª", callback_data="studio:set_gif:all")],
    ])
    await cb.message.answer("ðŸŽ¬ *×™×¦×™×¨×ª GIF*\n\n×‘×—×¨ ×¡×’× ×•×Ÿ:", parse_mode="Markdown", reply_markup=kb)
    await cb.answer()

@dp.callback_query(F.data.startswith("studio:set_"))
async def set_mode(cb: types.CallbackQuery):
    mode = cb.data.replace("studio:set_", "")
    user_image_mode[cb.from_user.id] = mode
    await cb.message.answer(f"âœ… ×ž×•×“ × ×‘×—×¨: `{mode}`\n\nðŸ“· ×¢×›×©×™×• ×©×œ×— ×ª×ž×•× ×”!", parse_mode="Markdown")
    await cb.answer()

@dp.message(F.photo)
async def handle_photo(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    mode = user_image_mode.get(m.from_user.id, "")
    if not mode:
        await m.answer("ðŸ“· ×©×œ×—×ª ×ª×ž×•× ×”! ××‘×œ ×§×•×“× ×‘×—×¨ ×ž×” ×œ×¢×©×•×ª:\n/studio")
        return
    try:
        from PIL import Image, ImageEnhance
        from aiogram.types import BufferedInputFile

        photo = m.photo[-1]
        file  = await bot.get_file(photo.file_id)
        data  = await bot.download_file(file.file_path)
        img   = Image.open(BytesIO(data.read())).convert("RGB")
        await m.answer("â³ ×ž×¢×‘×“...")

        if mode.startswith("resize:"):
            size_key = mode.split(":")[1]
            sizes = {"640x360":(640,360),"320x320":(320,320),"512x512":(512,512),
                     "1280x720":(1280,720),"1080x1080":(1080,1080)}
            targets = sizes.items() if size_key == "all" else [(size_key, sizes.get(size_key,(640,360)))]
            for name, sz in targets:
                buf = BytesIO()
                img.copy().resize(sz, Image.LANCZOS).save(buf, format="PNG")
                buf.seek(0)
                await m.answer_document(BufferedInputFile(buf.read(), f"slh_{name}.png"), caption=f"âœ… {name}")

        elif mode.startswith("gif:"):
            effect    = mode.split(":")[1]
            to_run    = [effect] if effect != "all" else ["zoom","pulse","wave","sparkle","rotate"]
            eff_names = {"zoom":"ðŸŒ€ Zoom","pulse":"ðŸ’« Pulse","wave":"ðŸŒŠ Wave","sparkle":"âœ¨ Sparkle","rotate":"ðŸ”„ Rotate"}
            for eff in to_run:
                frames, n = [], 20
                if eff == "zoom":
                    for i in range(n):
                        s  = 1.0 + 0.04 * math.sin(i*2*math.pi/n)
                        w, h = int(640*s), int(360*s)
                        f  = img.copy().resize((w,h), Image.LANCZOS)
                        frames.append(f.crop(((w-640)//2,(h-360)//2,(w-640)//2+640,(h-360)//2+360)))
                elif eff == "pulse":
                    for i in range(n):
                        f = ImageEnhance.Brightness(img.copy().resize((640,360),Image.LANCZOS)).enhance(1.0+0.3*math.sin(i*2*math.pi/n))
                        frames.append(f)
                elif eff == "wave":
                    base = img.copy().resize((700,400),Image.LANCZOS)
                    for i in range(n):
                        ox, oy = int(30*math.sin(i*2*math.pi/n)), int(20*math.cos(i*2*math.pi/n))
                        frames.append(base.crop((30+ox,20+oy,30+ox+640,20+oy+360)))
                elif eff == "sparkle":
                    for i in range(n):
                        f = ImageEnhance.Color(ImageEnhance.Contrast(img.copy().resize((640,360),Image.LANCZOS)).enhance(1.0+0.4*math.sin(i*4*math.pi/n))).enhance(1.0+0.2*math.cos(i*2*math.pi/n))
                        frames.append(f)
                elif eff == "rotate":
                    base = img.copy().resize((450,450),Image.LANCZOS)
                    for i in range(n):
                        f = base.rotate(i*(360/n),expand=False,fillcolor=(0,0,0))
                        frames.append(f.crop((65,65,385,385)))
                if frames:
                    buf = BytesIO()
                    frames[0].save(buf,format="GIF",save_all=True,append_images=frames[1:],duration=80,loop=0)
                    buf.seek(0)
                    await m.answer_document(BufferedInputFile(buf.read(),f"slh_{eff}.gif"), caption=f"ðŸŽ¬ {eff_names.get(eff,eff)}")

        user_image_mode.pop(m.from_user.id, None)
        await m.answer("âœ… ×¡×™×™×ž×ª×™! ×œ×¢×•×“: /studio")
    except Exception as e:
        await m.answer(f"âŒ ×©×’×™××”: {e}")

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Main
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ====================================================================
# Control Center commands (added 2026-04-25)
# 8 read-only commands - system status console for Osif (whitelist gated)
# ====================================================================

async def _http_get(url, headers=None, timeout=10):
    """Fetch JSON or text with safe error handling."""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers=headers or {}, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                ct = r.headers.get("Content-Type", "")
                if "application/json" in ct:
                    return r.status, await r.json()
                return r.status, await r.text()
    except Exception as e:
        return 0, str(e)[:200]


def _md_escape(s):
    if not isinstance(s, str):
        return str(s)
    return s.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`").replace("[", "\\[")


@dp.message(Command("status"))
async def control_status_cmd(m):
    if not is_admin(m.from_user.id):
        return
    await m.answer("⏳ מאסף נתונים...")

    sc1, health = await _http_get(f"{API_BASE}/api/health")
    health_line = (
        f"v{health.get('version','?')} db={health.get('db','?')}"
        if isinstance(health, dict) else f"err {sc1}"
    )

    sc2, mini = await _http_get(f"{API_BASE}/api/miniapp/health")
    bot_token_set = mini.get("primary_bot_token_set", False) if isinstance(mini, dict) else False

    sc3, reality = await _http_get(
        f"{API_BASE}/api/ops/reality",
        headers={"X-Broadcast-Key": SLH_BROADCAST_KEY}
    )
    users_obj = reality.get("users", {}) if isinstance(reality, dict) else {}
    founders = len(users_obj.get("founders", []) or [])
    community = len(users_obj.get("community", []) or [])
    payments_count = len(reality.get("payments", []) or []) if isinstance(reality, dict) else 0

    sc4, devs = await _http_get(
        f"{API_BASE}/api/admin/devices/list",
        headers={"X-Admin-Key": SLH_ADMIN_API_KEY}
    )
    if isinstance(devs, dict):
        d_list = devs.get("devices", []) if isinstance(devs.get("devices"), list) else []
    elif isinstance(devs, list):
        d_list = devs
    else:
        d_list = []
    devices_count = len(d_list)

    sc5, ev = await _http_get(
        f"{API_BASE}/api/admin/events?limit=1",
        headers={"X-Admin-Key": SLH_ADMIN_API_KEY}
    )
    total_events = ev.get("total_events", "?") if isinstance(ev, dict) else "?"
    events_24h = ev.get("events_24h_by_type", {}) if isinstance(ev, dict) else {}
    events_24h_summary = ", ".join(f"{k}={v}" for k, v in list(events_24h.items())[:3]) or "--"

    bot_token_emoji = "🟢" if bot_token_set else "🟡"

    text = (
        "📊 *SLH STATUS*\n"
        "\n"
        f"🟢 API: {health_line}\n"
        f"{bot_token_emoji} Mini-App: token_set={bot_token_set}\n"
        "\n"
        f"👥 Users: {founders} founders + {community} community\n"
        f"💰 Revenue: ₪0 (אין לקוח משלם)\n"
        f"📟 Devices: {devices_count}\n"
        f"📜 Events lifetime: {total_events}\n"
        f"📜 Events 24h: {events_24h_summary}\n"
        f"💳 Payments: {payments_count}\n"
        "\n"
        f"🔗 [CONTROL]({OPS_VIEWER_BASE}CONTROL.md) | "
        f"[Agents]({OPS_VIEWER_BASE}SYSTEM_ALIGNMENT_20260424.md)"
    )
    await m.answer(text, parse_mode="Markdown", disable_web_page_preview=True)


@dp.message(Command("control"))
async def control_links_cmd(m):
    if not is_admin(m.from_user.id):
        return
    await m.answer(
        "🎯 *Control Center*\n"
        "\n"
        f"📋 [CONTROL.md]({OPS_VIEWER_BASE}CONTROL.md)\n"
        f"📡 [Agents alignment]({OPS_VIEWER_BASE}SYSTEM_ALIGNMENT_20260424.md)\n"
        f"👤 [Customer prospectus DEMO]({OPS_VIEWER_BASE}CUSTOMER_PROSPECTUS_DEMO.md)\n"
        f"🛠 [Ops runbook]({OPS_VIEWER_BASE}OPS_RUNBOOK.md)\n"
        f"📨 [Followup templates]({OPS_VIEWER_BASE}FOLLOWUP_TEMPLATES.md)\n"
        f"🧪 [Test payment guide]({OPS_VIEWER_BASE}TEST_PAYMENT_GUIDE.md)\n"
        "\n"
        f"🌐 [Website](https://slh-nft.com)\n"
        f"⚡ [Mission Control](https://slh-nft.com/admin/mission-control.html)",
        parse_mode="Markdown", disable_web_page_preview=True
    )


@dp.message(Command("agents"))
async def control_agents_cmd(m):
    if not is_admin(m.from_user.id):
        return
    sc, txt = await _http_get(f"{WEBSITE_OPS_BASE}/SYSTEM_ALIGNMENT_20260424.md")
    if sc != 200 or not isinstance(txt, str):
        await m.answer(f"❌ alignment HTTP {sc}")
        return
    agents = []
    for line in txt.split("\n"):
        if line.startswith("### Agent:"):
            agents.append(line.replace("### Agent:", "").strip()[:90])
    if not agents:
        await m.answer("📡 No agents registered")
        return
    body = "\n".join(f"- {_md_escape(a)}" for a in agents[:15])
    await m.answer(f"📡 *Active agents:*\n\n{body}", parse_mode="Markdown")


@dp.message(Command("devices"))
async def control_devices_cmd(m):
    if not is_admin(m.from_user.id):
        return
    sc, dev = await _http_get(
        f"{API_BASE}/api/admin/devices/list",
        headers={"X-Admin-Key": SLH_ADMIN_API_KEY}
    )
    if sc != 200:
        await m.answer(f"❌ HTTP {sc}: {str(dev)[:200]}")
        return
    devices = dev.get("devices", []) if isinstance(dev, dict) else (dev if isinstance(dev, list) else [])
    if not devices:
        await m.answer("📟 No devices")
        return
    lines = ["📟 *ESP32 Fleet:*\n"]
    for d in devices[:10]:
        last = (d.get("last_seen") or "--")[:19]
        paired = d.get("paired_user_id") or "--"
        did = _md_escape(d.get("device_id", "?"))
        lines.append(f"- `{did}` last={last} user={paired}")
    if len(devices) > 10:
        lines.append(f"\n_+ {len(devices) - 10} more_")
    await m.answer("\n".join(lines), parse_mode="Markdown")


@dp.message(Command("git_log"))
async def control_git_cmd(m):
    if not is_admin(m.from_user.id):
        return
    sc, commits = await _http_get(
        f"{GITHUB_API_REPO}/commits?per_page=5",
        headers={"Accept": "application/vnd.github.v3+json"}
    )
    if sc != 200 or not isinstance(commits, list):
        await m.answer(f"❌ GitHub HTTP {sc}")
        return
    lines = ["📦 *Last 5 commits (slh-api master):*\n"]
    for c in commits[:5]:
        sha = c.get("sha", "")[:7]
        full_msg = c.get("commit", {}).get("message", "?").split("\n")[0][:60]
        date = c.get("commit", {}).get("author", {}).get("date", "")[:10]
        lines.append(f"- `{sha}` _{date}_\n  {_md_escape(full_msg)}")
    await m.answer("\n".join(lines), parse_mode="Markdown")


@dp.message(Command("audit_status"))
async def control_audit_cmd(m):
    if not is_admin(m.from_user.id):
        return
    await m.answer(
        "🔍 *Data Integrity Audit*\n"
        "\n"
        "Last logged state:\n"
        "- HIGH: 1 (slh-skeleton.js lib default - legit)\n"
        "- MED: 306 (`|| 0` benign)\n"
        "- LOW: 327\n"
        "\n"
        "Fresh run (PowerShell):\n"
        "`python scripts/audit_data_integrity.py --severity HIGH`",
        parse_mode="Markdown"
    )


@dp.message(Command("customer"))
async def control_customer_cmd(m):
    if not is_admin(m.from_user.id):
        return
    targets = [
        (1185887485, "Tzvika"),
        (8088324234, "Eliezer"),
        (590733872,  "Yaara"),
        (920721513,  "Rami"),
        (480100522,  "Zohar"),
        (1518680802, "Idan"),
    ]
    lines = ["👥 *Outreach status:*\n"]
    for tid, name in targets:
        lines.append(f"- {name} (`{tid}`) bot DM 22.4")
    lines.append("\n_WhatsApp personal: Yaara 24.4 | others pending_")
    lines.append(f"\n📋 Followups: {OPS_VIEWER_BASE}FOLLOWUP_TEMPLATES.md")
    await m.answer("\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)


@dp.message(Command("help_control"))
async def control_help_cmd(m):
    if not is_admin(m.from_user.id):
        return
    await m.answer(
        "🎯 *Control Commands*\n"
        "\n"
        "/status        - system snapshot\n"
        "/control       - links to ops docs\n"
        "/agents        - active agents\n"
        "/devices       - ESP32 fleet\n"
        "/git_log       - 5 last commits\n"
        "/audit_status  - audit findings\n"
        "/customer      - outreach status\n"
        "/help_control  - this menu\n"
        "\n"
        "_All commands whitelisted to admin only._",
        parse_mode="Markdown"
    )


async def main():
    await pay_db.init_schema()
    try:
        pool = await get_db()
        if pool:
            logger.info("Railway DB connected âœ…")
        else:
            logger.warning("Railway DB not configured â€” token ops disabled")
    except Exception as e:
        logger.warning(f"Railway DB init failed: {e}")
    logger.info("=" * 50)
    logger.info("SLH SPARK SYSTEM | Super Admin Bot â€” READY")
    logger.info("=" * 50)
    # Coordination: register inbound + post ready (no-op if env unset)
    try:
        from shared.coordination import init_coordination_for_bot
        me = await bot.get_me()
        await init_coordination_for_bot(
            bot, dp,
            name="admin-bot",
            username=me.username,
        )
    except Exception as e:
        logger.warning("coordination init failed: %s", e)

    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
