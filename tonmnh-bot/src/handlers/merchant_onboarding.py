import telebot
from src.ui.keyboards import kb_merchant_main

user_states = {}

def register_onboarding_handlers(bot, core_services):

    @bot.message_handler(commands=['setup_store'])
    def start_setup(message):
        u_id = message.from_user.id
        if not core_services.IdentityService.verify_access(u_id, "STORE_OPEN_4"):
            bot.reply_to(message, " שגיאה: דרוש רישיון STORE_OPEN_4.\nלרכישה: /buy_store")
            return

        user_states[u_id] = {'step': 'WAIT_TOKEN'}
        bot.send_message(u_id, " **הקמת חנות SLH**\nשלח לי את ה-Bot Token מ-BotFather:")

    @bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'WAIT_TOKEN')
    def handle_token(message):
        u_id = message.chat.id
        token = message.text
        bot.delete_message(u_id, message.message_id)

        store_id = core_services.MerchantRegistry.initialize_store(u_id, token)
        if store_id:
            user_states[u_id] = {'store_id': store_id, 'step': 'WAIT_NAME', 'prod_count': 0}
            bot.send_message(u_id, " אומת. מה שם החנות?")
        else:
            bot.send_message(u_id, " טוקן שגוי או בשימוש.")

    @bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'WAIT_NAME')
    def handle_name(message):
        u_id = message.chat.id
        store_name = message.text
        core_services.MerchantRegistry.set_store_name(user_states[u_id]['store_id'], store_name)
        
        bot.send_message(u_id, f" חנות '{store_name}' מוכנה!\nהשתמש בתפריט לניהול המוצרים:", 
                         reply_markup=kb_merchant_main())
        user_states[u_id]['step'] = 'IDLE'
