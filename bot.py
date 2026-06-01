from free_ai_client import converse
from database import init_db, db_pool
from handlers.payment import handle_premium_command, handle_confirm_command, check_premium
from handlers.taptoearn import handle_tap_command
from session import add_to_conversation, get_conversation, clear_conversation
import asyncio, os, json, datetime, requests
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or os.getenv("SLH_CLAUDE_BOT_TOKEN")
dp = Dispatcher()

CONTACTS_FILE = "contacts.json"
POINTS_FILE = "points.json"
IDENTITY_FILE = "identity.json"

def load_db(file):
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f: json.dump({}, f)
    with open(file, "r", encoding="utf-8") as f: return json.load(f)

def save_db(data, file):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "").replace(" ", ",").split(",") if x]

LOGO = """
╔══════════════════════════════════╗
║     ███████╗██╗     ██╗  ██╗     ║
║     ██╔════╝██║     ██║  ██║     ║
║     ███████╗██║     ███████║     ║
║     ╚════██║██║     ██╔══██║     ║
║     ███████║███████╗██║  ██║     ║
║     ╚══════╝╚══════╝╚═╝  ╚═╝     ║
║   🧠 SLH SPARK AI   v3.3        ║
╚══════════════════════════════════╝
"""

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Status", callback_data="cmd_status"),
         InlineKeyboardButton(text="⭐ Points", callback_data="cmd_points")],
        [InlineKeyboardButton(text="✅ Check-in", callback_data="cmd_checkin"),
         InlineKeyboardButton(text="⚡ Tap-to-Earn", callback_data="cmd_tap")],
        [InlineKeyboardButton(text="💰 Crypto", callback_data="cmd_crypto"),
         InlineKeyboardButton(text="🤝 Donate", callback_data="cmd_donate")],
        [InlineKeyboardButton(text="📖 Guide", callback_data="cmd_guide"),
         InlineKeyboardButton(text="❓ Help", callback_data="cmd_help")],
        [InlineKeyboardButton(text="🔮 Oracle", callback_data="cmd_oracle"),
         InlineKeyboardButton(text="☮️ Peace Game", callback_data="cmd_peace")],
        [InlineKeyboardButton(text="💎 Upgrade", callback_data="cmd_upgrade"),
         InlineKeyboardButton(text="📋 Tasks", callback_data="cmd_tasks")],
        [InlineKeyboardButton(text="💳 Buy", callback_data="cmd_buy"),
         InlineKeyboardButton(text="🛒 Pay", callback_data="cmd_pay")],
        [InlineKeyboardButton(text="👤 Identity", callback_data="cmd_identity")],
        [InlineKeyboardButton(text="🏦 דף משקיעים", url="https://slh-nft.com/investor-landing/")],
    ])

# ========== EXISTING COMMANDS ==========
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.answer(f"<pre>{LOGO}</pre>\n🤖 **SLH Spark AI v3.3**\n\nברוך הבא, {msg.from_user.full_name}!\nבחר אפשרות:", parse_mode="HTML", reply_markup=main_menu())

@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer("📘 **פקודות**: /start /help /crypto /guide /donate /tasks /menu /pay /buy /upgrade /oracle /peace /seed /sysinfo /profile /myid /leaderboard /checkin /points /daily /backup /broadcast /wallet /deposit /tap /referral /admin /users /morning /doctor /statusapi /test /crm /events /support /roadmap /transfer /faq /tutorial /progress /done /commission /links /about /healthcheck /identity /myidentity /community /wallet /game /invest")

@dp.message(Command("crypto"))
async def cmd_crypto(msg: Message):
    try:
        btc = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd").json()["bitcoin"]["usd"]
        eth = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd").json()["ethereum"]["usd"]
        await msg.answer(f"💰 BTC: ${btc} | ETH: ${eth}")
    except:
        await msg.answer("⚠️ Crypto prices temporarily unavailable.")

@dp.message(Command("guide"))
async def cmd_guide(msg: Message):
    await msg.answer("📘 **מדריך כלכלי**\n🔐 ארנק: Trust Wallet / Exodus\n💵 Stablecoin בלי בנק\n📉 הגנה: USDT/USDC\n⚠️ CBDC = שליטה\n🤝 /donate")

