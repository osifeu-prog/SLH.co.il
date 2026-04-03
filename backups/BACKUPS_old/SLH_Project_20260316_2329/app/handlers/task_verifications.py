import re

from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject

from app.core.admin_guard import is_admin
from app.services.task_verifications import (
    request_task_verification,
    list_pending_task_verifications,
    review_task_verification,
)

router = Router()


def _render_verify_result(res: dict) -> str:
    if not res.get("ok"):
        return res.get("message", "Task verification failed.")

    return (
        "Task verification submitted.\n\n"
        f"Task ID: {int(res['task_id'])}\n"
        f"Title: {res['title']}\n"
        f"Status: {res['status']}\n"
        "Awaiting admin review."
    )


def _render_pending_rows(rows: list[dict]) -> str:
    if not rows:
        return "No pending task verifications."

    lines = ["Pending task verifications", ""]
    for row in rows:
        lines.append(
            f"user={int(row['user_id'])} | "
            f"task={int(row['task_id'])} | "
            f"title={row['title'] or '-'} | "
            f"reward={float(row['reward'] or 0):.4f} SLH | "
            f"requested_at={row['requested_at']} | "
            f"username={row['username'] or '-'}"
        )
    return "\n".join(lines)


def _render_review_result(res: dict) -> str:
    if not res.get("ok"):
        return res.get("message", "Task review failed.")

    if res.get("action") == "approved":
        return (
            "Task approved.\n\n"
            f"User ID: {int(res['user_id'])}\n"
            f"Task ID: {int(res['task_id'])}\n"
            f"Reward: {float(res['reward']):.4f} SLH\n"
            f"XP gained: +{int(res['xp_delta'])}\n"
            f"XP total: {int(res['xp_total'])}\n"
            f"Level: {int(res['level'])}"
        )

    return (
        "Task rejected.\n\n"
        f"User ID: {int(res['user_id'])}\n"
        f"Task ID: {int(res['task_id'])}"
    )


@router.message(Command("verify_task"))
async def verify_task_cmd(message: types.Message, command: CommandObject | None = None):
    user_id = message.from_user.id if message.from_user else 0
    raw = (command.args or "").strip() if command else ""

    if not raw.isdigit():
        return await message.answer("Usage: /verify_task <id>")

    task_id = int(raw)
    res = await request_task_verification(user_id, task_id)
    await message.answer(_render_verify_result(res))


@router.message(F.text.regexp(r"^[Vv]erify task \d+$"))
async def verify_task_text(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    text = (message.text or "").strip()
    m = re.match(r"^[Vv]erify task (\d+)$", text)
    if not m:
        return await message.answer("Usage: Verify task 1")

    task_id = int(m.group(1))
    res = await request_task_verification(user_id, task_id)
    await message.answer(_render_verify_result(res))


@router.message(F.text.regexp(r"^/[Vv]erify task \d+$"))
async def verify_task_slash_text(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    text = (message.text or "").strip()
    m = re.match(r"^/[Vv]erify task (\d+)$", text)
    if not m:
        return await message.answer("Usage: /verify_task 1")

    task_id = int(m.group(1))
    res = await request_task_verification(user_id, task_id)
    await message.answer(_render_verify_result(res))


@router.message(Command("pending_tasks"))
async def pending_tasks_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        return await message.answer("Forbidden")

    rows = await list_pending_task_verifications(20)
    await message.answer(_render_pending_rows(rows))


@router.message(Command("approve_task"))
async def approve_task_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        return await message.answer("Forbidden")

    parts = (message.text or "").strip().split(maxsplit=3)
    if len(parts) < 3 or (not parts[1].isdigit()) or (not parts[2].isdigit()):
        return await message.answer("Usage: /approve_task <user_id> <task_id> [note]")

    user_id = int(parts[1])
    task_id = int(parts[2])
    note = parts[3] if len(parts) >= 4 else None

    res = await review_task_verification(
        admin_user_id=admin_id,
        user_id=user_id,
        task_id=task_id,
        approve=True,
        review_note=note,
    )
    await message.answer(_render_review_result(res))


@router.message(Command("reject_task"))
async def reject_task_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        return await message.answer("Forbidden")

    parts = (message.text or "").strip().split(maxsplit=3)
    if len(parts) < 3 or (not parts[1].isdigit()) or (not parts[2].isdigit()):
        return await message.answer("Usage: /reject_task <user_id> <task_id> [note]")

    user_id = int(parts[1])
    task_id = int(parts[2])
    note = parts[3] if len(parts) >= 4 else None

    res = await review_task_verification(
        admin_user_id=admin_id,
        user_id=user_id,
        task_id=task_id,
        approve=False,
        review_note=note,
    )
    await message.answer(_render_review_result(res))