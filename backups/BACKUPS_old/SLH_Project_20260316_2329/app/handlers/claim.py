import logging

from aiogram import F, Router, types
from aiogram.filters import Command

from app.services.daily import claim_daily
from app.services.bootstrap import grant_referral_reward_for_user

router = Router()
logger = logging.getLogger("slh.worker")


def _cooldown_text(wait_seconds: int, streak: int) -> str:
    hours = wait_seconds // 3600
    minutes = (wait_seconds % 3600) // 60
    return (
        "Daily reward already claimed.\n\n"
        f"Current streak: {streak}\n"
        f"Try again in about {hours}h {minutes}m."
    )


def _success_text(res: dict) -> str:
    reward = float(res["reward"])
    return (
        "Daily reward claimed.\n\n"
        f"Reward: {reward:.4f} SLH\n"
        f"MNH: {int(res['mnh_units'])}\n"
        f"Streak: {int(res['streak'])}\n"
        f"XP gained: +{int(res['xp_gain'])}\n"
        f"XP total: {int(res['xp_total'])}\n"
        f"Level: {int(res['level'])}"
    )


@router.message(Command("daily"))
@router.message(F.text == "Claim 1.0 SLH")
@router.message(F.text == "Daily Reward")
async def claim(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    username = message.from_user.username if message.from_user else None
    logger.info("HANDLER: daily claim by %s", user_id)

    res = await claim_daily(user_id, username)

    if not res["ok"]:
        if res.get("error") == "already_claimed":
            return await message.answer(
                _cooldown_text(
                    int(res.get("wait_seconds", 0)),
                    int(res.get("streak", 0)),
                )
            )
        return await message.answer("Daily reward failed. Please try again.")

    referral_reward_granted = await grant_referral_reward_for_user(user_id)
    logger.info(
        "HANDLER: daily referral reward check by %s granted=%s",
        user_id,
        referral_reward_granted,
    )

    await message.answer(_success_text(res))
