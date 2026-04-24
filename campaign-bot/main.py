"""
SLH Campaign SaaS - ×›×œ×™ × ×™×”×•×œ ×§×ž×¤×™×™× ×™× ×œ×ž×•×‘×™×œ×™ ×“×¢×ª ×§×”×œ
Powered by SPARK IND | SLH Ecosystem
"""
import os
import sys
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)

sys.path.insert(0, "/app/shared")
try:
    from slh_payments import db as pay_db
    from slh_payments.config import ADMIN_USER_ID, TON_WALLET
except Exception:
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "224223270"))
    TON_WALLET = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
    pay_db = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("slh.campaign")

TOKEN = os.getenv("BOT_TOKEN") or os.getenv("CAMPAIGN_TOKEN", "")
if not TOKEN:
    raise SystemExit("BOT_TOKEN missing")

# Storage
campaigns = {}
contacts = {}
surveys = {}
users_db = {}


def get_user(uid, username=""):
    if uid not in users_db:
        users_db[uid] = {"username": username, "joined": datetime.now().isoformat(), "premium": False}
    if username:
        users_db[uid]["username"] = username
    return users_db[uid]


def main_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("\U0001f4cb \u05e7\u05de\u05e4\u05d9\u05d9\u05e0\u05d9\u05dd"), KeyboardButton("\U0001f465 CRM")],
        [KeyboardButton("\U0001f4ca \u05e1\u05e7\u05e8\u05d9\u05dd"), KeyboardButton("\U0001f4e3 \u05e9\u05d9\u05d3\u05d5\u05e8")],
        [KeyboardButton("\U0001f4b0 \u05de\u05e0\u05d5\u05d9"), KeyboardButton("\u2753 \u05e2\u05d6\u05e8\u05d4")],
    ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    get_user(uid, update.effective_user.username or "")
    name = update.effective_user.first_name
    await update.message.reply_text(
        "\U0001f4a1 *SLH Campaign SaaS*\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        f"\u05e9\u05dc\u05d5\u05dd {name}! \U0001f44b\n\n"
        "\u05d4\u05db\u05dc\u05d9 \u05dc\u05e0\u05d9\u05d4\u05d5\u05dc \u05e7\u05de\u05e4\u05d9\u05d9\u05e0\u05d9\u05dd \u05d3\u05d9\u05d2\u05d9\u05d8\u05dc\u05d9\u05d9\u05dd\n"
        "\u05dc\u05de\u05d5\u05d1\u05d9\u05dc\u05d9 \u05d3\u05e2\u05ea \u05e7\u05d4\u05dc \u05d5\u05de\u05e0\u05d4\u05d9\u05d2\u05d9\u05dd.\n\n"
        "\U0001f4cb *\u05e7\u05de\u05e4\u05d9\u05d9\u05e0\u05d9\u05dd* - \u05e6\u05d5\u05e8, \u05e0\u05d4\u05dc, \u05e2\u05e7\u05d5\u05d1\n"
        "\U0001f465 *CRM* - \u05e0\u05d9\u05d4\u05d5\u05dc \u05ea\u05d5\u05de\u05db\u05d9\u05dd \u05d5\u05de\u05d5\u05de\u05d7\u05d9\u05dd\n"
        "\U0001f4ca *\u05e1\u05e7\u05e8\u05d9\u05dd* - \u05e9\u05d0\u05dc\u05d5\u05e0\u05d9\u05dd \u05d5\u05e1\u05e7\u05e8\u05d9 \u05d3\u05e2\u05ea \u05e7\u05d4\u05dc\n"
        "\U0001f4e3 *\u05e9\u05d9\u05d3\u05d5\u05e8* - \u05d4\u05d5\u05d3\u05e2\u05d5\u05ea \u05dc\u05db\u05dc \u05d4\u05e8\u05e9\u05d5\u05de\u05d9\u05dd\n"
        "\U0001f4b0 *\u05de\u05e0\u05d5\u05d9* - 59\u20aa / 3 TON \u05dc\u05d7\u05d5\u05d3\u05e9\n\n"
        "_Powered by SPARK IND | SLH Ecosystem_",
        parse_mode="Markdown",
        reply_markup=main_kb(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "\u2753 *SLH Campaign SaaS*\n\n"
        "/start - \u05d4\u05ea\u05d7\u05dc\u05d4\n"
        "/campaigns - \u05e0\u05d9\u05d4\u05d5\u05dc \u05e7\u05de\u05e4\u05d9\u05d9\u05e0\u05d9\u05dd\n"
        "/contacts - CRM \u05d0\u05e0\u05e9\u05d9 \u05e7\u05e9\u05e8\n"
        "/surveys - \u05e1\u05e7\u05e8\u05d9\u05dd\n"
        "/broadcast - \u05e9\u05d9\u05d3\u05d5\u05e8\n"
        "/subscribe - \u05de\u05e0\u05d5\u05d9\n"
        "/add_contact <\u05e9\u05dd> <\u05ea\u05e4\u05e7\u05d9\u05d3>\n"
        "/new_survey <\u05e9\u05d0\u05dc\u05d4>\n\n"
        "\U0001f4a1 SPARK IND | SLH Ecosystem",
        parse_mode="Markdown",
    )


async def campaigns_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_camps = campaigns.get(uid, [])
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("\u2795 \u05e7\u05de\u05e4\u05d9\u05d9\u05df \u05d7\u05d3\u05e9", callback_data="camp:new")],
        [InlineKeyboardButton("\U0001f4cb \u05d4\u05e7\u05de\u05e4\u05d9\u05d9\u05e0\u05d9\u05dd \u05e9\u05dc\u05d9", callback_data="camp:list")],
    ])
    await update.message.reply_text(
        f"\U0001f4cb \u05e7\u05de\u05e4\u05d9\u05d9\u05e0\u05d9\u05dd ({len(user_camps)})\n\n"
        "\u05e7\u05de\u05e4\u05d9\u05d9\u05df = \u05de\u05e9\u05d9\u05de\u05d4 \u05e2\u05dd \u05d9\u05e2\u05d3, \u05ea\u05d5\u05de\u05db\u05d9\u05dd, \u05d5\u05de\u05e2\u05e7\u05d1.",
        reply_markup=kb,
    )


