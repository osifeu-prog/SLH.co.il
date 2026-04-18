"""
SLH Investment House - Core Banking Module
Double-entry ledger, deposits, withdrawals, statements.
"""
import os
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Optional
import uuid

log = logging.getLogger("slh.banking")

_pool = None

async def pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@postgres:5432/slh_main"),
            min_size=1, max_size=5,
        )
    return _pool


# ═══════════════════════════════════
# ACCOUNTS
# ═══════════════════════════════════
async def get_or_create_account(user_id, account_type="main", currency="TON"):
    p = await pool()
    async with p.acquire() as c:
        row = await c.fetchrow(
            "SELECT id FROM bank_accounts WHERE user_id=$1 AND account_type=$2 AND currency=$3",
            user_id, account_type, currency)
        if row:
            return row["id"]
        row = await c.fetchrow(
            "INSERT INTO bank_accounts (user_id, account_type, currency) VALUES ($1,$2,$3) RETURNING id",
            user_id, account_type, currency)
        aid = row["id"]
        await c.execute(
            "INSERT INTO account_balances (account_id, available, locked) VALUES ($1, 0, 0) ON CONFLICT DO NOTHING", aid)
        return aid


async def get_balance(user_id, currency="TON"):
    p = await pool()
    async with p.acquire() as c:
        aid = await get_or_create_account(user_id, "main", currency)
        row = await c.fetchrow("SELECT available, locked, total FROM account_balances WHERE account_id=$1", aid)
        if row:
            return {"available": float(row["available"]), "locked": float(row["locked"]), "total": float(row["total"])}
        return {"available": 0, "locked": 0, "total": 0}


# ═══════════════════════════════════
# DOUBLE-ENTRY JOURNAL
# ═══════════════════════════════════
async def journal_entry(debit_id, credit_id, amount, currency, description, entry_type):
    """Create immutable journal entry + update balances."""
    tx_ref = f"TX-{uuid.uuid4().hex[:12].upper()}"
    p = await pool()
    async with p.acquire() as c:
        async with c.transaction():
            await c.execute(
                """INSERT INTO journal_entries (tx_ref, debit_account_id, credit_account_id, amount, currency, description, entry_type)
                   VALUES ($1,$2,$3,$4,$5,$6,$7)""",
                tx_ref, debit_id, credit_id, amount, currency, description, entry_type)
            # Debit: decrease available
            await c.execute(
                "UPDATE account_balances SET available = available - $2, updated_at = CURRENT_TIMESTAMP WHERE account_id = $1",
                debit_id, amount)
            # Credit: increase available
            await c.execute(
                "UPDATE account_balances SET available = available + $2, updated_at = CURRENT_TIMESTAMP WHERE account_id = $1",
                credit_id, amount)
    return tx_ref


# ═══════════════════════════════════
# DEPOSITS
# ═══════════════════════════════════
PLANS = {
    "m1": {"name": "פקדון חודשי", "monthly": 4, "apy": 48, "lock": 30, "min": 1},
    "m3": {"name": "פקדון רבעוני", "monthly": 4.5, "apy": 55, "lock": 90, "min": 5},
    "m6": {"name": "פקדון חצי-שנתי", "monthly": 5, "apy": 60, "lock": 180, "min": 10},
    "y1": {"name": "פקדון שנתי", "monthly": 5.4, "apy": 65, "lock": 365, "min": 25},
}

async def create_deposit(user_id, plan_key, amount):
    """Create a new deposit (pending payment)."""
    plan = PLANS.get(plan_key)
    if not plan:
        return None, "תוכנית לא קיימת"
    if amount < plan["min"]:
        return None, f"מינימום {plan['min']} TON"

    end_date = datetime.now() + timedelta(days=plan["lock"])
    p = await pool()
    async with p.acquire() as c:
        row = await c.fetchrow(
            """INSERT INTO deposits (user_id, plan_key, amount, monthly_rate, annual_rate, lock_days, end_date)
               VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id""",
            user_id, plan_key, amount, plan["monthly"], plan["apy"], plan["lock"], end_date)
    return row["id"], None


