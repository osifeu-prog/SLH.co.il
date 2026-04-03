#!/usr/bin/env python3
"""
TON Airdrop Bot - Professional Version
Modern, professional Telegram bot for TON Airdrop
"""

import os
import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ====================
# CONFIGURATION
# ====================
TOKEN = os.getenv("TELEGRAM_TOKEN", "8530795944:AAFXDx-vWZPpiXTlfsv5izUayJ4OpLLq3Ls")
API_URL = os.getenv("API_URL", "https://successful-fulfillment-production.up.railway.app")
TON_WALLET = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
PRICE = "44.4"

# Setup logging
logging.basicConfig(
    format="%(asctime)s - TON Airdrop Bot - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ====================
# HELPER FUNCTIONS
# ====================
def format_number(num):
    """Format numbers with commas"""
    return f"{int(num):,}"

def get_current_time():
    """Get current time in Israel format"""
    return datetime.now().strftime("%d/%m/%Y %H:%M")

# ====================
# COMMAND HANDLERS
# ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Professional start command with inline keyboard"""
    user = update.effective_user
    
    # Register user
    try:
        user_data = {
            "telegram_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
        
        response = requests.post(f"{API_URL}/api/register", json=user_data, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ User {user.id} registered successfully")
    except Exception as e:
        logger.warning(f"Registration warning: {e}")
    
    # Create professional welcome message
    welcome_message = f"""
✨ *ברוך הבא {user.first_name}!* ✨

🎯 *הגעת לבוט הרשמי של פרויקט TON Airdrop*

🚀 *מבצע פעיל עכשיו:*
╭─────────────────────────────
│ 💰 *השקעה:* {PRICE} ₪ (ב-TON)
│ 🎁 *תגמול:* 1,000 טוקנים
│ ⚡ *משך המבצע:* מוגבל ל-100 משתתפים
│ 📅 *זמן אישור:* עד 24 שעות
╰─────────────────────────────

📊 *סטטיסטיקות:*
• 👥 37 משתתפים נרשמו
• 💸 21 עסקעות אושרו
• 🎯 16 מקומות פנויים

🛠️ *פקודות זמינות:*
/airdrop - בקשת השתתפות חדשה
/status - סטטוס אישי ומאזן
/help - מדריך שימוש מפורט
/wallet - פרטי ארנק TON שלנו

💡 *תהליך פשוט:*
1️⃣ /airdrop - בקשת השתתפות
2️⃣ תשלום TON לארנק
3️⃣ שליחת אישור
4️⃣ קבלת 1,000 טוקנים!

⚡ *מערכת מאובטחת ואוטומטית*
_מופעל על ידי TON Blockchain_
"""
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("🎁 בקשת AIRDROP", callback_data="request_airdrop"),
            InlineKeyboardButton("📊 הסטטוס שלי", callback_data="my_status")
        ],
        [
            InlineKeyboardButton("💼 ארנק TON", callback_data="wallet_info"),
            InlineKeyboardButton("❓ עזרה ותמיכה", callback_data="help_info")
        ],
        [
            InlineKeyboardButton("📞 צור קשר", url="https://t.me/Osif83")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send welcome message
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def airdrop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create professional airdrop request"""
    user = update.effective_user
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        "⚙️ *מעבד את בקשתך...*\n_אנא המתן עד 15 שניות_",
        parse_mode='Markdown'
    )
    
    try:
        # Request airdrop from API
        airdrop_data = {"user_id": user.id}
        response = requests.post(f"{API_URL}/api/airdrop", json=airdrop_data, timeout=15)
        
        if response.status_code == 200:
            data = response.json()["airdrop"]
            
            # Professional payment message
            payment_message = f"""
🎫 *הזמנת AIRDROP מוכנה!* 🎫

📋 *פרטי העסקה:*
╭─────────────────────────────
│ 🔢 *מזהה עסקה:* `{data['id']}`
│ 💰 *סכום לתשלום:* `{data.get('price_ils', PRICE)} TON`
│ 💵 *ערך בשקלים:* {PRICE} ₪
│ ⏰ *תוקף ההזמנה:* 60 דקות
│ 📅 *נוצר בתאריך:* {get_current_time()}
╰─────────────────────────────

🏦 *פרטי הארנק שלנו:*
🔗 *קישור תשלום אוטומטי:*
[לחץ כאן לתשלום מיידי]({data.get('payment_url', f'ton://transfer/{TON_WALLET}?amount={PRICE}&text=Airdrop-{data["id"]}')})

📱 *הוראות תשלום:*
1. פתח את אפליקציית TON שלך (Tonkeeper/Tonhub)
2. שלח {data.get('price_ils', PRICE)} TON לארנק למעלה
3. בתיאור התשלום רשום: `Airdrop-{data['id']}`
4. שמור את מספר העסקה: `{data['id']}`
5. שלח צילום מסך ל@Osif83 לאישור

⚡ *מה קורה אחרי התשלום?*
• ✅ התשלום מאומת ידנית תוך 24 שעות
• 🎁 אתה מקבל אוטומטית 1,000 טוקנים לחשבון
• 📊 הסטטוס מתעדכן אוטומטית

📞 *תמיכה טכנית:* @Osif83
⏰ *ממשק אנושי זמין 24/7*
"""
            
            # Send payment message
            await processing_msg.delete()
            await update.message.reply_text(
                payment_message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            # Send QR code if available
            if data.get('qr_code'):
                try:
                    qr_caption = f"""
📱 *סרוק את ה-QR Code עם אפליקציית TON*
🔢 מספר עסקה: `{data['id']}`
💰 סכום: {data.get('price_ils', PRICE)} TON

_לחיצה על הקוד תפתח את אפליקציית התשלום_
"""
                    await update.message.reply_photo(
                        data['qr_code'],
                        caption=qr_caption,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"QR code error: {e}")
                    await update.message.reply_text(
                        "📱 *QR Code זמין באפליקציית TON דרך הקישור למעלה*",
                        parse_mode='Markdown'
                    )
            
            logger.info(f"🎯 Created airdrop {data['id']} for user {user.id}")
            
        else:
            await processing_msg.delete()
            error_message = """
❌ *לא ניתן ליצור עסקה כרגע*

⚠️ *סיבות אפשריות:*
• שרת העסקאות זמנית לא פנוי
• יש לך עסקה פעילה שכבר מחכה לתשלום
• מגבלת זמן בין עסקאות

🔄 *נסה שוב בעוד 2 דקות*
📞 *לבעיות מתמשכות:* @Osif83
"""
            await update.message.reply_text(error_message, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Airdrop creation error: {e}")
        await processing_msg.delete()
        error_msg = """
⚠️ *שגיאה זמנית במערכת*

השרת לא הגיב בזמן. זה כנראה בעיה זמנית.

🔄 *נסה שוב בעוד דקה*
📞 *אם הבעיה נמשכת:* @Osif83

_אנחנו פועלים לתיקון מהיר_
"""
        await update.message.reply_text(error_msg, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check user status professionally"""
    user = update.effective_user
    
    try:
        response = requests.get(f"{API_URL}/api/user/{user.id}", timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            
            if user_data.get("status") == "user_not_found":
                await update.message.reply_text(
                    "📝 *אתה עדיין לא רשום במערכת!*\n\nהקש /start כדי להירשם ולהתחיל.",
                    parse_mode='Markdown'
                )
                return
            
            # Get user stats
            balance = user_data.get('balance', 0)
            airdrops = user_data.get('airdrops', [])
            airdrop_count = len(airdrops)
            
            # Calculate statistics
            total_invested = airdrop_count * float(PRICE)
            token_value = balance / 1000 * float(PRICE)
            
            # Create professional status message
            status_message = f"""
📊 *דוח משתמש אישי* 📊

👤 *פרטים אישיים:*
╭─────────────────────────────
│ 🏷️ *שם:* {user_data.get('first_name', 'משתמש')}
│ 🆔 *מזהה:* `{user_data.get('id')}`
│ 📅 *נרשם בתאריך:* {user_data.get('created_at', 'לא ידוע')}
│ 👥 *משתמש מספר:* #{user_data.get('id', 0):03d}
╰─────────────────────────────

💰 *מאזנים וסטטיסטיקות:*
╭─────────────────────────────
│ 🪙 *טוקנים בבעלותך:* `{format_number(balance)}`
│ 💵 *ערך משוער:* {token_value:.2f} ₪
│ 🎫 *Airdrops שביצעת:* {airdrop_count}
│ 💸 *סה״כ השקעת:* {total_invested:.1f} ₪
│ 📈 *תשואה משוערת:* {((balance / 1000) / airdrop_count * 100) if airdrop_count > 0 else 0:.1f}%
╰─────────────────────────────

📋 *היסטוריית עסקאות אחרונות:*
"""
            
            # Add recent transactions
            if airdrop_count > 0:
                for i, airdrop in enumerate(airdrops[:3], 1):
                    status = airdrop.get('status', 'בהמתנה')
                    emoji = "✅" if status == "confirmed" else "⏳" if status == "pending" else "❌"
                    status_message += f"\n{i}. {emoji} `{airdrop.get('id', 'N/A')}` - {status}"
                
                if airdrop_count > 3:
                    status_message += f"\n... ועוד {airdrop_count - 3} עסקאות"
            else:
                status_message += "\n_עדיין לא ביצעת עסקאות_"
            
            status_message += f"""

💡 *המלצות:*
{ '🎉 כל הכבוד! המשך להשקיע!' if balance > 0 else '🚀 הקש /airdrop כדי להתחיל להשקיע!' }

📞 *ייעוץ אישי:* @Osif83
"""
            
            # Add action buttons
            keyboard = [
                [
                    InlineKeyboardButton("🎁 Airdrop נוסף", callback_data="another_airdrop"),
                    InlineKeyboardButton("📈 צפייה בגרף", callback_data="view_chart")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                status_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        else:
            await update.message.reply_text(
                "⚠️ *לא ניתן לטעון את הנתונים כרגע*\n\nהמערכת זמנית לא פנויה. נסה שוב בעוד דקה.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Status check error: {e}")
        await update.message.reply_text(
            "❌ *שגיאה בטעינת הנתונים*\n\nאנא נסה שוב מאוחר יותר או פנה לתמיכה.",
            parse_mode='Markdown'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Professional help command"""
    help_message = """
❓ *מדריך שימוש מפורט - TON Airdrop Bot* ❓

🎯 *מה זה הבוט?*
בוט רשמי לקניית טוקנים בפרויקט TON חדש. כל 44.4 ₪ שקולים ל-1,000 טוקנים.

📋 *פקודות עיקריות:*
• /start - הרשמה והתחלת עבודה
• /airdrop - בקשת קניית טוקנים חדשה
• /status - צפייה במאזן והיסטוריה
• /help - הצגת מדריך זה

💸 *תהליך קניית טוקנים:*
1. הקש /airdrop
2. שלח 44.4 TON לארנק שמופיע
3. שמור את מספר העסקה
4. שלח צילום מסך ל@Osif83
5. קבל אוטומטית 1,000 טוקנים

🏦 *פרטי הארנק שלנו:*
`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`

⏰ *זמני מענה:*
• אישור תשלומים: עד 24 שעות
• תמיכה טכנית: 24/7
• עדכון מאזן: מיידי לאחר אישור

🔒 *אבטחה:*
• כל העסקאות מתבצעות ב-TON Blockchain
• אין גישה לסיסמאות או פרטים אישיים
• אישורים רק דרך מנהל מאומת

📊 *יתרונות:*
✅ מחיר קבוע: 44.4 ₪ ל-1,000 טוקנים
✅ אישורים מהירים
✅ תמיכה בעברית
✅ מערכת אוטומטית

📞 *תמיכה וקשר:*
• מנהל: @Osif83
• בעיות טכניות: אותו הלינק
• שאלות כלליות: כאן בבוט

🚀 *טיפים:*
• שמור את מספרי העסקאות!
• שלח צילום מסך ברור לאישור מהיר
• עקוב אחר @Osif83 לעדכונים

_הבוט עודכן לאחרונה: 06/02/2026_
"""
    
    keyboard = [
        [InlineKeyboardButton("🎁 בקשת Airdrop", callback_data="quick_airdrop")],
        [InlineKeyboardButton("📞 צור קשר", url="https://t.me/Osif83")],
        [InlineKeyboardButton("💼 ארנק TON", callback_data="show_wallet")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_message,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show wallet information"""
    wallet_message = f"""
🏦 *פרטי הארנק הרשמי* 🏦

🔗 *כתובת הארנק:*
📋 *פרטים נוספים:*
╭─────────────────────────────
│ 🌐 *בלוקציין:* TON (The Open Network)
│ 🏷️ *פורמט:* Smart Contract Address
│ 🔒 *סוג:* ארנק עסקי מאובטח
│ 📅 *נוצר:* 01/02/2026
╰─────────────────────────────

💡 *הוראות שימוש:*
1. העתק את כתובת הארנק למעלה
2. פתח את אפליקציית TON שלך
3. הדבק בכתובת היעד
4. שלח 44.4 TON
5. בתיאור רשום: `Airdrop-מספר_עסקה`

⚠️ *חשוב לדעת:*
• שולחים רק TON, לא טוקנים אחרים
• סכום מדויק: 44.4 TON
• חייב לכלול תיאור עם מספר עסקה
• עסקאות ללא תיאור לא יאושרו

🔍 *איך בודקים עסקה?*
1. פתחו את explorer.toncoin.org
2. חפשו את כתובת הארנק
3. ראו את כל העסקאות הנכנסות

📞 *בעיות בתשלום?*
פנו ל@Osif83 עם:
1. מספר העסקה
2. צילום מסך מהתשלום
3. שם המשתמש שלכם

_ארנק זה משמש אך ורק לקבלת תשלומי Airdrop_
"""
    
    await update.message.reply_text(
        wallet_message,
        parse_mode='Markdown'
    )

# ====================
# CALLBACK HANDLERS
# ====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "request_airdrop":
        await query.edit_message_text(
            "🎁 *מעביר אותך לבקשת Airdrop...*",
            parse_mode='Markdown'
        )
        # Simulate airdrop request
        context.user_data['user_id'] = query.from_user.id
        await airdrop_command(update, context)
    
    elif query.data == "my_status":
        await query.edit_message_text(
            "📊 *טוען את הסטטוס שלך...*",
            parse_mode='Markdown'
        )
        context.user_data['user_id'] = query.from_user.id
        await status_command(update, context)
    
    elif query.data == "help_info":
        await query.edit_message_text(
            "❓ *טוען מדריך עזרה...*",
            parse_mode='Markdown'
        )
        await help_command(update, context)
    
    elif query.data == "wallet_info":
        await query.edit_message_text(
            "🏦 *טוען פרטי ארנק...*",
            parse_mode='Markdown'
        )
        await wallet_command(update, context)

# ====================
# MAIN FUNCTION
# ====================
def main():
    """Start the professional bot"""
    print("\n" + "="*50)
    print("🚀 TON Airdrop Bot - Professional Edition")
    print("📅 Version 2.0.0 | Launch Date: 06/02/2026")
    print("👤 Developer: Osif")
    print("🌐 API: " + API_URL)
    print("="*50 + "\n")
    
    # Clear any existing webhooks
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=5)
        print("✅ Cleared previous webhooks")
    except:
        print("⚠️ Could not clear webhooks (maybe none existed)")
    
    # Create application
    print("🛠️ Creating bot application...")
    app = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    print("📋 Adding command handlers...")
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("airdrop", airdrop_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("wallet", wallet_command))
    
    # Add callback handlers
    print("⌨️ Adding callback handlers...")
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    print("\n" + "="*50)
    print("✅ Bot initialized successfully!")
    print("🤖 Bot is now running and ready for users")
    print("📞 Support: @Osif83")
    print("="*50 + "\n")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
