import httpx
import os
from typing import List, Dict

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RAILWAY_API_BASE = os.getenv("SLH_API_BASE", "https://slh-fastapi-production.up.railway.app")

async def ask_groq(messages: List[Dict]) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.7}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

async def ask_gemini(messages: List[Dict]) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"
    prompt = messages[-1]["content"]
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

async def ask_railway_api(messages: List[Dict]) -> str:
    url = f"{RAILWAY_API_BASE}/api/chat"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json={"messages": messages})
        resp.raise_for_status()
        return resp.json()["response"]

async def converse(messages: List[Dict]) -> str:
    if GROQ_API_KEY:
        try:
            return await ask_groq(messages)
        except Exception as e:
            print(f"Groq failed: {e}")
    if GEMINI_API_KEY:
        try:
            return await ask_gemini(messages)
        except Exception as e:
            print(f"Gemini failed: {e}")
    try:
        return await ask_railway_api(messages)
    except Exception as e:
        print(f"Railway API failed: {e}")
        return "âš ï¸ AI service unavailable. Please try again later."

