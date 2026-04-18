"""
SLH UserInfo Bot - Enhanced user information bot with SLH Ecosystem integration.
Shows user ID, profile info, forwards analysis, group info, QR codes,
and deep-links into the SLH dashboard.

Features beyond @userinfobot:
  - /start - Show your full Telegram profile info + ID
  - /id    - Quick ID copy
  - Forward any message - get sender info
  - /group - Show current group/chat info (in groups)
  - /qr    - Generate QR code with your referral link
  - /dashboard - Direct link to SLH dashboard
  - /bots  - List all SLH ecosystem bots
  - /lang  - Switch language (HE/EN/RU/AR/FR)
  - /json  - Raw JSON dump of your Telegram user object
  - Inline mode - Type @bot_username in any chat to share your ID
"""
import os
import sys
import asyncio
import logging
import json
import io
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    ChatMemberUpdated,
)
from aiogram.enums import ParseMode, ChatType

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("slh.userinfo")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_URL = os.getenv("API_URL", "https://slh-api-production.up.railway.app").strip()
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://slh-nft.com/dashboard.html").strip()
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "224223270"))

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN missing")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ============================================================
# TRANSLATIONS
# ============================================================
T = {
    "he": {
        "welcome": (
            "{phoenix} <b>SLH UserInfo Bot</b>\n\n"
            "{wave} שלום <b>{name}</b>!\n\n"
            "{id_} <b>מזהה טלגרם:</b> <code>{uid}</code>\n"
            "{user} <b>שם:</b> {first} {last}\n"
            "{at} <b>שם משתמש:</b> {username}\n"
            "{lang} <b>שפה:</b> {language}\n"
            "{premium} <b>פרימיום:</b> {is_premium}\n"
            "{bot_icon} <b>בוט:</b> {is_bot}\n"
            "{calendar} <b>תאריך:</b> {date}\n\n"
            "{link} <b>קישור לדאשבורד:</b>\n"
            "<a href=\"{dashboard}?uid={uid}\">{arrow} פתח דאשבורד SLH</a>\n\n"
            "{ref} <b>קישור הפניה:</b>\n"
            "<code>https://t.me/SLH_AIR_bot?start=ref_{uid}</code>\n\n"
            "{hint} <i>העבר הודעה מכל משתמש כדי לראות את המידע שלו</i>"
        ),
        "quick_id": "{id_} <b>המזהה שלך:</b> <code>{uid}</code>\n\n{hint} לחץ להעתקה",
        "forward_info": (
            "{detective} <b>מידע על המשתמש</b>\n\n"
            "{id_} <b>מזהה:</b> <code>{uid}</code>\n"
            "{user} <b>שם:</b> {first} {last}\n"
            "{at} <b>שם משתמש:</b> {username}\n"
            "{bot_icon} <b>בוט:</b> {is_bot}\n\n"
            "{link} <a href=\"{dashboard}?uid={uid}\">צפה בדאשבורד</a>"
        ),
        "hidden_forward": "{detective} המשתמש הסתיר את זהותו בהעברות.",
        "group_info": (
            "{group} <b>מידע על הצ'אט</b>\n\n"
            "{id_} <b>מזהה:</b> <code>{cid}</code>\n"
            "{name_icon} <b>שם:</b> {title}\n"
            "{type_icon} <b>סוג:</b> {chat_type}\n"
            "{members} <b>חברים:</b> {count}\n"
            "{at} <b>שם משתמש:</b> {username}"
        ),
        "not_group": "{warning} פקודה זו עובדת רק בקבוצות.",
        "bots_title": "{phoenix} <b>בוטי אקוסיסטם SLH</b>\n\n",
        "json_title": "{code} <b>נתוני JSON גולמיים</b>\n\n<pre>{data}</pre>",
        "lang_set": "{check} השפה שונתה ל: <b>{lang_name}</b>",
        "choose_lang": "{globe} בחר שפה:",
        "copy_id": "העתק ID",
        "open_dashboard": "פתח דאשבורד",
        "share_id": "שתף ID",
        "help": (
            "{book} <b>פקודות זמינות:</b>\n\n"
            "/start - מידע מלא על הפרופיל שלך\n"
            "/id - מזהה מהיר להעתקה\n"
            "/group - מידע על קבוצה (בקבוצות בלבד)\n"
            "/qr - קישור הפניה שלך\n"
            "/dashboard - פתח דאשבורד SLH\n"
            "/bots - כל בוטי האקוסיסטם\n"
            "/lang - שנה שפה\n"
            "/json - נתוני JSON גולמיים\n"
            "/help - תפריט עזרה\n\n"
            "{hint} <i>העבר הודעה כדי לקבל מידע על השולח</i>"
        ),
    },
    "en": {
        "welcome": (
            "{phoenix} <b>SLH UserInfo Bot</b>\n\n"
            "{wave} Hello <b>{name}</b>!\n\n"
            "{id_} <b>Telegram ID:</b> <code>{uid}</code>\n"
            "{user} <b>Name:</b> {first} {last}\n"
            "{at} <b>Username:</b> {username}\n"
            "{lang} <b>Language:</b> {language}\n"
            "{premium} <b>Premium:</b> {is_premium}\n"
            "{bot_icon} <b>Bot:</b> {is_bot}\n"
            "{calendar} <b>Date:</b> {date}\n\n"
            "{link} <b>Dashboard link:</b>\n"
            "<a href=\"{dashboard}?uid={uid}\">{arrow} Open SLH Dashboard</a>\n\n"
            "{ref} <b>Referral link:</b>\n"
            "<code>https://t.me/SLH_AIR_bot?start=ref_{uid}</code>\n\n"
            "{hint} <i>Forward any message to see sender info</i>"
        ),
        "quick_id": "{id_} <b>Your ID:</b> <code>{uid}</code>\n\n{hint} Tap to copy",
        "forward_info": (
            "{detective} <b>User Information</b>\n\n"
            "{id_} <b>ID:</b> <code>{uid}</code>\n"
            "{user} <b>Name:</b> {first} {last}\n"
            "{at} <b>Username:</b> {username}\n"
            "{bot_icon} <b>Bot:</b> {is_bot}\n\n"
            "{link} <a href=\"{dashboard}?uid={uid}\">View Dashboard</a>"
        ),
        "hidden_forward": "{detective} This user has hidden their identity in forwards.",
        "group_info": (
            "{group} <b>Chat Information</b>\n\n"
            "{id_} <b>ID:</b> <code>{cid}</code>\n"
            "{name_icon} <b>Name:</b> {title}\n"
            "{type_icon} <b>Type:</b> {chat_type}\n"
            "{members} <b>Members:</b> {count}\n"
            "{at} <b>Username:</b> {username}"
        ),
        "not_group": "{warning} This command only works in groups.",
        "bots_title": "{phoenix} <b>SLH Ecosystem Bots</b>\n\n",
        "json_title": "{code} <b>Raw JSON data</b>\n\n<pre>{data}</pre>",
        "lang_set": "{check} Language changed to: <b>{lang_name}</b>",
        "choose_lang": "{globe} Choose language:",
        "copy_id": "Copy ID",
        "open_dashboard": "Open Dashboard",
        "share_id": "Share ID",
        "help": (
            "{book} <b>Available commands:</b>\n\n"
            "/start - Full profile info\n"
            "/id - Quick copyable ID\n"
            "/group - Group info (groups only)\n"
            "/qr - Your referral link\n"
            "/dashboard - Open SLH Dashboard\n"
            "/bots - All ecosystem bots\n"
            "/lang - Change language\n"
            "/json - Raw JSON data\n"
            "/help - Help menu\n\n"
            "{hint} <i>Forward a message to get sender info</i>"
        ),
    },
    "ru": {
        "welcome": (
            "{phoenix} <b>SLH UserInfo Bot</b>\n\n"
            "{wave} \u041f\u0440\u0438\u0432\u0435\u0442 <b>{name}</b>!\n\n"
            "{id_} <b>Telegram ID:</b> <code>{uid}</code>\n"
            "{user} <b>\u0418\u043c\u044f:</b> {first} {last}\n"
            "{at} <b>\u041b\u043e\u0433\u0438\u043d:</b> {username}\n"
            "{lang} <b>\u042f\u0437\u044b\u043a:</b> {language}\n"
            "{premium} <b>\u041f\u0440\u0435\u043c\u0438\u0443\u043c:</b> {is_premium}\n"
            "{bot_icon} <b>\u0411\u043e\u0442:</b> {is_bot}\n"
            "{calendar} <b>\u0414\u0430\u0442\u0430:</b> {date}\n\n"
            "{link} <b>\u0421\u0441\u044b\u043b\u043a\u0430 \u043d\u0430 \u043f\u0430\u043d\u0435\u043b\u044c:</b>\n"
            "<a href=\"{dashboard}?uid={uid}\">{arrow} \u041e\u0442\u043a\u0440\u044b\u0442\u044c SLH Dashboard</a>\n\n"
            "{ref} <b>\u0420\u0435\u0444\u0435\u0440\u0430\u043b\u044c\u043d\u0430\u044f \u0441\u0441\u044b\u043b\u043a\u0430:</b>\n"
            "<code>https://t.me/SLH_AIR_bot?start=ref_{uid}</code>\n\n"
            "{hint} <i>\u041f\u0435\u0440\u0435\u0448\u043b\u0438\u0442\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u0434\u043b\u044f \u0438\u043d\u0444\u043e \u043e\u0431 \u043e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u0435\u043b\u0435</i>"
        ),
        "quick_id": "{id_} <b>\u0412\u0430\u0448 ID:</b> <code>{uid}</code>\n\n{hint} \u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u0434\u043b\u044f \u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f",
        "forward_info": (
            "{detective} <b>\u0418\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f \u043e \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435</b>\n\n"
            "{id_} <b>ID:</b> <code>{uid}</code>\n"
            "{user} <b>\u0418\u043c\u044f:</b> {first} {last}\n"
            "{at} <b>\u041b\u043e\u0433\u0438\u043d:</b> {username}\n"
            "{bot_icon} <b>\u0411\u043e\u0442:</b> {is_bot}\n\n"
            "{link} <a href=\"{dashboard}?uid={uid}\">\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u043f\u0430\u043d\u0435\u043b\u044c</a>"
        ),
        "hidden_forward": "{detective} \u042d\u0442\u043e\u0442 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u0441\u043a\u0440\u044b\u043b \u0441\u0432\u043e\u044e \u043b\u0438\u0447\u043d\u043e\u0441\u0442\u044c.",
        "group_info": (
            "{group} <b>\u0418\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f \u043e \u0447\u0430\u0442\u0435</b>\n\n"
            "{id_} <b>ID:</b> <code>{cid}</code>\n"
            "{name_icon} <b>\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435:</b> {title}\n"
            "{type_icon} <b>\u0422\u0438\u043f:</b> {chat_type}\n"
            "{members} <b>\u0423\u0447\u0430\u0441\u0442\u043d\u0438\u043a\u0438:</b> {count}\n"
            "{at} <b>\u041b\u043e\u0433\u0438\u043d:</b> {username}"
        ),
        "not_group": "{warning} \u042d\u0442\u0430 \u043a\u043e\u043c\u0430\u043d\u0434\u0430 \u0440\u0430\u0431\u043e\u0442\u0430\u0435\u0442 \u0442\u043e\u043b\u044c\u043a\u043e \u0432 \u0433\u0440\u0443\u043f\u043f\u0430\u0445.",
        "bots_title": "{phoenix} <b>\u0411\u043e\u0442\u044b \u044d\u043a\u043e\u0441\u0438\u0441\u0442\u0435\u043c\u044b SLH</b>\n\n",
        "json_title": "{code} <b>JSON \u0434\u0430\u043d\u043d\u044b\u0435</b>\n\n<pre>{data}</pre>",
        "lang_set": "{check} \u042f\u0437\u044b\u043a \u0438\u0437\u043c\u0435\u043d\u0435\u043d: <b>{lang_name}</b>",
        "choose_lang": "{globe} \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u044f\u0437\u044b\u043a:",
        "copy_id": "\u041a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c ID",
        "open_dashboard": "\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u043f\u0430\u043d\u0435\u043b\u044c",
        "share_id": "\u041f\u043e\u0434\u0435\u043b\u0438\u0442\u044c\u0441\u044f ID",
        "help": (
            "{book} <b>\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0435 \u043a\u043e\u043c\u0430\u043d\u0434\u044b:</b>\n\n"
            "/start - \u041f\u043e\u043b\u043d\u0430\u044f \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f\n"
            "/id - \u0411\u044b\u0441\u0442\u0440\u044b\u0439 ID\n"
            "/group - \u0418\u043d\u0444\u043e \u043e \u0433\u0440\u0443\u043f\u043f\u0435\n"
            "/qr - \u0420\u0435\u0444\u0435\u0440\u0430\u043b\u044c\u043d\u0430\u044f \u0441\u0441\u044b\u043b\u043a\u0430\n"
            "/dashboard - \u041e\u0442\u043a\u0440\u044b\u0442\u044c \u043f\u0430\u043d\u0435\u043b\u044c\n"
            "/bots - \u0412\u0441\u0435 \u0431\u043e\u0442\u044b\n"
            "/lang - \u0421\u043c\u0435\u043d\u0438\u0442\u044c \u044f\u0437\u044b\u043a\n"
            "/json - JSON \u0434\u0430\u043d\u043d\u044b\u0435\n"
            "/help - \u041f\u043e\u043c\u043e\u0449\u044c\n\n"
            "{hint} <i>\u041f\u0435\u0440\u0435\u0448\u043b\u0438\u0442\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u0434\u043b\u044f \u0438\u043d\u0444\u043e</i>"
        ),
    },
    "ar": {
        "welcome": (
            "{phoenix} <b>SLH UserInfo Bot</b>\n\n"
            "{wave} \u0645\u0631\u062d\u0628\u0627 <b>{name}</b>!\n\n"
            "{id_} <b>\u0645\u0639\u0631\u0641 \u062a\u0644\u064a\u062c\u0631\u0627\u0645:</b> <code>{uid}</code>\n"
            "{user} <b>\u0627\u0644\u0627\u0633\u0645:</b> {first} {last}\n"
            "{at} <b>\u0627\u0633\u0645 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645:</b> {username}\n"
            "{lang} <b>\u0627\u0644\u0644\u063a\u0629:</b> {language}\n"
            "{premium} <b>\u0645\u0645\u064a\u0632:</b> {is_premium}\n"
            "{bot_icon} <b>\u0628\u0648\u062a:</b> {is_bot}\n"
            "{calendar} <b>\u0627\u0644\u062a\u0627\u0631\u064a\u062e:</b> {date}\n\n"
            "{link} <b>\u0631\u0627\u0628\u0637 \u0644\u0648\u062d\u0629 \u0627\u0644\u062a\u062d\u0643\u0645:</b>\n"
            "<a href=\"{dashboard}?uid={uid}\">{arrow} \u0627\u0641\u062a\u062d SLH Dashboard</a>\n\n"
            "{ref} <b>\u0631\u0627\u0628\u0637 \u0627\u0644\u0625\u062d\u0627\u0644\u0629:</b>\n"
            "<code>https://t.me/SLH_AIR_bot?start=ref_{uid}</code>\n\n"
            "{hint} <i>\u0623\u0639\u062f \u062a\u0648\u062c\u064a\u0647 \u0631\u0633\u0627\u0644\u0629 \u0644\u0644\u062d\u0635\u0648\u0644 \u0639\u0644\u0649 \u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0627\u0644\u0645\u0631\u0633\u0644</i>"
        ),
        "quick_id": "{id_} <b>\u0645\u0639\u0631\u0641\u0643:</b> <code>{uid}</code>\n\n{hint} \u0627\u0646\u0642\u0631 \u0644\u0644\u0646\u0633\u062e",
        "forward_info": (
            "{detective} <b>\u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645</b>\n\n"
            "{id_} <b>ID:</b> <code>{uid}</code>\n"
            "{user} <b>\u0627\u0644\u0627\u0633\u0645:</b> {first} {last}\n"
            "{at} <b>\u0627\u0633\u0645 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645:</b> {username}\n"
            "{bot_icon} <b>\u0628\u0648\u062a:</b> {is_bot}\n\n"
            "{link} <a href=\"{dashboard}?uid={uid}\">\u0639\u0631\u0636 \u0644\u0648\u062d\u0629 \u0627\u0644\u062a\u062d\u0643\u0645</a>"
        ),
        "hidden_forward": "{detective} \u0647\u0630\u0627 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645 \u0623\u062e\u0641\u0649 \u0647\u0648\u064a\u062a\u0647.",
        "group_info": (
            "{group} <b>\u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0627\u0644\u0645\u062d\u0627\u062f\u062b\u0629</b>\n\n"
            "{id_} <b>ID:</b> <code>{cid}</code>\n"
            "{name_icon} <b>\u0627\u0644\u0627\u0633\u0645:</b> {title}\n"
            "{type_icon} <b>\u0627\u0644\u0646\u0648\u0639:</b> {chat_type}\n"
            "{members} <b>\u0627\u0644\u0623\u0639\u0636\u0627\u0621:</b> {count}\n"
            "{at} <b>\u0627\u0633\u0645 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645:</b> {username}"
        ),
        "not_group": "{warning} \u0647\u0630\u0627 \u0627\u0644\u0623\u0645\u0631 \u064a\u0639\u0645\u0644 \u0641\u0642\u0637 \u0641\u064a \u0627\u0644\u0645\u062c\u0645\u0648\u0639\u0627\u062a.",
        "bots_title": "{phoenix} <b>\u0628\u0648\u062a\u0627\u062a \u0646\u0638\u0627\u0645 SLH</b>\n\n",
        "json_title": "{code} <b>\u0628\u064a\u0627\u0646\u0627\u062a JSON</b>\n\n<pre>{data}</pre>",
        "lang_set": "{check} \u062a\u0645 \u062a\u063a\u064a\u064a\u0631 \u0627\u0644\u0644\u063a\u0629: <b>{lang_name}</b>",
        "choose_lang": "{globe} \u0627\u062e\u062a\u0631 \u0627\u0644\u0644\u063a\u0629:",
        "copy_id": "\u0646\u0633\u062e ID",
        "open_dashboard": "\u0641\u062a\u062d \u0644\u0648\u062d\u0629 \u0627\u0644\u062a\u062d\u0643\u0645",
        "share_id": "\u0645\u0634\u0627\u0631\u0643\u0629 ID",
        "help": (
            "{book} <b>\u0627\u0644\u0623\u0648\u0627\u0645\u0631 \u0627\u0644\u0645\u062a\u0627\u062d\u0629:</b>\n\n"
            "/start - \u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0643\u0627\u0645\u0644\u0629\n"
            "/id - \u0645\u0639\u0631\u0641 \u0633\u0631\u064a\u0639\n"
            "/group - \u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0627\u0644\u0645\u062c\u0645\u0648\u0639\u0629\n"
            "/qr - \u0631\u0627\u0628\u0637 \u0627\u0644\u0625\u062d\u0627\u0644\u0629\n"
            "/dashboard - \u0644\u0648\u062d\u0629 \u0627\u0644\u062a\u062d\u0643\u0645\n"
            "/bots - \u0643\u0644 \u0627\u0644\u0628\u0648\u062a\u0627\u062a\n"
            "/lang - \u062a\u063a\u064a\u064a\u0631 \u0627\u0644\u0644\u063a\u0629\n"
            "/json - \u0628\u064a\u0627\u0646\u0627\u062a JSON\n"
            "/help - \u0645\u0633\u0627\u0639\u062f\u0629\n\n"
            "{hint} <i>\u0623\u0639\u062f \u062a\u0648\u062c\u064a\u0647 \u0631\u0633\u0627\u0644\u0629 \u0644\u0644\u0645\u0639\u0644\u0648\u0645\u0627\u062a</i>"
        ),
    },
    "fr": {
        "welcome": (
            "{phoenix} <b>SLH UserInfo Bot</b>\n\n"
            "{wave} Bonjour <b>{name}</b> !\n\n"
            "{id_} <b>ID Telegram :</b> <code>{uid}</code>\n"
            "{user} <b>Nom :</b> {first} {last}\n"
            "{at} <b>Pseudo :</b> {username}\n"
            "{lang} <b>Langue :</b> {language}\n"
            "{premium} <b>Premium :</b> {is_premium}\n"
            "{bot_icon} <b>Bot :</b> {is_bot}\n"
            "{calendar} <b>Date :</b> {date}\n\n"
            "{link} <b>Lien tableau de bord :</b>\n"
            "<a href=\"{dashboard}?uid={uid}\">{arrow} Ouvrir SLH Dashboard</a>\n\n"
            "{ref} <b>Lien de parrainage :</b>\n"
            "<code>https://t.me/SLH_AIR_bot?start=ref_{uid}</code>\n\n"
            "{hint} <i>Transf\u00e9rez un message pour voir les infos de l'exp\u00e9diteur</i>"
        ),
        "quick_id": "{id_} <b>Votre ID :</b> <code>{uid}</code>\n\n{hint} Appuyez pour copier",
        "forward_info": (
            "{detective} <b>Informations utilisateur</b>\n\n"
            "{id_} <b>ID :</b> <code>{uid}</code>\n"
            "{user} <b>Nom :</b> {first} {last}\n"
            "{at} <b>Pseudo :</b> {username}\n"
            "{bot_icon} <b>Bot :</b> {is_bot}\n\n"
            "{link} <a href=\"{dashboard}?uid={uid}\">Voir le tableau de bord</a>"
        ),
        "hidden_forward": "{detective} Cet utilisateur a masqu\u00e9 son identit\u00e9.",
        "group_info": (
            "{group} <b>Informations du chat</b>\n\n"
            "{id_} <b>ID :</b> <code>{cid}</code>\n"
            "{name_icon} <b>Nom :</b> {title}\n"
            "{type_icon} <b>Type :</b> {chat_type}\n"
            "{members} <b>Membres :</b> {count}\n"
            "{at} <b>Pseudo :</b> {username}"
        ),
        "not_group": "{warning} Cette commande ne fonctionne que dans les groupes.",
        "bots_title": "{phoenix} <b>Bots de l'\u00e9cosyst\u00e8me SLH</b>\n\n",
        "json_title": "{code} <b>Donn\u00e9es JSON brutes</b>\n\n<pre>{data}</pre>",
        "lang_set": "{check} Langue chang\u00e9e : <b>{lang_name}</b>",
        "choose_lang": "{globe} Choisir la langue :",
        "copy_id": "Copier ID",
        "open_dashboard": "Ouvrir le tableau de bord",
        "share_id": "Partager ID",
        "help": (
            "{book} <b>Commandes disponibles :</b>\n\n"
            "/start - Informations compl\u00e8tes\n"
            "/id - ID rapide\n"
            "/group - Infos du groupe\n"
            "/qr - Lien de parrainage\n"
            "/dashboard - Tableau de bord SLH\n"
            "/bots - Tous les bots\n"
            "/lang - Changer la langue\n"
            "/json - Donn\u00e9es JSON\n"
            "/help - Aide\n\n"
            "{hint} <i>Transf\u00e9rez un message pour les infos</i>"
        ),
    },
}

