"""
SLH Ecosystem — Blockchain Wallet Engine
=========================================
Provides on-chain reads (BSC / TON), internal ledger transfers,
deposit verification, portfolio queries and live price feeds.

Importable by both the FastAPI website API and Telegram bots.
"""

from __future__ import annotations

import os
import json
import hashlib
import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import asyncpg
import httpx
import redis.asyncio as aioredis
from web3 import AsyncWeb3, Web3
from web3.providers import AsyncHTTPProvider

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SLH_TOKEN_ADDRESS = Web3.to_checksum_address(
    "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"
)
SLH_DECIMALS = 15
SLH_PRICE_ILS = Decimal("444")

TON_WALLET = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
TON_API_BASE = "https://toncenter.com/api/v2"
TON_API_KEY = os.environ.get("TON_API_KEY", "fab6ade5108d472959112b2c2daba07c669826b221def532d8d38d7088cf65cd")

BSC_RPC = os.environ.get("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")

ABI_PATH = Path(__file__).parent / "slh_token_abi.json"

# Database: prefer RAILWAY env vars, fallback to Railway production
DATABASE_URL = os.environ.get(
    "RAILWAY_DATABASE_URL",
    os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:svNeqdqVRohdWMyPTiaqLHmZXlzIneuD"
        "@junction.proxy.rlwy.net:17913/railway"
    ),
)
REDIS_URL = os.environ.get(
    "RAILWAY_REDIS_URL",
    os.environ.get(
        "REDIS_URL",
        "redis://default:HmOAFgZBjEiPMYCMPUeeAipeLZgudHSU"
        "@junction.proxy.rlwy.net:12921"
    ),
)

COINGECKO_IDS = "bitcoin,ethereum,toncoin,binancecoin"

PRICE_CACHE_TTL = 60  # seconds

logger = logging.getLogger("wallet_engine")

