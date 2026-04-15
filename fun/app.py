"""
@SLH_community_bot — Main community bot
Updated: April 15, 2026 — New 4-path funnel with campaign tracking

Design principles:
- No friction on first message (removed "send to friend" antipattern)
- Campaign-aware: /start <campaign_id> routes to right flow
- Clear 4 paths: Buyer / Partner / Genesis / Community
- Payment info shown immediately (not after 3 clicks)
- Every interaction tracked to /api/campaign/click
"""
import logging
import os
import asyncio
from typing import Dict, Optional

import aiohttp
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Update, Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, FSInputFile,
)
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.enums import ChatType

from config import (
    BOT_TOKEN, WEBHOOK_BASE, WEBHOOK_SECRET, ADMIN_CHAT_ID,
    GROUP_MONITOR_ID, GROUP_PREMIUM_INVITE_LINK,
    PRICE_TEXT, PRICE_ILS, BANK_DETAILS, ALT_TELEGRAM_ROUTE,
    COMPANY_BSC_WALLET, SLH_BSC_CONTRACT, ASSETS_PROMO_IMAGE_PATH,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = os.getenv("SLH_API_BASE", "https://slh-api-production.up.railway.app")
CAMPAIGN_ID = "shekel_april26"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
fastapi_app = FastAPI()

# In-memory state (for per-user flow tracking)
user_states: Dict[int, Dict] = {}

# ============================================================
# Keyboards
# ============================================================

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """4-path main menu — the FIRST thing users see."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🛒 קונה — ₪{PRICE_ILS} Starter Pack", callback_data="path:buyer")],
        [InlineKeyboardButton(text="🤝 שותף — חינם + 20% עמלה", callback_data="path:partner")],
        [InlineKeyboardButton(text="💎 Genesis — מייסד היסטורי", callback_data="path:genesis")],
        [InlineKeyboardButton(text="🌱 קהילה — חינם, רק לראות", callback_data="path:community")],
        [InlineKeyboardButton(text="🌐 פתח דף קמפיין", url="https://slh-nft.com/promo-shekel.html")],
    ])


def buyer_payment_keyboard() -> InlineKeyboardMarkup:
    """Payment options for Buyer path."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 שלם ב-TON", callback_data="pay:ton")],
        [InlineKeyboardButton(text="🏦 העברה בנקאית", callback_data="pay:bank")],
        [InlineKeyboardButton(text="🟡 שלם ב-BNB", callback_data="pay:bnb")],
        [InlineKeyboardButton(text="⬅️ חזרה לתפריט", callback_data="back:main")],
    ])


def partner_keyboard(affiliate_code: Optional[str] = None) -> InlineKeyboardMarkup:
    """Partner onboarding — copy affiliate link."""
    btns = []
    if affiliate_code:
        share_url = f"https://slh-nft.com/promo-shekel.html?ref={affiliate_code}"
        btns.append([InlineKeyboardButton(text="📤 שתף קישור שלך", url=f"https://t.me/share/url?url={share_url}")])
    btns.extend([
        [InlineKeyboardButton(text="📊 דשבורד שותף", url="https://slh-nft.com/partner-dashboard.html")],
        [InlineKeyboardButton(text="📚 חומרי שיווק", url="https://slh-nft.com/promo-shekel.html")],
        [InlineKeyboardButton(text="⬅️ חזרה לתפריט", callback_data="back:main")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=btns)


def admin_approval_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ אשר", callback_data=f"admin_approve:{user_id}"),
        InlineKeyboardButton(text="❌ דחה", callback_data=f"admin_reject:{user_id}"),
    ]])


# ============================================================
# API calls
# ============================================================

