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
        "Ã°Å¸Å¡â‚¬ **SLH Crowdfunding**\n\n"
        "Ã—â€˜Ã—Â¨Ã—â€¢Ã—â€ºÃ—â„¢Ã—Â Ã—â€Ã—â€˜Ã—ÂÃ—â„¢Ã—Â Ã—Å“Ã—Â§Ã—Å¾Ã—Â¤Ã—â„¢Ã—â„¢Ã—Å¸ Ã—â€™Ã—â„¢Ã—â€¢Ã—Â¡ Ã—â€Ã—â€Ã—Å¾Ã—â€¢Ã—Â Ã—â„¢Ã—Â Ã—Â©Ã—Å“ SLH!\n"
        "Ã—ÂÃ—Â Ã—â€”Ã—Â Ã—â€¢ Ã—â€˜Ã—â€¢Ã—Â Ã—â„¢Ã—Â AI Ã—ÂÃ—â€¢Ã—ËœÃ—â€¢Ã—Â Ã—â€¢Ã—Å¾Ã—â„¢  Ã—â€¢Ã—Å¾Ã—â€”Ã—Â¤Ã—Â©Ã—â„¢Ã—Â Ã—ÂªÃ—â€¢Ã—Å¾Ã—â€ºÃ—â„¢Ã—Â Ã—â€ºÃ—Å¾Ã—â€¢Ã—Å¡.\n\n"
        "Ã°Å¸â€™Å½ **Ã—Â¤Ã—Â§Ã—â€¢Ã—â€œÃ—â€¢Ã—Âª:**\n"
        "/register  Ã—â€Ã—Â¨Ã—Â©Ã—Å¾Ã—â€ Ã—Å“Ã—Â¢Ã—â€œÃ—â€ºÃ—â€¢Ã—Â Ã—â„¢Ã—Â\n"
        "/donate  Ã—ÂªÃ—Â¨Ã—â€¢Ã—Å¾Ã—â€ Ã—â€¢Ã—â€Ã—Â©Ã—Â§Ã—Â¢Ã—â€\n"
        "/status  Ã—Â¡Ã—ËœÃ—ËœÃ—â€¢Ã—Â¡ Ã—Â¤Ã—Â¨Ã—â€¢Ã—â„¢Ã—Â§Ã—Ëœ\n"
        "/checkin  Ã—Â¦Ã—Â§-Ã—ÂÃ—â„¢Ã—Å¸ Ã—â„¢Ã—â€¢Ã—Å¾Ã—â„¢ (+5 Ã—Â Ã—Â§)\n"
        "/leaderboard  Ã—ËœÃ—â€˜Ã—Å“Ã—Âª Ã—Å¾Ã—â€¢Ã—â€˜Ã—â„¢Ã—Å“Ã—â„¢Ã—Â\n"
        "/help  Ã—â€ºÃ—Å“ Ã—â€Ã—Â¤Ã—Â§Ã—â€¢Ã—â€œÃ—â€¢Ã—Âª",
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
    await msg.answer("Ã¢Å“â€¦ Ã—Â Ã—Â¨Ã—Â©Ã—Å¾Ã—Âª Ã—â€˜Ã—â€Ã—Â¦Ã—Å“Ã—â€”Ã—â€! Ã—ÂªÃ—Â§Ã—â€˜Ã—Å“/Ã—â„¢ Ã—Â¢Ã—â€œÃ—â€ºÃ—â€¢Ã—Â Ã—â„¢Ã—Â.")

