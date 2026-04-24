"""Free AI client — drop-in replacement for claude_client.

Instead of calling Anthropic directly (paid), this routes through the SLH API's
`/api/ai/chat` endpoint which has a multi-provider fallback chain:
  groq (free Llama 3.3 70B) → gemini → together → openai

This means @SLH_Claude_bot works at zero cost per message.

No tool use here (the multi-provider endpoint is chat-only); for executor
capabilities the bot exposes slash commands (/ps, /logs, /git, /exec).

Public surface matches claude_client.converse() so bot.py needs minimal changes.
"""
from __future__ import annotations
import os
import logging
from typing import List, Tuple

import httpx

log = logging.getLogger("slh-claude-bot.free-ai")

API_BASE = os.getenv("SLH_API_BASE", "https://slh-api-production.up.railway.app")
AI_ENDPOINT = os.getenv("SLH_AI_ENDPOINT", "/api/ai/chat")
AI_USER_ID = os.getenv("SLH_AI_USER_ID", "claude_bot_admin")
DEFAULT_LANG = os.getenv("SLH_AI_LANG", "he")
TIMEOUT = float(os.getenv("SLH_AI_TIMEOUT", "45"))

_SYSTEM_PROMPT = (
    "אתה SLH Claude — העוזר האישי של אוסיף, הבעלים של אקוסיסטם SLH. "
    "ענה בעברית, קצר וישיר. אם נשאלת על פקודות docker/git/file — "
    "הציע לאוסיף להשתמש ב-slash commands: /ps, /logs <bot>, /git, /health, /price, /devices. "
    "לא תענה על שאלות שלא קשורות ל-SLH אלא אם כן זה ברור. "
    "הפרויקט: website ב-GitHub Pages (slh-nft.com), API ב-Railway, 25 Telegram bots, "
    "token SLH ב-BSC, phase 2 vision (Voice + Swarm)."
)


async def converse(history: List[dict], user_text: str) -> Tuple[str, List[dict]]:
    """Send user_text to /api/ai/chat and return (reply, new_msgs_for_history).

    Signature-compatible with claude_client.converse() so bot.py can swap us in.

    Args:
        history: list of {"role": "user"|"assistant", "content": str}
        user_text: the new user message

    Returns:
        (reply_text, new_msgs) where new_msgs is the pair [user_msg, assistant_msg]
        ready to append to session history.
    """
    # Build context from history (keep last 6 turns = ~12 msgs for Groq context window)
    context_parts = []
    for m in history[-12:]:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            # Legacy anthropic format — extract text
            content = " ".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            )
        context_parts.append(f"[{role}] {content}")

    context_block = "\n".join(context_parts) if context_parts else ""
    composed = _SYSTEM_PROMPT
    if context_block:
        composed += "\n\n--- שיחה קודמת ---\n" + context_block
    composed += f"\n\n--- הודעה נוכחית ---\n{user_text}"

    payload = {
        "message": composed,
        "user_id": AI_USER_ID,
        "lang": DEFAULT_LANG,
    }

    url = API_BASE.rstrip("/") + AI_ENDPOINT
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        reply = "⏱ ה-AI השתהה (timeout). נסה שוב או פצל לשאלה קצרה יותר."
    except httpx.HTTPStatusError as e:
        log.error(f"AI endpoint returned {e.response.status_code}: {e.response.text[:200]}")
        reply = f"⚠️ ה-AI endpoint החזיר {e.response.status_code}. נסה שוב בעוד רגע."
    except Exception as e:
        log.exception("AI call failed")
        reply = f"⚠️ שגיאה: {type(e).__name__}: {str(e)[:120]}"
    else:
        reply = data.get("reply") or data.get("detail") or "(התגובה הייתה ריקה)"
        model = data.get("model", "unknown")
        # Append provider tag for transparency
        if model and model != "unknown":
            reply += f"\n\n_{model}_"

    new_msgs = [
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": reply},
    ]
    return reply, new_msgs


# Backwards-compatible alias
async def chat(history: List[dict], user_text: str) -> Tuple[str, List[dict]]:
    return await converse(history, user_text)
