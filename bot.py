"""@SLH_Claude_bot ׳’ג‚¬ג€ aiogram entrypoint.

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
import quota
import subscriptions
import payment_flow
import admin_panel

# Defensive import ׳’ג‚¬ג€ anthropic may not be installed in all environments.
try:
    from anthropic import BadRequestError as AnthropicBadRequest
except ImportError:
    class AnthropicBadRequest(Exception):
        pass

# Two AI clients available simultaneously:
# - free_ai_client (Groq/Gemini): always loaded, used for Free tier
# - claude_client (Anthropic+tools): loaded only if ANTHROPIC_API_KEY set,
#   used for Pro/VIP tiers
# `quota.check()` per-message decides which one to call based on user's tier.
import free_ai_client as _free_client
_anthropic_available = os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-")
if _anthropic_available:
    import claude_client as _claude_client
    _AI_MODE = "anthropic-tools+free-fallback"
else:
    _claude_client = None
    _AI_MODE = "free-only (set ANTHROPIC_API_KEY to enable paid tiers)"


def _pick_ai_client(use_anthropic: bool):
    """Returns (client_module, provider_name, model_name)."""
    if use_anthropic and _claude_client is not None:
        return _claude_client, "anthropic", os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    return _free_client, "free", "groq/gemini"

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


# ---------- Cross-bot coordination (shared agents group) ----------
# Registers BEFORE the @dp.message handlers below so coord group messages
# don't get swallowed by the F.text catch-all on_text() handler. No-op when
# COORDINATION_GROUP_CHAT_ID is unset. See shared/coordination.py.
import sys as _sys
_WORKSPACE_ROOT = "/workspace" if os.path.isdir("/workspace/shared") else os.path.abspath(os.path.join(HERE, ".."))
if _WORKSPACE_ROOT not in _sys.path:
    _sys.path.insert(0, _WORKSPACE_ROOT)
try:
    from shared import coordination as _coord
    log.info("shared.coordination loaded; enabled=%s", _coord.is_enabled())
except Exception as _coord_err:
    _coord = None
    log.warning("shared.coordination not loadable: %s", _coord_err)


_BOT_USERNAME_FOR_COORD = os.getenv("SLH_CLAUDE_BOT_USERNAME", "SLH_Claude_bot").lstrip("@")


async def _coord_ping(msg) -> None:
    await msg.reply("pong")


async def _coord_health_handler(msg) -> None:
    try:
        h = await _http_get_json("/api/health")
        await msg.reply(
            f"[OK] API: {h.get('status','?')} ײ²ֲ· DB: {h.get('db','?')} ײ²ֲ· v{h.get('version','?')}"
        )
    except Exception as e:
        await msg.reply(f"[X!] {type(e).__name__}: {e}")


async def _coord_who_handler(msg) -> None:
    me = await bot.get_me()
    await msg.reply(f"[i] @{me.username} (claude-bot) ײ²ֲ· AI={_AI_MODE}")


if _coord is not None:
    _coord.register_inbound(
        dp,
        _BOT_USERNAME_FOR_COORD,
        handlers={
            "ping": _coord_ping,
            "health": _coord_health_handler,
            "who": _coord_who_handler,
        },
    )


# Telegram messages are capped at 4096 chars; split long replies
def _chunks(text: str, size: int = 4000) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [text]


@dp.message(Command("start"))
async def cmd_start(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    # Lazy-create subscription row + show tier
    try:
        sub = await subscriptions.get_or_create(msg.from_user.id)
        tier_line = f"׳ ֲג€™ֲ Tier: {sub.tier} ײ²ֲ· {sub.messages_used_this_period} ׳³ג€׳³ג€¢׳³ג€׳³ֲ¢׳³ג€¢׳³ֳ- ׳³ג€׳ֲ¿ֲ½-׳³ג€¢׳³ג€׳³ֲ©\n"
    except Exception:
        tier_line = ""
    # Send as plain text (no parse_mode) to avoid backslash pollution.
    await msg.answer(
        f"׳³ֲ©׳³ֲ׳³ג€¢׳³ֲ ׳³ֲ׳³ג€¢׳³ֲ¡׳³ג„¢׳³ֲ£ ׳ ֲג€˜ג€¹\n"
        f"׳³ֲ׳³ֲ ׳³ג„¢ SLH Claude ׳’ג‚¬ג€ ׳³ֲ׳³ֲ¦׳³ג€˜: {_AI_MODE}\n"
        f"{tier_line}\n"
        f"׳’ג€ֲ׳’ג€ֲ׳’ג€ֲ AI Spark ׳’ג€ֲ׳’ג€ֲ׳’ג€ֲ\n"
        f"/upgrade   ׳’ג‚¬ג€ ׳³ֲ©׳³ג€׳³ֲ¨׳³ג€¢׳³ג€™ ׳³ֲ-Pro/VIP\n"
        f"/credits   ׳’ג‚¬ג€ ׳³ֲ׳³ג€÷׳³ֲ¡׳³ג€ ׳³ג€“׳³ֲ׳³ג„¢׳³ֲ ׳³ג€ ׳³ג€׳ֲ¿ֲ½-׳³ג€¢׳³ג€׳³ֲ©\n"
        f"/pricing   ׳’ג‚¬ג€ ׳³ג€׳³ֲ©׳³ג€¢׳³ג€¢׳³ֲ׳³ֳ- ׳ֲ¿ֲ½-׳³ג€˜׳³ג„¢׳³ֲ׳³ג€¢׳³ֳ-\n\n"
        f"׳’ג€ֲ׳’ג€ֲ׳’ג€ֲ ׳³ג€׳³ג€÷׳³ג„¢ ׳³ֲ©׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ©׳³ג„¢ ׳’ג€ֲ׳’ג€ֲ׳’ג€ֲ\n"
        f"/control   ׳’ג‚¬ג€ ׳³ֲ¡׳³ג„¢׳³ג€÷׳³ג€¢׳³ֲ ׳³ֲ׳³ֲ¢׳³ֲ¨׳³ג€÷׳³ֳ- ׳³ג€˜׳³ֲ©׳³ג€¢׳³ֲ¨׳³ג€ ׳³ֲ׳ֲ¿ֲ½-׳³ֳ-\n"
        f"/health    ׳’ג‚¬ג€ ׳³ג€˜׳³ֲ¨׳³ג„¢׳³ֲ׳³ג€¢׳³ֳ- API + DB\n"
        f"/swarm     ׳’ג‚¬ג€ 4 ׳³ג€׳³ֲ׳³ג€÷׳³ֲ©׳³ג„¢׳³ֲ¨׳³ג„¢׳³ֲ ׳³ֲ©׳³ֲ׳³ֲ\n"
        f"/devices   ׳’ג‚¬ג€ ׳³ֲ¨׳³ֲ©׳³ג„¢׳³ֲ׳³ֳ- ESP ׳³ֲ׳ֲ¿ֲ½-׳³ג€¢׳³ג€˜׳³ֲ¨׳³ג„¢׳³ֲ\n"
        f"/price     ׳’ג‚¬ג€ ׳³ֲ׳ֲ¿ֲ½-׳³ג„¢׳³ֲ¨׳³ג„¢ SLH/MNH/ZVK\n\n"
        f"׳’ג€ֲ׳’ג€ֲ׳’ג€ֲ Admin ׳’ג€ֲ׳’ג€ֲ׳’ג€ֲ\n"
        f"/revenue        ׳’ג‚¬ג€ MRR + ׳³ֲ¨׳³ג€¢׳³ג€¢׳ֲ¿ֲ½- 30 ׳³ג„¢׳³ג€¢׳³ֲ\n"
        f"/anthropic_spend ׳’ג‚¬ג€ ׳³ֲ¢׳³ֲ׳³ג€¢׳³ֳ- AI\n"
        f"/top_users      ׳’ג‚¬ג€ Top 10 ׳³ֲ׳³ג‚×׳³ג„¢ ׳³ֲ©׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ©\n"
        f"/quota_user <id> ׳’ג‚¬ג€ ׳³ג€˜׳³ג€׳³ג„¢׳³ֲ§׳³ג€ ׳³ֲ׳³ֲ׳³ֲ©׳³ֳ-׳³ֲ׳³ֲ© ׳³ֲ¡׳³ג‚×׳³ֲ¦׳³ג„¢׳³ג‚×׳³ג„¢\n\n"
        f"׳’ג€ֲ׳’ג€ֲ׳’ג€ֲ Ops ׳’ג€ֲ׳’ג€ֲ׳’ג€ֲ\n"
        f"/ps  /bots  /logs <X>  /git  /task <X>\n\n"
        f"׳’ג€ֲ׳’ג€ֲ׳’ג€ֲ ׳³ֲ©׳³ג„¢׳ֲ¿ֲ½-׳³ג€ ׳ֲ¿ֲ½-׳³ג€¢׳³ג‚×׳³ֲ©׳³ג„¢׳³ֳ- ׳’ג€ֲ׳’ג€ֲ׳’ג€ֲ\n"
        f"׳³ג€÷׳³ֲ ׳³ֻ׳³ֲ§׳³ֲ¡׳³ֻ ׳³ֲ׳ֲ¿ֲ½-׳³ֲ¨ ׳’ג€ ג€™ AI ׳³ֲ׳³ג‚×׳³ג„¢ ׳³ג€-tier ׳³ֲ©׳³ֲ׳³ֲ\n\n"
        f"׳³ֲ¢׳³ג€“׳³ֲ¨׳³ג€ ׳³ֲ׳³ֲ׳³ֲ׳³ג€: /help",
        parse_mode=None,
    )


@dp.message(Command("help"))
async def cmd_help(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    await msg.answer(
        "*׳ ֲג‚×ג€“ ׳³ג‚×׳³ֲ§׳³ג€¢׳³ג€׳³ג€¢׳³ֳ- Ops \\(׳³ֲ׳³ג„¢׳³ג„¢׳³ג€׳³ג„¢, ׳³ֲ׳³ֲ׳³ֲ AI\\):*\n"
        "`/ps` `/bots` `/logs <name>` `/git` `/health` `/price` `/devices` `/task` `/ai_mode`\n\n"
        "*׳ ֲג€÷ֲ  ׳³ג‚×׳³ֲ§׳³ג€¢׳³ג€׳³ג€¢׳³ֳ- ׳³ֲ¢׳³ג€¢׳³ֲ¨׳³ֲ \\(׳³ֲ©׳³ֲ׳³ג„¢׳³ֻ׳³ג€ ׳³ג€˜׳³ֲ׳³ֳ-׳³ֲ¨\\):*\n"
        "`/cat` `/ls` `/grep` `/find`\n"
        "`/append` `/replace` `/newpage`\n"
        "`/commit` `/push` `/sync`\n"
        "`/draft` `/apply` `/reject`\n"
        "׳³ג‚×׳³ג„¢׳³ֲ¨׳³ג€¢׳³ֻ ׳³ֲ׳³ֲ׳³ֲ: `/editor`\n\n"
        f"*׳ ֲֲ§ֲ  ׳³ֲ©׳³ג„¢׳ֲ¿ֲ½-׳³ג€ ׳ֲ¿ֲ½-׳³ג€¢׳³ג‚×׳³ֲ©׳³ג„¢׳³ֳ- \\(AI: {_AI_MODE}\\):*\n"
        "׳³ג€÷׳³ֲ ׳³ֻ׳³ֲ§׳³ֲ¡׳³ֻ ׳³ֲ׳ֲ¿ֲ½-׳³ֲ¨ ׳³ֲ ׳³ֲ¢׳³ֲ ׳³ג€ ׳³ג€׳³ֲ¨׳³ֲ Groq ׳ֲ¿ֲ½-׳³ג„¢׳³ֲ ׳³ֲ\\.\n\n"
        "*׳³ג€׳³ג€¢׳³ג€™׳³ֲ׳³ֲ׳³ג€¢׳³ֳ-:*\n"
        "׳’ג‚¬ֲ¢ `/ls website`\n"
        "׳’ג‚¬ֲ¢ `/cat website/voice\\.html`\n"
        "׳’ג‚¬ֲ¢ `/draft website/index\\.html ׳³ֲ©׳³ֲ ׳³ג€ ׳³ֲ׳³ֳ- ׳³ג€׳³ג€÷׳³ג€¢׳³ֳ-׳³ֲ¨׳³ֳ-`\n"
        "׳’ג‚¬ֲ¢ `/sync \"feat: my edit\"`"
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
    # aiogram default is MARKDOWN (v1) ׳’ג‚¬ג€ escape only `_*`[
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
            f"*API:* {'׳ֲ¿ֲ½-׳³ג„¢ ׳’ֲג€' if api_ok else '׳³ג€÷׳³ג€˜׳³ג€¢׳³ג„¢ ׳ֲ¿ֲ½-'}",
            f"*DB:* `{_escape_md(db)}`",
        ]
        if "version" in h:
            lines.append(f"*׳³ג€™׳³ֲ¨׳³ֲ¡׳³ג€:* `{_escape_md(h['version'])}`")
        if "timestamp" in h:
            lines.append(f"*׳³ג€˜׳³ג€׳³ג€¢׳³ֲ§ ׳³ג€˜:* `{_escape_md(h['timestamp'])}`")
        await msg.answer("\n".join(lines))
    except httpx.HTTPStatusError as e:
        await msg.answer(f"׳³ג€-API ׳³ג€׳ֲ¿ֲ½-׳³ג€“׳³ג„¢׳³ֲ¨ {e.response.status_code}. ׳³ג€÷׳³ֲ ׳³ֲ¨׳³ֲ׳³ג€ down.")
    except Exception as e:
        log.exception("/health failed")
        await msg.answer(f"׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€: `{_escape_md(type(e).__name__)}: {_escape_md(str(e))}`")


@dp.message(Command("price"))
async def cmd_price(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    try:
        p = await _http_get_json("/api/prices")
        prices = p.get("prices") or p
        if not isinstance(prices, dict) or not prices:
            await msg.answer("׳³ֲ׳³ג„¢׳³ֲ ׳³ֲ ׳³ֳ-׳³ג€¢׳³ֲ ׳³ג„¢ ׳³ֲ׳ֲ¿ֲ½-׳³ג„¢׳³ֲ¨ ׳³ג€÷׳³ֲ¨׳³ג€™׳³ֲ¢.")
            return
        lines = ["*׳³ֲ׳ֲ¿ֲ½-׳³ג„¢׳³ֲ¨׳³ג„¢׳³ֲ \\(׳’ג€ֳ-\\):*"]
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
            lines.append(f"׳’ג‚¬ֲ¢ *{_escape_md(token)}:* `{fmt}`")
        await msg.answer("\n".join(lines))
    except Exception as e:
        log.exception("/price failed")
        await msg.answer(f"׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€: `{_escape_md(str(e))}`")


@dp.message(Command("devices"))
async def cmd_devices(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    if not ADMIN_KEY:
        await msg.answer("׳ֲ¿ֲ½-׳³ֲ¡׳³ֲ¨ `ADMIN_API_KEY` ׳³ג€˜-.env ׳³ֲ©׳³ֲ ׳³ג€׳³ג€˜׳³ג€¢׳³ֻ.")
        return
    try:
        d = await _http_get_json(
            "/api/admin/devices/list", headers={"X-Admin-Key": ADMIN_KEY}
        )
        devices = d.get("devices") or d if isinstance(d, (list, dict)) else []
        if not devices:
            await msg.answer("׳³ֲ׳³ג„¢׳³ֲ ׳³ֲ׳³ג€÷׳³ֲ©׳³ג„¢׳³ֲ¨׳³ג„¢׳³ֲ ׳³ֲ¨׳³ֲ©׳³ג€¢׳³ֲ׳³ג„¢׳³ֲ.")
            return
        lines = [f"*׳³ֲ׳³ג€÷׳³ֲ©׳³ג„¢׳³ֲ¨׳³ג„¢׳³ֲ \\({len(devices)}\\):*"]
        for dev in devices[:10]:
            dev_id = dev.get("device_id") or dev.get("id") or "?"
            last_seen = dev.get("last_seen_at") or dev.get("last_heartbeat") or "--"
            online = dev.get("online") or dev.get("is_online")
            mark = "׳ ֲֲֲ¢" if online else "׳’ֲֲ«"
            lines.append(
                f"{mark} `{_escape_md(str(dev_id))}` ײ²ֲ· {_escape_md(str(last_seen))}"
            )
        if len(devices) > 10:
            lines.append(f"_\\+ {len(devices) - 10} ׳³ֲ ׳³ג€¢׳³ֲ¡׳³ג‚×׳³ג„¢׳³ֲ_")
        await msg.answer("\n".join(lines))
    except httpx.HTTPStatusError as e:
        await msg.answer(f"admin API ׳³ג€׳ֲ¿ֲ½-׳³ג€“׳³ג„¢׳³ֲ¨ {e.response.status_code}.")
    except Exception as e:
        log.exception("/devices failed")
        await msg.answer(f"׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€: `{_escape_md(str(e))}`")


@dp.message(Command("control"))
async def cmd_control(msg: Message) -> None:
    """One-shot ops summary: API + DB + Gateway + Swarm + Marketplace + Events.

    This is THE 'where do I stand right now' command Osif's advisor asked for.
    No AI, no token cost, ~500ms response. Plain text, no markdown traps.
    """
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return

    sections = []
    timestamp = __import__("datetime").datetime.now().strftime("%H:%M:%S %d/%m")

    # 1. API health
    try:
        h = await _http_get_json("/api/health")
        api_ok = h.get("status") == "ok"
        db_ok = h.get("db") == "connected"
        sections.append(
            f"׳ ֲֲֲ¢ API: ok ײ²ֲ· DB: {h.get('db','?')} ײ²ֲ· v{h.get('version','?')}"
            if api_ok and db_ok
            else f"׳ ֲג€ֲ´ API: {h}"
        )
    except Exception as e:
        sections.append(f"׳ ֲג€ֲ´ API: unreachable ({type(e).__name__})")

    # 2. Gateway
    try:
        g = await _http_get_json("/api/miniapp/health")
        if g.get("gateway_loaded"):
            tok = "׳’ֲג€" if g.get("primary_bot_token_set") else "׳’ֲֲ  TELEGRAM_BOT_TOKEN ׳ֲ¿ֲ½-׳³ֲ¡׳³ֲ¨"
            sections.append(f"׳ ֲֲֲ¢ Gateway: loaded ײ²ֲ· admins:{g.get('admin_ids_count')} ײ²ֲ· bot_token:{tok}")
        else:
            sections.append(f"׳ ֲג€ֲ´ Gateway: not loaded")
    except Exception as e:
        sections.append(f"׳’ֲֳ- Gateway: skip ({type(e).__name__})")

    # 3. Swarm
    try:
        s = await _http_get_json("/api/swarm/stats")
        sections.append(
            f"׳ ֲֲֲ Swarm: {s.get('online',0)}/{s.get('total_devices',0)} online ײ²ֲ· "
            f"{s.get('events_24h',0)} events 24h ײ²ֲ· {s.get('pending_commands',0)} cmds pending"
        )
    except Exception as e:
        sections.append(f"׳’ֲֳ- Swarm: skip ({type(e).__name__})")

    # 4. Marketplace
    try:
        m = await _http_get_json("/api/marketplace/items?limit=100")
        items = [i for i in (m.get("items") or []) if i.get("status") == "approved"]
        sections.append(f"׳ ֲג€÷ג€™ Marketplace: {len(items)} ׳³ג‚×׳³ֲ¨׳³ג„¢׳³ֻ׳³ג„¢׳³ֲ approved")
    except Exception as e:
        sections.append(f"׳’ֲֳ- Marketplace: skip")

    # 5. Recent events
    try:
        e = await _http_get_json("/api/events/public?limit=5")
        evts = e.get("events") or []
        if evts:
            recent = ", ".join(set(ev.get("type") or ev.get("event_type", "?") for ev in evts[:5]))
            sections.append(f"׳ ֲג€ֲ¡ Events 5 last: {recent}")
        else:
            sections.append("׳ ֲג€ֲ¡ Events: 0 (׳³ג‚×׳³ג„¢׳³ג€ ׳³ג‚×׳³ֲ¢׳³ג„¢׳³ֲ׳³ג€¢׳³ֳ- ׳³ֲ¨׳³ג„¢׳³ֲ§)")
    except Exception:
        sections.append(f"׳’ֲֳ- Events: skip")

    # 6. Your queue (4 user-action blockers)
    queue_items = []
    if 'g' in locals() and not g.get("primary_bot_token_set"):
        queue_items.append("׳’ג‚¬ֲ¢ ׳³ג€׳³ג€™׳³ג€׳³ֲ¨ TELEGRAM_BOT_TOKEN ׳³ג€˜-Railway")
    queue_items.append("׳’ג‚¬ֲ¢ ׳³ג‚×׳³ג„¢׳³ג„¢׳³ֲ¨ ESP ׳’ג‚¬ג€ ׳³ֲ©׳³ֲ׳ֲ¿ֲ½- /devices ׳³ֲ׳³ג€˜׳³ג€׳³ג„¢׳³ֲ§׳³ג€")
    queue_items.append("׳’ג‚¬ֲ¢ ׳³ג€׳³ג€™׳³ג€׳³ֲ¨ SMS_PROVIDER ׳³ג€˜-Railway (Inforu)")
    queue_items.append("׳’ג‚¬ֲ¢ BotFather: ׳³ג€׳³ג€™׳³ג€׳³ֲ¨ Mini App URL")

    sections.append("")
    sections.append("׳ ֲג€ג€¹ ׳³ג€׳³ֳ-׳³ג€¢׳³ֲ¨ ׳³ֲ©׳³ֲ׳³ֲ:")
    sections.extend(queue_items)
    sections.append("")
    sections.append(f"׳ ֲֲֲ  ׳³ג€׳³ג€˜׳³ג„¢׳³ֳ-: https://slh-nft.com/my.html")
    sections.append(f"׳’ֲֲ± ׳³ֲ ׳³ג€˜׳³ג€׳³ֲ§: {timestamp}")

    await msg.answer("\n".join(sections), parse_mode=None)


@dp.message(Command("swarm"))
async def cmd_swarm(msg: Message) -> None:
    """Show SLH Swarm mesh status ׳’ג‚¬ג€ total/online/events/pending + per-device list."""
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    try:
        stats = await _http_get_json("/api/swarm/stats")
        devices_resp = await _http_get_json("/api/swarm/devices?limit=20")
        devices = devices_resp.get("devices", [])

        lines = [
            "*׳ ֲֲֲ ׳³ֲ¨׳³ֲ©׳³ֳ- Swarm:*",
            f"׳’ג‚¬ֲ¢ *׳³ֲ¡׳³ג€׳³ֲ´׳³ג€÷:* `{stats.get('total_devices', 0)}` ײ²ֲ· "
            f"*online:* `{stats.get('online', 0)}`",
            f"׳’ג‚¬ֲ¢ *events 24h:* `{stats.get('events_24h', 0)}` ײ²ֲ· "
            f"*commands ׳³ֲ׳³ֲ׳³ֳ-׳³ג„¢׳³ֲ ׳³ג€¢׳³ֳ-:* `{stats.get('pending_commands', 0)}`",
        ]

        if devices:
            lines.append("\n*׳³ֲ׳³ג€÷׳³ֲ©׳³ג„¢׳³ֲ¨׳³ג„¢׳³ֲ:*")
            for d in devices[:10]:
                dev_id = d.get("device_id", "?")
                online = d.get("online", False)
                mark = "׳ ֲֲֲ¢" if online else "׳’ֲֲ«"
                rssi = d.get("last_rssi")
                bat = d.get("last_battery_pct")
                tail_bits = []
                if rssi is not None:
                    tail_bits.append(f"RSSI {rssi}dBm")
                if bat is not None:
                    tail_bits.append(f"{bat}%")
                tail = " ײ²ֲ· ".join(tail_bits)
                lines.append(
                    f"{mark} `{_escape_md(str(dev_id))}`"
                    + (f" ײ²ֲ· {_escape_md(tail)}" if tail else "")
                )
            if len(devices) > 10:
                lines.append(f"_\\+ {len(devices) - 10} ׳³ֲ ׳³ג€¢׳³ֲ¡׳³ג‚×׳³ג„¢׳³ֲ_")
        else:
            lines.append(
                "\n_׳³ֲ׳³ג„¢׳³ֲ ׳³ֲ׳³ג€÷׳³ֲ©׳³ג„¢׳³ֲ¨׳³ג„¢׳³ֲ ׳³ֲ¨׳³ֲ©׳³ג€¢׳³ֲ׳³ג„¢׳³ֲ ׳³ֲ¢׳³ג€׳³ג„¢׳³ג„¢׳³ֲ\\. ׳³ג€÷׳³ֲ©׳³ֳ-׳³ג€˜׳³ֲ¢׳³ג„¢׳³ֲ¨ ׳³ֲ׳³ֳ- ׳³ג€-firmware ׳³ֲ¢׳³ֲ ׳³ֳ-׳³ֲ׳³ג„¢׳³ג€÷׳³ֳ- ESP-NOW, ׳³ג€׳³ֲ׳³ג€÷׳³ֲ©׳³ג„¢׳³ֲ¨׳³ג„¢׳³ֲ ׳³ג„¢׳³ג„¢׳³ֲ¨׳³ֲ©׳³ֲ׳³ג€¢ ׳³ֲ׳³ג€¢׳³ֻ׳³ג€¢׳³ֲ׳³ֻ׳³ג„¢׳³ֳ-\\._"
            )

        await msg.answer("\n".join(lines))
    except Exception as e:
        log.exception("/swarm failed")
        await msg.answer(f"׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€: `{_escape_md(str(e))}`")


@dp.message(Command("task"))
async def cmd_task(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    # Everything after the /task command word
    text = (msg.text or "").split(maxsplit=1)
    if len(text) < 2 or not text[1].strip():
        await msg.answer("׳³ֲ©׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ©: `/task \\<׳³ֳ-׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ¨ ׳³ג€׳³ֲ׳³ֲ©׳³ג„¢׳³ֲ׳³ג€\\>`")
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
            f"׳³ֲ ׳³ג€¢׳³ֲ¡׳³ֲ£ ׳³ֲ\\-TASK\\_BOARD\\.md:\n`{_escape_md(task_text)}`"
        )
    except Exception as e:
        log.exception("/task failed")
        await msg.answer(f"׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€: `{_escape_md(str(e))}`")


@dp.message(Command("status"))
async def cmd_status(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    await msg.answer("׳³ֲ׳³ג€˜׳³ֲ¦׳³ֲ¢ ׳³ג€˜׳³ג€׳³ג„¢׳³ֲ§׳³ֳ- ׳³ֲ׳³ֲ¦׳³ג€˜ ׳³ֲ׳³ג€׳³ג„¢׳³ֲ¨׳³ג€...")
    try:
        reply, new_msgs = await ai_client.converse(
            history=[],
            user_text="׳³ג€˜׳³ֲ¦׳³ֲ¢ ׳³ג€˜׳³ג€׳³ג„¢׳³ֲ§׳³ג€ ׳³ֲ׳³ג€׳³ג„¢׳³ֲ¨׳³ג€: 1) curl ׳³ֲ-/api/health ׳³ֲ©׳³ֲ Railway, 2) git status ׳³ג€˜׳³ֲ©׳³ֲ ׳³ג„¢ ׳³ג€-repos (D:\\SLH_ECOSYSTEM ׳³ג€¢-D:\\SLH_ECOSYSTEM\\website), 3) docker ps. ׳³ֳ-׳³ֲ ׳³ֲ¡׳³ג„¢׳³ג€÷׳³ג€¢׳³ֲ ׳³ֲ©׳³ֲ 3-5 ׳³ֲ©׳³ג€¢׳³ֲ¨׳³ג€¢׳³ֳ- ׳³ג€˜׳³ֲ¢׳³ג€˜׳³ֲ¨׳³ג„¢׳³ֳ-.",
        )
        for msg_part in new_msgs:
            await session.append(msg.chat.id, msg_part["role"], msg_part["content"])
        for chunk in _chunks(reply):
            await msg.answer(chunk)
    except Exception as e:
        log.exception("status failed")
        await msg.answer(f"׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€: `{type(e).__name__}: {e}`")


@dp.message(Command("clear"))
async def cmd_clear(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    n = await session.clear(msg.chat.id)
    await msg.answer(f"׳³ֲ ׳³ג€¢׳³ֲ§׳³ג€. ׳³ֲ ׳³ֲ׳ֲ¿ֲ½-׳³ֲ§׳³ג€¢ {n} ׳³ג€׳³ג€¢׳³ג€׳³ֲ¢׳³ג€¢׳³ֳ-.")


# ---------- Direct executor commands (no AI, no cost) ----------
import subprocess

_SAFE_EXEC_ALLOWLIST = {
    "docker ps", "docker compose ps", "docker stats --no-stream",
    "git status", "git log --oneline -10", "git diff --stat",
    "df -h", "uptime", "uname -a",
}


def _resolve_cwd() -> str:
    """Pick a valid working dir. /workspace works in container, falls back
    to repo root on local Windows installs."""
    candidates = ["/workspace", os.path.join(HERE, ".."), HERE]
    for c in candidates:
        if c and os.path.isdir(c):
            return c
    return os.getcwd()


_CMD_CWD = _resolve_cwd()


def _run_cmd(cmd: str, timeout: int = 15) -> str:
    """Run a shell command and return stdout+stderr, capped."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=_CMD_CWD,
        )
        out = (result.stdout or "") + (result.stderr or "")
        return out[:3500] or "(no output)"
    except subprocess.TimeoutExpired:
        return f"׳’ֲֲ± command timed out after {timeout}s"
    except FileNotFoundError as e:
        # Docker / git not in PATH ׳’ג‚¬ג€ friendly message
        return f"׳’ֲֲ ׳ֲ¸ֲ command not found: {e}"
    except Exception as e:
        return f"׳’ֲֲ ׳ֲ¸ֲ {type(e).__name__}: {e}"


