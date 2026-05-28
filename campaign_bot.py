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
        "ðŸš€ **SLH Crowdfunding**\n\n"
        "×× ×—× ×• ×‘×•× ×™× AI ××•×˜×•× ×•×ž×™  ×•×¦×¨×™×›×™× ××•×ª×š!\n\n"
        "ðŸ’Ž **×¤×§×•×“×•×ª:**\n"
        "/register  Register for updates\n"
        "/donate  Donate & Invest\n"
        "/status  Project Status\n"
        "/referral  ×”×¤× ×” ×—×‘×¨×™× ×•×§×‘×œ ×‘×•× ×•×¡\n"
        "/leaderboard  Leaderboard",
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
    await msg.answer("âœ… × ×¨×©×ž×ª ×‘×”×¦×œ×—×”! ×ª×§×‘×œ/×™ ×¢×“×›×•× ×™× ×¢×œ ×”×§×ž×¤×™×™×Ÿ.")

# ---- /donate ----
@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(
        "ðŸ’° **×ª×¨×ž×• ×œ×§×ž×¤×™×™×Ÿ:**\n\n"
        "×©×œ×—×• TON ×œ×›×ª×•×‘×ª:\n"
        "`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`\n\n"
        "ðŸ“Š **×¨×ž×•×ª ×ª×ž×™×›×”:**\n"
        "â€¢ Supporter ($1)  ×©× ×‘××ª×¨\n"
        "â€¢ Builder ($5)  Early access + ×‘××“×’'\n"
        "â€¢ Founder ($20)  ×”×¦×‘×¢×” ×¢×œ ×¤×™×¦'×¨×™×\n"
        "â€¢ Visionary ($50)  ×©×™×—×” ××™×©×™×ª + ×¡×˜×˜×•×¡ ×ž×™×™×¡×“",
        parse_mode="Markdown"
    )

# ---- /status ----
@dp.message(Command("status"))
async def cmd_status(msg: Message):
    await msg.answer("ðŸ“Š **Project Status:**\n"
                     "âœ… Bot: Online\nâœ… Crowdfunding: Active\n"
                     "âœ… Mini App: [slh-nft.com](https://slh-nft.com)")

# ---- /admin (×¨×©×™×ž×ª ×ž×©×ª×ž×©×™×) ----
@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("â›” ××“×ž×™×Ÿ ×‘×œ×‘×“")
        return
    db = load_db()
    text = f"ðŸ“‹ **{len(db)} ×ž×©×ª×ž×©×™× ×¨×©×•×ž×™×:**\n"
    for uid, data in db.items():
        text += f"â€¢ {data.get('full_name','?')} (@{data.get('username','?')})\n"
    await msg.answer(text)

# ---- /broadcast (×©×™×“×•×¨) ----
@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("â›” ××“×ž×™×Ÿ ×‘×œ×‘×“")
        return
    parts = msg.text.split(" ", 1)
    if len(parts) < 2:
        await msg.answer("×©×™×ž×•×©: /broadcast <×”×•×“×¢×”>")
        return
    db = load_db()
    sent = 0
    for uid in db:
        try:
            await msg.bot.send_message(int(uid), f"ðŸ“¢ {parts[1]}")
            sent += 1
        except: pass
    await msg.answer(f"ðŸ“¤ × ×©×œ×— ×œâ€‘{sent}/{len(db)} ×ž×©×ª×ž×©×™×.")

# ---- Main ----
async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


