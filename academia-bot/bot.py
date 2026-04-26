"""@WEWORK_teamviwer_bot â€” SLH Academia licensing bot.

aiogram 3.x. Sells academy licenses paid via TON / BNB / ILS (Bit manual).
Polls Railway /api/payment/status/{user_id} to confirm and then writes to
academy_licenses. No fake success â€” every confirm hits the Railway API.

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
    "[DEMO] ×ž×‘×•× ×œ-SLH â€” ×”×©×§×¢×” ×•×§×¨×™×¤×˜×• ×œ×™×©×¨××œ×™×",
    "×§×•×¨×¡ ×™×¡×•×“ ×©×¢×•×–×¨ ×œ×”×‘×™×Ÿ ××ª ×”×©×•×§, ×”×¡×™×›×•× ×™×, ×•×”×¤×œ×˜×¤×•×¨×ž×”.",
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
        [InlineKeyboardButton(text="×¨×›×•×© ×¨×™×©×™×•×Ÿ", callback_data="menu:buy")],
        [
            InlineKeyboardButton(
                text="×”×¨×™×©×™×•× ×•×ª ×©×œ×™", callback_data="menu:my_licenses"
            )
        ],
    ]
    if is_approved:
        rows.append(
            [InlineKeyboardButton(text="ðŸ“¤ ×”×¢×œ×” ×§×•×¨×¡", callback_data="instr:upload")]
        )
        rows.append(
            [InlineKeyboardButton(text="ðŸ’° ×”×”×›× ×¡×•×ª ×©×œ×™", callback_data="instr:earnings")]
        )
    elif is_instructor:
        rows.append(
            [InlineKeyboardButton(text="â³ ×ž×ž×ª×™×Ÿ ×œ××™×©×•×¨ ×ž×“×¨×™×š", callback_data="instr:pending")]
        )
    else:
        rows.append(
            [InlineKeyboardButton(text="ðŸŽ“ ×”×¦×˜×¨×£ ×›×ž×“×¨×™×š", callback_data="instr:register")]
        )
    rows.append([InlineKeyboardButton(text="×ª×ž×™×›×”", callback_data="menu:support")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def course_list_kb(courses) -> InlineKeyboardMarkup:
    rows = []
    for c in courses:
        price_ils = c["price_ils"] or 0
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{c['title_he']} Â· {price_ils}â‚ª",
                    callback_data=f"course:{c['id']}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="×—×–×¨×”", callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_methods_kb(course_id: int, allow_phone_pay: bool = False) -> InlineKeyboardMarkup:
    """Build payment menu. Bit/PayBox shown only when the course's instructor
    has registered a payout phone (allow_phone_pay=True). Osif's own courses
    have no phone configured so those buttons are hidden."""
    rows = [
        [
            InlineKeyboardButton(text="ðŸ’Ž TON", callback_data=f"pay:{course_id}:ton"),
            InlineKeyboardButton(text="ðŸŸ¡ BNB / BSC", callback_data=f"pay:{course_id}:bsc"),
        ],
        [
            InlineKeyboardButton(text="ðŸ¦Š MetaMask (BSC)", callback_data=f"pay:{course_id}:metamask"),
            InlineKeyboardButton(text="ðŸ¥ž PancakeSwap â†’ SLH", callback_data=f"pay:{course_id}:pancakeswap"),
        ],
        [
            InlineKeyboardButton(text="ðŸ¦ ×”×¢×‘×¨×” ×‘× ×§××™×ª", callback_data=f"pay:{course_id}:bank"),
            InlineKeyboardButton(text="â­ Telegram Stars", callback_data=f"pay:{course_id}:stars"),
        ],
    ]
    if allow_phone_pay:
        rows.append([
            InlineKeyboardButton(text="ðŸ“± Bit / PayBox (×œ×ž×“×¨×™×š)", callback_data=f"pay:{course_id}:phone"),
        ])
    rows.append([
        InlineKeyboardButton(text="ðŸ’¼ ×—×œ×•×¤×”: ×–×ž×Ÿ ×¢×‘×•×“×” / ×–×”×‘ / ××—×¨", callback_data=f"pay:{course_id}:alt"),
    ])
    rows.append([InlineKeyboardButton(text="×—×–×¨×”", callback_data="menu:buy")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ----------------------------------------------------------------------------
# Handlers
# ----------------------------------------------------------------------------


WELCOME = (
    "ðŸŽ“ <b>×‘×¨×•×š ×”×‘× ×œ××§×“×ž×™×™×ª SLH</b>\n\n"
    "×›××Ÿ ××ª×” ×¨×•×›×© ×¨×™×©×™×•× ×•×ª ×œ×§×•×¨×¡×™ ×”×”×©×§×¢×” ×•×”×§×¨×™×¤×˜×• ×©×œ SLH.\n"
    "×‘×—×¨ ×¤×¢×•×œ×” ×ž×”×ª×¤×¨×™×˜:"
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
            "<b>×¤×§×•×“×•×ª</b>\n"
            "/start â€” ×ª×¤×¨×™×˜ ×¨××©×™\n"
            "/buy â€” ×¨×›×™×©×ª ×§×•×¨×¡\n"
            "/my_licenses â€” ×”×¨×™×©×™×•× ×•×ª ×©×œ×™\n"
            "/become_instructor â€” ×”×¦×˜×¨×£ ×›×ž×“×¨×™×š\n"
            "/upload_course â€” ×”×¢×œ×” ×§×•×¨×¡ (×ž×“×¨×™×›×™× ×ž××•×©×¨×™× ×‘×œ×‘×“)\n"
            "/my_earnings â€” ×”×”×›× ×¡×•×ª ×©×œ×™ ×›×ž×“×¨×™×š\n"
            "/help â€” ×ž×¡×š ×–×”\n\n"
            f"×ª×ž×™×›×”: {SUPPORT_HANDLE}"
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
                "×©×’×™××” ×‘×˜×¢×™× ×ª ×”×§×•×¨×¡×™×. × ×¡×” ×©×•×‘ ××• ×¤× ×” ×œ×ª×ž×™×›×” "
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
                "×©×’×™××” ×‘×˜×¢×™× ×ª ×”×¨×™×©×™×•× ×•×ª. × ×¡×” ×©×•×‘ ××• ×¤× ×” ×œ×ª×ž×™×›×” "
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
        await cq.answer("×©×’×™××”", show_alert=False)


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
            f"×œ×ª×ž×™×›×”: {SUPPORT_HANDLE}\n× ×—×–×•×¨ ××œ×™×š ×‘×”×§×“×.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="×—×–×¨×”", callback_data="menu:home"
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
            await cq.answer("×”×§×•×¨×¡ ×œ× × ×ž×¦×", show_alert=True)
            return

        included_lines = ["ðŸ“š <b>×ž×” ×›×œ×•×œ ×‘×§×•×¨×¡:</b>"]
        if c["materials_url"]:
            included_lines.append("â€¢ ×’×™×©×” ×ž×œ××” ×œ×—×•×ž×¨×™ ×”×§×•×¨×¡ (×•×™×“××• + ×˜×§×¡×˜)")
            included_lines.append("â€¢ ×¨×™×©×™×•×Ÿ ×œ×›×œ ×”×—×™×™× â€” ×¦×¤×” ×ž×ª×™ ×©×ª×¨×¦×”")
        else:
            included_lines.append("â€¢ ×ª×•×›×Ÿ ×‘×”×›× ×” â€” ×¤× ×” ×œ×ª×ž×™×›×” ×œ×¤×¨×˜×™×")
        included_lines.append("â€¢ ×ª×¢×•×“×ª ×”×©×œ×ž×” (Premium ×œ×‘×•×˜)")
        included_lines.append("â€¢ ×”×©×ª×ª×¤×•×ª ×‘×§×”×™×œ×ª ×œ×•×ž×“×™ SLH")
        included = "\n".join(included_lines)

        instructor_line = (
            f"\nðŸ‘¨\u200dðŸ« ×ž×“×¨×™×š: {instructor_name}\n" if instructor_name else ""
        )

        text = (
            f"<b>{c['title_he']}</b>\n"
            f"{instructor_line}\n"
            f"{c['description_he'] or '×ª×™××•×¨ ×ž×œ× ×‘×§×¨×•×‘ â€” ×¤× ×” ×œ×ª×ž×™×›×” ×œ×ž×™×“×¢.'}\n\n"
            f"{included}\n\n"
            f"ðŸ’° <b>×ž×—×™×¨:</b> {c['price_ils'] or 0}â‚ª Â· {c['price_slh'] or 0} SLH\n\n"
            f"×‘×—×¨ ××ž×¦×¢×™ ×ª×©×œ×•× ×ž×ª×•×š ×”×¨×©×ª ×”×ž×œ××” ×©×œ× ×•:"
        )
        await cq.message.edit_text(
            text,
            reply_markup=payment_methods_kb(course_id, allow_phone_pay=allow_phone_pay),
            disable_web_page_preview=True,
        )
        await cq.answer()
    except Exception:
        log.exception("cb_course failed")
        await cq.answer("×©×’×™××” ×‘×˜×¢×™× ×ª ×”×§×•×¨×¡", show_alert=True)


@dp.callback_query(F.data.startswith("pay:"))
async def cb_pay(cq: CallbackQuery) -> None:
    # Acknowledge IMMEDIATELY so Telegram dismisses the loading spinner.
    # Without this, the user sees a hung click and may type new commands,
    # causing the actual payment response to surface out-of-order later.
    try:
        await cq.answer("×˜×•×¢×Ÿ ××ž×¦×¢×™ ×ª×©×œ×•×â€¦")
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
            await cq.answer("×”×§×•×¨×¡ ×œ× × ×ž×¦×", show_alert=True)
            return

        # Telegram Stars (XTR) â€” native invoice, no manual flow.
        if method == "stars":
            await _send_stars_invoice(cq.message.chat.id, c)
            return

        # Create a pending payment record by calling Railway API.
        payment_id, instructions = await _create_payment(
            user_id=user_id, course=c, method=method
        )
        if not payment_id:
            await cq.message.edit_text(
                "×©×’×™××” ×‘×™×¦×™×¨×ª ×”×ª×©×œ×•×. × ×¡×” ×©×•×‘ ×ž××•×—×¨ ×™×•×ª×¨ ××• ×¤× ×” ×œ×ª×ž×™×›×” "
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
                    text="ðŸŒ ×¤×ª×— ×˜×•×¤×¡ ×‘× ×§ (Mini App)",
                    web_app=WebAppInfo(url="https://slh-nft.com/buy.html#bank"),
                )
            ])
        elif method == "pancakeswap":
            slh_contract = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"
            action_rows.append([
                InlineKeyboardButton(
                    text="ðŸ¥ž ×¤×ª×— PancakeSwap",
                    url=f"https://pancakeswap.finance/swap?outputCurrency={slh_contract}&chain=bsc",
                )
            ])
        action_rows.append([
            InlineKeyboardButton(text="×—×–×¨×” ×œ×ª×¤×¨×™×˜", callback_data="menu:home")
        ])

        await cq.message.edit_text(
            instructions + "\n\n×× ×™ ×ž××ž×ª ××•×˜×•×ž×˜×™×ª ×¢×“ 10 ×“×§×•×ª. ×”×ž×ª×Ÿ ×œ×”×•×“×¢×”â€¦",
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
                    caption=f"ðŸ“· ×¡×¨×•×§ ×¢× Tonkeeper / @wallet â€” {amount} TON ×œ-{addr[:8]}â€¦",
                    uri=uri,
                )
        elif method in ("bsc", "metamask"):
            addr = cfg.get("bsc_genesis_address") or ""
            amount = float(cfg.get("premium_min_bnb") or 0.0005)
            if addr:
                uri = _wallet_uri(method, addr, amount)
                await _send_payment_qr(
                    cq.message.chat.id,
                    caption=f"ðŸ“· ×¡×¨×•×§ ×¢× MetaMask / Trust â€” {amount} BNB ×œ-{addr[:8]}â€¦",
                    uri=uri,
                )
        elif method == "pancakeswap":
            await _send_payment_qr(
                cq.message.chat.id,
                caption="ðŸ“· ×¡×¨×•×§ ×œ×¤×ª×™×—×ª PancakeSwap ×‘××¨× ×§ ×©×œ×š",
                uri="https://pancakeswap.finance/swap?outputCurrency=0xACb0A09414CEA1C879c67bB7A877E4e19480f022&chain=bsc",
            )

        # Background poll loop (skip for alt/phone â€” manual-only flows).
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
                "×©×’×™××” ×‘×˜×™×¤×•×œ ×‘×ª×©×œ×•×. × ×¡×” ×©×•×‘ ××• ×¤× ×” ×œ-" + SUPPORT_HANDLE,
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
            text = "××™×Ÿ ×§×•×¨×¡×™× ×–×ž×™× ×™× ×›×¨×’×¢."
            if edit_msg:
                await edit_msg.edit_text(text, reply_markup=main_menu_kb())
            else:
                await bot.send_message(
                    chat_id, text, reply_markup=main_menu_kb()
                )
            return

        text = "<b>×§×•×¨×¡×™× ×–×ž×™× ×™×:</b>\n×‘×—×¨ ×§×•×¨×¡ ×œ×”×ž×©×š."
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
                "×©×’×™××” ×‘×˜×¢×™× ×ª ×”×§×•×¨×¡×™×. × ×¡×” ×©×•×‘ ×ž××•×—×¨ ×™×•×ª×¨.",
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
                "××™×Ÿ ×œ×š ×¨×™×©×™×•× ×•×ª ×¤×¢×™×œ×™× ×¢×“×™×™×Ÿ.\n"
                "×œ×—×¥ /buy ×›×“×™ ×œ×¨×›×•×© ×§×•×¨×¡."
            )
        else:
            lines = ["<b>×”×¨×™×©×™×•× ×•×ª ×©×œ×š:</b>", ""]
            for r in rows:
                date = (
                    r["purchased_at"].strftime("%Y-%m-%d")
                    if r["purchased_at"]
                    else "â€”"
                )
                status = "×¤×¢×™×œ" if r["status"] == "active" else r["status"]
                link = (
                    f'\n<a href="{r["materials_url"]}">×’×™×©×” ×œ×—×•×ž×¨×™×</a>'
                    if r["materials_url"]
                    else ""
                )
                lines.append(
                    f"â€¢ {r['title_he']}\n  × ×¨×›×©: {date} Â· {status}{link}"
                )
            text = "\n".join(lines)

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="×—×–×¨×”", callback_data="menu:home"
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
            chat_id, "×©×’×™××” ×‘×˜×¢×™× ×ª ×”×¨×™×©×™×•× ×•×ª.", reply_markup=main_menu_kb()
        )


def _qr_image_url(data: str, size: int = 300) -> str:
    """Public QR code generator (no install). Returns image URL ready for send_photo."""
    return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={quote_plus(data)}"


def _wallet_uri(method: str, address: str, amount: float) -> str:
    """Build a wallet-deep-link URI that mobile wallets can scan/open.

    TON: ton://transfer/{addr}?amount={nano}
    BSC: ethereum:{addr}@56?value={wei}  (EIP-681 â€” Trust/MetaMask understand)
    """
    if method == "ton":
        nano = int(amount * 1_000_000_000)
        return f"ton://transfer/{address}?amount={nano}"
    if method in ("bsc", "metamask"):
        wei = int(amount * 1_000_000_000_000_000_000)
        return f"ethereum:{address}@56?value={wei}"
    return address  # PancakeSwap etc â€” just encode the address


async def _send_payment_qr(chat_id: int, caption: str, uri: str) -> None:
    """Send a QR photo to the user. Failures are logged, not raised â€” the
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
    tx_hash later â€” see _check_status). For ILS/Bit we record via
    /api/payment/external/record so Osif can approve manually via the
    admin panel; the bot polls payment status to pick up the approval.
    """
    cfg = await _api_config()
    ref = f"ACAD-{user_id}-{course['id']}-{int(datetime.utcnow().timestamp())}"

    if method == "ton":
        addr = cfg.get("ton_address") or "â€”"
        min_ton = course["price_slh"] or cfg.get("premium_min_ton") or 0.01
        instr = (
            f"<b>×ª×©×œ×•× ×‘-TON</b>\n\n"
            f"×©×œ×— <code>{min_ton}</code> TON ×œ×›×ª×•×‘×ª:\n"
            f"<code>{addr}</code>\n\n"
            f"×ž×–×”×” ×ª×©×œ×•×: <code>{ref}</code>"
        )
        return ref, instr

    if method == "bsc":
        addr = cfg.get("bsc_genesis_address") or "â€”"
        min_bnb = cfg.get("premium_min_bnb") or 0.0005
        instr = (
            f"<b>×ª×©×œ×•× ×‘-BNB (BSC)</b>\n\n"
            f"×©×œ×— ×œ×¤×—×•×ª <code>{min_bnb}</code> BNB ×œ×›×ª×•×‘×ª:\n"
            f"<code>{addr}</code>\n\n"
            f"×ž×–×”×” ×ª×©×œ×•×: <code>{ref}</code>"
        )
        return ref, instr

    if method == "metamask":
        addr = cfg.get("bsc_genesis_address") or "â€”"
        min_bnb = cfg.get("premium_min_bnb") or 0.0005
        instr = (
            f"<b>×ª×©×œ×•× ×‘-MetaMask (BSC)</b>\n\n"
            f"1. ×¤×ª×— MetaMask ×•×‘×—×¨ ×¨×©×ª BNB Smart Chain.\n"
            f"2. ×©×œ×— ×œ×¤×—×•×ª <code>{min_bnb}</code> BNB ×œ×›×ª×•×‘×ª:\n"
            f"<code>{addr}</code>\n\n"
            f"×ž×–×”×” ×ª×©×œ×•×: <code>{ref}</code>\n\n"
            f"ðŸ’¡ ××™×Ÿ ×œ×š MetaMask? ×”×ª×§×Ÿ ×ž-metamask.io ××• ×”×©×ª×ž×© ×‘-Trust Wallet."
        )
        return ref, instr

    if method == "pancakeswap":
        slh_contract = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"
        instr = (
            f"<b>×¨×›×™×©×” ×“×¨×š PancakeSwap (SLH)</b>\n\n"
            f"1. ×¤×ª×—: https://pancakeswap.finance/swap?outputCurrency={slh_contract}&chain=bsc\n"
            f"2. ×”×—×œ×£ BNB â†’ SLH ×œ×¤×™ ×”×ž×—×™×¨ ({course['price_slh'] or 0} SLH).\n"
            f"3. ×©×œ×— ××ª ×”-SLH ×œ×›×ª×•×‘×ª Genesis:\n"
            f"<code>{cfg.get('bsc_genesis_address') or 'â€”'}</code>\n\n"
            f"×ž×–×”×”: <code>{ref}</code>\n\n"
            f"ðŸ’Ž ×›×œ ×¨×›×™×©×ª SLH ×ž×¢× ×™×§×” ×’× ZVK ×‘×•× ×•×¡ + REP points."
        )
        return ref, instr

    if method == "bank":
        # Bank transfer to Tzvika (CEO) â€” same flow as buy.html
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
            f"<b>×”×¢×‘×¨×” ×‘× ×§××™×ª</b>\n\n"
            f"×œ×§×‘×œ×ª ×¤×¨×˜×™ ×—×©×‘×•×Ÿ ×‘× ×§ (×œ×¦×‘×™×§×” ×§××•×¤×ž×Ÿ, ×ž× ×›\"×œ) ×¤× ×” ×œ-{SUPPORT_HANDLE}.\n"
            f"×¡×›×•×: <code>{course['price_ils']}</code>â‚ª\n"
            f"×ž×–×”×” ×ª×©×œ×•×: <code>{ref}</code>\n\n"
            f"××• ×ž×œ× ××ª ×”×˜×•×¤×¡ ×”×ž×œ× (8 ×©×“×•×ª) ×‘××ª×¨:\n"
            f"https://slh-nft.com/buy.html#bank\n\n"
            f"×œ××—×¨ ××™×©×•×¨ ×™×“× ×™ ×ª×§×‘×œ ××ª ×”×’×™×©×” ×œ×—×•×ž×¨×™×."
        )
        return ref, instr

    if method == "phone":
        # Bit/PayBox routing to instructor's payout_phone (Phase 2 â€” requires
        # academy_instructors.payout_phone column and per-course lookup).
        instr = (
            f"<b>ðŸ“± Bit / PayBox ×œ×ž×“×¨×™×š</b>\n\n"
            f"×©×™×˜×ª ×ª×©×œ×•× ×–×• ×–×ž×™× ×” ×¨×§ ×›××©×¨ ×”×ž×“×¨×™×š ×”×’×“×™×¨ ×˜×œ×¤×•×Ÿ.\n"
            f"×¤× ×” ×œ×ž×“×¨×™×š ×™×©×™×¨×•×ª ××• ×œ-{SUPPORT_HANDLE} ×œ×ž×™×“×¢ × ×•×¡×£.\n\n"
            f"×ž×–×”×”: <code>{ref}</code>"
        )
        return ref, instr

    if method == "alt":
        instr = (
            f"<b>ðŸ’¼ ×—×œ×•×¤×•×ª ×ª×©×œ×•×</b>\n\n"
            f"×× ×• ×ž×§×‘×œ×™× ×’×:\n"
            f"â€¢ â± ×–×ž×Ÿ ×¢×‘×•×“×” / ×”×¡×¤×§ (×ª×¨×•×ž×” ×œ×¤×¨×•×™×§×˜)\n"
            f"â€¢ ðŸ¥‡ ×–×”×‘ ×¤×™×–×™ (×œ×¤×™ ×©×•×•×™ ×©×•×§)\n"
            f"â€¢ ðŸª™ OTC ×§×¨×™×¤×˜×• (USDT, USDC, BTC, ETH)\n"
            f"â€¢ ðŸ”„ Swap ×ž×‘×•×˜×™× ××—×¨×™× ×©×œ× ×• (ZVK, MNH)\n\n"
            f"×¤× ×” ×œ-{SUPPORT_HANDLE} ×¢× ×”×ž×–×”×” <code>{ref}</code> "
            f"×œ×‘×—×™×¨×ª ×”×ž×¡×œ×•×œ ×”×ž×ª××™× ×œ×š."
        )
        return ref, instr

    return None, ""


async def _check_status(user_id: int, course_id: int | None = None) -> bool:
    """Return True iff user has either:
      (a) an active `academy_licenses` row for this course in our own _pool
          (authoritative â€” this bot is what writes them), OR
      (b) an `approved` external_payment reference in the Railway API (covers the
          case where the admin approved a TON/bank payment manually via admin panel
          but the bot hadn't yet polled success), OR
      (c) bot-level premium for this BOT_NAME via Railway /api/payment/status
          (legacy fallback for non-course flows).

    The previous version only checked (c), which caused ACAD-* timeouts for
    successful course purchases â€” academy writes to academy_licenses on the
    bot's own DB, not to premium_users.
    """
    # (a) local DB â€” authoritative
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
                    # Approved payment exists â€” treat as success signal
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

            # Confirmed â€” grant license (idempotent per user+course).
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
            link = course["materials_url"] or "â€”"
            await bot.send_message(
                chat_id,
                f"âœ… <b>×”×ª×©×œ×•× ××•×©×¨</b>\n\n"
                f"×”×¨×™×©×™×•×Ÿ ×œ'{course['title_he']}' ×¤×¢×™×œ.\n"
                f'×’×™×©×” ×œ×—×•×ž×¨×™×: <a href="{link}">{link}</a>',
                disable_web_page_preview=False,
            )
            return

        # Timeout.
        await bot.send_message(
            chat_id,
            "×œ× ×”×¦×œ×—× ×• ×œ××ž×ª ××ª ×”×ª×©×œ×•× ×‘-10 ×“×§×•×ª ×”××—×¨×•× ×•×ª.\n"
            f"×× ×©×™×œ×ž×ª, ×¤× ×” ×œ-{SUPPORT_HANDLE} ×¢× ×ž×–×”×” "
            f"<code>{payment_id}</code>.",
        )
    except Exception:
        log.exception("_wait_and_grant failed")
        try:
            await bot.send_message(
                chat_id,
                f"×©×’×™××” ×‘××™×ž×•×ª. ×¤× ×” ×œ×ª×ž×™×›×” {SUPPORT_HANDLE} "
                f"(×ž×–×”×”: {payment_id}).",
            )
        except Exception:
            log.exception("failed to notify user of _wait_and_grant error")


# ----------------------------------------------------------------------------
# Telegram Stars (XTR) â€” native invoice flow
# ----------------------------------------------------------------------------

# Conversion: 1 XTR â‰ˆ $0.013 â‰ˆ â‚ª0.05 (rough)
ILS_PER_STAR = 0.05


def _course_to_stars(price_ils: float | None) -> int:
    """Convert ILS price to Telegram Stars amount. Minimum 1 star."""
    p = float(price_ils or 0)
    return max(1, int(round(p / ILS_PER_STAR)))


async def _send_stars_invoice(chat_id: int, course) -> None:
    """Send a native Telegram Stars invoice. The user pays inside Telegram â€”
    no bank, no crypto. We grant the license on successful_payment."""
    stars = _course_to_stars(course["price_ils"])
    title = course["title_he"][:32]  # Telegram limit
    description = (course["description_he"] or "×¨×™×©×™×•×Ÿ ×œ×›×œ ×”×—×™×™× ×œ×§×•×¨×¡ SLH")[:255]
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
                "âŒ ×œ× ×”×¦×œ×—× ×• ×œ×¤×ª×•×— ×—×©×‘×•× ×™×ª Stars. ×•×“× ×©××¤×œ×™×§×¦×™×™×ª Telegram ×ž×¢×•×“×›× ×ª, "
                f"××• ×¤× ×” ×œ-{SUPPORT_HANDLE}.",
            )
        except Exception:
            pass


@dp.pre_checkout_query()
async def on_pre_checkout(q: PreCheckoutQuery) -> None:
    """Telegram requires explicit ack for every pre_checkout. We always
    approve â€” the actual ledger entry happens on successful_payment."""
    try:
        await bot.answer_pre_checkout_query(q.id, ok=True)
    except Exception:
        log.exception("on_pre_checkout failed for id=%s", q.id)


@dp.message(F.successful_payment)
async def on_successful_payment(msg: Message) -> None:
    """Stars payment confirmed by Telegram â€” grant the license immediately."""
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
                    f"âš ï¸ ×”×ª×©×œ×•× ×”×ª×§×‘×œ ××‘×œ ×”×§×•×¨×¡ ×œ× × ×ž×¦×. ×¤× ×” ×œ-{SUPPORT_HANDLE} "
                    f"×¢× ×ž×–×”×”: {sp.telegram_payment_charge_id}"
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
        link = c["materials_url"] or "â€”"
        await msg.answer(
            f"âœ… <b>×”×ª×©×œ×•× ×‘-Stars ××•×©×¨ â­</b>\n\n"
            f"×”×¨×™×©×™×•×Ÿ ×œ'{c['title_he']}' ×¤×¢×™×œ.\n"
            f'×’×™×©×” ×œ×—×•×ž×¨×™×: <a href="{link}">{link}</a>',
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

    # Coordination: register inbound + post ready (no-op if env unset)
    try:
        from shared.coordination import init_coordination_for_bot
        await init_coordination_for_bot(
            bot, dp,
            name="academia-bot",
            username=me.username,
        )
    except Exception as e:
        log.warning("coordination init failed: %s", e)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


# ============================================================================
# UGC EXTENSION â€” instructor onboarding, course upload, earnings.
# Talks to Railway /api/academia/* (router academia_ugc.py).
# ============================================================================

# In-memory wizard state. user_id -> {"flow": str, "step": str, "data": dict}.
# Process-local (lost on restart) â€” acceptable for short multi-step flows.
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
            [InlineKeyboardButton(text="âŒ ×‘×™×˜×•×œ", callback_data="wiz:cancel")]
        ]
    )


def _back_home_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="×—×–×¨×” ×œ×ª×¤×¨×™×˜", callback_data="menu:home")]
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
            "â³ <b>×”×‘×§×©×” ×©×œ×š ×›×ž×“×¨×™×š ×ž×ž×ª×™× ×” ×œ××™×©×•×¨ ×ž× ×”×œ.</b>\n\n"
            "×ª×§×‘×œ ×”×•×“×¢×” ×‘×¨×’×¢ ×©×”××™×©×•×¨ ×™×•×©×œ×.",
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
                "âœ… ××ª×” ×›×‘×¨ ×¨×©×•× ×›×ž×“×¨×™×š ×ž××•×©×¨.",
                reply_markup=_back_home_kb(),
            )
            return
        if is_instr:
            await bot.send_message(
                chat_id,
                "â³ ×”×‘×§×©×” ×©×œ×š ×›×ž×“×¨×™×š ×›×‘×¨ × ×©×œ×—×” ×•×ž×ž×ª×™× ×” ×œ××™×©×•×¨.",
                reply_markup=_back_home_kb(),
            )
            return
        _wizards[user_id] = {"flow": "register", "step": "display_name", "data": {}}
        await bot.send_message(
            chat_id,
            "ðŸŽ“ <b>×”×¦×˜×¨×¤×•×ª ×›×ž×“×¨×™×š</b>\n\n"
            "×©×œ×‘ 1/4 â€” ×ž×” ×”×©× ×©×™×•×¦×’ ×œ×ª×œ×ž×™×“×™×? (×¢×“ 200 ×ª×•×•×™×)",
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
                "×ª×—×™×œ×” ×”×¦×˜×¨×£ ×›×ž×“×¨×™×š ×¢× /become_instructor.",
                reply_markup=_back_home_kb(),
            )
            return
        if not is_approved:
            await bot.send_message(
                chat_id,
                "â³ ×”×‘×§×©×” ×©×œ×š ×›×ž×“×¨×™×š ×¢×“×™×™×Ÿ ×œ× ××•×©×¨×”. ×× × ×”×ž×ª×Ÿ.",
                reply_markup=_back_home_kb(),
            )
            return
        _wizards[user_id] = {"flow": "upload", "step": "slug", "data": {}}
        await bot.send_message(
            chat_id,
            "ðŸ“¤ <b>×”×¢×œ××ª ×§×•×¨×¡ ×—×“×©</b>\n\n"
            "×©×œ×‘ 1/7 â€” ×ž×–×”×” (slug) ×‘×× ×’×œ×™×ª (××•×ª×™×•×ª, ×ž×¡×¤×¨×™×, ×ž×§×¤×™×): "
            "×œ×ž×©×œ <code>crypto-101</code>",
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
            text = "××™× ×š ×¨×©×•× ×›×ž×“×¨×™×š ×¢×“×™×™×Ÿ. ×”×©×ª×ž×© ×‘-/become_instructor."
        else:
            t = data.get("totals", {})
            split = data.get("split", {})
            text = (
                "ðŸ’° <b>×”×”×›× ×¡×•×ª ×©×œ×š</b>\n\n"
                f"×ž×›×™×¨×•×ª: <b>{t.get('sales_count', 0)}</b>\n"
                f"×¡×š ×‘×¨×•×˜×•: <b>{t.get('gross_ils', 0):.2f}â‚ª</b>\n"
                f"×—×œ×•×§×”: {split.get('instructor_pct', 70)}% ×ž×“×¨×™×š / "
                f"{split.get('platform_pct', 30)}% ×¤×œ×˜×¤×•×¨×ž×”\n\n"
                f"ðŸ’µ ×”×¨×•×•×—×ª: <b>{t.get('instructor_cut_ils', 0):.2f}â‚ª</b>\n"
                f"â³ ×ž×ž×ª×™×Ÿ ×œ×ª×©×œ×•×: <b>{t.get('unpaid_ils', 0):.2f}â‚ª</b>\n"
                f"âœ… ×©×•×œ×: <b>{t.get('paid_ils', 0):.2f}â‚ª</b>\n"
            )
        kb = _back_home_kb()
        if edit_msg:
            await edit_msg.edit_text(text, reply_markup=kb)
        else:
            await bot.send_message(chat_id, text, reply_markup=kb)
    except Exception:
        log.exception("_show_earnings failed")
        await bot.send_message(
            chat_id, "×©×’×™××” ×‘×˜×¢×™× ×ª ×”×”×›× ×¡×•×ª.", reply_markup=_back_home_kb()
        )


# ---- Wizard cancel ----------------------------------------------------------

@dp.callback_query(F.data == "wiz:cancel")
async def cb_wiz_cancel(cq: CallbackQuery) -> None:
    _wizards.pop(cq.from_user.id, None)
    try:
        is_instr, is_approved = await _instructor_status(cq.from_user.id)
        await cq.message.edit_text(
            "×‘×•×˜×œ. " + WELCOME, reply_markup=main_menu_kb(is_instr, is_approved)
        )
        await cq.answer("×‘×•×˜×œ")
    except Exception:
        log.exception("cb_wiz_cancel failed")


# ---- Wizard text router (must be LAST message handler) ----------------------

@dp.message(F.text & ~F.text.startswith("/"))
async def wizard_router(msg: Message) -> None:
    """Route plain-text replies into an active wizard, if any."""
    state = _wizards.get(msg.from_user.id)
    if not state:
        return  # no active wizard â€” silently ignore
    try:
        if state["flow"] == "register":
            await _wizard_register_step(msg, state)
        elif state["flow"] == "upload":
            await _wizard_upload_step(msg, state)
    except Exception:
        log.exception("wizard_router failed")
        await msg.answer("×©×’×™××” ×‘×ª×”×œ×™×š, × ×¡×” ×©×•×‘.", reply_markup=_back_home_kb())
        _wizards.pop(msg.from_user.id, None)


async def _wizard_register_step(msg: Message, state: dict) -> None:
    text = (msg.text or "").strip()
    user_id = msg.from_user.id

    if state["step"] == "display_name":
        if len(text) > 200:
            await msg.answer("×©× ××¨×•×š ×ž×“×™ (×¢×“ 200 ×ª×•×•×™×). × ×¡×” ×©×•×‘.")
            return
        state["data"]["display_name"] = text
        state["step"] = "bio"
        await msg.answer(
            "×©×œ×‘ 2/4 â€” ×›×ª×•×‘ ×‘×™×•×’×¨×¤×™×” ×§×¦×¨×” (×¢×“ 4000 ×ª×•×•×™×) ×©×ª×•×¤×™×¢ ×‘×¢×ž×•×“ ×”×§×•×¨×¡×™× ×©×œ×š:",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "bio":
        if len(text) > 4000:
            await msg.answer("×‘×™×• ××¨×•×š ×ž×“×™ (×¢×“ 4000 ×ª×•×•×™×). × ×¡×” ×©×•×‘.")
            return
        state["data"]["bio_he"] = text
        state["step"] = "wallet"
        await msg.answer(
            "×©×œ×‘ 3/4 â€” ×›×ª×•×‘×ª ××¨× ×§ ×œ×ª×©×œ×•×ž×™× (TON ××• BSC). "
            "××¤×©×¨ ×œ×“×œ×’ ×¢× ×”×ž×™×œ×” <code>×“×œ×’</code>:",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "wallet":
        wallet = None if text in ("×“×œ×’", "skip", "-") else text
        if wallet and len(wallet) > 200:
            await msg.answer("×”×›×ª×•×‘×ª ××¨×•×›×” ×ž×“×™. × ×¡×” ×©×•×‘.")
            return
        state["data"]["payout_wallet"] = wallet
        state["step"] = "phone"
        await msg.answer(
            "×©×œ×‘ 4/4 â€” ×ž×¡×¤×¨ ×˜×œ×¤×•×Ÿ ×œ-Bit / PayBox (×ª×œ×ž×™×“×™× ×™×•×›×œ×• ×œ×©×œ× ××œ×™×š ×™×©×™×¨×•×ª). "
            "××¤×©×¨ ×œ×“×œ×’ ×¢× <code>×“×œ×’</code>:",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "phone":
        phone = None if text in ("×“×œ×’", "skip", "-") else text
        if phone:
            cleaned = phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
            if not cleaned.isdigit() or len(phone) > 50:
                await msg.answer("×˜×œ×¤×•×Ÿ ×œ× ×ª×§×™×Ÿ. ×¡×¤×¨×•×ª ×‘×œ×‘×“ (××¤×©×¨ ×¢× +, ×¨×•×•×—×™×, ×ž×§×¤×™×), ×¢×“ 50 ×ª×•×•×™×.")
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
                "âŒ ×œ× ×”×¦×œ×—× ×• ×œ×©×ž×•×¨ ××ª ×”×‘×§×©×”. × ×¡×” ×©×•×‘ ×ž××•×—×¨ ×™×•×ª×¨.",
                reply_markup=_back_home_kb(),
            )
            return
        phone_note = (
            "\n\nðŸ“± ×”×˜×œ×¤×•×Ÿ × ×©×ž×¨ â€” ×ª×œ×ž×™×“×™× ×™×¨××• ××•×¤×¦×™×™×ª Bit/PayBox ×¢×‘×•×¨ ×”×§×•×¨×¡×™× ×©×œ×š."
            if phone else ""
        )
        await msg.answer(
            "âœ… <b>×”×‘×§×©×” ×”×ª×§×‘×œ×”!</b>\n\n"
            f"{result.get('message', '×ž×ž×ª×™×Ÿ ×œ××™×©×•×¨ ×ž× ×”×œ')}"
            f"{phone_note}\n\n"
            "×ª×§×‘×œ ×”×•×“×¢×” ×‘×¨×’×¢ ×©×ª××•×©×¨ ×•×ª×•×›×œ ×œ×”×¢×œ×•×ª ×§×•×¨×¡×™×.",
            reply_markup=_back_home_kb(),
        )


async def _wizard_upload_step(msg: Message, state: dict) -> None:
    text = (msg.text or "").strip()
    user_id = msg.from_user.id

    if state["step"] == "slug":
        slug = text.lower()
        if not slug or len(slug) > 120 or not all(c.isalnum() or c in "-_" for c in slug):
            await msg.answer(
                "×ž×–×”×” ×œ× ×ª×§×™×Ÿ. ×”×©×ª×ž×© ×‘××•×ª×™×•×ª ×‘×× ×’×œ×™×ª, ×ž×¡×¤×¨×™×, ×ž×§×¤×™× ×‘×œ×‘×“."
            )
            return
        state["data"]["slug"] = slug
        state["step"] = "title"
        await msg.answer("×©×œ×‘ 2/7 â€” ×©× ×”×§×•×¨×¡ ×‘×¢×‘×¨×™×ª (×¢×“ 300 ×ª×•×•×™×):", reply_markup=_cancel_kb())
        return

    if state["step"] == "title":
        if not text or len(text) > 300:
            await msg.answer("×©× ×œ× ×ª×§×™×Ÿ. × ×¡×” ×©×•×‘.")
            return
        state["data"]["title_he"] = text
        state["step"] = "description"
        await msg.answer(
            "×©×œ×‘ 3/7 â€” ×ª×™××•×¨ ×”×§×•×¨×¡ (××¤×©×¨ ×œ×“×œ×’ ×¢× <code>×“×œ×’</code>):",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "description":
        state["data"]["description_he"] = None if text in ("×“×œ×’", "skip", "-") else text
        state["step"] = "price_ils"
        await msg.answer("×©×œ×‘ 4/7 â€” ×ž×—×™×¨ ×‘×©×§×œ×™× (×ž×¡×¤×¨, ×œ×ž×©×œ <code>149</code>):", reply_markup=_cancel_kb())
        return

    if state["step"] == "price_ils":
        try:
            price = float(text.replace(",", "."))
            if price < 0:
                raise ValueError
        except ValueError:
            await msg.answer("×ž×—×™×¨ ×œ× ×ª×§×™×Ÿ. ×”×§×œ×“ ×ž×¡×¤×¨.")
            return
        state["data"]["price_ils"] = price
        state["step"] = "price_slh"
        await msg.answer(
            "×©×œ×‘ 5/7 â€” ×ž×—×™×¨ ×‘-SLH (×ž×¡×¤×¨, ×œ×ž×©×œ <code>0.5</code>, ××• <code>0</code>):",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "price_slh":
        try:
            price_slh = float(text.replace(",", "."))
            if price_slh < 0:
                raise ValueError
        except ValueError:
            await msg.answer("×ž×—×™×¨ ×œ× ×ª×§×™×Ÿ. ×”×§×œ×“ ×ž×¡×¤×¨.")
            return
        state["data"]["price_slh"] = price_slh
        state["step"] = "materials"
        await msg.answer(
            "×©×œ×‘ 6/7 â€” ×§×™×©×•×¨ ×œ×—×•×ž×¨×™ ×”×§×•×¨×¡ (URL, ××¤×©×¨ ×œ×“×œ×’):",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "materials":
        state["data"]["materials_url"] = None if text in ("×“×œ×’", "skip", "-") else text
        state["step"] = "preview"
        await msg.answer(
            "×©×œ×‘ 7/7 â€” ×§×™×©×•×¨ ×œ×ª×¦×•×’×” ×ž×§×“×™×ž×” (URL, ××¤×©×¨ ×œ×“×œ×’):",
            reply_markup=_cancel_kb(),
        )
        return

    if state["step"] == "preview":
        state["data"]["preview_url"] = None if text in ("×“×œ×’", "skip", "-") else text
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
                "âŒ ×œ× ×”×¦×œ×—× ×• ×œ×™×¦×•×¨ ××ª ×”×§×•×¨×¡. ×™×™×ª×›×Ÿ ×©×”×ž×–×”×” ×›×‘×¨ ×ª×¤×•×¡. "
                "× ×¡×” ×©×•×‘ ×¢× ×ž×–×”×” ××—×¨.",
                reply_markup=_back_home_kb(),
            )
            return
        await msg.answer(
            "âœ… <b>×”×§×•×¨×¡ × ×•×¦×¨!</b>\n\n"
            f"×ž×–×”×”: <code>{result.get('slug')}</code>\n"
            f"×¡×˜×˜×•×¡: {result.get('approval_status', 'pending')}\n\n"
            "×”×§×•×¨×¡ ×™×•×¤×™×¢ ×‘×§×˜×œ×•×’ ×œ××—×¨ ××™×©×•×¨ ×ž× ×”×œ.",
            reply_markup=_back_home_kb(),
        )


if __name__ == "__main__":
    asyncio.run(main())