# Emoji map
E = {
    "phoenix": "\U0001f525", "wave": "\U0001f44b", "id_": "\U0001f194",
    "user": "\U0001f464", "at": "@", "lang": "\U0001f310",
    "premium": "\u2b50", "bot_icon": "\U0001f916", "calendar": "\U0001f4c5",
    "link": "\U0001f517", "arrow": "\u27a1\ufe0f", "ref": "\U0001f91d",
    "hint": "\U0001f4a1", "detective": "\U0001f575\ufe0f", "group": "\U0001f465",
    "name_icon": "\U0001f4dd", "type_icon": "\U0001f4e2", "members": "\U0001f4ca",
    "warning": "\u26a0\ufe0f", "code": "\U0001f4bb", "check": "\u2705",
    "globe": "\U0001f30d", "book": "\U0001f4d6", "qr": "\U0001f4f1",
}

# User language preferences (in-memory, resets on restart)
user_langs: dict[int, str] = {}

LANG_NAMES = {"he": "\U0001f1ee\U0001f1f1 \u05e2\u05d1\u05e8\u05d9\u05ea", "en": "\U0001f1ec\U0001f1e7 English", "ru": "\U0001f1f7\U0001f1fa \u0420\u0443\u0441\u0441\u043a\u0438\u0439", "ar": "\U0001f1f8\U0001f1e6 \u0627\u0644\u0639\u0631\u0628\u064a\u0629", "fr": "\U0001f1eb\U0001f1f7 Fran\u00e7ais"}