def _has_binary(name: str) -> bool:
    import shutil
    return shutil.which(name) is not None


@dp.message(Command("ps"))
async def cmd_ps(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    if not _has_binary("docker"):
        # Fallback: list services from docker-compose.yml so the user sees
        # the configured fleet even when the bot has no docker socket.
        compose_path = os.path.join(_CMD_CWD, "docker-compose.yml")
        if os.path.isfile(compose_path):
            try:
                with open(compose_path, "r", encoding="utf-8") as f:
                    raw = f.read()
                services = []
                in_services = False
                for line in raw.splitlines():
                    if line.startswith("services:"):
                        in_services = True
                        continue
                    if in_services:
                        if line and not line.startswith((" ", "\t")):
                            break
                        # Service names are 2-space indented and end with ':'
                        if line.startswith("  ") and not line.startswith("    ") and line.rstrip().endswith(":"):
                            services.append(line.strip().rstrip(":"))
                services_str = "\n".join(f"׳’ג‚¬ֲ¢ {s}" for s in services[:40])
                await msg.answer(
                    "׳ ֲֲֲ³ docker ׳³ֲ׳³ֲ ׳³ֲ׳³ג€¢׳³ֳ-׳³ֲ§׳³ֲ ׳³ג€˜׳³ֲ¡׳³ג€˜׳³ג„¢׳³ג€˜׳³ג€ ׳³ג€׳³ג€“׳³ג€¢ ׳³ֲ©׳³ֲ ׳³ג€׳³ג€˜׳³ג€¢׳³ֻ.\n\n"
                    f"׳³ֲ©׳³ג„¢׳³ֲ¨׳³ג€¢׳³ֳ-׳³ג„¢׳³ֲ ׳³ֲ©׳³ֲ׳³ג€¢׳³ג€™׳³ג€׳³ֲ¨׳³ג„¢׳³ֲ ׳³ג€˜-docker-compose.yml ({len(services)}):\n"
                    f"{services_str}\n\n"
                    "׳³ֲ׳³ג€׳³ג‚×׳³ֲ¢׳³ֲ׳³ֳ- ׳³ג€׳³ֲ¡׳³ֻ׳³ֻ׳³ג€¢׳³ֲ¡ ׳³ג€˜׳³ג‚×׳³ג€¢׳³ֲ¢׳³ֲ ׳³ג€׳³ֲ¨׳³ֲ¥ ׳³ג€˜׳³ֲ׳ֲ¿ֲ½-׳³ֲ©׳³ג€˜ ׳³ג€׳³ֲ׳³ֲ׳³ֲ¨׳ֲ¿ֲ½-: `docker compose ps`",
                    parse_mode=None,
                )
                return
            except Exception as e:
                await msg.answer(f"docker ׳ֲ¿ֲ½-׳³ֲ¡׳³ֲ¨ ׳³ג€¢׳³ֲ׳³ֲ ׳³ג€׳³ֲ¦׳³ֲ׳ֲ¿ֲ½-׳³ֳ-׳³ג„¢ ׳³ֲ׳³ֲ§׳³ֲ¨׳³ג€¢׳³ֲ compose: {e}")
                return
        await msg.answer("׳ ֲֲֲ³ docker ׳³ֲ׳³ֲ ׳³ֲ׳³ג€¢׳³ֳ-׳³ֲ§׳³ֲ + docker-compose.yml ׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ׳³ֲ¦׳³ֲ.", parse_mode=None)
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
        await msg.answer("׳³ֲ©׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ©: `/logs \\<container\\-name\\>`  \n׳³ֲ׳³ֲ׳³ֲ©׳³ֲ: `/logs slh\\-claude\\-bot`")
        return
    name = parts[1].strip().replace(";", "").replace("&", "").replace("|", "")
    # Allowlist prefix check
    if not name.startswith(("slh-", "slh_")):
        await msg.answer("׳³ֲ¨׳³ֲ§ containers ׳³ֲ¢׳³ֲ prefix `slh-` ׳³ֲ׳³ג€¢׳³ֳ-׳³ֲ¨׳³ג„¢׳³ֲ.")
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
        await msg.answer(f"׳³ג‚×׳³ֲ§׳³ג€¢׳³ג€׳³ֳ- git ׳³ֲ׳³ג€¢׳³ֳ-׳³ֲ¨׳³ג€¢׳³ֳ- ׳³ג€˜׳³ֲ׳³ג€˜׳³ג€: {', '.join(safe_subs)}")
        return
    repo_hint = (parts[1].strip() if len(parts) > 1 else "")
    # Default = website (small repo); switch to main only if user says api/main
    if "api" in repo_hint or "main" in repo_hint:
        repo = "/workspace"
    else:
        repo = "/workspace/website"
    if subcmd == "log":
        out = _run_cmd(f"cd {repo} && git log --oneline -10", timeout=10)
    elif subcmd == "diff":
        out = _run_cmd(f"cd {repo} && git diff --stat HEAD", timeout=10)
    elif subcmd == "branch":
        out = _run_cmd(f"cd {repo} && git branch --show-current", timeout=5)
    else:
        # -uno = no untracked (workspace has 100s of untracked backup files)
        out = _run_cmd(f"cd {repo} && git status -s -uno", timeout=10)
    repo_short = "website" if "website" in repo else "main"
    await msg.answer(f"*git {subcmd} @ `{repo_short}`:*\n```\n{out[:3500]}\n```")


@dp.message(Command("bots"))
async def cmd_bots(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    out = _run_cmd("docker ps --format '{{.Names}}' | grep ^slh- | sort | wc -l")
    running = out.strip()
    out_list = _run_cmd("docker ps --format '{{.Names}}: {{.Status}}' | grep ^slh- | sort")
    await msg.answer(
        f"*Bot fleet: {running} ׳³ֲ¨׳³ֲ¦׳³ג„¢׳³ֲ*\n```\n{out_list[:3500]}\n```"
    )


@dp.message(Command("ai_mode"))
async def cmd_ai_mode(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    await msg.answer(
        f"*AI mode:* `{_AI_MODE}`\n\n"
        f"{'׳’ֲג€¦ Anthropic Claude ׳³ֲ¢׳³ֲ tool use (׳³ֲ¢׳³ג€¢׳³ֲ׳³ג€ ׳³ג€÷׳³ֲ¡׳³ֲ£)' if _AI_MODE == 'anthropic-tools' else '׳’ֲג€¦ SLH multi-provider (Groq/Gemini ׳ֲ¿ֲ½-׳³ג„¢׳³ֲ ׳³ֲ)'}"
    )


# Photo/screenshot handler ׳’ג‚¬ג€ saves incoming images to /workspace/incoming_screenshots/
# so the human operator can read them via Read tool from outside the container.
@dp.message(F.photo)
async def on_photo(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    try:
        from datetime import datetime
        photo = msg.photo[-1]  # largest size
        file = await bot.get_file(photo.file_id)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = "/workspace/incoming_screenshots"
        os.makedirs(out_dir, exist_ok=True)
        out_path = f"{out_dir}/screenshot_{ts}_{msg.from_user.id}.jpg"
        await bot.download_file(file.file_path, out_path)
        # Optional caption
        cap = (msg.caption or "").strip()
        log.info(f"saved screenshot from {msg.from_user.id} to {out_path} (caption='{cap[:60]}')")
        await msg.answer(
            f"׳’ֲג€¦ ׳³ֲ§׳³ג„¢׳³ג€˜׳³ֲ׳³ֳ-׳³ג„¢ ׳³ֳ-׳³ֲ׳³ג€¢׳³ֲ ׳³ג€ ׳³ג€¢׳³ֲ©׳³ֲ׳³ֲ¨׳³ֳ-׳³ג„¢\\.\n"
            f"׳ ֲג€ג€ `screenshot_{ts}`\n"
            f"{'׳ ֲג€ֲ ' + _escape_md(cap[:200]) if cap else ''}\n\n"
            f"Claude ׳³ֲ ׳³ג„¢׳³ג€™׳³ֲ© ׳³ֲ׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥ ׳³ג€׳³ג€“׳³ג€ ׳³ג€¢׳³ג„¢׳³ֲ§׳³ֲ¨׳³ֲ ׳³ֲ׳³ג€¢׳³ֳ-׳³ג€¢\\."
        )
    except Exception as e:
        log.exception("photo save failed")
        await msg.answer(f"׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€ ׳³ג€˜׳³ֲ©׳³ֲ׳³ג„¢׳³ֲ¨׳³ֳ- ׳³ג€׳³ֳ-׳³ֲ׳³ג€¢׳³ֲ ׳³ג€: `{type(e).__name__}: {e}`")


# Filter excludes slash-commands so they fall through to Command-filtered
# handlers registered LATER (payment_flow, admin_panel, editor_commands).
@dp.message(F.text & ~F.text.startswith("/"))
async def on_text(msg: Message) -> None:
    if not auth.is_authorized(msg.from_user.id):
        await msg.answer(auth.unauthorized_reply_he(msg.from_user.id))
        return
    text = msg.text or ""
    if not text.strip():
        return

    # ==== QUOTA GATE ====
    decision = await quota.check(msg.from_user.id)
    if not decision.allowed:
        await msg.answer(decision.refusal_he, parse_mode="Markdown")
        return

    # Show "typing" while we think
    await bot.send_chat_action(msg.chat.id, "typing")

    client, provider, model = _pick_ai_client(decision.use_anthropic)

    try:
        hist = await session.history(msg.chat.id)

        # Try the chosen client. If Anthropic returns a credit-balance error,
        # silently fall back to the free Groq pipeline so paid users still get
        # value (we'll log it as 'free-fallback' so /revenue cost numbers stay
        # honest, and prepend a one-line note so the user knows what happened).
        try:
            reply, new_msgs = await client.converse(hist, text)
        except AnthropicBadRequest as e:
            err_msg = str(e).lower()
            balance_exhausted = (
                provider == "anthropic"
                and ("credit balance" in err_msg or "credit_balance" in err_msg
                     or "insufficient" in err_msg or "billing" in err_msg)
            )
            if balance_exhausted:
                log.warning(f"Anthropic balance exhausted, falling back to free: {e}")
                client = _free_client
                provider = "free-fallback"
                model = "groq/llama-3.3-70b-versatile"
                # Pass tier_mode='pro_fallback' so the system prompt knows the
                # user paid for Pro ׳’ג‚¬ג€ answer richly + acknowledge tool absence.
                reply, new_msgs = await client.converse(hist, text, tier_mode="pro_fallback")
                # Tell the user once per message ׳’ג‚¬ג€ visible Pro-tier degradation
                reply = ("׳’ֲֲ ׳ֲ¸ֲ _Pro tier ׳³ג€“׳³ֲ׳³ֲ ׳³ג„¢ ׳³ֲ¢׳³ֲ Groq Llama (Anthropic balance ׳³ֲ¨׳³ג„¢׳³ֲ§). "
                         "׳³ֳ-׳³ג‚×׳³ֲ¢׳³ג€¢׳³ֲ׳³ג€ ׳³ֲ¨׳³ג€™׳³ג„¢׳³ֲ׳³ג€ ׳³ֳ-׳ֲ¿ֲ½-׳³ג€“׳³ג€¢׳³ֲ¨ ׳³ֲ׳³ג„¢׳³ג€ ׳³ֲ©׳³ג„¢׳³ֳ-׳³ג€¢׳³ג€¢׳³ֲ¡׳³ֲ£ balance._\n\n") + reply
            else:
                raise

        for m in new_msgs:
            await session.append(msg.chat.id, m["role"], m["content"])

        # ==== USAGE LOG ====
        # Token counts are best-effort estimates until claude_client.converse
        # returns real usage. char/4 is a rough heuristic.
        tokens_in = max(1, sum(len(str(m.get("content", ""))) for m in hist) // 4)
        tokens_out = max(1, len(reply) // 4)
        cost_cents = 0
        if provider == "anthropic":
            # Anthropic Sonnet 4.5: $3/Mtok in, $15/Mtok out ׳’ג€ ג€™ cents
            cost_usd = (tokens_in * 3.0 + tokens_out * 15.0) / 1_000_000
            cost_cents = int(cost_usd * 100)
        # provider == 'free-fallback' or 'free' ׳’ג€ ג€™ cost_cents stays 0
        await quota.record(
            user_id=msg.from_user.id,
            chat_id=msg.chat.id,
            tier=decision.tier,
            provider=provider,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd_cents=cost_cents,
        )

        for chunk in _chunks(reply):
            await msg.answer(chunk)

        # Low-quota nudge ׳’ג‚¬ג€ only on transitions
        new_remaining = decision.quota_remaining - 1
        if 0 < new_remaining <= 3 and decision.tier == "free":
            await msg.answer(
                f"׳’ֲֲ ׳ֲ¸ֲ ׳³ֲ ׳³ֲ©׳³ֲ׳³ֲ¨׳³ג€¢ ׳³ֲ׳³ֲ {new_remaining} ׳³ג€׳³ג€¢׳³ג€׳³ֲ¢׳³ג€¢׳³ֳ- ׳³ג€׳ֲ¿ֲ½-׳³ג€¢׳³ג€׳³ֲ©. "
                f"׳³ֲ©׳³ג€׳³ֲ¨׳³ג€™ ׳³ֲ-Pro: `/upgrade pro`"
            )
    except Exception as e:
        log.exception("converse failed")
        err = f"׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€: `{type(e).__name__}: {e}`"
        if "ANTHROPIC_API_KEY" in str(e):
            err += "\n\n׳³ֲ¦׳³ֲ¨׳³ג„¢׳³ֲ ׳³ֲ׳³ג€׳³ג€¢׳³ֲ¡׳³ג„¢׳³ֲ£ ANTHROPIC\\_API\\_KEY ׳³ֲ-slh-claude-bot/.env"
        await msg.answer(err)


async def main() -> None:
    await session.init_db()
    await subscriptions.init_db()
    # Wire monetization (must register BEFORE F.text handler runs, but since
    # F.text now excludes slash-commands these can register at runtime safely)
    payment_flow.register(dp, auth)
    admin_panel.register(dp, auth)
    # Rotation panel must register BEFORE the F.text handler in bot.py runs
    # so its token-input filter gets first crack at user messages when a
    # rotation flow is pending. Order matters: aiogram dispatches in
    # registration order.
    try:
        import rotation_panel
        rotation_panel.register(dp, auth)
        log.info("rotation_panel wired in")
    except Exception as e:
        log.warning(f"rotation_panel not loaded: {e}")
    try:
        import railway_ops
        railway_ops.register(dp, auth)
        log.info("payment_flow + admin_panel + railway_ops wired in")
    except Exception as e:
        log.warning(f"railway_ops not loaded: {e}")
        log.info("payment_flow + admin_panel wired in")
    # Wire up editor commands (cat/ls/grep/append/replace/newpage/commit/push/sync/draft/apply/reject)
    try:
        import editor_commands
        editor_commands.register(dp, auth, _chunks)
        log.info("editor_commands wired in")
    except Exception as e:
        log.warning(f"editor_commands not loaded: {e}")
    log.info(f"starting @SLH_Claude_bot ײ²ֲ· AI mode: {_AI_MODE}")
    me = await bot.get_me()
    log.info(f"connected as @{me.username} (id={me.id})")
    # Announce startup to the coordination group (no-op if disabled)
    if _coord is not None:
        await _coord.post_event(
            bot, "claude-bot", "ready",
            f"@{me.username} polling ײ²ֲ· AI={_AI_MODE}"
        )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())



# === AUTONOMOUS AGENTS ===
@dp.message(Command("scan"))
async def cmd_scan(msg: Message):
    target = msg.text.replace("/scan", "").strip() or r"D:\slh-website"
    await msg.reply("Scanning...")
    result = run_scan(target)
    await msg.reply(result)

@dp.message(Command("plan"))
async def cmd_plan(msg: Message):
    goal = msg.text.replace("/plan", "").strip()
    if not goal:
        await msg.reply("Usage: /plan <goal in English>")
        return
    await msg.reply("Planning...")
    result = run_plan(goal)
    await msg.reply(result)

@dp.message(Command("auto"))
async def cmd_auto(msg: Message):
    goal = msg.text.replace("/auto", "").strip()
    if not goal:
        await msg.reply("Usage: /auto <goal>")
        return
    await msg.reply("Running full auto pipeline...")
    result = run_auto(goal)
    await msg.reply(result[:4000])


@dp.message(Command("crowdfunding"))
async def cmd_crowdfunding(msg: Message):
    await msg.reply(
        "?? SLH Crowdfunding Campaign\n\n"
        "????? ????? AI ???????? - ???? ?????? ????? ??? ???.\n"
        "https://slh-nft.com/crowdfunding\n\n"
        "?? ????? ???????:\n"
        "ג€¢ ???? () - ??? ????\n"
        "ג€¢ ???? () - ???? ?????? + ????'\n"
        "ג€¢ ????? () - ????? ?? ???'??? + ????? ?????\n"
        "ג€¢ ???? () - ???? ????? + ????? ?????"
    )
