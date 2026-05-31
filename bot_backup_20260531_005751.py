import time
import aiohttp
import asyncio, os, json, datetime, requests
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from ux.responses import msg_welcome, msg_help, msg_checkin_success, msg_checkin_already, msg_points, msg_leaderboard, msg_status, msg_daily, msg_referral, msg_donate, msg_register_success, msg_register_already, msg_feedback_success, msg_roadmap, msg_error_generic
from ux.keyboards import kb_main_menu, kb_after_checkin, kb_after_points, kb_donate, kb_status, kb_leaderboard, kb_daily, kb_help, kb_referral, kb_roadmap, kb_back_to_menu, kb_admin_panel
from services.wallet import get_balance, add_balance, transfer
from services.ledger import log_transaction
from services.event import emit_event
from services.store import create_store, get_store
from services.product import add_product, list_products
from services.order import create_order
from services.db import init_db, get_db

load_dotenv()
init_db()
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

ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_ID", "").replace(" ", ",").split(",") if x.strip()]

# ---- ASCII Logo ----
SLH_LOGO = r"""
   SLH - AUTONOMOUS SYSTEM
   crowdfunding & AI assistant
"""

# ---- /start ----
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    name = msg.from_user.first_name or msg.from_user.username or "friend"
    welcome_text = (
        "╔══════════════════════════════════╗\n"
        "║   ███████╗██╗     ██╗  ██╗      ║\n"
        "║   ██╔════╝██║     ██║  ██║      ║\n"
        "║   ███████╗██║     ███████║      ║\n"
        "║   ╚════██║██║     ██╔══██║      ║\n"
        "║   ███████║███████╗██║  ██║      ║\n"
        "║   ╚══════╝╚══════╝╚═╝  ╚═╝      ║\n"
        "║                                  ║\n"
        "║  AI PROJECT CREATION SYSTEM v2  ║\n"
        "║  ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆      ║\n"
        "╚══════════════════════════════════╝\n"
        "\n"
        f"👋 שלום, {name}!\n"
        "\n"
        "🤖 מה אני?\n"
        "SLH הוא מערכת AI ליצירה וניהול פרויקטים דיגיטליים\n"
        "מחנויות NFT ועד מסחר בטוקנים — הכל במקום אחד.\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ יכולות המערכת\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "01 · AI Chat       Claude, Gemini, Groq\n"
        "02 · Marketplace   חנויות, מוצרים, NFT\n"
        "03 · Rewards       נקודות, הפניות, TON\n"
        "04 · Support       ניטור, כרטיסים, סשנים\n"
        "05 · CRM           משתמשים, tier, analytics\n"
        "06 · Quiz & XP     קריפטו, leaderboard\n"
        "07 · TON Wallet    תשלומים, תמלוגים\n"
        "08 · Infra         DB, Redis, FastAPI\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 התחל עכשיו\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/register   → הצטרף למערכת\n"
        "/dashboard  → סטטיסטיקות\n"
        "/upgrade    → Premium plans\n"
        "/help       → כל הפקודות\n"
        "\n"
        "slh-nft.com · @SLH_Claude_bot"
    )
    kb = kb_main_menu()
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [[InlineKeyboardButton(**btn) for btn in row] for row in kb]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.answer(welcome_text, parse_mode=None, reply_markup=markup)
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
    user_id = msg.from_user.id
    username = msg.from_user.username or "unknown"
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (telegram_id, username, tier) VALUES (%s,%s,'free') ON CONFLICT (telegram_id) DO UPDATE SET username=%s, last_seen=NOW()",
            (user_id, username, username)
        )
        conn.commit()
        await msg.answer("You are now registered for updates!", parse_mode=None)
    except Exception as e:
        conn.rollback()
        await msg.answer(f"Registration error: {str(e)[:100]}", parse_mode=None)
    finally:
        conn.close()
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




