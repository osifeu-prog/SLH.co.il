# config.py - Docker-compatible
import os
import time

TOKEN = os.environ.get('SLH_BOT_TOKEN') or os.environ.get('BOT_TOKEN')
RPC_URL = os.environ.get('RPC_URL', 'https://toncenter.com/api/v2')
USER_WALLET = os.environ.get('USER_WALLET', '')
TONCENTER_API_KEY = os.environ.get('TONCENTER_API_KEY', '')
TON_NETWORK = os.environ.get('TON_NETWORK', 'mainnet')
ADMIN_ID = int(os.environ.get('ADMIN_USER_ID', '224223270'))
ADMIN_USERNAME = "@osifungar"

VERSION = "3.1.0-docker"
START_TIME = time.time()

if not TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

BASE_DIR = os.environ.get('APP_DIR', '/app')
LOCK_FILE = os.path.join(BASE_DIR, 'bot.lock')
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'bot.log')
WATCHDOG_LOG = os.path.join(BASE_DIR, 'logs', 'watchdog.log')
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.json')
ORDERS_FILE = os.path.join(DATA_DIR, 'orders.json')
