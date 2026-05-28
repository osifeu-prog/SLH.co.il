"""Editor commands for @SLH_Claude_bot ׳’ג‚¬ג€ full website-building control from Telegram.

This module defines slash commands that let Osif (admin allowlist) inspect, edit,
commit, and deploy files in the SLH_ECOSYSTEM workspace from Telegram.

Security:
- All commands gated by auth.is_authorized() at the bot.py handler level
- _safe_path() prevents path traversal outside the workspace
- Subprocess calls have 30s timeout
- AI drafts require explicit /apply confirmation (no silent writes)

Available commands (all from Telegram):
  Inspection:
    /cat <file>            ׳’ג‚¬ג€ read file (masked secrets, 4000 chars)
    /ls [dir]              ׳’ג‚¬ג€ list directory
    /grep <pat> [file]     ׳’ג‚¬ג€ search in file/dir
    /find <pat> [dir]      ׳’ג‚¬ג€ find files by name pattern

  Edit (direct):
    /append <file> <text>  ׳’ג‚¬ג€ append a line
    /replace <file> :: <old> :: <new>   ׳’ג‚¬ג€ find/replace (use :: as separator)
    /newpage <name>        ׳’ג‚¬ג€ scaffold a new website/<name>.html from template

  Git:
    /commit <msg>          ׳’ג‚¬ג€ git add -A + commit (uses Osif's name/email)
    /push                  ׳’ג‚¬ג€ git push current branch (after commit)
    /sync <msg>            ׳’ג‚¬ג€ commit + push in one step

  AI-assisted:
    /draft <file> <instruction>  ׳’ג‚¬ג€ AI generates a diff plan; bot shows preview
    /apply                 ׳’ג‚¬ג€ apply last draft + commit + push
    /reject                ׳’ג‚¬ג€ discard last draft

Public surface: register(dp, bot, auth, _chunks, _escape_md) ׳’ג‚¬ג€ call from bot.py
"""
from __future__ import annotations

import os
import re
import asyncio
import subprocess
import logging
import html
import json
import time
from pathlib import Path
from typing import Optional

import httpx

from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

log = logging.getLogger("slh-claude-bot.editor")

WORKSPACE = Path(os.getenv("WORKSPACE", "/workspace")).resolve()
WEBSITE_DIR = WORKSPACE / "website"
API_BASE = os.getenv("SLH_API_BASE", "https://slh-api-production.up.railway.app")
GIT_AUTHOR_NAME = os.getenv("GIT_AUTHOR_NAME", "Osif Kaufman Ungar")
GIT_AUTHOR_EMAIL = os.getenv("GIT_AUTHOR_EMAIL", "osif.erez.ungar@gmail.com")

# In-memory store of pending AI drafts per chat_id
_DRAFTS: dict[int, dict] = {}


# ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬ Safety ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬

def _safe_path(rel: str) -> Optional[Path]:
    """Resolve a path inside WORKSPACE, return None if it escapes."""
    rel = (rel or "").strip().lstrip("/").lstrip("\\")
    if not rel:
        return None
    try:
        candidate = (WORKSPACE / rel).resolve()
    except (OSError, ValueError):
        return None
    if WORKSPACE not in candidate.parents and candidate != WORKSPACE:
        return None
    return candidate


def _mask(text: str) -> str:
    """Mask common secret patterns before sending to Telegram."""
    if not isinstance(text, str):
        return str(text)
    patterns = [
        (r"(sk-ant-[A-Za-z0-9\-_]{20,})", r"sk-ant-***REDACTED***"),
        (r"(\d{6,}:[A-Za-z0-9_\-]{30,})", r"***BOT_TOKEN_REDACTED***"),
        (r"(BOT_TOKEN\s*=\s*)([^\s\"']+)", r"\1***REDACTED***"),
        (r"(API_KEY\s*=\s*)([^\s\"']+)", r"\1***REDACTED***"),
        (r"(DB_PASSWORD\s*=\s*)([^\s\"']+)", r"\1***REDACTED***"),
        (r"(0x[a-fA-F0-9]{40})", r"\1"),  # public addr ok
    ]
    for pat, repl in patterns:
        text = re.sub(pat, repl, text)
    return text


