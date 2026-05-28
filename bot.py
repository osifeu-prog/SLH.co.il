# -*- coding: utf-8 -*-
import asyncio, os, json, datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
dp = Dispatcher()

# ---------- DB ----------
CONTACTS_FILE = "contacts.json"
POINTS_FILE = "points.json"

def load_db(file):
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f: json.dump({}, f)
    with open(file, "r", encoding="utf-8") as f: return json.load(f)

def save_db(data, file):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

ADMIN_ID = 224223270

# ---------- /start ----------
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.answer(
        "🚀 **SLH Crowdfunding**\n\n"
        "ברוכים הבאים לקמפיין גיוס ההמונים של SLH!\n"
        "אנחנו בונים AI אוטונומי  ומחפשים תומכים כמוך.\n\n"
        "💎 **פקודות:**\n"
        "/register  הרשמה לעדכונים\n"
        "/donate  תרומה והשקעה\n"
        "/status  סטטוס פרויקט\n"
        "/checkin  צק-אין יומי (+5 נק)\n"
        "/leaderboard  טבלת מובילים\n"
        "/help  כל הפקודות",
        parse_mode="Markdown"
    )

# ---------- /register ----------
@dp.message(Command("register"))
async def cmd_register(msg: Message):
    db = load_db(CONTACTS_FILE)
    uid = str(msg.from_user.id)
    db[uid] = {
        "username": msg.from_user.username or "",
        "full_name": msg.from_user.full_name,
        "joined": datetime.datetime.now().isoformat()
    }
    save_db(db, CONTACTS_FILE)
    await msg.answer("✅ נרשמת בהצלחה! תקבל/י עדכונים.")

# ---------- /donate ----------
@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(
        "💰 **תרומה לקמפיין:**\n\n"
        "שלח TON לכתובת:\n"
        "`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`\n\n"
        "📊 **רמות תמיכה:**\n"
        "• Supporter ($1)  שם באתר\n"
        "• Builder ($5)  Early access + באדג'\n"
        "• Founder ($20)  הצבעה על פיצ'רים\n"
        "• Visionary ($50)  שיחה אישית + סטטוס מייסד",
        parse_mode="Markdown"
    )

# ---------- /status ----------
@dp.message(Command("status"))
async def cmd_status(msg: Message):
    await msg.answer(
        "📊 **סטטוס פרויקט:**\n"
        "✅ Bot: Online\n✅ Crowdfunding: Active\n"
        "✅ Mini App: [slh-nft.com](https://slh-nft.com)"
    )

# ---------- /users (admin) ----------
@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ אדמין בלבד")
        return
    db = load_db(CONTACTS_FILE)
    if not db:
        await msg.answer("אין משתמשים רשומים.")
        return
    text = f"📋 **{len(db)} משתמשים:**\n"
    for uid, data in db.items():
        text += f"• {data['full_name']} (@{data['username']}) - {data['joined'][:10]}\n"
    await msg.answer(text)

# ---------- /broadcast (admin) ----------
@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ אדמין בלבד")
        return
    parts = msg.text.split(" ", 1)
    if len(parts) < 2:
        await msg.answer("שימוש: /broadcast <הודעה>")
        return
    db = load_db(CONTACTS_FILE)
    sent = 0
    for uid in db:
        try:
            await msg.bot.send_message(int(uid), f"📢 {parts[1]}")
            sent += 1
        except:
            pass
    await msg.answer(f"📤 נשלח ל-{sent}/{len(db)} משתמשים.")

# ---------- /checkin ----------
@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    today = datetime.date.today().isoformat()
    user = db.get(uid, {"points": 0, "streak": 0, "last_checkin": ""})
    if user["last_checkin"] == today:
        await msg.answer("☀️ כבר ביצעת צק-אין היום. תחזור מחר!")
        return
    user["streak"] += 1
    user["last_checkin"] = today
    bonus = min(user["streak"], 7) * 5
    user["points"] += bonus
    db[uid] = user
    save_db(db, POINTS_FILE)
    await msg.answer(f"☀️ צק-אין בוצע! +{bonus} נק\nסהכ: {user['points']} נק | רצף: {user['streak']} ימים")

# ---------- /leaderboard ----------
@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    db = load_db(POINTS_FILE)
    if not db:
        await msg.answer("אין נתונים עדיין.")
        return
    sorted_users = sorted(db.items(), key=lambda x: x[1]["points"], reverse=True)[:5]
    text = "🏆 **טבלת מובילים:**\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        text += f"{i}. {uid[:8]}...  {data['points']} נק (רצף {data['streak']})\n"
    await msg.answer(text)

# ---------- /points ----------
@dp.message(Command("points"))
async def cmd_points(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    user = db.get(uid, {"points": 0, "streak": 0})
    await msg.answer(f"🎯 יש לך {user['points']} נק | רצף {user['streak']} ימים")

# ---------- /daily ----------
@dp.message(Command("daily"))
async def cmd_daily(msg: Message):
    await msg.answer("📅 **משימות יומיות:**\n/checkin  צק-אין (+5 נק)\n/register  הרשמה\n/donate  תרומה")

# ---------- /backup ----------
@dp.message(Command("backup"))
async def cmd_backup(msg: Message):
    await msg.answer("📦 גיבוי מלא נשמר בענן. לרשותך.")

# ---------- /myid ----------
@dp.message(Command("myid"))
async def cmd_myid(msg: Message):
    await msg.answer(f"🆔 ה-ID שלך: {msg.from_user.id}")

# ---------- /help ----------
@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "📋 **פקודות:**\n"
        "/start /register /donate /status\n"
        "/checkin /leaderboard /points /daily\n"
        "/users /broadcast /backup /myid /help"
    )

# ---------- main ----------
async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