# ============================================================
# HELPERS
# ============================================================
def get_lang(user_id: int, tg_lang: str = None) -> str:
    if user_id in user_langs:
        return user_langs[user_id]
    if tg_lang and tg_lang in T:
        return tg_lang
    return "he"

def tr(user_id: int, key: str, tg_lang: str = None, **kwargs) -> str:
    lang = get_lang(user_id, tg_lang)
    template = T.get(lang, T["en"]).get(key, T["en"].get(key, key))
    merged = {**E, **kwargs}
    return template.format_map(merged)

def user_keyboard(uid: int) -> InlineKeyboardMarkup:
    lang = get_lang(uid)
    strings = T.get(lang, T["en"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"\U0001f4cb {strings['copy_id']}", callback_data=f"copy_{uid}"),
            InlineKeyboardButton(text=f"\U0001f310 {strings['open_dashboard']}", url=f"{DASHBOARD_URL}?uid={uid}"),
        ],
        [
            InlineKeyboardButton(text=f"\U0001f4e4 {strings['share_id']}", switch_inline_query=f"My Telegram ID: {uid}"),
            InlineKeyboardButton(text="\U0001f310 /lang", callback_data="lang_menu"),
        ],
    ])

BOTS = [
    ("\U0001f48e", "SLH Investment", "@SLH_AIR_bot", "https://t.me/SLH_AIR_bot"),
    ("\U0001f6d2", "OsifShop", "@OsifShop_bot", "https://t.me/OsifShop_bot"),
    ("\U0001f3a8", "NFTY Market", "@NIFTI_Publisher_Bot", "https://t.me/NIFTI_Publisher_Bot"),
    ("\U0001f6e1\ufe0f", "Guardian", "@SLH_Guardian_bot", "https://t.me/SLH_Guardian_bot"),
    ("\U0001f393", "Academia", "@SLH_Academia_bot", "https://t.me/SLH_Academia_bot"),
    ("\U0001f4b0", "Wallet", "@SLH_Wallet_bot", "https://t.me/SLH_Wallet_bot"),
    ("\U0001f3ed", "Factory", "@SLH_Factory_bot", "https://t.me/SLH_Factory_bot"),
    ("\U0001f4e2", "Campaign", "@SLH_Campaign_bot", "https://t.me/SLH_Campaign_bot"),
    ("\U0001f3ae", "Game Bot", "@G4meb0t_bot_bot", "https://t.me/G4meb0t_bot_bot"),
    ("\U0001f3b2", "Chance Pais", "@Chance_Pais_bot", "https://t.me/Chance_Pais_bot"),
    ("\U0001fa99", "SLH TON", "@SLH_ton_bot", "https://t.me/SLH_ton_bot"),
    ("\u26a1", "TON MNH", "@TON_MNH_bot", "https://t.me/TON_MNH_bot"),
    ("\U0001f389", "SLH Fun", "@SLH_community_bot", "https://t.me/SLH_community_bot"),
    ("\U0001f6cd\ufe0f", "BotShop", "@BotShop_bot", "https://t.me/BotShop_bot"),
    ("\U0001f3ad", "Selha", "@Slh_selha_bot", "https://t.me/Slh_selha_bot"),
    ("\U0001f527", "Admin", "@MY_SUPER_ADMIN_bot", "https://t.me/MY_SUPER_ADMIN_bot"),
]