# ---------- /donate ----------
@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(
        "Ã°Å¸â€™Â° **Ã—ÂªÃ—Â¨Ã—â€¢Ã—Å¾Ã—â€ Ã—Å“Ã—Â§Ã—Å¾Ã—Â¤Ã—â„¢Ã—â„¢Ã—Å¸:**\n\n"
        "Ã—Â©Ã—Å“Ã—â€” TON Ã—Å“Ã—â€ºÃ—ÂªÃ—â€¢Ã—â€˜Ã—Âª:\n"
        "`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`\n\n"
        "Ã°Å¸â€œÅ  **Ã—Â¨Ã—Å¾Ã—â€¢Ã—Âª Ã—ÂªÃ—Å¾Ã—â„¢Ã—â€ºÃ—â€:**\n"
        "Ã¢â‚¬Â¢ Supporter ($1)  Ã—Â©Ã—Â Ã—â€˜Ã—ÂÃ—ÂªÃ—Â¨\n"
        "Ã¢â‚¬Â¢ Builder ($5)  Early access + Ã—â€˜Ã—ÂÃ—â€œÃ—â€™'\n"
        "Ã¢â‚¬Â¢ Founder ($20)  Ã—â€Ã—Â¦Ã—â€˜Ã—Â¢Ã—â€ Ã—Â¢Ã—Å“ Ã—Â¤Ã—â„¢Ã—Â¦'Ã—Â¨Ã—â„¢Ã—Â\n"
        "Ã¢â‚¬Â¢ Visionary ($50)  Ã—Â©Ã—â„¢Ã—â€”Ã—â€ Ã—ÂÃ—â„¢Ã—Â©Ã—â„¢Ã—Âª + Ã—Â¡Ã—ËœÃ—ËœÃ—â€¢Ã—Â¡ Ã—Å¾Ã—â„¢Ã—â„¢Ã—Â¡Ã—â€œ",
        parse_mode="Markdown"
    )

# ---------- /status ----------
@dp.message(Command("status"))
async def cmd_status(msg: Message):
    await msg.answer(
        "Ã°Å¸â€œÅ  **Ã—Â¡Ã—ËœÃ—ËœÃ—â€¢Ã—Â¡ Ã—Â¤Ã—Â¨Ã—â€¢Ã—â„¢Ã—Â§Ã—Ëœ:**\n"
        "Ã¢Å“â€¦ Bot: Online\nÃ¢Å“â€¦ Crowdfunding: Active\n"
        "Ã¢Å“â€¦ Mini App: [slh-nft.com](https://slh-nft.com)"
    )

# ---------- /users (admin) ----------
@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Ã¢â€ºâ€ Ã—ÂÃ—â€œÃ—Å¾Ã—â„¢Ã—Å¸ Ã—â€˜Ã—Å“Ã—â€˜Ã—â€œ")
        return
    db = load_db(CONTACTS_FILE)
    if not db:
        await msg.answer("Ã—ÂÃ—â„¢Ã—Å¸ Ã—Å¾Ã—Â©Ã—ÂªÃ—Å¾Ã—Â©Ã—â„¢Ã—Â Ã—Â¨Ã—Â©Ã—â€¢Ã—Å¾Ã—â„¢Ã—Â.")
        return
    text = f"Ã°Å¸â€œâ€¹ **{len(db)} Ã—Å¾Ã—Â©Ã—ÂªÃ—Å¾Ã—Â©Ã—â„¢Ã—Â:**\n"
    for uid, data in db.items():
        text += f"Ã¢â‚¬Â¢ {data['full_name']} (@{data['username']}) - {data['joined'][:10]}\n"
    await msg.answer(text)

# ---------- /broadcast (admin) ----------
@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Ã¢â€ºâ€ Ã—ÂÃ—â€œÃ—Å¾Ã—â„¢Ã—Å¸ Ã—â€˜Ã—Å“Ã—â€˜Ã—â€œ")
        return
    parts = msg.text.split(" ", 1)
    if len(parts) < 2:
        await msg.answer("Ã—Â©Ã—â„¢Ã—Å¾Ã—â€¢Ã—Â©: /broadcast <Ã—â€Ã—â€¢Ã—â€œÃ—Â¢Ã—â€>")
        return
    db = load_db(CONTACTS_FILE)
    sent = 0
    for uid in db:
        try:
            await msg.bot.send_message(int(uid), f"Ã°Å¸â€œÂ¢ {parts[1]}")
            sent += 1
        except:
            pass
    await msg.answer(f"Ã°Å¸â€œÂ¤ Ã—Â Ã—Â©Ã—Å“Ã—â€” Ã—Å“-{sent}/{len(db)} Ã—Å¾Ã—Â©Ã—ÂªÃ—Å¾Ã—Â©Ã—â„¢Ã—Â.")

