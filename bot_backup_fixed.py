import asyncio, os, datetime, psycopg2
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Fix: split by comma OR space, handle empty values
admin_str = os.getenv("ADMIN_ID", "0")
ADMIN_IDS = []
for part in admin_str.replace(",", " ").split():
    if part.strip().isdigit():
        ADMIN_IDS.append(int(part.strip()))

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

@dp.message(Command("start"))
async def cmd_start(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="?? Status", callback_data="cmd_status")],
        [InlineKeyboardButton(text="?? Points", callback_data="cmd_points")],
        [InlineKeyboardButton(text="? Check-in", callback_data="cmd_checkin")],
        [InlineKeyboardButton(text="?? Admin", callback_data="cmd_admin")],
    ])
    await msg.answer("?? Welcome to SLH! Use buttons below.", reply_markup=kb)

@dp.message(Command("admin"))
async def cmd_admin(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("?? Admin only")
        return
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin = CURRENT_DATE")
    checked = cur.fetchone()[0]
    conn.close()
    await msg.answer(f"?? Admin Panel\n\nTotal users: {total}\nChecked in today: {checked}")

@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    user_id = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username or "user"
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (telegram_id, username) VALUES (%s,%s) ON CONFLICT (telegram_id) DO NOTHING", (user_id, name))
    cur.execute("SELECT points, streak, last_checkin FROM users WHERE telegram_id=%s", (user_id,))
    row = cur.fetchone()
    today = datetime.date.today()
    if row and row[2] == today:
        await msg.answer("? Already checked in today!")
        conn.close()
        return
    points = row[0] if row else 0
    streak = (row[1] + 1) if row else 1
    bonus = min(streak, 7) * 5
    new_points = points + bonus
    cur.execute("UPDATE users SET points=%s, streak=%s, last_checkin=%s WHERE telegram_id=%s", (new_points, streak, today, user_id))
    conn.commit()
    conn.close()
    await msg.answer(f"? Check-in! +{bonus} points | Total: {new_points} | Streak: {streak}")

@dp.message(Command("points"))
async def cmd_points(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT points FROM users WHERE telegram_id=%s", (msg.from_user.id,))
    row = cur.fetchone()
    conn.close()
    if row:
        await msg.answer(f"?? You have {row[0]} points")
    else:
        await msg.answer("Not registered. Use /start")

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 5")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await msg.answer("No data yet")
        return
    text = "?? Leaderboard\n" + "\n".join(f"{i+1}. {r[0]} - {r[1]} pts" for i, r in enumerate(rows))
    await msg.answer(text)

@dp.message(Command("status"))
async def cmd_status(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin = CURRENT_DATE")
    checked = cur.fetchone()[0]
    conn.close()
    await msg.answer(f"?? SLH Status\nUsers: {total}\nChecked in today: {checked}")

@dp.message(Command("doctor"))
async def cmd_doctor(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Admin only")
        return
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1")
        db_ok = "?"
    except:
        db_ok = "?"
    conn.close()
    await msg.answer(f"?? Doctor\nDatabase: {db_ok}\nBot online: ?")

@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    if data == "cmd_status":
        await cmd_status(callback.message)
    elif data == "cmd_points":
        await cmd_points(callback.message)
    elif data == "cmd_checkin":
        await cmd_checkin(callback.message)
    elif data == "cmd_admin":
        await cmd_admin(callback.message)
    else:
        await callback.message.answer(f"Unknown action: {data}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
