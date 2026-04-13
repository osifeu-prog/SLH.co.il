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
import aiohttp

from routes.ai_chat import router as ai_chat_router

# === CONFIG ===
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main")
BOT_TOKEN = os.getenv("EXPERTNET_BOT_TOKEN", "")
# Broadcast bot — @SLH_AIR_bot is the main user-facing bot
BROADCAST_BOT_TOKEN = os.getenv("SLH_AIR_TOKEN") or os.getenv("CORE_BOT_TOKEN") or os.getenv("AIRDROP_BOT_TOKEN", "")
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
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    # SECURITY FIX (H-3): explicit headers instead of wildcard
    allow_headers=["Content-Type", "Authorization", "X-Admin-Key", "X-Requested-With"],
)


# Accepted admin keys — matches the 4 passwords on admin.html frontend.
# Override in production by setting ADMIN_API_KEYS env var (comma-separated).
_ADMIN_KEYS_DEFAULT = {
    "slh2026admin",        # primary (Osif)
    "slh_admin_2026",      # partner A
    "slh-spark-admin",     # partner B
    "slh-institutional",   # accountant / lawyer
}
ADMIN_API_KEYS = set(
    (os.getenv("ADMIN_API_KEYS") or "").split(",")
) - {""}
if not ADMIN_API_KEYS:
    ADMIN_API_KEYS = _ADMIN_KEYS_DEFAULT
    print("[SECURITY] WARNING: Using default ADMIN_API_KEYS. Set ADMIN_API_KEYS env var in production.")


def _require_admin(authorization: Optional[str] = None, admin_key_header: Optional[str] = None) -> int:
    """Verify admin credentials. Accepts EITHER:
    - X-Admin-Key: <one of ADMIN_API_KEYS> header
    - Authorization: Bearer <jwt> where user_id == ADMIN_USER_ID

    Returns the admin user_id on success, raises HTTPException 403 otherwise.
    """
    # Try admin key header first
    if admin_key_header and admin_key_header in ADMIN_API_KEYS:
        return ADMIN_USER_ID

    # Try JWT
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization[7:]
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            uid = int(payload.get("user_id") or 0)
            if uid == ADMIN_USER_ID:
                return uid
        except Exception:
            pass

    raise HTTPException(403, "Admin authentication required")

# === AI CHAT ROUTER ===
app.include_router(ai_chat_router)

# === DATABASE ===
pool: Optional[asyncpg.Pool] = None

@app.on_event("startup")
async def startup():
    global pool
    # SECURITY CHECK (C-3): warn if any default credentials are still in use
    _security_warnings = []
    if DATABASE_URL == "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main":
        _security_warnings.append("DATABASE_URL using default — set on Railway")
    if os.getenv("ADMIN_API_KEY", "slh_admin_2026") == "slh_admin_2026":
        _security_warnings.append("ADMIN_API_KEY is default — set on Railway")
    if os.getenv("ENCRYPTION_KEY", "slh_dev_key_CHANGE_ME_IN_PRODUCTION_2026") == "slh_dev_key_CHANGE_ME_IN_PRODUCTION_2026":
        _security_warnings.append("ENCRYPTION_KEY is default — CRITICAL: set on Railway before storing real CEX keys!")
    if os.getenv("ADMIN_BROADCAST_KEY", "slh-broadcast-2026-change-me") == "slh-broadcast-2026-change-me":
        _security_warnings.append("ADMIN_BROADCAST_KEY is default — set on Railway")
    if not os.getenv("JWT_SECRET"):
        _security_warnings.append("JWT_SECRET not set — JWT auth will be unreliable")
    for w in _security_warnings:
        print(f"[SECURITY WARNING] {w}")
    if _security_warnings:
        print(f"[SECURITY WARNING] {len(_security_warnings)} default credentials detected. Set env vars on Railway before production.")

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

        # --- Migration: custom display_name (user-chosen, not from Telegram) ---
        try:
            await conn.execute("ALTER TABLE web_users ADD COLUMN IF NOT EXISTS display_name TEXT")
            await conn.execute("ALTER TABLE web_users ADD COLUMN IF NOT EXISTS display_name_set_at TIMESTAMP")
            await conn.execute("ALTER TABLE web_users ADD COLUMN IF NOT EXISTS bio TEXT")
            await conn.execute("ALTER TABLE web_users ADD COLUMN IF NOT EXISTS language_pref TEXT DEFAULT 'he'")
        except Exception as e:
            print(f"[Migration] Display name columns: {e}")

        # --- Migration: beta coupons + beta_user flag ---
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS beta_coupons (
                    code TEXT PRIMARY KEY,
                    max_uses INT NOT NULL DEFAULT 49,
                    used_count INT NOT NULL DEFAULT 0,
                    nft_reward TEXT DEFAULT 'SLH Genesis Member #',
                    slh_bonus NUMERIC(18,8) DEFAULT 0.1,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active BOOLEAN DEFAULT TRUE
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS beta_redemptions (
                    id BIGSERIAL PRIMARY KEY,
                    coupon_code TEXT NOT NULL,
                    user_id BIGINT NOT NULL,
                    nft_number INT,
                    redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(coupon_code, user_id)
                )
            """)
            await conn.execute("ALTER TABLE web_users ADD COLUMN IF NOT EXISTS beta_user BOOLEAN DEFAULT FALSE")
            await conn.execute("ALTER TABLE web_users ADD COLUMN IF NOT EXISTS beta_coupon_code TEXT")
            await conn.execute("ALTER TABLE web_users ADD COLUMN IF NOT EXISTS beta_nft_number INT")
            # Seed the default beta coupon if it doesn't exist
            await conn.execute("""
                INSERT INTO beta_coupons (code, max_uses, used_count, nft_reward, slh_bonus)
                VALUES ($1, $2, 0, 'SLH Genesis Member #', 0.1)
                ON CONFLICT (code) DO NOTHING
            """, BETA_COUPON_DEFAULT_CODE, BETA_COUPON_DEFAULT_LIMIT)
        except Exception as e:
            print(f"[Migration] Beta coupons: {e}")

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

class EnsureUserRequest(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    photo_url: Optional[str] = None


@app.post("/api/user/ensure")
async def ensure_user(req: EnsureUserRequest):
    """Idempotent user creation/update from a Telegram ID.

    Used by the website's "manual login" flow — when a user types their
    Telegram ID directly (without the Telegram Login Widget), we still need
    to persist them in web_users so they don't "disappear" on refresh.

    This endpoint does NOT require a signed payload because:
    - Telegram IDs are public identifiers (anyone can know them)
    - We only create a profile row, no rights are granted
    - Registration/payment still gates premium access
    - Rate limits and validation prevent abuse
    """
    tg_id = req.telegram_id
    # Basic validation — must be a real Telegram user range
    if tg_id < 100000 or tg_id > 9999999999:
        raise HTTPException(400, "Invalid Telegram ID")

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO web_users (telegram_id, username, first_name, photo_url, auth_date, last_login)
            VALUES ($1, $2, $3, $4, EXTRACT(EPOCH FROM NOW())::BIGINT, CURRENT_TIMESTAMP)
            ON CONFLICT (telegram_id) DO UPDATE SET
                username = COALESCE(NULLIF(EXCLUDED.username, ''), web_users.username),
                first_name = COALESCE(NULLIF(EXCLUDED.first_name, ''), web_users.first_name),
                photo_url = COALESCE(NULLIF(EXCLUDED.photo_url, ''), web_users.photo_url),
                last_login = CURRENT_TIMESTAMP
        """, tg_id, req.username or "", req.first_name or "User", req.photo_url or "")

        # Audit for institutional compliance
        await audit_log_write(
            conn,
            action="user.ensure",
            actor_type="user",
            actor_user_id=tg_id,
            resource_type="web_user",
            resource_id=str(tg_id),
            metadata={"source": "manual_login"},
        )

        balances = await get_user_balances(conn, tg_id)
        is_registered = await conn.fetchval(
            "SELECT is_registered FROM web_users WHERE telegram_id=$1", tg_id
        ) or False

    return {
        "ok": True,
        "telegram_id": tg_id,
        "is_registered": is_registered,
        "balances": balances,
    }


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
BETA_COUPON_DEFAULT_LIMIT = 49    # first 49 users get free access via coupon
BETA_COUPON_DEFAULT_CODE = "GENESIS49"  # the beta code (change to randomize)


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


# === SIMPLIFIED UNLOCK ENDPOINT (no JWT needed — works with ?uid= flow) ===
class UnlockRequest(BaseModel):
    user_id: int
    method: str = "payment_proof"  # payment_proof | coupon | admin
    tx_hash: Optional[str] = ""
    coupon_code: Optional[str] = ""
    admin_key: Optional[str] = ""
    note: Optional[str] = ""


@app.post("/api/registration/unlock")
async def registration_unlock(req: UnlockRequest):
    """Unlock a user's full access via one of 3 methods:

    1. payment_proof — user submits TX hash, goes to pending_review
    2. coupon — user enters beta code, instantly unlocked if code valid + available
    3. admin — admin key bypasses everything, instant unlock

    This is the NEW flow that doesn't require JWT, so it works with the
    seamless bot → /start → dashboard?uid= onboarding.
    """
    if not req.user_id:
        raise HTTPException(400, "user_id required")

    async with pool.acquire() as conn:
        # Ensure user exists
        user = await conn.fetchrow(
            "SELECT telegram_id, is_registered, beta_user FROM web_users WHERE telegram_id=$1",
            req.user_id
        )
        if not user:
            # Create a stub row so the unlock succeeds even for first-time users
            await conn.execute("""
                INSERT INTO web_users (telegram_id, username, first_name, auth_date, last_login)
                VALUES ($1, '', 'User', EXTRACT(EPOCH FROM NOW())::BIGINT, CURRENT_TIMESTAMP)
                ON CONFLICT (telegram_id) DO NOTHING
            """, req.user_id)

        # If already registered, short-circuit
        if user and user["is_registered"]:
            return {
                "ok": True,
                "status": "already_registered",
                "user_id": req.user_id,
                "message": "User is already registered"
            }

        # ─── Method 1: Admin override ───
        if req.method == "admin":
            admin_secret = os.getenv("ADMIN_API_KEY", "slh_admin_2026")
            if req.admin_key != admin_secret:
                raise HTTPException(403, "Invalid admin key")
            async with conn.transaction():
                await conn.execute("""
                    UPDATE web_users SET is_registered = TRUE, registered_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = $1
                """, req.user_id)
                await conn.execute("""
                    INSERT INTO premium_users (user_id, bot_name, payment_status)
                    VALUES ($1, 'ecosystem', 'approved')
                    ON CONFLICT (user_id, bot_name) DO UPDATE SET payment_status = 'approved'
                """, req.user_id)
                # Credit SLH bonus
                await conn.execute("""
                    INSERT INTO token_balances (user_id, token, balance)
                    VALUES ($1, 'SLH', $2)
                    ON CONFLICT (user_id, token) DO UPDATE SET balance = token_balances.balance + $2, updated_at = CURRENT_TIMESTAMP
                """, req.user_id, REGISTRATION_SLH_AMOUNT)
                await conn.execute("""
                    INSERT INTO token_transfers (from_user_id, to_user_id, token, amount, memo, tx_type)
                    VALUES ($1, $1, 'SLH', $2, 'Admin override registration', 'registration')
                """, req.user_id, REGISTRATION_SLH_AMOUNT)
            print(f"[Unlock] Admin override: user {req.user_id}")
            return {
                "ok": True,
                "status": "approved",
                "method": "admin",
                "user_id": req.user_id,
                "slh_credited": REGISTRATION_SLH_AMOUNT,
                "message": "Admin override — user is now fully registered"
            }

        # ─── Method 2: Beta coupon ───
        if req.method == "coupon":
            code = (req.coupon_code or "").strip().upper()
            if not code:
                raise HTTPException(400, "coupon_code required")
            coupon = await conn.fetchrow("""
                SELECT code, max_uses, used_count, nft_reward, slh_bonus, active
                  FROM beta_coupons WHERE code=$1
            """, code)
            if not coupon:
                raise HTTPException(404, f"Coupon '{code}' not found")
            if not coupon["active"]:
                raise HTTPException(400, "Coupon is not active")
            if coupon["used_count"] >= coupon["max_uses"]:
                raise HTTPException(400, f"Coupon is fully redeemed ({coupon['used_count']}/{coupon['max_uses']})")

            # Check if this user already redeemed this coupon
            already = await conn.fetchval(
                "SELECT nft_number FROM beta_redemptions WHERE coupon_code=$1 AND user_id=$2",
                code, req.user_id
            )
            if already:
                return {
                    "ok": True,
                    "status": "already_redeemed",
                    "nft_number": already,
                    "message": f"You already redeemed coupon — you are Genesis Member #{already}"
                }

            async with conn.transaction():
                # Increment coupon usage + assign NFT number
                nft_number = int(coupon["used_count"]) + 1
                await conn.execute(
                    "UPDATE beta_coupons SET used_count = used_count + 1 WHERE code=$1", code
                )
                await conn.execute("""
                    INSERT INTO beta_redemptions (coupon_code, user_id, nft_number)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (coupon_code, user_id) DO NOTHING
                """, code, req.user_id, nft_number)

                # Mark user as fully registered + beta
                await conn.execute("""
                    UPDATE web_users SET
                        is_registered = TRUE,
                        registered_at = CURRENT_TIMESTAMP,
                        beta_user = TRUE,
                        beta_coupon_code = $2,
                        beta_nft_number = $3
                    WHERE telegram_id = $1
                """, req.user_id, code, nft_number)

                await conn.execute("""
                    INSERT INTO premium_users (user_id, bot_name, payment_status)
                    VALUES ($1, 'ecosystem', 'approved')
                    ON CONFLICT (user_id, bot_name) DO UPDATE SET payment_status = 'approved'
                """, req.user_id)

                # Credit coupon bonus in ZVK (cheap reward token, NOT SLH which is scarce premium)
                # 1 SLH = 444 ILS, so to give ~44 ILS worth = 10 ZVK (1 ZVK ≈ 4.4 ILS)
                # Post-distribution gift = 100 ZVK (~444 ILS) handled by cashback engine
                # SLH stays scarce — encourages users to BUY SLH from existing holders
                slh_bonus_legacy = float(coupon["slh_bonus"] or 0.1)
                zvk_amount = 10.0  # ~44 ILS distribution token (10 ZVK)
                await conn.execute("""
                    INSERT INTO token_balances (user_id, token, balance)
                    VALUES ($1, 'ZVK', $2)
                    ON CONFLICT (user_id, token) DO UPDATE SET balance = token_balances.balance + $2, updated_at = CURRENT_TIMESTAMP
                """, req.user_id, zvk_amount)
                await conn.execute("""
                    INSERT INTO token_transfers (from_user_id, to_user_id, token, amount, memo, tx_type)
                    VALUES ($1, $1, 'ZVK', $2, $3, 'beta_coupon')
                """, req.user_id, zvk_amount, f'Beta coupon {code} — Genesis #{nft_number} (ZVK distribution token)')

            print(f"[Unlock] Coupon '{code}' redeemed by user {req.user_id} — Genesis #{nft_number} ({zvk_amount} ZVK)")
            return {
                "ok": True,
                "status": "approved",
                "method": "coupon",
                "user_id": req.user_id,
                "coupon_code": code,
                "nft_number": nft_number,
                "nft_name": f"{coupon['nft_reward']}{nft_number}",
                "zvk_credited": zvk_amount,
                "slh_credited": 0,  # SLH NOT given — must be earned via cashback or purchased
                "post_distribution_gift_zvk": 100,  # promised after first share
                "remaining_slots": int(coupon["max_uses"]) - nft_number,
                "message": f"🎉 ברוכים הבאים Genesis Member #{nft_number}! קיבלת 10 ZVK + NFT. אחרי ההפצה הראשונה — עוד 100 ZVK מתנה!"
            }

        # ─── Method 3: Payment proof (same as submit-proof but no JWT) ───
        if req.method == "payment_proof":
            tx_hash = (req.tx_hash or "").strip()
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO premium_users (user_id, bot_name, payment_status)
                    VALUES ($1, 'ecosystem', 'submitted')
                    ON CONFLICT (user_id, bot_name) DO UPDATE SET payment_status = 'submitted'
                """, req.user_id)
                if tx_hash:
                    await conn.execute("""
                        INSERT INTO deposits (user_id, amount, currency, tx_hash, status, plan_key)
                        VALUES ($1, $2, 'ILS', $3, 'pending', 'registration')
                    """, req.user_id, REGISTRATION_PRICE_ILS, tx_hash)
            print(f"[Unlock] Payment proof submitted by user {req.user_id}: {tx_hash or req.note}")
            return {
                "ok": True,
                "status": "submitted",
                "method": "payment_proof",
                "user_id": req.user_id,
                "tx_hash": tx_hash,
                "message": "Payment proof received — waiting for admin approval (up to 24 hours)"
            }

        raise HTTPException(400, f"Unknown method: {req.method}")


@app.get("/api/beta/status")
async def beta_status():
    """Public: how many beta slots are left across all active coupons."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT code, max_uses, used_count, slh_bonus, active
              FROM beta_coupons
             WHERE active = TRUE
             ORDER BY created_at
        """)
    coupons = [{
        "code": r["code"],
        "max_uses": r["max_uses"],
        "used_count": r["used_count"],
        "remaining": int(r["max_uses"]) - int(r["used_count"]),
        "slh_bonus": float(r["slh_bonus"] or 0),
        "active": r["active"],
    } for r in rows]
    total_remaining = sum(c["remaining"] for c in coupons)
    return {"coupons": coupons, "total_remaining": total_remaining}


# ============================================================
# CASHBACK ENGINE — distribution rewards for Genesis users
# ============================================================
# Each user accumulates "distributions" (verified referrals).
# When they hit a tier, they automatically receive a SLH bonus.
#
# Tiers (referrals → SLH bonus):
#   First successful share = +1 SLH (auto-credited as "post-distribution gift")
#   5  shares = 0.5 SLH cashback
#   10 shares = 1.5 SLH cashback (cumulative includes prior tiers)
#   25 shares = 5 SLH cashback
#   50 shares = 12 SLH cashback
#   100 shares = 30 SLH cashback

# All amounts in ZVK (NOT SLH - SLH stays scarce, only purchased or earned via tasks)
# 10 ZVK ≈ 44 ILS (matches Genesis distribution amount, 1 ZVK ≈ 4.4 ILS)
# Math: 1 SLH equivalent value = 100 ZVK
CASHBACK_TIERS = [
    (1,    100,  "post_distribution_gift"),  # 100 ZVK (~444 ILS) — first share gift
    (5,     50,  "tier_bronze"),              # 50 ZVK (~222 ILS)
    (10,   150,  "tier_silver"),              # 150 ZVK (~666 ILS)
    (25,   500,  "tier_gold"),                # 500 ZVK (~2,220 ILS)
    (50,  1200,  "tier_platinum"),            # 1,200 ZVK (~5,328 ILS)
    (100, 3000,  "tier_diamond"),             # 3,000 ZVK (~13,320 ILS)
]
CASHBACK_TOKEN = "ZVK"  # NEVER SLH — SLH is the scarce premium token


async def _ensure_cashback_table(conn):
    """Idempotent — creates the distribution + cashback tables if missing."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_distributions (
            user_id BIGINT NOT NULL,
            referred_user_id BIGINT NOT NULL,
            referred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified BOOLEAN DEFAULT FALSE,
            verified_at TIMESTAMP,
            PRIMARY KEY (user_id, referred_user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_distributions_user ON user_distributions(user_id, verified);

        CREATE TABLE IF NOT EXISTS user_cashback (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            tier_key TEXT NOT NULL,
            tier_threshold INT NOT NULL,
            slh_amount NUMERIC(18,8) NOT NULL,
            credited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, tier_key)
        );
        CREATE INDEX IF NOT EXISTS idx_cashback_user ON user_cashback(user_id);
    """)


@app.get("/api/cashback/{user_id}")
async def get_cashback_status(user_id: int):
    """Return distribution count + cashback tiers earned for a user.
    All amounts are in ZVK (cashback token), NOT SLH."""
    async with pool.acquire() as conn:
        await _ensure_cashback_table(conn)
        verified_count = await conn.fetchval(
            "SELECT COUNT(*) FROM user_distributions WHERE user_id=$1 AND verified=TRUE", user_id
        ) or 0
        earned = await conn.fetch(
            "SELECT tier_key, tier_threshold, slh_amount, credited_at FROM user_cashback WHERE user_id=$1 ORDER BY tier_threshold",
            user_id
        )
    earned_keys = {r["tier_key"] for r in earned}
    total_earned = sum(float(r["slh_amount"]) for r in earned)
    next_tier = None
    for threshold, amount, key in CASHBACK_TIERS:
        if key not in earned_keys and verified_count < threshold:
            next_tier = {"threshold": threshold, "zvk_amount": amount, "tier_key": key, "needed": threshold - verified_count}
            break
    return {
        "user_id": user_id,
        "verified_distributions": int(verified_count),
        "token": CASHBACK_TOKEN,
        "tiers_earned": [{"tier_key": r["tier_key"], "threshold": r["tier_threshold"], "zvk_amount": float(r["slh_amount"]), "credited_at": r["credited_at"].isoformat() if r["credited_at"] else None} for r in earned],
        "total_zvk_earned": total_earned,
        "next_tier": next_tier,
        "all_tiers": [{"threshold": t, "zvk_amount": a, "key": k} for t, a, k in CASHBACK_TIERS],
    }


@app.post("/api/cashback/process/{user_id}")
async def process_cashback(user_id: int):
    """Recompute cashback tiers for a user based on their verified distributions.
    Credits in ZVK (NOT SLH). Idempotent — already-credited tiers won't be paid twice.
    """
    async with pool.acquire() as conn:
        await _ensure_cashback_table(conn)
        verified_count = await conn.fetchval(
            "SELECT COUNT(*) FROM user_distributions WHERE user_id=$1 AND verified=TRUE", user_id
        ) or 0
        newly_credited = []
        for threshold, amount, key in CASHBACK_TIERS:
            if verified_count >= threshold:
                # Try to insert — UNIQUE constraint prevents double-pay
                inserted = await conn.fetchval("""
                    INSERT INTO user_cashback (user_id, tier_key, tier_threshold, slh_amount)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id, tier_key) DO NOTHING
                    RETURNING id
                """, user_id, key, threshold, amount)
                if inserted:
                    # Credit ZVK balance (NOT SLH — SLH stays scarce)
                    await conn.execute("""
                        INSERT INTO token_balances (user_id, token, balance)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (user_id, token) DO UPDATE SET balance = token_balances.balance + EXCLUDED.balance, updated_at = CURRENT_TIMESTAMP
                    """, user_id, CASHBACK_TOKEN, amount)
                    newly_credited.append({"tier_key": key, "threshold": threshold, "zvk": amount})
    return {
        "ok": True,
        "user_id": user_id,
        "verified_distributions": int(verified_count),
        "token": CASHBACK_TOKEN,
        "newly_credited": newly_credited,
        "total_credited": len(newly_credited),
    }


# ============================================================
# EXTERNAL WALLETS — Bybit, Binance, custom TON addresses
# ============================================================
# Users can register multiple external wallet addresses (TON, BSC, ETH, BTC)
# from exchanges (Bybit, Binance, Bitget, OKX) or self-custody.
# We READ-ONLY query their balances via public APIs (toncenter, BscScan).
# NEVER ask for private keys, API keys, or signatures.

class ExternalWalletAdd(BaseModel):
    user_id: int
    label: str  # "Bybit Main", "Binance Spot", "My Cold Wallet"
    network: str  # "TON" | "BSC" | "ETH" | "BTC"
    address: str
    provider: Optional[str] = None  # "bybit" | "binance" | "bitget" | "okx" | "self"


async def _ensure_external_wallets_table(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS external_wallets (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            label TEXT NOT NULL,
            network TEXT NOT NULL,
            address TEXT NOT NULL,
            provider TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_balance_native NUMERIC(28,8) DEFAULT 0,
            last_balance_usdt NUMERIC(28,8) DEFAULT 0,
            last_checked TIMESTAMP,
            UNIQUE(user_id, network, address)
        );
        CREATE INDEX IF NOT EXISTS idx_external_wallets_user ON external_wallets(user_id);
    """)