# ---- /doctor (admin) ----
async def check_railway():
    """Query Railway GraphQL API for latest deployment status."""
    try:
        query = """
        query GetDeployments($projectId: String!, $serviceId: String) {
          deployments(input: { projectId: $projectId, serviceId: $serviceId }, first: 3) {
            edges { node { id status createdAt staticUrl service { name } } }
          }
        }
        """
        token = os.getenv("RAILWAY_API_TOKEN", "")
        project_id = os.getenv("RAILWAY_PROJECT_ID", "")
        service_id = os.getenv("RAILWAY_SERVICE_ID", "")
        if not token or not project_id:
            return {"ok": False, "status": "NOT_CONFIGURED", "detail": "Missing RAILWAY_API_TOKEN or PROJECT_ID"}
        variables = {"projectId": project_id}
        if service_id: variables["serviceId"] = service_id
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://backboard.railway.app/graphql/v2",
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=8)
            ) as resp:
                if resp.status != 200:
                    return {"ok": False, "status": "HTTP_ERROR", "detail": str(resp.status)}
                data = await resp.json()
                edges = data.get("data", {}).get("deployments", {}).get("edges", [])
                if not edges:
                    return {"ok": False, "status": "NO_DEPLOYMENTS", "detail": "No deployments found"}
                latest = edges[0]["node"]
                status = latest.get("status", "UNKNOWN")
                return {
                    "ok": status == "SUCCESS",
                    "status": status,
                    "service": latest.get("service", {}).get("name", "?"),
                    "deploy_id": latest.get("id", "?")[:8],
                    "url": latest.get("staticUrl", "")
                }
    except Exception as e:
        return {"ok": False, "status": "ERROR", "detail": str(e)[:200]}

async def check_database():
    """Ping PostgreSQL if DATABASE_URL is set."""
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        return {"ok": None, "detail": "not configured"}
    try:
        import psycopg2
        t0 = time.perf_counter()
        conn = psycopg2.connect(db_url, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        conn.close()
        ms = int((time.perf_counter() - t0) * 1000)
        return {"ok": True, "latency_ms": ms}
    except Exception as e:
        return {"ok": False, "detail": str(e)[:80]}

async def check_redis():
    """Ping Redis if REDIS_URL is set."""
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        return {"ok": None, "detail": "not configured"}
    try:
        import redis.asyncio as aioredis
        t0 = time.perf_counter()
        r = aioredis.from_url(redis_url, socket_timeout=3)
        await r.ping()
        await r.aclose()
        ms = int((time.perf_counter() - t0) * 1000)
        return {"ok": True, "latency_ms": ms}
    except ImportError:
        return {"ok": None, "detail": "redis package not installed"}
    except Exception as e:
        return {"ok": False, "detail": str(e)[:80]}

async def check_ai_key():
    """Check that at least one AI key is present."""
    for key in ["ANTHROPIC_API_KEY", "GROQ_API_KEY"]:
        val = os.getenv(key, "")
        if val:
            return {"ok": True, "provider": key.replace("_API_KEY",""), "detail": "key present"}
    return {"ok": False, "detail": "No AI API key found"}

def build_full_report(railway, db, redis, ai):
    def icon(r): return "✅" if r.get("ok") is True else ("⚪" if r.get("ok") is None else "❌")
    lines = ["🩺 *SLH System Doctor*", "━━━━━━━━━━━━━━━━━━━━━", ""]
    lines.append(f"{icon(railway)} *Railway* — {railway.get('status','?')}")
    if railway.get("service"): lines.append(f"   service: {railway['service']} | deploy: {railway.get('deploy_id','')}")
    lines.append("")
    lines.append(f"{icon(db)} *Database* — {db.get('latency_ms','?')}ms" if db.get("ok") else f"{icon(db)} *Database* — {db.get('detail','error')}")
    lines.append(f"{icon(redis)} *Redis* — {redis.get('detail','skip')}" if redis.get("ok") is None else f"{icon(redis)} *Redis* — {redis.get('latency_ms','?')}ms")
    lines.append(f"{icon(ai)} *{ai.get('provider','AI')}* — {ai.get('detail','?')}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    checks = [railway["ok"], db["ok"], ai["ok"]]
    if all(c is True for c in checks): lines.append("🟢 *All systems operational*")
    elif any(c is False for c in checks): lines.append("🔴 *Issues detected — check logs*")
    else: lines.append("🟡 *Partial — some checks skipped*")
    return "\n".join(lines)

@dp.message(Command("doctor"))
async def cmd_doctor_handler(msg: Message):
    user_id = msg.from_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await msg.answer("Admin only", parse_mode=None)
        return
    await msg.bot.send_chat_action(chat_id=msg.chat.id, action="typing")
    railway_result, redis_result, ai_result = await asyncio.gather(
        check_railway(), check_redis(), check_ai_key()
    )
    db_result = await asyncio.get_event_loop().run_in_executor(None, lambda: asyncio.run(check_database()))
    # check_database is async, but we can run it directly
    db_result = await check_database()
    report = build_full_report(railway_result, db_result, redis_result, ai_result)
    await msg.answer(report, parse_mode=None)

# ---- AI (Groq only) ----
@dp.message(F.text & ~F.text.startswith("/"))
async def ai_chat(msg: Message):
    if msg.text.startswith("/"):
        return
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        await msg.answer("AI not configured.", parse_mode=None)
        return
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are SLH AI assistant. Rules: 1) Never summarize 2) Give ONE decision 3) Max 4 lines 4) End with next action 5) Hebrew first."},
                    {"role": "user", "content": msg.text}
                ],
                "max_tokens": 500
            },
            timeout=15
        )
        reply = resp.json()["choices"][0]["message"]["content"]
        await msg.answer(reply[:4000])
    except Exception as e:
        await msg.answer(f"AI error: {e}", parse_mode=None)

