# -*- coding: utf-8 -*-
import os
import asyncio
import logging
import psycopg2
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command

load_dotenv(".env", override=True)

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "admin")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "224223270"))
PRICE_ILS = os.getenv("PRICE_ILS", "22.2221")
VIP_GROUP_LINK = (os.getenv("VIP_GROUP_LINK") or "").strip()
PAYMENT_NETWORK = (os.getenv("PAYMENT_NETWORK") or "TON").strip()
PAYMENT_WALLET_ADDRESS = (os.getenv("PAYMENT_WALLET_ADDRESS") or "").strip()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing in .env")

print("DEBUG: Using Token ->", repr(BOT_TOKEN))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
    )

def ensure_schema():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        username TEXT,
        paid BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payment_requests (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        note TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

def upsert_user(user_id: int, username: str | None):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO users (user_id, username, paid)
    VALUES (%s, %s, FALSE)
    ON CONFLICT (user_id) DO UPDATE
    SET username = EXCLUDED.username
    """, (user_id, username))
    conn.commit()
    cur.close()
    conn.close()

def is_paid(user_id: int) -> bool:
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT paid FROM users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return bool(row and row[0])

def has_pending_request(user_id: int) -> bool:
    conn = db()
    cur = conn.cursor()
    cur.execute("""
    SELECT 1
    FROM payment_requests
    WHERE user_id = %s AND status = 'pending'
    LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return bool(row)

def create_payment_request(user_id: int, note: str = "BUY"):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO payment_requests (user_id, status, note)
    VALUES (%s, 'pending', %s)
    """, (user_id, note))
    conn.commit()
    cur.close()
    conn.close()

def approve_user(user_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO users (user_id, username, paid)
    VALUES (%s, NULL, TRUE)
    ON CONFLICT (user_id) DO UPDATE
    SET paid = TRUE
    """, (user_id,))
    cur.execute("""
    UPDATE payment_requests
    SET status = 'approved'
    WHERE user_id = %s AND status = 'pending'
    """, (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def reject_user(user_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
    UPDATE payment_requests
    SET status = 'rejected'
    WHERE user_id = %s AND status = 'pending'
    """, (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_user_status(user_id: int):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    SELECT user_id, username, paid, created_at
    FROM users
    WHERE user_id = %s
    """, (user_id,))
    user_row = cur.fetchone()

    cur.execute("""
    SELECT id, status, note, created_at
    FROM payment_requests
    WHERE user_id = %s
    ORDER BY id DESC
    """, (user_id,))
    req_rows = cur.fetchall()

    cur.close()
    conn.close()
    return user_row, req_rows

WELCOME_UNPAID = f"""?-ן¿½??-?ן¿½?-ג€¢?-?ן¿½ ?-ן¿½??-ן¿½??-?ן¿½.

?-ן¿½??-ג€?-ג„¢ ?-?ן¿½?-?ן¿½?-ן¿½??-?ן¿½ ?-ג€™?-ג„¢?-?ן¿½?-ן¿½? ?-ן¿½??-?ן¿½?-?ן¿½?-ן¿½? ?-ג„¢?-?ן¿½ ?-?ן¿½?-ן¿½??-?ן¿½?-?ן¿½?-ג„¢?-ג€ ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€ ?-?ן¿½?-?ן¿½ {PRICE_ILS} ?-?ן¿½"?-ג€”.

?-?ן¿½?-?ן¿½?-ג€”?-?ן¿½ ?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€ ?-?ן¿½?-?ן¿½?-ג€” ?-?ן¿½?-ג„¢?-?ן¿½?-ג€¢?-ג€ ?-ן¿½??-?ן¿½?-?ן¿½ / hash / ?-?ן¿½?-?ן¿½?-ן¿½??-ן¿½??-?ן¿½?-?ן¿½.
?-?ן¿½?-?ן¿½ ?-?ן¿½?-ג€”?-?ן¿½?-ג„¢ ?-ן¿½??-ג€?-ג„¢?-?ן¿½?-?ן¿½ ?-?ן¿½?-ג€?-ן¿½??-ג„¢?-?? ?-ן¿½??-ג€™?-ג„¢?-?ן¿½?-ן¿½? ?-?ן¿½?-?ן¿½?-ג€¢?-?ן¿½?-?ן¿½.
"""

WELCOME_PAID = """?????? ??? ????.

????? ??? ????? ???.
"""

PAYMENT_TEXT = f"""?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½ ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€ ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€”?-ן¿½?.

?-?ן¿½?-ן¿½??-ג€¢?-ג€ ?-?ן¿½?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€:
{PRICE_ILS} ?-?ן¿½"?-ג€”

?-?ן¿½?-?ן¿½?-?ן¿½:
{PAYMENT_NETWORK}

?-ן¿½??-?ן¿½?-ג€¢?-ן¿½??-?ן¿½ ?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½?-?ן¿½ ?-?ן¿½?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€:
{PAYMENT_WALLET_ADDRESS}

?-ג€”?-?ן¿½?-ג€¢?-ן¿½?:
- ?-ן¿½??-ג€™?-ג„¢?-?ן¿½?-ן¿½? ?-?ן¿½?-?ן¿½?-ג€¢?-?ן¿½?-?ן¿½ ?-?ן¿½?-?ן¿½ ?-?ן¿½?-?ן¿½?-ג€”?-?ן¿½ ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€ ?-ן¿½??-?ן¿½?-ג€¢?-?ן¿½?-?ן¿½ ?-?ן¿½?-ן¿½??-?ן¿½?-ג€¢?-ן¿½??-?ן¿½ ?-ן¿½??-ג€“?-?ן¿½?-?ן¿½
- ?-?ן¿½?-?ן¿½?-ג€”?-?ן¿½ ?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€ ?-?ן¿½?-?ן¿½?-ג€” ?-?ן¿½?-ג„¢?-?ן¿½?-ג€¢?-ג€ ?-ן¿½??-?ן¿½?-?ן¿½ / hash / ?-?ן¿½?-?ן¿½?-ן¿½??-ן¿½??-?ן¿½?-?ן¿½
- ?-?ן¿½?-?ן¿½ ?-?ן¿½?-ג€”?-?ן¿½?-ג„¢ ?-ן¿½??-ג€?-ג„¢?-?ן¿½?-?ן¿½ ?-?ן¿½?-ג€?-ן¿½??-ג„¢?-?? ?-?ן¿½?-?ן¿½?-ן¿½??-?ן¿½ ?-ג€™?-ג„¢?-?ן¿½?-ן¿½?

?-?ן¿½?-?ן¿½?-ג€”?-?ן¿½ ?-?ן¿½?-?ן¿½?-ג„¢?-ג€”?-?ן¿½ ?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€ ?-?ן¿½?-?ן¿½?-?ן¿½?-?ן¿½ ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€” ?-?ן¿½?-ג€¢?-ן¿½? BUY ?-?ן¿½?-ג€¢ ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€” ?-?ן¿½?-?ן¿½ ?-ן¿½??-?ן¿½?-?ן¿½?-ן¿½??-ן¿½??-?ן¿½?-?ן¿½ ?-ן¿½??-?ן¿½?-?? ?-ן¿½??-?ן¿½'?-?ן¿½?-?ן¿½.
"""

PENDING_TEXT = """?-ן¿½??-ן¿½??-?ן¿½ ?-?ן¿½?-ג„¢?-ג„¢?-ן¿½??-?ן¿½ ?-?ן¿½?-?ן¿½?-?ן¿½?-?ן¿½ ?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½ ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€ ?-?ן¿½?-?ן¿½?-ג€¢?-ג€”?-ן¿½?.

?-ג„¢?-?ן¿½ ?-?ן¿½?-ן¿½??-?ן¿½?-?ן¿½?-ג„¢?-ג€ ?-?ן¿½?-?ן¿½ ?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€ ?-ן¿½??-?ן¿½?-ג„¢?-ג„¢?-ג€ ?-ג€¢?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€” ?-?ן¿½?-?ן¿½?-ן¿½??-ן¿½??-?ן¿½?-?ן¿½ ?-ן¿½??-?ן¿½?-?? ?-ן¿½??-?ן¿½'?-?ן¿½?-?ן¿½.
?-?ן¿½?-ג„¢?-?? ?-?ן¿½?-ג€¢?-?ן¿½?-?ן¿½ ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€” ?-ן¿½??-?ן¿½?-?ן¿½?-ן¿½? ?-?ן¿½?-ג€¢?-?ן¿½?-?ן¿½?-?ן¿½ ?-ן¿½??-?ן¿½?-ג€™?-?ן¿½.
"""

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    upsert_user(message.from_user.id, message.from_user.username)
    if is_paid(message.from_user.id):
        text = WELCOME_PAID
        if VIP_GROUP_LINK:
            text += f"\n\n?-?ן¿½?-ג„¢?-?ן¿½?-?ן¿½ ?-ן¿½??-ג€™?-ג„¢?-?ן¿½?-ן¿½? ?-?ן¿½?-?ן¿½?-?ן¿½:\n{VIP_GROUP_LINK}"
        await message.answer(text)
    else:
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text=f"?-?ן¿½?-ן¿½??-ג€¢?-?ן¿½ ?-ג€™?-ג„¢?-?ן¿½?-ן¿½? ?-ן¿½?-{PRICE_ILS} ?-?ן¿½\"?-ג€”", callback_data="buy_now")]
            ]
        )
        await message.answer(WELCOME_UNPAID, reply_markup=kb)

