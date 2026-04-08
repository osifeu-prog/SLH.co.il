"""
SLH AI Chat — Backend proxy for OpenAI
Keeps API keys secure on server side
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter(prefix="/api/ai", tags=["AI"])

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

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

class ChatRequest(BaseModel):
    message: str
    user_id: str = ""
    lang: str = "en"

class ChatResponse(BaseModel):
    reply: str
    model: str

@router.post("/chat", response_model=ChatResponse)
async def ai_chat(req: ChatRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    lang_hint = {
        "he": "Respond in Hebrew.",
        "en": "Respond in English.",
        "ru": "Respond in Russian.",
        "ar": "Respond in Arabic.",
        "fr": "Respond in French."
    }.get(req.lang, "Respond in English.")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": SLH_SYSTEM_PROMPT + "\n\n" + lang_hint},
                        {"role": "user", "content": req.message}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
            )

            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="AI service error")

            data = response.json()
            reply = data["choices"][0]["message"]["content"]

            return ChatResponse(reply=reply, model=OPENAI_MODEL)

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI request timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
