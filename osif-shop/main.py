"""
OsifShop - Inventory Management SaaS Bot
Barcode scanning, stock management, reports.
Powered by SPARK IND
"""
import os, sys, asyncio, logging, re, io
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB,
    ReplyKeyboardMarkup as RKM, KeyboardButton as KB,
    BufferedInputFile, WebAppInfo,
)

sys.path.insert(0, "/app/shared")
sys.path.insert(0, "/app")

from slh_payments import db as pay_db
from slh_payments.config import ADMIN_USER_ID

from inventory_db import (
    init_tables, get_shop, create_shop,
    get_product_by_barcode, add_product, add_stock, remove_stock,
    set_price, set_cost, set_min_quantity,
    get_all_products, search_products, count_products,
    get_low_stock, get_report, export_csv,
)
from barcode_api import lookup_barcode

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("osifshop")

TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not TOKEN:
    raise SystemExit("BOT_TOKEN missing")

PRICE_ILS = float(os.getenv("PRICE_ILS", "49"))
PRICE_TON = float(os.getenv("PRICE_TON", "2.5"))
TON_WALLET = os.getenv("TON_WALLET", "UQDhfyUPSJ8x9xnoeccTl55PEny7zUvDW8UabZ7PdDo52noF")
FREE_PRODUCT_LIMIT = 5
SUPPORT_PHONE = "0584203384"
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://osifshop.slh-nft.com")

bot = Bot(TOKEN)
dp = Dispatcher()

# Track scan mode per user
scan_mode = {}


# ═══════════════════════════════════
# HELPERS
# ═══════════════════════════════════
async def is_paid(uid: int) -> bool:
    if uid == ADMIN_USER_ID:
        return True
    return await pay_db.is_premium(uid, "osif_shop")


NO_SHOP_MSG = "\U0001f6d2 \u05e6\u05e8\u05d9\u05da \u05dc\u05d9\u05e6\u05d5\u05e8 \u05d7\u05e0\u05d5\u05ea \u05e7\u05d5\u05d3\u05dd:\n/shop <\u05e9\u05dd \u05d4\u05d7\u05e0\u05d5\u05ea>\n\n\u05d3\u05d5\u05d2\u05de\u05d4: /shop Giga Store"

async def require_shop(uid: int):
    """Returns shop row or None."""
    return await get_shop(uid)


def home_kb():
    return RKM(keyboard=[
        [KB(text="\U0001f4f7 \u05e1\u05e8\u05d5\u05e7 \u05d1\u05e8\u05e7\u05d5\u05d3", web_app=WebAppInfo(url=WEBAPP_URL))],
        [KB(text="\U0001f4e6 \u05de\u05dc\u05d0\u05d9"), KB(text="\U0001f4c9 \u05de\u05dc\u05d0\u05d9 \u05e0\u05de\u05d5\u05da")],
        [KB(text="\U0001f50d \u05d7\u05d9\u05e4\u05d5\u05e9"), KB(text="\U0001f4ca \u05d3\u05d5\u05d7")],
        [KB(text="\U0001f4be \u05d9\u05d9\u05e6\u05d5\u05d0"), KB(text="\u2753 \u05e2\u05d6\u05e8\u05d4")],
    ], resize_keyboard=True)


def fmt_product(p, currency="ILS"):
    """Format product for display."""
    sym = "\u20aa" if currency == "ILS" else "$"
    qty = p['quantity']
    alert = " \u26a0\ufe0f" if qty <= p['min_quantity'] else ""
    price_s = f"{float(p['price']):.2f}{sym}" if p['price'] else "\u05dc\u05d0 \u05e0\u05e7\u05d1\u05e2"
    return (
        f"\U0001f4e6 {p['name']}\n"
        f"  \U0001f3f7 {p['barcode']}\n"
        f"  \U0001f4b0 {price_s}\n"
        f"  \U0001f4e6 \u05de\u05dc\u05d0\u05d9: {qty}{alert}\n"
    )


