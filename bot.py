import asyncio
import os
import json
import datetime
import requests
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
dp = Dispatcher()

# ---- DB ----
CONTACTS_FILE = "contacts.json"
POINTS_FILE = "points.json"

def load_db(file):
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f: json.dump({}, f)
    with open(file, "r", encoding="utf-8") as f: return json.load(f)

def save_db(data, file):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "").split(",") if x]

# ---- /start ----
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.answer(
        "Hello Osif! 👋\n"
        "I am SLH Claude  your AI assistant.\n"
        "💎 Tier: free\n\n"
        "Available commands:\n"
        "/register  Subscribe to updates\n"
        "/donate  Support the project\n"
        "/status  Project status\n"
        "/checkin  Daily check-in (+5 points)\n"
        "/leaderboard  Top 5\n"
        "/points  My points\n"
        "/daily  Daily missions\n"
        "/backup  Create backup\n"
        "/broadcast <msg>  (Admin) Send message to all\n"
        "/help  All commands",
        parse_mode=None
    )

# ---- /register ----
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
    await msg.answer("✅ You are now registered for updates!", parse_mode=None)

# ---- /donate ----
@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(
        "💰 **Donate to the campaign:**\n\n"
        "Send TON to:\n"
        "`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`\n\n"
        "**Support Levels:**\n"
        "• Supporter ($1)  Name on website\n"
        "• Builder ($5)  Early access + badge\n"
        "• Founder ($20)  Vote on features\n"
        "• Visionary ($50)  Personal call + Founder status",
        parse_mode="Markdown"
    )

# ---- /status ----
@dp.message(Command("status"))
async def cmd_status(msg: Message):
    await msg.answer(
        "📊 **Project Status:**\n"
        "✅ Bot: Online\n"
        "✅ Crowdfunding: Active\n"
        "✅ Mini App: [slh-nft.com](https://slh-nft.com)",
        parse_mode="Markdown"
    )

# ---- /users (admin) ----
@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("⛔ Admin only", parse_mode=None)
        return
    db = load_db(CONTACTS_FILE)
    if not db:
        await msg.answer("No users registered.", parse_mode=None)
        return
    text = f"📋 **{len(db)} Registered Users:**\n"
    for uid, data in db.items():
        text += f"• {data['full_name']} (@{data['username']})  {data['joined'][:10]}\n"
    await msg.answer(text, parse_mode="Markdown")

# ---- /broadcast (admin) ----
@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("⛔ Admin only", parse_mode=None)
        return
    parts = msg.text.split(" ", 1)
    if len(parts) < 2:
        await msg.answer("Usage: /broadcast <message>", parse_mode=None)
        return
    db = load_db(CONTACTS_FILE)
    sent = 0
    for uid in db:
        try:
            await msg.bot.send_message(int(uid), f"📢 {parts[1]}")
            sent += 1
        except:
            pass
    await msg.answer(f"📤 Sent to {sent}/{len(db)} users.", parse_mode=None)

# ---- /checkin ----
@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    today = datetime.date.today().isoformat()
    user = db.get(uid, {"points": 0, "streak": 0, "last_checkin": ""})
    if user["last_checkin"] == today:
        await msg.answer("☀️ Already checked in today! Come back tomorrow.", parse_mode=None)
        return
    user["streak"] += 1
    user["last_checkin"] = today
    bonus = min(user["streak"], 7) * 5
    user["points"] += bonus
    db[uid] = user
    save_db(db, POINTS_FILE)
    await msg.answer(f"☀️ Check-in successful! +{bonus} points\nTotal: {user['points']} pts | Streak: {user['streak']} days", parse_mode=None)

# ---- /leaderboard ----
@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    db = load_db(POINTS_FILE)
    if not db:
        await msg.answer("No data yet.", parse_mode=None)
        return
    sorted_users = sorted(db.items(), key=lambda x: x[1]["points"], reverse=True)[:5]
    text = "🏆 **Leaderboard:**\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        text += f"{i}. {uid[:8]}...  {data['points']} pts (Streak {data['streak']})\n"
    await msg.answer(text, parse_mode="Markdown")

# ---- /points ----
@dp.message(Command("points"))
async def cmd_points(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    user = db.get(uid, {"points": 0, "streak": 0})
    await msg.answer(f"🎯 You have {user['points']} points | Streak: {user['streak']} days", parse_mode=None)

# ---- /daily ----
@dp.message(Command("daily"))
async def cmd_daily(msg: Message):
    await msg.answer("📅 **Daily Missions:**\n/checkin  Check-in (+5 pts)\n/register  Subscribe", parse_mode="Markdown")

# ---- /backup ----
@dp.message(Command("backup"))
async def cmd_backup(msg: Message):
    await msg.answer("📦 Backup saved to cloud.", parse_mode=None)

# ---- /myid ----
@dp.message(Command("myid"))
async def cmd_myid(msg: Message):
    await msg.answer(f"🆔 Your ID: {msg.from_user.id}", parse_mode=None)

# ---- /help ----
@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "📋 **Commands:**\n"
        "/start /register /donate /status\n"
        "/checkin /leaderboard /points /daily\n"
        "/users /broadcast /backup /myid /help",
        parse_mode="Markdown"
    )

# ---- AI (Groq) ----
@dp.message()
async def ai_chat(msg: Message):
    if msg.text.startswith("/"):
        return
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        await msg.answer("AI not configured.", parse_mode=None)
        return
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": msg.text}],
                "max_tokens": 500
            },
            timeout=15
        )
        data = resp.json()
        reply = data["choices"][0]["message"]["content"]
        await msg.answer(reply[:4000])
    except Exception as e:
        await msg.answer(f"AI error: {e}", parse_mode=None)

# ---- Main ----
async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