# ---------------------------------------------------------------------------
# SQL — table creation
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS wallets (
    user_id       BIGINT PRIMARY KEY,
    bsc_address   TEXT,
    ton_address   TEXT,
    slh_balance   TEXT NOT NULL DEFAULT '0',
    bnb_balance   TEXT NOT NULL DEFAULT '0',
    ton_balance   TEXT NOT NULL DEFAULT '0',
    zvk_balance   TEXT NOT NULL DEFAULT '0',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transactions (
    id            BIGSERIAL PRIMARY KEY,
    from_user_id  BIGINT,
    to_user_id    BIGINT,
    amount        TEXT NOT NULL,
    token         TEXT NOT NULL,
    type          TEXT NOT NULL,
    tx_hash       TEXT,
    chain         TEXT,
    status        TEXT NOT NULL DEFAULT 'completed',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tx_from ON transactions (from_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tx_to   ON transactions (to_user_id,   created_at DESC);

CREATE TABLE IF NOT EXISTS deposits (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL,
    address       TEXT NOT NULL,
    amount        TEXT NOT NULL,
    token         TEXT NOT NULL,
    tx_hash       TEXT UNIQUE NOT NULL,
    chain         TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending',
    confirmed_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_dep_user ON deposits (user_id, confirmed_at DESC);
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_abi() -> list:
    with open(ABI_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _deterministic_address(user_id: int) -> str:
    """
    Derive a deterministic pseudo-address for a user.
    This is NOT a real private-key-backed address — it is used only as a
    unique deposit tag so the system can identify which user a deposit
    belongs to.  For production custody you would integrate a proper HD
    wallet or MPC signer.
    """
    raw = hashlib.sha256(f"slh-deposit-{user_id}".encode()).hexdigest()
    return Web3.to_checksum_address("0x" + raw[:40])


# ---------------------------------------------------------------------------
# WalletEngine
# ---------------------------------------------------------------------------


class WalletEngine:
    """Async wallet engine for the SLH Ecosystem."""

    def __init__(
        self,
        db_url: str = DATABASE_URL,
        redis_url: str = REDIS_URL,
        bsc_rpc: str = BSC_RPC,
    ):
        self._db_url = db_url
        self._redis_url = redis_url
        self._bsc_rpc = bsc_rpc

        self._pool: Optional[asyncpg.Pool] = None
        self._redis: Optional[aioredis.Redis] = None

        # Web3 (async)
        self._w3 = AsyncWeb3(AsyncHTTPProvider(bsc_rpc))
        self._abi = _load_abi()
        self._slh_contract = self._w3.eth.contract(
            address=SLH_TOKEN_ADDRESS, abi=self._abi
        )

        # httpx client for external API calls
        self._http: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def init(self) -> None:
        """Call once at app startup."""
        # Phase 0B (2026-04-21): unified fail-fast pool via shared_db_core.
        try:
            from shared_db_core import init_db_pool as _shared_init_db_pool
            self._pool = await _shared_init_db_pool(self._db_url)
        except Exception as _shared_err:
            logger.warning(f"shared_db_core unavailable, direct pool: {_shared_err}")
            self._pool = await asyncpg.create_pool(self._db_url, min_size=2, max_size=10)
        self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        self._http = httpx.AsyncClient(timeout=15)
        # ensure tables
        async with self._pool.acquire() as conn:
            await conn.execute(SCHEMA_SQL)
        logger.info("WalletEngine initialised — DB & Redis connected")

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
        if self._redis:
            await self._redis.close()
        if self._http:
            await self._http.aclose()

    # ------------------------------------------------------------------
    # Ensure wallet row exists
    # ------------------------------------------------------------------

    async def _ensure_wallet(self, user_id: int) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO wallets (user_id, bsc_address, ton_address)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id,
                _deterministic_address(user_id),
                None,
            )

    # ------------------------------------------------------------------
    # On-chain reads
    # ------------------------------------------------------------------

    async def get_slh_balance(self, address: str) -> str:
        """Return human-readable SLH token balance for a BSC address."""
        address = Web3.to_checksum_address(address)
        raw: int = await self._slh_contract.functions.balanceOf(address).call()
        return str(Decimal(raw) / Decimal(10**SLH_DECIMALS))

    async def get_bnb_balance(self, address: str) -> str:
        """Return BNB balance in ether units for a BSC address."""
        address = Web3.to_checksum_address(address)
        wei = await self._w3.eth.get_balance(address)
        return str(Web3.from_wei(wei, "ether"))

    async def get_ton_balance(self, address: str) -> str:
        """Return TON balance via toncenter public API."""
        try:
            resp = await self._http.get(
                f"{TON_API_BASE}/getAddressBalance",
                params={"address": address, "api_key": TON_API_KEY},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("ok"):
                nano = int(data["result"])
                return str(Decimal(nano) / Decimal(10**9))
        except Exception as exc:
            logger.error("TON balance fetch failed: %s", exc)
        return "0"

    # ------------------------------------------------------------------
    # Deposit address generation
    # ------------------------------------------------------------------

    async def generate_deposit_address(self, user_id: int) -> Dict[str, str]:
        """
        Return (or create) the deterministic BSC deposit address for a user.
        Also stores it in the wallets table.
        """
        await self._ensure_wallet(user_id)
        bsc_addr = _deterministic_address(user_id)
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE wallets SET bsc_address = $1 WHERE user_id = $2",
                bsc_addr,
                user_id,
            )
        return {
            "bsc_address": bsc_addr,
            "ton_address": TON_WALLET,  # shared TON address; memo = user_id
            "memo": str(user_id),
        }

    # ------------------------------------------------------------------
    # Deposit verification
    # ------------------------------------------------------------------

    async def process_deposit(
        self,
        user_id: int,
        tx_hash: str,
        chain: Literal["bsc", "ton"],
    ) -> Dict[str, Any]:
        """
        Verify a deposit on-chain and credit the user's internal balance.
        Returns the deposit record dict.
        """
        await self._ensure_wallet(user_id)

        # check for duplicate
        async with self._pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM deposits WHERE tx_hash = $1", tx_hash
            )
            if existing:
                return {"error": "tx_hash already processed", "deposit_id": existing["id"]}

        amount = Decimal("0")
        token = "SLH"

        if chain == "bsc":
            amount, token = await self._verify_bsc_tx(user_id, tx_hash)
        elif chain == "ton":
            amount, token = await self._verify_ton_tx(user_id, tx_hash)
        else:
            return {"error": f"Unsupported chain: {chain}"}

        if amount <= 0:
            return {"error": "Could not verify deposit amount"}

        amount_str = str(amount)
        now = datetime.now(timezone.utc)

        balance_col = f"{token.lower()}_balance"
        if balance_col not in ("slh_balance", "bnb_balance", "ton_balance"):
            return {"error": f"Unknown token {token}"}

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                dep_addr = _deterministic_address(user_id)
                deposit_id = await conn.fetchval(
                    """
                    INSERT INTO deposits (user_id, address, amount, token, tx_hash, chain, status, confirmed_at)
                    VALUES ($1, $2, $3, $4, $5, $6, 'confirmed', $7)
                    RETURNING id
                    """,
                    user_id, dep_addr, amount_str, token, tx_hash, chain, now,
                )
                # credit internal balance
                await conn.execute(
                    f"""
                    UPDATE wallets
                    SET {balance_col} = (CAST({balance_col} AS NUMERIC) + $1)::TEXT
                    WHERE user_id = $2
                    """,
                    amount, user_id,
                )
                # record transaction
                await conn.execute(
                    """
                    INSERT INTO transactions (from_user_id, to_user_id, amount, token, type, tx_hash, chain, status)
                    VALUES (NULL, $1, $2, $3, 'deposit', $4, $5, 'completed')
                    """,
                    user_id, amount_str, token, tx_hash, chain,
                )

        return {
            "deposit_id": deposit_id,
            "user_id": user_id,
            "amount": amount_str,
            "token": token,
            "chain": chain,
            "status": "confirmed",
        }

    async def _verify_bsc_tx(self, user_id: int, tx_hash: str) -> tuple[Decimal, str]:
        """Check a BSC tx receipt for SLH token transfer or BNB transfer."""
        try:
            receipt = await self._w3.eth.get_transaction_receipt(tx_hash)
            tx = await self._w3.eth.get_transaction(tx_hash)
        except Exception as exc:
            logger.error("BSC tx fetch failed for %s: %s", tx_hash, exc)
            return Decimal("0"), "SLH"

        user_addr = _deterministic_address(user_id).lower()

        # Check for SLH token Transfer event
        transfer_topic = Web3.keccak(text="Transfer(address,address,uint256)")
        for log_entry in receipt.get("logs", []):
            if (
                log_entry["address"].lower() == SLH_TOKEN_ADDRESS.lower()
                and len(log_entry["topics"]) == 3
                and log_entry["topics"][0] == transfer_topic
            ):
                to_addr = "0x" + log_entry["topics"][2].hex()[-40:]
                if to_addr.lower() == user_addr:
                    raw_amount = int(log_entry["data"].hex(), 16)
                    return Decimal(raw_amount) / Decimal(10**SLH_DECIMALS), "SLH"

        # Check plain BNB transfer
        if tx.get("to") and tx["to"].lower() == user_addr:
            return Decimal(Web3.from_wei(tx["value"], "ether")), "BNB"

        return Decimal("0"), "SLH"

    async def _verify_ton_tx(self, user_id: int, tx_hash: str) -> tuple[Decimal, str]:
        """Verify a TON deposit using toncenter API."""
        try:
            resp = await self._http.get(
                f"{TON_API_BASE}/getTransactions",
                params={"address": TON_WALLET, "limit": 50, "api_key": TON_API_KEY},
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                return Decimal("0"), "TON"

            for tx_item in data.get("result", []):
                tid = tx_item.get("transaction_id", {})
                if tid.get("hash") == tx_hash:
                    in_msg = tx_item.get("in_msg", {})
                    msg_body = in_msg.get("message", "")
                    # memo must match user_id
                    if str(user_id) in msg_body:
                        nano = int(in_msg.get("value", 0))
                        return Decimal(nano) / Decimal(10**9), "TON"
        except Exception as exc:
            logger.error("TON tx verification failed: %s", exc)
        return Decimal("0"), "TON"

    # ------------------------------------------------------------------
    # Internal transfer (instant, no gas)
    # ------------------------------------------------------------------

    async def internal_transfer(
        self,
        from_user_id: int,
        to_user_id: int,
        amount: str,
        token: str = "SLH",
    ) -> Dict[str, Any]:
        """Move tokens between two users' internal wallets."""
        token = token.upper()
        balance_col = f"{token.lower()}_balance"
        if balance_col not in ("slh_balance", "bnb_balance", "ton_balance", "zvk_balance"):
            return {"error": f"Unsupported token: {token}"}

        amt = Decimal(amount)
        if amt <= 0:
            return {"error": "Amount must be positive"}

        await self._ensure_wallet(from_user_id)
        await self._ensure_wallet(to_user_id)

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                sender = await conn.fetchrow(
                    "SELECT * FROM wallets WHERE user_id = $1 FOR UPDATE",
                    from_user_id,
                )
                if sender is None:
                    return {"error": "Sender wallet not found"}

                current = Decimal(sender[balance_col])
                if current < amt:
                    return {
                        "error": "Insufficient balance",
                        "available": str(current),
                        "requested": amount,
                    }

                # debit sender
                await conn.execute(
                    f"""
                    UPDATE wallets
                    SET {balance_col} = (CAST({balance_col} AS NUMERIC) - $1)::TEXT
                    WHERE user_id = $2
                    """,
                    amt, from_user_id,
                )
                # credit receiver
                await conn.execute(
                    f"""
                    UPDATE wallets
                    SET {balance_col} = (CAST({balance_col} AS NUMERIC) + $1)::TEXT
                    WHERE user_id = $2
                    """,
                    amt, to_user_id,
                )
                # record transaction
                tx_id = await conn.fetchval(
                    """
                    INSERT INTO transactions (from_user_id, to_user_id, amount, token, type, status)
                    VALUES ($1, $2, $3, $4, 'transfer', 'completed')
                    RETURNING id
                    """,
                    from_user_id, to_user_id, amount, token,
                )

        return {
            "tx_id": tx_id,
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "amount": amount,
            "token": token,
            "status": "completed",
        }

    # ------------------------------------------------------------------
    # Portfolio & history
    # ------------------------------------------------------------------

    async def get_user_portfolio(self, user_id: int) -> Dict[str, Any]:
        """Return all internal balances for a user."""
        await self._ensure_wallet(user_id)
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM wallets WHERE user_id = $1", user_id
            )

        if row is None:
            return {"error": "Wallet not found"}

        prices = await self.get_live_prices()
        slh_bal = Decimal(row["slh_balance"])
        bnb_bal = Decimal(row["bnb_balance"])
        ton_bal = Decimal(row["ton_balance"])
        zvk_bal = Decimal(row["zvk_balance"])

        slh_usd = float(slh_bal) * prices.get("slh_usd", 0)
        bnb_usd = float(bnb_bal) * prices.get("bnb_usd", 0)
        ton_usd = float(ton_bal) * prices.get("ton_usd", 0)
        total_usd = slh_usd + bnb_usd + ton_usd

        return {
            "user_id": user_id,
            "bsc_address": row["bsc_address"],
            "ton_address": row["ton_address"],
            "balances": {
                "SLH": str(slh_bal),
                "BNB": str(bnb_bal),
                "TON": str(ton_bal),
                "ZVK": str(zvk_bal),
            },
            "usd_values": {
                "SLH": round(slh_usd, 2),
                "BNB": round(bnb_usd, 2),
                "TON": round(ton_usd, 2),
                "total": round(total_usd, 2),
            },
            "prices": prices,
        }

    async def get_transaction_history(
        self, user_id: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Return the most recent transactions involving a user."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, from_user_id, to_user_id, amount, token,
                       type, tx_hash, chain, status, created_at
                FROM transactions
                WHERE from_user_id = $1 OR to_user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                user_id, limit,
            )
        result = []
        for r in rows:
            result.append({
                "id": r["id"],
                "from_user_id": r["from_user_id"],
                "to_user_id": r["to_user_id"],
                "amount": r["amount"],
                "token": r["token"],
                "type": r["type"],
                "tx_hash": r["tx_hash"],
                "chain": r["chain"],
                "status": r["status"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            })
        return result

    # ------------------------------------------------------------------
    # Live prices
    # ------------------------------------------------------------------

    async def get_live_prices(self) -> Dict[str, Any]:
        """
        Fetch BTC, ETH, TON, BNB prices from CoinGecko (cached in Redis
        for 60 s) and include the fixed SLH price.
        """
        cache_key = "slh:prices"

        # try cache first
        if self._redis:
            try:
                cached = await self._redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        prices: Dict[str, Any] = {
            "slh_ils": float(SLH_PRICE_ILS),
            "slh_usd": 0.0,
            "btc_usd": 0.0,
            "eth_usd": 0.0,
            "ton_usd": 0.0,
            "bnb_usd": 0.0,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            resp = await self._http.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": COINGECKO_IDS,
                    "vs_currencies": "usd,ils",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            usd_ils = data.get("bitcoin", {}).get("ils", 0) / max(
                data.get("bitcoin", {}).get("usd", 1), 1
            )

            prices["btc_usd"] = data.get("bitcoin", {}).get("usd", 0)
            prices["eth_usd"] = data.get("ethereum", {}).get("usd", 0)
            prices["ton_usd"] = data.get("toncoin", {}).get("usd", 0)
            prices["bnb_usd"] = data.get("binancecoin", {}).get("usd", 0)

            # SLH price in USD derived from the fixed ILS rate
            if usd_ils > 0:
                prices["slh_usd"] = round(float(SLH_PRICE_ILS) / usd_ils, 4)
            prices["usd_ils_rate"] = round(usd_ils, 4)

        except Exception as exc:
            logger.warning("CoinGecko price fetch failed: %s", exc)

        # cache result
        if self._redis:
            try:
                await self._redis.set(
                    cache_key, json.dumps(prices), ex=PRICE_CACHE_TTL
                )
            except Exception:
                pass

        return prices