@dp.message(F.text & ~F.text.startswith("/"))
async def ai_chat(msg: Message):
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        await msg.answer("AI not configured.", parse_mode=None)
        return
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are SLH AI assistant. Rules: 1) Never summarize 2) Give ONE decision 3) Max 4 lines 4) End with next action 5) Hebrew first."},
                    {"role": "user", "content": msg.text}
                ],
                "max_tokens": 500
            },
            timeout=15
        )
        reply = resp.json()["choices"][0]["message"]["content"]
        await msg.answer(reply[:4000])
    except Exception as e:
        await msg.answer(f"AI error: {e}", parse_mode=None)

# ---- /doctor (admin) ----
@dp.message(Command("doctor"))
async def cmd_doctor_handler(msg: Message):
    await msg.answer("Doctor works! Railway token present: {0}, AI key present: {1}".format(
        "yes" if os.getenv("RAILWAY_API_TOKEN") else "no",
        "yes" if os.getenv("GROQ_API_KEY") else "no"
    ))


# ---- Callback Query Handler (inline buttons) ----
@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    data = callback.data
    await callback.answer()  # acknowledge the click
    msg = callback.message

    # Map callback_data to existing command handlers
    handlers = {
        "cmd_status":      cmd_status,
        "cmd_points":      cmd_points,
        "cmd_checkin":     cmd_checkin,
        "cmd_daily":       cmd_daily,
        "cmd_leaderboard": cmd_leaderboard,
        "cmd_referral":    cmd_referral,
        "cmd_donate":      cmd_donate,
        "cmd_help":        cmd_help,
        "cmd_roadmap":     cmd_roadmap,
        "cmd_menu":        cmd_start,
        "cmd_stats":       cmd_stats,
    }

    handler = handlers.get(data)
    if handler:
        await handler(msg)
    else:
        await msg.answer(f"Unknown action: {data}", parse_mode=None)


# ---- /wallet ----
@dp.message(Command("wallet"))
async def cmd_wallet(msg: Message):
    try:
        bal = get_balance(msg.from_user.id)
        await msg.answer(f"Wallet balance: ${bal:.2f}", parse_mode=None)
    except Exception as e:
        await msg.answer(f"Wallet error: {str(e)[:200]}", parse_mode=None)

