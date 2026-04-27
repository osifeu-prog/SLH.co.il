"""Anthropic Claude API wrapper with tool-use loop.

Runs a single conversation turn:
  user message -> Claude -> [tool calls -> tool results -> Claude]* -> final text
"""
import os
from anthropic import AsyncAnthropic
from tools import TOOLS, execute

API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "8192"))
MAX_TOOL_ROUNDS = 10  # prevent infinite tool loops

# ═══════════════════════════════════════════════════════════════════════════════
# OPTIMIZED 2026-04-27: Prompt rewritten + Anthropic prompt caching enabled.
# Static portion below is sent with cache_control → 90% discount on repeat reads
# (5-min cache window, auto-refreshing on each call). See shared/ai_optimizer.py
# ═══════════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """You are the SLH Spark Executor — Telegram-native AI operator helping Osif manage his bot ecosystem from his phone.

WHO YOU SERVE
Osif Kaufman Ungar — two Telegram IDs, both his: 224223270 (@osifeu_prog) primary, 8789977826 secondary. Treat both as same person for DB rows, handoffs, audit logs. Solo Hebrew-speaking dev. Runs 25 Telegram bots, FastAPI on Railway, 140+ page site on GitHub Pages.

HOW YOU COMMUNICATE
- Reply in Hebrew unless Osif writes English
- Direct. Short. No filler
- After tool calls: 1-2 Hebrew sentences summarizing result — don't dump raw output

WORKSPACE
Paths relative to /workspace = D:\\SLH_ECOSYSTEM on host. Key files:
- CLAUDE.md — project instructions
- ops/SESSION_HANDOFF_*.md — latest session state
- main.py + api/main.py — Railway API (sync both!)
- website/ — GitHub Pages repo

WORK RULES (from real bugs)
1. Railway builds from ROOT main.py, NOT api/main.py — always sync both
2. Hebrew UI, English code/commits
3. Never fake data — use [DEMO] tag
4. Never hardcode passwords in HTML — use localStorage
5. 500 ZVK max reward (50 SLH = ₪22,200!)

YOUR TOOLS
read_file / write_file / list_dir / bash (restricted) / git / http_get

SAFETY
.env writes blocked, .env reads auto-redacted. rm -rf, force-push, reset-hard blocked unless ALLOW_DESTRUCTIVE=true. If tool blocked, explain in Hebrew, ask how to proceed.

STYLE
- "מה נשבר" → run actual checks: curl /api/health, docker ps, git status
- Don't speculate — verify with tools
- Never invent data. Say "אני לא יודע" + suggest verification method
"""

# Try to import the optimizer (graceful fallback if shared/ not on path)
try:
    import sys, os as _os
    sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "..", "shared"))
    from ai_optimizer import build_cached_system, estimate_tokens
    _OPTIMIZER_AVAILABLE = True
    print(f"[claude_client] AI Optimizer loaded. System prompt = ~{estimate_tokens(SYSTEM_PROMPT)} tokens (cacheable)")
except ImportError:
    _OPTIMIZER_AVAILABLE = False
    print("[claude_client] AI Optimizer not available — running without prompt caching")


def _get_client() -> AsyncAnthropic:
    if not API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set. Add it to .env.")
    return AsyncAnthropic(api_key=API_KEY)


async def converse(history: list[dict], user_text: str) -> tuple[str, list[dict]]:
    """Run one turn. Returns (final_text_for_user, new_messages_to_persist).

    `new_messages_to_persist` is a list of {role, content} dicts that should be
    appended to the chat history by the caller.
    """
    client = _get_client()

    # Build message list: prior history + new user message
    messages = list(history)
    messages.append({"role": "user", "content": user_text})

    new_messages: list[dict] = [{"role": "user", "content": user_text}]
    final_text_parts: list[str] = []

    # Build the system parameter — uses prompt caching if optimizer is available.
    # First call writes to cache (~25% premium). Subsequent calls within 5 min
    # read from cache at ~10% of normal price → 90% savings on the system block.
    if _OPTIMIZER_AVAILABLE:
        system_param = build_cached_system(SYSTEM_PROMPT, enable_cache=True)
    else:
        system_param = SYSTEM_PROMPT

    for _round in range(MAX_TOOL_ROUNDS):
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_param,
            tools=TOOLS,
            messages=messages,
        )

        # Record the assistant turn (as structured content for tool-use continuity)
        assistant_blocks = [
            block.model_dump() if hasattr(block, "model_dump") else block
            for block in resp.content
        ]
        messages.append({"role": "assistant", "content": assistant_blocks})
        new_messages.append({"role": "assistant", "content": assistant_blocks})

        if resp.stop_reason != "tool_use":
            # Collect any text blocks and return
            for block in resp.content:
                if getattr(block, "type", None) == "text":
                    final_text_parts.append(block.text)
            break

        # Execute all tool calls in this turn, build tool_result blocks
        tool_results = []
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use":
                result = await execute(block.name, block.input or {})
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )
            elif getattr(block, "type", None) == "text" and block.text:
                # Intermediate narration — show it to the user so they see progress
                final_text_parts.append(block.text)

        messages.append({"role": "user", "content": tool_results})
        new_messages.append({"role": "user", "content": tool_results})
    else:
        final_text_parts.append(
            "\n\n[הגעתי למקסימום סבבי כלים. עצרתי כדי לא להיכנס ללולאה.]"
        )

    final_text = "\n\n".join(p for p in final_text_parts if p.strip())
    if not final_text:
        final_text = "(אין תשובה טקסטואלית — בדוק תוצאות כלים)"
    return final_text, new_messages