def _md_escape(text: str) -> str:
    """Escape MarkdownV1 chars for Telegram."""
    if not isinstance(text, str):
        text = str(text)
    return text.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`").replace("[", "\\[")


def _run(cmd: list[str] | str, cwd: Optional[Path] = None, timeout: int = 30) -> tuple[int, str]:
    """Run subprocess, return (rc, combined_output_truncated)."""
    try:
        result = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd) if cwd else str(WORKSPACE),
        )
        out = (result.stdout or "") + (result.stderr or "")
        return result.returncode, out[:3500]
    except subprocess.TimeoutExpired:
        return 124, f"׳’ֲֲ± command timed out after {timeout}s"
    except Exception as e:
        return 1, f"׳’ֲֲ ׳ֲ¸ֲ {type(e).__name__}: {e}"


# ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬ Inspection commands ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬

async def _cmd_cat(msg: Message, parts: list[str], _chunks) -> None:
    if len(parts) < 2:
        await msg.answer("׳³ֲ©׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ©: `/cat \\<׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥\\>`")
        return
    p = _safe_path(parts[1])
    if not p or not p.is_file():
        await msg.answer(f"׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥ ׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ׳³ֲ¦׳³ֲ: `{_md_escape(parts[1])}`")
        return
    try:
        content = p.read_text(encoding="utf-8", errors="replace")[:4000]
        content = _mask(content)
    except Exception as e:
        await msg.answer(f"׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€: `{_md_escape(str(e))}`")
        return
    rel = p.relative_to(WORKSPACE)
    header = f"׳ ֲג€ג€ *{_md_escape(str(rel))}* \\({len(content)} chars\\)"
    body = f"```\n{content}\n```"
    for chunk in _chunks(header + "\n" + body):
        await msg.answer(chunk)


async def _cmd_ls(msg: Message, parts: list[str]) -> None:
    target = parts[1] if len(parts) >= 2 else "."
    p = _safe_path(target)
    if not p or not p.is_dir():
        await msg.answer(f"׳³ֲ׳³ֲ ׳³ֳ—׳³ג„¢׳³ֲ§׳³ג„¢׳³ג„¢׳³ג€: `{_md_escape(target)}`")
        return
    try:
        entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    except Exception as e:
        await msg.answer(f"׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€: `{_md_escape(str(e))}`")
        return
    lines = [f"׳ ֲג€ֲ *{_md_escape(str(p.relative_to(WORKSPACE)) or '.')}*"]
    for e in entries[:60]:
        icon = "׳ ֲג€ֲ" if e.is_dir() else "׳ ֲג€ג€"
        lines.append(f"{icon} `{_md_escape(e.name)}`")
    if len(entries) > 60:
        lines.append(f"_\\+ {len(entries) - 60} ׳³ֲ ׳³ג€¢׳³ֲ¡׳³ג‚×׳³ג„¢׳³ֲ_")
    await msg.answer("\n".join(lines))


async def _cmd_grep(msg: Message, parts: list[str]) -> None:
    if len(parts) < 2:
        await msg.answer("׳³ֲ©׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ©: `/grep \\<׳³ֳ—׳³ג€˜׳³ֲ ׳³ג„¢׳³ֳ—\\> \\[׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥\\|׳³ֳ—׳³ג„¢׳³ֲ§׳³ג„¢׳³ג„¢׳³ג€\\]`")
        return
    args = parts[1].strip().split(maxsplit=1)
    pattern = args[0]
    target = args[1] if len(args) >= 2 else "website"
    p = _safe_path(target)
    if not p or not p.exists():
        await msg.answer(f"׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ׳³ֲ¦׳³ֲ: `{_md_escape(target)}`")
        return
    cmd = ["grep", "-rn", "-m", "20", "--include=*.html", "--include=*.js", "--include=*.css", "--include=*.md", pattern, str(p)]
    rc, out = _run(cmd, timeout=15)
    out = _mask(out)
    if not out.strip():
        await msg.answer(f"׳³ֲ׳³ג„¢׳³ֲ ׳³ג€׳³ֳ—׳³ֲ׳³ֲ׳³ג€¢׳³ֳ— ׳³ֲ\\-`{_md_escape(pattern)}` ׳³ג€˜\\-`{_md_escape(target)}`")
        return
    await msg.answer(f"׳ ֲג€ֲ *grep* `{_md_escape(pattern)}` @ `{_md_escape(target)}`\n```\n{out[:3500]}\n```")


async def _cmd_find(msg: Message, parts: list[str]) -> None:
    if len(parts) < 2:
        await msg.answer("׳³ֲ©׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ©: `/find \\<׳³ג€׳³ג‚×׳³ג€¢׳³ֲ¡\\> \\[׳³ֳ—׳³ג„¢׳³ֲ§׳³ג„¢׳³ג„¢׳³ג€\\]`")
        return
    args = parts[1].strip().split(maxsplit=1)
    pattern = args[0]
    target = args[1] if len(args) >= 2 else "website"
    p = _safe_path(target)
    if not p or not p.exists():
        await msg.answer(f"׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ׳³ֲ¦׳³ֲ: `{_md_escape(target)}`")
        return
    cmd = ["find", str(p), "-type", "f", "-name", pattern, "-not", "-path", "*/node_modules/*", "-not", "-path", "*/.git/*"]
    rc, out = _run(cmd, timeout=10)
    if not out.strip():
        await msg.answer(f"׳³ֲ׳³ג„¢׳³ֲ ׳³ֲ§׳³ג€˜׳³ֲ¦׳³ג„¢׳³ֲ ׳³ֳ—׳³ג€¢׳³ֲ׳³ֲ׳³ג„¢׳³ֲ ׳³ֲ\\-`{_md_escape(pattern)}`")
        return
    files = out.strip().split("\n")[:30]
    rels = [str(Path(f).relative_to(WORKSPACE)) for f in files if f]
    await msg.answer(f"׳ ֲג€ג€ ׳³ֲ ׳³ֲ׳³ֲ¦׳³ֲ׳³ג€¢ {len(rels)} ׳³ֲ§׳³ג€˜׳³ֲ¦׳³ג„¢׳³ֲ:\n```\n" + "\n".join(rels) + "\n```")


# ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬ Edit commands ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬

async def _cmd_append(msg: Message, parts: list[str]) -> None:
    if len(parts) < 2:
        await msg.answer("׳³ֲ©׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ©: `/append \\<׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥\\> \\<׳³ֻ׳³ֲ§׳³ֲ¡׳³ֻ\\>`")
        return
    args = parts[1].strip().split(maxsplit=1)
    if len(args) < 2:
        await msg.answer("׳ֲ¿ֲ½-׳³ֲ¡׳³ֲ¨ ׳³ֻ׳³ֲ§׳³ֲ¡׳³ֻ ׳³ֲ׳³ג€׳³ג€¢׳³ֲ¡׳³ג‚×׳³ג€")
        return
    p = _safe_path(args[0])
    if not p or not p.is_file():
        await msg.answer(f"׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥ ׳³ֲ׳³ֲ ׳³ֲ§׳³ג„¢׳³ג„¢׳³ֲ: `{_md_escape(args[0])}`")
        return
    text = args[1]
    try:
        with p.open("a", encoding="utf-8") as f:
            f.write(("\n" if not p.read_text(encoding="utf-8", errors="replace").endswith("\n") else "") + text + "\n")
    except Exception as e:
        await msg.answer(f"׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€: `{_md_escape(str(e))}`")
        return
    await msg.answer(f"׳’ֲג€¦ ׳³ֲ ׳³ג€¢׳³ֲ¡׳³ֲ£ ׳³ֲ\\-`{_md_escape(str(p.relative_to(WORKSPACE)))}`:\n`{_md_escape(text[:200])}`")


async def _cmd_replace(msg: Message, parts: list[str]) -> None:
    if len(parts) < 2 or "::" not in parts[1]:
        await msg.answer("׳³ֲ©׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ©: `/replace \\<׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥\\> :: \\<old\\> :: \\<new\\>`")
        return
    chunks = parts[1].split("::")
    if len(chunks) < 3:
        await msg.answer("׳ֲ¿ֲ½-׳³ֲ¡׳³ֲ¨ :: \\(׳³ֲ¦׳³ֲ¨׳³ג„¢׳³ֲ ׳³ֲ©׳³ֲ ׳³ג„¢\\)")
        return
    file_part = chunks[0].strip()
    old = chunks[1].strip()
    new = "::".join(chunks[2:]).strip()
    p = _safe_path(file_part)
    if not p or not p.is_file():
        await msg.answer(f"׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥ ׳³ֲ׳³ֲ ׳³ֲ§׳³ג„¢׳³ג„¢׳³ֲ: `{_md_escape(file_part)}`")
        return
    try:
        content = p.read_text(encoding="utf-8")
        if old not in content:
            await msg.answer(f"׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ׳³ֲ¦׳³ֲ ׳³ֻ׳³ֲ§׳³ֲ¡׳³ֻ: `{_md_escape(old[:80])}`")
            return
        count = content.count(old)
        new_content = content.replace(old, new)
        p.write_text(new_content, encoding="utf-8")
    except Exception as e:
        await msg.answer(f"׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€: `{_md_escape(str(e))}`")
        return
    await msg.answer(f"׳’ֲג€¦ ׳³ג€׳³ג€¢׳ֲ¿ֲ½-׳³ֲ׳³ֲ£ ׳³ג€˜\\-`{_md_escape(file_part)}`: {count} ׳³ֲ׳³ג€¢׳³ג‚×׳³ֲ¢׳³ג„¢׳³ֲ")


async def _cmd_newpage(msg: Message, parts: list[str]) -> None:
    if len(parts) < 2:
        await msg.answer("׳³ֲ©׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ©: `/newpage \\<׳³ֲ©׳³ֲ\\>` \\(׳³ֲ׳³ֲ׳³ֲ \\.html\\)")
        return
    name = parts[1].strip().split()[0]
    name = re.sub(r"[^a-z0-9_-]", "", name.lower())
    if not name:
        await msg.answer("׳³ֲ©׳³ֲ ׳³ֲ׳³ֲ ׳ֲ¿ֲ½-׳³ג€¢׳³ֲ§׳³ג„¢ \\(׳³ֲ׳³ֲ ׳³ג€™׳³ֲ׳³ג„¢׳³ֳ— ׳³ג€˜׳³ֲ׳³ג€˜׳³ג€\\)")
        return
    target = WEBSITE_DIR / f"{name}.html"
    if target.exists():
        await msg.answer(f"׳³ֲ§׳³ג„¢׳³ג„¢׳³ֲ: `{name}.html`")
        return
    template = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SLH ײ²ֲ· {name.title()}</title>
<link rel="icon" type="image/png" href="/favicon-32.png">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/shared.css?v=20260424a">
<style>
  body{{font-family:'Heebo',system-ui,sans-serif;background:#0a0f1c;color:#e8f4ff;margin:0;line-height:1.7}}
  .wrap{{max-width:980px;margin:0 auto;padding:80px 20px}}
  h1{{font-size:32px;font-weight:900;background:linear-gradient(135deg,#00b4d8,#5ba3ff);-webkit-background-clip:text;background-clip:text;color:transparent}}
</style>
</head>
<body>
<div id="topnav-root"></div>

<main class="wrap">
  <h1>{name.title()}</h1>
  <p>׳³ֳ—׳³ג€¢׳³ג€÷׳³ֲ ׳ֲ¿ֲ½-׳³ג€׳³ֲ© ׳’ג‚¬ג€ ׳³ֲ ׳³ג€¢׳³ֲ¦׳³ֲ¨ ׳³ג€׳³ֲ¨׳³ֲ @SLH_Claude_bot</p>
</main>

<div id="bottomnav-root"></div>
<div id="footer-root"></div>

<script src="/js/translations.js?v=20260424a"></script>
<script src="/js/shared.js?v=20260424a"></script>
<script>initShared({{activePage:'{name}',showBottomNav:true}});</script>
</body>
</html>
"""
    try:
        target.write_text(template, encoding="utf-8")
    except Exception as e:
        await msg.answer(f"׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€: `{_md_escape(str(e))}`")
        return
    await msg.answer(
        f"׳’ֲג€¦ ׳³ֲ ׳³ג€¢׳³ֲ¦׳³ֲ¨ `website/{name}.html` \\({len(template)} chars\\)\n\n"
        f"׳³ֲ׳³ֲ¨׳³ֲ׳³ג€¢׳³ֳ—: `/cat website/{name}.html`\n"
        f"׳³ֲ׳³ג€׳³ג€¢׳³ֲ¡׳³ג„¢׳³ֲ£ ׳³ֲ׳³ג€™׳³ג„¢׳³ֻ: `/sync \"feat: add {name} page\"`\n"
        f"׳³ֲ׳ֲ¿ֲ½-׳³ֲ¨׳³ג„¢ push ׳³ג„¢׳³ֲ¨׳³ֲ׳³ג€ ׳³ג€˜\\-https://slh\\-nft\\.com/{name}\\.html"
    )


# ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬ Git commands ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬

async def _cmd_commit(msg: Message, parts: list[str]) -> None:
    if len(parts) < 2:
        await msg.answer("׳³ֲ©׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ©: `/commit \\<׳³ג€׳³ג€¢׳³ג€׳³ֲ¢׳³ג€\\>`")
        return
    commit_msg = parts[1].strip()
    cwd = WEBSITE_DIR if (WEBSITE_DIR / ".git").exists() else WORKSPACE

    rc1, status = _run(["git", "status", "--short"], cwd=cwd, timeout=10)
    if not status.strip():
        await msg.answer("׳³ֲ׳³ג„¢׳³ֲ ׳³ֲ©׳³ג„¢׳³ֲ ׳³ג€¢׳³ג„¢׳³ג„¢׳³ֲ ׳³ֲcommit")
        return

    rc2, _ = _run(["git", "add", "-A"], cwd=cwd, timeout=15)
    if rc2 != 0:
        await msg.answer(f"git add ׳³ֲ ׳³ג€÷׳³ֲ©׳³ֲ")
        return

    env_args = [
        "-c", f"user.name={GIT_AUTHOR_NAME}",
        "-c", f"user.email={GIT_AUTHOR_EMAIL}",
    ]
    rc3, out = _run(["git"] + env_args + ["commit", "-m", commit_msg], cwd=cwd, timeout=20)
    if rc3 != 0:
        await msg.answer(f"commit ׳³ֲ ׳³ג€÷׳³ֲ©׳³ֲ:\n```\n{out[-2000:]}\n```")
        return

    rc4, sha_line = _run(["git", "log", "-1", "--oneline"], cwd=cwd, timeout=5)
    await msg.answer(
        f"׳’ֲג€¦ commit ׳³ג€׳³ג€¢׳³ֲ¦׳³ֲ׳ֲ¿ֲ½- ׳³ג€˜\\-`{cwd.name}`\n"
        f"```\n{sha_line.strip()[:300]}\n```\n"
        f"׳³ֲ׳³ג€׳³ֲ¢׳³ֲ׳³ג€¢׳³ֳ— ׳³ֲ׳³ג€™׳³ג„¢׳³ֻ\\-׳³ג€׳³ֲ׳³ג€˜: `/push`"
    )


