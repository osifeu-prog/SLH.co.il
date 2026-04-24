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

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

import auth
import session

# Choose AI client: if ANTHROPIC_API_KEY is set, use paid Anthropic (with tool use);
# otherwise fall back to the free SLH multi-provider endpoint (chat-only, Groq/Gemini).
if os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-"):
    import claude_client as ai_client
    _AI_MODE = "anthropic-tools"
else:
    import free_ai_client as ai_client
    _AI_MODE = "slh-multiprovider-free"

API_BASE = os.getenv("SLH_API_BASE", "https://slh-api-production.up.railway.app")
ADMIN_KEY = os.getenv("ADMIN_API_KEY", "")
TASK_BOARD_PATH = os.getenv(
    "TASK_BOARD_PATH",
    os.path.join(HERE, "..", "ops", "TASK_BOARD.md"),
)

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
        "שלום עוסיף\\. אני SLH Claude \\(mode: `" + _AI_MODE + "`\\)\\.\n\n"
        "*פקודות מהירות \\(ללא עלות\\):*\n"
        "`/ps` `/bots` `/logs <name>` `/git` `/health` `/price` `/devices` `/task <טקסט>`\n\n"
        "*שיחה חופשית:*\n"
        "כל טקסט אחר → AI \\(groq/gemini חינם כרגע\\)\n\n"
        "עוד עזרה: `/help`"
    )


