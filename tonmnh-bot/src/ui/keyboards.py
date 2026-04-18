from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def kb_merchant_main():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(" ????? ????", callback_data="m_add_prod"),
        InlineKeyboardButton(" ????? ???", callback_data="m_view_store"),
        InlineKeyboardButton(" ????? ?-PRO", callback_data="buy_STORE_PRO")
    )
    return markup