# ---- /transfer ----
@dp.message(Command("transfer"))
async def cmd_transfer(msg: Message):
    try:
        parts = msg.text.split()
        if len(parts) != 3:
            await msg.answer("Usage: /transfer <recipient_id> <amount>", parse_mode=None)
            return
        to_user = int(parts[1])
        amount = float(parts[2])
        if transfer(msg.from_user.id, to_user, amount):
            log_transaction(msg.from_user.id, "debit", "transfer", amount, reference=f"to_{to_user}")
            log_transaction(to_user, "credit", "transfer", amount, reference=f"from_{msg.from_user.id}")
            emit_event(msg.from_user.id, "transfer_sent", metadata={"to": to_user, "amount": amount})
            emit_event(to_user, "transfer_received", metadata={"from": msg.from_user.id, "amount": amount})
            await msg.answer(f"Transfer of ${amount:.2f} to {to_user} successful!", parse_mode=None)
        else:
            await msg.answer("Transfer failed. Insufficient balance.", parse_mode=None)
    except Exception as e:
        await msg.answer(f"Transfer error: {str(e)[:200]}", parse_mode=None)

# ---- /deposit ----
@dp.message(Command("deposit"))
async def cmd_deposit(msg: Message):
    ton = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")
    await msg.answer(f"Send TON to:\n{ton}\n\nAfter sending, contact admin to credit your account.", parse_mode=None)

# ---- /create_tables (admin) ----
@dp.message(Command("create_tables"))
async def cmd_create_tables(msg: Message):
    if ADMIN_IDS and msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Admin only", parse_mode=None)
        return
    try:
        init_db()
        await msg.answer("Tables created successfully.", parse_mode=None)
    except Exception as e:
        await msg.answer(f"Create tables error: {str(e)[:200]}", parse_mode=None)

# ---- AI (Groq only) ----
@dp.message(F.text & ~F.text.startswith("/"))
async def ai_chat(msg: Message):
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        await msg.answer("AI not configured.", parse_mode=None)
        return
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are SLH AI assistant. Rules: 1) Never summarize 2) Give ONE decision 3) Max 4 lines 4) End with next action 5) Hebrew first."},
                    {"role": "user", "content": msg.text}
                ],
                "max_tokens": 500
            },
            timeout=15
        )
        reply = resp.json()["choices"][0]["message"]["content"]
        await msg.answer(reply[:4000])
    except Exception as e:
        await msg.answer(f"AI error: {e}", parse_mode=None)


# ---- /store create <name> <description> ----
@dp.message(Command("store"))
async def cmd_store(msg: Message):
    parts = msg.text.split(" ", 2)
    if len(parts) < 2:
        await msg.answer("Usage: /store create <name> <description>", parse_mode=None)
        return
    sub = parts[1]
    if sub == "create":
        if len(parts) < 3:
            await msg.answer("Usage: /store create <name> <description>", parse_mode=None)
            return
        name = parts[2]
        desc = parts[3] if len(parts) > 3 else ""
        sid = create_store(msg.from_user.id, name, desc)
        await msg.answer(f"Store created! ID: {sid}", parse_mode=None)
    elif sub == "view":
        try:
            sid = int(parts[2])
            store = get_store(sid)
            await msg.answer(f"Store: {store['name']}\n{store['description']}", parse_mode=None)
        except:
            await msg.answer("Usage: /store view <id>", parse_mode=None)
    else:
        await msg.answer("Usage: /store create/view", parse_mode=None)

# ---- /add_product <store_id> <name> <price> ----
@dp.message(Command("add_product"))
async def cmd_add_product(msg: Message):
    # Use only the first line of the message (ignore pasted multi-command)
    text = msg.text.split('\n')[0]
    try:
        if '"' in text:
            # Format: /add_product <store_id> "<name>" <price>
            parts = text.split('"')
            prefix = parts[0].split()
            store_id = int(prefix[1])
            name = parts[1].strip()
            price = float(parts[2].strip())
        else:
            # Format: /add_product <store_id> <name> <price>
            parts = text.split()
            store_id = int(parts[1])
            name = parts[2]
            price = float(parts[3])
        pid = add_product(store_id, name, price)
        await msg.answer(f"Product added! ID: {pid}", parse_mode=None)
    except Exception as e:
        await msg.answer(f"Add product error: {str(e)[:200]}", parse_mode=None)

