<<<<<<< HEAD
import json
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

USERS_FILE = "backend/data/users.json"
INVITES_FILE = "backend/data/invites.json"
AIRDROP_FILE = "backend/data/airdrops.json"

def load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    users = load(USERS_FILE, {})
    invites = load(INVITES_FILE, {})

    if user.id not in users:
        users[user.id] = {
            "id": user.id,
            "username": user.username,
            "approved": False,
            "invited_by": None
        }

    if args and args[0].startswith("invite_"):
        code = args[0].replace("invite_", "")
        if code in invites:
            inviter_id = invites[code]["inviter_id"]
            users[user.id]["invited_by"] = inviter_id

            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ אשר", callback_data=f"approve:{user.id}"),
                    InlineKeyboardButton("❌ דחה", callback_data=f"reject:{user.id}")
                ]
            ])

            await context.bot.send_message(
                chat_id=inviter_id,
                text=f"🔔 בקשת הצטרפות\n@{user.username}",
                reply_markup=kb
            )

            await update.message.reply_text(
                "👋 בקשת הצטרפות נשלחה\n⏳ ממתין לאישור"
            )

    save(USERS_FILE, users)

# ===== אישור =====
async def approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, uid = query.data.split(":")
    uid = int(uid)

    users = load(USERS_FILE, {})
    airdrops = load(AIRDROP_FILE, [])

    if action == "approve":
        users[uid]["approved"] = True

        airdrops.append({
            "user_id": uid,
            "amount": 4444
        })

        await context.bot.send_message(
            chat_id=uid,
            text="🎉 אושרת!\n🎁 קיבלת איירדרופ ראשון\n\nכתוב /invite להזמין חבר"
        )

        await query.edit_message_text("✅ המשתמש אושר")

    save(USERS_FILE, users)
    save(AIRDROP_FILE, airdrops)

# ===== הזמנה =====
async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load(USERS_FILE, {})

    if not users.get(user.id, {}).get("approved"):
        await update.message.reply_text("⛔ אין לך הרשאה להזמין")
        return

    code = str(uuid.uuid4())[:8]
    invites = load(INVITES_FILE, {})
    invites[code] = {"inviter_id": user.id}
    save(INVITES_FILE, invites)

    link = f"https://t.me/{context.bot.username}?start=invite_{code}"

    await update.message.reply_text(
        f"🔗 לינק הזמנה:\n{link}"
    )

# ===== main =====
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("invite", invite))
app.add_handler(CallbackQueryHandler(approval))

print("🤖 Bot running...")
app.run_polling()
=======
from .app.main import app  # noqa: F401
>>>>>>> 03e5c1437b28768ba89ff31f6cea0fc62306fdf0
