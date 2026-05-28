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
        "ÃƒÂ°Ã…Â¸Ã…Â¡Ã¢â€šÂ¬ **SLH Crowdfunding**\n\n"
        "Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã‚Â¨Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã¢â‚¬ÂºÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã¢â‚¬ÂÃƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã‚ÂÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã…â€œÃƒâ€”Ã‚Â§Ãƒâ€”Ã…Â¾Ãƒâ€”Ã‚Â¤Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¸ Ãƒâ€”Ã¢â‚¬â„¢Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â¡ Ãƒâ€”Ã¢â‚¬ÂÃƒâ€”Ã¢â‚¬ÂÃƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚Â©Ãƒâ€”Ã…â€œ SLH!\n"
        "Ãƒâ€”Ã‚ÂÃƒâ€”Ã‚Â Ãƒâ€”Ã¢â‚¬â€Ãƒâ€”Ã‚Â Ãƒâ€”Ã¢â‚¬Â¢ Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â AI Ãƒâ€”Ã‚ÂÃƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‹Å“Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â€žÂ¢  Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬â€Ãƒâ€”Ã‚Â¤Ãƒâ€”Ã‚Â©Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚ÂªÃƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬ÂºÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã¢â‚¬ÂºÃƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã…Â¡.\n\n"
        "ÃƒÂ°Ã…Â¸Ã¢â‚¬â„¢Ã…Â½ **Ãƒâ€”Ã‚Â¤Ãƒâ€”Ã‚Â§Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã¢â‚¬Å“Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Âª:**\n"
        "/register  Ãƒâ€”Ã¢â‚¬ÂÃƒâ€”Ã‚Â¨Ãƒâ€”Ã‚Â©Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬Â Ãƒâ€”Ã…â€œÃƒâ€”Ã‚Â¢Ãƒâ€”Ã¢â‚¬Å“Ãƒâ€”Ã¢â‚¬ÂºÃƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â\n"
        "/donate  Ãƒâ€”Ã‚ÂªÃƒâ€”Ã‚Â¨Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬Â Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã¢â‚¬ÂÃƒâ€”Ã‚Â©Ãƒâ€”Ã‚Â§Ãƒâ€”Ã‚Â¢Ãƒâ€”Ã¢â‚¬Â\n"
        "/status  Ãƒâ€”Ã‚Â¡Ãƒâ€”Ã‹Å“Ãƒâ€”Ã‹Å“Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â¡ Ãƒâ€”Ã‚Â¤Ãƒâ€”Ã‚Â¨Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â§Ãƒâ€”Ã‹Å“\n"
        "/checkin  Ãƒâ€”Ã‚Â¦Ãƒâ€”Ã‚Â§-Ãƒâ€”Ã‚ÂÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¸ Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â€žÂ¢ (+5 Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚Â§)\n"
        "/leaderboard  Ãƒâ€”Ã‹Å“Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã…â€œÃƒâ€”Ã‚Âª Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…â€œÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â\n"
        "/help  Ãƒâ€”Ã¢â‚¬ÂºÃƒâ€”Ã…â€œ Ãƒâ€”Ã¢â‚¬ÂÃƒâ€”Ã‚Â¤Ãƒâ€”Ã‚Â§Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã¢â‚¬Å“Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Âª",
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
    await msg.answer("ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚Â¨Ãƒâ€”Ã‚Â©Ãƒâ€”Ã…Â¾Ãƒâ€”Ã‚Âª Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã¢â‚¬ÂÃƒâ€”Ã‚Â¦Ãƒâ€”Ã…â€œÃƒâ€”Ã¢â‚¬â€Ãƒâ€”Ã¢â‚¬Â! Ãƒâ€”Ã‚ÂªÃƒâ€”Ã‚Â§Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã…â€œ/Ãƒâ€”Ã¢â€žÂ¢ Ãƒâ€”Ã‚Â¢Ãƒâ€”Ã¢â‚¬Å“Ãƒâ€”Ã¢â‚¬ÂºÃƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â.")