@dp.message(Command("help"))
async def cmd_help(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    await msg.answer(
        "*פקודות Direct \\(ללא AI, מיידי\\):*\n"
        "/ps — רשימת containers רצים\n"
        "/bots — ספירה של bot fleet \\+ סטטוס\n"
        "/logs \\<name\\> — 25 שורות אחרונות של container\n"
        "/git \\<status\\|log\\|diff\\|branch\\> \\[website\\]\n"
        "/health — בריאות ה\\-API \\+ DB\n"
        "/price — מחירי SLH/MNH/ZVK\n"
        "/devices — רשימת ESP\\-ים מחוברים\n"
        "/task \\<טקסט\\> — הוסף למשימות\n"
        "/ai\\_mode — מה מצב ה\\-AI כרגע\n\n"
        "*שיחה חופשית \\(AI\\):*\n"
        f"כל טקסט אחר מופעל ב\\-AI \\({_AI_MODE}\\)\\.\n"
        "אם ANTHROPIC\\_API\\_KEY לא מוגדר — משתמש ב\\-groq\\+gemini \\(חינם\\)\\.\n\n"
        "*דוגמאות:*\n"
        "• `/ps` — מי רץ עכשיו?\n"
        "• `/logs slh\\-guardian\\-bot`\n"
        "• `/git status website`\n"
        "• \"מה הכי דחוף לעשות עכשיו?\""
    )


# ---------- Phase 1: direct API handlers (no Claude, no $ cost) ----------

async def _http_get_json(path: str, headers: dict | None = None) -> dict:
    """Thin httpx wrapper. Raises on non-2xx."""
    url = path if path.startswith("http") else API_BASE + path
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(url, headers=headers or {})
        resp.raise_for_status()
        return resp.json()


def _escape_md(text: str) -> str:
    """Escape MarkdownV1 special chars inside values."""
    if not isinstance(text, str):
        text = str(text)
    # aiogram default is MARKDOWN (v1) — escape only `_*`[
    return (
        text.replace("_", "\\_")
        .replace("*", "\\*")
        .replace("`", "\\`")
        .replace("[", "\\[")
    )


@dp.message(Command("health"))
async def cmd_health(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    try:
        h = await _http_get_json("/api/health")
        api_ok = h.get("status") == "ok" or h.get("api") == "ok"
        db = h.get("db") or (h.get("checks") or {}).get("db") or "unknown"
        lines = [
            f"*API:* {'חי ✓' if api_ok else 'כבוי ✗'}",
            f"*DB:* `{_escape_md(db)}`",
        ]
        if "version" in h:
            lines.append(f"*גרסה:* `{_escape_md(h['version'])}`")
        if "timestamp" in h:
            lines.append(f"*בדוק ב:* `{_escape_md(h['timestamp'])}`")
        await msg.answer("\n".join(lines))
    except httpx.HTTPStatusError as e:
        await msg.answer(f"ה-API החזיר {e.response.status_code}. כנראה down.")
    except Exception as e:
        log.exception("/health failed")
        await msg.answer(f"שגיאה: `{_escape_md(type(e).__name__)}: {_escape_md(str(e))}`")


@dp.message(Command("price"))
async def cmd_price(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    try:
        p = await _http_get_json("/api/prices")
        prices = p.get("prices") or p
        if not isinstance(prices, dict) or not prices:
            await msg.answer("אין נתוני מחיר כרגע.")
            return
        lines = ["*מחירים \\(₪\\):*"]
        for token, value in prices.items():
            # /api/prices returns {ils, usd} objects; fall back to scalar if not
            if isinstance(value, dict):
                ils = value.get("ils") or value.get("price") or value.get("value")
            else:
                ils = value
            try:
                fmt = f"{float(ils):,.2f}"
            except (TypeError, ValueError):
                fmt = str(ils)
            lines.append(f"• *{_escape_md(token)}:* `{fmt}`")
        await msg.answer("\n".join(lines))
    except Exception as e:
        log.exception("/price failed")
        await msg.answer(f"שגיאה: `{_escape_md(str(e))}`")


@dp.message(Command("devices"))
async def cmd_devices(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    if not ADMIN_KEY:
        await msg.answer("חסר `ADMIN_API_KEY` ב-.env של הבוט.")
        return
    try:
        d = await _http_get_json(
            "/api/admin/devices/list", headers={"X-Admin-Key": ADMIN_KEY}
        )
        devices = d.get("devices") or d if isinstance(d, (list, dict)) else []
        if not devices:
            await msg.answer("אין מכשירים רשומים.")
            return
        lines = [f"*מכשירים \\({len(devices)}\\):*"]
        for dev in devices[:10]:
            dev_id = dev.get("device_id") or dev.get("id") or "?"
            last_seen = dev.get("last_seen_at") or dev.get("last_heartbeat") or "--"
            online = dev.get("online") or dev.get("is_online")
            mark = "🟢" if online else "⚫"
            lines.append(
                f"{mark} `{_escape_md(str(dev_id))}` · {_escape_md(str(last_seen))}"
            )
        if len(devices) > 10:
            lines.append(f"_\\+ {len(devices) - 10} נוספים_")
        await msg.answer("\n".join(lines))
    except httpx.HTTPStatusError as e:
        await msg.answer(f"admin API החזיר {e.response.status_code}.")
    except Exception as e:
        log.exception("/devices failed")
        await msg.answer(f"שגיאה: `{_escape_md(str(e))}`")


@dp.message(Command("task"))
async def cmd_task(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    # Everything after the /task command word
    text = (msg.text or "").split(maxsplit=1)
    if len(text) < 2 or not text[1].strip():
        await msg.answer("שימוש: `/task \\<תיאור המשימה\\>`")
        return
    task_text = text[1].strip()
    try:
        import datetime

        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        line = f"- [ ] {task_text}  _(added {ts} via bot)_\n"
        os.makedirs(os.path.dirname(TASK_BOARD_PATH), exist_ok=True)
        with open(TASK_BOARD_PATH, "a", encoding="utf-8") as f:
            f.write(line)
        await msg.answer(
            f"נוסף ל\\-TASK\\_BOARD\\.md:\n`{_escape_md(task_text)}`"
        )
    except Exception as e:
        log.exception("/task failed")
        await msg.answer(f"שגיאה: `{_escape_md(str(e))}`")


@dp.message(Command("status"))
async def cmd_status(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    await msg.answer("מבצע בדיקת מצב מהירה...")
    try:
        reply, new_msgs = await ai_client.converse(
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


# ---------- Direct executor commands (no AI, no cost) ----------
import subprocess

_SAFE_EXEC_ALLOWLIST = {
    "docker ps", "docker compose ps", "docker stats --no-stream",
    "git status", "git log --oneline -10", "git diff --stat",
    "df -h", "uptime", "uname -a",
}


def _run_cmd(cmd: str, timeout: int = 15) -> str:
    """Run a shell command and return stdout+stderr, capped."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd="/workspace",
        )
        out = (result.stdout or "") + (result.stderr or "")
        return out[:3500] or "(no output)"
    except subprocess.TimeoutExpired:
        return f"⏱ command timed out after {timeout}s"
    except Exception as e:
        return f"⚠️ {type(e).__name__}: {e}"


@dp.message(Command("ps"))
async def cmd_ps(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    out = _run_cmd("docker ps --format 'table {{.Names}}\\t{{.Status}}'")
    await msg.answer(f"```\n{out}\n```")


@dp.message(Command("logs"))
async def cmd_logs(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    parts = (msg.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("שימוש: `/logs \\<container\\-name\\>`  \nלמשל: `/logs slh\\-claude\\-bot`")
        return
    name = parts[1].strip().replace(";", "").replace("&", "").replace("|", "")
    # Allowlist prefix check
    if not name.startswith(("slh-", "slh_")):
        await msg.answer("רק containers עם prefix `slh-` מותרים.")
        return
    out = _run_cmd(f"docker logs {name} --tail 25 2>&1")
    await msg.answer(f"*logs {name}:*\n```\n{out[-3500:]}\n```")


@dp.message(Command("git"))
async def cmd_git(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    parts = (msg.text or "").split(maxsplit=1)
    subcmd = (parts[1].strip() if len(parts) > 1 else "status").split()[0]
    safe_subs = {"status", "log", "diff", "branch"}
    if subcmd not in safe_subs:
        await msg.answer(f"פקודת git מותרות בלבד: {', '.join(safe_subs)}")
        return
    repo_hint = (parts[1].strip() if len(parts) > 1 else "")
    repo = "website" if "website" in repo_hint else "."
    if subcmd == "log":
        out = _run_cmd(f"cd {repo} && git log --oneline -10")
    elif subcmd == "diff":
        out = _run_cmd(f"cd {repo} && git diff --stat")
    elif subcmd == "branch":
        out = _run_cmd(f"cd {repo} && git branch --show-current")
    else:
        out = _run_cmd(f"cd {repo} && git status -s")
    await msg.answer(f"*git {subcmd} @ {repo}:*\n```\n{out}\n```")


@dp.message(Command("bots"))
async def cmd_bots(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    out = _run_cmd("docker ps --format '{{.Names}}' | grep ^slh- | sort | wc -l")
    running = out.strip()
    out_list = _run_cmd("docker ps --format '{{.Names}}: {{.Status}}' | grep ^slh- | sort")
    await msg.answer(
        f"*Bot fleet: {running} רצים*\n```\n{out_list[:3500]}\n```"
    )


@dp.message(Command("ai_mode"))
async def cmd_ai_mode(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    await msg.answer(
        f"*AI mode:* `{_AI_MODE}`\n\n"
        f"{'✅ Anthropic Claude עם tool use (עולה כסף)' if _AI_MODE == 'anthropic-tools' else '✅ SLH multi-provider (Groq/Gemini חינם)'}"
    )


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
        reply, new_msgs = await ai_client.converse(hist, text)
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
