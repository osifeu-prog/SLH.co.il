"""
SLH Minimal Bot Template - used for bots without dedicated code.
Provides: /start, /premium, payment proof handling, admin approve/reject.

Usage:
    BOT_KEY=campaign BOT_DESCRIPTION="×§×ž×¤×™×™× ×™× ×©×™×•×•×§×™×™×" python bot_template.py
"""
import os
import sys
import asyncio
import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from register_api import register_device, verify_device

sys.path.insert(0, "/app/shared")
from slh_payments.payment_gate import PaymentGate
from slh_payments.config import ADMIN_USER_ID, BotPricing
from slh_payments import db as pay_db
from slh_payments.promotions import promo_engine
from slh_payments.referrals import referral_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("slh.bot")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BOT_KEY = os.getenv("BOT_KEY", "generic").strip()
BOT_DISPLAY_NAME = os.getenv("BOT_DISPLAY_NAME", "SLH Bot").strip()
BOT_DESCRIPTION = os.getenv("BOT_DESCRIPTION", "\u05e9\u05d9\u05e8\u05d5\u05ea SLH").strip()
PRICE_ILS = float(os.getenv("PRICE_ILS", "41"))
PRICE_TON = float(os.getenv("PRICE_TON", "2.0"))  # legacy, kept for config compat

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN missing")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# Create pricing
pricing = BotPricing(
    bot_name=BOT_DISPLAY_NAME,
    price_ils=PRICE_ILS,
    price_ton=PRICE_TON,
    description_he=BOT_DESCRIPTION,
    features=[],
)

# Register payment gate
gate = PaymentGate(BOT_KEY, bot=bot, dp=dp)
gate.pricing = pricing
gate.register_handlers()


@dp.message(Command("start"))
async def start_cmd(m: types.Message):
    # Handle referral tracking from deep link
    args = m.text.split(maxsplit=1)
    if len(args) > 1:
        referrer_id = referral_engine.parse_referral(args[1])
        if referrer_id:
            await referral_engine.track_referral(referrer_id, m.from_user.id, BOT_KEY)

    is_paid = await pay_db.is_premium(m.from_user.id, BOT_KEY)
    status = "\u2705 Premium" if is_paid else "\U0001f512 Free"

    # Build promo line
    deals = promo_engine.get_active_deals(BOT_KEY)
    promo_line = ""
    if deals and not is_paid:
        best = deals[0]
        promo_line = f"\n\n\U0001f525 *{best.title_he}*\n\u23f0 {best.remaining_time} | /deals"

    # Referral link
    ref_link = referral_engine.get_link(m.from_user.id, BOT_KEY)

    await m.answer(
        f"\U0001f680 {BOT_DISPLAY_NAME}\n\n"
        f"{BOT_DESCRIPTION}\n\n"
        f"\u05de\u05e6\u05d1: {status}\n\n"
        "\u05e4\u05e7\u05d5\u05d3\u05d5\u05ea:\n"
        "/premium  - \u05e9\u05d3\u05e8\u05d5\u05d2 \u05dc\u05e4\u05e8\u05d9\u05de\u05d9\u05d5\u05dd\n"
        "/deals    - \U0001f381 \u05de\u05d1\u05e6\u05e2\u05d9\u05dd\n"
        "/mylink   - \U0001f517 \u05e7\u05d9\u05e9\u05d5\u05e8 \u05d4\u05e4\u05e0\u05d9\u05d4 \u05e9\u05dc\u05d9\n"
        "/referral - \U0001f465 \u05e1\u05d8\u05d8\u05d9\u05e1\u05d8\u05d9\u05e7\u05ea \u05d4\u05e4\u05e0\u05d9\u05d5\u05ea\n"
        "/status   - \u05de\u05e6\u05d1 \u05d7\u05e9\u05d1\u05d5\u05df\n"
        "/help     - \u05e2\u05d6\u05e8\u05d4"
        f"{promo_line}\n\n"
        f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\U0001f465 *\u05e9\u05ea\u05e3 \u05d5\u05d4\u05e8\u05d5\u05d5\u05d7 15% \u05d1\u05e0\u05e7\u05d5\u05d3\u05d5\u05ea SLH!*\n"
        f"\U0001f517 `{ref_link}`",
        parse_mode="Markdown",
    )
    await pay_db.log_event("user.start", BOT_KEY, m.from_user.id)