# ---------- /donate ----------
@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(
        "ÃƒÂ°Ã…Â¸Ã¢â‚¬â„¢Ã‚Â° **Ãƒâ€”Ã‚ÂªÃƒâ€”Ã‚Â¨Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬Â Ãƒâ€”Ã…â€œÃƒâ€”Ã‚Â§Ãƒâ€”Ã…Â¾Ãƒâ€”Ã‚Â¤Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¸:**\n\n"
        "Ãƒâ€”Ã‚Â©Ãƒâ€”Ã…â€œÃƒâ€”Ã¢â‚¬â€ TON Ãƒâ€”Ã…â€œÃƒâ€”Ã¢â‚¬ÂºÃƒâ€”Ã‚ÂªÃƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã‚Âª:\n"
        "`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`\n\n"
        "ÃƒÂ°Ã…Â¸Ã¢â‚¬Å“Ã…Â  **Ãƒâ€”Ã‚Â¨Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Âª Ãƒâ€”Ã‚ÂªÃƒâ€”Ã…Â¾Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã¢â‚¬ÂºÃƒâ€”Ã¢â‚¬Â:**\n"
        "ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢ Supporter ($1)  Ãƒâ€”Ã‚Â©Ãƒâ€”Ã‚Â Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã‚ÂÃƒâ€”Ã‚ÂªÃƒâ€”Ã‚Â¨\n"
        "ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢ Builder ($5)  Early access + Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã‚ÂÃƒâ€”Ã¢â‚¬Å“Ãƒâ€”Ã¢â‚¬â„¢'\n"
        "ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢ Founder ($20)  Ãƒâ€”Ã¢â‚¬ÂÃƒâ€”Ã‚Â¦Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã‚Â¢Ãƒâ€”Ã¢â‚¬Â Ãƒâ€”Ã‚Â¢Ãƒâ€”Ã…â€œ Ãƒâ€”Ã‚Â¤Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â¦'Ãƒâ€”Ã‚Â¨Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â\n"
        "ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢ Visionary ($50)  Ãƒâ€”Ã‚Â©Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã¢â‚¬â€Ãƒâ€”Ã¢â‚¬Â Ãƒâ€”Ã‚ÂÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â©Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Âª + Ãƒâ€”Ã‚Â¡Ãƒâ€”Ã‹Å“Ãƒâ€”Ã‹Å“Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â¡ Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â¡Ãƒâ€”Ã¢â‚¬Å“",
        parse_mode="Markdown"
    )

# ---------- /status ----------
@dp.message(Command("status"))
async def cmd_status(msg: Message):
    await msg.answer(
        "ÃƒÂ°Ã…Â¸Ã¢â‚¬Å“Ã…Â  **Ãƒâ€”Ã‚Â¡Ãƒâ€”Ã‹Å“Ãƒâ€”Ã‹Å“Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â¡ Ãƒâ€”Ã‚Â¤Ãƒâ€”Ã‚Â¨Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â§Ãƒâ€”Ã‹Å“:**\n"
        "ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ Bot: Online\nÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ Crowdfunding: Active\n"
        "ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ Mini App: [slh-nft.com](https://slh-nft.com)"
    )

# ---------- /users (admin) ----------
@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("ÃƒÂ¢Ã¢â‚¬ÂºÃ¢â‚¬Â Ãƒâ€”Ã‚ÂÃƒâ€”Ã¢â‚¬Å“Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¸ Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã…â€œÃƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã¢â‚¬Å“")
        return
    db = load_db(CONTACTS_FILE)
    if not db:
        await msg.answer("Ãƒâ€”Ã‚ÂÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¸ Ãƒâ€”Ã…Â¾Ãƒâ€”Ã‚Â©Ãƒâ€”Ã‚ÂªÃƒâ€”Ã…Â¾Ãƒâ€”Ã‚Â©Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚Â¨Ãƒâ€”Ã‚Â©Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â.")
        return
    text = f"ÃƒÂ°Ã…Â¸Ã¢â‚¬Å“Ã¢â‚¬Â¹ **{len(db)} Ãƒâ€”Ã…Â¾Ãƒâ€”Ã‚Â©Ãƒâ€”Ã‚ÂªÃƒâ€”Ã…Â¾Ãƒâ€”Ã‚Â©Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â:**\n"
    for uid, data in db.items():
        text += f"ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢ {data['full_name']} (@{data['username']}) - {data['joined'][:10]}\n"
    await msg.answer(text)