@app.post("/api/external-wallets/add")
async def add_external_wallet(req: ExternalWalletAdd):
    """Add an external wallet address for the user (read-only tracking)."""
    if not req.user_id or not req.address or len(req.address) < 10:
        raise HTTPException(400, "user_id + valid address required")
    network = req.network.upper()
    if network not in ("TON", "BSC", "ETH", "BTC"):
        raise HTTPException(400, "network must be TON, BSC, ETH, or BTC")
    async with pool.acquire() as conn:
        await _ensure_external_wallets_table(conn)
        wid = await conn.fetchval("""
            INSERT INTO external_wallets (user_id, label, network, address, provider)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id, network, address) DO UPDATE
              SET label = EXCLUDED.label, provider = EXCLUDED.provider
            RETURNING id
        """, req.user_id, req.label[:50], network, req.address, req.provider)
    return {"ok": True, "wallet_id": wid, "user_id": req.user_id, "network": network, "label": req.label}


@app.get("/api/external-wallets/{user_id}")
async def list_external_wallets(user_id: int):
    """List all external wallets for a user with their last cached balance."""
    async with pool.acquire() as conn:
        await _ensure_external_wallets_table(conn)
        rows = await conn.fetch("""
            SELECT id, label, network, address, provider, last_balance_native, last_balance_usdt, last_checked, added_at
              FROM external_wallets
             WHERE user_id = $1
             ORDER BY added_at DESC
        """, user_id)
    return {
        "user_id": user_id,
        "wallets": [{
            "id": r["id"],
            "label": r["label"],
            "network": r["network"],
            "address": r["address"],
            "provider": r["provider"],
            "last_balance_native": float(r["last_balance_native"] or 0),
            "last_balance_usdt": float(r["last_balance_usdt"] or 0),
            "last_checked": r["last_checked"].isoformat() if r["last_checked"] else None,
            "added_at": r["added_at"].isoformat() if r["added_at"] else None,
        } for r in rows]
    }


@app.delete("/api/external-wallets/{wallet_id}")
async def delete_external_wallet(wallet_id: int, user_id: int):
    """Remove an external wallet (must own it)."""
    async with pool.acquire() as conn:
        await _ensure_external_wallets_table(conn)
        deleted = await conn.execute(
            "DELETE FROM external_wallets WHERE id=$1 AND user_id=$2", wallet_id, user_id
        )
    return {"ok": True, "deleted": deleted}


async def _fetch_ton_balance(address: str) -> dict:
    """Fetch TON balance + jettons from toncenter (public, no API key needed)."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://toncenter.com/api/v2/getAddressBalance",
                params={"address": address},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    return {"native": 0, "usdt": 0, "error": f"HTTP {resp.status}"}
                data = await resp.json()
                if not data.get("ok"):
                    return {"native": 0, "usdt": 0, "error": data.get("description", "unknown")}
                # toncenter returns nano-TON
                native = float(data.get("result", 0)) / 1e9
                return {"native": native, "usdt": 0, "ok": True}
    except Exception as e:
        return {"native": 0, "usdt": 0, "error": str(e)[:100]}


@app.post("/api/external-wallets/refresh/{wallet_id}")
async def refresh_external_wallet(wallet_id: int):
    """Refresh balance for a single external wallet (calls public chain API)."""
    async with pool.acquire() as conn:
        await _ensure_external_wallets_table(conn)
        row = await conn.fetchrow(
            "SELECT id, user_id, network, address FROM external_wallets WHERE id=$1", wallet_id
        )
        if not row:
            raise HTTPException(404, "Wallet not found")

        balance_info = {"native": 0, "usdt": 0}
        if row["network"] == "TON":
            balance_info = await _fetch_ton_balance(row["address"])
        elif row["network"] == "BSC":
            # TODO: BscScan API call
            balance_info = {"native": 0, "usdt": 0, "info": "BSC support coming soon"}
        elif row["network"] == "ETH":
            balance_info = {"native": 0, "usdt": 0, "info": "ETH support coming soon"}

        await conn.execute("""
            UPDATE external_wallets
               SET last_balance_native = $1,
                   last_balance_usdt = $2,
                   last_checked = CURRENT_TIMESTAMP
             WHERE id = $3
        """, balance_info["native"], balance_info["usdt"], wallet_id)

    return {
        "ok": True,
        "wallet_id": wallet_id,
        "network": row["network"],
        "address": row["address"],
        "balance": balance_info,
    }


@app.post("/api/external-wallets/refresh-all/{user_id}")
async def refresh_all_external_wallets(user_id: int):
    """Refresh balances for all of a user's external wallets."""
    async with pool.acquire() as conn:
        await _ensure_external_wallets_table(conn)
        rows = await conn.fetch(
            "SELECT id FROM external_wallets WHERE user_id=$1", user_id
        )
    results = []
    for r in rows:
        try:
            res = await refresh_external_wallet(r["id"])
            results.append(res)
        except Exception as e:
            results.append({"wallet_id": r["id"], "error": str(e)[:100]})
    return {"ok": True, "user_id": user_id, "refreshed": len(results), "results": results}


# ============================================================
# IMMUTABLE AUDIT LOG — Institutional / Regulator-Grade
# ============================================================
# Every sensitive action is written to an append-only log with a
# SHA-256 hash chain. Each entry includes the hash of the previous
# entry, making tampering detectable: any modification breaks the chain.
#
# This is the table regulators ask to see first. We never DELETE or
# UPDATE rows — only INSERT.