async def _cmd_push(msg: Message, parts: list[str]) -> None:
    cwd = WEBSITE_DIR if (WEBSITE_DIR / ".git").exists() else WORKSPACE
    rc, out = _run(["git", "push"], cwd=cwd, timeout=60)
    if rc != 0:
        await msg.answer(f"push ׳³ֲ ׳³ג€÷׳³ֲ©׳³ֲ:\n```\n{_md_escape(out[-2000:])}\n```")
        return
    await msg.answer(f"׳’ֲג€¦ push ׳³ג€׳³ג€¢׳³ֲ¦׳³ֲ׳ֲ¿ֲ½- \\(`{cwd.name}`\\)\nGitHub Pages ׳³ג„¢׳³ֲ¢׳³ג€׳³ג€÷׳³ֲ ׳³ג€˜׳³ֲ¢׳³ג€¢׳³ג€ 30\\-60 ׳³ֲ©׳³ֲ ׳³ג„¢׳³ג€¢׳³ֳ—.")


async def _cmd_sync(msg: Message, parts: list[str]) -> None:
    """Combined commit + push in one step."""
    if len(parts) < 2:
        await msg.answer("׳³ֲ©׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ©: `/sync \\<׳³ג€׳³ג€¢׳³ג€׳³ֲ¢׳³ג€\\>`")
        return
    # Reuse commit logic
    await _cmd_commit(msg, parts)
    # Wait briefly then push
    await asyncio.sleep(1)
    await _cmd_push(msg, parts)


# ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬ AI-assisted draft flow ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬

async def _cmd_draft(msg: Message, parts: list[str]) -> None:
    """User: /draft <file> <instruction in Hebrew/English>
    Bot uses /api/ai/chat to generate a proposed change. Stores draft
    in _DRAFTS[chat_id]. User then runs /apply or /reject."""
    if len(parts) < 2:
        await msg.answer(
            "׳³ֲ©׳³ג„¢׳³ֲ׳³ג€¢׳³ֲ©: `/draft \\<׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥\\> \\<׳³ג€׳³ג€¢׳³ֲ¨׳³ֲ׳³ג€\\>`\n"
            "׳³ֲ׳³ג€׳³ג€¢׳³ג€™׳³ֲ׳³ג€: `/draft website/voice\\.html ׳³ֲ©׳³ֲ ׳³ג€ ׳³ֲ׳³ֳ— ׳³ג€׳³ג€÷׳³ג€¢׳³ֳ—׳³ֲ¨׳³ֳ— ׳³ֲMicroskick`"
        )
        return
    args = parts[1].strip().split(maxsplit=1)
    if len(args) < 2:
        await msg.answer("׳ֲ¿ֲ½-׳³ֲ¡׳³ֲ¨׳³ג€ ׳³ג€׳³ג€¢׳³ֲ¨׳³ֲ׳³ג€")
        return
    file_arg, instruction = args
    p = _safe_path(file_arg)
    if not p or not p.is_file():
        await msg.answer(f"׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥ ׳³ֲ׳³ֲ ׳³ֲ§׳³ג„¢׳³ג„¢׳³ֲ: `{_md_escape(file_arg)}`")
        return

    content = p.read_text(encoding="utf-8", errors="replace")
    if len(content) > 8000:
        await msg.answer(
            f"׳’ֲֲ ׳ֲ¸ֲ ׳³ג€׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥ ׳³ג€™׳³ג€׳³ג€¢׳³ֲ \\({len(content)} chars\\) \\׳’ג‚¬ג€ ׳³ֳ—׳³ֲ׳³ֲ¨ ׳³ג€˜׳³ג€׳³ג„¢׳³ג€¢׳³ֲ§ *׳³ֲ׳³ג„¢׳³ג€“׳³ג€ ׳ֲ¿ֲ½-׳³ֲ׳³ֲ§* ׳³ֲ׳³ֲ©׳³ֲ ׳³ג€¢׳³ֳ—, "
            "׳³ֲ׳³ג€¢ ׳³ג€׳³ֲ©׳³ֳ—׳³ֲ׳³ֲ© ׳³ג€˜\\-`/replace` ׳³ֲ׳³ֲ©׳³ג„¢׳³ֲ ׳³ג€¢׳³ג„¢ ׳³ֲ׳³ג€׳³ג€¢׳³ג„¢׳³ֲ§ ׳³ג€˜׳³ֲ׳³ֲ§׳³ג€¢׳³ֲ AI draft\\."
        )
        return

    await msg.bot.send_chat_action(msg.chat.id, "typing")

    prompt = (
        "׳³ֲ׳³ֳ—׳³ג€ ׳³ֲ¢׳³ג€¢׳³ג€“׳³ֲ¨ ׳³ֲ¢׳³ֲ¨׳³ג„¢׳³ג€÷׳³ג€ ׳³ֲ׳³ֲ׳³ֳ—׳³ֲ¨. ׳³ֳ—׳³ֲ§׳³ג€˜׳³ֲ ׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥ HTML/JS/CSS ׳³ג€¢׳³ג€׳³ג€׳³ג€¢׳³ֲ¨׳³ֲ׳³ג€ ׳³ֲ׳³ֲ©׳³ג„¢׳³ֲ ׳³ג€¢׳³ג„¢. "
        "׳³ֳ—׳ֲ¿ֲ½-׳³ג€“׳³ג„¢׳³ֲ¨ ׳³ג€˜׳³ג€׳³ג„¢׳³ג€¢׳³ֲ§ ׳³ֲ׳³ֳ— ׳³ג€׳³ג€“׳³ג€¢׳³ג€™: OLD: (׳³ֻ׳³ֲ§׳³ֲ¡׳³ֻ ׳³ֲ§׳³ג„¢׳³ג„¢׳³ֲ ׳³ֲ׳³ג€׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥) ׳³ג€¢-NEW: (׳³ג€׳ֲ¿ֲ½-׳³ֲ׳³ג‚×׳³ג€). "
        "׳³ֲ׳³ֲ׳³ֲ ׳³ג€׳³ֲ¡׳³ג€˜׳³ֲ¨׳³ג„¢׳³ֲ ׳³ֲ׳³ֲ¡׳³ג€˜׳³ג„¢׳³ג€˜. ׳³ֲ׳³ֲ׳³ֲ ׳³ֳ—׳³ג€™׳³ג„¢׳³ג€¢׳³ֳ— markdown. ׳³ֲ¨׳³ֲ§ 2 ׳³ג€˜׳³ֲ׳³ג€¢׳³ֲ§׳³ג„¢׳³ֲ: OLD: ... NEW: ...\n\n"
        f"--- INSTRUCTION ---\n{instruction}\n\n"
        f"--- FILE: {file_arg} ---\n{content}\n--- END FILE ---"
    )
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{API_BASE}/api/ai/chat",
                json={"message": prompt, "user_id": "claude_bot_editor", "lang": "he"},
            )
            data = resp.json()
            reply = data.get("reply", "")
    except Exception as e:
        await msg.answer(f"AI ׳³ֲ ׳³ג€÷׳³ֲ©׳³ֲ: `{_md_escape(str(e))}`")
        return

    # Parse OLD: / NEW: blocks
    old_match = re.search(r"OLD:\s*(.+?)(?=NEW:|$)", reply, re.DOTALL)
    new_match = re.search(r"NEW:\s*(.+?)$", reply, re.DOTALL)
    if not old_match or not new_match:
        await msg.answer(
            f"AI ׳³ֲ׳³ֲ ׳³ג€׳ֲ¿ֲ½-׳³ג€“׳³ג„¢׳³ֲ¨ OLD:/NEW: ׳³ג€˜׳³ג‚×׳³ג€¢׳³ֲ¨׳³ֲ׳³ֻ ׳³ֳ—׳³ֲ§׳³ג„¢׳³ֲ:\n```\n{reply[:800]}\n```\n"
            "׳³ֲ ׳³ֲ¡׳³ג€ ׳³ג€׳³ג€¢׳³ֲ¨׳³ֲ׳³ג€ ׳³ֲ¡׳³ג‚×׳³ֲ¦׳³ג„¢׳³ג‚×׳³ג„¢׳³ֳ— ׳³ג„¢׳³ג€¢׳³ֳ—׳³ֲ¨."
        )
        return

    old = old_match.group(1).strip().strip("`").strip()
    new = new_match.group(1).strip().strip("`").strip()

    if old not in content:
        await msg.answer(
            f"׳’ֲֲ ׳ֲ¸ֲ ׳³ג€-OLD ׳³ֲ©׳³ג€-AI ׳³ג€׳³ֲ¦׳³ג„¢׳³ֲ¢ ׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ׳³ֲ¦׳³ֲ ׳³ג€˜׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥. ׳³ֲ׳³ג€¢׳³ֲ׳³ג„¢ ׳³ג€׳³ג€¢׳³ֲ ׳³ג€׳³ֲ׳³ֲ¦׳³ג„¢׳³ֲ ׳³ֻ׳³ֲ§׳³ֲ¡׳³ֻ\\.\n"
            f"AI proposed OLD:\n```\n{old[:500]}\n```\n"
            "׳³ֲ ׳³ֲ¡׳³ג€ ׳³ג€׳³ג€¢׳³ֲ¨׳³ֲ׳³ג€ ׳³ֲ׳³ג€׳³ג€¢׳³ג„¢׳³ֲ§׳³ֳ— ׳³ג„¢׳³ג€¢׳³ֳ—׳³ֲ¨ \\(׳³ֲ¦׳³ג„¢׳³ג„¢׳³ֲ ׳³ֲ׳³ֳ— ׳³ג€׳³ֻ׳³ֲ§׳³ֲ¡׳³ֻ ׳³ג€׳³ֲ׳³ג€׳³ג€¢׳³ג„¢׳³ֲ§\\)."
        )
        return

    _DRAFTS[msg.chat.id] = {
        "file": file_arg,
        "old": old,
        "new": new,
        "instruction": instruction,
        "ts": time.time(),
    }

    preview = (
        f"׳ ֲג€ג€¹ *Draft ׳³ֲ׳³ג€¢׳³ג€÷׳³ֲ ׳³ֲ\\-{_md_escape(file_arg)}:*\n\n"
        f"*OLD:*\n```\n{old[:600]}\n```\n\n"
        f"*NEW:*\n```\n{new[:600]}\n```\n\n"
        f"׳³ֲ׳³ֲ׳³ֲ©׳³ֲ¨ ׳³ג€¢׳³ֲ׳³ֲ¢׳³ֲ׳³ג€¢׳³ֳ—: `/apply`\n"
        f"׳³ֲ׳³ג€˜׳³ֻ׳³ֲ: `/reject`"
    )
    await msg.answer(preview)