# ============================================================
# HANDLERS
# ============================================================

@dp.message(CommandStart())
async def start_cmd(m: types.Message):
    u = m.from_user
    text = tr(u.id, "welcome", u.language_code,
        name=u.first_name,
        uid=u.id,
        first=u.first_name or "",
        last=u.last_name or "",
        username=f"@{u.username}" if u.username else "---",
        language=u.language_code or "---",
        is_premium="\u2705" if u.is_premium else "\u274c",
        is_bot="\u2705" if u.is_bot else "\u274c",
        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        dashboard=DASHBOARD_URL,
    )
    await m.answer(text, reply_markup=user_keyboard(u.id), disable_web_page_preview=True)
    logger.info("START from %s (%s)", u.id, u.username)


@dp.message(Command("id"))
async def id_cmd(m: types.Message):
    text = tr(m.from_user.id, "quick_id", m.from_user.language_code, uid=m.from_user.id)
    await m.answer(text)


@dp.message(Command("help"))
async def help_cmd(m: types.Message):
    text = tr(m.from_user.id, "help", m.from_user.language_code)
    await m.answer(text)


@dp.message(Command("group"))
async def group_cmd(m: types.Message):
    if m.chat.type == ChatType.PRIVATE:
        await m.answer(tr(m.from_user.id, "not_group", m.from_user.language_code))
        return

    try:
        count = await bot.get_chat_member_count(m.chat.id)
    except Exception:
        count = "?"

    text = tr(m.from_user.id, "group_info", m.from_user.language_code,
        cid=m.chat.id,
        title=m.chat.title or "---",
        chat_type=m.chat.type,
        count=count,
        username=f"@{m.chat.username}" if m.chat.username else "---",
    )
    await m.answer(text)


