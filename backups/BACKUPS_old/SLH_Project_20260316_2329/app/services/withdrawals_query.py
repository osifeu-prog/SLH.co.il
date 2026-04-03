from app.db.database import db


async def list_user_withdrawals(user_id: int, limit: int = 10) -> list[dict]:
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                id,
                user_id,
                amount,
                wallet,
                status,
                created_at,
                reviewed_at,
                processed_at,
                reject_reason,
                tx_hash,
                reservation_status
            FROM v_user_withdrawal_history
            WHERE user_id = $1
            ORDER BY id DESC
            LIMIT $2
            """,
            int(user_id),
            int(limit),
        )
    return [dict(r) for r in rows]


async def list_pending_withdrawals(limit: int = 20) -> list[dict]:
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                id,
                user_id,
                username,
                amount,
                wallet,
                status,
                created_at,
                reviewed_at,
                processed_at,
                reject_reason,
                tx_hash,
                reservation_status,
                available,
                locked,
                ledger_available,
                ledger_locked,
                delta_available,
                delta_locked
            FROM v_withdrawal_admin_queue
            WHERE status IN ('pending', 'approved')
            ORDER BY id DESC
            LIMIT $1
            """,
            int(limit),
        )
    return [dict(r) for r in rows]


async def approve_withdrawal(withdrawal_id: int, admin_user_id: int) -> dict:
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT id, user_id, amount, wallet, status
                FROM withdrawals
                WHERE id = $1
                FOR UPDATE
                """,
                int(withdrawal_id),
            )
            if not row:
                return {"ok": False, "error": "Withdrawal not found."}

            status = str(row["status"])
            if status not in ("pending", "approved"):
                return {"ok": False, "error": f"Withdrawal status is {status}, not pending/approved."}

            if status == "pending":
                try:
                    await conn.fetchval(
                        "SELECT finance_request_withdrawal_reserve($1::bigint)",
                        int(withdrawal_id),
                    )
                except Exception as e:
                    return {"ok": False, "error": str(e)}

            updated = await conn.fetchrow(
                """
                SELECT
                    id,
                    user_id,
                    username,
                    amount,
                    wallet,
                    status,
                    created_at,
                    reviewed_at,
                    processed_at,
                    reject_reason,
                    tx_hash,
                    reservation_status,
                    available,
                    locked,
                    ledger_available,
                    ledger_locked,
                    delta_available,
                    delta_locked
                FROM v_withdrawal_admin_queue
                WHERE id = $1
                """,
                int(withdrawal_id),
            )

            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                VALUES ($1, $2, $3, NOW())
                """,
                int(row["user_id"]),
                "withdrawal.admin_approved",
                '{"withdrawal_id":%s,"admin_user_id":%s,"status":"approved"}'
                % (int(withdrawal_id), int(admin_user_id)),
            )

    return {"ok": True, "row": dict(updated)}