async def _cmd_apply(msg: Message, parts: list[str]) -> None:
    draft = _DRAFTS.get(msg.chat.id)
    if not draft:
        await msg.answer("׳³ֲ׳³ג„¢׳³ֲ draft ׳³ג‚×׳³ֳ—׳³ג€¢׳ֲ¿ֲ½-. ׳³ג€׳³ֲ¨׳³ֲ¥ `/draft` ׳³ֲ§׳³ג€¢׳³ג€׳³ֲ.")
        return
    if time.time() - draft["ts"] > 600:
        await msg.answer("Draft ׳³ג‚×׳³ג€™ ׳³ֳ—׳³ג€¢׳³ֲ§׳³ֲ£ \\(>10 ׳³ג€׳³ֲ§'\\). ׳³ג€׳³ֲ¨׳³ֲ¥ `/draft` ׳³ֲ©׳³ג€¢׳³ג€˜.")
        _DRAFTS.pop(msg.chat.id, None)
        return

    p = _safe_path(draft["file"])
    if not p or not p.is_file():
        await msg.answer(f"׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥ ׳³ֲ ׳³ֲ¢׳³ֲ׳³ֲ: `{_md_escape(draft['file'])}`")
        _DRAFTS.pop(msg.chat.id, None)
        return

    content = p.read_text(encoding="utf-8")
    if draft["old"] not in content:
        await msg.answer("׳³ג€׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥ ׳³ג€׳³ֲ©׳³ֳ—׳³ֲ ׳³ג€ ׳³ֲ׳³ֲ׳³ג€“ ׳³ג€\\-draft. ׳³ג€׳³ֲ¨׳³ֲ¥ ׳³ֲ©׳³ג€¢׳³ג€˜\\.")
        _DRAFTS.pop(msg.chat.id, None)
        return

    new_content = content.replace(draft["old"], draft["new"], 1)
    p.write_text(new_content, encoding="utf-8")
    _DRAFTS.pop(msg.chat.id, None)

    await msg.answer(f"׳’ֲג€¦ ׳³ג€׳³ג€¢׳ֲ¿ֲ½-׳³ֲ\\. ׳³ֲ¢׳³ג€÷׳³ֲ©׳³ג„¢׳³ג€¢ commit\\+push:")
    # Auto commit + push
    fake_parts = ["/sync", f"edit({draft['file']}): {draft['instruction'][:60]}"]
    await _cmd_sync(msg, fake_parts)