# ═══════════════════════════════════
# /start
# ═══════════════════════════════════
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    uid = m.from_user.id
    paid = await is_paid(uid)
    shop = await get_shop(uid)

    if not paid:
        await m.answer(
            "\U0001f6d2 OsifShop - \u05e0\u05d9\u05d4\u05d5\u05dc \u05de\u05dc\u05d0\u05d9 \u05d7\u05db\u05dd\n"
            "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
            "\u2705 \u05e1\u05e8\u05d9\u05e7\u05ea \u05d1\u05e8\u05e7\u05d5\u05d3\u05d9\u05dd - \u05d6\u05d9\u05d4\u05d5\u05d9 \u05d0\u05d5\u05d8\u05d5\u05de\u05d8\u05d9\n"
            "\u2705 \u05e0\u05d9\u05d4\u05d5\u05dc \u05de\u05dc\u05d0\u05d9 + \u05de\u05db\u05d9\u05e8\u05d5\u05ea\n"
            "\u2705 \u05d4\u05ea\u05e8\u05d0\u05d5\u05ea \u05de\u05dc\u05d0\u05d9 \u05e0\u05de\u05d5\u05da\n"
            "\u2705 \u05d3\u05d5\u05d7\u05d5\u05ea \u05d5\u05d9\u05d9\u05e6\u05d5\u05d0 CSV\n"
            "\u2705 \u05d7\u05d9\u05e4\u05d5\u05e9 \u05de\u05d5\u05e6\u05e8\u05d9\u05dd\n\n"
            f"\U0001f4b3 \u05de\u05d7\u05d9\u05e8: {PRICE_ILS}\u20aa / {PRICE_TON} TON\n\n"
            "\U0001f4b0 \u05dc\u05ea\u05e9\u05dc\u05d5\u05dd \u05e9\u05dc\u05d7 TON \u05de-@wallet \u05dc:\n"
            f"<code>{TON_WALLET}</code>\n\n"
            "\u05d5\u05e9\u05dc\u05d7 \u05e6\u05d9\u05dc\u05d5\u05dd \u05de\u05e1\u05da \u05db\u05d0\u05df.",
            parse_mode="HTML",
        )
        return

    if not shop:
        # Auto-create shop with user's first name
        name = m.from_user.first_name or "My Shop"
        default_name = f"\u05d7\u05e0\u05d5\u05ea {name}"
        shop = await create_shop(uid, default_name)
        await m.answer(
            f"\u2705 \u05d7\u05e0\u05d5\u05ea \"{default_name}\" \u05e0\u05d5\u05e6\u05e8\u05d4 \u05d0\u05d5\u05d8\u05d5\u05de\u05d8\u05d9\u05ea!\n\n"
            "\U0001f4a1 \u05dc\u05e9\u05d9\u05e0\u05d5\u05d9 \u05e9\u05dd: /shop <\u05e9\u05dd \u05d7\u05d3\u05e9>\n\n"
            "\u05e2\u05db\u05e9\u05d9\u05d5 \u05e1\u05e8\u05d5\u05e7 \u05d1\u05e8\u05e7\u05d5\u05d3 \u05dc\u05d4\u05d5\u05e1\u05e4\u05ea \u05de\u05d5\u05e6\u05e8!",
            reply_markup=home_kb(),
        )

    n_products = await count_products(shop["id"])
    low = await get_low_stock(shop["id"])
    n_low = len(low)

    await m.answer(
        f"\U0001f6d2 {shop['shop_name']}\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        f"\U0001f4e6 \u05de\u05d5\u05e6\u05e8\u05d9\u05dd: {n_products}\n"
        f"\u26a0\ufe0f \u05de\u05dc\u05d0\u05d9 \u05e0\u05de\u05d5\u05da: {n_low}\n\n"
        "\U0001f4f7 \u05e1\u05e8\u05d5\u05e7 \u05d1\u05e8\u05e7\u05d5\u05d3 - \u05d4\u05d5\u05e1\u05e3 \u05de\u05d5\u05e6\u05e8\n"
        "\U0001f4e6 \u05de\u05dc\u05d0\u05d9 - \u05e8\u05e9\u05d9\u05de\u05ea \u05de\u05d5\u05e6\u05e8\u05d9\u05dd\n"
        "\U0001f4c9 \u05de\u05dc\u05d0\u05d9 \u05e0\u05de\u05d5\u05da - \u05d4\u05ea\u05e8\u05d0\u05d5\u05ea\n"
        "\U0001f50d \u05d7\u05d9\u05e4\u05d5\u05e9 - \u05de\u05e6\u05d0 \u05de\u05d5\u05e6\u05e8\n"
        "\U0001f4ca \u05d3\u05d5\u05d7 - \u05e1\u05d9\u05db\u05d5\u05dd \u05e9\u05d1\u05d5\u05e2\u05d9\n"
        "\U0001f4be \u05d9\u05d9\u05e6\u05d5\u05d0 - \u05d4\u05d5\u05e8\u05d3\u05ea CSV\n\n"
        "OsifShop | SPARK IND",
        reply_markup=home_kb(),
    )


# ═══════════════════════════════════
# /shop - Create/rename store
# ═══════════════════════════════════
@dp.message(Command("shop"))
async def cmd_shop(m: types.Message, command: CommandObject = None):
    if not await is_paid(m.from_user.id):
        await m.answer(f"\U0001f512 \u05e9\u05dc\u05dd {PRICE_ILS}\u20aa \u05dc\u05d4\u05e4\u05e2\u05dc\u05d4"); return
    if not command or not command.args:
        existing = await get_shop(m.from_user.id)
        if existing:
            await m.answer(f"\U0001f6d2 \u05d7\u05e0\u05d5\u05ea: {existing['shop_name']}\n\n\u05dc\u05e9\u05d9\u05e0\u05d5\u05d9 \u05e9\u05dd: /shop <\u05e9\u05dd \u05d7\u05d3\u05e9>")
        else:
            await m.answer(
                "\U0001f6d2 \u05d9\u05e6\u05d9\u05e8\u05ea \u05d7\u05e0\u05d5\u05ea\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
                "\u05e9\u05dc\u05d7:\n/shop <\u05e9\u05dd \u05d4\u05d7\u05e0\u05d5\u05ea>\n\n"
                "\u05d3\u05d5\u05d2\u05de\u05d0\u05d5\u05ea:\n"
                "/shop Giga Store\n"
                "/shop \u05de\u05db\u05d5\u05dc\u05ea \u05d0\u05d5\u05e1\u05d9\u05e3\n"
                "/shop My Shop"
            )
        return
    name = command.args.strip()
    shop = await create_shop(m.from_user.id, name)
    await m.answer(f"\u2705 \u05d7\u05e0\u05d5\u05ea \"{shop['shop_name']}\" \u05e0\u05d5\u05e6\u05e8\u05d4!\n\n\u05e2\u05db\u05e9\u05d9\u05d5 \u05e1\u05e8\u05d5\u05e7 \u05d1\u05e8\u05e7\u05d5\u05d3 \u05dc\u05d4\u05d5\u05e1\u05e4\u05ea \u05de\u05d5\u05e6\u05e8 \u05e8\u05d0\u05e9\u05d5\u05df!", reply_markup=home_kb())