@dp.callback_query(F.data == "buy_now")
async def buy_now(callback: types.CallbackQuery):
    upsert_user(callback.from_user.id, callback.from_user.username)

    if is_paid(callback.from_user.id):
        text = "?-ן¿½??-ג€™?-ג„¢?-?ן¿½?-ן¿½? ?-?ן¿½?-?ן¿½?-?ן¿½ ?-ן¿½??-ן¿½??-?ן¿½ ?-?ן¿½?-?ן¿½?-ג„¢?-?ן¿½?-ן¿½?."
        if VIP_GROUP_LINK:
            text += f"\n\n?-?ן¿½?-ג„¢?-?ן¿½?-?ן¿½ ?-ן¿½??-ג€™?-ג„¢?-?ן¿½?-ן¿½? ?-?ן¿½?-?ן¿½?-?ן¿½:\n{VIP_GROUP_LINK}"
        await callback.message.answer(text)
        await callback.answer()
        return

    if has_pending_request(callback.from_user.id):
        await callback.message.answer(PENDING_TEXT)
        await callback.answer()
        return

    create_payment_request(callback.from_user.id, "BUY")
    await callback.message.answer(PAYMENT_TEXT)
    await bot.send_message(
        ADMIN_ID,
        f"Payment request\nuser_id={callback.from_user.id}\nusername=@{callback.from_user.username or 'unknown'}\nnote=BUY\nnetwork={PAYMENT_NETWORK}\nwallet={PAYMENT_WALLET_ADDRESS}"
    )
    await callback.answer("?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½ ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€ ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€”?-ן¿½?")