async def contacts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_contacts = contacts.get(uid, [])
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("\u2795 \u05d7\u05d3\u05e9", callback_data="crm:new")],
        [InlineKeyboardButton("\U0001f4cb \u05e8\u05e9\u05d9\u05de\u05d4", callback_data="crm:list")],
        [InlineKeyboardButton("\U0001f4e4 CSV", callback_data="crm:csv")],
    ])
    await update.message.reply_text(
        f"\U0001f465 CRM ({len(user_contacts)} \u05d0\u05e0\u05e9\u05d9 \u05e7\u05e9\u05e8)\n\n"
        "\u05d4\u05d5\u05e1\u05e3: /add_contact <\u05e9\u05dd> <\u05ea\u05e4\u05e7\u05d9\u05d3>",
        reply_markup=kb,
    )


async def subscribe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"\U0001f4b0 *\u05de\u05e0\u05d5\u05d9 \u05e4\u05e8\u05d9\u05de\u05d9\u05d5\u05dd*\n\n"
        "\u05de\u05d7\u05d9\u05e8: 59\u20aa / 3 TON \u05dc\u05d7\u05d5\u05d3\u05e9\n\n"
        "\u05db\u05d5\u05dc\u05dc: \u05e7\u05de\u05e4\u05d9\u05d9\u05e0\u05d9\u05dd \u05dc\u05dc\u05d0 \u05d4\u05d2\u05d1\u05dc\u05d4, CRM, \u05e1\u05e7\u05e8\u05d9\u05dd, \u05e9\u05d9\u05d3\u05d5\u05e8, CSV\n\n"
        f"\u05e9\u05dc\u05d7 3 TON \u05dc:\n`{TON_WALLET}`\n\n"
        "\u05d5\u05e9\u05dc\u05d7 \u05e6\u05d9\u05dc\u05d5\u05dd \u05de\u05e1\u05da \u05dc\u05d0\u05d9\u05e9\u05d5\u05e8.",
        parse_mode="Markdown",
    )


async def add_contact_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = " ".join(context.args) if context.args else ""
    parts = args.rsplit(" ", 1)
    if len(parts) < 2:
        await update.message.reply_text("\u05e9\u05d9\u05de\u05d5\u05e9: /add_contact <\u05e9\u05dd> <\u05ea\u05e4\u05e7\u05d9\u05d3>")
        return
    name, role = parts[0], parts[1]
    contacts.setdefault(uid, []).append({"name": name, "role": role, "added": datetime.now().strftime("%Y-%m-%d")})
    await update.message.reply_text(f"\u2705 {name} \u05e0\u05d5\u05e1\u05e3 \u05db-{role}")


