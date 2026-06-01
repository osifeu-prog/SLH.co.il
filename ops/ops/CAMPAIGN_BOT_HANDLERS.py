"""
SLH Campaign Bot Handlers — Drop-in for community bot
Handles /start promo_shekel_april26_<AFFCODE> and 4 path types

Integration:
1. Copy these handlers into your community bot's main.py
2. Register them BEFORE the default /start handler
3. Restart bot

Routes:
  /start promo_shekel_april26       -> Show 4-path picker
  /start promo_shekel_april26_<CODE> -> Show with referral attribution
  /start partner_april26            -> Direct partner registration
  /start genesis_april26            -> Direct genesis flow
  /start community_april26          -> Direct community signup
"""

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, CommandObject
import aiohttp
import os

API_BASE = os.getenv("SLH_API_BASE", "https://slh-api-production.up.railway.app")
CAMPAIGN_ID = "shekel_april26"

router = Router()


def make_path_keyboard(ref_code: str = None) -> InlineKeyboardMarkup:
    """4-path picker keyboard."""
    suffix = f"_{ref_code}" if ref_code else ""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 קונה מיידי — ₪99", callback_data=f"promo:buyer{suffix}")],
        [InlineKeyboardButton(text="🤝 שותף משווק — חינם + 20% ZVK", callback_data=f"promo:partner{suffix}")],
        [InlineKeyboardButton(text="💎 Genesis Contributor — 0.002+ BNB", callback_data=f"promo:genesis{suffix}")],
        [InlineKeyboardButton(text="🌱 חבר קהילה — חינם", callback_data=f"promo:community{suffix}")],
        [InlineKeyboardButton(text="🌐 דף הקמפיין באתר", url="https://slh-nft.com/promo-shekel.html")]
    ])


@router.message(CommandStart(deep_link=True, magic=F.args.startswith("promo_shekel_april26")))
async def cmd_promo_start(message: Message, command: CommandObject):
    """Handle /start promo_shekel_april26 with optional _<AFFCODE>"""
    args = (command.args or "").replace("promo_shekel_april26", "").lstrip("_")
    ref_code = args if args else None

    text = (
        "🎯 <b>SLH Spark — חלון 48 שעות</b>\n\n"
        "הדולר נחלש, השקל התחזק → רגע מושלם להיכנס לאקוסיסטם.\n\n"
        "📍 בחר את הדרך שלך:\n\n"
        "🛒 <b>קונה מיידי</b> — ₪99 בלבד\n"
        "   0.25 SLH + 1,000 ZVK + Premium\n\n"
        "🤝 <b>שותף / משווק</b> — חינם\n"
        "   20% ZVK + 10% SLH על כל קנייה\n\n"
        "💎 <b>Genesis</b> — 0.002+ BNB\n"
        "   NFT היסטורי + שמך לעד\n\n"
        "🌱 <b>חבר קהילה</b> — חינם\n"
        "   100 ZVK ברכת פתיחה"
    )
    if ref_code:
        text += f"\n\n✨ הוזמנת ע\"י: <code>{ref_code}</code>\nהוא יקבל בונוס על ההצטרפות שלך."

    await message.answer(text, parse_mode="HTML", reply_markup=make_path_keyboard(ref_code))


@router.message(CommandStart(deep_link=True, magic=F.args.in_({"partner_april26", "genesis_april26", "community_april26"})))
async def cmd_path_start(message: Message, command: CommandObject):
    """Handle direct path links."""
    path = command.args.replace("_april26", "")  # partner | genesis | community
    await register_path(message, path, ref_code=None)


@router.callback_query(F.data.startswith("promo:"))
async def cb_path_select(cb: CallbackQuery):
    """Handle path button click."""
    parts = cb.data.split(":")[1].split("_")
    path = parts[0]  # buyer | partner | genesis | community
    ref_code = parts[1] if len(parts) > 1 else None
    await cb.answer()
    await register_path(cb.message, path, ref_code=ref_code, user_id=cb.from_user.id, username=cb.from_user.username)