# ═══════════════════════════════════
# SCAN BARCODE
# ═══════════════════════════════════
@dp.message(F.text == "\U0001f4f7 \u05e1\u05e8\u05d5\u05e7 \u05d1\u05e8\u05e7\u05d5\u05d3")
@dp.message(Command("scan"))
async def cmd_scan(m: types.Message):
    uid = m.from_user.id
    if not await is_paid(uid):
        await m.answer(f"\U0001f512 \u05e9\u05dc\u05dd {PRICE_ILS}\u20aa \u05dc\u05d4\u05e4\u05e2\u05dc\u05d4"); return
    shop = await get_shop(uid)
    if not shop:
        await m.answer(NO_SHOP_MSG); return

    scan_mode[uid] = True
    await m.answer(
        "\U0001f4f7 \u05de\u05e6\u05d1 \u05e1\u05e8\u05d9\u05e7\u05d4\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "\u05d4\u05e7\u05dc\u05d3 \u05d0\u05ea \u05de\u05e1\u05e4\u05e8 \u05d4\u05d1\u05e8\u05e7\u05d5\u05d3 (13 \u05e1\u05e4\u05e8\u05d5\u05ea)\n"
        "\u05d0\u05d5 \u05e9\u05dc\u05d7 \u05ea\u05de\u05d5\u05e0\u05d4 \u05e9\u05dc \u05d4\u05d1\u05e8\u05e7\u05d5\u05d3\n\n"
        "\u05dc\u05d1\u05d9\u05d8\u05d5\u05dc: /cancel",
        reply_markup=IKM(inline_keyboard=[
            [IKB(text="\u274c \u05d1\u05d8\u05dc", callback_data="cancel_scan")],
        ]),
    )


@dp.callback_query(F.data == "cancel_scan")
async def cancel_scan(cb: types.CallbackQuery):
    scan_mode.pop(cb.from_user.id, None)
    await cb.message.answer("\u2705 \u05d9\u05e6\u05d0\u05ea \u05de\u05de\u05e6\u05d1 \u05e1\u05e8\u05d9\u05e7\u05d4", reply_markup=home_kb())
    await cb.answer()


@dp.message(Command("cancel"))
async def cmd_cancel(m: types.Message):
    scan_mode.pop(m.from_user.id, None)
    await m.answer("\u2705 \u05d1\u05d5\u05d8\u05dc", reply_markup=home_kb())


# Handle barcode from Mini App (camera scan)
@dp.message(F.web_app_data)
async def handle_webapp_barcode(m: types.Message):
    uid = m.from_user.id
    if not await is_paid(uid):
        await m.answer(f"\U0001f512 \u05e9\u05dc\u05dd {PRICE_ILS}\u20aa \u05dc\u05d4\u05e4\u05e2\u05dc\u05d4"); return
    shop = await get_shop(uid)
    if not shop:
        await m.answer(NO_SHOP_MSG); return

    barcode = m.web_app_data.data.strip()
    log.info("WebApp scan: user=%s barcode=%s", uid, barcode)
    await process_barcode(m, shop, barcode)


# Handle barcode text input (number patterns)
@dp.message(F.text.regexp(r"^\d{8,13}$"))
async def handle_barcode_text(m: types.Message):
    uid = m.from_user.id
    if not await is_paid(uid):
        return
    shop = await get_shop(uid)
    if not shop:
        return

    barcode = m.text.strip()
    await process_barcode(m, shop, barcode)


