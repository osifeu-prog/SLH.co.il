import os
import time
import hashlib


async def send_ton_withdrawal(*, withdrawal_id: int, wallet: str, amount: float) -> dict:
    mode = os.getenv("TON_MODE", "dry-run").strip().lower()

    if mode != "live":
        raw = f"{withdrawal_id}|{wallet}|{amount}|{int(time.time())}"
        tx_hash = "DRYRUN_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24].upper()
        return {
            "ok": True,
            "mode": "dry-run",
            "tx_hash": tx_hash,
        }

    return {
        "ok": False,
        "error": "TON live mode is not implemented yet in this gateway.",
    }