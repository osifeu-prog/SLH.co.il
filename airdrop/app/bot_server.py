# -*- coding: utf-8 -*-
"""
SLH Investment House + HUB BOT
Full-featured investment house with HUB economic engine.

Features:
- ï¿½Y"S Live prices (12 coins)
- ï¿½Y'ï¿½ Investment plans (4 tiers, 4%-5.4% monthly)
- ï¿½Y'ï¿½ Wallet (TON/BNB/SLH/ZVK)
- ï¿½YZï¿½ Bonuses & games (slots, dice, basketball, darts)
- ï¿½Y>ï¿½ Risk management
- ï¿½Y"ï¿½ Swap/DEX
- ï¿½Yï¿½ï¿½ AI analysis
- ï¿½Y"S Dashboard
- ï¿½Y'ï¿½ Referrals (15% commission in SLH points)
- ï¿½Yï¿½T Buy SLH (444ï¿½,ï¿½ per coin)
- ï¿½Y'' VIP membership
- ï¿½YZï¿½ Airdrop
- ï¿½Y'ï¿½ Earn (daily tasks)
- ï¿½Y"ï¿½ Deals & promotions
"""
import os
import sys
import logging
import requests
import time
import json
import re
import random
import asyncio
import threading
from datetime import datetime, timedelta
from pathlib import Path