async def process_barcode(m: types.Message, shop, barcode: str):
    """Process a scanned/typed barcode."""
    # Check if product exists in shop
    existing = await get_product_by_barcode(shop["id"], barcode)
    if existing:
        currency = shop.get("currency", "ILS")
        txt = fmt_product(existing, currency)
        kb = IKM(inline_keyboard=[
            [IKB(text="\u2795 \u05d4\u05d5\u05e1\u05e3 \u05de\u05dc\u05d0\u05d9", callback_data=f"qadd:{barcode}:1"),
             IKB(text="\u2795 5", callback_data=f"qadd:{barcode}:5"),
             IKB(text="\u2795 10", callback_data=f"qadd:{barcode}:10")],
            [IKB(text="\u2796 \u05de\u05db\u05d9\u05e8\u05d4", callback_data=f"qrem:{barcode}:1"),
             IKB(text="\u2796 5", callback_data=f"qrem:{barcode}:5"),
             IKB(text="\u2796 10", callback_data=f"qrem:{barcode}:10")],
        ])
        await m.answer(f"\u2705 \u05de\u05d5\u05e6\u05e8 \u05e7\u05d9\u05d9\u05dd!\n\n{txt}", reply_markup=kb)
        return

    # Look up in Open Food Facts
    await m.answer(f"\U0001f50d \u05de\u05d7\u05e4\u05e9 {barcode}...")
    info = await lookup_barcode(barcode)

    if info and info.get("name"):
        prod = await add_product(shop["id"], barcode, info["name"], info.get("brand", ""),
                                 info.get("category", ""), info.get("image_url", ""))
        kb = IKM(inline_keyboard=[
            [IKB(text="\u2795 1", callback_data=f"qadd:{barcode}:1"),
             IKB(text="\u2795 5", callback_data=f"qadd:{barcode}:5"),
             IKB(text="\u2795 10", callback_data=f"qadd:{barcode}:10")],
            [IKB(text="\U0001f4b0 \u05e7\u05d1\u05e2 \u05de\u05d7\u05d9\u05e8", callback_data=f"setprice:{barcode}")],
        ])
        brand_s = f"\n\U0001f3f7 {info['brand']}" if info.get("brand") else ""
        await m.answer(
            f"\u2705 \u05de\u05d5\u05e6\u05e8 \u05d7\u05d3\u05e9 \u05e0\u05d5\u05e1\u05e3!\n\n"
            f"\U0001f4e6 {info['name']}{brand_s}\n"
            f"\U0001f3f7 {barcode}\n\n"
            "\u05db\u05de\u05d4 \u05d9\u05d7\u05d9\u05d3\u05d5\u05ea \u05dc\u05d4\u05d5\u05e1\u05d9\u05e3?",
            reply_markup=kb,
        )
    else:
        # Not found - ask user to name it
        scan_mode[m.from_user.id] = {"naming": barcode}
        await m.answer(
            f"\U0001f50d \u05d1\u05e8\u05e7\u05d5\u05d3 {barcode} \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0 \u05d1\u05de\u05d0\u05d2\u05e8.\n\n"
            "\u05d4\u05e7\u05dc\u05d3 \u05e9\u05dd \u05de\u05d5\u05e6\u05e8:"
        )


# Handle product naming (when barcode not found in API)
@dp.message(F.text)
async def handle_text(m: types.Message):
    uid = m.from_user.id
    state = scan_mode.get(uid)
    if not isinstance(state, dict) or "naming" not in state:
        return  # Not in naming mode, ignore

    shop = await get_shop(uid)
    if not shop:
        return

    barcode = state["naming"]
    name = m.text.strip()
    scan_mode.pop(uid, None)

    prod = await add_product(shop["id"], barcode, name)
    kb = IKM(inline_keyboard=[
        [IKB(text="\u2795 1", callback_data=f"qadd:{barcode}:1"),
         IKB(text="\u2795 5", callback_data=f"qadd:{barcode}:5"),
         IKB(text="\u2795 10", callback_data=f"qadd:{barcode}:10")],
    ])
    await m.answer(
        f"\u2705 {name} \u05e0\u05d5\u05e1\u05e3!\n\U0001f3f7 {barcode}\n\n\u05db\u05de\u05d4 \u05dc\u05d4\u05d5\u05e1\u05d9\u05e3?",
        reply_markup=kb,
    )


# ═══════════════════════════════════
# QUICK ADD/REMOVE CALLBACKS
# ═══════════════════════════════════
@dp.callback_query(F.data.startswith("qadd:"))
async def quick_add(cb: types.CallbackQuery):
    parts = cb.data.split(":")
    barcode, qty = parts[1], int(parts[2])
    shop = await get_shop(cb.from_user.id)
    if not shop:
        await cb.answer("\u274c"); return
    prod = await add_stock(shop["id"], barcode, qty, "\u05d4\u05d5\u05e1\u05e4\u05d4 \u05de\u05d4\u05d9\u05e8\u05d4")
    if prod:
        await cb.message.answer(f"\u2795 +{qty} | {prod['name']} | \u05de\u05dc\u05d0\u05d9: {prod['quantity']}")
    else:
        await cb.message.answer("\u274c \u05de\u05d5\u05e6\u05e8 \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0")
    await cb.answer()


@dp.callback_query(F.data.startswith("qrem:"))
async def quick_remove(cb: types.CallbackQuery):
    parts = cb.data.split(":")
    barcode, qty = parts[1], int(parts[2])
    shop = await get_shop(cb.from_user.id)
    if not shop:
        await cb.answer("\u274c"); return
    prod, status = await remove_stock(shop["id"], barcode, qty, "sale")
    if status == "ok":
        await cb.message.answer(f"\u2796 -{qty} | {prod['name']} | \u05de\u05dc\u05d0\u05d9: {prod['quantity']}")
    elif status == "insufficient":
        await cb.message.answer("\u274c \u05d0\u05d9\u05df \u05de\u05e1\u05e4\u05d9\u05e7 \u05d1\u05de\u05dc\u05d0\u05d9!")
    else:
        await cb.message.answer("\u274c \u05de\u05d5\u05e6\u05e8 \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0")
    await cb.answer()