@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer("🤝 **תמיכה ב‑SLH Ecosystem**\nTON: `UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`\nUSDT (TRC-20): `TYoB3sXqH3kL9xQZqR5nL8wJqVkL3wYxZ`")

@dp.message(Command("tasks"))
async def cmd_tasks(msg: Message):
    await msg.answer("📋 **משימות**\n(מערכת משימות תגיע בקרוב)")

@dp.message(Command("menu"))
async def cmd_menu(msg: Message):
    await msg.answer("תפריט:", reply_markup=main_menu())

@dp.message(Command("pay"))
async def cmd_pay(msg: Message):
    await msg.answer_invoice(title="SLH Premium",description="גישה חודשית לפרימיום",payload="premium_monthly",currency="XTR",prices=[LabeledPrice(label="SLH Premium", amount=5000)],start_parameter="premium",provider_token="")

@dp.message(Command("buy"))
async def cmd_buy(msg: Message):
    await msg.answer_invoice(title="SLH Premium - 1 Month",description="Double XP + live alerts + priority support",payload="premium_1month",currency="XTR",prices=[LabeledPrice(label="Premium", amount=50)],start_parameter="slh_premium",provider_token="")

@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: Message):
    await msg.answer("💎 **מסלולי Premium**\nPro: 9.9 TON/חודש\nBusiness: 29 TON/חודש")

@dp.message(Command("oracle"))
async def cmd_oracle(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ask Oracle", callback_data="oracle_ask")],
        [InlineKeyboardButton(text="System Scan", callback_data="oracle_scan")],
        [InlineKeyboardButton(text="Prediction", callback_data="oracle_predict")],
        [InlineKeyboardButton(text="Mission", callback_data="oracle_mission")],
    ])
    await msg.answer("🔮 **SLH Oracle+**\nבחרו:", reply_markup=kb)

@dp.message(Command("peace"))
async def cmd_peace(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☮️ Peace Path", callback_data="peace_path")],
        [InlineKeyboardButton(text="🤖 Innovation Path", callback_data="innovation_path")],
        [InlineKeyboardButton(text="🌍 Humanity Path", callback_data="humanity_path")],
    ])
    await msg.answer("☮️ **Peace Game**\nבחרו נתיב:", reply_markup=kb)

@dp.message(Command("seed"))
async def cmd_seed(msg: Message):
    await msg.answer("Seed planted! 🌱")

@dp.message(Command("sysinfo"))
async def cmd_sysinfo(msg: Message):
    await msg.answer(f"System: {os.name}\nCPU: {os.cpu_count()} cores")

@dp.message(Command("commission"))
async def cmd_commission(msg: Message):
    await msg.answer("Commission tracking coming soon.")

@dp.message(Command("profile"))
async def cmd_profile(msg: Message):
    await msg.answer(f"👤 {msg.from_user.full_name}\nID: {msg.from_user.id}")

@dp.message(Command("myid"))
async def cmd_myid(msg: Message):
    await msg.answer(f"🆔 {msg.from_user.id}")

@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    await msg.answer("Dashboard: https://slh-nft.com/my.html")

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    db = load_db(POINTS_FILE)
    if not db: await msg.answer("No data yet."); return
    sorted_users = sorted(db.items(), key=lambda x: x[1]["points"], reverse=True)[:5]
    text = "🏆 **Leaderboard:**\n"
    for i, (uid, data) in enumerate(sorted_users, 1): text += f"{i}. {uid[:8]}...  {data['points']} pts (Streak {data['streak']})\n"
    await msg.answer(text)

@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    db = load_db(POINTS_FILE)
    uid = str(msg.from_user.id)
    today = datetime.date.today().isoformat()
    user = db.get(uid, {"points":0,"streak":0,"last_checkin":""})
    if user["last_checkin"]==today: await msg.answer("☀️ Already checked in today!"); return
    user["streak"]+=1; user["last_checkin"]=today; bonus=min(user["streak"],7)*5; user["points"]+=bonus
    db[uid]=user; save_db(db,POINTS_FILE)
    await msg.answer(f"☀️ Check-in successful! +{bonus} points\nTotal: {user['points']} pts | Streak: {user['streak']} days")

@dp.message(Command("points"))
async def cmd_points(msg: Message):
    db=load_db(POINTS_FILE); uid=str(msg.from_user.id); user=db.get(uid,{"points":0,"streak":0})
    await msg.answer(f"🎯 You have {user['points']} points | Streak: {user['streak']} days")

