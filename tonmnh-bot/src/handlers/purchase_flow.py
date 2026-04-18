# handlers/purchase_flow.py
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler
from utils.json_utils import save_json

# שלבים לשיחה
(PRODUCT_SELECT, CONFIRM) = range(2)

async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE, products):
    user_id = update.effective_user.id
    if not context.args:
        # אם אין ארגומנט, הצג רשימת מוצרים עם כפתורים
        keyboard = []
        for pid, p in products.items():
            keyboard.append([InlineKeyboardButton(f"{p['name']} - {p['price']} TON", callback_data=f"buy_{pid}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Please select a product:", reply_markup=reply_markup)
        return PRODUCT_SELECT
    else:
        # אם יש ארגומנט, נשתמש בו ישירות
        context.user_data['temp_product'] = context.args[0]
        return await confirm_purchase(update, context, products)

async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE, products):
    query = update.callback_query
    if query:
        await query.answer()
        product_id = query.data.replace('buy_', '')
        context.user_data['temp_product'] = product_id
    else:
        product_id = context.user_data.get('temp_product')
        if not product_id:
            await update.message.reply_text("Error: No product selected.")
            return ConversationHandler.END

    product = products.get(product_id)
    if not product:
        await update.message.reply_text("Product not found.")
        return ConversationHandler.END

    context.user_data['temp_product_id'] = product_id
    context.user_data['temp_product_name'] = product['name']
    context.user_data['temp_price'] = product['price']

    keyboard = [[InlineKeyboardButton("✅ Confirm", callback_data="confirm_yes"),
                 InlineKeyboardButton("❌ Cancel", callback_data="confirm_no")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"*Confirm Purchase*\nProduct: {product['name']}\nPrice: {product['price']} TON\n\nAre you sure?"
    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return CONFIRM

async def finalize_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE, users, orders, products, USER_WALLET, ORDERS_FILE):
    query = update.callback_query
    await query.answer()
    if query.data == "confirm_yes":
        user_id = update.effective_user.id
        product_id = context.user_data.get('temp_product_id')
        price = context.user_data.get('temp_price')
        memo = f"slh_payment_{user_id}_{int(time.time())}"
        order_id = f"SLH-{int(time.time())}"
        orders[order_id] = {
            'order_id': order_id,
            'user_id': str(user_id),
            'product_id': product_id,
            'amount': price,
            'status': 'pending',
            'memo': memo,
            'timestamp': time.time()
        }
        save_json(ORDERS_FILE, orders)
        await query.edit_message_text(
            f"✅ Order created!\n\nTo complete purchase, send exactly {price} TON\n"
            f"to address {USER_WALLET}\nwith memo: {memo}",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text("Purchase cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Purchase cancelled.")
    context.user_data.clear()
    return ConversationHandler.END
