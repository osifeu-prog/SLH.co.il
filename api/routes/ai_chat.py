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

class MeteredChatRequest(BaseModel):
    message: str
    user_id: int  # required for AIC accounting
    lang: str = "en"

class MeteredChatResponse(BaseModel):
    reply: str
    model: str
    aic_balance_before: float
    aic_balance_after: float
    aic_burned: float
    provider_tier: str  # "free" | "paid"


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


# === Metered Chat (AIC-gated) ==============================================
# Burns AIC from user balance before serving. Free tier = 0.5 AIC. Paid = 1 AIC.
# Returns 402 Payment Required if user has insufficient balance.
#
# First free allowance: if user has NEVER interacted with AIC (lifetime_earned == 0),
# auto-mint 5 AIC as welcome gift so they can try the AI 10 times.
# ============================================================================

FREE_TIER_COST = 0.5
PAID_TIER_COST = 1.0
WELCOME_GIFT = 5.0

_aic_pool_ref = None
def set_aic_pool(pool):
    """Called from main.py at startup to inject DB pool for AIC accounting."""
    global _aic_pool_ref
    _aic_pool_ref = pool


async def _check_and_reserve_aic(user_id: int, expected_cost: float) -> tuple[float, float]:
    """Ensure user has >= expected_cost AIC. Auto-gift 5 AIC on first-ever interaction.
    Returns (balance_before, welcome_gift_amount). Raises 402 if still insufficient.
    """
    if _aic_pool_ref is None:
        return (float("inf"), 0)  # AIC not wired — pass through

    async with _aic_pool_ref.acquire() as conn:
        # Ensure tables exist
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS aic_balances (
                user_id BIGINT PRIMARY KEY,
                balance NUMERIC(18,4) NOT NULL DEFAULT 0,
                lifetime_earned NUMERIC(18,4) NOT NULL DEFAULT 0,
                lifetime_spent NUMERIC(18,4) NOT NULL DEFAULT 0,
                updated_at TIMESTAMPTZ DEFAULT now()
            );
            """
        )
        row = await conn.fetchrow(
            "SELECT balance, lifetime_earned FROM aic_balances WHERE user_id=$1", user_id
        )
        welcome = 0.0
        if row is None or float(row["lifetime_earned"]) == 0:
            # First touch — welcome gift
            await conn.execute(
                """
                INSERT INTO aic_balances (user_id, balance, lifetime_earned)
                VALUES ($1, $2, $2)
                ON CONFLICT (user_id) DO UPDATE
                  SET balance = aic_balances.balance + EXCLUDED.balance,
                      lifetime_earned = aic_balances.lifetime_earned + EXCLUDED.lifetime_earned,
                      updated_at = now()
                """,
                user_id, WELCOME_GIFT,
            )
            await conn.execute(
                """INSERT INTO aic_transactions (user_id, kind, amount, reason, metadata)
                   VALUES ($1, 'mint', $2, 'system_seed', '{"source":"ai_first_chat"}'::jsonb)""",
                user_id, WELCOME_GIFT,
            )
            welcome = WELCOME_GIFT
            balance = WELCOME_GIFT + (float(row["balance"]) if row else 0)
        else:
            balance = float(row["balance"])

        if balance < expected_cost:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient AIC. Have {balance:.2f}, need {expected_cost}. Earn more via community activity or ask admin to top up.",
            )
        return balance, welcome


async def _burn_aic(user_id: int, amount: float, provider: str, tokens_consumed: int | None = None):
    if _aic_pool_ref is None:
        return
    async with _aic_pool_ref.acquire() as conn:
        await conn.execute(
            """
            UPDATE aic_balances SET
              balance = balance - $2,
              lifetime_spent = lifetime_spent + $2,
              updated_at = now()
            WHERE user_id = $1
            """,
            user_id, amount,
        )
        await conn.execute(
            """
            INSERT INTO aic_transactions (user_id, kind, amount, reason, provider, tokens_consumed)
            VALUES ($1, 'spend', $2, 'ai_chat', $3, $4)
            """,
            user_id, amount, provider, tokens_consumed,
        )


async def _get_balance(user_id: int) -> float:
    if _aic_pool_ref is None:
        return float("inf")
    async with _aic_pool_ref.acquire() as conn:
        row = await conn.fetchrow("SELECT balance FROM aic_balances WHERE user_id=$1", user_id)
    return float(row["balance"]) if row else 0.0


@router.post("/chat-metered", response_model=MeteredChatResponse)
async def ai_chat_metered(req: MeteredChatRequest):
    """AI chat with AIC accounting. Preferred endpoint for user-facing AI features.

    - Checks balance >= estimated cost
    - Gifts 5 AIC on first-ever chat (welcome)
    - Routes to first working provider
    - Burns actual cost after success (0.5 AIC free tier, 1 AIC paid)
    - Returns remaining balance + provider tier used
    """
    providers = _get_providers()
    if not providers:
        raise HTTPException(status_code=503, detail="AI service not configured — no API keys set")

    # Estimate cost — assume free tier first
    estimated_cost = FREE_TIER_COST
    balance_before, welcome = await _check_and_reserve_aic(req.user_id, estimated_cost)

    lang_hint = {
        "he": "Respond in Hebrew.",
        "en": "Respond in English.",
        "ru": "Respond in Russian.",
        "ar": "Respond in Arabic.",
        "fr": "Respond in French.",
    }.get(req.lang, "Respond in English.")

    messages = [
        {"role": "system", "content": SLH_SYSTEM_PROMPT + "\n\n" + lang_hint},
        {"role": "user", "content": req.message},
    ]

    last_error = None
    async with httpx.AsyncClient(timeout=25.0) as client:
        for name, call_fn in providers:
            try:
                reply, model_id = await call_fn(client, messages)
                # Determine tier + actual cost
                tier = "paid" if name == "openai" else "free"
                actual_cost = PAID_TIER_COST if tier == "paid" else FREE_TIER_COST
                # Re-check balance if paid
                if tier == "paid" and balance_before < actual_cost:
                    # downgrade — should not happen because we already reserved free cost,
                    # but protect against provider switch mid-flight
                    raise HTTPException(
                        status_code=402,
                        detail=f"Insufficient AIC for paid tier. Have {balance_before}, need {actual_cost}.",
                    )
                await _burn_aic(req.user_id, actual_cost, model_id)
                balance_after = await _get_balance(req.user_id)
                print(f"[AI-metered] {name} user={req.user_id} burned={actual_cost} balance={balance_after} welcome={welcome}")
                return MeteredChatResponse(
                    reply=reply,
                    model=model_id,
                    aic_balance_before=balance_before,
                    aic_balance_after=balance_after,
                    aic_burned=actual_cost,
                    provider_tier=tier,
                )
            except HTTPException:
                raise
            except Exception as e:
                last_error = f"{name}: {e}"
                print(f"[AI-metered] Provider {name} failed: {e}")
                continue

    raise HTTPException(status_code=502, detail=f"All AI providers failed. Last: {last_error}")


@router.get("/cost")
async def ai_cost():
    """Public: current AIC cost per AI call. UI uses this to display 'will cost X AIC'."""
    return {
        "free_tier_cost": FREE_TIER_COST,
        "paid_tier_cost": PAID_TIER_COST,
        "welcome_gift": WELCOME_GIFT,
        "currency": "AIC",
    }


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
