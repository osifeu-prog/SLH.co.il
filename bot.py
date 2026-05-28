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

ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "").split(",") if x]

# ---------- /start ----------
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.answer(
        "ðŸš€ **SLH Crowdfunding**\n\n"
        "×‘×¨×•×›×™× ×”×‘××™× ×œ×§×ž×¤×™×™×Ÿ ×’×™×•×¡ ×”×”×ž×•× ×™× ×©×œ SLH!\n"
        "×× ×—× ×• ×‘×•× ×™× AI ××•×˜×•× ×•×ž×™  ×•×ž×—×¤×©×™× ×ª×•×ž×›×™× ×›×ž×•×š.\n\n"
        "ðŸ’Ž **×¤×§×•×“×•×ª:**\n"
        "/register  ×”×¨×©×ž×” ×œ×¢×“×›×•× ×™×\n"
        "/donate  ×ª×¨×•×ž×” ×•×”×©×§×¢×”\n"
        "/status  ×¡×˜×˜×•×¡ ×¤×¨×•×™×§×˜\n"
        "/checkin  ×¦×§-××™×Ÿ ×™×•×ž×™ (+5 × ×§)\n"
        "/leaderboard  ×˜×‘×œ×ª ×ž×•×‘×™×œ×™×\n"
        "/help  ×›×œ ×”×¤×§×•×“×•×ª",
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
    await msg.answer("âœ… × ×¨×©×ž×ª ×‘×”×¦×œ×—×”! ×ª×§×‘×œ/×™ ×¢×“×›×•× ×™×.")

# ---------- /donate ----------
@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(
        "ðŸ’° **×ª×¨×•×ž×” ×œ×§×ž×¤×™×™×Ÿ:**\n\n"
        "×©×œ×— TON ×œ×›×ª×•×‘×ª:\n"
        "`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`\n\n"
        "ðŸ“Š **×¨×ž×•×ª ×ª×ž×™×›×”:**\n"
        "â€¢ Supporter ($1)  ×©× ×‘××ª×¨\n"
        "â€¢ Builder ($5)  Early access + ×‘××“×’'\n"
        "â€¢ Founder ($20)  ×”×¦×‘×¢×” ×¢×œ ×¤×™×¦'×¨×™×\n"
        "â€¢ Visionary ($50)  ×©×™×—×” ××™×©×™×ª + ×¡×˜×˜×•×¡ ×ž×™×™×¡×“",
        parse_mode="Markdown"
    )

# ---------- /status ----------
@dp.message(Command("status"))
async def cmd_status(msg: Message):
    await msg.answer(
        "ðŸ“Š **×¡×˜×˜×•×¡ ×¤×¨×•×™×§×˜:**\n"
        "âœ… Bot: Online\nâœ… Crowdfunding: Active\n"
        "âœ… Mini App: [slh-nft.com](https://slh-nft.com)"
    )

# ---------- /users (admin) ----------
@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("â›” ××“×ž×™×Ÿ ×‘×œ×‘×“")
        return
    db = load_db(CONTACTS_FILE)
    if not db:
        await msg.answer("××™×Ÿ ×ž×©×ª×ž×©×™× ×¨×©×•×ž×™×.")
        return
    text = f"ðŸ“‹ **{len(db)} ×ž×©×ª×ž×©×™×:**\n"
    for uid, data in db.items():
        text += f"â€¢ {data['full_name']} (@{data['username']}) - {data['joined'][:10]}\n"
    await msg.answer(text)

# ---------- /broadcast (admin) ----------
@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("â›” ××“×ž×™×Ÿ ×‘×œ×‘×“")
        return
    parts = msg.text.split(" ", 1)
    if len(parts) < 2:
        await msg.answer("×©×™×ž×•×©: /broadcast <×”×•×“×¢×”>")
        return
    db = load_db(CONTACTS_FILE)
    sent = 0
    for uid in db:
        try:
            await msg.bot.send_message(int(uid), f"ðŸ“¢ {parts[1]}")
            sent += 1
        except:
            pass
    await msg.answer(f"ðŸ“¤ × ×©×œ×— ×œ-{sent}/{len(db)} ×ž×©×ª×ž×©×™×.")

# ---------- /checkin ----------
@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    today = datetime.date.today().isoformat()
    user = db.get(uid, {"points": 0, "streak": 0, "last_checkin": ""})
    if user["last_checkin"] == today:
        await msg.answer("â˜€ï¸ ×›×‘×¨ ×‘×™×¦×¢×ª ×¦×§-××™×Ÿ ×”×™×•×. ×ª×—×–×•×¨ ×ž×—×¨!")
        return
    user["streak"] += 1
    user["last_checkin"] = today
    bonus = min(user["streak"], 7) * 5
    user["points"] += bonus
    db[uid] = user
    save_db(db, POINTS_FILE)
    await msg.answer(f"â˜€ï¸ ×¦×§-××™×Ÿ ×‘×•×¦×¢! +{bonus} × ×§\n×¡×”×›: {user['points']} × ×§ | ×¨×¦×£: {user['streak']} ×™×ž×™×")

# ---------- /leaderboard ----------
@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    db = load_db(POINTS_FILE)
    if not db:
        await msg.answer("××™×Ÿ × ×ª×•× ×™× ×¢×“×™×™×Ÿ.")
        return
    sorted_users = sorted(db.items(), key=lambda x: x[1]["points"], reverse=True)[:5]
    text = "ðŸ† **×˜×‘×œ×ª ×ž×•×‘×™×œ×™×:**\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        text += f"{i}. {uid[:8]}...  {data['points']} × ×§ (×¨×¦×£ {data['streak']})\n"
    await msg.answer(text)

# ---------- /points ----------
@dp.message(Command("points"))
async def cmd_points(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    user = db.get(uid, {"points": 0, "streak": 0})
    await msg.answer(f"ðŸŽ¯ ×™×© ×œ×š {user['points']} × ×§ | ×¨×¦×£ {user['streak']} ×™×ž×™×")

# ---------- /daily ----------
@dp.message(Command("daily"))
async def cmd_daily(msg: Message):
    await msg.answer("ðŸ“… **×ž×©×™×ž×•×ª ×™×•×ž×™×•×ª:**\n/checkin  ×¦×§-××™×Ÿ (+5 × ×§)\n/register  ×”×¨×©×ž×”\n/donate  ×ª×¨×•×ž×”")

# ---------- /backup ----------
@dp.message(Command("backup"))
async def cmd_backup(msg: Message):
    await msg.answer("ðŸ“¦ ×’×™×‘×•×™ ×ž×œ× × ×©×ž×¨ ×‘×¢× ×Ÿ. ×œ×¨×©×•×ª×š.")

# ---------- /myid ----------
@dp.message(Command("myid"))
async def cmd_myid(msg: Message):
    await msg.answer(f"ðŸ†” ×”-ID ×©×œ×š: {msg.from_user.id}")

# ---------- /help ----------
@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "ðŸ“‹ **×¤×§×•×“×•×ª:**\n"
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
