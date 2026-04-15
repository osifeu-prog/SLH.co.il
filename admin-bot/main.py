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


# ═══════════════════════════════════════════
# Access Requests - approve old paying users
# ═══════════════════════════════════════════
@dp.message(Command("requests"))
async def access_requests_cmd(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    pending = await pay_db.get_pending_access_requests()
    if not pending:
        await m.answer("\u2705 \u05d0\u05d9\u05df \u05d1\u05e7\u05e9\u05d5\u05ea \u05d2\u05d9\u05e9\u05d4 \u05de\u05de\u05ea\u05d9\u05e0\u05d5\u05ea!")
        return
    for p in pending[:10]:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2705 \u05d0\u05e9\u05e8", callback_data=f"acc_ok:{p['id']}"),
             InlineKeyboardButton(text="\u274c \u05d3\u05d7\u05d4", callback_data=f"acc_no:{p['id']}")]
        ])
        text = (
            f"\U0001f4cb \u05d1\u05e7\u05e9\u05ea \u05d2\u05d9\u05e9\u05d4 #{p['id']}\n"
            f"\u05de\u05e9\u05ea\u05de\u05e9: @{p.get('username') or '?'} ({p['user_id']})\n"
            f"\u05d1\u05d5\u05d8: {p['bot_name']}\n"
            f"\u05e1\u05d9\u05d1\u05d4: {p.get('reason') or '-'}\n"
            f"\u05ea\u05d0\u05e8\u05d9\u05da: {str(p.get('created_at',''))[:16]}"
        )
        if p.get("receipt_file_id"):
            try:
                await bot.send_photo(m.chat.id, p["receipt_file_id"], caption=text, reply_markup=kb)
            except Exception:
                await m.answer(text, reply_markup=kb)
        else:
            await m.answer(text, reply_markup=kb)


@dp.callback_query(F.data.startswith("acc_ok:"))
async def approve_access_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    rid = int(cb.data.split(":")[1])
    result = await pay_db.approve_access(rid)
    if result:
        try:
            await bot.send_message(result["user_id"],
                "\u2705 \u05d1\u05e7\u05e9\u05ea \u05d4\u05d2\u05d9\u05e9\u05d4 \u05e9\u05dc\u05da \u05d0\u05d5\u05e9\u05e8\u05d4!\n"
                "\u05db\u05dc \u05d4\u05e4\u05d9\u05e6'\u05e8\u05d9\u05dd \u05d6\u05de\u05d9\u05e0\u05d9\u05dd \u05e2\u05d1\u05d5\u05e8\u05da. \U0001f680")
        except Exception:
            pass
        await cb.message.edit_text(f"\u2705 \u05d0\u05d5\u05e9\u05e8 #{rid} | @{result.get('username','?')}")
    await cb.answer("\u2705")


@dp.callback_query(F.data.startswith("acc_no:"))
async def reject_access_cb(cb: types.CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    rid = int(cb.data.split(":")[1])
    result = await pay_db.reject_access(rid)
    if result:
        try:
            await bot.send_message(result["user_id"],
                "\u274c \u05d1\u05e7\u05e9\u05ea \u05d4\u05d2\u05d9\u05e9\u05d4 \u05e0\u05d3\u05d7\u05ea\u05d4.\n\u05dc\u05e4\u05e8\u05d8\u05d9\u05dd: /premium")
        except Exception:
            pass
        await cb.message.edit_text(f"\u274c \u05e0\u05d3\u05d7\u05d4 #{rid}")
    await cb.answer("\u274c")


# ═══════════════════════════════════════════
# Image Studio - Resize + GIF Creator
# ═══════════════════════════════════════════
user_image_mode = {}  # uid -> "resize_XXX" or "gif_XXX"

@dp.message(Command("studio"))
@dp.message(Command("resize"))
async def studio_menu(m: types.Message):
    if not is_admin(m.from_user.id):
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4f7 \u05e9\u05d9\u05e0\u05d5\u05d9 \u05d2\u05d5\u05d3\u05dc", callback_data="studio:resize_menu")],
        [InlineKeyboardButton(text="\U0001f3ac \u05d9\u05e6\u05d9\u05e8\u05ea GIF", callback_data="studio:gif_menu")],
    ])
    await m.answer(
        "\U0001f3a8 *SLH Image Studio*\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "\u05d1\u05d7\u05e8 \u05de\u05d4 \u05dc\u05e2\u05e9\u05d5\u05ea:",
        parse_mode="Markdown", reply_markup=kb,
    )

