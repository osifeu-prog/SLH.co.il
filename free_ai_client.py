import logging
import os
import httpx

log = logging.getLogger("slh-claude-bot.free-ai")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TIMEOUT = float(os.getenv("SLH_AI_TIMEOUT", "30"))

GROQ_MODEL_PRIMARY = "llama-3.3-70b-versatile"
GROQ_MODEL_FALLBACK = "llama-3.1-8b-instant"
GEMINI_MODEL = "gemini-1.5-pro"

SYSTEM_PROMPT = (
    "You are SLH Spark AI — a helpful assistant.\n"
    "Respond in Hebrew, short and practical.\n"
    "If you don't know, say so directly."
)

async def _call_groq(messages: list[dict], model: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "max_tokens": 1024, "temperature": 0.7}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

async def _call_gemini(messages: list[dict]) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    parts = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        parts.append({"role": role, "parts": [{"text": m["content"]}]})
    payload = {"contents": parts}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

_LOCAL_REPLY = (
    "⚠️ No AI connection right now.\n\n"
    "Add free API keys to slh-claude-bot/.env:\n"
    "GROQ_API_KEY=gsk_...\n"
    "GEMINI_API_KEY=AIza...\n"
    "Commands that work without AI:\n"
    "/ps /logs /git /health /control /price /devices"
)

async def converse(history: list[dict], user_text: str, tier_mode: str = "free"):
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-6:]:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            msgs.append({"role": m["role"], "content": m["content"]})
    msgs.append({"role": "user", "content": user_text})

    reply = None
    if GROQ_API_KEY:
        try:
            reply = await _call_groq(msgs, GROQ_MODEL_PRIMARY)
            log.info("Groq answered (%d chars)", len(reply))
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                log.warning("Groq rate-limited, trying fallback model")
                try:
                    reply = await _call_groq(msgs, GROQ_MODEL_FALLBACK)
                except Exception as e2:
                    log.warning("Groq fallback failed: %s", e2)
            else:
                log.warning("Groq error: %s", e)
        except Exception as e:
            log.warning("Groq exception: %s", e)

    if reply is None and GEMINI_API_KEY:
        try:
            reply = await _call_gemini(msgs)
            log.info("Gemini answered (%d chars)", len(reply))
        except Exception as e:
            log.warning("Gemini failed: %s", e)

    if reply is None:
        reply = _LOCAL_REPLY

    new_msgs = [{"role": "user", "content": user_text}, {"role": "assistant", "content": reply}]
    return reply, new_msgs