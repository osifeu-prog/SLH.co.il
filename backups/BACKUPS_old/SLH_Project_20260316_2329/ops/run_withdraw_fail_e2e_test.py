import asyncio
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.database import db
from app.services.withdrawals import create_withdrawal
from app.services.withdrawals_query import approve_withdrawal, mark_withdraw_failed

USER_ID = 224223270
ADMIN_USER_ID = 224223270
AMOUNT = 1.0

async def row(conn, sql, *args):
    r = await conn.fetchrow(sql, *args)
    return dict(r) if r else None

async def rows(conn, sql, *args):
    rr = await conn.fetch(sql, *args)
    return [dict(x) for x in rr]

async def main():
    await db.connect()
    try:
        async with db.pool.acquire() as conn:
            before_user = await row(conn, """
                SELECT
                  u.user_id,
                  u.username,
                  COALESCE(ub.available,0)::numeric(20,8) AS available,
                  COALESCE(ub.locked,0)::numeric(20,8) AS locked,
                  COALESCE(u.balance,0)::numeric(20,8) AS users_balance
                FROM users u
                LEFT JOIN user_balances ub ON ub.user_id = u.user_id
                WHERE u.user_id = $1
            """, USER_ID)

            before_system = await row(conn, """
                SELECT
                  ROUND((SELECT COALESCE(SUM(available),0) FROM user_balances)::numeric, 8) AS user_balances_available,
                  ROUND((SELECT COALESCE(SUM(locked),0) FROM user_balances)::numeric, 8) AS user_balances_locked,
                  ROUND((SELECT COALESCE(SUM(balance),0) FROM users)::numeric, 8) AS users_balance,
                  ROUND((
                    SELECT COALESCE(SUM(
                      CASE
                        WHEN la.account_type='user_liability_available' AND la.normal_side='credit' AND le.entry_side='credit' THEN le.amount
                        WHEN la.account_type='user_liability_available' AND la.normal_side='credit' AND le.entry_side='debit' THEN -le.amount
                        ELSE 0
                      END
                    ),0)
                    FROM ledger_entries le
                    JOIN ledger_accounts la ON la.id = le.account_id
                  )::numeric, 8) AS ledger_user_available,
                  ROUND((
                    SELECT COALESCE(SUM(
                      CASE
                        WHEN la.account_type='user_liability_locked' AND la.normal_side='credit' AND le.entry_side='credit' THEN le.amount
                        WHEN la.account_type='user_liability_locked' AND la.normal_side='credit' AND le.entry_side='debit' THEN -le.amount
                        ELSE 0
                      END
                    ),0)
                    FROM ledger_entries le
                    JOIN ledger_accounts la ON la.id = le.account_id
                  )::numeric, 8) AS ledger_user_locked
            """)

        wallet = "FAIL_" + uuid.uuid4().hex[:12].upper()
        create_result = await create_withdrawal(USER_ID, AMOUNT, wallet)
        if not create_result.get("ok"):
            print(json.dumps({"stage": "create_failed", "create_result": create_result}, ensure_ascii=False, indent=2, default=str))
            return

        withdrawal_id = int(create_result["withdrawal_id"])

        approve_result = await approve_withdrawal(withdrawal_id, ADMIN_USER_ID)
        if not approve_result.get("ok"):
            print(json.dumps({
                "stage": "approve_failed",
                "withdrawal_id": withdrawal_id,
                "create_result": create_result,
                "approve_result": approve_result
            }, ensure_ascii=False, indent=2, default=str))
            return

        fail_result = await mark_withdraw_failed(withdrawal_id, ADMIN_USER_ID, "E2E simulated failure")

        async with db.pool.acquire() as conn:
            after_user = await row(conn, """
                SELECT
                  u.user_id,
                  u.username,
                  COALESCE(ub.available,0)::numeric(20,8) AS available,
                  COALESCE(ub.locked,0)::numeric(20,8) AS locked,
                  COALESCE(u.balance,0)::numeric(20,8) AS users_balance
                FROM users u
                LEFT JOIN user_balances ub ON ub.user_id = u.user_id
                WHERE u.user_id = $1
            """, USER_ID)

            after_system = await row(conn, """
                SELECT
                  ROUND((SELECT COALESCE(SUM(available),0) FROM user_balances)::numeric, 8) AS user_balances_available,
                  ROUND((SELECT COALESCE(SUM(locked),0) FROM user_balances)::numeric, 8) AS user_balances_locked,
                  ROUND((SELECT COALESCE(SUM(balance),0) FROM users)::numeric, 8) AS users_balance,
                  ROUND((
                    SELECT COALESCE(SUM(
                      CASE
                        WHEN la.account_type='user_liability_available' AND la.normal_side='credit' AND le.entry_side='credit' THEN le.amount
                        WHEN la.account_type='user_liability_available' AND la.normal_side='credit' AND le.entry_side='debit' THEN -le.amount
                        ELSE 0
                      END
                    ),0)
                    FROM ledger_entries le
                    JOIN ledger_accounts la ON la.id = le.account_id
                  )::numeric, 8) AS ledger_user_available,
                  ROUND((
                    SELECT COALESCE(SUM(
                      CASE
                        WHEN la.account_type='user_liability_locked' AND la.normal_side='credit' AND le.entry_side='credit' THEN le.amount
                        WHEN la.account_type='user_liability_locked' AND la.normal_side='credit' AND le.entry_side='debit' THEN -le.amount
                        ELSE 0
                      END
                    ),0)
                    FROM ledger_entries le
                    JOIN ledger_accounts la ON la.id = le.account_id
                  )::numeric, 8) AS ledger_user_locked
            """)

            withdrawal_row = await row(conn, """
                SELECT id, user_id, amount, wallet, status, tx_hash, error_message, created_at, approved_at, processed_at, reviewed_by
                FROM withdrawals
                WHERE id = $1
            """, withdrawal_id)

            reservation_row = await row(conn, """
                SELECT withdrawal_id, user_id, amount, status, created_at, updated_at
                FROM withdrawal_reservations
                WHERE withdrawal_id = $1
            """, withdrawal_id)

            audit_tail = await rows(conn, """
                SELECT id, user_id, event_type, payload_json, created_at
                FROM audit_log
                WHERE user_id = $1
                  AND (event_type ILIKE 'finance.withdrawal%%' OR event_type ILIKE 'withdraw.%%')
                ORDER BY id DESC
                LIMIT 20
            """, USER_ID)

        print(json.dumps({
            "before_user": before_user,
            "before_system": before_system,
            "create_result": create_result,
            "approve_result": approve_result,
            "fail_result": fail_result,
            "after_user": after_user,
            "after_system": after_system,
            "withdrawal_row": withdrawal_row,
            "reservation_row": reservation_row,
            "audit_tail": audit_tail
        }, ensure_ascii=False, indent=2, default=str))

    finally:
        if getattr(db, "pool", None) is not None:
            await db.pool.close()

if __name__ == "__main__":
    asyncio.run(main())