async def api_register_path(
    user_id: int, username: Optional[str], full_name: str,
    path: str, ref_code: Optional[str] = None, lang: str = "he"
) -> Optional[dict]:
    """Register user to a path via campaign API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE}/api/campaign/register",
                json={
                    "campaign_id": CAMPAIGN_ID,
                    "path_type": path,
                    "user_id": user_id,
                    "tg_username": username,
                    "full_name": full_name,
                    "ref_code": ref_code,
                    "lang": lang,
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        logger.warning(f"API register failed: {e}")
    return None


async def api_track_click(user_id: int, path: str, source: str = "telegram"):
    """Track path click."""
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{API_BASE}/api/campaign/click",
                json={
                    "campaign_id": CAMPAIGN_ID,
                    "path_type": path,
                    "user_id": user_id,
                    "source": source,
                    "lang": "he",
                },
                timeout=aiohttp.ClientTimeout(total=5),
            )
    except Exception:
        pass


# ============================================================
# /start handler — the critical first impression
# ============================================================

@dp.message(CommandStart())
async def on_start(message: Message, command: CommandObject = None):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name or (username or "משתמש")

    # Parse start parameter (deep link)
    args = (command.args if command else None) or ""
    ref_code = None
    direct_path = None

    # Campaign deep-link parsing:
    # /start promo_shekel_april26             → show full menu
    # /start promo_shekel_april26_SLH-ABC12   → with affiliate
    # /start partner_april26                  → direct to partner
    # /start genesis_april26                  → direct to genesis
    # /start community_april26                → direct to community
    # /start kosher_wallet                    → kosher wallet info
    if args.startswith("promo_shekel_april26"):
        tail = args[len("promo_shekel_april26"):].lstrip("_")
        if tail:
            ref_code = tail
    elif args.startswith("partner"):
        direct_path = "partner"
    elif args.startswith("genesis"):
        direct_path = "genesis"
    elif args.startswith("community"):
        direct_path = "community"
    elif args == "kosher_wallet":
        direct_path = "kosher"

    # Initialize state
    user_states.setdefault(user_id, {"path": None, "ref_code": ref_code, "step": "start"})
    user_states[user_id]["ref_code"] = ref_code or user_states[user_id].get("ref_code")

    # Track the click
    await api_track_click(user_id, direct_path or "pageview", source="telegram_start")

    # If direct path — route immediately
    if direct_path == "partner":
        return await handle_partner(message, user_id, username, full_name, ref_code)
    if direct_path == "genesis":
        return await handle_genesis(message, user_id, username, full_name, ref_code)
    if direct_path == "community":
        return await handle_community(message, user_id, username, full_name, ref_code)
    if direct_path == "kosher":
        return await handle_kosher(message)

    # Default: show the beautiful main menu
    greet = f"👋 שלום {full_name}!" if full_name else "👋 שלום!"
    ref_note = f"\n✨ הגעת עם קוד הפניה: <code>{ref_code}</code>" if ref_code else ""

    text = (
        f"🌟 <b>{greet}</b>\n"
        f"<b>ברוך הבא ל-SLH Spark</b> ⚡{ref_note}\n\n"
        f"💎 האקוסיסטם הקריפטו הישראלי — <b>25 בוטים · 5 טוקנים · 5 שפות · קוד פתוח</b>\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"<b>בחר את הדרך שלך:</b>\n\n"
        f"🛒 <b>קונה מיידי</b> — ₪{PRICE_ILS} Starter Pack\n"
        f"   0.25 SLH + 1,000 ZVK + Premium + קורס\n\n"
        f"🤝 <b>שותף</b> — חינם, 20% עמלה על כל קנייה\n\n"
        f"💎 <b>Genesis</b> — מייסד היסטורי עם NFT\n\n"
        f"🌱 <b>קהילה</b> — חינם, לראות ולהשתתף\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💬 /help · 🌐 /menu · 🎯 /invite"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard())

    # Admin notification (single, not triple)
    if ADMIN_CHAT_ID and ADMIN_CHAT_ID != user_id:
        try:
            await bot.send_message(
                ADMIN_CHAT_ID,
                f"👤 משתמש חדש: @{username or 'ללא'} (ID: {user_id}){(' ref: ' + ref_code) if ref_code else ''}"
            )
        except Exception:
            pass


# ============================================================
# Path handlers
# ============================================================

@dp.callback_query(F.data.startswith("path:"))
async def on_path_select(cb: CallbackQuery):
    path = cb.data.split(":", 1)[1]
    user_id = cb.from_user.id
    username = cb.from_user.username
    full_name = cb.from_user.full_name or (username or "משתמש")
    ref_code = user_states.get(user_id, {}).get("ref_code")

    await cb.answer()
    await api_track_click(user_id, path, source="telegram_path")

    if path == "buyer":
        await handle_buyer(cb.message, user_id, username, full_name, ref_code)
    elif path == "partner":
        await handle_partner(cb.message, user_id, username, full_name, ref_code)
    elif path == "genesis":
        await handle_genesis(cb.message, user_id, username, full_name, ref_code)
    elif path == "community":
        await handle_community(cb.message, user_id, username, full_name, ref_code)


async def handle_buyer(msg_ref, user_id, username, full_name, ref_code):
    """Buyer path — show payment options."""
    user_states[user_id]["path"] = "buyer"
    text = (
        f"🛒 <b>SLH Starter Pack — ₪{PRICE_ILS}</b>\n"
        f"(במקום ₪222 · מבצע השקה)\n\n"
        f"💎 <b>מקבל:</b>\n"
        f"• 0.25 SLH + 10% בונוס\n"
        f"• 1,000 ZVK פתיחה\n"
        f"• גישה לקבוצת Premium (30 יום)\n"
        f"• קורס בסיס באקדמיה + יכולת למכור קורסים משלך\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💳 <b>בחר שיטת תשלום:</b>"
    )
    try:
        await msg_ref.edit_text(text, parse_mode="HTML", reply_markup=buyer_payment_keyboard())
    except Exception:
        await msg_ref.answer(text, parse_mode="HTML", reply_markup=buyer_payment_keyboard())


async def handle_partner(msg_ref, user_id, username, full_name, ref_code):
    """Partner path — register + show affiliate code."""
    user_states[user_id]["path"] = "partner"
    # Register via API
    result = await api_register_path(user_id, username, full_name, "partner", ref_code)
    aff_code = (result or {}).get("affiliate_code")
    share_link = (result or {}).get("referral_link", f"https://slh-nft.com/promo-shekel.html?ref={aff_code or 'NEW'}")

    text = (
        f"🤝 <b>ברוך הבא, שותף!</b>\n\n"
        f"קוד האפילייט שלך:\n<code>{aff_code or 'יופק תוך רגע'}</code>\n\n"
        f"💰 <b>איך אתה מרוויח:</b>\n"
        f"• <b>50 ZVK</b> על כל הרשמה דרכך (גם בלי תשלום)\n"
        f"• <b>20% ZVK + 10% SLH</b> על כל קנייה\n"
        f"• בונוסים מצטברים — אין תקרה\n\n"
        f"📤 <b>הקישור שלך לשיתוף:</b>\n"
        f"{share_link}\n\n"
        f"🎯 שתף עם חברים, בקבוצות, ברשתות — והתחל להרוויח."
    )
    try:
        await msg_ref.edit_text(text, parse_mode="HTML", reply_markup=partner_keyboard(aff_code))
    except Exception:
        await msg_ref.answer(text, parse_mode="HTML", reply_markup=partner_keyboard(aff_code))


async def handle_genesis(msg_ref, user_id, username, full_name, ref_code):
    """Genesis path — BNB payment."""
    user_states[user_id]["path"] = "genesis"
    await api_register_path(user_id, username, full_name, "genesis", ref_code)
    text = (
        f"💎 <b>Genesis Contributor</b>\n\n"
        f"להיות חלק היסטורי בייסוד SLH Spark.\n"
        f"רק 8 אנשים נמצאים שם היום.\n\n"
        f"💰 <b>השקעה:</b> 0.002+ BNB (~₪40+)\n\n"
        f"🎁 <b>מקבל:</b>\n"
        f"• NFT Genesis ייחודי\n"
        f"• 500 ZVK + 0.5 SLH\n"
        f"• שמך ב-Wall of Founders לנצח\n"
        f"• 7x תגמול עתידי\n\n"
        f"📍 <b>כתובת BNB לתרומה:</b>\n"
        f"<code>{COMPANY_BSC_WALLET}</code>\n\n"
        f"לאחר ההעברה — שלח צילום מסך של העסקה."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 פרטי Genesis Launch", url="https://slh-nft.com/launch-event.html")],
        [InlineKeyboardButton(text="📜 Wall of Founders", url="https://slh-nft.com/about.html")],
        [InlineKeyboardButton(text="⬅️ חזרה לתפריט", callback_data="back:main")],
    ])
    try:
        await msg_ref.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await msg_ref.answer(text, parse_mode="HTML", reply_markup=kb)


async def handle_community(msg_ref, user_id, username, full_name, ref_code):
    """Community path — free entry."""
    user_states[user_id]["path"] = "community"
    result = await api_register_path(user_id, username, full_name, "community", ref_code)
    aff = (result or {}).get("affiliate_code")
    text = (
        f"🌱 <b>ברוך הבא לקהילה!</b>\n\n"
        f"✅ נרשמת בהצלחה — 100 ZVK הוקפצו לחשבונך\n"
        f"✅ תקבל עדכונים יומיים כאן\n"
        f"✅ תוכל לעלות לסטייקינג ולרכוש בהמשך\n\n"
        f"🎁 <b>אם תרצה להרוויח — יש לך קוד הפניה:</b>\n"
        f"<code>{aff or 'יופק תוך רגע'}</code>\n"
        f"שתף אותו וקבל 50 ZVK על כל הרשמה דרכך."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 דשבורד אישי", url=f"https://slh-nft.com/dashboard.html?uid={user_id}")],
        [InlineKeyboardButton(text="📖 התחל ללמוד", url="https://slh-nft.com/getting-started.html")],
        [InlineKeyboardButton(text="🤝 ארצה להיות שותף", callback_data="path:partner")],
        [InlineKeyboardButton(text="⬅️ חזרה לתפריט", callback_data="back:main")],
    ])
    try:
        await msg_ref.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await msg_ref.answer(text, parse_mode="HTML", reply_markup=kb)


async def handle_kosher(message: Message):
    """Kosher wallet info."""
    text = (
        f"🕊️ <b>הארנק הקריפטוגרפי הכשר</b>\n\n"
        f"המכשיר הראשון בעולם לניהול קריפטו מטלפון כשר ב-SMS.\n\n"
        f"💰 <b>מכירה מוקדמת: ₪888</b> (במקום ₪1,222)\n"
        f"📅 <b>השקה: 7 בנובמבר 2026</b>\n"
        f"🎯 100 ראשונים בלבד\n\n"
        f"פרטים מלאים באתר:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕊️ פרטים + הזמנה", url="https://slh-nft.com/kosher-wallet.html#preorder")],
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


# ============================================================
# Payment option handlers (for buyer)
# ============================================================

@dp.callback_query(F.data.startswith("pay:"))
async def on_payment_method(cb: CallbackQuery):
    method = cb.data.split(":", 1)[1]
    await cb.answer()

    if method == "ton":
        text = (
            f"💎 <b>תשלום ב-TON</b>\n\n"
            f"<b>סכום:</b> {PRICE_TEXT} (≈ ₪{PRICE_ILS})\n\n"
            f"<b>כתובת:</b>\n<code>{ALT_TELEGRAM_ROUTE}</code>\n\n"
            f"📲 לאחר ההעברה — שלח <b>צילום מסך</b> של אישור העסקה כאן.\n"
            f"אשלח לך אישור תוך 24 שעות."
        )
    elif method == "bank":
        text = (
            f"🏦 <b>העברה בנקאית (ILS)</b>\n\n"
            f"<b>סכום:</b> ₪{PRICE_ILS}\n\n"
            f"<b>פרטי חשבון:</b>\n"
            f"{BANK_DETAILS}\n\n"
            f"📲 לאחר ההעברה — מלא טופס באתר (לאסמכתא):\n"
            f"https://slh-nft.com/buy.html\n\n"
            f"או שלח כאן צילום אסמכתא + מספר טלפון."
        )
    elif method == "bnb":
        text = (
            f"🟡 <b>תשלום ב-BNB (BSC)</b>\n\n"
            f"<b>סכום:</b> כ-0.04 BNB (₪{PRICE_ILS})\n\n"
            f"<b>כתובת:</b>\n<code>{COMPANY_BSC_WALLET}</code>\n\n"
            f"<b>Network:</b> Binance Smart Chain (BEP-20)\n\n"
            f"📲 לאחר ההעברה — שלח צילום מסך של אישור העסקה."
        )
    else:
        text = "שיטה לא מוכרת"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ חזרה לתשלום", callback_data="path:buyer")],
    ])
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await cb.message.answer(text, parse_mode="HTML", reply_markup=kb)


@dp.callback_query(F.data == "back:main")
async def on_back_main(cb: CallbackQuery):
    """Back to main menu."""
    await cb.answer()
    full_name = cb.from_user.full_name or "משתמש"
    text = (
        f"🌟 <b>{full_name}</b>, בחר את הדרך שלך:\n\n"
        f"🛒 <b>קונה</b> — ₪{PRICE_ILS} Starter Pack\n"
        f"🤝 <b>שותף</b> — חינם + 20% עמלה\n"
        f"💎 <b>Genesis</b> — מייסד היסטורי\n"
        f"🌱 <b>קהילה</b> — חינם, לראות"
    )
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_keyboard())
    except Exception:
        await cb.message.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard())


# ============================================================
# Commands
# ============================================================

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    text = f"🌟 <b>תפריט ראשי — SLH Spark</b>\n\nבחר את הדרך שלך:"
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard())


@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>עזרה — SLH Spark Bot</b>\n\n"
        "/start — התחל מההתחלה\n"
        "/menu — תפריט ראשי\n"
        "/invite — קבל את קוד ההפניה שלך\n"
        "/help — עזרה זו\n\n"
        "🌐 אתר: slh-nft.com\n"
        "📱 תמיכה: @osifeu_prog"
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(Command("invite"))
async def cmd_invite(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name or "משתמש"
    # Register as community if not registered
    result = await api_register_path(user_id, username, full_name, "community")
    aff = (result or {}).get("affiliate_code")
    share_link = f"https://slh-nft.com/promo-shekel.html?ref={aff or ''}"
    text = (
        f"🎯 <b>קוד ההפניה שלך:</b>\n<code>{aff or 'יופק'}</code>\n\n"
        f"📤 הקישור לשיתוף:\n{share_link}\n\n"
        f"💰 תרוויח 50 ZVK על כל הרשמה דרכך + 20% ZVK ו-10% SLH על כל קנייה."
    )
    await message.answer(text, parse_mode="HTML")


# ============================================================
# Payment proof photo handler (buyers)
# ============================================================

@dp.message(F.photo)
async def on_payment_proof(message: Message):
    user_id = message.from_user.id
    state = user_states.setdefault(user_id, {"path": None})

    await message.reply(
        "✅ <b>קיבלתי את אישור התשלום.</b>\n\n"
        "שולח לאדמין לאימות. תקבל תגובה תוך 24 שעות.\n"
        "תודה על ההצטרפות! 🌟",
        parse_mode="HTML"
    )

    if ADMIN_CHAT_ID:
        try:
            caption = (
                f"💳 <b>אישור תשלום חדש</b>\n"
                f"משתמש: @{message.from_user.username or 'ללא'} (ID: {user_id})\n"
                f"נתיב: {state.get('path', 'לא זוהה')}\n"
                f"סכום: {PRICE_TEXT} / ₪{PRICE_ILS}\n"
                f"ref_code: {state.get('ref_code') or 'ללא'}"
            )
            photo = message.photo[-1]
            await bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=photo.file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=admin_approval_keyboard(user_id),
            )
        except Exception as e:
            logger.warning(f"Admin notification failed: {e}")


# ============================================================
# Admin approval
# ============================================================

@dp.callback_query(F.data.startswith("admin_approve:"))
async def on_admin_approve(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_CHAT_ID:
        await cb.answer("רק אדמין יכול לאשר", show_alert=True)
        return
    target_user_id = int(cb.data.split(":")[1])
    await cb.answer()
    await cb.message.edit_caption(cb.message.caption + "\n\n✅ <b>אושר</b>", parse_mode="HTML")
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=(
                "🎉 <b>התשלום שלך אושר!</b>\n\n"
                f"הטוקנים זוכו לחשבונך.\n"
                f"קישור לקבוצת Premium: {GROUP_PREMIUM_INVITE_LINK}\n"
                f"דשבורד: https://slh-nft.com/dashboard.html?uid={target_user_id}"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Notify user failed: {e}")


@dp.callback_query(F.data.startswith("admin_reject:"))
async def on_admin_reject(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_CHAT_ID:
        await cb.answer("רק אדמין יכול לדחות", show_alert=True)
        return
    target_user_id = int(cb.data.split(":")[1])
    await cb.answer()
    await cb.message.edit_caption(cb.message.caption + "\n\n❌ <b>נדחה</b>", parse_mode="HTML")
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text="❌ התשלום לא אושר. פנה לתמיכה @osifeu_prog לבירור."
        )
    except Exception:
        pass


# ============================================================
# FastAPI endpoints
# ============================================================

@fastapi_app.get("/")
async def root():
    return {"status": "up", "service": "SLH Community Bot", "version": "2.0"}


@fastapi_app.get("/health")
async def health():
    return {"status": "ok"}


@fastapi_app.get("/debug")
async def debug():
    return {
        "webhook_base": WEBHOOK_BASE,
        "has_token": bool(BOT_TOKEN),
        "price": PRICE_TEXT,
        "price_ils": PRICE_ILS,
    }


@fastapi_app.on_event("startup")
async def on_startup():
    mode = os.getenv("MODE", "webhook").lower()
    if mode == "polling" or not WEBHOOK_BASE:
        logger.info("Starting in polling mode — SLH Community Bot v2.0")
        await bot.delete_webhook(drop_pending_updates=True)
        asyncio.create_task(dp.start_polling(bot, drop_pending_updates=True))
    else:
        webhook_url = f"{WEBHOOK_BASE}/{WEBHOOK_SECRET}"
        try:
            await bot.set_webhook(url=webhook_url)
            logger.info(f"Webhook set: {webhook_url}")
        except Exception as e:
            logger.error(f"Webhook failed: {e}")


@fastapi_app.post("/{secret_path}")
async def handle_update(secret_path: str, request: Request):
    if secret_path != WEBHOOK_SECRET:
        return {"status": "ignored"}
    body = await request.json()
    update = Update.model_validate(body)
    await dp.feed_update(bot, update)
    return {"status": "ok"}


@fastapi_app.on_event("shutdown")
async def on_shutdown():
    try:
        await bot.delete_webhook()
    except Exception as e:
        logger.error(f"Webhook delete failed: {e}")
    await bot.session.close()
