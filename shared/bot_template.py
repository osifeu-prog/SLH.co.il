import os
import sys
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Ensure shared modules path
sys.path.insert(0, "/app/shared")

from slh_payments.payment_gate import PaymentGate
from slh_payments.config import BotPricing
from slh_payments import db as pay_db
from slh_payments.promotions import promo_engine
from slh_payments.referrals import referral_engine

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("slh.bot")

# Environment
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BOT_KEY = os.getenv("BOT_KEY", "generic").strip()
BOT_DISPLAY_NAME = os.getenv("BOT_DISPLAY_NAME", "SLH Bot").strip()
BOT_DESCRIPTION = os.getenv("BOT_DESCRIPTION", "שירות SLH").strip()

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN missing")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# -------------------- PAYMENT SETUP --------------------

pricing = BotPricing(
    bot_name=BOT_DISPLAY_NAME,
    price_ils=float(os.getenv("PRICE_ILS", "41")),
    price_ton=float(os.getenv("PRICE_TON", "2.0")),
    description_he=BOT_DESCRIPTION,
    features=[]
)

gate = PaymentGate(BOT_KEY, bot=bot, dp=dp)
gate.pricing = pricing
gate.register_handlers()

# -------------------- START --------------------

@dp.message(Command("start"))
async def start_cmd(m: types.Message):
    ref_link = referral_engine.get_link(m.from_user.id, BOT_KEY)

    await m.answer(
        f"🚀 {BOT_DISPLAY_NAME}\n\n"
        f"{BOT_DESCRIPTION}\n\n"
        "פקודות:\n"
        "/premium  - שדרוג\n"
        "/deals    - מבצעים\n"
        "/mylink   - קישור הפניה\n"
        "/referral - סטטיסטיקה\n"
        "/status   - מצב\n"
        "/help     - עזרה\n\n"
        "───────────────\n"
        "👥 שתף והרווח 15%\n"
        f"{ref_link}"
    )

# -------------------- STATUS --------------------

@dp.message(Command("status"))
async def status_cmd(m: types.Message):
    is_paid = await pay_db.is_premium(m.from_user.id, BOT_KEY)

    await m.answer(
        f"📊 מצב חשבון\n\n"
        f"User ID: {m.from_user.id}\n"
        f"Premium: {'כן' if is_paid else 'לא'}"
    )

# -------------------- MYLINK --------------------

@dp.message(Command("mylink"))
async def mylink_cmd(m: types.Message):
    link = referral_engine.get_link(m.from_user.id, BOT_KEY)

    await m.answer(
        f"🔗 הקישור האישי שלך:\n\n"
        f"{link}\n\n"
        "📋 העתק ושתף עם חברים\n"
        "💰 15% עמלה על כל שדרוג\n\n"
        "📊 /referral"
    )

# -------------------- REFERRAL --------------------

@dp.message(Command("referral"))
async def referral_cmd(m: types.Message):
    stats = await referral_engine.get_user_stats(m.from_user.id)

    await m.answer(
        f"👥 ההפניות שלך\n\n"
        f"הפניות: {stats.get('count', 0)}\n"
        f"המרות: {stats.get('converted', 0)}"
    )

# -------------------- PROMO --------------------

@dp.message(Command("promo"))
async def promo_cmd(m: types.Message):
    args = m.text.split(maxsplit=1)

    if len(args) < 2:
        await m.answer("🏷️ שלח /promo CODE\nלדוגמה: /promo LAUNCH30")
        return

    code = args[1]
    deal = promo_engine.get_deal_by_code(code)

    if not deal:
        await m.answer("❌ קוד לא תקין או שפג תוקפו\n/deals")
        return

    await m.answer(f"✅ קוד {code} הופעל!")

# -------------------- DEALS --------------------

@dp.message(Command("deals"))
async def deals_cmd(m: types.Message):
    text = promo_engine.format_deals_message(BOT_KEY, lang="he")
    await m.answer(text)

# -------------------- HELP --------------------

@dp.message(Command("help"))
async def help_cmd(m: types.Message):
    await m.answer(
        "עזרה:\n"
        "/start\n"
        "/premium\n"
        "/deals\n"
        "/mylink\n"
        "/referral\n"
        "/promo\n"
        "/status"
    )

# -------------------- MAIN --------------------

async def main():
    await pay_db.init_schema()
    await referral_engine.init_schema()

    logger.info("Starting bot: %s (%s)", BOT_DISPLAY_NAME, BOT_KEY)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())