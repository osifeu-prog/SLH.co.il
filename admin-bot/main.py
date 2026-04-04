"""
SLH SPARK SYSTEM - Super Admin Bot (@MY_SUPER_ADMIN_bot)
Central control panel for the entire SLH ecosystem.
"""
import os
import sys
import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Add shared lib to path
sys.path.insert(0, "/app/shared")
from slh_payments import db as pay_db
from slh_payments.config import ADMIN_USER_ID, BOT_PRICING

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("slh.admin")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN missing")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

ECOSYSTEM_BOTS = {
    "academia": {"name": "SLH Academia", "username": "SLH_Academia_bot", "container": "slh-core-bot"},
    "guardian": {"name": "SLH Guardian", "username": "Grdian_bot", "container": "slh-guardian-bot"},
    "botshop": {"name": "GATE BotShop", "username": "Buy_My_Shop_bot", "container": "slh-botshop"},
    "wallet": {"name": "SLH Wallet", "username": "SLH_Wallet_bot", "container": "slh-wallet"},
    "factory": {"name": "BOT Factory", "username": "Osifs_Factory_bot", "container": "slh-factory"},
    "community": {"name": "SLH Community", "username": "SLH_community_bot", "container": "slh-fun"},
}

ASCII_BANNER = """
 ███████╗██╗     ██╗  ██╗
 ██╔════╝██║     ██║  ██║
 ███████╗██║     ████████║
 ╚════██║██║     ██╔════██║
 ███████║███████╗██║  ██║
 ╚══════╝╚══════╝╚═╝  ╚═╝
"""


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_USER_ID


@dp.message(Command("start"))
async def start_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        await m.answer("\u274c \u05d2\u05d9\u05e9\u05d4 \u05dc\u05d0\u05d3\u05de\u05d9\u05e0\u05d9\u05dd \u05d1\u05dc\u05d1\u05d3.")
        return

    await m.answer(
        f"```\n{ASCII_BANNER.strip()}\n```\n"
        "*SLH SPARK SYSTEM*\n"
        "Mission Control \U0001f680\n\n"
        "\u05e4\u05e7\u05d5\u05d3\u05d5\u05ea:\n"
        "/dashboard - \u05e1\u05e7\u05d9\u05e8\u05ea \u05de\u05e6\u05d1\n"
        "/payments  - \u05ea\u05e9\u05dc\u05d5\u05de\u05d9\u05dd \u05de\u05de\u05ea\u05d9\u05e0\u05d9\u05dd\n"
        "/stats     - \u05e1\u05d8\u05d8\u05d9\u05e1\u05d8\u05d9\u05e7\u05d5\u05ea \u05d5\u05d4\u05db\u05e0\u05e1\u05d5\u05ea\n"
        "/bots      - \u05e8\u05e9\u05d9\u05de\u05ea \u05d1\u05d5\u05d8\u05d9\u05dd\n"
        "/revenue   - \u05d3\u05d5\u05d7 \u05d4\u05db\u05e0\u05e1\u05d5\u05ea\n"
        "/broadcast - \u05e9\u05dc\u05d7 \u05d4\u05d5\u05d3\u05e2\u05d4 \u05dc\u05db\u05d5\u05dc\u05dd",
        parse_mode="Markdown",
    )


