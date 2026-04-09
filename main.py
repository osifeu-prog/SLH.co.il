"""
SLH Ecosystem API - FastAPI Backend
Deployed on Railway | Connected to PostgreSQL
"""
import os
import hmac
import hashlib
import time
import json
from datetime import datetime, timedelta
import jwt
import secrets
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Query, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncpg

from routes.ai_chat import router as ai_chat_router

# === CONFIG ===
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main")
BOT_TOKEN = os.getenv("EXPERTNET_BOT_TOKEN", "")
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "12"))
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "224223270"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://slh-nft.com,http://localhost:8899,http://localhost:3000").split(",")

# Wallet constants (used early by registration endpoints)
SLH_BSC_CONTRACT = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"
SLH_TON_WALLET = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
SLH_PRICE_ILS = 444
USD_ILS_RATE = 3.65

app = FastAPI(
    title="SLH Ecosystem API",
    description="Backend API for SLH Digital Investment House",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === AI CHAT ROUTER ===
app.include_router(ai_chat_router)

# === DATABASE ===
pool: Optional[asyncpg.Pool] = None

@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS web_users (
                telegram_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                photo_url TEXT,
                auth_date BIGINT,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_registered BOOLEAN DEFAULT FALSE,
                registered_at TIMESTAMP,
                eth_wallet VARCHAR(42),
                eth_wallet_linked_at TIMESTAMP,
                ton_wallet VARCHAR(68),
                ton_wallet_linked_at TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS staking_positions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                plan TEXT NOT NULL,
                amount NUMERIC(18,8) NOT NULL,
                currency TEXT DEFAULT 'TON',
                apy_monthly NUMERIC(5,2) NOT NULL,
                lock_days INT NOT NULL,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'active',
                earned NUMERIC(18,8) DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES web_users(telegram_id)
            );
            CREATE TABLE IF NOT EXISTS referrals (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL UNIQUE,
                referrer_id BIGINT,
                depth INT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES web_users(telegram_id)
            );
            CREATE TABLE IF NOT EXISTS referral_earnings (
                id BIGSERIAL PRIMARY KEY,
                earner_id BIGINT NOT NULL,
                from_user_id BIGINT NOT NULL,
                generation INT NOT NULL,
                source_type TEXT NOT NULL,
                source_amount NUMERIC(18,8) NOT NULL,
                commission_rate NUMERIC(5,4) NOT NULL,
                commission_amount NUMERIC(18,8) NOT NULL,
                token TEXT DEFAULT 'TON',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
            CREATE INDEX IF NOT EXISTS idx_referral_earnings_earner ON referral_earnings(earner_id);

            CREATE TABLE IF NOT EXISTS token_balances (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                token TEXT NOT NULL DEFAULT 'SLH',
                balance NUMERIC(18,8) NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, token)
            );

            CREATE TABLE IF NOT EXISTS token_transfers (
                id BIGSERIAL PRIMARY KEY,
                from_user_id BIGINT,
                to_user_id BIGINT,
                token TEXT NOT NULL DEFAULT 'SLH',
                amount NUMERIC(18,8) NOT NULL,
                memo TEXT,
                tx_type TEXT DEFAULT 'transfer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS wallet_idempotency (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                request_id TEXT NOT NULL,
                tx_transfer_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, request_id)
            );

            CREATE INDEX IF NOT EXISTS idx_wallet_idempotency_user_created
            ON wallet_idempotency(user_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS deposits (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                amount NUMERIC(18,8) NOT NULL,
                currency TEXT DEFAULT 'SLH',
                tx_hash TEXT,
                status TEXT DEFAULT 'pending',
                plan_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS premium_users (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                bot_name TEXT NOT NULL,
                payment_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, bot_name)
            );

            CREATE TABLE IF NOT EXISTS daily_claims (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                amount NUMERIC(18,8) NOT NULL DEFAULT 0,
                streak INT NOT NULL DEFAULT 1,
                claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                xp_total NUMERIC(18,2) DEFAULT 0,
                balance NUMERIC(18,8) DEFAULT 0,
                level INT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS marketplace_items (
                id BIGSERIAL PRIMARY KEY,
                seller_id BIGINT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                price NUMERIC(18,8) NOT NULL,
                currency TEXT NOT NULL DEFAULT 'SLH',
                image_url TEXT,
                category TEXT DEFAULT 'general',
                stock INT DEFAULT 1,
                status TEXT DEFAULT 'pending',
                promotion TEXT DEFAULT 'none',
                promoted_until TIMESTAMP,
                views INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES web_users(telegram_id)
            );
            CREATE INDEX IF NOT EXISTS idx_marketplace_items_status ON marketplace_items(status);
            CREATE INDEX IF NOT EXISTS idx_marketplace_items_seller ON marketplace_items(seller_id);
            CREATE INDEX IF NOT EXISTS idx_marketplace_items_category ON marketplace_items(category);

            CREATE TABLE IF NOT EXISTS marketplace_orders (
                id BIGSERIAL PRIMARY KEY,
                buyer_id BIGINT NOT NULL,
                seller_id BIGINT NOT NULL,
                item_id BIGINT NOT NULL,
                quantity INT NOT NULL DEFAULT 1,
                total_price NUMERIC(18,8) NOT NULL,
                currency TEXT NOT NULL DEFAULT 'SLH',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (buyer_id) REFERENCES web_users(telegram_id),
                FOREIGN KEY (item_id) REFERENCES marketplace_items(id)
            );
            CREATE INDEX IF NOT EXISTS idx_marketplace_orders_buyer ON marketplace_orders(buyer_id);
            CREATE INDEX IF NOT EXISTS idx_marketplace_orders_seller ON marketplace_orders(seller_id);
            CREATE INDEX IF NOT EXISTS idx_marketplace_orders_item ON marketplace_orders(item_id);
        """)

        # --- Migration: add is_registered columns to existing DBs ---
        try:
            await conn.execute("ALTER TABLE web_users ADD COLUMN IF NOT EXISTS is_registered BOOLEAN DEFAULT FALSE")
            await conn.execute("ALTER TABLE web_users ADD COLUMN IF NOT EXISTS registered_at TIMESTAMP")
        except Exception:
            pass  # columns already exist in CREATE TABLE

        # --- Migration: add Web3 wallet columns to existing DBs ---
        try:
            await conn.execute("ALTER TABLE web_users ADD COLUMN IF NOT EXISTS eth_wallet VARCHAR(42)")
            await conn.execute("ALTER TABLE web_users ADD COLUMN IF NOT EXISTS eth_wallet_linked_at TIMESTAMP")
            await conn.execute("ALTER TABLE web_users ADD COLUMN IF NOT EXISTS ton_wallet VARCHAR(68)")
            await conn.execute("ALTER TABLE web_users ADD COLUMN IF NOT EXISTS ton_wallet_linked_at TIMESTAMP")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_web_users_eth_wallet ON web_users(eth_wallet)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_web_users_ton_wallet ON web_users(ton_wallet)")
        except Exception as e:
            print(f"[Migration] Web3 wallet columns: {e}")

        # --- Migration: ensure marketplace tables exist on already-running DBs ---
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS marketplace_items (
                    id BIGSERIAL PRIMARY KEY,
                    seller_id BIGINT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    price NUMERIC(18,8) NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'SLH',
                    image_url TEXT,
                    category TEXT DEFAULT 'general',
                    stock INT DEFAULT 1,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_at TIMESTAMP
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS marketplace_orders (
                    id BIGSERIAL PRIMARY KEY,
                    buyer_id BIGINT NOT NULL,
                    seller_id BIGINT NOT NULL,
                    item_id BIGINT NOT NULL,
                    quantity INT NOT NULL DEFAULT 1,
                    total_price NUMERIC(18,8) NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'SLH',
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_marketplace_items_status ON marketplace_items(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_marketplace_items_seller ON marketplace_items(seller_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_marketplace_items_category ON marketplace_items(category)")
            # Migration: add promotion/views columns to existing marketplace_items
            await conn.execute("ALTER TABLE marketplace_items ADD COLUMN IF NOT EXISTS promotion TEXT DEFAULT 'none'")
            await conn.execute("ALTER TABLE marketplace_items ADD COLUMN IF NOT EXISTS promoted_until TIMESTAMP")
            await conn.execute("ALTER TABLE marketplace_items ADD COLUMN IF NOT EXISTS views INT DEFAULT 0")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_marketplace_orders_buyer ON marketplace_orders(buyer_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_marketplace_orders_seller ON marketplace_orders(seller_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_marketplace_orders_item ON marketplace_orders(item_id)")
        except Exception as e:
            print(f"[Migration] Marketplace tables: {e}")

        # --- Auto-register admin + existing premium users ---
        # Ensure admin row exists with sane defaults (first-run bootstrap)
        admin_username = os.getenv("ADMIN_USERNAME", "osifeu_prog")
        admin_first_name = os.getenv("ADMIN_FIRST_NAME", "Osif")
        await conn.execute("""
            INSERT INTO web_users (telegram_id, username, first_name, auth_date, last_login, is_registered, registered_at)
            VALUES ($1, $2, $3, EXTRACT(EPOCH FROM NOW())::BIGINT, CURRENT_TIMESTAMP, TRUE, CURRENT_TIMESTAMP)
            ON CONFLICT (telegram_id) DO UPDATE SET
                username = EXCLUDED.username,
                first_name = CASE
                    WHEN web_users.first_name IN ('', 'User') THEN EXCLUDED.first_name
                    ELSE web_users.first_name
                END,
                is_registered = TRUE,
                registered_at = COALESCE(web_users.registered_at, CURRENT_TIMESTAMP)
        """, ADMIN_USER_ID, admin_username, admin_first_name)

        await conn.execute("""
            UPDATE web_users SET is_registered = TRUE, registered_at = COALESCE(registered_at, CURRENT_TIMESTAMP)
            WHERE is_registered = FALSE AND telegram_id IN (
                SELECT DISTINCT user_id FROM premium_users WHERE payment_status = 'approved'
            )
        """)


@app.on_event("shutdown")
async def shutdown():
    if pool:
        await pool.close()


# === TELEGRAM AUTH ===
def verify_telegram_auth(data: dict) -> bool:
    """Verify Telegram Login Widget data"""
    if not BOT_TOKEN:
        return False
    check_hash = data.pop("hash", "")
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hashlib.sha256(BOT_TOKEN.encode()).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if expected != check_hash:
        return False
    if time.time() - int(data.get("auth_date", 0)) > 86400:
        return False
    return True


class TelegramAuth(BaseModel):
    id: int
    first_name: str
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


def create_jwt(user_id: int, username: Optional[str] = None) -> str:
    if not JWT_SECRET:
        raise HTTPException(500, "JWT_SECRET is not configured")
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "username": username or "",
        "iat": now,
        "exp": now + (JWT_EXPIRES_HOURS * 3600),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()

    if not JWT_SECRET:
        raise HTTPException(500, "JWT_SECRET is not configured")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

    sub = payload.get("sub")
    if not sub or not str(sub).isdigit():
        raise HTTPException(401, "Invalid token payload")

    return int(sub)


_wallet_send_rate = {}


def _check_wallet_send_rate(user_id: int, cooldown_seconds: int = 5) -> bool:
    now = time.time()
    last = _wallet_send_rate.get(user_id, 0)
    if now - last < cooldown_seconds:
        return False
    _wallet_send_rate[user_id] = now
    return True


# === AUTH ENDPOINTS ===
@app.post("/api/auth/telegram")
async def auth_telegram(auth: TelegramAuth):
    """Authenticate user via Telegram Login Widget"""
    auth_dict = auth.dict()
    if not verify_telegram_auth(auth_dict.copy()):
        raise HTTPException(401, "Invalid Telegram authentication")

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO web_users (telegram_id, username, first_name, photo_url, auth_date, last_login)
            VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
            ON CONFLICT (telegram_id) DO UPDATE SET
                username = $2, first_name = $3, photo_url = $4, last_login = CURRENT_TIMESTAMP
        """, auth.id, auth.username, auth.first_name, auth.photo_url, auth.auth_date)

        # Fetch user balances and registration status
        balances = await get_user_balances(conn, auth.id)
        premium = await conn.fetchval(
            "SELECT payment_status FROM premium_users WHERE user_id=$1 AND bot_name='expertnet'", auth.id
        )
        is_registered = await conn.fetchval(
            "SELECT is_registered FROM web_users WHERE telegram_id=$1", auth.id
        ) or False

    jwt_token = create_jwt(auth.id, auth.username)

    return {
        "status": "ok",
        "token": jwt_token,
        "user": {
            "id": auth.id,
            "username": auth.username,
            "first_name": auth.first_name,
            "photo_url": auth.photo_url,
            "premium": premium == "approved",
            "is_registered": is_registered,
        },
        "balances": balances,
    }


# === REGISTRATION SYSTEM ===

REGISTRATION_PRICE_ILS = 22.221  # unified price across bot + website + mini-app
REGISTRATION_SLH_AMOUNT = 0.05    # SLH bonus credited on approval (scaled down from 0.1)


class RegistrationInitRequest(BaseModel):
    referrer_id: Optional[int] = None


class RegistrationProofRequest(BaseModel):
    tx_hash: str = ""
    note: str = ""


class RegistrationApproveRequest(BaseModel):
    user_id: int
    admin_key: str = ""


@app.post("/api/registration/initiate")
async def registration_initiate(req: RegistrationInitRequest, authorization: Optional[str] = Header(None)):
    """Start registration — create pending payment record."""
    user_id = get_current_user_id(authorization)

    async with pool.acquire() as conn:
        # Check if already registered
        is_reg = await conn.fetchval("SELECT is_registered FROM web_users WHERE telegram_id=$1", user_id)
        if is_reg:
            return {"status": "already_registered"}

        # Check if pending payment exists
        existing = await conn.fetchrow(
            "SELECT id, payment_status FROM premium_users WHERE user_id=$1 AND bot_name='ecosystem'", user_id
        )
        if existing and existing["payment_status"] in ("submitted", "approved"):
            return {"status": existing["payment_status"], "message": "Payment already " + existing["payment_status"]}

        # Create or update pending registration
        await conn.execute("""
            INSERT INTO premium_users (user_id, bot_name, payment_status)
            VALUES ($1, 'ecosystem', 'pending')
            ON CONFLICT (user_id, bot_name) DO UPDATE SET payment_status = 'pending'
        """, user_id)

        # Register referral if provided
        if req.referrer_id and req.referrer_id != user_id:
            existing_ref = await conn.fetchrow("SELECT id FROM referrals WHERE user_id=$1", user_id)
            if not existing_ref:
                # Ensure referrer exists in web_users
                ref_exists = await conn.fetchval("SELECT 1 FROM web_users WHERE telegram_id=$1", req.referrer_id)
                if ref_exists:
                    ref_depth = await conn.fetchval("SELECT depth FROM referrals WHERE user_id=$1", req.referrer_id)
                    depth = (ref_depth or 0) + 1
                    try:
                        await conn.execute("""
                            INSERT INTO referrals (user_id, referrer_id, depth) VALUES ($1, $2, $3)
                        """, user_id, req.referrer_id, depth)
                    except Exception:
                        pass  # referral already registered

    return {
        "status": "pending",
        "price_ils": REGISTRATION_PRICE_ILS,
        "slh_amount": REGISTRATION_SLH_AMOUNT,
        "ton_wallet": SLH_TON_WALLET,
        "bsc_contract": SLH_BSC_CONTRACT,
        "message": f"Send {REGISTRATION_PRICE_ILS} ILS worth of TON to the wallet address"
    }


@app.post("/api/registration/submit-proof")
async def registration_submit_proof(req: RegistrationProofRequest, authorization: Optional[str] = Header(None)):
    """User submits payment proof (tx_hash or note)."""
    user_id = get_current_user_id(authorization)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, payment_status FROM premium_users WHERE user_id=$1 AND bot_name='ecosystem'", user_id
        )
        if not row:
            raise HTTPException(400, "No pending registration found. Call /api/registration/initiate first.")
        if row["payment_status"] == "approved":
            return {"status": "already_approved"}

        await conn.execute("""
            UPDATE premium_users SET payment_status = 'submitted'
            WHERE user_id = $1 AND bot_name = 'ecosystem'
        """, user_id)

        # Store proof in deposits table
        if req.tx_hash.strip():
            await conn.execute("""
                INSERT INTO deposits (user_id, amount, currency, tx_hash, status, plan_key)
                VALUES ($1, $2, 'ILS', $3, 'pending', 'registration')
            """, user_id, REGISTRATION_PRICE_ILS, req.tx_hash.strip())

    print(f"[Registration] User {user_id} submitted payment proof: {req.tx_hash or req.note}")
    return {"status": "submitted", "message": "Payment proof received. Waiting for admin approval."}


