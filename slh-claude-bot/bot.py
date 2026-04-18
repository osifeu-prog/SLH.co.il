"""@SLH_Claude_bot — aiogram entrypoint.

Routes every text message from Osif to Claude with workspace tools.
Guards with Telegram ID allowlist. Persists conversation per chat.
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

# Load .env from the bot directory (slh-claude-bot/.env)
HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, ".env"))

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

import auth
import session
import claude_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("slh-claude-bot")

TOKEN = os.getenv("SLH_CLAUDE_BOT_TOKEN")
if not TOKEN:
    raise SystemExit("SLH_CLAUDE_BOT_TOKEN not set. See .env.example.")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()


# Telegram messages are capped at 4096 chars; split long replies
def _chunks(text: str, size: int = 4000) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [text]


@dp.message(Command("start"))
async def cmd_start(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    await msg.answer(
        "שלום עוסיף. אני SLH Claude — הגשר שלך לניהול המערכת מהטלגרם.\n\n"
        "*מה אני יודע לעשות:*\n"
        "• לקרוא קבצים מ-D:\\\\SLH\\_ECOSYSTEM\n"
        "• להריץ git / docker / curl\n"
        "• לבדוק את ה-API ב-Railway\n"
        "• לזכור את השיחה בינינו\n\n"
        "תן לי משימה בעברית ואני מבצע.\n"
        "פקודות: /clear — מחק היסטוריה, /status — בדיקת מצב, /help — עזרה"
    )


@dp.message(Command("help"))
async def cmd_help(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    await msg.answer(
        "*פקודות:*\n"
        "/start — פתיחה\n"
        "/status — בדוק API+git+docker\n"
        "/clear — מחק היסטוריית שיחה\n"
        "/help — המסך הזה\n\n"
        "*דוגמאות למשימות:*\n"
        "• \"בדוק את הבריאות של ה-API\"\n"
        "• \"הראה לי את 30 השורות הראשונות של CLAUDE.md\"\n"
        "• \"מה סטטוס הגיט?\"\n"
        "• \"אילו קונטיינרים רצים?\""
    )


@dp.message(Command("status"))
async def cmd_status(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    await msg.answer("מבצע בדיקת מצב מהירה...")
    try:
        reply, new_msgs = await claude_client.converse(
            history=[],
            user_text="בצע בדיקה מהירה: 1) curl ל-/api/health של Railway, 2) git status בשני ה-repos (D:\\SLH_ECOSYSTEM ו-D:\\SLH_ECOSYSTEM\\website), 3) docker ps. תן סיכום של 3-5 שורות בעברית.",
        )
        for msg_part in new_msgs:
            await session.append(msg.chat.id, msg_part["role"], msg_part["content"])
        for chunk in _chunks(reply):
            await msg.answer(chunk)
    except Exception as e:
        log.exception("status failed")
        await msg.answer(f"שגיאה: `{type(e).__name__}: {e}`")


@dp.message(Command("clear"))
async def cmd_clear(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    n = await session.clear(msg.chat.id)
    await msg.answer(f"נוקה. נמחקו {n} הודעות.")


@dp.message(F.text)
async def on_text(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    text = msg.text or ""
    if not text.strip():
        return

    # Show "typing" while we think
    await bot.send_chat_action(msg.chat.id, "typing")

    try:
        hist = await session.history(msg.chat.id)
        reply, new_msgs = await claude_client.converse(hist, text)
        for m in new_msgs:
            await session.append(msg.chat.id, m["role"], m["content"])
        for chunk in _chunks(reply):
            await msg.answer(chunk)
    except Exception as e:
        log.exception("converse failed")
        err = f"שגיאה: `{type(e).__name__}: {e}`"
        if "ANTHROPIC_API_KEY" in str(e):
            err += "\n\nצריך להוסיף ANTHROPIC\\_API\\_KEY ל-slh-claude-bot/.env"
        await msg.answer(err)


async def main() -> None:
    await session.init_db()
    log.info("starting @SLH_Claude_bot")
    me = await bot.get_me()
    log.info(f"connected as @{me.username} (id={me.id})")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