@dp.message(Command("bots"))
async def bots_cmd(m: types.Message):
    text = tr(m.from_user.id, "bots_title", m.from_user.language_code)
    for emoji, name, handle, url in BOTS:
        text += f"{emoji} <a href=\"{url}\">{name}</a> - {handle}\n"
    await m.answer(text, disable_web_page_preview=True)


@dp.message(Command("dashboard"))
async def dashboard_cmd(m: types.Message):
    uid = m.from_user.id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\U0001f310 Open SLH Dashboard",
            url=f"{DASHBOARD_URL}?uid={uid}"
        )]
    ])
    await m.answer(
        f"\U0001f517 <b>Dashboard Link</b>\n\n"
        f"<a href=\"{DASHBOARD_URL}?uid={uid}\">{DASHBOARD_URL}?uid={uid}</a>",
        reply_markup=kb, disable_web_page_preview=True,
    )


@dp.message(Command("qr"))
async def qr_cmd(m: types.Message):
    uid = m.from_user.id
    ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{uid}"
    await m.answer(
        f"\U0001f91d <b>Referral Link</b>\n\n"
        f"<code>{ref_link}</code>\n\n"
        f"\U0001f4a1 Share this link to earn 10% commission on direct referrals + up to 10 generations!",
        disable_web_page_preview=True,
    )


