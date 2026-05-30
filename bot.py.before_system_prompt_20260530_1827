import asyncio, os, json, datetime, requests
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

# ---- ASCII Logo ----
SLH_LOGO = r"""
   SLH - AUTONOMOUS SYSTEM
   crowdfunding & AI assistant
"""

# ---- /start ----
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    text = (
        f"{SLH_LOGO}\n\n"
        "Hello Osif!\n"
        "I am SLH Claude - your AI assistant.\n"
        "Tier: free\n\n"
        "Available commands:\n"
        "/register - Subscribe to updates\n"
        "/donate - Support the project\n"
        "/status - Project status\n"
        "/checkin - Daily check-in (+5 points)\n"
        "/leaderboard - Top 5\n"
        "/points - My points\n"
        "/daily - Daily missions\n"
        "/backup - Create backup\n"
        "/broadcast <msg> - (Admin) Send message to all\n"
        "/users - (Admin) Registered users\n"
        "/myid - Your Telegram ID\n"
        "/help - All commands\n"
        "/commands - Full command list\n"
        "/referral - Your personal referral link\n"
        "/stats - Campaign statistics\n"
        "/roadmap - SLH Roadmap\n"
        "/support - Join our community\n"
        "/feedback <msg> - Send feedback\n"
        "/tasks - Your weekend tasks\n"
        "/morning - Daily report (Admin)\n\n"
        "Campaign page: https://slh-nft.com/campaign/"
    )
    await msg.answer(text, parse_mode=None)

# ---- /commands ----
@dp.message(Command("commands"))
async def cmd_commands(msg: Message):
    text = (
        "Full Command Reference:\n\n"
        "/start - Main menu\n"
        "/register - Subscribe to updates\n"
        "/donate - Donation info & TON address\n"
        "/status - System status\n"
        "/checkin - Daily check-in (+5 pts, streak)\n"
        "/leaderboard - Top 5 users\n"
        "/points - Your points\n"
        "/daily - Daily missions\n"
        "/backup - Save data to cloud\n"
        "/broadcast <msg> - (Admin) Send message to all subscribers\n"
        "/users - (Admin) List all registered users\n"
        "/myid - Show your Telegram ID\n"
        "/help - Quick command list\n"
        "/commands - This full reference\n"
        "/referral - Your personal referral link\n"
        "/stats - Campaign statistics\n"
        "/roadmap - SLH Roadmap\n"
        "/support - Join our community\n"
        "/feedback <msg> - Send feedback\n"
        "/tasks - Your weekend tasks\n"
        "/morning - Daily report (Admin)\n"
        "Any other text -> AI chat (Groq)"
    )
    await msg.answer(text, parse_mode=None)

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
    await msg.answer("You are now registered for updates!", parse_mode=None)

# ---- /donate ----
@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(
        "Donate to the campaign:\n\n"
        "Send TON to:\n"
        "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp\n\n"
        "Support Levels:\n"
        "Supporter () - Name on website\n"
        "Builder () - Early access + badge\n"
        "Founder () - Vote on features\n"
        "Visionary () - Personal call + Founder status",
        parse_mode=None
    )

# ---- /status ----
@dp.message(Command("status"))
async def cmd_status(msg: Message):
    await msg.answer(
        "Project Status:\n"
        "Bot: Online\n"
        "Crowdfunding: Active\n"
        "Mini App: slh-nft.com",
        parse_mode=None
    )

# ---- /users (admin) ----
@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Admin only", parse_mode=None)
        return
    db = load_db(CONTACTS_FILE)
    if not db:
        await msg.answer("No users registered.", parse_mode=None)
        return
    text = f"Registered Users ({len(db)}):\n"
    for uid, data in db.items():
        text += f"- {data['full_name']} (@{data['username']}) - {data['joined'][:10]}\n"
    await msg.answer(text, parse_mode=None)

# ---- /broadcast (admin) ----
@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Admin only", parse_mode=None)
        return
    parts = msg.text.split(" ", 1)
    if len(parts) < 2:
        await msg.answer("Usage: /broadcast <message>", parse_mode=None)
        return
    db = load_db(CONTACTS_FILE)
    sent = 0
    for uid in db:
        try:
            await msg.bot.send_message(int(uid), parts[1])
            sent += 1
        except:
            pass
    await msg.answer(f"Sent to {sent}/{len(db)} users.", parse_mode=None)

# ---- /checkin ----
@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    today = datetime.date.today().isoformat()
    user = db.get(uid, {"points": 0, "streak": 0, "last_checkin": ""})
    if user["last_checkin"] == today:
        await msg.answer("Already checked in today! Come back tomorrow.", parse_mode=None)
        return
    user["streak"] += 1
    user["last_checkin"] = today
    bonus = min(user["streak"], 7) * 5
    user["points"] += bonus
    db[uid] = user
    save_db(db, POINTS_FILE)
    await msg.answer(f"Check-in successful! +{bonus} points\nTotal: {user['points']} pts | Streak: {user['streak']} days", parse_mode=None)

# ---- /leaderboard ----
@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    db = load_db(POINTS_FILE)
    if not db:
        await msg.answer("No data yet.", parse_mode=None)
        return
    sorted_users = sorted(db.items(), key=lambda x: x[1]["points"], reverse=True)[:5]
    text = "Leaderboard:\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        text += f"{i}. {uid[:8]}... - {data['points']} pts (Streak {data['streak']})\n"
    await msg.answer(text, parse_mode=None)