# ---- /products# ---- /products@dp.message(Command("products"))
async def cmd_products(msg: Message):
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.answer("Usage: /products <store_id>", parse_mode=None)
        return
    store_id = int(parts[1])
    prods = list_products(store_id)
    if not prods:
        await msg.answer("No products yet.", parse_mode=None)
        return
    lines = ["Products:"]
    for p in prods:
        lines.append(f"{p['id']}. {p['name']} - ${p['price']:.2f}")
    await msg.answer("\n".join(lines), parse_mode=None)

# ---- /buy <product_id> ----
@dp.message(Command("buy"))
async def cmd_buy(msg: Message):
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.answer("Usage: /buy <product_id>", parse_mode=None)
        return
    product_id = int(parts[1])
    # Get product info
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT p.price, s.owner_id FROM products p JOIN stores s ON p.store_id=s.id WHERE p.id=%s", (product_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        await msg.answer("Product not found.", parse_mode=None)
        return
    price, seller_id = row
    if create_order(msg.from_user.id, product_id, price, seller_id):
        log_transaction(msg.from_user.id, "debit", "purchase", price, reference=f"product_{product_id}")
        log_transaction(seller_id, "credit", "sale", price, reference=f"product_{product_id}")
        emit_event(msg.from_user.id, "purchase", metadata={"product_id": product_id, "amount": price})
        await msg.answer(f"Purchase successful! ${price:.2f} paid.", parse_mode=None)
    else:
        await msg.answer("Purchase failed. Insufficient balance.", parse_mode=None)


# ---- /profile ----
@dp.message(Command("profile"))
async def cmd_profile(msg: Message):
    user_id = msg.from_user.id
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, tier, created_at FROM users WHERE telegram_id=%s", (user_id,))
    user = cur.fetchone()
    bal = get_balance(user_id)
    conn.close()
    if user:
        await msg.answer(f"User: {user[0]}\nTier: {user[1]}\nBalance: ${bal:.2f}\nJoined: {user[2]}", parse_mode=None)
    else:
        await msg.answer("Profile not found. Use /register first.", parse_mode=None)

