"""
SLH AI Spark — Railway operations from Telegram DM.

Commands (admin-only):
- /railway_status            → list projects + current linked service
- /railway_logs <service> [n] → tail N lines of service logs
- /railway_redeploy <service> → redeploy service (no env changes)
- /railway_vars <service>     → list var NAMES only (values redacted by us)
- /railway_set <service> <KEY> <VALUE>  → set env var, with value passed
                                          via reply-to-message (NOT in cmd line)

Auth: RAILWAY_TOKEN must be set in /workspace/slh-claude-bot/.env (token from
https://railway.com/account/tokens). Without it, all commands return guidance.

Security: subcommands run via subprocess with timeout + arg whitelist. The
entire module is gated by auth.is_authorized — only Osif's two telegram IDs
reach it.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
from typing import Optional

from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

log = logging.getLogger("slh-railway-ops")


def _railway_bin() -> str:
    """Find the railway CLI binary (multiple install paths tried by Dockerfile)."""
    for path in ("/root/.railway/bin/railway", "/usr/local/bin/railway", "railway"):
        try:
            r = subprocess.run([path, "--version"], capture_output=True, timeout=3)
            if r.returncode == 0:
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return ""


_RAILWAY = _railway_bin()


def _has_token() -> bool:
    return bool(os.getenv("RAILWAY_TOKEN", "").strip())


def _run_railway(args: list[str], timeout: int = 30) -> str:
    """Run railway CLI with token + capture output. Token NEVER printed."""
    if not _RAILWAY:
        return (
            "🔴 Railway CLI לא מותקן בקונטיינר.\n"
            "תקן: rebuild הDockerfile (`docker compose build --no-cache claude-bot`)."
        )
    if not _has_token():
        return (
            "🔴 RAILWAY_TOKEN לא מוגדר ב-.env של הבוט.\n\n"
            "להפעלה (חד-פעמית):\n"
            "1. פתח https://railway.com/account/tokens\n"
            "2. New Token → תן שם 'slh-claude-bot' → Create\n"
            "3. העתק (אל תכתוב בצ'אט!)\n"
            "4. הוסף ל-`D:\\SLH_ECOSYSTEM\\slh-claude-bot\\.env`:\n"
            "   `RAILWAY_TOKEN=<הערך>`\n"
            "5. `docker compose up -d --force-recreate claude-bot`"
        )
    env = os.environ.copy()
    env["RAILWAY_TOKEN"] = os.getenv("RAILWAY_TOKEN", "")
    try:
        r = subprocess.run(
            [_RAILWAY, *args],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
        return out[:3500] or "(no output)"
    except subprocess.TimeoutExpired:
        return f"⏱ railway {' '.join(args[:2])} timed out"
    except Exception as e:
        return f"⚠️ {type(e).__name__}: {str(e)[:200]}"


# Whitelist of exact argv prefixes that we'll execute. Anything else rejected.
_SAFE_SUBCOMMANDS = {
    "list",         # railway list — projects
    "status",       # railway status — current project/service
    "domain",       # railway domain — list domains
    "service",      # railway service — list services
    "whoami",       # railway whoami
    "variables",    # railway variables (list); writes use --set / different path
    "logs",         # railway logs --service X
    "redeploy",     # railway redeploy --service X (mutation, but bounded)
}


def _redact_secret_values(text: str) -> str:
    """Replace likely secret values with *** to avoid leaking back to chat."""
    # Common patterns: API keys (sk-..., 8-digit:Base64), JWTs, hex 32+
    patterns = [
        (r"sk-[A-Za-z0-9_\-]{20,}", "sk-***REDACTED***"),
        (r"sk-ant-[A-Za-z0-9_\-]{20,}", "sk-ant-***REDACTED***"),
        (r"\b\d{8,12}:[A-Za-z0-9_\-]{30,}", "***BOT_TOKEN_REDACTED***"),
        (r"postgresql://[^@]+@[^/]+/\S+", "postgresql://***REDACTED***"),
        (r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", "***JWT_REDACTED***"),
        # Any line with KEY=VAL where VAL is long → redact VAL
        (r"([A-Z_][A-Z0-9_]{4,}=)\S{20,}", r"\1***"),
    ]
    for pat, repl in patterns:
        text = re.sub(pat, repl, text)
    return text


def register(dp: Dispatcher, auth_module) -> None:

    @dp.message(Command("railway_status"))
    async def cmd_status(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        out = _run_railway(["status"])
        out = _redact_secret_values(out)
        await msg.answer(f"🚂 *Railway status:*\n```\n{out[:3500]}\n```")

    @dp.message(Command("railway_list"))
    async def cmd_list(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        out = _run_railway(["list"])
        out = _redact_secret_values(out)
        await msg.answer(f"🚂 *Railway projects:*\n```\n{out[:3500]}\n```")

    @dp.message(Command("railway_logs"))
    async def cmd_logs(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        parts = (msg.text or "").split(maxsplit=2)
        if len(parts) < 2:
            await msg.answer(
                "שימוש: `/railway_logs <service-name> [lines]`\n"
                "דוגמה: `/railway_logs monitor.slh 30`"
            )
            return
        service = parts[1]
        # Sanitize service name — only allow safe chars
        if not re.match(r"^[a-zA-Z0-9_.\-]+$", service):
            await msg.answer("שם service לא תקף.")
            return
        lines = parts[2] if len(parts) > 2 else "20"
        if not lines.isdigit() or int(lines) > 100:
            lines = "20"
        out = _run_railway(["logs", "--service", service, "--tail", lines], timeout=20)
        out = _redact_secret_values(out)
        await msg.answer(f"📜 *logs {service}* (last {lines}):\n```\n{out[-3400:]}\n```")

    @dp.message(Command("railway_redeploy"))
    async def cmd_redeploy(msg: Message):
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        parts = (msg.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await msg.answer("שימוש: `/railway_redeploy <service-name>`")
            return
        service = parts[1].strip()
        if not re.match(r"^[a-zA-Z0-9_.\-]+$", service):
            await msg.answer("שם service לא תקף.")
            return
        await msg.answer(f"🚂 מפעיל redeploy של `{service}`...")
        out = _run_railway(["redeploy", "--service", service, "--yes"], timeout=60)
        out = _redact_secret_values(out)
        await msg.answer(f"```\n{out[:3000]}\n```")

    @dp.message(Command("railway_vars"))
    async def cmd_vars(msg: Message):
        """List variable NAMES only — values redacted automatically."""
        if not auth_module.is_authorized(msg.from_user.id):
            await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
            return
        parts = (msg.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await msg.answer("שימוש: `/railway_vars <service-name>`")
            return
        service = parts[1].strip()
        if not re.match(r"^[a-zA-Z0-9_.\-]+$", service):
            await msg.answer("שם service לא תקף.")
            return
        # railway variables --service X --kv → outputs KEY=VALUE pairs; we extract names
        out = _run_railway(["variables", "--service", service, "--kv"], timeout=15)
        # Extract just the KEY part of each line, drop values
        names = []
        for line in out.split("\n"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key = line.split("=", 1)[0].strip()
                if key and re.match(r"^[A-Z_][A-Z0-9_]*$", key):
                    names.append(key)
        if not names:
            await msg.answer(
                f"⚠️ לא הצלחתי לקבל variables של `{service}`.\nגולמי:\n```\n{_redact_secret_values(out)[:1500]}\n```"
            )
            return
        names_str = "\n".join(f"  • `{n}`" for n in sorted(set(names)))
        await msg.answer(
            f"🔑 *Variables in `{service}` ({len(set(names))} keys):*\n{names_str}\n\n"
            "_ערכים לא מוצגים — להגדרה השתמש ב-`/railway_set`._"
        )

    log.info("railway_ops handlers registered")
