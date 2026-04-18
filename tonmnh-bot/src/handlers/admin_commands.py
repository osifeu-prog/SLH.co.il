# handlers/admin_commands.py
import subprocess
import sys
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID
from utils.json_utils import save_json

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied.")
        return
    keyboard = [
        ['Statistics', 'Last users'],
        ['Pending payments', 'Settings'],
        ['System', 'Processes'],
        ['Kill', 'Restart', 'Stop'],
        ['/help']
    ]
    await update.message.reply_text(
        "Admin panel - choose action:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, users, orders):
    if update.effective_user.id != ADMIN_ID:
        return
    total = len(users)
    paid = len([o for o in orders.values() if o.get('status') == 'paid'])
    pending = len([o for o in orders.values() if o.get('status') == 'pending'])
    affiliates = len([u for u in users.values() if u.get('referrer')])
    await update.message.reply_text(
        f"*Statistics*\n"
        f"Registered: {total}\n"
        f"Paid: {paid}\n"
        f"Pending: {pending}\n"
        f"Affiliates: {affiliates}",
        parse_mode='Markdown'
    )

async def admin_last_users(update: Update, context: ContextTypes.DEFAULT_TYPE, users):
    if update.effective_user.id != ADMIN_ID:
        return
    last = list(users.keys())[-15:]
    await update.message.reply_text("Last 15 users:\n" + "\n".join(last))

async def admin_pending(update: Update, context: ContextTypes.DEFAULT_TYPE, orders):
    if update.effective_user.id != ADMIN_ID:
        return
    pending = [o for o in orders.values() if o.get('status') == 'pending']
    if not pending:
        await update.message.reply_text("No pending payments.")
        return
    msg = "Pending payments:\n"
    for p in pending:
        msg += f"#{p.get('order_id')}: {p.get('amount')} TON from user {p.get('user_id')} (memo: {p.get('memo')})\n"
    await update.message.reply_text(msg)

async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "Settings:\n"
        "/set_price <product_id> <price>\n"
        "/set_group <product_id> <link>"
    )

async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE, products, PRODUCTS_FILE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        pid = context.args[0]
        price = float(context.args[1])
        if pid in products:
            products[pid]['price'] = price
            save_json(PRODUCTS_FILE, products)
            await update.message.reply_text(f"Price for product {pid} updated to {price} TON.")
        else:
            await update.message.reply_text("Product not found.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /set_price <product_id> <price>")

async def set_group(update: Update, context: ContextTypes.DEFAULT_TYPE, products, PRODUCTS_FILE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        pid = context.args[0]
        link = context.args[1]
        if pid in products:
            products[pid]['group_link'] = link
            save_json(PRODUCTS_FILE, products)
            await update.message.reply_text(f"Group link for product {pid} updated.")
        else:
            await update.message.reply_text("Product not found.")
    except IndexError:
        await update.message.reply_text("Usage: /set_group <product_id> <link>")

async def system_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /system <command>")
        return
    cmd = ' '.join(context.args)
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout + result.stderr
        if not output:
            output = "Command executed (no output)."
        if len(output) > 3500:
            for i in range(0, len(output), 3500):
                await update.message.reply_text(f"`\n{output[i:i+3500]}\n`", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"`\n{output}\n`", parse_mode='Markdown')
    except subprocess.TimeoutExpired:
        await update.message.reply_text("Command timed out after 10 seconds.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied.")
        return
    logging.warning(f"Bot restart triggered by admin {update.effective_user.id}")
    await update.message.reply_text("Restarting bot... Watchdog will bring it back.")
    sys.exit(0)

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied.")
        return
    logging.warning(f"Bot stopped by admin {update.effective_user.id}")
    await update.message.reply_text("Stopping bot... Watchdog will restart it.")
    sys.exit(0)

async def ps_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied.")
        return
    try:
        result = subprocess.run('ps aux | grep python', shell=True, capture_output=True, text=True)
        output = result.stdout + result.stderr
        await update.message.reply_text(f"`\n{output}\n`", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def kill_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /kill <PID>")
        return
    try:
        pid = int(context.args[0])
        subprocess.run(f"kill -9 {pid}", shell=True, capture_output=True)
        await update.message.reply_text(f"Process {pid} killed.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
