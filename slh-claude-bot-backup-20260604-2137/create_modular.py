import os

BASE = r"D:\slh-website\slh-claude-bot\modular_bot"
for d in ["core", "handlers", "features", "services", "keyboards"]:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

files = {}

files["core\\config.py"] = '''import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "224223270").split(",")]
TON_WALLET = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
'''

files["core\\database.py"] = '''import asyncpg
from .config import DATABASE_URL

pool = None

async def create_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY, telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT, full_name TEXT, points INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 100, tier TEXT DEFAULT 'free',
                referral_code TEXT, referred_by BIGINT,
                created_at TIMESTAMP DEFAULT NOW(), last_seen TIMESTAMP DEFAULT NOW(),
                last_energy_update TIMESTAMP DEFAULT NOW(), is_admin BOOLEAN DEFAULT FALSE
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY, user_id BIGINT, description TEXT,
                done BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS identities (
                id SERIAL PRIMARY KEY, user_id BIGINT, full_name TEXT,
                doc_type TEXT, verified BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY, name TEXT, phone TEXT,
                added_by BIGINT, created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY, customer_id INTEGER, content TEXT,
                created_by BIGINT, created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY, name TEXT, description TEXT,
                price INTEGER, stock INTEGER DEFAULT 0, deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id SERIAL PRIMARY KEY, user_id BIGINT, product_id INTEGER,
                points_spent INTEGER, created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY, from_user BIGINT, to_user BIGINT,
                amount INTEGER, type TEXT, created_at TIMESTAMP DEFAULT NOW()
            );
        """)
    print("All tables & migration OK")

async def ensure_user(uid: int, username: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (telegram_id, username, referral_code) "
            "VALUES ($1, $2, $3) ON CONFLICT (telegram_id) "
            "DO UPDATE SET username = $2, last_seen = NOW()",
            uid, username, f"SLH{uid}"
        )
'''

