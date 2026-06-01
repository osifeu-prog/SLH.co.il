"""
bots/_shared/base_bot.py
SLH Base Bot — inherit this for any new or migrated bot.

Provides:
  - Aiogram 3.x setup (Bot + Dispatcher)
  - DB pool connection via SLH API
  - Bot registry heartbeat (every 30s)
  - Webhook support (production) + polling fallback (dev)
  - /start, /status, /help handlers (override as needed)
  - Graceful shutdown

Usage:
    from bots._shared.base_bot import SLHBaseBot
    from aiogram import types
    from aiogram.filters import Command

    class MyBot(SLHBaseBot):
        BOT_NAME    = "mybot"           # unique key for registry
        DISPLAY_NAME = "My Bot"
        USERNAME    = "@MyBot"
        VERSION     = "1.0.0"

        def register_handlers(self):
            super().register_handlers()  # keep /start, /status, /help

            @self.dp.message(Command("ping"))
            async def ping(m: types.Message):
                await m.answer("pong")

    if __name__ == "__main__":
        import asyncio
        asyncio.run(MyBot().run())
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Optional

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# ── Config ────────────────────────────────────────────────────────────────────

SLH_API_URL       = os.getenv("SLH_API_URL", "https://slh-fastapi-production.up.railway.app")
BOT_SYNC_SECRET   = os.getenv("BOT_SYNC_SECRET", "slh_bot_heartbeat_2026")
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
WEBHOOK_BASE_URL  = os.getenv("WEBHOOK_URL", "")       # e.g. https://slh-fastapi.up.railway.app
WEBHOOK_SECRET    = os.getenv("WEBHOOK_SECRET", "")
USE_WEBHOOK       = bool(WEBHOOK_BASE_URL)

logger = logging.getLogger("slh.bot")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


# ── Base Bot ──────────────────────────────────────────────────────────────────

class SLHBaseBot:
    """
    Base class for all SLH Telegram bots.
    Subclass and set class variables, then call run().
    """

    # ── Override in subclass ──
    BOT_NAME:     str = "base"
    DISPLAY_NAME: str = "SLH Bot"
    USERNAME:     str = "@SLH_bot"
    VERSION:      str = "1.0.0"
    DESCRIPTION:  str = "שירות SLH"

    def __init__(self):
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            raise SystemExit(f"[{self.BOT_NAME}] BOT_TOKEN env var missing — cannot start")

        self.bot = Bot(token=token)
        self.dp  = Dispatcher()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._session: Optional[aiohttp.ClientSession] = None

        self.register_handlers()

    # ── Handlers (override or extend) ────────────────────────────────────────

    def register_handlers(self):
        """Register default /start, /status, /help. Call super() from subclass."""

        @self.dp.message(Command("start"))
        async def start_cmd(m: types.Message):
            await m.answer(
                f"🚀 *{self.DISPLAY_NAME}*\n\n"
                f"{self.DESCRIPTION}\n\n"
                "פקודות:\n"
                "/status  — מצב חשבון\n"
                "/help    — עזרה\n",
                parse_mode="Markdown",
            )

        @self.dp.message(Command("status"))
        async def status_cmd(m: types.Message):
            uid = m.from_user.id
            data = await self._api_get(f"/api/user/{uid}")
            if data:
                slh = data.get("slh_balance", 0)
                mnh = data.get("mnh_balance", 0)
                rep = data.get("rep_score", 0)
                await m.answer(
                    f"📊 *מצב חשבון*\n\n"
                    f"Telegram ID: `{uid}`\n"
                    f"SLH: {slh:.2f}\n"
                    f"MNH: {mnh:.2f}\n"
                    f"REP: {rep}",
                    parse_mode="Markdown",
                )
            else:
                await m.answer("⚠️ לא נמצא חשבון. הירשם ב slh-nft.com")

        @self.dp.message(Command("help"))
        async def help_cmd(m: types.Message):
            await m.answer(
                f"ℹ️ *{self.DISPLAY_NAME}* v{self.VERSION}\n\n"
                "לעזרה נוספת: t.me/SLH_Community\n"
                "אתר: slh-nft.com",
                parse_mode="Markdown",
            )

    # ── API helpers ───────────────────────────────────────────────────────────

    async def _api_get(self, path: str, headers: dict = None) -> Optional[dict]:
        """GET from SLH API. Returns parsed JSON or None on error."""
        try:
            async with self._session.get(
                f"{SLH_API_URL}{path}",
                headers=headers or {},
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            logger.warning("[%s] API GET %s failed: %s", self.BOT_NAME, path, e)
        return None

    async def _api_post(self, path: str, data: dict, headers: dict = None) -> Optional[dict]:
        """POST to SLH API. Returns parsed JSON or None on error."""
        try:
            async with self._session.post(
                f"{SLH_API_URL}{path}",
                json=data,
                headers=headers or {},
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
        except Exception as e:
            logger.warning("[%s] API POST %s failed: %s", self.BOT_NAME, path, e)
        return None

    # ── Heartbeat ────────────────────────────────────────────────────────────

    async def _heartbeat_loop(self):
        """Send heartbeat to /api/bots/heartbeat every HEARTBEAT_INTERVAL seconds."""
        while True:
            try:
                await self._api_post(
                    "/api/bots/heartbeat",
                    {
                        "bot_name":    self.BOT_NAME,
                        "display_name": self.DISPLAY_NAME,
                        "username":    self.USERNAME,
                        "version":     self.VERSION,
                        "status":      "active",
                    },
                    headers={"X-Bot-Secret": BOT_SYNC_SECRET},
                )
                logger.debug("[%s] heartbeat sent", self.BOT_NAME)
            except Exception as e:
                logger.warning("[%s] heartbeat error: %s", self.BOT_NAME, e)
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def on_startup(self):
        """Called before polling/webhook starts. Override to add custom startup logic."""
        self._session = aiohttp.ClientSession()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("[%s] started (webhook=%s)", self.BOT_NAME, USE_WEBHOOK)

    async def on_shutdown(self):
        """Called on graceful shutdown."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._session:
            await self._session.close()
        await self.bot.session.close()
        logger.info("[%s] shut down gracefully", self.BOT_NAME)

    # ── Runner ────────────────────────────────────────────────────────────────

    async def run(self):
        """Start the bot — webhook in production, polling in dev."""
        await self.on_startup()

        try:
            if USE_WEBHOOK:
                await self._run_webhook()
            else:
                await self._run_polling()
        finally:
            await self.on_shutdown()

    async def _run_polling(self):
        logger.info("[%s] starting polling...", self.BOT_NAME)
        await self.dp.start_polling(self.bot, allowed_updates=self.dp.resolve_used_update_types())

    async def _run_webhook(self):
        webhook_path = f"/webhook/{self.BOT_NAME}"
        webhook_url  = f"{WEBHOOK_BASE_URL}{webhook_path}"

        await self.bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET or None,
            drop_pending_updates=True,
        )
        logger.info("[%s] webhook set: %s", self.BOT_NAME, webhook_url)

        # aiohttp server for webhook
        app = web.Application()
        SimpleRequestHandler(
            dispatcher=self.dp,
            bot=self.bot,
            secret_token=WEBHOOK_SECRET or None,
        ).register(app, path=webhook_path)
        setup_application(app, self.dp, bot=self.bot)

        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.getenv("PORT", "8080"))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info("[%s] webhook server on port %d", self.BOT_NAME, port)

        # Keep alive
        await asyncio.Event().wait()


# ── Minimal bot example ───────────────────────────────────────────────────────
# Copy this pattern for every new bot:
#
# from bots._shared.base_bot import SLHBaseBot
# from aiogram import types
# from aiogram.filters import Command
#
# class AcademiaBot(SLHBaseBot):
#     BOT_NAME     = "academia"
#     DISPLAY_NAME = "SLH Academia"
#     USERNAME     = "@SLH_Academia_bot"
#     VERSION      = "2.0.0"
#     DESCRIPTION  = "📚 למד, הרוויח ZVK, עלה ברמות"
#
#     def register_handlers(self):
#         super().register_handlers()
#
#         @self.dp.message(Command("courses"))
#         async def courses(m: types.Message):
#             data = await self._api_get("/api/courses/")
#             # ... render courses list
#
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(AcademiaBot().run())