@dp.message(Command("dashboard"))
async def dashboard_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return

    stats = await pay_db.get_stats()

    lines = [
        "\U0001f4ca *SLH SPARK DASHBOARD*\n",
        f"\U0001f465 \u05de\u05e9\u05ea\u05de\u05e9\u05d9\u05dd: {stats['total_users']}",
        f"\u2705 \u05de\u05d0\u05d5\u05e9\u05e8\u05d9\u05dd: {stats['approved']}",
        f"\u23f3 \u05de\u05de\u05ea\u05d9\u05e0\u05d9\u05dd: {stats['pending']}",
        f"\U0001f4b0 \u05d4\u05db\u05e0\u05e1\u05d5\u05ea: {stats['total_revenue']:.0f} \u20aa\n",
        "*\u05dc\u05e4\u05d9 \u05d1\u05d5\u05d8:*",
    ]
    for row in stats["by_bot"]:
        lines.append(f"  \u2022 {row['bot_name']}: {row['cnt']} \u05de\u05e9\u05ea\u05de\u05e9\u05d9\u05dd | {float(row['revenue']):.0f} \u20aa")

    lines.append(f"\n\u23f0 \u05e2\u05d3\u05db\u05d5\u05df: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    await m.answer("\n".join(lines), parse_mode="Markdown")


@dp.message(Command("payments"))
async def payments_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return

    pending = await pay_db.get_pending_payments()
    if not pending:
        await m.answer("\u2705 \u05d0\u05d9\u05df \u05ea\u05e9\u05dc\u05d5\u05de\u05d9\u05dd \u05de\u05de\u05ea\u05d9\u05e0\u05d9\u05dd!")
        return

    for p in pending[:10]:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="\u2705 \u05d0\u05e9\u05e8", callback_data=f"adm_approve:{p['id']}"),
                InlineKeyboardButton(text="\u274c \u05d3\u05d7\u05d4", callback_data=f"adm_reject:{p['id']}"),
            ]
        ])
        text = (
            f"\U0001f4b3 *\u05ea\u05e9\u05dc\u05d5\u05dd #{p['id']}*\n"
            f"\u05d1\u05d5\u05d8: {p['bot_name']}\n"
            f"\u05de\u05e9\u05ea\u05de\u05e9: @{p['username'] or '?'} ({p['user_id']})\n"
            f"\u05e1\u05db\u05d5\u05dd: {p['payment_amount']} {p['payment_currency']}\n"
            f"\u05ea\u05d0\u05e8\u05d9\u05da: {p['created_at'].strftime('%d/%m %H:%M') if p['created_at'] else '?'}"
        )
        if p.get("payment_proof_file_id"):
            try:
                await bot.send_photo(m.chat.id, p["payment_proof_file_id"], caption=text,
                                     parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await m.answer(text + "\n(\u05ea\u05de\u05d5\u05e0\u05d4 \u05dc\u05d0 \u05d6\u05de\u05d9\u05e0\u05d4)",
                              parse_mode="Markdown", reply_markup=kb)
        else:
            await m.answer(text + "\n(\u05d0\u05d9\u05df \u05ea\u05de\u05d5\u05e0\u05d4)",
                          parse_mode="Markdown", reply_markup=kb)

    if len(pending) > 10:
        await m.answer(f"\u05d5\u05e2\u05d5\u05d3 {len(pending) - 10} \u05ea\u05e9\u05dc\u05d5\u05de\u05d9\u05dd...")


@dp.callback_query(F.data.startswith("adm_approve:"))
async def approve_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("\u274c")
        return
    pid = int(cb.data.split(":")[1])
    result = await pay_db.approve_payment(pid, cb.from_user.id)
    if result:
        # Notify user via their bot (best effort)
        await cb.message.edit_caption(
            caption=f"\u2705 \u05d0\u05d5\u05e9\u05e8 #{pid} | {result['bot_name']} | @{result.get('username','?')}"
        ) if cb.message.photo else await cb.message.edit_text(
            f"\u2705 \u05d0\u05d5\u05e9\u05e8 #{pid} | {result['bot_name']} | @{result.get('username','?')}"
        )
        await cb.answer("\u05d0\u05d5\u05e9\u05e8!")
    else:
        await cb.answer("\u05dc\u05d0 \u05e0\u05de\u05e6\u05d0")


@dp.callback_query(F.data.startswith("adm_reject:"))
async def reject_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("\u274c")
        return
    pid = int(cb.data.split(":")[1])
    result = await pay_db.reject_payment(pid, cb.from_user.id)
    if result:
        await cb.message.edit_caption(
            caption=f"\u274c \u05e0\u05d3\u05d7\u05d4 #{pid} | @{result.get('username','?')}"
        ) if cb.message.photo else await cb.message.edit_text(
            f"\u274c \u05e0\u05d3\u05d7\u05d4 #{pid} | @{result.get('username','?')}"
        )
        await cb.answer("\u05e0\u05d3\u05d7\u05d4")


@dp.message(Command("stats"))
async def stats_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    stats = await pay_db.get_stats()
    text = (
        "\U0001f4c8 *\u05e1\u05d8\u05d8\u05d9\u05e1\u05d8\u05d9\u05e7\u05d5\u05ea*\n\n"
        f"\u05de\u05e9\u05ea\u05de\u05e9\u05d9\u05dd \u05e8\u05e9\u05d5\u05de\u05d9\u05dd: {stats['total_users']}\n"
        f"\u05de\u05e9\u05dc\u05de\u05d9\u05dd: {stats['approved']}\n"
        f"\u05de\u05de\u05ea\u05d9\u05e0\u05d9\u05dd: {stats['pending']}\n"
        f"\u05d4\u05db\u05e0\u05e1\u05d5\u05ea \u05db\u05d5\u05dc\u05dc\u05ea: {stats['total_revenue']:.0f} \u20aa\n\n"
        f"*\u05d4\u05db\u05e0\u05e1\u05d4 \u05de\u05de\u05d5\u05e6\u05e2\u05ea/\u05d7\u05d5\u05d3\u05e9:*\n"
    )
    total_monthly = sum(
        BOT_PRICING[k].price_ils for k in BOT_PRICING
    )
    text += f"\u05e4\u05d5\u05d8\u05e0\u05e6\u05d9\u05d0\u05dc \u05dc\u05de\u05e9\u05ea\u05de\u05e9: {total_monthly} \u20aa\n"
    text += f"\u05e4\u05d5\u05d8\u05e0\u05e6\u05d9\u05d0\u05dc \u05dc-100 \u05de\u05e9\u05ea\u05de\u05e9\u05d9\u05dd: {total_monthly * 100:,.0f} \u20aa"

    await m.answer(text, parse_mode="Markdown")


@dp.message(Command("bots"))
async def bots_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    lines = ["\U0001f916 *\u05e8\u05e9\u05d9\u05de\u05ea \u05d1\u05d5\u05d8\u05d9\u05dd*\n"]
    for key, info in ECOSYSTEM_BOTS.items():
        pricing = BOT_PRICING.get(key)
        price = f"{pricing.price_ils}\u20aa" if pricing else "?"
        lines.append(f"\u2022 *{info['name']}* @{info['username']} | {price}")
    lines.append(f"\n\u05e1\u05d4\"\u05db \u05d1\u05d5\u05d8\u05d9\u05dd \u05e4\u05e2\u05d9\u05dc\u05d9\u05dd: {len(ECOSYSTEM_BOTS)}")
    await m.answer("\n".join(lines), parse_mode="Markdown")


@dp.message(Command("revenue"))
async def revenue_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    stats = await pay_db.get_stats()
    lines = ["\U0001f4b0 *\u05d3\u05d5\u05d7 \u05d4\u05db\u05e0\u05e1\u05d5\u05ea*\n"]
    for row in stats["by_bot"]:
        lines.append(f"\u2022 {row['bot_name']}: {float(row['revenue']):.0f} \u20aa ({row['cnt']} \u05de\u05e9\u05ea\u05de\u05e9\u05d9\u05dd)")
    lines.append(f"\n*\u05e1\u05d4\"\u05db: {stats['total_revenue']:.0f} \u20aa*")
    await m.answer("\n".join(lines), parse_mode="Markdown")


@dp.message(Command("broadcast"))
async def broadcast_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    text = m.text.replace("/broadcast", "").strip()
    if not text:
        await m.answer("\u05e9\u05d9\u05de\u05d5\u05e9: `/broadcast \u05d4\u05d5\u05d3\u05e2\u05d4 \u05dc\u05db\u05d5\u05dc\u05dd`", parse_mode="Markdown")
        return

    pool = await pay_db.get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT DISTINCT user_id FROM premium_users WHERE payment_status='approved'"
        )
    sent = 0
    for row in rows:
        try:
            await bot.send_message(row["user_id"], f"\U0001f4e2 *SLH SPARK*\n\n{text}", parse_mode="Markdown")
            sent += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)

    await m.answer(f"\u2705 \u05e0\u05e9\u05dc\u05d7 \u05dc-{sent}/{len(rows)} \u05de\u05e9\u05ea\u05de\u05e9\u05d9\u05dd")


async def main():
    await pay_db.init_schema()
    logger.info("=" * 50)
    logger.info("SLH SPARK SYSTEM | Super Admin Bot")
    logger.info("=" * 50)
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