# ---------- /broadcast (admin) ----------
@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("ÃƒÂ¢Ã¢â‚¬ÂºÃ¢â‚¬Â Ãƒâ€”Ã‚ÂÃƒâ€”Ã¢â‚¬Å“Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¸ Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã…â€œÃƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã¢â‚¬Å“")
        return
    parts = msg.text.split(" ", 1)
    if len(parts) < 2:
        await msg.answer("Ãƒâ€”Ã‚Â©Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â©: /broadcast <Ãƒâ€”Ã¢â‚¬ÂÃƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã¢â‚¬Å“Ãƒâ€”Ã‚Â¢Ãƒâ€”Ã¢â‚¬Â>")
        return
    db = load_db(CONTACTS_FILE)
    sent = 0
    for uid in db:
        try:
            await msg.bot.send_message(int(uid), f"ÃƒÂ°Ã…Â¸Ã¢â‚¬Å“Ã‚Â¢ {parts[1]}")
            sent += 1
        except:
            pass
    await msg.answer(f"ÃƒÂ°Ã…Â¸Ã¢â‚¬Å“Ã‚Â¤ Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚Â©Ãƒâ€”Ã…â€œÃƒâ€”Ã¢â‚¬â€ Ãƒâ€”Ã…â€œ-{sent}/{len(db)} Ãƒâ€”Ã…Â¾Ãƒâ€”Ã‚Â©Ãƒâ€”Ã‚ÂªÃƒâ€”Ã…Â¾Ãƒâ€”Ã‚Â©Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â.")

# ---------- /checkin ----------
@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    today = datetime.date.today().isoformat()
    user = db.get(uid, {"points": 0, "streak": 0, "last_checkin": ""})
    if user["last_checkin"] == today:
        await msg.answer("ÃƒÂ¢Ã‹Å“Ã¢â€šÂ¬ÃƒÂ¯Ã‚Â¸Ã‚Â Ãƒâ€”Ã¢â‚¬ÂºÃƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã‚Â¨ Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â¦Ãƒâ€”Ã‚Â¢Ãƒâ€”Ã‚Âª Ãƒâ€”Ã‚Â¦Ãƒâ€”Ã‚Â§-Ãƒâ€”Ã‚ÂÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¸ Ãƒâ€”Ã¢â‚¬ÂÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â. Ãƒâ€”Ã‚ÂªÃƒâ€”Ã¢â‚¬â€Ãƒâ€”Ã¢â‚¬â€œÃƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â¨ Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬â€Ãƒâ€”Ã‚Â¨!")
        return
    user["streak"] += 1
    user["last_checkin"] = today
    bonus = min(user["streak"], 7) * 5
    user["points"] += bonus
    db[uid] = user
    save_db(db, POINTS_FILE)
    await msg.answer(f"ÃƒÂ¢Ã‹Å“Ã¢â€šÂ¬ÃƒÂ¯Ã‚Â¸Ã‚Â Ãƒâ€”Ã‚Â¦Ãƒâ€”Ã‚Â§-Ãƒâ€”Ã‚ÂÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¸ Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â¦Ãƒâ€”Ã‚Â¢! +{bonus} Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚Â§\nÃƒâ€”Ã‚Â¡Ãƒâ€”Ã¢â‚¬ÂÃƒâ€”Ã¢â‚¬Âº: {user['points']} Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚Â§ | Ãƒâ€”Ã‚Â¨Ãƒâ€”Ã‚Â¦Ãƒâ€”Ã‚Â£: {user['streak']} Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â")

# ---------- /leaderboard ----------
@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    db = load_db(POINTS_FILE)
    if not db:
        await msg.answer("Ãƒâ€”Ã‚ÂÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¸ Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚ÂªÃƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚Â¢Ãƒâ€”Ã¢â‚¬Å“Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¸.")
        return
    sorted_users = sorted(db.items(), key=lambda x: x[1]["points"], reverse=True)[:5]
    text = "ÃƒÂ°Ã…Â¸Ã‚ÂÃ¢â‚¬Â  **Ãƒâ€”Ã‹Å“Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã…â€œÃƒâ€”Ã‚Âª Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…â€œÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â:**\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        text += f"{i}. {uid[:8]}...  {data['points']} Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚Â§ (Ãƒâ€”Ã‚Â¨Ãƒâ€”Ã‚Â¦Ãƒâ€”Ã‚Â£ {data['streak']})\n"
    await msg.answer(text)