@dp.callback_query(F.data == "studio:resize_menu")
async def resize_menu(cb: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="640x360 (BotFather Game)", callback_data="studio:set_resize:640x360")],
        [InlineKeyboardButton(text="320x320 (Bot Profile)", callback_data="studio:set_resize:320x320")],
        [InlineKeyboardButton(text="512x512 (Sticker)", callback_data="studio:set_resize:512x512")],
        [InlineKeyboardButton(text="1280x720 (HD Preview)", callback_data="studio:set_resize:1280x720")],
        [InlineKeyboardButton(text="1080x1080 (Instagram)", callback_data="studio:set_resize:1080x1080")],
        [InlineKeyboardButton(text="\U0001f4f7 \u05db\u05dc \u05d4\u05d2\u05d3\u05dc\u05d9\u05dd \u05d1\u05d9\u05d7\u05d3", callback_data="studio:set_resize:all")],
    ])
    await cb.message.answer(
        "\U0001f4f7 *\u05e9\u05d9\u05e0\u05d5\u05d9 \u05d2\u05d5\u05d3\u05dc*\n\n"
        "\u05d1\u05d7\u05e8 \u05d2\u05d5\u05d3\u05dc, \u05d0\u05d7\u05e8 \u05db\u05da \u05e9\u05dc\u05d7 \u05ea\u05de\u05d5\u05e0\u05d4:",
        parse_mode="Markdown", reply_markup=kb,
    )
    await cb.answer()

@dp.callback_query(F.data == "studio:gif_menu")
async def gif_menu(cb: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f300 Zoom (640x360)", callback_data="studio:set_gif:zoom")],
        [InlineKeyboardButton(text="\U0001f4ab Pulse (640x360)", callback_data="studio:set_gif:pulse")],
        [InlineKeyboardButton(text="\U0001f30a Wave (640x360)", callback_data="studio:set_gif:wave")],
        [InlineKeyboardButton(text="\u2728 Sparkle (640x360)", callback_data="studio:set_gif:sparkle")],
        [InlineKeyboardButton(text="\U0001f504 Rotate (320x320)", callback_data="studio:set_gif:rotate")],
        [InlineKeyboardButton(text="\U0001f3ac \u05db\u05dc \u05d4\u05d0\u05e0\u05d9\u05de\u05e6\u05d9\u05d5\u05ea \u05d1\u05d9\u05d7\u05d3", callback_data="studio:set_gif:all")],
    ])
    await cb.message.answer(
        "\U0001f3ac *\u05d9\u05e6\u05d9\u05e8\u05ea GIF*\n\n"
        "\u05d1\u05d7\u05e8 \u05e1\u05d2\u05e0\u05d5\u05df \u05d0\u05e0\u05d9\u05de\u05e6\u05d9\u05d4, \u05d0\u05d7\u05e8 \u05db\u05da \u05e9\u05dc\u05d7 \u05ea\u05de\u05d5\u05e0\u05d4:",
        parse_mode="Markdown", reply_markup=kb,
    )
    await cb.answer()

@dp.callback_query(F.data.startswith("studio:set_"))
async def set_mode(cb: types.CallbackQuery):
    mode = cb.data.replace("studio:set_", "")
    user_image_mode[cb.from_user.id] = mode
    mode_names = {
        "resize:640x360": "\U0001f4f7 640x360",
        "resize:320x320": "\U0001f4f7 320x320",
        "resize:512x512": "\U0001f4f7 512x512",
        "resize:1280x720": "\U0001f4f7 1280x720",
        "resize:1080x1080": "\U0001f4f7 1080x1080",
        "resize:all": "\U0001f4f7 \u05db\u05dc \u05d4\u05d2\u05d3\u05dc\u05d9\u05dd",
        "gif:zoom": "\U0001f300 Zoom GIF",
        "gif:pulse": "\U0001f4ab Pulse GIF",
        "gif:wave": "\U0001f30a Wave GIF",
        "gif:sparkle": "\u2728 Sparkle GIF",
        "gif:rotate": "\U0001f504 Rotate GIF",
        "gif:all": "\U0001f3ac \u05db\u05dc \u05d4\u05d0\u05e0\u05d9\u05de\u05e6\u05d9\u05d5\u05ea",
    }
    name = mode_names.get(mode, mode)
    await cb.message.answer(f"\u2705 \u05de\u05d5\u05d3 \u05e0\u05d1\u05d7\u05e8: {name}\n\n\U0001f4f7 \u05e2\u05db\u05e9\u05d9\u05d5 \u05e9\u05dc\u05d7 \u05ea\u05de\u05d5\u05e0\u05d4!")
    await cb.answer()


