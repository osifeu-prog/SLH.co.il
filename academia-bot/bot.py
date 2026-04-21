"""@WEWORK_teamviwer_bot — SLH Academia licensing bot.

aiogram 3.x. Sells academy licenses paid via TON / BNB / ILS (Bit manual).
Polls Railway /api/payment/status/{user_id} to confirm and then writes to
academy_licenses. No fake success — every confirm hits the Railway API.

Hebrew UI, English logs. Every handler is wrapped in try/except with
logging.exception so a broken DB query never silently kills the polling loop.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from decimal import Decimal

import aiohttp
import asyncpg
from shared_db_core import init_db_pool as _shared_init_db_pool
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from urllib.parse import quote_plus

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    WebAppInfo,
)
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, ".env"), override=False)
# Fall back to the shared ecosystem .env (where WEWORK_TEAMVIWER_TOKEN lives).
load_dotenv(os.path.join(HERE, "..", ".env"), override=False)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("academia-bot")

TOKEN = os.getenv("WEWORK_TEAMVIWER_TOKEN") or os.getenv("BOT_TOKEN")
if not TOKEN:
    raise SystemExit("WEWORK_TEAMVIWER_TOKEN not set")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL not set")

API_BASE = os.getenv(
    "SLH_API_BASE", "https://slh-api-production.up.railway.app"
).rstrip("/")
SUPPORT_HANDLE = os.getenv("SUPPORT_HANDLE", "@osifeu_prog")
BOT_NAME = os.getenv("ACADEMIA_BOT_NAME", "academia")

POLL_INTERVAL_SEC = 10
POLL_TIMEOUT_SEC = 600  # 10 minutes

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

_pool: asyncpg.Pool | None = None


# ----------------------------------------------------------------------------
# DB bootstrap
# ----------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS academy_courses (
    id BIGSERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    title_he TEXT NOT NULL,
    description_he TEXT,
    price_ils NUMERIC(10,2),
    price_slh NUMERIC(18,4),
    materials_url TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS academy_licenses (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    course_id BIGINT REFERENCES academy_courses(id),
    payment_id TEXT,
    status TEXT DEFAULT 'active',
    purchased_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_acad_user ON academy_licenses(user_id);
"""

SEED_COURSE = (
    "intro-slh",
    "[DEMO] מבוא ל-SLH — השקעה וקריפטו לישראלים",
    "קורס יסוד שעוזר להבין את השוק, הסיכונים, והפלטפורמה.",
    Decimal("49.0"),
    Decimal("0.11"),
    "https://slh-nft.com/academy/intro-slh",
)


async def init_db() -> None:
    global _pool
    _pool = await _shared_init_db_pool(DATABASE_URL)
    async with _pool.acquire() as conn:
        await conn.execute(SCHEMA)
        await conn.execute(
            """
            INSERT INTO academy_courses
                (slug, title_he, description_he, price_ils, price_slh, materials_url)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (slug) DO NOTHING
            """,
            *SEED_COURSE,
        )
    log.info("DB ready (academy_courses + academy_licenses)")


# ----------------------------------------------------------------------------
# Keyboards
# ----------------------------------------------------------------------------


