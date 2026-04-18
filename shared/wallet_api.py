"""
SLH Ecosystem — Wallet API Router
===================================
FastAPI router that exposes the WalletEngine over HTTP.
Mount this in the main Railway FastAPI app:

    from shared.wallet_api import router as wallet_router, wallet_engine, lifespan
    app = FastAPI(lifespan=lifespan)
    app.include_router(wallet_router)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import APIRouter, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .wallet_engine import WalletEngine

# ---------------------------------------------------------------------------
# Shared engine instance
# ---------------------------------------------------------------------------

wallet_engine = WalletEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Plug into FastAPI lifespan to init / close the engine."""
    await wallet_engine.init()
    yield
    await wallet_engine.close()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TransferRequest(BaseModel):
    from_user_id: int
    to_user_id: int
    amount: str = Field(..., description="Amount as string to preserve precision")
    token: str = Field(default="SLH", description="SLH | BNB | TON | ZVK")


class DepositVerifyRequest(BaseModel):
    user_id: int
    tx_hash: str
    chain: str = Field(..., description="bsc | ton")


class PortfolioResponse(BaseModel):
    user_id: int
    bsc_address: Optional[str] = None
    ton_address: Optional[str] = None
    balances: dict
    usd_values: dict
    prices: dict


class TransferResponse(BaseModel):
    tx_id: Optional[int] = None
    from_user_id: int
    to_user_id: int
    amount: str
    token: str
    status: str
    error: Optional[str] = None


class DepositResponse(BaseModel):
    deposit_id: Optional[int] = None
    user_id: Optional[int] = None
    amount: Optional[str] = None
    token: Optional[str] = None
    chain: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api", tags=["wallet"])


@router.get("/wallet/{user_id}", response_model=PortfolioResponse)
async def get_portfolio(user_id: int):
    """Return the full portfolio for a user."""
    result = await wallet_engine.get_user_portfolio(user_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/wallet/{user_id}/history")
async def get_history(user_id: int, limit: int = Query(default=20, le=100)):
    """Return recent transactions for a user."""
    rows = await wallet_engine.get_transaction_history(user_id, limit=limit)
    return {"user_id": user_id, "transactions": rows}


@router.post("/wallet/transfer", response_model=TransferResponse)
async def internal_transfer(req: TransferRequest):
    """Execute an instant internal transfer between two users."""
    result = await wallet_engine.internal_transfer(
        from_user_id=req.from_user_id,
        to_user_id=req.to_user_id,
        amount=req.amount,
        token=req.token,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    return result


@router.post("/wallet/deposit/verify", response_model=DepositResponse)
async def verify_deposit(req: DepositVerifyRequest):
    """Verify an on-chain deposit and credit the user's internal balance."""
    result = await wallet_engine.process_deposit(
        user_id=req.user_id,
        tx_hash=req.tx_hash,
        chain=req.chain,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    return result


@router.get("/prices")
async def live_prices():
    """Return cached live prices for BTC, ETH, TON, BNB, SLH."""
    return await wallet_engine.get_live_prices()


@router.get("/wallet/{user_id}/deposit-address")
async def get_deposit_address(user_id: int):
    """Generate / return the deposit addresses for a user."""
    return await wallet_engine.generate_deposit_address(user_id)


@router.get("/wallet/{user_id}/balance/onchain")
async def get_onchain_balances(user_id: int):
    """
    Read real on-chain balances for a user's deposit address (BSC only).
    This is slower than the internal ledger and hits the RPC node.
    """
    addr_info = await wallet_engine.generate_deposit_address(user_id)
    bsc_addr = addr_info["bsc_address"]
    slh = await wallet_engine.get_slh_balance(bsc_addr)
    bnb = await wallet_engine.get_bnb_balance(bsc_addr)
    return {
        "user_id": user_id,
        "bsc_address": bsc_addr,
        "onchain": {"SLH": slh, "BNB": bnb},
    }