async def reject_withdrawal(withdrawal_id: int, admin_user_id: int, reason: str) -> dict:
    reason = (reason or "").strip() or "Rejected by admin"

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT id, user_id, amount, wallet, status
                FROM withdrawals
                WHERE id = $1
                FOR UPDATE
                """,
                int(withdrawal_id),
            )
            if not row:
                return {"ok": False, "error": "Withdrawal not found."}

            status = str(row["status"])

            if status == "pending":
                updated = await conn.fetchrow(
                    """
                    UPDATE withdrawals
                    SET status = 'rejected',
                        reviewed_at = CURRENT_TIMESTAMP,
                        reject_reason = $2
                    WHERE id = $1
                    RETURNING id, user_id, amount, wallet, status, reject_reason
                    """,
                    int(withdrawal_id),
                    reason,
                )

                await conn.execute(
                    """
                    INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                    VALUES ($1, $2, $3, NOW())
                    """,
                    int(updated["user_id"]),
                    "withdrawal.admin_rejected",
                    '{"withdrawal_id":%s,"admin_user_id":%s,"reason":"%s","source_status":"pending"}'
                    % (int(updated["id"]), int(admin_user_id), reason.replace('"', "'")),
                )
                return {"ok": True, "row": dict(updated)}

            if status == "approved":
                try:
                    await conn.fetchval(
                        "SELECT finance_reject_withdrawal_release($1::bigint, $2::text)",
                        int(withdrawal_id),
                        reason,
                    )
                except Exception as e:
                    return {"ok": False, "error": str(e)}

                updated = await conn.fetchrow(
                    """
                    SELECT
                        id,
                        user_id,
                        username,
                        amount,
                        wallet,
                        status,
                        created_at,
                        reviewed_at,
                        processed_at,
                        reject_reason,
                        tx_hash,
                        reservation_status,
                        available,
                        locked,
                        ledger_available,
                        ledger_locked,
                        delta_available,
                        delta_locked
                    FROM v_withdrawal_admin_queue
                    WHERE id = $1
                    """,
                    int(withdrawal_id),
                )

                await conn.execute(
                    """
                    INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                    VALUES ($1, $2, $3, NOW())
                    """,
                    int(row["user_id"]),
                    "withdrawal.admin_rejected",
                    '{"withdrawal_id":%s,"admin_user_id":%s,"reason":"%s","source_status":"approved"}'
                    % (int(withdrawal_id), int(admin_user_id), reason.replace('"', "'")),
                )
                return {"ok": True, "row": dict(updated)}

            return {"ok": False, "error": f"Withdrawal status is {status}, not pending/approved."}


async def mark_withdraw_sent(withdrawal_id: int, admin_user_id: int, tx_hash: str) -> dict:
    tx_hash = (tx_hash or "").strip()
    if not tx_hash:
        return {"ok": False, "error": "tx_hash is required."}

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT id, user_id, status
                FROM withdrawals
                WHERE id = $1
                FOR UPDATE
                """,
                int(withdrawal_id),
            )
            if not row:
                return {"ok": False, "error": "Withdrawal not found."}

            if str(row["status"]) != "approved":
                return {"ok": False, "error": f"Withdrawal status is {row['status']}, not approved."}

            try:
                await conn.fetchval(
                    "SELECT finance_mark_withdrawal_sent_consume($1::bigint, $2::text)",
                    int(withdrawal_id),
                    tx_hash,
                )
            except Exception as e:
                return {"ok": False, "error": str(e)}

            updated = await conn.fetchrow(
                """
                SELECT
                    id,
                    user_id,
                    username,
                    amount,
                    wallet,
                    status,
                    created_at,
                    reviewed_at,
                    processed_at,
                    reject_reason,
                    tx_hash,
                    reservation_status,
                    available,
                    locked,
                    ledger_available,
                    ledger_locked,
                    delta_available,
                    delta_locked
                FROM v_withdrawal_admin_queue
                WHERE id = $1
                """,
                int(withdrawal_id),
            )

            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                VALUES ($1, $2, $3, NOW())
                """,
                int(row["user_id"]),
                "withdrawal.admin_sent",
                '{"withdrawal_id":%s,"admin_user_id":%s,"tx_hash":"%s"}'
                % (int(withdrawal_id), int(admin_user_id), tx_hash.replace('"', "'")),
            )

    return {"ok": True, "row": dict(updated)}


async def mark_withdraw_failed(withdrawal_id: int, admin_user_id: int, error_message: str) -> dict:
    error_message = (error_message or "").strip() or "Unknown failure"

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT id, user_id, amount, wallet, status
                FROM withdrawals
                WHERE id = $1
                FOR UPDATE
                """,
                int(withdrawal_id),
            )
            if not row:
                return {"ok": False, "error": "Withdrawal not found."}

            status = str(row["status"])

            if status == "approved":
                try:
                    await conn.fetchval(
                        "SELECT finance_reject_withdrawal_release($1::bigint, $2::text)",
                        int(withdrawal_id),
                        error_message,
                    )
                except Exception as e:
                    return {"ok": False, "error": str(e)}

                updated = await conn.fetchrow(
                    """
                    SELECT
                        id,
                        user_id,
                        username,
                        amount,
                        wallet,
                        status,
                        created_at,
                        reviewed_at,
                        processed_at,
                        reject_reason,
                        tx_hash,
                        reservation_status,
                        available,
                        locked,
                        ledger_available,
                        ledger_locked,
                        delta_available,
                        delta_locked
                    FROM v_withdrawal_admin_queue
                    WHERE id = $1
                    """,
                    int(withdrawal_id),
                )

                await conn.execute(
                    """
                    INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                    VALUES ($1, $2, $3, NOW())
                    """,
                    int(row["user_id"]),
                    "withdrawal.admin_failed",
                    '{"withdrawal_id":%s,"admin_user_id":%s,"error":"%s","source_status":"approved"}'
                    % (int(withdrawal_id), int(admin_user_id), error_message.replace('"', "'")),
                )
                return {"ok": True, "row": dict(updated)}

            if status == "pending":
                updated = await conn.fetchrow(
                    """
                    UPDATE withdrawals
                    SET status = 'rejected',
                        reviewed_at = CURRENT_TIMESTAMP,
                        reject_reason = $2
                    WHERE id = $1
                    RETURNING id, user_id, amount, wallet, status, reject_reason
                    """,
                    int(withdrawal_id),
                    error_message,
                )

                await conn.execute(
                    """
                    INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                    VALUES ($1, $2, $3, NOW())
                    """,
                    int(updated["user_id"]),
                    "withdrawal.admin_failed",
                    '{"withdrawal_id":%s,"admin_user_id":%s,"error":"%s","source_status":"pending"}'
                    % (int(updated["id"]), int(admin_user_id), error_message.replace('"', "'")),
                )
                return {"ok": True, "row": dict(updated)}

            return {"ok": False, "error": f"Withdrawal status is {status}, not pending/approved."}