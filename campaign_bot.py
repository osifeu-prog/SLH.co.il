# campaign_bot.py  SLH Crowdfunding Bot
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

# ---- DB Simples (JSON) ----
DB_FILE = "campaign_users.json"
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f: json.dump({}, f)
    with open(DB_FILE, "r") as f: return json.load(f)
def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=2)

ADMIN_ID = 224223270

# ---- /start ----
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    user_id = str(msg.from_user.id)
    db = load_db()
    if user_id not in db:
        db[user_id] = {"joined": datetime.datetime.now().isoformat()}
        save_db(db)
    await msg.answer(
        "🚀 **SLH Crowdfunding**\n\n"
        "אנחנו בונים AI אוטונומי  וצריכים אותך!\n\n"
        "💎 **פקודות:**\n"
        "/register  הרשמה לעדכונים\n"
        "/donate  תרומה והשקעה\n"
        "/status  סטטוס פרויקט\n"
        "/referral  הפנה חברים וקבל בונוס\n"
        "/leaderboard  טבלת מובילים",
        parse_mode="Markdown"
    )

# ---- /register ----
@dp.message(Command("register"))
async def cmd_register(msg: Message):
    user_id = str(msg.from_user.id)
    db = load_db()
    db[user_id] = {
        "username": msg.from_user.username or "no_username",
        "full_name": msg.from_user.full_name,
        "joined": datetime.datetime.now().isoformat()
    }
    save_db(db)
    await msg.answer("✅ נרשמת בהצלחה! תקבל/י עדכונים על הקמפיין.")

# ---- /donate ----
@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(
        "💰 **תרמו לקמפיין:**\n\n"
        "שלחו TON לכתובת:\n"
        "`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`\n\n"
        "📊 **רמות תמיכה:**\n"
        "• Supporter ($1)  שם באתר\n"
        "• Builder ($5)  Early access + באדג'\n"
        "• Founder ($20)  הצבעה על פיצ'רים\n"
        "• Visionary ($50)  שיחה אישית + סטטוס מייסד",
        parse_mode="Markdown"
    )

# ---- /status ----
@dp.message(Command("status"))
async def cmd_status(msg: Message):
    await msg.answer("📊 **סטטוס פרויקט:**\n"
                     "✅ Bot: Online\n✅ Crowdfunding: Active\n"
                     "✅ Mini App: [slh-nft.com](https://slh-nft.com)")

# ---- /admin (רשימת משתמשים) ----
@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ אדמין בלבד")
        return
    db = load_db()
    text = f"📋 **{len(db)} משתמשים רשומים:**\n"
    for uid, data in db.items():
        text += f"• {data.get('full_name','?')} (@{data.get('username','?')})\n"
    await msg.answer(text)

# ---- /broadcast (שידור) ----
@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ אדמין בלבד")
        return
    parts = msg.text.split(" ", 1)
    if len(parts) < 2:
        await msg.answer("שימוש: /broadcast <הודעה>")
        return
    db = load_db()
    sent = 0
    for uid in db:
        try:
            await msg.bot.send_message(int(uid), f"📢 {parts[1]}")
            sent += 1
        except: pass
    await msg.answer(f"📤 נשלח ל‑{sent}/{len(db)} משתמשים.")

# ---- Main ----
async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
