import telebot
from telebot import types

def register_merchant_handlers(bot):
    user_data = {}

    @bot.message_handler(commands=['open_store'])
    def start_wizard(message):
        print(f"DEBUG: Received /open_store from {message.chat.id}")
        user_data[message.chat.id] = {'step': 'TOKEN'}
        bot.send_message(message.chat.id, " **???? ??? ?-SLH Merchant!**\n??? ???? ?? ????? ???.\n\n??? ?? ?? ?-Bot Token ?-BotFather:")

    @bot.message_handler(func=lambda m: m.chat.id in user_data)
    def handle_wizard(message):
        print(f"DEBUG: Wizard Step: {user_data[message.chat.id].get('step')} | Input: {message.text}")
        state = user_data[message.chat.id]
        
        if state['step'] == 'TOKEN':
            token = message.text
            bot.delete_message(message.chat.id, message.message_id)
            state['step'] = 'NAME'
            bot.send_message(message.chat.id, " ????? ????. ??? ???? ????? ????")

        elif state['step'] == 'NAME':
            state['name'] = message.text
            state['step'] = 'PROD_1_TITLE'
            bot.send_message(message.chat.id, f" ???? '{state['name']}' ?????!\n?? ?? ????? ???????")

        # ... ??? ??????? ????? ...
