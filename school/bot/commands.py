#!/usr/bin/env python3
"""
מודול פקודות הבוט - Crypto-Class
גרסה 2.4.0 - מלא ומאורגן עם כל הפקודות
"""

import logging
import random
import string
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.queries import (
    get_user, register_user, checkin_user, get_balance,
    get_user_referrals, get_top_users, get_level_info,
    get_total_referrals, get_or_create_referral_code,
    get_referred_users, add_tokens, update_level,
    get_system_stats, get_activity_count, get_daily_stats,
    get_today_stats, get_streak_stats, get_activity_stats,
    get_available_tasks, complete_task, get_user_attendance_history,
    get_user_activity_report, search_users, get_all_users,
    add_tokens_to_user, reset_user_checkin, get_checkin_data
)

logger = logging.getLogger(__name__)

# ========== הגדרות קבועות ==========

# בונוסים לפי יום רצוף
STREAK_BONUS = {
    3: 5,    # יום שלישי רצוף: +5 טוקנים
    7: 10,   # שבוע רצוף: +10 טוקנים
    14: 20,  # שבועיים רצופים: +20 טוקנים
    30: 50   # חודש רצוף: +50 טוקנים
}

# פרטי מנהל המערכת
ADMIN_INFO = {
    "name": "אוסיף אונגר",
    "telegram": "@osifeu",
    "phone": "0584203384",
    "email": "osif.programmer@gmail.com",
    "response_time": "24-48 שעות"
}

# ========== פונקציות עזר ==========

def generate_referral_code(user_id: int, length: int = 8) -> str:
    """יצירת קוד הפניה ייחודי"""
    base = str(user_id)[-4:] if len(str(user_id)) >= 4 else str(user_id).zfill(4)
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(length - 4))
    code = f"{base}{random_part}"
    return code[:length]

def calculate_level(tokens: int) -> int:
    """חישוב רמה לפי כמות הטוקנים"""
    level_thresholds = [0, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
    
    for level, threshold in enumerate(level_thresholds, 1):
        if tokens < threshold:
            return level - 1 if level > 1 else 1
    
    return 10

def get_level_progress(tokens: int) -> tuple:
    """קבלת התקדמות ברמה הנוכחית"""
    level = calculate_level(tokens)
    level_thresholds = [0, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
    
    current_level_min = level_thresholds[level - 1]
    next_level_min = level_thresholds[level] if level < len(level_thresholds) - 1 else float('inf')
    
    progress = tokens - current_level_min
    total_for_level = next_level_min - current_level_min
    
    return level, progress, total_for_level, next_level_min

def format_number(num: int) -> str:
    """פורמט מספר עם פסיקים"""
    return f"{num:,}".replace(",", ",")

def create_progress_bar(progress: int, total: int, length: int = 10) -> str:
    """יצירת סרגל התקדמות ויזואלי"""
    filled = int((progress / total) * length) if total > 0 else 0
    bar = "▓" * filled + "░" * (length - filled)
    percentage = (progress / total * 100) if total > 0 else 0
    return f"{bar} {percentage:.1f}%"

def get_day_name(date_str: str) -> str:
    """קבלת שם היום בעברית"""
    days = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return days[date_obj.weekday()]
    except:
        return date_str

def format_time_delta(delta: timedelta) -> str:
    """פורמט זמן בעברית"""
    if delta.days > 0:
        return f"{delta.days} ימים"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} שעות"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} דקות"
    else:
        return f"{delta.seconds} שניות"

# ========== פקודות בסיסיות ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פקודת התחלה - רישום/התחברות משתמש"""
    try:
        user = update.effective_user
        logger.info(f"🚀 קבלת /start ממשתמש: {user.id} ({user.first_name})")
        
        # בדיקת פרמטר הפניה
        referral_param = None
        if context.args:
            referral_param = context.args[0]
        
        # בדוק אם המשתמש קיים
        existing_user = get_user(user.id)
        
        if existing_user:
            # משתמש קיים - הצג הודעת ברוכים השב
            welcome_message = (
                f"🎉 **ברוך השב, {user.first_name}!** 👋\n\n"
                f"📍 כבר רשום במערכת Crypto-Class\n"
                f"📅 תאריך הצטרפות: {existing_user.created_at.strftime('%d/%m/%Y')}\n\n"
                f"📋 **פקודות זמינות:**\n"
                f"└── /checkin - צ'ק-אין יומי\n"
                f"└── /balance - יתרת טוקנים\n"
                f"└── /referral - קוד הפניה שלך\n"
                f"└── /leaderboard - טבלת מובילים\n"
                f"└── /level - הרמה שלך\n"
                f"└── /help - עזרה והדרכה\n\n"
                f"🚀 **מה עכשיו?**\n"
                f"השתמש ב-/checkin כדי לקבל את הטוקן היומי שלך!"
            )
            
            await update.message.reply_text(welcome_message, parse_mode='Markdown')
        else:
            # משתמש חדש - רשום אותו
            referral_code = generate_referral_code(user.id)
            success = register_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                referral_code=referral_code
            )
            
            if success:
                # מעקב הפניה אם קיים
                if referral_param:
                    try:
                        referrer = get_user_by_referral_code(referral_param)
                        if referrer:
                            # הוסף טוקנים למזמין
                            add_tokens_to_user(referrer.telegram_id, 10)
                            logger.info(f"🎯 משתמש {user.id} הצטרף דרך קוד הפניה של {referrer.telegram_id}")
                    except Exception as e:
                        logger.error(f"❌ שגיאה בעיבוד הפניה: {e}")
                
                logger.info(f"✅ משתמש נרשם: {user.id} עם קוד הפניה: {referral_code}")
                
                welcome_message = (
                    f"🎉 **ברוך הבא ל-Crypto-Class!** 🚀\n\n"
                    f"✅ **נרשמת בהצלחה למערכת!**\n"
                    f"└── 👤 שם: {user.first_name}\n"
                    f"└── 🆔 מזהה: {user.id}\n"
                    f"└── 📅 תאריך: {datetime.now().strftime('%d/%m/%Y')}\n"
                    f"└── 🔐 קוד הפניה: `{referral_code}`\n\n"
                    f"📋 **פקודות זמינות:**\n"
                    f"└── /checkin - צ'ק-אין יומי (מקבל טוקן)\n"
                    f"└── /balance - בדיקת יתרת טוקנים\n"
                    f"└── /referral - קוד ההפניה שלך\n"
                    f"└── /my_referrals - המוזמנים שלך\n"
                    f"└── /leaderboard - טבלת מובילים\n"
                    f"└── /level - הרמה והניסיון שלך\n\n"
                    f"💰 **מערכת הטוקנים:**\n"
                    f"└── צ'ק-אין יומי: 1 טוקן\n"
                    f"└── הזמנת חבר: 10 טוקנים\n"
                    f"└── רצף יומי: עד 50 טוקנים\n\n"
                    f"🚀 **התחל עם:**\n"
                    f"/checkin - כדי לצבור טוקנים!\n"
                    f"/referral - כדי להזמין חברים!"
                )
                
                await update.message.reply_text(welcome_message, parse_mode='Markdown')
            else:
                await update.message.reply_text(
                    "❌ **אירעה שגיאה בזמן הרישום**\n\n"
                    "אנא נסה שוב מאוחר יותר או פנה למנהל המערכת עם /contact."
                )
                
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת start: {e}")
        await update.message.reply_text(
            "❌ **שגיאה בפקודת התחלה**\n\n"
            "אנא נסה שוב או פנה למנהל המערכת עם /contact."
        )

