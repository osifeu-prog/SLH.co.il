from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def register_sales_handlers(bot, core_services):
    @bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
    def handle_purchase(call):
        u_id = call.message.chat.id
        product = call.data.replace("buy_", "")
        price = 5 if product == "STORE_PRO" else 2
        wallet = core_services._db['wallets']['TON']
        
        # רישום התשלום כממתין
        core_services._db['pending_payments'][u_id] = {'amount': price, 'product': product}
        
        msg = (f" **רכישת שדרוג: {product}**\n\n"
               f"1. שלח **{price} TON** לכתובת:\n{wallet}\n\n"
               f"2. **חובה:** הוסף את המספר הבא בהערה (Comment) של השליחה:\n{u_id}\n\n"
               "המערכת תאשר את הרכישה אוטומטית תוך מספר דקות מהשליחה.")
        
        bot.send_message(u_id, msg, parse_mode="Markdown")