async def _cmd_reject(msg: Message, parts: list[str]) -> None:
    draft = _DRAFTS.pop(msg.chat.id, None)
    if not draft:
        await msg.answer("׳³ֲ׳³ג„¢׳³ֲ draft ׳³ג‚×׳³ֳ—׳³ג€¢׳ֲ¿ֲ½-\\.")
        return
    await msg.answer(f"׳’ֲֲ Draft ׳³ֲ\\-`{_md_escape(draft['file'])}` ׳³ג€˜׳³ג€¢׳³ֻ׳³ֲ\\.")


# ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬ Help ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬

EDITOR_HELP = (
    "*׳ ֲג€÷ֲ  ׳³ג‚×׳³ֲ§׳³ג€¢׳³ג€׳³ג€¢׳³ֳ— ׳³ֲ¢׳³ג€¢׳³ֲ¨׳³ֲ \\(׳³ֲ©׳³ֲ׳³ג„¢׳³ֻ׳³ג€ ׳³ֲ׳³ֲ׳³ֲ׳³ג€ ׳³ג€˜׳³ֲ׳³ֳ—׳³ֲ¨\\):*\n\n"
    "*Inspection:*\n"
    "`/cat <file>` \\- ׳³ֲ§׳³ֲ¨׳³ֲ ׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥\n"
    "`/ls [dir]` \\- ׳³ֲ¨׳³ֲ©׳³ג„¢׳³ֲ׳³ֳ— ׳³ֳ—׳³ג„¢׳³ֲ§׳³ג„¢׳³ג„¢׳³ג€\n"
    "`/grep <pat> [target]` \\- ׳ֲ¿ֲ½-׳³ג„¢׳³ג‚×׳³ג€¢׳³ֲ© ׳³ג€˜׳³ֳ—׳³ג€¢׳³ג€÷׳³ֲ\n"
    "`/find <pat> [dir]` \\- ׳ֲ¿ֲ½-׳³ג„¢׳³ג‚×׳³ג€¢׳³ֲ© ׳³ֲ©׳³ֲ׳³ג€¢׳³ֳ— ׳³ֲ§׳³ג€˜׳³ֲ¦׳³ג„¢׳³ֲ\n\n"
    "*Edit:*\n"
    "`/append <file> <text>` \\- ׳³ג€׳³ג€¢׳³ֲ¡׳³ֲ£ ׳³ֲ©׳³ג€¢׳³ֲ¨׳³ג€\n"
    "`/replace <file> :: <old> :: <new>` \\- ׳³ג€׳ֲ¿ֲ½-׳³ֲ׳³ֲ£\n"
    "`/newpage <name>` \\- ׳³ֲ¦׳³ג€¢׳³ֲ¨ ׳³ג€׳³ֲ£ ׳ֲ¿ֲ½-׳³ג€׳³ֲ©\n\n"
    "*Git:*\n"
    "`/commit <msg>` \\- commit ׳³ֲ©׳³ג„¢׳³ֲ ׳³ג€¢׳³ג„¢׳³ג„¢׳³ֲ\n"
    "`/push` \\- push ׳³ֲ׳³ג€™׳³ג„¢׳³ֻ\\-׳³ג€׳³ֲ׳³ג€˜\n"
    "`/sync <msg>` \\- commit \\+ push ׳³ג€˜׳³ג€˜׳³ֳ— ׳³ֲ׳ֲ¿ֲ½-׳³ֳ—\n\n"
    "*AI\\-assisted:*\n"
    "`/draft <file> <instruction>` \\- AI ׳³ֲ׳³ֲ¦׳³ג„¢׳³ֲ¢ ׳³ֲ©׳³ג„¢׳³ֲ ׳³ג€¢׳³ג„¢\n"
    "`/apply` \\- ׳³ֲ׳³ֲ©׳³ֲ¨ \\+ commit \\+ push\n"
    "`/reject` \\- ׳³ג€˜׳³ֻ׳³ֲ draft\n\n"
    "*׳³ג€׳³ג€¢׳³ג€™׳³ֲ׳³ג€ ׳³ֲ׳³ֲ׳³ֲ׳³ג€:*\n"
    "1\\. `/draft website/voice\\.html ׳³ֲ©׳³ֲ ׳³ג€ ׳³ֲ׳³ֳ— ׳³ג€׳³ג€÷׳³ג€¢׳³ֳ—׳³ֲ¨׳³ֳ— ׳³ֲ\\-Voice 2025`\n"
    "2\\. ׳³ג€˜׳³ג€׳³ג€¢׳³ֲ§ ׳³ֲ׳³ֳ— ׳³ג€diff\n"
    "3\\. `/apply` ׳’ג€ ג€™ ׳³ֲ׳³ג€¢׳³ֻ׳³ג€¢׳³ֲ׳³ֻ׳³ג„¢ ׳³ֲ¢׳³ג€¢׳³ֲ׳³ג€ ׳³ֲ׳³ג‚×׳³ֲ¨׳³ג€¢׳³ג€׳³ֲ§׳³ֲ©׳³ֲ"
)


# ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬ Public registration ׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬׳’ג€ג‚¬

def register(dp: Dispatcher, auth_module, _chunks_fn) -> None:
    """Wire up all editor commands. Call from bot.py main()."""

    def _gate(handler):
        async def wrapper(msg: Message, *args, **kwargs):
            if not auth_module.is_authorized(msg.from_user.id):
                await msg.answer(auth_module.unauthorized_reply_he(msg.from_user.id))
                return
            return await handler(msg, *args, **kwargs)
        return wrapper

    @dp.message(Command("cat"))
    @_gate
    async def h_cat(msg: Message):
        parts = (msg.text or "").split(maxsplit=1)
        await _cmd_cat(msg, parts, _chunks_fn)

    @dp.message(Command("ls"))
    @_gate
    async def h_ls(msg: Message):
        parts = (msg.text or "").split(maxsplit=1)
        await _cmd_ls(msg, parts)

    @dp.message(Command("grep"))
    @_gate
    async def h_grep(msg: Message):
        parts = (msg.text or "").split(maxsplit=1)
        await _cmd_grep(msg, parts)

    @dp.message(Command("find"))
    @_gate
    async def h_find(msg: Message):
        parts = (msg.text or "").split(maxsplit=1)
        await _cmd_find(msg, parts)

    @dp.message(Command("append"))
    @_gate
    async def h_append(msg: Message):
        parts = (msg.text or "").split(maxsplit=1)
        await _cmd_append(msg, parts)

    @dp.message(Command("replace"))
    @_gate
    async def h_replace(msg: Message):
        parts = (msg.text or "").split(maxsplit=1)
        await _cmd_replace(msg, parts)

    @dp.message(Command("newpage"))
    @_gate
    async def h_newpage(msg: Message):
        parts = (msg.text or "").split(maxsplit=1)
        await _cmd_newpage(msg, parts)

    @dp.message(Command("commit"))
    @_gate
    async def h_commit(msg: Message):
        parts = (msg.text or "").split(maxsplit=1)
        await _cmd_commit(msg, parts)

    @dp.message(Command("push"))
    @_gate
    async def h_push(msg: Message):
        parts = (msg.text or "").split(maxsplit=1)
        await _cmd_push(msg, parts)

    @dp.message(Command("sync"))
    @_gate
    async def h_sync(msg: Message):
        parts = (msg.text or "").split(maxsplit=1)
        await _cmd_sync(msg, parts)

    @dp.message(Command("draft"))
    @_gate
    async def h_draft(msg: Message):
        parts = (msg.text or "").split(maxsplit=1)
        await _cmd_draft(msg, parts)

    @dp.message(Command("apply"))
    @_gate
    async def h_apply(msg: Message):
        parts = (msg.text or "").split(maxsplit=1)
        await _cmd_apply(msg, parts)

    @dp.message(Command("reject"))
    @_gate
    async def h_reject(msg: Message):
        parts = (msg.text or "").split(maxsplit=1)
        await _cmd_reject(msg, parts)

    @dp.message(Command("editor"))
    @_gate
    async def h_editor(msg: Message):
        await msg.answer(EDITOR_HELP)

    log.info("editor_commands registered: cat ls grep find append replace newpage commit push sync draft apply reject editor")

