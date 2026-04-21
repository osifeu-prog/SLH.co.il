"""
SLH SPARK SYSTEM — Super Admin Bot (@MY_SUPER_ADMIN_bot)
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

TOKEN_EMOJIS = {"SLH": "💎", "ZVK": "🟡", "MNH": "🔵", "REP": "⭐", "ZUZ": "🔴"}

# ─── DB ───────────────────────────────────────────────────────
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

# ─── FSM States ───────────────────────────────────────────────
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

# ─── Helpers ──────────────────────────────────────────────────
def is_admin(uid: int) -> bool:
    return uid == ADMIN_USER_ID

def target_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 כל המשתמשים",   callback_data="bc_target:all")],
        [InlineKeyboardButton(text="✅ רשומים בלבד",   callback_data="bc_target:registered")],
        [InlineKeyboardButton(text="❌ ביטול",          callback_data="bc_cancel")],
    ])

def gift_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Airdrop יומי (0.12 SLH+8 ZVK+32 MNH+12 REP+100 ZUZ)", callback_data="bc_gift:daily")],
        [InlineKeyboardButton(text="🇮🇱 יום עצמאות (78 ZVK + 78 REP)",                        callback_data="bc_gift:independence")],
        [InlineKeyboardButton(text="⭐ REP בלבד (+50)",                                       callback_data="bc_gift:rep50")],
        [InlineKeyboardButton(text="🚫 ללא מתנה",                                             callback_data="bc_gift:none")],
        [InlineKeyboardButton(text="❌ ביטול",                                                 callback_data="bc_cancel")],
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
        return "ללא מתנה"
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

# ═══════════════════════════════════════════════════════════════
# /start
# ═══════════════════════════════════════════════════════════════
@dp.message(Command("start"))
async def start_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        await m.answer("❌ גישה לאדמינים בלבד.")
        return
    await m.answer(
        "```\n ███████╗██╗     ██╗  ██╗\n ██╔════╝██║     ██║  ██║\n"
        " ███████╗██║     ████████║\n ╚════██║██║     ██╔════██║\n"
        " ███████║███████╗██║  ██║\n ╚══════╝╚══════╝╚═╝  ╚═╝\n```\n"
        "*SLH SPARK SYSTEM* — Mission Control 🚀\n\n"
        "📣 *שידורים:*\n"
        "/broadcast — שלח הודעה + מתנה לכולם\n"
        "/airdrop   — חלוקת טוקנים מהירה\n"
        "/gift      — מתנה לאדם ספציפי\n\n"
        "📊 *ניהול:*\n"
        "/dashboard — סקירת מצב\n"
        "/payments  — תשלומים ממתינים\n"
        "/users     — רשימת משתמשים\n"
        "/stats     — סטטיסטיקות\n"
        "/bots      — רשימת בוטים\n"
        "/revenue   — דוח הכנסות\n\n"
        "🎨 *כלים:*\n"
        "/studio    — Image Studio",
        parse_mode="Markdown",
    )

# ═══════════════════════════════════════════════════════════════
# /broadcast — FSM flow: target → gift → message → confirm → send
# ═══════════════════════════════════════════════════════════════
@dp.message(Command("broadcast"))
async def broadcast_start(m: types.Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    await state.clear()
    await state.set_state(BroadcastFlow.target)
    await m.answer("📣 *שידור חדש*\n\nבחר קהל יעד:", parse_mode="Markdown", reply_markup=target_kb())

@dp.callback_query(F.data.startswith("bc_target:"), BroadcastFlow.target)
async def bc_target(cb: types.CallbackQuery, state: FSMContext):
    target = cb.data.split(":")[1]
    await state.update_data(target=target)
    await state.set_state(BroadcastFlow.gift)
    label = "כל המשתמשים" if target == "all" else "רשומים בלבד"
    await cb.message.edit_text(
        f"✅ קהל: *{label}*\n\nבחר מתנה לצירוף:",
        parse_mode="Markdown", reply_markup=gift_kb()
    )
    await cb.answer()

@dp.callback_query(F.data.startswith("bc_gift:"), BroadcastFlow.gift)
async def bc_gift(cb: types.CallbackQuery, state: FSMContext):
    gift_key = cb.data.split(":")[1]
    await state.update_data(gift_key=gift_key)
    await state.set_state(BroadcastFlow.message)
    await cb.message.edit_text(
        f"🎁 מתנה: *{gift_label(gift_key)}*\n\n✍️ כעת כתוב את ההודעה:",
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

    gift_str = gift_label(gift_key) if gifts else "ללא מתנה"
    preview = m.text[:300] + ("..." if len(m.text) > 300 else "")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ שלח עכשיו",  callback_data="bc_confirm:yes")],
        [InlineKeyboardButton(text="❌ בטל",        callback_data="bc_confirm:no")],
    ])
    await m.answer(
        f"📋 *אישור שידור*\n\n"
        f"👥 קהל: {len(users)} משתמשים\n"
        f"🎁 מתנה: {gift_str}\n\n"
        f"📝 *תצוגה מקדימה:*\n{preview}",
        parse_mode="Markdown", reply_markup=kb
    )

@dp.callback_query(F.data.startswith("bc_confirm:"), BroadcastFlow.confirm)
async def bc_confirm(cb: types.CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("❌")
        return
    if cb.data == "bc_confirm:no":
        await state.clear()
        await cb.message.edit_text("❌ שידור בוטל.")
        return

    data    = await state.get_data()
    target  = data["target"]
    gift_key = data["gift_key"]
    message = data["message"]
    gifts   = GIFT_PRESETS[gift_key]
    users   = await get_all_users() if target == "all" else await get_registered_users()

    await cb.message.edit_text(f"⏳ שולח ל-{len(users)} משתמשים...")
    await cb.answer()

    # Build final message with gift info
    if gifts:
        gift_lines = "\n".join(f"• {TOKEN_EMOJIS.get(t,'')}{t}: +{v}" for t, v in gifts.items())
        full_msg = f"{message}\n\n🎁 *מתנה מ-SLH Spark:*\n{gift_lines}"
    else:
        full_msg = message

    sent, failed, err = await do_broadcast(users, full_msg, gifts, actor="admin_bot_broadcast")
    await state.clear()

    await cb.message.answer(
        f"✅ *שידור הושלם!*\n\n"
        f"👥 משתמשים: {len(users)}\n"
        f"📤 נשלח: {sent}\n"
        f"❌ נכשל: {failed}" + (f"\n⚠️ {err}" if err else ""),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "bc_cancel")
async def bc_cancel(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("❌ בוטל.")
    await cb.answer()

# ═══════════════════════════════════════════════════════════════
# /airdrop — FSM: target → preset gift → confirm
# ═══════════════════════════════════════════════════════════════
@dp.message(Command("airdrop"))
async def airdrop_start(m: types.Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    await state.clear()
    await state.set_state(AirdropFlow.target)
    await m.answer("💰 *Airdrop מהיר*\n\nבחר קהל:", parse_mode="Markdown", reply_markup=target_kb())

@dp.callback_query(F.data.startswith("bc_target:"), AirdropFlow.target)
async def airdrop_target(cb: types.CallbackQuery, state: FSMContext):
    target = cb.data.split(":")[1]
    await state.update_data(target=target)
    await state.set_state(AirdropFlow.tokens)
    await cb.message.edit_text(
        "💰 *בחר חבילת Airdrop:*",
        parse_mode="Markdown", reply_markup=gift_kb()
    )
    await cb.answer()

@dp.callback_query(F.data.startswith("bc_gift:"), AirdropFlow.tokens)
async def airdrop_tokens(cb: types.CallbackQuery, state: FSMContext):
    gift_key = cb.data.split(":")[1]
    gifts    = GIFT_PRESETS[gift_key]
    if not gifts:
        await cb.message.edit_text("⚠️ בחרת ללא מתנה — airdrop בוטל.")
        await state.clear()
        await cb.answer()
        return

    await state.update_data(gift_key=gift_key)
    data  = await state.get_data()
    users = await get_all_users() if data["target"] == "all" else await get_registered_users()

    await state.update_data(users_count=len(users))
    await state.set_state(AirdropFlow.confirm)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ אשר Airdrop", callback_data="ad_confirm:yes")],
        [InlineKeyboardButton(text="❌ בטל",          callback_data="ad_confirm:no")],
    ])
    await cb.message.edit_text(
        f"💰 *אישור Airdrop*\n\n"
        f"👥 משתמשים: {len(users)}\n"
        f"🎁 {gift_label(gift_key)}\n\n"
        f"⚠️ פעולה זו תכתוב לDB ישירות.",
        parse_mode="Markdown", reply_markup=kb
    )
    await cb.answer()

@dp.callback_query(F.data.startswith("ad_confirm:"), AirdropFlow.confirm)
async def airdrop_confirm(cb: types.CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("❌")
        return
    if cb.data == "ad_confirm:no":
        await state.clear()
        await cb.message.edit_text("❌ Airdrop בוטל.")
        return

    data     = await state.get_data()
    gift_key = data["gift_key"]
    target   = data["target"]
    gifts    = GIFT_PRESETS[gift_key]
    users    = await get_all_users() if target == "all" else await get_registered_users()

    await cb.message.edit_text(f"⏳ מחלק ל-{len(users)} משתמשים...")
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
        f"✅ *Airdrop הושלם!*\n\n"
        f"👥 משתמשים: {len(users)}\n"
        f"💾 עסקאות: {tx}\n"
        f"🎁 {gift_label(gift_key)}",
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════════════════════════════
# /gift <telegram_id|@username> <amount> <TOKEN>
# ═══════════════════════════════════════════════════════════════
@dp.message(Command("gift"))
async def gift_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    parts = m.text.split()[1:]
    if len(parts) != 3:
        await m.answer("שימוש: `/gift <telegram_id> <amount> <TOKEN>`\nדוגמה: `/gift 224223270 100 ZVK`",
                       parse_mode="Markdown")
        return
    try:
        uid    = int(parts[0])
        amount = float(parts[1])
        token  = parts[2].upper()
    except ValueError:
        await m.answer("❌ פרמטרים שגויים.")
        return

    pool = await get_db()
    if not pool:
        await m.answer("❌ DB לא זמין.")
        return

    await credit_tokens(uid, {token: amount})
    bal = await pool.fetchval(
        "SELECT balance FROM token_balances WHERE user_id=$1 AND token=$2",
        uid, token
    )
    await m.answer(
        f"✅ *מתנה נשלחה!*\n\n"
        f"👤 ID: `{uid}`\n"
        f"🎁 {TOKEN_EMOJIS.get(token,'')}{token}: +{amount}\n"
        f"💰 יתרה חדשה: {bal}",
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════════════════════════════
# /users — רשימת משתמשים
# ═══════════════════════════════════════════════════════════════
@dp.message(Command("users"))
async def users_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    users = await get_all_users()
    reg   = [u for u in users if u["is_registered"]]
    lines = [f"👥 *משתמשים ({len(users)} סה\"כ | {len(reg)} רשומים)*\n"]
    for u in users:
        mark = "✅" if u["is_registered"] else "⏳"
        name = u["first_name"] or u["username"] or "?"
        lines.append(f"{mark} {name} — `{u['telegram_id']}`")
    await m.answer("\n".join(lines), parse_mode="Markdown")

# ═══════════════════════════════════════════════════════════════
# /dashboard, /payments, /stats, /bots, /revenue (unchanged core)
# ═══════════════════════════════════════════════════════════════
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
        "📊 *SLH SPARK DASHBOARD*\n",
        f"🌐 רשומים באתר: {reg_count}",
        f"👥 משתמשים (legacy): {stats['total_users']}",
        f"✅ מאושרים: {stats['approved']}",
        f"⏳ ממתינים: {stats['pending']}",
        f"💰 הכנסות: {stats['total_revenue']:.0f} ₪\n",
        "*לפי בוט:*",
    ]
    for row in stats["by_bot"]:
        lines.append(f"  • {row['bot_name']}: {row['cnt']} משתמשים | {float(row['revenue']):.0f} ₪")
    lines.append(f"\n⏰ עדכון: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    await m.answer("\n".join(lines), parse_mode="Markdown")

@dp.message(Command("payments"))
async def payments_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    pending = await pay_db.get_pending_payments()
    if not pending:
        await m.answer("✅ אין תשלומים ממתינים!")
        return
    for p in pending[:10]:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ אשר", callback_data=f"adm_approve:{p['id']}"),
            InlineKeyboardButton(text="❌ דחה", callback_data=f"adm_reject:{p['id']}"),
        ]])
        text = (
            f"💳 *תשלום #{p['id']}*\n"
            f"בוט: {p['bot_name']}\n"
            f"משתמש: @{p['username'] or '?'} ({p['user_id']})\n"
            f"סכום: {p['payment_amount']} {p['payment_currency']}\n"
            f"תאריך: {p['created_at'].strftime('%d/%m %H:%M') if p['created_at'] else '?'}"
        )
        if p.get("payment_proof_file_id"):
            try:
                await bot.send_photo(m.chat.id, p["payment_proof_file_id"],
                                     caption=text, parse_mode="Markdown", reply_markup=kb)
                continue
            except Exception:
                pass
        await m.answer(text + "\n(אין תמונה)", parse_mode="Markdown", reply_markup=kb)
    if len(pending) > 10:
        await m.answer(f"ועוד {len(pending)-10} תשלומים...")

@dp.callback_query(F.data.startswith("adm_approve:"))
async def approve_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    pid    = int(cb.data.split(":")[1])
    result = await pay_db.approve_payment(pid, cb.from_user.id)
    if result:
        txt = f"✅ אושר #{pid} | {result['bot_name']} | @{result.get('username','?')}"
        await (cb.message.edit_caption(caption=txt) if cb.message.photo
               else cb.message.edit_text(txt))
    await cb.answer("אושר!" if result else "לא נמצא")

@dp.callback_query(F.data.startswith("adm_reject:"))
async def reject_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    pid    = int(cb.data.split(":")[1])
    result = await pay_db.reject_payment(pid, cb.from_user.id)
    if result:
        txt = f"❌ נדחה #{pid} | @{result.get('username','?')}"
        await (cb.message.edit_caption(caption=txt) if cb.message.photo
               else cb.message.edit_text(txt))
    await cb.answer("נדחה")

@dp.message(Command("stats"))
async def stats_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    stats = await pay_db.get_stats()
    total_monthly = sum(BOT_PRICING[k].price_ils for k in BOT_PRICING)
    await m.answer(
        f"📈 *סטטיסטיקות*\n\n"
        f"משתמשים רשומים: {stats['total_users']}\n"
        f"משלמים: {stats['approved']}\n"
        f"ממתינים: {stats['pending']}\n"
        f"הכנסות כולל: {stats['total_revenue']:.0f} ₪\n\n"
        f"פוטנציאל/משתמש: {total_monthly} ₪\n"
        f"פוטנציאל/100 משתמשים: {total_monthly*100:,.0f} ₪",
        parse_mode="Markdown"
    )

@dp.message(Command("bots"))
async def bots_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    lines = ["🤖 *רשימת בוטים*\n"]
    for key, info in ECOSYSTEM_BOTS.items():
        pricing = BOT_PRICING.get(key)
        price   = f"{pricing.price_ils}₪" if pricing else "?"
        lines.append(f"• *{info['name']}* @{info['username']} | {price}")
    lines.append(f"\nסה\"כ בוטים פעילים: {len(ECOSYSTEM_BOTS)}")
    await m.answer("\n".join(lines), parse_mode="Markdown")

@dp.message(Command("revenue"))
async def revenue_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    stats = await pay_db.get_stats()
    lines = ["💰 *דוח הכנסות*\n"]
    for row in stats["by_bot"]:
        lines.append(f"• {row['bot_name']}: {float(row['revenue']):.0f} ₪ ({row['cnt']} משתמשים)")
    lines.append(f"\n*סה\"כ: {stats['total_revenue']:.0f} ₪*")
    await m.answer("\n".join(lines), parse_mode="Markdown")

# ═══════════════════════════════════════════════════════════════
# Access requests callbacks (unchanged)
# ═══════════════════════════════════════════════════════════════
@dp.message(Command("requests"))
async def access_requests_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    pending = await pay_db.get_pending_access_requests()
    if not pending:
        await m.answer("✅ אין בקשות גישה ממתינות!")
        return
    for p in pending[:10]:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ אשר", callback_data=f"acc_ok:{p['id']}"),
            InlineKeyboardButton(text="❌ דחה", callback_data=f"acc_no:{p['id']}"),
        ]])
        text = (
            f"📋 בקשת גישה #{p['id']}\n"
            f"משתמש: @{p.get('username') or '?'} ({p['user_id']})\n"
            f"בוט: {p['bot_name']}\n"
            f"סיבה: {p.get('reason') or '-'}\n"
            f"תאריך: {str(p.get('created_at',''))[:16]}"
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
                "✅ בקשת הגישה שלך אושרה!\nכל הפיצ'רים זמינים עבורך. 🚀")
        except Exception:
            pass
        await cb.message.edit_text(f"✅ אושר | @{result.get('username','?')}")
    await cb.answer("✅")

@dp.callback_query(F.data.startswith("acc_no:"))
async def reject_access_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    result = await pay_db.reject_access(int(cb.data.split(":")[1]))
    if result:
        try:
            await bot.send_message(result["user_id"],
                "❌ בקשת הגישה נדחתה.\nלפרטים: /premium")
        except Exception:
            pass
        await cb.message.edit_text(f"❌ נדחה | @{result.get('username','?')}")
    await cb.answer("❌")

# ═══════════════════════════════════════════════════════════════
# Image Studio (unchanged logic, refactored strings)
# ═══════════════════════════════════════════════════════════════
user_image_mode = {}

@dp.message(Command("studio"))
@dp.message(Command("resize"))
async def studio_menu(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📷 שינוי גודל", callback_data="studio:resize_menu")],
        [InlineKeyboardButton(text="🎬 יצירת GIF",  callback_data="studio:gif_menu")],
    ])
    await m.answer("🎨 *SLH Image Studio*\n\nבחר מה לעשות:", parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data == "studio:resize_menu")
async def resize_menu(cb: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="640x360 (BotFather)",  callback_data="studio:set_resize:640x360")],
        [InlineKeyboardButton(text="320x320 (Bot Profile)", callback_data="studio:set_resize:320x320")],
        [InlineKeyboardButton(text="512x512 (Sticker)",     callback_data="studio:set_resize:512x512")],
        [InlineKeyboardButton(text="1280x720 (HD)",         callback_data="studio:set_resize:1280x720")],
        [InlineKeyboardButton(text="1080x1080 (Instagram)", callback_data="studio:set_resize:1080x1080")],
        [InlineKeyboardButton(text="📷 כל הגדלים",         callback_data="studio:set_resize:all")],
    ])
    await cb.message.answer("📷 *שינוי גודל*\n\nבחר גודל, אחר כך שלח תמונה:", parse_mode="Markdown", reply_markup=kb)
    await cb.answer()

@dp.callback_query(F.data == "studio:gif_menu")
async def gif_menu(cb: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌀 Zoom",    callback_data="studio:set_gif:zoom")],
        [InlineKeyboardButton(text="💫 Pulse",   callback_data="studio:set_gif:pulse")],
        [InlineKeyboardButton(text="🌊 Wave",    callback_data="studio:set_gif:wave")],
        [InlineKeyboardButton(text="✨ Sparkle", callback_data="studio:set_gif:sparkle")],
        [InlineKeyboardButton(text="🔄 Rotate",  callback_data="studio:set_gif:rotate")],
        [InlineKeyboardButton(text="🎬 כל האנימציות", callback_data="studio:set_gif:all")],
    ])
    await cb.message.answer("🎬 *יצירת GIF*\n\nבחר סגנון:", parse_mode="Markdown", reply_markup=kb)
    await cb.answer()

@dp.callback_query(F.data.startswith("studio:set_"))
async def set_mode(cb: types.CallbackQuery):
    mode = cb.data.replace("studio:set_", "")
    user_image_mode[cb.from_user.id] = mode
    await cb.message.answer(f"✅ מוד נבחר: `{mode}`\n\n📷 עכשיו שלח תמונה!", parse_mode="Markdown")
    await cb.answer()

@dp.message(F.photo)
async def handle_photo(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    mode = user_image_mode.get(m.from_user.id, "")
    if not mode:
        await m.answer("📷 שלחת תמונה! אבל קודם בחר מה לעשות:\n/studio")
        return
    try:
        from PIL import Image, ImageEnhance
        from aiogram.types import BufferedInputFile

        photo = m.photo[-1]
        file  = await bot.get_file(photo.file_id)
        data  = await bot.download_file(file.file_path)
        img   = Image.open(BytesIO(data.read())).convert("RGB")
        await m.answer("⏳ מעבד...")

        if mode.startswith("resize:"):
            size_key = mode.split(":")[1]
            sizes = {"640x360":(640,360),"320x320":(320,320),"512x512":(512,512),
                     "1280x720":(1280,720),"1080x1080":(1080,1080)}
            targets = sizes.items() if size_key == "all" else [(size_key, sizes.get(size_key,(640,360)))]
            for name, sz in targets:
                buf = BytesIO()
                img.copy().resize(sz, Image.LANCZOS).save(buf, format="PNG")
                buf.seek(0)
                await m.answer_document(BufferedInputFile(buf.read(), f"slh_{name}.png"), caption=f"✅ {name}")

        elif mode.startswith("gif:"):
            effect    = mode.split(":")[1]
            to_run    = [effect] if effect != "all" else ["zoom","pulse","wave","sparkle","rotate"]
            eff_names = {"zoom":"🌀 Zoom","pulse":"💫 Pulse","wave":"🌊 Wave","sparkle":"✨ Sparkle","rotate":"🔄 Rotate"}
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
                    await m.answer_document(BufferedInputFile(buf.read(),f"slh_{eff}.gif"), caption=f"🎬 {eff_names.get(eff,eff)}")

        user_image_mode.pop(m.from_user.id, None)
        await m.answer("✅ סיימתי! לעוד: /studio")
    except Exception as e:
        await m.answer(f"❌ שגיאה: {e}")

# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════
async def main():
    await pay_db.init_schema()
    try:
        pool = await get_db()
        if pool:
            logger.info("Railway DB connected ✅")
        else:
            logger.warning("Railway DB not configured — token ops disabled")
    except Exception as e:
        logger.warning(f"Railway DB init failed: {e}")
    logger.info("=" * 50)
    logger.info("SLH SPARK SYSTEM | Super Admin Bot — READY")
    logger.info("=" * 50)
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
