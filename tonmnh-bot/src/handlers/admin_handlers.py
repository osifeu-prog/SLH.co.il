from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def register_admin_handlers(bot, core_services):
    @bot.message_handler(commands=['admin'])
    def admin_main(message):
        if message.from_user.id != 224223270: return
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(" דוח רווחים", callback_data="adm_revenue"))
        markup.add(InlineKeyboardButton(" רשימת סוחרים", callback_data="adm_merchants"))
        markup.add(InlineKeyboardButton(" צפה בלוגים (Last 5)", callback_data="adm_logs"))
        
        bot.send_message(message.chat.id, " **SLH ADMIN OPERATOR**\nבחר פעולה לניהול האימפריה:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "adm_logs")
    def show_logs(call):
        with open('slh_core.log', 'r') as f:
            lines = f.readlines()[-5:]
        bot.send_message(call.message.chat.id, " **לוגים אחרונים:**\n" + "".join(lines))
