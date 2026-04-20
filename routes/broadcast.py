"""
SLH Broadcast — cross-post to multiple networks via one endpoint.
Starts with Telegram channel (@slhniffty, @SLH_AIR bot tokens).
Extendable to Twitter/LinkedIn/Facebook/Discord when OAuth tokens added.

Endpoints:
  POST /api/broadcast/publish        — post to chosen networks in one call
  POST /api/broadcast/telegram       — Telegram-only (uses bot token)
  POST /api/broadcast/discord        — Discord webhook (if DISCORD_WEBHOOK set)
  GET  /api/broadcast/status         — which networks are configured
  GET  /api/broadcast/history/{uid}  — user's broadcast history
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Optional, List

import aiohttp
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

router = APIRouter(prefix="/api/broadcast", tags=["Broadcast"])

_pool = None
def set_pool(pool):
    global _pool
    _pool = pool


TELEGRAM_CHANNEL = os.getenv("TELEGRAM_BROADCAST_CHANNEL", "@slhniffty")
SLH_AIR_TOKEN = os.getenv("SLH_AIR_TOKEN", "").strip()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
TWITTER_BEARER = os.getenv("TWITTER_BEARER_TOKEN", "").strip()
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
FACEBOOK_PAGE_TOKEN = os.getenv("FACEBOOK_PAGE_TOKEN", "").strip()
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "").strip()


async def _ensure_broadcast_tables(conn):
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS broadcast_history (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT,
            message TEXT NOT NULL,
            networks TEXT[] NOT NULL,
            results JSONB DEFAULT '{}'::jsonb,
            success_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_bc_hist_user ON broadcast_history(user_id, created_at DESC);
        """
    )


# ══════════════════ Per-network publishers ══════════════════

