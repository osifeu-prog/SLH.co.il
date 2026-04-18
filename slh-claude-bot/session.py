"""SQLite-backed conversation memory. One row per message, per Telegram chat."""
import aiosqlite
import json
import os
from typing import Any

DB_PATH = os.getenv("SESSION_DB", "/workspace/slh-claude-bot/sessions.db")
MAX_HISTORY = 40  # last N turns kept in context


async def init_db() -> None:
    # Ensure parent dir exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_msg_chat ON messages(chat_id, id)"
        )
        await db.commit()


async def append(chat_id: int, role: str, content: Any) -> None:
    """Append a message. content may be str or list[dict] (tool-use blocks)."""
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
            (chat_id, role, content),
        )
        await db.commit()


async def history(chat_id: int, limit: int = MAX_HISTORY) -> list[dict]:
    """Return last `limit` messages ordered oldest->newest, ready for Anthropic API."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT role, content FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT ?",
            (chat_id, limit),
        )
        rows = await cur.fetchall()
    # reverse to oldest-first
    out = []
    for role, content in reversed(rows):
        # try decode JSON (tool-use blocks), fall back to plain text
        try:
            parsed = json.loads(content)
            out.append({"role": role, "content": parsed})
        except (json.JSONDecodeError, TypeError):
            out.append({"role": role, "content": content})
    return out


async def clear(chat_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
        await db.commit()
        return cur.rowcount
