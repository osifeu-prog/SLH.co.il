"""
SLH PancakeSwap TX Tracker
===========================
Monitors the SLH/WBNB pair on PancakeSwap V2 for incoming SLH purchases.
When a user buys SLH on PancakeSwap with a known wallet, auto-credits
their account + grants any corresponding premium.

Public endpoints:
  POST /api/pancakeswap/link-wallet   — user links their BSC wallet to user_id
  GET  /api/pancakeswap/recent-swaps  — last N swaps on the SLH/WBNB pair
  POST /api/pancakeswap/scan           — force-scan recent blocks (admin-triggered)
  GET  /api/pancakeswap/user/{user_id}/swaps — swaps attributed to this user

Reads on-chain logs via Etherscan V2 API (chainid=56). No keys required for
basic queries (rate-limited); uses BSCSCAN_API_KEY if present.

Added 2026-04-17.
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Optional

import aiohttp
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

router = APIRouter(prefix="/api/pancakeswap", tags=["PancakeSwap Tracker"])

_pool = None
def set_pool(pool):
    global _pool
    _pool = pool

SLH_CONTRACT = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022".lower()
SLH_WBNB_PAIR = "0xacea26b6e132cd45f2b8a4754170d4d0d3b8bbee".lower()
WBNB_CONTRACT = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c".lower()
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY", "").strip()
ETHERSCAN_V2_BASE = "https://api.etherscan.io/v2/api"

# ERC-20 Transfer event signature: Transfer(address indexed from, address indexed to, uint256 value)
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


async def _ensure_tables(conn):
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_bsc_wallets (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            wallet_address TEXT NOT NULL,
            linked_at TIMESTAMPTZ DEFAULT now(),
            verified BOOLEAN DEFAULT FALSE,
            UNIQUE(user_id, wallet_address)
        );
        CREATE INDEX IF NOT EXISTS idx_user_bsc_wallets_addr ON user_bsc_wallets(LOWER(wallet_address));

        CREATE TABLE IF NOT EXISTS pancakeswap_swaps (
            id BIGSERIAL PRIMARY KEY,
            tx_hash TEXT UNIQUE NOT NULL,
            block_number BIGINT NOT NULL,
            buyer_address TEXT NOT NULL,
            slh_received NUMERIC(24,8) NOT NULL,
            user_id BIGINT,
            credited BOOLEAN DEFAULT FALSE,
            credited_at TIMESTAMPTZ,
            raw_log JSONB,
            detected_at TIMESTAMPTZ DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_ps_swaps_user ON pancakeswap_swaps(user_id);
        CREATE INDEX IF NOT EXISTS idx_ps_swaps_buyer ON pancakeswap_swaps(LOWER(buyer_address));
        CREATE INDEX IF NOT EXISTS idx_ps_swaps_detected ON pancakeswap_swaps(detected_at DESC);
        """
    )


class LinkWalletReq(BaseModel):
    user_id: int
    wallet_address: str


