import os
import json
import anthropic

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """
××ª×” SLH AI â€” ×¢×•×–×¨ ×˜×›× ×™ ×•×¢×¡×§×™ ×©×œ ×ž×¢×¨×›×ª SLH ×‘-Telegram.

## ×›×œ×œ×™× ×ž×•×—×œ×˜×™×:
1. ××œ ×ª×¡×›× ×ž×” ×”×ž×©×ª×ž×© ××ž×¨. ×”×•× ×™×•×“×¢ ×ž×” ××ž×¨.
2. ×ª×ž×™×“ ×ª×—×œ×™×˜. ×œ× "×™×© ×›×ž×” ××¤×©×¨×•×™×•×ª..." â€” ×ª×‘×—×¨ ××ª ×”×˜×•×‘×” ×‘×™×•×ª×¨.
3. ×§×¦×¨. ×ž×§×¡×™×ž×•× 5 ×©×•×¨×•×ª ×œ×ª×©×•×‘×” ×¨×’×™×œ×”. ×§×•×“ â€” ×‘×œ×•×§ ××—×“.
4. ×ª×ž×™×“ ×ª×¡×™×™× ×‘×¤×¢×•×œ×” ××—×ª ×‘×¨×•×¨×” â€” ×ž×” ×œ×¢×©×•×ª ×¢×›×©×™×•.
5. ×¢×‘×¨×™×ª ×¨××©×•× ×”. ×§×•×“ â€” ×× ×’×œ×™×ª.

## ×ž×” ××ª×” ×™×•×“×¢ ×¢×œ SLH:
- ×‘×•×˜ Telegram ×¢×œ Railway
- Stack: Python, aiogram v3, PostgreSQL, Redis, FastAPI
- ×§×‘×¦×™×: handlers_ux.py, responses.py, keyboards.py
- ×ž×¢×¨×›×ª: events â†’ ledger â†’ CRM â†’ analytics
- ×™×¢×“: autonomous platform ×¢× AI Dev Agent

## ×ª×‘× ×™×ª ×ª×’×•×‘×”:
[×ž×” ×œ×¢×©×•×ª â€” ×ž×©×¤×˜ ××—×“]

[×§×•×“ ×× ×¦×¨×™×š â€” ×§×¦×¨]

ðŸ‘‰ ×”×¦×¢×“ ×”×‘×: [×¤×¢×•×œ×” ××—×ª ×¡×¤×¦×™×¤×™×ª]

## ×“×•×’×ž×” × ×›×•× ×”:
×©××œ×”: "××™×š ×ž×•×¡×™×¤×™× checkin?"
×ª×©×•×‘×”:
×”×•×¡×£ handler ×‘-handlers_ux.py:

async def cmd_checkin(update, context):
    await _typing(update, context, 0.6)
    # DB logic here
    await _reply(update, R.msg_checkin_success(...), K.kb_after_checkin())
ðŸ‘‰ ×”×¦×¢×“ ×”×‘×: ×—×‘×¨ ×œ×¤×•× ×§×¦×™×™×ª DB ×”××ž×™×ª×™×ª ×©×œ×š ×‘-_get_user().

## ×“×•×’×ž×” ×©×’×•×™×” (××œ ×ª×¢×©×” ×–××ª):
"× ×¨××” ×©××ª×” ×‘×•× ×” ×ž×¢×¨×›×ª ×ž×ª×•×—×›×ž×ª... ×™×© ×ž×¡×¤×¨ ××¤×©×¨×•×™×•×ª... ×¨××©×™×ª... ×©× ×™×ª... ×œ×¡×™×›×•×..."
â† ×–×” ××¡×•×¨.
""".strip()

INTENT_SYSTEM = """
Classify the user message. Return ONLY valid JSON, no other text.

{
  "intent": "code|architecture|debug|question|command|chat",
  "topic": "checkin|ledger|wallet|store|ci_cd|docker|ai|general",
  "lang": "he|en|mixed",
  "needs_code": true|false
}
""".strip()

def detect_intent(message: str) -> dict:
    try:
        resp = _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            system=INTENT_SYSTEM,
            messages=[{"role": "user", "content": message}],
        )
        return json.loads(resp.content[0].text)
    except Exception:
        return {"intent": "chat", "topic": "general", "lang": "he", "needs_code": False}

def ask_slh_ai(
    message: str,
    history: list | None = None,
    user_context: dict | None = None,
) -> str:
    context_block = ""
    if user_context:
        context_block = (
            f"\n\n[User context: {user_context.get('username', 'unknown')} | "
            f"tier={user_context.get('tier', 'free')} | "
            f"points={user_context.get('points', 0)} | "
            f"streak={user_context.get('streak', 0)}]"
        )

    system = SYSTEM_PROMPT + context_block
    messages = list(history or [])
    messages.append({"role": "user", "content": message})

    try:
        resp = _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=system,
            messages=messages,
        )
        return resp.content[0].text.strip()
    except anthropic.APIError as e:
        return f"âš ï¸ ×©×’×™××ª AI: {e.status_code}"
    except Exception as e:
        return f"âš ï¸ ×©×’×™××”: {str(e)}"

class ConversationMemory:
    def __init__(self, max_turns: int = 10):
        self._store: dict[int, list[dict]] = {}
        self.max_turns = max_turns

    def add(self, user_id: int, role: str, content: str):
        if user_id not in self._store:
            self._store[user_id] = []
        self._store[user_id].append({"role": role, "content": content})
        if len(self._store[user_id]) > self.max_turns * 2:
            self._store[user_id] = self._store[user_id][-(self.max_turns * 2):]

    def get(self, user_id: int) -> list[dict]:
        return self._store.get(user_id, [])

    def clear(self, user_id: int):
        self._store.pop(user_id, None)

memory = ConversationMemory()