async def new_survey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    question = " ".join(context.args) if context.args else ""
    if not question:
        await update.message.reply_text("\u05e9\u05d9\u05de\u05d5\u05e9: /new_survey <\u05e9\u05d0\u05dc\u05d4>")
        return
    surveys.setdefault(uid, []).append({"question": question, "answers": []})
    await update.message.reply_text(f"\u2705 \u05e1\u05e7\u05e8 \u05e0\u05d5\u05e6\u05e8: {question}")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data

    if data == "camp:new":
        cid = len(campaigns.get(uid, [])) + 1
        campaigns.setdefault(uid, []).append({
            "id": cid, "name": f"\u05e7\u05de\u05e4\u05d9\u05d9\u05df #{cid}",
            "target": 100, "current": 0,
        })
        await q.message.reply_text(f"\u2705 \u05e7\u05de\u05e4\u05d9\u05d9\u05df #{cid} \u05e0\u05d5\u05e6\u05e8!")

    elif data == "camp:list":
        user_camps = campaigns.get(uid, [])
        if not user_camps:
            await q.message.reply_text("\u05d0\u05d9\u05df \u05e7\u05de\u05e4\u05d9\u05d9\u05e0\u05d9\u05dd.")
            return
        lines = []
        for c in user_camps:
            pct = int(c["current"] / max(1, c["target"]) * 100)
            bar = "\u2588" * (pct // 10) + "\u2591" * (10 - pct // 10)
            lines.append(f"#{c['id']} {c['name']}\n[{bar}] {pct}%")
        await q.message.reply_text("\n\n".join(lines))

    elif data == "crm:new":
        await q.message.reply_text("/add_contact <\u05e9\u05dd> <\u05ea\u05e4\u05e7\u05d9\u05d3>")

    elif data == "crm:list":
        user_contacts = contacts.get(uid, [])
        if not user_contacts:
            await q.message.reply_text("\u05e8\u05d9\u05e7.")
            return
        lines = [f"{i}. {c['name']} | {c['role']}" for i, c in enumerate(user_contacts, 1)]
        await q.message.reply_text("\n".join(lines))

    elif data == "crm:csv":
        user_contacts = contacts.get(uid, [])
        if not user_contacts:
            await q.message.reply_text("\u05d0\u05d9\u05df \u05e0\u05ea\u05d5\u05e0\u05d9\u05dd.")
            return
        csv = "\u05e9\u05dd,\u05ea\u05e4\u05e7\u05d9\u05d3,\u05ea\u05d0\u05e8\u05d9\u05da\n"
        for c in user_contacts:
            csv += f"{c['name']},{c['role']},{c.get('added', '')}\n"
        await q.message.reply_text(f"```\n{csv}```", parse_mode="Markdown")


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    if "\u05e7\u05de\u05e4\u05d9\u05d9\u05e0\u05d9\u05dd" in text:
        await campaigns_cmd(update, context)
    elif "CRM" in text or "\u05e7\u05e9\u05e8" in text:
        await contacts_cmd(update, context)
    elif "\u05e1\u05e7\u05e8" in text:
        await update.message.reply_text("\U0001f4ca \u05e1\u05e7\u05e8\u05d9\u05dd\n\n\u05e6\u05d5\u05e8: /new_survey <\u05e9\u05d0\u05dc\u05d4>")
    elif "\u05e9\u05d9\u05d3\u05d5\u05e8" in text:
        await update.message.reply_text("\U0001f4e3 \u05e9\u05d9\u05d3\u05d5\u05e8\n\n/broadcast <\u05d4\u05d5\u05d3\u05e2\u05d4>")
    elif "\u05de\u05e0\u05d5\u05d9" in text:
        await subscribe_cmd(update, context)
    elif "\u05e2\u05d6\u05e8\u05d4" in text:
        await help_cmd(update, context)


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    uname = update.effective_user.username or ""
    if pay_db:
        await pay_db.create_payment(uid, uname, "campaign", 59, "ILS")
        await pay_db.submit_proof(uid, "campaign", update.message.photo[-1].file_id)
    await update.message.reply_text("\u2705 \u05d0\u05d9\u05e9\u05d5\u05e8 \u05ea\u05e9\u05dc\u05d5\u05dd \u05d4\u05ea\u05e7\u05d1\u05dc!\n\u05de\u05de\u05ea\u05d9\u05df \u05dc\u05d0\u05d9\u05e9\u05d5\u05e8...")


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("campaigns", campaigns_cmd))
    app.add_handler(CommandHandler("contacts", contacts_cmd))
    app.add_handler(CommandHandler("subscribe", subscribe_cmd))
    app.add_handler(CommandHandler("add_contact", add_contact_cmd))
    app.add_handler(CommandHandler("new_survey", new_survey_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    logger.info("=" * 40)
    logger.info("SLH Campaign SaaS - Starting")
    logger.info("=" * 40)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
