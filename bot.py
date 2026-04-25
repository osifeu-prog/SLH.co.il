import logging
import os
import sys
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

BOT_START_TIME = datetime.utcnow()

# Fix for event loop on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

def _serve_static_and_exit():
    # Fallback for Railway services that deploy this repo without TELEGRAM_BOT_TOKEN
    # (e.g. the SLH.co.il service, which is meant to serve the website, not run the bot).
    # Without this fallback, those services crash-loop because railway.json's startCommand
    # is shared across all services in the project.
    import http.server
    import socketserver
    port = int(os.getenv('PORT', '8080'))
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')
    if not os.path.isdir(docs_dir):
        logger.error("No TELEGRAM_BOT_TOKEN and docs/ not present — cannot fall back to static serve")
        sys.exit(1)
    os.chdir(docs_dir)
    handler = http.server.SimpleHTTPRequestHandler
    logger.info(f"TELEGRAM_BOT_TOKEN not set — serving {docs_dir} on :{port}")
    with socketserver.TCPServer(('', port), handler) as httpd:
        httpd.serve_forever()

if not TOKEN:
    _serve_static_and_exit()
if not DATABASE_URL:
    logger.error("DATABASE_URL not set")
    sys.exit(1)

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    # Schema matches the existing production database on Railway.
    # first_seen and feedback.timestamp are TEXT (ISO-8601) for legacy compatibility.
    conn = None
    cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_seen TEXT,
                is_admin BOOLEAN DEFAULT FALSE
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS roi_records (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                roi_percentage FLOAT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                user_id TEXT,
                username TEXT,
                message TEXT,
                timestamp TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS preorders (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                username TEXT,
                first_name TEXT,
                product TEXT,
                source TEXT,
                status TEXT DEFAULT 'interested',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Mining ledger — tracks 2 SLH utility reward earned via Guardian device operation.
        # NOT a token sale. Reward accrues over 90 days of device uptime post-launch (7.11.2026).
        # See CLAUDE.md rule #2 + docs/SIG_STATISTICAL_DEFENSE.md for the legal/economic framing.
        cur.execute('''
            CREATE TABLE IF NOT EXISTS device_mining (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                device_serial TEXT UNIQUE,
                slh_earned NUMERIC(18,8) DEFAULT 0,
                slh_target NUMERIC(18,8) DEFAULT 2.0,
                mining_started_at TIMESTAMP,
                mining_ends_at TIMESTAMP,
                last_heartbeat_at TIMESTAMP,
                status TEXT DEFAULT 'pending_shipment',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"DB init error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# Menu functions
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 ROI", callback_data="menu_roi"),
         InlineKeyboardButton("💬 משוב", callback_data="menu_feedback")],
        [InlineKeyboardButton("📊 סטטוס", callback_data="menu_status"),
         InlineKeyboardButton("🤖 AI", callback_data="menu_ai")],
        [InlineKeyboardButton("📚 תיעוד", callback_data="menu_docs"),
         InlineKeyboardButton("👑 מנהלים", callback_data="menu_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Command handlers
def _save_preorder(user, product: str, source: str) -> int:
    """Insert pre-order interest, return row id. Idempotent by (user_id, product)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id FROM preorders WHERE user_id = %s AND product = %s",
            (user.id, product),
        )
        existing = cur.fetchone()
        if existing:
            return existing[0]
        cur.execute(
            "INSERT INTO preorders (user_id, username, first_name, product, source) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (user.id, user.username, user.first_name, product, source),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    finally:
        cur.close()
        conn.close()

async def _reply_guardian_preorder(update, user, source: str):
    pid = _save_preorder(user, "guardian", source)
    await update.message.reply_text(
        "🛡️ *SLH Guardian — שריון מקום*\n\n"
        f"קיבלנו את העניין שלך (רישום #{pid}).\n\n"
        "📦 מכשיר הדגל — ₪888 ב-early bird (99 ראשונים)\n"
        "🪙 *בונוס:* 2 SLH mining reward (90 ימי הפעלה)\n"
        "📊 Target 65% APY · SIG-validated · forward-looking\n"
        "📅 שחרור רשמי: 7.11.2026\n\n"
        "נחזור אליך תוך 24 שעות עם פרטי תשלום ומשלוח.\n"
        "שאלות דחופות? @osifeu_prog\n\n"
        "_2 SLH = utility reward הנחצב דרך הפעלת המכשיר, לא רכישת טוקנים. "
        "Target APY = forward-looking projection, לא הבטחה._",
        parse_mode='Markdown'
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    now_iso = datetime.utcnow().isoformat()
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO users (user_id, username, first_seen)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET username = EXCLUDED.username
        ''', (user.id, user.username, now_iso))
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving user: {e}")
    finally:
        cur.close()
        conn.close()

    # Deep-link from slh.co.il/guardian.html → t.me/SLH_macro_bot?start=guardian
    if context.args and context.args[0] == "guardian":
        await _reply_guardian_preorder(update, user, source="deeplink")
        return

    await update.message.reply_text(
        f"🤖 Welcome {user.first_name}!\n\n"
        f"Send /menu to see all commands"
    )

async def preorder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _reply_guardian_preorder(update, update.effective_user, source="command")

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Public command — quick pulse of the bot + DB."""
    up = datetime.utcnow() - BOT_START_TIME
    hours, rem = divmod(int(up.total_seconds()), 3600)
    minutes, seconds = divmod(rem, 60)
    uptime = f"{hours}h {minutes}m {seconds}s"
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        users_total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM preorders")
        preorders_total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM roi_records")
        roi_total = cur.fetchone()[0]
        db_ok = True
    except Exception as e:
        users_total = preorders_total = roi_total = -1
        db_ok = False
        db_err = str(e)
    finally:
        cur.close()
        conn.close()

    lines = [
        "🩺 *Bot Health*",
        "",
        f"⏱ uptime: `{uptime}`",
        f"💾 DB: {'✅ ok' if db_ok else '❌ ' + db_err}",
        f"👥 users: `{users_total}`",
        f"🛡 preorders: `{preorders_total}`",
        f"📊 roi_records: `{roi_total}`",
    ]
    await update.message.reply_text("\n".join(lines), parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only: 7-day window summary."""
    user_id = update.effective_user.id
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT is_admin FROM users WHERE user_id = %s', (user_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            await update.message.reply_text("❌ Admin only.")
            return

        week_cutoff_iso = (datetime.utcnow() - timedelta(days=7)).isoformat()
        cur.execute(
            "SELECT COUNT(*) FROM users WHERE first_seen IS NOT NULL AND first_seen >= %s",
            (week_cutoff_iso,)
        )
        new_users_7d = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM roi_records WHERE created_at >= NOW() - INTERVAL '7 days'"
        )
        roi_7d = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM feedback WHERE timestamp IS NOT NULL AND timestamp >= %s",
            (week_cutoff_iso,)
        )
        fb_7d = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM preorders WHERE created_at >= NOW() - INTERVAL '7 days'"
        )
        preorders_7d = cur.fetchone()[0]
        cur.execute(
            "SELECT status, COUNT(*) FROM preorders GROUP BY status ORDER BY status"
        )
        preorder_status = cur.fetchall()

        lines = [
            "📈 *7-Day Stats*",
            "",
            f"👥 new users: `{new_users_7d}`",
            f"💰 ROI entries: `{roi_7d}`",
            f"💬 feedback: `{fb_7d}`",
            f"🛡 preorders: `{preorders_7d}`",
            "",
            "*Preorder pipeline:*",
        ]
        if preorder_status:
            for status_name, count in preorder_status:
                lines.append(f"  • {status_name}: `{count}`")
        else:
            lines.append("  _(empty)_")
        await update.message.reply_text("\n".join(lines), parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

async def mining_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Public command — shows the user how much SLH their Guardian device has mined.

    Legal framing (CLAUDE.md rule #2): SLH is a utility reward earned via device
    operation, NOT a token sale. The ₪888 pre-order pays for hardware. Display
    must always reference SIG methodology and forward-looking disclaimer.
    """
    user_id = update.effective_user.id
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT device_serial, slh_earned, slh_target, status, "
            "mining_started_at, mining_ends_at "
            "FROM device_mining WHERE user_id = %s "
            "ORDER BY created_at DESC",
            (user_id,)
        )
        rows = cur.fetchall()
        if not rows:
            await update.message.reply_text(
                "🪙 *2 SLH Mining — לא נמצאו מכשירים*\n\n"
                "אין לך מכשיר Guardian רשום עדיין.\n\n"
                "📦 שריין מקום ב-early bird: /preorder\n"
                "🔗 פרטים: https://www.slh.co.il/guardian.html\n\n"
                "_2 SLH הוא utility reward הנחצב דרך הפעלת המכשיר — לא רכישת טוקנים._",
                parse_mode='Markdown'
            )
            return

        lines = ["🪙 *Mining Status — המכשירים שלך*", ""]
        total_earned = 0
        total_target = 0
        for r in rows:
            serial, earned, target, status, started, ends = r
            earned = float(earned or 0)
            target = float(target or 2.0)
            total_earned += earned
            total_target += target
            pct = (earned / target * 100) if target else 0
            bar_len = 20
            filled = int(pct / 5)
            bar = '█' * filled + '░' * (bar_len - filled)
            serial_short = (serial or "TBD")[:12]
            lines.append(f"📟 `{serial_short}` · {status}")
            lines.append(f"   `{bar}` {earned:.4f} / {target:.2f} SLH ({pct:.1f}%)")
            if started:
                lines.append(f"   ⏱ התחלה: {started.strftime('%Y-%m-%d')}")
            if ends:
                lines.append(f"   🏁 סיום: {ends.strftime('%Y-%m-%d')}")
            lines.append("")

        lines.append(f"*סה\"כ: {total_earned:.4f} / {total_target:.2f} SLH*")
        lines.append("")
        lines.append("📊 *Target 65% APY · SIG-validated · σ=0.0049%*")
        lines.append("_Forward-looking projection, not guaranteed. See /sig._")
        await update.message.reply_text("\n".join(lines), parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

async def sig_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Public command — explains the SIG methodology + Target 65% APY framing."""
    text = (
        "📊 *SIG — Signal Information Gain*\n\n"
        "מתודולוגיה סטטיסטית מאחורי היעד הכלכלי של SLH:\n\n"
        "`APY_target = σ × √t × SIG × growth_factor`\n\n"
        "🎯 *Target: 65% APY* (forward-looking, לא מובטח)\n"
        "📐 σ = 0.0049% (פי 4.9 ממודל ללא SIG)\n"
        "🔬 SIG-validated על נתוני backtest\n\n"
        "*למה 65% הוא ראלי לעסק חדש?* — צמיחה אופיינית "
        "של עסק בשלב 0→1 + עוצמת הסיגנל = יעד defensible מתמטית.\n\n"
        "📄 מסמך מלא: https://www.slh.co.il/SIG_STATISTICAL_DEFENSE.md\n\n"
        "⚠️ _Forward-looking projection. ביצועי עבר אינם מבטיחים "
        "ביצועים עתידיים. לא הבטחת תשואה, לא ייעוץ השקעות, "
        "לא הצעה ציבורית._"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def preorders_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only: list pending pre-orders."""
    user_id = update.effective_user.id
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT is_admin FROM users WHERE user_id = %s', (user_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            await update.message.reply_text("❌ Admin only.")
            return
        cur.execute(
            "SELECT id, user_id, username, first_name, product, status, created_at "
            "FROM preorders ORDER BY created_at DESC LIMIT 50"
        )
        rows = cur.fetchall()
        if not rows:
            await update.message.reply_text("📋 אין הזמנות מוקדמות עדיין.")
            return
        lines = ["📋 *הזמנות מוקדמות (אחרונות 50):*", ""]
        for r in rows:
            pid, uid, uname, fname, product, status, ts = r
            uname_s = f"@{uname}" if uname else (fname or str(uid))
            lines.append(f"`#{pid}` {uname_s} · {product} · {status} · {ts.strftime('%Y-%m-%d %H:%M')}")
        await update.message.reply_text("\n".join(lines), parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔷 **SLH Macro System - תפריט ראשי** 🔷\n\nבחר אפשרות:",
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM users')
        user_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM roi_records')
        roi_count = cur.fetchone()[0]
        await update.message.reply_text(
            f"✅ System Online\n\n"
            f"👥 Users: {user_count}\n"
            f"💰 ROI Records: {roi_count}\n"
            f"🤖 Bot: Active"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

async def add_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /add_roi 15.5 [description]")
        return
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT is_admin FROM users WHERE user_id = %s', (user_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            await update.message.reply_text("❌ Admin only. Use /make_me_admin first")
            return
        roi = float(context.args[0])
        desc = ' '.join(context.args[1:]) if len(context.args) > 1 else "No description"
        cur.execute('''
            INSERT INTO roi_records (user_id, roi_percentage, description)
            VALUES (%s, %s, %s)
        ''', (user_id, roi, desc))
        conn.commit()
        await update.message.reply_text(f"✅ ROI {roi}% added!\n📝 {desc}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

async def last_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT roi_percentage, description, created_at FROM roi_records ORDER BY created_at DESC LIMIT 1')
        record = cur.fetchone()
        if record:
            await update.message.reply_text(f"📊 Last ROI: {record['roi_percentage']}%\n📝 {record['description']}")
        else:
            await update.message.reply_text("No ROI records")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

def _save_feedback(user, tagged_message: str):
    """Insert feedback row with all columns populated (matches prod schema)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO feedback (user_id, username, message, timestamp) VALUES (%s, %s, %s, %s)",
            (
                str(user.id),
                user.username or "no_username",
                tagged_message,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

async def feedback_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /feedback_ai [your feedback]")
        return
    msg = ' '.join(context.args)
    try:
        _save_feedback(update.effective_user, f"[AI] {msg}")
        await update.message.reply_text("✅ Feedback received!\n\n📝 Thank you for your input!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /suggest [your idea]")
        return
    idea = ' '.join(context.args)
    try:
        _save_feedback(update.effective_user, f"[IDEA] {idea}")
        await update.message.reply_text("✅ Thank you! Your idea has been saved.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /report [issue description]")
        return
    issue = ' '.join(context.args)
    try:
        _save_feedback(update.effective_user, f"[BUG] {issue}")
        await update.message.reply_text("✅ Issue reported. We'll handle it soon.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def summary_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # first_seen / feedback.timestamp are ISO-8601 text columns; cast to timestamp before DATE().
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM users "
            "WHERE first_seen IS NOT NULL AND first_seen::timestamp::date = CURRENT_DATE"
        )
        new_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM roi_records WHERE DATE(created_at) = CURRENT_DATE")
        today_roi = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM feedback "
            "WHERE timestamp IS NOT NULL AND timestamp::timestamp::date = CURRENT_DATE"
        )
        today_fb = cur.fetchone()[0]
        await update.message.reply_text(
            f"📊 **Daily Summary**\n\n"
            f"👥 New users: {new_users}\n"
            f"💰 ROI records: {today_roi}\n"
            f"💬 Feedback: {today_fb}",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        cur.close()
        conn.close()

async def roadmap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roadmap_text = """🗺️ **SLH.co.il Roadmap**

✅ **Completed:**
• Telegram bot
• PostgreSQL DB
• ROI system
• Admin rights

🚧 **In Progress:**
• AI feedback analysis
• Monitor dashboard

📅 **Future:**
• Web app
• Public API
• Slack integration"""
    await update.message.reply_text(roadmap_text, parse_mode='Markdown')

async def docs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Commands wrapped in backticks so Markdown doesn't strip the underscores
    # (Telegram legacy Markdown treats _word_ as italic; backticks = code span, no parsing).
    docs_text = """📚 **SLH.co.il Documentation**

📖 **Commands:**
`/menu` - Main menu
`/status` - System status
`/health` - Bot health + DB
`/stats` - 7-day stats (admin)
`/preorder` - שריון Guardian early bird
`/mining_status` - 2 SLH Mining status (Guardian)
`/sig` - SIG methodology + Target APY
`/add_roi` - Add ROI
`/last_roi` - Last ROI
`/feedback_ai` - Smart feedback
`/suggest` - Suggest improvement
`/report` - Report issue
`/summary_today` - Daily summary
`/roadmap` - Roadmap

🌐 **Web:**
• https://www.slh.co.il
• https://www.slh.co.il/guardian.html
• https://monitor.slh.co.il"""
    await update.message.reply_text(docs_text, parse_mode='Markdown')

async def request_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    await update.message.reply_text("✅ Admin request sent. An admin will review your request.")

async def make_me_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM users WHERE is_admin = TRUE')
        admin_count = cur.fetchone()[0]
        
        if admin_count == 0:
            cur.execute('UPDATE users SET is_admin = TRUE WHERE user_id = %s', (user_id,))
            conn.commit()
            await update.message.reply_text("✅ You are now an admin! 🎉")
        else:
            await update.message.reply_text("❌ An admin already exists.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "menu_roi":
        await query.edit_message_text("💰 **ROI:**\n`/add_roi` [amount]\n`/last_roi`", parse_mode='Markdown')
    elif query.data == "menu_feedback":
        await query.edit_message_text("💬 **Feedback:**\n`/feedback_ai` [msg]\n`/suggest` [idea]\n`/report` [issue]", parse_mode='Markdown')
    elif query.data == "menu_status":
        await query.edit_message_text("📊 **Status:**\n`/status`", parse_mode='Markdown')
    elif query.data == "menu_ai":
        await query.edit_message_text("🤖 **AI:**\n`/summary_today`\n`/feedback_ai`", parse_mode='Markdown')
    elif query.data == "menu_docs":
        await query.edit_message_text("📚 **Docs:**\n`/roadmap`\n`/docs`", parse_mode='Markdown')
    elif query.data == "menu_admin":
        await query.edit_message_text("👑 **Admin:**\n`/request_admin`\n`/make_me_admin`", parse_mode='Markdown')

async def main():
    logger.info("Starting bot...")
    init_db()
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("add_roi", add_roi))
    app.add_handler(CommandHandler("last_roi", last_roi))
    app.add_handler(CommandHandler("feedback_ai", feedback_ai))
    app.add_handler(CommandHandler("suggest", suggest))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("summary_today", summary_today))
    app.add_handler(CommandHandler("roadmap", roadmap))
    app.add_handler(CommandHandler("docs", docs_cmd))
    app.add_handler(CommandHandler("request_admin", request_admin))
    app.add_handler(CommandHandler("make_me_admin", make_me_admin))
    app.add_handler(CommandHandler("preorder", preorder))
    app.add_handler(CommandHandler("preorders", preorders_list))
    app.add_handler(CommandHandler("mining_status", mining_status))
    app.add_handler(CommandHandler("mining", mining_status))
    app.add_handler(CommandHandler("sig", sig_info))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    logger.info("Bot started polling...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