# ═══════════════════════════════════
# /add /remove - Manual stock commands
# ═══════════════════════════════════
@dp.message(Command("add"))
async def cmd_add(m: types.Message, command: CommandObject = None):
    if not command or not command.args:
        await m.answer("/add <\u05d1\u05e8\u05e7\u05d5\u05d3> <\u05db\u05de\u05d5\u05ea>\n\u05d3\u05d5\u05d2\u05de\u05d4: /add 7290000001 10"); return
    shop = await get_shop(m.from_user.id)
    if not shop:
        await m.answer(NO_SHOP_MSG); return
    args = command.args.strip().split()
    barcode = args[0]
    qty = int(args[1]) if len(args) > 1 else 1
    prod = await add_stock(shop["id"], barcode, qty)
    if prod:
        await m.answer(f"\u2795 +{qty} | {prod['name']} | \u05de\u05dc\u05d0\u05d9: {prod['quantity']}")
    else:
        await m.answer(f"\u274c \u05d1\u05e8\u05e7\u05d5\u05d3 {barcode} \u05dc\u05d0 \u05e7\u05d9\u05d9\u05dd. \u05e1\u05e8\u05d5\u05e7 \u05e7\u05d5\u05d3\u05dd.")


@dp.message(Command("remove"))
async def cmd_remove(m: types.Message, command: CommandObject = None):
    if not command or not command.args:
        await m.answer("/remove <\u05d1\u05e8\u05e7\u05d5\u05d3> <\u05db\u05de\u05d5\u05ea>\n\u05d3\u05d5\u05d2\u05de\u05d4: /remove 7290000001 3"); return
    shop = await get_shop(m.from_user.id)
    if not shop:
        await m.answer(NO_SHOP_MSG); return
    args = command.args.strip().split()
    barcode = args[0]
    qty = int(args[1]) if len(args) > 1 else 1
    prod, status = await remove_stock(shop["id"], barcode, qty, "sale")
    if status == "ok":
        await m.answer(f"\u2796 -{qty} | {prod['name']} | \u05de\u05dc\u05d0\u05d9: {prod['quantity']}")
    elif status == "insufficient":
        await m.answer("\u274c \u05d0\u05d9\u05df \u05de\u05e1\u05e4\u05d9\u05e7 \u05d1\u05de\u05dc\u05d0\u05d9!")
    else:
        await m.answer(f"\u274c \u05d1\u05e8\u05e7\u05d5\u05d3 {barcode} \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0")


# ═══════════════════════════════════
# /setprice /setcost /setmin
# ═══════════════════════════════════
@dp.message(Command("setprice"))
async def cmd_setprice(m: types.Message, command: CommandObject = None):
    if not command or not command.args:
        await m.answer("/setprice <\u05d1\u05e8\u05e7\u05d5\u05d3> <\u05de\u05d7\u05d9\u05e8>"); return
    shop = await get_shop(m.from_user.id)
    if not shop: return
    args = command.args.strip().split()
    if len(args) < 2: await m.answer("/setprice <\u05d1\u05e8\u05e7\u05d5\u05d3> <\u05de\u05d7\u05d9\u05e8>"); return
    await set_price(shop["id"], args[0], float(args[1]))
    await m.answer(f"\u2705 \u05de\u05d7\u05d9\u05e8 \u05e2\u05d5\u05d3\u05db\u05df: {args[1]}\u20aa")


@dp.message(Command("setcost"))
async def cmd_setcost(m: types.Message, command: CommandObject = None):
    if not command or not command.args:
        await m.answer("/setcost <\u05d1\u05e8\u05e7\u05d5\u05d3> <\u05e2\u05dc\u05d5\u05ea>"); return
    shop = await get_shop(m.from_user.id)
    if not shop: return
    args = command.args.strip().split()
    if len(args) < 2: return
    await set_cost(shop["id"], args[0], float(args[1]))
    await m.answer(f"\u2705 \u05e2\u05dc\u05d5\u05ea \u05e2\u05d5\u05d3\u05db\u05e0\u05d4: {args[1]}\u20aa")


@dp.message(Command("setmin"))
async def cmd_setmin(m: types.Message, command: CommandObject = None):
    if not command or not command.args:
        await m.answer("/setmin <\u05d1\u05e8\u05e7\u05d5\u05d3> <\u05de\u05d9\u05e0\u05d9\u05de\u05d5\u05dd>"); return
    shop = await get_shop(m.from_user.id)
    if not shop: return
    args = command.args.strip().split()
    if len(args) < 2: return
    await set_min_quantity(shop["id"], args[0], int(args[1]))
    await m.answer(f"\u2705 \u05de\u05d9\u05e0\u05d9\u05de\u05d5\u05dd \u05e2\u05d5\u05d3\u05db\u05df: {args[1]}")