@dp.message(Command("status"))
async def status_cmd(m: types.Message):
    is_paid = await pay_db.is_premium(m.from_user.id, BOT_KEY)
    uname = m.from_user.username or "?"
    premium_str = "\u2705 \u05db\u05df" if is_paid else "\u274c \u05dc\u05d0"
    await m.answer(
        f"\U0001f4ca {BOT_DISPLAY_NAME}\n\n"
        f"User ID: {m.from_user.id}\n"
        f"Username: {uname}\n"
        f"Premium: {premium_str}\n\n"
        f"\U0001f4b0 \u05de\u05d7\u05d9\u05e8: {PRICE_ILS} \u20aa\n"
        "\u05dc\u05e9\u05d3\u05e8\u05d5\u05d2 \u2192 /premium",
    )


@dp.message(Command("deals"))
async def deals_cmd(m: types.Message):
    text = promo_engine.format_deals_message(BOT_KEY, lang="he")
    await m.answer(text, parse_mode="Markdown")


@dp.message(Command("mylink"))
async def mylink_cmd(m: types.Message):
    link = referral_engine.get_link(m.from_user.id, BOT_KEY)
    await m.answer(
        "\U0001f517 *×”×§×™×©×•×¨ ×”××™×©×™ ×©×œ×š:*\n\n"
        f"`{link}`\n\n"
        "\U0001f4cb ×”×¢×ª×§ ×•×©×ª×£ ×¢× ×—×‘×¨×™×!\n"
        "\U0001f4b0 ×¢×œ ×›×œ ×—×‘×¨ ×©×ž×©×“×¨×’ â€” ×ž×§×‘×œ *15% ×¢×ž×œ×” ×‘× ×§×•×“×•×ª SLH*\n\n"
        "\U0001f4ca ×œ×¡×˜×˜×™×¡×˜×™×§×”: /referral",
        parse_mode="Markdown",
    )


@dp.message(Command("referral"))
async def referral_cmd(m: types.Message):
    stats = await referral_engine.get_user_stats(m.from_user.id)
    card = referral_engine.format_referral_card(m.from_user.id, BOT_KEY, stats)
    await m.answer(card, parse_mode="Markdown")


@dp.message(Command("promo"))
async def promo_cmd(m: types.Message):
    args = m.text.split(maxsplit=1)
    if len(args) < 2:
        await m.answer("\U0001f3f7\ufe0f ×©×œ×— /promo CODE\n×œ×“×•×’×ž×”: /promo LAUNCH30")
        return
    deal = promo_engine.get_deal_by_code(args[1])
    if not deal:
        await m.answer("\u274c ×§×•×“ ×œ× ×ª×§×™×Ÿ ××• ×©×¤×’ ×ª×•×§×¤×•.\n/deals ×œ×¨×©×™×ž×” ×ž×œ××”")
        return
    if deal.min_referrals > 0:
        count = await referral_engine.get_referral_count(m.from_user.id, BOT_KEY)
        if count < deal.min_referrals:
            await m.answer(
                f"\U0001f512 ×ž×‘×¦×¢ ×–×” ×“×•×¨×© {deal.min_referrals} ×”×¤× ×™×•×ª.\n"
                f"×™×© ×œ×š: {count}\n\n"
                "/mylink â€” ×©×ª×£ ×•×ª×ª×§×“×!"
            )
            return
    from slh_payments.config import BOT_PRICING
    bp = BOT_PRICING.get(BOT_KEY)
    if bp:
        new_ils, new_ton = promo_engine.calculate_price(deal, bp.price_ils, bp.price_ton)
        await m.answer(
            f"\u2705 *{deal.title_he}*\n\n"
            f"×ž×—×™×¨ ×¨×’×™×œ: {bp.price_ils}\u20aa\n"
            f"×ž×—×™×¨ ×ž×‘×¦×¢: *{new_ils}\u20aa*\n\n"
            f"\u23f0 × ×•×ª×¨: {deal.remaining_time}\n\n"
            "×©×œ×— /premium ×œ×”×ž×©×š ×ª×©×œ×•× \U0001f680",
            parse_mode="Markdown",
        )
    else:
        await m.answer(f"\u2705 ×§×•×“ {deal.code} ×”×•×¤×¢×œ! ×©×œ×— /premium ×œ×”×ž×©×š.")