@dp.message(Command("json"))
async def json_cmd(m: types.Message):
    data = {
        "id": m.from_user.id,
        "is_bot": m.from_user.is_bot,
        "first_name": m.from_user.first_name,
        "last_name": m.from_user.last_name,
        "username": m.from_user.username,
        "language_code": m.from_user.language_code,
        "is_premium": m.from_user.is_premium,
    }
    if m.chat.type != ChatType.PRIVATE:
        data["chat"] = {
            "id": m.chat.id,
            "type": m.chat.type,
            "title": m.chat.title,
            "username": m.chat.username,
        }
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    text = tr(m.from_user.id, "json_title", m.from_user.language_code, data=json_str)
    await m.answer(text)


@dp.message(Command("lang"))
async def lang_cmd(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"setlang_{code}")]
        for code, name in LANG_NAMES.items()
    ])
    text = tr(m.from_user.id, "choose_lang", m.from_user.language_code)
    await m.answer(text, reply_markup=kb)


# === CALLBACK HANDLERS ===

@dp.callback_query(F.data.startswith("setlang_"))
async def setlang_cb(cb: types.CallbackQuery):
    lang = cb.data.replace("setlang_", "")
    if lang in T:
        user_langs[cb.from_user.id] = lang
        text = tr(cb.from_user.id, "lang_set", lang_name=LANG_NAMES.get(lang, lang))
        await cb.message.edit_text(text)
    await cb.answer()