@app.post("/api/registration/approve")
async def registration_approve(req: RegistrationApproveRequest):
    """Admin approves a registration payment. Credits 0.1 SLH + triggers referral commissions."""
    # Admin verification: check admin_key or accept from known admin
    admin_secret = os.getenv("ADMIN_API_KEY", "slh_admin_2026")
    if req.admin_key != admin_secret:
        raise HTTPException(403, "Invalid admin key")

    async with pool.acquire() as conn:
        # Verify pending registration exists
        row = await conn.fetchrow(
            "SELECT id, payment_status FROM premium_users WHERE user_id=$1 AND bot_name='ecosystem'", req.user_id
        )
        if not row:
            raise HTTPException(404, "No registration record found for this user")
        if row["payment_status"] == "approved":
            return {"status": "already_approved"}

        async with conn.transaction():
            # 1. Mark registration as approved
            await conn.execute("""
                UPDATE premium_users SET payment_status = 'approved'
                WHERE user_id = $1 AND bot_name = 'ecosystem'
            """, req.user_id)

            # 2. Set user as registered
            await conn.execute("""
                UPDATE web_users SET is_registered = TRUE, registered_at = CURRENT_TIMESTAMP
                WHERE telegram_id = $1
            """, req.user_id)

            # 3. Credit 0.1 SLH token
            await conn.execute("""
                INSERT INTO token_balances (user_id, token, balance)
                VALUES ($1, 'SLH', $2)
                ON CONFLICT (user_id, token) DO UPDATE SET balance = token_balances.balance + $2, updated_at = CURRENT_TIMESTAMP
            """, req.user_id, REGISTRATION_SLH_AMOUNT)

            # 4. Record token transfer
            await conn.execute("""
                INSERT INTO token_transfers (from_user_id, to_user_id, token, amount, memo, tx_type)
                VALUES ($1, $1, 'SLH', $2, 'Ecosystem registration bonus', 'registration')
            """, req.user_id, REGISTRATION_SLH_AMOUNT)

            # 5. Update deposit status if exists
            await conn.execute("""
                UPDATE deposits SET status = 'confirmed'
                WHERE user_id = $1 AND plan_key = 'registration' AND status = 'pending'
            """, req.user_id)

            # 6. Distribute referral commissions
            commissions = await distribute_referral_commissions(
                conn, req.user_id, REGISTRATION_PRICE_ILS, 'registration', 'ILS'
            )

    print(f"[Registration] User {req.user_id} APPROVED. 0.1 SLH credited. {len(commissions)} referral commissions distributed.")
    return {
        "status": "approved",
        "user_id": req.user_id,
        "slh_credited": REGISTRATION_SLH_AMOUNT,
        "referral_commissions": commissions
    }


@app.get("/api/registration/status/{user_id}")
async def registration_status(user_id: int):
    """Check registration status for a user."""
    async with pool.acquire() as conn:
        is_reg = await conn.fetchval("SELECT is_registered FROM web_users WHERE telegram_id=$1", user_id)
        if is_reg:
            return {"is_registered": True, "payment_status": "approved"}

        row = await conn.fetchrow(
            "SELECT payment_status FROM premium_users WHERE user_id=$1 AND bot_name='ecosystem'", user_id
        )
        if row:
            return {"is_registered": False, "payment_status": row["payment_status"]}

    return {"is_registered": False, "payment_status": "none"}


# === PENDING REGISTRATIONS (admin) ===

@app.get("/api/registration/pending")
async def registration_pending():
    """List all pending/submitted registrations for admin review."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT p.user_id, w.username, w.first_name, p.payment_status, p.created_at,
                   d.tx_hash, d.amount as deposit_amount
            FROM premium_users p
            LEFT JOIN web_users w ON w.telegram_id = p.user_id
            LEFT JOIN deposits d ON d.user_id = p.user_id AND d.plan_key = 'registration'
            WHERE p.bot_name = 'ecosystem' AND p.payment_status IN ('pending', 'submitted')
            ORDER BY p.created_at DESC
        """)
    return [dict(r) for r in rows]


# === WEB3 WALLET LINKING ===

class LinkWalletRequest(BaseModel):
    user_id: int
    address: Optional[str] = ""
    signature: Optional[str] = None   # optional personal_sign proof
    message: Optional[str] = None     # the message that was signed


@app.post("/api/user/link-wallet")
async def link_wallet(req: LinkWalletRequest):
    """Link a Web3 (BSC/ETH) wallet address to a web_users row.

    Validates the address format (0x + 40 hex chars) and stores it lowercase.
    Signature verification is optional — if present, we verify personal_sign.
    """
    addr = (req.address or "").strip().lower()
    if not addr.startswith("0x") or len(addr) != 42:
        raise HTTPException(400, "Invalid Ethereum address format")
    try:
        int(addr[2:], 16)  # ensure hex
    except ValueError:
        raise HTTPException(400, "Invalid Ethereum address — not hex")

    if not req.user_id:
        raise HTTPException(400, "user_id required")

    async with pool.acquire() as conn:
        # Ensure user exists
        exists = await conn.fetchval("SELECT 1 FROM web_users WHERE telegram_id=$1", req.user_id)
        if not exists:
            raise HTTPException(404, "User not found — please login first")

        # Check for collision: this wallet already linked to a different user
        other = await conn.fetchval(
            "SELECT telegram_id FROM web_users WHERE eth_wallet=$1 AND telegram_id<>$2",
            addr, req.user_id
        )
        if other:
            raise HTTPException(409, "This wallet is already linked to another account")

        await conn.execute("""
            UPDATE web_users
               SET eth_wallet = $1,
                   eth_wallet_linked_at = CURRENT_TIMESTAMP
             WHERE telegram_id = $2
        """, addr, req.user_id)

    print(f"[Web3] Linked wallet {addr} to user {req.user_id}")
    return {"ok": True, "address": addr, "user_id": req.user_id}


@app.get("/api/user/wallet/{user_id}")
async def get_linked_wallet(user_id: int):
    """Return the linked Web3 wallet address (if any) for a user."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT eth_wallet, eth_wallet_linked_at FROM web_users WHERE telegram_id=$1",
            user_id
        )
    if not row:
        raise HTTPException(404, "User not found")
    return {
        "user_id": user_id,
        "address": row["eth_wallet"],
        "linked_at": row["eth_wallet_linked_at"].isoformat() if row["eth_wallet_linked_at"] else None
    }


@app.post("/api/user/unlink-wallet")
async def unlink_wallet(req: LinkWalletRequest):
    """Remove the linked Web3 wallet from a user row."""
    if not req.user_id:
        raise HTTPException(400, "user_id required")
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE web_users
               SET eth_wallet = NULL, eth_wallet_linked_at = NULL
             WHERE telegram_id = $1
        """, req.user_id)
    return {"ok": True, "user_id": req.user_id}


async def get_user_balances(conn, user_id: int):
    """Get all token balances for a user"""
    balances = {"TON_available": 0.0, "TON_locked": 0.0}

    try:
        rows = await conn.fetch(
            "SELECT token, balance FROM token_balances WHERE user_id=$1", user_id
        )
        for row in rows:
            balances[row["token"]] = float(row["balance"])
    except Exception:
        pass

    try:
        bank = await conn.fetchrow(
            "SELECT COALESCE(available,0) as available, COALESCE(locked,0) as locked_amt "
            "FROM account_balances WHERE account_id=$1", user_id
        )
        if bank:
            balances["TON_available"] = float(bank["available"])
            balances["TON_locked"] = float(bank["locked_amt"])
    except Exception:
        pass

    # Fallback: check user_balances table
    try:
        ub = await conn.fetchrow(
            "SELECT COALESCE(balance,0) as bal FROM user_balances WHERE user_id=$1", user_id
        )
        if ub and float(ub["bal"]) > 0 and balances["TON_available"] == 0:
            balances["TON_available"] = float(ub["bal"])
    except Exception:
        pass

    return balances


