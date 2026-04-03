from aiogram import Router, F, types
from aiogram.filters import Command
import re

from app.core.admin_guard import is_admin
from app.services.withdrawals import create_withdrawal
from app.services.withdrawals_query import (
    list_user_withdrawals,
    list_pending_withdrawals,
    approve_withdrawal,
    reject_withdrawal,
    mark_withdraw_sent,
    mark_withdraw_failed,
)

router = Router()

WALLET_RE = re.compile(r"^[A-Za-z0-9:_\-.]{6,}$")

HELP_TEXT = (
    "Withdraw format:\n"
    "Withdraw <amount> <wallet>\n\n"
    "Example:\n"
    "Withdraw 10 TQabc123xyz"
)


def _clean_wallet(raw: str) -> str:
    return (raw or "").splitlines()[0].strip()


@router.message(F.text == "Withdraw")
async def withdraw_help_btn(message: types.Message):
    await message.answer(HELP_TEXT)


@router.message(Command("withdraw"))
async def withdraw_help_cmd(message: types.Message):
    await message.answer(HELP_TEXT)


@router.message(F.text.startswith("Withdraw "))
async def withdraw_create(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0

    parts = (message.text or "").strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(HELP_TEXT)
        return

    _, amount_text, wallet_raw = parts
    wallet = _clean_wallet(wallet_raw)

    try:
        amount = float(amount_text)
    except ValueError:
        await message.answer("Amount must be a number.")
        return

    if amount <= 0:
        await message.answer("Amount must be positive.")
        return

    if not WALLET_RE.fullmatch(wallet):
        await message.answer("Wallet format is invalid. Use one-line wallet text only.")
        return

    result = await create_withdrawal(user_id, amount, wallet)

    if not result["ok"]:
        await message.answer(result["error"])
        return

    await message.answer(
        "Withdrawal created.\n\n"
        f"ID: {result['withdrawal_id']}\n"
        f"Amount: {result['amount']:.8f} SLH\n"
        f"Wallet: {result['wallet']}\n"
        f"Status: {result['status']}"
    )


@router.message(F.text == "Withdrawals")
async def withdrawals_btn(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    rows = await list_user_withdrawals(user_id, 10)

    if not rows:
        await message.answer("No withdrawals yet.")
        return

    lines = ["Your latest withdrawals", ""]
    for r in rows:
        tx = f" | tx={r['tx_hash']}" if r.get("tx_hash") else ""
        res = f" | reserve={r['reservation_status']}" if r.get("reservation_status") else ""
        lines.append(
            f"#{int(r['id'])} | {float(r['amount']):.8f} SLH | {r['status']} | {r['wallet']}{res}{tx}"
        )

    await message.answer("\n".join(lines))


@router.message(Command("withdrawals"))
async def withdrawals_cmd(message: types.Message):
    await withdrawals_btn(message)


@router.message(Command("pending_withdrawals"))
async def pending_withdrawals_cmd(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    if not is_admin(user_id):
        await message.answer("Forbidden")
        return

    rows = await list_pending_withdrawals(20)
    if not rows:
        await message.answer("No pending withdrawals.")
        return

    lines = ["Pending / approved withdrawals", ""]
    for r in rows:
        reserve = r.get("reservation_status") or "-"
        username = r.get("username") or "-"
        lines.append(
            f"#{int(r['id'])} | user={int(r['user_id'])} | @{username} | "
            f"{float(r['amount']):.8f} SLH | {r['wallet']} | status={r['status']} | reserve={reserve}"
        )
    await message.answer("\n".join(lines))


@router.message(Command("admin_withdrawals"))
async def admin_withdrawals_cmd(message: types.Message):
    await pending_withdrawals_cmd(message)


@router.message(Command("approve_withdraw"))
async def approve_withdraw_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = (message.text or "").strip().split(maxsplit=1)
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Usage: /approve_withdraw <id>")
        return

    withdrawal_id = int(parts[1])
    result = await approve_withdrawal(withdrawal_id, admin_id)

    if not result["ok"]:
        await message.answer(result["error"])
        return

    row = result["row"]
    await message.answer(
        f"Approved withdrawal #{int(row['id'])}\n"
        f"user={int(row['user_id'])}\n"
        f"amount={float(row['amount']):.8f} SLH\n"
        f"wallet={row['wallet']}\n"
        f"status={row['status']}\n"
        f"reserve={row.get('reservation_status')}"
    )


@router.message(Command("reject_withdraw"))
async def reject_withdraw_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = (message.text or "").strip().split(maxsplit=2)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: /reject_withdraw <id> <reason>")
        return

    withdrawal_id = int(parts[1])
    reason = parts[2] if len(parts) >= 3 else "Rejected by admin"

    result = await reject_withdrawal(withdrawal_id, admin_id, reason)

    if not result["ok"]:
        await message.answer(result["error"])
        return

    row = result["row"]
    await message.answer(
        f"Rejected withdrawal #{int(row['id'])}\n"
        f"user={int(row['user_id'])}\n"
        f"amount={float(row['amount']):.8f} SLH\n"
        f"reason={row.get('reject_reason')}\n"
        f"status={row['status']}"
    )


@router.message(Command("mark_sent"))
async def mark_sent_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = (message.text or "").strip().split(maxsplit=2)
    if len(parts) != 3 or not parts[1].isdigit():
        await message.answer("Usage: /mark_sent <id> <tx_hash>")
        return

    withdrawal_id = int(parts[1])
    tx_hash = parts[2].strip()

    result = await mark_withdraw_sent(withdrawal_id, admin_id, tx_hash)
    if not result["ok"]:
        await message.answer(result["error"])
        return

    row = result["row"]
    await message.answer(
        f"Marked sent withdrawal #{int(row['id'])}\n"
        f"user={int(row['user_id'])}\n"
        f"amount={float(row['amount']):.8f} SLH\n"
        f"tx_hash={row.get('tx_hash')}\n"
        f"status={row['status']}\n"
        f"reserve={row.get('reservation_status')}"
    )


@router.message(Command("mark_failed"))
async def mark_failed_cmd(message: types.Message):
    admin_id = message.from_user.id if message.from_user else 0
    if not is_admin(admin_id):
        await message.answer("Forbidden")
        return

    parts = (message.text or "").strip().split(maxsplit=2)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: /mark_failed <id> <error>")
        return

    withdrawal_id = int(parts[1])
    error_message = parts[2] if len(parts) >= 3 else "Unknown failure"

    result = await mark_withdraw_failed(withdrawal_id, admin_id, error_message)
    if not result["ok"]:
        await message.answer(result["error"])
        return

    row = result["row"]
    await message.answer(
        f"Marked failed withdrawal #{int(row['id'])}\n"
        f"user={int(row['user_id'])}\n"
        f"amount={float(row['amount']):.8f} SLH\n"
        f"reason={row.get('reject_reason')}\n"
        f"status={row['status']}"
    )