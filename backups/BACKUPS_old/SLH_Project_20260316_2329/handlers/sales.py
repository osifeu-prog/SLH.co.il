from aiogram import Router, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(F.text.startswith("Sell"))
async def ask_confirm_sell(message: types.Message, user):
    try:
        amount = float(message.text.split()[1])

        if amount <= 0:
            await message.answer("Amount must be positive")
            return

        if amount > user["balance"]:
            await message.answer("Not enough SLH")
            return

        kb = InlineKeyboardBuilder()

        kb.button(
            text=f"Confirm sell {amount} SLH",
            callback_data=f"sell:{amount}"
        )

        kb.button(
            text="Cancel",
            callback_data="cancel"
        )

        await message.answer(
            f"Sell {amount} SLH ?",
            reply_markup=kb.as_markup()
        )

    except:
        await message.answer("Usage: Sell 10")


@router.callback_query(F.data.startswith("sell:"))
async def confirm_sell(callback: types.CallbackQuery, user):

    amount = float(callback.data.split(":")[1])

    await callback.message.edit_text(
        f"Sale order created for {amount} SLH"
    )

    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_sell(callback: types.CallbackQuery):

    await callback.message.edit_text("Cancelled")

    await callback.answer()