def main_menu_kb(is_instructor: bool = False, is_approved: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="רכוש רישיון", callback_data="menu:buy")],
        [
            InlineKeyboardButton(
                text="הרישיונות שלי", callback_data="menu:my_licenses"
            )
        ],
    ]
    if is_approved:
        rows.append(
            [InlineKeyboardButton(text="📤 העלה קורס", callback_data="instr:upload")]
        )
        rows.append(
            [InlineKeyboardButton(text="💰 ההכנסות שלי", callback_data="instr:earnings")]
        )
    elif is_instructor:
        rows.append(
            [InlineKeyboardButton(text="⏳ ממתין לאישור מדריך", callback_data="instr:pending")]
        )
    else:
        rows.append(
            [InlineKeyboardButton(text="🎓 הצטרף כמדריך", callback_data="instr:register")]
        )
    rows.append([InlineKeyboardButton(text="תמיכה", callback_data="menu:support")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def course_list_kb(courses) -> InlineKeyboardMarkup:
    rows = []
    for c in courses:
        price_ils = c["price_ils"] or 0
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{c['title_he']} · {price_ils}₪",
                    callback_data=f"course:{c['id']}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="חזרה", callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_methods_kb(course_id: int, allow_phone_pay: bool = False) -> InlineKeyboardMarkup:
    """Build payment menu. Bit/PayBox shown only when the course's instructor
    has registered a payout phone (allow_phone_pay=True). Osif's own courses
    have no phone configured so those buttons are hidden."""
    rows = [
        [
            InlineKeyboardButton(text="💎 TON", callback_data=f"pay:{course_id}:ton"),
            InlineKeyboardButton(text="🟡 BNB / BSC", callback_data=f"pay:{course_id}:bsc"),
        ],
        [
            InlineKeyboardButton(text="🦊 MetaMask (BSC)", callback_data=f"pay:{course_id}:metamask"),
            InlineKeyboardButton(text="🥞 PancakeSwap → SLH", callback_data=f"pay:{course_id}:pancakeswap"),
        ],
        [
            InlineKeyboardButton(text="🏦 העברה בנקאית", callback_data=f"pay:{course_id}:bank"),
            InlineKeyboardButton(text="⭐ Telegram Stars", callback_data=f"pay:{course_id}:stars"),
        ],
    ]
    if allow_phone_pay:
        rows.append([
            InlineKeyboardButton(text="📱 Bit / PayBox (למדריך)", callback_data=f"pay:{course_id}:phone"),
        ])
    rows.append([
        InlineKeyboardButton(text="💼 חלופה: זמן עבודה / זהב / אחר", callback_data=f"pay:{course_id}:alt"),
    ])
    rows.append([InlineKeyboardButton(text="חזרה", callback_data="menu:buy")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ----------------------------------------------------------------------------
# Handlers
# ----------------------------------------------------------------------------


WELCOME = (
    "🎓 <b>ברוך הבא לאקדמיית SLH</b>\n\n"
    "כאן אתה רוכש רישיונות לקורסי ההשקעה והקריפטו של SLH.\n"
    "בחר פעולה מהתפריט:"
)


@dp.message(Command("start"))
async def cmd_start(msg: Message) -> None:
    try:
        is_instr, is_approved = await _instructor_status(msg.from_user.id)
        await msg.answer(WELCOME, reply_markup=main_menu_kb(is_instr, is_approved))
    except Exception:
        log.exception("cmd_start failed")


@dp.message(Command("help"))
async def cmd_help(msg: Message) -> None:
    try:
        await msg.answer(
            "<b>פקודות</b>\n"
            "/start — תפריט ראשי\n"
            "/buy — רכישת קורס\n"
            "/my_licenses — הרישיונות שלי\n"
            "/become_instructor — הצטרף כמדריך\n"
            "/upload_course — העלה קורס (מדריכים מאושרים בלבד)\n"
            "/my_earnings — ההכנסות שלי כמדריך\n"
            "/help — מסך זה\n\n"
            f"תמיכה: {SUPPORT_HANDLE}"
        )
    except Exception:
        log.exception("cmd_help failed")


@dp.message(Command("buy"))
async def cmd_buy(msg: Message) -> None:
    log.info("cmd_buy from user_id=%s chat_id=%s", msg.from_user.id, msg.chat.id)
    try:
        await _show_courses(msg.chat.id)
    except Exception:
        log.exception("cmd_buy failed")
        try:
            await msg.answer(
                "שגיאה בטעינת הקורסים. נסה שוב או פנה לתמיכה "
                f"{SUPPORT_HANDLE}.",
                reply_markup=main_menu_kb(),
            )
        except Exception:
            log.exception("cmd_buy fallback notify failed")


@dp.message(Command("my_licenses"))
async def cmd_my_licenses(msg: Message) -> None:
    log.info("cmd_my_licenses from user_id=%s", msg.from_user.id)
    try:
        await _show_licenses(msg.chat.id, msg.from_user.id)
    except Exception:
        log.exception("cmd_my_licenses failed")
        try:
            await msg.answer(
                "שגיאה בטעינת הרישיונות. נסה שוב או פנה לתמיכה "
                f"{SUPPORT_HANDLE}.",
                reply_markup=main_menu_kb(),
            )
        except Exception:
            log.exception("cmd_my_licenses fallback notify failed")


# ----------------------------------------------------------------------------
# Callbacks
# ----------------------------------------------------------------------------


@dp.callback_query(F.data == "menu:home")
async def cb_home(cq: CallbackQuery) -> None:
    try:
        is_instr, is_approved = await _instructor_status(cq.from_user.id)
        await cq.message.edit_text(WELCOME, reply_markup=main_menu_kb(is_instr, is_approved))
        await cq.answer()
    except Exception:
        log.exception("cb_home failed")
        await cq.answer("שגיאה", show_alert=False)


@dp.callback_query(F.data == "menu:buy")
async def cb_buy(cq: CallbackQuery) -> None:
    await _show_courses(cq.message.chat.id, edit_msg=cq.message)
    await cq.answer()


@dp.callback_query(F.data == "menu:my_licenses")
async def cb_my_licenses(cq: CallbackQuery) -> None:
    await _show_licenses(
        cq.message.chat.id, cq.from_user.id, edit_msg=cq.message
    )
    await cq.answer()


@dp.callback_query(F.data == "menu:support")
async def cb_support(cq: CallbackQuery) -> None:
    try:
        await cq.message.edit_text(
            f"לתמיכה: {SUPPORT_HANDLE}\nנחזור אליך בהקדם.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="חזרה", callback_data="menu:home"
                        )
                    ]
                ]
            ),
        )
        await cq.answer()
    except Exception:
        log.exception("cb_support failed")


@dp.callback_query(F.data.startswith("course:"))
async def cb_course(cq: CallbackQuery) -> None:
    try:
        course_id = int(cq.data.split(":", 1)[1])
        assert _pool is not None
        async with _pool.acquire() as conn:
            c = await conn.fetchrow(
                "SELECT id, title_he, description_he, price_ils, price_slh, materials_url "
                "FROM academy_courses WHERE id=$1 AND active=TRUE",
                course_id,
            )
            allow_phone_pay = False
            instructor_name: str | None = None
            try:
                row = await conn.fetchrow(
                    "SELECT i.display_name, i.payout_phone "
                    "FROM academy_courses c "
                    "JOIN academy_instructors i ON i.id = c.instructor_id "
                    "WHERE c.id = $1",
                    course_id,
                )
                if row:
                    instructor_name = row["display_name"]
                    allow_phone_pay = bool(row["payout_phone"])
            except Exception:
                pass
        if not c:
            await cq.answer("הקורס לא נמצא", show_alert=True)
            return

        included_lines = ["📚 <b>מה כלול בקורס:</b>"]
        if c["materials_url"]:
            included_lines.append("• גישה מלאה לחומרי הקורס (וידאו + טקסט)")
            included_lines.append("• רישיון לכל החיים — צפה מתי שתרצה")
        else:
            included_lines.append("• תוכן בהכנה — פנה לתמיכה לפרטים")
        included_lines.append("• תעודת השלמה (Premium לבוט)")
        included_lines.append("• השתתפות בקהילת לומדי SLH")
        included = "\n".join(included_lines)

        instructor_line = (
            f"\n👨\u200d🏫 מדריך: {instructor_name}\n" if instructor_name else ""
        )

        text = (
            f"<b>{c['title_he']}</b>\n"
            f"{instructor_line}\n"
            f"{c['description_he'] or 'תיאור מלא בקרוב — פנה לתמיכה למידע.'}\n\n"
            f"{included}\n\n"
            f"💰 <b>מחיר:</b> {c['price_ils'] or 0}₪ · {c['price_slh'] or 0} SLH\n\n"
            f"בחר אמצעי תשלום מתוך הרשת המלאה שלנו:"
        )
        await cq.message.edit_text(
            text,
            reply_markup=payment_methods_kb(course_id, allow_phone_pay=allow_phone_pay),
            disable_web_page_preview=True,
        )
        await cq.answer()
    except Exception:
        log.exception("cb_course failed")
        await cq.answer("שגיאה בטעינת הקורס", show_alert=True)