# === USER PROFILE ===
@app.get("/api/user/{telegram_id}")
async def get_user(telegram_id: int):
    """Get user profile and balances"""
    async with pool.acquire() as conn:
        # Try web_users first, fallback to users table
        user = None
        try:
            user = await conn.fetchrow(
                """SELECT telegram_id, username, first_name, photo_url, auth_date, last_login,
                          is_registered, registered_at, eth_wallet, eth_wallet_linked_at,
                          ton_wallet, ton_wallet_linked_at
                     FROM web_users WHERE telegram_id=$1""",
                telegram_id
            )
        except Exception:
            pass

        if not user:
            try:
                row = await conn.fetchrow(
                    "SELECT user_id, username, balance, xp_total, level, joined_at, daily_streak FROM users WHERE user_id=$1", telegram_id
                )
                if row:
                    user = {
                        "telegram_id": row["user_id"],
                        "username": row["username"],
                        "first_name": row["username"] or "User",
                        "photo_url": None,
                        "xp_total": row["xp_total"],
                        "level": row["level"],
                        "daily_streak": row["daily_streak"],
                        "joined_at": str(row["joined_at"]) if row["joined_at"] else None,
                    }
            except Exception:
                pass

        if not user:
            raise HTTPException(404, "User not found")

        balances = await get_user_balances(conn, telegram_id)

        # Deposits - safe query
        deposits = []
        try:
            deposits = await conn.fetch(
                "SELECT id, plan_key, amount, currency, status, start_date, end_date, total_earned, created_at "
                "FROM deposits WHERE user_id=$1 ORDER BY created_at DESC LIMIT 10", telegram_id
            )
        except Exception:
            pass

        # Premium status - safe query
        premium = None
        try:
            premium = await conn.fetchval(
                "SELECT payment_status FROM premium_users WHERE user_id=$1 AND bot_name='expertnet'", telegram_id
            )
        except Exception:
            pass

        # Staking positions
        staking = []
        try:
            staking = await conn.fetch(
                "SELECT * FROM staking_positions WHERE user_id=$1 AND status='active' ORDER BY start_date DESC", telegram_id
            )
        except Exception:
            pass

    return {
        "user": dict(user) if hasattr(user, 'keys') else user,
        "balances": balances,
        "premium": premium == "approved",
        "deposits": [dict(d) for d in deposits] if deposits else [],
        "staking": [dict(s) for s in staking] if staking else [],
    }


# === STAKING ===
STAKING_PLANS = {
    "monthly": {"name": "Monthly", "apy_monthly": 4.0, "apy_annual": 48, "min_ton": 1, "lock_days": 30},
    "quarterly": {"name": "Quarterly", "apy_monthly": 4.5, "apy_annual": 55, "min_ton": 5, "lock_days": 90},
    "semi_annual": {"name": "Semi-Annual", "apy_monthly": 5.0, "apy_annual": 60, "min_ton": 10, "lock_days": 180},
    "annual": {"name": "Annual", "apy_monthly": 5.4, "apy_annual": 65, "min_ton": 25, "lock_days": 365},
}


@app.get("/api/staking/plans")
async def get_staking_plans():
    """Get available staking plans"""
    return {"plans": STAKING_PLANS}


class StakeRequest(BaseModel):
    user_id: int
    plan: str
    amount: float


@app.post("/api/staking/stake")
async def create_stake(req: StakeRequest):
    """Create a new staking position"""
    plan = STAKING_PLANS.get(req.plan)
    if not plan:
        raise HTTPException(400, f"Invalid plan. Choose from: {list(STAKING_PLANS.keys())}")
    if req.amount < plan["min_ton"]:
        raise HTTPException(400, f"Minimum deposit is {plan['min_ton']} TON")

    end_date = datetime.utcnow() + timedelta(days=plan["lock_days"])

    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM web_users WHERE telegram_id=$1", req.user_id)
        if not user:
            raise HTTPException(404, "User not found. Login first.")

        pos_id = await conn.fetchval("""
            INSERT INTO staking_positions (user_id, plan, amount, apy_monthly, lock_days, end_date)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
        """, req.user_id, req.plan, req.amount, plan["apy_monthly"], plan["lock_days"], end_date)

        # Distribute referral commissions automatically
        commissions = await distribute_referral_commissions(
            conn, req.user_id, float(req.amount), f"staking_{req.plan}", "TON"
        )

    return {
        "id": pos_id,
        "plan": req.plan,
        "amount": req.amount,
        "apy_monthly": plan["apy_monthly"],
        "lock_days": plan["lock_days"],
        "end_date": end_date.isoformat(),
        "status": "active",
        "referral_commissions": commissions,
    }


@app.get("/api/staking/positions/{user_id}")
async def get_staking_positions(user_id: int):
    """Get user's staking positions"""
    async with pool.acquire() as conn:
        positions = await conn.fetch(
            "SELECT * FROM staking_positions WHERE user_id=$1 ORDER BY start_date DESC", user_id
        )
    return {"positions": [dict(p) for p in positions]}


# === PRICES (with cache + timeout + retry) ===
_price_cache = {"data": None, "ts": 0}

@app.get("/api/prices")
async def get_prices():
    """Proxy for CoinGecko prices — cached 60s, 10s timeout, 2 retries"""
    import aiohttp, time as _time
    now = _time.time()
    # Return cached data if fresh (< 60s)
    if _price_cache["data"] and (now - _price_cache["ts"]) < 60:
        return _price_cache["data"]

    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,the-open-network,binancecoin,solana,ripple,dogecoin&vs_currencies=usd,ils"
    timeout = aiohttp.ClientTimeout(total=10)
    for attempt in range(2):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        _price_cache["data"] = data
                        _price_cache["ts"] = now
                        return data
        except Exception:
            if attempt == 1:
                break
    # Return stale cache if available, else 502
    if _price_cache["data"]:
        return _price_cache["data"]
    raise HTTPException(502, "Price API unavailable")


# === ECOSYSTEM STATS ===
@app.get("/api/stats")
async def get_stats():
    """Get ecosystem-wide statistics"""
    async def safe_count(conn, query):
        try:
            return await conn.fetchval(query) or 0
        except Exception:
            return 0

    async with pool.acquire() as conn:
        total_users = await safe_count(conn, "SELECT COUNT(*) FROM web_users")
        premium_users = await safe_count(conn, "SELECT COUNT(*) FROM premium_users WHERE payment_status='approved'")
        total_staked = await safe_count(conn, "SELECT COALESCE(SUM(amount),0) FROM staking_positions WHERE status='active'")
        total_deposits = await safe_count(conn, "SELECT COALESCE(SUM(amount),0) FROM deposits WHERE status='active'")

    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "total_staked_ton": float(total_staked),
        "total_deposits_ton": float(total_deposits),
        "bots_live": 20,
        "supported_coins": 12,
    }


# === HEALTH ===
@app.get("/api/health")
async def health():
    """Health check"""
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok", "db": "connected", "version": "1.0.0"}
    except Exception as e:
        return JSONResponse({"status": "error", "db": str(e)}, status_code=503)


# === TOKEN TRANSFERS ===
class TransferRequest(BaseModel):
    from_user_id: int
    to_user_id: int
    token: str
    amount: float
    memo: Optional[str] = None


@app.post("/api/transfer")
async def transfer_tokens(req: TransferRequest):
    """Transfer internal tokens between users"""
    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    if req.token not in ("SLH", "ZVK"):
        raise HTTPException(400, "Token must be SLH or ZVK")

    async with pool.acquire() as conn:
        async with conn.transaction():
            balance = await conn.fetchval(
                "SELECT balance FROM token_balances WHERE user_id=$1 AND token=$2",
                req.from_user_id, req.token
            )
            if not balance or float(balance) < req.amount:
                raise HTTPException(400, "Insufficient balance")

            await conn.execute(
                "UPDATE token_balances SET balance = balance - $1 WHERE user_id=$2 AND token=$3",
                req.amount, req.from_user_id, req.token
            )
            await conn.execute("""
                INSERT INTO token_balances (user_id, token, balance)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, token) DO UPDATE SET balance = token_balances.balance + $3
            """, req.to_user_id, req.token, req.amount)

            await conn.execute("""
                INSERT INTO token_transfers (from_user_id, to_user_id, token, amount, memo, tx_type)
                VALUES ($1, $2, $3, $4, $5, 'transfer')
            """, req.from_user_id, req.to_user_id, req.token, req.amount, req.memo or "web transfer")

    return {"status": "ok", "amount": req.amount, "token": req.token}


# === MULTI-GENERATION REFERRAL SYSTEM ===
# Commission rates by generation (up to 10 levels)
REFERRAL_RATES = {
    1: 0.10,   # 10% - direct referral
    2: 0.05,   # 5%
    3: 0.03,   # 3%
    4: 0.02,   # 2%
    5: 0.01,   # 1%
    6: 0.005,  # 0.5%
    7: 0.005,
    8: 0.005,
    9: 0.005,
    10: 0.005,
}
MAX_GENERATIONS = 10


async def get_referral_chain(conn, user_id: int) -> list[int]:
    """Walk up the referral chain and return list of ancestor IDs (generation 1 = direct referrer)"""
    chain = []
    current = user_id
    for _ in range(MAX_GENERATIONS):
        row = await conn.fetchrow("SELECT referrer_id FROM referrals WHERE user_id=$1", current)
        if not row or not row["referrer_id"]:
            break
        chain.append(row["referrer_id"])
        current = row["referrer_id"]
    return chain


