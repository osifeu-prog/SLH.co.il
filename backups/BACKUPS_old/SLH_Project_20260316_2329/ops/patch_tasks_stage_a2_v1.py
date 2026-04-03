from pathlib import Path
from textwrap import dedent

root = Path(".")

service_path = root / "app" / "services" / "tasks.py"
handler_path = root / "app" / "handlers" / "tasks.py"

service_text = dedent("""\
import json

from app.db.database import db
from app.services.xp import level_from_xp


TASK_XP_REWARDS = {
    2: 15,  # Invite 1 Friend
    3: 5,   # Daily Activity
}


async def get_tasks_overview(user_id: int) -> list[dict]:
    async with db.pool.acquire() as conn:
        tasks = await conn.fetch(
            \"""
            SELECT id, title, reward, type
            FROM tasks
            ORDER BY id
            \"""
        )

        user_row = await conn.fetchrow(
            \"""
            SELECT COALESCE(invited_count, 0) AS invited_count
            FROM users
            WHERE user_id = $1
            \""",
            user_id,
        )

        claimed_rows = await conn.fetch(
            \"""
            SELECT task_id, completed
            FROM user_tasks
            WHERE user_id = $1
            \""",
            user_id,
        )

        has_daily = await conn.fetchval(
            \"""
            SELECT EXISTS(
                SELECT 1
                FROM audit_log
                WHERE user_id = $1
                  AND event_type = 'claim.daily.v2'
            )
            \""",
            user_id,
        )

    invited_count = int(user_row["invited_count"] or 0) if user_row else 0
    claimed_map = {int(r["task_id"]): bool(r["completed"]) for r in claimed_rows}

    result = []
    for row in tasks:
        task_id = int(row["id"])
        reward = float(row["reward"] or 0)
        task_type = row["type"] or ""

        if claimed_map.get(task_id):
            status = "Claimed"
        elif task_id == 1:
            status = "Manual"
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
            await conn.execute("SELECT pg_advisory_xact_lock($1::bigint, $2::integer)", user_id, task_id)

            task = await conn.fetchrow(
                \"""
                SELECT id, title, reward, type
                FROM tasks
                WHERE id = $1
                \""",
                task_id,
            )

            if not task:
                return {
                    "ok": False,
                    "error": "task_not_found",
                    "message": "Task not found.",
                }

            existing = await conn.fetchrow(
                \"""
                SELECT completed
                FROM user_tasks
                WHERE user_id = $1 AND task_id = $2
                LIMIT 1
                \""",
                user_id,
                task_id,
            )

            if existing and bool(existing["completed"]):
                return {
                    "ok": False,
                    "error": "already_claimed",
                    "message": "Task already claimed.",
                }

            user_row = await conn.fetchrow(
                \"""
                SELECT COALESCE(invited_count, 0) AS invited_count,
                       COALESCE(xp_total, 0) AS xp_total
                FROM users
                WHERE user_id = $1
                FOR UPDATE
                \""",
                user_id,
            )

            if not user_row:
                return {
                    "ok": False,
                    "error": "user_not_found",
                    "message": "User not found.",
                }

            invited_count = int(user_row["invited_count"] or 0)
            current_xp = int(user_row["xp_total"] or 0)

            has_daily = await conn.fetchval(
                \"""
                SELECT EXISTS(
                    SELECT 1
                    FROM audit_log
                    WHERE user_id = $1
                      AND event_type = 'claim.daily.v2'
                )
                \""",
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

            await conn.execute(
                \"""
                INSERT INTO user_balances (user_id, available, locked)
                VALUES ($1, 0, 0)
                ON CONFLICT (user_id) DO NOTHING
                \""",
                user_id,
            )

            if existing:
                await conn.execute(
                    \"""
                    UPDATE user_tasks
                    SET completed = TRUE
                    WHERE user_id = $1 AND task_id = $2
                    \""",
                    user_id,
                    task_id,
                )
            else:
                await conn.execute(
                    \"""
                    INSERT INTO user_tasks (user_id, task_id, completed)
                    VALUES ($1, $2, TRUE)
                    \""",
                    user_id,
                    task_id,
                )

            await conn.execute(
                \"""
                UPDATE user_balances
                SET available = available + $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $2
                \""",
                reward,
                user_id,
            )

            await conn.execute(
                \"""
                UPDATE users
                SET balance = COALESCE(balance, 0) + $1,
                    xp_total = $2,
                    level = $3,
                    last_active_at = CURRENT_TIMESTAMP
                WHERE user_id = $4
                \""",
                reward,
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
                \"""
                INSERT INTO xp_events (user_id, event_type, xp_delta, payload_json)
                VALUES ($1, $2, $3, $4)
                \""",
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
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )

            await conn.execute(
                \"""
                INSERT INTO audit_log (user_id, event_type, payload_json)
                VALUES ($1, $2, $3)
                \""",
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
""")

handler_text = dedent("""\
import re
import logging

from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject

from app.services.tasks import get_tasks_overview, claim_task_reward

router = Router()
logger = logging.getLogger("slh.worker")


def _render_tasks_text(tasks: list[dict]) -> str:
    if not tasks:
        return "No tasks available."

    lines = ["Available Tasks", ""]
    for t in tasks:
        lines.append(
            f"{t['id']}. {t['title']} | {float(t['reward']):.4f} SLH | {t['status']}"
        )

    lines.extend(
        [
            "",
            "Claimable now:",
            "- Task 2: Invite 1 Friend",
            "- Task 3: Daily Activity",
            "",
            "Use /claim_task <id> or send: Claim task 2",
        ]
    )
    return "\\n".join(lines)


def _render_claim_result(res: dict) -> str:
    if not res["ok"]:
        return res.get("message", "Task claim failed.")

    return (
        "Task reward claimed.\\n\\n"
        f"Task ID: {int(res['task_id'])}\\n"
        f"Reward: {float(res['reward']):.4f} SLH\\n"
        f"XP gained: +{int(res['xp_delta'])}\\n"
        f"XP total: {int(res['xp_total'])}\\n"
        f"Level: {int(res['level'])}"
    )


@router.message(F.text == "Tasks")
@router.message(Command("tasks"))
async def show_tasks(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    logger.info("HANDLER: Tasks by %s", user_id)
    tasks = await get_tasks_overview(user_id)
    await message.answer(_render_tasks_text(tasks))


@router.message(Command("claim_task"))
async def claim_task_cmd(message: types.Message, command: CommandObject | None = None):
    user_id = message.from_user.id if message.from_user else 0
    raw = (command.args or "").strip() if command else ""

    if not raw.isdigit():
        return await message.answer("Usage: /claim_task <id>")

    task_id = int(raw)
    logger.info("HANDLER: /claim_task by %s task_id=%s", user_id, task_id)
    res = await claim_task_reward(user_id, task_id)
    await message.answer(_render_claim_result(res))


@router.message(F.text.regexp(r"^Claim task \\d+$"))
async def claim_task_text(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    text = message.text or ""
    m = re.match(r"^Claim task (\\d+)$", text.strip())
    if not m:
        return await message.answer("Usage: Claim task 2")

    task_id = int(m.group(1))
    logger.info("HANDLER: text claim_task by %s task_id=%s", user_id, task_id)
    res = await claim_task_reward(user_id, task_id)
    await message.answer(_render_claim_result(res))
""")

service_path.write_text(service_text, encoding="utf-8", newline="\\n")
handler_path.write_text(handler_text, encoding="utf-8", newline="\\n")

print("tasks service + handler patched")