"""
Bot Heartbeat Client — drop-in module for any SLH bot.

Usage (in your bot's main.py):

    from shared.bot_heartbeat import start_heartbeat
    import asyncio

    async def main():
        await start_heartbeat(
            bot_name="ledger",
            display_name="SLH Ledger",
            username="@SLH_ledger_bot",
            version="1.0.0",
        )
        # ... rest of bot startup ...
        await dp.start_polling(bot)

What it does:
    Spawns a background task that POSTs to /api/bots/heartbeat every 30s.
    If the API is down it logs and keeps trying — never blocks the bot.

Env vars:
    SLH_API_URL       — defaults to https://slh-api-production.up.railway.app
    BOT_SYNC_SECRET   — shared secret (same one the API validates)
    HEARTBEAT_INTERVAL — seconds between heartbeats (default 30)
"""
from __future__ import annotations

import os
import asyncio
import logging
import time
from typing import Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None  # will raise loudly if someone tries to use this without it

log = logging.getLogger("slh.heartbeat")

API_URL = os.getenv("SLH_API_URL", "https://slh-api-production.up.railway.app").rstrip("/")
BOT_SECRET = os.getenv("BOT_SYNC_SECRET", "slh_bot_heartbeat_2026")
INTERVAL_SEC = int(os.getenv("HEARTBEAT_INTERVAL", "30"))


async def _post_heartbeat(
    session: "aiohttp.ClientSession",
    bot_name: str,
    display_name: Optional[str],
    username: Optional[str],
    version: Optional[str],
    metadata: Optional[dict],
) -> bool:
    """Single POST to /api/bots/heartbeat. Returns True on 200."""
    try:
        payload = {
            "bot_name": bot_name,
            "display_name": display_name,
            "username": username,
            "version": version,
            "metadata": metadata or {},
        }
        headers = {"X-Bot-Secret": BOT_SECRET, "Content-Type": "application/json"}
        async with session.post(
            f"{API_URL}/api/bots/heartbeat",
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=5),
        ) as resp:
            if resp.status == 200:
                return True
            body = await resp.text()
            log.warning("heartbeat non-200: status=%s body=%s", resp.status, body[:200])
            return False
    except asyncio.CancelledError:
        raise
    except Exception as e:
        log.warning("heartbeat error: %s", e)
        return False


async def _heartbeat_loop(bot_name: str, display_name: Optional[str],
                          username: Optional[str], version: Optional[str],
                          get_metadata):
    """Runs forever. Cancels cleanly on asyncio.CancelledError."""
    if aiohttp is None:
        log.error("aiohttp not installed — heartbeat disabled for %s", bot_name)
        return

    start_time = time.time()
    connector = aiohttp.TCPConnector(limit=2, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            try:
                meta = {}
                if callable(get_metadata):
                    try:
                        meta = get_metadata() or {}
                    except Exception:
                        meta = {}
                meta["uptime_seconds"] = int(time.time() - start_time)
                await _post_heartbeat(session, bot_name, display_name, username, version, meta)
            except asyncio.CancelledError:
                log.info("heartbeat loop for %s cancelled", bot_name)
                return
            except Exception as e:
                log.warning("heartbeat loop exception: %s", e)
            await asyncio.sleep(INTERVAL_SEC)


def start_heartbeat(
    bot_name: str,
    display_name: Optional[str] = None,
    username: Optional[str] = None,
    version: Optional[str] = None,
    get_metadata=None,
):
    """
    Fire-and-forget: start the heartbeat loop as a background task.

    Call this from your bot's startup after the event loop is running.
    The returned task is kept alive for the lifetime of the process.

    Args:
        bot_name: required, short identifier (e.g. "ledger", "academia")
        display_name: optional human name for admin panels
        username: optional Telegram @handle
        version: optional version string
        get_metadata: optional callable returning a dict to merge into metadata
    """
    loop = asyncio.get_event_loop()
    task = loop.create_task(
        _heartbeat_loop(bot_name, display_name, username, version, get_metadata)
    )
    # Prevent GC — module-level list keeps a ref
    _tasks.append(task)
    log.info("heartbeat started for bot=%s every=%ds api=%s", bot_name, INTERVAL_SEC, API_URL)
    return task


_tasks = []