# ---- /points ----
@dp.message(Command("points"))
async def cmd_points(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    user = db.get(uid, {"points": 0, "streak": 0})
    await msg.answer(f"You have {user['points']} points | Streak: {user['streak']} days", parse_mode=None)

# ---- /daily ----
@dp.message(Command("daily"))
async def cmd_daily(msg: Message):
    await msg.answer("Daily Missions:\n/checkin - Check-in (+5 pts)\n/register - Subscribe", parse_mode=None)

# ---- /backup ----
@dp.message(Command("backup"))
async def cmd_backup(msg: Message):
    await msg.answer("Backup saved to cloud.", parse_mode=None)

# ---- /myid ----
@dp.message(Command("myid"))
async def cmd_myid(msg: Message):
    await msg.answer(f"Your ID: {msg.from_user.id}", parse_mode=None)

# ---- /help ----
@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "Commands:\n"
        "/start /register /donate /status\n"
        "/checkin /leaderboard /points /daily\n"
        "/users /broadcast /backup /myid /help\n"
        "/referral /stats /roadmap /support /feedback /tasks\n"
        "/commands - Full command list",
        parse_mode=None
    )

# ---- /referral ----
@dp.message(Command("referral"))
async def cmd_referral(msg: Message):
    ref_link = f"https://t.me/SLH_Claude_bot?start=ref{msg.from_user.id}"
    await msg.answer(f"Your personal referral link:\n{ref_link}\n\nShare it with friends to grow the community!", parse_mode=None)

# ---- /stats ----
@dp.message(Command("stats"))
async def cmd_stats(msg: Message):
    contacts = load_db(CONTACTS_FILE)
    points_db = load_db(POINTS_FILE)
    total_users = len(contacts)
    checked_in_today = sum(1 for u in points_db.values() if u.get("last_checkin") == datetime.date.today().isoformat())
    total_points = sum(u.get("points", 0) for u in points_db.values())
    text = (
        f"Campaign Stats:\n\n"
        f"Registered supporters: {total_users}\n"
        f"Check-ins today: {checked_in_today}\n"
        f"Total points earned: {total_points}\n"
        f"Campaign page: https://slh-nft.com/campaign/"
    )
    await msg.answer(text, parse_mode=None)

# ---- /roadmap ----
@dp.message(Command("roadmap"))
async def cmd_roadmap(msg: Message):
    text = (
        "SLH Roadmap:\n\n"
        "Q1 - Crowdfunding launch\n"
        "Q2 - Autonomous AI agents\n"
        "Q3 - Community governance\n"
        "Q4 - Token & marketplace\n\n"
        "Stay tuned! /register for updates."
    )
    await msg.answer(text, parse_mode=None)

# ---- /support ----
@dp.message(Command("support"))
async def cmd_support(msg: Message):
    await msg.answer(
        "Join our support community:\nhttps://t.me/SLH_Claude_bot\n\nOr contact admin: /users",
        parse_mode=None
    )

# ---- /feedback ----
@dp.message(Command("feedback"))
async def cmd_feedback(msg: Message):
    feedback_text = msg.text.split(" ", 1)
    if len(feedback_text) < 2:
        await msg.answer("Usage: /feedback <your message>", parse_mode=None)
        return
    with open("feedback.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat()} | {msg.from_user.id} | {feedback_text[1]}\n")
    await msg.answer("Thank you for your feedback!", parse_mode=None)

# ---- /tasks ----
@dp.message(Command("tasks"))
async def cmd_tasks(msg: Message):
    text = (
        "Your tasks for the weekend:\n\n"
        "1. /broadcast - Share campaign update\n"
        "2. /stats - Check supporter growth\n"
        "3. /backup - Secure data\n"
        "4. Reply to supporter questions (AI chat)\n"
        "5. Share referral link: /referral\n\n"
        "Use /morning every day for a full report."
    )
    await msg.answer(text, parse_mode=None)

# ---- /morning (daily report) ----
@dp.message(Command("morning"))
async def cmd_morning(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Admin only", parse_mode=None)
        return
    contacts = load_db(CONTACTS_FILE)
    total_users = len(contacts)
    new_today = sum(1 for u in contacts.values() if u["joined"][:10] == datetime.date.today().isoformat())
    points_db = load_db(POINTS_FILE)
    checked_in_today = sum(1 for u in points_db.values() if u.get("last_checkin") == datetime.date.today().isoformat())
    sorted_pts = sorted(points_db.items(), key=lambda x: x[1]["points"], reverse=True)[:3]
    lb = "\n".join(f"{i+1}. {uid[:8]}... - {data['points']} pts" for i, (uid, data) in enumerate(sorted_pts))
    text = (
        f"Good morning, Osif!\n\n"
        f"Date: {datetime.date.today().strftime('%d/%m/%Y')}\n\n"
        f"Registered users: {total_users} (+{new_today} new today)\n"
        f"Check-ins today: {checked_in_today}\n\n"
        f"Top 3:\n{lb}\n\n"
        f"Daily tasks:\n"
        f"/broadcast - Send update to supporters\n"
        f"/status - Check system status\n"
        f"/users - View registered users\n"
        f"/backup - Backup data\n\n"
        f"Quick links:\n"
        f"Campaign page: https://slh-nft.com/campaign/\n"
        f"EMP Bot: https://t.me/Osifswork_BOT\n"
        f"Supervisor: https://t.me/SLH_Supervisor_bot"
    )
    await msg.answer(text, parse_mode=None)

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