async def register_path(message: Message, path: str, ref_code: str = None, user_id: int = None, username: str = None):
    """Register user to a path via API and show next steps."""
    user_id = user_id or message.from_user.id
    username = username or message.from_user.username
    full_name = message.from_user.full_name

    # Call campaign register endpoint
    affiliate_code = None
    referral_link = None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_BASE}/api/campaign/register", json={
                "campaign_id": CAMPAIGN_ID,
                "path_type": path,
                "user_id": user_id,
                "tg_username": username,
                "full_name": full_name,
                "ref_code": ref_code,
                "lang": "he"
            }, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                affiliate_code = data.get("affiliate_code")
                referral_link = data.get("referral_link")
    except Exception as e:
        print(f"[campaign] register failed: {e}")

    # Path-specific responses
    if path == "buyer":
        text = (
            "💎 <b>Starter Pack — ₪99</b>\n\n"
            "מה תקבל אחרי תשלום:\n"
            "✅ 0.25 SLH + 10% בונוס\n"
            "✅ 1,000 ZVK פתיחה\n"
            "✅ קבוצת Premium 30 יום\n"
            "✅ קורס בסיס באקדמיה\n\n"
            "💳 לתשלום לחץ:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 רכישה ב-₪99", url=f"https://slh-nft.com/buy.html?campaign={CAMPAIGN_ID}&path=buyer&ref={ref_code or ''}")],
            [InlineKeyboardButton(text="❓ שאלות נפוצות", url="https://slh-nft.com/promo-shekel.html#faq")]
        ])

    elif path == "partner":
        text = (
            "🤝 <b>ברוך הבא, שותף!</b>\n\n"
            f"קוד האפילייט שלך: <code>{affiliate_code or 'מתעדכן...'}</code>\n\n"
            "💰 איך אתה מרוויח:\n"
            "• 50 ZVK על כל הרשמה דרכך (גם בלי תשלום)\n"
            "• 20% ZVK + 10% SLH על כל קנייה\n"
            "• בונוסים מצטברים — אין תקרה\n\n"
            "📤 שתף את הקישור שלך:"
        )
        share_link = referral_link or f"https://slh-nft.com/promo-shekel.html?ref={affiliate_code or 'NEW'}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 העתק קישור הפנייה", url=share_link)],
            [InlineKeyboardButton(text="📊 דשבורד שותף", url=f"https://slh-nft.com/partner-dashboard.html?code={affiliate_code or ''}")],
            [InlineKeyboardButton(text="📚 חומרי שיווק מוכנים", url="https://slh-nft.com/promo-shekel.html#materials")]
        ])

    elif path == "genesis":
        text = (
            "💎 <b>Genesis Contributor</b>\n\n"
            "להיות חלק היסטורי בייסוד SLH — רק 8 אנשים נמצאים שם היום.\n\n"
            "💰 השקעה: 0.002+ BNB (~₪40+)\n"
            "🎁 מקבל:\n"
            "✅ NFT Genesis ייחודי\n"
            "✅ 500 ZVK + 0.5 SLH\n"
            "✅ שמך ב-Wall of Founders לנצח\n"
            "✅ 7x תגמול עתידי\n\n"
            "📍 כתובת BNB:\n<code>0xd061de73B06d5E91bfA46b35EfB7B08b16903da4</code>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 פרטי התרומה", url="https://slh-nft.com/launch-event.html")],
            [InlineKeyboardButton(text="📜 Wall of Founders", url="https://slh-nft.com/about.html#founders")]
        ])

    else:  # community
        text = (
            "🌱 <b>ברוך הבא לקהילה!</b>\n\n"
            "✅ נרשמת בהצלחה — 100 ZVK הוקפצו לחשבונך\n"
            "✅ דשבורד צפייה זמין באתר\n"
            "✅ עדכונים יומיים יישלחו אליך כאן\n\n"
            f"קוד האפילייט שלך (במידה ותרצה להזמין חברים):\n<code>{affiliate_code or 'מתעדכן...'}</code>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌐 דשבורד", url=f"https://slh-nft.com/dashboard.html?uid={user_id}")],
            [InlineKeyboardButton(text="📖 התחל ללמוד", url="https://slh-nft.com/getting-started.html")],
            [InlineKeyboardButton(text="🤝 ארצה להיות שותף בעתיד", callback_data=f"promo:partner_{ref_code or ''}")]
        ])

    await message.answer(text, parse_mode="HTML", reply_markup=kb)


# Register router with: dp.include_router(router)