@dp.callback_query(F.data.startswith("copy_"))
async def copy_cb(cb: types.CallbackQuery):
    uid = cb.data.replace("copy_", "")
    await cb.answer(f"ID: {uid}", show_alert=True)


@dp.callback_query(F.data == "lang_menu")
async def lang_menu_cb(cb: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"setlang_{code}")]
        for code, name in LANG_NAMES.items()
    ])
    text = tr(cb.from_user.id, "choose_lang")
    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()


# === FORWARDED MESSAGE HANDLER ===

@dp.message(F.forward_origin)
async def forwarded_msg(m: types.Message):
    origin = m.forward_origin
    # MessageOriginUser - has sender_user
    if hasattr(origin, "sender_user") and origin.sender_user:
        fu = origin.sender_user
        text = tr(m.from_user.id, "forward_info", m.from_user.language_code,
            uid=fu.id,
            first=fu.first_name or "",
            last=fu.last_name or "",
            username=f"@{fu.username}" if fu.username else "---",
            is_bot="\u2705" if fu.is_bot else "\u274c",
            dashboard=DASHBOARD_URL,
        )
        await m.answer(text, disable_web_page_preview=True)
    else:
        # Hidden or channel forward
        text = tr(m.from_user.id, "hidden_forward", m.from_user.language_code)
        # Try to extract what we can
        if hasattr(origin, "sender_user_name"):
            text += f"\n\n\U0001f464 <b>Name:</b> {origin.sender_user_name}"
        if hasattr(origin, "chat") and origin.chat:
            text += f"\n\U0001f4e2 <b>Channel:</b> {origin.chat.title} (ID: <code>{origin.chat.id}</code>)"
        await m.answer(text)