# ï¿½"?ï¿½"? Add shared module to path ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
_SHARED_DIR = Path(__file__).resolve().parent.parent.parent / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger("slh.hub")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8530795944:AAFXDx-vWZPpiXTlfsv5izUayJ4OpLLq3Ls")
ADMIN_ID = os.getenv("ADMIN_ID", "224223270")
TON_WALLET = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
BSC_CONTRACT = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"
SLH_PRICE_ILS = 444
LETSEXCHANGE_REF = os.getenv("LETSEXCHANGE_REF", "SLH_SWAP")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# ï¿½"?ï¿½"? Price API ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
COINS = {
    "BTC": {"symbol": "bitcoin", "emoji": "ï¿½YYï¿½", "name": "BTC"},
    "ETH": {"symbol": "ethereum", "emoji": "ï¿½Y"ï¿½", "name": "ETH"},
    "TON": {"symbol": "the-open-network", "emoji": "ï¿½Y'ï¿½", "name": "TON"},
    "BNB": {"symbol": "binancecoin", "emoji": "ï¿½YYï¿½", "name": "BNB"},
    "SOL": {"symbol": "solana", "emoji": "ï¿½YYï¿½", "name": "SOL"},
    "DOGE": {"symbol": "dogecoin", "emoji": "ï¿½Yï¿½ï¿½", "name": "DOGE"},
    "XRP": {"symbol": "ripple", "emoji": "ï¿½sï¿½", "name": "XRP"},
    "ADA": {"symbol": "cardano", "emoji": "ï¿½Y"ï¿½", "name": "ADA"},
    "DOT": {"symbol": "polkadot", "emoji": "ï¿½YYï¿½", "name": "DOT"},
    "AVAX": {"symbol": "avalanche-2", "emoji": "â¤ï¸", "name": "AVAX"},
    "LINK": {"symbol": "chainlink", "emoji": "ï¿½Y"-", "name": "LINK"},
}
ILS_RATE = 3.13  # USD to ILS approximate

_price_cache = {"prices": {}, "last_update": 0}

def fetch_prices():
    """Fetch live prices from CoinGecko."""
    now = time.time()
    if now - _price_cache["last_update"] < 120:  # cache 2 min
        return _price_cache["prices"]
    try:
        ids = ",".join(c["symbol"] for c in COINS.values())
        r = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd",
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            prices = {}
            for key, info in COINS.items():
                if info["symbol"] in data:
                    usd = data[info["symbol"]]["usd"]
                    prices[key] = {"usd": usd, "ils": round(usd * ILS_RATE, 2)}
            _price_cache["prices"] = prices
            _price_cache["last_update"] = now
            return prices
    except Exception as e:
        logger.error(f"Price fetch error: {e}")
    return _price_cache["prices"]


# ï¿½"?ï¿½"? In-memory user state ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
_user_data = {}

# Investment plans
INVESTMENT_PLANS = [
    {"name": "ï¿½YOï¿½ ×¤×§ï¿½"ï¿½.ï¿½Y ï¿½-ï¿½.ï¿½"×©ï¿½T", "rate": 4, "annual": 48, "min_ton": 1, "days": 30},
    {"name": "ï¿½Y"^ ×¤×§ï¿½"ï¿½.ï¿½Y ×¨ï¿½'×¢ï¿½.× ï¿½T", "rate": 4.5, "annual": 55, "min_ton": 5, "days": 90},
    {"name": "ï¿½Y'Z ×¤×§ï¿½"ï¿½.ï¿½Y ï¿½-×¦ï¿½T-×©× ×ªï¿½T", "rate": 5, "annual": 60, "min_ton": 10, "days": 180},
    {"name": "ï¿½Y'' ×¤×§ï¿½"ï¿½.ï¿½Y ×©× ×ªï¿½T", "rate": 5.4, "annual": 65, "min_ton": 25, "days": 365},
]

VIP_PLANS = {
    "basic": {"name": "VIP Basic", "price_ils": 41, "features": ["ï¿½"×ª×¨×ï¿½.×ª ï¿½zï¿½-ï¿½T×¨ï¿½T×", "ï¿½'ï¿½T×©ï¿½" ï¿½o×¢×¨ï¿½.×¥ VIP", "5 ï¿½z×©ï¿½Tï¿½zï¿½.×ª × ï¿½.×¡×¤ï¿½.×ª ï¿½'ï¿½Tï¿½.×"]},
    "pro": {"name": "VIP Pro", "price_ils": 99, "features": ["ï¿½"ï¿½>ï¿½o ï¿½'-Basic", "×¡ï¿½Tï¿½'× ï¿½oï¿½T× ï¿½oï¿½z×¡ï¿½-×¨", "ï¿½'ï¿½T×©ï¿½" ï¿½o-1-on-1", "×¢ï¿½zï¿½o×ª ×¨×¤×¨ï¿½o ï¿½>×¤ï¿½.ï¿½oï¿½" (30%)"]},
    "elite": {"name": "VIP Elite", "price_ils": 199, "features": ["ï¿½"ï¿½>ï¿½o ï¿½'-Pro", "×§ï¿½'ï¿½.×¦×ª ï¿½.ï¿½.ï¿½T×¡ï¿½~ ï¿½'ï¿½o×¢ï¿½"ï¿½T×ª", "NFT ï¿½-ï¿½T× × ï¿½>ï¿½o ï¿½-ï¿½.ï¿½"×©", "ï¿½'ï¿½T×©ï¿½" ï¿½zï¿½.×§ï¿½"ï¿½z×ª ï¿½oï¿½>ï¿½o ï¿½zï¿½.×¦×¨ ï¿½-ï¿½"×©"]},
}

SLH_BUY_TIERS = [
    {"amount": 0.0001, "price": 0.044},
    {"amount": 0.001, "price": 0.444},
    {"amount": 0.01, "price": 4.44},
    {"amount": 0.1, "price": 44.4},
    {"amount": 1, "price": 444},
]

_daily_tasks = [
    {"id": "join_channel", "title": "ï¿½Y"ï¿½ ï¿½"×¦ï¿½~×¨×£ ï¿½o×¢×¨ï¿½.×¥ @SLH_Community", "reward": 50},
    {"id": "share_bot", "title": "ï¿½Y"ï¿½ ×©×ª×£ ××ª ï¿½"ï¿½'ï¿½.ï¿½~ ×¢× ï¿½-ï¿½'×¨", "reward": 100},
    {"id": "visit_site", "title": "ï¿½YOï¿½ ï¿½'×§×¨ ï¿½'××ª×¨ slh-nft.com", "reward": 30},
    {"id": "follow_fb", "title": "ï¿½Y'ï¿½ ×¢×§ï¿½.ï¿½' ×ï¿½-×¨ï¿½T Facebook SLH", "reward": 40},
    {"id": "daily_login", "title": "ï¿½o. ï¿½>× ï¿½T×¡ï¿½" ï¿½Tï¿½.ï¿½zï¿½T×ª", "reward": 10},
]


def _get_user(user_id: int) -> dict:
    if user_id not in _user_data:
        _user_data[user_id] = {
            "username": "", "first_name": "",
            "slh_balance": 0.0, "zvk_balance": 0,
            "mnh_balance": 0.0, "rep_balance": 0, "zuz_balance": 0,
            "ton_available": 0.0, "ton_locked": 0.0,
            "ton_connected": False, "bnb_connected": False,
            "referrer": None, "referral_count": 0,
            "tasks_done": [], "total_earned": 0,
            "vip": None, "activated": False,
            "deposits": [], "withdrawals": 0, "transactions": 0,
            "games_played": 0, "games_won": 0,
            "risk_daily_loss": 10, "risk_max_position": 50, "risk_stop_loss": True,
            "joined": datetime.utcnow().isoformat(),
            "hub_points": 0,
            "balances_loaded": False,
        }
    return _user_data[user_id]


class SLHInvestmentBot:
    def __init__(self):
        self.offset = 0
        self.session = requests.Session()
        self.session.timeout = 30

        # ï¿½"?ï¿½"? Async event loop in background thread (for WalletEngine) ï¿½"?ï¿½"?
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._loop_thread.start()

        # ï¿½"?ï¿½"? WalletEngine (blockchain wallets) ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
        self.wallet = None
        self._wallet_ready = False
        self._pending_send = {}  # chat_id -> {step, token, to_user}
        self._pending_p2p  = {}  # chat_id -> {flow, step, data}
        try:
            from wallet_engine import WalletEngine
            self.wallet = WalletEngine()
            future = asyncio.run_coroutine_threadsafe(self.wallet.init(), self._loop)
            future.result(timeout=15)
            self._wallet_ready = True
            logger.info("ï¿½o. WalletEngine connected ï¿½?" DB + Redis + BSC + TON")
        except Exception as e:
            logger.warning(f"ï¿½sï¿½ï¸ WalletEngine init failed (falling back to mock): {e}")

        logger.info("ï¿½Ys? SLH Investment House + HUB initialized")

    def _run_async(self, coro, timeout=10):
        """Run an async coroutine from synchronous code via the background loop."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    # ï¿½"?ï¿½"? Telegram API ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
    def api(self, method, data=None):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
        try:
            r = self.session.post(url, json=data or {}, timeout=10)
            return r.json() if r.status_code == 200 else {}
        except:
            return {}

    def send(self, chat_id, text, reply_markup=None, parse_mode="HTML"):
        data = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        return self.api("sendMessage", data)

    def answer_callback(self, callback_id, text="", show_alert=False):
        return self.api("answerCallbackQuery", {"callback_query_id": callback_id, "text": text, "show_alert": show_alert})

    def edit_message(self, chat_id, message_id, text, keyboard=None):
        data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        if keyboard:
            data["reply_markup"] = json.dumps(keyboard)
        return self.api("editMessageText", data)

    # ï¿½"?ï¿½"? Reply keyboard (main menu buttons at bottom) ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
    def main_reply_keyboard(self):
        return {"keyboard": [
            [{"text": "ï¿½Y"S ï¿½"×©ï¿½.×§ ×¢ï¿½>×©ï¿½Tï¿½."}, {"text": "ï¿½Y'ï¿½ ï¿½"×©×§×¢ï¿½.×ª"}],
            [{"text": "ï¿½Y'ï¿½ ××¨× ×§"}, {"text": "ï¿½Y"" P2P ï¿½z×¡ï¿½-×¨"}],
            [{"text": "ï¿½YZï¿½ ï¿½'ï¿½.× ï¿½.×¡ï¿½T×"}, {"text": "ï¿½Y'ï¿½ ï¿½"ï¿½-ï¿½zï¿½Y"}],
            [{"text": "ï¿½Y"S ï¿½"×©ï¿½'ï¿½.×¨ï¿½""}, {"text": "ï¿½Yï¿½T ×¨ï¿½>ï¿½T×©×ª SLH"}],
            [{"text": "ï¿½Y'ï¿½ ï¿½"×¤×¢ï¿½oï¿½""}, {"text": "ï¿½Y"ï¿½ ×©ï¿½T×ªï¿½.×£"}],
            [{"text": "ï¿½Y"s ï¿½zï¿½"×¨ï¿½Tï¿½>ï¿½T×"}, {"text": "ï¿½Y"ï¿½ ï¿½zï¿½'×¦×¢ï¿½T×"}],
        ], "resize_keyboard": True, "one_time_keyboard": False}

    # ï¿½"?ï¿½"? Inline keyboards ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
    def hub_inline_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "ï¿½Y'ï¿½ Earn", "callback_data": "menu_earn"}, {"text": "ï¿½Y"" Swap", "callback_data": "menu_swap"}],
            [{"text": "ï¿½Y'' VIP", "callback_data": "menu_vip"}, {"text": "ï¿½YZï¿½ Airdrop", "callback_data": "menu_airdrop"}],
            [{"text": "ï¿½Yï¿½T Buy SLH", "callback_data": "menu_buy_slh"}],
            [{"text": "ï¿½Y'ï¿½ ï¿½"×¤× ï¿½Tï¿½.×ª ×©ï¿½oï¿½T", "callback_data": "menu_referral"}, {"text": "ï¿½Y"S ï¿½"×ªï¿½T×§ ×©ï¿½oï¿½T", "callback_data": "menu_portfolio"}],
            [{"text": "ï¿½Y"ï¿½ ï¿½zï¿½'×¦×¢ï¿½T×", "callback_data": "menu_deals"}, {"text": "ï¿½" ×¢ï¿½-×¨ï¿½"", "callback_data": "menu_help"}],
        ]}

    def back_keyboard(self):
        return {"inline_keyboard": [[{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½" ï¿½o×ª×¤×¨ï¿½Tï¿½~", "callback_data": "menu_main"}]]}

    def earn_keyboard(self):
        rows = []
        for t in _daily_tasks:
            rows.append([{"text": f"{t['title']} (+{t['reward']})", "callback_data": f"task_{t['id']}"}])
        rows.append([{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½" ï¿½o×ª×¤×¨ï¿½Tï¿½~", "callback_data": "menu_main"}])
        return {"inline_keyboard": rows}

    def vip_keyboard(self):
        return {"inline_keyboard": [
            [{"text": f"â­ Basic ï¿½?" {VIP_PLANS['basic']['price_ils']}ï¿½,ï¿½", "callback_data": "vip_basic"}],
            [{"text": f"ï¿½Y'Z Pro ï¿½?" {VIP_PLANS['pro']['price_ils']}ï¿½,ï¿½", "callback_data": "vip_pro"}],
            [{"text": f"ï¿½Y'' Elite ï¿½?" {VIP_PLANS['elite']['price_ils']}ï¿½,ï¿½", "callback_data": "vip_elite"}],
            [{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½" ï¿½o×ª×¤×¨ï¿½Tï¿½~", "callback_data": "menu_main"}],
        ]}

    def buy_slh_keyboard(self):
        rows = []
        for tier in SLH_BUY_TIERS:
            rows.append([{"text": f"ï¿½Yï¿½T {tier['amount']} SLH = {tier['price']}ï¿½,ï¿½", "callback_data": f"buy_slh_{tier['amount']}"}])
        rows.append([{"text": "ï¿½oï¿½ï¸ ×¡ï¿½>ï¿½.× ï¿½zï¿½.×ª×× ×ï¿½T×©ï¿½T×ª", "callback_data": "buy_slh_custom"}])
        rows.append([{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½" ï¿½o×ª×¤×¨ï¿½Tï¿½~", "callback_data": "menu_main"}])
        return {"inline_keyboard": rows}

    def invest_keyboard(self):
        rows = []
        for i, plan in enumerate(INVESTMENT_PLANS):
            rows.append([{"text": f"{plan['name']} | {plan['rate']}% | {plan['min_ton']} TON", "callback_data": f"invest_{i}"}])
        rows.append([{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½"", "callback_data": "menu_main"}])
        return {"inline_keyboard": rows}

    def games_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "ï¿½YZï¿½ ×¡ï¿½oï¿½.ï¿½~ï¿½T×", "callback_data": "game_slots"}, {"text": "ï¿½YZï¿½ ×§ï¿½.ï¿½'ï¿½Tï¿½.×ª", "callback_data": "game_dice"}],
            [{"text": "ï¿½Yï¿½? ï¿½>ï¿½"ï¿½.×¨×¡ï¿½o", "callback_data": "game_basketball"}, {"text": "ï¿½YZï¿½ ï¿½-×¦ï¿½T×", "callback_data": "game_darts"}],
            [{"text": "ï¿½Y'ï¿½ ï¿½"ï¿½z×¨ ZVK ï¿½?' TON", "callback_data": "game_convert"}],
            [{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½"", "callback_data": "menu_main"}],
        ]}

    # ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½
    # INVESTMENT HOUSE HANDLERS (original reply-keyboard buttons)
    # ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½

    def handle_start(self, chat_id, first_name, username, start_param=""):
        user = _get_user(chat_id)
        user["username"] = username or ""
        user["first_name"] = first_name or ""

        # Referral tracking
        referrer_id = None
        if start_param.startswith("ref_"):
            try:
                referrer_id = int(start_param[4:])
                if referrer_id != chat_id and not user["referrer"]:
                    user["referrer"] = referrer_id
                    ref_user = _get_user(referrer_id)
                    ref_user["referral_count"] += 1
                    ref_user["hub_points"] += 50
                    ref_user["total_earned"] += 50
                    self.send(referrer_id, f"ï¿½YZ? <b>ï¿½"×¤× ï¿½Tï¿½" ï¿½-ï¿½"×©ï¿½"!</b>\n\n@{username or first_name} ï¿½"×¦ï¿½~×¨×£ ï¿½"×¨ï¿½>ï¿½s!\n+50 × ×§ï¿½.ï¿½"ï¿½.×ª SLH ï¿½YZï¿½")
            except:
                referrer_id = None

        # === AUTO-SYNC TO WEBSITE DB ===
        # Critical: every /start creates/updates the user on Railway so they
        # can log into slh-nft.com immediately without @userinfobot friction.
        try:
            sync_url = os.getenv("SLH_API_URL", "https://slh-api-production.up.railway.app") + "/api/auth/bot-sync"
            sync_payload = {
                "telegram_id": chat_id,
                "username": username or "",
                "first_name": first_name or "",
                "photo_url": "",
                "referrer_id": referrer_id,
                "bot_secret": os.getenv("BOT_SYNC_SECRET", "slh-bot-sync-2026-default-please-override"),
            }
            sync_resp = self.session.post(sync_url, json=sync_payload, timeout=5)
            if sync_resp.status_code == 200:
                sync_data = sync_resp.json()
                user["web_synced"] = True
                user["web_is_registered"] = sync_data.get("is_registered", False)
                user["web_login_url"] = sync_data.get("login_url")
                logger.info(f"[bot-sync] ï¿½o. Synced {chat_id} (@{username}) to website ï¿½?" registered={sync_data.get('is_registered')}")
            else:
                logger.warning(f"[bot-sync] HTTP {sync_resp.status_code}: {sync_resp.text[:200]}")
        except Exception as e:
            logger.warning(f"[bot-sync] failed for {chat_id}: {e}")

        # === SYNC REAL TOKEN BALANCES FROM RAILWAY DB ===
        try:
            api_base = os.getenv("SLH_API_URL", "https://slh-api-production.up.railway.app")
            bal_resp = self.session.get(f"{api_base}/api/wallet/{chat_id}/balances", timeout=5)
            if bal_resp.status_code == 200:
                bal_data = bal_resp.json().get("balances", {})
                user["slh_balance"] = float(bal_data.get("SLH", user["slh_balance"]))
                user["zvk_balance"] = int(bal_data.get("ZVK", user["zvk_balance"]))
                user["mnh_balance"] = float(bal_data.get("MNH", user.get("mnh_balance", 0.0)))
                user["rep_balance"] = int(bal_data.get("REP", user.get("rep_balance", 0)))
                user["zuz_balance"] = int(bal_data.get("ZUZ", user.get("zuz_balance", 0)))
                user["balances_loaded"] = True
                logger.info(f"[bal-sync] ï¿½o. {chat_id}: SLH={user['slh_balance']}, ZVK={user['zvk_balance']}")
        except Exception as e:
            logger.warning(f"[bal-sync] failed for {chat_id}: {e}")

        invested = user["ton_locked"]
        profit = user["ton_locked"] * 0.04 if user["ton_locked"] > 0 else 0
        status = "ï¿½o. ï¿½z×©×§ï¿½T×¢ ×¤×¢ï¿½Tï¿½o" if user["activated"] else "â³ ï¿½zï¿½z×ªï¿½Tï¿½Y ï¿½oï¿½"×¤×¢ï¿½oï¿½""

        # Personal login link for the website (comes from auto-sync)
        login_url = user.get("web_login_url") or f"https://slh-nft.com/dashboard.html?uid={chat_id}"

        # Professional ASCII branding ï¿½?" clean, monospace-safe, SLH colors
        text = (
            f"<b>ï¿½oï¿½ SLH SPARK ï¿½oï¿½</b>\n"
            f"<i>Digital Investment House</i>\n"
            f"<code>ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½</code>\n"
            f"        ï¿½Y'Z  S L H\n"
            f"   Investment Ecosystem\n"
            f"      by SPARK IND\n"
            f"<code>ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½</code>\n\n"
            f"×©ï¿½oï¿½.× <b>{first_name}</b>! ï¿½Y'<\n"
            f"ï¿½Y?" <b>ï¿½"ï¿½zï¿½-ï¿½"ï¿½" ×©ï¿½oï¿½s:</b> <code>{chat_id}</code>\n"
            f"ï¿½Y'ï¿½ <b>Username:</b> @{username or 'ï¿½o× ï¿½"ï¿½.ï¿½'ï¿½"×¨'}\n\n"
            f"ï¿½YOï¿½ <b><a href=\"{login_url}\">ï¿½"ï¿½Tï¿½>× ×¡ ï¿½o××ª×¨ ï¿½"×ï¿½T×©ï¿½T ×©ï¿½oï¿½s ï¿½?ï¿½</a></b>\n"
            f"   <i>(ï¿½oï¿½-ï¿½T×¦ï¿½" ×ï¿½-×ª Â· ï¿½oï¿½o× ×¡ï¿½T×¡ï¿½zï¿½")</i>\n\n"
            f"<code>ï¿½"ï¿½ï¿½"ï¿½ ï¿½"×¡ï¿½~ï¿½~ï¿½.×¡ ×©ï¿½oï¿½s ï¿½"ï¿½ï¿½"ï¿½</code>\n"
            f"ï¿½Y'ï¿½ {status}\n"
            f"ï¿½Y'ï¿½ ï¿½zï¿½.×©×§×¢: <b>{invested:.2f} TON</b>\n"
            f"ï¿½Y"^ ×¨ï¿½.ï¿½.ï¿½-: <b>+{profit:.4f} TON</b>\n"
            f"ï¿½Y'Z SLH: <b>{user['slh_balance']:,.2f}</b>\n"
            f"ï¿½YZï¿½ ZVK: <b>{user['zvk_balance']}</b>\n\n"
            f"<code>ï¿½"ï¿½ï¿½"ï¿½ ï¿½zï¿½" ×ª×¨×¦ï¿½" ï¿½o×¢×©ï¿½.×ª? ï¿½"ï¿½ï¿½"ï¿½</code>\n"
            f"ï¿½Y"S <b>ï¿½"×©ï¿½.×§ ×¢ï¿½>×©ï¿½Tï¿½.</b> ï¿½?" ï¿½zï¿½-ï¿½T×¨ï¿½T×, ï¿½zï¿½'ï¿½zï¿½.×ª, ×¡ï¿½Tï¿½'× ï¿½oï¿½T×\n"
            f"ï¿½Y'ï¿½ <b>ï¿½"×©×§×¢ï¿½.×ª</b> ï¿½?" 4 ×ªï¿½.ï¿½>× ï¿½Tï¿½.×ª, 4%-5.4% ï¿½-ï¿½.ï¿½"×©ï¿½T\n"
            f"ï¿½Y'ï¿½ <b>××¨× ×§</b> ï¿½?" TON/BNB/SLH + ï¿½"×¢ï¿½'×¨ï¿½.×ª\n"
            f"ï¿½Y>ï¿½ <b>×¡ï¿½Tï¿½>ï¿½.ï¿½Y</b> ï¿½?" ï¿½"ï¿½'ï¿½"×¨ï¿½.×ª ×¡ï¿½Tï¿½>ï¿½.ï¿½Y ×ï¿½T×©ï¿½Tï¿½.×ª\n"
            f"ï¿½YZï¿½ <b>ï¿½'ï¿½.× ï¿½.×¡ï¿½T×</b> ï¿½?" ï¿½z×©ï¿½-×§ï¿½T× + ZVK\n"
            f"ï¿½Y'ï¿½ <b>ï¿½"ï¿½-ï¿½zï¿½Y</b> ï¿½?" +5 ZVK + ×¢ï¿½zï¿½oï¿½.×ª 10 ï¿½"ï¿½.×¨ï¿½.×ª\n"
            f"ï¿½Yï¿½ï¿½ <b>ï¿½-× ï¿½.×ª ×§ï¿½"ï¿½Tï¿½o×ªï¿½T×ª</b> ï¿½?" ï¿½zï¿½>ï¿½.×¨/×§× ï¿½" ï¿½'ï¿½z×¢×¨ï¿½>×ª\n"
            f"ï¿½Y"ï¿½ <b>ï¿½'ï¿½oï¿½.ï¿½' ï¿½Tï¿½.ï¿½zï¿½T</b> ï¿½?" ï¿½zï¿½" ï¿½-ï¿½"×© ï¿½"ï¿½Tï¿½.×\n"
            f"ï¿½YZ" <b>××§ï¿½"ï¿½zï¿½Tï¿½"</b> ï¿½?" ï¿½zï¿½"×¨ï¿½Tï¿½>ï¿½T× ï¿½.×§ï¿½.×¨×¡ï¿½T×\n\n"
            f"<code>ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½</code>\n"
            f"ï¿½Y'ï¿½ <b>SLH Investment House</b>\n"
            f"ï¿½sï¿½ <i>Powered by SPARK IND</i>\n"
            f"ï¿½Y?ï¿½ï¿½Y?ï¿½ <i>Built in Israel Â· 2026</i>"
        )
        # Inline keyboard with direct website button
        inline_kb = {
            "inline_keyboard": [
                [{"text": "ï¿½YOï¿½ ï¿½"ï¿½Tï¿½>× ×¡ ï¿½o××ª×¨ ï¿½"×ï¿½T×©ï¿½T", "url": login_url}],
                [
                    {"text": "ï¿½Yï¿½ï¿½ ï¿½-× ï¿½.×ª", "url": "https://slh-nft.com/community.html"},
                    {"text": "ï¿½Y"ï¿½ ï¿½'ï¿½oï¿½.ï¿½'", "url": "https://slh-nft.com/daily-blog.html"},
                ],
                [
                    {"text": "ï¿½YZï¿½ ï¿½"ï¿½-ï¿½zï¿½Y ï¿½-ï¿½'×¨ï¿½T×", "url": "https://slh-nft.com/invite.html"},
                    {"text": "ï¿½Y"- ï¿½zï¿½"×¨ï¿½Tï¿½>ï¿½T×", "url": "https://slh-nft.com/guides.html"},
                ],
            ]
        }
        try:
            self.session.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                    "reply_markup": inline_kb,
                },
                timeout=10,
            )
        except Exception as e:
            # Fallback to regular send if inline keyboard fails
            logger.warning(f"[handle_start] inline kb send failed: {e}")
            self.send(chat_id, text, self.main_reply_keyboard())
            return
        # Also show the persistent reply keyboard separately so bot menu stays visible
        self.send(chat_id, "ï¿½Y'? <i>×ª×¤×¨ï¿½Tï¿½~ ï¿½zï¿½"ï¿½T×¨:</i>", self.main_reply_keyboard())

    def handle_prices(self, chat_id):
        prices = fetch_prices()
        now = datetime.now()
        ts = now.strftime("%H:%M %d/%m/%Y")

        if not prices:
            self.send(chat_id, "ï¿½Y"S <b>ï¿½zï¿½-ï¿½T×¨ï¿½T× ï¿½-ï¿½Tï¿½T×</b>\nï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\nâ³ ï¿½~ï¿½.×¢ï¿½Y ï¿½zï¿½-ï¿½T×¨ï¿½T×...\n× ×¡ï¿½" ×©ï¿½.ï¿½' ï¿½'×¢ï¿½.ï¿½" ×¨ï¿½'×¢.",
                      self.main_reply_keyboard())
            return

        top = ["BTC", "ETH", "TON", "BNB", "SOL"]
        alts = ["DOGE", "XRP", "ADA", "DOT", "AVAX", "LINK"]

        text = "ï¿½Y"S <b>ï¿½zï¿½-ï¿½T×¨ï¿½T× ï¿½-ï¿½Tï¿½T×</b>\nï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\nï¿½Y'' <b>ï¿½zï¿½~ï¿½'×¢ï¿½.×ª ï¿½zï¿½.ï¿½'ï¿½Tï¿½oï¿½.×ª:</b>\n"
        for coin in top:
            if coin in prices:
                p = prices[coin]
                info = COINS[coin]
                text += f"  {info['emoji']} {coin}: ${p['usd']:,.2f} | {p['ils']:,.1f}ï¿½,ï¿½\n"

        text += "\nï¿½Y'ï¿½ <b>Altcoins:</b>\n"
        for coin in alts:
            if coin in prices:
                p = prices[coin]
                info = COINS[coin]
                text += f"  {info['emoji']} {coin}: ${p['usd']:.4f} | {p['ils']:.2f}ï¿½,ï¿½\n"

        ton_price = prices.get("TON", {})
        if ton_price:
            text += f"\nï¿½Y'ï¿½ 1 TON = {ton_price['ils']}ï¿½,ï¿½ | ${ton_price['usd']}\n"

        text += f"\nâ° {ts}\n\nï¿½Y'ï¿½ SLH Investment House"
        self.send(chat_id, text, self.main_reply_keyboard())

    def wallet_inline_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "ï¿½Y"ï¿½ ï¿½"×¤×§ï¿½"ï¿½"", "callback_data": "wallet_deposit"}, {"text": "ï¿½Y"ï¿½ ×©ï¿½oï¿½-", "callback_data": "wallet_send"}],
            [{"text": "ï¿½Y"o ï¿½"ï¿½T×¡ï¿½~ï¿½.×¨ï¿½Tï¿½"", "callback_data": "wallet_history"}, {"text": "ï¿½Y"" ×¨×¢× ï¿½Y", "callback_data": "wallet_refresh"}],
            [{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½" ï¿½o×ª×¤×¨ï¿½Tï¿½~", "callback_data": "menu_main"}],
        ]}

    def _refresh_balances(self, chat_id: int):
        """Pull fresh token balances from Railway API into in-memory dict."""
        user = _get_user(chat_id)
        try:
            api_base = os.getenv("SLH_API_URL", "https://slh-api-production.up.railway.app")
            r = self.session.get(f"{api_base}/api/wallet/{chat_id}/balances", timeout=5)
            if r.status_code == 200:
                bal = r.json().get("balances", {})
                user["slh_balance"] = float(bal.get("SLH", user["slh_balance"]))
                user["zvk_balance"] = int(bal.get("ZVK", user["zvk_balance"]))
                user["mnh_balance"] = float(bal.get("MNH", user.get("mnh_balance", 0.0)))
                user["rep_balance"] = int(bal.get("REP", user.get("rep_balance", 0)))
                user["zuz_balance"] = int(bal.get("ZUZ", user.get("zuz_balance", 0)))
                user["balances_loaded"] = True
        except Exception as e:
            logger.warning(f"[_refresh_balances] {chat_id}: {e}")

    def handle_wallet(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        # Always pull fresh balances from DB before displaying wallet
        self._refresh_balances(chat_id)

        # ï¿½"?ï¿½"? Try real blockchain wallet ï¿½"?ï¿½"?
        if self._wallet_ready and self.wallet:
            try:
                portfolio = self._run_async(self.wallet.get_user_portfolio(chat_id), timeout=12)
                if "error" not in portfolio:
                    bal = portfolio["balances"]
                    usd = portfolio["usd_values"]
                    prices = portfolio.get("prices", {})
                    bsc_addr = portfolio.get("bsc_address", "ï¿½?"")

                    text = (
                        f"ï¿½Y'ï¿½ <b>××¨× ×§ SLH</b>\n"
                        f"ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½\n\n"
                        f"ï¿½Y'Z <b>SLH:</b> {bal['SLH']}\n"
                        f"ï¿½YYï¿½ <b>BNB:</b> {bal['BNB']}\n"
                        f"ï¿½Y'ï¿½ <b>TON:</b> {bal['TON']}\n"
                        f"ï¿½YZï¿½ <b>ZVK:</b> {bal['ZVK']}\n\n"
                        f"ï¿½Y'ï¿½ <b>×©ï¿½.ï¿½.ï¿½T ï¿½'ï¿½"ï¿½.ï¿½o×¨:</b>\n"
                        f"  SLH: ${usd.get('SLH', 0):,.2f}\n"
                        f"  BNB: ${usd.get('BNB', 0):,.2f}\n"
                        f"  TON: ${usd.get('TON', 0):,.2f}\n"
                        f"  ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n"
                        f"  ï¿½Y'ï¿½ ×¡ï¿½"\"ï¿½>: <b>${usd.get('total', 0):,.2f}</b>\n\n"
                        f"ï¿½Y"- <b>ï¿½>×ªï¿½.ï¿½'×ª BSC:</b>\n<code>{bsc_addr}</code>\n\n"
                        f"ï¿½Y'ï¿½ <b>×¤×§ï¿½.ï¿½"ï¿½.×ª:</b>\n"
                        f"/deposit_address ï¿½?" ï¿½>×ªï¿½.ï¿½'×ª ï¿½"×¤×§ï¿½"ï¿½"\n"
                        f"/send_slh USER_ID AMOUNT ï¿½?" ×©ï¿½oï¿½- SLH\n"
                        f"/send_ton USER_ID AMOUNT ï¿½?" ×©ï¿½oï¿½- TON\n"
                        f"/tx_history ï¿½?" ï¿½"ï¿½T×¡ï¿½~ï¿½.×¨ï¿½Tï¿½T×ª ×¢×¡×§×ï¿½.×ª\n"
                        f"/verify TX_HASH CHAIN ï¿½?" ×ï¿½z×ª ï¿½"×¤×§ï¿½"ï¿½""
                    )
                    if message_id:
                        self.edit_message(chat_id, message_id, text, self.wallet_inline_keyboard())
                    else:
                        self.send(chat_id, text, self.wallet_inline_keyboard())
                    return
            except Exception as e:
                logger.warning(f"Wallet fetch failed for {chat_id}: {e}")

        # ï¿½"?ï¿½"? Fallback to in-memory ï¿½"?ï¿½"?
        ton_total = user["ton_available"] + user["ton_locked"]
        text = (
            f"ï¿½Y'ï¿½ <b>××¨× ×§</b>\n"
            f"ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
            f"ï¿½Y'Z SLH: {user['slh_balance']:.4f}\n"
            f"ï¿½YZï¿½ ZVK: {user['zvk_balance']}\n\n"
            f"ï¿½Yï¿½ï¿½ <b>ï¿½-×©ï¿½'ï¿½.ï¿½Y ï¿½'× ×§:</b>\n"
            f"  ï¿½Y'ï¿½ ï¿½-ï¿½zï¿½Tï¿½Y: {user['ton_available']:.4f} TON\n"
            f"  ï¿½Y"' × ×¢ï¿½.ï¿½o: {user['ton_locked']:.4f} TON\n"
            f"  ï¿½Y'ï¿½ ×¡ï¿½"\"ï¿½>: {ton_total:.4f} TON\n\n"
            f"ï¿½sï¿½ï¸ <i>××¨× ×§ blockchain ï¿½z×ªï¿½-ï¿½'×¨... × ×¡ï¿½" ×©ï¿½.ï¿½' ï¿½'×¢ï¿½.ï¿½" ×¨ï¿½'×¢</i>\n\n"
            f"ï¿½Y'ï¿½ <b>×¤×§ï¿½.ï¿½"ï¿½.×ª:</b>\n"
            f"/deposit - ï¿½"×¤×§ï¿½"ï¿½" ï¿½-ï¿½"×©ï¿½"\n"
            f"/send_slh USER_ID AMOUNT ï¿½?" ×©ï¿½oï¿½- SLH\n"
            f"/tx_history ï¿½?" ï¿½"ï¿½T×¡ï¿½~ï¿½.×¨ï¿½Tï¿½T×ª ×¢×¡×§×ï¿½.×ª"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.wallet_inline_keyboard())
        else:
            self.send(chat_id, text, self.wallet_inline_keyboard())

    # ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½
    # BLOCKCHAIN WALLET HANDLERS (wallet_engine integration)
    # ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½

    def handle_deposit_address(self, chat_id):
        """Generate and show deposit addresses for BSC + TON."""
        if not self._wallet_ready:
            self.send(chat_id, "ï¿½sï¿½ï¸ ï¿½z×¢×¨ï¿½>×ª ï¿½"××¨× ×§ï¿½T× ï¿½z×ªï¿½-ï¿½'×¨×ª... × ×¡ï¿½" ×©ï¿½.ï¿½' ï¿½'×¢ï¿½.ï¿½" ×¨ï¿½'×¢.", self.main_reply_keyboard())
            return
        try:
            addrs = self._run_async(self.wallet.generate_deposit_address(chat_id))
            text = (
                f"ï¿½Y"ï¿½ <b>ï¿½>×ªï¿½.ï¿½'ï¿½.×ª ï¿½"×¤×§ï¿½"ï¿½"</b>\n"
                f"ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½\n\n"
                f"ï¿½YYï¿½ <b>BSC (BNB / SLH Token):</b>\n"
                f"<code>{addrs['bsc_address']}</code>\n\n"
                f"ï¿½Y'ï¿½ <b>TON:</b>\n"
                f"<code>{addrs['ton_address']}</code>\n"
                f"ï¿½Y"ï¿½ <b>Memo:</b> <code>{addrs['memo']}</code>\n\n"
                f"ï¿½sï¿½ï¸ <b>ï¿½-×©ï¿½.ï¿½':</b>\n"
                f"ï¿½?ï¿½ BSC ï¿½?" ×©ï¿½oï¿½- BNB ×ï¿½. SLH Token ï¿½oï¿½>×ªï¿½.ï¿½'×ª ï¿½oï¿½z×¢ï¿½oï¿½"\n"
                f"ï¿½?ï¿½ TON ï¿½?" ×©ï¿½oï¿½- TON ï¿½oï¿½>×ªï¿½.ï¿½'×ª + ï¿½"ï¿½.×¡×£ ××ª ï¿½"-Memo\n"
                f"ï¿½?ï¿½ ×ï¿½-×¨ï¿½T ï¿½"×©ï¿½oï¿½Tï¿½-ï¿½": /verify TX_HASH bsc (×ï¿½. ton)\n\n"
                f"ï¿½Y'ï¿½ <i>ï¿½"ï¿½"×¤×§ï¿½"ï¿½" ×ªï¿½Tï¿½-×§×£ ×ï¿½.ï¿½~ï¿½.ï¿½zï¿½~ï¿½T×ª ×ï¿½-×¨ï¿½T ×ï¿½Tï¿½zï¿½.×ª</i>"
            )
            self.send(chat_id, text, self.wallet_inline_keyboard())
        except Exception as e:
            logger.error(f"Deposit address error: {e}")
            self.send(chat_id, "ï¿½O ×©ï¿½'ï¿½T×ï¿½" ï¿½'ï¿½T×¦ï¿½T×¨×ª ï¿½>×ªï¿½.ï¿½'×ª. × ×¡ï¿½" ×©ï¿½.ï¿½'.", self.main_reply_keyboard())

    def handle_verify_deposit(self, chat_id, args):
        """Verify a deposit tx on-chain: /verify TX_HASH bsc|ton"""
        if not self._wallet_ready:
            self.send(chat_id, "ï¿½sï¿½ï¸ ï¿½z×¢×¨ï¿½>×ª ï¿½"××¨× ×§ï¿½T× ï¿½z×ªï¿½-ï¿½'×¨×ª...", self.main_reply_keyboard())
            return
        parts = args.strip().split()
        if len(parts) < 2:
            self.send(chat_id,
                "ï¿½Y"< <b>×ï¿½Tï¿½zï¿½.×ª ï¿½"×¤×§ï¿½"ï¿½"</b>\n\n"
                "×©ï¿½Tï¿½zï¿½.×©: /verify TX_HASH CHAIN\n\n"
                "ï¿½"ï¿½.ï¿½'ï¿½zï¿½" BSC:\n<code>/verify 0xabc123... bsc</code>\n\n"
                "ï¿½"ï¿½.ï¿½'ï¿½zï¿½" TON:\n<code>/verify abc123... ton</code>",
                self.main_reply_keyboard())
            return

        tx_hash = parts[0]
        chain = parts[1].lower()
        if chain not in ("bsc", "ton"):
            self.send(chat_id, "ï¿½O Chain ï¿½-ï¿½Tï¿½Tï¿½' ï¿½oï¿½"ï¿½Tï¿½.×ª bsc ×ï¿½. ton", self.main_reply_keyboard())
            return

        self.send(chat_id, f"â³ ï¿½z×ï¿½z×ª ×¢×¡×§ï¿½" ×¢ï¿½o {chain.upper()}...", self.main_reply_keyboard())
        try:
            result = self._run_async(self.wallet.process_deposit(chat_id, tx_hash, chain), timeout=20)
            if "error" in result:
                self.send(chat_id, f"ï¿½O {result['error']}", self.wallet_inline_keyboard())
            else:
                self.send(chat_id,
                    f"ï¿½o. <b>ï¿½"×¤×§ï¿½"ï¿½" ×ï¿½.ï¿½z×ªï¿½"!</b>\n\n"
                    f"ï¿½Y'ï¿½ ×¡ï¿½>ï¿½.×: <b>{result['amount']} {result['token']}</b>\n"
                    f"ï¿½Y"- Chain: {result['chain'].upper()}\n"
                    f"ï¿½Y"ï¿½ ID: #{result['deposit_id']}\n\n"
                    f"ï¿½"ï¿½T×ª×¨ï¿½" ×¢ï¿½.ï¿½"ï¿½>× ï¿½". /wallet ï¿½o×¦×¤ï¿½Tï¿½Tï¿½"",
                    self.wallet_inline_keyboard())
                # Notify admin
                if str(chat_id) != ADMIN_ID:
                    user = _get_user(chat_id)
                    self.send(int(ADMIN_ID),
                        f"ï¿½Y'ï¿½ <b>ï¿½"×¤×§ï¿½"ï¿½" ï¿½-ï¿½"×©ï¿½"!</b>\n"
                        f"ï¿½Y'ï¿½ @{user['username']} ({chat_id})\n"
                        f"ï¿½Y'ï¿½ {result['amount']} {result['token']} ({chain.upper()})\n"
                        f"ï¿½Y"- TX: <code>{tx_hash[:30]}...</code>")
        except Exception as e:
            logger.error(f"Verify deposit error: {e}")
            self.send(chat_id, "ï¿½O ×©ï¿½'ï¿½T×ï¿½" ï¿½'×ï¿½Tï¿½zï¿½.×ª. × ×¡ï¿½" ×©ï¿½.ï¿½'.", self.main_reply_keyboard())

    def handle_send_internal(self, chat_id, args, token="SLH"):
        """Internal transfer: /send_slh USER_ID AMOUNT ï¿½?" uses bot-transfer API directly."""
        parts = args.strip().split()
        if len(parts) < 2:
            self.send(chat_id,
                f"ï¿½Y"ï¿½ <b>ï¿½"×¢ï¿½'×¨×ª {token}</b>\n\n"
                f"×©ï¿½Tï¿½zï¿½.×©: /send_{token.lower()} USER_ID AMOUNT\n\n"
                f"ï¿½"ï¿½.ï¿½'ï¿½zï¿½":\n<code>/send_{token.lower()} 123456789 10</code>\n\n"
                f"ï¿½Y'ï¿½ ï¿½"-USER_ID ×©ï¿½o ï¿½"× ï¿½z×¢ï¿½Y: ï¿½'×§×© ï¿½zï¿½z× ï¿½. ï¿½o×©ï¿½oï¿½.ï¿½- /myid\n"
                f"ï¿½Y'ï¿½ ×ï¿½. ï¿½"×©×ªï¿½z×© ï¿½'×ª×¤×¨ï¿½Tï¿½~: ï¿½Y"" P2P ï¿½z×¡ï¿½-×¨",
                self.main_reply_keyboard())
            return
        try:
            to_user = int(parts[0])
            amount  = float(parts[1])
        except (ValueError, IndexError):
            self.send(chat_id, "ï¿½O ×¤ï¿½.×¨ï¿½zï¿½~ ×©ï¿½'ï¿½.ï¿½T. ×©ï¿½oï¿½- USER_ID ï¿½.×ï¿½- ×¡ï¿½>ï¿½.×.", self.main_reply_keyboard())
            return

        if to_user == chat_id:
            self.send(chat_id, "ï¿½O ×ï¿½T ××¤×©×¨ ï¿½o×©ï¿½oï¿½.ï¿½- ï¿½o×¢×¦ï¿½zï¿½s", self.main_reply_keyboard())
            return

        # Use bot-transfer API (no JWT needed)
        self._p2p_execute_send(chat_id, {"token": token, "to_user": to_user, "amount": amount})

    def handle_tx_history(self, chat_id):
        """Show transaction history from DB."""
        if not self._wallet_ready:
            self.send(chat_id, "ï¿½sï¿½ï¸ ï¿½z×¢×¨ï¿½>×ª ï¿½"××¨× ×§ï¿½T× ï¿½z×ªï¿½-ï¿½'×¨×ª...", self.main_reply_keyboard())
            return
        try:
            history = self._run_async(self.wallet.get_transaction_history(chat_id, limit=10))
            if not history:
                self.send(chat_id, "ï¿½Y"o <b>ï¿½"ï¿½T×¡ï¿½~ï¿½.×¨ï¿½Tï¿½T×ª ×¢×¡×§×ï¿½.×ª</b>\n\n×ï¿½Tï¿½Y ×¢×¡×§×ï¿½.×ª ×¢ï¿½"ï¿½Tï¿½Tï¿½Y.", self.wallet_inline_keyboard())
                return
            text = "ï¿½Y"o <b>ï¿½"ï¿½T×¡ï¿½~ï¿½.×¨ï¿½Tï¿½T×ª ×¢×¡×§×ï¿½.×ª (10 ×ï¿½-×¨ï¿½.× ï¿½.×ª)</b>\nï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½\n\n"
            for tx in history:
                direction = "ï¿½Y"ï¿½" if tx["from_user_id"] == chat_id else "ï¿½Y"ï¿½"
                other = tx["to_user_id"] if tx["from_user_id"] == chat_id else tx["from_user_id"]
                dt = tx["created_at"][:16].replace("T", " ") if tx["created_at"] else "ï¿½?""
                text += (
                    f"{direction} <b>{tx['amount']} {tx['token']}</b> "
                    f"{'ï¿½?'' if direction == 'ï¿½Y"ï¿½' else 'ï¿½?ï¿½'} {other or 'system'} "
                    f"| {tx['type']} | {dt}\n"
                )
            self.send(chat_id, text, self.wallet_inline_keyboard())
        except Exception as e:
            logger.error(f"TX history error: {e}")
            self.send(chat_id, "ï¿½O ×©ï¿½'ï¿½T×ï¿½" ï¿½'ï¿½~×¢ï¿½T× ×ª ï¿½"ï¿½T×¡ï¿½~ï¿½.×¨ï¿½Tï¿½".", self.main_reply_keyboard())

    def handle_onchain_balance(self, chat_id):
        """Read on-chain balance for the ecosystem master wallets."""
        if not self._wallet_ready:
            self.send(chat_id, "ï¿½sï¿½ï¸ ï¿½z×¢×¨ï¿½>×ª ï¿½"××¨× ×§ï¿½T× ï¿½z×ªï¿½-ï¿½'×¨×ª...", self.main_reply_keyboard())
            return
        try:
            self.send(chat_id, "â³ ×§ï¿½.×¨× ï¿½T×ª×¨ï¿½.×ª ï¿½zï¿½"-blockchain...", self.main_reply_keyboard())
            slh_bal = self._run_async(self.wallet.get_slh_balance(BSC_CONTRACT), timeout=15)
            ton_bal = self._run_async(self.wallet.get_ton_balance(TON_WALLET), timeout=15)
            prices = self._run_async(self.wallet.get_live_prices())
            text = (
                f"ï¿½Y"- <b>ï¿½T×ª×¨ï¿½.×ª On-Chain</b>\n"
                f"ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½\n\n"
                f"ï¿½Y'Z <b>SLH Token (BSC):</b>\n"
                f"  Contract: <code>{BSC_CONTRACT[:20]}...</code>\n"
                f"  ï¿½T×ª×¨ï¿½": {slh_bal}\n\n"
                f"ï¿½Y'ï¿½ <b>TON Wallet:</b>\n"
                f"  ï¿½>×ªï¿½.ï¿½'×ª: <code>{TON_WALLET[:20]}...</code>\n"
                f"  ï¿½T×ª×¨ï¿½": {ton_bal} TON\n\n"
                f"ï¿½Y"S <b>ï¿½zï¿½-ï¿½T×¨ï¿½T×:</b>\n"
                f"  BTC: ${prices.get('btc_usd', 0):,.0f}\n"
                f"  ETH: ${prices.get('eth_usd', 0):,.0f}\n"
                f"  TON: ${prices.get('ton_usd', 0):.2f}\n"
                f"  BNB: ${prices.get('bnb_usd', 0):,.0f}\n"
                f"  SLH: {prices.get('slh_ils', 444)}ï¿½,ï¿½ (${prices.get('slh_usd', 0):.2f})"
            )
            self.send(chat_id, text, self.wallet_inline_keyboard())
        except Exception as e:
            logger.error(f"On-chain balance error: {e}")
            self.send(chat_id, "ï¿½O ×©ï¿½'ï¿½T×ï¿½" ï¿½'×§×¨ï¿½T×ï¿½" ï¿½zï¿½"-blockchain.", self.main_reply_keyboard())

    def handle_investments(self, chat_id, message_id=None):
        text = "ï¿½Y'ï¿½ <b>×ªï¿½.ï¿½>× ï¿½Tï¿½.×ª ï¿½"×©×§×¢ï¿½"</b>\nï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
        for plan in INVESTMENT_PLANS:
            text += (
                f"{plan['name']}\n"
                f"  ï¿½Y'ï¿½ {plan['rate']}% ï¿½-ï¿½.ï¿½"×©ï¿½T | {plan['annual']}% ×©× ×ªï¿½T\n"
                f"  ï¿½zï¿½T× ï¿½Tï¿½zï¿½.× {plan['min_ton']} TON | {plan['days']} ï¿½Tï¿½.×\n\n"
            )
        text += (
            "ï¿½Y'ï¿½ <b>×ï¿½Tï¿½s ï¿½oï¿½"×¤×§ï¿½Tï¿½":</b>\n"
            "1. ï¿½'ï¿½-×¨ ×ªï¿½.ï¿½>× ï¿½T×ª\n"
            "2. ×©ï¿½oï¿½- TON ï¿½z-@wallet\n"
            "3. ×©ï¿½oï¿½- ×¦ï¿½Tï¿½oï¿½.× ï¿½z×¡ï¿½s\n"
            "4. ï¿½"×¤×§ï¿½"ï¿½.ï¿½Y × ×¤×ªï¿½-!"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.invest_keyboard())
        else:
            self.send(chat_id, text, self.invest_keyboard())

    def handle_risk(self, chat_id):
        user = _get_user(chat_id)
        text = (
            f"ï¿½Y>ï¿½ <b>×¡ï¿½Tï¿½>ï¿½.ï¿½Y ï¿½.ï¿½'×§×¨ï¿½"</b>\n"
            f"ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
            f"ï¿½Y'ï¿½ <b>ï¿½"ï¿½'ï¿½"×¨ï¿½.×ª ï¿½"×¡ï¿½Tï¿½>ï¿½.ï¿½Y ×©ï¿½oï¿½s:</b>\n\n"
            f"ï¿½Ysï¿½ ï¿½"×¤×¡ï¿½" ï¿½Tï¿½.ï¿½zï¿½T: {user['risk_daily_loss']}%\n"
            f"ï¿½Y"S ×¤ï¿½.ï¿½-ï¿½T×¦ï¿½Tï¿½" ï¿½z×§×¡ï¿½Tï¿½zï¿½oï¿½T×ª: {user['risk_max_position']}%\n"
            f"ï¿½Y>' Stop Loss: {'ï¿½o. ×¤×¢ï¿½Tï¿½o' if user['risk_stop_loss'] else 'ï¿½O ï¿½>ï¿½'ï¿½.ï¿½T'}\n\n"
            f"ï¿½Y"ï¿½ <b>×¢×§×¨ï¿½.× ï¿½.×ª:</b>\n"
            f"ï¿½?ï¿½ ï¿½o× ï¿½oï¿½"×©×§ï¿½T×¢ ï¿½Tï¿½.×ª×¨ ï¿½zï¿½zï¿½" ×©ï¿½zï¿½.ï¿½>× ï¿½T× ï¿½oï¿½"×¤×¡ï¿½Tï¿½"\n"
            f"ï¿½?ï¿½ ï¿½oï¿½"×¤×¨ï¿½Tï¿½" ï¿½'ï¿½Tï¿½Y ï¿½z×¡×¤×¨ ×ªï¿½.ï¿½>× ï¿½Tï¿½.×ª\n"
            f"ï¿½?ï¿½ ï¿½o× ï¿½o×©ï¿½T× ï¿½"ï¿½>ï¿½o ×¢ï¿½o ×§ï¿½o×£ ×ï¿½-ï¿½"\n"
            f"ï¿½?ï¿½ ï¿½oï¿½"×©×ï¿½T×¨ × ï¿½-ï¿½Tï¿½oï¿½.×ª ï¿½oï¿½z×§×¨ï¿½" ï¿½-ï¿½T×¨ï¿½.×\n\n"
            f"ï¿½Y>ï¿½ <b>ï¿½"ï¿½z×¢×¨ï¿½>×ª ×©ï¿½.ï¿½z×¨×ª ×¢ï¿½oï¿½Tï¿½s!</b>"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_invite(self, chat_id):
        user = _get_user(chat_id)
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            f"ï¿½Y'ï¿½ <b>ï¿½"ï¿½-ï¿½zï¿½Y ï¿½-ï¿½'×¨ï¿½T×</b>\n\n"
            f"ï¿½Y"- <code>{ref_link}</code>\n\n"
            f"ï¿½"ï¿½-ï¿½z× ï¿½.×ª: {user['referral_count']} | +5 ZVK ï¿½oï¿½>ï¿½o ï¿½-ï¿½'×¨"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_activate(self, chat_id):
        user = _get_user(chat_id)
        user["activated"] = True
        self.send(chat_id, "ï¿½o. ï¿½zï¿½.×¤×¢ï¿½o!", self.main_reply_keyboard())

    def handle_share(self, chat_id):
        user = _get_user(chat_id)
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            f"ï¿½Y'Z SLH - ï¿½'ï¿½T×ª ï¿½"×©×§×¢ï¿½.×ª ï¿½"ï¿½Tï¿½'ï¿½Tï¿½~ï¿½oï¿½T\n\n"
            f"ï¿½o. ×ª×©ï¿½.×ï¿½" 4% ï¿½-ï¿½.ï¿½"×©ï¿½T / 65% ×©× ×ªï¿½T\n"
            f"ï¿½o. ××¨× ×§ ï¿½zï¿½o× (TON/BNB/SLH)\n"
            f"ï¿½o. ï¿½"×¢ï¿½'×¨ï¿½.×ª ï¿½zï¿½Tï¿½Tï¿½"ï¿½Tï¿½.×ª + blockchain\n"
            f"ï¿½o. × ï¿½T×ªï¿½.ï¿½- ×©ï¿½.×§ + ×¡ï¿½Tï¿½'× ï¿½oï¿½T×\n"
            f"ï¿½YZï¿½ +100 ZVK ï¿½z×ª× ï¿½"!\n\n"
            f"ï¿½Y'ï¿½ 22.221ï¿½,ï¿½ ï¿½'ï¿½oï¿½'ï¿½"!\n"
            f"ï¿½Y'? {ref_link}\n\n"
            f"ï¿½Y'ï¿½ SPARK IND | SLH Ecosystem"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_guides(self, chat_id):
        text = (
            "ï¿½Y"s <b>ï¿½zï¿½"×¨ï¿½Tï¿½>ï¿½T×</b>\n"
            "ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
            "ï¿½Y"- <b>ï¿½zï¿½"×¨ï¿½Tï¿½>ï¿½T SLH:</b>\n"
            "ï¿½?ï¿½ <a href='https://slh-nft.com/guides.html'>ï¿½zï¿½"×¨ï¿½Tï¿½s ï¿½zï¿½o× ï¿½'××ª×¨</a>\n\n"
            "ï¿½Y"< <b>× ï¿½.×©×ï¿½T×:</b>\n"
            "1ï¸ï¿½fï¿½ ×ï¿½Tï¿½s ï¿½oï¿½"×ªï¿½-ï¿½Tï¿½o ×¢× SLH\n"
            "2ï¸ï¿½fï¿½ ×ï¿½Tï¿½s ï¿½o×¤×ªï¿½.ï¿½- ××¨× ×§ TON\n"
            "3ï¸ï¿½fï¿½ ×ï¿½Tï¿½s ï¿½oï¿½"×¤×§ï¿½Tï¿½" ï¿½.ï¿½oï¿½"×©×§ï¿½T×¢\n"
            "4ï¸ï¿½fï¿½ ×ï¿½Tï¿½s ï¿½oï¿½"×©×ªï¿½z×© ï¿½'×¡ï¿½.ï¿½.××¤\n"
            "5ï¸ï¿½fï¿½ ï¿½zï¿½"×¨ï¿½Tï¿½s ×ï¿½'ï¿½~ï¿½-ï¿½"\n"
            "6ï¸ï¿½fï¿½ ×©×ï¿½oï¿½.×ª × ×¤ï¿½.×¦ï¿½.×ª\n\n"
            "ï¿½Y'ï¿½ ï¿½oï¿½>ï¿½o ×©×ï¿½oï¿½": /support"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_bonuses(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        text = (
            f"ï¿½YZï¿½ <b>ï¿½'ï¿½.× ï¿½.×¡ï¿½T×</b> | ZVK: {user['zvk_balance']}\n"
            f"ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
            f"ï¿½>ï¿½o ï¿½z×©ï¿½-×§ = 1 ZVK\n"
            f"ï¿½YZï¿½ ×¡ï¿½oï¿½.ï¿½~ï¿½T×: ×¤×¨×¡ ï¿½'ï¿½"ï¿½.ï¿½o ×¢ï¿½" 25 ZVK!\n"
            f"ï¿½YZï¿½ ×§ï¿½.ï¿½'ï¿½Tï¿½.×ª: 6=5 ZVK, 4-5=2 ZVK\n"
            f"ï¿½Yï¿½? ï¿½>ï¿½"ï¿½.×¨×¡ï¿½o: 4+=3 ZVK\n"
            f"ï¿½YZï¿½ ï¿½-×¦ï¿½T×: 6=5 ZVK, 4-5=2 ZVK\n\n"
            f"ï¿½Y'ï¿½ 10 ZVK = 1 TON | 50 = 4 | 100 = 7"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.games_keyboard())
        else:
            self.send(chat_id, text, self.games_keyboard())

    def handle_game(self, chat_id, game_type, callback_id, message_id):
        user = _get_user(chat_id)
        if user["zvk_balance"] < 1:
            self.answer_callback(callback_id, "ï¿½O ×ï¿½Tï¿½Y ï¿½z×¡×¤ï¿½T×§ ZVK!", True)
            return

        user["zvk_balance"] -= 1
        user["games_played"] += 1

        if game_type == "slots":
            symbols = ["ï¿½Yï¿½'", "ï¿½Yï¿½<", "ï¿½Yï¿½S", "ï¿½Y'Z", "7ï¸ï¿½fï¿½", "ï¿½Y"""]
            s1, s2, s3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)
            if s1 == s2 == s3:
                win = 25 if s1 == "ï¿½Y'Z" else 15
                user["zvk_balance"] += win
                user["games_won"] += 1
                result = f"ï¿½YZï¿½ {s1}{s2}{s3}\n\nï¿½YZ? ï¿½''×§×¤ï¿½.ï¿½~! +{win} ZVK!"
            elif s1 == s2 or s2 == s3:
                win = 3
                user["zvk_balance"] += win
                user["games_won"] += 1
                result = f"ï¿½YZï¿½ {s1}{s2}{s3}\n\nï¿½YZ? × ï¿½T×¦ï¿½-×ª! +{win} ZVK!"
            else:
                result = f"ï¿½YZï¿½ {s1}{s2}{s3}\n\nï¿½O ï¿½o× ï¿½"×¤×¢×"
        elif game_type == "dice":
            roll = random.randint(1, 6)
            if roll == 6:
                user["zvk_balance"] += 5
                user["games_won"] += 1
                result = f"ï¿½YZï¿½ {roll}\n\nï¿½YZ? ï¿½zï¿½.×©ï¿½o×! +5 ZVK!"
            elif roll >= 4:
                user["zvk_balance"] += 2
                user["games_won"] += 1
                result = f"ï¿½YZï¿½ {roll}\n\nï¿½YZ? × ï¿½T×¦ï¿½-×ª! +2 ZVK!"
            else:
                result = f"ï¿½YZï¿½ {roll}\n\nï¿½O ï¿½o× ï¿½"×¤×¢×"
        elif game_type == "basketball":
            score = random.randint(1, 6)
            if score >= 4:
                user["zvk_balance"] += 3
                user["games_won"] += 1
                result = f"ï¿½Yï¿½? {score} × ×§ï¿½.ï¿½"ï¿½.×ª!\n\nï¿½YZ? × ï¿½T×¦ï¿½-×ª! +3 ZVK!"
            else:
                result = f"ï¿½Yï¿½? {score} × ×§ï¿½.ï¿½"ï¿½.×ª\n\nï¿½O ï¿½o× ï¿½"×¤×¢×"
        elif game_type == "darts":
            score = random.randint(1, 6)
            if score == 6:
                user["zvk_balance"] += 5
                user["games_won"] += 1
                result = f"ï¿½YZï¿½ ï¿½z×¨ï¿½>ï¿½-! {score}\n\nï¿½YZ? × ï¿½T×¦ï¿½-×ª! +5 ZVK!"
            elif score >= 4:
                user["zvk_balance"] += 2
                user["games_won"] += 1
                result = f"ï¿½YZï¿½ {score}\n\nï¿½YZ? × ï¿½T×¦ï¿½-×ª! +2 ZVK!"
            else:
                result = f"ï¿½YZï¿½ {score}\n\nï¿½O ï¿½o× ï¿½"×¤×¢×"
        else:
            result = "ï¿½""

        result += f"\nï¿½YZï¿½ ZVK: {user['zvk_balance']}"
        self.edit_message(chat_id, message_id, result, self.games_keyboard())
        self.answer_callback(callback_id)

    def handle_game_convert(self, chat_id, callback_id, message_id):
        text = (
            "ï¿½Y'ï¿½ <b>ï¿½"ï¿½z×¨×ª ZVK ï¿½?' TON</b>\n\n"
            "10 ZVK = 1 TON\n"
            "50 ZVK = 4 TON\n"
            "100 ZVK = 7 TON\n\n"
            f"×©ï¿½oï¿½- ï¿½o:\n<code>{TON_WALLET}</code>"
        )
        self.edit_message(chat_id, message_id, text, self.games_keyboard())
        self.answer_callback(callback_id)

    def handle_dashboard(self, chat_id):
        user = _get_user(chat_id)
        self._refresh_balances(chat_id)
        ton_total = user["ton_available"] + user["ton_locked"]
        active_deposits = len([d for d in user.get("deposits", []) if d.get("status") == "active"])
        pending_deposits = len([d for d in user.get("deposits", []) if d.get("status") == "pending"])
        invested = user["ton_locked"]
        profit = user["ton_locked"] * 0.04

        win_rate = round(user["games_won"] / user["games_played"] * 100) if user["games_played"] > 0 else 0

        text = (
            f"ï¿½Y"S <b>ï¿½"×©ï¿½'ï¿½.×¨ï¿½"</b>\n"
            f"ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
            f"ï¿½Yï¿½ï¿½ <b>ï¿½-×©ï¿½'ï¿½.ï¿½Y ï¿½'× ×§:</b>\n"
            f"  ï¿½Y'ï¿½ ï¿½-ï¿½zï¿½Tï¿½Y: {user['ton_available']:.4f} TON\n"
            f"  ï¿½Y"' × ×¢ï¿½.ï¿½o: {user['ton_locked']:.4f} TON\n"
            f"  ï¿½Y'ï¿½ ×¡ï¿½"\"ï¿½>: {ton_total:.4f} TON\n\n"
            f"ï¿½Y'ï¿½ ï¿½"×©×§×¢ï¿½.×ª ×¤×¢ï¿½Tï¿½oï¿½.×ª: {active_deposits}\n"
            f"â³ ï¿½zï¿½z×ªï¿½T× ï¿½.×ª ï¿½o×ï¿½T×©ï¿½.×¨: {pending_deposits}\n"
            f"ï¿½Y'ï¿½ ï¿½zï¿½.×©×§×¢: {invested:.2f} TON\n"
            f"ï¿½Y"^ ×¨ï¿½.ï¿½.ï¿½-: +{profit:.4f} TON\n\n"
            f"ï¿½YZï¿½ ZVK: {user['zvk_balance']} | ï¿½z×©ï¿½-×§ï¿½T×: {user['games_played']} ({win_rate}%)\n"
            f"ï¿½Y'ï¿½ ï¿½"ï¿½-ï¿½z× ï¿½.×ª: {user['referral_count']}\n\n"
            f"SLH Investment House"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_swap_text(self, chat_id):
        text = (
            "ï¿½Y"" <b>SLH Swap ï¿½?" ï¿½"ï¿½z×¨×ª ï¿½zï¿½~ï¿½'×¢ï¿½.×ª</b>\n\n"
            "ï¿½"ï¿½zï¿½T×¨ï¿½. ï¿½'ï¿½Tï¿½Y 4,500+ ï¿½zï¿½~ï¿½'×¢ï¿½.×ª ×§×¨ï¿½T×¤ï¿½~ï¿½. ï¿½'×§ï¿½oï¿½.×ª!\n\n"
            "ï¿½Y'ï¿½ <b>ï¿½T×ª×¨ï¿½.× ï¿½.×ª:</b>\n"
            "ï¿½?ï¿½ ï¿½oï¿½o× ï¿½"×¨×©ï¿½zï¿½"\n"
            "ï¿½?ï¿½ ×¢ï¿½zï¿½oï¿½.×ª × ï¿½zï¿½.ï¿½>ï¿½.×ª\n"
            "ï¿½?ï¿½ ï¿½"ï¿½z×¨ï¿½" ï¿½T×©ï¿½T×¨ï¿½" ï¿½z××¨× ×§ ï¿½o××¨× ×§\n"
            "ï¿½?ï¿½ ×ªï¿½zï¿½Tï¿½>ï¿½" ï¿½'-TON, BTC, ETH, BNB ï¿½.×¢ï¿½.ï¿½"\n\n"
            "ï¿½Y"ï¿½ <b>ï¿½zï¿½'×¦×¢:</b> Cashback 0.5% ×¢ï¿½o ï¿½>ï¿½o ×¢×¡×§ï¿½"!\n\n"
            "ï¿½Y'? ï¿½oï¿½-×¥ ï¿½oï¿½"×ªï¿½-ï¿½oï¿½":"
        )
        kb = {"inline_keyboard": [
            [{"text": "ï¿½Y"" ï¿½"ï¿½z×¨ ×¢ï¿½>×©ï¿½Tï¿½.", "url": f"https://letsexchange.io/?ref={LETSEXCHANGE_REF}"}],
            [{"text": "ï¿½Y'ï¿½ TON ï¿½?' USDT", "url": f"https://letsexchange.io/?from=TON&to=USDT&ref={LETSEXCHANGE_REF}"}],
            [{"text": "ï¿½Y'ï¿½ BTC ï¿½?' TON", "url": f"https://letsexchange.io/?from=BTC&to=TON&ref={LETSEXCHANGE_REF}"}],
        ]}
        self.send(chat_id, text, kb)

    def handle_ai_analysis(self, chat_id):
        prices = fetch_prices()
        btc = prices.get("BTC", {}).get("usd", 67000)
        text = (
            f"ï¿½Yï¿½ï¿½ <b>× ï¿½T×ªï¿½.ï¿½- AI</b>\n"
            f"ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
            f"ï¿½Y"^ <b>×ª×¨ï¿½-ï¿½T×© ×©ï¿½.×¨ï¿½T:</b> ×× BTC ×©ï¿½.ï¿½'×¨ ${int(btc/1000)*1000+3000:,}, ×¦×¤ï¿½.ï¿½T ï¿½zï¿½"ï¿½oï¿½s ï¿½o-${int(btc/1000)*1000+8000:,}\n\n"
            f"ï¿½Y"ï¿½ <b>×ª×¨ï¿½-ï¿½T×© ï¿½"ï¿½.ï¿½'ï¿½T:</b> ×× BTC ×©ï¿½.ï¿½'×¨ ${int(btc/1000)*1000-2000:,}, ××¤×©×¨ï¿½T × ×¤ï¿½Tï¿½oï¿½" ï¿½o-${int(btc/1000)*1000-7000:,}\n\n"
            f"ï¿½YYï¿½ <b>×ª×¨ï¿½-ï¿½T×© × ï¿½Tï¿½Tï¿½~×¨ï¿½oï¿½T:</b> ×¦×¤ï¿½.ï¿½T ï¿½"ï¿½-ï¿½T×¡ï¿½" ×¦ï¿½"ï¿½"ï¿½T×ª\n\n"
            f"ï¿½sï¿½ï¸ ï¿½-ï¿½" ï¿½o× ï¿½Tï¿½T×¢ï¿½.×¥ ï¿½"×©×§×¢ï¿½"."
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_alerts(self, chat_id):
        text = (
            "ï¿½Y"" <b>ï¿½"×ª×¨×ï¿½.×ª ï¿½zï¿½-ï¿½T×¨</b>\n"
            "ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
            "ï¿½'×§×¨ï¿½.ï¿½'! ×ªï¿½.ï¿½>ï¿½o ï¿½oï¿½"ï¿½'ï¿½"ï¿½T×¨ ï¿½"×ª×¨×ï¿½.×ª ×¢ï¿½o:\n"
            "ï¿½?ï¿½ ï¿½zï¿½-ï¿½T×¨ ×©×¢ï¿½.ï¿½'×¨ ×¨ï¿½zï¿½"\n"
            "ï¿½?ï¿½ × ×¤ï¿½- ï¿½-×¨ï¿½Tï¿½'\n"
            "ï¿½?ï¿½ ï¿½-ï¿½"×©ï¿½.×ª ×©ï¿½.×§\n"
            "ï¿½?ï¿½ ×©ï¿½T× ï¿½.ï¿½T ï¿½'×ªï¿½T×§"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_deals_text(self, chat_id):
        text = (
            "ï¿½Y"ï¿½ <b>ï¿½zï¿½'×¦×¢ï¿½T× ×¤×¢ï¿½Tï¿½oï¿½T×</b>\n\n"
            "ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\n\n"
            "ï¿½Y"ï¿½ <b>ï¿½zï¿½'×¦×¢ ï¿½"×©×§ï¿½" ï¿½?" 30% ï¿½"× ï¿½-ï¿½"!</b>\n"
            "  ï¿½Y'ï¿½ ï¿½>ï¿½o ï¿½"ï¿½'ï¿½.ï¿½~ï¿½T× ï¿½'-30% ï¿½"× ï¿½-ï¿½"\n"
            "  ï¿½Yï¿½ï¿½ï¸ ×§ï¿½.ï¿½": <code>LAUNCH30</code>\n"
            "  â° ï¿½-ï¿½zï¿½Y ï¿½zï¿½.ï¿½'ï¿½'ï¿½o\n\n"
            "ï¿½Y'Z <b>ï¿½-ï¿½'ï¿½Tï¿½oï¿½" ï¿½zï¿½o×ï¿½" ï¿½?" 6 ï¿½'ï¿½.ï¿½~ï¿½T×</b>\n"
            "  ï¿½Y'ï¿½ ï¿½zï¿½-ï¿½T×¨: <b>199ï¿½,ï¿½</b>\n"
            "  ï¿½Y"ï¿½ ï¿½>ï¿½o 6 ï¿½'ï¿½.ï¿½~ï¿½T ï¿½"×¤×¨ï¿½Tï¿½zï¿½Tï¿½.×\n\n"
            "ï¿½Yï¿½ï¿½ <b>ï¿½"ï¿½-ï¿½zï¿½Y 3 = ×¤×¨ï¿½Tï¿½zï¿½Tï¿½.× ï¿½-ï¿½T× ×!</b>\n"
            "  ï¿½Y'ï¿½ ï¿½"ï¿½-ï¿½zï¿½Y 3 ï¿½-ï¿½'×¨ï¿½T×\n"
            "  ï¿½YZï¿½ ×§ï¿½'ï¿½o Community Premium ï¿½'ï¿½-ï¿½T× ×\n\n"
            "ï¿½Y>ï¿½ï¸ <b>ï¿½-ï¿½'ï¿½Tï¿½o×ª ×ï¿½'ï¿½~ï¿½-ï¿½"</b>\n"
            "  ï¿½Y'ï¿½ Guardian + Wallet = <b>99ï¿½,ï¿½</b>\n\n"
            "ï¿½YZ" <b>ï¿½zï¿½'×¦×¢ ×¡ï¿½~ï¿½.ï¿½"× ï¿½~ï¿½T×</b>\n"
            "  ï¿½Y'ï¿½ 50% ï¿½"× ï¿½-ï¿½" ×¢ï¿½o Academia\n"
            "  ï¿½Yï¿½ï¿½ï¸ ×§ï¿½.ï¿½": <code>STUDENT50</code>\n"
            "ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_buy_slh_text(self, chat_id):
        text = (
            f"ï¿½Yï¿½T <b>×¨ï¿½>ï¿½T×©×ª SLH Coin</b>\n\n"
            f"ï¿½Y'ï¿½ <b>ï¿½zï¿½-ï¿½T×¨:</b> 1 SLH = {SLH_PRICE_ILS}ï¿½,ï¿½\n"
            f"ï¿½Y"ï¿½ ï¿½zï¿½T× ï¿½Tï¿½zï¿½.×: 0.00004 SLH (0.018ï¿½,ï¿½)\n\n"
            f"ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\n"
            f"ï¿½Y"S <b>ï¿½zï¿½"×¨ï¿½'ï¿½.×ª ï¿½zï¿½-ï¿½T×¨:</b>\n\n"
        )
        for tier in SLH_BUY_TIERS:
            text += f"  ï¿½Yï¿½T {tier['amount']} SLH = {tier['price']}ï¿½,ï¿½\n"
        text += (
            f"\nï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\n"
            f"ï¿½Y'ï¿½ <b>××¨× ×§ TON:</b>\n<code>{TON_WALLET}</code>\n\n"
            f"ï¿½Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            f"ï¿½Y"ï¿½ ×©ï¿½oï¿½- ×¦ï¿½Tï¿½oï¿½.× ï¿½z×¡ï¿½s ×ï¿½. Transaction Hash\n"
            f"×ï¿½. ×¦ï¿½.×¨ ×§×©×¨ ×¢× @Osif83"
        )
        self.send(chat_id, text, self.buy_slh_keyboard())

    # ï¿½"?ï¿½"? Banking commands ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
    def handle_deposit(self, chat_id, args=""):
        user = _get_user(chat_id)
        if not args:
            self.send(chat_id, self._format_invest_plans(), self.invest_keyboard())
            return

        parts = args.split()
        try:
            plan_idx = int(parts[0]) - 1 if parts else 0
            amount = float(parts[1]) if len(parts) > 1 else INVESTMENT_PLANS[plan_idx]["min_ton"]
        except:
            plan_idx = 0
            amount = INVESTMENT_PLANS[0]["min_ton"]

        if plan_idx < 0 or plan_idx >= len(INVESTMENT_PLANS):
            plan_idx = 0
        plan = INVESTMENT_PLANS[plan_idx]

        deposit_id = len(user["deposits"]) + 1
        unlock_date = (datetime.utcnow() + timedelta(days=plan["days"])).strftime("%d/%m/%Y")
        monthly_return = round(amount * plan["rate"] / 100, 2)

        deposit = {
            "id": deposit_id, "plan": plan["name"], "amount": amount,
            "rate": plan["rate"], "days": plan["days"],
            "unlock_date": unlock_date, "status": "pending",
            "created": datetime.utcnow().isoformat()
        }
        user["deposits"].append(deposit)

        text = (
            f"ï¿½o. <b>ï¿½"×¤×§ï¿½"ï¿½" #{deposit_id} × ï¿½.×¦×¨ï¿½"!</b>\n"
            f"ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
            f"{plan['name']} | {amount} TON\n"
            f"×ª×©ï¿½.×ï¿½" ï¿½-ï¿½.ï¿½"×©ï¿½T×ª: ~{monthly_return} TON\n"
            f"× ×¢ï¿½.ï¿½o ×¢ï¿½": {unlock_date}\n\n"
            f"ï¿½Y'ï¿½ ×©ï¿½oï¿½- {amount} TON ï¿½o:\n"
            f"<code>{TON_WALLET}</code>\n\n"
            f"ï¿½.×©ï¿½oï¿½- ×¦ï¿½Tï¿½oï¿½.× ï¿½z×¡ï¿½s ï¿½o×ï¿½T×©ï¿½.×¨."
        )
        self.send(chat_id, text, self.main_reply_keyboard())

        # Notify admin
        if str(chat_id) != ADMIN_ID:
            admin_text = (
                f"ï¿½Y'ï¿½ <b>ï¿½"×¤×§ï¿½"ï¿½" ï¿½-ï¿½"×©ï¿½" #{deposit_id}</b>\n"
                f"ï¿½Y'ï¿½ @{user['username']} ({chat_id})\n"
                f"ï¿½Y'ï¿½ {plan['name']} | {amount} TON\n"
                f"ï¿½Y'ï¿½ {plan['rate']}% ï¿½-ï¿½.ï¿½"×©ï¿½T | {plan['days']} ï¿½Tï¿½zï¿½T×"
            )
            kb = {"inline_keyboard": [
                [{"text": "ï¿½o. ××©×¨", "callback_data": f"admin_approve_{chat_id}_{deposit_id}"},
                 {"text": "ï¿½O ï¿½"ï¿½-ï¿½"", "callback_data": f"admin_reject_{chat_id}_{deposit_id}"}],
            ]}
            self.send(int(ADMIN_ID), admin_text, kb)

    def handle_mydeposits(self, chat_id):
        user = _get_user(chat_id)
        if not user["deposits"]:
            self.send(chat_id, "ï¿½Y"< ×ï¿½Tï¿½Y ï¿½"×¤×§ï¿½"ï¿½.×ª ×¤×¢ï¿½Tï¿½oï¿½.×ª.\n\nï¿½oï¿½"×¤×§ï¿½"ï¿½" ï¿½-ï¿½"×©ï¿½": /deposit", self.main_reply_keyboard())
            return

        text = "ï¿½Y"< <b>ï¿½"ï¿½"×¤×§ï¿½"ï¿½.×ª ×©ï¿½oï¿½T</b>\nï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
        for d in user["deposits"]:
            status = "ï¿½o." if d["status"] == "active" else "â³" if d["status"] == "pending" else "ï¿½O"
            text += f"{status} #{d['id']} | {d['plan']} | {d['amount']} TON | {d['rate']}%\n"
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_withdraw(self, chat_id, args=""):
        if not args:
            self.send(chat_id,
                "ï¿½Y'ï¿½ <b>ï¿½z×©ï¿½Tï¿½>ï¿½"</b>\n\n×©ï¿½Tï¿½zï¿½.×©: /withdraw <ï¿½z×¡×¤×¨ ï¿½"×¤×§ï¿½"ï¿½"> <ï¿½>×ªï¿½.ï¿½'×ª TON>\n\nï¿½"ï¿½.ï¿½'ï¿½zï¿½": /withdraw 1 UQDhfy...\n\nï¿½o×¨×©ï¿½Tï¿½zï¿½": /mydeposits",
                self.main_reply_keyboard())
            return
        self.send(chat_id, "ï¿½Y"ï¿½ ï¿½'×§×©×ª ï¿½"ï¿½z×©ï¿½Tï¿½>ï¿½" × ×©ï¿½oï¿½-ï¿½" ï¿½o×ï¿½T×©ï¿½.×¨. × ×¢ï¿½"ï¿½>ï¿½Y ï¿½'ï¿½"×§ï¿½"×.", self.main_reply_keyboard())
        if str(chat_id) != ADMIN_ID:
            user = _get_user(chat_id)
            self.send(int(ADMIN_ID), f"ï¿½Y'ï¿½ <b>ï¿½'×§×©×ª ï¿½z×©ï¿½Tï¿½>ï¿½"!</b>\nUser: @{user['username']} ({chat_id})\nArgs: {args}")

    def handle_statement(self, chat_id):
        user = _get_user(chat_id)
        ton_total = user["ton_available"] + user["ton_locked"]
        text = (
            f"ï¿½Y"< <b>ï¿½"×£ ï¿½-×©ï¿½'ï¿½.ï¿½Y (30 ï¿½Tï¿½.×)</b>\n"
            f"ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
            f"ï¿½Y'ï¿½ ï¿½-ï¿½zï¿½Tï¿½Y: {user['ton_available']:.4f} TON\n"
            f"ï¿½Y"' × ×¢ï¿½.ï¿½o: {user['ton_locked']:.4f} TON\n"
            f"ï¿½Y'ï¿½ ×¡ï¿½"\"ï¿½>: {ton_total:.4f} TON\n\n"
            f"ï¿½Y"^ ï¿½"×¤×§ï¿½"ï¿½.×ª: {len(user['deposits'])}\n"
            f"ï¿½Y'ï¿½ ï¿½z×©ï¿½Tï¿½>ï¿½.×ª: {user['withdrawals']}\n"
            f"ï¿½Y"ï¿½ ×ª× ï¿½.×¢ï¿½.×ª: {user['transactions']}\n\n"
            f"SLH Investment House"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_kyc(self, chat_id, args=""):
        if args:
            self.send(chat_id, f"ï¿½o. ×©ï¿½oï¿½' 1 ï¿½"ï¿½.×©ï¿½o×: {args}\n\n×©ï¿½oï¿½- ×¦ï¿½Tï¿½oï¿½.× ×ª.ï¿½-. (ï¿½>×ªï¿½zï¿½.× ï¿½")", self.main_reply_keyboard())
        else:
            text = (
                "ï¿½Y"< <b>KYC - ï¿½-ï¿½Tï¿½"ï¿½.ï¿½T</b>\nï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
                "×©ï¿½oï¿½' 1: /kyc <×©× ï¿½zï¿½o×>\n"
                "×©ï¿½oï¿½' 2: ×©ï¿½oï¿½- ×¦ï¿½Tï¿½oï¿½.× ×ª.ï¿½-. (ï¿½>×ªï¿½zï¿½.× ï¿½")\n"
                "×©ï¿½oï¿½' 3: ï¿½"ï¿½z×ªï¿½Y ï¿½o×ï¿½T×©ï¿½.×¨"
            )
            self.send(chat_id, text, self.main_reply_keyboard())

    def handle_faq(self, chat_id):
        text = (
            "ï¿½" <b>FAQ</b>\n\n"
            "Q: ï¿½>ï¿½zï¿½" ×¢ï¿½.ï¿½oï¿½"?\nA: 22.221ï¿½,ï¿½ ï¿½-ï¿½" ×¤×¢ï¿½zï¿½T\n\n"
            "Q: ×ï¿½Tï¿½s ï¿½z×©ï¿½oï¿½zï¿½T×?\nA: @wallet ï¿½?' Buy TON ï¿½?' Send\n\n"
            "Q: ï¿½'ï¿½~ï¿½.ï¿½-?\nA: ï¿½z×¤×ªï¿½-ï¿½.×ª ×¤×¨ï¿½~ï¿½Tï¿½T× ï¿½o× × ×©ï¿½z×¨ï¿½T×\n\n"
            "Q: ×ªï¿½zï¿½Tï¿½>ï¿½"?\nA: /support"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_help(self, chat_id, message_id=None):
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            "ï¿½" <b>SLH Investment House</b>\n"
            "ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
            "ï¿½Y"S <b>ï¿½"×©ï¿½.×§</b> - 12 ï¿½zï¿½~ï¿½'×¢ï¿½.×ª, ×¡ï¿½.ï¿½.××¤, ï¿½"×ª×¨×ï¿½.×ª\n"
            "ï¿½Y'ï¿½ <b>ï¿½"×©×§×¢ï¿½.×ª</b> - 4 ×¤×§ï¿½"ï¿½.× ï¿½.×ª, 4%-65%\n"
            "ï¿½Y'ï¿½ <b>××¨× ×§</b> - TON/BNB/SLH + ï¿½"×¢ï¿½'×¨ï¿½.×ª\n"
            "ï¿½Y"ï¿½ <b>ï¿½z×¡ï¿½-×¨</b> - ×¡ï¿½.ï¿½.××¤, Limit, ï¿½"×ª×¨×ï¿½.×ª\n\n"
            "ï¿½Y'ï¿½ <b>ï¿½'× ×§:</b>\n"
            "/deposit /mydeposits /withdraw /statement\n\n"
            "ï¿½Y'ï¿½ <b>ï¿½z×¡ï¿½-×¨:</b>\n"
            "/prices /swap /limit /orders /alert /portfolio\n\n"
            "ï¿½Y'ï¿½ <b>××¨× ×§:</b>\n"
            "/pay /send /mybalance /myid /gas\n\n"
            "ï¿½Yï¿½T <b>SLH Coin:</b>\n"
            "/buyslh - ×¨ï¿½>ï¿½T×©×ª ï¿½zï¿½~ï¿½'×¢ SLH\n\n"
            "ï¿½Y"s <b>×¢ï¿½.ï¿½":</b>\n"
            "/share /faq /support /kyc /help\n\n"
            f"ï¿½Y'ï¿½ <b>×©×ª×£ ï¿½.ï¿½"×¨ï¿½.ï¿½.ï¿½Tï¿½- 15% ï¿½'× ×§ï¿½.ï¿½"ï¿½.×ª SLH!</b>\n"
            f"ï¿½Y"- <code>{ref_link}</code>\n\n"
            "SLH Investment House | SPARK IND"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.back_keyboard())
        else:
            self.send(chat_id, text, self.main_reply_keyboard())

    def _format_invest_plans(self):
        text = "ï¿½Y'ï¿½ <b>×ªï¿½.ï¿½>× ï¿½Tï¿½.×ª ï¿½"×©×§×¢ï¿½"</b>\nï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?\n\n"
        for i, plan in enumerate(INVESTMENT_PLANS, 1):
            text += (
                f"{plan['name']}\n"
                f"  ï¿½Y'ï¿½ {plan['rate']}% ï¿½-ï¿½.ï¿½"×©ï¿½T | {plan['annual']}% ×©× ×ªï¿½T\n"
                f"  ï¿½zï¿½T× ï¿½Tï¿½zï¿½.× {plan['min_ton']} TON | {plan['days']} ï¿½Tï¿½.×\n\n"
            )
        return text

    # ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½
    # HUB HANDLERS (inline keyboard callbacks)
    # ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½

    def handle_earn(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        done = len(user["tasks_done"])
        total = len(_daily_tasks)
        total_reward = sum(t["reward"] for t in _daily_tasks)
        done_reward = sum(t["reward"] for t in _daily_tasks if t["id"] in user["tasks_done"])
        text = (
            f"ï¿½Y'ï¿½ <b>ï¿½"×¨ï¿½.ï¿½.ï¿½Tï¿½- × ×§ï¿½.ï¿½"ï¿½.×ª SLH</b>\n\n"
            f"ï¿½Y"S ï¿½"×ª×§ï¿½"ï¿½zï¿½.×ª: {done}/{total} ï¿½z×©ï¿½Tï¿½zï¿½.×ª\n"
            f"ï¿½Y'Z ×©× ×¦ï¿½'×¨ ï¿½"ï¿½Tï¿½.×: {done_reward}/{total_reward} × ×§ï¿½.ï¿½"ï¿½.×ª\n"
            f"ï¿½Y'ï¿½ ï¿½T×ª×¨ï¿½": {user['hub_points']} × ×§ï¿½.ï¿½"ï¿½.×ª\n\n"
            f"ï¿½Y'? <b>ï¿½z×©ï¿½Tï¿½zï¿½.×ª ï¿½-ï¿½zï¿½T× ï¿½.×ª:</b>"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.earn_keyboard())
        else:
            self.send(chat_id, text, self.earn_keyboard())

    def handle_task(self, chat_id, task_id, callback_id, message_id):
        user = _get_user(chat_id)
        task = next((t for t in _daily_tasks if t["id"] == task_id), None)
        if not task:
            self.answer_callback(callback_id, "ï¿½O ï¿½z×©ï¿½Tï¿½zï¿½" ï¿½o× × ï¿½z×¦×ï¿½"")
            return
        if task_id in user["tasks_done"]:
            self.answer_callback(callback_id, "ï¿½o. ï¿½>ï¿½'×¨ ï¿½'ï¿½T×¦×¢×ª ï¿½z×©ï¿½Tï¿½zï¿½" ï¿½-ï¿½. ï¿½"ï¿½Tï¿½.×!", True)
            return
        user["tasks_done"].append(task_id)
        user["hub_points"] += task["reward"]
        user["total_earned"] += task["reward"]
        self.answer_callback(callback_id, f"ï¿½o. +{task['reward']} × ×§ï¿½.ï¿½"ï¿½.×ª!", True)
        self.handle_earn(chat_id, message_id)

    def handle_swap_inline(self, chat_id, message_id=None):
        text = (
            "ï¿½Y"" <b>SLH Swap ï¿½?" ï¿½"ï¿½z×¨×ª ï¿½zï¿½~ï¿½'×¢ï¿½.×ª</b>\n\n"
            "ï¿½"ï¿½zï¿½T×¨ï¿½. ï¿½'ï¿½Tï¿½Y 4,500+ ï¿½zï¿½~ï¿½'×¢ï¿½.×ª ×§×¨ï¿½T×¤ï¿½~ï¿½. ï¿½'×§ï¿½oï¿½.×ª!\n\n"
            "ï¿½Y'ï¿½ <b>ï¿½T×ª×¨ï¿½.× ï¿½.×ª:</b>\n"
            "ï¿½?ï¿½ ï¿½oï¿½o× ï¿½"×¨×©ï¿½zï¿½"\nï¿½?ï¿½ ×¢ï¿½zï¿½oï¿½.×ª × ï¿½zï¿½.ï¿½>ï¿½.×ª\n"
            "ï¿½?ï¿½ ï¿½"ï¿½z×¨ï¿½" ï¿½T×©ï¿½T×¨ï¿½" ï¿½z××¨× ×§ ï¿½o××¨× ×§\n"
            "ï¿½?ï¿½ ×ªï¿½zï¿½Tï¿½>ï¿½" ï¿½'-TON, BTC, ETH, BNB ï¿½.×¢ï¿½.ï¿½"\n\n"
            "ï¿½Y"ï¿½ <b>ï¿½zï¿½'×¦×¢:</b> Cashback 0.5% ×¢ï¿½o ï¿½>ï¿½o ×¢×¡×§ï¿½"!"
        )
        kb = {"inline_keyboard": [
            [{"text": "ï¿½Y"" ï¿½"ï¿½z×¨ ×¢ï¿½>×©ï¿½Tï¿½.", "url": f"https://letsexchange.io/?ref={LETSEXCHANGE_REF}"}],
            [{"text": "ï¿½Y'ï¿½ TON ï¿½?' USDT", "url": f"https://letsexchange.io/?from=TON&to=USDT&ref={LETSEXCHANGE_REF}"}],
            [{"text": "ï¿½Y'ï¿½ BTC ï¿½?' TON", "url": f"https://letsexchange.io/?from=BTC&to=TON&ref={LETSEXCHANGE_REF}"}],
            [{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½" ï¿½o×ª×¤×¨ï¿½Tï¿½~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_vip(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        current = user["vip"]
        status = f"ï¿½o. {VIP_PLANS[current]['name']}" if current else "ï¿½Y?" ï¿½-ï¿½T× ×"
        text = f"ï¿½Y'' <b>VIP Membership</b>\n\n×¡ï¿½~ï¿½~ï¿½.×¡: <b>{status}</b>\n\nï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\n"
        for key, plan in VIP_PLANS.items():
            marker = "ï¿½o." if current == key else "â­"
            text += f"\n{marker} <b>{plan['name']}</b> ï¿½?" {plan['price_ils']}ï¿½,ï¿½\n"
            for f in plan["features"]:
                text += f"  ï¿½?ï¿½ {f}\n"
        text += f"\nï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\nï¿½Y'ï¿½ <b>×ª×©ï¿½oï¿½.×:</b> ï¿½"×¢ï¿½'×¨ ï¿½o××¨× ×§ + ×¦ï¿½Tï¿½oï¿½.× ï¿½z×¡ï¿½s\nï¿½Y"ï¿½ <b>ï¿½-ï¿½'ï¿½Tï¿½oï¿½" ï¿½zï¿½o×ï¿½":</b> ï¿½>ï¿½o ï¿½"-VIP + 6 ï¿½'ï¿½.ï¿½~ï¿½T× = 199ï¿½,ï¿½ ï¿½'ï¿½oï¿½'ï¿½"!"
        if message_id:
            self.edit_message(chat_id, message_id, text, self.vip_keyboard())
        else:
            self.send(chat_id, text, self.vip_keyboard())

    def handle_vip_select(self, chat_id, plan_key, callback_id, message_id):
        plan = VIP_PLANS.get(plan_key)
        if not plan:
            self.answer_callback(callback_id, "ï¿½O")
            return
        text = (
            f"ï¿½Y'' <b>{plan['name']}</b>\n\n"
            f"ï¿½Y'ï¿½ <b>ï¿½zï¿½-ï¿½T×¨:</b> {plan['price_ils']}ï¿½,ï¿½\n\n"
            f"<b>×¤ï¿½T×¦'×¨ï¿½T×:</b>\n" +
            "\n".join(f"  ï¿½o. {f}" for f in plan["features"]) +
            f"\n\nï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\n"
            f"ï¿½Y'ï¿½ <b>×©ï¿½oï¿½- {plan['price_ils']}ï¿½,ï¿½ ï¿½o××¨× ×§ TON:</b>\n\n"
            f"<code>{TON_WALLET}</code>\n\n×ï¿½. ×¦ï¿½.×¨ ×§×©×¨ ×¢× @Osif83\n\n"
            f"ï¿½Y"ï¿½ ×©ï¿½oï¿½- ×¦ï¿½Tï¿½oï¿½.× ï¿½z×¡ï¿½s ×©ï¿½o ï¿½"×¢×¡×§ï¿½" ï¿½>×ï¿½Y\nï¿½o. ×ª×§ï¿½'ï¿½o ï¿½'ï¿½T×©ï¿½" ×ªï¿½.ï¿½s ï¿½"×§ï¿½.×ª"
        )
        kb = {"inline_keyboard": [
            [{"text": "ï¿½Y'ï¿½ ï¿½"×¢×ª×§ ï¿½>×ªï¿½.ï¿½'×ª ××¨× ×§", "callback_data": f"copy_wallet_{plan_key}"}],
            [{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½" ï¿½o-VIP", "callback_data": "menu_vip"}],
        ]}
        self.edit_message(chat_id, message_id, text, kb)
        self.answer_callback(callback_id)

    def handle_airdrop(self, chat_id, message_id=None):
        text = (
            "ï¿½YZï¿½ <b>SLH Airdrop</b>\n\n"
            f"ï¿½Y'ï¿½ <b>ï¿½zï¿½'×¦×¢ ï¿½"×©×§ï¿½":</b>\n1,000 ï¿½~ï¿½.×§× ï¿½T SLH = <b>444,000ï¿½,ï¿½</b>\n\n"
            f"ï¿½Y"S <b>×¡ï¿½~ï¿½~ï¿½.×¡:</b>\nï¿½Y'ï¿½ ï¿½z×©×ªï¿½z×©ï¿½T×: 38\nï¿½Y'ï¿½ ×¢×¡×§×ï¿½.×ª: 22\nï¿½YZï¿½ ï¿½z×§ï¿½.ï¿½zï¿½.×ª ×¤× ï¿½.ï¿½Tï¿½T×: 978/1,000\n\n"
            f"ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\n"
            f"ï¿½Y'ï¿½ <b>ï¿½o×¨ï¿½>ï¿½T×©ï¿½" ×©ï¿½oï¿½- ï¿½o××¨× ×§ TON:</b>\n<code>{TON_WALLET}</code>\n\n"
            f"ï¿½Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            "ï¿½Y"ï¿½ ×©ï¿½oï¿½- ×¦ï¿½Tï¿½oï¿½.× ï¿½z×¡ï¿½s / Transaction Hash\nï¿½o. ×§ï¿½'ï¿½oï¿½" ×ªï¿½.ï¿½s 24 ×©×¢ï¿½.×ª"
        )
        kb = {"inline_keyboard": [
            [{"text": "ï¿½Y'ï¿½ ×©ï¿½oï¿½- ×ª×©ï¿½oï¿½.×", "callback_data": "airdrop_pay"}],
            [{"text": "ï¿½Y"S ×¡ï¿½~ï¿½~ï¿½.×¡ ×©ï¿½oï¿½T", "callback_data": "airdrop_status"}],
            [{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½" ï¿½o×ª×¤×¨ï¿½Tï¿½~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_referral(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            f"ï¿½Y'ï¿½ <b>ï¿½"ï¿½"×¤× ï¿½Tï¿½.×ª ×©ï¿½oï¿½s</b>\n\n"
            f"ï¿½Y"- <b>ï¿½"×§ï¿½T×©ï¿½.×¨ ï¿½"×ï¿½T×©ï¿½T ×©ï¿½oï¿½s:</b>\n<code>{ref_link}</code>\n\n"
            f"ï¿½Y"S <b>×¡ï¿½~ï¿½~ï¿½T×¡ï¿½~ï¿½T×§ï¿½":</b>\n"
            f"ï¿½Y'ï¿½ ï¿½"×¤× ï¿½Tï¿½.×ª: <b>{user['referral_count']}</b>\n"
            f"ï¿½Y'ï¿½ × ×¦ï¿½'×¨ ï¿½zï¿½"×¤× ï¿½Tï¿½.×ª: <b>{user['referral_count'] * 50}</b> × ×§ï¿½.ï¿½"ï¿½.×ª SLH\n\n"
            f"ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\n"
            f"ï¿½Y'ï¿½ <b>×ï¿½Tï¿½s ï¿½oï¿½"×¨ï¿½.ï¿½.ï¿½Tï¿½-?</b>\n"
            f"1ï¸ï¿½fï¿½ ×©×ª×£ ××ª ï¿½"×§ï¿½T×©ï¿½.×¨ ×©ï¿½oï¿½s\n"
            f"2ï¸ï¿½fï¿½ ï¿½-ï¿½'×¨ï¿½T× × ×¨×©ï¿½zï¿½T× ï¿½"×¨ï¿½>ï¿½s\n"
            f"3ï¸ï¿½fï¿½ ï¿½z×§ï¿½'ï¿½o <b>50 × ×§ï¿½.ï¿½"ï¿½.×ª SLH</b> + <b>15% ×¢ï¿½zï¿½oï¿½" ï¿½'× ×§ï¿½.ï¿½"ï¿½.×ª SLH</b> ï¿½zï¿½>ï¿½o ×¨ï¿½>ï¿½T×©ï¿½"\n\n"
            f"ï¿½YZï¿½ ï¿½"ï¿½-ï¿½zï¿½Y 3 ï¿½-ï¿½'×¨ï¿½T× = <b>Community Premium ï¿½'ï¿½-ï¿½T× ×!</b>\n\n"
            f"ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\n"
            f"ï¿½Y"- <b>×§ï¿½T×©ï¿½.×¨ï¿½T× ï¿½oï¿½>ï¿½o ï¿½"ï¿½'ï¿½.ï¿½~ï¿½T×:</b>\n"
            f"ï¿½?ï¿½ ï¿½YZï¿½ Airdrop: <code>https://t.me/SLH_AIR_bot?start=ref_{chat_id}</code>\n"
            f"ï¿½?ï¿½ ï¿½Y>ï¿½ï¸ Guardian: <code>https://t.me/Grdian_bot?start=ref_{chat_id}</code>\n"
            f"ï¿½?ï¿½ ï¿½Y>' BotShop: <code>https://t.me/BotShop_bot?start=ref_{chat_id}</code>\n"
            f"ï¿½?ï¿½ ï¿½Y'ï¿½ Wallet: <code>https://t.me/SLH_Wallet_bot?start=ref_{chat_id}</code>\n"
            f"ï¿½?ï¿½ ï¿½YZ" Academia: <code>https://t.me/SLH_Academia_bot?start=ref_{chat_id}</code>\n"
            f"ï¿½?ï¿½ ï¿½Y'ï¿½ Community: <code>https://t.me/SLH_community_bot?start=ref_{chat_id}</code>"
        )
        kb = {"inline_keyboard": [
            [{"text": "ï¿½Y"< ï¿½"×¢×ª×§ ×§ï¿½T×©ï¿½.×¨ ï¿½"×¤× ï¿½Tï¿½"", "callback_data": "copy_ref"}],
            [{"text": "ï¿½Y"ï¿½ ×©×ª×£ ×¢× ï¿½-ï¿½'×¨", "url": f"https://t.me/share/url?url={ref_link}&text=ï¿½Ys? ï¿½"×¦ï¿½~×¨×¤ï¿½. ï¿½o-SLH - ï¿½'ï¿½T×ª ï¿½"×©×§×¢ï¿½.×ª ï¿½"ï¿½Tï¿½'ï¿½Tï¿½~ï¿½oï¿½T!"}],
            [{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½" ï¿½o×ª×¤×¨ï¿½Tï¿½~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_portfolio(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        vip_str = VIP_PLANS[user["vip"]]["name"] if user["vip"] else "ï¿½Y?" Free"
        text = (
            f"ï¿½Y"S <b>ï¿½"×ªï¿½T×§ ×©ï¿½oï¿½T</b>\n\n"
            f"ï¿½Y'Z SLH: {user['slh_balance']:.2f}\n"
            f"ï¿½YZï¿½ ZVK: {user['zvk_balance']}\n"
            f"ï¿½Y'ï¿½ Hub × ×§ï¿½.ï¿½"ï¿½.×ª: {user['hub_points']}\n"
            f"ï¿½Y'' ×¡ï¿½~ï¿½~ï¿½.×¡: {vip_str}\n"
            f"ï¿½Y'ï¿½ ï¿½"×¤× ï¿½Tï¿½.×ª: {user['referral_count']}\n"
            f"ï¿½o. ï¿½z×©ï¿½Tï¿½zï¿½.×ª ×©ï¿½'ï¿½.×¦×¢ï¿½.: {len(user['tasks_done'])}\n"
            f"ï¿½Y". ï¿½"×¦ï¿½~×¨×£: {user['joined'][:10]}\n\n"
            f"ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\n"
            f"ï¿½Y'ï¿½ <b>ï¿½"ï¿½z×¨×ª × ×§ï¿½.ï¿½"ï¿½.×ª:</b>\n"
            f"1,000 × ×§ï¿½.ï¿½"ï¿½.×ª = 1 SLH Token\n"
            f"5,000 × ×§ï¿½.ï¿½"ï¿½.×ª = 1 ï¿½-ï¿½.ï¿½"×© VIP Basic"
        )
        kb = {"inline_keyboard": [
            [{"text": "ï¿½Y'ï¿½ ï¿½"×¨ï¿½.ï¿½.ï¿½Tï¿½- ×¢ï¿½.ï¿½"", "callback_data": "menu_earn"}, {"text": "ï¿½Y'' ×©ï¿½"×¨ï¿½' VIP", "callback_data": "menu_vip"}],
            [{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½" ï¿½o×ª×¤×¨ï¿½Tï¿½~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_deals_inline(self, chat_id, message_id=None):
        text = (
            "ï¿½Y"ï¿½ <b>ï¿½zï¿½'×¦×¢ï¿½T× ×¤×¢ï¿½Tï¿½oï¿½T×</b>\n\nï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\n\n"
            "ï¿½Y"ï¿½ <b>ï¿½zï¿½'×¦×¢ ï¿½"×©×§ï¿½" ï¿½?" 30% ï¿½"× ï¿½-ï¿½"!</b>\n  ï¿½Y'ï¿½ ï¿½>ï¿½o ï¿½"ï¿½'ï¿½.ï¿½~ï¿½T× ï¿½'-30% ï¿½"× ï¿½-ï¿½"\n  ï¿½Yï¿½ï¿½ï¸ ×§ï¿½.ï¿½": <code>LAUNCH30</code>\n  â° ï¿½-ï¿½zï¿½Y ï¿½zï¿½.ï¿½'ï¿½'ï¿½o\n\n"
            "ï¿½Y'Z <b>ï¿½-ï¿½'ï¿½Tï¿½oï¿½" ï¿½zï¿½o×ï¿½" ï¿½?" 6 ï¿½'ï¿½.ï¿½~ï¿½T×</b>\n  ï¿½Y'ï¿½ ï¿½zï¿½-ï¿½T×¨: <b>199ï¿½,ï¿½</b>\n\n"
            "ï¿½Yï¿½ï¿½ <b>ï¿½"ï¿½-ï¿½zï¿½Y 3 = ×¤×¨ï¿½Tï¿½zï¿½Tï¿½.× ï¿½-ï¿½T× ×!</b>\n\n"
            "ï¿½Y>ï¿½ï¸ <b>ï¿½-ï¿½'ï¿½Tï¿½o×ª ×ï¿½'ï¿½~ï¿½-ï¿½"</b>\n  ï¿½Y'ï¿½ Guardian + Wallet = <b>99ï¿½,ï¿½</b>\n\n"
            "ï¿½YZ" <b>ï¿½zï¿½'×¦×¢ ×¡ï¿½~ï¿½.ï¿½"× ï¿½~ï¿½T×</b>\n  ï¿½Y'ï¿½ 50% ï¿½"× ï¿½-ï¿½" ï¿½?" ×§ï¿½.ï¿½": <code>STUDENT50</code>\nï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½"
        )
        kb = {"inline_keyboard": [
            [{"text": "ï¿½Y'Z ×¨ï¿½>ï¿½.×© ï¿½-ï¿½'ï¿½Tï¿½oï¿½" ï¿½zï¿½o×ï¿½"", "callback_data": "vip_elite"}],
            [{"text": "ï¿½Y>ï¿½ï¸ ï¿½-ï¿½'ï¿½Tï¿½o×ª ×ï¿½'ï¿½~ï¿½-ï¿½"", "callback_data": "vip_basic"}],
            [{"text": "ï¿½Y'ï¿½ ï¿½"ï¿½-ï¿½zï¿½Y ï¿½-ï¿½'×¨ï¿½T×", "callback_data": "menu_referral"}],
            [{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½" ï¿½o×ª×¤×¨ï¿½Tï¿½~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_buy_slh_inline(self, chat_id, message_id=None):
        text = (
            f"ï¿½Yï¿½T <b>×¨ï¿½>ï¿½T×©×ª SLH Coin</b>\n\n"
            f"ï¿½Y'ï¿½ <b>ï¿½zï¿½-ï¿½T×¨:</b> 1 SLH = {SLH_PRICE_ILS}ï¿½,ï¿½\n"
            f"ï¿½Y"ï¿½ ï¿½zï¿½T× ï¿½Tï¿½zï¿½.×: 0.00004 SLH (0.018ï¿½,ï¿½)\n\nï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\nï¿½Y"S <b>ï¿½zï¿½"×¨ï¿½'ï¿½.×ª ï¿½zï¿½-ï¿½T×¨:</b>\n\n"
        )
        for tier in SLH_BUY_TIERS:
            text += f"  ï¿½Yï¿½T {tier['amount']} SLH = {tier['price']}ï¿½,ï¿½\n"
        text += (
            f"\nï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\n"
            f"ï¿½Y'ï¿½ <b>××¨× ×§ TON:</b>\n<code>{TON_WALLET}</code>\n\n"
            f"ï¿½Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            "ï¿½Y"ï¿½ ×©ï¿½oï¿½- ×¦ï¿½Tï¿½oï¿½.× ï¿½z×¡ï¿½s ×ï¿½. Transaction Hash\n×ï¿½. ×¦ï¿½.×¨ ×§×©×¨ ×¢× @Osif83"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.buy_slh_keyboard())
        else:
            self.send(chat_id, text, self.buy_slh_keyboard())

    def handle_buy_slh_select(self, chat_id, amount_str, callback_id, message_id):
        if amount_str == "custom":
            text = (
                f"ï¿½oï¿½ï¸ <b>×¡ï¿½>ï¿½.× ï¿½zï¿½.×ª×× ×ï¿½T×©ï¿½T×ª</b>\n\n"
                f"ï¿½Y'ï¿½ ï¿½zï¿½-ï¿½T×¨: 1 SLH = {SLH_PRICE_ILS}ï¿½,ï¿½\n"
                f"ï¿½Y"ï¿½ ï¿½zï¿½T× ï¿½Tï¿½zï¿½.×: 0.00004 SLH (0.018ï¿½,ï¿½)\n\n"
                "×©ï¿½oï¿½- ××ª ï¿½"×¡ï¿½>ï¿½.× ×©×ª×¨×¦ï¿½" ï¿½o×¨ï¿½>ï¿½.×© (ï¿½'SLH).\nï¿½oï¿½"ï¿½.ï¿½'ï¿½zï¿½": <code>0.005</code>\n\n"
                f"ï¿½Y'ï¿½ <b>××¨× ×§ TON:</b>\n<code>{TON_WALLET}</code>\n\n"
                f"ï¿½Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n×ï¿½. ×¦ï¿½.×¨ ×§×©×¨ ×¢× @Osif83"
            )
            self.edit_message(chat_id, message_id, text, self.back_keyboard())
            self.answer_callback(callback_id)
            return
        try:
            amount = float(amount_str)
        except ValueError:
            self.answer_callback(callback_id, "ï¿½O ×©ï¿½'ï¿½T×ï¿½"")
            return
        price = round(amount * SLH_PRICE_ILS, 3)
        text = (
            f"ï¿½Yï¿½T <b>×¨ï¿½>ï¿½T×©×ª {amount} SLH</b>\n\nï¿½Y'ï¿½ <b>ï¿½zï¿½-ï¿½T×¨:</b> {price}ï¿½,ï¿½\n\nï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\n"
            f"ï¿½Y'ï¿½ <b>×©ï¿½oï¿½- {price}ï¿½,ï¿½ ï¿½o××¨× ×§ TON:</b>\n\n<code>{TON_WALLET}</code>\n\n"
            f"ï¿½Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            f"ï¿½Y"ï¿½ ×©ï¿½oï¿½- ×¦ï¿½Tï¿½oï¿½.× ï¿½z×¡ï¿½s ×ï¿½. Transaction Hash\n×ï¿½. ×¦ï¿½.×¨ ×§×©×¨ ×¢× @Osif83\n\nï¿½o. ×ª×§ï¿½'ï¿½o {amount} SLH ×ªï¿½.ï¿½s 24 ×©×¢ï¿½.×ª"
        )
        kb = {"inline_keyboard": [
            [{"text": "ï¿½Y'ï¿½ ï¿½"×¢×ª×§ ï¿½>×ªï¿½.ï¿½'×ª ××¨× ×§", "callback_data": "copy_wallet_slh"}],
            [{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½" ï¿½o×¨ï¿½>ï¿½T×©ï¿½"", "callback_data": "menu_buy_slh"}],
        ]}
        self.edit_message(chat_id, message_id, text, kb)
        self.answer_callback(callback_id)

    def handle_help_inline(self, chat_id, message_id=None):
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            "ï¿½" <b>SLH HUB ï¿½?" ×¢ï¿½-×¨ï¿½"</b>\n\n"
            "<b>×¤×§ï¿½.ï¿½"ï¿½.×ª:</b>\n"
            "/start ï¿½?" ×ª×¤×¨ï¿½Tï¿½~ ×¨××©ï¿½T\n/earn ï¿½?" ï¿½z×©ï¿½Tï¿½zï¿½.×ª ï¿½.ï¿½"×¨ï¿½.ï¿½.ï¿½-ï¿½"\n/swap ï¿½?" ï¿½"ï¿½z×¨×ª ï¿½zï¿½~ï¿½'×¢ï¿½.×ª\n/vip ï¿½?" ï¿½z× ï¿½.ï¿½T ×¤×¨ï¿½Tï¿½zï¿½Tï¿½.×\n"
            "/airdrop ï¿½?" ×¨ï¿½>ï¿½T×©×ª ï¿½~ï¿½.×§× ï¿½T×\n/buyslh ï¿½?" ï¿½Yï¿½T ×¨ï¿½>ï¿½T×©×ª SLH Coin\n/referral ï¿½?" ×§ï¿½T×©ï¿½.×¨ ï¿½"×¤× ï¿½Tï¿½"\n"
            "/deals ï¿½?" ï¿½zï¿½'×¦×¢ï¿½T×\n/portfolio ï¿½?" ï¿½"×ªï¿½T×§ ×©ï¿½oï¿½T\n/help ï¿½?" ×¢ï¿½-×¨ï¿½"\n\n"
            "<b>×ªï¿½zï¿½Tï¿½>ï¿½":</b> @Osif83\n<b>××ª×¨:</b> slh-nft.com\n\n"
            f"ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½ï¿½"ï¿½\nï¿½Y'ï¿½ <b>×©×ª×£ ï¿½.ï¿½"×¨ï¿½.ï¿½.ï¿½Tï¿½- 15% ï¿½'× ×§ï¿½.ï¿½"ï¿½.×ª SLH!</b>\nï¿½Y"- <code>{ref_link}</code>"
        )
        kb = {"inline_keyboard": [[{"text": "ï¿½Y"T ï¿½-ï¿½-×¨ï¿½" ï¿½o×ª×¤×¨ï¿½Tï¿½~", "callback_data": "menu_main"}]]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    # ï¿½"?ï¿½"? Admin ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
    def handle_admin(self, chat_id):
        if str(chat_id) != ADMIN_ID:
            return
        total_users = len(_user_data)
        total_vip = sum(1 for u in _user_data.values() if u.get("vip"))
        total_points = sum(u.get("hub_points", 0) for u in _user_data.values())
        total_refs = sum(u["referral_count"] for u in _user_data.values())
        text = (
            f"ï¿½Y>ï¿½ <b>ADMIN PANEL</b>\n\n"
            f"ï¿½Y'ï¿½ ï¿½z×©×ªï¿½z×©ï¿½T×: <b>{total_users}</b>\nï¿½Y'' VIP: <b>{total_vip}</b>\n"
            f"ï¿½Y'ï¿½ × ×§ï¿½.ï¿½"ï¿½.×ª ×©ï¿½-ï¿½.ï¿½o×§ï¿½.: <b>{total_points}</b>\nï¿½Y'ï¿½ ï¿½"×¤× ï¿½Tï¿½.×ª: <b>{total_refs}</b>\n\n"
            f"<b>×¤×§ï¿½.ï¿½"ï¿½.×ª:</b>\n/stats ï¿½?" ×¡ï¿½~ï¿½~ï¿½T×¡ï¿½~ï¿½T×§ï¿½.×ª\n/broadcast TEXT ï¿½?" ×©ï¿½oï¿½- ï¿½"ï¿½.ï¿½"×¢ï¿½" ï¿½oï¿½>ï¿½.ï¿½o×\n"
            f"/approve USER_ID PLAN ï¿½?" ××©×¨ VIP\n/admin ï¿½?" ×¤×× ï¿½o ï¿½-ï¿½""
        )
        self.send(chat_id, text)

    def handle_broadcast(self, chat_id, text):
        if str(chat_id) != ADMIN_ID:
            return
        sent = 0
        for uid in _user_data:
            if self.send(uid, f"ï¿½Y"ï¿½ <b>ï¿½"ï¿½.ï¿½"×¢ï¿½" ï¿½zï¿½"ï¿½z×¢×¨ï¿½>×ª:</b>\n\n{text}"):
                sent += 1
        self.send(chat_id, f"ï¿½o. × ×©ï¿½oï¿½- ï¿½o-{sent} ï¿½z×©×ªï¿½z×©ï¿½T×")

    def handle_approve(self, chat_id, args):
        if str(chat_id) != ADMIN_ID:
            return
        parts = args.split()
        if len(parts) < 2:
            self.send(chat_id, "×©ï¿½Tï¿½zï¿½.×©: /approve USER_ID PLAN\nï¿½oï¿½"ï¿½.ï¿½'ï¿½zï¿½": /approve 123456 pro")
            return
        try:
            uid = int(parts[0])
            plan = parts[1]
            if plan in VIP_PLANS:
                user = _get_user(uid)
                user["vip"] = plan
                self.send(chat_id, f"ï¿½o. ×ï¿½.×©×¨ VIP {VIP_PLANS[plan]['name']} ï¿½oï¿½z×©×ªï¿½z×© {uid}")
                self.send(uid, f"ï¿½YZ? <b>VIP ï¿½"ï¿½.×¤×¢ï¿½o!</b>\n\n×©ï¿½"×¨ï¿½'×ª ï¿½o-{VIP_PLANS[plan]['name']}! ï¿½Y''")
            else:
                self.send(chat_id, f"ï¿½O ×ªï¿½.ï¿½>× ï¿½T×ª ï¿½o× ×§ï¿½Tï¿½Tï¿½z×ª. ××¤×©×¨ï¿½.ï¿½Tï¿½.×ª: {', '.join(VIP_PLANS.keys())}")
        except:
            self.send(chat_id, "ï¿½O ×©ï¿½'ï¿½T×ï¿½". ×©ï¿½Tï¿½zï¿½.×©: /approve USER_ID PLAN")

    # ï¿½"?ï¿½"? Callback handler ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
    def handle_callback(self, callback):
        data = callback.get("data", "")
        chat_id = callback["message"]["chat"]["id"]
        message_id = callback["message"]["message_id"]
        callback_id = callback["id"]
        first_name = callback["from"].get("first_name", "")

        # ï¿½"?ï¿½"? P2P callbacks (delegate to handle_p2p_callback) ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
        if (data.startswith("p2p_") or data.startswith("send_tok_") or
                data.startswith("sell_tok_") or data.startswith("pay_")):
            self.handle_p2p_callback(chat_id, data, callback_id, message_id)
            return

        if data == "menu_main":
            user = _get_user(chat_id)
            vip_badge = "ï¿½Y'' VIP" if user["vip"] else "ï¿½Y?" Free"
            self.edit_message(chat_id, message_id,
                f"ï¿½Ys? <b>SLH HUB SYSTEM</b>\n\n"
                f"ï¿½Y'ï¿½ <b>{first_name}</b> | {vip_badge}\n"
                f"ï¿½Y'ï¿½ ï¿½T×ª×¨ï¿½": <b>{user['hub_points']}</b> × ×§ï¿½.ï¿½"ï¿½.×ª\n"
                f"ï¿½Y'Z SLH: <b>{user['slh_balance']:.2f}</b>\n"
                f"ï¿½Y'ï¿½ ï¿½"×¤× ï¿½Tï¿½.×ª: <b>{user['referral_count']}</b>\n\nï¿½Y'? ï¿½'ï¿½-×¨ ×¤×¢ï¿½.ï¿½oï¿½":",
                self.hub_inline_keyboard()
            )
            self.answer_callback(callback_id)
        elif data == "menu_earn":
            self.handle_earn(chat_id, message_id)
            self.answer_callback(callback_id)
        elif data == "menu_swap":
            self.handle_swap_inline(chat_id, message_id)
            self.answer_callback(callback_id)
        elif data == "menu_vip":
            self.handle_vip(chat_id, message_id)
            self.answer_callback(callback_id)
        elif data == "menu_airdrop":
            self.handle_airdrop(chat_id, message_id)
            self.answer_callback(callback_id)
        elif data == "menu_referral":
            self.handle_referral(chat_id, message_id)
            self.answer_callback(callback_id)
        elif data == "menu_portfolio":
            self.handle_portfolio(chat_id, message_id)
            self.answer_callback(callback_id)
        elif data == "menu_deals":
            self.handle_deals_inline(chat_id, message_id)
            self.answer_callback(callback_id)
        elif data == "menu_buy_slh":
            self.handle_buy_slh_inline(chat_id, message_id)
            self.answer_callback(callback_id)
        elif data == "menu_help":
            self.handle_help_inline(chat_id, message_id)
            self.answer_callback(callback_id)
        elif data.startswith("buy_slh_"):
            self.handle_buy_slh_select(chat_id, data[8:], callback_id, message_id)
        elif data == "copy_wallet_slh":
            self.answer_callback(callback_id, f"ï¿½Y'ï¿½ {TON_WALLET}", True)
        elif data.startswith("task_"):
            self.handle_task(chat_id, data[5:], callback_id, message_id)
        elif data.startswith("vip_"):
            self.handle_vip_select(chat_id, data[4:], callback_id, message_id)
        elif data == "airdrop_pay":
            self.send(chat_id,
                f"ï¿½Y'ï¿½ <b>×©ï¿½oï¿½- ×ª×©ï¿½oï¿½.× ï¿½o××¨× ×§ TON:</b>\n\n<code>{TON_WALLET}</code>\n\n"
                f"ï¿½Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
                "ï¿½Y"ï¿½ ×ï¿½-×¨ï¿½T ï¿½"×ª×©ï¿½oï¿½.×, ×©ï¿½oï¿½- ï¿½>×ï¿½Y:\nï¿½?ï¿½ ×¦ï¿½Tï¿½oï¿½.× ï¿½z×¡ï¿½s, ×ï¿½.\nï¿½?ï¿½ Transaction Hash",
                self.back_keyboard())
            self.answer_callback(callback_id)
        elif data == "airdrop_status":
            user = _get_user(chat_id)
            self.answer_callback(callback_id, f"ï¿½Y'ï¿½ ï¿½T×ª×¨ï¿½": {user['hub_points']} × ×§ï¿½.ï¿½"ï¿½.×ª | VIP: {'ï¿½>ï¿½Y' if user['vip'] else 'ï¿½o×'}", True)
        elif data == "copy_ref":
            self.answer_callback(callback_id, f"ï¿½Y"- https://t.me/SLH_AIR_bot?start=ref_{chat_id}", True)
        elif data.startswith("copy_wallet_"):
            self.answer_callback(callback_id, f"ï¿½Y'ï¿½ {TON_WALLET}", True)
        elif data.startswith("invest_"):
            try:
                idx = int(data[7:])
                plan = INVESTMENT_PLANS[idx]
                self.handle_deposit(chat_id, f"{idx+1} {plan['min_ton']}")
            except:
                pass
            self.answer_callback(callback_id)
        elif data.startswith("game_"):
            game = data[5:]
            if game == "convert":
                self.handle_game_convert(chat_id, callback_id, message_id)
            else:
                self.handle_game(chat_id, game, callback_id, message_id)
        elif data == "wallet_deposit":
            self.handle_deposit_address(chat_id)
            self.answer_callback(callback_id)
        elif data == "wallet_send":
            self.send(chat_id,
                "ï¿½Y"ï¿½ <b>×©ï¿½oï¿½Tï¿½-×ª ï¿½zï¿½~ï¿½'×¢ï¿½.×ª</b>\n\n"
                "ï¿½Y'Z SLH: <code>/send_slh USER_ID AMOUNT</code>\n"
                "ï¿½Y'ï¿½ TON: <code>/send_ton USER_ID AMOUNT</code>\n"
                "ï¿½YYï¿½ BNB: <code>/send_bnb USER_ID AMOUNT</code>\n"
                "ï¿½YZï¿½ ZVK: <code>/send_zvk USER_ID AMOUNT</code>\n\n"
                "ï¿½Y'ï¿½ ×§ï¿½'ï¿½o ××ª ï¿½"-USER_ID ×©ï¿½o ï¿½"× ï¿½z×¢ï¿½Y: ï¿½'×§×© ï¿½zï¿½z× ï¿½. /myid",
                self.wallet_inline_keyboard())
            self.answer_callback(callback_id)
        elif data == "wallet_history":
            self.handle_tx_history(chat_id)
            self.answer_callback(callback_id)
        elif data == "wallet_refresh":
            self.handle_wallet(chat_id, message_id)
            self.answer_callback(callback_id, "ï¿½Y"" ï¿½z×¨×¢× ï¿½Y...")
        elif data.startswith("admin_approve_"):
            if str(chat_id) == ADMIN_ID:
                parts = data.split("_")
                uid = int(parts[2])
                dep_id = int(parts[3])
                user = _get_user(uid)
                for d in user["deposits"]:
                    if d["id"] == dep_id:
                        d["status"] = "active"
                        user["ton_locked"] += d["amount"]
                        break
                self.send(uid, f"ï¿½o. ï¿½"×¤×§ï¿½"ï¿½" #{dep_id} ×ï¿½.×©×¨ï¿½"! ï¿½"×¤×§ï¿½"ï¿½.ï¿½Y ×¤×¢ï¿½Tï¿½o.")
                self.answer_callback(callback_id, "ï¿½o. ×ï¿½.×©×¨!", True)
        elif data.startswith("admin_reject_"):
            if str(chat_id) == ADMIN_ID:
                parts = data.split("_")
                uid = int(parts[2])
                dep_id = int(parts[3])
                user = _get_user(uid)
                for d in user["deposits"]:
                    if d["id"] == dep_id:
                        d["status"] = "rejected"
                        break
                self.send(uid, f"ï¿½O ï¿½"×¤×§ï¿½"ï¿½" #{dep_id} × ï¿½"ï¿½-×ªï¿½".\n× ×¡ï¿½" ×©ï¿½.ï¿½' ×ï¿½. ×¤× ï¿½" ï¿½o×ªï¿½zï¿½Tï¿½>ï¿½".")
                self.answer_callback(callback_id, "ï¿½O × ï¿½"ï¿½-ï¿½"", True)
        else:
            self.answer_callback(callback_id)

    # ï¿½"?ï¿½"? Text message handler ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
    # ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½
    # P2P TRADING MODULE
    # ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½
    API_BASE = "https://slh-api-production.up.railway.app"

    def _p2p_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "ï¿½Y"ï¿½ ×©ï¿½oï¿½- ï¿½~ï¿½.×§ï¿½Y", "callback_data": "p2p_send"},
             {"text": "ï¿½Y>' ï¿½oï¿½.ï¿½- ï¿½zï¿½>ï¿½T×¨ï¿½.×ª", "callback_data": "p2p_browse"}],
            [{"text": "ï¿½Y'ï¿½ ×¤×¨×¡× ï¿½zï¿½>ï¿½T×¨ï¿½"", "callback_data": "p2p_sell"},
             {"text": "ï¿½Y"< ï¿½"ï¿½"ï¿½-ï¿½z× ï¿½.×ª ×©ï¿½oï¿½T", "callback_data": "p2p_myorders"}],
            [{"text": "ï¿½Y"T ×ª×¤×¨ï¿½Tï¿½~ ×¨××©ï¿½T", "callback_data": "menu_main"}],
        ]}

    def _token_keyboard(self, prefix):
        return {"inline_keyboard": [
            [{"text": "ï¿½Y'Z SLH", "callback_data": f"{prefix}_SLH"},
             {"text": "ï¿½YZï¿½ ZVK", "callback_data": f"{prefix}_ZVK"},
             {"text": "ï¿½Y'ï¿½ MNH", "callback_data": f"{prefix}_MNH"}],
            [{"text": "ï¿½O ï¿½'ï¿½Tï¿½~ï¿½.ï¿½o", "callback_data": "p2p_cancel"}],
        ]}

    def _payment_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "ï¿½Y"ï¿½ Bit", "callback_data": "pay_Bit"},
             {"text": "ï¿½Y"ï¿½ PayBox", "callback_data": "pay_PayBox"}],
            [{"text": "ï¿½Yï¿½ï¿½ Bank", "callback_data": "pay_Bank"},
             {"text": "ï¿½Y'ï¿½ MNH", "callback_data": "pay_MNH"}],
            [{"text": "ï¿½O ï¿½'ï¿½Tï¿½~ï¿½.ï¿½o", "callback_data": "p2p_cancel"}],
        ]}

    def handle_p2p_menu(self, chat_id):
        self._refresh_balances(chat_id)
        user = _get_user(chat_id)
        self.send(chat_id,
            f"ï¿½Y"" <b>P2P ï¿½z×¡ï¿½-×¨ ï¿½?" SLH Spark</b>\n"
            f"ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½\n\n"
            f"ï¿½Y'Z SLH: <b>{user['slh_balance']:,.4f}</b>\n"
            f"ï¿½YZï¿½ ZVK: <b>{user['zvk_balance']}</b>\n"
            f"ï¿½Y'ï¿½ MNH: <b>{user.get('mnh_balance', 0):.2f}</b>\n\n"
            f"ï¿½Y"ï¿½ <b>×©ï¿½oï¿½- ï¿½~ï¿½.×§ï¿½Y</b> ï¿½?" ï¿½"×¢ï¿½'×¨ï¿½" ï¿½T×©ï¿½T×¨ï¿½" ï¿½oï¿½z×©×ªï¿½z×©\n"
            f"ï¿½Y>' <b>ï¿½oï¿½.ï¿½- ï¿½zï¿½>ï¿½T×¨ï¿½.×ª</b> ï¿½?" ×§× ï¿½" ï¿½zï¿½"×§ï¿½"ï¿½Tï¿½oï¿½"\n"
            f"ï¿½Y'ï¿½ <b>×¤×¨×¡× ï¿½zï¿½>ï¿½T×¨ï¿½"</b> ï¿½?" ï¿½zï¿½>ï¿½.×¨ ××ª ï¿½"ï¿½~ï¿½.×§× ï¿½T× ×©ï¿½oï¿½s\n"
            f"ï¿½Y"< <b>ï¿½"ï¿½"ï¿½-ï¿½z× ï¿½.×ª ×©ï¿½oï¿½T</b> ï¿½?" × ï¿½Tï¿½"ï¿½.ï¿½o ï¿½"ï¿½-ï¿½z× ï¿½.×ª ×¤×ªï¿½.ï¿½-ï¿½.×ª",
            self._p2p_keyboard())

    # ï¿½"?ï¿½"? SEND FLOW ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
    def p2p_start_send(self, chat_id):
        self._pending_p2p[chat_id] = {"flow": "send", "step": "choose_token", "data": {}}
        self.send(chat_id, "ï¿½Y"ï¿½ <b>×©ï¿½oï¿½- ï¿½~ï¿½.×§ï¿½Y</b>\n\nï¿½'ï¿½-×¨ ×ï¿½Tï¿½-ï¿½" ï¿½~ï¿½.×§ï¿½Y ï¿½o×©ï¿½oï¿½.ï¿½-:", self._token_keyboard("send_tok"))

    def p2p_send_step(self, chat_id, text):
        state = self._pending_p2p.get(chat_id, {})
        if not state or state.get("flow") != "send":
            return False
        step = state["step"]
        data = state["data"]

        if step == "enter_recipient":
            try:
                to_user = int(text.strip())
                if to_user == chat_id:
                    self.send(chat_id, "ï¿½O ×ï¿½T ××¤×©×¨ ï¿½o×©ï¿½oï¿½.ï¿½- ï¿½o×¢×¦ï¿½zï¿½s.")
                    return True
                data["to_user"] = to_user
                state["step"] = "enter_amount"
                self.send(chat_id,
                    f"ï¿½Y'ï¿½ <b>ï¿½>ï¿½zï¿½" {data['token']} ï¿½o×©ï¿½oï¿½.ï¿½-?</b>\n"
                    f"ï¿½"ï¿½T×ª×¨ï¿½" ×©ï¿½oï¿½s: {self._get_balance_for(chat_id, data['token']):.4f}\n\n"
                    f"ï¿½"ï¿½>× ×¡ ×¡ï¿½>ï¿½.× (ï¿½z×¡×¤×¨ ï¿½'ï¿½oï¿½'ï¿½"):")
            except ValueError:
                self.send(chat_id, "ï¿½O User ID ï¿½o× ×ª×§ï¿½Tï¿½Y. ï¿½"ï¿½>× ×¡ ï¿½z×¡×¤×¨ ï¿½'ï¿½oï¿½'ï¿½" (ï¿½oï¿½"ï¿½.ï¿½'ï¿½zï¿½": 224223270)")
            return True

        if step == "enter_amount":
            try:
                amount = float(text.strip())
                if amount <= 0:
                    raise ValueError
                bal = self._get_balance_for(chat_id, data["token"])
                if amount > bal:
                    self.send(chat_id, f"ï¿½O ï¿½T×ª×¨ï¿½" ï¿½o× ï¿½z×¡×¤ï¿½T×§ï¿½". ï¿½T×© ï¿½oï¿½s {bal:.4f} {data['token']}")
                    return True
                data["amount"] = amount
                state["step"] = "confirm"
                self.send(chat_id,
                    f"ï¿½o. <b>×ï¿½T×©ï¿½.×¨ ï¿½"×¢ï¿½'×¨ï¿½"</b>\n\n"
                    f"ï¿½Y"ï¿½ ×©ï¿½.ï¿½oï¿½-: <b>{amount} {data['token']}</b>\n"
                    f"ï¿½Y'ï¿½ ï¿½oï¿½z×©×ªï¿½z×© ID: <code>{data['to_user']}</code>\n\n"
                    f"×©ï¿½oï¿½- <b>ï¿½>ï¿½Y</b> ï¿½o×ï¿½T×©ï¿½.×¨ ×ï¿½. <b>ï¿½o×</b> ï¿½oï¿½'ï¿½Tï¿½~ï¿½.ï¿½o:")
            except ValueError:
                self.send(chat_id, "ï¿½O ×¡ï¿½>ï¿½.× ï¿½o× ×ª×§ï¿½Tï¿½Y. ï¿½"ï¿½>× ×¡ ï¿½z×¡×¤×¨ (ï¿½oï¿½"ï¿½.ï¿½'ï¿½zï¿½": 10.5)")
            return True

        if step == "confirm":
            if text.strip().lower() in ("ï¿½>ï¿½Y", "yes", "×ï¿½T×©ï¿½.×¨", "ï¿½o."):
                self._p2p_execute_send(chat_id, data)
            else:
                del self._pending_p2p[chat_id]
                self.send(chat_id, "ï¿½O ï¿½"×¢ï¿½'×¨ï¿½" ï¿½'ï¿½.ï¿½~ï¿½oï¿½".", self.main_reply_keyboard())
            return True

        return False

    def _get_balance_for(self, chat_id, token):
        user = _get_user(chat_id)
        return {"SLH": user.get("slh_balance", 0),
                "ZVK": float(user.get("zvk_balance", 0)),
                "MNH": user.get("mnh_balance", 0)}.get(token, 0)

    def _p2p_execute_send(self, chat_id, data):
        try:
            bot_secret = os.getenv("BOT_SYNC_SECRET", "slh-bot-sync-2026-default-please-override")
            resp = self.session.post(
                f"{self.API_BASE}/api/p2p/bot-transfer",
                json={"from_user_id": chat_id, "to_user_id": data["to_user"],
                      "token": data["token"], "amount": data["amount"], "memo": "bot-send"},
                headers={"x-bot-secret": bot_secret},
                timeout=10
            )
            result = resp.json()
            if resp.status_code == 200 and result.get("ok"):
                # Update local cache
                user = _get_user(chat_id)
                if data["token"] == "SLH":
                    user["slh_balance"] = max(0, user["slh_balance"] - data["amount"])
                elif data["token"] == "ZVK":
                    user["zvk_balance"] = max(0, int(user["zvk_balance"]) - int(data["amount"]))
                elif data["token"] == "MNH":
                    user["mnh_balance"] = max(0, user.get("mnh_balance", 0) - data["amount"])

                self.send(chat_id,
                    f"ï¿½o. <b>× ×©ï¿½oï¿½- ï¿½'ï¿½"×¦ï¿½oï¿½-ï¿½"!</b>\n\n"
                    f"ï¿½Y'ï¿½ <b>{data['amount']} {data['token']}</b> ï¿½?' ï¿½z×©×ªï¿½z×© <code>{data['to_user']}</code>\n"
                    f"ï¿½Yï¿½ï¿½ TX: #{result.get('transfer_id', 'ï¿½?"')}\n\n"
                    f"ï¿½Y'ï¿½ /wallet ï¿½o×¦×¤ï¿½Tï¿½Tï¿½" ï¿½'ï¿½T×ª×¨ï¿½"", self.main_reply_keyboard())
                # Notify receiver
                self.send(data["to_user"],
                    f"ï¿½Y'ï¿½ <b>×§ï¿½Tï¿½'ï¿½o×ª {data['amount']} {data['token']}!</b>\n\n"
                    f"ï¿½Y'ï¿½ ï¿½z: ï¿½z×©×ªï¿½z×© {chat_id}\n"
                    f"ï¿½Y'ï¿½ /wallet ï¿½o×¦×¤ï¿½Tï¿½Tï¿½" ï¿½'ï¿½T×ª×¨ï¿½"")
            else:
                err = result.get("detail", result.get("error", "×©ï¿½'ï¿½T×ï¿½" ï¿½o× ï¿½Tï¿½"ï¿½.×¢ï¿½""))
                self.send(chat_id, f"ï¿½O {err}", self.main_reply_keyboard())
        except Exception as e:
            logger.error(f"P2P send error: {e}")
            self.send(chat_id, "ï¿½O ×©ï¿½'ï¿½T×ï¿½" ï¿½'×©ï¿½oï¿½Tï¿½-ï¿½". × ×¡ï¿½" ×©ï¿½.ï¿½'.", self.main_reply_keyboard())
        finally:
            self._pending_p2p.pop(chat_id, None)

    # ï¿½"?ï¿½"? SELL FLOW ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
    def p2p_start_sell(self, chat_id):
        self._refresh_balances(chat_id)
        user = _get_user(chat_id)
        if user["slh_balance"] <= 0 and user["zvk_balance"] <= 0 and user.get("mnh_balance", 0) <= 0:
            self.send(chat_id, "ï¿½O ×ï¿½Tï¿½Y ï¿½oï¿½s ï¿½~ï¿½.×§× ï¿½T× ï¿½oï¿½zï¿½>ï¿½T×¨ï¿½".", self.main_reply_keyboard())
            return
        self._pending_p2p[chat_id] = {"flow": "sell", "step": "choose_token", "data": {}}
        self.send(chat_id, "ï¿½Y'ï¿½ <b>×¤×¨×¡× ï¿½zï¿½>ï¿½T×¨ï¿½"</b>\n\nï¿½'ï¿½-×¨ ×ï¿½Tï¿½-ï¿½" ï¿½~ï¿½.×§ï¿½Y ï¿½oï¿½zï¿½>ï¿½.×¨:", self._token_keyboard("sell_tok"))

    def p2p_sell_step(self, chat_id, text):
        state = self._pending_p2p.get(chat_id, {})
        if not state or state.get("flow") != "sell":
            return False
        step = state["step"]
        data = state["data"]

        if step == "enter_amount":
            try:
                amount = float(text.strip())
                if amount <= 0:
                    raise ValueError
                bal = self._get_balance_for(chat_id, data["token"])
                if amount > bal:
                    self.send(chat_id, f"ï¿½O ï¿½T×ª×¨ï¿½" ï¿½o× ï¿½z×¡×¤ï¿½T×§ï¿½". ï¿½T×© ï¿½oï¿½s {bal:.4f} {data['token']}")
                    return True
                data["amount"] = amount
                state["step"] = "enter_price"
                self.send(chat_id,
                    f"ï¿½Y'ï¿½ <b>ï¿½zï¿½-ï¿½T×¨ ï¿½oï¿½>ï¿½o {data['token']} (ï¿½'×©×§ï¿½oï¿½T× ï¿½,ï¿½)</b>\n\n"
                    f"ï¿½oï¿½"ï¿½.ï¿½'ï¿½zï¿½": ×× SLH = 444ï¿½,ï¿½, ï¿½"ï¿½>× ×¡ <b>444</b>\n"
                    f"ï¿½"ï¿½>× ×¡ ï¿½zï¿½-ï¿½T×¨:")
            except ValueError:
                self.send(chat_id, "ï¿½O ×¡ï¿½>ï¿½.× ï¿½o× ×ª×§ï¿½Tï¿½Y.")
            return True

        if step == "enter_price":
            try:
                price = float(text.strip())
                if price <= 0:
                    raise ValueError
                data["price"] = price
                state["step"] = "choose_payment"
                total = data["amount"] * price
                self.send(chat_id,
                    f"ï¿½Y'ï¿½ <b>×©ï¿½Tï¿½~×ª ×ª×©ï¿½oï¿½.× ï¿½zï¿½.×¢ï¿½"×¤×ª</b>\n\n"
                    f"×ª×§ï¿½'ï¿½o: <b>{total:.2f} ï¿½,ï¿½</b> ×¢ï¿½'ï¿½.×¨ {data['amount']} {data['token']}\n\n"
                    f"ï¿½'ï¿½-×¨ ×ï¿½Tï¿½s ï¿½o×§ï¿½'ï¿½o ×ª×©ï¿½oï¿½.×:", self._payment_keyboard())
            except ValueError:
                self.send(chat_id, "ï¿½O ï¿½zï¿½-ï¿½T×¨ ï¿½o× ×ª×§ï¿½Tï¿½Y.")
            return True

        if step == "confirm":
            if text.strip().lower() in ("ï¿½>ï¿½Y", "yes", "×ï¿½T×©ï¿½.×¨", "ï¿½o."):
                self._p2p_execute_sell(chat_id, data)
            else:
                del self._pending_p2p[chat_id]
                self.send(chat_id, "ï¿½O ï¿½zï¿½>ï¿½T×¨ï¿½" ï¿½'ï¿½.ï¿½~ï¿½oï¿½".", self.main_reply_keyboard())
            return True

        return False

    def _p2p_execute_sell(self, chat_id, data):
        try:
            resp = self.session.post(
                f"{self.API_BASE}/api/p2p/create-order",
                json={"seller_id": chat_id, "token": data["token"], "amount": data["amount"],
                      "price_per_unit": data["price"], "currency": "ILS",
                      "payment_method": data["payment"]},
                timeout=10
            )
            result = resp.json()
            if resp.status_code == 200 and result.get("ok"):
                order = result["order"]
                self.send(chat_id,
                    f"ï¿½o. <b>ï¿½"ï¿½-ï¿½z× ×ª ï¿½zï¿½>ï¿½T×¨ï¿½" × ï¿½.×¦×¨ï¿½"!</b>\n\n"
                    f"ï¿½Y?" ï¿½"ï¿½-ï¿½z× ï¿½": <b>#{order['id']}</b>\n"
                    f"ï¿½Y'ï¿½ ï¿½zï¿½.ï¿½>×¨: <b>{order['amount']} {order['token']}</b>\n"
                    f"ï¿½Y'ï¿½ ï¿½zï¿½-ï¿½T×¨: <b>{order['price_per_unit']} ï¿½,ï¿½</b> ï¿½oï¿½Tï¿½-ï¿½Tï¿½"ï¿½"\n"
                    f"ï¿½Y"S ×¡ï¿½"\"ï¿½>: <b>{order['amount'] * order['price_per_unit']:.2f} ï¿½,ï¿½</b>\n"
                    f"ï¿½Y'ï¿½ ×ª×©ï¿½oï¿½.×: <b>{order['payment_method']}</b>\n\n"
                    f"ï¿½Y"' ï¿½"ï¿½~ï¿½.×§× ï¿½T× × × ×¢ï¿½oï¿½. ï¿½'-escrow ï¿½?" ï¿½Tï¿½.×¢ï¿½'×¨ï¿½. ï¿½o×§ï¿½.× ï¿½" ×ï¿½.ï¿½~ï¿½.ï¿½zï¿½~ï¿½T×ª.\n"
                    f"ï¿½oï¿½'ï¿½Tï¿½~ï¿½.ï¿½o: ï¿½Y"< ï¿½"ï¿½"ï¿½-ï¿½z× ï¿½.×ª ×©ï¿½oï¿½T", self.main_reply_keyboard())
                # Refresh balance (tokens were escrowed)
                self._refresh_balances(chat_id)
            else:
                err = result.get("detail", "×©ï¿½'ï¿½T×ï¿½" ï¿½o× ï¿½Tï¿½"ï¿½.×¢ï¿½"")
                self.send(chat_id, f"ï¿½O {err}", self.main_reply_keyboard())
        except Exception as e:
            logger.error(f"P2P sell error: {e}")
            self.send(chat_id, "ï¿½O ×©ï¿½'ï¿½T×ï¿½" ï¿½'ï¿½T×¦ï¿½T×¨×ª ï¿½"ï¿½-ï¿½z× ï¿½".", self.main_reply_keyboard())
        finally:
            self._pending_p2p.pop(chat_id, None)

    # ï¿½"?ï¿½"? BROWSE + BUY ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
    def p2p_browse(self, chat_id, token_filter=None):
        try:
            params = {"status": "active", "limit": 10}
            if token_filter:
                params["token"] = token_filter
            resp = self.session.get(f"{self.API_BASE}/api/p2p/orders", params=params, timeout=8)
            data = resp.json()
            orders = data.get("orders", [])
            if not orders:
                self.send(chat_id,
                    "ï¿½Y>' <b>ï¿½oï¿½.ï¿½- ï¿½zï¿½>ï¿½T×¨ï¿½.×ª</b>\n\n×ï¿½Tï¿½Y ï¿½"ï¿½-ï¿½z× ï¿½.×ª ×¤×ªï¿½.ï¿½-ï¿½.×ª ï¿½>×¨ï¿½'×¢.\n"
                    "ï¿½"ï¿½Tï¿½" ï¿½"×¨××©ï¿½.ï¿½Y ï¿½o×¤×¨×¡×! ï¿½?' ï¿½Y'ï¿½ ×¤×¨×¡× ï¿½zï¿½>ï¿½T×¨ï¿½"", self.main_reply_keyboard())
                return

            text = "ï¿½Y>' <b>ï¿½oï¿½.ï¿½- ï¿½zï¿½>ï¿½T×¨ï¿½.×ª ï¿½?" ï¿½"ï¿½-ï¿½z× ï¿½.×ª ×¤×ªï¿½.ï¿½-ï¿½.×ª</b>\nï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½\n\n"
            buttons = []
            for o in orders[:8]:
                total = o["amount"] * o["price_per_unit"]
                text += (
                    f"ï¿½Y"- <b>#{o['id']}</b> | {o['token']} | {o['amount']:.4f} ï¿½Tï¿½-ï¿½Tï¿½"ï¿½.×ª\n"
                    f"   ï¿½Y'ï¿½ {o['price_per_unit']} ï¿½,ï¿½/ï¿½Tï¿½-ï¿½Tï¿½"ï¿½" | ×¡ï¿½"\"ï¿½>: <b>{total:.2f} ï¿½,ï¿½</b>\n"
                    f"   ï¿½Y'ï¿½ {o['payment_method']} | ï¿½Y'ï¿½ ï¿½zï¿½.ï¿½>×¨: {o['seller_id']}\n\n"
                )
                if o["seller_id"] != chat_id:
                    buttons.append([{"text": f"ï¿½Y>' ×§× ï¿½" #{o['id']} ({o['amount']:.2f} {o['token']})",
                                     "callback_data": f"p2p_buy_{o['id']}"}])

            buttons.append([{"text": "ï¿½Y'ï¿½ ×¤×¨×¡× ï¿½zï¿½>ï¿½T×¨ï¿½"", "callback_data": "p2p_sell"},
                             {"text": "ï¿½Y"T P2P", "callback_data": "p2p_menu"}])
            self.send(chat_id, text, {"inline_keyboard": buttons})
        except Exception as e:
            logger.error(f"P2P browse error: {e}")
            self.send(chat_id, "ï¿½O ×©ï¿½'ï¿½T×ï¿½" ï¿½'ï¿½~×¢ï¿½T× ×ª ï¿½oï¿½.ï¿½- ï¿½zï¿½>ï¿½T×¨ï¿½.×ª.", self.main_reply_keyboard())

    def p2p_buy(self, chat_id, order_id):
        """Fill an order (buy from seller)."""
        try:
            # Fetch order details first
            resp = self.session.get(f"{self.API_BASE}/api/p2p/orders",
                                    params={"status": "active", "limit": 50}, timeout=8)
            orders = {o["id"]: o for o in resp.json().get("orders", [])}
            order = orders.get(order_id)
            if not order:
                self.send(chat_id, "ï¿½O ï¿½"ï¿½-ï¿½z× ï¿½" ï¿½o× × ï¿½z×¦×ï¿½" ×ï¿½. ï¿½>ï¿½'×¨ × ×¡ï¿½'×¨ï¿½".", self.main_reply_keyboard())
                return

            total = order["amount"] * order["price_per_unit"]
            # Execute fill
            fill_resp = self.session.post(
                f"{self.API_BASE}/api/p2p/fill-order",
                json={"order_id": order_id, "buyer_id": chat_id},
                timeout=10
            )
            result = fill_resp.json()
            if fill_resp.status_code == 200 and result.get("ok"):
                self.send(chat_id,
                    f"ï¿½o. <b>×¨ï¿½>ï¿½T×©ï¿½" ï¿½"ï¿½.×©ï¿½oï¿½zï¿½"!</b>\n\n"
                    f"ï¿½Y'ï¿½ ×§ï¿½Tï¿½'ï¿½o×ª: <b>{order['amount']:.4f} {order['token']}</b>\n"
                    f"ï¿½Y'ï¿½ ï¿½o×©ï¿½o×: <b>{total:.2f} ï¿½,ï¿½</b>\n"
                    f"ï¿½Y'ï¿½ ×©ï¿½Tï¿½~ï¿½": <b>{order['payment_method']}</b>\n"
                    f"ï¿½Y'ï¿½ ï¿½zï¿½.ï¿½>×¨ ID: <code>{order['seller_id']}</code>\n\n"
                    f"ï¿½sï¿½ï¸ <b>×©ï¿½o× ï¿½oï¿½zï¿½.ï¿½>×¨ ï¿½T×©ï¿½T×¨ï¿½.×ª!</b>\n"
                    f"×©ï¿½oï¿½- ï¿½oï¿½. ï¿½"ï¿½.ï¿½"×¢ï¿½" ï¿½'-Telegram ×¢× ID: <code>{order['seller_id']}</code>\n"
                    f"ï¿½"ï¿½~ï¿½.×§× ï¿½T× ï¿½>ï¿½'×¨ ï¿½-ï¿½.ï¿½>ï¿½. ï¿½oï¿½-×©ï¿½'ï¿½.× ï¿½s ï¿½?" /wallet ï¿½o×¦×¤ï¿½Tï¿½Tï¿½".",
                    self.main_reply_keyboard())
                # Notify seller
                self.send(order["seller_id"],
                    f"ï¿½YZ? <b>ï¿½"ï¿½-ï¿½z× ï¿½" #{order_id} × ï¿½zï¿½>×¨ï¿½"!</b>\n\n"
                    f"ï¿½Y'ï¿½ {order['amount']:.4f} {order['token']}\n"
                    f"ï¿½Y'ï¿½ ï¿½o×§ï¿½'ï¿½o: <b>{total:.2f} ï¿½,ï¿½</b> ï¿½z-{order['payment_method']}\n"
                    f"ï¿½Y'ï¿½ ×§ï¿½.× ï¿½" ID: <code>{chat_id}</code>\n\n"
                    f"ï¿½zï¿½z×ªï¿½Tï¿½Y ï¿½o×ª×©ï¿½oï¿½.× ï¿½zï¿½z× ï¿½.!")
                self._refresh_balances(chat_id)
            else:
                err = result.get("detail", "×©ï¿½'ï¿½T×ï¿½" ï¿½o× ï¿½Tï¿½"ï¿½.×¢ï¿½"")
                self.send(chat_id, f"ï¿½O {err}", self.main_reply_keyboard())
        except Exception as e:
            logger.error(f"P2P buy error: {e}")
            self.send(chat_id, "ï¿½O ×©ï¿½'ï¿½T×ï¿½" ï¿½'×¨ï¿½>ï¿½T×©ï¿½".", self.main_reply_keyboard())

    # ï¿½"?ï¿½"? MY ORDERS ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
    def p2p_my_orders(self, chat_id):
        try:
            resp = self.session.get(f"{self.API_BASE}/api/p2p/orders",
                                    params={"status": "active", "limit": 50}, timeout=8)
            all_orders = resp.json().get("orders", [])
            mine = [o for o in all_orders if o["seller_id"] == chat_id]

            if not mine:
                self.send(chat_id,
                    "ï¿½Y"< <b>ï¿½"ï¿½"ï¿½-ï¿½z× ï¿½.×ª ×©ï¿½oï¿½T</b>\n\n×ï¿½Tï¿½Y ï¿½oï¿½s ï¿½"ï¿½-ï¿½z× ï¿½.×ª ×¤×ªï¿½.ï¿½-ï¿½.×ª.\nï¿½Y'ï¿½ ×¨ï¿½.×¦ï¿½" ï¿½oï¿½zï¿½>ï¿½.×¨? ï¿½?' ×¤×¨×¡× ï¿½zï¿½>ï¿½T×¨ï¿½"",
                    self._p2p_keyboard())
                return

            text = "ï¿½Y"< <b>ï¿½"ï¿½"ï¿½-ï¿½z× ï¿½.×ª ×©ï¿½oï¿½T</b>\nï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½\n\n"
            buttons = []
            for o in mine:
                total = o["amount"] * o["price_per_unit"]
                text += (
                    f"ï¿½Y"- <b>#{o['id']}</b> | {o['token']}\n"
                    f"   ï¿½Y'ï¿½ {o['amount']:.4f} | {o['price_per_unit']} ï¿½,ï¿½/ï¿½Tï¿½-' | ×¡ï¿½"\"ï¿½> {total:.2f} ï¿½,ï¿½\n"
                    f"   ï¿½Y'ï¿½ {o['payment_method']}\n\n"
                )
                buttons.append([{"text": f"ï¿½O ï¿½'ï¿½~ï¿½o ï¿½"ï¿½-ï¿½z× ï¿½" #{o['id']}",
                                  "callback_data": f"p2p_cancel_order_{o['id']}"}])

            buttons.append([{"text": "ï¿½Y"T P2P", "callback_data": "p2p_menu"}])
            self.send(chat_id, text, {"inline_keyboard": buttons})
        except Exception as e:
            logger.error(f"P2P my_orders error: {e}")
            self.send(chat_id, "ï¿½O ×©ï¿½'ï¿½T×ï¿½" ï¿½'ï¿½~×¢ï¿½T× ×ª ï¿½"ï¿½-ï¿½z× ï¿½.×ª.", self.main_reply_keyboard())

    def p2p_cancel_order(self, chat_id, order_id):
        try:
            resp = self.session.delete(
                f"{self.API_BASE}/api/p2p/cancel-order/{order_id}",
                params={"seller_id": chat_id}, timeout=10
            )
            result = resp.json()
            if resp.status_code == 200 and result.get("ok"):
                self.send(chat_id,
                    f"ï¿½o. <b>ï¿½"ï¿½-ï¿½z× ï¿½" #{order_id} ï¿½'ï¿½.ï¿½~ï¿½oï¿½"</b>\n\n"
                    f"ï¿½Y"" ï¿½"ï¿½.ï¿½-ï¿½-×¨: <b>{result['refunded_amount']} {result['refunded_token']}</b>\n"
                    f"ï¿½Y'ï¿½ /wallet ï¿½o×¦×¤ï¿½Tï¿½Tï¿½" ï¿½'ï¿½T×ª×¨ï¿½"", self.main_reply_keyboard())
                self._refresh_balances(chat_id)
            else:
                err = result.get("detail", "×©ï¿½'ï¿½T×ï¿½"")
                self.send(chat_id, f"ï¿½O {err}", self.main_reply_keyboard())
        except Exception as e:
            logger.error(f"P2P cancel order error: {e}")
            self.send(chat_id, "ï¿½O ×©ï¿½'ï¿½T×ï¿½" ï¿½'ï¿½'ï¿½Tï¿½~ï¿½.ï¿½o.", self.main_reply_keyboard())

    # ï¿½"?ï¿½"? P2P CALLBACK DISPATCHER ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
    def handle_p2p_callback(self, chat_id, data, callback_id, message_id):
        self.answer_callback(callback_id)

        if data == "p2p_menu":
            self.handle_p2p_menu(chat_id)
        elif data == "p2p_send":
            self.p2p_start_send(chat_id)
        elif data == "p2p_sell":
            self.p2p_start_sell(chat_id)
        elif data == "p2p_browse":
            self.p2p_browse(chat_id)
        elif data == "p2p_myorders":
            self.p2p_my_orders(chat_id)
        elif data == "p2p_cancel":
            self._pending_p2p.pop(chat_id, None)
            self.send(chat_id, "ï¿½O ï¿½'ï¿½.ï¿½~ï¿½o.", self.main_reply_keyboard())

        # Token selection for send
        elif data.startswith("send_tok_"):
            token = data.split("_")[-1]
            state = self._pending_p2p.get(chat_id, {})
            if state.get("flow") == "send":
                state["data"]["token"] = token
                state["step"] = "enter_recipient"
                self.send(chat_id,
                    f"ï¿½Y"ï¿½ <b>×©ï¿½oï¿½- {token}</b>\n\n"
                    f"ï¿½"ï¿½>× ×¡ ××ª ï¿½"-Telegram User ID ×©ï¿½o ï¿½"× ï¿½z×¢ï¿½Y:\n"
                    f"(ï¿½"× ï¿½z×¢ï¿½Y ï¿½Tï¿½>ï¿½.ï¿½o ï¿½o×©ï¿½oï¿½.ï¿½- /myid ï¿½>ï¿½"ï¿½T ï¿½oï¿½"×¢×ª ××ª ï¿½"-ID ×©ï¿½oï¿½.)")

        # Token selection for sell
        elif data.startswith("sell_tok_"):
            token = data.split("_")[-1]
            state = self._pending_p2p.get(chat_id, {})
            if state.get("flow") == "sell":
                bal = self._get_balance_for(chat_id, token)
                if bal <= 0:
                    self.send(chat_id, f"ï¿½O ×ï¿½Tï¿½Y ï¿½oï¿½s {token} ï¿½oï¿½zï¿½>ï¿½T×¨ï¿½".")
                    return
                state["data"]["token"] = token
                state["step"] = "enter_amount"
                self.send(chat_id,
                    f"ï¿½Y'ï¿½ <b>ï¿½>ï¿½zï¿½" {token} ï¿½oï¿½zï¿½>ï¿½.×¨?</b>\n"
                    f"ï¿½"ï¿½T×ª×¨ï¿½" ×©ï¿½oï¿½s: <b>{bal:.4f}</b>\n\n"
                    f"ï¿½"ï¿½>× ×¡ ï¿½>ï¿½zï¿½.×ª:")

        # Payment method selection
        elif data.startswith("pay_"):
            method = data[4:]
            state = self._pending_p2p.get(chat_id, {})
            if state and state.get("flow") == "sell":
                state["data"]["payment"] = method
                state["step"] = "confirm"
                d = state["data"]
                total = d["amount"] * d["price"]
                self.send(chat_id,
                    f"ï¿½o. <b>×ï¿½T×©ï¿½.×¨ ×¤×¨×¡ï¿½.× ï¿½zï¿½>ï¿½T×¨ï¿½"</b>\n\n"
                    f"ï¿½Y'ï¿½ ï¿½zï¿½.ï¿½>×¨: <b>{d['amount']} {d['token']}</b>\n"
                    f"ï¿½Y'ï¿½ ï¿½zï¿½-ï¿½T×¨: <b>{d['price']} ï¿½,ï¿½</b> ï¿½oï¿½Tï¿½-ï¿½Tï¿½"ï¿½"\n"
                    f"ï¿½Y"S ×¡ï¿½"\"ï¿½>: <b>{total:.2f} ï¿½,ï¿½</b>\n"
                    f"ï¿½Y'ï¿½ ×ª×©ï¿½oï¿½.×: <b>{method}</b>\n\n"
                    f"ï¿½Y"' ï¿½"ï¿½~ï¿½.×§× ï¿½T× ï¿½T× ×¢ï¿½oï¿½. ï¿½'-escrow ×¢ï¿½" ï¿½oï¿½zï¿½>ï¿½T×¨ï¿½".\n\n"
                    f"×©ï¿½oï¿½- <b>ï¿½>ï¿½Y</b> ï¿½o×ï¿½T×©ï¿½.×¨ ×ï¿½. <b>ï¿½o×</b> ï¿½oï¿½'ï¿½Tï¿½~ï¿½.ï¿½o:")

        # Buy order
        elif data.startswith("p2p_buy_"):
            order_id = int(data.split("_")[-1])
            self.p2p_buy(chat_id, order_id)

        # Cancel own order
        elif data.startswith("p2p_cancel_order_"):
            order_id = int(data.split("_")[-1])
            self.p2p_cancel_order(chat_id, order_id)

    # ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½ï¿½.ï¿½

    def handle_text(self, chat_id, text, first_name, username):
        """Handle non-command text and legacy reply keyboard buttons.

        STRICT rules ï¿½?" no more 'any text = payment':
        - Valid username: 3ï¿½?"32 chars of [A-Za-z0-9_], and user is in username-collection state
        - Valid BSC/ETH TX hash: '0x' + exactly 64 hex chars (66 total)
        - Valid TON TX hash: 44 base64 chars OR 64 hex chars
        - Anything else ï¿½?' polite fallback (no false "payment received")
        """
        text = (text or "").strip()

        # Ignore group/channel messages (negative chat IDs)
        if chat_id < 0:
            return

        # --- 0) P2P multi-step flow (highest priority) ---
        if chat_id in self._pending_p2p:
            flow = self._pending_p2p[chat_id].get("flow")
            if flow == "send" and self.p2p_send_step(chat_id, text):
                return
            if flow == "sell" and self.p2p_sell_step(chat_id, text):
                return

        user = _get_user(chat_id)
        state = user.get("state", "")

        # --- 1) Username capture (only while in username state) ---
        is_username = bool(re.match(r'^[A-Za-z0-9_]{3,32}$', text))
        if is_username and state == "awaiting_username":
            user["username"] = text
            user["state"] = "awaiting_payment"
            # state persists via in-memory _user_data reference
            self.send(chat_id,
                f"ï¿½o. <b>× ×¨×©ï¿½z×ª!</b> @{text}\n\n"
                f"ï¿½Y'ï¿½ ï¿½o×¨ï¿½>ï¿½T×©ï¿½" ×©ï¿½oï¿½- ï¿½o××¨× ×§ TON:\n<code>{TON_WALLET}</code>\n\n"
                "ï¿½Y"ï¿½ ×©ï¿½oï¿½- ×¦ï¿½Tï¿½oï¿½.× ï¿½z×¡ï¿½s ×ï¿½. Transaction Hash",
                self.back_keyboard())
            if str(chat_id) != ADMIN_ID:
                self.send(int(ADMIN_ID), f"ï¿½Y'ï¿½ <b>ï¿½z×©×ªï¿½z×© ï¿½-ï¿½"×©:</b> @{text} ({chat_id})")
            return

        # --- 2) TX hash detection (strict format, only when awaiting payment) ---
        is_bsc_hash = bool(re.match(r'^0x[0-9a-fA-F]{64}$', text))
        is_hex64    = bool(re.match(r'^[0-9a-fA-F]{64}$', text))
        is_ton_b64  = bool(re.match(r'^[A-Za-z0-9+/=_-]{44}$', text))
        is_tx_hash  = is_bsc_hash or is_hex64 or is_ton_b64

        if is_tx_hash and state == "awaiting_payment":
            user["state"] = "payment_pending_review"
            user.setdefault("deposits", []).append({
                "id": len(user.get("deposits", [])) + 1,
                "tx_hash": text,
                "chain": "BSC" if is_bsc_hash else ("TON" if is_ton_b64 else "unknown"),
                "status": "pending_verification",
                "amount": None,
                "created_at": int(time.time()),
            })
            self.send(chat_id,
                "ï¿½Y"ï¿½ <b>×ª×©ï¿½oï¿½.× ï¿½"×ª×§ï¿½'ï¿½o ï¿½oï¿½'ï¿½"ï¿½T×§ï¿½"!</b>\n\n"
                "ï¿½Y"- Hash: <code>" + text[:20] + "...</code>\n"
                "â³ ×¡ï¿½~ï¿½~ï¿½.×¡: <b>ï¿½zï¿½z×ªï¿½Tï¿½Y ï¿½o×ï¿½T×©ï¿½.×¨ ×ï¿½"ï¿½zï¿½Tï¿½Y</b>\n\n"
                "×ª×§ï¿½'ï¿½o ï¿½"×ª×¨×ï¿½" ï¿½'×¨ï¿½'×¢ ×©ï¿½"×ª×©ï¿½oï¿½.× ï¿½T×ï¿½.ï¿½z×ª (×¢ï¿½" 24 ×©×¢ï¿½.×ª).\n"
                "ï¿½Y'ï¿½ ï¿½'ï¿½T× ×ªï¿½Tï¿½T×, ï¿½"×¦ï¿½~×¨×£: @SLH_Community",
                self.back_keyboard())
            if str(chat_id) != ADMIN_ID:
                self.send(int(ADMIN_ID),
                    f"ï¿½Y'ï¿½ <b>×¢×¡×§ï¿½" ï¿½-ï¿½"×©ï¿½" ï¿½o×ï¿½T×©ï¿½.×¨!</b>\n"
                    f"User: {chat_id} (@{user.get('username','?')})\n"
                    f"Hash: <code>{text}</code>\n"
                    f"/approve_{chat_id} ×ï¿½. /reject_{chat_id}")
            return

        # --- 3) TX hash received OUT OF state ï¿½?' tell user to start flow ---
        if is_tx_hash and state != "awaiting_payment":
            self.send(chat_id,
                "ï¿½sï¿½ï¸ ×§ï¿½Tï¿½'ï¿½o×ªï¿½T Hash ×ï¿½'ï¿½o ×ï¿½Tï¿½Y ï¿½'×§×©×ª ×ª×©ï¿½oï¿½.× ×¤×ªï¿½.ï¿½-ï¿½".\n\n"
                "ï¿½o×ª×©ï¿½oï¿½.× ï¿½-ï¿½"×©, ï¿½oï¿½-×¥ /start ï¿½?' ï¿½Y'ï¿½ ï¿½"×¤×¢ï¿½oï¿½"",
                self.main_reply_keyboard())
            return

        # --- 4) Wallet address (informational only, no payment assumed) ---
        if re.match(r'^(0x[0-9a-fA-F]{40}|[UE]Q[A-Za-z0-9_-]{46})$', text):
            self.send(chat_id,
                "ï¿½Y"< ×§ï¿½Tï¿½'ï¿½o×ªï¿½T ï¿½>×ªï¿½.ï¿½'×ª ××¨× ×§. ï¿½o×©ï¿½oï¿½.ï¿½- ï¿½>×¡×£ ×ï¿½o ï¿½>×ªï¿½.ï¿½'×ª ï¿½-ï¿½.? ï¿½oï¿½-×¥ /start ï¿½?' ï¿½Y'ï¿½ ××¨× ×§\n\n"
                "ï¿½sï¿½ï¸ ×©ï¿½T× ï¿½oï¿½': ×©ï¿½oï¿½Tï¿½-×ª ï¿½>×ªï¿½.ï¿½'×ª ï¿½oï¿½'ï¿½" ï¿½o× ×¤ï¿½.×ªï¿½-×ª ×ª×©ï¿½oï¿½.×.",
                self.main_reply_keyboard())
            return

        # --- 5) Fallback (no more false payment confirmations) ---
        # If user is in payment state but didn't send TX hash or photo ï¿½?" remind them
        if state == "awaiting_payment":
            self.send(chat_id,
                "ï¿½sï¿½ï¸ <b>×©ï¿½oï¿½' ï¿½"×ª×©ï¿½oï¿½.× ×¤×ªï¿½.ï¿½-!</b>\n\n"
                "ï¿½>ï¿½"ï¿½T ï¿½oï¿½"×©ï¿½oï¿½T×:\n"
                "1ï¸ï¿½fï¿½ ï¿½"×¢ï¿½'×¨ TON ï¿½oï¿½>×ªï¿½.ï¿½'×ª:\n<code>" + TON_WALLET + "</code>\n\n"
                "2ï¸ï¿½fï¿½ ×©ï¿½oï¿½- ï¿½oï¿½T <b>×¦ï¿½Tï¿½oï¿½.× ï¿½z×¡ï¿½s</b> ×©ï¿½o ï¿½"ï¿½"×¢ï¿½'×¨ï¿½"\n"
                "   ×ï¿½. <b>Transaction Hash</b>\n\n"
                "ï¿½Y"ï¿½ ××¤×©×¨ ï¿½o×©ï¿½oï¿½.ï¿½- ×ªï¿½zï¿½.× ï¿½" ï¿½T×©ï¿½T×¨ï¿½.×ª ï¿½o×¦'×ï¿½~ ï¿½"ï¿½-ï¿½"!\n\n"
                "ï¿½" ×¦×¨ï¿½Tï¿½s ×¢ï¿½-×¨ï¿½"? ×¦ï¿½.×¨ ×§×©×¨: @osifeu_prog",
                self.back_keyboard())
            return

        self.send(chat_id, "ï¿½Yï¿½- ï¿½o× ï¿½"ï¿½'× ×ªï¿½T. ï¿½oï¿½-×¥ /start ï¿½o×ª×¤×¨ï¿½Tï¿½~ ï¿½"×¨××©ï¿½T", self.main_reply_keyboard())

    # ï¿½"?ï¿½"? Main loop ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
    def process_updates(self):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {"offset": self.offset, "timeout": 30}

        try:
            response = self.session.get(url, params=params, timeout=35)
            if response.status_code != 200:
                return
            data = response.json()
            if not data.get("ok"):
                return

            for update in data["result"]:
                self.offset = update["update_id"] + 1

                # Callback queries (inline buttons)
                if "callback_query" in update:
                    try:
                        self.handle_callback(update["callback_query"])
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                    continue

                if "message" not in update:
                    continue
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "").strip()
                first_name = msg["chat"].get("first_name", "")
                username = msg["chat"].get("username", "")

                if not text:
                    if msg.get("photo"):
                        self.send(chat_id, "ï¿½Y"ï¿½ ×§ï¿½'ï¿½o× ï¿½.! × ï¿½'ï¿½"ï¿½.×§ ï¿½.× ×¢ï¿½"ï¿½>ï¿½Y ï¿½'ï¿½"×§ï¿½"×.", self.back_keyboard())
                        if str(chat_id) != ADMIN_ID:
                            self.send(int(ADMIN_ID), f"ï¿½Y"ï¿½ <b>ï¿½"ï¿½.ï¿½>ï¿½-×ª ×ª×©ï¿½oï¿½.×!</b>\nUser: {chat_id} (@{username})")
                    continue

                logger.info(f"ï¿½Y"ï¿½ {first_name}: {text}")

                # ï¿½"?ï¿½"? Slash commands ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
                if text == "/start" or text.startswith("/start "):
                    start_param = text.split(" ", 1)[1] if " " in text else ""
                    self.handle_start(chat_id, first_name, username, start_param)
                elif text == "/prices":
                    self.handle_prices(chat_id)
                elif text == "/wallet" or text == "/mybalance":
                    self.handle_wallet(chat_id)
                elif text == "/deposit_address":
                    self.handle_deposit_address(chat_id)
                elif text.startswith("/verify "):
                    self.handle_verify_deposit(chat_id, text[8:])
                elif text.startswith("/send_slh "):
                    self.handle_send_internal(chat_id, text[10:], "SLH")
                elif text.startswith("/send_ton "):
                    self.handle_send_internal(chat_id, text[10:], "TON")
                elif text.startswith("/send_bnb "):
                    self.handle_send_internal(chat_id, text[10:], "BNB")
                elif text.startswith("/send_zvk "):
                    self.handle_send_internal(chat_id, text[10:], "ZVK")
                elif text == "/tx_history":
                    self.handle_tx_history(chat_id)
                elif text == "/onchain":
                    self.handle_onchain_balance(chat_id)
                elif text == "/deposit" or text.startswith("/deposit "):
                    args = text.split(" ", 1)[1] if " " in text else ""
                    self.handle_deposit(chat_id, args)
                elif text == "/mydeposits":
                    self.handle_mydeposits(chat_id)
                elif text == "/withdraw" or text.startswith("/withdraw "):
                    args = text.split(" ", 1)[1] if " " in text else ""
                    self.handle_withdraw(chat_id, args)
                elif text == "/statement":
                    self.handle_statement(chat_id)
                elif text == "/portfolio":
                    self.handle_portfolio(chat_id)
                elif text == "/earn":
                    self.handle_earn(chat_id)
                elif text == "/swap":
                    self.handle_swap_text(chat_id)
                elif text == "/vip":
                    self.handle_vip(chat_id)
                elif text == "/airdrop":
                    self.handle_airdrop(chat_id)
                elif text in ("/p2p", "/trade"):
                    self.handle_p2p_menu(chat_id)
                elif text.startswith("/send "):
                    # /send TOKEN USER_ID AMOUNT shorthand
                    parts = text.split()
                    if len(parts) == 4:
                        tok = parts[1].upper()
                        self.handle_send_internal(chat_id, f"{parts[2]} {parts[3]}", tok)
                    else:
                        self.send(chat_id, "×©ï¿½Tï¿½zï¿½.×©: /send TOKEN USER_ID AMOUNT\nï¿½"ï¿½.ï¿½'ï¿½zï¿½": /send ZVK 123456789 50")
                elif text in ("/referral", "/mylink"):
                    self.handle_referral(chat_id)
                elif text == "/deals":
                    self.handle_deals_text(chat_id)
                elif text == "/buyslh":
                    self.handle_buy_slh_text(chat_id)
                elif text == "/help":
                    self.handle_help(chat_id)
                elif text == "/faq":
                    self.handle_faq(chat_id)
                elif text == "/kyc" or text.startswith("/kyc "):
                    args = text.split(" ", 1)[1] if " " in text else ""
                    self.handle_kyc(chat_id, args)
                elif text == "/share":
                    self.handle_share(chat_id)
                elif text in ("/admin", "/stats"):
                    self.handle_admin(chat_id)
                elif text.startswith("/broadcast "):
                    self.handle_broadcast(chat_id, text[11:])
                elif text.startswith("/approve "):
                    self.handle_approve(chat_id, text[9:])
                elif text == "/support":
                    self.send(chat_id, "ï¿½Y"z <b>×ªï¿½zï¿½Tï¿½>ï¿½"</b>\n\n×¤× ï¿½" ï¿½o-@Osif83 ï¿½oï¿½>ï¿½o ×©×ï¿½oï¿½".", self.main_reply_keyboard())
                elif text == "/myid":
                    self.send(chat_id, f"ï¿½Y?" <b>ï¿½"ï¿½zï¿½-ï¿½"ï¿½" ×©ï¿½oï¿½s:</b> <code>{chat_id}</code>", self.main_reply_keyboard())
                elif text == "/hub":
                    user = _get_user(chat_id)
                    vip_badge = "ï¿½Y'' VIP" if user["vip"] else "ï¿½Y?" Free"
                    self.send(chat_id,
                        f"ï¿½Ys? <b>SLH HUB SYSTEM</b>\n\n"
                        f"ï¿½Y'ï¿½ <b>{first_name}</b> | {vip_badge}\n"
                        f"ï¿½Y'ï¿½ ï¿½T×ª×¨ï¿½": <b>{user['hub_points']}</b> × ×§ï¿½.ï¿½"ï¿½.×ª\n"
                        f"ï¿½Y'Z SLH: <b>{user['slh_balance']:.2f}</b>\n"
                        f"ï¿½Y'ï¿½ ï¿½"×¤× ï¿½Tï¿½.×ª: <b>{user['referral_count']}</b>\n\nï¿½Y'? ï¿½'ï¿½-×¨ ×¤×¢ï¿½.ï¿½oï¿½":",
                        self.hub_inline_keyboard())

                # ï¿½"?ï¿½"? Reply keyboard buttons (text buttons at bottom) ï¿½"?ï¿½"?
                elif text == "ï¿½Y"S ï¿½"×©ï¿½.×§ ×¢ï¿½>×©ï¿½Tï¿½.":
                    self.handle_prices(chat_id)
                elif text == "ï¿½Y'ï¿½ ï¿½"×©×§×¢ï¿½.×ª":
                    self.handle_investments(chat_id)
                elif text == "ï¿½Y'ï¿½ ××¨× ×§":
                    self.handle_wallet(chat_id)
                elif text == "ï¿½Y"" P2P ï¿½z×¡ï¿½-×¨":
                    self.handle_p2p_menu(chat_id)
                elif text == "ï¿½Y"- On-Chain":
                    self.handle_onchain_balance(chat_id)
                elif text == "ï¿½Y>ï¿½ ×¡ï¿½Tï¿½>ï¿½.ï¿½Y ï¿½.ï¿½'×§×¨ï¿½"":
                    self.handle_risk(chat_id)
                elif text == "ï¿½YZï¿½ ï¿½'ï¿½.× ï¿½.×¡ï¿½T×":
                    self.handle_bonuses(chat_id)
                elif text == "ï¿½Y'ï¿½ ï¿½"ï¿½-ï¿½zï¿½Y":
                    self.handle_invite(chat_id)
                elif text == "ï¿½Y"S ï¿½"×©ï¿½'ï¿½.×¨ï¿½"":
                    self.handle_dashboard(chat_id)
                elif text == "ï¿½Y'ï¿½ ï¿½"×¤×¢ï¿½oï¿½"":
                    self.handle_activate(chat_id)
                elif text == "ï¿½Y"ï¿½ ×©ï¿½T×ªï¿½.×£":
                    self.handle_share(chat_id)
                elif text == "ï¿½Y"s ï¿½zï¿½"×¨ï¿½Tï¿½>ï¿½T×":
                    self.handle_guides(chat_id)
                elif text == "ï¿½Y"ï¿½ ï¿½zï¿½'×¦×¢ï¿½T×":
                    self.handle_deals_text(chat_id)
                elif text == "ï¿½Yï¿½T ×¨ï¿½>ï¿½T×©×ª SLH":
                    self.handle_buy_slh_text(chat_id)

                # ï¿½"?ï¿½"? Swap commands ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?ï¿½"?
                elif text.startswith("/swap "):
                    self.handle_swap_text(chat_id)
                elif text.startswith("/limit "):
                    self.send(chat_id, "ï¿½Y"ï¿½ ×¤×§ï¿½.ï¿½"×ª Limit × ×¨×©ï¿½zï¿½". ×ª×§ï¿½'ï¿½o ï¿½"×ª×¨×ï¿½" ï¿½>×©ï¿½"ï¿½zï¿½-ï¿½T×¨ ï¿½Tï¿½'ï¿½T×¢ ï¿½oï¿½T×¢ï¿½".", self.main_reply_keyboard())
                elif text.startswith("/alert "):
                    self.handle_alerts(chat_id)
                elif text == "/orders":
                    self.send(chat_id, "ï¿½Y"< <b>×¤×§ï¿½.ï¿½"ï¿½.×ª ×¤×ªï¿½.ï¿½-ï¿½.×ª:</b>\n\n×ï¿½Tï¿½Y ×¤×§ï¿½.ï¿½"ï¿½.×ª ×¤×ªï¿½.ï¿½-ï¿½.×ª.", self.main_reply_keyboard())
                elif text == "/ai" or text == "ï¿½Yï¿½ï¿½ × ï¿½T×ªï¿½.ï¿½- AI":
                    self.handle_ai_analysis(chat_id)

                elif not text.startswith("/"):
                    self.handle_text(chat_id, text, first_name, username)
                else:
                    self.send(chat_id, "ï¿½Yï¿½- ×¤×§ï¿½.ï¿½"ï¿½" ï¿½o× ï¿½zï¿½.ï¿½>×¨×ª. ï¿½oï¿½-×¥ /start", self.main_reply_keyboard())

        except Exception as e:
            logger.error(f"Update error: {e}")

    def run(self):
        logger.info("=" * 50)
        logger.info("ï¿½Ys? SLH Investment House + HUB BOT ï¿½?" Starting...")
        logger.info("=" * 50)

        try:
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe", timeout=10)
            if r.status_code == 200 and r.json().get("ok"):
                logger.info(f"ï¿½o. Bot: @{r.json()['result']['username']}")
            else:
                logger.error("ï¿½O Bot connection failed")
                return
        except Exception as e:
            logger.error(f"ï¿½O Bot test error: {e}")
            return

        logger.info("ï¿½Y"" Running ï¿½?" Investment House + HUB + Buy SLH")

        while True:
            try:
                self.process_updates()
                time.sleep(0.5)
            except KeyboardInterrupt:
                logger.info("ï¿½Y>' Bot stopped")
                break
            except Exception as e:
                logger.error(f"ï¿½O Main loop error: {e}")
                time.sleep(5)


def main():
    bot = SLHInvestmentBot()
    bot.run()


if __name__ == "__main__":
    main()