async def confirm_deposit(deposit_id, admin_id, proof_file_id=None):
    """Admin confirms deposit after verifying payment."""
    p = await pool()
    async with p.acquire() as c:
        dep = await c.fetchrow("SELECT * FROM deposits WHERE id=$1 AND status='pending_payment'", deposit_id)
        if not dep:
            return False, "הפקדה לא נמצאה"

        async with c.transaction():
            # Update deposit status
            await c.execute(
                """UPDATE deposits SET status='active', approved_by=$2, approved_at=CURRENT_TIMESTAMP,
                   payment_proof_file_id=$3, last_interest_date=CURRENT_TIMESTAMP WHERE id=$1""",
                deposit_id, admin_id, proof_file_id)

            # Create account if needed
            user_aid = await get_or_create_account(dep["user_id"], "main", "TON")

            # Journal entry: System receives deposit
            tx = await journal_entry(1, user_aid, float(dep["amount"]), "TON",
                                     f"Deposit #{deposit_id} confirmed", "deposit")

            # Lock the amount
            await c.execute(
                "UPDATE account_balances SET available = available - $2, locked = locked + $2 WHERE account_id = $1",
                user_aid, float(dep["amount"]))

    return True, tx


async def get_user_deposits(user_id):
    p = await pool()
    async with p.acquire() as c:
        rows = await c.fetch(
            "SELECT * FROM deposits WHERE user_id=$1 ORDER BY created_at DESC", user_id)
    result = []
    for r in rows:
        d = dict(r)
        if d["status"] == "active" and d["start_date"]:
            days = max(1, (datetime.now() - d["start_date"]).days)
            d["earned"] = float(d["amount"]) * float(d["monthly_rate"]) / 100 * days / 30
        else:
            d["earned"] = 0
        result.append(d)
    return result


async def get_all_deposits(status=None):
    """Admin: get all deposits."""
    p = await pool()
    async with p.acquire() as c:
        if status:
            rows = await c.fetch("SELECT * FROM deposits WHERE status=$1 ORDER BY created_at DESC", status)
        else:
            rows = await c.fetch("SELECT * FROM deposits ORDER BY created_at DESC LIMIT 50")
    return [dict(r) for r in rows]


# ═══════════════════════════════════
# WITHDRAWALS
# ═══════════════════════════════════
async def request_withdrawal(user_id, deposit_id, to_address):
    """User requests withdrawal of matured deposit."""
    p = await pool()
    async with p.acquire() as c:
        dep = await c.fetchrow(
            "SELECT * FROM deposits WHERE id=$1 AND user_id=$2 AND status='active'",
            deposit_id, user_id)
        if not dep:
            return None, "הפקדה לא נמצאה"

        now = datetime.now()
        is_early = now < dep["end_date"]
        earned = float(dep["amount"]) * float(dep["monthly_rate"]) / 100 * max(1, (now - dep["start_date"]).days) / 30
        fee = float(dep["amount"]) * 0.05 if is_early else 0  # 5% early withdrawal penalty
        net = float(dep["amount"]) + earned - fee

        row = await c.fetchrow(
            """INSERT INTO withdrawals (user_id, deposit_id, amount, fee, net_amount, to_address)
               VALUES ($1,$2,$3,$4,$5,$6) RETURNING id""",
            user_id, deposit_id, float(dep["amount"]) + earned, fee, net, to_address)

    return row["id"], "early" if is_early else "matured"


async def approve_withdrawal(withdrawal_id, admin_id, tx_hash=None):
    """Admin approves and processes withdrawal."""
    p = await pool()
    async with p.acquire() as c:
        w = await c.fetchrow("SELECT * FROM withdrawals WHERE id=$1 AND status='pending'", withdrawal_id)
        if not w:
            return False, "משיכה לא נמצאה"

        async with c.transaction():
            await c.execute(
                "UPDATE withdrawals SET status='approved', approved_by=$2, approved_at=CURRENT_TIMESTAMP, tx_hash=$3 WHERE id=$1",
                withdrawal_id, admin_id, tx_hash)

            if w["deposit_id"]:
                await c.execute("UPDATE deposits SET status='closed', closed_at=CURRENT_TIMESTAMP WHERE id=$1", w["deposit_id"])

            user_aid = await get_or_create_account(w["user_id"], "main", "TON")
            await c.execute(
                "UPDATE account_balances SET locked = GREATEST(0, locked - $2) WHERE account_id = $1",
                user_aid, float(w["amount"]))

    return True, "approved"