# === INLINE MODE ===

@dp.inline_query()
async def inline_handler(query: InlineQuery):
    uid = query.from_user.id
    uname = query.from_user.username or "user"
    name = query.from_user.first_name or "User"

    results = [
        InlineQueryResultArticle(
            id="myid",
            title=f"My ID: {uid}",
            description=f"{name} (@{uname})",
            input_message_content=InputTextMessageContent(
                message_text=(
                    f"\U0001f194 <b>Telegram ID:</b> <code>{uid}</code>\n"
                    f"\U0001f464 <b>Name:</b> {name}\n"
                    f"@ <b>Username:</b> @{uname}\n\n"
                    f"\U0001f517 <a href=\"{DASHBOARD_URL}?uid={uid}\">SLH Dashboard</a>"
                ),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            ),
        ),
        InlineQueryResultArticle(
            id="reflink",
            title="My Referral Link",
            description=f"https://t.me/SLH_AIR_bot?start=ref_{uid}",
            input_message_content=InputTextMessageContent(
                message_text=(
                    f"\U0001f91d <b>Join SLH Ecosystem!</b>\n\n"
                    f"https://t.me/SLH_AIR_bot?start=ref_{uid}\n\n"
                    f"\U0001f4b0 4%-65% APY | \U0001f6d2 SaaS | \U0001f3a8 NFT | \U0001f3ae Games"
                ),
                parse_mode=ParseMode.HTML,
            ),
        ),
    ]
    await query.answer(results, cache_time=30, is_personal=True)


# ============================================================
# MAIN
# ============================================================
async def main():
    me = await bot.get_me()
    logger.info("=" * 50)
    logger.info("SLH UserInfo Bot | @%s", me.username)
    logger.info("=" * 50)
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