files["handlers\\marketplace.py"] = '''from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core import database
from core.config import ADMIN_IDS

router = Router(name="marketplace")

class ProductForm(StatesGroup):
    waiting_name = State()
    waiting_desc = State()
    waiting_price = State()
    waiting_stock = State()

@router.message(Command("store"))
async def cmd_store(msg: types.Message):
    async with database.pool.acquire() as conn:
        products = await conn.fetch(
            "SELECT id, name, price FROM products WHERE stock > 0 ORDER BY id"
        )
        if not products:
            return await msg.answer("\U0001f6d2 \u05d4\u05d7\u05e0\u05d5\u05ea \u05e8\u05d9\u05e7\u05d4 \u05db\u05e8\u05d2\u05e2.")
        kb = [
            [
                types.InlineKeyboardButton(
                    text=f"{p['name']} - {p['price']} \u05e0\u05e7'",
                    callback_data=f"buy_{p['id']}"
                )
            ]
            for p in products
        ]
        kb.append([types.InlineKeyboardButton(text="\U0001f519 \u05d7\u05d6\u05e8\u05d4", callback_data="main_menu")])
        await msg.answer(
            "\U0001f6d2 <b>\u05d7\u05e0\u05d5\u05ea SLH</b>\n\u05d1\u05d7\u05e8 \u05de\u05d5\u05e6\u05e8 \u05dc\u05e8\u05db\u05d9\u05e9\u05d4:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
        )

@router.message(Command("add_product"))
async def cmd_add_product(msg: types.Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("\u26d4 \u05d2\u05d9\u05e9\u05ea \u05de\u05e0\u05d4\u05dc \u05d1\u05dc\u05d1\u05d3.")
    await state.set_state(ProductForm.waiting_name)
    await msg.answer("\u05e9\u05dd \u05d4\u05de\u05d5\u05e6\u05e8:")

@router.message(ProductForm.waiting_name)
async def product_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await state.set_state(ProductForm.waiting_desc)
    await msg.answer("\u05ea\u05d9\u05d0\u05d5\u05e8 \u05d4\u05de\u05d5\u05e6\u05e8:")

@router.message(ProductForm.waiting_desc)
async def product_desc(msg: types.Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await state.set_state(ProductForm.waiting_price)
    await msg.answer("\u05de\u05d7\u05d9\u05e8 (\u05d1\u05e0\u05e7\u05d5\u05d3\u05d5\u05ea):")

@router.message(ProductForm.waiting_price)
async def product_price(msg: types.Message, state: FSMContext):
    try:
        price = int(msg.text)
    except ValueError:
        return await msg.answer("\u05de\u05d7\u05d9\u05e8 \u05d7\u05d9\u05d9\u05d1 \u05dc\u05d4\u05d9\u05d5\u05ea \u05de\u05e1\u05e4\u05e8. \u05e0\u05e1\u05d4 \u05e9\u05d5\u05d1.")
    await state.update_data(price=price)
    await state.set_state(ProductForm.waiting_stock)
    await msg.answer("\u05db\u05de\u05d5\u05ea \u05d1\u05de\u05dc\u05d0\u05d9:")

@router.message(ProductForm.waiting_stock)
async def product_stock(msg: types.Message, state: FSMContext):
    try:
        stock = int(msg.text)
    except ValueError:
        return await msg.answer("\u05db\u05de\u05d5\u05ea \u05d7\u05d9\u05d9\u05d1\u05ea \u05dc\u05d4\u05d9\u05d5\u05ea \u05de\u05e1\u05e4\u05e8. \u05e0\u05e1\u05d4 \u05e9\u05d5\u05d1.")
    data = await state.get_data()
    async with database.pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO products (name, description, price, stock) "
            "VALUES ($1, $2, $3, $4)",
            data['name'], data['description'], data['price'], stock
        )
    await state.clear()
    await msg.answer(f"\u2705 \u05de\u05d5\u05e6\u05e8 '{data['name']}' \u05e0\u05d5\u05e1\u05e3 \u05d1\u05d4\u05e6\u05dc\u05d7\u05d4!")

@router.message(Command("products"))
async def cmd_products(msg: types.Message):
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, price, stock FROM products ORDER BY id"
        )
        if not rows:
            return await msg.answer("\U0001f4e6 \u05d0\u05d9\u05df \u05de\u05d5\u05e6\u05e8\u05d9\u05dd \u05d1\u05de\u05e2\u05e8\u05db\u05ea.")
        text = "\n".join(
            f"{r['id']}: {r['name']} - {r['price']} \u05e0\u05e7' ({r['stock']} \u05d1\u05de\u05dc\u05d0\u05d9)"
            for r in rows
        )
        await msg.answer(f"\U0001f4e6 <b>\u05de\u05d5\u05e6\u05e8\u05d9\u05dd</b>:\n{text}")

@router.message(Command("buy"))
async def cmd_buy(msg: types.Message):
    parts = msg.text.split()
    if len(parts) < 2:
        return await msg.answer("\u05e9\u05d9\u05de\u05d5\u05e9: /buy [\u05de\u05d6\u05d4\u05d4 \u05de\u05d5\u05e6\u05e8]")
    try:
        product_id = int(parts[1])
    except ValueError:
        return await msg.answer("\u05de\u05d6\u05d4\u05d4 \u05de\u05d5\u05e6\u05e8 \u05d7\u05d9\u05d9\u05d1 \u05dc\u05d4\u05d9\u05d5\u05ea \u05de\u05e1\u05e4\u05e8.")
    uid = msg.from_user.id
    async with database.pool.acquire() as conn:
        product = await conn.fetchrow(
            "SELECT id, name, price, stock FROM products WHERE id = $1", product_id
        )
        if not product or product['stock'] <= 0:
            return await msg.answer("\u05d4\u05de\u05d5\u05e6\u05e8 \u05dc\u05d0 \u05d6\u05de\u05d9\u05df.")
        user = await conn.fetchrow(
            "SELECT points FROM users WHERE telegram_id = $1", uid
        )
        if not user or user['points'] < product['price']:
            return await msg.answer("\u05d0\u05d9\u05df \u05de\u05e1\u05e4\u05d9\u05e7 \u05e0\u05e7\u05d5\u05d3\u05d5\u05ea.")
        await conn.execute(
            "UPDATE users SET points = points - $1 WHERE telegram_id = $2",
            product['price'], uid
        )
        await conn.execute(
            "UPDATE products SET stock = stock - 1 WHERE id = $1", product_id
        )
        await conn.execute(
            "INSERT INTO purchases (user_id, product_id, points_spent) "
            "VALUES ($1, $2, $3)",
            uid, product_id, product['price']
        )
        new_points = user['points'] - product['price']
        await msg.answer(
            f"\U0001f389 \u05e8\u05db\u05e9\u05ea {product['name']} \u05d1-{product['price']} \u05e0\u05e7\u05d5\u05d3\u05d5\u05ea!\n\u05d9\u05ea\u05e8\u05d4: {new_points}"
        )

@router.callback_query(F.data.startswith("buy_"))
async def buy_callback(call: types.CallbackQuery):
    product_id = int(call.data.split("_")[1])
    uid = call.from_user.id
    async with database.pool.acquire() as conn:
        product = await conn.fetchrow(
            "SELECT id, name, price, stock FROM products WHERE id = $1", product_id
        )
        if not product or product['stock'] <= 0:
            await call.answer("\u05d4\u05de\u05d5\u05e6\u05e8 \u05dc\u05d0 \u05d6\u05de\u05d9\u05df.", show_alert=True)
            return
        user = await conn.fetchrow(
            "SELECT points FROM users WHERE telegram_id = $1", uid
        )
        if not user or user['points'] < product['price']:
            await call.answer("\u05d0\u05d9\u05df \u05de\u05e1\u05e4\u05d9\u05e7 \u05e0\u05e7\u05d5\u05d3\u05d5\u05ea.", show_alert=True)
            return
        await conn.execute(
            "UPDATE users SET points = points - $1 WHERE telegram_id = $2",
            product['price'], uid
        )
        await conn.execute(
            "UPDATE products SET stock = stock - 1 WHERE id = $1", product_id
        )
        await conn.execute(
            "INSERT INTO purchases (user_id, product_id, points_spent) "
            "VALUES ($1, $2, $3)",
            uid, product_id, product['price']
        )
        new_points = user['points'] - product['price']
        await call.message.answer(
            f"\U0001f389 \u05e8\u05db\u05e9\u05ea {product['name']} \u05d1-{product['price']} \u05e0\u05e7\u05d5\u05d3\u05d5\u05ea!\n\u05d9\u05ea\u05e8\u05d4: {new_points}"
        )
    await call.answer()
'''

files["features\\system.py"] = '''from aiogram import Router, types
from aiogram.filters import Command

router = Router(name="system")

@router.message(Command("status"))
async def cmd_status(msg: types.Message):
    await msg.answer("\U0001f4ca System status: OK")
'''

files["main.py"] = '''import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from core.config import TOKEN
from core.database import create_pool
from handlers.marketplace import router as marketplace_router
from features.system import router as system_router

async def main():
    await create_pool()
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(marketplace_router)
    dp.include_router(system_router)
    await bot.delete_webhook(drop_pending_updates=True)
    print("\U0001f680 SLH Modular Bot  Marketplace + System")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
'''

for path, content in files.items():
    full = os.path.join(BASE, path)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created {path}")