# ═══════════════════════════════════
# STOCK VIEW + SEARCH
# ═══════════════════════════════════
@dp.message(F.text == "\U0001f4e6 \u05de\u05dc\u05d0\u05d9")
@dp.message(Command("stock"))
async def cmd_stock(m: types.Message):
    shop = await get_shop(m.from_user.id)
    if not shop:
        await m.answer("\U0001f6d2 \u05e6\u05e8\u05d9\u05da \u05e7\u05d5\u05d3\u05dd \u05dc\u05d9\u05e6\u05d5\u05e8 \u05d7\u05e0\u05d5\u05ea:\n/shop <\u05e9\u05dd \u05d4\u05d7\u05e0\u05d5\u05ea>"); return
    products = await get_all_products(shop["id"])
    if not products:
        await m.answer("\U0001f4e6 \u05d0\u05d9\u05df \u05de\u05d5\u05e6\u05e8\u05d9\u05dd \u05e2\u05d3\u05d9\u05d9\u05df.\n\u05e1\u05e8\u05d5\u05e7 \u05d1\u05e8\u05e7\u05d5\u05d3 \u05dc\u05d4\u05ea\u05d7\u05dc\u05d4!"); return
    currency = shop.get("currency", "ILS")
    txt = f"\U0001f4e6 \u05de\u05dc\u05d0\u05d9 - {shop['shop_name']}\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
    for p in products[:30]:
        qty = p["quantity"]
        alert = " \u26a0\ufe0f" if qty <= p["min_quantity"] else ""
        price_s = f"{float(p['price']):.2f}\u20aa" if p["price"] else ""
        txt += f"\U0001f4e6 {p['name']} | {qty}{alert} | {price_s}\n"
    if len(products) > 30:
        txt += f"\n... \u05d5\u05e2\u05d5\u05d3 {len(products) - 30} \u05de\u05d5\u05e6\u05e8\u05d9\u05dd"
    txt += f"\n\n\u05e1\u05d4\"\u05db: {len(products)} \u05de\u05d5\u05e6\u05e8\u05d9\u05dd"
    await m.answer(txt)


@dp.message(F.text == "\U0001f50d \u05d7\u05d9\u05e4\u05d5\u05e9")
@dp.message(Command("search"))
async def cmd_search(m: types.Message, command: CommandObject = None):
    shop = await get_shop(m.from_user.id)
    if not shop:
        await m.answer(NO_SHOP_MSG); return
    if command and command.args:
        query = command.args.strip()
    else:
        await m.answer("\U0001f50d \u05d4\u05e7\u05dc\u05d3 \u05d8\u05e7\u05e1\u05d8 \u05dc\u05d7\u05d9\u05e4\u05d5\u05e9:\n/search <\u05e9\u05dd/\u05d1\u05e8\u05e7\u05d5\u05d3/\u05de\u05d5\u05ea\u05d2>")
        return
    results = await search_products(shop["id"], query)
    if not results:
        await m.answer(f"\u274c \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0: \"{query}\""); return
    txt = f"\U0001f50d \u05ea\u05d5\u05e6\u05d0\u05d5\u05ea \u05dc-\"{query}\":\n\n"
    for p in results:
        txt += fmt_product(p, shop.get("currency", "ILS")) + "\n"
    await m.answer(txt)


# ═══════════════════════════════════
# LOW STOCK
# ═══════════════════════════════════
@dp.message(F.text == "\U0001f4c9 \u05de\u05dc\u05d0\u05d9 \u05e0\u05de\u05d5\u05da")
@dp.message(Command("low"))
async def cmd_low(m: types.Message):
    shop = await get_shop(m.from_user.id)
    if not shop: return
    low = await get_low_stock(shop["id"])
    if not low:
        await m.answer("\u2705 \u05d0\u05d9\u05df \u05de\u05d5\u05e6\u05e8\u05d9\u05dd \u05d1\u05de\u05dc\u05d0\u05d9 \u05e0\u05de\u05d5\u05da!"); return
    txt = f"\u26a0\ufe0f \u05de\u05dc\u05d0\u05d9 \u05e0\u05de\u05d5\u05da ({len(low)})\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
    for p in low:
        txt += f"\U0001f534 {p['name']} | \u05de\u05dc\u05d0\u05d9: {p['quantity']} (\u05de\u05d9\u05e0\u05d9\u05de\u05d5\u05dd: {p['min_quantity']})\n"
        txt += f"  \U0001f3f7 {p['barcode']}\n\n"
    await m.answer(txt)