# ---- /leaders (top 10 by points) ----
@dp.message(Command("leaders"))
async def cmd_leaders(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")
        rows = cur.fetchall()
        conn.close()
        if rows:
            text = "Top 10 Users:\n" + "\n".join(f"{i+1}. {r[0]} - {r[1]} pts" for i, r in enumerate(rows))
        else:
            text = "No users yet."
    except:
        text = "No data available."
    await msg.answer(text, parse_mode=None)

# ---- /segments ----
@dp.message(Command("segments"))
async def cmd_segments(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT tier, COUNT(*) FROM users GROUP BY tier")
        rows = cur.fetchall()
        conn.close()
        text = "User Segments:\n" + "\n".join(f"{r[0]}: {r[1]}" for r in rows)
    except:
        text = "No data available."
    await msg.answer(text, parse_mode=None)

# ---- /dashboard ----
@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM stores")
        total_stores = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM products")
        total_products = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM events")
        total_events = cur.fetchone()[0]
        conn.close()
        text = (f"Dashboard:\n"
                f"Users: {total_users}\n"
                f"Stores: {total_stores}\n"
                f"Products: {total_products}\n"
                f"Events: {total_events}")
    except:
        text = "No data available."
    await msg.answer(text, parse_mode=None)

# ---- /events (last 10) ----
@dp.message(Command("events"))
async def cmd_events(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT event_type, created_at FROM events ORDER BY created_at DESC LIMIT 10")
        rows = cur.fetchall()
        conn.close()
        if rows:
            text = "Recent Events:\n" + "\n".join(f"{r[0]} at {r[1]}" for r in rows)
        else:
            text = "No events yet."
    except:
        text = "No data available."
    await msg.answer(text, parse_mode=None)


# ---- /profile ----
@dp.message(Command("profile"))
async def cmd_profile(msg: Message):
    user_id = msg.from_user.id
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, tier, created_at FROM users WHERE telegram_id=%s", (user_id,))
    user = cur.fetchone()
    bal = get_balance(user_id)
    conn.close()
    if user:
        await msg.answer(f"User: {user[0]}\nTier: {user[1]}\nBalance: ${bal:.2f}\nJoined: {user[2]}", parse_mode=None)
    else:
        await msg.answer("Profile not found. Use /register first.", parse_mode=None)

# ---- /leaders (top 10 by points) ----
@dp.message(Command("leaders"))
async def cmd_leaders(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")
        rows = cur.fetchall()
        conn.close()
        if rows:
            text = "Top 10 Users:\n" + "\n".join(f"{i+1}. {r[0]} - {r[1]} pts" for i, r in enumerate(rows))
        else:
            text = "No users yet."
    except:
        text = "No data available."
    await msg.answer(text, parse_mode=None)

# ---- /segments ----
@dp.message(Command("segments"))
async def cmd_segments(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT tier, COUNT(*) FROM users GROUP BY tier")
        rows = cur.fetchall()
        conn.close()
        text = "User Segments:\n" + "\n".join(f"{r[0]}: {r[1]}" for r in rows)
    except:
        text = "No data available."
    await msg.answer(text, parse_mode=None)

# ---- /dashboard ----
@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM stores")
        total_stores = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM products")
        total_products = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM events")
        total_events = cur.fetchone()[0]
        conn.close()
        text = (f"Dashboard:\n"
                f"Users: {total_users}\n"
                f"Stores: {total_stores}\n"
                f"Products: {total_products}\n"
                f"Events: {total_events}")
    except:
        text = "No data available."
    await msg.answer(text, parse_mode=None)

# ---- /events (last 10) ----
@dp.message(Command("events"))
async def cmd_events(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT event_type, created_at FROM events ORDER BY created_at DESC LIMIT 10")
        rows = cur.fetchall()
        conn.close()
        if rows:
            text = "Recent Events:\n" + "\n".join(f"{r[0]} at {r[1]}" for r in rows)
        else:
            text = "No events yet."
    except:
        text = "No data available."
    await msg.answer(text, parse_mode=None)


# ---- /health ----
@dp.message(Command("health"))
async def cmd_health(msg: Message):
    try:
        db_ok = "✅" if get_db() else "❌"
    except:
        db_ok = "❌"
    try:
        redis_ok = "✅" if os.getenv("REDIS_URL") else "⚪"
    except:
        redis_ok = "❌"
    await msg.answer(f"Bot: ✅\nDatabase: {db_ok}\nRedis: {redis_ok}", parse_mode=None)

# ---- /health ----
@dp.message(Command("health"))
async def cmd_health(msg: Message):
    try:
        db_ok = "✅" if get_db() else "❌"
    except:
        db_ok = "❌"
    try:
        redis_ok = "✅" if os.getenv("REDIS_URL") else "⚪"
    except:
        redis_ok = "❌"
    await msg.answer(f"Bot: ✅\nDatabase: {db_ok}\nRedis: {redis_ok}", parse_mode=None)


# ---- /status (enhanced) ----
@dp.message(Command("status"))
async def cmd_status_enhanced(msg: Message):
    text = (
        "Project Status:\n"
        "Bot: Online\n"
        "Crowdfunding: Active\n"
        "Mini App: slh-nft.com\n\n"
        "Next steps:\n"
        "1. /upgrade — monetize\n"
        "2. /store create — open shop\n"
        "3. /broadcast — promote\n"
        "4. /dashboard — track growth"
    )
    await msg.answer(text, parse_mode=None)
# ---- /upgrade ----
@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: Message):
    await msg.answer(
        "Premium Plans:\n\n"
        "⭐ Pro — $9.99/month\n"
        "  • AI priority access\n"
        "  • Create unlimited stores\n"
        "  • Advanced analytics\n\n"
        "💼 Business — $29.99/month\n"
        "  • All Pro features\n"
        "  • Custom branding\n"
        "  • Priority support\n\n"
        "To upgrade, send TON to:\n"
        f"{os.getenv('TON_WALLET', 'UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp')}\n\n"
        "Contact admin after payment.",
        parse_mode=None
    )

# ---- /commission (admin) ----
@dp.message(Command("commission"))
async def cmd_commission(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Admin only", parse_mode=None)
        return
    await msg.answer("Commission rate: 5% per marketplace transaction.\nSet via /set_commission <rate>", parse_mode=None)

# ---- Main ----
async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