@dp.message(Command("daily"))
async def cmd_daily(msg: Message):
    await msg.answer("📅 **Daily Missions:**\n/checkin  Check-in (+5 pts)\n/register  Subscribe")

@dp.message(Command("backup"))
async def cmd_backup(msg: Message):
    await msg.answer("📦 Backup saved to cloud.")

@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: await msg.answer("⛔ Admin only"); return
    parts=msg.text.split(" ",1)
    if len(parts)<2: await msg.answer("Usage: /broadcast <message>"); return
    db=load_db(CONTACTS_FILE); sent=0
    for uid in db:
        try: await msg.bot.send_message(int(uid), f"📢 {parts[1]}"); sent+=1
        except: pass
    await msg.answer(f"📤 Sent to {sent}/{len(db)} users.")

@dp.message(Command("wallet"))
async def cmd_wallet(msg: Message):
    await msg.answer("💰 **ארנק SLH**\n(בקרוב: ניהול SLH Points, TON, NFT)")

@dp.message(Command("deposit"))
async def cmd_deposit(msg: Message):
    await msg.answer("Deposit address: UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")

@dp.message(Command("tap"))
async def cmd_tap(msg: Message):
    await msg.answer("Tap-to-Earn: Coming soon!")

@dp.message(Command("referral"))
async def cmd_referral(msg: Message):
    await msg.answer("Referral link: https://t.me/SLH_Claude_bot?start=ref224223270")

@dp.message(Command("admin"))
async def cmd_admin(msg: Message):
    await msg.answer("Admin panel: /users /broadcast /crm /events /healthcheck")

@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return
    db=load_db(CONTACTS_FILE); await msg.answer(f"Total users: {len(db)}")

@dp.message(Command("morning"))
async def cmd_morning(msg: Message):
    await msg.answer("Good morning! ☀️")

@dp.message(Command("doctor"))
async def cmd_doctor(msg: Message):
    await msg.answer("Doctor appointment reminders coming soon.")

@dp.message(Command("statusapi"))
async def cmd_statusapi(msg: Message):
    await msg.answer("API status: OK")

@dp.message(Command("test"))
async def cmd_test(msg: Message):
    await msg.answer("Test passed.")

@dp.message(Command("crm"))
async def cmd_crm(msg: Message):
    await msg.answer("📇 **CRM**\n(לקוחות, לידים, היסטוריה  בקרוב)")

@dp.message(Command("events"))
async def cmd_events(msg: Message):
    await msg.answer("Events: none yet")

@dp.message(Command("support"))
async def cmd_support(msg: Message):
    await msg.answer("Support: @OsifUngar")

@dp.message(Command("roadmap"))
async def cmd_roadmap(msg: Message):
    await msg.answer("Roadmap: https://slh-nft.com/roadmap")

@dp.message(Command("transfer"))
async def cmd_transfer(msg: Message):
    await msg.answer("Transfer coming soon.")

@dp.message(Command("faq"))
async def cmd_faq(msg: Message):
    await msg.answer("FAQ: /guide and /help")

@dp.message(Command("tutorial"))
async def cmd_tutorial(msg: Message):
    await msg.answer("Tutorial: follow /guide")

@dp.message(Command("progress"))
async def cmd_progress(msg: Message):
    await msg.answer("Progress: 50%")

@dp.message(Command("done"))
async def cmd_done(msg: Message):
    await msg.answer("Task marked as done.")

@dp.message(Command("about"))
async def cmd_about(msg: Message):
    await msg.answer("SLH Spark AI v3.3 - Intelligent Project Engine")

@dp.message(Command("links"))
async def cmd_links(msg: Message):
    await msg.answer("Links:\nWebsite: https://slh-nft.com\nGitHub: https://github.com/osifeu-prog/slh-master-bot")

@dp.message(Command("healthcheck"))
async def cmd_healthcheck(msg: Message):
    results = ["✅ Bot: Online"]
    if os.getenv("GROQ_API_KEY"): results.append("✅ Groq API Key: Set")
    else: results.append("❌ Groq API Key: Missing")
    for f in [CONTACTS_FILE, POINTS_FILE]:
        results.append(f"✅ {f}: Exists" if os.path.exists(f) else f"⚠️ {f}: Not yet created")
    try:
        r = requests.get("https://api.telegram.org/bot" + TOKEN + "/getMe", timeout=5)
        results.append("✅ Telegram API: Reachable" if r.ok else "❌ Telegram API: Error")
    except: results.append("❌ Telegram API: Unreachable")
    await msg.answer("\n".join(results))