# ═══════════════════════════════════
# REPORT
# ═══════════════════════════════════
@dp.message(F.text == "\U0001f4ca \u05d3\u05d5\u05d7")
@dp.message(Command("report"))
async def cmd_report(m: types.Message):
    shop = await get_shop(m.from_user.id)
    if not shop: return
    r = await get_report(shop["id"], 7)
    sym = "\u20aa"
    txt = (
        f"\U0001f4ca \u05d3\u05d5\u05d7 \u05e9\u05d1\u05d5\u05e2\u05d9 - {shop['shop_name']}\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        f"\U0001f4e6 \u05de\u05d5\u05e6\u05e8\u05d9\u05dd: {r['total_products']}\n"
        f"\U0001f4e6 \u05e1\u05d4\"\u05db \u05d9\u05d7\u05d9\u05d3\u05d5\u05ea: {r['total_stock']}\n"
        f"\U0001f4b0 \u05e9\u05d5\u05d5\u05d9 \u05de\u05dc\u05d0\u05d9: {r['stock_value']:.2f}{sym}\n"
        f"\U0001f4b8 \u05e2\u05dc\u05d5\u05ea \u05de\u05dc\u05d0\u05d9: {r['cost_value']:.2f}{sym}\n"
    )
    profit = r["stock_value"] - r["cost_value"]
    if profit > 0:
        txt += f"\U0001f4c8 \u05e8\u05d5\u05d5\u05d7 \u05e6\u05e4\u05d5\u05d9: {profit:.2f}{sym}\n"
    txt += (
        f"\n\U0001f4e5 \u05e0\u05db\u05e0\u05e1\u05d5 \u05d4\u05e9\u05d1\u05d5\u05e2: {r['movements_in']} \u05d9\u05d7\u05d9\u05d3\u05d5\u05ea\n"
        f"\U0001f4e4 \u05e0\u05de\u05db\u05e8\u05d5 \u05d4\u05e9\u05d1\u05d5\u05e2: {r['movements_out']} \u05d9\u05d7\u05d9\u05d3\u05d5\u05ea\n"
        f"\u26a0\ufe0f \u05de\u05dc\u05d0\u05d9 \u05e0\u05de\u05d5\u05da: {r['low_stock']}\n"
    )
    if r["top_sold"]:
        txt += "\n\U0001f3c6 \u05e0\u05de\u05db\u05e8\u05d9\u05dd \u05d1\u05d9\u05d5\u05ea\u05e8:\n"
        for ts in r["top_sold"]:
            txt += f"  {ts['name']}: {ts['sold']} \u05d9\u05d7\u05d9\u05d3\u05d5\u05ea\n"
    await m.answer(txt)


# ═══════════════════════════════════
# EXPORT CSV
# ═══════════════════════════════════
@dp.message(F.text == "\U0001f4be \u05d9\u05d9\u05e6\u05d5\u05d0")
@dp.message(Command("export"))
async def cmd_export(m: types.Message):
    shop = await get_shop(m.from_user.id)
    if not shop: return
    csv_data = await export_csv(shop["id"])
    buf = io.BytesIO(csv_data.encode("utf-8-sig"))
    doc = BufferedInputFile(buf.read(), filename=f"{shop['shop_name']}_inventory.csv")
    await m.answer_document(doc, caption=f"\U0001f4be \u05de\u05dc\u05d0\u05d9 - {shop['shop_name']}")


# ═══════════════════════════════════
# HELP
# ═══════════════════════════════════
@dp.message(F.text == "\u2753 \u05e2\u05d6\u05e8\u05d4")
@dp.message(Command("help"))
async def cmd_help(m: types.Message):
    await m.answer(
        "\U0001f6d2 OsifShop - \u05e2\u05d6\u05e8\u05d4\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "\U0001f4f7 \u05e1\u05e8\u05d9\u05e7\u05d4:\n"
        "  \u05d4\u05e7\u05dc\u05d3 \u05de\u05e1\u05e4\u05e8 \u05d1\u05e8\u05e7\u05d5\u05d3 (8-13 \u05e1\u05e4\u05e8\u05d5\u05ea)\n"
        "  \u05d4\u05de\u05d5\u05e6\u05e8 \u05d9\u05d6\u05d5\u05d4\u05d4 \u05d0\u05d5\u05d8\u05d5\u05de\u05d8\u05d9\u05ea!\n\n"
        "\U0001f4e6 \u05de\u05dc\u05d0\u05d9:\n"
        "  /add <\u05d1\u05e8\u05e7\u05d5\u05d3> <\u05db\u05de\u05d5\u05ea> - \u05d4\u05d5\u05e1\u05e4\u05d4\n"
        "  /remove <\u05d1\u05e8\u05e7\u05d5\u05d3> <\u05db\u05de\u05d5\u05ea> - \u05de\u05db\u05d9\u05e8\u05d4\n"
        "  /stock - \u05e8\u05e9\u05d9\u05de\u05ea \u05de\u05dc\u05d0\u05d9\n"
        "  /low - \u05de\u05dc\u05d0\u05d9 \u05e0\u05de\u05d5\u05da\n"
        "  /search <\u05d8\u05e7\u05e1\u05d8> - \u05d7\u05d9\u05e4\u05d5\u05e9\n\n"
        "\U0001f4b0 \u05de\u05d7\u05d9\u05e8\u05d9\u05dd:\n"
        "  /setprice <\u05d1\u05e8\u05e7\u05d5\u05d3> <\u05de\u05d7\u05d9\u05e8>\n"
        "  /setcost <\u05d1\u05e8\u05e7\u05d5\u05d3> <\u05e2\u05dc\u05d5\u05ea>\n"
        "  /setmin <\u05d1\u05e8\u05e7\u05d5\u05d3> <\u05de\u05d9\u05e0\u05d9\u05de\u05d5\u05dd>\n\n"
        "\U0001f4ca \u05d3\u05d5\u05d7\u05d5\u05ea:\n"
        "  /report - \u05d3\u05d5\u05d7 \u05e9\u05d1\u05d5\u05e2\u05d9\n"
        "  /export - \u05d9\u05d9\u05e6\u05d5\u05d0 CSV\n\n"
        f"\U0001f4de \u05ea\u05de\u05d9\u05db\u05d4: {SUPPORT_PHONE}\n"
        "OsifShop | SPARK IND"
    )


