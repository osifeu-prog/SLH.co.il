"""One-shot: capture the chat_id of the SLH coordination group.

Workflow:
  1. Add @SLH_Claude_bot (or any SLH bot) to the coordination group via the
     Telegram invite link.
  2. Run this script from the project root:
        python scripts/capture_coordination_chat_id.py
  3. Send any message in the group (e.g. "/id" or just "hi").
  4. The script prints the chat_id and exits. Copy that into .env as
        COORDINATION_GROUP_CHAT_ID=-100xxxxxxxxxx
     and into Railway env vars (same key/value).

Token resolution order:
  1. CAPTURE_BOT_TOKEN env var (override)
  2. SLH_CLAUDE_BOT_TOKEN env var (default — claude-bot)
  3. Fail.

Reads .env from project root and from slh-claude-bot/.env so the token can
live in either place.

Pure stdlib + httpx (already a dependency). Safe to delete after use.
"""

from __future__ import annotations

import asyncio
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))


def _load_dotenv_safe(path: str) -> None:
    """Best-effort .env loader. Falls back to manual parse if python-dotenv missing."""
    if not os.path.isfile(path):
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(path, override=False)
        return
    except ImportError:
        pass
    # Manual fallback
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


_load_dotenv_safe(os.path.join(ROOT, ".env"))
_load_dotenv_safe(os.path.join(ROOT, "slh-claude-bot", ".env"))

TOKEN = os.getenv("CAPTURE_BOT_TOKEN") or os.getenv("SLH_CLAUDE_BOT_TOKEN")
if not TOKEN:
    print(
        "ERROR: SLH_CLAUDE_BOT_TOKEN (or CAPTURE_BOT_TOKEN) not set.\n"
        "       Add it to .env or slh-claude-bot/.env, or export it.",
        file=sys.stderr,
    )
    sys.exit(1)


async def capture() -> int:
    try:
        import httpx
    except ImportError:
        print("ERROR: httpx not installed. Run: pip install httpx", file=sys.stderr)
        return 2

    print("=" * 60)
    print("SLH coordination chat_id capture")
    print("=" * 60)
    print()
    print("Listening for the next message in any group/supergroup.")
    print("Send any message in the coordination group to trigger capture.")
    print("(Ctrl-C to abort.)")
    print()

    offset: int | None = None
    async with httpx.AsyncClient(timeout=70.0) as client:
        while True:
            params = {"timeout": 60}
            if offset is not None:
                params["offset"] = offset
            try:
                r = await client.get(
                    f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                    params=params,
                )
            except httpx.RequestError as e:
                print(f"network error: {e}; retrying in 3s")
                await asyncio.sleep(3)
                continue
            if r.status_code != 200:
                print(f"telegram API returned {r.status_code}: {r.text[:200]}")
                return 3
            data = r.json()
            for u in data.get("result", []):
                offset = u["update_id"] + 1
                m = u.get("message") or u.get("edited_message") or u.get("channel_post")
                if not m:
                    continue
                chat = m.get("chat", {})
                chat_type = chat.get("type")
                chat_id = chat.get("id")
                title = chat.get("title")
                if chat_type in ("group", "supergroup", "channel"):
                    print()
                    print(f"FOUND group: chat_id={chat_id}  title={title!r}  type={chat_type}")
                    print()
                    print("Add to .env (project root) AND to Railway env vars:")
                    print(f"    COORDINATION_GROUP_CHAT_ID={chat_id}")
                    print()
                    print("Then restart claude-bot to activate:")
                    print("    docker compose restart claude-bot")
                    return 0
                else:
                    sender = m.get("from", {}).get("username") or m.get("from", {}).get("id")
                    print(f"  (skip {chat_type} from {sender}: not a group)")


def main() -> int:
    try:
        return asyncio.run(capture())
    except KeyboardInterrupt:
        print("\naborted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
