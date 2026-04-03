from aiogram import Router, F, types
import os
import logging

router = Router()
logger = logging.getLogger("slh.worker")

BOT_USERNAME = os.getenv("BOT_USERNAME", "TON_MNH_bot")

@router.message(F.text == "Invite Friend")
async def invite(message: types.Message):
    user_id = message.from_user.id if message.from_user else 0
    logger.info("HANDLER: Invite Friend by %s", user_id)

    link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    text = (
        "Invite friends and earn SLH!\n\n"
        f"Your referral link:\n{link}"
    )

    await message.answer(text)