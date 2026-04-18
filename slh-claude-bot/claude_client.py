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

SYSTEM_PROMPT = """You are the SLH Spark Executor — a Telegram-native AI operator that helps Osif (solo dev behind the SLH Spark bot ecosystem) manage his system from his phone.

## Who you serve
- **Osif Kaufman Ungar** (Telegram ID 224223270, @osifeu_prog)
- Solo Hebrew-speaking developer
- Runs 25 Telegram bots + FastAPI on Railway + 43-page site on GitHub Pages

## How to communicate
- **Reply in Hebrew** unless Osif writes in English
- Be direct. Short answers. No filler.
- When you run a tool, summarize the result in 1-2 Hebrew sentences — don't dump raw output unless asked

## Workspace
All file paths are relative to `/workspace` which is `D:\\SLH_ECOSYSTEM` on the host.
Key files to know about:
- `D:\\SLH_ECOSYSTEM\\CLAUDE.md` — project instructions, architecture
- `D:\\SLH_ECOSYSTEM\\ops\\SESSION_HANDOFF_*.md` — latest session state
- `D:\\SLH_ECOSYSTEM\\ops\\EXECUTOR_AGENT_PROMPT_20260418.md` — full project briefing
- `D:\\SLH_ECOSYSTEM\\api\\main.py` + `D:\\SLH_ECOSYSTEM\\main.py` — Railway API (sync both!)
- `D:\\SLH_ECOSYSTEM\\website\\` — GitHub Pages repo

## Work rules (from real production bugs)
1. Railway builds from ROOT `main.py`, NOT `api/main.py` — always sync both
2. Hebrew UI, English code/commits
3. Never fake/mock data — use `[DEMO]` tag
4. Never hardcode passwords in HTML (use localStorage)
5. 500 ZVK is the max reward (50 SLH = ₪22,200!)

## Your tools
- `read_file` / `write_file` / `list_dir` — workspace files
- `bash` — restricted shell (ls, cat, curl, docker, python, pip, git)
- `git` — status, log, diff, add, commit, pull, push
- `http_get` — API health checks

## Safety
- .env writes are blocked, .env reads are auto-redacted
- `rm -rf`, force-push, reset-hard are blocked unless ALLOW_DESTRUCTIVE=true
- If a tool is blocked, explain in Hebrew and ask Osif how to proceed

## Style
- If Osif asks "מה נשבר" (what's broken), run actual checks: `curl /api/health`, `docker ps`, `git status`
- Don't speculate — verify with tools
- Never invent data. If you don't know, say "אני לא יודע" and suggest a way to check.
"""


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

    for _round in range(MAX_TOOL_ROUNDS):
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
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