# ═══════════════════════════════════
# STATEMENTS
# ═══════════════════════════════════
async def generate_statement(user_id, days=30):
    """Generate account statement for last N days."""
    p = await pool()
    async with p.acquire() as c:
        aid = await get_or_create_account(user_id, "main", "TON")
        since = datetime.now() - timedelta(days=days)

        entries = await c.fetch(
            """SELECT * FROM journal_entries
               WHERE (debit_account_id=$1 OR credit_account_id=$1) AND created_at >= $2
               ORDER BY created_at""",
            aid, since)

        bal = await c.fetchrow("SELECT * FROM account_balances WHERE account_id=$1", aid)

        deposits = await c.fetch(
            "SELECT * FROM deposits WHERE user_id=$1 AND created_at >= $2 ORDER BY created_at", user_id, since)

        withdrawals_list = await c.fetch(
            "SELECT * FROM withdrawals WHERE user_id=$1 AND created_at >= $2 ORDER BY created_at", user_id, since)

    return {
        "user_id": user_id,
        "period_days": days,
        "balance": dict(bal) if bal else {},
        "entries": [dict(e) for e in entries],
        "deposits": [dict(d) for d in deposits],
        "withdrawals": [dict(w) for w in withdrawals_list],
    }


# ═══════════════════════════════════
# KYC
# ═══════════════════════════════════
async def start_kyc(user_id, full_name, phone=None):
    p = await pool()
    async with p.acquire() as c:
        await c.execute(
            """INSERT INTO kyc_records (user_id, full_name, phone)
               VALUES ($1,$2,$3) ON CONFLICT (user_id) DO UPDATE SET full_name=$2, phone=$3""",
            user_id, full_name, phone)


async def submit_kyc_doc(user_id, doc_type, file_id):
    p = await pool()
    async with p.acquire() as c:
        if doc_type == "id":
            await c.execute("UPDATE kyc_records SET id_doc_file_id=$2, status='submitted' WHERE user_id=$1", user_id, file_id)
        elif doc_type == "selfie":
            await c.execute("UPDATE kyc_records SET selfie_file_id=$2 WHERE user_id=$1", user_id, file_id)


async def approve_kyc(user_id, admin_id):
    p = await pool()
    async with p.acquire() as c:
        await c.execute(
            "UPDATE kyc_records SET status='approved', approved_by=$2, approved_at=CURRENT_TIMESTAMP WHERE user_id=$1",
            user_id, admin_id)


async def get_kyc_status(user_id):
    p = await pool()
    async with p.acquire() as c:
        row = await c.fetchrow("SELECT * FROM kyc_records WHERE user_id=$1", user_id)
    return dict(row) if row else None


async def get_pending_kyc():
    p = await pool()
    async with p.acquire() as c:
        rows = await c.fetch("SELECT * FROM kyc_records WHERE status IN ('pending','submitted') ORDER BY created_at")
    return [dict(r) for r in rows]


# ═══════════════════════════════════
# ADMIN STATS
# ═══════════════════════════════════
async def get_bank_stats():
    p = await pool()
    async with p.acquire() as c:
        total_deposits = await c.fetchval("SELECT COALESCE(SUM(amount), 0) FROM deposits WHERE status='active'")
        total_users = await c.fetchval("SELECT COUNT(DISTINCT user_id) FROM bank_accounts WHERE user_id > 0")
        pending_deposits = await c.fetchval("SELECT COUNT(*) FROM deposits WHERE status='pending_payment'")
        active_deposits = await c.fetchval("SELECT COUNT(*) FROM deposits WHERE status='active'")
        pending_withdrawals = await c.fetchval("SELECT COUNT(*) FROM withdrawals WHERE status='pending'")
        pending_kyc = await c.fetchval("SELECT COUNT(*) FROM kyc_records WHERE status IN ('pending','submitted')")
        total_journal = await c.fetchval("SELECT COUNT(*) FROM journal_entries")

    return {
        "total_deposits_ton": float(total_deposits),
        "total_users": total_users,
        "pending_deposits": pending_deposits,
        "active_deposits": active_deposits,
        "pending_withdrawals": pending_withdrawals,
        "pending_kyc": pending_kyc,
        "journal_entries": total_journal,
    }