@dp.message(F.text == "BUY")
async def buy_text(message: types.Message):
    upsert_user(message.from_user.id, message.from_user.username)

    if is_paid(message.from_user.id):
        text = "?-ן¿½??-ג€™?-ג„¢?-?ן¿½?-ן¿½? ?-?ן¿½?-?ן¿½?-?ן¿½ ?-ן¿½??-ן¿½??-?ן¿½ ?-?ן¿½?-?ן¿½?-ג„¢?-?ן¿½?-ן¿½?."
        if VIP_GROUP_LINK:
            text += f"\n\n?-?ן¿½?-ג„¢?-?ן¿½?-?ן¿½ ?-ן¿½??-ג€™?-ג„¢?-?ן¿½?-ן¿½? ?-?ן¿½?-?ן¿½?-?ן¿½:\n{VIP_GROUP_LINK}"
        await message.answer(text)
        return

    if has_pending_request(message.from_user.id):
        await message.answer(PENDING_TEXT)
        return

    create_payment_request(message.from_user.id, "BUY")
    await message.answer(PAYMENT_TEXT)
    await bot.send_message(
        ADMIN_ID,
        f"Payment request\nuser_id={message.from_user.id}\nusername=@{message.from_user.username or 'unknown'}\nnote=BUY\nnetwork={PAYMENT_NETWORK}\nwallet={PAYMENT_WALLET_ADDRESS}"
    )

@dp.message(Command("approve"))
async def approve_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("?-?ן¿½?-ג„¢?-?? ?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½?-ן¿½?.")
        return

    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("?-?ן¿½?-ג„¢?-ן¿½??-ג€¢?-?ן¿½ ?-?ן¿½?-ן¿½??-ג€¢?-??: /approve <user_id>")
        return

    target_id = int(parts[1])
    approve_user(target_id)
    await message.answer(f"?-ן¿½??-ן¿½??-?ן¿½?-?ן¿½?-ן¿½??-?ן¿½ {target_id} ?-?ן¿½?-ג€¢?-?ן¿½?-?ן¿½")

    user_text = "?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€ ?-?ן¿½?-?ן¿½?-?ן¿½ ?-?ן¿½?-ג€¢?-?ן¿½?-?ן¿½.\n\n?-ן¿½??-ג€™?-ג„¢?-?ן¿½?-ן¿½? ?-?ן¿½?-?ן¿½?-?ן¿½ ?-?ן¿½?-?ן¿½?-ג„¢?-?ן¿½?-ן¿½? ?-ן¿½??-?ן¿½?-?ן¿½."
    if VIP_GROUP_LINK:
        user_text += f"\n\n?-?ן¿½?-ג„¢?-?ן¿½?-?ן¿½ ?-ן¿½??-ג€™?-ג„¢?-?ן¿½?-ן¿½? ?-?ן¿½?-?ן¿½?-?ן¿½:\n{VIP_GROUP_LINK}"

    try:
        await bot.send_message(target_id, user_text)
    except Exception as e:
        await message.answer(f"?-?ן¿½?-?ן¿½ ?-?ן¿½?-ג„¢?-?ן¿½?-?? ?-ן¿½??-ג„¢?-ן¿½? ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€” ?-ן¿½??-ג€¢?-ג€?-?ן¿½?-ן¿½? ?-?ן¿½?-ן¿½??-?ן¿½?-?ן¿½?-ן¿½??-?ן¿½: {e}")

