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
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncpg

# === CONFIG ===
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main")
BOT_TOKEN = os.getenv("EXPERTNET_BOT_TOKEN", "")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "224223270"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://slh-nft.com,http://localhost:8899,http://localhost:3000").split(",")

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
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        """)


@app.on_event("shutdown")
async def shutdown():
    if pool:
        await pool.close()


# === TELEGRAM AUTH ===
def verify_telegram_auth(data: dict) -> bool:
    """Verify Telegram Login Widget data"""
    if not BOT_TOKEN:
        return True  # Dev mode
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

        # Fetch user balances
        balances = await get_user_balances(conn, auth.id)
        premium = await conn.fetchval(
            "SELECT payment_status FROM premium_users WHERE user_id=$1 AND bot_name='expertnet'", auth.id
        )

    return {
        "user": {
            "id": auth.id,
            "username": auth.username,
            "first_name": auth.first_name,
            "photo_url": auth.photo_url,
            "premium": premium == "approved",
        },
        "balances": balances,
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
                "SELECT telegram_id, username, first_name, photo_url, auth_date, last_login FROM web_users WHERE telegram_id=$1", telegram_id
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


# === PRICES ===
@app.get("/api/prices")
async def get_prices():
    """Proxy for CoinGecko prices (cached)"""
    import aiohttp
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,the-open-network,binancecoin,solana,ripple,dogecoin&vs_currencies=usd,ils"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.json()
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