async def _post_telegram(text: str, channel: Optional[str] = None) -> dict:
    if not SLH_AIR_TOKEN:
        return {"ok": False, "error": "SLH_AIR_TOKEN not configured"}
    target = channel or TELEGRAM_CHANNEL
    url = f"https://api.telegram.org/bot{SLH_AIR_TOKEN}/sendMessage"
    payload = {"chat_id": target, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as r:
                data = await r.json()
                if not data.get("ok"):
                    return {"ok": False, "error": data.get("description", "unknown")}
                return {"ok": True, "message_id": data["result"].get("message_id"), "channel": target}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _post_discord(text: str) -> dict:
    if not DISCORD_WEBHOOK_URL:
        return {"ok": False, "error": "DISCORD_WEBHOOK_URL not configured"}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(DISCORD_WEBHOOK_URL, json={"content": text[:2000]}, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status not in (200, 204):
                    return {"ok": False, "error": f"discord returned {r.status}"}
                return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _post_twitter(text: str) -> dict:
    """Post to Twitter/X via API v2. Requires OAuth 2.0 bearer token (write scope)."""
    if not TWITTER_BEARER:
        return {"ok": False, "error": "TWITTER_BEARER_TOKEN not configured — setup at developer.twitter.com"}
    url = "https://api.twitter.com/2/tweets"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER}", "Content-Type": "application/json"}
    payload = {"text": text[:280]}  # Twitter 280 char limit
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as r:
                data = await r.json()
                if r.status != 201:
                    return {"ok": False, "error": data.get("detail") or data}
                return {"ok": True, "tweet_id": data.get("data", {}).get("id")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _post_linkedin(text: str) -> dict:
    """Post to LinkedIn via Marketing API v2. Requires OAuth with w_member_social scope."""
    if not LINKEDIN_ACCESS_TOKEN:
        return {"ok": False, "error": "LINKEDIN_ACCESS_TOKEN not configured — setup at developer.linkedin.com"}
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}", "Content-Type": "application/json", "X-Restli-Protocol-Version": "2.0.0"}
    # LinkedIn requires user URN — we need LINKEDIN_USER_URN env
    user_urn = os.getenv("LINKEDIN_USER_URN", "").strip()
    if not user_urn:
        return {"ok": False, "error": "LINKEDIN_USER_URN not configured"}
    payload = {
        "author": user_urn,  # e.g. "urn:li:person:XXX"
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status not in (200, 201):
                    err = await r.text()
                    return {"ok": False, "error": f"{r.status}: {err[:200]}"}
                data = await r.json()
                return {"ok": True, "post_urn": data.get("id")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _post_facebook(text: str) -> dict:
    """Post to Facebook Page via Graph API. Requires pages_manage_posts permission."""
    if not FACEBOOK_PAGE_TOKEN or not FACEBOOK_PAGE_ID:
        return {"ok": False, "error": "FACEBOOK_PAGE_TOKEN or FACEBOOK_PAGE_ID not configured"}
    url = f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/feed"
    payload = {"message": text, "access_token": FACEBOOK_PAGE_TOKEN}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, data=payload, timeout=aiohttp.ClientTimeout(total=15)) as r:
                data = await r.json()
                if "id" not in data:
                    return {"ok": False, "error": data.get("error", {}).get("message") or data}
                return {"ok": True, "post_id": data["id"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ══════════════════ Endpoints ══════════════════

class BroadcastReq(BaseModel):
    message: str
    networks: List[str] = ["telegram"]
    user_id: Optional[int] = None
    # Network-specific overrides
    telegram_channel: Optional[str] = None


NETWORK_PUBLISHERS = {
    "telegram": _post_telegram,
    "discord": _post_discord,
    "twitter": _post_twitter,
    "linkedin": _post_linkedin,
    "facebook": _post_facebook,
}


@router.post("/publish")
async def broadcast_publish(req: BroadcastReq, x_admin_key: Optional[str] = Header(None)):
    """Cross-post to selected networks. Returns per-network results."""
    # Admin check (broadcast is not public)
    admin_keys = [k.strip() for k in os.getenv("ADMIN_API_KEYS", "").split(",") if k.strip()]
    if not x_admin_key or x_admin_key not in admin_keys:
        raise HTTPException(403, "admin key required (X-Admin-Key header)")

    if not req.message.strip():
        raise HTTPException(400, "message is empty")
    if not req.networks:
        raise HTTPException(400, "networks list is empty")

    results = {}
    for net in req.networks:
        net = net.lower().strip()
        pub = NETWORK_PUBLISHERS.get(net)
        if not pub:
            results[net] = {"ok": False, "error": f"unknown network '{net}'. supported: {sorted(NETWORK_PUBLISHERS)}"}
            continue
        if net == "telegram":
            results[net] = await pub(req.message, req.telegram_channel)
        else:
            results[net] = await pub(req.message)

    success = sum(1 for r in results.values() if r.get("ok"))
    failed = len(results) - success

    # Log
    if _pool is not None:
        try:
            async with _pool.acquire() as conn:
                await _ensure_broadcast_tables(conn)
                await conn.execute(
                    """
                    INSERT INTO broadcast_history (user_id, message, networks, results, success_count, failed_count)
                    VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                    """,
                    req.user_id, req.message, req.networks, json.dumps(results), success, failed,
                )
        except Exception as e:
            print(f"[broadcast] log failed: {e}")

    return {
        "success_count": success,
        "failed_count": failed,
        "networks": req.networks,
        "results": results,
    }


@router.post("/telegram")
async def broadcast_telegram(req: BroadcastReq, x_admin_key: Optional[str] = Header(None)):
    """Telegram-only shortcut. Uses SLH_AIR_TOKEN + TELEGRAM_BROADCAST_CHANNEL."""
    admin_keys = [k.strip() for k in os.getenv("ADMIN_API_KEYS", "").split(",") if k.strip()]
    if not x_admin_key or x_admin_key not in admin_keys:
        raise HTTPException(403, "admin key required")
    result = await _post_telegram(req.message, req.telegram_channel)
    return result


@router.get("/status")
async def broadcast_status():
    """Which networks are configured (no tokens exposed)."""
    return {
        "telegram": {
            "configured": bool(SLH_AIR_TOKEN),
            "channel": TELEGRAM_CHANNEL,
            "bot": "@SLH_AIR_bot",
        },
        "discord": {"configured": bool(DISCORD_WEBHOOK_URL)},
        "twitter": {"configured": bool(TWITTER_BEARER)},
        "linkedin": {
            "configured": bool(LINKEDIN_ACCESS_TOKEN and os.getenv("LINKEDIN_USER_URN")),
        },
        "facebook": {
            "configured": bool(FACEBOOK_PAGE_TOKEN and FACEBOOK_PAGE_ID),
        },
        "supported_networks": sorted(NETWORK_PUBLISHERS.keys()),
    }


@router.get("/history/{user_id}")
async def broadcast_history(user_id: int, limit: int = 20):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    limit = max(1, min(limit, 100))
    async with _pool.acquire() as conn:
        await _ensure_broadcast_tables(conn)
        rows = await conn.fetch(
            """
            SELECT id, message, networks, success_count, failed_count, created_at
            FROM broadcast_history WHERE user_id=$1 ORDER BY id DESC LIMIT $2
            """,
            user_id, limit,
        )
    return {
        "broadcasts": [
            {
                "id": r["id"],
                "message": r["message"][:100] + ("..." if len(r["message"]) > 100 else ""),
                "networks": r["networks"],
                "success": r["success_count"],
                "failed": r["failed_count"],
                "created_at": r["created_at"].isoformat(),
            }
            for r in rows
        ],
    }
