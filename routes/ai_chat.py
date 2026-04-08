"""
SLH AI Chat — Multi-provider backend with automatic fallback
Providers (in priority order):
  1. Groq (free tier — llama-3.3-70b)
  2. Google Gemini (free tier — gemini-2.0-flash)
  3. Together.ai (free tier — meta-llama/Llama-3.3-70B-Instruct-Turbo-Free)
  4. OpenAI (paid — gpt-4o, if key available)
Keeps all API keys secure on server side.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os
import asyncio

router = APIRouter(prefix="/api/ai", tags=["AI"])

# === API Keys (set in Railway env vars) ===
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY", "")

SLH_SYSTEM_PROMPT = """You are SLH AI Assistant — the smart assistant for the SLH Ecosystem crypto investment platform.

About SLH:
- SLH is an Israeli crypto ecosystem with 20+ Telegram bots, a website (slh-nft.com), and its own token
- SLH Token: BSC contract 0xACb0A09414CEA1C879c67bB7A877E4e19480f022, price ₪444 ($121.64)
- 12 tokens in the ecosystem, 176 holders, 111M supply
- Staking plans: 30/60/90/180 days with up to 65% annual yield
- Admin wallet BSC: 0xD0617B54FB4b6b66307846f217b4D685800E3dA4
- Admin wallet TON: UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp

Your capabilities:
- Explain crypto concepts in simple terms
- Provide market analysis based on current trends
- Help users navigate the SLH ecosystem
- Recommend investment strategies (with disclaimers)
- Answer in the user's language (Hebrew, English, Russian, Arabic, French)

Important rules:
- Always add a disclaimer that this is not financial advice
- Be helpful, concise, and friendly
- If asked about specific prices, say you show real-time data on the trade page
- Promote SLH ecosystem features when relevant
- Keep responses under 300 words
"""


# === Provider Definitions ===

async def _call_groq(client: httpx.AsyncClient, messages: list) -> tuple[str, str]:
    """Groq — free tier, Llama 3.3 70B, very fast."""
    model = "llama-3.3-70b-versatile"
    r = await client.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages, "max_tokens": 500, "temperature": 0.7}
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"], f"groq/{model}"


async def _call_gemini(client: httpx.AsyncClient, messages: list) -> tuple[str, str]:
    """Google Gemini — free tier, Gemini 2.0 Flash."""
    model = "gemini-2.0-flash"
    # Gemini uses different message format
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        if msg["role"] == "system":
            # Gemini handles system as first user message
            contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will follow these instructions."}]})
        else:
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    r = await client.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": contents,
            "generationConfig": {"maxOutputTokens": 500, "temperature": 0.7}
        }
    )
    r.raise_for_status()
    data = r.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return text, f"gemini/{model}"


async def _call_together(client: httpx.AsyncClient, messages: list) -> tuple[str, str]:
    """Together.ai — free tier, Llama 3.3 70B Turbo."""
    model = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
    r = await client.post(
        "https://api.together.xyz/v1/chat/completions",
        headers={"Authorization": f"Bearer {TOGETHER_API_KEY}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages, "max_tokens": 500, "temperature": 0.7}
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"], f"together/{model.split('/')[-1]}"


async def _call_openai(client: httpx.AsyncClient, messages: list) -> tuple[str, str]:
    """OpenAI — paid, GPT-4o."""
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    r = await client.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages, "max_tokens": 500, "temperature": 0.7}
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"], f"openai/{model}"


# === Build provider chain ===

def _get_providers():
    """Return list of (name, callable) in priority order, only if key is set."""
    providers = []
    if GROQ_API_KEY:
        providers.append(("groq", _call_groq))
    if GEMINI_API_KEY:
        providers.append(("gemini", _call_gemini))
    if TOGETHER_API_KEY:
        providers.append(("together", _call_together))
    if OPENAI_API_KEY:
        providers.append(("openai", _call_openai))
    return providers


# === Request / Response Models ===

class ChatRequest(BaseModel):
    message: str
    user_id: str = ""
    lang: str = "en"

class ChatResponse(BaseModel):
    reply: str
    model: str


# === Endpoint ===

@router.post("/chat", response_model=ChatResponse)
async def ai_chat(req: ChatRequest):
    providers = _get_providers()
    if not providers:
        raise HTTPException(status_code=503, detail="AI service not configured — no API keys set")

    lang_hint = {
        "he": "Respond in Hebrew.",
        "en": "Respond in English.",
        "ru": "Respond in Russian.",
        "ar": "Respond in Arabic.",
        "fr": "Respond in French."
    }.get(req.lang, "Respond in English.")

    messages = [
        {"role": "system", "content": SLH_SYSTEM_PROMPT + "\n\n" + lang_hint},
        {"role": "user", "content": req.message}
    ]

    last_error = None

    async with httpx.AsyncClient(timeout=25.0) as client:
        for name, call_fn in providers:
            try:
                reply, model_id = await call_fn(client, messages)
                print(f"[AI] Success via {name}: {model_id}")
                return ChatResponse(reply=reply, model=model_id)
            except Exception as e:
                last_error = f"{name}: {e}"
                print(f"[AI] Provider {name} failed: {e}")
                continue

    raise HTTPException(status_code=502, detail=f"All AI providers failed. Last: {last_error}")


# === Provider status endpoint ===

@router.get("/providers")
async def ai_providers():
    """Show which AI providers are configured (no keys exposed)."""
    return {
        "providers": [
            {"name": "groq", "model": "llama-3.3-70b-versatile", "configured": bool(GROQ_API_KEY), "tier": "free"},
            {"name": "gemini", "model": "gemini-2.0-flash", "configured": bool(GEMINI_API_KEY), "tier": "free"},
            {"name": "together", "model": "Llama-3.3-70B-Instruct-Turbo-Free", "configured": bool(TOGETHER_API_KEY), "tier": "free"},
            {"name": "openai", "model": os.environ.get("OPENAI_MODEL", "gpt-4o"), "configured": bool(OPENAI_API_KEY), "tier": "paid"},
        ],
        "active_count": len(_get_providers())
    }