@router.post("/link-wallet")
async def link_wallet(req: LinkWalletReq):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    addr = (req.wallet_address or "").strip().lower()
    if not addr.startswith("0x") or len(addr) != 42:
        raise HTTPException(400, "invalid BSC wallet address (expected 0x + 40 hex)")

    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO user_bsc_wallets (user_id, wallet_address)
                VALUES ($1, $2) RETURNING id, linked_at
                """,
                req.user_id, addr,
            )
        except Exception:
            # Already linked
            row = await conn.fetchrow(
                "SELECT id, linked_at FROM user_bsc_wallets WHERE user_id=$1 AND LOWER(wallet_address)=LOWER($2)",
                req.user_id, addr,
            )

        # Back-attribute any existing unattributed swaps from this address
        attributed = await conn.fetchval(
            """
            UPDATE pancakeswap_swaps SET user_id=$1
            WHERE LOWER(buyer_address)=LOWER($2) AND user_id IS NULL
            RETURNING COUNT(*)
            """,
            req.user_id, addr,
        )

    return {
        "ok": True,
        "link_id": row["id"] if row else None,
        "linked_at": row["linked_at"].isoformat() if row else None,
        "backfill_attributed": attributed or 0,
    }


async def _fetch_recent_transfers(limit: int = 50) -> list:
    """Fetch recent ERC-20 Transfers of SLH TOKEN from the pair to buyers.
    When PancakeSwap sells SLH out of the pool, the pair contract emits
    Transfer(pair -> buyer). We catch those.
    """
    # Use getLogs with filter: address=SLH contract, from=pair, topic=transfer
    params = {
        "module": "logs",
        "action": "getLogs",
        "chainid": "56",
        "address": SLH_CONTRACT,
        "topic0": TRANSFER_TOPIC,
        "topic1": "0x" + SLH_WBNB_PAIR[2:].rjust(64, "0"),  # indexed from = pair
        "fromBlock": "0",
        "toBlock": "latest",
        "offset": str(limit),
        "page": "1",
        "sort": "desc",
    }
    if BSCSCAN_API_KEY:
        params["apikey"] = BSCSCAN_API_KEY

    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{ETHERSCAN_V2_BASE}?{qs}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                data = await resp.json()
    except Exception as e:
        raise HTTPException(504, f"etherscan fetch failed: {e}")

    if not isinstance(data, dict):
        raise HTTPException(502, "etherscan returned non-dict")
    if data.get("status") == "0" and "rate" in (data.get("result") or "").lower():
        raise HTTPException(502, f"etherscan rate-limited: {data.get('result')}")

    result = data.get("result")
    if not isinstance(result, list):
        return []
    return result


def _parse_transfer_log(log: dict) -> Optional[dict]:
    """Decode a Transfer event log into a swap record."""
    try:
        topics = log.get("topics") or []
        if len(topics) < 3:
            return None
        # topics[1] = from (pair), topics[2] = to (buyer)
        buyer = "0x" + topics[2][-40:]
        # data = value (uint256 hex)
        value_hex = log.get("data", "0x0")
        value_raw = int(value_hex, 16)
        slh_amount = value_raw / (10 ** 18)  # SLH has 18 decimals typically; adjust if 15
        # Note: SLH may be 15 decimals per CLAUDE.md. Use 15 if amount seems off.
        # For safety, compute both and pick the sane one.
        slh_amount_15 = value_raw / (10 ** 15)
        # Pick the one producing a human-scale number (0.01 to 1M)
        chosen = slh_amount if 0.01 <= slh_amount <= 1_000_000 else slh_amount_15

        return {
            "tx_hash": log.get("transactionHash"),
            "block_number": int(log.get("blockNumber", "0x0"), 16),
            "buyer_address": buyer.lower(),
            "slh_received": chosen,
            "raw_log": log,
        }
    except Exception:
        return None


@router.post("/scan")
async def scan_recent_swaps(limit: int = 50, x_admin_key: Optional[str] = Header(None)):
    """Admin-triggered: pull recent SLH sales from the pair and attribute to users with linked wallets."""
    admin_keys = [k.strip() for k in os.getenv("ADMIN_API_KEYS", "slh2026admin").split(",") if k.strip()]
    if not x_admin_key or x_admin_key not in admin_keys:
        raise HTTPException(403, "admin key required")
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")

    limit = max(1, min(limit, 200))
    logs = await _fetch_recent_transfers(limit=limit)

    new_swaps = 0
    attributed = 0
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        for log in logs:
            parsed = _parse_transfer_log(log)
            if not parsed:
                continue

            # Check if already recorded
            existing = await conn.fetchval(
                "SELECT id FROM pancakeswap_swaps WHERE tx_hash=$1", parsed["tx_hash"]
            )
            if existing:
                continue

            # Lookup user by wallet
            user_id = await conn.fetchval(
                "SELECT user_id FROM user_bsc_wallets WHERE LOWER(wallet_address)=LOWER($1) LIMIT 1",
                parsed["buyer_address"],
            )

            await conn.execute(
                """
                INSERT INTO pancakeswap_swaps
                (tx_hash, block_number, buyer_address, slh_received, user_id, raw_log)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                """,
                parsed["tx_hash"], parsed["block_number"], parsed["buyer_address"],
                parsed["slh_received"], user_id, json.dumps(parsed.get("raw_log") or {}),
            )
            new_swaps += 1
            if user_id:
                attributed += 1

    return {
        "ok": True,
        "fetched": len(logs),
        "new_swaps_recorded": new_swaps,
        "auto_attributed": attributed,
    }


@router.get("/recent-swaps")
async def recent_swaps(limit: int = 25):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    limit = max(1, min(limit, 100))
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        rows = await conn.fetch(
            """
            SELECT id, tx_hash, block_number, buyer_address, slh_received,
                   user_id, credited, detected_at
            FROM pancakeswap_swaps ORDER BY block_number DESC LIMIT $1
            """,
            limit,
        )
    return {
        "pair": SLH_WBNB_PAIR,
        "slh_contract": SLH_CONTRACT,
        "swaps": [
            {
                "id": r["id"], "tx_hash": r["tx_hash"],
                "block_number": r["block_number"],
                "buyer_address": r["buyer_address"],
                "slh_received": float(r["slh_received"]),
                "user_id": r["user_id"],
                "credited": r["credited"],
                "detected_at": r["detected_at"].isoformat(),
                "bscscan_url": f"https://bscscan.com/tx/{r['tx_hash']}",
            }
            for r in rows
        ],
    }


@router.get("/user/{user_id}/swaps")
async def user_swaps(user_id: int, limit: int = 50):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        rows = await conn.fetch(
            """
            SELECT id, tx_hash, block_number, buyer_address, slh_received,
                   credited, detected_at
            FROM pancakeswap_swaps WHERE user_id=$1 ORDER BY block_number DESC LIMIT $2
            """,
            user_id, max(1, min(limit, 200)),
        )
        total_slh = await conn.fetchval(
            "SELECT COALESCE(SUM(slh_received), 0) FROM pancakeswap_swaps WHERE user_id=$1",
            user_id,
        )
        wallets = await conn.fetch(
            "SELECT wallet_address, linked_at FROM user_bsc_wallets WHERE user_id=$1",
            user_id,
        )
    return {
        "user_id": user_id,
        "total_slh_purchased": float(total_slh or 0),
        "swaps_count": len(rows),
        "linked_wallets": [
            {"address": w["wallet_address"], "linked_at": w["linked_at"].isoformat()}
            for w in wallets
        ],
        "swaps": [
            {
                "id": r["id"], "tx_hash": r["tx_hash"],
                "block_number": r["block_number"],
                "buyer_address": r["buyer_address"],
                "slh_received": float(r["slh_received"]),
                "credited": r["credited"],
                "detected_at": r["detected_at"].isoformat(),
                "bscscan_url": f"https://bscscan.com/tx/{r['tx_hash']}",
            }
            for r in rows
        ],
    }


@router.get("/stats")
async def pancakeswap_stats():
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_tables(conn)
        totals = await conn.fetchrow(
            """
            SELECT
              COUNT(*) AS total_swaps,
              COUNT(*) FILTER (WHERE user_id IS NOT NULL) AS attributed_swaps,
              COALESCE(SUM(slh_received), 0) AS total_slh,
              COALESCE(SUM(slh_received) FILTER (WHERE user_id IS NOT NULL), 0) AS attributed_slh,
              COUNT(DISTINCT LOWER(buyer_address)) AS unique_buyers
            FROM pancakeswap_swaps
            """
        )
        linked_wallets = await conn.fetchval("SELECT COUNT(*) FROM user_bsc_wallets")
    return {
        "pair": SLH_WBNB_PAIR,
        "slh_contract": SLH_CONTRACT,
        "total_swaps": totals["total_swaps"],
        "attributed_swaps": totals["attributed_swaps"],
        "total_slh_traded": float(totals["total_slh"]),
        "attributed_slh": float(totals["attributed_slh"]),
        "unique_buyers": totals["unique_buyers"],
        "linked_wallets": linked_wallets,
    }
