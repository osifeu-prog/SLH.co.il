import json

from app.db.database import db
from app.services.xp import level_from_xp


TASK_XP_REWARDS = {
    2: 15,
    3: 5,
}


async def get_tasks_overview(user_id: int) -> list[dict]:
    async with db.pool.acquire() as conn:
        tasks = await conn.fetch(
            """
            SELECT id, title, reward, type
            FROM tasks
            ORDER BY id
            """
        )

        user_row = await conn.fetchrow(
            """
            SELECT COALESCE(invited_count, 0) AS invited_count
            FROM users
            WHERE user_id = $1
            """,
            user_id,
        )

        claimed_rows = await conn.fetch(
            """
            SELECT task_id, completed
            FROM user_tasks
            WHERE user_id = $1
            """,
            user_id,
        )

        verification_rows = await conn.fetch(
            """
            SELECT task_id, status
            FROM task_verifications
            WHERE user_id = $1
            """,
            user_id,
        )

        has_daily = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1
                FROM audit_log
                WHERE user_id = $1
                  AND event_type IN ('claim.daily.v2','claim.daily.v3')
            )
            """,
            user_id,
        )

    invited_count = int(user_row["invited_count"] or 0) if user_row else 0
    claimed_map = {int(r["task_id"]): bool(r["completed"]) for r in claimed_rows}
    verification_map = {
        int(r["task_id"]): str(r["status"] or "").strip().lower()
        for r in verification_rows
    }

    result: list[dict] = []

    for row in tasks:
        task_id = int(row["id"])
        reward = float(row["reward"] or 0)
        task_type = str(row["type"] or "")
        verification_status = verification_map.get(task_id, "")

        if claimed_map.get(task_id):
            status = "Claimed"
        elif task_id == 1:
            if verification_status == "pending":
                status = "Pending Review"
            elif verification_status == "rejected":
                status = "Rejected"
            elif verification_status == "approved":
                status = "Claimed"
            else:
                status = "Verify Required"
        elif task_id == 2:
            status = "Claimable" if invited_count >= 1 else "Locked"
        elif task_id == 3:
            status = "Claimable" if bool(has_daily) else "Locked"
        else:
            status = "Locked"

        result.append(
            {
                "id": task_id,
                "title": row["title"] or f"Task {task_id}",
                "reward": reward,
                "type": task_type,
                "status": status,
            }
        )

    return result


async def claim_task_reward(user_id: int, task_id: int) -> dict:
    if task_id not in (2, 3):
        return {
            "ok": False,
            "error": "unsupported_task",
            "message": "This task is not claimable yet.",
        }

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

            existing = await conn.fetchrow(
                """
                SELECT completed
                FROM user_tasks
                WHERE user_id = $1 AND task_id = $2
                LIMIT 1
                """,
                user_id,
                task_id,
            )

            if existing and bool(existing["completed"]):
                return {"ok": False, "error": "already_claimed", "message": "Task already claimed."}

            user_row = await conn.fetchrow(
                """
                SELECT COALESCE(invited_count, 0) AS invited_count,
                       COALESCE(xp_total, 0) AS xp_total
                FROM users
                WHERE user_id = $1
                FOR UPDATE
                """,
                user_id,
            )

            if not user_row:
                return {"ok": False, "error": "user_not_found", "message": "User not found."}

            invited_count = int(user_row["invited_count"] or 0)
            current_xp = int(user_row["xp_total"] or 0)

            has_daily = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1
                    FROM audit_log
                    WHERE user_id = $1
                      AND event_type IN ('claim.daily.v2','claim.daily.v3')
                )
                """,
                user_id,
            )

            eligible = False
            if task_id == 2:
                eligible = invited_count >= 1
            elif task_id == 3:
                eligible = bool(has_daily)

            if not eligible:
                return {
                    "ok": False,
                    "error": "not_eligible",
                    "message": "Task requirements are not met yet.",
                }

            reward = float(task["reward"] or 0)
            xp_delta = int(TASK_XP_REWARDS.get(task_id, 0))
            new_xp = current_xp + xp_delta
            new_level = level_from_xp(new_xp)

            if existing:
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
                    "task_id": task_id,
                    "title": str(task["title"] or f"Task {task_id}"),
                    "task_type": str(task["type"] or ""),
                    "reward": reward,
                    "kind": "task_reward",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )

            ref_key = f"task:reward:{int(user_id)}:{int(task_id)}:v2"

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
                "Task reward posted via finance ledger",
                "user_tasks",
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

            xp_payload = json.dumps(
                {
                    "task_id": task_id,
                    "task_type": task["type"],
                    "reward": reward,
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
                xp_delta,
                xp_payload,
            )

            audit_payload = json.dumps(
                {
                    "task_id": task_id,
                    "title": task["title"],
                    "reward": reward,
                    "xp_delta": xp_delta,
                    "task_type": task["type"],
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
        "task_id": task_id,
        "reward": reward,
        "xp_delta": xp_delta,
        "xp_total": new_xp,
        "level": new_level,
    }