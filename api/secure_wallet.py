from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import uuid4
import jwt
import time

router = APIRouter()

JWT_SECRET = "CHANGE_THIS_SECRET_NOW"
JWT_ALG = "HS256"

# ========= AUTH =========

def get_current_user_id(authorization: str = Header(None)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")

    token = authorization.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Invalid token payload")

    return int(user_id)


# ========= REQUEST =========

class WalletSendRequest(BaseModel):
    to: str
    amount: Decimal = Field(..., gt=0)
    currency: str = "SLH"
    request_id: str


# ========= FAKE STORAGE (× ×—×œ×™×£ ××—×¨ ×›×š DB ××ž×™×ª×™) =========

IDEMPOTENCY_STORE = {}
BALANCE_STORE = {
    123456: Decimal("1000")  # user test
}


def get_balance(user_id, token):
    return BALANCE_STORE.get(user_id, Decimal("0"))


def deduct_balance(user_id, amount):
    BALANCE_STORE[user_id] -= amount


def credit_balance(user_id, amount):
    BALANCE_STORE[user_id] = BALANCE_STORE.get(user_id, Decimal("0")) + amount


# ========= ROUTE =========

@router.post("/api/secure/wallet/send")
async def secure_wallet_send(
    req: WalletSendRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
):
    token = req.currency.upper()

    if token != "SLH":
        raise HTTPException(400, "Only SLH supported")

    if not req.to.isdigit():
        raise HTTPException(400, "Recipient must be numeric ID")

    to_id = int(req.to)

    if to_id == user_id:
        raise HTTPException(400, "Cannot send to yourself")

    # ===== Idempotency =====
    key = f"{user_id}:{req.request_id}"
    if key in IDEMPOTENCY_STORE:
        return {
            "status": "ok",
            "data": IDEMPOTENCY_STORE[key]
        }

    balance = get_balance(user_id, token)

    if balance < req.amount:
        raise HTTPException(400, "Insufficient balance")

    tx_id = str(uuid4())

    # ===== Atomic simulation =====
    try:
        deduct_balance(user_id, req.amount)
        credit_balance(to_id, req.amount)

        result = {
            "tx_id": tx_id,
            "from_id": user_id,
            "to_id": to_id,
            "amount": str(req.amount),
            "token": token,
            "created_at": int(time.time())
        }

        IDEMPOTENCY_STORE[key] = result

    except Exception:
        raise HTTPException(500, "Transfer failed")

    return {
        "status": "ok",
        "data": result
    }