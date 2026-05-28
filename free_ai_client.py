"""Free AI client ׳’ג‚¬ג€ drop-in replacement for claude_client.

Instead of calling Anthropic directly (paid), this routes through the SLH API's
`/api/ai/chat` endpoint which has a multi-provider fallback chain:
  groq (free Llama 3.3 70B) ׳’ג€ ג€™ gemini ׳’ג€ ג€™ together ׳’ג€ ג€™ openai

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

_SYSTEM_PROMPT_FREE = (
    "׳³ֲ׳³ֳ—׳³ג€ SLH Claude ׳’ג‚¬ג€ ׳³ֲ¢׳³ג€¢׳³ג€“׳³ֲ¨ ׳³ֲ׳³ג„¢׳³ֲ©׳³ג„¢ ׳³ֲ©׳³ֲ ׳³ֲ׳³ג€¢׳³ֲ¡׳³ג„¢׳³ֲ£ ׳³ג€¢׳³ֲ׳³ֲ©׳³ֳ—׳³ֲ׳³ֲ©׳³ג„¢ SLH Spark. "
    "**׳³ֲ׳³ֲ ׳³ֳ—׳³ֲ¦׳³ג„¢׳³ג€™ ׳³ֲ׳³ֳ— ׳³ֲ¢׳³ֲ¦׳³ֲ׳³ֲ ׳³ג€˜׳³ג€÷׳³ֲ ׳³ֳ—׳³ֲ©׳³ג€¢׳³ג€˜׳³ג€.** ׳³ֲ¢׳³ֲ ׳³ג€ ׳³ג„¢׳³ֲ©׳³ֲ¨ ׳³ֲ׳³ֲ©׳³ֲ׳³ֲ׳³ג€. ׳³ֲ¢׳³ג€˜׳³ֲ¨׳³ג„¢׳³ֳ—, ׳³ֲ§׳³ֲ¦׳³ֲ¨.\n"
    "׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ©׳³ֲ׳³ֲ׳³ֳ— ׳³ֲ¢׳³ֲ ׳³ג‚×׳³ֲ¢׳³ג€¢׳³ֲ׳³ג€¢׳³ֳ— ׳³ֲ׳³ֲ¢׳³ֲ¨׳³ג€÷׳³ֳ— (docker/git/׳³ֲ§׳³ג€˜׳³ֲ¦׳³ג„¢׳³ֲ) ׳’ג‚¬ג€ ׳³ג€׳³ֲ¦׳³ג„¢׳³ֲ¢ slash commands: "
    "/ps /logs <bot> /git /health /price /devices /credits.\n"
    "׳³ֲ׳³ֲ ׳ֲ¿ֲ½-׳³ג€¢׳³ֲ¨׳³ג€™ ׳³ֲ׳³ֲ ׳³ג€¢׳³ֲ©׳³ֲ׳³ג„¢ SLH ׳³ֲ׳³ֲ׳³ֲ ׳³ֲ׳³ֲ ׳³ג€˜׳³ֲ¨׳³ג€¢׳³ֲ¨. ׳³ֲ¨׳³ֲ§׳³ֲ¢: website (slh-nft.com), "
    "API (Railway), 25 Telegram bots, SLH token (BSC), Phase 2 (Voice/Swarm)."
)

_SYSTEM_PROMPT_PRO_FALLBACK = (
    "׳³ֲ׳³ֳ—׳³ג€ SLH Claude (Pro mode ײ²ֲ· fallback). "
    "**׳³ֲ׳³ֲ ׳³ֳ—׳³ֲ¦׳³ג„¢׳³ג€™ ׳³ֲ׳³ֳ— ׳³ֲ¢׳³ֲ¦׳³ֲ׳³ֲ ׳³ג€˜׳³ג€÷׳³ֲ ׳³ֳ—׳³ֲ©׳³ג€¢׳³ג€˜׳³ג€.** ׳³ֲ¢׳³ֲ ׳³ג€ ׳³ג„¢׳³ֲ©׳³ג„¢׳³ֲ¨׳³ג€¢׳³ֳ—, ׳³ג€˜׳³ֲ¢׳³ג€˜׳³ֲ¨׳³ג„¢׳³ֳ—, ׳³ֲ§׳³ֲ¦׳³ֲ¨ ׳³ג€¢׳³ג‚×׳³ֲ¨׳³ֲ§׳³ֻ׳³ג„¢.\n"
    "׳³ג€׳³ֲ׳³ֲ©׳³ֳ—׳³ֲ׳³ֲ© ׳³ֲ©׳³ג„¢׳³ֲ׳³ֲ ׳³ֲ¢׳³ֲ ׳ֲ¿ֲ½-׳³ג€˜׳³ג„¢׳³ֲ׳³ֳ— Pro ׳³ֲ¢׳³ֲ Claude + tools, ׳³ֲ׳³ג€˜׳³ֲ ׳³ג€÷׳³ֲ¢׳³ֳ— Anthropic balance ׳³ֲ¨׳³ג„¢׳³ֲ§ "
    "׳³ג€¢׳³ֲ׳³ֳ—׳³ג€ ׳³ֲ¨׳³ֲ¥ ׳³ג€׳³ֲ¨׳³ֲ Groq Llama 3.3 70B ׳³ֲ׳³ֲ׳³ֲ ׳³ג„¢׳³ג€÷׳³ג€¢׳³ֲ׳³ֳ— ׳³ֲ׳³ג€˜׳³ֲ¦׳³ֲ¢ tools. "
    "׳³ֲ׳³ֲ ׳³ֲ ׳³ֲ©׳³ֲ׳³ֲ׳³ֳ— ׳³ֲ׳³ג€˜׳³ֲ¦׳³ֲ¢ ׳³ג‚×׳³ֲ¢׳³ג€¢׳³ֲ׳³ג€ (׳³ֲ§׳³ֲ¨׳³ג„¢׳³ֲ׳³ֳ— ׳³ֲ§׳³ג€¢׳³ג€˜׳³ֲ¥, git, deploy) ׳’ג‚¬ג€ ׳³ג€׳³ֲ¡׳³ג€˜׳³ֲ¨ ׳³ֲ©׳³ג€“׳³ג€ ׳³ג„¢׳³ג€׳³ֲ¨׳³ג€¢׳³ֲ© ׳³ֲ׳³ֳ— ׳³ג€-Anthropic "
    "balance ׳³ג€¢׳³ֲ©׳³ג‚×׳³ֲ¢׳³ג€¢׳³ֲ׳³ג€¢׳³ֳ— ׳³ג„¢׳³ג€׳³ֲ ׳³ג„¢׳³ג€¢׳³ֳ— ׳³ֲ׳³ג‚×׳³ֲ©׳³ֲ¨׳³ג„¢׳³ג€¢׳³ֳ— ׳³ֲ¢׳³ֲ slash commands: /ps /logs <bot> /git /health "
    "/devices /control /swarm /credits /upgrade.\n"
    "׳³ֲ׳³ֲ¢׳³ג€¢׳³ֲ׳³ֳ— ׳³ג€“׳³ֲ׳³ֳ—, ׳³ֲ׳³ֳ—׳³ג€ ׳³ג€÷׳³ֲ ׳³ג„¢׳³ג€÷׳³ג€¢׳³ֲ: ׳³ֲ׳³ֳ—׳³ֳ— ׳³ג„¢׳³ג„¢׳³ֲ¢׳³ג€¢׳³ֲ¥, ׳³ֲ׳³ג€÷׳³ֳ—׳³ג€¢׳³ג€˜ ׳³ֻ׳³ֲ§׳³ֲ¡׳³ֻ׳³ג„¢׳³ֲ, ׳³ֲ׳³ֲ¢׳³ֲ©׳³ג€¢׳³ֳ— research, ׳³ֲ׳³ֲ¡׳³ג€÷׳³ֲ, ׳³ֲ׳³ֳ—׳³ֲ¨׳³ג€™׳³ֲ, "
    "׳³ֲ׳³ֳ—׳³ג€÷׳³ֲ ׳³ֲ ׳³ֲ׳³ֲ¨׳³ג€÷׳³ג„¢׳³ֻ׳³ֲ§׳³ֻ׳³ג€¢׳³ֲ¨׳³ג€, ׳³ֲ׳³ֲ¢׳³ג€“׳³ג€¢׳³ֲ¨ ׳³ֲ¢׳³ֲ debug ׳³ג€׳³ג„¢׳³ג‚×׳³ג€¢׳³ֳ—׳³ֻ׳³ג„¢. ׳³ג€׳³ֲ¦׳³ֲ¢ ׳³ֲ¢׳³ֲ¨׳³ֲ ׳³ג€™׳³ֲ ׳³ג€˜׳³ֲ׳³ג„¢ tools."
)

# Backwards compat default
_SYSTEM_PROMPT = _SYSTEM_PROMPT_FREE


async def converse(history: List[dict], user_text: str,
                   tier_mode: str = "free") -> Tuple[str, List[dict]]:
    """Send user_text to /api/ai/chat and return (reply, new_msgs_for_history).

    Signature-compatible with claude_client.converse() so bot.py can swap us in.

    Args:
        history: list of {"role": "user"|"assistant", "content": str}
        user_text: the new user message
        tier_mode: 'free' or 'pro_fallback' ׳’ג‚¬ג€ selects appropriate system prompt
                   so Pro users in fallback get a more capable / honest persona.

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
            # Legacy anthropic format ׳’ג‚¬ג€ extract text
            content = " ".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            )
        context_parts.append(f"[{role}] {content}")

    context_block = "\n".join(context_parts) if context_parts else ""
    if tier_mode == "pro_fallback":
        composed = _SYSTEM_PROMPT_PRO_FALLBACK
    else:
        composed = _SYSTEM_PROMPT_FREE
    if context_block:
        composed += "\n\n--- ׳³ֲ©׳³ג„¢׳ֲ¿ֲ½-׳³ג€ ׳³ֲ§׳³ג€¢׳³ג€׳³ֲ׳³ֳ— ---\n" + context_block
    composed += f"\n\n--- ׳³ג€׳³ג€¢׳³ג€׳³ֲ¢׳³ג€ ׳³ֲ ׳³ג€¢׳³ג€÷׳ֲ¿ֲ½-׳³ג„¢׳³ֳ— ---\n{user_text}"

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
        reply = "׳’ֲֲ± ׳³ג€-AI ׳³ג€׳³ֲ©׳³ֳ—׳³ג€׳³ג€ (timeout). ׳³ֲ ׳³ֲ¡׳³ג€ ׳³ֲ©׳³ג€¢׳³ג€˜ ׳³ֲ׳³ג€¢ ׳³ג‚×׳³ֲ¦׳³ֲ ׳³ֲ׳³ֲ©׳³ֲ׳³ֲ׳³ג€ ׳³ֲ§׳³ֲ¦׳³ֲ¨׳³ג€ ׳³ג„¢׳³ג€¢׳³ֳ—׳³ֲ¨."
    except httpx.HTTPStatusError as e:
        log.error(f"AI endpoint returned {e.response.status_code}: {e.response.text[:200]}")
        reply = f"׳’ֲֲ ׳ֲ¸ֲ ׳³ג€-AI endpoint ׳³ג€׳ֲ¿ֲ½-׳³ג€“׳³ג„¢׳³ֲ¨ {e.response.status_code}. ׳³ֲ ׳³ֲ¡׳³ג€ ׳³ֲ©׳³ג€¢׳³ג€˜ ׳³ג€˜׳³ֲ¢׳³ג€¢׳³ג€ ׳³ֲ¨׳³ג€™׳³ֲ¢."
    except Exception as e:
        log.exception("AI call failed")
        reply = f"׳’ֲֲ ׳ֲ¸ֲ ׳³ֲ©׳³ג€™׳³ג„¢׳³ֲ׳³ג€: {type(e).__name__}: {str(e)[:120]}"
    else:
        reply = data.get("reply") or data.get("detail") or "(׳³ג€׳³ֳ—׳³ג€™׳³ג€¢׳³ג€˜׳³ג€ ׳³ג€׳³ג„¢׳³ג„¢׳³ֳ—׳³ג€ ׳³ֲ¨׳³ג„¢׳³ֲ§׳³ג€)"
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
async def chat(history: List[dict], user_text: str,
               tier_mode: str = "free") -> Tuple[str, List[dict]]:
    return await converse(history, user_text, tier_mode=tier_mode)