@dp.message(F.photo)
async def handle_photo(m: types.Message):
    if not is_admin(m.from_user.id):
        return

    mode = user_image_mode.get(m.from_user.id, "")
    if not mode:
        await m.answer(
            "\U0001f4f7 \u05e9\u05dc\u05d7\u05ea \u05ea\u05de\u05d5\u05e0\u05d4! \u05d0\u05d1\u05dc \u05e7\u05d5\u05d3\u05dd \u05d1\u05d7\u05e8 \u05de\u05d4 \u05dc\u05e2\u05e9\u05d5\u05ea:\n/studio"
        )
        return

    try:
        from io import BytesIO
        import math
        from PIL import Image, ImageEnhance, ImageFilter
        from aiogram.types import BufferedInputFile

        photo = m.photo[-1]
        file = await bot.get_file(photo.file_id)
        data = await bot.download_file(file.file_path)
        img = Image.open(BytesIO(data.read())).convert("RGB")

        await m.answer("\u23f3 \u05de\u05e2\u05d1\u05d3...")

        if mode.startswith("resize:"):
            size_key = mode.split(":")[1]
            sizes = {
                "640x360": (640, 360), "320x320": (320, 320),
                "512x512": (512, 512), "1280x720": (1280, 720),
                "1080x1080": (1080, 1080),
            }
            if size_key == "all":
                for name, sz in sizes.items():
                    resized = img.copy().resize(sz, Image.LANCZOS)
                    buf = BytesIO()
                    resized.save(buf, format="PNG")
                    buf.seek(0)
                    doc = BufferedInputFile(buf.read(), filename=f"slh_{name}.png")
                    await m.answer_document(doc, caption=f"\u2705 {name}")
            else:
                sz = sizes.get(size_key, (640, 360))
                resized = img.copy().resize(sz, Image.LANCZOS)
                buf = BytesIO()
                resized.save(buf, format="PNG")
                buf.seek(0)
                doc = BufferedInputFile(buf.read(), filename=f"slh_{size_key}.png")
                await m.answer_document(doc, caption=f"\u2705 {size_key}")

        elif mode.startswith("gif:"):
            effect = mode.split(":")[1]
            effects_to_run = [effect] if effect != "all" else ["zoom", "pulse", "wave", "sparkle", "rotate"]

            for eff in effects_to_run:
                frames = []
                n = 20

                if eff == "zoom":
                    for i in range(n):
                        s = 1.0 + 0.04 * math.sin(i * 2 * math.pi / n)
                        w, h = int(640 * s), int(360 * s)
                        f = img.copy().resize((w, h), Image.LANCZOS)
                        l, t = (w - 640) // 2, (h - 360) // 2
                        frames.append(f.crop((l, t, l + 640, t + 360)))

                elif eff == "pulse":
                    for i in range(n):
                        brightness = 1.0 + 0.3 * math.sin(i * 2 * math.pi / n)
                        f = img.copy().resize((640, 360), Image.LANCZOS)
                        f = ImageEnhance.Brightness(f).enhance(brightness)
                        frames.append(f)

                elif eff == "wave":
                    base = img.copy().resize((700, 400), Image.LANCZOS)
                    for i in range(n):
                        offset_x = int(30 * math.sin(i * 2 * math.pi / n))
                        offset_y = int(20 * math.cos(i * 2 * math.pi / n))
                        l = 30 + offset_x
                        t = 20 + offset_y
                        frames.append(base.crop((l, t, l + 640, t + 360)))

                elif eff == "sparkle":
                    for i in range(n):
                        f = img.copy().resize((640, 360), Image.LANCZOS)
                        contrast = 1.0 + 0.4 * math.sin(i * 4 * math.pi / n)
                        color = 1.0 + 0.2 * math.cos(i * 2 * math.pi / n)
                        f = ImageEnhance.Contrast(f).enhance(contrast)
                        f = ImageEnhance.Color(f).enhance(color)
                        frames.append(f)

                elif eff == "rotate":
                    base = img.copy().resize((450, 450), Image.LANCZOS)
                    for i in range(n):
                        angle = i * (360 / n)
                        f = base.rotate(angle, expand=False, fillcolor=(0, 0, 0))
                        l = (450 - 320) // 2
                        t = (450 - 320) // 2
                        f = f.crop((l, t, l + 320, t + 320))
                        frames.append(f)

                if frames:
                    buf = BytesIO()
                    frames[0].save(buf, format="GIF", save_all=True,
                                   append_images=frames[1:], duration=80, loop=0)
                    buf.seek(0)
                    eff_names = {
                        "zoom": "\U0001f300 Zoom",
                        "pulse": "\U0001f4ab Pulse",
                        "wave": "\U0001f30a Wave",
                        "sparkle": "\u2728 Sparkle",
                        "rotate": "\U0001f504 Rotate",
                    }
                    doc = BufferedInputFile(buf.read(), filename=f"slh_{eff}.gif")
                    await m.answer_document(doc, caption=f"\U0001f3ac {eff_names.get(eff, eff)}")

        user_image_mode.pop(m.from_user.id, None)
        await m.answer("\u2705 \u05e1\u05d9\u05d9\u05de\u05ea\u05d9! \u05dc\u05e2\u05d5\u05d3: /studio")

    except Exception as e:
        await m.answer(f"\u274c \u05e9\u05d2\u05d9\u05d0\u05d4: {e}")


async def main():
    await pay_db.init_schema()
    logger.info("=" * 50)
    logger.info("SLH SPARK SYSTEM | Super Admin Bot")
    logger.info("=" * 50)
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