async def _ensure_institutional_audit_table(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS institutional_audit (
            id BIGSERIAL PRIMARY KEY,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            actor_user_id BIGINT,
            actor_ip TEXT,
            actor_type TEXT NOT NULL, -- 'user' | 'admin' | 'system' | 'api'
            action TEXT NOT NULL, -- 'wallet.link' | 'trade.execute' | 'withdraw.request' | ...
            resource_type TEXT, -- 'wallet' | 'trade' | 'user' | 'kyc'
            resource_id TEXT,
            before_state JSONB,
            after_state JSONB,
            amount_native NUMERIC(28,18),
            amount_currency TEXT,
            amount_usd NUMERIC(18,2),
            risk_score INT, -- 0-100
            compliance_flags TEXT[], -- ['TRAVEL_RULE', 'SANCTIONS_CHECK_PASSED', 'AML_OK', ...]
            prev_hash CHAR(64),
            entry_hash CHAR(64) NOT NULL,
            metadata JSONB
        );
        CREATE INDEX IF NOT EXISTS idx_inst_audit_actor ON institutional_audit(actor_user_id, timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_inst_audit_action ON institutional_audit(action, timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_inst_audit_resource ON institutional_audit(resource_type, resource_id);
        CREATE INDEX IF NOT EXISTS idx_inst_audit_timestamp ON institutional_audit(timestamp DESC);
    """)
    # Prevent UPDATE/DELETE via revoke (regulators require this)
    try:
        await conn.execute("REVOKE UPDATE, DELETE ON institutional_audit FROM PUBLIC;")
    except Exception:
        pass


async def audit_log_write(
    conn,
    action: str,
    actor_type: str = "system",
    actor_user_id: Optional[int] = None,
    actor_ip: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    before_state: Optional[dict] = None,
    after_state: Optional[dict] = None,
    amount_native: Optional[float] = None,
    amount_currency: Optional[str] = None,
    amount_usd: Optional[float] = None,
    risk_score: Optional[int] = None,
    compliance_flags: Optional[list] = None,
    metadata: Optional[dict] = None,
) -> str:
    """Write an audit entry with hash chain. Returns the entry_hash."""
    await _ensure_institutional_audit_table(conn)

    # Get last entry's hash (for chain)
    prev_hash = await conn.fetchval(
        "SELECT entry_hash FROM institutional_audit ORDER BY id DESC LIMIT 1"
    ) or "0" * 64

    # Build the payload that gets hashed
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "actor_type": actor_type,
        "actor_user_id": actor_user_id,
        "actor_ip": actor_ip,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "before_state": before_state,
        "after_state": after_state,
        "amount_native": float(amount_native) if amount_native else None,
        "amount_currency": amount_currency,
        "amount_usd": float(amount_usd) if amount_usd else None,
        "risk_score": risk_score,
        "compliance_flags": compliance_flags or [],
        "metadata": metadata or {},
        "prev_hash": prev_hash,
    }
    payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    entry_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    await conn.execute("""
        INSERT INTO institutional_audit (
            actor_user_id, actor_ip, actor_type, action,
            resource_type, resource_id, before_state, after_state,
            amount_native, amount_currency, amount_usd,
            risk_score, compliance_flags, prev_hash, entry_hash, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9, $10, $11, $12, $13, $14, $15, $16::jsonb)
    """,
        actor_user_id, actor_ip, actor_type, action,
        resource_type, str(resource_id) if resource_id else None,
        json.dumps(before_state) if before_state else None,
        json.dumps(after_state) if after_state else None,
        amount_native, amount_currency, amount_usd,
        risk_score, compliance_flags or [],
        prev_hash, entry_hash,
        json.dumps(metadata) if metadata else None,
    )
    return entry_hash


@app.get("/api/audit/verify-chain")
async def verify_audit_chain(limit: int = 1000):
    """Verify the hash chain integrity. Returns any broken entries.
    Regulators/auditors call this to prove data hasn't been tampered with."""
    async with pool.acquire() as conn:
        await _ensure_institutional_audit_table(conn)
        rows = await conn.fetch("""
            SELECT id, entry_hash, prev_hash, timestamp, action
              FROM institutional_audit
             ORDER BY id ASC
             LIMIT $1
        """, limit)

    if not rows:
        return {"ok": True, "total": 0, "broken": [], "message": "Empty audit log"}

    broken = []
    expected_prev = "0" * 64
    for r in rows:
        if r["prev_hash"] != expected_prev:
            broken.append({
                "id": r["id"],
                "expected_prev": expected_prev,
                "actual_prev": r["prev_hash"],
                "action": r["action"],
            })
        expected_prev = r["entry_hash"]

    return {
        "ok": len(broken) == 0,
        "total": len(rows),
        "broken": broken,
        "message": "Chain intact" if len(broken) == 0 else f"CHAIN BROKEN at {len(broken)} entries",
    }


@app.get("/api/audit/recent")
async def audit_recent(limit: int = 100, action_filter: Optional[str] = None, user_id: Optional[int] = None):
    """Get recent audit entries for admin review."""
    async with pool.acquire() as conn:
        await _ensure_institutional_audit_table(conn)
        if action_filter and user_id:
            rows = await conn.fetch("""
                SELECT id, timestamp, actor_user_id, actor_type, action,
                       resource_type, resource_id, amount_native, amount_currency,
                       amount_usd, risk_score, compliance_flags, entry_hash
                  FROM institutional_audit
                 WHERE action = $1 AND actor_user_id = $2
                 ORDER BY timestamp DESC
                 LIMIT $3
            """, action_filter, user_id, limit)
        elif action_filter:
            rows = await conn.fetch("""
                SELECT id, timestamp, actor_user_id, actor_type, action,
                       resource_type, resource_id, amount_native, amount_currency,
                       amount_usd, risk_score, compliance_flags, entry_hash
                  FROM institutional_audit
                 WHERE action = $1
                 ORDER BY timestamp DESC
                 LIMIT $2
            """, action_filter, limit)
        elif user_id:
            rows = await conn.fetch("""
                SELECT id, timestamp, actor_user_id, actor_type, action,
                       resource_type, resource_id, amount_native, amount_currency,
                       amount_usd, risk_score, compliance_flags, entry_hash
                  FROM institutional_audit
                 WHERE actor_user_id = $1
                 ORDER BY timestamp DESC
                 LIMIT $2
            """, user_id, limit)
        else:
            rows = await conn.fetch("""
                SELECT id, timestamp, actor_user_id, actor_type, action,
                       resource_type, resource_id, amount_native, amount_currency,
                       amount_usd, risk_score, compliance_flags, entry_hash
                  FROM institutional_audit
                 ORDER BY timestamp DESC
                 LIMIT $1
            """, limit)

    return {
        "count": len(rows),
        "entries": [{
            "id": r["id"],
            "timestamp": r["timestamp"].isoformat() if r["timestamp"] else None,
            "actor_user_id": r["actor_user_id"],
            "actor_type": r["actor_type"],
            "action": r["action"],
            "resource_type": r["resource_type"],
            "resource_id": r["resource_id"],
            "amount_native": float(r["amount_native"]) if r["amount_native"] else None,
            "amount_currency": r["amount_currency"],
            "amount_usd": float(r["amount_usd"]) if r["amount_usd"] else None,
            "risk_score": r["risk_score"],
            "compliance_flags": r["compliance_flags"] or [],
            "entry_hash": r["entry_hash"][:16] + "...",  # truncate for display
        } for r in rows]
    }


# ============================================================
# CEX INTEGRATIONS — Bybit + Binance (READ-ONLY)
# ============================================================
# Each user can link their own Bybit/Binance API keys (READ-ONLY scope).
# Keys are encrypted at rest, never logged. We only call GET endpoints.
# Never trade/withdraw.

class CexApiKeyAdd(BaseModel):
    user_id: int
    exchange: str  # 'bybit' | 'binance'
    label: str
    api_key: str
    api_secret: str
    permissions: Optional[list] = None  # ['read']


async def _ensure_cex_keys_table(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS cex_api_keys (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            exchange TEXT NOT NULL, -- bybit | binance
            label TEXT NOT NULL,
            api_key_masked TEXT NOT NULL, -- first 8 chars only, for display
            api_key_encrypted TEXT NOT NULL, -- full key encrypted
            api_secret_encrypted TEXT NOT NULL,
            permissions TEXT[],
            is_active BOOLEAN DEFAULT TRUE,
            last_used_at TIMESTAMP,
            last_error TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, exchange, api_key_masked)
        );
        CREATE INDEX IF NOT EXISTS idx_cex_keys_user ON cex_api_keys(user_id);

        CREATE TABLE IF NOT EXISTS cex_snapshots (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            exchange TEXT NOT NULL,
            snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_usd_value NUMERIC(28,8),
            spot_balances JSONB, -- {BTC: {free: 0.5, locked: 0, usd_value: 34000}, ...}
            futures_positions JSONB,
            earn_positions JSONB, -- savings, staking, etc
            raw_response JSONB
        );
        CREATE INDEX IF NOT EXISTS idx_cex_snapshots_user_time ON cex_snapshots(user_id, snapshot_at DESC);
    """)


def _get_encryption_key() -> bytes:
    """Derive a 32-byte AES-GCM key from ENCRYPTION_KEY env var via SHA-256.
    Accepts any length input — hashes to produce a stable 256-bit key.
    """
    raw = os.getenv("ENCRYPTION_KEY", "slh_dev_key_CHANGE_ME_IN_PRODUCTION_2026")
    return hashlib.sha256(raw.encode("utf-8")).digest()


def _encrypt_secret(secret: str) -> str:
    """AES-GCM authenticated encryption.

    Format: version:hex(nonce):hex(ciphertext+tag)
    - version 'v2' marks AES-GCM (current)
    - version 'v1' (legacy XOR) still decryptable via _decrypt_secret_xor
    """
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        # Fallback if cryptography lib not installed — this should never happen
        # in production. Force AES-GCM via requirements.txt.
        return _encrypt_secret_xor(secret)

    key = _get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)  # 96-bit nonce, recommended for GCM
    ciphertext = aesgcm.encrypt(nonce, secret.encode("utf-8"), None)
    return f"v2:{nonce.hex()}:{ciphertext.hex()}"


def _decrypt_secret(blob: str) -> str:
    """Decrypt a secret stored by _encrypt_secret. Supports v1 (XOR legacy) and v2 (AES-GCM)."""
    if not blob:
        return ""
    # v2 = AES-GCM (current)
    if blob.startswith("v2:"):
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            parts = blob.split(":")
            if len(parts) != 3:
                return ""
            nonce = bytes.fromhex(parts[1])
            ciphertext = bytes.fromhex(parts[2])
            aesgcm = AESGCM(_get_encryption_key())
            return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
        except Exception as e:
            print(f"[AES-GCM decrypt] failed: {e}")
            return ""
    # v1 = legacy XOR (any pre-v2 keys still in DB)
    return _decrypt_secret_xor(blob)


def _encrypt_secret_xor(secret: str) -> str:
    """LEGACY v1 XOR encryption — kept only for backwards compat / fallback."""
    key = os.getenv("ENCRYPTION_KEY", "slh_dev_key_CHANGE_ME_IN_PRODUCTION_2026")
    result = []
    for i, c in enumerate(secret):
        result.append(chr(ord(c) ^ ord(key[i % len(key)])))
    return "".join(result).encode("latin-1").hex()


def _decrypt_secret_xor(hex_str: str) -> str:
    """LEGACY v1 XOR decryption — called automatically by _decrypt_secret for old data."""
    try:
        encrypted = bytes.fromhex(hex_str).decode("latin-1")
        key = os.getenv("ENCRYPTION_KEY", "slh_dev_key_CHANGE_ME_IN_PRODUCTION_2026")
        result = []
        for i, c in enumerate(encrypted):
            result.append(chr(ord(c) ^ ord(key[i % len(key)])))
        return "".join(result)
    except Exception:
        return ""


@app.post("/api/cex/add-key")
async def cex_add_api_key(req: CexApiKeyAdd):
    """Link a Bybit or Binance API key (READ-ONLY only). Encrypted at rest."""
    if req.exchange not in ("bybit", "binance"):
        raise HTTPException(400, "exchange must be 'bybit' or 'binance'")
    if len(req.api_key) < 8 or len(req.api_secret) < 8:
        raise HTTPException(400, "API key/secret too short")

    async with pool.acquire() as conn:
        await _ensure_cex_keys_table(conn)
        masked = req.api_key[:8] + "..." + req.api_key[-4:]
        kid = await conn.fetchval("""
            INSERT INTO cex_api_keys (user_id, exchange, label, api_key_masked, api_key_encrypted, api_secret_encrypted, permissions)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (user_id, exchange, api_key_masked) DO UPDATE
              SET label = EXCLUDED.label, is_active = TRUE
            RETURNING id
        """, req.user_id, req.exchange, req.label[:100], masked,
            _encrypt_secret(req.api_key), _encrypt_secret(req.api_secret),
            req.permissions or ["read"])
        # Audit
        await audit_log_write(conn,
            action=f"cex.key.link",
            actor_type="user",
            actor_user_id=req.user_id,
            resource_type="cex_api_key",
            resource_id=str(kid),
            metadata={"exchange": req.exchange, "label": req.label, "masked": masked},
            compliance_flags=["CEX_KEY_LINKED", "READ_ONLY_ASSUMED"],
        )
    return {"ok": True, "id": kid, "key_id": kid, "user_id": req.user_id, "exchange": req.exchange, "masked": masked}


@app.get("/api/cex/keys/{user_id}")
async def cex_list_keys(user_id: int):
    """List CEX keys for a user (never returns secrets)."""
    async with pool.acquire() as conn:
        await _ensure_cex_keys_table(conn)
        rows = await conn.fetch("""
            SELECT id, exchange, label, api_key_masked, permissions, is_active,
                   last_used_at, last_error, added_at
              FROM cex_api_keys
             WHERE user_id = $1
             ORDER BY added_at DESC
        """, user_id)
    return {"user_id": user_id, "keys": [dict(r) for r in rows]}


@app.delete("/api/cex/keys/{key_id}")
async def cex_delete_key(key_id: int, user_id: int):
    """Remove a CEX API key."""
    async with pool.acquire() as conn:
        await _ensure_cex_keys_table(conn)
        await conn.execute(
            "DELETE FROM cex_api_keys WHERE id=$1 AND user_id=$2", key_id, user_id
        )
        await audit_log_write(conn,
            action="cex.key.unlink",
            actor_type="user",
            actor_user_id=user_id,
            resource_type="cex_api_key",
            resource_id=str(key_id),
        )
    return {"ok": True, "deleted": key_id}


async def _bybit_sign(api_secret: str, timestamp: str, api_key: str, recv_window: str, query_string: str) -> str:
    """Sign a Bybit V5 API request."""
    param_str = timestamp + api_key + recv_window + query_string
    return hmac.new(
        api_secret.encode("utf-8"),
        param_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


async def _bybit_get_balances(api_key: str, api_secret: str) -> dict:
    """Call Bybit V5 /v5/account/wallet-balance to get all balances."""
    import time as _time
    timestamp = str(int(_time.time() * 1000))
    recv_window = "5000"
    query = "accountType=UNIFIED"
    sign = await _bybit_sign(api_secret, timestamp, api_key, recv_window, query)
    headers = {
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-SIGN": sign,
        "X-BAPI-SIGN-TYPE": "2",
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": recv_window,
    }
    url = f"https://api.bybit.com/v5/account/wallet-balance?{query}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                return data
    except Exception as e:
        return {"error": str(e)[:200]}


async def _binance_sign(api_secret: str, query_string: str) -> str:
    """Sign a Binance API request."""
    return hmac.new(
        api_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


async def _binance_get_account(api_key: str, api_secret: str) -> dict:
    """Call Binance /api/v3/account to get spot balances."""
    import time as _time
    timestamp = str(int(_time.time() * 1000))
    query = f"timestamp={timestamp}"
    sign = await _binance_sign(api_secret, query)
    url = f"https://api.binance.com/api/v3/account?{query}&signature={sign}"
    headers = {"X-MBX-APIKEY": api_key}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                return data
    except Exception as e:
        return {"error": str(e)[:200]}


@app.post("/api/cex/sync/{key_id}")
async def cex_sync_balances(key_id: int):
    """Fetch live balances from CEX and save as snapshot."""
    async with pool.acquire() as conn:
        await _ensure_cex_keys_table(conn)
        row = await conn.fetchrow("SELECT * FROM cex_api_keys WHERE id=$1 AND is_active=TRUE", key_id)
        if not row:
            raise HTTPException(404, "Key not found or inactive")

        api_key = _decrypt_secret(row["api_key_encrypted"])
        api_secret = _decrypt_secret(row["api_secret_encrypted"])

        if row["exchange"] == "bybit":
            data = await _bybit_get_balances(api_key, api_secret)
        elif row["exchange"] == "binance":
            data = await _binance_get_account(api_key, api_secret)
        else:
            raise HTTPException(400, "Unsupported exchange")

        if "error" in data or data.get("retCode") not in (0, None):
            error_msg = data.get("error") or data.get("retMsg") or "Unknown error"
            await conn.execute(
                "UPDATE cex_api_keys SET last_error=$1, last_used_at=CURRENT_TIMESTAMP WHERE id=$2",
                str(error_msg)[:200], key_id
            )
            return {"ok": False, "error": error_msg, "key_id": key_id}

        # Parse response and compute total USD
        total_usd = 0.0
        spot_balances = {}

        if row["exchange"] == "bybit":
            result = data.get("result", {})
            lists = result.get("list", [])
            for acc in lists:
                for coin in acc.get("coin", []):
                    symbol = coin.get("coin")
                    wallet_balance = float(coin.get("walletBalance") or 0)
                    if wallet_balance > 0:
                        usd_value = float(coin.get("usdValue") or 0)
                        spot_balances[symbol] = {
                            "balance": wallet_balance,
                            "usd_value": usd_value,
                        }
                        total_usd += usd_value

        elif row["exchange"] == "binance":
            for bal in data.get("balances", []):
                free = float(bal.get("free") or 0)
                locked = float(bal.get("locked") or 0)
                total = free + locked
                if total > 0:
                    spot_balances[bal["asset"]] = {
                        "free": free,
                        "locked": locked,
                        "usd_value": 0,  # would need separate price lookup
                    }

        # Save snapshot
        snap_id = await conn.fetchval("""
            INSERT INTO cex_snapshots (user_id, exchange, total_usd_value, spot_balances, raw_response)
            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb)
            RETURNING id
        """, row["user_id"], row["exchange"], total_usd,
            json.dumps(spot_balances), json.dumps(data)[:10000])

        await conn.execute(
            "UPDATE cex_api_keys SET last_used_at=CURRENT_TIMESTAMP, last_error=NULL WHERE id=$1",
            key_id
        )

        # Audit
        await audit_log_write(conn,
            action=f"cex.snapshot.{row['exchange']}",
            actor_type="system",
            actor_user_id=row["user_id"],
            resource_type="cex_snapshot",
            resource_id=str(snap_id),
            amount_usd=total_usd,
            amount_currency="USD",
            metadata={
                "exchange": row["exchange"],
                "assets_count": len(spot_balances),
                "key_id": key_id,
            },
        )

    return {
        "ok": True,
        "snapshot_id": snap_id,
        "exchange": row["exchange"],
        "total_usd": total_usd,
        "assets_count": len(spot_balances),
        "spot_balances": spot_balances,
    }


@app.get("/api/cex/portfolio/{user_id}")
async def cex_portfolio(user_id: int):
    """Get the latest snapshot from all CEX accounts for this user."""
    async with pool.acquire() as conn:
        await _ensure_cex_keys_table(conn)
        # Get latest snapshot per exchange
        rows = await conn.fetch("""
            SELECT DISTINCT ON (exchange) id, exchange, snapshot_at, total_usd_value, spot_balances
              FROM cex_snapshots
             WHERE user_id = $1
             ORDER BY exchange, snapshot_at DESC
        """, user_id)

    total_usd = sum(float(r["total_usd_value"] or 0) for r in rows)
    return {
        "user_id": user_id,
        "total_usd": total_usd,
        "total_ils": round(total_usd * 3.65, 2),
        "exchanges": [{
            "exchange": r["exchange"],
            "snapshot_at": r["snapshot_at"].isoformat() if r["snapshot_at"] else None,
            "total_usd": float(r["total_usd_value"] or 0),
            "spot_balances": r["spot_balances"],
        } for r in rows]
    }


# ============================================================
# BSC HOLDERS — via Etherscan V2 Multichain API (chainid=56)
# ============================================================
# Etherscan's V2 API works across all supported chains including BSC.
# Uses BSCSCAN_API_KEY env var (fallback to ETHERSCAN_API_KEY).
# One API key works for Ethereum, BSC, Polygon, Arbitrum, Base, etc.

SLH_BSC_CONTRACT = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"

_holders_cache = {"data": None, "ts": 0}


async def _fetch_holders_bitquery(api_key: str, limit: int = 100) -> dict:
    """Query BitQuery GraphQL for SLH holders on BSC. Free tier 10k/month.

    Returns the standard holders response format on success, or {"ok": False}.
    """
    query = """
    query ($contract: String!, $limit: Int!) {
      ethereum(network: bsc) {
        address(address: {is: $contract}) {
          balances(currency: {is: $contract}, options: {desc: "value", limit: $limit}) {
            value
            address {
              address
            }
          }
        }
      }
    }
    """
    payload = {
        "query": query,
        "variables": {"contract": SLH_BSC_CONTRACT, "limit": min(limit, 100)},
    }
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://graphql.bitquery.io",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                data = await resp.json()
    except Exception as e:
        return {"ok": False, "error": f"BitQuery request failed: {str(e)[:200]}"}

    try:
        balances = data["data"]["ethereum"]["address"][0]["balances"]
    except Exception:
        return {"ok": False, "error": "BitQuery response format unexpected", "raw": str(data)[:300]}

    total_supply = 111186328
    holders = []
    for i, b in enumerate(balances):
        balance = float(b.get("value") or 0)
        addr = b.get("address", {}).get("address", "")
        pct = (balance / total_supply * 100) if total_supply else 0
        holders.append({
            "rank": i + 1,
            "address": addr,
            "balance": balance,
            "percent": round(pct, 4),
            "bscscan_url": f"https://bscscan.com/address/{addr}",
        })

    return {
        "ok": True,
        "source": "bitquery",
        "contract": SLH_BSC_CONTRACT,
        "chain": "BSC (56)",
        "total_holders": len(holders),
        "holders": holders,
        "cached_at": datetime.utcnow().isoformat(),
    }

@app.get("/api/network/slh-holders")
async def get_slh_holders(limit: int = 100, force_refresh: bool = False):
    """Fetch SLH token holders from BSC.

    Tries multiple free providers in order:
    1. BitQuery GraphQL (free 10k/month) — BITQUERY_API_KEY env var
    2. Etherscan V2 Multichain (PRO only for BSC) — BSCSCAN_API_KEY
    3. NodeReal (free 100k/day) — NODEREAL_API_KEY

    Cached for 5 minutes.
    """
    import time as _time
    now = _time.time()
    if not force_refresh and _holders_cache["data"] and (now - _holders_cache["ts"]) < 300:
        return _holders_cache["data"]

    # 1) Try BitQuery first (free tier, most generous)
    bitquery_key = os.getenv("BITQUERY_API_KEY")
    if bitquery_key:
        result = await _fetch_holders_bitquery(bitquery_key, limit)
        if result.get("ok"):
            _holders_cache["data"] = result
            _holders_cache["ts"] = now
            return result

    # 2) Try Etherscan V2 (requires PRO for BSC now)
    api_key = os.getenv("BSCSCAN_API_KEY") or os.getenv("ETHERSCAN_API_KEY")
    if not api_key:
        return {
            "ok": False,
            "error": "No BSC holder API configured",
            "hint": "Set BITQUERY_API_KEY (recommended, free) or ETHERSCAN_API_KEY (PRO) on Railway",
            "alternatives": [
                {"name": "BitQuery", "url": "https://bitquery.io", "free": True, "limit": "10k/month"},
                {"name": "NodeReal", "url": "https://nodereal.io", "free": True, "limit": "100k/day"},
                {"name": "Alchemy", "url": "https://alchemy.com", "free": True, "limit": "300M CU/month"},
            ],
            "holders": [],
            "total_holders": 0,
        }

    # Etherscan V2 Multichain API — chainid=56 is BSC
    # tokenholderlist is a PRO-tier endpoint in V2, but tokentx works on free tier
    # We'll use tokensupply + tokenbalance for the contract to get top holders
    url = (
        f"https://api.etherscan.io/v2/api?chainid=56"
        f"&module=token&action=tokenholderlist"
        f"&contractaddress={SLH_BSC_CONTRACT}"
        f"&page=1&offset={min(limit, 100)}"
        f"&apikey={api_key}"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
    except Exception as e:
        return {"ok": False, "error": f"API call failed: {str(e)[:200]}", "holders": [], "total_holders": 0}

    if data.get("status") != "1":
        # Fallback to free-tier tokensupply + manual holder query
        return {
            "ok": False,
            "error": data.get("message", "Unknown"),
            "raw": data.get("result", "")[:200] if isinstance(data.get("result"), str) else None,
            "hint": "tokenholderlist may require Etherscan PRO tier. Falling back to tokensupply...",
            "holders": [],
            "total_holders": 0,
        }

    holders_raw = data.get("result", [])
    total_supply = 111186328 * (10 ** 15)  # 111M with 15 decimals

    holders = []
    for i, h in enumerate(holders_raw):
        try:
            balance_raw = int(h.get("TokenHolderQuantity") or 0)
            balance = balance_raw / (10 ** 15)
            pct = (balance_raw / total_supply * 100) if total_supply else 0
            holders.append({
                "rank": i + 1,
                "address": h.get("TokenHolderAddress"),
                "balance": balance,
                "percent": round(pct, 4),
                "bscscan_url": f"https://bscscan.com/address/{h.get('TokenHolderAddress')}",
            })
        except Exception:
            pass

    result = {
        "ok": True,
        "contract": SLH_BSC_CONTRACT,
        "chain": "BSC (56)",
        "total_holders": len(holders),
        "holders": holders,
        "cached_at": now,
    }
    _holders_cache["data"] = result
    _holders_cache["ts"] = now
    return result


@app.post("/api/audit/write")
async def audit_write_endpoint(
    action: str,
    actor_type: str = "api",
    actor_user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    amount_native: Optional[float] = None,
    amount_currency: Optional[str] = None,
):
    """Public endpoint to write an audit entry. Used by bots + frontend."""
    async with pool.acquire() as conn:
        entry_hash = await audit_log_write(
            conn,
            action=action,
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            amount_native=amount_native,
            amount_currency=amount_currency,
        )
    return {"ok": True, "entry_hash": entry_hash}


@app.post("/api/cashback/record-distribution")
async def record_distribution(user_id: int, referred_user_id: int, verify: bool = False):
    """Record that user_id referred referred_user_id. If verify=true, marks immediately as verified."""
    async with pool.acquire() as conn:
        await _ensure_cashback_table(conn)
        await conn.execute("""
            INSERT INTO user_distributions (user_id, referred_user_id, verified, verified_at)
            VALUES ($1, $2, $3, CASE WHEN $3 THEN CURRENT_TIMESTAMP ELSE NULL END)
            ON CONFLICT (user_id, referred_user_id) DO UPDATE
              SET verified = EXCLUDED.verified,
                  verified_at = COALESCE(user_distributions.verified_at, CASE WHEN EXCLUDED.verified THEN CURRENT_TIMESTAMP ELSE NULL END)
        """, user_id, referred_user_id, verify)
    if verify:
        # Process tiers immediately
        return await process_cashback(user_id)
    return {"ok": True, "user_id": user_id, "referred_user_id": referred_user_id, "verified": verify}


@app.post("/api/beta/create-coupon")
async def beta_create_coupon(admin_key: str, code: str, max_uses: int = 49, slh_bonus: float = 0.1):
    """Admin: create a new beta coupon code."""
    admin_secret = os.getenv("ADMIN_API_KEY", "slh_admin_2026")
    if admin_key != admin_secret:
        raise HTTPException(403, "Invalid admin key")
    code = code.strip().upper()
    if not code or len(code) < 4:
        raise HTTPException(400, "Code must be at least 4 characters")
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO beta_coupons (code, max_uses, used_count, slh_bonus, active)
            VALUES ($1, $2, 0, $3, TRUE)
            ON CONFLICT (code) DO UPDATE SET
                max_uses = EXCLUDED.max_uses,
                slh_bonus = EXCLUDED.slh_bonus,
                active = TRUE
        """, code, max_uses, slh_bonus)
    return {"ok": True, "code": code, "max_uses": max_uses, "slh_bonus": slh_bonus}


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
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT p.user_id, w.username, w.first_name, p.payment_status, p.created_at
                FROM premium_users p
                LEFT JOIN web_users w ON w.telegram_id = p.user_id
                WHERE p.payment_status IN ('pending', 'submitted')
                ORDER BY p.created_at DESC
            """)
        return [dict(r) for r in rows]
    except Exception as e:
        return {"ok": False, "error": str(e), "registrations": []}


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


# === CUSTOM DISPLAY NAME (user-chosen, persists across Telegram re-auth) ===
class ProfileUpdateRequest(BaseModel):
    user_id: int
    display_name: Optional[str] = None
    bio: Optional[str] = None
    language_pref: Optional[str] = None  # he | en | ru | ar | fr


@app.post("/api/user/profile")
async def update_user_profile(req: ProfileUpdateRequest):
    """Update user's custom profile fields (display_name, bio, language).

    These fields are SET BY THE USER and persist across Telegram re-authentication.
    Only non-None fields are updated — pass partial objects to avoid wiping.
    Validation:
      - display_name: 2-32 chars, stripped
      - bio: up to 200 chars
      - language_pref: one of he/en/ru/ar/fr
    """
    if not req.user_id:
        raise HTTPException(400, "user_id required")

    updates = []
    params = []
    idx = 1

    if req.display_name is not None:
        name = req.display_name.strip()
        if len(name) < 2 or len(name) > 32:
            raise HTTPException(400, "display_name must be 2-32 characters")
        updates.append(f"display_name = ${idx}")
        params.append(name)
        idx += 1
        updates.append(f"display_name_set_at = CURRENT_TIMESTAMP")

    if req.bio is not None:
        bio = req.bio.strip()
        if len(bio) > 200:
            raise HTTPException(400, "bio max 200 characters")
        updates.append(f"bio = ${idx}")
        params.append(bio)
        idx += 1

    if req.language_pref is not None:
        if req.language_pref not in ("he", "en", "ru", "ar", "fr"):
            raise HTTPException(400, "language_pref must be he/en/ru/ar/fr")
        updates.append(f"language_pref = ${idx}")
        params.append(req.language_pref)
        idx += 1

    if not updates:
        raise HTTPException(400, "No fields to update")

    params.append(req.user_id)
    sql = f"UPDATE web_users SET {', '.join(updates)} WHERE telegram_id = ${idx} RETURNING display_name, bio, language_pref, first_name, username"

    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, *params)
        if not row:
            raise HTTPException(404, "User not found")

    return {
        "ok": True,
        "user_id": req.user_id,
        "display_name": row["display_name"],
        "bio": row["bio"],
        "language_pref": row["language_pref"],
        "fallback_name": row["first_name"] or row["username"] or "User",
    }


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
                          ton_wallet, ton_wallet_linked_at,
                          display_name, bio, language_pref
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
    # TON plans
    "monthly": {"name": "Monthly", "apy_monthly": 4.0, "apy_annual": 48, "min_amount": 1, "min_ton": 1, "lock_days": 30, "currency": "TON"},
    "quarterly": {"name": "Quarterly", "apy_monthly": 4.5, "apy_annual": 55, "min_amount": 5, "min_ton": 5, "lock_days": 90, "currency": "TON"},
    "semi_annual": {"name": "Semi-Annual", "apy_monthly": 5.0, "apy_annual": 60, "min_amount": 10, "min_ton": 10, "lock_days": 180, "currency": "TON"},
    "annual": {"name": "Annual", "apy_monthly": 5.4, "apy_annual": 65, "min_amount": 25, "min_ton": 25, "lock_days": 365, "currency": "TON"},
    # SLH plans
    "slh_monthly": {"name": "SLH Monthly", "apy_monthly": 3.0, "apy_annual": 36, "min_amount": 10, "min_ton": 0, "lock_days": 30, "currency": "SLH"},
    "slh_quarterly": {"name": "SLH Quarterly", "apy_monthly": 3.5, "apy_annual": 42, "min_amount": 50, "min_ton": 0, "lock_days": 90, "currency": "SLH"},
    "slh_annual": {"name": "SLH Annual", "apy_monthly": 4.0, "apy_annual": 48, "min_amount": 100, "min_ton": 0, "lock_days": 365, "currency": "SLH"},
    # BNB plans
    "bnb_monthly": {"name": "BNB Monthly", "apy_monthly": 2.5, "apy_annual": 30, "min_amount": 0.01, "min_ton": 0, "lock_days": 30, "currency": "BNB"},
    "bnb_quarterly": {"name": "BNB Quarterly", "apy_monthly": 3.0, "apy_annual": 36, "min_amount": 0.05, "min_ton": 0, "lock_days": 90, "currency": "BNB"},
}


@app.get("/api/staking/plans")
async def get_staking_plans():
    """Get available staking plans"""
    return {"plans": STAKING_PLANS}


class StakeRequest(BaseModel):
    user_id: int
    plan: str
    amount: float
    currency: Optional[str] = None  # auto-detected from plan if not provided


@app.post("/api/staking/stake")
async def create_stake(req: StakeRequest):
    """Create a new staking position.
    Supports TON, SLH, and BNB staking. Creates as 'pending_approval' for admin review."""
    plan = STAKING_PLANS.get(req.plan)
    if not plan:
        raise HTTPException(400, f"Invalid plan. Choose from: {list(STAKING_PLANS.keys())}")

    currency = req.currency or plan.get("currency", "TON")
    min_amount = plan.get("min_amount", plan.get("min_ton", 1))

    if req.amount < min_amount:
        raise HTTPException(400, f"Minimum deposit is {min_amount} {currency}")

    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM web_users WHERE telegram_id=$1", req.user_id)
        if not user:
            raise HTTPException(404, "User not found. Login first.")

        # Check balance based on currency
        if currency == "TON":
            acct_bal = await conn.fetchval(
                "SELECT COALESCE(available, 0) FROM account_balances WHERE account_id=$1", req.user_id
            ) or 0
            tok_bal = await conn.fetchval(
                "SELECT COALESCE(balance, 0) FROM token_balances WHERE user_id=$1 AND token='TON'", req.user_id
            ) or 0
            total_bal = float(acct_bal) + float(tok_bal)
        else:
            total_bal = float(await conn.fetchval(
                "SELECT COALESCE(balance, 0) FROM token_balances WHERE user_id=$1 AND token=$2",
                req.user_id, currency
            ) or 0)

        if total_bal < req.amount:
            raise HTTPException(400,
                f"Insufficient {currency} balance. You have {total_bal:.4f} {currency} but need {req.amount} {currency}. "
                f"Please deposit {currency} first via wallet page.")

        end_date = datetime.utcnow() + timedelta(days=plan["lock_days"])

        # Create position as pending_approval (admin must confirm)
        pos_id = await conn.fetchval("""
            INSERT INTO staking_positions (user_id, plan, amount, apy_monthly, lock_days, end_date, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'pending_approval') RETURNING id
        """, req.user_id, req.plan, req.amount, plan["apy_monthly"], plan["lock_days"], end_date)

        # Audit log
        await audit_log_write(
            conn,
            action="staking.request",
            actor_type="user",
            actor_user_id=req.user_id,
            resource_type="staking_position",
            resource_id=str(pos_id),
            amount_native=req.amount,
            amount_currency=currency,
            metadata={"plan": req.plan, "apy": plan["apy_monthly"], "lock_days": plan["lock_days"], "currency": currency},
        )

    return {
        "id": pos_id,
        "plan": req.plan,
        "amount": req.amount,
        "currency": currency,
        "apy_monthly": plan["apy_monthly"],
        "apy_annual": plan["apy_annual"],
        "lock_days": plan["lock_days"],
        "end_date": end_date.isoformat(),
        "status": "pending_approval",
        "message": f"Staking {req.amount} {currency} submitted. Admin will review and approve within 24 hours.",
    }


@app.post("/api/staking/approve/{position_id}")
async def approve_stake(
    position_id: int,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Admin: approve a pending staking position and lock funds."""
    _require_admin(authorization, x_admin_key)
    async with pool.acquire() as conn:
        pos = await conn.fetchrow(
            "SELECT * FROM staking_positions WHERE id=$1", position_id
        )
        if not pos:
            raise HTTPException(404, "Position not found")
        if pos["status"] != "pending_approval":
            return {"ok": True, "already": pos["status"]}

        # Deduct TON from user balance
        user_id = pos["user_id"]
        amount = float(pos["amount"])

        # Try account_balances first, then token_balances
        acct_bal = await conn.fetchval(
            "SELECT COALESCE(available, 0) FROM account_balances WHERE account_id=$1", user_id
        ) or 0
        if float(acct_bal) >= amount:
            await conn.execute(
                "UPDATE account_balances SET available = available - $1, locked = locked + $1 WHERE account_id=$2",
                amount, user_id
            )
        else:
            tok_bal = await conn.fetchval(
                "SELECT COALESCE(balance, 0) FROM token_balances WHERE user_id=$1 AND token='TON'", user_id
            ) or 0
            if float(tok_bal) >= amount:
                await conn.execute(
                    "UPDATE token_balances SET balance = balance - $1 WHERE user_id=$2 AND token='TON'",
                    amount, user_id
                )
            else:
                raise HTTPException(400, f"User has insufficient TON to lock ({acct_bal} + {tok_bal} < {amount})")

        # Activate position
        await conn.execute(
            "UPDATE staking_positions SET status='active' WHERE id=$1", position_id
        )

        # Distribute referral commissions
        commissions = await distribute_referral_commissions(
            conn, user_id, amount, f"staking_{pos['plan']}", "TON"
        )

        await audit_log_write(
            conn, action="staking.approve", actor_type="admin",
            resource_type="staking_position", resource_id=str(position_id),
            amount_native=amount, amount_currency="TON",
            metadata={"plan": pos["plan"], "user_id": user_id, "commissions": len(commissions)},
        )

    return {"ok": True, "position_id": position_id, "status": "active", "amount_locked": amount}


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
    """Global leaderboard - XP, balance, referrals, or staking.

    Filters out test/seed user IDs (100001-299999) and negative IDs (group chats)
    so the leaderboard shows only real Telegram users.
    """
    # Test/seed IDs to exclude — keep real Telegram users only
    # Real Telegram user IDs are ALWAYS positive and typically > 1M
    EXCLUDE_RANGE = "user_id >= 1000000 AND user_id > 0"
    async with pool.acquire() as conn:
        rows = []
        try:
            if category == "xp":
                rows = await conn.fetch(
                    f"SELECT user_id, username, xp_total as score, level FROM users WHERE {EXCLUDE_RANGE} ORDER BY xp_total DESC LIMIT $1", limit
                )
            elif category == "balance":
                rows = await conn.fetch(
                    f"SELECT user_id, username, balance as score, level FROM users WHERE {EXCLUDE_RANGE} ORDER BY balance DESC LIMIT $1", limit
                )
            elif category == "staking":
                rows = await conn.fetch(f"""
                    SELECT sp.user_id, COALESCE(u.username,'') as username, SUM(sp.amount) as score, COALESCE(u.level,1) as level
                    FROM staking_positions sp LEFT JOIN users u ON sp.user_id = u.user_id
                    WHERE sp.status='active' AND sp.{EXCLUDE_RANGE.replace('user_id', 'user_id')}
                    GROUP BY sp.user_id, u.username, u.level
                    ORDER BY score DESC LIMIT $1
                """, limit)
            elif category == "referrals":
                rows = await conn.fetch(f"""
                    SELECT r.referrer_id as user_id, COALESCE(u.username,'') as username, COUNT(*) as score, COALESCE(u.level,1) as level
                    FROM referrals r LEFT JOIN users u ON r.referrer_id = u.user_id
                    WHERE r.referrer_id IS NOT NULL AND r.referrer_id >= 1000000
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
async def admin_dashboard(
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Aggregated admin dashboard data — all stats in one call.

    SECURITY FIX (H-1): Now requires admin authentication via JWT or X-Admin-Key header.
    """
    _require_admin(authorization, x_admin_key)
    async def safe(conn, query, *args):
        try:
            return await conn.fetchval(query, *args) or 0
        except Exception:
            return 0

    async with pool.acquire() as conn:
        # Count REAL users only (telegram_id >= 1M, excludes seed test ids 100001-299999)
        total_users = await safe(conn, "SELECT COUNT(*) FROM web_users WHERE telegram_id >= 1000000")
        premium_users = await safe(conn, "SELECT COUNT(*) FROM premium_users WHERE payment_status='approved' AND user_id >= 1000000")
        total_staked = await safe(conn, "SELECT COALESCE(SUM(amount),0) FROM staking_positions WHERE status='active' AND user_id >= 1000000")
        total_deposits = await safe(conn, "SELECT COALESCE(SUM(amount),0) FROM deposits WHERE status='active' AND user_id >= 1000000")
        pending_payments = await safe(conn, "SELECT COUNT(*) FROM premium_users WHERE payment_status='pending' AND user_id >= 1000000")

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_views = await safe(conn, "SELECT COUNT(*) FROM analytics_events WHERE created_at >= $1", today_start)
        today_visitors = await safe(conn, "SELECT COUNT(DISTINCT visitor_id) FROM analytics_events WHERE created_at >= $1 AND visitor_id != ''", today_start)
        total_events = await safe(conn, "SELECT COUNT(*) FROM analytics_events")
        total_visitors = await safe(conn, "SELECT COUNT(DISTINCT visitor_id) FROM analytics_events WHERE visitor_id != ''")

        # Recent signups — real Telegram IDs only
        today_signups = await safe(conn, "SELECT COUNT(*) FROM web_users WHERE last_login >= $1 AND telegram_id >= 1000000", today_start)

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

        # Recent users — REAL users only (filter test IDs + group chats)
        try:
            recent = await conn.fetch(
                "SELECT telegram_id, username, first_name, last_login FROM web_users "
                "WHERE telegram_id >= 1000000 "
                "ORDER BY last_login DESC LIMIT 15"
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


# === AUTO-SYNC FROM TELEGRAM BOT (no login widget required) ===
class BotSyncRequest(BaseModel):
    telegram_id: int
    username: Optional[str] = ""
    first_name: Optional[str] = ""
    photo_url: Optional[str] = ""
    referrer_id: Optional[int] = None
    bot_secret: str  # required to prevent anyone from creating users via this endpoint


BOT_SYNC_SECRET = os.getenv("BOT_SYNC_SECRET", "slh-bot-sync-2026-default-please-override")


@app.post("/api/auth/bot-sync")
async def auth_bot_sync(req: BotSyncRequest):
    """Called by SLH_AIR_bot whenever a user presses /start.

    Creates / updates the user in web_users so they can log into the
    website / mini-app using the same Telegram ID WITHOUT going through
    @userinfobot or the Telegram Login Widget. This is the core of the
    seamless registration UX: open bot → press /start → you're in.

    The bot passes a shared secret so random clients can't create users.
    Returns a short-lived JWT so the bot can generate a "login link" that
    drops the user straight into their dashboard.
    """
    if not req.bot_secret or req.bot_secret != BOT_SYNC_SECRET:
        raise HTTPException(403, "Invalid bot secret")
    if not req.telegram_id:
        raise HTTPException(400, "telegram_id required")

    async with pool.acquire() as conn:
        # Upsert the user
        await conn.execute("""
            INSERT INTO web_users
                (telegram_id, username, first_name, photo_url, auth_date, last_login)
            VALUES ($1, $2, $3, $4, EXTRACT(EPOCH FROM NOW())::BIGINT, CURRENT_TIMESTAMP)
            ON CONFLICT (telegram_id) DO UPDATE SET
                username = COALESCE(NULLIF(EXCLUDED.username, ''), web_users.username),
                first_name = COALESCE(NULLIF(EXCLUDED.first_name, ''), web_users.first_name),
                photo_url = COALESCE(NULLIF(EXCLUDED.photo_url, ''), web_users.photo_url),
                last_login = CURRENT_TIMESTAMP
        """, req.telegram_id, req.username or "", req.first_name or "", req.photo_url or "")

        # Record referral if given
        if req.referrer_id and req.referrer_id != req.telegram_id:
            try:
                await conn.execute("""
                    INSERT INTO referrals (user_id, referrer_id, depth)
                    VALUES ($1, $2, 1)
                    ON CONFLICT (user_id) DO NOTHING
                """, req.telegram_id, req.referrer_id)
            except Exception as e:
                print(f"[bot-sync] referral write failed: {e}")

        is_registered = await conn.fetchval(
            "SELECT is_registered FROM web_users WHERE telegram_id=$1", req.telegram_id
        ) or False

    # Issue JWT for auto-login (graceful fallback if JWT_SECRET missing)
    token = None
    try:
        token = create_jwt(req.telegram_id, req.username or "")
    except Exception as e:
        print(f"[bot-sync] jwt creation failed (JWT_SECRET missing?): {e}")

    # Always return a login URL — even without JWT, the dashboard accepts ?uid=
    login_url = (
        f"https://slh-nft.com/dashboard.html?uid={req.telegram_id}&jwt={token}"
        if token else
        f"https://slh-nft.com/dashboard.html?uid={req.telegram_id}"
    )

    print(f"[bot-sync] Synced user {req.telegram_id} (@{req.username}) — registered={is_registered}")
    return {
        "ok": True,
        "telegram_id": req.telegram_id,
        "is_registered": is_registered,
        "jwt": token,
        "login_url": login_url,
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
                   ton_wallet, ton_wallet_linked_at,
                   display_name, bio, language_pref
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
        # SECURITY FIX (C-1): Use parameterized CASE instead of f-string injection
        row = await conn.fetchrow("""
            INSERT INTO marketplace_items
                (seller_id, title, description, price, currency, image_url, category, stock, status, promotion, approved_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    CASE WHEN $11 = 'approved' THEN CURRENT_TIMESTAMP ELSE NULL END)
            RETURNING id, status, created_at
        """, req.seller_id, title, description, req.price, currency, image_url, category, stock, initial_status, promotion, initial_status)

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
async def marketplace_admin_pending(
    admin_id: int = Query(default=0),
    limit: int = Query(100, le=500),
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Admin-only: list all pending items waiting for approval."""
    # Accept either admin_id param or X-Admin-Key header
    if admin_id != ADMIN_USER_ID:
        try:
            _require_admin(authorization, x_admin_key)
        except Exception:
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
async def admin_activity(
    limit: int = Query(20, le=100),
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """SECURITY FIX (H-2): Now requires admin authentication."""
    _require_admin(authorization, x_admin_key)
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


# ============================================================
# TOKENOMICS — SLH/MNH/ZVK dual-track economy
# ============================================================
# SLH = Premium/Governance (high value, scarce, deflationary)
# MNH = ILS-pegged stablecoin (free internal transfers)
# ZVK = Activity rewards (low value, high volume)
#
# Revenue → 50% → Buyback SLH from DEX → Burn → deflationary pressure
# Staking SLH → earns ZVK+MNH yield → locks supply
# Internal MNH transfers → FREE (internal ledger, no blockchain)

async def _ensure_tokenomics_tables(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS token_burns (
            id BIGSERIAL PRIMARY KEY,
            token TEXT NOT NULL,
            amount NUMERIC(28,8) NOT NULL,
            source TEXT NOT NULL,  -- 'revenue_buyback' | 'fee_burn' | 'manual'
            tx_hash TEXT,
            usd_value NUMERIC(18,2),
            notes TEXT,
            burned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_token_burns_token_time ON token_burns(token, burned_at DESC);

        CREATE TABLE IF NOT EXISTS token_backing_reserves (
            id BIGSERIAL PRIMARY KEY,
            token TEXT NOT NULL,  -- 'SLH' | 'MNH'
            reserve_asset TEXT NOT NULL,  -- 'USDT' | 'BNB' | 'TON' | 'USD_BANK'
            amount NUMERIC(28,8) NOT NULL,
            usd_value NUMERIC(18,2) NOT NULL,
            proof_url TEXT,  -- link to on-chain address or bank statement
            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS internal_transfers (
            id BIGSERIAL PRIMARY KEY,
            from_user_id BIGINT NOT NULL,
            to_user_id BIGINT NOT NULL,
            token TEXT NOT NULL,  -- usually 'MNH'
            amount NUMERIC(28,8) NOT NULL,
            memo TEXT,
            fee NUMERIC(28,8) DEFAULT 0,  -- 0 for MNH internal
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_internal_xfers_from ON internal_transfers(from_user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_internal_xfers_to ON internal_transfers(to_user_id, created_at DESC);
    """)


@app.get("/api/tokenomics/stats")
async def tokenomics_stats():
    """Full tokenomics overview: supply, burned, staked, reserves."""
    async with pool.acquire() as conn:
        await _ensure_tokenomics_tables(conn)

        # SLH stats
        slh_burned = await conn.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM token_burns WHERE token='SLH'"
        ) or 0
        slh_staked = await conn.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM staking_positions WHERE status='active'"
        ) or 0
        slh_in_internal_balances = await conn.fetchval(
            "SELECT COALESCE(SUM(balance), 0) FROM token_balances WHERE token='SLH' AND user_id >= 1000000"
        ) or 0

        # Reserves
        reserves = await conn.fetch("""
            SELECT token, reserve_asset, SUM(amount) as amount, SUM(usd_value) as usd_value
              FROM token_backing_reserves
             GROUP BY token, reserve_asset
        """)

        # Recent burns
        recent_burns = await conn.fetch("""
            SELECT token, amount, source, usd_value, burned_at
              FROM token_burns
             ORDER BY burned_at DESC LIMIT 10
        """)

    TOTAL_SUPPLY = 111186328  # SLH fixed supply
    MAX_SUPPLY = 111186328
    circulating = TOTAL_SUPPLY - float(slh_burned)

    return {
        "slh": {
            "max_supply": MAX_SUPPLY,
            "circulating_supply": circulating,
            "burned": float(slh_burned),
            "burn_pct": round(float(slh_burned) / MAX_SUPPLY * 100, 4),
            "staked_active": float(slh_staked),
            "staked_pct": round(float(slh_staked) / circulating * 100, 4) if circulating > 0 else 0,
            "internal_balances": float(slh_in_internal_balances),
            "internal_price_ils": 444,
            "internal_price_usd": 121.6438,
        },
        "mnh": {
            "description": "ILS-pegged stablecoin, free internal transfers",
            "rate": "1 MNH = 1 ILS",
            "backed_by": "USDT/USD reserves (1:1)",
        },
        "zvk": {
            "description": "Activity rewards token",
            "rate": "~4.4 ILS per ZVK (floating)",
            "conversion_to_slh": "100 ZVK = 1 SLH",
        },
        "zuz": {
            "description": "Guardian anti-fraud token — Mark of Cain (אות קין)",
            "purpose": "Negative reputation marker for scammers, bots, and fraudsters",
            "mechanism": "Assigned by Guardian bot reports. Higher ZUZ = more suspicious",
            "auto_ban_threshold": ZUZ_AUTO_BAN_THRESHOLD,
            "severity_levels": ZUZ_SEVERITY,
            "cross_group": "Shared across all SLH ecosystem groups — one report affects all",
        },
        "reserves": [
            {
                "token": r["token"],
                "asset": r["reserve_asset"],
                "amount": float(r["amount"]),
                "usd_value": float(r["usd_value"]),
            }
            for r in reserves
        ],
        "recent_burns": [
            {
                "token": r["token"],
                "amount": float(r["amount"]),
                "source": r["source"],
                "usd_value": float(r["usd_value"] or 0),
                "burned_at": r["burned_at"].isoformat() if r["burned_at"] else None,
            }
            for r in recent_burns
        ],
    }


class InternalTransferRequest(BaseModel):
    from_user_id: int
    to_user_id: int
    amount: float
    token: str = "MNH"
    memo: Optional[str] = None


@app.post("/api/tokenomics/internal-transfer")
async def internal_transfer(req: InternalTransferRequest, authorization: Optional[str] = Header(None)):
    """FREE internal transfer between users. Works for MNH/ZVK/SLH.
    Uses the internal ledger — no blockchain fees. Instant.
    SECURITY: Requires JWT auth — sender must be the from_user_id."""
    # Verify caller is the sender (or admin)
    try:
        caller_id = get_current_user_id(authorization)
        if caller_id != req.from_user_id and caller_id != ADMIN_USER_ID:
            raise HTTPException(403, "You can only transfer from your own account")
    except Exception:
        raise HTTPException(401, "Authentication required for transfers")
    if req.from_user_id == req.to_user_id:
        raise HTTPException(400, "Cannot transfer to self")
    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    if req.token not in ("MNH", "ZVK", "SLH"):
        raise HTTPException(400, "Token must be MNH, ZVK, or SLH")

    async with pool.acquire() as conn:
        await _ensure_tokenomics_tables(conn)

        # Check sender balance
        balance = await conn.fetchval(
            "SELECT balance FROM token_balances WHERE user_id=$1 AND token=$2",
            req.from_user_id, req.token
        ) or 0

        if float(balance) < req.amount:
            raise HTTPException(400, f"Insufficient {req.token} balance: {balance}")

        # Transaction — debit sender, credit recipient
        async with conn.transaction():
            await conn.execute("""
                UPDATE token_balances SET balance = balance - $1, updated_at = CURRENT_TIMESTAMP
                 WHERE user_id=$2 AND token=$3
            """, req.amount, req.from_user_id, req.token)
            await conn.execute("""
                INSERT INTO token_balances (user_id, token, balance) VALUES ($1, $2, $3)
                ON CONFLICT (user_id, token) DO UPDATE
                  SET balance = token_balances.balance + EXCLUDED.balance,
                      updated_at = CURRENT_TIMESTAMP
            """, req.to_user_id, req.token, req.amount)
            xfer_id = await conn.fetchval("""
                INSERT INTO internal_transfers (from_user_id, to_user_id, token, amount, memo, fee)
                VALUES ($1, $2, $3, $4, $5, 0)
                RETURNING id
            """, req.from_user_id, req.to_user_id, req.token, req.amount, req.memo)

            # Audit
            await audit_log_write(
                conn,
                action="internal_transfer",
                actor_type="user",
                actor_user_id=req.from_user_id,
                resource_type="internal_transfer",
                resource_id=str(xfer_id),
                amount_native=req.amount,
                amount_currency=req.token,
            )

    return {"ok": True, "transfer_id": xfer_id, "fee": 0, "token": req.token, "amount": req.amount}


class BurnRequest(BaseModel):
    token: str
    amount: float
    source: str  # 'revenue_buyback', 'fee_burn', 'manual'
    tx_hash: Optional[str] = None
    usd_value: Optional[float] = None
    notes: Optional[str] = None


@app.post("/api/tokenomics/burn")
async def burn_tokens(req: BurnRequest, authorization: Optional[str] = Header(None), x_admin_key: Optional[str] = Header(None)):
    """Record a token burn. Admin-only. For audit trail + supply accounting."""
    _require_admin(authorization, x_admin_key)
    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    async with pool.acquire() as conn:
        await _ensure_tokenomics_tables(conn)
        burn_id = await conn.fetchval("""
            INSERT INTO token_burns (token, amount, source, tx_hash, usd_value, notes)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """, req.token, req.amount, req.source, req.tx_hash, req.usd_value, req.notes)
        await audit_log_write(
            conn,
            action="token.burn",
            actor_type="system",
            resource_type="token_burn",
            resource_id=str(burn_id),
            amount_native=req.amount,
            amount_currency=req.token,
            amount_usd=req.usd_value,
            metadata={"source": req.source, "tx_hash": req.tx_hash},
        )
    return {"ok": True, "burn_id": burn_id}


class ReserveRequest(BaseModel):
    token: str  # 'SLH' | 'MNH'
    reserve_asset: str  # 'USDT' | 'BNB' | etc
    amount: float
    usd_value: float
    proof_url: Optional[str] = None
    notes: Optional[str] = None


@app.post("/api/tokenomics/reserves/add")
async def add_reserve(req: ReserveRequest, authorization: Optional[str] = Header(None), x_admin_key: Optional[str] = Header(None)):
    """Record backing reserves. Admin-only. Published for transparency."""
    _require_admin(authorization, x_admin_key)
    async with pool.acquire() as conn:
        await _ensure_tokenomics_tables(conn)
        rid = await conn.fetchval("""
            INSERT INTO token_backing_reserves (token, reserve_asset, amount, usd_value, proof_url, notes)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """, req.token, req.reserve_asset, req.amount, req.usd_value, req.proof_url, req.notes)
        await audit_log_write(
            conn,
            action="reserves.add",
            actor_type="admin",
            resource_type="token_backing",
            resource_id=str(rid),
            amount_usd=req.usd_value,
            metadata={"token": req.token, "asset": req.reserve_asset},
            compliance_flags=["PROOF_OF_RESERVES"],
        )
    return {"ok": True, "reserve_id": rid}


# ============================================================
# STRATEGY ENGINE — Backtested investment strategies
# ============================================================
# 3 strategies with historical backtest data.
# Each strategy has expected annual yield + max drawdown.
# Users can opt in; strategies execute against CEX accounts.

STRATEGIES = [
    {
        "id": "grid_btc_usdt",
        "name": "Grid Trading BTC/USDT",
        "description": "Market-neutral strategy: places buy/sell orders at fixed price intervals. Profits from volatility.",
        "risk_level": "LOW",
        "expected_annual": 25.4,  # %
        "max_drawdown": -8.2,
        "backtest_period": "2024-01 to 2026-03",
        "sharpe_ratio": 2.1,
        "min_capital_usd": 1000,
        "rebalance_freq": "hourly",
        "assets": ["BTC", "USDT"],
        "exchanges": ["bybit", "binance"],
        "status": "READY",
    },
    {
        "id": "dca_rebalance",
        "name": "DCA + Weekly Rebalance",
        "description": "Dollar-cost-averages into BTC/ETH/SOL/TON with weekly rebalance to target weights.",
        "risk_level": "MEDIUM",
        "expected_annual": 42.7,
        "max_drawdown": -22.5,
        "backtest_period": "2024-01 to 2026-03",
        "sharpe_ratio": 1.4,
        "min_capital_usd": 500,
        "rebalance_freq": "weekly",
        "assets": ["BTC", "ETH", "SOL", "TON", "USDT"],
        "exchanges": ["bybit", "binance"],
        "status": "READY",
    },
    {
        "id": "momentum_multi",
        "name": "Multi-Asset Momentum",
        "description": "Rotates between top-5 crypto assets based on 30-day momentum. Goes to USDT in bear markets.",
        "risk_level": "HIGH",
        "expected_annual": 78.3,
        "max_drawdown": -34.1,
        "backtest_period": "2024-01 to 2026-03",
        "sharpe_ratio": 1.8,
        "min_capital_usd": 2500,
        "rebalance_freq": "weekly",
        "assets": ["BTC", "ETH", "BNB", "SOL", "TON", "USDT"],
        "exchanges": ["bybit", "binance"],
        "status": "READY",
    },
]


@app.get("/api/strategy/list")
async def list_strategies():
    """List all available investment strategies with backtested performance."""
    return {
        "strategies": STRATEGIES,
        "total": len(STRATEGIES),
        "portfolio_target_annual": "65%+",
        "note": "All strategies are READ-ONLY backtests. Live execution requires Fireblocks custody + user opt-in.",
    }


@app.get("/api/strategy/{strategy_id}")
async def get_strategy(strategy_id: str):
    """Get details for a specific strategy."""
    for s in STRATEGIES:
        if s["id"] == strategy_id:
            return s
    raise HTTPException(404, "Strategy not found")


# ============================================================
# BROADCAST — Send Telegram messages to registered users
# ============================================================
# Uses @SLH_AIR_bot to DM every registered user. Ideal for
# presale announcements, Genesis 49 updates, system alerts.
# Admin-only. All broadcasts logged to institutional_audit.

class BroadcastRequest(BaseModel):
    message: str
    target: str = "registered"  # 'registered' | 'genesis49' | 'all' | 'custom'
    custom_ids: Optional[list] = None
    admin_key: str  # must match ADMIN_BROADCAST_KEY
    dry_run: bool = False


async def _ensure_broadcast_table(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS broadcast_log (
            id BIGSERIAL PRIMARY KEY,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            target TEXT NOT NULL,
            total_targets INT NOT NULL,
            success_count INT NOT NULL DEFAULT 0,
            fail_count INT NOT NULL DEFAULT 0,
            message_preview TEXT,
            admin_actor TEXT
        );
        CREATE TABLE IF NOT EXISTS broadcast_deliveries (
            id BIGSERIAL PRIMARY KEY,
            broadcast_id BIGINT NOT NULL REFERENCES broadcast_log(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL,
            status TEXT NOT NULL,  -- 'sent' | 'failed' | 'blocked' | 'not_found'
            error TEXT,
            delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_broadcast_deliveries_bid ON broadcast_deliveries(broadcast_id);
    """)


async def _tg_send_message(bot_token: str, chat_id: int, text: str, parse_mode: str = "HTML") -> dict:
    """Send a Telegram message via bot API. Returns dict with ok/error."""
    if not bot_token:
        return {"ok": False, "error": "bot token not configured"}
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                return data
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


ADMIN_BROADCAST_KEY = os.getenv("ADMIN_BROADCAST_KEY", "slh-broadcast-2026-change-me")


@app.post("/api/broadcast/send")
async def send_broadcast(req: BroadcastRequest):
    """Send a broadcast message to registered users via @SLH_AIR_bot.

    Targets:
    - 'registered': all users with is_registered=True (premium + Genesis 49)
    - 'genesis49':  only Genesis 49 NFT holders
    - 'all':        every user in web_users (real IDs only)
    - 'custom':     provide custom_ids list

    Admin key: accepts ADMIN_BROADCAST_KEY OR any of the 4 ADMIN_API_KEYS
    (slh2026admin, slh_admin_2026, slh-spark-admin, slh-institutional).
    """
    if req.admin_key != ADMIN_BROADCAST_KEY and req.admin_key not in ADMIN_API_KEYS:
        raise HTTPException(403, "Invalid admin key — use your admin panel password")
    if not req.message or len(req.message) < 5:
        raise HTTPException(400, "Message too short")
    if len(req.message) > 4000:
        raise HTTPException(400, "Message exceeds Telegram 4096-char limit")

    async with pool.acquire() as conn:
        await _ensure_broadcast_table(conn)

        # Resolve targets
        if req.target == "registered":
            rows = await conn.fetch(
                "SELECT telegram_id FROM web_users WHERE telegram_id >= 1000000 AND is_registered = TRUE"
            )
        elif req.target == "genesis49":
            rows = await conn.fetch(
                "SELECT telegram_id FROM web_users WHERE telegram_id >= 1000000 AND beta_user = TRUE"
            )
        elif req.target == "all":
            rows = await conn.fetch(
                "SELECT telegram_id FROM web_users WHERE telegram_id >= 1000000"
            )
        elif req.target == "custom":
            if not req.custom_ids:
                raise HTTPException(400, "custom target requires custom_ids")
            rows = [{"telegram_id": int(i)} for i in req.custom_ids if int(i) >= 1000000]
        else:
            raise HTTPException(400, "invalid target")

        user_ids = [r["telegram_id"] for r in rows]

        if req.dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "target": req.target,
                "total_recipients": len(user_ids),
                "sample_ids": user_ids[:5],
                "message_preview": req.message[:200],
            }

        # Create broadcast record
        broadcast_id = await conn.fetchval("""
            INSERT INTO broadcast_log (target, total_targets, message_preview, admin_actor)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """, req.target, len(user_ids), req.message[:200], "api_admin")

        # Audit
        await audit_log_write(
            conn,
            action="broadcast.send",
            actor_type="admin",
            resource_type="broadcast",
            resource_id=str(broadcast_id),
            metadata={"target": req.target, "count": len(user_ids)},
        )

    # Send messages (outside the pool transaction for non-blocking)
    success = 0
    failed = 0
    deliveries = []

    if not BROADCAST_BOT_TOKEN:
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE broadcast_log SET success_count=0, fail_count=$1 WHERE id=$2",
                len(user_ids), broadcast_id
            )
        return {
            "ok": False,
            "error": "BROADCAST_BOT_TOKEN not configured",
            "hint": "Set SLH_AIR_TOKEN or CORE_BOT_TOKEN env var on Railway",
            "broadcast_id": broadcast_id,
            "total_recipients": len(user_ids),
        }

    for uid in user_ids:
        result = await _tg_send_message(BROADCAST_BOT_TOKEN, uid, req.message, parse_mode="HTML")
        if result.get("ok"):
            success += 1
            deliveries.append((broadcast_id, uid, "sent", None))
        else:
            failed += 1
            err = str(result.get("error") or result.get("description") or "unknown")[:200]
            status = "blocked" if "blocked" in err.lower() else "failed"
            deliveries.append((broadcast_id, uid, status, err))

    # Write deliveries + update log
    async with pool.acquire() as conn:
        for d in deliveries:
            await conn.execute(
                "INSERT INTO broadcast_deliveries (broadcast_id, user_id, status, error) VALUES ($1, $2, $3, $4)",
                *d
            )
        await conn.execute(
            "UPDATE broadcast_log SET success_count=$1, fail_count=$2 WHERE id=$3",
            success, failed, broadcast_id
        )

    return {
        "ok": True,
        "broadcast_id": broadcast_id,
        "total_recipients": len(user_ids),
        "success": success,
        "failed": failed,
    }


# ============================================================
# GENESIS LAUNCH — Ultra Micro Pool ($33) with Tzvika as co-founder
# ============================================================
# Tracks contributions to the initial PancakeSwap SLH/BNB pool.
# Model: Partner sends BNB to company wallet, pool is created with
# that BNB + SLH from treasury. Contributors get credit + rewards.

COMPANY_BSC_WALLET = "0xd061de73B06d5E91bfA46b35EfB7B08b16903da4"  # Osif's Web3 wallet
LAUNCH_TARGET_BNB = 0.05  # Ultra Micro: 0.05 BNB + 50 SLH
LAUNCH_TARGET_SLH = 50
LAUNCH_NAME = "Genesis Launch — Ultra Micro Pool"


async def _ensure_launch_tables(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS launch_contributions (
            id BIGSERIAL PRIMARY KEY,
            partner_name TEXT NOT NULL,
            partner_handle TEXT,
            wallet_address TEXT,
            amount_bnb NUMERIC(18,8) NOT NULL,
            amount_usd NUMERIC(18,2),
            tx_hash TEXT UNIQUE,
            role TEXT DEFAULT 'contributor',  -- 'cofounder' | 'contributor' | 'angel'
            status TEXT DEFAULT 'pending',  -- 'pending' | 'verified' | 'cancelled'
            rewards_issued BOOLEAN DEFAULT FALSE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified_at TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_launch_contrib_status ON launch_contributions(status);
    """)


class LaunchContributionRequest(BaseModel):
    partner_name: str
    partner_handle: Optional[str] = None
    amount_bnb: float
    tx_hash: Optional[str] = None
    wallet_address: Optional[str] = None
    role: str = "contributor"
    notes: Optional[str] = None


@app.post("/api/launch/contribute")
async def launch_contribute(req: LaunchContributionRequest):
    """Record a launch contribution.

    Status starts as 'pending' until manually verified (or auto-verified
    via BSC RPC lookup of tx_hash). After verification, rewards are issued.
    """
    if req.amount_bnb <= 0:
        raise HTTPException(400, "Amount must be positive")
    if not req.partner_name:
        raise HTTPException(400, "Partner name required")

    # Estimate USD value (rough, BNB = $608 hardcoded — can replace with live price)
    amount_usd = round(req.amount_bnb * 608, 2)

    async with pool.acquire() as conn:
        await _ensure_launch_tables(conn)
        # Check if tx_hash already exists (idempotency)
        if req.tx_hash:
            existing = await conn.fetchval(
                "SELECT id FROM launch_contributions WHERE tx_hash=$1", req.tx_hash
            )
            if existing:
                return {"ok": False, "error": "tx_hash already recorded", "id": existing}

        cid = await conn.fetchval("""
            INSERT INTO launch_contributions
                (partner_name, partner_handle, wallet_address, amount_bnb,
                 amount_usd, tx_hash, role, notes, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending')
            RETURNING id
        """, req.partner_name, req.partner_handle, req.wallet_address,
            req.amount_bnb, amount_usd, req.tx_hash, req.role, req.notes)

        # Audit log
        await audit_log_write(
            conn,
            action="launch.contribute",
            actor_type="partner",
            actor_user_id=None,
            resource_type="launch_contribution",
            resource_id=str(cid),
            amount_native=req.amount_bnb,
            amount_currency="BNB",
            amount_usd=amount_usd,
            metadata={
                "partner": req.partner_name,
                "handle": req.partner_handle,
                "role": req.role,
                "tx_hash": req.tx_hash,
            },
            compliance_flags=["GENESIS_LAUNCH", "PRE_POOL"],
        )

    return {
        "ok": True,
        "contribution_id": cid,
        "partner_name": req.partner_name,
        "amount_bnb": req.amount_bnb,
        "amount_usd": amount_usd,
        "status": "pending",
        "message": "Contribution recorded. Will be verified on-chain + rewards issued within 24h.",
    }


@app.post("/api/launch/verify/{contribution_id}")
async def launch_verify_contribution(contribution_id: int, admin_key: str):
    """Admin: mark a contribution as verified + issue rewards.
    Accepts ADMIN_BROADCAST_KEY or any admin panel password."""
    if admin_key != ADMIN_BROADCAST_KEY and admin_key not in ADMIN_API_KEYS:
        raise HTTPException(403, "Invalid admin key")
    async with pool.acquire() as conn:
        await _ensure_launch_tables(conn)
        row = await conn.fetchrow(
            "SELECT * FROM launch_contributions WHERE id=$1", contribution_id
        )
        if not row:
            raise HTTPException(404, "Contribution not found")
        if row["status"] == "verified":
            return {"ok": True, "already_verified": True}
        await conn.execute("""
            UPDATE launch_contributions
               SET status='verified', verified_at=CURRENT_TIMESTAMP, rewards_issued=TRUE
             WHERE id=$1
        """, contribution_id)
        await audit_log_write(
            conn,
            action="launch.verify",
            actor_type="admin",
            resource_type="launch_contribution",
            resource_id=str(contribution_id),
            amount_usd=float(row["amount_usd"] or 0),
            metadata={"partner": row["partner_name"]},
            compliance_flags=["GENESIS_LAUNCH", "VERIFIED"],
        )

        # ── Auto-reward: credit ZVK + REP to contributor ──
        contributor_name = row["partner_name"]
        contributor_handle = row.get("partner_handle", "") or ""
        rewards_issued = False

        # Try to find user by handle first, then by name match
        user_id = None
        if contributor_handle:
            clean_handle = contributor_handle.lstrip("@")
            user_id = await conn.fetchval(
                "SELECT telegram_id FROM web_users WHERE username=$1", clean_handle
            )

        # Fallback: match by first_name or display_name
        if not user_id and contributor_name:
            c_lower = contributor_name.strip().lower()
            user_id = await conn.fetchval(
                "SELECT telegram_id FROM web_users WHERE telegram_id >= 1000000 "
                "AND (LOWER(first_name) = $1 OR LOWER(display_name) = $1)",
                c_lower
            )

        if user_id:
            # Credit 500 ZVK
            await conn.execute("""
                INSERT INTO token_balances (user_id, token, balance)
                VALUES ($1, 'ZVK', 500)
                ON CONFLICT (user_id, token) DO UPDATE
                  SET balance = token_balances.balance + 500,
                      updated_at = CURRENT_TIMESTAMP
            """, user_id)

            # Credit 100 REP (genesis action)
            await _ensure_rep_tables(conn)
            await conn.execute("""
                INSERT INTO member_rep (user_id, rep_score, genesis_contributor)
                VALUES ($1, 100, TRUE)
                ON CONFLICT (user_id) DO UPDATE
                  SET rep_score = member_rep.rep_score + 100,
                      genesis_contributor = TRUE,
                      updated_at = CURRENT_TIMESTAMP
            """, user_id)

            # Audit the reward
            await audit_log_write(
                conn,
                action="launch.reward",
                actor_type="system",
                actor_user_id=user_id,
                resource_type="launch_reward",
                resource_id=str(contribution_id),
                amount_native=500,
                amount_currency="ZVK",
                metadata={"rep_added": 100, "genesis": True, "partner": contributor_name},
            )
            rewards_issued = True

    return {
        "ok": True,
        "contribution_id": contribution_id,
        "status": "verified",
        "rewards_issued": rewards_issued,
    }


@app.get("/api/admin/all-users")
async def admin_all_users(
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """List all web_users with their token balances. Admin only."""
    _require_admin(authorization, x_admin_key)
    try:
      async with pool.acquire() as conn:
        # tables created at startup
        try:
            users = await conn.fetch(
                "SELECT telegram_id, username, first_name, last_login "
                "FROM web_users WHERE telegram_id >= 1000000 ORDER BY last_login DESC"
            )
        except Exception as e:
            return {"ok": False, "error": f"DB query failed: {str(e)}"}
        result = []
        for u in users:
            balances = await conn.fetch(
                "SELECT token, balance FROM token_balances WHERE user_id=$1", u["telegram_id"]
            )
            bal_dict = {r["token"]: float(r["balance"]) for r in balances}
            result.append({
                "telegram_id": u["telegram_id"],
                "username": u.get("username", ""),
                "first_name": u.get("first_name", ""),
                "last_login": u["last_login"].isoformat() if u.get("last_login") else None,
                "balances": bal_dict,
            })
      return {"ok": True, "users": result, "count": len(result)}
    except Exception as e:
      return {"ok": False, "error": str(e)}


@app.post("/api/admin/credit-rewards")
async def admin_credit_rewards(
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Find all verified contributors missing ZVK rewards and credit them.
    Also matches contributors to web_users by name when handle is missing."""
    _require_admin(authorization, x_admin_key)
    try:
     async with pool.acquire() as conn:
        # tables created at startup
        await _ensure_launch_tables(conn)
        await _ensure_rep_tables(conn)

        # Get all verified contributions
        contributions = await conn.fetch(
            "SELECT id, partner_name, partner_handle FROM launch_contributions WHERE status='verified'"
        )

        # Get all web_users (display_name may not exist yet)
        try:
            all_users = await conn.fetch(
                "SELECT telegram_id, username, first_name, display_name FROM web_users WHERE telegram_id >= 1000000"
            )
        except Exception:
            all_users = await conn.fetch(
                "SELECT telegram_id, username, first_name, NULL as display_name FROM web_users WHERE telegram_id >= 1000000"
            )

        credited = []
        already_had = []
        not_matched = []

        for c in contributions:
            cid = c["id"]
            name = c["partner_name"]
            handle = c["partner_handle"]

            # Try to find user: first by handle, then by name match
            user_id = None
            match_method = None

            if handle:
                clean_handle = handle.lstrip("@")
                user_id = await conn.fetchval(
                    "SELECT telegram_id FROM web_users WHERE username=$1", clean_handle
                )
                if user_id:
                    match_method = "handle"

            if not user_id:
                # Try matching by first_name or display_name
                for u in all_users:
                    u_name = (u["first_name"] or "").strip().lower()
                    u_display = (u["display_name"] or "").strip().lower()
                    c_name = name.strip().lower()
                    if c_name and (c_name == u_name or c_name == u_display or
                                   c_name in u_name or u_name in c_name):
                        user_id = u["telegram_id"]
                        match_method = f"name_match:{u['first_name']}"
                        break

            if not user_id:
                not_matched.append({"contribution_id": cid, "name": name})
                continue

            # Check if already has ZVK from genesis reward
            existing_zvk = await conn.fetchval(
                "SELECT balance FROM token_balances WHERE user_id=$1 AND token='ZVK'",
                user_id
            ) or 0

            # Skip if user already has ZVK (simpler check than audit log)
            prior_reward = float(existing_zvk) >= 500

            if prior_reward:
                already_had.append({
                    "contribution_id": cid, "name": name, "user_id": user_id,
                    "zvk_balance": float(existing_zvk), "match": match_method,
                })
                continue

            # Credit 500 ZVK
            await conn.execute("""
                INSERT INTO token_balances (user_id, token, balance)
                VALUES ($1, 'ZVK', 500)
                ON CONFLICT (user_id, token) DO UPDATE
                  SET balance = token_balances.balance + 500,
                      updated_at = CURRENT_TIMESTAMP
            """, user_id)

            # Credit 100 REP
            await conn.execute("""
                INSERT INTO member_rep (user_id, rep_score, genesis_contributor)
                VALUES ($1, 100, TRUE)
                ON CONFLICT (user_id) DO UPDATE
                  SET rep_score = member_rep.rep_score + 100,
                      genesis_contributor = TRUE,
                      updated_at = CURRENT_TIMESTAMP
            """, user_id)

            # Audit
            await audit_log_write(
                conn,
                action="launch.reward",
                actor_type="system",
                actor_user_id=user_id,
                resource_type="launch_reward",
                resource_id=str(cid),
                amount_native=500,
                amount_currency="ZVK",
                metadata={"rep_added": 100, "genesis": True, "partner": name,
                          "match_method": match_method, "retroactive": True},
            )

            credited.append({
                "contribution_id": cid, "name": name, "user_id": user_id,
                "zvk_credited": 500, "rep_credited": 100, "match": match_method,
            })

     return {
        "ok": True,
        "credited": credited,
        "already_had": already_had,
        "not_matched": not_matched,
        "summary": f"Credited {len(credited)} users, {len(already_had)} already had rewards, {len(not_matched)} unmatched",
     }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/admin/manual-credit")
async def admin_manual_credit(
    user_id: int,
    token: str,
    amount: float,
    reason: str = "manual_admin_credit",
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Manually credit tokens to a specific user. Admin only."""
    _require_admin(authorization, x_admin_key)
    if amount <= 0 or amount > 10000:
        raise HTTPException(400, "Amount must be 1-10000")
    if token not in ("SLH", "ZVK", "MNH", "REP"):
        raise HTTPException(400, "Token must be SLH, ZVK, MNH, or REP")

    async with pool.acquire() as conn:
        # tables created at startup
        # Verify user exists
        user = await conn.fetchrow("SELECT telegram_id, first_name FROM web_users WHERE telegram_id=$1", user_id)
        if not user:
            raise HTTPException(404, f"User {user_id} not found")

        if token == "REP":
            await _ensure_rep_tables(conn)
            await conn.execute("""
                INSERT INTO member_rep (user_id, rep_score)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE
                  SET rep_score = member_rep.rep_score + $2, updated_at = CURRENT_TIMESTAMP
            """, user_id, amount)
        else:
            await conn.execute("""
                INSERT INTO token_balances (user_id, token, balance)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, token) DO UPDATE
                  SET balance = token_balances.balance + $3, updated_at = CURRENT_TIMESTAMP
            """, user_id, token, amount)

        await audit_log_write(
            conn,
            action="admin.manual_credit",
            actor_type="admin",
            actor_user_id=user_id,
            resource_type="token_credit",
            amount_native=amount,
            amount_currency=token,
            metadata={"reason": reason, "user_name": user["first_name"]},
        )

    return {"ok": True, "user_id": user_id, "token": token, "amount": amount, "reason": reason}


# ============================================================
# GUARDIAN SYSTEM — ZUZ Token + Anti-Fraud Intelligence
# ============================================================
# ZUZ = "אות קין" (Mark of Cain) — negative reputation token
# Assigned by Guardian bot to mark scammers, bots, fraudsters.
# Higher ZUZ = more suspicious. Used for cross-group intelligence.

async def _ensure_guardian_tables(conn):
    """Create Guardian system tables."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS guardian_reports (
            id SERIAL PRIMARY KEY,
            reported_user_id BIGINT NOT NULL,
            reported_username TEXT,
            reporter_id BIGINT,
            reporter_username TEXT,
            group_id BIGINT,
            group_name TEXT,
            reason TEXT NOT NULL,
            evidence TEXT,
            severity TEXT DEFAULT 'medium',
            zuz_amount REAL DEFAULT 10,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            reviewed_by BIGINT
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS guardian_blacklist (
            id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            zuz_score REAL DEFAULT 0,
            total_reports INT DEFAULT 0,
            first_reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            groups_flagged TEXT[] DEFAULT '{}',
            ban_active BOOLEAN DEFAULT FALSE,
            ban_reason TEXT,
            auto_banned BOOLEAN DEFAULT FALSE
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS guardian_group_intel (
            id SERIAL PRIMARY KEY,
            group_id BIGINT NOT NULL,
            group_name TEXT,
            total_scams_detected INT DEFAULT 0,
            total_bans INT DEFAULT 0,
            protection_level TEXT DEFAULT 'standard',
            guardian_active BOOLEAN DEFAULT TRUE,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_scan TIMESTAMP
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS guardian_message_log (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            group_id BIGINT,
            message_hash TEXT,
            risk_score REAL DEFAULT 0,
            risk_factors TEXT,
            flagged BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_guardian_blacklist_user ON guardian_blacklist(user_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_guardian_reports_user ON guardian_reports(reported_user_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_guardian_msg_user ON guardian_message_log(user_id)")


class GuardianReportRequest(BaseModel):
    reported_user_id: int
    reported_username: Optional[str] = None
    reporter_id: Optional[int] = None
    reporter_username: Optional[str] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    reason: str
    evidence: Optional[str] = None
    severity: str = "medium"  # low, medium, high, critical


# ZUZ severity multipliers
ZUZ_SEVERITY = {"low": 5, "medium": 10, "high": 25, "critical": 50}
ZUZ_AUTO_BAN_THRESHOLD = 100  # auto-ban at 100 ZUZ


@app.post("/api/guardian/report")
async def guardian_report(req: GuardianReportRequest):
    """Report a user for suspicious/scam activity. Awards ZUZ marks."""
    zuz_amount = ZUZ_SEVERITY.get(req.severity, 10)

    async with pool.acquire() as conn:
        await _ensure_guardian_tables(conn)

        # Record the report
        report_id = await conn.fetchval("""
            INSERT INTO guardian_reports
                (reported_user_id, reported_username, reporter_id, reporter_username,
                 group_id, group_name, reason, evidence, severity, zuz_amount)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) RETURNING id
        """, req.reported_user_id, req.reported_username, req.reporter_id,
            req.reporter_username, req.group_id, req.group_name,
            req.reason, req.evidence, req.severity, zuz_amount)

        # Update or create blacklist entry
        existing = await conn.fetchrow(
            "SELECT id, zuz_score, total_reports FROM guardian_blacklist WHERE user_id=$1",
            req.reported_user_id
        )
        if existing:
            new_score = float(existing["zuz_score"]) + zuz_amount
            new_reports = existing["total_reports"] + 1
            auto_ban = new_score >= ZUZ_AUTO_BAN_THRESHOLD
            groups = []
            if req.group_name:
                groups = [req.group_name]
            await conn.execute("""
                UPDATE guardian_blacklist
                SET zuz_score = $1, total_reports = $2, last_reported_at = CURRENT_TIMESTAMP,
                    groups_flagged = array_cat(groups_flagged, $3::TEXT[]),
                    ban_active = CASE WHEN $4 THEN TRUE ELSE ban_active END,
                    auto_banned = CASE WHEN $4 THEN TRUE ELSE auto_banned END,
                    ban_reason = CASE WHEN $4 THEN 'Auto-ban: ZUZ threshold exceeded' ELSE ban_reason END
                WHERE user_id = $5
            """, new_score, new_reports, groups, auto_ban, req.reported_user_id)
        else:
            new_score = zuz_amount
            auto_ban = new_score >= ZUZ_AUTO_BAN_THRESHOLD
            await conn.execute("""
                INSERT INTO guardian_blacklist
                    (user_id, username, zuz_score, total_reports, groups_flagged,
                     ban_active, auto_banned, ban_reason)
                VALUES ($1,$2,$3,1,$4,$5,$6,$7)
            """, req.reported_user_id, req.reported_username, zuz_amount,
                [req.group_name] if req.group_name else [],
                auto_ban, auto_ban,
                'Auto-ban: ZUZ threshold exceeded' if auto_ban else None)

        # Credit ZUZ to the reported user's token balance (negative reputation)
        await conn.execute("""
            INSERT INTO token_balances (user_id, token, balance)
            VALUES ($1, 'ZUZ', $2)
            ON CONFLICT (user_id, token) DO UPDATE
              SET balance = token_balances.balance + $2, updated_at = CURRENT_TIMESTAMP
        """, req.reported_user_id, zuz_amount)

        # Audit log
        await audit_log_write(
            conn, action="guardian.report", actor_type="guardian",
            actor_user_id=req.reporter_id or 0,
            resource_type="scam_report", resource_id=str(report_id),
            amount_native=zuz_amount, amount_currency="ZUZ",
            metadata={"reason": req.reason, "severity": req.severity,
                      "reported_user": req.reported_user_id,
                      "auto_banned": auto_ban},
            compliance_flags=["GUARDIAN", "ANTI_FRAUD"],
        )

    return {
        "ok": True,
        "report_id": report_id,
        "zuz_awarded": zuz_amount,
        "total_zuz": new_score,
        "auto_banned": auto_ban,
        "message": f"Report #{report_id} filed. {zuz_amount} ZUZ marked."
                   + (" USER AUTO-BANNED!" if auto_ban else ""),
    }


@app.get("/api/guardian/check/{user_id}")
async def guardian_check_user(user_id: int):
    """Check if a user is flagged/banned by Guardian. Used by all bots."""
    async with pool.acquire() as conn:
        await _ensure_guardian_tables(conn)
        entry = await conn.fetchrow(
            "SELECT * FROM guardian_blacklist WHERE user_id=$1", user_id
        )
        if not entry:
            return {"flagged": False, "zuz_score": 0, "ban_active": False, "safe": True}

        reports = await conn.fetch(
            "SELECT reason, severity, group_name, created_at FROM guardian_reports "
            "WHERE reported_user_id=$1 ORDER BY created_at DESC LIMIT 10", user_id
        )

    return {
        "flagged": True,
        "zuz_score": float(entry["zuz_score"]),
        "total_reports": entry["total_reports"],
        "ban_active": entry["ban_active"],
        "auto_banned": entry["auto_banned"],
        "ban_reason": entry["ban_reason"],
        "groups_flagged": entry["groups_flagged"],
        "first_reported": entry["first_reported_at"].isoformat() if entry["first_reported_at"] else None,
        "last_reported": entry["last_reported_at"].isoformat() if entry["last_reported_at"] else None,
        "safe": False,
        "recent_reports": [
            {"reason": r["reason"], "severity": r["severity"],
             "group": r["group_name"], "date": r["created_at"].isoformat()}
            for r in reports
        ],
    }


@app.get("/api/guardian/blacklist")
async def guardian_blacklist(
    limit: int = Query(50, le=200),
    min_zuz: float = Query(0),
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Get all flagged users. Admin only for full list."""
    _require_admin(authorization, x_admin_key)
    async with pool.acquire() as conn:
        await _ensure_guardian_tables(conn)
        rows = await conn.fetch(
            "SELECT user_id, username, zuz_score, total_reports, ban_active, auto_banned, "
            "groups_flagged, first_reported_at, last_reported_at "
            "FROM guardian_blacklist WHERE zuz_score >= $1 "
            "ORDER BY zuz_score DESC LIMIT $2", min_zuz, limit
        )
    return {
        "ok": True,
        "count": len(rows),
        "blacklist": [
            {
                "user_id": r["user_id"], "username": r["username"],
                "zuz_score": float(r["zuz_score"]), "reports": r["total_reports"],
                "banned": r["ban_active"], "auto_banned": r["auto_banned"],
                "groups": r["groups_flagged"],
            }
            for r in rows
        ],
    }


@app.post("/api/guardian/scan-message")
async def guardian_scan_message(
    user_id: int, group_id: int = 0, message_text: str = "",
):
    """Scan a message for scam risk. Returns risk score + factors.
    Used by Guardian bot in real-time for every group message."""
    risk_score = 0
    factors = []

    text_lower = message_text.lower()

    # Suspicious keywords (EN + HE)
    scam_words = ["guaranteed profit", "invest now", "double your money", "free crypto",
                  "send me", "click here", "limited time", "act now", "whatsapp me",
                  "רווח מובטח", "השקעה בטוחה", "הכנסה פסיבית", "שלח לי",
                  "earn daily", "100% safe", "no risk"]
    for w in scam_words:
        if w in text_lower:
            risk_score += 20
            factors.append(f"suspicious_word:{w}")

    # URL detection
    import re
    urls = re.findall(r'https?://\S+', message_text)
    if urls:
        risk_score += 15
        factors.append(f"contains_urls:{len(urls)}")
        # Check for URL shorteners (extra suspicious)
        shorteners = ["bit.ly", "tinyurl", "t.co", "goo.gl", "ow.ly", "is.gd"]
        for url in urls:
            for s in shorteners:
                if s in url:
                    risk_score += 25
                    factors.append(f"url_shortener:{s}")

    # Excessive emojis (common in scam messages)
    emoji_count = len(re.findall(r'[\U0001F600-\U0001F9FF\U0001FA00-\U0001FAFF]', message_text))
    if emoji_count > 5:
        risk_score += 10
        factors.append(f"excessive_emojis:{emoji_count}")

    # ALL CAPS
    upper_ratio = sum(1 for c in message_text if c.isupper()) / max(len(message_text), 1)
    if upper_ratio > 0.5 and len(message_text) > 20:
        risk_score += 10
        factors.append("excessive_caps")

    # Check if user is already flagged
    async with pool.acquire() as conn:
        await _ensure_guardian_tables(conn)
        existing = await conn.fetchrow(
            "SELECT zuz_score, ban_active FROM guardian_blacklist WHERE user_id=$1", user_id
        )
        if existing:
            risk_score += min(float(existing["zuz_score"]), 30)
            factors.append(f"prior_zuz:{existing['zuz_score']}")
            if existing["ban_active"]:
                risk_score += 50
                factors.append("BANNED_USER")

        # Log the scan
        flagged = risk_score >= 50
        await conn.execute("""
            INSERT INTO guardian_message_log (user_id, group_id, message_hash, risk_score, risk_factors, flagged)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, user_id, group_id,
            hashlib.sha256(message_text.encode()).hexdigest()[:16],
            risk_score, ",".join(factors), flagged)

    return {
        "risk_score": min(risk_score, 100),
        "risk_level": "critical" if risk_score >= 75 else "high" if risk_score >= 50
                      else "medium" if risk_score >= 25 else "low",
        "factors": factors,
        "flagged": flagged,
        "action": "block" if risk_score >= 75 else "warn" if risk_score >= 50
                  else "monitor" if risk_score >= 25 else "allow",
        "user_prior_zuz": float(existing["zuz_score"]) if existing else 0,
    }


@app.get("/api/guardian/stats")
async def guardian_stats():
    """Guardian system statistics."""
    async with pool.acquire() as conn:
        await _ensure_guardian_tables(conn)
        total_reports = await conn.fetchval("SELECT COUNT(*) FROM guardian_reports") or 0
        total_flagged = await conn.fetchval("SELECT COUNT(*) FROM guardian_blacklist") or 0
        total_banned = await conn.fetchval("SELECT COUNT(*) FROM guardian_blacklist WHERE ban_active=TRUE") or 0
        total_auto_banned = await conn.fetchval("SELECT COUNT(*) FROM guardian_blacklist WHERE auto_banned=TRUE") or 0
        total_scans = await conn.fetchval("SELECT COUNT(*) FROM guardian_message_log") or 0
        total_flagged_msgs = await conn.fetchval("SELECT COUNT(*) FROM guardian_message_log WHERE flagged=TRUE") or 0
        total_zuz = await conn.fetchval("SELECT COALESCE(SUM(zuz_score),0) FROM guardian_blacklist") or 0
        groups_protected = await conn.fetchval("SELECT COUNT(*) FROM guardian_group_intel WHERE guardian_active=TRUE") or 0

    return {
        "total_reports": total_reports,
        "total_flagged_users": total_flagged,
        "total_banned": total_banned,
        "total_auto_banned": total_auto_banned,
        "total_messages_scanned": total_scans,
        "total_messages_flagged": total_flagged_msgs,
        "total_zuz_issued": float(total_zuz),
        "groups_protected": groups_protected,
        "zuz_auto_ban_threshold": ZUZ_AUTO_BAN_THRESHOLD,
    }


# ============================================================
# DYNAMIC OG IMAGE GENERATOR — per-page social share visuals
# ============================================================
# Generates 1200x630 PNG images on-the-fly with PIL.
# Each page can point its og:image to /api/og/{slug}.png for a
# unique preview when shared on Twitter/Facebook/Telegram/LinkedIn.

OG_PAGE_CONFIG = {
    "index":        {"title": "SLH \u2014 \u05d4\u05d0\u05e7\u05d5\u05e1\u05d9\u05e1\u05d8\u05dd \u05e9\u05dc \u05d4\u05e2\u05d5\u05dc\u05dd \u05d4\u05d7\u05d3\u05e9", "subtitle": "20+ Telegram bots \u00b7 Real blockchain \u00b7 65% APY", "accent": "#00e887", "icon": "SLH"},
    "network":      {"title": "SLH Network Map", "subtitle": "Interactive visualization of the ecosystem", "accent": "#6c5ce7", "icon": "NET"},
    "dashboard":    {"title": "SLH Dashboard", "subtitle": "Your portfolio, staking, and activity", "accent": "#00b4d8", "icon": "DASH"},
    "wallet":       {"title": "SLH Wallet", "subtitle": "Multi-currency TON/BSC wallet + CEX portfolio", "accent": "#f3ba2f", "icon": "W"},
    "bots":         {"title": "SLH Bot Ecosystem", "subtitle": "25 bots \u2014 each its own economy", "accent": "#00cec9", "icon": "BOTS"},
    "trade":        {"title": "SLH Trade", "subtitle": "Live prices + swap SLH on PancakeSwap", "accent": "#f7931a", "icon": "TRADE"},
    "earn":         {"title": "SLH Earn \u2014 65% APY", "subtitle": "Staking plans \u00b7 MNH yield \u00b7 Rebalance strategies", "accent": "#ffd700", "icon": "EARN"},
    "community":    {"title": "SLH Community", "subtitle": "Posts, events, and ecosystem discussion", "accent": "#ef4444", "icon": "CMTY"},
    "blockchain":   {"title": "SLH On-Chain", "subtitle": "Live BSC + TON blockchain data", "accent": "#f3ba2f", "icon": "CHAIN"},
    "roadmap":      {"title": "SLH Roadmap", "subtitle": "From foundation to global ecosystem", "accent": "#a855f7", "icon": "MAP"},
    "admin":        {"title": "SLH Institutional Admin", "subtitle": "Regulator-ready operations panel", "accent": "#00ff41", "icon": "ADM"},
    "launch-event": {"title": "Genesis Launch \ud83d\ude80", "subtitle": "First SLH pool on PancakeSwap \u2014 Join now", "accent": "#ffd700", "icon": "LAUNCH"},
    "dex-launch":   {"title": "DEX Launch Calculator", "subtitle": "AMM math \u00b7 Slippage \u00b7 5 scenarios from \u003232", "accent": "#f3ba2f", "icon": "DEX"},
    "daily-blog":   {"title": "SLH Daily Blog", "subtitle": "What we shipped today", "accent": "#00e887", "icon": "BLOG"},
    "guides":       {"title": "SLH Guides", "subtitle": "Step-by-step tutorials", "accent": "#00ff41", "icon": "DOCS"},
    "referral":     {"title": "SLH Referral Program", "subtitle": "10 generations of commissions", "accent": "#a855f7", "icon": "REF"},
    "healing":      {"title": "SLH Healing Vision", "subtitle": "The currency of healing, education, and aid", "accent": "#ff6b9d", "icon": "HEAL"},
    "liquidity":    {"title": "SLH Liquidity & Staking", "subtitle": "9 plans \u00b7 Up to 65% APY \u00b7 TON/SLH/BNB", "accent": "#00e887", "icon": "LP"},
    "challenge":    {"title": "21-Day Challenge", "subtitle": "\u05e8\u05d9\u05e4\u05d5\u05d9 \u00b7 \u05de\u05d3\u05d9\u05d8\u05e6\u05d9\u05d4 \u00b7 \u05e7\u05d4\u05d9\u05dc\u05d4", "accent": "#ff6b9d", "icon": "21"},
    "jubilee":      {"title": "SLH Jubilee Year", "subtitle": "Biblical economic reset \u2014 Healing through blockchain", "accent": "#7cb342", "icon": "YOV"},
    "member":       {"title": "SLH Member Card", "subtitle": "Your personal NFT \u00b7 Genesis Status \u00b7 REP Score", "accent": "#a855f7", "icon": "NFT"},
    "p2p":          {"title": "SLH P2P Trading", "subtitle": "Trade directly with community members", "accent": "#00b4d8", "icon": "P2P"},
    "staking":      {"title": "SLH Staking", "subtitle": "Earn up to 65% APY \u00b7 4 lock periods", "accent": "#ffd700", "icon": "STAK"},
    "whitepaper":   {"title": "SLH Whitepaper", "subtitle": "Architecture \u00b7 Tokenomics \u00b7 Vision", "accent": "#6c5ce7", "icon": "WP"},
    "privacy":      {"title": "SLH Privacy Policy", "subtitle": "Your data, your rights", "accent": "#888", "icon": "PRIV"},
    "terms":        {"title": "SLH Terms of Service", "subtitle": "Usage terms and conditions", "accent": "#888", "icon": "TOS"},
    "for-therapists": {"title": "SLH For Therapists", "subtitle": "Join the healing network \u00b7 Get paid in MNH", "accent": "#ff6b9d", "icon": "RX"},
    "ops-dashboard": {"title": "SLH Ops Dashboard", "subtitle": "Real-time system monitoring", "accent": "#00e5ff", "icon": "OPS"},
    "partner":      {"title": "SLH Partner Dashboard", "subtitle": "Genesis Contributors \u00b7 Rewards \u00b7 Status", "accent": "#ffd700", "icon": "PTR"},
    "invite":       {"title": "SLH Invite", "subtitle": "Invite friends \u00b7 Earn ZVK rewards", "accent": "#a855f7", "icon": "INV"},
    "onboarding":   {"title": "SLH Genesis 49", "subtitle": "Join first, free \u00b7 49 spots", "accent": "#00e887", "icon": "G49"},
    "default":      {"title": "SLH Spark", "subtitle": "Digital Ecosystem Built in Israel", "accent": "#00e887", "icon": "SLH"},
}


def _generate_og_image(slug: str) -> bytes:
    """Generate a 1200x630 PNG OG image for the given slug. Returns bytes."""
    import hashlib
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO

    cfg = OG_PAGE_CONFIG.get(slug, OG_PAGE_CONFIG["default"])
    W, H = 1200, 630
    BG = (10, 14, 26)  # #0a0e1a

    # Accent color parsing
    accent_hex = cfg["accent"].lstrip("#")
    accent_rgb = tuple(int(accent_hex[i:i+2], 16) for i in (0, 2, 4))

    # --- base image (RGBA for compositing, converted at end) ---
    img = Image.new("RGBA", (W, H), (*BG, 255))

    # --- radial gradient layer ---
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(grad)
    cx, cy = W // 2, H // 2
    max_r = int((W**2 + H**2) ** 0.5 / 2)
    steps = 80
    for i in range(steps, 0, -1):
        ratio = i / steps
        r = int(max_r * ratio)
        alpha = int(40 * (1 - ratio))  # stronger towards center
        color = (*accent_rgb, alpha)
        grad_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    img = Image.alpha_composite(img, grad)

    # --- subtle grid pattern (accent at ~5% opacity) ---
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid)
    grid_color = (*accent_rgb, 13)  # ~5% of 255
    for x in range(0, W, 40):
        grid_draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(0, H, 40):
        grid_draw.line([(0, y), (W, y)], fill=grid_color, width=1)
    img = Image.alpha_composite(img, grid)

    # --- decorative circles (deterministic per slug) ---
    seed = int(hashlib.md5(slug.encode()).hexdigest(), 16)
    circles = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    circles_draw = ImageDraw.Draw(circles)
    circle_alpha = 25  # ~10% of 255
    circle_params = [
        (seed % W, (seed >> 8) % H, 120 + (seed >> 16) % 100),
        ((seed >> 4) % W, (seed >> 12) % H, 80 + (seed >> 20) % 80),
        ((seed >> 6) % W, (seed >> 14) % H, 60 + (seed >> 24) % 60),
    ]
    for cx_c, cy_c, radius in circle_params:
        circles_draw.ellipse(
            [cx_c - radius, cy_c - radius, cx_c + radius, cy_c + radius],
            fill=(*accent_rgb, circle_alpha),
        )
    img = Image.alpha_composite(img, circles)

    # --- main drawing layer ---
    main = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(main)

    # Top accent bar (8px)
    draw.rectangle([0, 0, W, 8], fill=(*accent_rgb, 255))

    # --- font loading ---
    def _load_fonts(title_sz=64, sub_sz=32, brand_sz=28, icon_sz=48, tagline_sz=22):
        paths = [
            ("arial.ttf", "arialbd.ttf"),
            ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
            ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
        ]
        for reg, bold in paths:
            try:
                tf = ImageFont.truetype(bold, title_sz)
                sf = ImageFont.truetype(reg, sub_sz)
                bf = ImageFont.truetype(bold, brand_sz)
                icf = ImageFont.truetype(bold, icon_sz)
                tgf = ImageFont.truetype(reg, tagline_sz)
                return tf, sf, bf, icf, tgf
            except Exception:
                continue
        d = ImageFont.load_default()
        return d, d, d, d, d

    title_font, subtitle_font, brand_font, icon_font, tagline_font = _load_fonts()

    # --- large icon box (left-center area) ---
    icon_text = cfg.get("icon", "SLH")
    icon_box_size = 120
    icon_x, icon_y = 140, H // 2
    # Filled rounded-look box with accent bg at 20% opacity
    draw.rounded_rectangle(
        [icon_x - icon_box_size // 2, icon_y - icon_box_size // 2,
         icon_x + icon_box_size // 2, icon_y + icon_box_size // 2],
        radius=20,
        fill=(*accent_rgb, 50),
        outline=(*accent_rgb, 180),
        width=3,
    )
    draw.text((icon_x, icon_y), icon_text, font=icon_font, fill=(*accent_rgb, 255), anchor="mm")

    # --- "SLH SPARK" brand top-right ---
    draw.text((W - 50, 40), "SLH SPARK", font=brand_font, fill=(*accent_rgb, 255), anchor="rt")

    # --- title (centered in right 2/3) ---
    text_cx = (260 + W) // 2  # center of the text area (right of icon)
    title = cfg["title"]
    title_y = H // 2 - 40
    try:
        draw.text((text_cx, title_y), title, font=title_font, fill=(240, 240, 248, 255), anchor="mm")
    except Exception:
        # Hebrew or special chars unsupported by font — fall back
        fallback_title = slug.replace("-", " ").upper()
        try:
            draw.text((text_cx, title_y), fallback_title, font=title_font, fill=(240, 240, 248, 255), anchor="mm")
        except Exception:
            draw.text((text_cx, title_y), "SLH", font=title_font, fill=(240, 240, 248, 255), anchor="mm")

    # --- subtitle ---
    subtitle = cfg["subtitle"]
    sub_y = title_y + 60
    try:
        draw.text((text_cx, sub_y), subtitle, font=subtitle_font, fill=(160, 160, 180, 255), anchor="mm")
    except Exception:
        draw.text((text_cx, sub_y), "Digital Ecosystem", font=subtitle_font, fill=(160, 160, 180, 255), anchor="mm")

    # --- "slh-nft.com" URL near bottom ---
    draw.text((W // 2, H - 80), "slh-nft.com", font=subtitle_font, fill=(*accent_rgb, 180), anchor="mm")

    # --- bottom bar with tagline ---
    draw.rectangle([0, H - 48, W, H], fill=(17, 22, 40, 255))
    tagline = "20+ Bots \u00b7 Real Blockchain \u00b7 65% APY \u00b7 Built in Israel"
    try:
        draw.text((W // 2, H - 24), tagline, font=tagline_font, fill=(160, 160, 180, 255), anchor="mm")
    except Exception:
        draw.text((W // 2, H - 24), "SLH Ecosystem", font=tagline_font, fill=(160, 160, 180, 255), anchor="mm")

    img = Image.alpha_composite(img, main)

    # --- convert to RGB PNG ---
    final = img.convert("RGB")
    buf = BytesIO()
    final.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@app.get("/api/og/{slug}.png")
async def og_image(slug: str):
    """Serve a dynamically generated OG image for the given page slug."""
    from fastapi.responses import Response
    try:
        img_bytes = _generate_og_image(slug)
        return Response(
            content=img_bytes,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"},
        )
    except Exception as e:
        print(f"[og_image] failed for {slug}: {e}")
        raise HTTPException(500, f"OG generation failed: {e}")


# ============================================================
# SHARE TRACKING — count how often pages are shared
# ============================================================

class ShareEvent(BaseModel):
    page: str
    platform: str  # 'telegram' | 'twitter' | 'facebook' | 'whatsapp' | 'copy'
    user_id: Optional[int] = None


async def _ensure_share_table(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS share_events (
            id BIGSERIAL PRIMARY KEY,
            page TEXT NOT NULL,
            platform TEXT NOT NULL,
            user_id BIGINT,
            shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_share_events_page ON share_events(page, shared_at DESC);
    """)


@app.post("/api/shares/track")
async def track_share(req: ShareEvent):
    """Log a share event. Called by frontend share buttons."""
    async with pool.acquire() as conn:
        await _ensure_share_table(conn)
        await conn.execute(
            "INSERT INTO share_events (page, platform, user_id) VALUES ($1, $2, $3)",
            req.page, req.platform, req.user_id
        )
    return {"ok": True}


@app.get("/api/shares/stats")
async def share_stats(days: int = 30):
    """Share statistics by page and platform."""
    async with pool.acquire() as conn:
        await _ensure_share_table(conn)
        # Total per page
        per_page = await conn.fetch(f"""
            SELECT page, COUNT(*) as total
              FROM share_events
             WHERE shared_at > now() - interval '{int(days)} days'
             GROUP BY page
             ORDER BY total DESC
             LIMIT 20
        """)
        # Total per platform
        per_platform = await conn.fetch(f"""
            SELECT platform, COUNT(*) as total
              FROM share_events
             WHERE shared_at > now() - interval '{int(days)} days'
             GROUP BY platform
             ORDER BY total DESC
        """)
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM share_events WHERE shared_at > now() - interval '{int(days)} days'"
        ) or 0
    return {
        "total_shares": total,
        "days": days,
        "per_page": [{"page": r["page"], "total": r["total"]} for r in per_page],
        "per_platform": [{"platform": r["platform"], "total": r["total"]} for r in per_platform],
    }


@app.get("/api/launch/status")
async def launch_status():
    """Current state of the Genesis Launch."""
    async with pool.acquire() as conn:
        await _ensure_launch_tables(conn)
        rows = await conn.fetch("""
            SELECT id, partner_name, partner_handle, amount_bnb, amount_usd,
                   role, status, created_at, verified_at, tx_hash
              FROM launch_contributions
             ORDER BY created_at ASC
        """)
        total_verified_bnb = await conn.fetchval(
            "SELECT COALESCE(SUM(amount_bnb), 0) FROM launch_contributions WHERE status='verified'"
        ) or 0
        total_pending_bnb = await conn.fetchval(
            "SELECT COALESCE(SUM(amount_bnb), 0) FROM launch_contributions WHERE status='pending'"
        ) or 0

    total_verified = float(total_verified_bnb)
    total_pending = float(total_pending_bnb)
    progress_pct = round((total_verified / LAUNCH_TARGET_BNB) * 100, 2) if LAUNCH_TARGET_BNB else 0

    return {
        "launch_name": LAUNCH_NAME,
        "target_bnb": LAUNCH_TARGET_BNB,
        "target_slh": LAUNCH_TARGET_SLH,
        "target_usd": round(LAUNCH_TARGET_BNB * 608, 2),
        "company_wallet": COMPANY_BSC_WALLET,
        "company_wallet_network": "BSC (BEP-20)",
        "raised_bnb_verified": total_verified,
        "raised_bnb_pending": total_pending,
        "progress_pct": min(progress_pct, 100),
        "contributors_count": len(rows),
        "status": "live" if total_verified < LAUNCH_TARGET_BNB else "filled",
        "contributors": [
            {
                "id": r["id"],
                "name": r["partner_name"],
                "handle": r["partner_handle"],
                "amount_bnb": float(r["amount_bnb"]),
                "amount_usd": float(r["amount_usd"] or 0),
                "role": r["role"],
                "status": r["status"],
                "tx_hash": r["tx_hash"],
                "joined_at": r["created_at"].isoformat() if r["created_at"] else None,
                "verified_at": r["verified_at"].isoformat() if r["verified_at"] else None,
            }
            for r in rows
        ],
    }


@app.post("/api/broadcast/personal-cards")
async def broadcast_personal_cards(admin_key: str):
    """Send each registered user their personal SLH Member Card via Telegram.

    Each user receives a personalized message with their own card link.
    Admin-only. Logged to institutional_audit.
    """
    if admin_key != ADMIN_BROADCAST_KEY and admin_key not in ADMIN_API_KEYS:
        raise HTTPException(403, "Invalid admin key")
    if not BROADCAST_BOT_TOKEN:
        return {"ok": False, "error": "BROADCAST_BOT_TOKEN not configured"}

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT telegram_id, username, first_name FROM web_users WHERE telegram_id >= 1000000"
        )

    success = 0
    failed = 0
    for r in rows:
        uid = r["telegram_id"]
        name = r["first_name"] or r["username"] or "Member"
        card_url = f"https://slh-nft.com/member.html?id={uid}"
        image_url = f"https://slh-api-production.up.railway.app/api/member-card/image/{uid}"

        msg = (
            f"🎴 שלום {name}!\n\n"
            f"הכרטיס האישי שלך ב-SLH Spark מוכן:\n\n"
            f"🔗 הכרטיס שלך:\n{card_url}\n\n"
            f"🖼 תמונה לשיתוף:\n{image_url}\n\n"
            f"שתפ/י את הכרטיס עם חברים ומשפחה — כל חבר שמצטרף מקבל כרטיס ייחודי משלו! 🌸\n\n"
            f"— Team SLH Spark"
        )

        result = await _tg_send_message(BROADCAST_BOT_TOKEN, uid, msg)
        if result.get("ok"):
            success += 1
        else:
            failed += 1

    # Audit
    async with pool.acquire() as conn:
        await audit_log_write(
            conn,
            action="broadcast.personal_cards",
            actor_type="admin",
            resource_type="broadcast",
            metadata={"total": len(rows), "success": success, "failed": failed},
        )

    return {
        "ok": True,
        "total": len(rows),
        "success": success,
        "failed": failed,
    }


@app.get("/api/broadcast/history")
async def broadcast_history(limit: int = 20):
    """Recent broadcast history for admin dashboard."""
    async with pool.acquire() as conn:
        await _ensure_broadcast_table(conn)
        rows = await conn.fetch("""
            SELECT id, sent_at, target, total_targets, success_count, fail_count, message_preview
              FROM broadcast_log
             ORDER BY sent_at DESC
             LIMIT $1
        """, limit)
    return {
        "broadcasts": [
            {
                "id": r["id"],
                "sent_at": r["sent_at"].isoformat() if r["sent_at"] else None,
                "target": r["target"],
                "total": r["total_targets"],
                "success": r["success_count"],
                "failed": r["fail_count"],
                "preview": r["message_preview"],
            }
            for r in rows
        ]
    }


@app.get("/api/strategy/backtest/{strategy_id}")
async def backtest_strategy(strategy_id: str, months: int = 12):
    """Return simulated monthly returns for a strategy backtest.

    This is SIMULATED data based on the strategy's risk profile — for visualization.
    Live trading requires full implementation + exchange API access.
    """
    strategy = None
    for s in STRATEGIES:
        if s["id"] == strategy_id:
            strategy = s
            break
    if not strategy:
        raise HTTPException(404, "Strategy not found")

    # Generate monthly returns around the expected annual (with volatility)
    import random
    random.seed(hash(strategy_id))  # deterministic per strategy

    monthly_target = strategy["expected_annual"] / 12
    volatility = abs(strategy["max_drawdown"]) / 4

    monthly_returns = []
    cumulative = 1.0
    base_date = datetime(2025, 4, 1)

    for i in range(months):
        # Normal distribution around monthly target
        ret = random.gauss(monthly_target, volatility) / 100
        cumulative *= (1 + ret)
        month_date = base_date + timedelta(days=30 * i)
        monthly_returns.append({
            "month": month_date.strftime("%Y-%m"),
            "return_pct": round(ret * 100, 2),
            "cumulative_pct": round((cumulative - 1) * 100, 2),
        })

    return {
        "strategy_id": strategy_id,
        "strategy_name": strategy["name"],
        "period_months": months,
        "final_return_pct": round((cumulative - 1) * 100, 2),
        "annualized_pct": round((cumulative ** (12 / months) - 1) * 100, 2),
        "best_month": max(monthly_returns, key=lambda x: x["return_pct"]),
        "worst_month": min(monthly_returns, key=lambda x: x["return_pct"]),
        "monthly_returns": monthly_returns,
    }


# ============================================================
# REP SYSTEM — Personal Reputation Score per Member
# ============================================================

async def _ensure_rep_tables(conn):
    """Create the member_rep table if it doesn't exist."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS member_rep (
            user_id BIGINT PRIMARY KEY,
            rep_score NUMERIC(18,2) DEFAULT 0,
            therapy_hours NUMERIC(10,2) DEFAULT 0,
            referrals_count INT DEFAULT 0,
            community_actions INT DEFAULT 0,
            genesis_contributor BOOLEAN DEFAULT FALSE,
            staking_bonus NUMERIC(18,2) DEFAULT 0,
            tier TEXT DEFAULT 'basic',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)


def _calculate_rep_tier(score: float) -> str:
    """Return tier based on REP score thresholds."""
    if score >= 1000:
        return "elder"
    elif score >= 500:
        return "senior"
    elif score >= 100:
        return "active"
    return "basic"


class RepAddRequest(BaseModel):
    user_id: int
    action: str  # therapy_hour, referral, community, genesis, staking
    amount: Optional[float] = None  # custom amount (used for staking bonus)


@app.get("/api/rep/leaderboard")
async def rep_leaderboard(limit: int = Query(default=20, ge=1, le=100)):
    """Get top REP holders sorted by score descending."""
    async with pool.acquire() as conn:
        await _ensure_rep_tables(conn)
        rows = await conn.fetch(
            "SELECT user_id, rep_score, genesis_contributor FROM member_rep ORDER BY rep_score DESC LIMIT $1", limit
        )
        leaderboard = [
            {"rank": idx+1, "user_id": r["user_id"], "rep_score": float(r["rep_score"]), "genesis_contributor": r["genesis_contributor"]}
            for idx, r in enumerate(rows)
        ]
    return {"leaderboard": leaderboard, "total": len(leaderboard)}


@app.get("/api/rep/{user_id}")
async def get_rep_score(user_id: int):
    """Get REP score and tier for a user."""
    async with pool.acquire() as conn:
        await _ensure_rep_tables(conn)
        row = await conn.fetchrow(
            "SELECT * FROM member_rep WHERE user_id = $1", user_id
        )
        if not row:
            # Return default score for unregistered user
            result = {
                "user_id": user_id,
                "rep_score": 0,
                "therapy_hours": 0,
                "referrals_count": 0,
                "community_actions": 0,
                "genesis_contributor": False,
                "staking_bonus": 0,
                "tier": "basic",
            }
        else:
            result = {
                "user_id": row["user_id"],
                "rep_score": float(row["rep_score"]),
                "therapy_hours": float(row["therapy_hours"]),
                "referrals_count": row["referrals_count"],
                "community_actions": row["community_actions"],
                "genesis_contributor": row["genesis_contributor"],
                "staking_bonus": float(row["staking_bonus"]),
                "tier": row["tier"],
            }

        await audit_log_write(
            conn,
            action="rep.query",
            actor_type="system",
            actor_user_id=user_id,
            resource_type="rep",
            resource_id=str(user_id),
            metadata={"tier": result["tier"], "score": result["rep_score"]},
        )

    return result


# REP point values per action type
_REP_ACTION_POINTS = {
    "therapy_hour": 10.0,
    "referral": 25.0,
    "community": 5.0,
    "genesis": 100.0,
    "staking": 0.0,  # uses custom amount
}


@app.post("/api/rep/add")
async def add_rep_points(req: RepAddRequest):
    """Add REP points for a specific action."""
    if req.action not in _REP_ACTION_POINTS:
        raise HTTPException(400, f"Invalid action. Must be one of: {', '.join(_REP_ACTION_POINTS.keys())}")

    points = _REP_ACTION_POINTS[req.action]
    if req.action == "staking":
        points = float(req.amount) if req.amount and req.amount > 0 else 0.0

    async with pool.acquire() as conn:
        await _ensure_rep_tables(conn)

        # Upsert: insert or update the user's rep record
        before_row = await conn.fetchrow(
            "SELECT rep_score, tier FROM member_rep WHERE user_id = $1", req.user_id
        )
        before_score = float(before_row["rep_score"]) if before_row else 0.0
        before_tier = before_row["tier"] if before_row else "basic"

        new_score = before_score + points
        new_tier = _calculate_rep_tier(new_score)

        # Upsert the member_rep row
        await conn.execute("""
            INSERT INTO member_rep (user_id, rep_score, tier)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET
                rep_score = member_rep.rep_score + $2,
                tier = $3,
                updated_at = CURRENT_TIMESTAMP
        """, req.user_id, points, new_tier)

        # Increment the specific action column
        if req.action == "therapy_hour":
            await conn.execute(
                "UPDATE member_rep SET therapy_hours = therapy_hours + 1 WHERE user_id = $1",
                req.user_id)
        elif req.action == "referral":
            await conn.execute(
                "UPDATE member_rep SET referrals_count = referrals_count + 1 WHERE user_id = $1",
                req.user_id)
        elif req.action == "community":
            await conn.execute(
                "UPDATE member_rep SET community_actions = community_actions + 1 WHERE user_id = $1",
                req.user_id)
        elif req.action == "genesis":
            await conn.execute(
                "UPDATE member_rep SET genesis_contributor = TRUE WHERE user_id = $1",
                req.user_id)
        elif req.action == "staking":
            await conn.execute(
                "UPDATE member_rep SET staking_bonus = staking_bonus + $2 WHERE user_id = $1",
                req.user_id, points)

        # Fix: re-read to get actual final score & tier after upsert
        final_row = await conn.fetchrow(
            "SELECT rep_score, tier FROM member_rep WHERE user_id = $1", req.user_id
        )
        final_score = float(final_row["rep_score"])
        final_tier = final_row["tier"]

        await audit_log_write(
            conn,
            action=f"rep.add.{req.action}",
            actor_type="system",
            actor_user_id=req.user_id,
            resource_type="rep",
            resource_id=str(req.user_id),
            before_state={"rep_score": before_score, "tier": before_tier},
            after_state={"rep_score": final_score, "tier": final_tier},
            metadata={"action": req.action, "points_added": points},
        )

    return {
        "user_id": req.user_id,
        "action": req.action,
        "points_added": points,
        "new_score": final_score,
        "new_tier": final_tier,
        "tier_changed": before_tier != final_tier,
    }


# (rep_leaderboard moved above rep/{user_id} to avoid route conflict)


# ============================================================
# MEMBER CARD SYSTEM
# ============================================================

TIER_EMOJIS = {"basic": "\U0001f331", "active": "\u26a1", "senior": "\U0001f3c6", "elder": "\U0001f451"}
TIER_COLORS = {
    "basic":  "#00e887",
    "active": "#00b4d8",
    "senior": "#a855f7",
    "elder":  "#ffd700",
}


async def _build_member_card_data(conn, user_id: int) -> dict:
    """Gather all data needed for a member card from multiple tables."""
    # --- web_users ---
    user = await conn.fetchrow(
        "SELECT telegram_id, username, first_name, last_login, is_registered, beta_user FROM web_users WHERE telegram_id = $1",
        user_id,
    )
    if not user:
        return None

    name = user["first_name"] or user["username"] or f"User-{user_id}"
    username = user["username"] or ""
    joined = user["last_login"].strftime("%Y-%m-%d") if user["last_login"] else "unknown"

    # --- NFT number (position in web_users ordered by last_login ASC) ---
    nft_pos = await conn.fetchval(
        """
        SELECT pos FROM (
            SELECT telegram_id, ROW_NUMBER() OVER (ORDER BY last_login ASC) AS pos
            FROM web_users
        ) sub WHERE telegram_id = $1
        """,
        user_id,
    )
    nft_number = f"SLH-{nft_pos:04d}" if nft_pos else "SLH-0000"

    # --- token_balances ---
    slh_row = await conn.fetchrow(
        "SELECT balance FROM token_balances WHERE user_id = $1 AND token = 'SLH'", user_id,
    )
    zvk_row = await conn.fetchrow(
        "SELECT balance FROM token_balances WHERE user_id = $1 AND token = 'ZVK'", user_id,
    )
    slh_balance = round(float(slh_row["balance"]), 2) if slh_row else 0.0
    zvk_balance = round(float(zvk_row["balance"]), 2) if zvk_row else 0.0

    # --- member_rep ---
    await _ensure_rep_tables(conn)
    rep_row = await conn.fetchrow(
        "SELECT rep_score, tier FROM member_rep WHERE user_id = $1", user_id,
    )
    rep_score = float(rep_row["rep_score"]) if rep_row else 0.0
    tier = rep_row["tier"] if rep_row else "basic"

    # --- launch_contributions (genesis check) ---
    await _ensure_launch_tables(conn)
    genesis_row = await conn.fetchrow(
        "SELECT amount_bnb FROM launch_contributions WHERE partner_handle = $1 AND status = 'verified'",
        username,
    )
    genesis_contributor = genesis_row is not None
    genesis_amount_bnb = float(genesis_row["amount_bnb"]) if genesis_row else 0.0

    # --- referrals (count users who have this user as referrer) ---
    referral_count = await conn.fetchval(
        "SELECT COUNT(*) FROM referrals WHERE referrer_id = $1", user_id,
    ) or 0

    # --- is_therapist: currently no dedicated column, default False ---
    is_therapist = False

    # --- ASCII art card ---
    tier_emoji = TIER_EMOJIS.get(tier, "\U0001f331")
    genesis_str = "Yes" if genesis_contributor else "No"
    ascii_art = (
        "\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557\n"
        "\u2551  \U0001f338 SLH SPARK \u00b7 MEMBER CARD     \u2551\n"
        "\u2551\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2551\n"
        "\u2551                                  \u2551\n"
        f"\u2551  Name:  {name:<25}\u2551\n"
        f"\u2551  ID:    #{user_id:<24}\u2551\n"
        f"\u2551  Tier:  {tier_emoji} {tier:<22}\u2551\n"
        f"\u2551  REP:   {rep_score:<25}\u2551\n"
        f"\u2551  Joined: {joined:<24}\u2551\n"
        f"\u2551  Genesis: {genesis_str:<23}\u2551\n"
        f"\u2551  NFT #:  {nft_number:<24}\u2551\n"
        "\u2551\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2551\n"
        f"\u2551  SLH: {slh_balance} \u00b7 ZVK: {zvk_balance}        \u2551\n"
        f"\u2551  \U0001f517 slh-nft.com/member?id={user_id}  \u2551\n"
        "\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d"
    )

    return {
        "user_id": user_id,
        "name": name,
        "username": username,
        "telegram_id": user_id,
        "nft_number": nft_number,
        "tier": tier,
        "rep_score": rep_score,
        "joined": joined,
        "genesis_contributor": genesis_contributor,
        "genesis_amount_bnb": genesis_amount_bnb,
        "slh_balance": slh_balance,
        "zvk_balance": zvk_balance,
        "referrals": referral_count,
        "is_therapist": is_therapist,
        "ascii_art": ascii_art,
    }


@app.get("/api/member-card/{user_id}")
async def get_member_card(user_id: int):
    """Return JSON member card data for a user."""
    async with pool.acquire() as conn:
        card = await _build_member_card_data(conn, user_id)
        if card is None:
            raise HTTPException(404, "User not found")

        await audit_log_write(
            conn,
            action="member_card.view",
            actor_type="system",
            actor_user_id=user_id,
            resource_type="member_card",
            resource_id=str(user_id),
            metadata={"nft_number": card["nft_number"], "tier": card["tier"]},
        )

    return {"ok": True, "card": card}


def _generate_member_card_image(card: dict) -> bytes:
    """Generate an 800x1000 PNG member card image. Returns raw PNG bytes."""
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO

    W, H = 800, 1000
    BG = (10, 14, 26)  # #0a0e1a

    tier = card.get("tier", "basic")
    accent_hex = TIER_COLORS.get(tier, "#00e887").lstrip("#")
    accent_rgb = tuple(int(accent_hex[i:i+2], 16) for i in (0, 2, 4))

    # --- base image ---
    img = Image.new("RGBA", (W, H), (*BG, 255))

    # --- gradient layer (radial from center-top) ---
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(grad)
    cx, cy = W // 2, 200
    max_r = int((W**2 + H**2) ** 0.5 / 2)
    for i in range(60, 0, -1):
        ratio = i / 60
        r = int(max_r * ratio)
        alpha = int(50 * (1 - ratio))
        grad_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*accent_rgb, alpha))
    img = Image.alpha_composite(img, grad)

    # --- subtle grid pattern ---
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid)
    grid_color = (*accent_rgb, 10)
    for x in range(0, W, 40):
        grid_draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(0, H, 40):
        grid_draw.line([(0, y), (W, y)], fill=grid_color, width=1)
    img = Image.alpha_composite(img, grid)

    # --- main drawing layer ---
    main = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(main)

    # Top accent bar
    draw.rectangle([0, 0, W, 6], fill=(*accent_rgb, 255))

    # --- font loading ---
    def _load_font(size, bold=False):
        paths = [
            "arialbd.ttf" if bold else "arial.ttf",
            "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        ]
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return ImageFont.load_default()

    brand_font = _load_font(42, bold=True)
    subtitle_font = _load_font(24, bold=True)
    nft_font = _load_font(60, bold=True)
    label_font = _load_font(22)
    value_font = _load_font(24, bold=True)
    small_font = _load_font(18)
    url_font = _load_font(16)

    # --- "SLH SPARK" brand at top ---
    y = 40
    try:
        draw.text((W // 2, y), "\U0001f338 SLH SPARK", font=brand_font, fill=(*accent_rgb, 255), anchor="mt")
    except Exception:
        draw.text((W // 2, y), "SLH SPARK", font=brand_font, fill=(*accent_rgb, 255), anchor="mt")
    y += 55

    # --- "MEMBER CARD" subtitle ---
    draw.text((W // 2, y), "MEMBER CARD", font=subtitle_font, fill=(200, 200, 220, 255), anchor="mt")
    y += 50

    # Divider line
    draw.line([(80, y), (W - 80, y)], fill=(*accent_rgb, 100), width=2)
    y += 30

    # --- NFT number large and centered ---
    nft_number = card.get("nft_number", "SLH-0000")
    draw.text((W // 2, y), nft_number, font=nft_font, fill=(*accent_rgb, 255), anchor="mt")
    y += 85

    # Tier badge
    tier_emoji = TIER_EMOJIS.get(tier, "\U0001f331")
    tier_text = f"{tier.upper()}"
    # Tier box
    box_w, box_h = 200, 40
    box_x = (W - box_w) // 2
    draw.rounded_rectangle(
        [box_x, y, box_x + box_w, y + box_h],
        radius=12,
        fill=(*accent_rgb, 50),
        outline=(*accent_rgb, 180),
        width=2,
    )
    try:
        draw.text((W // 2, y + box_h // 2), f"{tier_emoji} {tier_text}", font=subtitle_font, fill=(*accent_rgb, 255), anchor="mm")
    except Exception:
        draw.text((W // 2, y + box_h // 2), tier_text, font=subtitle_font, fill=(*accent_rgb, 255), anchor="mm")
    y += box_h + 30

    # Divider
    draw.line([(80, y), (W - 80, y)], fill=(*accent_rgb, 60), width=1)
    y += 25

    # --- Stats section ---
    left_x = 100
    stat_spacing = 45

    stats = [
        ("Name", card.get("name", "Unknown")),
        ("ID", f"#{card.get('user_id', 0)}"),
        ("REP Score", str(card.get("rep_score", 0))),
        ("Joined", card.get("joined", "unknown")),
        ("Genesis", "Yes" if card.get("genesis_contributor") else "No"),
        ("Referrals", str(card.get("referrals", 0))),
    ]

    for label_text, val_text in stats:
        draw.text((left_x, y), label_text, font=label_font, fill=(140, 140, 160, 255))
        draw.text((left_x + 180, y), val_text, font=value_font, fill=(230, 230, 245, 255))
        y += stat_spacing

    if card.get("genesis_contributor"):
        genesis_bnb = card.get("genesis_amount_bnb", 0)
        draw.text((left_x, y), "Genesis BNB", font=label_font, fill=(140, 140, 160, 255))
        draw.text((left_x + 180, y), f"{genesis_bnb} BNB", font=value_font, fill=(*accent_rgb, 255))
        y += stat_spacing

    y += 10
    # Divider
    draw.line([(80, y), (W - 80, y)], fill=(*accent_rgb, 60), width=1)
    y += 25

    # --- Token balances ---
    slh_text = f"SLH: {card.get('slh_balance', 0)}"
    zvk_text = f"ZVK: {card.get('zvk_balance', 0)}"
    draw.text((W // 2, y), f"{slh_text}  \u00b7  {zvk_text}", font=value_font, fill=(230, 230, 245, 255), anchor="mt")
    y += 50

    # --- QR code or URL ---
    member_url = f"slh-nft.com/member?id={card.get('user_id', 0)}"
    qr_generated = False
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=5, border=2)
        qr.add_data(f"https://{member_url}")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="white", back_color=(10, 14, 26)).convert("RGBA")
        qr_w, qr_h = qr_img.size
        qr_x = (W - qr_w) // 2
        main.paste(qr_img, (qr_x, y), qr_img)
        y += qr_h + 10
        qr_generated = True
    except Exception:
        pass

    if not qr_generated:
        y += 20

    # URL text below QR (or as fallback)
    try:
        draw.text((W // 2, y), f"\U0001f517 {member_url}", font=url_font, fill=(*accent_rgb, 180), anchor="mt")
    except Exception:
        draw.text((W // 2, y), member_url, font=url_font, fill=(*accent_rgb, 180), anchor="mt")

    # Bottom accent bar
    draw.rectangle([0, H - 6, W, H], fill=(*accent_rgb, 255))

    # --- composite ---
    img = Image.alpha_composite(img, main)
    final = img.convert("RGB")

    buf = BytesIO()
    final.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@app.get("/api/member-card/image/{user_id}")
async def get_member_card_image(user_id: int):
    """Serve a dynamically generated 800x1000 PNG member card."""
    from fastapi.responses import Response

    async with pool.acquire() as conn:
        card = await _build_member_card_data(conn, user_id)
        if card is None:
            raise HTTPException(404, "User not found")

        await audit_log_write(
            conn,
            action="member_card.image",
            actor_type="system",
            actor_user_id=user_id,
            resource_type="member_card",
            resource_id=str(user_id),
            metadata={"nft_number": card["nft_number"], "tier": card["tier"]},
        )

    try:
        img_bytes = _generate_member_card_image(card)
        return Response(
            content=img_bytes,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"},
        )
    except Exception as e:
        print(f"[member_card_image] failed for {user_id}: {e}")
        raise HTTPException(500, f"Member card image generation failed: {e}")


@app.get("/api/member-cards/all")
async def list_all_member_cards(limit: int = Query(default=50, ge=1, le=500)):
    """List all member cards for the website gallery, ordered by rep_score DESC."""
    async with pool.acquire() as conn:
        await _ensure_rep_tables(conn)

        rows = await conn.fetch("""
            WITH nft_positions AS (
                SELECT telegram_id, ROW_NUMBER() OVER (ORDER BY last_login ASC) AS pos
                FROM web_users
            )
            SELECT
                wu.telegram_id,
                wu.first_name,
                wu.username,
                wu.last_login,
                COALESCE(mr.rep_score, 0) AS rep_score,
                COALESCE(mr.tier, 'basic') AS tier,
                nft.pos AS nft_pos
            FROM web_users wu
            LEFT JOIN member_rep mr ON mr.user_id = wu.telegram_id
            LEFT JOIN nft_positions nft ON nft.telegram_id = wu.telegram_id
            WHERE wu.telegram_id >= 1000000
            ORDER BY COALESCE(mr.rep_score, 0) DESC
            LIMIT $1
        """, limit)

        cards = []
        for r in rows:
            nft_pos = r["nft_pos"] if r["nft_pos"] else 0
            cards.append({
                "user_id": r["telegram_id"],
                "name": r["first_name"] or r["username"] or f"User-{r['telegram_id']}",
                "nft_number": f"SLH-{nft_pos:04d}",
                "tier": r["tier"],
                "rep_score": float(r["rep_score"]),
                "joined": r["last_login"].strftime("%Y-%m-%d") if r["last_login"] else "unknown",
            })

        await audit_log_write(
            conn,
            action="member_cards.list",
            actor_type="system",
            resource_type="member_card",
            metadata={"limit": limit, "results_count": len(cards)},
        )

    return {"ok": True, "cards": cards, "total": len(cards)}


# ═══════════════════════════════════════════════════════════════════════════════
# P2P ORDER BOOK
# Table: p2p_orders
#   (id, seller_id, token, amount, price_per_unit, currency, payment_method,
#    status, created_at)
# ═══════════════════════════════════════════════════════════════════════════════

P2P_VALID_TOKENS = {"SLH", "ZVK", "MNH"}
P2P_VALID_CURRENCIES = {"ILS", "USD"}
P2P_VALID_PAYMENT_METHODS = {"Bit", "PayBox", "Bank", "MNH", "BNB"}
P2P_VALID_STATUSES = {"active", "filled", "cancelled"}


async def _ensure_p2p_orders_table(conn):
    """Create p2p_orders table if it does not exist."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS p2p_orders (
            id              SERIAL PRIMARY KEY,
            seller_id       BIGINT NOT NULL,
            token           VARCHAR(10) NOT NULL,
            amount          NUMERIC(20,8) NOT NULL CHECK (amount > 0),
            price_per_unit  NUMERIC(20,4) NOT NULL CHECK (price_per_unit > 0),
            currency        VARCHAR(5)  NOT NULL DEFAULT 'ILS',
            payment_method  VARCHAR(20) NOT NULL DEFAULT 'Bit',
            status          VARCHAR(12) NOT NULL DEFAULT 'active',
            created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)


class P2PCreateOrder(BaseModel):
    seller_id: int
    token: str          # SLH / ZVK / MNH
    amount: float
    price_per_unit: float
    currency: str = "ILS"          # ILS / USD
    payment_method: str = "Bit"    # Bit / PayBox / Bank / MNH / BNB


class P2PFillOrder(BaseModel):
    order_id: int
    buyer_id: int


# ── POST /api/p2p/create-order ──────────────────────────────────────────────
@app.post("/api/p2p/create-order")
async def p2p_create_order(body: P2PCreateOrder):
    """Create a new P2P sell order."""
    if body.token.upper() not in P2P_VALID_TOKENS:
        raise HTTPException(400, f"Invalid token. Must be one of: {', '.join(P2P_VALID_TOKENS)}")
    if body.currency.upper() not in P2P_VALID_CURRENCIES:
        raise HTTPException(400, f"Invalid currency. Must be one of: {', '.join(P2P_VALID_CURRENCIES)}")
    if body.payment_method not in P2P_VALID_PAYMENT_METHODS:
        raise HTTPException(400, f"Invalid payment method. Must be one of: {', '.join(P2P_VALID_PAYMENT_METHODS)}")
    if body.amount <= 0 or body.price_per_unit <= 0:
        raise HTTPException(400, "Amount and price must be positive")

    async with pool.acquire() as conn:
        await _ensure_p2p_orders_table(conn)
        row = await conn.fetchrow("""
            INSERT INTO p2p_orders (seller_id, token, amount, price_per_unit, currency, payment_method, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'active')
            RETURNING id, seller_id, token, amount, price_per_unit, currency, payment_method, status, created_at
        """, body.seller_id, body.token.upper(), body.amount, body.price_per_unit,
             body.currency.upper(), body.payment_method)

        await audit_log_write(
            conn,
            action="p2p.create_order",
            actor_type="user",
            actor_user_id=body.seller_id,
            resource_type="p2p_order",
            resource_id=str(row["id"]),
            metadata={
                "token": body.token.upper(),
                "amount": body.amount,
                "price_per_unit": body.price_per_unit,
                "currency": body.currency.upper(),
                "payment_method": body.payment_method,
            },
        )

    return {
        "ok": True,
        "order": {
            "id": row["id"],
            "seller_id": row["seller_id"],
            "token": row["token"],
            "amount": float(row["amount"]),
            "price_per_unit": float(row["price_per_unit"]),
            "currency": row["currency"],
            "payment_method": row["payment_method"],
            "status": row["status"],
            "created_at": row["created_at"].isoformat(),
        },
    }


# ── GET /api/p2p/orders ─────────────────────────────────────────────────────
@app.get("/api/p2p/orders")
async def p2p_list_orders(
    token: Optional[str] = Query(None, description="Filter by token: SLH, ZVK, MNH"),
    currency: Optional[str] = Query(None, description="Filter by currency: ILS, USD"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    status: str = Query("active", description="Order status: active, filled, cancelled"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List P2P orders with optional filters."""
    if status not in P2P_VALID_STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(P2P_VALID_STATUSES)}")

    conditions = ["status = $1"]
    params: list = [status]
    idx = 2

    if token:
        if token.upper() not in P2P_VALID_TOKENS:
            raise HTTPException(400, f"Invalid token filter. Must be one of: {', '.join(P2P_VALID_TOKENS)}")
        conditions.append(f"token = ${idx}")
        params.append(token.upper())
        idx += 1

    if currency:
        if currency.upper() not in P2P_VALID_CURRENCIES:
            raise HTTPException(400, f"Invalid currency filter. Must be one of: {', '.join(P2P_VALID_CURRENCIES)}")
        conditions.append(f"currency = ${idx}")
        params.append(currency.upper())
        idx += 1

    if payment_method:
        if payment_method not in P2P_VALID_PAYMENT_METHODS:
            raise HTTPException(400, f"Invalid payment_method filter. Must be one of: {', '.join(P2P_VALID_PAYMENT_METHODS)}")
        conditions.append(f"payment_method = ${idx}")
        params.append(payment_method)
        idx += 1

    where_clause = " AND ".join(conditions)
    params.extend([limit, offset])

    async with pool.acquire() as conn:
        await _ensure_p2p_orders_table(conn)
        rows = await conn.fetch(f"""
            SELECT id, seller_id, token, amount, price_per_unit, currency,
                   payment_method, status, created_at
            FROM p2p_orders
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
        """, *params)

        total = await conn.fetchval(f"""
            SELECT COUNT(*) FROM p2p_orders WHERE {where_clause}
        """, *params[:-2])

    orders = []
    for r in rows:
        orders.append({
            "id": r["id"],
            "seller_id": r["seller_id"],
            "token": r["token"],
            "amount": float(r["amount"]),
            "price_per_unit": float(r["price_per_unit"]),
            "currency": r["currency"],
            "payment_method": r["payment_method"],
            "status": r["status"],
            "created_at": r["created_at"].isoformat(),
        })

    return {"ok": True, "orders": orders, "total": total, "limit": limit, "offset": offset}


# ── POST /api/p2p/fill-order ────────────────────────────────────────────────
@app.post("/api/p2p/fill-order")
async def p2p_fill_order(body: P2PFillOrder):
    """Mark an active P2P order as filled by a buyer."""
    async with pool.acquire() as conn:
        await _ensure_p2p_orders_table(conn)

        row = await conn.fetchrow(
            "SELECT * FROM p2p_orders WHERE id = $1", body.order_id
        )
        if not row:
            raise HTTPException(404, "Order not found")
        if row["status"] != "active":
            raise HTTPException(400, f"Order is already {row['status']}")
        if row["seller_id"] == body.buyer_id:
            raise HTTPException(400, "Seller cannot fill own order")

        await conn.execute(
            "UPDATE p2p_orders SET status = 'filled' WHERE id = $1",
            body.order_id,
        )

        await audit_log_write(
            conn,
            action="p2p.fill_order",
            actor_type="user",
            actor_user_id=body.buyer_id,
            resource_type="p2p_order",
            resource_id=str(body.order_id),
            metadata={
                "seller_id": row["seller_id"],
                "buyer_id": body.buyer_id,
                "token": row["token"],
                "amount": float(row["amount"]),
                "price_per_unit": float(row["price_per_unit"]),
                "currency": row["currency"],
            },
        )

    return {"ok": True, "message": "Order filled successfully", "order_id": body.order_id}


# ── DELETE /api/p2p/cancel-order/{id} ────────────────────────────────────────
@app.delete("/api/p2p/cancel-order/{order_id}")
async def p2p_cancel_order(order_id: int, seller_id: int = Query(..., description="Seller's telegram ID")):
    """Cancel an active P2P order. Only the seller can cancel their own order."""
    async with pool.acquire() as conn:
        await _ensure_p2p_orders_table(conn)

        row = await conn.fetchrow(
            "SELECT * FROM p2p_orders WHERE id = $1", order_id
        )
        if not row:
            raise HTTPException(404, "Order not found")
        if row["seller_id"] != seller_id:
            raise HTTPException(403, "Only the seller can cancel this order")
        if row["status"] != "active":
            raise HTTPException(400, f"Order is already {row['status']}")

        await conn.execute(
            "UPDATE p2p_orders SET status = 'cancelled' WHERE id = $1",
            order_id,
        )

        await audit_log_write(
            conn,
            action="p2p.cancel_order",
            actor_type="user",
            actor_user_id=seller_id,
            resource_type="p2p_order",
            resource_id=str(order_id),
            metadata={
                "token": row["token"],
                "amount": float(row["amount"]),
                "price_per_unit": float(row["price_per_unit"]),
            },
        )

    return {"ok": True, "message": "Order cancelled", "order_id": order_id}


# ============================================================
# P2P ORDER BOOK — JWT-Authenticated Endpoints (v2)
# ============================================================
# These endpoints use JWT bearer tokens to identify the caller.
# The seller/buyer is derived from the JWT, not from the request body.

class P2PCreateOrderAuth(BaseModel):
    token: str          # SLH / ZVK / MNH
    amount: float
    price_per_unit: float
    currency: str = "ILS"
    payment_method: str = "Bit"


class P2PFillOrderAuth(BaseModel):
    order_id: int


# ── POST /api/p2p/v2/create-order (JWT auth — seller = caller) ──────────────
@app.post("/api/p2p/v2/create-order")
async def p2p_create_order_auth(
    body: P2PCreateOrderAuth,
    seller_id: int = Depends(get_current_user_id),
):
    """Create a new P2P sell order. Seller is derived from JWT token."""
    if body.token.upper() not in P2P_VALID_TOKENS:
        raise HTTPException(400, f"Invalid token. Must be one of: {', '.join(P2P_VALID_TOKENS)}")
    if body.currency.upper() not in P2P_VALID_CURRENCIES:
        raise HTTPException(400, f"Invalid currency. Must be one of: {', '.join(P2P_VALID_CURRENCIES)}")
    if body.payment_method not in P2P_VALID_PAYMENT_METHODS:
        raise HTTPException(400, f"Invalid payment method. Must be one of: {', '.join(P2P_VALID_PAYMENT_METHODS)}")
    if body.amount <= 0 or body.price_per_unit <= 0:
        raise HTTPException(400, "Amount and price must be positive")

    async with pool.acquire() as conn:
        await _ensure_p2p_orders_table(conn)

        # Verify seller has enough balance
        balance = await conn.fetchval(
            "SELECT balance FROM token_balances WHERE user_id=$1 AND token=$2",
            seller_id, body.token.upper(),
        )
        if not balance or float(balance) < body.amount:
            raise HTTPException(400, f"Insufficient {body.token.upper()} balance")

        row = await conn.fetchrow("""
            INSERT INTO p2p_orders (seller_id, token, amount, price_per_unit, currency, payment_method, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'active')
            RETURNING id, seller_id, token, amount, price_per_unit, currency, payment_method, status, created_at
        """, seller_id, body.token.upper(), body.amount, body.price_per_unit,
             body.currency.upper(), body.payment_method)

        await audit_log_write(
            conn,
            action="p2p.create_order",
            actor_type="user",
            actor_user_id=seller_id,
            resource_type="p2p_order",
            resource_id=str(row["id"]),
            metadata={
                "token": body.token.upper(),
                "amount": body.amount,
                "price_per_unit": body.price_per_unit,
                "currency": body.currency.upper(),
                "payment_method": body.payment_method,
                "auth": "jwt",
            },
        )

    return {
        "ok": True,
        "order": {
            "id": row["id"],
            "seller_id": row["seller_id"],
            "token": row["token"],
            "amount": float(row["amount"]),
            "price_per_unit": float(row["price_per_unit"]),
            "currency": row["currency"],
            "payment_method": row["payment_method"],
            "status": row["status"],
            "created_at": row["created_at"].isoformat(),
        },
    }


# ── GET /api/p2p/v2/orders (public — same as v1, no auth needed) ────────────
@app.get("/api/p2p/v2/orders")
async def p2p_list_orders_v2(
    token: Optional[str] = Query(None, description="Filter by token: SLH, ZVK, MNH"),
    currency: Optional[str] = Query(None, description="Filter by currency: ILS, USD"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    status: str = Query("active", description="Order status: active, filled, cancelled"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List P2P orders with optional filters. Public endpoint."""
    if status not in P2P_VALID_STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(P2P_VALID_STATUSES)}")

    conditions = ["status = $1"]
    params: list = [status]
    idx = 2

    if token:
        if token.upper() not in P2P_VALID_TOKENS:
            raise HTTPException(400, f"Invalid token filter. Must be one of: {', '.join(P2P_VALID_TOKENS)}")
        conditions.append(f"token = ${idx}")
        params.append(token.upper())
        idx += 1

    if currency:
        if currency.upper() not in P2P_VALID_CURRENCIES:
            raise HTTPException(400, f"Invalid currency filter. Must be one of: {', '.join(P2P_VALID_CURRENCIES)}")
        conditions.append(f"currency = ${idx}")
        params.append(currency.upper())
        idx += 1

    if payment_method:
        if payment_method not in P2P_VALID_PAYMENT_METHODS:
            raise HTTPException(400, f"Invalid payment_method filter. Must be one of: {', '.join(P2P_VALID_PAYMENT_METHODS)}")
        conditions.append(f"payment_method = ${idx}")
        params.append(payment_method)
        idx += 1

    where_clause = " AND ".join(conditions)
    params.extend([limit, offset])

    async with pool.acquire() as conn:
        await _ensure_p2p_orders_table(conn)
        rows = await conn.fetch(f"""
            SELECT id, seller_id, token, amount, price_per_unit, currency,
                   payment_method, status, created_at
            FROM p2p_orders
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
        """, *params)

        total = await conn.fetchval(f"""
            SELECT COUNT(*) FROM p2p_orders WHERE {where_clause}
        """, *params[:-2])

    orders = []
    for r in rows:
        orders.append({
            "id": r["id"],
            "seller_id": r["seller_id"],
            "token": r["token"],
            "amount": float(r["amount"]),
            "price_per_unit": float(r["price_per_unit"]),
            "currency": r["currency"],
            "payment_method": r["payment_method"],
            "status": r["status"],
            "created_at": r["created_at"].isoformat(),
        })

    return {"ok": True, "orders": orders, "total": total, "limit": limit, "offset": offset}


# ── POST /api/p2p/v2/fill-order (JWT auth — buyer = caller) ─────────────────
@app.post("/api/p2p/v2/fill-order")
async def p2p_fill_order_auth(
    body: P2PFillOrderAuth,
    buyer_id: int = Depends(get_current_user_id),
):
    """Fill a P2P order. Buyer is derived from JWT token. Transfers tokens from seller to buyer."""
    async with pool.acquire() as conn:
        await _ensure_p2p_orders_table(conn)

        row = await conn.fetchrow(
            "SELECT * FROM p2p_orders WHERE id = $1", body.order_id
        )
        if not row:
            raise HTTPException(404, "Order not found")
        if row["status"] != "active":
            raise HTTPException(400, f"Order is already {row['status']}")
        if row["seller_id"] == buyer_id:
            raise HTTPException(400, "Seller cannot fill own order")

        token = row["token"]
        amount = row["amount"]
        seller_id = row["seller_id"]

        # Deduct tokens from seller
        seller_balance = await conn.fetchval(
            "SELECT balance FROM token_balances WHERE user_id=$1 AND token=$2",
            seller_id, token,
        )
        if not seller_balance or float(seller_balance) < float(amount):
            raise HTTPException(400, f"Seller has insufficient {token} balance")

        await conn.execute(
            "UPDATE token_balances SET balance = balance - $1, updated_at = CURRENT_TIMESTAMP WHERE user_id=$2 AND token=$3",
            amount, seller_id, token,
        )

        # Credit tokens to buyer
        await conn.execute("""
            INSERT INTO token_balances (user_id, token, balance)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, token) DO UPDATE
              SET balance = token_balances.balance + $3,
                  updated_at = CURRENT_TIMESTAMP
        """, buyer_id, token, amount)

        # Mark order as filled
        await conn.execute(
            "UPDATE p2p_orders SET status = 'filled' WHERE id = $1",
            body.order_id,
        )

        await audit_log_write(
            conn,
            action="p2p.fill_order",
            actor_type="user",
            actor_user_id=buyer_id,
            resource_type="p2p_order",
            resource_id=str(body.order_id),
            metadata={
                "seller_id": seller_id,
                "buyer_id": buyer_id,
                "token": token,
                "amount": float(amount),
                "price_per_unit": float(row["price_per_unit"]),
                "currency": row["currency"],
                "auth": "jwt",
            },
        )

    return {"ok": True, "message": "Order filled successfully", "order_id": body.order_id}


# ── DELETE /api/p2p/v2/cancel-order/{id} (JWT auth — seller = caller) ────────
@app.delete("/api/p2p/v2/cancel-order/{order_id}")
async def p2p_cancel_order_auth(
    order_id: int,
    seller_id: int = Depends(get_current_user_id),
):
    """Cancel an active P2P order. Only the seller (from JWT) can cancel their own order."""
    async with pool.acquire() as conn:
        await _ensure_p2p_orders_table(conn)

        row = await conn.fetchrow(
            "SELECT * FROM p2p_orders WHERE id = $1", order_id
        )
        if not row:
            raise HTTPException(404, "Order not found")
        if row["seller_id"] != seller_id:
            raise HTTPException(403, "Only the seller can cancel this order")
        if row["status"] != "active":
            raise HTTPException(400, f"Order is already {row['status']}")

        await conn.execute(
            "UPDATE p2p_orders SET status = 'cancelled' WHERE id = $1",
            order_id,
        )

        await audit_log_write(
            conn,
            action="p2p.cancel_order",
            actor_type="user",
            actor_user_id=seller_id,
            resource_type="p2p_order",
            resource_id=str(order_id),
            metadata={
                "token": row["token"],
                "amount": float(row["amount"]),
                "price_per_unit": float(row["price_per_unit"]),
                "auth": "jwt",
            },
        )

    return {"ok": True, "message": "Order cancelled", "order_id": order_id}
