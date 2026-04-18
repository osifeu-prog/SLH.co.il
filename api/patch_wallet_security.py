from pathlib import Path

path = Path(r"D:\SLH_ECOSYSTEM\api\main.py")
text = path.read_text(encoding="utf-8")

def must_replace(old: str, new: str, label: str):
    global text
    if old not in text:
        raise RuntimeError(f"Missing block for: {label}")
    text = text.replace(old, new, 1)
    print(f"[OK] {label}")

# 1) imports
must_replace(
    "from fastapi import FastAPI, HTTPException, Depends, Query, Request",
    "from fastapi import FastAPI, HTTPException, Depends, Query, Request, Header",
    "fastapi Header import"
)

if "import jwt" not in text:
    text = text.replace(
        "from datetime import datetime, timedelta\n",
        "from datetime import datetime, timedelta\nimport jwt\nimport secrets\n",
        1
    )
    print("[OK] jwt/secrets imports")
else:
    if "import secrets" not in text:
        text = text.replace("import jwt\n", "import jwt\nimport secrets\n", 1)
        print("[OK] secrets import")
    print("[OK] jwt import already present")

# 2) config
if 'JWT_SECRET = os.getenv("JWT_SECRET", "")' not in text:
    must_replace(
        'BOT_TOKEN = os.getenv("EXPERTNET_BOT_TOKEN", "")\nADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "224223270"))',
        'BOT_TOKEN = os.getenv("EXPERTNET_BOT_TOKEN", "")\nJWT_SECRET = os.getenv("JWT_SECRET", "")\nJWT_ALGORITHM = "HS256"\nJWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "12"))\nADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "224223270"))',
        "JWT config"
    )

# 3) fail closed when BOT_TOKEN missing
must_replace(
    '    if not BOT_TOKEN:\n        return True  # Dev mode\n',
    '    if not BOT_TOKEN:\n        return False\n',
    "telegram auth fail-closed"
)

# 4) helper functions after TelegramAuth
if "def create_jwt(" not in text:
    old_block = """class TelegramAuth(BaseModel):
    id: int
    first_name: str
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str
"""
    new_block = """class TelegramAuth(BaseModel):
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
"""
    must_replace(old_block, new_block, "JWT helpers + wallet rate limiter")

# 5) auth endpoint returns token
old_return = """    return {
        "user": {
            "id": auth.id,
            "username": auth.username,
            "first_name": auth.first_name,
            "photo_url": auth.photo_url,
            "premium": premium == "approved",
        },
        "balances": balances,
    }
"""
new_return = """    jwt_token = create_jwt(auth.id, auth.username)

    return {
        "status": "ok",
        "token": jwt_token,
        "user": {
            "id": auth.id,
            "username": auth.username,
            "first_name": auth.first_name,
            "photo_url": auth.photo_url,
            "premium": premium == "approved",
        },
        "balances": balances,
    }
"""
must_replace(old_return, new_return, "auth endpoint returns JWT")

# 6) wallet idempotency table
if "CREATE TABLE IF NOT EXISTS wallet_idempotency" not in text:
    old_sql = """            CREATE TABLE IF NOT EXISTS token_transfers (
                id BIGSERIAL PRIMARY KEY,
                from_user_id BIGINT,
                to_user_id BIGINT,
                token TEXT NOT NULL DEFAULT 'SLH',
                amount NUMERIC(18,8) NOT NULL,
                memo TEXT,
                tx_type TEXT DEFAULT 'transfer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS deposits (
"""
    new_sql = """            CREATE TABLE IF NOT EXISTS token_transfers (
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
"""
    must_replace(old_sql, new_sql, "wallet_idempotency table")

# 7) replace insecure wallet_send
old_wallet = """class WalletSendRequest(BaseModel):
    from_id: int
    to: str
    amount: float
    currency: str = "SLH"

@app.post("/api/wallet/send")
async def wallet_send(req: WalletSendRequest):
    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    token = (req.currency or "SLH").upper().strip()
    if token != "SLH":
        raise HTTPException(400, "Only SLH internal transfer is supported right now")

    if not req.to.isdigit():
        raise HTTPException(400, "Recipient must be a Telegram numeric ID for now")

    transfer_req = TransferRequest(
        from_user_id=req.from_id,
        to_user_id=int(req.to),
        token=token,
        amount=req.amount,
        memo="wallet send"
    )

    result = await transfer_tokens(transfer_req)
    return {"success": True, "result": result}
"""
new_wallet = """class WalletSendRequest(BaseModel):
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
                    \"\"\"
                    SELECT id, from_user_id, to_user_id, token, amount, memo, tx_type, created_at
                    FROM token_transfers
                    WHERE id=$1
                    \"\"\",
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
                \"\"\"
                INSERT INTO token_balances (user_id, token, balance, updated_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, token)
                DO UPDATE SET balance = token_balances.balance + $3, updated_at = CURRENT_TIMESTAMP
                \"\"\",
                to_user_id, token, req.amount
            )

            transfer_id = await conn.fetchval(
                \"\"\"
                INSERT INTO token_transfers (from_user_id, to_user_id, token, amount, memo, tx_type)
                VALUES ($1, $2, $3, $4, $5, 'wallet_send')
                RETURNING id
                \"\"\",
                user_id, to_user_id, token, req.amount, f"wallet send | request_id={req.request_id.strip()}"
            )

            await conn.execute(
                \"\"\"
                INSERT INTO wallet_idempotency (user_id, request_id, tx_transfer_id)
                VALUES ($1, $2, $3)
                \"\"\",
                user_id, req.request_id.strip(), transfer_id
            )

            row = await conn.fetchrow(
                \"\"\"
                SELECT id, from_user_id, to_user_id, token, amount, memo, tx_type, created_at
                FROM token_transfers
                WHERE id=$1
                \"\"\",
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
"""
must_replace(old_wallet, new_wallet, "secure wallet_send")

path.write_text(text, encoding="utf-8")
print(f"[DONE] patched {path}")