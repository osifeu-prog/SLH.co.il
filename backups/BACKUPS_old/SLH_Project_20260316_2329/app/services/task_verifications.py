import json

from app.db.database import db
from app.services.xp import level_from_xp

TASK1_ID = 1
TASK1_XP = 10
TASK1_REJECT_POLICY = "retry"


async def request_task_verification(user_id: int, task_id: int) -> dict:
    if int(task_id) != TASK1_ID:
        return {"ok": False, "error": "unsupported_task", "message": "This task does not use manual verification."}

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            lock_key = int(user_id) * 1000 + int(task_id)
            await conn.execute(
                "SELECT pg_advisory_xact_lock($1::bigint)",
                lock_key,
            )

            task = await conn.fetchrow(
                """
                SELECT id, title, reward, type
                FROM tasks
                WHERE id = $1
                """,
                task_id,
            )
            if not task:
                return {"ok": False, "error": "task_not_found", "message": "Task not found."}

            existing_claim = await conn.fetchrow(
                """
                SELECT completed
                FROM user_tasks
                WHERE user_id = $1 AND task_id = $2
                LIMIT 1
                """,
                user_id,
                task_id,
            )
            if existing_claim and bool(existing_claim["completed"]):
                return {"ok": False, "error": "already_claimed", "message": "Task already claimed."}

            existing_verification = await conn.fetchrow(
                """
                SELECT status, requested_at, reviewed_at, reviewed_by, review_note
                FROM task_verifications
                WHERE user_id = $1 AND task_id = $2
                LIMIT 1
                """,
                user_id,
                task_id,
            )

            if existing_verification:
                status = str(existing_verification["status"] or "pending")
                if status == "pending":
                    return {
                        "ok": False,
                        "error": "already_pending",
                        "message": "Verification already pending review.",
                    }

                if status == "approved":
                    return {
                        "ok": False,
                        "error": "already_approved",
                        "message": "Task already approved.",
                    }

                if status == "rejected" and TASK1_REJECT_POLICY == "retry":
                    await conn.execute(
                        """
                        UPDATE task_verifications
                        SET status = 'pending',
                            requested_at = CURRENT_TIMESTAMP,
                            reviewed_at = NULL,
                            reviewed_by = NULL,
                            review_note = NULL
                        WHERE user_id = $1 AND task_id = $2
                        """,
                        user_id,
                        task_id,
                    )
                else:
                    return {
                        "ok": False,
                        "error": "rejected_final",
                        "message": "Task verification was rejected.",
                    }
            else:
                await conn.execute(
                    """
                    INSERT INTO task_verifications (
                        user_id, task_id, status, requested_at, reviewed_at, reviewed_by, review_note
                    )
                    VALUES ($1, $2, 'pending', CURRENT_TIMESTAMP, NULL, NULL, NULL)
                    """,
                    user_id,
                    task_id,
                )

            audit_payload = json.dumps(
                {
                    "task_id": int(task["id"]),
                    "title": str(task["title"] or f"Task {task_id}"),
                    "task_type": str(task["type"] or ""),
                    "mode": "manual_verification_requested",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json)
                VALUES ($1, $2, $3)
                """,
                user_id,
                "task.verification_requested",
                audit_payload,
            )

            return {
                "ok": True,
                "task_id": int(task["id"]),
                "title": str(task["title"] or f"Task {task_id}"),
                "status": "pending",
                "message": "Task verification submitted for review.",
            }


async def list_pending_task_verifications(limit: int = 20) -> list[dict]:
    safe_limit = max(1, min(int(limit), 100))

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                tv.user_id,
                tv.task_id,
                tv.status,
                tv.requested_at,
                u.username,
                t.title,
                t.reward,
                t.type
            FROM task_verifications tv
            LEFT JOIN users u ON u.user_id = tv.user_id
            LEFT JOIN tasks t ON t.id = tv.task_id
            WHERE tv.status = 'pending'
            ORDER BY tv.requested_at ASC, tv.user_id ASC, tv.task_id ASC
            LIMIT $1
            """,
            safe_limit,
        )

    return [dict(r) for r in rows]