# ========== INVEST COMMAND ==========
@dp.message(Command("invest"))
async def cmd_invest(msg: Message):
    text = (
        "🏦 **הזדמנות השקעה - SLH**\n\n"
        "**מסלולי השקעה:**\n"
        "• מיקרו-השקעה (1,000$-10,000$): חוזים עתידיים על מכירות\n"
        "• משקיע בינוני (10,000$-80,000$): שותפות ברווחים\n"
        "• משקיע אסטרטגי (80,000$-500,000$): מניות בחברה\n\n"
        "**תרחישי רווח שנתי:**\n"
        "📊 שמרני: 600,000$\n"
        "🚀 בינוני: 3.6M$\n"
        "🌙 אגרסיבי: 12M$\n\n"
        "לפרטים נוספים, צור קשר עם @OsifUngar"
    )
    await msg.answer(text, parse_mode="Markdown")

# ========== IDENTITY SYSTEM ==========
@dp.message(Command("identity"))
async def cmd_identity(msg: Message):
    db = load_db(IDENTITY_FILE)
    uid = str(msg.from_user.id)
    if uid in db:
        await msg.answer("✅ כבר הגדרת את הזהות שלך!\nשלח /myidentity כדי לראות.")
        return
    await msg.answer("👤 **ברוך הבא למסע החיים של SLH**\n\nמה השם שלך?\n(פשוט שלח הודעה עם השם)")
    if not hasattr(dp, 'temp'): dp.temp = {}
    dp.temp[uid] = {'step': 'name'}

@dp.message(Command("myidentity"))
async def cmd_myidentity(msg: Message):
    db = load_db(IDENTITY_FILE)
    uid = str(msg.from_user.id)
    if uid not in db:
        await msg.answer("❌ עדיין לא הגדרת זהות. שלח /identity")
        return
    data = db[uid]
    await msg.answer(f"👤 **{data['name']}**\n🌱 חזון: {data['vision']}\n💎 ערכים: {', '.join(data['values'])}")

@dp.message()
async def identity_flow(msg: Message):
    if not hasattr(dp, 'temp') or str(msg.from_user.id) not in dp.temp:
        return
    uid = str(msg.from_user.id)
    state = dp.temp[uid]
    db = load_db(IDENTITY_FILE)

    if state['step'] == 'name':
        state['name'] = msg.text
        state['step'] = 'vision'
        await msg.answer("🌱 **מה החזון שלך?**\n(משפט אחד שמתאר את המטרה הגדולה שלך)")
    elif state['step'] == 'vision':
        state['vision'] = msg.text
        state['step'] = 'values'
        await msg.answer("💎 **בחר 3 ערכים שמנחים אותך:**\n(לדוגמה: אהבה, חופש, שלום, צדק, אומץ, חכמה)\nשלח את שלושתם מופרדים בפסיקים")
    elif state['step'] == 'values':
        values = [v.strip() for v in msg.text.split(",")]
        if len(values) < 3:
            await msg.answer("⚠️ אנא שלח 3 ערכים לפחות.")
            return
        state['values'] = values[:3]
        db[uid] = {
            'name': state['name'],
            'vision': state['vision'],
            'values': state['values'],
            'created_at': str(datetime.datetime.now())
        }
        save_db(db, IDENTITY_FILE)
        points_db = load_db(POINTS_FILE)
        user_points = points_db.get(uid, {"points": 0, "streak": 0})
        user_points['points'] += 50
        points_db[uid] = user_points
        save_db(points_db, POINTS_FILE)
        del dp.temp[uid]
        await msg.answer(f"🎉 **הזהות שלך נוצרה!**\n\nשם: {state['name']}\nחזון: {state['vision']}\nערכים: {', '.join(state['values'])}\n\n+50 נקודות! 🎯\nשלח /myidentity כדי לראות את הדף שלך.")
    else:
        del dp.temp[uid]