# ═══════════════════════════════════
# PAYMENT (photo proof) - only for unpaid users
# ═══════════════════════════════════
@dp.message(F.photo)
async def handle_photo(m: types.Message):
    uid = m.from_user.id

    # If already paid, photo is not payment - might be barcode scan attempt
    if await is_paid(uid):
        await m.answer(
            "\U0001f4f7 \u05dc\u05e1\u05e8\u05d9\u05e7\u05ea \u05d1\u05e8\u05e7\u05d5\u05d3 \u05d4\u05e7\u05dc\u05d3 \u05d0\u05ea \u05d4\u05de\u05e1\u05e4\u05e8 (8-13 \u05e1\u05e4\u05e8\u05d5\u05ea).\n\n"
            "\u05d3\u05d5\u05d2\u05de\u05d4: 7290000066318\n\n"
            "\U0001f4a1 \u05e1\u05e8\u05d9\u05e7\u05d4 \u05de\u05ea\u05de\u05d5\u05e0\u05d4 \u05ea\u05d4\u05d9\u05d4 \u05d6\u05de\u05d9\u05e0\u05d4 \u05d1\u05e7\u05e8\u05d5\u05d1!"
        )
        return

    # Not paid - treat as payment proof
    uname = m.from_user.username or ""
    fid = m.photo[-1].file_id
    await pay_db.create_payment(uid, uname, "osif_shop", PRICE_ILS, "ILS")
    await pay_db.submit_proof(uid, "osif_shop", fid)
    await m.answer("\u2705 \u05d0\u05d9\u05e9\u05d5\u05e8 \u05ea\u05e9\u05dc\u05d5\u05dd \u05d4\u05ea\u05e7\u05d1\u05dc!\n\u05de\u05de\u05ea\u05d9\u05df \u05dc\u05d0\u05d9\u05e9\u05d5\u05e8...")
    kb = IKM(inline_keyboard=[
        [IKB(text="\u2705 \u05d0\u05e9\u05e8", callback_data=f"shop_ok:{uid}"),
         IKB(text="\u274c \u05d3\u05d7\u05d4", callback_data=f"shop_no:{uid}")],
    ])
    try:
        await bot.send_photo(ADMIN_USER_ID, fid,
            caption=f"\U0001f6d2 OsifShop \u05ea\u05e9\u05dc\u05d5\u05dd\n@{uname} ({uid})\n{PRICE_ILS}\u20aa",
            reply_markup=kb)
    except: pass


@dp.callback_query(F.data.startswith("shop_ok:"))
async def approve_payment(cb: types.CallbackQuery):
    if cb.from_user.id != ADMIN_USER_ID: return
    uid = int(cb.data.split(":")[1])
    await pay_db.approve_payment(uid, "osif_shop", cb.from_user.id)
    await cb.message.edit_caption(caption=f"\u2705 \u05d0\u05d5\u05e9\u05e8 {uid}")
    try:
        await bot.send_message(uid,
            "\u2705 \u05ea\u05e9\u05dc\u05d5\u05dd \u05d0\u05d5\u05e9\u05e8! OsifShop \u05de\u05d5\u05e4\u05e2\u05dc!\n\n"
            "\u05e9\u05dc\u05d7:\n/shop <\u05e9\u05dd \u05d4\u05d7\u05e0\u05d5\u05ea>\n\n"
            "\u05dc\u05d3\u05d5\u05d2\u05de\u05d4: /shop \u05de\u05db\u05d5\u05dc\u05ea \u05d0\u05d5\u05e1\u05d9\u05e3")
    except: pass
    await cb.answer()


@dp.callback_query(F.data.startswith("shop_no:"))
async def reject_payment(cb: types.CallbackQuery):
    if cb.from_user.id != ADMIN_USER_ID: return
    uid = int(cb.data.split(":")[1])
    await pay_db.reject_payment(uid, "osif_shop")
    await cb.message.edit_caption(caption=f"\u274c \u05e0\u05d3\u05d7\u05d4 {uid}")
    try:
        await bot.send_message(uid, "\u274c \u05ea\u05e9\u05dc\u05d5\u05dd \u05e0\u05d3\u05d7\u05d4. \u05e0\u05e1\u05d4 \u05e9\u05d5\u05d1.")
    except: pass
    await cb.answer()


# ═══════════════════════════════════
# MAIN
# ═══════════════════════════════════
async def main():
    await pay_db.init_schema()
    await init_tables()
    log.info("=" * 40)
    log.info("OsifShop - Inventory Management")
    log.info("=" * 40)
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