async def review_task_verification(
    admin_user_id: int,
    user_id: int,
    task_id: int,
    approve: bool,
    review_note: str | None = None,
) -> dict:
    if int(task_id) != TASK1_ID:
        return {"ok": False, "error": "unsupported_task", "message": "This task does not use manual verification."}

    note = (review_note or "").strip()
    if len(note) > 1000:
        note = note[:1000]

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            lock_key = int(user_id) * 1000 + int(task_id)
            await conn.execute(
                "SELECT pg_advisory_xact_lock($1::bigint)",
                lock_key,
            )

            task = await conn.fetchrow(
                """
                SELECT id, title, reward, type
                FROM tasks
                WHERE id = $1
                """,
                task_id,
            )
            if not task:
                return {"ok": False, "error": "task_not_found", "message": "Task not found."}

            verification = await conn.fetchrow(
                """
                SELECT user_id, task_id, status
                FROM task_verifications
                WHERE user_id = $1 AND task_id = $2
                FOR UPDATE
                """,
                user_id,
                task_id,
            )
            if not verification:
                return {"ok": False, "error": "verification_not_found", "message": "Verification request not found."}

            status = str(verification["status"] or "pending")
            if status != "pending":
                return {
                    "ok": False,
                    "error": "verification_not_pending",
                    "message": f"Verification is already {status}.",
                }

            existing_claim = await conn.fetchrow(
                """
                SELECT completed
                FROM user_tasks
                WHERE user_id = $1 AND task_id = $2
                LIMIT 1
                """,
                user_id,
                task_id,
            )
            if existing_claim and bool(existing_claim["completed"]):
                return {"ok": False, "error": "already_claimed", "message": "Task already claimed."}

            if approve:
                user_row = await conn.fetchrow(
                    """
                    SELECT COALESCE(xp_total, 0) AS xp_total
                    FROM users
                    WHERE user_id = $1
                    FOR UPDATE
                    """,
                    user_id,
                )
                if not user_row:
                    return {"ok": False, "error": "user_not_found", "message": "User not found."}

                current_xp = int(user_row["xp_total"] or 0)
                reward = float(task["reward"] or 0)
                new_xp = current_xp + int(TASK1_XP)
                new_level = level_from_xp(new_xp)

                if existing_claim:
                    await conn.execute(
                        """
                        UPDATE user_tasks
                        SET completed = TRUE
                        WHERE user_id = $1 AND task_id = $2
                        """,
                        user_id,
                        task_id,
                    )
                else:
                    await conn.execute(
                        """
                        INSERT INTO user_tasks (user_id, task_id, completed)
                        VALUES ($1, $2, TRUE)
                        """,
                        user_id,
                        task_id,
                    )

                reward_metadata = json.dumps(
                    {
                        "task_id": int(task["id"]),
                        "title": str(task["title"] or f"Task {task_id}"),
                        "task_type": str(task["type"] or ""),
                        "reward": reward,
                        "kind": "task_reward",
                        "mode": "manual_approved",
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )

                ref_key = f"task:reward:{int(user_id)}:{int(task_id)}:manual:v2"

                await conn.fetchval(
                    """
                    SELECT finance_post_user_reward(
                        $1, $2, $3, $4, $5, $6, $7, $8
                    )
                    """,
                    ref_key,
                    user_id,
                    reward,
                    "task_reward",
                    "Manual task approval reward posted via finance ledger",
                    "task_verifications",
                    task_id,
                    reward_metadata,
                )

                await conn.execute(
                    """
                    UPDATE users
                    SET xp_total = $1,
                        level = $2,
                        last_active_at = CURRENT_TIMESTAMP
                    WHERE user_id = $3
                    """,
                    new_xp,
                    new_level,
                    user_id,
                )

                await conn.execute(
                    """
                    UPDATE task_verifications
                    SET status = 'approved',
                        reviewed_at = CURRENT_TIMESTAMP,
                        reviewed_by = $3,
                        review_note = $4
                    WHERE user_id = $1 AND task_id = $2
                    """,
                    user_id,
                    task_id,
                    admin_user_id,
                    note or None,
                )

                xp_payload = json.dumps(
                    {
                        "task_id": int(task["id"]),
                        "task_type": str(task["type"] or ""),
                        "reward": reward,
                        "mode": "manual_approved",
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                await conn.execute(
                    """
                    INSERT INTO xp_events (user_id, event_type, xp_delta, payload_json)
                    VALUES ($1, $2, $3, $4)
                    """,
                    user_id,
                    "xp.task_complete",
                    int(TASK1_XP),
                    xp_payload,
                )

                audit_payload = json.dumps(
                    {
                        "task_id": int(task["id"]),
                        "title": str(task["title"] or f"Task {task_id}"),
                        "reward": reward,
                        "xp_delta": int(TASK1_XP),
                        "task_type": str(task["type"] or ""),
                        "mode": "manual_approved",
                        "reviewed_by": int(admin_user_id),
                        "review_note": note or None,
                        "finance_ref_key": ref_key,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                await conn.execute(
                    """
                    INSERT INTO audit_log (user_id, event_type, payload_json)
                    VALUES ($1, $2, $3)
                    """,
                    user_id,
                    "task.reward_claimed",
                    audit_payload,
                )

                return {
                    "ok": True,
                    "action": "approved",
                    "user_id": int(user_id),
                    "task_id": int(task_id),
                    "reward": reward,
                    "xp_delta": int(TASK1_XP),
                    "xp_total": int(new_xp),
                    "level": int(new_level),
                    "message": "Task approved and rewarded.",
                }

            await conn.execute(
                """
                UPDATE task_verifications
                SET status = 'rejected',
                    reviewed_at = CURRENT_TIMESTAMP,
                    reviewed_by = $3,
                    review_note = $4
                WHERE user_id = $1 AND task_id = $2
                """,
                user_id,
                task_id,
                admin_user_id,
                note or None,
            )

            audit_payload = json.dumps(
                {
                    "task_id": int(task["id"]),
                    "title": str(task["title"] or f"Task {task_id}"),
                    "task_type": str(task["type"] or ""),
                    "mode": "manual_rejected",
                    "reviewed_by": int(admin_user_id),
                    "review_note": note or None,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json)
                VALUES ($1, $2, $3)
                """,
                user_id,
                "task.verification_rejected",
                audit_payload,
            )

            return {
                "ok": True,
                "action": "rejected",
                "user_id": int(user_id),
                "task_id": int(task_id),
                "message": "Task verification rejected.",
            }