# ========== NEW PLACEHOLDERS ==========
@dp.message(Command("community"))
async def cmd_community(msg: Message):
    await msg.answer("👥 **קהילה**\n(בקרוב: יצירת קהילות, חדרים, אירועים)")

@dp.message(Command("game"))
async def cmd_game(msg: Message):
    await msg.answer("🎮 **משחק החיים**\n(בקרוב: משימות, אתגרים, לוח מובילים)")

# ========== CALLBACKS ==========
@dp.callback_query(F.data.startswith("cmd_"))
async def on_cmd_button(call: CallbackQuery):
    data = call.data
    if data == "cmd_status": await call.message.answer("✅ Bot Online\n✅ Railway: Connected")
    elif data == "cmd_points": await cmd_points(call.message)
    elif data == "cmd_checkin": await cmd_checkin(call.message)
    elif data == "cmd_tap": await call.message.answer("Tap-to-Earn: Coming soon!")
    elif data == "cmd_crypto": await cmd_crypto(call.message)
    elif data == "cmd_donate": await cmd_donate(call.message)
    elif data == "cmd_guide": await cmd_guide(call.message)
    elif data == "cmd_help": await cmd_help(call.message)
    elif data == "cmd_oracle": await cmd_oracle(call.message)
    elif data == "cmd_peace": await cmd_peace(call.message)
    elif data == "cmd_upgrade": await cmd_upgrade(call.message)
    elif data == "cmd_tasks": await cmd_tasks(call.message)
    elif data == "cmd_buy": await cmd_buy(call.message)
    elif data == "cmd_pay": await cmd_pay(call.message)
    elif data == "cmd_identity": await cmd_identity(call.message)
    await call.answer()

@dp.callback_query(F.data.startswith("oracle_"))
async def on_oracle_button(call: CallbackQuery):
    data = call.data
    if data == "oracle_ask": await call.message.answer("🔮 Oracle says: Ask me anything about the project.")
    elif data == "oracle_scan": await call.message.answer("🔍 System Scan: Bot: Online, DB: Connected, Railway: Online")
    elif data == "oracle_predict": await call.message.answer("📈 Prediction: +0.5 TON/day, 15 TON by month end.")
    elif data == "oracle_mission": await call.message.answer("💙 Daily Peace Mission: Share the bot with one person.")
    await call.answer()

@dp.callback_query(F.data.startswith("peace_"))
async def on_peace_button(call: CallbackQuery):
    data = call.data
    if data == "peace_path": await call.message.answer("Peace Path: What is the most important element in conflict resolution?\nA) Communication B) Force C) Ignoring D) Punishment")
    elif data == "innovation_path": await call.message.answer("Innovation Path: What is the main benefit of humanitarian robots?\nA) Unbiased assistance B) Replacing humans C) Control D) Data collection")
    elif data == "humanity_path": await call.message.answer("Humanity Path: What strengthens a community?\nA) Volunteerism B) Criticism C) Isolation D) Competition")
    await call.answer()

# ========== AI CHAT ==========
@dp.message()
async def ai_chat(msg: Message):
    if msg.text is None or msg.text.startswith("/"):
        return
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        await msg.answer("AI not configured.")
        return
    try:
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role":"user","content":msg.text}], "max_tokens":500},
            timeout=15)
        data = resp.json()
        reply = data["choices"][0]["message"]["content"]
        await msg.answer(reply[:4000])
    except Exception as e:
        await msg.answer(f"AI error: {e}")

async def main():`n    await init_db()
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    print("🚀 SLH Spark AI v3.3 starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
@dp.message_handler(commands=['premium', 'upgrade'])
async def premium_cmd(message: types.Message):
    await handle_premium_command(message)

@dp.message_handler(commands=['confirm'])
async def confirm_cmd(message: types.Message):
    await handle_confirm_command(message)

@dp.message_handler(commands=['tap'])
async def tap_cmd(message: types.Message):
    await handle_tap_command(message)

from handlers.payment import handle_premium_command, handle_confirm_command, check_premium
from handlers.taptoearn import handle_tap_command

def register_extra(dp):
    dp.message(Command('premium'))(handle_premium_command)
    dp.message(Command('upgrade'))(handle_premium_command)
    dp.message(Command('confirm'))(handle_confirm_command)
    dp.message(Command('tap'))(handle_tap_command)

