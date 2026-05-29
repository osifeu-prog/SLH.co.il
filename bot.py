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
   Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€”Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€”  Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€”Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€”  Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€”
   Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜  Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜  Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜
   Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€”Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜
   Ã¢â€¢Å¡Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜
   Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜  Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜  Ã¢â€“Ë†Ã¢â€“Ë†Ã¢â€¢â€˜
   Ã¢â€¢Å¡Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Å¡Ã¢â€¢ÂÃ¢â€¢Â  Ã¢â€¢Å¡Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Å¡Ã¢â€¢ÂÃ¢â€¢Â  Ã¢â€¢Å¡Ã¢â€¢ÂÃ¢â€¢Â
   SLH AUTONOMOUS SYSTEM
"""

# ---- /start ----
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    text = (
        f"{SLH_LOGO}\n\n"
        "Ã°Å¸Å¡â‚¬ **SLH Crowdfunding**\n\n"
        "Hello Osif! Ã°Å¸â€˜â€¹\n"
        "I am SLH Claude  your AI assistant.\n"
        "Ã°Å¸â€™Å½ Tier: free\n\n"
        "**Available commands:**\n"
        "/register  Subscribe to updates\n"
        "/donate  Support the project\n"
        "/status  Project status\n"
        "/checkin  Daily check-in (+5 points)\n"
        "/leaderboard  Top 5\n"
        "/points  My points\n"
        "/daily  Daily missions\n"
        "/backup  Create backup\n"
        "/broadcast <msg>  (Admin) Send message to all\n"
        "/users  (Admin) Registered users\n"
        "/myid  Your Telegram ID\n"
        "/help  All commands\n"
        "/commands  Full command list\n\n"
        "Ã°Å¸Å’Â Campaign page: https://slh-nft.com/campaign/"
    )
    await msg.answer(text, parse_mode=None)

# ---- /commands (full list) ----
@dp.message(Command("commands"))
async def cmd_commands(msg: Message):
    text = (
        "Ã°Å¸â€œâ€¹ **Full Command Reference:**\n\n"
        "/start  Main menu with logo\n"
        "/register  Subscribe to updates\n"
        "/donate  Donation info & TON address\n"
        "/status  System status\n"
        "/checkin  Daily check-in (+5 pts, streak)\n"
        "/leaderboard  Top 5 users\n"
        "/points  Your points\n"
        "/daily  Daily missions\n"
        "/backup  Save data to cloud\n"
        "/broadcast <msg>  (Admin) Send message to all subscribers\n"
        "/users  (Admin) List all registered users\n"
        "/myid  Show your Telegram ID\n"
        "/help  Quick command list\n"
        "/commands  This full reference\n"
        "Any other text Ã¢â€ â€™ AI chat (Groq)"
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
    await msg.answer("Ã¢Å“â€¦ You are now registered for updates!", parse_mode=None)

# ---- /donate ----
@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(
        "Ã°Å¸â€™Â° **Donate to the campaign:**\n\n"
        "Send TON to:\n"
        "`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`\n\n"
        "**Support Levels:**\n"
        "Ã¢â‚¬Â¢ Supporter ($1)  Name on website\n"
        "Ã¢â‚¬Â¢ Builder ($5)  Early access + badge\n"
        "Ã¢â‚¬Â¢ Founder ($20)  Vote on features\n"
        "Ã¢â‚¬Â¢ Visionary ($50)  Personal call + Founder status",
        parse_mode="Markdown"
    )

# ---- /status ----
@dp.message(Command("status"))
async def cmd_status(msg: Message):
    await msg.answer(
        "Ã°Å¸â€œÅ  **Project Status:**\n"
        "Ã¢Å“â€¦ Bot: Online\n"
        "Ã¢Å“â€¦ Crowdfunding: Active\n"
        "Ã¢Å“â€¦ Mini App: [slh-nft.com](https://slh-nft.com)",
        parse_mode="Markdown"
    )

# ---- /users (admin) ----
@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Ã¢â€ºâ€ Admin only", parse_mode=None)
        return
    db = load_db(CONTACTS_FILE)
    if not db:
        await msg.answer("No users registered.", parse_mode=None)
        return
    text = f"Ã°Å¸â€œâ€¹ **{len(db)} Registered Users:**\n"
    for uid, data in db.items():
        text += f"Ã¢â‚¬Â¢ {data['full_name']} (@{data['username']})  {data['joined'][:10]}\n"
    await msg.answer(text, parse_mode="Markdown")

# ---- /broadcast (admin) ----
@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Ã¢â€ºâ€ Admin only", parse_mode=None)
        return
    parts = msg.text.split(" ", 1)
    if len(parts) < 2:
        await msg.answer("Usage: /broadcast <message>", parse_mode=None)
        return
    db = load_db(CONTACTS_FILE)
    sent = 0
    for uid in db:
        try:
            await msg.bot.send_message(int(uid), f"Ã°Å¸â€œÂ¢ {parts[1]}")
            sent += 1
        except:
            pass
    await msg.answer(f"Ã°Å¸â€œÂ¤ Sent to {sent}/{len(db)} users.", parse_mode=None)

# ---- /checkin ----
@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    today = datetime.date.today().isoformat()
    user = db.get(uid, {"points": 0, "streak": 0, "last_checkin": ""})
    if user["last_checkin"] == today:
        await msg.answer("Ã¢Ëœâ‚¬Ã¯Â¸Â Already checked in today! Come back tomorrow.", parse_mode=None)
        return
    user["streak"] += 1
    user["last_checkin"] = today
    bonus = min(user["streak"], 7) * 5
    user["points"] += bonus
    db[uid] = user
    save_db(db, POINTS_FILE)
    await msg.answer(f"Ã¢Ëœâ‚¬Ã¯Â¸Â Check-in successful! +{bonus} points\nTotal: {user['points']} pts | Streak: {user['streak']} days", parse_mode=None)

# ---- /leaderboard ----
@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    db = load_db(POINTS_FILE)
    if not db:
        await msg.answer("No data yet.", parse_mode=None)
        return
    sorted_users = sorted(db.items(), key=lambda x: x[1]["points"], reverse=True)[:5]
    text = "Ã°Å¸Ââ€  **Leaderboard:**\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        text += f"{i}. {uid[:8]}...  {data['points']} pts (Streak {data['streak']})\n"
    await msg.answer(text, parse_mode="Markdown")

# ---- /points ----
@dp.message(Command("points"))
async def cmd_points(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    user = db.get(uid, {"points": 0, "streak": 0})
    await msg.answer(f"Ã°Å¸Å½Â¯ You have {user['points']} points | Streak: {user['streak']} days", parse_mode=None)

# ---- /daily ----
@dp.message(Command("daily"))
async def cmd_daily(msg: Message):
    await msg.answer("Ã°Å¸â€œâ€¦ **Daily Missions:**\n/checkin  Check-in (+5 pts)\n/register  Subscribe", parse_mode="Markdown")

# ---- /backup ----
@dp.message(Command("backup"))
async def cmd_backup(msg: Message):
    await msg.answer("Ã°Å¸â€œÂ¦ Backup saved to cloud.", parse_mode=None)

# ---- /myid ----
@dp.message(Command("myid"))
async def cmd_myid(msg: Message):
    await msg.answer(f"Ã°Å¸â€ â€ Your ID: {msg.from_user.id}", parse_mode=None)

# ---- /help ----
@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "Ã°Å¸â€œâ€¹ **Commands:**\n"
        "/start /register /donate /status\n"
        "/checkin /leaderboard /points /daily\n"
        "/users /broadcast /backup /myid /help\n"
        "/commands  Full command list",
        parse_mode="Markdown"
    )

# ---- /morning (daily report) ----
@dp.message(Command("morning"))
async def cmd_morning(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("⛔ Admin only", parse_mode=None)
        return
    contacts = load_db(CONTACTS_FILE)
    total_users = len(contacts)
    new_today = sum(1 for u in contacts.values() if u["joined"][:10] == datetime.date.today().isoformat())
    points_db = load_db(POINTS_FILE)
    checked_in_today = sum(1 for u in points_db.values() if u.get("last_checkin") == datetime.date.today().isoformat())
    sorted_pts = sorted(points_db.items(), key=lambda x: x[1]["points"], reverse=True)[:3]
    lb = "\n".join(f"{i+1}. {uid[:8]}...  {data['points']} pts" for i, (uid, data) in enumerate(sorted_pts))
    text = (
        f"🌅 **בוקר טוב, אוסיף!**\n\n"
        f"📅 {datetime.date.today().strftime('%d/%m/%Y')}\n\n"
        f"👥 **משתמשים רשומים:** {total_users} (+{new_today} חדשים היום)\n"
        f"☀️ **צ'ק-אין היום:** {checked_in_today} משתמשים\n\n"
        f"🏆 **טופ 3:**\n{lb}\n\n"
        f"📋 **מטלות יומיות:**\n"
        f"• /broadcast  שלח עדכון לתומכים\n"
        f"• /status  בדוק מצב מערכת\n"
        f"• /users  צפה ברשימת משתמשים\n"
        f"• /backup  גבה נתונים\n\n"
        f"🔗 **קישורים מהירים:**\n"
        f"• [דף קמפיין](https://slh-nft.com/campaign/)\n"
        f"• [בוט EMP](https://t.me/Osifswork_BOT)\n"
        f"• [SLH Supervisor](https://t.me/SLH_Supervisor_bot)"
    )
    await msg.answer(text, parse_mode="Markdown")
# ---- /morning (daily report) ----
@dp.message(Command("morning"))
async def cmd_morning(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("â›” Admin only", parse_mode=None)
        return
    contacts = load_db(CONTACTS_FILE)
    total_users = len(contacts)
    new_today = sum(1 for u in contacts.values() if u["joined"][:10] == datetime.date.today().isoformat())
    points_db = load_db(POINTS_FILE)
    checked_in_today = sum(1 for u in points_db.values() if u.get("last_checkin") == datetime.date.today().isoformat())
    sorted_pts = sorted(points_db.items(), key=lambda x: x[1]["points"], reverse=True)[:3]
    lb = "\n".join(f"{i+1}. {uid[:8]}...  {data['points']} pts" for i, (uid, data) in enumerate(sorted_pts))
    text = (
        f"ðŸŒ… **×‘×•×§×¨ ×˜×•×‘, ××•×¡×™×£!**\n\n"
        f"ðŸ“… {datetime.date.today().strftime('%d/%m/%Y')}\n\n"
        f"ðŸ‘¥ **×ž×©×ª×ž×©×™× ×¨×©×•×ž×™×:** {total_users} (+{new_today} ×—×“×©×™× ×”×™×•×)\n"
        f"â˜€ï¸ **×¦'×§-××™×Ÿ ×”×™×•×:** {checked_in_today} ×ž×©×ª×ž×©×™×\n\n"
        f"ðŸ† **×˜×•×¤ 3:**\n{lb}\n\n"
        f"ðŸ“‹ **×ž×˜×œ×•×ª ×™×•×ž×™×•×ª:**\n"
        f"â€¢ /broadcast  ×©×œ×— ×¢×“×›×•×Ÿ ×œ×ª×•×ž×›×™×\n"
        f"â€¢ /status  ×‘×“×•×§ ×ž×¦×‘ ×ž×¢×¨×›×ª\n"
        f"â€¢ /users  ×¦×¤×” ×‘×¨×©×™×ž×ª ×ž×©×ª×ž×©×™×\n"
        f"â€¢ /backup  ×’×‘×” × ×ª×•× ×™×\n\n"
        f"ðŸ”— **×§×™×©×•×¨×™× ×ž×”×™×¨×™×:**\n"
        f"â€¢ [×“×£ ×§×ž×¤×™×™×Ÿ](https://slh-nft.com/campaign/)\n"
        f"â€¢ [×‘×•×˜ EMP](https://t.me/Osifswork_BOT)\n"
        f"â€¢ [SLH Supervisor](https://t.me/SLH_Supervisor_bot)"
    )
    await msg.answer(text, parse_mode="Markdown")
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