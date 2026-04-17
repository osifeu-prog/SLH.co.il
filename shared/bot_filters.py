"""
SLH bot-to-bot filters — prevents multi-bot spam in shared Telegram groups.

Use pattern (every bot):
    from aiogram import Dispatcher
    from shared.bot_filters import install_cross_bot_filters

    dp = Dispatcher()
    install_cross_bot_filters(dp, BOT_USERNAME)  # e.g. "SLH_Ledger_bot"

Effects:
1. Drop messages from other bots (message.from_user.is_bot)
2. Drop commands addressed to other bots (/start@other_bot)
3. Drop duplicate rapid-fire messages (same text within 3s — prevents echo loops)
"""
import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import Message, TelegramObject, Update


class IgnoreOtherBotsMiddleware(BaseMiddleware):
    """Drops: bot-origin messages, wrong-@bot commands, echo duplicates."""

    def __init__(self, my_username: str, echo_window_sec: float = 3.0) -> None:
        self.my_username = (my_username or "").lower().lstrip("@")
        self.echo_window_sec = echo_window_sec
        self._recent: Dict[int, tuple] = {}  # chat_id -> (text, ts)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        msg = event.message if isinstance(event, Update) else (event if isinstance(event, Message) else None)
        if msg is None:
            return await handler(event, data)

        # 1. Skip messages from other bots entirely
        if msg.from_user and msg.from_user.is_bot:
            return None

        # 2. If command addresses a specific bot, make sure it's us
        text = (msg.text or "").strip()
        if text.startswith("/") and "@" in text:
            # /cmd@botname args...
            first_token = text.split()[0]
            if "@" in first_token:
                addressed = first_token.split("@", 1)[1].lower()
                if addressed != self.my_username:
                    return None  # not for us

        # 3. Echo protection — if same text in same chat within window, drop
        if msg.chat and text:
            key = msg.chat.id
            now = time.time()
            last = self._recent.get(key)
            if last and last[0] == text and (now - last[1]) < self.echo_window_sec:
                return None
            self._recent[key] = (text, now)
            # Simple cleanup: keep dict bounded
            if len(self._recent) > 500:
                cutoff = now - self.echo_window_sec
                self._recent = {k: v for k, v in self._recent.items() if v[1] >= cutoff}

        return await handler(event, data)


def install_cross_bot_filters(dp: Dispatcher, bot_username: str, echo_window_sec: float = 3.0) -> None:
    """Register IgnoreOtherBotsMiddleware on both message + callback_query handlers."""
    mw = IgnoreOtherBotsMiddleware(bot_username, echo_window_sec=echo_window_sec)
    dp.message.middleware(mw)
    dp.callback_query.middleware(mw)