@dp.message(Command("reject"))
async def reject_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("?-?ן¿½?-ג„¢?-?? ?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½?-ן¿½?.")
        return

    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("?-?ן¿½?-ג„¢?-ן¿½??-ג€¢?-?ן¿½ ?-?ן¿½?-ן¿½??-ג€¢?-??: /reject <user_id>")
        return

    target_id = int(parts[1])
    reject_user(target_id)
    await message.answer(f"?-ן¿½??-ן¿½??-?ן¿½?-?ן¿½?-ן¿½??-?ן¿½ {target_id} ?-?ן¿½?-ג€?-ג€”?-ן¿½?")

    try:
        await bot.send_message(target_id, "?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½ ?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€ ?-?ן¿½?-ג€?-ג€”?-?ן¿½?-ן¿½?. ?-?ן¿½?-?ן¿½?-?ן¿½?-?ן¿½ ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€” BUY ?-ן¿½??-ג€”?-ג€?-?ן¿½ ?-ג€¢?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€” ?-ן¿½??-?ן¿½?-?ן¿½?-ן¿½? ?-ג€”?-ג€?-?ן¿½?-ן¿½?.")
    except Exception as e:
        await message.answer(f"?-?ן¿½?-?ן¿½ ?-?ן¿½?-ג„¢?-?ן¿½?-?? ?-ן¿½??-ג„¢?-ן¿½? ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€” ?-ן¿½??-ג€¢?-ג€?-?ן¿½?-ן¿½? ?-?ן¿½?-ן¿½??-?ן¿½?-?ן¿½?-ן¿½??-?ן¿½: {e}")

@dp.message(Command("status"))
async def status_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("?-?ן¿½?-ג„¢?-?? ?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½?-ן¿½?.")
        return

    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("?-?ן¿½?-ג„¢?-ן¿½??-ג€¢?-?ן¿½ ?-?ן¿½?-ן¿½??-ג€¢?-??: /status <user_id>")
        return

    target_id = int(parts[1])
    user_row, req_rows = get_user_status(target_id)

    lines = [f"STATUS user_id={target_id}"]
    lines.append(f"paid={is_paid(target_id)}")
    lines.append(f"pending={has_pending_request(target_id)}")

    if user_row:
        lines.append(f"user={user_row}")
    else:
        lines.append("user=NOT_FOUND")

    if req_rows:
        lines.append("payment_requests:")
        for row in req_rows[:10]:
            lines.append(str(row))
    else:
        lines.append("payment_requests=NONE")

    await message.answer("\n".join(lines))

@dp.message()
async def catch_all(message: types.Message):
    upsert_user(message.from_user.id, message.from_user.username)

    if message.from_user.id != ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"Inbox\nuser_id={message.from_user.id}\nusername=@{message.from_user.username or 'unknown'}\ntext={message.text or ''}"
            )
        except Exception:
            pass

    if is_paid(message.from_user.id):
        await message.answer("?-ן¿½??-ג€™?-ג„¢?-?ן¿½?-ן¿½? ?-?ן¿½?-?ן¿½?-?ן¿½ ?-?ן¿½?-?ן¿½?-ג„¢?-?ן¿½?-ן¿½?.")
    elif has_pending_request(message.from_user.id):
        await message.answer(PENDING_TEXT)
    else:
        await message.answer("?-ן¿½??-ג€?-ג„¢ ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€” ?-ן¿½??-?ן¿½?-?ן¿½?-?ן¿½ ?-?ן¿½?-?ן¿½?-?ן¿½?-ג€¢?-ג€ ?-?ן¿½?-?ן¿½?-ג€” BUY.")

async def main():
    ensure_schema()
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



