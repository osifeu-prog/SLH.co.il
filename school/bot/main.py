#!/usr/bin/env python3
"""
Crypto-Class - מערכת מלאה משולבת
גרסה 3.0.0 - מבוסס webhook בלבד, ללא polling
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# הוסף את התיקיות הנדרשות ל-PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('crypto_class.log')
    ]
)
logger = logging.getLogger(__name__)

# ========== הגדרות מערכת ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN לא מוגדר!")
    sys.exit(1)

PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip('/')
TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "admin123")
SECRET_KEY = os.environ.get("SECRET_KEY", "crypto-class-secret-key-2026-change-this")

# ========== יבוא מודולים פנימיים ==========
try:
    from database.db import ensure_database_initialized
    from database.queries import (
        get_top_users, get_system_stats, get_today_stats,
        get_streak_stats, get_activity_stats
    )
    logger.info("✅ מודולי מסד נתונים נטענו")
except ImportError as e:
    logger.error(f"❌ שגיאה בטעינת מודולי מסד נתונים: {e}")
    sys.exit(1)

# ========== יצירת Flask app ==========
flask_app = Flask(__name__)
flask_app.secret_key = SECRET_KEY

# ========== אתחול מסד נתונים ==========
def initialize_database():
    """אתחול מסד הנתונים בעת הפעלה"""
    try:
        ensure_database_initialized()
        logger.info("✅ מסד נתונים אותחל")
    except Exception as e:
        logger.error(f"❌ שגיאה באתחול מסד נתונים: {e}")

# ========== יבוא פקודות ==========
try:
    # יבוא פקודות מקובץ commands.py
    from bot.commands import (
        start, checkin, balance, referral, my_referrals,
        leaderboard, level, profile, contact, help_command, 
        website, admin_panel, add_tokens, reset_checkin,
        handle_callback_query
    )
    logger.info("✅ פקודות הבוט נטענו")
except ImportError as e:
    logger.error(f"❌ שגיאה ביבוא פקודות: {e}")
    sys.exit(1)

# ========== אתחול הבוט ==========
def setup_bot():
    """הגדרת הבוט והוספת handlers"""
    try:
        # יצירת Application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # הוספת handlers לפקודות
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("checkin", checkin))
        application.add_handler(CommandHandler("balance", balance))
        application.add_handler(CommandHandler("referral", referral))
        application.add_handler(CommandHandler("my_referrals", my_referrals))
        application.add_handler(CommandHandler("leaderboard", leaderboard))
        application.add_handler(CommandHandler("level", level))
        application.add_handler(CommandHandler("profile", profile))
        application.add_handler(CommandHandler("contact", contact))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("website", website))
        application.add_handler(CommandHandler("admin", admin_panel))
        application.add_handler(CommandHandler("add_tokens", add_tokens))
        application.add_handler(CommandHandler("reset_checkin", reset_checkin))
        
        # הוספת handler ל-callback queries
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # טיפול בשגיאות
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"שגיאה: {context.error}", exc_info=context.error)
            try:
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "❌ אירעה שגיאה. אנא נסה שוב מאוחר יותר."
                    )
            except:
                pass
        
        application.add_error_handler(error_handler)
        
        logger.info("✅ הבוט אותחל עם כל הפקודות")
        return application
    except Exception as e:
        logger.error(f"❌ שגיאה באתחול הבוט: {e}")
        return None

# אתחול הבוט
bot_app = setup_bot()

# ========== הגדרת Webhook ==========
@flask_app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """הגדרת webhook לבוט"""
    try:
        if not WEBHOOK_URL:
            return jsonify({
                "success": False,
                "message": "WEBHOOK_URL לא מוגדר בסביבה",
                "suggestion": "הגדר את WEBHOOK_URL להפעלת webhook"
            }), 400
        
        webhook_url = f"{WEBHOOK_URL}/webhook"
        
        # הגדר את webhook
        bot_app.bot.set_webhook(webhook_url)
        
        logger.info(f"✅ Webhook הוגדר: {webhook_url}")
        return jsonify({
            "success": True,
            "message": "Webhook הוגדר בהצלחה",
            "webhook_url": webhook_url
        })
    except Exception as e:
        logger.error(f"❌ שגיאה בהגדרת webhook: {e}")
        return jsonify({
            "success": False,
            "message": f"שגיאה בהגדרת webhook: {str(e)}"
        }), 500

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """נקודת כניסה ל-webhook מטלגרם"""
    try:
        if bot_app is None:
            return jsonify({"status": "error", "message": "Bot not initialized"}), 500
        
        # עיבוד העדכון
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        
        # השתמש ב-ThreadPoolExecutor כדי להריץ את ה-update
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                lambda: bot_app.update_queue.put_nowait(update)
            )
            future.result(timeout=5)
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"❌ שגיאה בעיבוד webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== דפי אתר ==========
@flask_app.route('/')
def index():
    """דף הבית"""
    try:
        stats = get_system_stats()
        bot_username = "CryptoClassBot"
        
        # קבל נתונים נוספים
        today_stats = get_today_stats()
        streak_stats = get_streak_stats()
        activity_stats = get_activity_stats()
        
        return render_template('index.html', 
                             stats=stats,
                             today_stats=today_stats,
                             streak_stats=streak_stats,
                             activity_stats=activity_stats,
                             bot_username=bot_username,
                             now=datetime.now)
    except Exception as e:
        logger.error(f"❌ שגיאה בטעינת דף הבית: {e}")
        return render_template('error.html', error="שגיאה בטעינת הדף")

@flask_app.route('/stats')
def stats_page():
    """דף סטטיסטיקות"""
    try:
        stats = get_system_stats()
        top_users = get_top_users(10, 'tokens')
        
        def intcomma(value):
            try:
                return f"{int(value):,}"
            except:
                return str(value)
        
        return render_template('stats.html', 
                             stats=stats,
                             top_users=top_users,
                             intcomma=intcomma,
                             now=datetime.now)
    except Exception as e:
        logger.error(f"❌ שגיאה בטעינת סטטיסטיקות: {e}")
        return render_template('error.html', error="שגיאה בטעינת סטטיסטיקות")

@flask_app.route('/health')
def health_check():
    """בדיקת בריאות המערכת"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "bot": "active" if bot_app else "inactive",
            "database": "connected",
            "webhook": bool(WEBHOOK_URL),
            "version": "3.0.0",
            "features": ["web", "bot", "database", "webhook"]
        }
        
        # בדיקת מסד נתונים
        try:
            from database.db import Session
            session = Session()
            session.execute("SELECT 1")
            session.close()
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        return jsonify(health_status)
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@flask_app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    """כניסת מורה"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        if password == TEACHER_PASSWORD:
            session['teacher_logged_in'] = True
            session['teacher_login_time'] = datetime.now().isoformat()
            return redirect(url_for('teacher_dashboard'))
        else:
            return render_template('teacher/teacher_login.html', 
                                 error="סיסמה שגויה")
    
    return render_template('teacher/teacher_login.html')

@flask_app.route('/teacher')
def teacher_dashboard():
    """דשבורד מורה"""
    if not session.get('teacher_logged_in'):
        return redirect(url_for('teacher_login'))
    
    try:
        stats = get_system_stats()
        top_users = get_top_users(10, 'tokens')
        
        def intcomma(value):
            try:
                return f"{int(value):,}"
            except:
                return str(value)
        
        return render_template('teacher/teacher_dashboard.html',
                             stats=stats,
                             top_users=top_users,
                             intcomma=intcomma)
    except Exception as e:
        logger.error(f"❌ שגיאה בטעינת דשבורד מורה: {e}")
        return render_template('error.html', error="שגיאה בטעינת הדשבורד")

@flask_app.route('/teacher/logout')
def teacher_logout():
    """יציאת מורה"""
    session.pop('teacher_logged_in', None)
    return redirect(url_for('index'))

# ========== הרצת המערכת ==========
def main():
    """הרצה ראשית של כל המערכת"""
    # אתחול מסד נתונים
    initialize_database()
    
    # הגדר webhook אם קיים URL
    if WEBHOOK_URL and bot_app:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        try:
            bot_app.bot.set_webhook(webhook_url)
            logger.info(f"✅ Webhook הוגדר: {webhook_url}")
        except Exception as e:
            logger.error(f"❌ שגיאה בהגדרת webhook: {e}")
    else:
        logger.warning("⚠️ WEBHOOK_URL לא מוגדר - הבוט ירוץ בפולינג מקומי")
        # הרץ polling רק במקרה שאין webhook (לפיתוח מקומי)
        if bot_app and os.environ.get('USE_POLLING', 'false').lower() == 'true':
            logger.info("🤖 מפעיל בוט בפולינג...")
            bot_app.run_polling(allowed_updates=None)
    
    # הפעלת שרת Flask
    logger.info(f"🚀 מפעיל שרת Flask על פורט {PORT}")
    logger.info(f"🌐 כתובת: http://localhost:{PORT}")
    logger.info(f"📊 בריאות מערכת: http://localhost:{PORT}/health")
    logger.info(f"🤖 Webhook: {WEBHOOK_URL or 'לא מוגדר'}")
    
    flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()