async def distribute_referral_commissions(conn, from_user_id: int, amount: float, source_type: str, token: str = "TON"):
    """Distribute commissions up the referral chain"""
    chain = await get_referral_chain(conn, from_user_id)
    results = []
    for gen, earner_id in enumerate(chain, 1):
        rate = REFERRAL_RATES.get(gen, 0)
        if rate <= 0:
            break
        commission = round(amount * rate, 8)
        if commission <= 0:
            continue
        await conn.execute("""
            INSERT INTO referral_earnings (earner_id, from_user_id, generation, source_type, source_amount, commission_rate, commission_amount, token)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, earner_id, from_user_id, gen, source_type, amount, rate, commission, token)
        results.append({"earner_id": earner_id, "generation": gen, "rate": rate, "commission": commission})
    return results


@app.post("/api/referral/register")
async def register_referral(user_id: int = Query(...), referrer_id: int = Query(None)):
    """Register a user in the referral system"""
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM referrals WHERE user_id=$1", user_id)
        if existing:
            return {"status": "already_registered", "referrer_id": existing["referrer_id"]}

        # Auto-create user if not exists
        await conn.execute("""
            INSERT INTO web_users (telegram_id, first_name) VALUES ($1, 'User')
            ON CONFLICT (telegram_id) DO NOTHING
        """, user_id)
        if referrer_id:
            await conn.execute("""
                INSERT INTO web_users (telegram_id, first_name) VALUES ($1, 'User')
                ON CONFLICT (telegram_id) DO NOTHING
            """, referrer_id)

        # Prevent self-referral
        if referrer_id == user_id:
            referrer_id = None

        # Calculate depth
        depth = 1
        if referrer_id:
            parent = await conn.fetchrow("SELECT depth FROM referrals WHERE user_id=$1", referrer_id)
            if parent:
                depth = parent["depth"] + 1

        await conn.execute("""
            INSERT INTO referrals (user_id, referrer_id, depth)
            VALUES ($1, $2, $3) ON CONFLICT (user_id) DO NOTHING
        """, user_id, referrer_id, depth)

    return {"status": "ok", "user_id": user_id, "referrer_id": referrer_id, "depth": depth}


@app.get("/api/referral/tree/{user_id}")
async def get_referral_tree(user_id: int, max_depth: int = Query(5, le=10)):
    """Get the referral tree for a user (who they referred, and who those referred, etc.)"""
    async with pool.acquire() as conn:
        async def build_tree(uid: int, current_depth: int) -> dict:
            if current_depth > max_depth:
                return None
            children_rows = await conn.fetch(
                "SELECT r.user_id, w.username, w.first_name FROM referrals r LEFT JOIN web_users w ON r.user_id = w.telegram_id WHERE r.referrer_id=$1 ORDER BY r.created_at",
                uid
            )
            children = []
            for row in children_rows:
                child = {
                    "user_id": row["user_id"],
                    "username": row["username"] or "",
                    "first_name": row["first_name"] or "",
                    "generation": current_depth,
                }
                subtree = await build_tree(row["user_id"], current_depth + 1)
                child["children"] = subtree["children"] if subtree else []
                child["total_descendants"] = len(child["children"]) + sum(c.get("total_descendants", 0) for c in child["children"])
                children.append(child)
            return {"children": children}

        tree = await build_tree(user_id, 1)

        # Get earnings summary
        earnings = await conn.fetch("""
            SELECT generation, COUNT(*) as count, SUM(commission_amount) as total, token
            FROM referral_earnings WHERE earner_id=$1
            GROUP BY generation, token ORDER BY generation
        """, user_id)

        total_earned = await conn.fetchval(
            "SELECT COALESCE(SUM(commission_amount), 0) FROM referral_earnings WHERE earner_id=$1", user_id
        ) or 0

        direct_count = await conn.fetchval(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id=$1", user_id
        ) or 0

    return {
        "user_id": user_id,
        "direct_referrals": direct_count,
        "total_earned": float(total_earned),
        "tree": tree["children"] if tree else [],
        "earnings_by_generation": [
            {"generation": r["generation"], "count": r["count"], "total": float(r["total"]), "token": r["token"]}
            for r in earnings
        ],
        "commission_rates": REFERRAL_RATES,
    }


@app.get("/api/referral/link/{user_id}")
async def get_referral_link(user_id: int):
    """Generate referral links for a user"""
    return {
        "telegram_link": f"https://t.me/SLH_AIR_bot?start={user_id}",
        "web_link": f"https://slh-nft.com/?ref={user_id}",
        "rates": REFERRAL_RATES,
        "max_generations": MAX_GENERATIONS,
    }


@app.get("/api/referral/leaderboard")
async def referral_leaderboard(limit: int = Query(20, le=100)):
    """Top referrers by total earnings"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT e.earner_id,
                   COALESCE(w.username, u.username, '') as username,
                   COALESCE(w.first_name, u.username, '') as first_name,
                   COUNT(DISTINCT e.from_user_id) as unique_referrals,
                   SUM(e.commission_amount) as total_earned,
                   MAX(e.generation) as deepest_generation
            FROM referral_earnings e
            LEFT JOIN web_users w ON e.earner_id = w.telegram_id
            LEFT JOIN users u ON e.earner_id = u.user_id
            GROUP BY e.earner_id, w.username, w.first_name, u.username
            ORDER BY total_earned DESC
            LIMIT $1
        """, limit)
    return {
        "leaderboard": [
            {
                "rank": i + 1,
                "user_id": r["earner_id"],
                "username": r["username"] or "",
                "first_name": r["first_name"] or "",
                "unique_referrals": r["unique_referrals"],
                "total_earned": float(r["total_earned"]),
                "deepest_generation": r["deepest_generation"],
            }
            for i, r in enumerate(rows)
        ]
    }


@app.get("/api/referral/stats/{user_id}")
async def referral_stats(user_id: int):
    """Detailed referral statistics for a user"""
    async with pool.acquire() as conn:
        direct = await conn.fetchval("SELECT COUNT(*) FROM referrals WHERE referrer_id=$1", user_id) or 0

        # Count all descendants (recursive)
        all_descendants = 0
        queue = [user_id]
        visited = set()
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            children = await conn.fetch("SELECT user_id FROM referrals WHERE referrer_id=$1", current)
            for c in children:
                all_descendants += 1
                queue.append(c["user_id"])

        total_earned = await conn.fetchval(
            "SELECT COALESCE(SUM(commission_amount), 0) FROM referral_earnings WHERE earner_id=$1", user_id
        ) or 0

        by_gen = await conn.fetch("""
            SELECT generation, COUNT(DISTINCT from_user_id) as people, SUM(commission_amount) as earned
            FROM referral_earnings WHERE earner_id=$1 GROUP BY generation ORDER BY generation
        """, user_id)

        # Who referred me
        my_referrer = await conn.fetchval("SELECT referrer_id FROM referrals WHERE user_id=$1", user_id)

    return {
        "user_id": user_id,
        "my_referrer": my_referrer,
        "direct_referrals": direct,
        "total_network": all_descendants,
        "total_earned_ton": float(total_earned),
        "by_generation": [
            {"generation": r["generation"], "people": r["people"], "earned": float(r["earned"])}
            for r in by_gen
        ],
        "potential_generations": MAX_GENERATIONS,
        "rates": REFERRAL_RATES,
    }


# === ACTIVITY FEED & TRANSACTION HISTORY ===
@app.get("/api/activity/{user_id}")
async def get_activity(user_id: int, limit: int = Query(30, le=100)):
    """Get user activity feed - combines all events into a timeline"""
    activities = []
    async with pool.acquire() as conn:
        # Staking events
        try:
            rows = await conn.fetch(
                "SELECT id, plan, amount, status, start_date as ts FROM staking_positions WHERE user_id=$1 ORDER BY start_date DESC LIMIT $2",
                user_id, limit
            )
            for r in rows:
                activities.append({
                    "type": "staking", "icon": "💎",
                    "title": f"Staked {float(r['amount'])} TON ({r['plan']})",
                    "status": r["status"], "timestamp": r["ts"].isoformat() if r["ts"] else None,
                })
        except Exception:
            pass

        # Deposits
        try:
            rows = await conn.fetch(
                "SELECT plan_key, amount, currency, status, created_at as ts FROM deposits WHERE user_id=$1 ORDER BY created_at DESC LIMIT $2",
                user_id, limit
            )
            for r in rows:
                activities.append({
                    "type": "deposit", "icon": "📥",
                    "title": f"Deposited {float(r['amount'])} {r['currency'] or 'TON'} ({r['plan_key']})",
                    "status": r["status"], "timestamp": r["ts"].isoformat() if r["ts"] else None,
                })
        except Exception:
            pass

        # Token transfers (sent)
        try:
            rows = await conn.fetch(
                "SELECT to_user_id, token, amount, memo, created_at as ts FROM token_transfers WHERE from_user_id=$1 ORDER BY created_at DESC LIMIT $2",
                user_id, limit
            )
            for r in rows:
                activities.append({
                    "type": "transfer_out", "icon": "📤",
                    "title": f"Sent {float(r['amount'])} {r['token']} to {r['to_user_id']}",
                    "status": "completed", "timestamp": r["ts"].isoformat() if r["ts"] else None,
                })
        except Exception:
            pass

        # Token transfers (received)
        try:
            rows = await conn.fetch(
                "SELECT from_user_id, token, amount, created_at as ts FROM token_transfers WHERE to_user_id=$1 ORDER BY created_at DESC LIMIT $2",
                user_id, limit
            )
            for r in rows:
                activities.append({
                    "type": "transfer_in", "icon": "📥",
                    "title": f"Received {float(r['amount'])} {r['token']} from {r['from_user_id']}",
                    "status": "completed", "timestamp": r["ts"].isoformat() if r["ts"] else None,
                })
        except Exception:
            pass

        # Referral earnings
        try:
            rows = await conn.fetch(
                "SELECT from_user_id, generation, commission_amount, token, source_type, created_at as ts FROM referral_earnings WHERE earner_id=$1 ORDER BY created_at DESC LIMIT $2",
                user_id, limit
            )
            for r in rows:
                activities.append({
                    "type": "referral_earning", "icon": "🤝",
                    "title": f"Earned {float(r['commission_amount'])} {r['token']} from Gen {r['generation']} referral",
                    "status": "completed", "timestamp": r["ts"].isoformat() if r["ts"] else None,
                })
        except Exception:
            pass

        # Daily claims
        try:
            rows = await conn.fetch(
                "SELECT amount, streak, claimed_at as ts FROM daily_claims WHERE user_id=$1 ORDER BY claimed_at DESC LIMIT $2",
                user_id, limit
            )
            for r in rows:
                activities.append({
                    "type": "daily_claim", "icon": "🎁",
                    "title": f"Daily claim: {float(r['amount'])} tokens (streak {r['streak']})",
                    "status": "completed", "timestamp": r["ts"].isoformat() if r["ts"] else None,
                })
        except Exception:
            pass

    # Sort by timestamp descending
    activities.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    return {"activities": activities[:limit], "total": len(activities)}


@app.get("/api/transactions/{user_id}")
async def get_transactions(user_id: int, limit: int = Query(50, le=200), offset: int = Query(0)):
    """Full transaction history with pagination"""
    txns = []
    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch("""
                SELECT id, from_user_id, to_user_id, token, amount, memo, tx_type, created_at
                FROM token_transfers
                WHERE from_user_id=$1 OR to_user_id=$1
                ORDER BY created_at DESC LIMIT $2 OFFSET $3
            """, user_id, limit, offset)
            for r in rows:
                direction = "out" if r["from_user_id"] == user_id else "in"
                txns.append({
                    "id": r["id"],
                    "direction": direction,
                    "counterparty": r["to_user_id"] if direction == "out" else r["from_user_id"],
                    "token": r["token"],
                    "amount": float(r["amount"]),
                    "memo": r["memo"],
                    "type": r["tx_type"],
                    "timestamp": r["created_at"].isoformat() if r["created_at"] else None,
                })
        except Exception:
            pass

    return {"transactions": txns, "count": len(txns), "offset": offset}


@app.get("/api/leaderboard")
async def global_leaderboard(category: str = Query("xp", enum=["xp", "balance", "referrals", "staking"]), limit: int = Query(20, le=100)):
    """Global leaderboard - XP, balance, referrals, or staking"""
    async with pool.acquire() as conn:
        rows = []
        try:
            if category == "xp":
                rows = await conn.fetch(
                    "SELECT user_id, username, xp_total as score, level FROM users ORDER BY xp_total DESC LIMIT $1", limit
                )
            elif category == "balance":
                rows = await conn.fetch(
                    "SELECT user_id, username, balance as score, level FROM users ORDER BY balance DESC LIMIT $1", limit
                )
            elif category == "staking":
                rows = await conn.fetch("""
                    SELECT sp.user_id, COALESCE(u.username,'') as username, SUM(sp.amount) as score, COALESCE(u.level,1) as level
                    FROM staking_positions sp LEFT JOIN users u ON sp.user_id = u.user_id
                    WHERE sp.status='active' GROUP BY sp.user_id, u.username, u.level
                    ORDER BY score DESC LIMIT $1
                """, limit)
            elif category == "referrals":
                rows = await conn.fetch("""
                    SELECT r.referrer_id as user_id, COALESCE(u.username,'') as username, COUNT(*) as score, COALESCE(u.level,1) as level
                    FROM referrals r LEFT JOIN users u ON r.referrer_id = u.user_id
                    WHERE r.referrer_id IS NOT NULL
                    GROUP BY r.referrer_id, u.username, u.level
                    ORDER BY score DESC LIMIT $1
                """, limit)
        except Exception:
            pass

    return {
        "category": category,
        "leaderboard": [
            {"rank": i + 1, "user_id": r["user_id"], "username": r["username"] or "", "score": float(r["score"]), "level": r.get("level", 1)}
            for i, r in enumerate(rows)
        ]
    }


# === COMMUNITY SYSTEM ===
# Rate limit store (in-memory)
_community_rate: dict[str, list[float]] = {}

def _check_community_rate(key: str, max_per_hour: int) -> bool:
    now = time.time()
    cutoff = now - 3600
    entries = _community_rate.get(key, [])
    entries = [t for t in entries if t > cutoff]
    _community_rate[key] = entries
    if len(entries) >= max_per_hour:
        return False
    entries.append(now)
    return True

COMMUNITY_SCHEMA = """
CREATE TABLE IF NOT EXISTS community_posts (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    telegram_id TEXT,
    text TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    image_data TEXT,
    likes_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Migration: add image_data for existing DBs
ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS image_data TEXT;
CREATE TABLE IF NOT EXISTS community_likes (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES community_posts(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(post_id, username)
);
CREATE TABLE IF NOT EXISTS community_comments (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES community_posts(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_community_posts_created ON community_posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_community_comments_post ON community_comments(post_id, created_at);
"""

COMMUNITY_SEEDS = [
    ("SLH Official", "\U0001f4cc \u05de\u05d5\u05e6\u05de\u05d3\n\n\u05d1\u05e8\u05d5\u05e8 \u05e9\u05e4\u05e1\u05e4\u05e1\u05ea\u05dd \u05d0\u05ea \u05d4\u05d1\u05d9\u05d8\u05e7\u05d5\u05d9\u05d9\u05df,\n\u05dc\u05d0 \u05d4\u05d1\u05e0\u05ea\u05dd \u05de\u05d4 \u05d6\u05d4 \u05d0\u05d5\u05de\u05e8,\n\u05d1\u05d9\u05d8, \u05d0\u05d5 \u05e7\u05d5\u05d9\u05d9\u05df..\n\n\u05d4\u05d9\u05d5\u05dd \u05d0\u05ea\u05dd \u05de\u05e9\u05dc\u05de\u05d9\u05dd \u05d1\u05d1\u05d9\u05d8 \u05db\u05de\u05e2\u05d8 \u05d1\u05db\u05dc \u05e8\u05db\u05d9\u05e9\u05d4,\n\u05d0\u05d1\u05dc \u05e2\u05d3\u05d9\u05d9\u05df \u05dc\u05d0 \u05de\u05d1\u05d9\u05e0\u05d9\u05dd \u05e9\u05e7\u05d5\u05d9\u05d9\u05df \u2014 \u05d6\u05d4 \u05dc\u05de\u05e2\u05e9\u05d4 \u05d1\u05d7\u05d9\u05e8\u05d4.\n\nSLH \u05d6\u05d5 \u05d4\u05d1\u05d7\u05d9\u05e8\u05d4 \u05d4\u05d7\u05db\u05de\u05d4 \u2014 \u05e1\u05d5\u05e6\u05d9\u05d5\u05e7\u05e8\u05d8\u05d9\u05d4.\n\u05de\u05e0\u05d4\u05dc, \u05dc\u05d0 \u05de\u05e9\u05d8\u05e8 \u05d5\u05dc\u05d0 \u05de\u05de\u05e9\u05dc.\n\u05e7\u05d4\u05d9\u05dc\u05d4. \U0001f3db\ufe0f", "slh", 147),
    ("AvivCrypto", "\u05de\u05d9 \u05e2\u05d5\u05d3 \u05e2\u05e9\u05d4 staking \u05e9\u05dc SLH \u05d4\u05e9\u05d1\u05d5\u05e2? \u05d4\u05ea\u05e9\u05d5\u05d0\u05d5\u05ea \u05de\u05d8\u05d5\u05e8\u05e4\u05d5\u05ea! \U0001f680", "slh", 24),
    ("MosheTrader", "\u05e0\u05d9\u05ea\u05d5\u05d7 \u05e9\u05d5\u05e7 \u05d9\u05d5\u05de\u05d9:\nSLH \u05e0\u05e1\u05d7\u05e8 \u05d1-444\u20aa \u05e2\u05dd \u05e0\u05e4\u05d7 \u05de\u05e1\u05d7\u05e8 \u05d2\u05d1\u05d5\u05d4.", "investments", 31),
    ("NoaInvest", "\u05e9\u05de\u05e2\u05ea\u05dd \u05e2\u05dc \u05d4\u05d1\u05d5\u05d8 \u05d4\u05d7\u05d3\u05e9? Guardian Bot \u05de\u05d2\u05df \u05e2\u05dc \u05d4\u05e7\u05d1\u05d5\u05e6\u05d5\u05ea \u05e9\u05dc\u05db\u05dd! \U0001f6e1\ufe0f", "slh", 18),
    ("DanielDeFi", "\u05d8\u05d9\u05e4 \u05dc\u05de\u05e9\u05e7\u05d9\u05e2\u05d9\u05dd \u05d7\u05d3\u05e9\u05d9\u05dd: \u05ea\u05de\u05d9\u05d3 \u05ea\u05e2\u05e9\u05d5 DYOR \u05dc\u05e4\u05e0\u05d9 \u05db\u05dc \u05d4\u05e9\u05e7\u05e2\u05d4.", "investments", 45),
    ("YosiBlockchain", "\u05de\u05d9\u05e9\u05d4\u05d5 \u05e8\u05d5\u05e6\u05d4 \u05dc\u05d4\u05e6\u05d8\u05e8\u05e3 \u05dc\u05de\u05d9\u05d8\u05d0\u05e4 \u05d1\u05ea\u05dc \u05d0\u05d1\u05d9\u05d1? \U0001f1ee\U0001f1f1", "general", 37),
]

async def _init_community_tables():
    """Create community tables and seed if empty. Called after pool is ready."""
    async with pool.acquire() as conn:
        await conn.execute(COMMUNITY_SCHEMA)
        count = await conn.fetchval("SELECT count(*) FROM community_posts")
        if count == 0:
            for i, (uname, txt, cat, likes) in enumerate(COMMUNITY_SEEDS):
                await conn.execute(
                    "INSERT INTO community_posts (username, text, category, likes_count, created_at) VALUES ($1,$2,$3,$4, now() - interval '1 hour' * $5)",
                    uname, txt, cat, likes, (len(COMMUNITY_SEEDS) - i) * 4
                )

# Hook into existing startup
_original_startup = startup
async def _extended_startup():
    await _original_startup()
    try:
        await _init_community_tables()
    except Exception as e:
        print(f"[community] init warning: {e}")
app.router.on_startup.clear()
app.add_event_handler("startup", _extended_startup)


class CommunityPostCreate(BaseModel):
    username: str
    text: str
    category: str = "general"
    telegram_id: Optional[str] = None
    image_data: Optional[str] = None  # base64 data URL, stored as-is (frontend-capped to 2MB)

class CommunityLikeToggle(BaseModel):
    username: str

class CommunityCommentCreate(BaseModel):
    username: str
    text: str


@app.get("/api/community/posts")
async def community_get_posts(category: str = Query("all"), limit: int = Query(50, le=100), offset: int = Query(0)):
    """Get community posts with comments"""
    async with pool.acquire() as conn:
        if category == "all":
            rows = await conn.fetch(
                "SELECT id, username, telegram_id, text, category, image_data, likes_count, created_at FROM community_posts ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                limit, offset
            )
        else:
            rows = await conn.fetch(
                "SELECT id, username, telegram_id, text, category, image_data, likes_count, created_at FROM community_posts WHERE category=$1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                category, limit, offset
            )
        posts = []
        for row in rows:
            post = dict(row)
            post["created_at"] = post["created_at"].isoformat()
            comments = await conn.fetch(
                "SELECT id, username, text, created_at FROM community_comments WHERE post_id=$1 ORDER BY created_at ASC",
                post["id"]
            )
            post["comments"] = [
                {"id": c["id"], "username": c["username"], "text": c["text"], "created_at": c["created_at"].isoformat()}
                for c in comments
            ]
            posts.append(post)
    return {"posts": posts, "count": len(posts), "offset": offset}


@app.post("/api/community/posts")
async def community_create_post(body: CommunityPostCreate):
    """Create a new community post"""
    if not body.text.strip() or not body.username.strip():
        raise HTTPException(400, "Username and text required")
    if not _check_community_rate(f"post:{body.username}", 10):
        raise HTTPException(429, "Rate limit: max 10 posts per hour")

    # Image validation: accept data URL only (frontend caps at 2MB), reject suspicious URLs
    image_data = body.image_data
    if image_data:
        if not image_data.startswith("data:image/"):
            image_data = None  # silently drop if not a proper data URL
        elif len(image_data) > 3_500_000:  # 2MB base64 ≈ 2.7MB encoded, +safety
            raise HTTPException(413, "Image too large (max 2MB)")

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO community_posts (username, telegram_id, text, category, image_data) VALUES ($1,$2,$3,$4,$5) RETURNING id, username, telegram_id, text, category, image_data, likes_count, created_at",
            body.username.strip(), body.telegram_id, body.text.strip(), body.category, image_data
        )
        post = dict(row)
        post["created_at"] = post["created_at"].isoformat()
        post["comments"] = []
        return post


@app.post("/api/community/posts/{post_id}/like")
async def community_toggle_like(post_id: int, body: CommunityLikeToggle):
    """Toggle like on a post"""
    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT id FROM community_posts WHERE id=$1", post_id)
        if not exists:
            raise HTTPException(404, "Post not found")
        existing = await conn.fetchval(
            "SELECT id FROM community_likes WHERE post_id=$1 AND username=$2", post_id, body.username
        )
        if existing:
            await conn.execute("DELETE FROM community_likes WHERE id=$1", existing)
            await conn.execute("UPDATE community_posts SET likes_count=GREATEST(likes_count-1,0) WHERE id=$1", post_id)
            return {"action": "unliked", "post_id": post_id}
        else:
            await conn.execute("INSERT INTO community_likes (post_id,username) VALUES ($1,$2)", post_id, body.username)
            await conn.execute("UPDATE community_posts SET likes_count=likes_count+1 WHERE id=$1", post_id)
            return {"action": "liked", "post_id": post_id}


@app.post("/api/community/posts/{post_id}/comments")
async def community_add_comment(post_id: int, body: CommunityCommentCreate):
    """Add a comment to a post"""
    if not body.text.strip() or not body.username.strip():
        raise HTTPException(400, "Username and text required")
    if not _check_community_rate(f"comment:{body.username}", 50):
        raise HTTPException(429, "Rate limit: max 50 comments per hour")
    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT id FROM community_posts WHERE id=$1", post_id)
        if not exists:
            raise HTTPException(404, "Post not found")
        row = await conn.fetchrow(
            "INSERT INTO community_comments (post_id, username, text) VALUES ($1,$2,$3) RETURNING id, post_id, username, text, created_at",
            post_id, body.username.strip(), body.text.strip()
        )
        comment = dict(row)
        comment["created_at"] = comment["created_at"].isoformat()
        return comment


@app.get("/api/community/stats")
async def community_stats():
    """Community statistics"""
    async with pool.acquire() as conn:
        total_posts = await conn.fetchval("SELECT count(*) FROM community_posts")
        total_users = await conn.fetchval("SELECT count(DISTINCT username) FROM community_posts")
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        posts_today = await conn.fetchval("SELECT count(*) FROM community_posts WHERE created_at >= $1", today_start)
        active_today = await conn.fetchval("SELECT count(DISTINCT username) FROM community_posts WHERE created_at >= $1", today_start)
    return {"total_posts": total_posts, "total_users": total_users, "posts_today": posts_today, "active_today": active_today}


@app.get("/api/community/health")
async def community_health():
    return {"status": "ok", "service": "community"}


# === ANALYTICS ENDPOINTS ===
@app.post("/api/analytics/event")
async def analytics_event(request: Request):
    """Receive analytics events from the website tracker"""
    try:
        data = await request.json()
        # Store in DB if table exists, otherwise just acknowledge
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id BIGSERIAL PRIMARY KEY,
                    event_type TEXT,
                    page TEXT,
                    visitor_id TEXT,
                    session_id TEXT,
                    data JSONB,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            await conn.execute(
                "INSERT INTO analytics_events (event_type, page, visitor_id, session_id, data) VALUES ($1,$2,$3,$4,$5)",
                data.get("event", "pageview"),
                data.get("page", ""),
                data.get("visitor_id", ""),
                data.get("session_id", ""),
                json.dumps(data)
            )
        return {"status": "ok"}
    except Exception as e:
        return {"status": "ok", "note": str(e)}


@app.get("/api/analytics/stats")
async def analytics_stats():
    """Get aggregated analytics stats for the admin dashboard"""
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id BIGSERIAL PRIMARY KEY,
                    event_type TEXT,
                    page TEXT,
                    visitor_id TEXT,
                    session_id TEXT,
                    data JSONB,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            total_events = await conn.fetchval("SELECT count(*) FROM analytics_events")
            unique_visitors = await conn.fetchval("SELECT count(DISTINCT visitor_id) FROM analytics_events WHERE visitor_id != ''")
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_views = await conn.fetchval("SELECT count(*) FROM analytics_events WHERE created_at >= $1", today_start)
            today_visitors = await conn.fetchval("SELECT count(DISTINCT visitor_id) FROM analytics_events WHERE created_at >= $1 AND visitor_id != ''", today_start)

            # Last 7 days breakdown
            daily = await conn.fetch("""
                SELECT DATE(created_at) as day, count(*) as views, count(DISTINCT visitor_id) as visitors
                FROM analytics_events WHERE created_at >= now() - interval '7 days'
                GROUP BY DATE(created_at) ORDER BY day
            """)

            # Top pages
            pages = await conn.fetch("""
                SELECT page, count(*) as views FROM analytics_events
                WHERE page != '' GROUP BY page ORDER BY views DESC LIMIT 10
            """)

            return {
                "total_events": total_events,
                "unique_visitors": unique_visitors,
                "today_views": today_views,
                "today_visitors": today_visitors,
                "daily": [{"day": str(r["day"]), "views": r["views"], "visitors": r["visitors"]} for r in daily],
                "top_pages": [{"page": r["page"], "views": r["views"]} for r in pages],
            }
        except Exception as e:
            return {"error": str(e)}


# === WALLET API ENDPOINTS ===
# For wallet.html real data integration

class DepositRequest(BaseModel):
    user_id: int
    amount: float
    currency: str = "SLH"
    tx_hash: str


def _generate_bsc_address(user_id: int) -> str:
    """Generate a deterministic BSC deposit address from user_id."""
    raw = hashlib.sha256(f"slh-deposit-{user_id}".encode()).hexdigest()
    return "0x" + raw[:40]



# Static route MUST come before /{user_id} to avoid FastAPI matching "price" as user_id
@app.get("/api/wallet/price")
async def get_slh_price():
    """Return current SLH price in ILS and USD"""
    slh_usd = round(SLH_PRICE_ILS / USD_ILS_RATE, 4)
    return {
        "token": "SLH",
        "price_ils": SLH_PRICE_ILS,
        "price_usd": slh_usd,
        "usd_ils_rate": USD_ILS_RATE,
        "bsc_contract": SLH_BSC_CONTRACT,
    }


@app.get("/api/wallet/{user_id}")
async def get_wallet(user_id: int):
    """Get user wallet info: SLH balance, deposit addresses"""
    async with pool.acquire() as conn:
        # Get SLH balance from token_balances
        balance_row = await conn.fetchrow(
            "SELECT balance FROM token_balances WHERE user_id=$1 AND token='SLH'",
            user_id
        )
        slh_balance = float(balance_row["balance"]) if balance_row else 0.0

    bsc_address = _generate_bsc_address(user_id)
    slh_usd = round(SLH_PRICE_ILS / USD_ILS_RATE, 4)

    return {
        "user_id": user_id,
        "slh_balance": slh_balance,
        "slh_value_ils": round(slh_balance * SLH_PRICE_ILS, 2),
        "slh_value_usd": round(slh_balance * slh_usd, 2),
        "bsc_deposit_address": bsc_address,
        "ton_deposit_address": SLH_TON_WALLET,
        "ton_memo": str(user_id),
        "bsc_contract": SLH_BSC_CONTRACT,
    }


@app.get("/api/wallet/{user_id}/balances")
async def get_wallet_balances(user_id: int):
    """Get all token balances for a user"""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT token, balance FROM token_balances WHERE user_id=$1",
            user_id
        )
    balances = {r["token"]: float(r["balance"]) for r in rows}
    # Ensure SLH always appears
    if "SLH" not in balances:
        balances["SLH"] = 0.0

    slh_usd = round(SLH_PRICE_ILS / USD_ILS_RATE, 4)
    slh_bal = balances.get("SLH", 0.0)

    return {
        "user_id": user_id,
        "balances": balances,
        "total_slh": slh_bal,
        "total_value_ils": round(slh_bal * SLH_PRICE_ILS, 2),
        "total_value_usd": round(slh_bal * slh_usd, 2),
    }


@app.post("/api/wallet/deposit")
async def record_deposit(req: DepositRequest):
    """Record a deposit and credit token_balances"""
    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    if not req.tx_hash.strip():
        raise HTTPException(400, "tx_hash is required")

    async with pool.acquire() as conn:
        # Check for duplicate tx_hash
        existing = await conn.fetchval(
            "SELECT id FROM deposits WHERE tx_hash=$1", req.tx_hash.strip()
        )
        if existing:
            raise HTTPException(409, "Transaction already recorded")

        async with conn.transaction():
            # Insert deposit record
            dep_id = await conn.fetchval("""
                INSERT INTO deposits (user_id, amount, currency, tx_hash, status, created_at)
                VALUES ($1, $2, $3, $4, 'confirmed', now())
                RETURNING id
            """, req.user_id, req.amount, req.currency, req.tx_hash.strip())

            # Credit token_balances
            await conn.execute("""
                INSERT INTO token_balances (user_id, token, balance)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, token) DO UPDATE SET balance = token_balances.balance + $3
            """, req.user_id, req.currency, req.amount)

            # Record in token_transfers
            await conn.execute("""
                INSERT INTO token_transfers (from_user_id, to_user_id, token, amount, memo, tx_type)
                VALUES ($1, $2, $3, $4, $5, 'deposit')
            """, req.user_id, req.user_id, req.currency, req.amount, f"deposit:{req.tx_hash.strip()}")

    return {
        "status": "ok",
        "deposit_id": dep_id,
        "user_id": req.user_id,
        "amount": req.amount,
        "currency": req.currency,
        "tx_hash": req.tx_hash.strip(),
    }


@app.get("/api/wallet/{user_id}/transactions")
async def get_wallet_transactions(user_id: int, limit: int = Query(50, le=200), offset: int = Query(0)):
    """Get transaction history from token_transfers for a user"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, from_user_id, to_user_id, token, amount, memo, tx_type, created_at
            FROM token_transfers
            WHERE from_user_id=$1 OR to_user_id=$1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """, user_id, limit, offset)

        total = await conn.fetchval(
            "SELECT count(*) FROM token_transfers WHERE from_user_id=$1 OR to_user_id=$1",
            user_id
        )

    transactions = []
    for r in rows:
        direction = "out" if r["from_user_id"] == user_id and r["to_user_id"] != user_id else "in"
        if r["tx_type"] == "deposit":
            direction = "in"
        transactions.append({
            "id": r["id"],
            "direction": direction,
            "counterparty": r["to_user_id"] if direction == "out" else r["from_user_id"],
            "token": r["token"],
            "amount": float(r["amount"]),
            "memo": r["memo"],
            "type": r["tx_type"],
            "timestamp": r["created_at"].isoformat() if r["created_at"] else None,
        })

    return {
        "user_id": user_id,
        "transactions": transactions,
        "total": total or 0,
        "limit": limit,
        "offset": offset,
    }

class WalletSendRequest(BaseModel):
    to: str
    amount: float
    currency: str = "SLH"
    request_id: str


@app.post("/api/wallet/send")
async def wallet_send(req: WalletSendRequest, authorization: Optional[str] = Header(None)):
    user_id = get_current_user_id(authorization)

    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    if not req.request_id or len(req.request_id.strip()) < 8:
        raise HTTPException(400, "request_id is required")

    if not _check_wallet_send_rate(user_id, cooldown_seconds=5):
        raise HTTPException(429, "Too many requests, wait a few seconds")

    token = (req.currency or "SLH").upper().strip()
    if token != "SLH":
        raise HTTPException(400, "Only SLH internal transfer is supported right now")

    if not req.to.isdigit():
        raise HTTPException(400, "Recipient must be a Telegram numeric ID for now")

    to_user_id = int(req.to)
    if to_user_id == user_id:
        raise HTTPException(400, "Cannot send to yourself")

    async with pool.acquire() as conn:
        async with conn.transaction():
            existing = await conn.fetchrow(
                "SELECT tx_transfer_id FROM wallet_idempotency WHERE user_id=$1 AND request_id=$2",
                user_id, req.request_id.strip()
            )

            if existing and existing["tx_transfer_id"]:
                row = await conn.fetchrow(
                    """
                    SELECT id, from_user_id, to_user_id, token, amount, memo, tx_type, created_at
                    FROM token_transfers
                    WHERE id=$1
                    """,
                    existing["tx_transfer_id"]
                )
                if row:
                    return {
                        "status": "ok",
                        "data": {
                            "transfer_id": row["id"],
                            "from_id": row["from_user_id"],
                            "to_id": row["to_user_id"],
                            "token": row["token"],
                            "amount": float(row["amount"]),
                            "memo": row["memo"],
                            "type": row["tx_type"],
                            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                            "idempotent_replay": True
                        }
                    }

            balance = await conn.fetchval(
                "SELECT balance FROM token_balances WHERE user_id=$1 AND token=$2",
                user_id, token
            )
            if balance is None or float(balance) < req.amount:
                raise HTTPException(400, "Insufficient balance")

            await conn.execute(
                "UPDATE token_balances SET balance = balance - $1, updated_at = CURRENT_TIMESTAMP WHERE user_id=$2 AND token=$3",
                req.amount, user_id, token
            )

            await conn.execute(
                """
                INSERT INTO token_balances (user_id, token, balance, updated_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, token)
                DO UPDATE SET balance = token_balances.balance + $3, updated_at = CURRENT_TIMESTAMP
                """,
                to_user_id, token, req.amount
            )

            transfer_id = await conn.fetchval(
                """
                INSERT INTO token_transfers (from_user_id, to_user_id, token, amount, memo, tx_type)
                VALUES ($1, $2, $3, $4, $5, 'wallet_send')
                RETURNING id
                """,
                user_id, to_user_id, token, req.amount, f"wallet send | request_id={req.request_id.strip()}"
            )

            await conn.execute(
                """
                INSERT INTO wallet_idempotency (user_id, request_id, tx_transfer_id)
                VALUES ($1, $2, $3)
                """,
                user_id, req.request_id.strip(), transfer_id
            )

            row = await conn.fetchrow(
                """
                SELECT id, from_user_id, to_user_id, token, amount, memo, tx_type, created_at
                FROM token_transfers
                WHERE id=$1
                """,
                transfer_id
            )

    return {
        "status": "ok",
        "data": {
            "transfer_id": row["id"],
            "from_id": row["from_user_id"],
            "to_id": row["to_user_id"],
            "token": row["token"],
            "amount": float(row["amount"]),
            "memo": row["memo"],
            "type": row["tx_type"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "idempotent_replay": False
        }
    }


# === ADMIN DASHBOARD API ===

@app.get("/api/admin/dashboard")
async def admin_dashboard():
    """Aggregated admin dashboard data — all stats in one call"""
    async def safe(conn, query, *args):
        try:
            return await conn.fetchval(query, *args) or 0
        except Exception:
            return 0

    async with pool.acquire() as conn:
        total_users = await safe(conn, "SELECT COUNT(*) FROM web_users")
        premium_users = await safe(conn, "SELECT COUNT(*) FROM premium_users WHERE payment_status='approved'")
        total_staked = await safe(conn, "SELECT COALESCE(SUM(amount),0) FROM staking_positions WHERE status='active'")
        total_deposits = await safe(conn, "SELECT COALESCE(SUM(amount),0) FROM deposits WHERE status='active'")
        pending_payments = await safe(conn, "SELECT COUNT(*) FROM premium_users WHERE payment_status='pending'")

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_views = await safe(conn, "SELECT COUNT(*) FROM analytics_events WHERE created_at >= $1", today_start)
        today_visitors = await safe(conn, "SELECT COUNT(DISTINCT visitor_id) FROM analytics_events WHERE created_at >= $1 AND visitor_id != ''", today_start)
        total_events = await safe(conn, "SELECT COUNT(*) FROM analytics_events")
        total_visitors = await safe(conn, "SELECT COUNT(DISTINCT visitor_id) FROM analytics_events WHERE visitor_id != ''")

        # Recent signups
        today_signups = await safe(conn, "SELECT COUNT(*) FROM web_users WHERE last_login >= $1", today_start)

        # Referral stats
        referral_count = await safe(conn, "SELECT COUNT(*) FROM referrals")

        # Last 7 days analytics
        try:
            daily = await conn.fetch("""
                SELECT DATE(created_at) as day, COUNT(*) as views, COUNT(DISTINCT visitor_id) as visitors
                FROM analytics_events WHERE created_at >= now() - interval '7 days'
                GROUP BY DATE(created_at) ORDER BY day
            """)
            daily_data = [{"day": str(r["day"]), "views": r["views"], "visitors": r["visitors"]} for r in daily]
        except Exception:
            daily_data = []

        # Top pages
        try:
            pages = await conn.fetch("""
                SELECT page, COUNT(*) as views FROM analytics_events
                WHERE page != '' GROUP BY page ORDER BY views DESC LIMIT 10
            """)
            top_pages = [{"page": r["page"], "views": r["views"]} for r in pages]
        except Exception:
            top_pages = []

        # Recent users
        try:
            recent = await conn.fetch(
                "SELECT telegram_id, username, first_name, last_login FROM web_users ORDER BY last_login DESC LIMIT 15"
            )
            recent_users = [{"id": r["telegram_id"], "username": r["username"], "name": r["first_name"], "last_login": str(r["last_login"])} for r in recent]
        except Exception:
            recent_users = []

    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "pending_payments": pending_payments,
        "total_staked_ton": float(total_staked),
        "total_deposits_ton": float(total_deposits),
        "referral_count": referral_count,
        "today_signups": today_signups,
        "analytics": {
            "total_events": total_events,
            "total_visitors": total_visitors,
            "today_views": today_views,
            "today_visitors": today_visitors,
            "daily": daily_data,
            "top_pages": top_pages,
        },
        "recent_users": recent_users,
        "bots_live": 20,
        "timestamp": datetime.utcnow().isoformat(),
    }


# === UNIFIED USER ENDPOINT (single call for everything) ===
@app.get("/api/user/full/{telegram_id}")
async def get_user_full(telegram_id: int):
    """Return EVERYTHING about a user in one call.

    Consolidates: profile, registration, wallets (internal + linked Web3),
    balances (from all sources), premium status, staking, deposits,
    referrals, recent transactions, marketplace activity.

    Designed to be the single source of truth for the dashboard / mini-app,
    so the bot / website / mini-app all show the same numbers.
    """
    async with pool.acquire() as conn:
        profile = await conn.fetchrow("""
            SELECT telegram_id, username, first_name, photo_url, auth_date, last_login,
                   is_registered, registered_at, eth_wallet, eth_wallet_linked_at,
                   ton_wallet, ton_wallet_linked_at
              FROM web_users WHERE telegram_id=$1
        """, telegram_id)
        if not profile:
            raise HTTPException(404, "User not found")

        # All internal token balances
        balances = {"TON_available": 0.0, "TON_locked": 0.0}
        try:
            rows = await conn.fetch(
                "SELECT token, balance FROM token_balances WHERE user_id=$1", telegram_id
            )
            for row in rows:
                balances[row["token"]] = float(row["balance"])
        except Exception:
            pass

        # Bank account balances if available
        try:
            bank = await conn.fetchrow(
                "SELECT COALESCE(available,0) as available, COALESCE(locked,0) as locked_amt "
                "FROM account_balances WHERE account_id=$1", telegram_id
            )
            if bank:
                balances["TON_available"] = float(bank["available"] or 0)
                balances["TON_locked"] = float(bank["locked_amt"] or 0)
        except Exception:
            pass

        # Deposits
        deposits = []
        try:
            rows = await conn.fetch(
                "SELECT id, amount, currency, tx_hash, status, plan_key, created_at "
                "FROM deposits WHERE user_id=$1 ORDER BY created_at DESC LIMIT 20",
                telegram_id
            )
            deposits = [{
                "id": r["id"], "amount": float(r["amount"]), "currency": r["currency"],
                "tx_hash": r["tx_hash"], "status": r["status"], "plan_key": r["plan_key"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            } for r in rows]
        except Exception:
            pass

        # Active staking positions
        staking = []
        try:
            rows = await conn.fetch("""
                SELECT id, plan, amount, currency, apy_monthly, lock_days,
                       start_date, end_date, status, earned
                  FROM staking_positions
                 WHERE user_id=$1 AND status='active'
                 ORDER BY start_date DESC
            """, telegram_id)
            staking = [{
                "id": r["id"], "plan": r["plan"], "amount": float(r["amount"]),
                "currency": r["currency"], "apy_monthly": float(r["apy_monthly"]),
                "lock_days": r["lock_days"],
                "start_date": r["start_date"].isoformat() if r["start_date"] else None,
                "end_date": r["end_date"].isoformat() if r["end_date"] else None,
                "status": r["status"], "earned": float(r["earned"] or 0),
            } for r in rows]
        except Exception:
            pass

        # Referral stats
        referrals = {"direct_count": 0, "total_network": 0, "total_earned": 0.0}
        try:
            direct = await conn.fetchval(
                "SELECT count(*) FROM referrals WHERE referrer_id=$1", telegram_id
            ) or 0
            earned = await conn.fetchval(
                "SELECT COALESCE(SUM(commission_amount), 0) FROM referral_earnings WHERE earner_id=$1",
                telegram_id
            ) or 0
            referrals = {
                "direct_count": int(direct),
                "total_network": int(direct),  # TODO: real recursive count
                "total_earned": float(earned),
            }
        except Exception:
            pass

        # Recent transfers
        transactions = []
        try:
            rows = await conn.fetch("""
                SELECT id, from_user_id, to_user_id, token, amount, memo, tx_type, created_at
                  FROM token_transfers
                 WHERE from_user_id=$1 OR to_user_id=$1
                 ORDER BY created_at DESC LIMIT 20
            """, telegram_id)
            transactions = [{
                "id": r["id"],
                "direction": "out" if r["from_user_id"] == telegram_id else "in",
                "counterparty": r["to_user_id"] if r["from_user_id"] == telegram_id else r["from_user_id"],
                "token": r["token"], "amount": float(r["amount"]),
                "memo": r["memo"] or "", "tx_type": r["tx_type"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            } for r in rows]
        except Exception:
            pass

        # Marketplace activity
        marketplace = {"listings": 0, "orders_bought": 0, "orders_sold": 0}
        try:
            marketplace["listings"] = int(await conn.fetchval(
                "SELECT count(*) FROM marketplace_items WHERE seller_id=$1", telegram_id
            ) or 0)
            marketplace["orders_bought"] = int(await conn.fetchval(
                "SELECT count(*) FROM marketplace_orders WHERE buyer_id=$1", telegram_id
            ) or 0)
            marketplace["orders_sold"] = int(await conn.fetchval(
                "SELECT count(*) FROM marketplace_orders WHERE seller_id=$1", telegram_id
            ) or 0)
        except Exception:
            pass

        # Premium status
        premium_status = "none"
        try:
            row = await conn.fetchrow(
                "SELECT payment_status FROM premium_users WHERE user_id=$1 AND bot_name='expertnet'",
                telegram_id
            )
            if row:
                premium_status = row["payment_status"]
        except Exception:
            pass

    return {
        "profile": {
            "telegram_id": profile["telegram_id"],
            "username": profile["username"],
            "first_name": profile["first_name"],
            "photo_url": profile["photo_url"],
            "last_login": profile["last_login"].isoformat() if profile["last_login"] else None,
            "is_registered": profile["is_registered"],
            "registered_at": profile["registered_at"].isoformat() if profile["registered_at"] else None,
        },
        "wallets": {
            "ton_internal": SLH_TON_WALLET,  # shared project wallet
            "eth_linked": profile["eth_wallet"],
            "eth_linked_at": profile["eth_wallet_linked_at"].isoformat() if profile["eth_wallet_linked_at"] else None,
            "ton_linked": profile["ton_wallet"],
            "ton_linked_at": profile["ton_wallet_linked_at"].isoformat() if profile["ton_wallet_linked_at"] else None,
        },
        "balances": balances,
        "deposits": deposits,
        "staking": staking,
        "referrals": referrals,
        "transactions": transactions,
        "marketplace": marketplace,
        "premium": {
            "status": premium_status,
            "is_premium": premium_status == "approved",
        },
        "price_info": {
            "slh_ils": SLH_PRICE_ILS,
            "slh_usd": round(SLH_PRICE_ILS / USD_ILS_RATE, 4),
            "registration_ils": REGISTRATION_PRICE_ILS,
            "registration_usd": round(REGISTRATION_PRICE_ILS / USD_ILS_RATE, 4),
        },
    }


# === MARKETPLACE ENDPOINTS ===
class MarketplaceListRequest(BaseModel):
    seller_id: int
    title: str
    description: Optional[str] = ""
    price: float
    currency: Optional[str] = "SLH"
    image_url: Optional[str] = ""  # URL or data:image/... base64
    category: Optional[str] = "general"
    stock: Optional[int] = 1
    promotion: Optional[str] = "none"  # none | featured | top | homepage


class MarketplaceBuyRequest(BaseModel):
    buyer_id: int
    item_id: int
    quantity: Optional[int] = 1


class MarketplaceApproveRequest(BaseModel):
    admin_id: int
    item_id: int
    action: str  # 'approve' | 'reject'


ALLOWED_CURRENCIES = {"SLH", "TON", "ILS", "USD"}
ALLOWED_CATEGORIES = {"general", "digital", "physical", "nft", "course", "service"}


@app.post("/api/marketplace/list")
async def marketplace_list_item(req: MarketplaceListRequest):
    """Create a new marketplace listing. Starts as 'pending' until admin approves."""
    title = (req.title or "").strip()
    if not title or len(title) < 3:
        raise HTTPException(400, "Title must be at least 3 characters")
    if len(title) > 200:
        raise HTTPException(400, "Title too long (max 200 chars)")
    if req.price is None or req.price <= 0:
        raise HTTPException(400, "Price must be positive")
    currency = (req.currency or "SLH").upper()
    if currency not in ALLOWED_CURRENCIES:
        raise HTTPException(400, f"Currency must be one of: {sorted(ALLOWED_CURRENCIES)}")
    category = (req.category or "general").lower()
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(400, f"Category must be one of: {sorted(ALLOWED_CATEGORIES)}")
    stock = max(1, int(req.stock or 1))
    description = (req.description or "").strip()[:2000]
    # Image: accept either regular URL (capped at 500 chars) or data:image/... base64 (3.5MB raw cap)
    image_url = (req.image_url or "").strip()
    if image_url.startswith("data:image/"):
        if len(image_url) > 3_500_000:
            raise HTTPException(413, "Image too large (max 2MB)")
    else:
        image_url = image_url[:500]
    promotion = (req.promotion or "none").lower()
    if promotion not in {"none", "featured", "top", "homepage"}:
        promotion = "none"

    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT 1 FROM web_users WHERE telegram_id=$1", req.seller_id)
        if not exists:
            raise HTTPException(404, "Seller not found — please login first")

        # Admin listings are auto-approved
        initial_status = "approved" if req.seller_id == ADMIN_USER_ID else "pending"
        approved_at = "CURRENT_TIMESTAMP" if initial_status == "approved" else "NULL"

        row = await conn.fetchrow(f"""
            INSERT INTO marketplace_items
                (seller_id, title, description, price, currency, image_url, category, stock, status, promotion, approved_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, {approved_at})
            RETURNING id, status, created_at
        """, req.seller_id, title, description, req.price, currency, image_url, category, stock, initial_status, promotion)

    print(f"[Marketplace] New listing #{row['id']} by {req.seller_id}: {title} ({req.price} {currency}) status={row['status']}")
    return {
        "ok": True,
        "item_id": row["id"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "message": "פריט הועלה לאישור" if initial_status == "pending" else "פריט פורסם בהצלחה"
    }


@app.get("/api/marketplace/items")
async def marketplace_get_items(
    category: Optional[str] = None,
    status: str = "approved",
    limit: int = Query(50, le=200),
    offset: int = 0
):
    """List marketplace items. Default: approved only. Supports category filter.

    Promoted items (homepage > top > featured > none) sort first.
    """
    query = """
        SELECT mi.id, mi.seller_id, mi.title, mi.description, mi.price, mi.currency,
               mi.image_url, mi.category, mi.stock, mi.status,
               COALESCE(mi.promotion, 'none') AS promotion,
               COALESCE(mi.views, 0) AS views,
               mi.created_at, mi.approved_at,
               COALESCE(wu.username, wu.first_name, '') AS seller_name
          FROM marketplace_items mi
          LEFT JOIN web_users wu ON wu.telegram_id = mi.seller_id
         WHERE 1=1
    """
    params = []
    if status:
        params.append(status)
        query += f" AND mi.status = ${len(params)}"
    if category:
        params.append(category.lower())
        query += f" AND mi.category = ${len(params)}"
    query += """
         ORDER BY
            CASE COALESCE(mi.promotion, 'none')
                WHEN 'homepage' THEN 0
                WHEN 'top' THEN 1
                WHEN 'featured' THEN 2
                ELSE 3
            END,
            mi.created_at DESC
    """
    params.append(limit)
    query += f" LIMIT ${len(params)}"
    params.append(offset)
    query += f" OFFSET ${len(params)}"

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "seller_id": r["seller_id"],
            "seller_name": r["seller_name"] or f"user{r['seller_id']}",
            "title": r["title"],
            "description": r["description"] or "",
            "price": float(r["price"]),
            "currency": r["currency"],
            "image_url": r["image_url"] or "",
            "category": r["category"],
            "stock": r["stock"],
            "status": r["status"],
            "promotion": r["promotion"] or "none",
            "views": r["views"] or 0,
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "approved_at": r["approved_at"].isoformat() if r["approved_at"] else None,
        })
    return {"items": items, "count": len(items), "limit": limit, "offset": offset}


@app.get("/api/marketplace/items/{item_id}")
async def marketplace_get_item(item_id: int):
    """Get a single marketplace item by ID."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT mi.id, mi.seller_id, mi.title, mi.description, mi.price, mi.currency,
                   mi.image_url, mi.category, mi.stock, mi.status, mi.created_at, mi.approved_at,
                   COALESCE(wu.username, wu.first_name, '') AS seller_name
              FROM marketplace_items mi
              LEFT JOIN web_users wu ON wu.telegram_id = mi.seller_id
             WHERE mi.id = $1
        """, item_id)
    if not row:
        raise HTTPException(404, "Item not found")
    return {
        "id": row["id"],
        "seller_id": row["seller_id"],
        "seller_name": row["seller_name"] or f"user{row['seller_id']}",
        "title": row["title"],
        "description": row["description"] or "",
        "price": float(row["price"]),
        "currency": row["currency"],
        "image_url": row["image_url"] or "",
        "category": row["category"],
        "stock": row["stock"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "approved_at": row["approved_at"].isoformat() if row["approved_at"] else None,
    }


@app.post("/api/marketplace/buy")
async def marketplace_buy(req: MarketplaceBuyRequest):
    """Create an order for an approved marketplace item. Decrements stock atomically."""
    if req.quantity < 1:
        raise HTTPException(400, "Quantity must be at least 1")

    async with pool.acquire() as conn:
        async with conn.transaction():
            buyer = await conn.fetchval("SELECT 1 FROM web_users WHERE telegram_id=$1", req.buyer_id)
            if not buyer:
                raise HTTPException(404, "Buyer not found — please login first")

            item = await conn.fetchrow("""
                SELECT id, seller_id, title, price, currency, stock, status
                  FROM marketplace_items
                 WHERE id = $1
                 FOR UPDATE
            """, req.item_id)
            if not item:
                raise HTTPException(404, "Item not found")
            if item["status"] != "approved":
                raise HTTPException(400, f"Item is {item['status']}, not available for purchase")
            if item["seller_id"] == req.buyer_id:
                raise HTTPException(400, "Cannot buy your own item")
            if item["stock"] < req.quantity:
                raise HTTPException(400, f"Not enough stock (available: {item['stock']})")

            total_price = float(item["price"]) * req.quantity

            order = await conn.fetchrow("""
                INSERT INTO marketplace_orders
                    (buyer_id, seller_id, item_id, quantity, total_price, currency, status)
                VALUES ($1, $2, $3, $4, $5, $6, 'pending')
                RETURNING id, created_at
            """, req.buyer_id, item["seller_id"], item["id"], req.quantity, total_price, item["currency"])

            # Decrement stock (mark sold-out if it hits zero)
            new_stock = item["stock"] - req.quantity
            new_status = "sold_out" if new_stock == 0 else item["status"]
            await conn.execute("""
                UPDATE marketplace_items
                   SET stock = $1, status = $2
                 WHERE id = $3
            """, new_stock, new_status, item["id"])

    print(f"[Marketplace] Order #{order['id']}: buyer={req.buyer_id} item={req.item_id} x{req.quantity} = {total_price} {item['currency']}")
    return {
        "ok": True,
        "order_id": order["id"],
        "item_id": req.item_id,
        "quantity": req.quantity,
        "total_price": total_price,
        "currency": item["currency"],
        "status": "pending",
        "created_at": order["created_at"].isoformat() if order["created_at"] else None,
        "message": "הזמנה נוצרה — ממתין לתשלום",
    }


@app.get("/api/marketplace/orders/{user_id}")
async def marketplace_user_orders(user_id: int, role: str = "buyer", limit: int = Query(50, le=200)):
    """List orders for a user. role=buyer|seller."""
    if role not in ("buyer", "seller"):
        raise HTTPException(400, "role must be 'buyer' or 'seller'")

    col = "buyer_id" if role == "buyer" else "seller_id"
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT mo.id, mo.buyer_id, mo.seller_id, mo.item_id, mo.quantity,
                   mo.total_price, mo.currency, mo.status, mo.created_at, mo.completed_at,
                   mi.title AS item_title, mi.image_url AS item_image
              FROM marketplace_orders mo
              LEFT JOIN marketplace_items mi ON mi.id = mo.item_id
             WHERE mo.{col} = $1
             ORDER BY mo.created_at DESC
             LIMIT $2
        """, user_id, limit)

    orders = []
    for r in rows:
        orders.append({
            "id": r["id"],
            "buyer_id": r["buyer_id"],
            "seller_id": r["seller_id"],
            "item_id": r["item_id"],
            "item_title": r["item_title"] or "",
            "item_image": r["item_image"] or "",
            "quantity": r["quantity"],
            "total_price": float(r["total_price"]),
            "currency": r["currency"],
            "status": r["status"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "completed_at": r["completed_at"].isoformat() if r["completed_at"] else None,
        })
    return {"orders": orders, "count": len(orders), "role": role}


@app.get("/api/marketplace/my-listings/{user_id}")
async def marketplace_my_listings(user_id: int, limit: int = Query(50, le=200)):
    """List all items a user has put up for sale (any status)."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, seller_id, title, description, price, currency, image_url,
                   category, stock, status, created_at, approved_at
              FROM marketplace_items
             WHERE seller_id = $1
             ORDER BY created_at DESC
             LIMIT $2
        """, user_id, limit)
    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "title": r["title"],
            "description": r["description"] or "",
            "price": float(r["price"]),
            "currency": r["currency"],
            "image_url": r["image_url"] or "",
            "category": r["category"],
            "stock": r["stock"],
            "status": r["status"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "approved_at": r["approved_at"].isoformat() if r["approved_at"] else None,
        })
    return {"items": items, "count": len(items)}


@app.post("/api/marketplace/admin/approve")
async def marketplace_admin_approve(req: MarketplaceApproveRequest):
    """Admin-only: approve or reject a pending marketplace item."""
    if req.admin_id != ADMIN_USER_ID:
        raise HTTPException(403, "Admin only")
    if req.action not in ("approve", "reject"):
        raise HTTPException(400, "Action must be 'approve' or 'reject'")

    new_status = "approved" if req.action == "approve" else "rejected"
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            UPDATE marketplace_items
               SET status = $1,
                   approved_at = CASE WHEN $1 = 'approved' THEN CURRENT_TIMESTAMP ELSE approved_at END
             WHERE id = $2
         RETURNING id, title, seller_id, status
        """, new_status, req.item_id)
    if not row:
        raise HTTPException(404, "Item not found")
    print(f"[Marketplace] Admin {req.admin_id} {req.action}d item #{row['id']}")
    return {"ok": True, "item_id": row["id"], "status": row["status"], "title": row["title"]}


@app.get("/api/marketplace/admin/pending")
async def marketplace_admin_pending(admin_id: int, limit: int = Query(100, le=500)):
    """Admin-only: list all pending items waiting for approval."""
    if admin_id != ADMIN_USER_ID:
        raise HTTPException(403, "Admin only")
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT mi.id, mi.seller_id, mi.title, mi.description, mi.price, mi.currency,
                   mi.image_url, mi.category, mi.stock, mi.created_at,
                   COALESCE(wu.username, wu.first_name, '') AS seller_name
              FROM marketplace_items mi
              LEFT JOIN web_users wu ON wu.telegram_id = mi.seller_id
             WHERE mi.status = 'pending'
             ORDER BY mi.created_at ASC
             LIMIT $1
        """, limit)
    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "seller_id": r["seller_id"],
            "seller_name": r["seller_name"] or f"user{r['seller_id']}",
            "title": r["title"],
            "description": r["description"] or "",
            "price": float(r["price"]),
            "currency": r["currency"],
            "image_url": r["image_url"] or "",
            "category": r["category"],
            "stock": r["stock"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        })
    return {"items": items, "count": len(items)}