# ---------- /checkin ----------
@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    today = datetime.date.today().isoformat()
    user = db.get(uid, {"points": 0, "streak": 0, "last_checkin": ""})
    if user["last_checkin"] == today:
        await msg.answer("Ã¢Ëœâ‚¬Ã¯Â¸Â Ã—â€ºÃ—â€˜Ã—Â¨ Ã—â€˜Ã—â„¢Ã—Â¦Ã—Â¢Ã—Âª Ã—Â¦Ã—Â§-Ã—ÂÃ—â„¢Ã—Å¸ Ã—â€Ã—â„¢Ã—â€¢Ã—Â. Ã—ÂªÃ—â€”Ã—â€“Ã—â€¢Ã—Â¨ Ã—Å¾Ã—â€”Ã—Â¨!")
        return
    user["streak"] += 1
    user["last_checkin"] = today
    bonus = min(user["streak"], 7) * 5
    user["points"] += bonus
    db[uid] = user
    save_db(db, POINTS_FILE)
    await msg.answer(f"Ã¢Ëœâ‚¬Ã¯Â¸Â Ã—Â¦Ã—Â§-Ã—ÂÃ—â„¢Ã—Å¸ Ã—â€˜Ã—â€¢Ã—Â¦Ã—Â¢! +{bonus} Ã—Â Ã—Â§\nÃ—Â¡Ã—â€Ã—â€º: {user['points']} Ã—Â Ã—Â§ | Ã—Â¨Ã—Â¦Ã—Â£: {user['streak']} Ã—â„¢Ã—Å¾Ã—â„¢Ã—Â")

# ---------- /leaderboard ----------
@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    db = load_db(POINTS_FILE)
    if not db:
        await msg.answer("Ã—ÂÃ—â„¢Ã—Å¸ Ã—Â Ã—ÂªÃ—â€¢Ã—Â Ã—â„¢Ã—Â Ã—Â¢Ã—â€œÃ—â„¢Ã—â„¢Ã—Å¸.")
        return
    sorted_users = sorted(db.items(), key=lambda x: x[1]["points"], reverse=True)[:5]
    text = "Ã°Å¸Ââ€  **Ã—ËœÃ—â€˜Ã—Å“Ã—Âª Ã—Å¾Ã—â€¢Ã—â€˜Ã—â„¢Ã—Å“Ã—â„¢Ã—Â:**\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        text += f"{i}. {uid[:8]}...  {data['points']} Ã—Â Ã—Â§ (Ã—Â¨Ã—Â¦Ã—Â£ {data['streak']})\n"
    await msg.answer(text)

# ---------- /points ----------
@dp.message(Command("points"))
async def cmd_points(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    user = db.get(uid, {"points": 0, "streak": 0})
    await msg.answer(f"Ã°Å¸Å½Â¯ Ã—â„¢Ã—Â© Ã—Å“Ã—Å¡ {user['points']} Ã—Â Ã—Â§ | Ã—Â¨Ã—Â¦Ã—Â£ {user['streak']} Ã—â„¢Ã—Å¾Ã—â„¢Ã—Â")

# ---------- /daily ----------
@dp.message(Command("daily"))
async def cmd_daily(msg: Message):
    await msg.answer("Ã°Å¸â€œâ€¦ **Ã—Å¾Ã—Â©Ã—â„¢Ã—Å¾Ã—â€¢Ã—Âª Ã—â„¢Ã—â€¢Ã—Å¾Ã—â„¢Ã—â€¢Ã—Âª:**\n/checkin  Ã—Â¦Ã—Â§-Ã—ÂÃ—â„¢Ã—Å¸ (+5 Ã—Â Ã—Â§)\n/register  Ã—â€Ã—Â¨Ã—Â©Ã—Å¾Ã—â€\n/donate  Ã—ÂªÃ—Â¨Ã—â€¢Ã—Å¾Ã—â€")

# ---------- /backup ----------
@dp.message(Command("backup"))
async def cmd_backup(msg: Message):
    await msg.answer("Ã°Å¸â€œÂ¦ Ã—â€™Ã—â„¢Ã—â€˜Ã—â€¢Ã—â„¢ Ã—Å¾Ã—Å“Ã—Â Ã—Â Ã—Â©Ã—Å¾Ã—Â¨ Ã—â€˜Ã—Â¢Ã—Â Ã—Å¸. Ã—Å“Ã—Â¨Ã—Â©Ã—â€¢Ã—ÂªÃ—Å¡.")

# ---------- /myid ----------
@dp.message(Command("myid"))
async def cmd_myid(msg: Message):
    await msg.answer(f"Ã°Å¸â€ â€ Ã—â€-ID Ã—Â©Ã—Å“Ã—Å¡: {msg.from_user.id}")

# ---------- /help ----------
@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "Ã°Å¸â€œâ€¹ **Ã—Â¤Ã—Â§Ã—â€¢Ã—â€œÃ—â€¢Ã—Âª:**\n"
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