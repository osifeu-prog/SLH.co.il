# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
TON Airdrop Bot - CLEAN WORKING VERSION
"""
import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config
TOKEN = os.getenv("TELEGRAM_TOKEN", "8530795944:AAFXDx-vWZPpiXTlfsv5izUayJ4OpLLq3Ls")
API_URL = os.getenv("API_URL", "https://successful-fulfillment-production.up.railway.app")
TON_WALLET = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
PRICE = "44.4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    user = update.effective_user
    
    # Simple registration attempt
    try:
        user_data = {
            "telegram_id": user.id,
            "username": user.username,
            "first_name": user.first_name
        }
        response = requests.post(f"{API_URL}/api/register", json=user_data, timeout=5)
        if response.status_code == 200:
            logger.info(f"User registered: {user.id}")
    except:
        pass
    
    # SIMPLE welcome - no complex formatting
    welcome = f"""???? ??? {user.first_name}!

??? Airdrop TON ????.

????: {PRICE} ? (TON)
??????: 1000 ??????

??????:
/airdrop - ???? airdrop
/status - ??? ?????
/help - ????

???? ??????:
{TON_WALLET}"""
    
    await update.message.reply_text(welcome)

async def airdrop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create airdrop request"""
    user = update.effective_user
    await update.message.reply_text("???? airdrop...")
    
    try:
        # Request airdrop from API
        airdrop_data = {"user_id": user.id}
        response = requests.post(f"{API_URL}/api/airdrop", json=airdrop_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()["airdrop"]
            
            # SIMPLE payment message
            payment_msg = f"""Airdrop ????!

???? ????: {data['id']}
????: {data.get('price_ils', PRICE)} TON
????: ???

???? TON:
{data.get('ton_wallet', TON_WALLET)}

????? ?????:
{data.get('payment_url', '')}"""
            
            await update.message.reply_text(payment_msg)
            
            # Send QR code
            if data.get('qr_code'):
                await update.message.reply_photo(data['qr_code'])
                
            logger.info(f"Airdrop created: {data['id']}")
            
        else:
            await update.message.reply_text("????? ????. ??? ???.")
            
    except Exception as e:
        logger.error(f"Airdrop error: {e}")
        await update.message.reply_text("?????. ??? ??? ????? ????.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check user status"""
    user = update.effective_user
    
    try:
        response = requests.get(f"{API_URL}/api/user/{user.id}", timeout=5)
        
        if response.status_code == 200:
            user_data = response.json()
            
            if user_data.get("status") == "user_not_found":
                await update.message.reply_text("?? ?????. ??? /start")
                return
            
            status_msg = f"""????? ?????

??: {user_data.get('first_name', '?????')}
??????: {user_data.get('balance', 0)}
Airdrops: {len(user_data.get('airdrops', []))}"""
            
            await update.message.reply_text(status_msg)
        else:
            await update.message.reply_text("?? ???? ????? ??????.")
            
    except Exception as e:
        logger.error(f"Status error: {e}")
        await update.message.reply_text("????? ?????.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    help_text = """????

/start - ?????
/airdrop - ???? airdrop
/status - ??? ?????

?????:
1. ??? /start
2. ??? /airdrop
3. ??? ?????
4. ??? ??????

?????: @Osif83"""
    
    await update.message.reply_text(help_text)

def main():
    """Start the bot"""
    print("?? Starting CLEAN Airdrop Bot...")
    print(f"?? API: {API_URL}")
    
    # Clear webhooks
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=5)
        print("? Cleared webhooks")
    except:
        print("?? Could not clear webhooks")
    
    # Create app
    app = Application.builder().token(TOKEN).build()
    
    # Add commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("airdrop", airdrop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_cmd))
    
    # Start
    print("?? Bot is running and ready!")
    app.run_polling()

if __name__ == "__main__":
    main()