@app.get("/api/marketplace/stats")
async def marketplace_stats():
    """Public stats about the marketplace."""
    async with pool.acquire() as conn:
        total_items = await conn.fetchval("SELECT COUNT(*) FROM marketplace_items WHERE status='approved'") or 0
        total_orders = await conn.fetchval("SELECT COUNT(*) FROM marketplace_orders") or 0
        total_volume = await conn.fetchval("SELECT COALESCE(SUM(total_price), 0) FROM marketplace_orders WHERE status='completed'") or 0
        active_sellers = await conn.fetchval("SELECT COUNT(DISTINCT seller_id) FROM marketplace_items WHERE status='approved'") or 0
    return {
        "total_items": int(total_items),
        "total_orders": int(total_orders),
        "total_volume": float(total_volume),
        "active_sellers": int(active_sellers),
    }


@app.get("/api/admin/activity")
async def admin_activity(limit: int = Query(20, le=100)):
    """Recent activity across the ecosystem"""
    activities = []
    async with pool.acquire() as conn:
        # Recent logins
        try:
            logins = await conn.fetch(
                "SELECT telegram_id, username, first_name, last_login FROM web_users ORDER BY last_login DESC LIMIT $1",
                limit // 2
            )
            for r in logins:
                name = r["username"] or r["first_name"] or str(r["telegram_id"])
                activities.append({
                    "type": "login",
                    "icon": "👤",
                    "text": f"User @{name} logged in",
                    "time": r["last_login"].isoformat() if r["last_login"] else ""
                })
        except Exception:
            pass

        # Recent premium payments
        try:
            payments = await conn.fetch(
                "SELECT user_id, amount, payment_status, created_at FROM premium_users ORDER BY created_at DESC LIMIT $1",
                limit // 2
            )
            for r in payments:
                status = "approved" if r["payment_status"] == "approved" else "pending"
                activities.append({
                    "type": "payment",
                    "icon": "💰",
                    "text": f"Premium payment ({status}): {r['amount']} from user #{r['user_id']}",
                    "time": r["created_at"].isoformat() if r["created_at"] else ""
                })
        except Exception:
            pass

    # Sort by time
    activities.sort(key=lambda x: x.get("time", ""), reverse=True)
    return activities[:limit]