@dp.callback_query(F.data.startswith("pay:"))
async def cb_pay(cq: CallbackQuery) -> None:
    # Acknowledge IMMEDIATELY so Telegram dismisses the loading spinner.
    # Without this, the user sees a hung click and may type new commands,
    # causing the actual payment response to surface out-of-order later.
    try:
        await cq.answer("טוען אמצעי תשלום…")
    except Exception:
        log.exception("cb_pay early ack failed")
    try:
        _, course_id_s, method = cq.data.split(":")
        course_id = int(course_id_s)
        user_id = cq.from_user.id

        assert _pool is not None
        async with _pool.acquire() as conn:
            c = await conn.fetchrow(
                "SELECT id, title_he, description_he, price_ils, price_slh, materials_url "
                "FROM academy_courses WHERE id=$1 AND active=TRUE",
                course_id,
            )
        if not c:
            await cq.answer("הקורס לא נמצא", show_alert=True)
            return

        # Telegram Stars (XTR) — native invoice, no manual flow.
        if method == "stars":
            await _send_stars_invoice(cq.message.chat.id, c)
            return

        # Create a pending payment record by calling Railway API.
        payment_id, instructions = await _create_payment(
            user_id=user_id, course=c, method=method
        )
        if not payment_id:
            await cq.message.edit_text(
                "שגיאה ביצירת התשלום. נסה שוב מאוחר יותר או פנה לתמיכה "
                f"{SUPPORT_HANDLE}.",
                reply_markup=main_menu_kb(),
            )
            return

        # Build per-method action keyboard (WebApp / explorer link / etc).
        action_rows: list[list[InlineKeyboardButton]] = []
        if method == "bank":
            # WebApp: opens buy.html#bank inside the Telegram Mini App
            action_rows.append([
                InlineKeyboardButton(
                    text="🌐 פתח טופס בנק (Mini App)",
                    web_app=WebAppInfo(url="https://slh-nft.com/buy.html#bank"),
                )
            ])
        elif method == "pancakeswap":
            slh_contract = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"
            action_rows.append([
                InlineKeyboardButton(
                    text="🥞 פתח PancakeSwap",
                    url=f"https://pancakeswap.finance/swap?outputCurrency={slh_contract}&chain=bsc",
                )
            ])
        action_rows.append([
            InlineKeyboardButton(text="חזרה לתפריט", callback_data="menu:home")
        ])

        await cq.message.edit_text(
            instructions + "\n\nאני מאמת אוטומטית עד 10 דקות. המתן להודעה…",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=action_rows),
            disable_web_page_preview=True,
        )

        # QR code as separate photo for crypto methods (TON/BSC/MetaMask).
        cfg = await _api_config()
        if method == "ton":
            addr = cfg.get("ton_address") or ""
            amount = float(c["price_slh"] or cfg.get("premium_min_ton") or 0.01)
            if addr:
                uri = _wallet_uri("ton", addr, amount)
                await _send_payment_qr(
                    cq.message.chat.id,
                    caption=f"📷 סרוק עם Tonkeeper / @wallet — {amount} TON ל-{addr[:8]}…",
                    uri=uri,
                )
        elif method in ("bsc", "metamask"):
            addr = cfg.get("bsc_genesis_address") or ""
            amount = float(cfg.get("premium_min_bnb") or 0.0005)
            if addr:
                uri = _wallet_uri(method, addr, amount)
                await _send_payment_qr(
                    cq.message.chat.id,
                    caption=f"📷 סרוק עם MetaMask / Trust — {amount} BNB ל-{addr[:8]}…",
                    uri=uri,
                )
        elif method == "pancakeswap":
            await _send_payment_qr(
                cq.message.chat.id,
                caption="📷 סרוק לפתיחת PancakeSwap בארנק שלך",
                uri="https://pancakeswap.finance/swap?outputCurrency=0xACb0A09414CEA1C879c67bB7A877E4e19480f022&chain=bsc",
            )

        # Background poll loop (skip for alt/phone — manual-only flows).
        if method not in ("alt", "phone"):
            asyncio.create_task(
                _wait_and_grant(
                    chat_id=cq.message.chat.id,
                    user_id=user_id,
                    course=c,
                    payment_id=payment_id,
                )
            )
    except Exception:
        log.exception("cb_pay failed")
        try:
            await cq.message.answer(
                "שגיאה בטיפול בתשלום. נסה שוב או פנה ל-" + SUPPORT_HANDLE,
                reply_markup=main_menu_kb(),
            )
        except Exception:
            log.exception("cb_pay fallback notify failed")


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


async def _show_courses(chat_id: int, edit_msg: Message | None = None) -> None:
    try:
        assert _pool is not None
        async with _pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, title_he, price_ils FROM academy_courses "
                "WHERE active=TRUE ORDER BY id"
            )
        log.info("_show_courses fetched %d active course(s) for chat=%s", len(rows), chat_id)
        if not rows:
            text = "אין קורסים זמינים כרגע."
            if edit_msg:
                await edit_msg.edit_text(text, reply_markup=main_menu_kb())
            else:
                await bot.send_message(
                    chat_id, text, reply_markup=main_menu_kb()
                )
            return

        text = "<b>קורסים זמינים:</b>\nבחר קורס להמשך."
        kb = course_list_kb(rows)
        if edit_msg:
            await edit_msg.edit_text(text, reply_markup=kb)
        else:
            await bot.send_message(chat_id, text, reply_markup=kb)
    except Exception:
        log.exception("_show_courses failed (chat=%s)", chat_id)
        try:
            await bot.send_message(
                chat_id,
                "שגיאה בטעינת הקורסים. נסה שוב מאוחר יותר.",
                reply_markup=main_menu_kb(),
            )
        except Exception:
            log.exception("_show_courses fallback notify failed (chat=%s)", chat_id)