@dp.message(Command("help"))
async def help_cmd(m: types.Message):
    ref_link = referral_engine.get_link(m.from_user.id, BOT_KEY)
    await m.answer(
        f"{BOT_DISPLAY_NAME} - \u05e2\u05d6\u05e8\u05d4\n\n"
        "/start    - \u05d4\u05ea\u05d7\u05dc\u05d4\n"
        "/premium  - \u05e9\u05d3\u05e8\u05d5\u05d2 \u05dc\u05e4\u05e8\u05d9\u05de\u05d9\u05d5\u05dd\n"
        "/deals    - \U0001f381 \u05de\u05d1\u05e6\u05e2\u05d9\u05dd \u05e4\u05e2\u05d9\u05dc\u05d9\u05dd\n"
        "/mylink   - \U0001f517 \u05e7\u05d9\u05e9\u05d5\u05e8 \u05d4\u05e4\u05e0\u05d9\u05d4 \u05e9\u05dc\u05d9\n"
        "/referral - \U0001f465 \u05e1\u05d8\u05d8\u05d9\u05e1\u05d8\u05d9\u05e7\u05ea \u05d4\u05e4\u05e0\u05d9\u05d5\u05ea\n"
        "/promo    - \U0001f3f7\ufe0f \u05d4\u05e4\u05e2\u05dc\u05ea \u05e7\u05d5\u05d3 \u05de\u05d1\u05e6\u05e2\n"
        "/status   - \u05de\u05e6\u05d1 \u05d7\u05e9\u05d1\u05d5\u05df\n"
        "/help     - \u05e2\u05d6\u05e8\u05d4\n\n"
        "\u05e9\u05dc\u05d7 \u05e6\u05d9\u05dc\u05d5\u05dd \u05de\u05e1\u05da \u05e9\u05dc \u05ea\u05e9\u05dc\u05d5\u05dd \u05db\u05d3\u05d9 \u05dc\u05d4\u05e4\u05e2\u05d9\u05dc \u05e4\u05e8\u05d9\u05de\u05d9\u05d5\u05dd.\n\n"
        f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\U0001f465 *\u05e9\u05ea\u05e3 \u05d5\u05d4\u05e8\u05d5\u05d5\u05d7 15% \u05d1\u05e0\u05e7\u05d5\u05d3\u05d5\u05ea SLH!*\n"
        f"\U0001f517 `{ref_link}`",
        parse_mode="Markdown",
    )


async def main():
    await pay_db.init_schema()
    await referral_engine.init_schema()
    logger.info("=" * 50)
    logger.info("SLH SPARK | %s (%s)", BOT_DISPLAY_NAME, BOT_KEY)
    logger.info("=" * 50)
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())

@dp.message(Command("register"))
async def cmd_register(message):
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Usage: /register SERIAL PHONE")
        return

    serial = args[1]
    phone = args[2]

    res = register_device(serial, phone)

    if "code" in res:
        await message.answer(f"Code: {res['code']}")
    else:
        await message.answer("Register failed")

@dp.message(Command("verify"))
async def cmd_verify(message):
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Usage: /verify SERIAL CODE")
        return

    serial = args[1]
    code = args[2]

    res = verify_device(serial, code)

    if res.get("status") == "verified":
        await message.answer(f"Device OK\nToken: {res['token']}")
Token: {res['token']}")
    else:
        await message.answer("Verify failed")


