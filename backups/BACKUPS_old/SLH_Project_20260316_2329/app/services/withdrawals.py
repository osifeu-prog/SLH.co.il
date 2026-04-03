import re

from app.db.database import db


WALLET_RE = re.compile(r"^[A-Za-z0-9:_\-.]{6,}$")


def normalize_wallet(wallet: str) -> str:
    return (wallet or "").splitlines()[0].strip()


def is_valid_wallet(wallet: str) -> bool:
    return bool(WALLET_RE.fullmatch(wallet))


async def create_withdrawal(user_id: int, amount: float, wallet: str) -> dict:
    try:
        amount = float(amount)
    except Exception:
        return {"ok": False, "error": "Amount must be a number."}

    wallet = normalize_wallet(wallet)

    if amount <= 0:
        return {"ok": False, "error": "Amount must be positive."}

    if not wallet:
        return {"ok": False, "error": "Wallet is required."}

    if not is_valid_wallet(wallet):
        return {"ok": False, "error": "Wallet format is invalid. Use one-line wallet text only."}

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            try:
                withdrawal_id = await conn.fetchval(
                    "SELECT create_withdrawal_request($1::bigint, $2::numeric, $3::text)",
                    int(user_id),
                    amount,
                    wallet,
                )
            except Exception as e:
                return {"ok": False, "error": str(e)}

            row = await conn.fetchrow(
                """
                SELECT id, user_id, amount, wallet, status
                FROM withdrawals
                WHERE id = $1
                """,
                int(withdrawal_id),
            )

    if not row:
        return {"ok": False, "error": "Withdrawal was not created."}

    return {
        "ok": True,
        "withdrawal_id": int(row["id"]),
        "amount": float(row["amount"]),
        "wallet": str(row["wallet"]),
        "status": str(row["status"]),
    }