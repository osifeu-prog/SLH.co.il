from pathlib import Path

p = Path("app/handlers/tasks.py")
s = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")

s = '''import re
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
    claimable_lines = []

    for t in tasks:
        task_id = int(t["id"])
        title = t["title"]
        reward = float(t["reward"])
        status = t["status"]

        lines.append(f"{task_id}. {title} | {reward:.4f} SLH | {status}")

        if status == "Claimable":
            claimable_lines.append(f"- Task {task_id}: {title}")

    if claimable_lines:
        lines.extend([
            "",
            "Claimable now:",
            *claimable_lines,
            "",
            "Use /claim_task <id> or send: Claim task 2",
        ])
    else:
        lines.extend([
            "",
            "No task is claimable right now.",
            "",
            "Use /claim_task <id> after completing the requirement.",
        ])

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


@router.message(F.text.regexp(r"^(?i)claim task \d+$"))
async def claim_task_text(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    text = (message.text or "").strip()
    m = re.match(r"(?i)^claim task (\d+)$", text)
    if not m:
        return await message.answer("Usage: Claim task 2")

    task_id = int(m.group(1))
    logger.info("HANDLER: text claim_task by %s task_id=%s", user_id, task_id)
    res = await claim_task_reward(user_id, task_id)
    await message.answer(_render_claim_result(res))


@router.message(F.text.regexp(r"^/(?i:claim task) \d+$"))
async def claim_task_slash_text(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    text = (message.text or "").strip()
    m = re.match(r"^/(?i:claim task) (\d+)$", text)
    if not m:
        return await message.answer("Usage: /claim_task 2")

    task_id = int(m.group(1))
    logger.info("HANDLER: slash-text claim_task by %s task_id=%s", user_id, task_id)
    res = await claim_task_reward(user_id, task_id)
    await message.answer(_render_claim_result(res))
'''
p.write_text(s, encoding="utf-8", newline="\n")
print("tasks handler UX fixed")