# ---------- /points ----------
@dp.message(Command("points"))
async def cmd_points(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    user = db.get(uid, {"points": 0, "streak": 0})
    await msg.answer(f"ÃƒÂ°Ã…Â¸Ã…Â½Ã‚Â¯ Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â© Ãƒâ€”Ã…â€œÃƒâ€”Ã…Â¡ {user['points']} Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚Â§ | Ãƒâ€”Ã‚Â¨Ãƒâ€”Ã‚Â¦Ãƒâ€”Ã‚Â£ {user['streak']} Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã‚Â")

# ---------- /daily ----------
@dp.message(Command("daily"))
async def cmd_daily(msg: Message):
    await msg.answer("ÃƒÂ°Ã…Â¸Ã¢â‚¬Å“Ã¢â‚¬Â¦ **Ãƒâ€”Ã…Â¾Ãƒâ€”Ã‚Â©Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Âª Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Âª:**\n/checkin  Ãƒâ€”Ã‚Â¦Ãƒâ€”Ã‚Â§-Ãƒâ€”Ã‚ÂÃƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã…Â¸ (+5 Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚Â§)\n/register  Ãƒâ€”Ã¢â‚¬ÂÃƒâ€”Ã‚Â¨Ãƒâ€”Ã‚Â©Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬Â\n/donate  Ãƒâ€”Ã‚ÂªÃƒâ€”Ã‚Â¨Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã…Â¾Ãƒâ€”Ã¢â‚¬Â")

# ---------- /backup ----------
@dp.message(Command("backup"))
async def cmd_backup(msg: Message):
    await msg.answer("ÃƒÂ°Ã…Â¸Ã¢â‚¬Å“Ã‚Â¦ Ãƒâ€”Ã¢â‚¬â„¢Ãƒâ€”Ã¢â€žÂ¢Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã¢â€žÂ¢ Ãƒâ€”Ã…Â¾Ãƒâ€”Ã…â€œÃƒâ€”Ã‚Â Ãƒâ€”Ã‚Â Ãƒâ€”Ã‚Â©Ãƒâ€”Ã…Â¾Ãƒâ€”Ã‚Â¨ Ãƒâ€”Ã¢â‚¬ËœÃƒâ€”Ã‚Â¢Ãƒâ€”Ã‚Â Ãƒâ€”Ã…Â¸. Ãƒâ€”Ã…â€œÃƒâ€”Ã‚Â¨Ãƒâ€”Ã‚Â©Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚ÂªÃƒâ€”Ã…Â¡.")

# ---------- /myid ----------
@dp.message(Command("myid"))
async def cmd_myid(msg: Message):
    await msg.answer(f"ÃƒÂ°Ã…Â¸Ã¢â‚¬Â Ã¢â‚¬Â Ãƒâ€”Ã¢â‚¬Â-ID Ãƒâ€”Ã‚Â©Ãƒâ€”Ã…â€œÃƒâ€”Ã…Â¡: {msg.from_user.id}")

# ---------- /help ----------
@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "ÃƒÂ°Ã…Â¸Ã¢â‚¬Å“Ã¢â‚¬Â¹ **Ãƒâ€”Ã‚Â¤Ãƒâ€”Ã‚Â§Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã¢â‚¬Å“Ãƒâ€”Ã¢â‚¬Â¢Ãƒâ€”Ã‚Âª:**\n"
        "/start /register /donate /status\n"
        "/checkin /leaderboard /points /daily\n"
        "/users /broadcast /backup /myid /help"
    )

# ---------- main ----------

# ---------- AI Chat (Groq) ----------
import requests
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@dp.message()
async def ai_chat(msg: Message):
    if not GROQ_API_KEY:
        await msg.answer("AI not configured.")
        return
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": msg.text}],
                "max_tokens": 500
            },
            timeout=15
        )
        data = resp.json()
        reply = data["choices"][0]["message"]["content"]
        await msg.answer(reply[:4000])  # Telegram limit
    except Exception as e:
        await msg.answer(f"AI error: {e}")
async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