async def _show_licenses(
    chat_id: int, user_id: int, edit_msg: Message | None = None
) -> None:
    try:
        assert _pool is not None
        async with _pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT l.id, l.status, l.purchased_at, l.expires_at,
                       c.title_he, c.materials_url
                FROM academy_licenses l
                JOIN academy_courses c ON c.id = l.course_id
                WHERE l.user_id = $1
                ORDER BY l.id DESC
                """,
                user_id,
            )
        if not rows:
            text = (
                "אין לך רישיונות פעילים עדיין.\n"
                "לחץ /buy כדי לרכוש קורס."
            )
        else:
            lines = ["<b>הרישיונות שלך:</b>", ""]
            for r in rows:
                date = (
                    r["purchased_at"].strftime("%Y-%m-%d")
                    if r["purchased_at"]
                    else "—"
                )
                status = "פעיל" if r["status"] == "active" else r["status"]
                link = (
                    f'\n<a href="{r["materials_url"]}">גישה לחומרים</a>'
                    if r["materials_url"]
                    else ""
                )
                lines.append(
                    f"• {r['title_he']}\n  נרכש: {date} · {status}{link}"
                )
            text = "\n".join(lines)

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="חזרה", callback_data="menu:home"
                    )
                ]
            ]
        )
        if edit_msg:
            await edit_msg.edit_text(
                text, reply_markup=kb, disable_web_page_preview=True
            )
        else:
            await bot.send_message(
                chat_id, text, reply_markup=kb, disable_web_page_preview=True
            )
    except Exception:
        log.exception("_show_licenses failed")
        await bot.send_message(
            chat_id, "שגיאה בטעינת הרישיונות.", reply_markup=main_menu_kb()
        )


def _qr_image_url(data: str, size: int = 300) -> str:
    """Public QR code generator (no install). Returns image URL ready for send_photo."""
    return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={quote_plus(data)}"


def _wallet_uri(method: str, address: str, amount: float) -> str:
    """Build a wallet-deep-link URI that mobile wallets can scan/open.

    TON: ton://transfer/{addr}?amount={nano}
    BSC: ethereum:{addr}@56?value={wei}  (EIP-681 — Trust/MetaMask understand)
    """
    if method == "ton":
        nano = int(amount * 1_000_000_000)
        return f"ton://transfer/{address}?amount={nano}"
    if method in ("bsc", "metamask"):
        wei = int(amount * 1_000_000_000_000_000_000)
        return f"ethereum:{address}@56?value={wei}"
    return address  # PancakeSwap etc — just encode the address


async def _send_payment_qr(chat_id: int, caption: str, uri: str) -> None:
    """Send a QR photo to the user. Failures are logged, not raised — the
    text instructions already give the address, so QR is a nice-to-have."""
    try:
        await bot.send_photo(
            chat_id,
            photo=_qr_image_url(uri),
            caption=caption,
        )
    except Exception:
        log.exception("_send_payment_qr failed for chat=%s", chat_id)


async def _api_config() -> dict:
    """Fetch the Railway payment config (TON addr + BSC addr + min amounts)."""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{API_BASE}/api/payment/config",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                if r.status != 200:
                    log.warning("payment/config returned %s", r.status)
                    return {}
                return await r.json()
    except Exception:
        log.exception("_api_config failed")
        return {}


async def _create_payment(
    user_id: int, course, method: str
) -> tuple[str | None, str]:
    """Create a pending payment reference.

    Returns (payment_id, user_facing_instructions_hebrew). If creation fails,
    payment_id is None.

    For TON/BSC we use local reference IDs (the verify endpoint takes a
    tx_hash later — see _check_status). For ILS/Bit we record via
    /api/payment/external/record so Osif can approve manually via the
    admin panel; the bot polls payment status to pick up the approval.
    """
    cfg = await _api_config()
    ref = f"ACAD-{user_id}-{course['id']}-{int(datetime.utcnow().timestamp())}"

    if method == "ton":
        addr = cfg.get("ton_address") or "—"
        min_ton = course["price_slh"] or cfg.get("premium_min_ton") or 0.01
        instr = (
            f"<b>תשלום ב-TON</b>\n\n"
            f"שלח <code>{min_ton}</code> TON לכתובת:\n"
            f"<code>{addr}</code>\n\n"
            f"מזהה תשלום: <code>{ref}</code>"
        )
        return ref, instr

    if method == "bsc":
        addr = cfg.get("bsc_genesis_address") or "—"
        min_bnb = cfg.get("premium_min_bnb") or 0.0005
        instr = (
            f"<b>תשלום ב-BNB (BSC)</b>\n\n"
            f"שלח לפחות <code>{min_bnb}</code> BNB לכתובת:\n"
            f"<code>{addr}</code>\n\n"
            f"מזהה תשלום: <code>{ref}</code>"
        )
        return ref, instr

    if method == "metamask":
        addr = cfg.get("bsc_genesis_address") or "—"
        min_bnb = cfg.get("premium_min_bnb") or 0.0005
        instr = (
            f"<b>תשלום ב-MetaMask (BSC)</b>\n\n"
            f"1. פתח MetaMask ובחר רשת BNB Smart Chain.\n"
            f"2. שלח לפחות <code>{min_bnb}</code> BNB לכתובת:\n"
            f"<code>{addr}</code>\n\n"
            f"מזהה תשלום: <code>{ref}</code>\n\n"
            f"💡 אין לך MetaMask? התקן מ-metamask.io או השתמש ב-Trust Wallet."
        )
        return ref, instr

    if method == "pancakeswap":
        slh_contract = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"
        instr = (
            f"<b>רכישה דרך PancakeSwap (SLH)</b>\n\n"
            f"1. פתח: https://pancakeswap.finance/swap?outputCurrency={slh_contract}&chain=bsc\n"
            f"2. החלף BNB → SLH לפי המחיר ({course['price_slh'] or 0} SLH).\n"
            f"3. שלח את ה-SLH לכתובת Genesis:\n"
            f"<code>{cfg.get('bsc_genesis_address') or '—'}</code>\n\n"
            f"מזהה: <code>{ref}</code>\n\n"
            f"💎 כל רכישת SLH מעניקה גם ZVK בונוס + REP points."
        )
        return ref, instr

    if method == "bank":
        # Bank transfer to Tzvika (CEO) — same flow as buy.html
        try:
            async with aiohttp.ClientSession() as s:
                payload = {
                    "user_id": user_id,
                    "provider": "manual_bank",
                    "provider_tx_id": ref,
                    "amount": float(course["price_ils"] or 0),
                    "currency": "ILS",
                    "plan_key": f"academy_{course['id']}",
                    "bot_name": BOT_NAME,
                    "grant_premium": False,
                    "issue_receipt": False,
                }
                async with s.post(
                    f"{API_BASE}/api/payment/external/record",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as r:
                    if r.status >= 400:
                        body = await r.text()
                        log.warning("external/record %s: %s", r.status, body[:200])
                        return None, ""
        except Exception:
            log.exception("_create_payment bank failed")
            return None, ""

        instr = (
            f"<b>העברה בנקאית</b>\n\n"
            f"לקבלת פרטי חשבון בנק (לצביקה קאופמן, מנכ\"ל) פנה ל-{SUPPORT_HANDLE}.\n"
            f"סכום: <code>{course['price_ils']}</code>₪\n"
            f"מזהה תשלום: <code>{ref}</code>\n\n"
            f"או מלא את הטופס המלא (8 שדות) באתר:\n"
            f"https://slh-nft.com/buy.html#bank\n\n"
            f"לאחר אישור ידני תקבל את הגישה לחומרים."
        )
        return ref, instr

    if method == "phone":
        # Bit/PayBox routing to instructor's payout_phone (Phase 2 — requires
        # academy_instructors.payout_phone column and per-course lookup).
        instr = (
            f"<b>📱 Bit / PayBox למדריך</b>\n\n"
            f"שיטת תשלום זו זמינה רק כאשר המדריך הגדיר טלפון.\n"
            f"פנה למדריך ישירות או ל-{SUPPORT_HANDLE} למידע נוסף.\n\n"
            f"מזהה: <code>{ref}</code>"
        )
        return ref, instr

    if method == "alt":
        instr = (
            f"<b>💼 חלופות תשלום</b>\n\n"
            f"אנו מקבלים גם:\n"
            f"• ⏱ זמן עבודה / הספק (תרומה לפרויקט)\n"
            f"• 🥇 זהב פיזי (לפי שווי שוק)\n"
            f"• 🪙 OTC קריפטו (USDT, USDC, BTC, ETH)\n"
            f"• 🔄 Swap מבוטים אחרים שלנו (ZVK, MNH)\n\n"
            f"פנה ל-{SUPPORT_HANDLE} עם המזהה <code>{ref}</code> "
            f"לבחירת המסלול המתאים לך."
        )
        return ref, instr

    return None, ""


async def _check_status(user_id: int, course_id: int | None = None) -> bool:
    """Return True iff user has either:
      (a) an active `academy_licenses` row for this course in our own _pool
          (authoritative — this bot is what writes them), OR
      (b) an `approved` external_payment reference in the Railway API (covers the
          case where the admin approved a TON/bank payment manually via admin panel
          but the bot hadn't yet polled success), OR
      (c) bot-level premium for this BOT_NAME via Railway /api/payment/status
          (legacy fallback for non-course flows).

    The previous version only checked (c), which caused ACAD-* timeouts for
    successful course purchases — academy writes to academy_licenses on the
    bot's own DB, not to premium_users.
    """
    # (a) local DB — authoritative
    if course_id is not None and _pool is not None:
        try:
            async with _pool.acquire() as conn:
                row = await conn.fetchval(
                    """
                    SELECT 1 FROM academy_licenses
                    WHERE user_id = $1 AND course_id = $2 AND status = 'active'
                    LIMIT 1
                    """,
                    user_id, course_id,
                )
                if row:
                    return True
        except Exception:
            log.exception("_check_status local DB check failed")

    # (b) Railway payment approved reference (auto-verify side)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{API_BASE}/api/payment/status/{user_id}",
                params={"bot_name": BOT_NAME},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                if r.status != 200:
                    return False
                data = await r.json()
                # (c) legacy premium check
                if bool(data.get("has_premium")):
                    return True
                # (b) check last_external payment for this course reference
                ext = data.get("last_external") or {}
                if ext.get("status") == "approved" and course_id is not None:
                    # Approved payment exists — treat as success signal
                    return True
                return False
    except Exception:
        log.exception("_check_status Railway API check failed")
        return False


async def _wait_and_grant(
    chat_id: int, user_id: int, course, payment_id: str
) -> None:
    """Poll up to 10 minutes. On confirmed, insert license + send materials."""
    deadline = datetime.utcnow().timestamp() + POLL_TIMEOUT_SEC
    try:
        while datetime.utcnow().timestamp() < deadline:
            await asyncio.sleep(POLL_INTERVAL_SEC)
            if not await _check_status(user_id, course.get("id") if isinstance(course, dict) else None):
                continue

            # Confirmed — grant license (idempotent per user+course).
            assert _pool is not None
            async with _pool.acquire() as conn:
                existing = await conn.fetchval(
                    "SELECT id FROM academy_licenses "
                    "WHERE user_id=$1 AND course_id=$2 AND status='active'",
                    user_id,
                    course["id"],
                )
                if not existing:
                    await conn.execute(
                        """
                        INSERT INTO academy_licenses
                            (user_id, course_id, payment_id, status)
                        VALUES ($1, $2, $3, 'active')
                        """,
                        user_id,
                        course["id"],
                        payment_id,
                    )
            link = course["materials_url"] or "—"
            await bot.send_message(
                chat_id,
                f"✅ <b>התשלום אושר</b>\n\n"
                f"הרישיון ל'{course['title_he']}' פעיל.\n"
                f'גישה לחומרים: <a href="{link}">{link}</a>',
                disable_web_page_preview=False,
            )
            return

        # Timeout.
        await bot.send_message(
            chat_id,
            "לא הצלחנו לאמת את התשלום ב-10 דקות האחרונות.\n"
            f"אם שילמת, פנה ל-{SUPPORT_HANDLE} עם מזהה "
            f"<code>{payment_id}</code>.",
        )
    except Exception:
        log.exception("_wait_and_grant failed")
        try:
            await bot.send_message(
                chat_id,
                f"שגיאה באימות. פנה לתמיכה {SUPPORT_HANDLE} "
                f"(מזהה: {payment_id}).",
            )
        except Exception:
            log.exception("failed to notify user of _wait_and_grant error")


# ----------------------------------------------------------------------------
# Telegram Stars (XTR) — native invoice flow
# ----------------------------------------------------------------------------

# Conversion: 1 XTR ≈ $0.013 ≈ ₪0.05 (rough)
ILS_PER_STAR = 0.05


def _course_to_stars(price_ils: float | None) -> int:
    """Convert ILS price to Telegram Stars amount. Minimum 1 star."""
    p = float(price_ils or 0)
    return max(1, int(round(p / ILS_PER_STAR)))


async def _send_stars_invoice(chat_id: int, course) -> None:
    """Send a native Telegram Stars invoice. The user pays inside Telegram —
    no bank, no crypto. We grant the license on successful_payment."""
    stars = _course_to_stars(course["price_ils"])
    title = course["title_he"][:32]  # Telegram limit
    description = (course["description_he"] or "רישיון לכל החיים לקורס SLH")[:255]
    payload = f"academy_stars:{course['id']}"
    try:
        await bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # XTR requires NO provider token
            currency="XTR",
            prices=[LabeledPrice(label=title, amount=stars)],
        )
    except Exception:
        log.exception("_send_stars_invoice failed (chat=%s, stars=%s)", chat_id, stars)
        try:
            await bot.send_message(
                chat_id,
                "❌ לא הצלחנו לפתוח חשבונית Stars. ודא שאפליקציית Telegram מעודכנת, "
                f"או פנה ל-{SUPPORT_HANDLE}.",
            )
        except Exception:
            pass


@dp.pre_checkout_query()
async def on_pre_checkout(q: PreCheckoutQuery) -> None:
    """Telegram requires explicit ack for every pre_checkout. We always
    approve — the actual ledger entry happens on successful_payment."""
    try:
        await bot.answer_pre_checkout_query(q.id, ok=True)
    except Exception:
        log.exception("on_pre_checkout failed for id=%s", q.id)


@dp.message(F.successful_payment)
async def on_successful_payment(msg: Message) -> None:
    """Stars payment confirmed by Telegram — grant the license immediately."""
    try:
        sp = msg.successful_payment
        if not sp or not sp.invoice_payload.startswith("academy_stars:"):
            return
        course_id = int(sp.invoice_payload.split(":", 1)[1])
        user_id = msg.from_user.id

        assert _pool is not None
        async with _pool.acquire() as conn:
            c = await conn.fetchrow(
                "SELECT id, title_he, materials_url FROM academy_courses "
                "WHERE id=$1 AND active=TRUE",
                course_id,
            )
            if not c:
                await msg.answer(
                    f"⚠️ התשלום התקבל אבל הקורס לא נמצא. פנה ל-{SUPPORT_HANDLE} "
                    f"עם מזהה: {sp.telegram_payment_charge_id}"
                )
                return

            existing = await conn.fetchval(
                "SELECT id FROM academy_licenses "
                "WHERE user_id=$1 AND course_id=$2 AND status='active'",
                user_id, course_id,
            )
            if not existing:
                await conn.execute(
                    """
                    INSERT INTO academy_licenses
                        (user_id, course_id, payment_id, status)
                    VALUES ($1, $2, $3, 'active')
                    """,
                    user_id, course_id, f"stars:{sp.telegram_payment_charge_id}",
                )
        link = c["materials_url"] or "—"
        await msg.answer(
            f"✅ <b>התשלום ב-Stars אושר ⭐</b>\n\n"
            f"הרישיון ל'{c['title_he']}' פעיל.\n"
            f'גישה לחומרים: <a href="{link}">{link}</a>',
            disable_web_page_preview=False,
        )
    except Exception:
        log.exception("on_successful_payment failed")


# ----------------------------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------------------------


async def main() -> None:
    await init_db()
    me = await bot.get_me()
    log.info("starting academia-bot as @%s (id=%s)", me.username, me.id)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


# ============================================================================
# UGC EXTENSION — instructor onboarding, course upload, earnings.
# Talks to Railway /api/academia/* (router academia_ugc.py).
# ============================================================================

# In-memory wizard state. user_id -> {"flow": str, "step": str, "data": dict}.
# Process-local (lost on restart) — acceptable for short multi-step flows.
_wizards: dict[int, dict] = {}


async def _api_get(path: str) -> dict | None:
    """GET helper. Returns parsed JSON or None on any failure."""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{API_BASE}{path}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                if r.status >= 400:
                    log.warning("GET %s -> %s", path, r.status)
                    return None
                return await r.json()
    except Exception:
        log.exception("_api_get %s failed", path)
        return None


async def _api_post(path: str, payload: dict, admin: bool = False) -> dict | None:
    """POST helper. Returns parsed JSON or None on any failure."""
    headers = {}
    if admin:
        admin_key = os.getenv("ADMIN_API_KEY") or os.getenv("ADMIN_API_KEYS", "").split(",")[0].strip()
        if admin_key:
            headers["X-Admin-Key"] = admin_key
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{API_BASE}{path}",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                body = await r.json() if r.content_type == "application/json" else None
                if r.status >= 400:
                    log.warning("POST %s -> %s: %s", path, r.status, body)
                    return None
                return body
    except Exception:
        log.exception("_api_post %s failed", path)
        return None


async def _instructor_status(user_id: int) -> tuple[bool, bool]:
    """Returns (is_registered, is_approved) for the given user_id."""
    data = await _api_get(f"/api/academia/instructor/{user_id}")
    if not data or not isinstance(data, dict) or not data.get("id"):
        return False, False
    return True, bool(data.get("approved"))


def _cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ ביטול", callback_data="wiz:cancel")]
        ]
    )


def _back_home_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="חזרה לתפריט", callback_data="menu:home")]
        ]
    )


# ---- /become_instructor wizard ----------------------------------------------

@dp.message(Command("become_instructor"))
async def cmd_become_instructor(msg: Message) -> None:
    await _start_register_wizard(msg.chat.id, msg.from_user.id)


@dp.callback_query(F.data == "instr:register")
async def cb_instr_register(cq: CallbackQuery) -> None:
    await _start_register_wizard(cq.message.chat.id, cq.from_user.id)
    await cq.answer()


@dp.callback_query(F.data == "instr:pending")
async def cb_instr_pending(cq: CallbackQuery) -> None:
    try:
        await cq.message.edit_text(
            "⏳ <b>הבקשה שלך כמדריך ממתינה לאישור מנהל.</b>\n\n"
            "תקבל הודעה ברגע שהאישור יושלם.",
            reply_markup=_back_home_kb(),
        )
        await cq.answer()
    except Exception:
        log.exception("cb_instr_pending failed")


async def _start_register_wizard(chat_id: int, user_id: int) -> None:
    try:
        is_instr, is_approved = await _instructor_status(user_id)
        if is_approved:
            await bot.send_message(
                chat_id,
                "✅ אתה כבר רשום כמדריך מאושר.",
                reply_markup=_back_home_kb(),
            )
            return
        if is_instr:
            await bot.send_message(
                chat_id,
                "⏳ הבקשה שלך כמדריך כבר נשלחה וממתינה לאישור.",
                reply_markup=_back_home_kb(),
            )
            return
        _wizards[user_id] = {"flow": "register", "step": "display_name", "data": {}}
        await bot.send_message(
            chat_id,
            "🎓 <b>הצטרפות כמדריך</b>\n\n"
            "שלב 1/4 — מה השם שיוצג לתלמידים? (עד 200 תווים)",
            reply_markup=_cancel_kb(),
        )
    except Exception:
        log.exception("_start_register_wizard failed")


# ---- /upload_course wizard --------------------------------------------------

@dp.message(Command("upload_course"))
async def cmd_upload_course(msg: Message) -> None:
    await _start_upload_wizard(msg.chat.id, msg.from_user.id)


@dp.callback_query(F.data == "instr:upload")
async def cb_instr_upload(cq: CallbackQuery) -> None:
    await _start_upload_wizard(cq.message.chat.id, cq.from_user.id)
    await cq.answer()


async def _start_upload_wizard(chat_id: int, user_id: int) -> None:
    try:
        is_instr, is_approved = await _instructor_status(user_id)
        if not is_instr:
            await bot.send_message(
                chat_id,
                "תחילה הצטרף כמדריך עם /become_instructor.",
                reply_markup=_back_home_kb(),
            )
            return
        if not is_approved:
            await bot.send_message(
                chat_id,
                "⏳ הבקשה שלך כמדריך עדיין לא אושרה. אנא המתן.",
                reply_markup=_back_home_kb(),
            )
            return
        _wizards[user_id] = {"flow": "upload", "step": "slug", "data": {}}
        await bot.send_message(
            chat_id,
            "📤 <b>העלאת קורס חדש</b>\n\n"
            "שלב 1/7 — מזהה (slug) באנגלית (אותיות, מספרים, מקפים): "
            "למשל <code>crypto-101</code>",
            reply_markup=_cancel_kb(),
        )
    except Exception:
        log.exception("_start_upload_wizard failed")


# ---- /my_earnings -----------------------------------------------------------

@dp.message(Command("my_earnings"))
async def cmd_my_earnings(msg: Message) -> None:
    await _show_earnings(msg.chat.id, msg.from_user.id)


@dp.callback_query(F.data == "instr:earnings")
async def cb_instr_earnings(cq: CallbackQuery) -> None:
    await _show_earnings(cq.message.chat.id, cq.from_user.id, edit_msg=cq.message)
    await cq.answer()


async def _show_earnings(
    chat_id: int, user_id: int, edit_msg: Message | None = None
) -> None:
    try:
        data = await _api_get(f"/api/academia/earnings/{user_id}")
        if not data or not data.get("instructor_id"):
            text = "אינך רשום כמדריך עדיין. השתמש ב-/become_instructor."
        else:
            t = data.get("totals", {})
            split = data.get("split", {})
            text = (
                "💰 <b>ההכנסות שלך</b>\n\n"
                f"מכירות: <b>{t.get('sales_count', 0)}</b>\n"
                f"סך ברוטו: <b>{t.get('gross_ils', 0):.2f}₪</b>\n"
                f"חלוקה: {split.get('instructor_pct', 70)}% מדריך / "
                f"{split.get('platform_pct', 30)}% פלטפורמה\n\n"
                f"💵 הרווחת: <b>{t.get('instructor_cut_ils', 0):.2f}₪</b>\n"
                f"⏳ ממתין לתשלום: <b>{t.get('unpaid_ils', 0):.2f}₪</b>\n"
                f"✅ שולם: <b>{t.get('paid_ils', 0):.2f}₪</b>\n"
            )
        kb = _back_home_kb()
        if edit_msg:
            await edit_msg.edit_text(text, reply_markup=kb)
        else:
            await bot.send_message(chat_id, text, reply_markup=kb)
    except Exception:
        log.exception("_show_earnings failed")
        await bot.send_message(
            chat_id, "שגיאה בטעינת ההכנסות.", reply_markup=_back_home_kb()
        )


# ---- Wizard cancel ----------------------------------------------------------

@dp.callback_query(F.data == "wiz:cancel")
async def cb_wiz_cancel(cq: CallbackQuery) -> None:
    _wizards.pop(cq.from_user.id, None)
    try:
        is_instr, is_approved = await _instructor_status(cq.from_user.id)
        await cq.message.edit_text(
            "בוטל. " + WELCOME, reply_markup=main_menu_kb(is_instr, is_approved)
        )
        await cq.answer("בוטל")
    except Exception:
        log.exception("cb_wiz_cancel failed")


# ---- Wizard text router (must be LAST message handler) ----------------------

@dp.message(F.text & ~F.text.startswith("/"))
async def wizard_router(msg: Message) -> None:
    """Route plain-text replies into an active wizard, if any."""
    state = _wizards.get(msg.from_user.id)
    if not state:
        return  # no active wizard — silently ignore
    try:
        if state["flow"] == "register":
            await _wizard_register_step(msg, state)
        elif state["flow"] == "upload":
            await _wizard_upload_step(msg, state)
    except Exception:
        log.exception("wizard_router failed")
        await msg.answer("שגיאה בתהליך, נסה שוב.", reply_markup=_back_home_kb())
        _wizards.pop(msg.from_user.id, None)


async def _wizard_register_step(msg: Message, state: dict) -> None:
    text = (msg.text or "").strip()
    user_id = msg.from_user.id

    if state["step"] == "display_name":
        if len(text) > 200:
            await msg.answer("שם ארוך מדי (עד 200 תווים). נסה שוב.")
            return
        state["data"]["display_name"] = text
        state["step"] = "bio"
        await msg.answer(
            "שלב 2/4 — כתוב ביוגרפיה קצרה (עד 4000 תווים) שתופיע בעמוד הקורסים שלך:",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "bio":
        if len(text) > 4000:
            await msg.answer("ביו ארוך מדי (עד 4000 תווים). נסה שוב.")
            return
        state["data"]["bio_he"] = text
        state["step"] = "wallet"
        await msg.answer(
            "שלב 3/4 — כתובת ארנק לתשלומים (TON או BSC). "
            "אפשר לדלג עם המילה <code>דלג</code>:",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "wallet":
        wallet = None if text in ("דלג", "skip", "-") else text
        if wallet and len(wallet) > 200:
            await msg.answer("הכתובת ארוכה מדי. נסה שוב.")
            return
        state["data"]["payout_wallet"] = wallet
        state["step"] = "phone"
        await msg.answer(
            "שלב 4/4 — מספר טלפון ל-Bit / PayBox (תלמידים יוכלו לשלם אליך ישירות). "
            "אפשר לדלג עם <code>דלג</code>:",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "phone":
        phone = None if text in ("דלג", "skip", "-") else text
        if phone:
            cleaned = phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
            if not cleaned.isdigit() or len(phone) > 50:
                await msg.answer("טלפון לא תקין. ספרות בלבד (אפשר עם +, רווחים, מקפים), עד 50 תווים.")
                return
        state["data"]["payout_phone"] = phone
        # Submit
        result = await _api_post(
            "/api/academia/instructor/register",
            {
                "user_id": user_id,
                "display_name": state["data"].get("display_name"),
                "bio_he": state["data"].get("bio_he"),
                "payout_wallet": state["data"].get("payout_wallet"),
                "payout_phone": phone,
            },
        )
        _wizards.pop(user_id, None)
        if not result:
            await msg.answer(
                "❌ לא הצלחנו לשמור את הבקשה. נסה שוב מאוחר יותר.",
                reply_markup=_back_home_kb(),
            )
            return
        phone_note = (
            "\n\n📱 הטלפון נשמר — תלמידים יראו אופציית Bit/PayBox עבור הקורסים שלך."
            if phone else ""
        )
        await msg.answer(
            "✅ <b>הבקשה התקבלה!</b>\n\n"
            f"{result.get('message', 'ממתין לאישור מנהל')}"
            f"{phone_note}\n\n"
            "תקבל הודעה ברגע שתאושר ותוכל להעלות קורסים.",
            reply_markup=_back_home_kb(),
        )


async def _wizard_upload_step(msg: Message, state: dict) -> None:
    text = (msg.text or "").strip()
    user_id = msg.from_user.id

    if state["step"] == "slug":
        slug = text.lower()
        if not slug or len(slug) > 120 or not all(c.isalnum() or c in "-_" for c in slug):
            await msg.answer(
                "מזהה לא תקין. השתמש באותיות באנגלית, מספרים, מקפים בלבד."
            )
            return
        state["data"]["slug"] = slug
        state["step"] = "title"
        await msg.answer("שלב 2/7 — שם הקורס בעברית (עד 300 תווים):", reply_markup=_cancel_kb())
        return

    if state["step"] == "title":
        if not text or len(text) > 300:
            await msg.answer("שם לא תקין. נסה שוב.")
            return
        state["data"]["title_he"] = text
        state["step"] = "description"
        await msg.answer(
            "שלב 3/7 — תיאור הקורס (אפשר לדלג עם <code>דלג</code>):",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "description":
        state["data"]["description_he"] = None if text in ("דלג", "skip", "-") else text
        state["step"] = "price_ils"
        await msg.answer("שלב 4/7 — מחיר בשקלים (מספר, למשל <code>149</code>):", reply_markup=_cancel_kb())
        return

    if state["step"] == "price_ils":
        try:
            price = float(text.replace(",", "."))
            if price < 0:
                raise ValueError
        except ValueError:
            await msg.answer("מחיר לא תקין. הקלד מספר.")
            return
        state["data"]["price_ils"] = price
        state["step"] = "price_slh"
        await msg.answer(
            "שלב 5/7 — מחיר ב-SLH (מספר, למשל <code>0.5</code>, או <code>0</code>):",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "price_slh":
        try:
            price_slh = float(text.replace(",", "."))
            if price_slh < 0:
                raise ValueError
        except ValueError:
            await msg.answer("מחיר לא תקין. הקלד מספר.")
            return
        state["data"]["price_slh"] = price_slh
        state["step"] = "materials"
        await msg.answer(
            "שלב 6/7 — קישור לחומרי הקורס (URL, אפשר לדלג):",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "materials":
        state["data"]["materials_url"] = None if text in ("דלג", "skip", "-") else text
        state["step"] = "preview"
        await msg.answer(
            "שלב 7/7 — קישור לתצוגה מקדימה (URL, אפשר לדלג):",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "preview":
        state["data"]["preview_url"] = None if text in ("דלג", "skip", "-") else text
        # Submit
        payload = {
            "instructor_user_id": user_id,
            "slug": state["data"]["slug"],
            "title_he": state["data"]["title_he"],
            "description_he": state["data"].get("description_he"),
            "price_ils": state["data"].get("price_ils", 0),
            "price_slh": state["data"].get("price_slh", 0),
            "materials_url": state["data"].get("materials_url"),
            "preview_url": state["data"].get("preview_url"),
            "language": "he",
        }
        result = await _api_post("/api/academia/course/create", payload)
        _wizards.pop(user_id, None)
        if not result:
            await msg.answer(
                "❌ לא הצלחנו ליצור את הקורס. ייתכן שהמזהה כבר תפוס. "
                "נסה שוב עם מזהה אחר.",
                reply_markup=_back_home_kb(),
            )
            return
        await msg.answer(
            "✅ <b>הקורס נוצר!</b>\n\n"
            f"מזהה: <code>{result.get('slug')}</code>\n"
            f"סטטוס: {result.get('approval_status', 'pending')}\n\n"
            "הקורס יופיע בקטלוג לאחר אישור מנהל.",
            reply_markup=_back_home_kb(),
        )


if __name__ == "__main__":
    asyncio.run(main())