async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """צ'ק-אין יומי - קבלת טוקן יומי"""
    try:
        user = update.effective_user
        logger.info(f"📅 קבלת /checkin ממשתמש: {user.id}")
        
        # בדוק אם המשתמש רשום
        db_user = get_user(user.id)
        if not db_user:
            await update.message.reply_text(
                "❌ **אתה לא רשום במערכת!**\n\n"
                "שלח /start כדי להירשם."
            )
            return
        
        # בצע צ'ק-אין
        success, message = checkin_user(user.id)
        
        if success:
            # קבל את היתרה המעודכנת
            balance = get_balance(user.id)
            
            # בדוק בונוסי רצף
            streak_days = getattr(db_user, 'current_streak', 0) or 0
            bonus_tokens = 0
            
            for streak_day, bonus in STREAK_BONUS.items():
                if streak_days >= streak_day and streak_days % streak_day == 0:
                    bonus_tokens = bonus
                    break
            
            response = (
                f"✅ **צ'ק-אין מוצלח!** 🎉\n\n"
                f"{message}\n\n"
                f"📊 **פרטים:**\n"
                f"└── 💰 יתרה מעודכנת: **{format_number(balance)} טוקנים** 🪙\n"
                f"└── 🔥 רצף נוכחי: {streak_days} ימים\n"
            )
            
            if bonus_tokens > 0:
                response += f"└── 🎁 בונוס רצף: +{bonus_tokens} טוקנים!\n\n"
            else:
                response += f"└── 🎯 לרמה הבאה: עוד {get_level_progress(balance)[3] - balance} טוקנים\n\n"
            
            response += (
                f"📈 **המשך להתמיד!**\n"
                f"חזור מחר ל-/checkin כדי לשמור על הרצף!"
            )
            
            # יצירת סרגל התקדמות
            level, progress, total, _ = get_level_progress(balance)
            progress_bar = create_progress_bar(progress, total)
            response += f"\n\n🏆 **רמה {level}:**\n{progress_bar}"
            
            await update.message.reply_text(response, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ **{message}**\n\nנסה שוב מחר עם /checkin!")
            
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת checkin: {e}")
        await update.message.reply_text(
            "❌ **שגיאה בצ'ק-אין**\n\n"
            "אנא נסה שוב או פנה למנהל המערכת עם /contact."
        )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """הצגת יתרת הטוקנים של המשתמש"""
    try:
        user = update.effective_user
        logger.info(f"💰 קבלת /balance ממשתמש: {user.id}")
        
        # בדוק אם המשתמש רשום
        db_user = get_user(user.id)
        if not db_user:
            await update.message.reply_text(
                "❌ **אתה לא רשום במערכת!**\n\n"
                "שלח /start כדי להירשם."
            )
            return
        
        balance = get_balance(user.id)
        level, progress, total, next_level = get_level_progress(balance)
        progress_bar = create_progress_bar(progress, total)
        
        # סטטיסטיקות נוספות
        total_referrals = get_total_referrals(user.id)
        streak_days = getattr(db_user, 'current_streak', 0) or 0
        
        response = (
            f"💰 **פרטי חשבון - {user.first_name}**\n\n"
            f"📊 **יתרה נוכחית:**\n"
            f"└── 🪙 טוקנים: **{format_number(balance)}**\n"
            f"└── 🏦 ערך כולל: **{format_number(balance * 100)} נקודות**\n\n"
            f"🏆 **רמה והתקדמות:**\n"
            f"└── 📈 רמה: {level}\n"
            f"└── 📊 התקדמות: {progress}/{total}\n"
            f"└── 🎯 עד רמה {level+1}: {next_level - balance} טוקנים\n"
            f"└── {progress_bar}\n\n"
            f"📈 **סטטיסטיקות:**\n"
            f"└── 🔥 רצף יומי: {streak_days} ימים\n"
            f"└── 👥 מוזמנים: {total_referrals}\n"
            f"└── 💰 טוקנים מהפניות: {format_number(total_referrals * 10)}\n\n"
            f"💡 **טיפ:** השתמש ב-/checkin כל יום כדי לשמור על הרצף ולקבל בונוסים!"
        )
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת balance: {e}")
        await update.message.reply_text(
            "❌ **שגיאה בבדיקת יתרה**\n\n"
            "אנא נסה שוב מאוחר יותר."
        )

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """הצגת קוד ההפניה של המשתמש"""
    try:
        user = update.effective_user
        logger.info(f"📱 קבלת /referral ממשתמש: {user.id}")
        
        # בדוק אם המשתמש רשום
        db_user = get_user(user.id)
        if not db_user:
            await update.message.reply_text(
                "❌ **אתה לא רשום במערכת!**\n\n"
                "שלח /start כדי להירשם."
            )
            return
        
        referral_code = db_user.referral_code
        total_referrals = get_total_referrals(user.id)
        
        # בניית קישור הפניה
        bot_username = context.bot.username
        referral_link = f"https://t.me/{bot_username}?start={referral_code}"
        
        response = (
            f"👤 **קוד ההפניה שלך**\n\n"
            f"📱 **קוד אישי:**\n"
            f"`{referral_code}`\n\n"
            f"🔗 **קישור להזמנה:**\n"
            f"`{referral_link}`\n\n"
            f"📊 **סטטיסטיקות הפניות:**\n"
            f"└── 👥 משתמשים שהזמנת: **{total_referrals}**\n"
            f"└── 💰 טוקנים שהרווחת: **{format_number(total_referrals * 10)}**\n"
            f"└── 🎯 יעד הבא: 5 חברים (50 טוקנים)\n\n"
            f"📚 **איך להזמין חברים:**\n"
            f"1. שלח לחבר את הקישור למעלה\n"
            f"2. או בקש ממנו לשלוח: /start {referral_code}\n"
            f"3. קבל 10 טוקנים על כל חבר שמצטרף!\n\n"
            f"💡 **טיפ:** שתף בקבוצות לימוד לקבל יותר הפניות!"
        )
        
        # יצירת כפתורי שיתוף
        keyboard = [
            [
                InlineKeyboardButton("📤 שתף קישור", url=f"tg://msg?text={referral_link}"),
                InlineKeyboardButton("📊 המוזמנים שלי", callback_data="my_referrals")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            response, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת referral: {e}")
        await update.message.reply_text(
            "❌ **שגיאה בהצגת קוד הפניה**\n\n"
            "אנא נסה שוב מאוחר יותר."
        )

async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """הצגת רשימת המוזמנים של המשתמש"""
    try:
        user = update.effective_user
        logger.info(f"👥 קבלת /my_referrals ממשתמש: {user.id}")
        
        # בדוק אם המשתמש רשום
        db_user = get_user(user.id)
        if not db_user:
            await update.message.reply_text(
                "❌ **אתה לא רשום במערכת!**\n\n"
                "שלח /start כדי להירשם."
            )
            return
        
        # קבל את המוזמנים
        referrals = get_referred_users(user.id)
        total_referrals = get_total_referrals(user.id)
        
        if not referrals:
            response = (
                f"📊 **סטטיסטיקות הפניות של {user.first_name}**\n\n"
                f"👥 **מוזמנים:** 0\n"
                f"💰 **טוקנים מהפניות:** 0\n"
                f"🎯 **יעד הבא:** הזמן חבר אחד (10 טוקנים)\n\n"
                f"📱 **עדיין לא הזמנת חברים.**\n"
                f"השתמש ב-/referral כדי לקבל את קוד ההפניה שלך!\n\n"
                f"💡 כל חבר מזמין שווה 10 טוקנים!"
            )
        else:
            # סטטיסטיקות מפורטות
            today = datetime.now().date()
            recent_referrals = 0
            for ref in referrals:
                if ref.created_at and ref.created_at.date() == today:
                    recent_referrals += 1
            
            response = (
                f"📊 **סטטיסטיקות הפניות של {user.first_name}**\n\n"
                f"👥 **סך הכל מוזמנים:** {total_referrals}\n"
                f"💰 **טוקנים מהפניות:** {format_number(total_referrals * 10)}\n"
                f"📈 **הוזמנו היום:** {recent_referrals}\n\n"
                f"📋 **רשימת המוזמנים:**\n"
            )
            
            # הצגת 5 מוזמנים אחרונים
            for i, ref in enumerate(referrals[:5], 1):
                name = ref.first_name or ref.username or f"משתמש {ref.telegram_id}"
                ref_date = ref.created_at.strftime('%d/%m/%Y') if ref.created_at else "תאריך לא ידוע"
                days_ago = ""
                
                if ref.created_at:
                    delta = today - ref.created_at.date()
                    if delta.days == 0:
                        days_ago = "היום"
                    elif delta.days == 1:
                        days_ago = "אתמול"
                    else:
                        days_ago = f"לפני {delta.days} ימים"
                
                response += f"{i}. {name} - {ref_date} ({days_ago})\n"
            
            if len(referrals) > 5:
                response += f"\n... ועוד {len(referrals) - 5} מוזמנים"
            
            response += "\n\n💡 **הזמן עוד חברים וקבל עוד טוקנים!**"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת my_referrals: {e}")
        await update.message.reply_text(
            "❌ **שגיאה בהצגת המוזמנים**\n\n"
            "אנא נסה שוב מאוחר יותר."
        )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טבלת המובילים - המשתמשים עם הכי הרבה טוקנים"""
    try:
        user = update.effective_user
        logger.info(f"🏆 קבלת /leaderboard ממשתמש: {user.id}")
        
        # קבל את המובילים (Top 10)
        top_users = get_top_users(limit=10, order_by='tokens')
        
        if not top_users:
            response = (
                "🏆 **טבלת המובילים**\n\n"
                "אין עדיין נתונים. היה הראשון שצובר טוקנים! 💪\n\n"
                "🚀 שלח /checkin כדי להתחיל לצבור טוקנים!"
            )
        else:
            response = "🏆 **טבלת המובילים - Top 10**\n\n"
            
            # סמלים לפי מיקום
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            
            for i, top_user in enumerate(top_users[:10], 0):
                name = top_user.first_name or top_user.username or f"משתמש {top_user.telegram_id}"
                
                # קיצור שם אם ארוך מדי
                if len(name) > 15:
                    name = name[:12] + "..."
                
                # סמל מיוחד אם זה המשתמש הנוכחי
                user_indicator = " 👈" if top_user.telegram_id == user.id else ""
                
                response += f"{medals[i] if i < 10 else str(i+1)+'.'} {name}: {format_number(top_user.tokens)} טוקנים{user_indicator}\n"
            
            # הוסף את המיקום של המשתמש הנוכחי
            all_users = get_top_users(limit=100, order_by='tokens')
            user_position = None
            user_tokens = 0
            
            for i, u in enumerate(all_users, 1):
                if u.telegram_id == user.id:
                    user_position = i
                    user_tokens = u.tokens
                    break
            
            if user_position:
                response += f"\n📊 **המיקום שלך:** #{user_position} עם {format_number(user_tokens)} טוקנים\n"
                
                # הצעה לשיפור מיקום
                if user_position > 10:
                    users_ahead = all_users[9]  # המשתמש במקום ה-10
                    tokens_needed = users_ahead.tokens - user_tokens + 1
                    response += f"🎯 **ל-Top 10 חסרים:** {format_number(tokens_needed)} טוקנים\n"
            
            response += "\n💪 **התחרה עם החברים וטפס למעלה!**"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת leaderboard: {e}")
        await update.message.reply_text(
            "❌ **שגיאה בטבלת המובילים**\n\n"
            "אנא נסה שוב מאוחר יותר."
        )

async def level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """הצגת הרמה וההתקדמות של המשתמש"""
    try:
        user = update.effective_user
        logger.info(f"🏅 קבלת /level ממשתמש: {user.id}")
        
        # בדוק אם המשתמש רשום
        db_user = get_user(user.id)
        if not db_user:
            await update.message.reply_text(
                "❌ **אתה לא רשום במערכת!**\n\n"
                "שלח /start כדי להירשם."
            )
            return
        
        balance = get_balance(user.id)
        level, progress, total, next_level = get_level_progress(balance)
        progress_bar = create_progress_bar(progress, total)
        
        # קבל מידע על הרמה
        level_info = get_level_info(level)
        next_level_info = get_level_info(level + 1) if level < 10 else None
        
        # סטטיסטיקות נוספות
        total_users = get_system_stats().get('total_users', 0)
        activity_today = get_activity_count()
        streak_days = getattr(db_user, 'current_streak', 0) or 0
        
        response = (
            f"🏆 **פרופיל משתמש - {user.first_name}**\n\n"
            f"📊 **נתונים כלליים:**\n"
            f"└── 💰 טוקנים: **{format_number(balance)}**\n"
            f"└── 🏅 רמה נוכחית: **{level}**\n"
            f"└── 🔥 רצף יומי: **{streak_days} ימים**\n\n"
            f"📈 **התקדמות ברמה:**\n"
            f"└── {progress_bar}\n"
            f"└── 📊 התקדמות: {progress}/{total} טוקנים\n"
            f"└── 🎯 עד לרמה {level+1}: {next_level - balance} טוקנים\n\n"
        )
        
        # תיאור הרמה הנוכחית
        if level_info:
            response += f"📋 **רמה {level}:** {level_info.get('description', '')}\n\n"
        
        # מידע על הרמה הבאה
        if next_level_info:
            response += f"🚀 **רמה {level+1}:** {next_level_info.get('description', '')}\n\n"
        
        # הוסף מוטיבציה לפי הרמה
        if level < 3:
            response += "🌱 **מתחיל** - עבודה טובה! כל יום צ'ק-אין מקרב אותך לרמה הבאה.\n"
        elif level < 6:
            response += "🚀 **מתקדם** - מעולה! אתה בדרך להצלחה.\n"
        elif level < 9:
            response += "💎 **מנוסה** - מדהים! אתה אחד המובילים.\n"
        else:
            response += "👑 **אלוף** - פנטסטי! אתה בפסגה.\n"
        
        response += (
            f"\n📊 **סטטיסטיקות מערכת:**\n"
            f"└── 👥 משתמשים רשומים: {format_number(total_users)}\n"
            f"└── 📈 פעילים היום: {activity_today}\n"
            f"└── 🏆 המיקום שלך: #{get_user_rank(user.id)}\n\n"
            f"💪 **השתמש ב-/checkin כל יום כדי להתקדם!**"
        )
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת level: {e}")
        await update.message.reply_text(
            "❌ **שגיאה בהצגת הרמה**\n\n"
            "אנא נסה שוב מאוחר יותר."
        )

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """הצגת פרופיל מלא של המשתמש"""
    try:
        user = update.effective_user
        logger.info(f"👤 קבלת /profile ממשתמש: {user.id}")
        
        # בדוק אם המשתמש רשום
        db_user = get_user(user.id)
        if not db_user:
            await update.message.reply_text(
                "❌ **אתה לא רשום במערכת!**\n\n"
                "שלח /start כדי להירשם."
            )
            return
        
        balance = get_balance(user.id)
        level, progress, total, next_level = get_level_progress(balance)
        total_referrals = get_total_referrals(user.id)
        streak_days = getattr(db_user, 'current_streak', 0) or 0
        
        # היסטוריית נוכחות (7 ימים אחרונים)
        attendance_history = get_user_attendance_history(user.id, 7)
        
        response = (
            f"👤 **פרופיל משתמש מלא**\n\n"
            f"**👤 פרטים אישיים:**\n"
            f"└── שם: {user.first_name}\n"
            f"└── משתמש: @{user.username or 'ללא'}\n"
            f"└── 🆔 מזהה: {user.id}\n"
            f"└── 📅 הצטרף: {db_user.created_at.strftime('%d/%m/%Y')}\n\n"
            
            f"**💰 כלכלה:**\n"
            f"└── 🪙 טוקנים: {format_number(balance)}\n"
            f"└── 🏅 רמה: {level}\n"
            f"└── 📊 התקדמות: {progress}/{total} טוקנים\n"
            f"└── 🔥 רצף יומי: {streak_days} ימים\n\n"
            
            f"**👥 רשת:**\n"
            f"└── 👥 מוזמנים: {total_referrals}\n"
            f"└── 💰 טוקנים מהפניות: {format_number(total_referrals * 10)}\n"
            f"└── 🔗 קוד הפניה: `{db_user.referral_code}`\n\n"
        )
        
        # היסטוריית נוכחות
        if attendance_history:
            response += "**📅 נוכחות 7 ימים אחרונים:**\n"
            for record in attendance_history:
                date_str = record['date'].strftime('%d/%m') if isinstance(record['date'], datetime) else record['date']
                day_name = get_day_name(record['date'].strftime('%Y-%m-%d') if isinstance(record['date'], datetime) else record['date'])
                checkin_status = "✅" if record['checked_in'] else "❌"
                response += f"└── {day_name} ({date_str}): {checkin_status}\n"
        else:
            response += "**📅 נוכחות:** אין היסטוריה זמינה\n"
        
        response += "\n💡 **השתמש ב-/checkin כל יום כדי לשפר את הפרופיל שלך!**"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת profile: {e}")
        await update.message.reply_text(
            "❌ **שגיאה בהצגת פרופיל**\n\n"
            "אנא נסה שוב מאוחר יותר."
        )

async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """הצגת המשימות הזמינות"""
    try:
        user = update.effective_user
        logger.info(f"📋 קבלת /tasks ממשתמש: {user.id}")
        
        # בדוק אם המשתמש רשום
        db_user = get_user(user.id)
        if not db_user:
            await update.message.reply_text(
                "❌ **אתה לא רשום במערכת!**\n\n"
                "שלח /start כדי להירשם."
            )
            return
        
        # קבל משימות זמינות
        available_tasks = get_available_tasks(user.id)
        
        if not available_tasks:
            response = (
                "📋 **משימות זמינות**\n\n"
                "כרגע אין משימות זמינות.\n\n"
                "💡 **משימות יומיות אוטומטיות:**\n"
                "└── 📅 צ'ק-אין יומי - 1 טוקן\n"
                "└── 🔥 7 ימים רצופים - 10 טוקנים\n"
                "└── 🗓️ 30 ימים רצופים - 50 טוקנים\n\n"
                "🔔 משימות חדשות יופיעו כאן בקרוב!"
            )
        else:
            response = "📋 **משימות זמינות**\n\n"
            
            for i, task in enumerate(available_tasks[:5], 1):
                task_name = task.get('name', 'משימה')
                task_reward = task.get('reward', 0)
                task_description = task.get('description', '')
                
                response += f"{i}. **{task_name}**\n"
                response += f"   └── 🎁 פרס: {task_reward} טוקנים\n"
                response += f"   └── 📝 {task_description}\n\n"
            
            if len(available_tasks) > 5:
                response += f"... ועוד {len(available_tasks) - 5} משימות\n\n"
            
            response += "💡 **בצע משימות וקבל טוקנים נוספים!**"
        
        # כפתורים לניהול משימות
        keyboard = [
            [
                InlineKeyboardButton("✅ סיימתי משימה", callback_data="complete_task"),
                InlineKeyboardButton("📊 משימות שלי", callback_data="my_tasks")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            response, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת tasks: {e}")
        await update.message.reply_text(
            "❌ **שגיאה בהצגת משימות**\n\n"
            "אנא נסה שוב מאוחר יותר."
        )

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """הצגת פרטי קשר עם המנהל"""
    try:
        response = (
            f"📞 **צור קשר עם המנהל**\n\n"
            f"**👤 פרטי מנהל:**\n"
            f"└── שם: {ADMIN_INFO['name']}\n"
            f"└── 📱 טלגרם: {ADMIN_INFO['telegram']}\n"
            f"└── 📞 טלפון: {ADMIN_INFO['phone']}\n"
            f"└── 📧 אימייל: {ADMIN_INFO['email']}\n\n"
            
            f"**🕒 זמני תגובה:**\n"
            f"└── {ADMIN_INFO['response_time']}\n\n"
            
            f"**💬 ניתן לפנות בנושאים:**\n"
            f"• 🛠️ תמיכה טכנית\n"
            f"• ❓ שאלות על המערכת\n"
            f"• 💡 הצעות לשיפור\n"
            f"• 🐛 דיווח על בעיות\n"
            f"• 🤝 שיתופי פעולה\n\n"
            
            f"**✉️ נשמח לעזור בכל שאלה!**\n\n"
            f"📧 **דרכי התקשרות מועדפות:**\n"
            f"1. הודעה פרטית בטלגרם\n"
            f"2. שיחת טלפון\n"
            f"3. אימייל"
        )
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת contact: {e}")
        await update.message.reply_text(
            "❌ **שגיאה בהצגת פרטי קשר**\n\n"
            "אנא נסה שוב מאוחר יותר."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """הצגת הודעת עזרה עם כל הפקודות"""
    try:
        response = (
            f"🆘 **עזרה והדרכה - Crypto-Class**\n\n"
            
            f"**📚 רשימת הפקודות המלאה:**\n\n"
            
            f"**👤 פקודות בסיסיות:**\n"
            f"└── /start - הרשמה והתחלת שימוש\n"
            f"└── /help - תפריט זה\n"
            f"└── /contact - פרטי קשר עם מנהל\n\n"
            
            f"**💰 כלכלת טוקנים:**\n"
            f"└── /checkin - צ'ק-אין יומי (טוקן + בונוסים)\n"
            f"└── /balance - הצגת יתרת טוקנים\n"
            f"└── /level - הרמה וההתקדמות שלך\n"
            f"└── /profile - פרופיל משתמש מלא\n\n"
            
            f"**👥 רשת והפניות:**\n"
            f"└── /referral - קוד ההפניה שלך\n"
            f"└── /my_referrals - המוזמנים שלך\n\n"
            
            f"**🏆 תחרות ולידרבורד:**\n"
            f"└── /leaderboard - טבלת המובילים\n"
            f"└── /stats - סטטיסטיקות מערכת\n\n"
            
            f"**📋 משימות:**\n"
            f"└── /tasks - משימות זמינות\n\n"
            
            f"**🌐 אתר המערכת:**\n"
            f"└── /website - קישור לאתר\n\n"
            
            f"**🎯 איך להצליח במערכת:**\n"
            f"1. שלח /start כדי להירשם\n"
            f"2. שלח /checkin כל יום (רצף=בונוסים)\n"
            f"3. הזמן חברים עם /referral\n"
            f"4. עקוב אחר ההתקדמות עם /level\n"
            f"5. תחרה עם אחרים ב-/leaderboard\n\n"
            
            f"**💰 מערכת הטוקנים:**\n"
            f"└── צ'ק-אין יומי: 1 טוקן\n"
            f"└── הזמנת חבר: 10 טוקנים\n"
            f"└── רצף 7 ימים: 10 טוקנים\n"
            f"└── רצף 30 ימים: 50 טוקנים\n\n"
            
            f"**❓ בעיות טכניות?** שלח /contact"
        )
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת help: {e}")
        await update.message.reply_text(
            "❌ **שגיאה בהצגת עזרה**\n\n"
            "אנא נסה שוב מאוחר יותר."
        )

async def website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """שליחת קישור לאתר המערכת"""
    try:
        web_url = "https://school-production-4d9d.up.railway.app"
        
        response = (
            f"🌐 **אתר המערכת - Crypto-Class**\n\n"
            
            f"**🔗 קישור לאתר:**\n"
            f"{web_url}\n\n"
            
            f"**📊 באתר תוכל למצוא:**\n"
            f"• 📈 סטטיסטיקות מערכת בזמן אמת\n"
            f"• 🏆 טבלאות מובילים מפורטות\n"
            f"• 👨‍🏫 דשבורד ניהול למורים\n"
            f"• 💪 בדיקת בריאות המערכת\n"
            f"• 📊 גרפים ומגמות\n"
            f"• 🔍 חיפוש משתמשים מתקדם\n\n"
            
            f"**💻 גש לאתר למידע נוסף!**\n\n"
            f"💡 האתר מעודכן בזמן אמת עם הנתונים מהבוט."
        )
        
        # כפתור לקישור ישיר
        keyboard = [[InlineKeyboardButton("🌐 כניסה לאתר", url=web_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            response, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת website: {e}")
        await update.message.reply_text(
            "❌ **שגיאה בהצגת קישור לאתר**\n\n"
            "אנא נסה שוב מאוחר יותר."
        )

# ========== פקודות מנהל ==========

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פאנל ניהול למערכת (למנהל בלבד)"""
    try:
        user = update.effective_user
        
        # בדוק אם המשתמש הוא מנהל
        if str(user.id) != "224223270":  # החלף במזהה הטלגרם שלך
            await update.message.reply_text(
                "❌ **גישה נדחתה**\n\n"
                "רק מנהל המערכת יכול לגשת לפאנל זה."
            )
            return
        
        logger.info(f"🔧 מנהל נכנס לפאנל: {user.id}")
        
        # קבל סטטיסטיקות מערכת
        stats = get_system_stats()
        today_stats = get_today_stats()
        
        response = (
            f"🔧 **פאנל ניהול - Crypto-Class**\n\n"
            
            f"**📊 סטטיסטיקות מערכת:**\n"
            f"└── 👥 משתמשים: {stats.get('total_users', 0)}\n"
            f"└── 💰 טוקנים כוללים: {format_number(stats.get('total_tokens', 0))}\n"
            f"└── 📈 פעילים היום: {today_stats.get('active_users', 0)}\n"
            f"└── 🔥 צ'ק-אין היום: {today_stats.get('checkins_today', 0)}\n\n"
            
            f"**⚡ פקודות ניהול:**\n"
            f"└── /add_tokens - הוספת טוקנים למשתמש\n"
            f"└── /reset_checkin - איפוס צ'ק-אין למשתמש\n"
            f"└── /system_stats - סטטיסטיקות מפורטות\n"
            f"└── /broadcast - שליחת הודעה לכל המשתמשים\n\n"
            
            f"**🔍 ניטור:**\n"
            f"└── /user_info - מידע על משתמש ספציפי\n"
            f"└── /recent_activity - פעילות אחרונה\n"
            f"└── /top_referrers - המובילים בהפניות\n\n"
            
            f"💡 השתמש בפקודות לעיל לניהול המערכת."
        )
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת admin: {e}")
        await update.message.reply_text(
            "❌ **שגיאה בפאנל ניהול**\n\n"
            "אנא נסה שוב מאוחר יותר."
        )

async def add_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """הוספת טוקנים למשתמש (למנהל בלבד)"""
    try:
        user = update.effective_user
        
        # בדוק אם המשתמש הוא מנהל
        if str(user.id) != "224223270":
            await update.message.reply_text("❌ גישה נדחתה")
            return
        
        # בדוק פרמטרים
        if len(context.args) < 2:
            await update.message.reply_text(
                "**❌ שימוש לא נכון:**\n"
                "השתמש: /add_tokens [user_id] [amount]\n\n"
                "**דוגמה:** /add_tokens 123456 100"
            )
            return
        
        user_id = int(context.args[0])
        amount = int(context.args[1])
        
        # הוסף טוקנים
        success, message = add_tokens_to_user(user_id, amount)
        
        if success:
            response = (
                f"✅ **טוקנים נוספו בהצלחה!**\n\n"
                f"**📝 פרטים:**\n"
                f"└── 🆔 מזהה משתמש: {user_id}\n"
                f"└── 💰 כמות טוקנים: {amount}\n"
                f"└── 📅 תאריך: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                f"{message}"
            )
        else:
            response = f"❌ **שגיאה:** {message}"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת add_tokens: {e}")
        await update.message.reply_text("❌ שגיאה בהוספת טוקנים")

async def reset_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """איפוס צ'ק-אין למשתמש (למנהל בלבד)"""
    try:
        user = update.effective_user
        
        # בדוק אם המשתמש הוא מנהל
        if str(user.id) != "224223270":
            await update.message.reply_text("❌ גישה נדחתה")
            return
        
        # בדוק פרמטרים
        if not context.args:
            await update.message.reply_text(
                "**❌ שימוש לא נכון:**\n"
                "השתמש: /reset_checkin [user_id]\n\n"
                "**דוגמה:** /reset_checkin 123456"
            )
            return
        
        user_id = int(context.args[0])
        
        # אפס צ'ק-אין
        success, message = reset_user_checkin(user_id)
        
        if success:
            response = (
                f"✅ **צ'ק-אין אופס בהצלחה!**\n\n"
                f"**📝 פרטים:**\n"
                f"└── 🆔 מזהה משתמש: {user_id}\n"
                f"└── 📅 תאריך: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                f"{message}"
            )
        else:
            response = f"❌ **שגיאה:** {message}"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת reset_checkin: {e}")
        await update.message.reply_text("❌ שגיאה באיפוס צ'ק-אין")

# ========== פונקציות עזר נוספות ==========

def get_user_by_referral_code(referral_code: str):
    """מציאת משתמש לפי קוד הפניה"""
    from database.queries import get_user_by_referral_code as db_query
    return db_query(referral_code)

def get_user_rank(user_id: int) -> int:
    """קבלת מיקום המשתמש בטבלת המובילים"""
    all_users = get_top_users(limit=1000, order_by='tokens')
    for i, user in enumerate(all_users, 1):
        if user.telegram_id == user_id:
            return i
    return 0

# ========== פונקציות לטיפול בבקשות ==========

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בבקשות callback"""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "my_referrals":
            await my_referrals(update, context)
        elif data == "complete_task":
            await query.edit_message_text(
                "📝 **שלח את פרטי המשימה שביצעת:**\n\n"
                "• שם המשימה\n"
                • תיאור קצר\n"
                • הוכחה (קישור/תמונה)",
                parse_mode='Markdown'
            )
        elif data == "my_tasks":
            await query.edit_message_text(
                "📋 **משימות שביצעת:**\n\n"
                "כרגע אין מידע על משימות שבוצעו.\n\n"
                "💡 בצע משימות חדשות דרך /tasks",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"❌ שגיאה ב-callback: {e}")

# ========== אתחול לוגר ==========
if __name__ == "__main__":
    print("✅ קובץ commands.py נטען בהצלחה")
    print(f"📁 פקודות זמינות: {[func for func in dir() if not func.startswith('_')]}")

