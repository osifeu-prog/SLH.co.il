# -*- coding: utf-8 -*-
"""
SLH Investment House + HUB BOT
Full-featured investment house with HUB economic engine.

Features:
- ן¿½Y"S Live prices (12 coins)
- ן¿½Y'ן¿½ Investment plans (4 tiers, 4%-5.4% monthly)
- ן¿½Y'ן¿½ Wallet (TON/BNB/SLH/ZVK)
- ן¿½YZן¿½ Bonuses & games (slots, dice, basketball, darts)
- ן¿½Y>ן¿½ Risk management
- ן¿½Y"ן¿½ Swap/DEX
- ן¿½Yן¿½ן¿½ AI analysis
- ן¿½Y"S Dashboard
- ן¿½Y'ן¿½ Referrals (15% commission in SLH points)
- ן¿½Yן¿½T Buy SLH (444ן¿½,ן¿½ per coin)
- ן¿½Y'' VIP membership
- ן¿½YZן¿½ Airdrop
- ן¿½Y'ן¿½ Earn (daily tasks)
- ן¿½Y"ן¿½ Deals & promotions
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

# ן¿½"?ן¿½"? Add shared module to path ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
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

# ן¿½"?ן¿½"? Price API ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
COINS = {
    "BTC": {"symbol": "bitcoin", "emoji": "ן¿½YYן¿½", "name": "BTC"},
    "ETH": {"symbol": "ethereum", "emoji": "ן¿½Y"ן¿½", "name": "ETH"},
    "TON": {"symbol": "the-open-network", "emoji": "ן¿½Y'ן¿½", "name": "TON"},
    "BNB": {"symbol": "binancecoin", "emoji": "ן¿½YYן¿½", "name": "BNB"},
    "SOL": {"symbol": "solana", "emoji": "ן¿½YYן¿½", "name": "SOL"},
    "DOGE": {"symbol": "dogecoin", "emoji": "ן¿½Yן¿½ן¿½", "name": "DOGE"},
    "XRP": {"symbol": "ripple", "emoji": "ן¿½sן¿½", "name": "XRP"},
    "ADA": {"symbol": "cardano", "emoji": "ן¿½Y"ן¿½", "name": "ADA"},
    "DOT": {"symbol": "polkadot", "emoji": "ן¿½YYן¿½", "name": "DOT"},
    "AVAX": {"symbol": "avalanche-2", "emoji": "ג₪ן¸", "name": "AVAX"},
    "LINK": {"symbol": "chainlink", "emoji": "ן¿½Y"-", "name": "LINK"},
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


# ן¿½"?ן¿½"? In-memory user state ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
_user_data = {}

# Investment plans
INVESTMENT_PLANS = [
    {"name": "ן¿½YOן¿½ ׳₪׳§ן¿½"ן¿½.ן¿½Y ן¿½-ן¿½.ן¿½"׳©ן¿½T", "rate": 4, "annual": 48, "min_ton": 1, "days": 30},
    {"name": "ן¿½Y"^ ׳₪׳§ן¿½"ן¿½.ן¿½Y ׳¨ן¿½'׳¢ן¿½.׳ ן¿½T", "rate": 4.5, "annual": 55, "min_ton": 5, "days": 90},
    {"name": "ן¿½Y'Z ׳₪׳§ן¿½"ן¿½.ן¿½Y ן¿½-׳¦ן¿½T-׳©׳ ׳×ן¿½T", "rate": 5, "annual": 60, "min_ton": 10, "days": 180},
    {"name": "ן¿½Y'' ׳₪׳§ן¿½"ן¿½.ן¿½Y ׳©׳ ׳×ן¿½T", "rate": 5.4, "annual": 65, "min_ton": 25, "days": 365},
]

VIP_PLANS = {
    "basic": {"name": "VIP Basic", "price_ils": 41, "features": ["ן¿½"׳×׳¨׳-ן¿½.׳× ן¿½zן¿½-ן¿½T׳¨ן¿½T׳", "ן¿½'ן¿½T׳©ן¿½" ן¿½o׳¢׳¨ן¿½.׳¥ VIP", "5 ן¿½z׳©ן¿½Tן¿½zן¿½.׳× ׳ ן¿½.׳¡׳₪ן¿½.׳× ן¿½'ן¿½Tן¿½.׳"]},
    "pro": {"name": "VIP Pro", "price_ils": 99, "features": ["ן¿½"ן¿½>ן¿½o ן¿½'-Basic", "׳¡ן¿½Tן¿½'׳ ן¿½oן¿½T׳ ן¿½oן¿½z׳¡ן¿½-׳¨", "ן¿½'ן¿½T׳©ן¿½" ן¿½o-1-on-1", "׳¢ן¿½zן¿½o׳× ׳¨׳₪׳¨ן¿½o ן¿½>׳₪ן¿½.ן¿½oן¿½" (30%)"]},
    "elite": {"name": "VIP Elite", "price_ils": 199, "features": ["ן¿½"ן¿½>ן¿½o ן¿½'-Pro", "׳§ן¿½'ן¿½.׳¦׳× ן¿½.ן¿½.ן¿½T׳¡ן¿½~ ן¿½'ן¿½o׳¢ן¿½"ן¿½T׳×", "NFT ן¿½-ן¿½T׳ ׳ ן¿½>ן¿½o ן¿½-ן¿½.ן¿½"׳©", "ן¿½'ן¿½T׳©ן¿½" ן¿½zן¿½.׳§ן¿½"ן¿½z׳× ן¿½oן¿½>ן¿½o ן¿½zן¿½.׳¦׳¨ ן¿½-ן¿½"׳©"]},
}

SLH_BUY_TIERS = [
    {"amount": 0.0001, "price": 0.044},
    {"amount": 0.001, "price": 0.444},
    {"amount": 0.01, "price": 4.44},
    {"amount": 0.1, "price": 44.4},
    {"amount": 1, "price": 444},
]

_daily_tasks = [
    {"id": "join_channel", "title": "ן¿½Y"ן¿½ ן¿½"׳¦ן¿½~׳¨׳£ ן¿½o׳¢׳¨ן¿½.׳¥ @SLH_Community", "reward": 50},
    {"id": "share_bot", "title": "ן¿½Y"ן¿½ ׳©׳×׳£ ׳-׳× ן¿½"ן¿½'ן¿½.ן¿½~ ׳¢׳ ן¿½-ן¿½'׳¨", "reward": 100},
    {"id": "visit_site", "title": "ן¿½YOן¿½ ן¿½'׳§׳¨ ן¿½'׳-׳×׳¨ slh-nft.com", "reward": 30},
    {"id": "follow_fb", "title": "ן¿½Y'ן¿½ ׳¢׳§ן¿½.ן¿½' ׳-ן¿½-׳¨ן¿½T Facebook SLH", "reward": 40},
    {"id": "daily_login", "title": "ן¿½o. ן¿½>׳ ן¿½T׳¡ן¿½" ן¿½Tן¿½.ן¿½zן¿½T׳×", "reward": 10},
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

        # ן¿½"?ן¿½"? Async event loop in background thread (for WalletEngine) ן¿½"?ן¿½"?
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._loop_thread.start()

        # ן¿½"?ן¿½"? WalletEngine (blockchain wallets) ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
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
            logger.info("ן¿½o. WalletEngine connected ן¿½?" DB + Redis + BSC + TON")
        except Exception as e:
            logger.warning(f"ן¿½sן¿½ן¸ WalletEngine init failed (falling back to mock): {e}")

        logger.info("ן¿½Ys? SLH Investment House + HUB initialized")

    def _run_async(self, coro, timeout=10):
        """Run an async coroutine from synchronous code via the background loop."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    # ן¿½"?ן¿½"? Telegram API ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
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

    # ן¿½"?ן¿½"? Reply keyboard (main menu buttons at bottom) ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
    def main_reply_keyboard(self):
        return {"keyboard": [
            [{"text": "ן¿½Y"S ן¿½"׳©ן¿½.׳§ ׳¢ן¿½>׳©ן¿½Tן¿½."}, {"text": "ן¿½Y'ן¿½ ן¿½"׳©׳§׳¢ן¿½.׳×"}],
            [{"text": "ן¿½Y'ן¿½ ׳-׳¨׳ ׳§"}, {"text": "ן¿½Y"" P2P ן¿½z׳¡ן¿½-׳¨"}],
            [{"text": "ן¿½YZן¿½ ן¿½'ן¿½.׳ ן¿½.׳¡ן¿½T׳"}, {"text": "ן¿½Y'ן¿½ ן¿½"ן¿½-ן¿½zן¿½Y"}],
            [{"text": "ן¿½Y"S ן¿½"׳©ן¿½'ן¿½.׳¨ן¿½""}, {"text": "ן¿½Yן¿½T ׳¨ן¿½>ן¿½T׳©׳× SLH"}],
            [{"text": "ן¿½Y'ן¿½ ן¿½"׳₪׳¢ן¿½oן¿½""}, {"text": "ן¿½Y"ן¿½ ׳©ן¿½T׳×ן¿½.׳£"}],
            [{"text": "ן¿½Y"s ן¿½zן¿½"׳¨ן¿½Tן¿½>ן¿½T׳"}, {"text": "ן¿½Y"ן¿½ ן¿½zן¿½'׳¦׳¢ן¿½T׳"}],
        ], "resize_keyboard": True, "one_time_keyboard": False}

    # ן¿½"?ן¿½"? Inline keyboards ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
    def hub_inline_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "ן¿½Y'ן¿½ Earn", "callback_data": "menu_earn"}, {"text": "ן¿½Y"" Swap", "callback_data": "menu_swap"}],
            [{"text": "ן¿½Y'' VIP", "callback_data": "menu_vip"}, {"text": "ן¿½YZן¿½ Airdrop", "callback_data": "menu_airdrop"}],
            [{"text": "ן¿½Yן¿½T Buy SLH", "callback_data": "menu_buy_slh"}],
            [{"text": "ן¿½Y'ן¿½ ן¿½"׳₪׳ ן¿½Tן¿½.׳× ׳©ן¿½oן¿½T", "callback_data": "menu_referral"}, {"text": "ן¿½Y"S ן¿½"׳×ן¿½T׳§ ׳©ן¿½oן¿½T", "callback_data": "menu_portfolio"}],
            [{"text": "ן¿½Y"ן¿½ ן¿½zן¿½'׳¦׳¢ן¿½T׳", "callback_data": "menu_deals"}, {"text": "ן¿½" ׳¢ן¿½-׳¨ן¿½"", "callback_data": "menu_help"}],
        ]}

    def back_keyboard(self):
        return {"inline_keyboard": [[{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½" ן¿½o׳×׳₪׳¨ן¿½Tן¿½~", "callback_data": "menu_main"}]]}

    def earn_keyboard(self):
        rows = []
        for t in _daily_tasks:
            rows.append([{"text": f"{t['title']} (+{t['reward']})", "callback_data": f"task_{t['id']}"}])
        rows.append([{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½" ן¿½o׳×׳₪׳¨ן¿½Tן¿½~", "callback_data": "menu_main"}])
        return {"inline_keyboard": rows}

    def vip_keyboard(self):
        return {"inline_keyboard": [
            [{"text": f"ג­- Basic ן¿½?" {VIP_PLANS['basic']['price_ils']}ן¿½,ן¿½", "callback_data": "vip_basic"}],
            [{"text": f"ן¿½Y'Z Pro ן¿½?" {VIP_PLANS['pro']['price_ils']}ן¿½,ן¿½", "callback_data": "vip_pro"}],
            [{"text": f"ן¿½Y'' Elite ן¿½?" {VIP_PLANS['elite']['price_ils']}ן¿½,ן¿½", "callback_data": "vip_elite"}],
            [{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½" ן¿½o׳×׳₪׳¨ן¿½Tן¿½~", "callback_data": "menu_main"}],
        ]}

    def buy_slh_keyboard(self):
        rows = []
        for tier in SLH_BUY_TIERS:
            rows.append([{"text": f"ן¿½Yן¿½T {tier['amount']} SLH = {tier['price']}ן¿½,ן¿½", "callback_data": f"buy_slh_{tier['amount']}"}])
        rows.append([{"text": "ן¿½oן¿½ן¸ ׳¡ן¿½>ן¿½.׳ ן¿½zן¿½.׳×׳-׳ ׳-ן¿½T׳©ן¿½T׳×", "callback_data": "buy_slh_custom"}])
        rows.append([{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½" ן¿½o׳×׳₪׳¨ן¿½Tן¿½~", "callback_data": "menu_main"}])
        return {"inline_keyboard": rows}

    def invest_keyboard(self):
        rows = []
        for i, plan in enumerate(INVESTMENT_PLANS):
            rows.append([{"text": f"{plan['name']} | {plan['rate']}% | {plan['min_ton']} TON", "callback_data": f"invest_{i}"}])
        rows.append([{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½"", "callback_data": "menu_main"}])
        return {"inline_keyboard": rows}

    def games_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "ן¿½YZן¿½ ׳¡ן¿½oן¿½.ן¿½~ן¿½T׳", "callback_data": "game_slots"}, {"text": "ן¿½YZן¿½ ׳§ן¿½.ן¿½'ן¿½Tן¿½.׳×", "callback_data": "game_dice"}],
            [{"text": "ן¿½Yן¿½? ן¿½>ן¿½"ן¿½.׳¨׳¡ן¿½o", "callback_data": "game_basketball"}, {"text": "ן¿½YZן¿½ ן¿½-׳¦ן¿½T׳", "callback_data": "game_darts"}],
            [{"text": "ן¿½Y'ן¿½ ן¿½"ן¿½z׳¨ ZVK ן¿½?' TON", "callback_data": "game_convert"}],
            [{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½"", "callback_data": "menu_main"}],
        ]}

    # ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½
    # INVESTMENT HOUSE HANDLERS (original reply-keyboard buttons)
    # ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½

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
                    self.send(referrer_id, f"ן¿½YZ? <b>ן¿½"׳₪׳ ן¿½Tן¿½" ן¿½-ן¿½"׳©ן¿½"!</b>\n\n@{username or first_name} ן¿½"׳¦ן¿½~׳¨׳£ ן¿½"׳¨ן¿½>ן¿½s!\n+50 ׳ ׳§ן¿½.ן¿½"ן¿½.׳× SLH ן¿½YZן¿½")
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
                logger.info(f"[bot-sync] ן¿½o. Synced {chat_id} (@{username}) to website ן¿½?" registered={sync_data.get('is_registered')}")
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
                logger.info(f"[bal-sync] ן¿½o. {chat_id}: SLH={user['slh_balance']}, ZVK={user['zvk_balance']}")
        except Exception as e:
            logger.warning(f"[bal-sync] failed for {chat_id}: {e}")

        invested = user["ton_locked"]
        profit = user["ton_locked"] * 0.04 if user["ton_locked"] > 0 else 0
        status = "ן¿½o. ן¿½z׳©׳§ן¿½T׳¢ ׳₪׳¢ן¿½Tן¿½o" if user["activated"] else "ג³ ן¿½zן¿½z׳×ן¿½Tן¿½Y ן¿½oן¿½"׳₪׳¢ן¿½oן¿½""

        # Personal login link for the website (comes from auto-sync)
        login_url = user.get("web_login_url") or f"https://slh-nft.com/dashboard.html?uid={chat_id}"

        # Professional ASCII branding ן¿½?" clean, monospace-safe, SLH colors
        text = (
            f"<b>ן¿½oן¿½ SLH SPARK ן¿½oן¿½</b>\n"
            f"<i>Digital Investment House</i>\n"
            f"<code>ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½</code>\n"
            f"        ן¿½Y'Z  S L H\n"
            f"   Investment Ecosystem\n"
            f"      by SPARK IND\n"
            f"<code>ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½</code>\n\n"
            f"׳©ן¿½oן¿½.׳ <b>{first_name}</b>! ן¿½Y'<\n"
            f"ן¿½Y?" <b>ן¿½"ן¿½zן¿½-ן¿½"ן¿½" ׳©ן¿½oן¿½s:</b> <code>{chat_id}</code>\n"
            f"ן¿½Y'ן¿½ <b>Username:</b> @{username or 'ן¿½o׳- ן¿½"ן¿½.ן¿½'ן¿½"׳¨'}\n\n"
            f"ן¿½YOן¿½ <b><a href=\"{login_url}\">ן¿½"ן¿½Tן¿½>׳ ׳¡ ן¿½o׳-׳×׳¨ ן¿½"׳-ן¿½T׳©ן¿½T ׳©ן¿½oן¿½s ן¿½?ן¿½</a></b>\n"
            f"   <i>(ן¿½oן¿½-ן¿½T׳¦ן¿½" ׳-ן¿½-׳× ֲ· ן¿½oן¿½o׳- ׳¡ן¿½T׳¡ן¿½zן¿½")</i>\n\n"
            f"<code>ן¿½"ן¿½ן¿½"ן¿½ ן¿½"׳¡ן¿½~ן¿½~ן¿½.׳¡ ׳©ן¿½oן¿½s ן¿½"ן¿½ן¿½"ן¿½</code>\n"
            f"ן¿½Y'ן¿½ {status}\n"
            f"ן¿½Y'ן¿½ ן¿½zן¿½.׳©׳§׳¢: <b>{invested:.2f} TON</b>\n"
            f"ן¿½Y"^ ׳¨ן¿½.ן¿½.ן¿½-: <b>+{profit:.4f} TON</b>\n"
            f"ן¿½Y'Z SLH: <b>{user['slh_balance']:,.2f}</b>\n"
            f"ן¿½YZן¿½ ZVK: <b>{user['zvk_balance']}</b>\n\n"
            f"<code>ן¿½"ן¿½ן¿½"ן¿½ ן¿½zן¿½" ׳×׳¨׳¦ן¿½" ן¿½o׳¢׳©ן¿½.׳×? ן¿½"ן¿½ן¿½"ן¿½</code>\n"
            f"ן¿½Y"S <b>ן¿½"׳©ן¿½.׳§ ׳¢ן¿½>׳©ן¿½Tן¿½.</b> ן¿½?" ן¿½zן¿½-ן¿½T׳¨ן¿½T׳, ן¿½zן¿½'ן¿½zן¿½.׳×, ׳¡ן¿½Tן¿½'׳ ן¿½oן¿½T׳\n"
            f"ן¿½Y'ן¿½ <b>ן¿½"׳©׳§׳¢ן¿½.׳×</b> ן¿½?" 4 ׳×ן¿½.ן¿½>׳ ן¿½Tן¿½.׳×, 4%-5.4% ן¿½-ן¿½.ן¿½"׳©ן¿½T\n"
            f"ן¿½Y'ן¿½ <b>׳-׳¨׳ ׳§</b> ן¿½?" TON/BNB/SLH + ן¿½"׳¢ן¿½'׳¨ן¿½.׳×\n"
            f"ן¿½Y>ן¿½ <b>׳¡ן¿½Tן¿½>ן¿½.ן¿½Y</b> ן¿½?" ן¿½"ן¿½'ן¿½"׳¨ן¿½.׳× ׳¡ן¿½Tן¿½>ן¿½.ן¿½Y ׳-ן¿½T׳©ן¿½Tן¿½.׳×\n"
            f"ן¿½YZן¿½ <b>ן¿½'ן¿½.׳ ן¿½.׳¡ן¿½T׳</b> ן¿½?" ן¿½z׳©ן¿½-׳§ן¿½T׳ + ZVK\n"
            f"ן¿½Y'ן¿½ <b>ן¿½"ן¿½-ן¿½zן¿½Y</b> ן¿½?" +5 ZVK + ׳¢ן¿½zן¿½oן¿½.׳× 10 ן¿½"ן¿½.׳¨ן¿½.׳×\n"
            f"ן¿½Yן¿½ן¿½ <b>ן¿½-׳ ן¿½.׳× ׳§ן¿½"ן¿½Tן¿½o׳×ן¿½T׳×</b> ן¿½?" ן¿½zן¿½>ן¿½.׳¨/׳§׳ ן¿½" ן¿½'ן¿½z׳¢׳¨ן¿½>׳×\n"
            f"ן¿½Y"ן¿½ <b>ן¿½'ן¿½oן¿½.ן¿½' ן¿½Tן¿½.ן¿½zן¿½T</b> ן¿½?" ן¿½zן¿½" ן¿½-ן¿½"׳© ן¿½"ן¿½Tן¿½.׳\n"
            f"ן¿½YZ" <b>׳-׳§ן¿½"ן¿½zן¿½Tן¿½"</b> ן¿½?" ן¿½zן¿½"׳¨ן¿½Tן¿½>ן¿½T׳ ן¿½.׳§ן¿½.׳¨׳¡ן¿½T׳\n\n"
            f"<code>ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½</code>\n"
            f"ן¿½Y'ן¿½ <b>SLH Investment House</b>\n"
            f"ן¿½sן¿½ <i>Powered by SPARK IND</i>\n"
            f"ן¿½Y?ן¿½ן¿½Y?ן¿½ <i>Built in Israel ֲ· 2026</i>"
        )
        # Inline keyboard with direct website button
        inline_kb = {
            "inline_keyboard": [
                [{"text": "ן¿½YOן¿½ ן¿½"ן¿½Tן¿½>׳ ׳¡ ן¿½o׳-׳×׳¨ ן¿½"׳-ן¿½T׳©ן¿½T", "url": login_url}],
                [
                    {"text": "ן¿½Yן¿½ן¿½ ן¿½-׳ ן¿½.׳×", "url": "https://slh-nft.com/community.html"},
                    {"text": "ן¿½Y"ן¿½ ן¿½'ן¿½oן¿½.ן¿½'", "url": "https://slh-nft.com/daily-blog.html"},
                ],
                [
                    {"text": "ן¿½YZן¿½ ן¿½"ן¿½-ן¿½zן¿½Y ן¿½-ן¿½'׳¨ן¿½T׳", "url": "https://slh-nft.com/invite.html"},
                    {"text": "ן¿½Y"- ן¿½zן¿½"׳¨ן¿½Tן¿½>ן¿½T׳", "url": "https://slh-nft.com/guides.html"},
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
        self.send(chat_id, "ן¿½Y'? <i>׳×׳₪׳¨ן¿½Tן¿½~ ן¿½zן¿½"ן¿½T׳¨:</i>", self.main_reply_keyboard())

    def handle_prices(self, chat_id):
        prices = fetch_prices()
        now = datetime.now()
        ts = now.strftime("%H:%M %d/%m/%Y")

        if not prices:
            self.send(chat_id, "ן¿½Y"S <b>ן¿½zן¿½-ן¿½T׳¨ן¿½T׳ ן¿½-ן¿½Tן¿½T׳</b>\nן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\nג³ ן¿½~ן¿½.׳¢ן¿½Y ן¿½zן¿½-ן¿½T׳¨ן¿½T׳...\n׳ ׳¡ן¿½" ׳©ן¿½.ן¿½' ן¿½'׳¢ן¿½.ן¿½" ׳¨ן¿½'׳¢.",
                      self.main_reply_keyboard())
            return

        top = ["BTC", "ETH", "TON", "BNB", "SOL"]
        alts = ["DOGE", "XRP", "ADA", "DOT", "AVAX", "LINK"]

        text = "ן¿½Y"S <b>ן¿½zן¿½-ן¿½T׳¨ן¿½T׳ ן¿½-ן¿½Tן¿½T׳</b>\nן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\nן¿½Y'' <b>ן¿½zן¿½~ן¿½'׳¢ן¿½.׳× ן¿½zן¿½.ן¿½'ן¿½Tן¿½oן¿½.׳×:</b>\n"
        for coin in top:
            if coin in prices:
                p = prices[coin]
                info = COINS[coin]
                text += f"  {info['emoji']} {coin}: ${p['usd']:,.2f} | {p['ils']:,.1f}ן¿½,ן¿½\n"

        text += "\nן¿½Y'ן¿½ <b>Altcoins:</b>\n"
        for coin in alts:
            if coin in prices:
                p = prices[coin]
                info = COINS[coin]
                text += f"  {info['emoji']} {coin}: ${p['usd']:.4f} | {p['ils']:.2f}ן¿½,ן¿½\n"

        ton_price = prices.get("TON", {})
        if ton_price:
            text += f"\nן¿½Y'ן¿½ 1 TON = {ton_price['ils']}ן¿½,ן¿½ | ${ton_price['usd']}\n"

        text += f"\nג° {ts}\n\nן¿½Y'ן¿½ SLH Investment House"
        self.send(chat_id, text, self.main_reply_keyboard())

    def wallet_inline_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "ן¿½Y"ן¿½ ן¿½"׳₪׳§ן¿½"ן¿½"", "callback_data": "wallet_deposit"}, {"text": "ן¿½Y"ן¿½ ׳©ן¿½oן¿½-", "callback_data": "wallet_send"}],
            [{"text": "ן¿½Y"o ן¿½"ן¿½T׳¡ן¿½~ן¿½.׳¨ן¿½Tן¿½"", "callback_data": "wallet_history"}, {"text": "ן¿½Y"" ׳¨׳¢׳ ן¿½Y", "callback_data": "wallet_refresh"}],
            [{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½" ן¿½o׳×׳₪׳¨ן¿½Tן¿½~", "callback_data": "menu_main"}],
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

        # ן¿½"?ן¿½"? Try real blockchain wallet ן¿½"?ן¿½"?
        if self._wallet_ready and self.wallet:
            try:
                portfolio = self._run_async(self.wallet.get_user_portfolio(chat_id), timeout=12)
                if "error" not in portfolio:
                    bal = portfolio["balances"]
                    usd = portfolio["usd_values"]
                    prices = portfolio.get("prices", {})
                    bsc_addr = portfolio.get("bsc_address", "ן¿½?"")

                    text = (
                        f"ן¿½Y'ן¿½ <b>׳-׳¨׳ ׳§ SLH</b>\n"
                        f"ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½\n\n"
                        f"ן¿½Y'Z <b>SLH:</b> {bal['SLH']}\n"
                        f"ן¿½YYן¿½ <b>BNB:</b> {bal['BNB']}\n"
                        f"ן¿½Y'ן¿½ <b>TON:</b> {bal['TON']}\n"
                        f"ן¿½YZן¿½ <b>ZVK:</b> {bal['ZVK']}\n\n"
                        f"ן¿½Y'ן¿½ <b>׳©ן¿½.ן¿½.ן¿½T ן¿½'ן¿½"ן¿½.ן¿½o׳¨:</b>\n"
                        f"  SLH: ${usd.get('SLH', 0):,.2f}\n"
                        f"  BNB: ${usd.get('BNB', 0):,.2f}\n"
                        f"  TON: ${usd.get('TON', 0):,.2f}\n"
                        f"  ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n"
                        f"  ן¿½Y'ן¿½ ׳¡ן¿½"\"ן¿½>: <b>${usd.get('total', 0):,.2f}</b>\n\n"
                        f"ן¿½Y"- <b>ן¿½>׳×ן¿½.ן¿½'׳× BSC:</b>\n<code>{bsc_addr}</code>\n\n"
                        f"ן¿½Y'ן¿½ <b>׳₪׳§ן¿½.ן¿½"ן¿½.׳×:</b>\n"
                        f"/deposit_address ן¿½?" ן¿½>׳×ן¿½.ן¿½'׳× ן¿½"׳₪׳§ן¿½"ן¿½"\n"
                        f"/send_slh USER_ID AMOUNT ן¿½?" ׳©ן¿½oן¿½- SLH\n"
                        f"/send_ton USER_ID AMOUNT ן¿½?" ׳©ן¿½oן¿½- TON\n"
                        f"/tx_history ן¿½?" ן¿½"ן¿½T׳¡ן¿½~ן¿½.׳¨ן¿½Tן¿½T׳× ׳¢׳¡׳§׳-ן¿½.׳×\n"
                        f"/verify TX_HASH CHAIN ן¿½?" ׳-ן¿½z׳× ן¿½"׳₪׳§ן¿½"ן¿½""
                    )
                    if message_id:
                        self.edit_message(chat_id, message_id, text, self.wallet_inline_keyboard())
                    else:
                        self.send(chat_id, text, self.wallet_inline_keyboard())
                    return
            except Exception as e:
                logger.warning(f"Wallet fetch failed for {chat_id}: {e}")

        # ן¿½"?ן¿½"? Fallback to in-memory ן¿½"?ן¿½"?
        ton_total = user["ton_available"] + user["ton_locked"]
        text = (
            f"ן¿½Y'ן¿½ <b>׳-׳¨׳ ׳§</b>\n"
            f"ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
            f"ן¿½Y'Z SLH: {user['slh_balance']:.4f}\n"
            f"ן¿½YZן¿½ ZVK: {user['zvk_balance']}\n\n"
            f"ן¿½Yן¿½ן¿½ <b>ן¿½-׳©ן¿½'ן¿½.ן¿½Y ן¿½'׳ ׳§:</b>\n"
            f"  ן¿½Y'ן¿½ ן¿½-ן¿½zן¿½Tן¿½Y: {user['ton_available']:.4f} TON\n"
            f"  ן¿½Y"' ׳ ׳¢ן¿½.ן¿½o: {user['ton_locked']:.4f} TON\n"
            f"  ן¿½Y'ן¿½ ׳¡ן¿½"\"ן¿½>: {ton_total:.4f} TON\n\n"
            f"ן¿½sן¿½ן¸ <i>׳-׳¨׳ ׳§ blockchain ן¿½z׳×ן¿½-ן¿½'׳¨... ׳ ׳¡ן¿½" ׳©ן¿½.ן¿½' ן¿½'׳¢ן¿½.ן¿½" ׳¨ן¿½'׳¢</i>\n\n"
            f"ן¿½Y'ן¿½ <b>׳₪׳§ן¿½.ן¿½"ן¿½.׳×:</b>\n"
            f"/deposit - ן¿½"׳₪׳§ן¿½"ן¿½" ן¿½-ן¿½"׳©ן¿½"\n"
            f"/send_slh USER_ID AMOUNT ן¿½?" ׳©ן¿½oן¿½- SLH\n"
            f"/tx_history ן¿½?" ן¿½"ן¿½T׳¡ן¿½~ן¿½.׳¨ן¿½Tן¿½T׳× ׳¢׳¡׳§׳-ן¿½.׳×"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.wallet_inline_keyboard())
        else:
            self.send(chat_id, text, self.wallet_inline_keyboard())

    # ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½
    # BLOCKCHAIN WALLET HANDLERS (wallet_engine integration)
    # ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½

    def handle_deposit_address(self, chat_id):
        """Generate and show deposit addresses for BSC + TON."""
        if not self._wallet_ready:
            self.send(chat_id, "ן¿½sן¿½ן¸ ן¿½z׳¢׳¨ן¿½>׳× ן¿½"׳-׳¨׳ ׳§ן¿½T׳ ן¿½z׳×ן¿½-ן¿½'׳¨׳×... ׳ ׳¡ן¿½" ׳©ן¿½.ן¿½' ן¿½'׳¢ן¿½.ן¿½" ׳¨ן¿½'׳¢.", self.main_reply_keyboard())
            return
        try:
            addrs = self._run_async(self.wallet.generate_deposit_address(chat_id))
            text = (
                f"ן¿½Y"ן¿½ <b>ן¿½>׳×ן¿½.ן¿½'ן¿½.׳× ן¿½"׳₪׳§ן¿½"ן¿½"</b>\n"
                f"ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½\n\n"
                f"ן¿½YYן¿½ <b>BSC (BNB / SLH Token):</b>\n"
                f"<code>{addrs['bsc_address']}</code>\n\n"
                f"ן¿½Y'ן¿½ <b>TON:</b>\n"
                f"<code>{addrs['ton_address']}</code>\n"
                f"ן¿½Y"ן¿½ <b>Memo:</b> <code>{addrs['memo']}</code>\n\n"
                f"ן¿½sן¿½ן¸ <b>ן¿½-׳©ן¿½.ן¿½':</b>\n"
                f"ן¿½?ן¿½ BSC ן¿½?" ׳©ן¿½oן¿½- BNB ׳-ן¿½. SLH Token ן¿½oן¿½>׳×ן¿½.ן¿½'׳× ן¿½oן¿½z׳¢ן¿½oן¿½"\n"
                f"ן¿½?ן¿½ TON ן¿½?" ׳©ן¿½oן¿½- TON ן¿½oן¿½>׳×ן¿½.ן¿½'׳× + ן¿½"ן¿½.׳¡׳£ ׳-׳× ן¿½"-Memo\n"
                f"ן¿½?ן¿½ ׳-ן¿½-׳¨ן¿½T ן¿½"׳©ן¿½oן¿½Tן¿½-ן¿½": /verify TX_HASH bsc (׳-ן¿½. ton)\n\n"
                f"ן¿½Y'ן¿½ <i>ן¿½"ן¿½"׳₪׳§ן¿½"ן¿½" ׳×ן¿½Tן¿½-׳§׳£ ׳-ן¿½.ן¿½~ן¿½.ן¿½zן¿½~ן¿½T׳× ׳-ן¿½-׳¨ן¿½T ׳-ן¿½Tן¿½zן¿½.׳×</i>"
            )
            self.send(chat_id, text, self.wallet_inline_keyboard())
        except Exception as e:
            logger.error(f"Deposit address error: {e}")
            self.send(chat_id, "ן¿½O ׳©ן¿½'ן¿½T׳-ן¿½" ן¿½'ן¿½T׳¦ן¿½T׳¨׳× ן¿½>׳×ן¿½.ן¿½'׳×. ׳ ׳¡ן¿½" ׳©ן¿½.ן¿½'.", self.main_reply_keyboard())

    def handle_verify_deposit(self, chat_id, args):
        """Verify a deposit tx on-chain: /verify TX_HASH bsc|ton"""
        if not self._wallet_ready:
            self.send(chat_id, "ן¿½sן¿½ן¸ ן¿½z׳¢׳¨ן¿½>׳× ן¿½"׳-׳¨׳ ׳§ן¿½T׳ ן¿½z׳×ן¿½-ן¿½'׳¨׳×...", self.main_reply_keyboard())
            return
        parts = args.strip().split()
        if len(parts) < 2:
            self.send(chat_id,
                "ן¿½Y"< <b>׳-ן¿½Tן¿½zן¿½.׳× ן¿½"׳₪׳§ן¿½"ן¿½"</b>\n\n"
                "׳©ן¿½Tן¿½zן¿½.׳©: /verify TX_HASH CHAIN\n\n"
                "ן¿½"ן¿½.ן¿½'ן¿½zן¿½" BSC:\n<code>/verify 0xabc123... bsc</code>\n\n"
                "ן¿½"ן¿½.ן¿½'ן¿½zן¿½" TON:\n<code>/verify abc123... ton</code>",
                self.main_reply_keyboard())
            return

        tx_hash = parts[0]
        chain = parts[1].lower()
        if chain not in ("bsc", "ton"):
            self.send(chat_id, "ן¿½O Chain ן¿½-ן¿½Tן¿½Tן¿½' ן¿½oן¿½"ן¿½Tן¿½.׳× bsc ׳-ן¿½. ton", self.main_reply_keyboard())
            return

        self.send(chat_id, f"ג³ ן¿½z׳-ן¿½z׳× ׳¢׳¡׳§ן¿½" ׳¢ן¿½o {chain.upper()}...", self.main_reply_keyboard())
        try:
            result = self._run_async(self.wallet.process_deposit(chat_id, tx_hash, chain), timeout=20)
            if "error" in result:
                self.send(chat_id, f"ן¿½O {result['error']}", self.wallet_inline_keyboard())
            else:
                self.send(chat_id,
                    f"ן¿½o. <b>ן¿½"׳₪׳§ן¿½"ן¿½" ׳-ן¿½.ן¿½z׳×ן¿½"!</b>\n\n"
                    f"ן¿½Y'ן¿½ ׳¡ן¿½>ן¿½.׳: <b>{result['amount']} {result['token']}</b>\n"
                    f"ן¿½Y"- Chain: {result['chain'].upper()}\n"
                    f"ן¿½Y"ן¿½ ID: #{result['deposit_id']}\n\n"
                    f"ן¿½"ן¿½T׳×׳¨ן¿½" ׳¢ן¿½.ן¿½"ן¿½>׳ ן¿½". /wallet ן¿½o׳¦׳₪ן¿½Tן¿½Tן¿½"",
                    self.wallet_inline_keyboard())
                # Notify admin
                if str(chat_id) != ADMIN_ID:
                    user = _get_user(chat_id)
                    self.send(int(ADMIN_ID),
                        f"ן¿½Y'ן¿½ <b>ן¿½"׳₪׳§ן¿½"ן¿½" ן¿½-ן¿½"׳©ן¿½"!</b>\n"
                        f"ן¿½Y'ן¿½ @{user['username']} ({chat_id})\n"
                        f"ן¿½Y'ן¿½ {result['amount']} {result['token']} ({chain.upper()})\n"
                        f"ן¿½Y"- TX: <code>{tx_hash[:30]}...</code>")
        except Exception as e:
            logger.error(f"Verify deposit error: {e}")
            self.send(chat_id, "ן¿½O ׳©ן¿½'ן¿½T׳-ן¿½" ן¿½'׳-ן¿½Tן¿½zן¿½.׳×. ׳ ׳¡ן¿½" ׳©ן¿½.ן¿½'.", self.main_reply_keyboard())

    def handle_send_internal(self, chat_id, args, token="SLH"):
        """Internal transfer: /send_slh USER_ID AMOUNT ן¿½?" uses bot-transfer API directly."""
        parts = args.strip().split()
        if len(parts) < 2:
            self.send(chat_id,
                f"ן¿½Y"ן¿½ <b>ן¿½"׳¢ן¿½'׳¨׳× {token}</b>\n\n"
                f"׳©ן¿½Tן¿½zן¿½.׳©: /send_{token.lower()} USER_ID AMOUNT\n\n"
                f"ן¿½"ן¿½.ן¿½'ן¿½zן¿½":\n<code>/send_{token.lower()} 123456789 10</code>\n\n"
                f"ן¿½Y'ן¿½ ן¿½"-USER_ID ׳©ן¿½o ן¿½"׳ ן¿½z׳¢ן¿½Y: ן¿½'׳§׳© ן¿½zן¿½z׳ ן¿½. ן¿½o׳©ן¿½oן¿½.ן¿½- /myid\n"
                f"ן¿½Y'ן¿½ ׳-ן¿½. ן¿½"׳©׳×ן¿½z׳© ן¿½'׳×׳₪׳¨ן¿½Tן¿½~: ן¿½Y"" P2P ן¿½z׳¡ן¿½-׳¨",
                self.main_reply_keyboard())
            return
        try:
            to_user = int(parts[0])
            amount  = float(parts[1])
        except (ValueError, IndexError):
            self.send(chat_id, "ן¿½O ׳₪ן¿½.׳¨ן¿½zן¿½~ ׳©ן¿½'ן¿½.ן¿½T. ׳©ן¿½oן¿½- USER_ID ן¿½.׳-ן¿½- ׳¡ן¿½>ן¿½.׳.", self.main_reply_keyboard())
            return

        if to_user == chat_id:
            self.send(chat_id, "ן¿½O ׳-ן¿½T ׳-׳₪׳©׳¨ ן¿½o׳©ן¿½oן¿½.ן¿½- ן¿½o׳¢׳¦ן¿½zן¿½s", self.main_reply_keyboard())
            return

        # Use bot-transfer API (no JWT needed)
        self._p2p_execute_send(chat_id, {"token": token, "to_user": to_user, "amount": amount})

    def handle_tx_history(self, chat_id):
        """Show transaction history from DB."""
        if not self._wallet_ready:
            self.send(chat_id, "ן¿½sן¿½ן¸ ן¿½z׳¢׳¨ן¿½>׳× ן¿½"׳-׳¨׳ ׳§ן¿½T׳ ן¿½z׳×ן¿½-ן¿½'׳¨׳×...", self.main_reply_keyboard())
            return
        try:
            history = self._run_async(self.wallet.get_transaction_history(chat_id, limit=10))
            if not history:
                self.send(chat_id, "ן¿½Y"o <b>ן¿½"ן¿½T׳¡ן¿½~ן¿½.׳¨ן¿½Tן¿½T׳× ׳¢׳¡׳§׳-ן¿½.׳×</b>\n\n׳-ן¿½Tן¿½Y ׳¢׳¡׳§׳-ן¿½.׳× ׳¢ן¿½"ן¿½Tן¿½Tן¿½Y.", self.wallet_inline_keyboard())
                return
            text = "ן¿½Y"o <b>ן¿½"ן¿½T׳¡ן¿½~ן¿½.׳¨ן¿½Tן¿½T׳× ׳¢׳¡׳§׳-ן¿½.׳× (10 ׳-ן¿½-׳¨ן¿½.׳ ן¿½.׳×)</b>\nן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½\n\n"
            for tx in history:
                direction = "ן¿½Y"ן¿½" if tx["from_user_id"] == chat_id else "ן¿½Y"ן¿½"
                other = tx["to_user_id"] if tx["from_user_id"] == chat_id else tx["from_user_id"]
                dt = tx["created_at"][:16].replace("T", " ") if tx["created_at"] else "ן¿½?""
                text += (
                    f"{direction} <b>{tx['amount']} {tx['token']}</b> "
                    f"{'ן¿½?'' if direction == 'ן¿½Y"ן¿½' else 'ן¿½?ן¿½'} {other or 'system'} "
                    f"| {tx['type']} | {dt}\n"
                )
            self.send(chat_id, text, self.wallet_inline_keyboard())
        except Exception as e:
            logger.error(f"TX history error: {e}")
            self.send(chat_id, "ן¿½O ׳©ן¿½'ן¿½T׳-ן¿½" ן¿½'ן¿½~׳¢ן¿½T׳ ׳× ן¿½"ן¿½T׳¡ן¿½~ן¿½.׳¨ן¿½Tן¿½".", self.main_reply_keyboard())

    def handle_onchain_balance(self, chat_id):
        """Read on-chain balance for the ecosystem master wallets."""
        if not self._wallet_ready:
            self.send(chat_id, "ן¿½sן¿½ן¸ ן¿½z׳¢׳¨ן¿½>׳× ן¿½"׳-׳¨׳ ׳§ן¿½T׳ ן¿½z׳×ן¿½-ן¿½'׳¨׳×...", self.main_reply_keyboard())
            return
        try:
            self.send(chat_id, "ג³ ׳§ן¿½.׳¨׳- ן¿½T׳×׳¨ן¿½.׳× ן¿½zן¿½"-blockchain...", self.main_reply_keyboard())
            slh_bal = self._run_async(self.wallet.get_slh_balance(BSC_CONTRACT), timeout=15)
            ton_bal = self._run_async(self.wallet.get_ton_balance(TON_WALLET), timeout=15)
            prices = self._run_async(self.wallet.get_live_prices())
            text = (
                f"ן¿½Y"- <b>ן¿½T׳×׳¨ן¿½.׳× On-Chain</b>\n"
                f"ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½\n\n"
                f"ן¿½Y'Z <b>SLH Token (BSC):</b>\n"
                f"  Contract: <code>{BSC_CONTRACT[:20]}...</code>\n"
                f"  ן¿½T׳×׳¨ן¿½": {slh_bal}\n\n"
                f"ן¿½Y'ן¿½ <b>TON Wallet:</b>\n"
                f"  ן¿½>׳×ן¿½.ן¿½'׳×: <code>{TON_WALLET[:20]}...</code>\n"
                f"  ן¿½T׳×׳¨ן¿½": {ton_bal} TON\n\n"
                f"ן¿½Y"S <b>ן¿½zן¿½-ן¿½T׳¨ן¿½T׳:</b>\n"
                f"  BTC: ${prices.get('btc_usd', 0):,.0f}\n"
                f"  ETH: ${prices.get('eth_usd', 0):,.0f}\n"
                f"  TON: ${prices.get('ton_usd', 0):.2f}\n"
                f"  BNB: ${prices.get('bnb_usd', 0):,.0f}\n"
                f"  SLH: {prices.get('slh_ils', 444)}ן¿½,ן¿½ (${prices.get('slh_usd', 0):.2f})"
            )
            self.send(chat_id, text, self.wallet_inline_keyboard())
        except Exception as e:
            logger.error(f"On-chain balance error: {e}")
            self.send(chat_id, "ן¿½O ׳©ן¿½'ן¿½T׳-ן¿½" ן¿½'׳§׳¨ן¿½T׳-ן¿½" ן¿½zן¿½"-blockchain.", self.main_reply_keyboard())

    def handle_investments(self, chat_id, message_id=None):
        text = "ן¿½Y'ן¿½ <b>׳×ן¿½.ן¿½>׳ ן¿½Tן¿½.׳× ן¿½"׳©׳§׳¢ן¿½"</b>\nן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
        for plan in INVESTMENT_PLANS:
            text += (
                f"{plan['name']}\n"
                f"  ן¿½Y'ן¿½ {plan['rate']}% ן¿½-ן¿½.ן¿½"׳©ן¿½T | {plan['annual']}% ׳©׳ ׳×ן¿½T\n"
                f"  ן¿½zן¿½T׳ ן¿½Tן¿½zן¿½.׳ {plan['min_ton']} TON | {plan['days']} ן¿½Tן¿½.׳\n\n"
            )
        text += (
            "ן¿½Y'ן¿½ <b>׳-ן¿½Tן¿½s ן¿½oן¿½"׳₪׳§ן¿½Tן¿½":</b>\n"
            "1. ן¿½'ן¿½-׳¨ ׳×ן¿½.ן¿½>׳ ן¿½T׳×\n"
            "2. ׳©ן¿½oן¿½- TON ן¿½z-@wallet\n"
            "3. ׳©ן¿½oן¿½- ׳¦ן¿½Tן¿½oן¿½.׳ ן¿½z׳¡ן¿½s\n"
            "4. ן¿½"׳₪׳§ן¿½"ן¿½.ן¿½Y ׳ ׳₪׳×ן¿½-!"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.invest_keyboard())
        else:
            self.send(chat_id, text, self.invest_keyboard())

    def handle_risk(self, chat_id):
        user = _get_user(chat_id)
        text = (
            f"ן¿½Y>ן¿½ <b>׳¡ן¿½Tן¿½>ן¿½.ן¿½Y ן¿½.ן¿½'׳§׳¨ן¿½"</b>\n"
            f"ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
            f"ן¿½Y'ן¿½ <b>ן¿½"ן¿½'ן¿½"׳¨ן¿½.׳× ן¿½"׳¡ן¿½Tן¿½>ן¿½.ן¿½Y ׳©ן¿½oן¿½s:</b>\n\n"
            f"ן¿½Ysן¿½ ן¿½"׳₪׳¡ן¿½" ן¿½Tן¿½.ן¿½zן¿½T: {user['risk_daily_loss']}%\n"
            f"ן¿½Y"S ׳₪ן¿½.ן¿½-ן¿½T׳¦ן¿½Tן¿½" ן¿½z׳§׳¡ן¿½Tן¿½zן¿½oן¿½T׳×: {user['risk_max_position']}%\n"
            f"ן¿½Y>' Stop Loss: {'ן¿½o. ׳₪׳¢ן¿½Tן¿½o' if user['risk_stop_loss'] else 'ן¿½O ן¿½>ן¿½'ן¿½.ן¿½T'}\n\n"
            f"ן¿½Y"ן¿½ <b>׳¢׳§׳¨ן¿½.׳ ן¿½.׳×:</b>\n"
            f"ן¿½?ן¿½ ן¿½o׳- ן¿½oן¿½"׳©׳§ן¿½T׳¢ ן¿½Tן¿½.׳×׳¨ ן¿½zן¿½zן¿½" ׳©ן¿½zן¿½.ן¿½>׳ ן¿½T׳ ן¿½oן¿½"׳₪׳¡ן¿½Tן¿½"\n"
            f"ן¿½?ן¿½ ן¿½oן¿½"׳₪׳¨ן¿½Tן¿½" ן¿½'ן¿½Tן¿½Y ן¿½z׳¡׳₪׳¨ ׳×ן¿½.ן¿½>׳ ן¿½Tן¿½.׳×\n"
            f"ן¿½?ן¿½ ן¿½o׳- ן¿½o׳©ן¿½T׳ ן¿½"ן¿½>ן¿½o ׳¢ן¿½o ׳§ן¿½o׳£ ׳-ן¿½-ן¿½"\n"
            f"ן¿½?ן¿½ ן¿½oן¿½"׳©׳-ן¿½T׳¨ ׳ ן¿½-ן¿½Tן¿½oן¿½.׳× ן¿½oן¿½z׳§׳¨ן¿½" ן¿½-ן¿½T׳¨ן¿½.׳\n\n"
            f"ן¿½Y>ן¿½ <b>ן¿½"ן¿½z׳¢׳¨ן¿½>׳× ׳©ן¿½.ן¿½z׳¨׳× ׳¢ן¿½oן¿½Tן¿½s!</b>"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_invite(self, chat_id):
        user = _get_user(chat_id)
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            f"ן¿½Y'ן¿½ <b>ן¿½"ן¿½-ן¿½zן¿½Y ן¿½-ן¿½'׳¨ן¿½T׳</b>\n\n"
            f"ן¿½Y"- <code>{ref_link}</code>\n\n"
            f"ן¿½"ן¿½-ן¿½z׳ ן¿½.׳×: {user['referral_count']} | +5 ZVK ן¿½oן¿½>ן¿½o ן¿½-ן¿½'׳¨"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_activate(self, chat_id):
        user = _get_user(chat_id)
        user["activated"] = True
        self.send(chat_id, "ן¿½o. ן¿½zן¿½.׳₪׳¢ן¿½o!", self.main_reply_keyboard())

    def handle_share(self, chat_id):
        user = _get_user(chat_id)
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            f"ן¿½Y'Z SLH - ן¿½'ן¿½T׳× ן¿½"׳©׳§׳¢ן¿½.׳× ן¿½"ן¿½Tן¿½'ן¿½Tן¿½~ן¿½oן¿½T\n\n"
            f"ן¿½o. ׳×׳©ן¿½.׳-ן¿½" 4% ן¿½-ן¿½.ן¿½"׳©ן¿½T / 65% ׳©׳ ׳×ן¿½T\n"
            f"ן¿½o. ׳-׳¨׳ ׳§ ן¿½zן¿½o׳- (TON/BNB/SLH)\n"
            f"ן¿½o. ן¿½"׳¢ן¿½'׳¨ן¿½.׳× ן¿½zן¿½Tן¿½Tן¿½"ן¿½Tן¿½.׳× + blockchain\n"
            f"ן¿½o. ׳ ן¿½T׳×ן¿½.ן¿½- ׳©ן¿½.׳§ + ׳¡ן¿½Tן¿½'׳ ן¿½oן¿½T׳\n"
            f"ן¿½YZן¿½ +100 ZVK ן¿½z׳×׳ ן¿½"!\n\n"
            f"ן¿½Y'ן¿½ 22.221ן¿½,ן¿½ ן¿½'ן¿½oן¿½'ן¿½"!\n"
            f"ן¿½Y'? {ref_link}\n\n"
            f"ן¿½Y'ן¿½ SPARK IND | SLH Ecosystem"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_guides(self, chat_id):
        text = (
            "ן¿½Y"s <b>ן¿½zן¿½"׳¨ן¿½Tן¿½>ן¿½T׳</b>\n"
            "ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
            "ן¿½Y"- <b>ן¿½zן¿½"׳¨ן¿½Tן¿½>ן¿½T SLH:</b>\n"
            "ן¿½?ן¿½ <a href='https://slh-nft.com/guides.html'>ן¿½zן¿½"׳¨ן¿½Tן¿½s ן¿½zן¿½o׳- ן¿½'׳-׳×׳¨</a>\n\n"
            "ן¿½Y"< <b>׳ ן¿½.׳©׳-ן¿½T׳:</b>\n"
            "1ן¸ן¿½fן¿½ ׳-ן¿½Tן¿½s ן¿½oן¿½"׳×ן¿½-ן¿½Tן¿½o ׳¢׳ SLH\n"
            "2ן¸ן¿½fן¿½ ׳-ן¿½Tן¿½s ן¿½o׳₪׳×ן¿½.ן¿½- ׳-׳¨׳ ׳§ TON\n"
            "3ן¸ן¿½fן¿½ ׳-ן¿½Tן¿½s ן¿½oן¿½"׳₪׳§ן¿½Tן¿½" ן¿½.ן¿½oן¿½"׳©׳§ן¿½T׳¢\n"
            "4ן¸ן¿½fן¿½ ׳-ן¿½Tן¿½s ן¿½oן¿½"׳©׳×ן¿½z׳© ן¿½'׳¡ן¿½.ן¿½.׳-׳₪\n"
            "5ן¸ן¿½fן¿½ ן¿½zן¿½"׳¨ן¿½Tן¿½s ׳-ן¿½'ן¿½~ן¿½-ן¿½"\n"
            "6ן¸ן¿½fן¿½ ׳©׳-ן¿½oן¿½.׳× ׳ ׳₪ן¿½.׳¦ן¿½.׳×\n\n"
            "ן¿½Y'ן¿½ ן¿½oן¿½>ן¿½o ׳©׳-ן¿½oן¿½": /support"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_bonuses(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        text = (
            f"ן¿½YZן¿½ <b>ן¿½'ן¿½.׳ ן¿½.׳¡ן¿½T׳</b> | ZVK: {user['zvk_balance']}\n"
            f"ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
            f"ן¿½>ן¿½o ן¿½z׳©ן¿½-׳§ = 1 ZVK\n"
            f"ן¿½YZן¿½ ׳¡ן¿½oן¿½.ן¿½~ן¿½T׳: ׳₪׳¨׳¡ ן¿½'ן¿½"ן¿½.ן¿½o ׳¢ן¿½" 25 ZVK!\n"
            f"ן¿½YZן¿½ ׳§ן¿½.ן¿½'ן¿½Tן¿½.׳×: 6=5 ZVK, 4-5=2 ZVK\n"
            f"ן¿½Yן¿½? ן¿½>ן¿½"ן¿½.׳¨׳¡ן¿½o: 4+=3 ZVK\n"
            f"ן¿½YZן¿½ ן¿½-׳¦ן¿½T׳: 6=5 ZVK, 4-5=2 ZVK\n\n"
            f"ן¿½Y'ן¿½ 10 ZVK = 1 TON | 50 = 4 | 100 = 7"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.games_keyboard())
        else:
            self.send(chat_id, text, self.games_keyboard())

    def handle_game(self, chat_id, game_type, callback_id, message_id):
        user = _get_user(chat_id)
        if user["zvk_balance"] < 1:
            self.answer_callback(callback_id, "ן¿½O ׳-ן¿½Tן¿½Y ן¿½z׳¡׳₪ן¿½T׳§ ZVK!", True)
            return

        user["zvk_balance"] -= 1
        user["games_played"] += 1

        if game_type == "slots":
            symbols = ["ן¿½Yן¿½'", "ן¿½Yן¿½<", "ן¿½Yן¿½S", "ן¿½Y'Z", "7ן¸ן¿½fן¿½", "ן¿½Y"""]
            s1, s2, s3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)
            if s1 == s2 == s3:
                win = 25 if s1 == "ן¿½Y'Z" else 15
                user["zvk_balance"] += win
                user["games_won"] += 1
                result = f"ן¿½YZן¿½ {s1}{s2}{s3}\n\nן¿½YZ? ן¿½''׳§׳₪ן¿½.ן¿½~! +{win} ZVK!"
            elif s1 == s2 or s2 == s3:
                win = 3
                user["zvk_balance"] += win
                user["games_won"] += 1
                result = f"ן¿½YZן¿½ {s1}{s2}{s3}\n\nן¿½YZ? ׳ ן¿½T׳¦ן¿½-׳×! +{win} ZVK!"
            else:
                result = f"ן¿½YZן¿½ {s1}{s2}{s3}\n\nן¿½O ן¿½o׳- ן¿½"׳₪׳¢׳"
        elif game_type == "dice":
            roll = random.randint(1, 6)
            if roll == 6:
                user["zvk_balance"] += 5
                user["games_won"] += 1
                result = f"ן¿½YZן¿½ {roll}\n\nן¿½YZ? ן¿½zן¿½.׳©ן¿½o׳! +5 ZVK!"
            elif roll >= 4:
                user["zvk_balance"] += 2
                user["games_won"] += 1
                result = f"ן¿½YZן¿½ {roll}\n\nן¿½YZ? ׳ ן¿½T׳¦ן¿½-׳×! +2 ZVK!"
            else:
                result = f"ן¿½YZן¿½ {roll}\n\nן¿½O ן¿½o׳- ן¿½"׳₪׳¢׳"
        elif game_type == "basketball":
            score = random.randint(1, 6)
            if score >= 4:
                user["zvk_balance"] += 3
                user["games_won"] += 1
                result = f"ן¿½Yן¿½? {score} ׳ ׳§ן¿½.ן¿½"ן¿½.׳×!\n\nן¿½YZ? ׳ ן¿½T׳¦ן¿½-׳×! +3 ZVK!"
            else:
                result = f"ן¿½Yן¿½? {score} ׳ ׳§ן¿½.ן¿½"ן¿½.׳×\n\nן¿½O ן¿½o׳- ן¿½"׳₪׳¢׳"
        elif game_type == "darts":
            score = random.randint(1, 6)
            if score == 6:
                user["zvk_balance"] += 5
                user["games_won"] += 1
                result = f"ן¿½YZן¿½ ן¿½z׳¨ן¿½>ן¿½-! {score}\n\nן¿½YZ? ׳ ן¿½T׳¦ן¿½-׳×! +5 ZVK!"
            elif score >= 4:
                user["zvk_balance"] += 2
                user["games_won"] += 1
                result = f"ן¿½YZן¿½ {score}\n\nן¿½YZ? ׳ ן¿½T׳¦ן¿½-׳×! +2 ZVK!"
            else:
                result = f"ן¿½YZן¿½ {score}\n\nן¿½O ן¿½o׳- ן¿½"׳₪׳¢׳"
        else:
            result = "ן¿½""

        result += f"\nן¿½YZן¿½ ZVK: {user['zvk_balance']}"
        self.edit_message(chat_id, message_id, result, self.games_keyboard())
        self.answer_callback(callback_id)

    def handle_game_convert(self, chat_id, callback_id, message_id):
        text = (
            "ן¿½Y'ן¿½ <b>ן¿½"ן¿½z׳¨׳× ZVK ן¿½?' TON</b>\n\n"
            "10 ZVK = 1 TON\n"
            "50 ZVK = 4 TON\n"
            "100 ZVK = 7 TON\n\n"
            f"׳©ן¿½oן¿½- ן¿½o:\n<code>{TON_WALLET}</code>"
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
            f"ן¿½Y"S <b>ן¿½"׳©ן¿½'ן¿½.׳¨ן¿½"</b>\n"
            f"ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
            f"ן¿½Yן¿½ן¿½ <b>ן¿½-׳©ן¿½'ן¿½.ן¿½Y ן¿½'׳ ׳§:</b>\n"
            f"  ן¿½Y'ן¿½ ן¿½-ן¿½zן¿½Tן¿½Y: {user['ton_available']:.4f} TON\n"
            f"  ן¿½Y"' ׳ ׳¢ן¿½.ן¿½o: {user['ton_locked']:.4f} TON\n"
            f"  ן¿½Y'ן¿½ ׳¡ן¿½"\"ן¿½>: {ton_total:.4f} TON\n\n"
            f"ן¿½Y'ן¿½ ן¿½"׳©׳§׳¢ן¿½.׳× ׳₪׳¢ן¿½Tן¿½oן¿½.׳×: {active_deposits}\n"
            f"ג³ ן¿½zן¿½z׳×ן¿½T׳ ן¿½.׳× ן¿½o׳-ן¿½T׳©ן¿½.׳¨: {pending_deposits}\n"
            f"ן¿½Y'ן¿½ ן¿½zן¿½.׳©׳§׳¢: {invested:.2f} TON\n"
            f"ן¿½Y"^ ׳¨ן¿½.ן¿½.ן¿½-: +{profit:.4f} TON\n\n"
            f"ן¿½YZן¿½ ZVK: {user['zvk_balance']} | ן¿½z׳©ן¿½-׳§ן¿½T׳: {user['games_played']} ({win_rate}%)\n"
            f"ן¿½Y'ן¿½ ן¿½"ן¿½-ן¿½z׳ ן¿½.׳×: {user['referral_count']}\n\n"
            f"SLH Investment House"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_swap_text(self, chat_id):
        text = (
            "ן¿½Y"" <b>SLH Swap ן¿½?" ן¿½"ן¿½z׳¨׳× ן¿½zן¿½~ן¿½'׳¢ן¿½.׳×</b>\n\n"
            "ן¿½"ן¿½zן¿½T׳¨ן¿½. ן¿½'ן¿½Tן¿½Y 4,500+ ן¿½zן¿½~ן¿½'׳¢ן¿½.׳× ׳§׳¨ן¿½T׳₪ן¿½~ן¿½. ן¿½'׳§ן¿½oן¿½.׳×!\n\n"
            "ן¿½Y'ן¿½ <b>ן¿½T׳×׳¨ן¿½.׳ ן¿½.׳×:</b>\n"
            "ן¿½?ן¿½ ן¿½oן¿½o׳- ן¿½"׳¨׳©ן¿½zן¿½"\n"
            "ן¿½?ן¿½ ׳¢ן¿½zן¿½oן¿½.׳× ׳ ן¿½zן¿½.ן¿½>ן¿½.׳×\n"
            "ן¿½?ן¿½ ן¿½"ן¿½z׳¨ן¿½" ן¿½T׳©ן¿½T׳¨ן¿½" ן¿½z׳-׳¨׳ ׳§ ן¿½o׳-׳¨׳ ׳§\n"
            "ן¿½?ן¿½ ׳×ן¿½zן¿½Tן¿½>ן¿½" ן¿½'-TON, BTC, ETH, BNB ן¿½.׳¢ן¿½.ן¿½"\n\n"
            "ן¿½Y"ן¿½ <b>ן¿½zן¿½'׳¦׳¢:</b> Cashback 0.5% ׳¢ן¿½o ן¿½>ן¿½o ׳¢׳¡׳§ן¿½"!\n\n"
            "ן¿½Y'? ן¿½oן¿½-׳¥ ן¿½oן¿½"׳×ן¿½-ן¿½oן¿½":"
        )
        kb = {"inline_keyboard": [
            [{"text": "ן¿½Y"" ן¿½"ן¿½z׳¨ ׳¢ן¿½>׳©ן¿½Tן¿½.", "url": f"https://letsexchange.io/?ref={LETSEXCHANGE_REF}"}],
            [{"text": "ן¿½Y'ן¿½ TON ן¿½?' USDT", "url": f"https://letsexchange.io/?from=TON&to=USDT&ref={LETSEXCHANGE_REF}"}],
            [{"text": "ן¿½Y'ן¿½ BTC ן¿½?' TON", "url": f"https://letsexchange.io/?from=BTC&to=TON&ref={LETSEXCHANGE_REF}"}],
        ]}
        self.send(chat_id, text, kb)

    def handle_ai_analysis(self, chat_id):
        prices = fetch_prices()
        btc = prices.get("BTC", {}).get("usd", 67000)
        text = (
            f"ן¿½Yן¿½ן¿½ <b>׳ ן¿½T׳×ן¿½.ן¿½- AI</b>\n"
            f"ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
            f"ן¿½Y"^ <b>׳×׳¨ן¿½-ן¿½T׳© ׳©ן¿½.׳¨ן¿½T:</b> ׳-׳ BTC ׳©ן¿½.ן¿½'׳¨ ${int(btc/1000)*1000+3000:,}, ׳¦׳₪ן¿½.ן¿½T ן¿½zן¿½"ן¿½oן¿½s ן¿½o-${int(btc/1000)*1000+8000:,}\n\n"
            f"ן¿½Y"ן¿½ <b>׳×׳¨ן¿½-ן¿½T׳© ן¿½"ן¿½.ן¿½'ן¿½T:</b> ׳-׳ BTC ׳©ן¿½.ן¿½'׳¨ ${int(btc/1000)*1000-2000:,}, ׳-׳₪׳©׳¨ן¿½T ׳ ׳₪ן¿½Tן¿½oן¿½" ן¿½o-${int(btc/1000)*1000-7000:,}\n\n"
            f"ן¿½YYן¿½ <b>׳×׳¨ן¿½-ן¿½T׳© ׳ ן¿½Tן¿½Tן¿½~׳¨ן¿½oן¿½T:</b> ׳¦׳₪ן¿½.ן¿½T ן¿½"ן¿½-ן¿½T׳¡ן¿½" ׳¦ן¿½"ן¿½"ן¿½T׳×\n\n"
            f"ן¿½sן¿½ן¸ ן¿½-ן¿½" ן¿½o׳- ן¿½Tן¿½T׳¢ן¿½.׳¥ ן¿½"׳©׳§׳¢ן¿½"."
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_alerts(self, chat_id):
        text = (
            "ן¿½Y"" <b>ן¿½"׳×׳¨׳-ן¿½.׳× ן¿½zן¿½-ן¿½T׳¨</b>\n"
            "ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
            "ן¿½'׳§׳¨ן¿½.ן¿½'! ׳×ן¿½.ן¿½>ן¿½o ן¿½oן¿½"ן¿½'ן¿½"ן¿½T׳¨ ן¿½"׳×׳¨׳-ן¿½.׳× ׳¢ן¿½o:\n"
            "ן¿½?ן¿½ ן¿½zן¿½-ן¿½T׳¨ ׳©׳¢ן¿½.ן¿½'׳¨ ׳¨ן¿½zן¿½"\n"
            "ן¿½?ן¿½ ׳ ׳₪ן¿½- ן¿½-׳¨ן¿½Tן¿½'\n"
            "ן¿½?ן¿½ ן¿½-ן¿½"׳©ן¿½.׳× ׳©ן¿½.׳§\n"
            "ן¿½?ן¿½ ׳©ן¿½T׳ ן¿½.ן¿½T ן¿½'׳×ן¿½T׳§"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_deals_text(self, chat_id):
        text = (
            "ן¿½Y"ן¿½ <b>ן¿½zן¿½'׳¦׳¢ן¿½T׳ ׳₪׳¢ן¿½Tן¿½oן¿½T׳</b>\n\n"
            "ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\n\n"
            "ן¿½Y"ן¿½ <b>ן¿½zן¿½'׳¦׳¢ ן¿½"׳©׳§ן¿½" ן¿½?" 30% ן¿½"׳ ן¿½-ן¿½"!</b>\n"
            "  ן¿½Y'ן¿½ ן¿½>ן¿½o ן¿½"ן¿½'ן¿½.ן¿½~ן¿½T׳ ן¿½'-30% ן¿½"׳ ן¿½-ן¿½"\n"
            "  ן¿½Yן¿½ן¿½ן¸ ׳§ן¿½.ן¿½": <code>LAUNCH30</code>\n"
            "  ג° ן¿½-ן¿½zן¿½Y ן¿½zן¿½.ן¿½'ן¿½'ן¿½o\n\n"
            "ן¿½Y'Z <b>ן¿½-ן¿½'ן¿½Tן¿½oן¿½" ן¿½zן¿½o׳-ן¿½" ן¿½?" 6 ן¿½'ן¿½.ן¿½~ן¿½T׳</b>\n"
            "  ן¿½Y'ן¿½ ן¿½zן¿½-ן¿½T׳¨: <b>199ן¿½,ן¿½</b>\n"
            "  ן¿½Y"ן¿½ ן¿½>ן¿½o 6 ן¿½'ן¿½.ן¿½~ן¿½T ן¿½"׳₪׳¨ן¿½Tן¿½zן¿½Tן¿½.׳\n\n"
            "ן¿½Yן¿½ן¿½ <b>ן¿½"ן¿½-ן¿½zן¿½Y 3 = ׳₪׳¨ן¿½Tן¿½zן¿½Tן¿½.׳ ן¿½-ן¿½T׳ ׳!</b>\n"
            "  ן¿½Y'ן¿½ ן¿½"ן¿½-ן¿½zן¿½Y 3 ן¿½-ן¿½'׳¨ן¿½T׳\n"
            "  ן¿½YZן¿½ ׳§ן¿½'ן¿½o Community Premium ן¿½'ן¿½-ן¿½T׳ ׳\n\n"
            "ן¿½Y>ן¿½ן¸ <b>ן¿½-ן¿½'ן¿½Tן¿½o׳× ׳-ן¿½'ן¿½~ן¿½-ן¿½"</b>\n"
            "  ן¿½Y'ן¿½ Guardian + Wallet = <b>99ן¿½,ן¿½</b>\n\n"
            "ן¿½YZ" <b>ן¿½zן¿½'׳¦׳¢ ׳¡ן¿½~ן¿½.ן¿½"׳ ן¿½~ן¿½T׳</b>\n"
            "  ן¿½Y'ן¿½ 50% ן¿½"׳ ן¿½-ן¿½" ׳¢ן¿½o Academia\n"
            "  ן¿½Yן¿½ן¿½ן¸ ׳§ן¿½.ן¿½": <code>STUDENT50</code>\n"
            "ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_buy_slh_text(self, chat_id):
        text = (
            f"ן¿½Yן¿½T <b>׳¨ן¿½>ן¿½T׳©׳× SLH Coin</b>\n\n"
            f"ן¿½Y'ן¿½ <b>ן¿½zן¿½-ן¿½T׳¨:</b> 1 SLH = {SLH_PRICE_ILS}ן¿½,ן¿½\n"
            f"ן¿½Y"ן¿½ ן¿½zן¿½T׳ ן¿½Tן¿½zן¿½.׳: 0.00004 SLH (0.018ן¿½,ן¿½)\n\n"
            f"ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\n"
            f"ן¿½Y"S <b>ן¿½zן¿½"׳¨ן¿½'ן¿½.׳× ן¿½zן¿½-ן¿½T׳¨:</b>\n\n"
        )
        for tier in SLH_BUY_TIERS:
            text += f"  ן¿½Yן¿½T {tier['amount']} SLH = {tier['price']}ן¿½,ן¿½\n"
        text += (
            f"\nן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\n"
            f"ן¿½Y'ן¿½ <b>׳-׳¨׳ ׳§ TON:</b>\n<code>{TON_WALLET}</code>\n\n"
            f"ן¿½Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            f"ן¿½Y"ן¿½ ׳©ן¿½oן¿½- ׳¦ן¿½Tן¿½oן¿½.׳ ן¿½z׳¡ן¿½s ׳-ן¿½. Transaction Hash\n"
            f"׳-ן¿½. ׳¦ן¿½.׳¨ ׳§׳©׳¨ ׳¢׳ @Osif83"
        )
        self.send(chat_id, text, self.buy_slh_keyboard())

    # ן¿½"?ן¿½"? Banking commands ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
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
            f"ן¿½o. <b>ן¿½"׳₪׳§ן¿½"ן¿½" #{deposit_id} ׳ ן¿½.׳¦׳¨ן¿½"!</b>\n"
            f"ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
            f"{plan['name']} | {amount} TON\n"
            f"׳×׳©ן¿½.׳-ן¿½" ן¿½-ן¿½.ן¿½"׳©ן¿½T׳×: ~{monthly_return} TON\n"
            f"׳ ׳¢ן¿½.ן¿½o ׳¢ן¿½": {unlock_date}\n\n"
            f"ן¿½Y'ן¿½ ׳©ן¿½oן¿½- {amount} TON ן¿½o:\n"
            f"<code>{TON_WALLET}</code>\n\n"
            f"ן¿½.׳©ן¿½oן¿½- ׳¦ן¿½Tן¿½oן¿½.׳ ן¿½z׳¡ן¿½s ן¿½o׳-ן¿½T׳©ן¿½.׳¨."
        )
        self.send(chat_id, text, self.main_reply_keyboard())

        # Notify admin
        if str(chat_id) != ADMIN_ID:
            admin_text = (
                f"ן¿½Y'ן¿½ <b>ן¿½"׳₪׳§ן¿½"ן¿½" ן¿½-ן¿½"׳©ן¿½" #{deposit_id}</b>\n"
                f"ן¿½Y'ן¿½ @{user['username']} ({chat_id})\n"
                f"ן¿½Y'ן¿½ {plan['name']} | {amount} TON\n"
                f"ן¿½Y'ן¿½ {plan['rate']}% ן¿½-ן¿½.ן¿½"׳©ן¿½T | {plan['days']} ן¿½Tן¿½zן¿½T׳"
            )
            kb = {"inline_keyboard": [
                [{"text": "ן¿½o. ׳-׳©׳¨", "callback_data": f"admin_approve_{chat_id}_{deposit_id}"},
                 {"text": "ן¿½O ן¿½"ן¿½-ן¿½"", "callback_data": f"admin_reject_{chat_id}_{deposit_id}"}],
            ]}
            self.send(int(ADMIN_ID), admin_text, kb)

    def handle_mydeposits(self, chat_id):
        user = _get_user(chat_id)
        if not user["deposits"]:
            self.send(chat_id, "ן¿½Y"< ׳-ן¿½Tן¿½Y ן¿½"׳₪׳§ן¿½"ן¿½.׳× ׳₪׳¢ן¿½Tן¿½oן¿½.׳×.\n\nן¿½oן¿½"׳₪׳§ן¿½"ן¿½" ן¿½-ן¿½"׳©ן¿½": /deposit", self.main_reply_keyboard())
            return

        text = "ן¿½Y"< <b>ן¿½"ן¿½"׳₪׳§ן¿½"ן¿½.׳× ׳©ן¿½oן¿½T</b>\nן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
        for d in user["deposits"]:
            status = "ן¿½o." if d["status"] == "active" else "ג³" if d["status"] == "pending" else "ן¿½O"
            text += f"{status} #{d['id']} | {d['plan']} | {d['amount']} TON | {d['rate']}%\n"
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_withdraw(self, chat_id, args=""):
        if not args:
            self.send(chat_id,
                "ן¿½Y'ן¿½ <b>ן¿½z׳©ן¿½Tן¿½>ן¿½"</b>\n\n׳©ן¿½Tן¿½zן¿½.׳©: /withdraw <ן¿½z׳¡׳₪׳¨ ן¿½"׳₪׳§ן¿½"ן¿½"> <ן¿½>׳×ן¿½.ן¿½'׳× TON>\n\nן¿½"ן¿½.ן¿½'ן¿½zן¿½": /withdraw 1 UQDhfy...\n\nן¿½o׳¨׳©ן¿½Tן¿½zן¿½": /mydeposits",
                self.main_reply_keyboard())
            return
        self.send(chat_id, "ן¿½Y"ן¿½ ן¿½'׳§׳©׳× ן¿½"ן¿½z׳©ן¿½Tן¿½>ן¿½" ׳ ׳©ן¿½oן¿½-ן¿½" ן¿½o׳-ן¿½T׳©ן¿½.׳¨. ׳ ׳¢ן¿½"ן¿½>ן¿½Y ן¿½'ן¿½"׳§ן¿½"׳.", self.main_reply_keyboard())
        if str(chat_id) != ADMIN_ID:
            user = _get_user(chat_id)
            self.send(int(ADMIN_ID), f"ן¿½Y'ן¿½ <b>ן¿½'׳§׳©׳× ן¿½z׳©ן¿½Tן¿½>ן¿½"!</b>\nUser: @{user['username']} ({chat_id})\nArgs: {args}")

    def handle_statement(self, chat_id):
        user = _get_user(chat_id)
        ton_total = user["ton_available"] + user["ton_locked"]
        text = (
            f"ן¿½Y"< <b>ן¿½"׳£ ן¿½-׳©ן¿½'ן¿½.ן¿½Y (30 ן¿½Tן¿½.׳)</b>\n"
            f"ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
            f"ן¿½Y'ן¿½ ן¿½-ן¿½zן¿½Tן¿½Y: {user['ton_available']:.4f} TON\n"
            f"ן¿½Y"' ׳ ׳¢ן¿½.ן¿½o: {user['ton_locked']:.4f} TON\n"
            f"ן¿½Y'ן¿½ ׳¡ן¿½"\"ן¿½>: {ton_total:.4f} TON\n\n"
            f"ן¿½Y"^ ן¿½"׳₪׳§ן¿½"ן¿½.׳×: {len(user['deposits'])}\n"
            f"ן¿½Y'ן¿½ ן¿½z׳©ן¿½Tן¿½>ן¿½.׳×: {user['withdrawals']}\n"
            f"ן¿½Y"ן¿½ ׳×׳ ן¿½.׳¢ן¿½.׳×: {user['transactions']}\n\n"
            f"SLH Investment House"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_kyc(self, chat_id, args=""):
        if args:
            self.send(chat_id, f"ן¿½o. ׳©ן¿½oן¿½' 1 ן¿½"ן¿½.׳©ן¿½o׳: {args}\n\n׳©ן¿½oן¿½- ׳¦ן¿½Tן¿½oן¿½.׳ ׳×.ן¿½-. (ן¿½>׳×ן¿½zן¿½.׳ ן¿½")", self.main_reply_keyboard())
        else:
            text = (
                "ן¿½Y"< <b>KYC - ן¿½-ן¿½Tן¿½"ן¿½.ן¿½T</b>\nן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
                "׳©ן¿½oן¿½' 1: /kyc <׳©׳ ן¿½zן¿½o׳->\n"
                "׳©ן¿½oן¿½' 2: ׳©ן¿½oן¿½- ׳¦ן¿½Tן¿½oן¿½.׳ ׳×.ן¿½-. (ן¿½>׳×ן¿½zן¿½.׳ ן¿½")\n"
                "׳©ן¿½oן¿½' 3: ן¿½"ן¿½z׳×ן¿½Y ן¿½o׳-ן¿½T׳©ן¿½.׳¨"
            )
            self.send(chat_id, text, self.main_reply_keyboard())

    def handle_faq(self, chat_id):
        text = (
            "ן¿½" <b>FAQ</b>\n\n"
            "Q: ן¿½>ן¿½zן¿½" ׳¢ן¿½.ן¿½oן¿½"?\nA: 22.221ן¿½,ן¿½ ן¿½-ן¿½" ׳₪׳¢ן¿½zן¿½T\n\n"
            "Q: ׳-ן¿½Tן¿½s ן¿½z׳©ן¿½oן¿½zן¿½T׳?\nA: @wallet ן¿½?' Buy TON ן¿½?' Send\n\n"
            "Q: ן¿½'ן¿½~ן¿½.ן¿½-?\nA: ן¿½z׳₪׳×ן¿½-ן¿½.׳× ׳₪׳¨ן¿½~ן¿½Tן¿½T׳ ן¿½o׳- ׳ ׳©ן¿½z׳¨ן¿½T׳\n\n"
            "Q: ׳×ן¿½zן¿½Tן¿½>ן¿½"?\nA: /support"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_help(self, chat_id, message_id=None):
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            "ן¿½" <b>SLH Investment House</b>\n"
            "ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
            "ן¿½Y"S <b>ן¿½"׳©ן¿½.׳§</b> - 12 ן¿½zן¿½~ן¿½'׳¢ן¿½.׳×, ׳¡ן¿½.ן¿½.׳-׳₪, ן¿½"׳×׳¨׳-ן¿½.׳×\n"
            "ן¿½Y'ן¿½ <b>ן¿½"׳©׳§׳¢ן¿½.׳×</b> - 4 ׳₪׳§ן¿½"ן¿½.׳ ן¿½.׳×, 4%-65%\n"
            "ן¿½Y'ן¿½ <b>׳-׳¨׳ ׳§</b> - TON/BNB/SLH + ן¿½"׳¢ן¿½'׳¨ן¿½.׳×\n"
            "ן¿½Y"ן¿½ <b>ן¿½z׳¡ן¿½-׳¨</b> - ׳¡ן¿½.ן¿½.׳-׳₪, Limit, ן¿½"׳×׳¨׳-ן¿½.׳×\n\n"
            "ן¿½Y'ן¿½ <b>ן¿½'׳ ׳§:</b>\n"
            "/deposit /mydeposits /withdraw /statement\n\n"
            "ן¿½Y'ן¿½ <b>ן¿½z׳¡ן¿½-׳¨:</b>\n"
            "/prices /swap /limit /orders /alert /portfolio\n\n"
            "ן¿½Y'ן¿½ <b>׳-׳¨׳ ׳§:</b>\n"
            "/pay /send /mybalance /myid /gas\n\n"
            "ן¿½Yן¿½T <b>SLH Coin:</b>\n"
            "/buyslh - ׳¨ן¿½>ן¿½T׳©׳× ן¿½zן¿½~ן¿½'׳¢ SLH\n\n"
            "ן¿½Y"s <b>׳¢ן¿½.ן¿½":</b>\n"
            "/share /faq /support /kyc /help\n\n"
            f"ן¿½Y'ן¿½ <b>׳©׳×׳£ ן¿½.ן¿½"׳¨ן¿½.ן¿½.ן¿½Tן¿½- 15% ן¿½'׳ ׳§ן¿½.ן¿½"ן¿½.׳× SLH!</b>\n"
            f"ן¿½Y"- <code>{ref_link}</code>\n\n"
            "SLH Investment House | SPARK IND"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.back_keyboard())
        else:
            self.send(chat_id, text, self.main_reply_keyboard())

    def _format_invest_plans(self):
        text = "ן¿½Y'ן¿½ <b>׳×ן¿½.ן¿½>׳ ן¿½Tן¿½.׳× ן¿½"׳©׳§׳¢ן¿½"</b>\nן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?\n\n"
        for i, plan in enumerate(INVESTMENT_PLANS, 1):
            text += (
                f"{plan['name']}\n"
                f"  ן¿½Y'ן¿½ {plan['rate']}% ן¿½-ן¿½.ן¿½"׳©ן¿½T | {plan['annual']}% ׳©׳ ׳×ן¿½T\n"
                f"  ן¿½zן¿½T׳ ן¿½Tן¿½zן¿½.׳ {plan['min_ton']} TON | {plan['days']} ן¿½Tן¿½.׳\n\n"
            )
        return text

    # ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½
    # HUB HANDLERS (inline keyboard callbacks)
    # ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½

    def handle_earn(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        done = len(user["tasks_done"])
        total = len(_daily_tasks)
        total_reward = sum(t["reward"] for t in _daily_tasks)
        done_reward = sum(t["reward"] for t in _daily_tasks if t["id"] in user["tasks_done"])
        text = (
            f"ן¿½Y'ן¿½ <b>ן¿½"׳¨ן¿½.ן¿½.ן¿½Tן¿½- ׳ ׳§ן¿½.ן¿½"ן¿½.׳× SLH</b>\n\n"
            f"ן¿½Y"S ן¿½"׳×׳§ן¿½"ן¿½zן¿½.׳×: {done}/{total} ן¿½z׳©ן¿½Tן¿½zן¿½.׳×\n"
            f"ן¿½Y'Z ׳©׳ ׳¦ן¿½'׳¨ ן¿½"ן¿½Tן¿½.׳: {done_reward}/{total_reward} ׳ ׳§ן¿½.ן¿½"ן¿½.׳×\n"
            f"ן¿½Y'ן¿½ ן¿½T׳×׳¨ן¿½": {user['hub_points']} ׳ ׳§ן¿½.ן¿½"ן¿½.׳×\n\n"
            f"ן¿½Y'? <b>ן¿½z׳©ן¿½Tן¿½zן¿½.׳× ן¿½-ן¿½zן¿½T׳ ן¿½.׳×:</b>"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.earn_keyboard())
        else:
            self.send(chat_id, text, self.earn_keyboard())

    def handle_task(self, chat_id, task_id, callback_id, message_id):
        user = _get_user(chat_id)
        task = next((t for t in _daily_tasks if t["id"] == task_id), None)
        if not task:
            self.answer_callback(callback_id, "ן¿½O ן¿½z׳©ן¿½Tן¿½zן¿½" ן¿½o׳- ׳ ן¿½z׳¦׳-ן¿½"")
            return
        if task_id in user["tasks_done"]:
            self.answer_callback(callback_id, "ן¿½o. ן¿½>ן¿½'׳¨ ן¿½'ן¿½T׳¦׳¢׳× ן¿½z׳©ן¿½Tן¿½zן¿½" ן¿½-ן¿½. ן¿½"ן¿½Tן¿½.׳!", True)
            return
        user["tasks_done"].append(task_id)
        user["hub_points"] += task["reward"]
        user["total_earned"] += task["reward"]
        self.answer_callback(callback_id, f"ן¿½o. +{task['reward']} ׳ ׳§ן¿½.ן¿½"ן¿½.׳×!", True)
        self.handle_earn(chat_id, message_id)

    def handle_swap_inline(self, chat_id, message_id=None):
        text = (
            "ן¿½Y"" <b>SLH Swap ן¿½?" ן¿½"ן¿½z׳¨׳× ן¿½zן¿½~ן¿½'׳¢ן¿½.׳×</b>\n\n"
            "ן¿½"ן¿½zן¿½T׳¨ן¿½. ן¿½'ן¿½Tן¿½Y 4,500+ ן¿½zן¿½~ן¿½'׳¢ן¿½.׳× ׳§׳¨ן¿½T׳₪ן¿½~ן¿½. ן¿½'׳§ן¿½oן¿½.׳×!\n\n"
            "ן¿½Y'ן¿½ <b>ן¿½T׳×׳¨ן¿½.׳ ן¿½.׳×:</b>\n"
            "ן¿½?ן¿½ ן¿½oן¿½o׳- ן¿½"׳¨׳©ן¿½zן¿½"\nן¿½?ן¿½ ׳¢ן¿½zן¿½oן¿½.׳× ׳ ן¿½zן¿½.ן¿½>ן¿½.׳×\n"
            "ן¿½?ן¿½ ן¿½"ן¿½z׳¨ן¿½" ן¿½T׳©ן¿½T׳¨ן¿½" ן¿½z׳-׳¨׳ ׳§ ן¿½o׳-׳¨׳ ׳§\n"
            "ן¿½?ן¿½ ׳×ן¿½zן¿½Tן¿½>ן¿½" ן¿½'-TON, BTC, ETH, BNB ן¿½.׳¢ן¿½.ן¿½"\n\n"
            "ן¿½Y"ן¿½ <b>ן¿½zן¿½'׳¦׳¢:</b> Cashback 0.5% ׳¢ן¿½o ן¿½>ן¿½o ׳¢׳¡׳§ן¿½"!"
        )
        kb = {"inline_keyboard": [
            [{"text": "ן¿½Y"" ן¿½"ן¿½z׳¨ ׳¢ן¿½>׳©ן¿½Tן¿½.", "url": f"https://letsexchange.io/?ref={LETSEXCHANGE_REF}"}],
            [{"text": "ן¿½Y'ן¿½ TON ן¿½?' USDT", "url": f"https://letsexchange.io/?from=TON&to=USDT&ref={LETSEXCHANGE_REF}"}],
            [{"text": "ן¿½Y'ן¿½ BTC ן¿½?' TON", "url": f"https://letsexchange.io/?from=BTC&to=TON&ref={LETSEXCHANGE_REF}"}],
            [{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½" ן¿½o׳×׳₪׳¨ן¿½Tן¿½~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_vip(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        current = user["vip"]
        status = f"ן¿½o. {VIP_PLANS[current]['name']}" if current else "ן¿½Y?" ן¿½-ן¿½T׳ ׳"
        text = f"ן¿½Y'' <b>VIP Membership</b>\n\n׳¡ן¿½~ן¿½~ן¿½.׳¡: <b>{status}</b>\n\nן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\n"
        for key, plan in VIP_PLANS.items():
            marker = "ן¿½o." if current == key else "ג­-"
            text += f"\n{marker} <b>{plan['name']}</b> ן¿½?" {plan['price_ils']}ן¿½,ן¿½\n"
            for f in plan["features"]:
                text += f"  ן¿½?ן¿½ {f}\n"
        text += f"\nן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\nן¿½Y'ן¿½ <b>׳×׳©ן¿½oן¿½.׳:</b> ן¿½"׳¢ן¿½'׳¨ ן¿½o׳-׳¨׳ ׳§ + ׳¦ן¿½Tן¿½oן¿½.׳ ן¿½z׳¡ן¿½s\nן¿½Y"ן¿½ <b>ן¿½-ן¿½'ן¿½Tן¿½oן¿½" ן¿½zן¿½o׳-ן¿½":</b> ן¿½>ן¿½o ן¿½"-VIP + 6 ן¿½'ן¿½.ן¿½~ן¿½T׳ = 199ן¿½,ן¿½ ן¿½'ן¿½oן¿½'ן¿½"!"
        if message_id:
            self.edit_message(chat_id, message_id, text, self.vip_keyboard())
        else:
            self.send(chat_id, text, self.vip_keyboard())

    def handle_vip_select(self, chat_id, plan_key, callback_id, message_id):
        plan = VIP_PLANS.get(plan_key)
        if not plan:
            self.answer_callback(callback_id, "ן¿½O")
            return
        text = (
            f"ן¿½Y'' <b>{plan['name']}</b>\n\n"
            f"ן¿½Y'ן¿½ <b>ן¿½zן¿½-ן¿½T׳¨:</b> {plan['price_ils']}ן¿½,ן¿½\n\n"
            f"<b>׳₪ן¿½T׳¦'׳¨ן¿½T׳:</b>\n" +
            "\n".join(f"  ן¿½o. {f}" for f in plan["features"]) +
            f"\n\nן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\n"
            f"ן¿½Y'ן¿½ <b>׳©ן¿½oן¿½- {plan['price_ils']}ן¿½,ן¿½ ן¿½o׳-׳¨׳ ׳§ TON:</b>\n\n"
            f"<code>{TON_WALLET}</code>\n\n׳-ן¿½. ׳¦ן¿½.׳¨ ׳§׳©׳¨ ׳¢׳ @Osif83\n\n"
            f"ן¿½Y"ן¿½ ׳©ן¿½oן¿½- ׳¦ן¿½Tן¿½oן¿½.׳ ן¿½z׳¡ן¿½s ׳©ן¿½o ן¿½"׳¢׳¡׳§ן¿½" ן¿½>׳-ן¿½Y\nן¿½o. ׳×׳§ן¿½'ן¿½o ן¿½'ן¿½T׳©ן¿½" ׳×ן¿½.ן¿½s ן¿½"׳§ן¿½.׳×"
        )
        kb = {"inline_keyboard": [
            [{"text": "ן¿½Y'ן¿½ ן¿½"׳¢׳×׳§ ן¿½>׳×ן¿½.ן¿½'׳× ׳-׳¨׳ ׳§", "callback_data": f"copy_wallet_{plan_key}"}],
            [{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½" ן¿½o-VIP", "callback_data": "menu_vip"}],
        ]}
        self.edit_message(chat_id, message_id, text, kb)
        self.answer_callback(callback_id)

    def handle_airdrop(self, chat_id, message_id=None):
        text = (
            "ן¿½YZן¿½ <b>SLH Airdrop</b>\n\n"
            f"ן¿½Y'ן¿½ <b>ן¿½zן¿½'׳¦׳¢ ן¿½"׳©׳§ן¿½":</b>\n1,000 ן¿½~ן¿½.׳§׳ ן¿½T SLH = <b>444,000ן¿½,ן¿½</b>\n\n"
            f"ן¿½Y"S <b>׳¡ן¿½~ן¿½~ן¿½.׳¡:</b>\nן¿½Y'ן¿½ ן¿½z׳©׳×ן¿½z׳©ן¿½T׳: 38\nן¿½Y'ן¿½ ׳¢׳¡׳§׳-ן¿½.׳×: 22\nן¿½YZן¿½ ן¿½z׳§ן¿½.ן¿½zן¿½.׳× ׳₪׳ ן¿½.ן¿½Tן¿½T׳: 978/1,000\n\n"
            f"ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\n"
            f"ן¿½Y'ן¿½ <b>ן¿½o׳¨ן¿½>ן¿½T׳©ן¿½" ׳©ן¿½oן¿½- ן¿½o׳-׳¨׳ ׳§ TON:</b>\n<code>{TON_WALLET}</code>\n\n"
            f"ן¿½Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            "ן¿½Y"ן¿½ ׳©ן¿½oן¿½- ׳¦ן¿½Tן¿½oן¿½.׳ ן¿½z׳¡ן¿½s / Transaction Hash\nן¿½o. ׳§ן¿½'ן¿½oן¿½" ׳×ן¿½.ן¿½s 24 ׳©׳¢ן¿½.׳×"
        )
        kb = {"inline_keyboard": [
            [{"text": "ן¿½Y'ן¿½ ׳©ן¿½oן¿½- ׳×׳©ן¿½oן¿½.׳", "callback_data": "airdrop_pay"}],
            [{"text": "ן¿½Y"S ׳¡ן¿½~ן¿½~ן¿½.׳¡ ׳©ן¿½oן¿½T", "callback_data": "airdrop_status"}],
            [{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½" ן¿½o׳×׳₪׳¨ן¿½Tן¿½~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_referral(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            f"ן¿½Y'ן¿½ <b>ן¿½"ן¿½"׳₪׳ ן¿½Tן¿½.׳× ׳©ן¿½oן¿½s</b>\n\n"
            f"ן¿½Y"- <b>ן¿½"׳§ן¿½T׳©ן¿½.׳¨ ן¿½"׳-ן¿½T׳©ן¿½T ׳©ן¿½oן¿½s:</b>\n<code>{ref_link}</code>\n\n"
            f"ן¿½Y"S <b>׳¡ן¿½~ן¿½~ן¿½T׳¡ן¿½~ן¿½T׳§ן¿½":</b>\n"
            f"ן¿½Y'ן¿½ ן¿½"׳₪׳ ן¿½Tן¿½.׳×: <b>{user['referral_count']}</b>\n"
            f"ן¿½Y'ן¿½ ׳ ׳¦ן¿½'׳¨ ן¿½zן¿½"׳₪׳ ן¿½Tן¿½.׳×: <b>{user['referral_count'] * 50}</b> ׳ ׳§ן¿½.ן¿½"ן¿½.׳× SLH\n\n"
            f"ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\n"
            f"ן¿½Y'ן¿½ <b>׳-ן¿½Tן¿½s ן¿½oן¿½"׳¨ן¿½.ן¿½.ן¿½Tן¿½-?</b>\n"
            f"1ן¸ן¿½fן¿½ ׳©׳×׳£ ׳-׳× ן¿½"׳§ן¿½T׳©ן¿½.׳¨ ׳©ן¿½oן¿½s\n"
            f"2ן¸ן¿½fן¿½ ן¿½-ן¿½'׳¨ן¿½T׳ ׳ ׳¨׳©ן¿½zן¿½T׳ ן¿½"׳¨ן¿½>ן¿½s\n"
            f"3ן¸ן¿½fן¿½ ן¿½z׳§ן¿½'ן¿½o <b>50 ׳ ׳§ן¿½.ן¿½"ן¿½.׳× SLH</b> + <b>15% ׳¢ן¿½zן¿½oן¿½" ן¿½'׳ ׳§ן¿½.ן¿½"ן¿½.׳× SLH</b> ן¿½zן¿½>ן¿½o ׳¨ן¿½>ן¿½T׳©ן¿½"\n\n"
            f"ן¿½YZן¿½ ן¿½"ן¿½-ן¿½zן¿½Y 3 ן¿½-ן¿½'׳¨ן¿½T׳ = <b>Community Premium ן¿½'ן¿½-ן¿½T׳ ׳!</b>\n\n"
            f"ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\n"
            f"ן¿½Y"- <b>׳§ן¿½T׳©ן¿½.׳¨ן¿½T׳ ן¿½oן¿½>ן¿½o ן¿½"ן¿½'ן¿½.ן¿½~ן¿½T׳:</b>\n"
            f"ן¿½?ן¿½ ן¿½YZן¿½ Airdrop: <code>https://t.me/SLH_AIR_bot?start=ref_{chat_id}</code>\n"
            f"ן¿½?ן¿½ ן¿½Y>ן¿½ן¸ Guardian: <code>https://t.me/Grdian_bot?start=ref_{chat_id}</code>\n"
            f"ן¿½?ן¿½ ן¿½Y>' BotShop: <code>https://t.me/BotShop_bot?start=ref_{chat_id}</code>\n"
            f"ן¿½?ן¿½ ן¿½Y'ן¿½ Wallet: <code>https://t.me/SLH_Wallet_bot?start=ref_{chat_id}</code>\n"
            f"ן¿½?ן¿½ ן¿½YZ" Academia: <code>https://t.me/SLH_Academia_bot?start=ref_{chat_id}</code>\n"
            f"ן¿½?ן¿½ ן¿½Y'ן¿½ Community: <code>https://t.me/SLH_community_bot?start=ref_{chat_id}</code>"
        )
        kb = {"inline_keyboard": [
            [{"text": "ן¿½Y"< ן¿½"׳¢׳×׳§ ׳§ן¿½T׳©ן¿½.׳¨ ן¿½"׳₪׳ ן¿½Tן¿½"", "callback_data": "copy_ref"}],
            [{"text": "ן¿½Y"ן¿½ ׳©׳×׳£ ׳¢׳ ן¿½-ן¿½'׳¨", "url": f"https://t.me/share/url?url={ref_link}&text=ן¿½Ys? ן¿½"׳¦ן¿½~׳¨׳₪ן¿½. ן¿½o-SLH - ן¿½'ן¿½T׳× ן¿½"׳©׳§׳¢ן¿½.׳× ן¿½"ן¿½Tן¿½'ן¿½Tן¿½~ן¿½oן¿½T!"}],
            [{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½" ן¿½o׳×׳₪׳¨ן¿½Tן¿½~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_portfolio(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        vip_str = VIP_PLANS[user["vip"]]["name"] if user["vip"] else "ן¿½Y?" Free"
        text = (
            f"ן¿½Y"S <b>ן¿½"׳×ן¿½T׳§ ׳©ן¿½oן¿½T</b>\n\n"
            f"ן¿½Y'Z SLH: {user['slh_balance']:.2f}\n"
            f"ן¿½YZן¿½ ZVK: {user['zvk_balance']}\n"
            f"ן¿½Y'ן¿½ Hub ׳ ׳§ן¿½.ן¿½"ן¿½.׳×: {user['hub_points']}\n"
            f"ן¿½Y'' ׳¡ן¿½~ן¿½~ן¿½.׳¡: {vip_str}\n"
            f"ן¿½Y'ן¿½ ן¿½"׳₪׳ ן¿½Tן¿½.׳×: {user['referral_count']}\n"
            f"ן¿½o. ן¿½z׳©ן¿½Tן¿½zן¿½.׳× ׳©ן¿½'ן¿½.׳¦׳¢ן¿½.: {len(user['tasks_done'])}\n"
            f"ן¿½Y". ן¿½"׳¦ן¿½~׳¨׳£: {user['joined'][:10]}\n\n"
            f"ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\n"
            f"ן¿½Y'ן¿½ <b>ן¿½"ן¿½z׳¨׳× ׳ ׳§ן¿½.ן¿½"ן¿½.׳×:</b>\n"
            f"1,000 ׳ ׳§ן¿½.ן¿½"ן¿½.׳× = 1 SLH Token\n"
            f"5,000 ׳ ׳§ן¿½.ן¿½"ן¿½.׳× = 1 ן¿½-ן¿½.ן¿½"׳© VIP Basic"
        )
        kb = {"inline_keyboard": [
            [{"text": "ן¿½Y'ן¿½ ן¿½"׳¨ן¿½.ן¿½.ן¿½Tן¿½- ׳¢ן¿½.ן¿½"", "callback_data": "menu_earn"}, {"text": "ן¿½Y'' ׳©ן¿½"׳¨ן¿½' VIP", "callback_data": "menu_vip"}],
            [{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½" ן¿½o׳×׳₪׳¨ן¿½Tן¿½~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_deals_inline(self, chat_id, message_id=None):
        text = (
            "ן¿½Y"ן¿½ <b>ן¿½zן¿½'׳¦׳¢ן¿½T׳ ׳₪׳¢ן¿½Tן¿½oן¿½T׳</b>\n\nן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\n\n"
            "ן¿½Y"ן¿½ <b>ן¿½zן¿½'׳¦׳¢ ן¿½"׳©׳§ן¿½" ן¿½?" 30% ן¿½"׳ ן¿½-ן¿½"!</b>\n  ן¿½Y'ן¿½ ן¿½>ן¿½o ן¿½"ן¿½'ן¿½.ן¿½~ן¿½T׳ ן¿½'-30% ן¿½"׳ ן¿½-ן¿½"\n  ן¿½Yן¿½ן¿½ן¸ ׳§ן¿½.ן¿½": <code>LAUNCH30</code>\n  ג° ן¿½-ן¿½zן¿½Y ן¿½zן¿½.ן¿½'ן¿½'ן¿½o\n\n"
            "ן¿½Y'Z <b>ן¿½-ן¿½'ן¿½Tן¿½oן¿½" ן¿½zן¿½o׳-ן¿½" ן¿½?" 6 ן¿½'ן¿½.ן¿½~ן¿½T׳</b>\n  ן¿½Y'ן¿½ ן¿½zן¿½-ן¿½T׳¨: <b>199ן¿½,ן¿½</b>\n\n"
            "ן¿½Yן¿½ן¿½ <b>ן¿½"ן¿½-ן¿½zן¿½Y 3 = ׳₪׳¨ן¿½Tן¿½zן¿½Tן¿½.׳ ן¿½-ן¿½T׳ ׳!</b>\n\n"
            "ן¿½Y>ן¿½ן¸ <b>ן¿½-ן¿½'ן¿½Tן¿½o׳× ׳-ן¿½'ן¿½~ן¿½-ן¿½"</b>\n  ן¿½Y'ן¿½ Guardian + Wallet = <b>99ן¿½,ן¿½</b>\n\n"
            "ן¿½YZ" <b>ן¿½zן¿½'׳¦׳¢ ׳¡ן¿½~ן¿½.ן¿½"׳ ן¿½~ן¿½T׳</b>\n  ן¿½Y'ן¿½ 50% ן¿½"׳ ן¿½-ן¿½" ן¿½?" ׳§ן¿½.ן¿½": <code>STUDENT50</code>\nן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½"
        )
        kb = {"inline_keyboard": [
            [{"text": "ן¿½Y'Z ׳¨ן¿½>ן¿½.׳© ן¿½-ן¿½'ן¿½Tן¿½oן¿½" ן¿½zן¿½o׳-ן¿½"", "callback_data": "vip_elite"}],
            [{"text": "ן¿½Y>ן¿½ן¸ ן¿½-ן¿½'ן¿½Tן¿½o׳× ׳-ן¿½'ן¿½~ן¿½-ן¿½"", "callback_data": "vip_basic"}],
            [{"text": "ן¿½Y'ן¿½ ן¿½"ן¿½-ן¿½zן¿½Y ן¿½-ן¿½'׳¨ן¿½T׳", "callback_data": "menu_referral"}],
            [{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½" ן¿½o׳×׳₪׳¨ן¿½Tן¿½~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_buy_slh_inline(self, chat_id, message_id=None):
        text = (
            f"ן¿½Yן¿½T <b>׳¨ן¿½>ן¿½T׳©׳× SLH Coin</b>\n\n"
            f"ן¿½Y'ן¿½ <b>ן¿½zן¿½-ן¿½T׳¨:</b> 1 SLH = {SLH_PRICE_ILS}ן¿½,ן¿½\n"
            f"ן¿½Y"ן¿½ ן¿½zן¿½T׳ ן¿½Tן¿½zן¿½.׳: 0.00004 SLH (0.018ן¿½,ן¿½)\n\nן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\nן¿½Y"S <b>ן¿½zן¿½"׳¨ן¿½'ן¿½.׳× ן¿½zן¿½-ן¿½T׳¨:</b>\n\n"
        )
        for tier in SLH_BUY_TIERS:
            text += f"  ן¿½Yן¿½T {tier['amount']} SLH = {tier['price']}ן¿½,ן¿½\n"
        text += (
            f"\nן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\n"
            f"ן¿½Y'ן¿½ <b>׳-׳¨׳ ׳§ TON:</b>\n<code>{TON_WALLET}</code>\n\n"
            f"ן¿½Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            "ן¿½Y"ן¿½ ׳©ן¿½oן¿½- ׳¦ן¿½Tן¿½oן¿½.׳ ן¿½z׳¡ן¿½s ׳-ן¿½. Transaction Hash\n׳-ן¿½. ׳¦ן¿½.׳¨ ׳§׳©׳¨ ׳¢׳ @Osif83"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.buy_slh_keyboard())
        else:
            self.send(chat_id, text, self.buy_slh_keyboard())

    def handle_buy_slh_select(self, chat_id, amount_str, callback_id, message_id):
        if amount_str == "custom":
            text = (
                f"ן¿½oן¿½ן¸ <b>׳¡ן¿½>ן¿½.׳ ן¿½zן¿½.׳×׳-׳ ׳-ן¿½T׳©ן¿½T׳×</b>\n\n"
                f"ן¿½Y'ן¿½ ן¿½zן¿½-ן¿½T׳¨: 1 SLH = {SLH_PRICE_ILS}ן¿½,ן¿½\n"
                f"ן¿½Y"ן¿½ ן¿½zן¿½T׳ ן¿½Tן¿½zן¿½.׳: 0.00004 SLH (0.018ן¿½,ן¿½)\n\n"
                "׳©ן¿½oן¿½- ׳-׳× ן¿½"׳¡ן¿½>ן¿½.׳ ׳©׳×׳¨׳¦ן¿½" ן¿½o׳¨ן¿½>ן¿½.׳© (ן¿½'SLH).\nן¿½oן¿½"ן¿½.ן¿½'ן¿½zן¿½": <code>0.005</code>\n\n"
                f"ן¿½Y'ן¿½ <b>׳-׳¨׳ ׳§ TON:</b>\n<code>{TON_WALLET}</code>\n\n"
                f"ן¿½Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n׳-ן¿½. ׳¦ן¿½.׳¨ ׳§׳©׳¨ ׳¢׳ @Osif83"
            )
            self.edit_message(chat_id, message_id, text, self.back_keyboard())
            self.answer_callback(callback_id)
            return
        try:
            amount = float(amount_str)
        except ValueError:
            self.answer_callback(callback_id, "ן¿½O ׳©ן¿½'ן¿½T׳-ן¿½"")
            return
        price = round(amount * SLH_PRICE_ILS, 3)
        text = (
            f"ן¿½Yן¿½T <b>׳¨ן¿½>ן¿½T׳©׳× {amount} SLH</b>\n\nן¿½Y'ן¿½ <b>ן¿½zן¿½-ן¿½T׳¨:</b> {price}ן¿½,ן¿½\n\nן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\n"
            f"ן¿½Y'ן¿½ <b>׳©ן¿½oן¿½- {price}ן¿½,ן¿½ ן¿½o׳-׳¨׳ ׳§ TON:</b>\n\n<code>{TON_WALLET}</code>\n\n"
            f"ן¿½Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            f"ן¿½Y"ן¿½ ׳©ן¿½oן¿½- ׳¦ן¿½Tן¿½oן¿½.׳ ן¿½z׳¡ן¿½s ׳-ן¿½. Transaction Hash\n׳-ן¿½. ׳¦ן¿½.׳¨ ׳§׳©׳¨ ׳¢׳ @Osif83\n\nן¿½o. ׳×׳§ן¿½'ן¿½o {amount} SLH ׳×ן¿½.ן¿½s 24 ׳©׳¢ן¿½.׳×"
        )
        kb = {"inline_keyboard": [
            [{"text": "ן¿½Y'ן¿½ ן¿½"׳¢׳×׳§ ן¿½>׳×ן¿½.ן¿½'׳× ׳-׳¨׳ ׳§", "callback_data": "copy_wallet_slh"}],
            [{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½" ן¿½o׳¨ן¿½>ן¿½T׳©ן¿½"", "callback_data": "menu_buy_slh"}],
        ]}
        self.edit_message(chat_id, message_id, text, kb)
        self.answer_callback(callback_id)

    def handle_help_inline(self, chat_id, message_id=None):
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            "ן¿½" <b>SLH HUB ן¿½?" ׳¢ן¿½-׳¨ן¿½"</b>\n\n"
            "<b>׳₪׳§ן¿½.ן¿½"ן¿½.׳×:</b>\n"
            "/start ן¿½?" ׳×׳₪׳¨ן¿½Tן¿½~ ׳¨׳-׳©ן¿½T\n/earn ן¿½?" ן¿½z׳©ן¿½Tן¿½zן¿½.׳× ן¿½.ן¿½"׳¨ן¿½.ן¿½.ן¿½-ן¿½"\n/swap ן¿½?" ן¿½"ן¿½z׳¨׳× ן¿½zן¿½~ן¿½'׳¢ן¿½.׳×\n/vip ן¿½?" ן¿½z׳ ן¿½.ן¿½T ׳₪׳¨ן¿½Tן¿½zן¿½Tן¿½.׳\n"
            "/airdrop ן¿½?" ׳¨ן¿½>ן¿½T׳©׳× ן¿½~ן¿½.׳§׳ ן¿½T׳\n/buyslh ן¿½?" ן¿½Yן¿½T ׳¨ן¿½>ן¿½T׳©׳× SLH Coin\n/referral ן¿½?" ׳§ן¿½T׳©ן¿½.׳¨ ן¿½"׳₪׳ ן¿½Tן¿½"\n"
            "/deals ן¿½?" ן¿½zן¿½'׳¦׳¢ן¿½T׳\n/portfolio ן¿½?" ן¿½"׳×ן¿½T׳§ ׳©ן¿½oן¿½T\n/help ן¿½?" ׳¢ן¿½-׳¨ן¿½"\n\n"
            "<b>׳×ן¿½zן¿½Tן¿½>ן¿½":</b> @Osif83\n<b>׳-׳×׳¨:</b> slh-nft.com\n\n"
            f"ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½ן¿½"ן¿½\nן¿½Y'ן¿½ <b>׳©׳×׳£ ן¿½.ן¿½"׳¨ן¿½.ן¿½.ן¿½Tן¿½- 15% ן¿½'׳ ׳§ן¿½.ן¿½"ן¿½.׳× SLH!</b>\nן¿½Y"- <code>{ref_link}</code>"
        )
        kb = {"inline_keyboard": [[{"text": "ן¿½Y"T ן¿½-ן¿½-׳¨ן¿½" ן¿½o׳×׳₪׳¨ן¿½Tן¿½~", "callback_data": "menu_main"}]]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    # ן¿½"?ן¿½"? Admin ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
    def handle_admin(self, chat_id):
        if str(chat_id) != ADMIN_ID:
            return
        total_users = len(_user_data)
        total_vip = sum(1 for u in _user_data.values() if u.get("vip"))
        total_points = sum(u.get("hub_points", 0) for u in _user_data.values())
        total_refs = sum(u["referral_count"] for u in _user_data.values())
        text = (
            f"ן¿½Y>ן¿½ <b>ADMIN PANEL</b>\n\n"
            f"ן¿½Y'ן¿½ ן¿½z׳©׳×ן¿½z׳©ן¿½T׳: <b>{total_users}</b>\nן¿½Y'' VIP: <b>{total_vip}</b>\n"
            f"ן¿½Y'ן¿½ ׳ ׳§ן¿½.ן¿½"ן¿½.׳× ׳©ן¿½-ן¿½.ן¿½o׳§ן¿½.: <b>{total_points}</b>\nן¿½Y'ן¿½ ן¿½"׳₪׳ ן¿½Tן¿½.׳×: <b>{total_refs}</b>\n\n"
            f"<b>׳₪׳§ן¿½.ן¿½"ן¿½.׳×:</b>\n/stats ן¿½?" ׳¡ן¿½~ן¿½~ן¿½T׳¡ן¿½~ן¿½T׳§ן¿½.׳×\n/broadcast TEXT ן¿½?" ׳©ן¿½oן¿½- ן¿½"ן¿½.ן¿½"׳¢ן¿½" ן¿½oן¿½>ן¿½.ן¿½o׳\n"
            f"/approve USER_ID PLAN ן¿½?" ׳-׳©׳¨ VIP\n/admin ן¿½?" ׳₪׳-׳ ן¿½o ן¿½-ן¿½""
        )
        self.send(chat_id, text)

    def handle_broadcast(self, chat_id, text):
        if str(chat_id) != ADMIN_ID:
            return
        sent = 0
        for uid in _user_data:
            if self.send(uid, f"ן¿½Y"ן¿½ <b>ן¿½"ן¿½.ן¿½"׳¢ן¿½" ן¿½zן¿½"ן¿½z׳¢׳¨ן¿½>׳×:</b>\n\n{text}"):
                sent += 1
        self.send(chat_id, f"ן¿½o. ׳ ׳©ן¿½oן¿½- ן¿½o-{sent} ן¿½z׳©׳×ן¿½z׳©ן¿½T׳")

    def handle_approve(self, chat_id, args):
        if str(chat_id) != ADMIN_ID:
            return
        parts = args.split()
        if len(parts) < 2:
            self.send(chat_id, "׳©ן¿½Tן¿½zן¿½.׳©: /approve USER_ID PLAN\nן¿½oן¿½"ן¿½.ן¿½'ן¿½zן¿½": /approve 123456 pro")
            return
        try:
            uid = int(parts[0])
            plan = parts[1]
            if plan in VIP_PLANS:
                user = _get_user(uid)
                user["vip"] = plan
                self.send(chat_id, f"ן¿½o. ׳-ן¿½.׳©׳¨ VIP {VIP_PLANS[plan]['name']} ן¿½oן¿½z׳©׳×ן¿½z׳© {uid}")
                self.send(uid, f"ן¿½YZ? <b>VIP ן¿½"ן¿½.׳₪׳¢ן¿½o!</b>\n\n׳©ן¿½"׳¨ן¿½'׳× ן¿½o-{VIP_PLANS[plan]['name']}! ן¿½Y''")
            else:
                self.send(chat_id, f"ן¿½O ׳×ן¿½.ן¿½>׳ ן¿½T׳× ן¿½o׳- ׳§ן¿½Tן¿½Tן¿½z׳×. ׳-׳₪׳©׳¨ן¿½.ן¿½Tן¿½.׳×: {', '.join(VIP_PLANS.keys())}")
        except:
            self.send(chat_id, "ן¿½O ׳©ן¿½'ן¿½T׳-ן¿½". ׳©ן¿½Tן¿½zן¿½.׳©: /approve USER_ID PLAN")

    # ן¿½"?ן¿½"? Callback handler ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
    def handle_callback(self, callback):
        data = callback.get("data", "")
        chat_id = callback["message"]["chat"]["id"]
        message_id = callback["message"]["message_id"]
        callback_id = callback["id"]
        first_name = callback["from"].get("first_name", "")

        # ן¿½"?ן¿½"? P2P callbacks (delegate to handle_p2p_callback) ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
        if (data.startswith("p2p_") or data.startswith("send_tok_") or
                data.startswith("sell_tok_") or data.startswith("pay_")):
            self.handle_p2p_callback(chat_id, data, callback_id, message_id)
            return

        if data == "menu_main":
            user = _get_user(chat_id)
            vip_badge = "ן¿½Y'' VIP" if user["vip"] else "ן¿½Y?" Free"
            self.edit_message(chat_id, message_id,
                f"ן¿½Ys? <b>SLH HUB SYSTEM</b>\n\n"
                f"ן¿½Y'ן¿½ <b>{first_name}</b> | {vip_badge}\n"
                f"ן¿½Y'ן¿½ ן¿½T׳×׳¨ן¿½": <b>{user['hub_points']}</b> ׳ ׳§ן¿½.ן¿½"ן¿½.׳×\n"
                f"ן¿½Y'Z SLH: <b>{user['slh_balance']:.2f}</b>\n"
                f"ן¿½Y'ן¿½ ן¿½"׳₪׳ ן¿½Tן¿½.׳×: <b>{user['referral_count']}</b>\n\nן¿½Y'? ן¿½'ן¿½-׳¨ ׳₪׳¢ן¿½.ן¿½oן¿½":",
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
            self.answer_callback(callback_id, f"ן¿½Y'ן¿½ {TON_WALLET}", True)
        elif data.startswith("task_"):
            self.handle_task(chat_id, data[5:], callback_id, message_id)
        elif data.startswith("vip_"):
            self.handle_vip_select(chat_id, data[4:], callback_id, message_id)
        elif data == "airdrop_pay":
            self.send(chat_id,
                f"ן¿½Y'ן¿½ <b>׳©ן¿½oן¿½- ׳×׳©ן¿½oן¿½.׳ ן¿½o׳-׳¨׳ ׳§ TON:</b>\n\n<code>{TON_WALLET}</code>\n\n"
                f"ן¿½Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
                "ן¿½Y"ן¿½ ׳-ן¿½-׳¨ן¿½T ן¿½"׳×׳©ן¿½oן¿½.׳, ׳©ן¿½oן¿½- ן¿½>׳-ן¿½Y:\nן¿½?ן¿½ ׳¦ן¿½Tן¿½oן¿½.׳ ן¿½z׳¡ן¿½s, ׳-ן¿½.\nן¿½?ן¿½ Transaction Hash",
                self.back_keyboard())
            self.answer_callback(callback_id)
        elif data == "airdrop_status":
            user = _get_user(chat_id)
            self.answer_callback(callback_id, f"ן¿½Y'ן¿½ ן¿½T׳×׳¨ן¿½": {user['hub_points']} ׳ ׳§ן¿½.ן¿½"ן¿½.׳× | VIP: {'ן¿½>ן¿½Y' if user['vip'] else 'ן¿½o׳-'}", True)
        elif data == "copy_ref":
            self.answer_callback(callback_id, f"ן¿½Y"- https://t.me/SLH_AIR_bot?start=ref_{chat_id}", True)
        elif data.startswith("copy_wallet_"):
            self.answer_callback(callback_id, f"ן¿½Y'ן¿½ {TON_WALLET}", True)
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
                "ן¿½Y"ן¿½ <b>׳©ן¿½oן¿½Tן¿½-׳× ן¿½zן¿½~ן¿½'׳¢ן¿½.׳×</b>\n\n"
                "ן¿½Y'Z SLH: <code>/send_slh USER_ID AMOUNT</code>\n"
                "ן¿½Y'ן¿½ TON: <code>/send_ton USER_ID AMOUNT</code>\n"
                "ן¿½YYן¿½ BNB: <code>/send_bnb USER_ID AMOUNT</code>\n"
                "ן¿½YZן¿½ ZVK: <code>/send_zvk USER_ID AMOUNT</code>\n\n"
                "ן¿½Y'ן¿½ ׳§ן¿½'ן¿½o ׳-׳× ן¿½"-USER_ID ׳©ן¿½o ן¿½"׳ ן¿½z׳¢ן¿½Y: ן¿½'׳§׳© ן¿½zן¿½z׳ ן¿½. /myid",
                self.wallet_inline_keyboard())
            self.answer_callback(callback_id)
        elif data == "wallet_history":
            self.handle_tx_history(chat_id)
            self.answer_callback(callback_id)
        elif data == "wallet_refresh":
            self.handle_wallet(chat_id, message_id)
            self.answer_callback(callback_id, "ן¿½Y"" ן¿½z׳¨׳¢׳ ן¿½Y...")
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
                self.send(uid, f"ן¿½o. ן¿½"׳₪׳§ן¿½"ן¿½" #{dep_id} ׳-ן¿½.׳©׳¨ן¿½"! ן¿½"׳₪׳§ן¿½"ן¿½.ן¿½Y ׳₪׳¢ן¿½Tן¿½o.")
                self.answer_callback(callback_id, "ן¿½o. ׳-ן¿½.׳©׳¨!", True)
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
                self.send(uid, f"ן¿½O ן¿½"׳₪׳§ן¿½"ן¿½" #{dep_id} ׳ ן¿½"ן¿½-׳×ן¿½".\n׳ ׳¡ן¿½" ׳©ן¿½.ן¿½' ׳-ן¿½. ׳₪׳ ן¿½" ן¿½o׳×ן¿½zן¿½Tן¿½>ן¿½".")
                self.answer_callback(callback_id, "ן¿½O ׳ ן¿½"ן¿½-ן¿½"", True)
        else:
            self.answer_callback(callback_id)

    # ן¿½"?ן¿½"? Text message handler ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
    # ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½
    # P2P TRADING MODULE
    # ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½
    API_BASE = "https://slh-api-production.up.railway.app"

    def _p2p_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "ן¿½Y"ן¿½ ׳©ן¿½oן¿½- ן¿½~ן¿½.׳§ן¿½Y", "callback_data": "p2p_send"},
             {"text": "ן¿½Y>' ן¿½oן¿½.ן¿½- ן¿½zן¿½>ן¿½T׳¨ן¿½.׳×", "callback_data": "p2p_browse"}],
            [{"text": "ן¿½Y'ן¿½ ׳₪׳¨׳¡׳ ן¿½zן¿½>ן¿½T׳¨ן¿½"", "callback_data": "p2p_sell"},
             {"text": "ן¿½Y"< ן¿½"ן¿½"ן¿½-ן¿½z׳ ן¿½.׳× ׳©ן¿½oן¿½T", "callback_data": "p2p_myorders"}],
            [{"text": "ן¿½Y"T ׳×׳₪׳¨ן¿½Tן¿½~ ׳¨׳-׳©ן¿½T", "callback_data": "menu_main"}],
        ]}

    def _token_keyboard(self, prefix):
        return {"inline_keyboard": [
            [{"text": "ן¿½Y'Z SLH", "callback_data": f"{prefix}_SLH"},
             {"text": "ן¿½YZן¿½ ZVK", "callback_data": f"{prefix}_ZVK"},
             {"text": "ן¿½Y'ן¿½ MNH", "callback_data": f"{prefix}_MNH"}],
            [{"text": "ן¿½O ן¿½'ן¿½Tן¿½~ן¿½.ן¿½o", "callback_data": "p2p_cancel"}],
        ]}

    def _payment_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "ן¿½Y"ן¿½ Bit", "callback_data": "pay_Bit"},
             {"text": "ן¿½Y"ן¿½ PayBox", "callback_data": "pay_PayBox"}],
            [{"text": "ן¿½Yן¿½ן¿½ Bank", "callback_data": "pay_Bank"},
             {"text": "ן¿½Y'ן¿½ MNH", "callback_data": "pay_MNH"}],
            [{"text": "ן¿½O ן¿½'ן¿½Tן¿½~ן¿½.ן¿½o", "callback_data": "p2p_cancel"}],
        ]}

    def handle_p2p_menu(self, chat_id):
        self._refresh_balances(chat_id)
        user = _get_user(chat_id)
        self.send(chat_id,
            f"ן¿½Y"" <b>P2P ן¿½z׳¡ן¿½-׳¨ ן¿½?" SLH Spark</b>\n"
            f"ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½\n\n"
            f"ן¿½Y'Z SLH: <b>{user['slh_balance']:,.4f}</b>\n"
            f"ן¿½YZן¿½ ZVK: <b>{user['zvk_balance']}</b>\n"
            f"ן¿½Y'ן¿½ MNH: <b>{user.get('mnh_balance', 0):.2f}</b>\n\n"
            f"ן¿½Y"ן¿½ <b>׳©ן¿½oן¿½- ן¿½~ן¿½.׳§ן¿½Y</b> ן¿½?" ן¿½"׳¢ן¿½'׳¨ן¿½" ן¿½T׳©ן¿½T׳¨ן¿½" ן¿½oן¿½z׳©׳×ן¿½z׳©\n"
            f"ן¿½Y>' <b>ן¿½oן¿½.ן¿½- ן¿½zן¿½>ן¿½T׳¨ן¿½.׳×</b> ן¿½?" ׳§׳ ן¿½" ן¿½zן¿½"׳§ן¿½"ן¿½Tן¿½oן¿½"\n"
            f"ן¿½Y'ן¿½ <b>׳₪׳¨׳¡׳ ן¿½zן¿½>ן¿½T׳¨ן¿½"</b> ן¿½?" ן¿½zן¿½>ן¿½.׳¨ ׳-׳× ן¿½"ן¿½~ן¿½.׳§׳ ן¿½T׳ ׳©ן¿½oן¿½s\n"
            f"ן¿½Y"< <b>ן¿½"ן¿½"ן¿½-ן¿½z׳ ן¿½.׳× ׳©ן¿½oן¿½T</b> ן¿½?" ׳ ן¿½Tן¿½"ן¿½.ן¿½o ן¿½"ן¿½-ן¿½z׳ ן¿½.׳× ׳₪׳×ן¿½.ן¿½-ן¿½.׳×",
            self._p2p_keyboard())

    # ן¿½"?ן¿½"? SEND FLOW ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
    def p2p_start_send(self, chat_id):
        self._pending_p2p[chat_id] = {"flow": "send", "step": "choose_token", "data": {}}
        self.send(chat_id, "ן¿½Y"ן¿½ <b>׳©ן¿½oן¿½- ן¿½~ן¿½.׳§ן¿½Y</b>\n\nן¿½'ן¿½-׳¨ ׳-ן¿½Tן¿½-ן¿½" ן¿½~ן¿½.׳§ן¿½Y ן¿½o׳©ן¿½oן¿½.ן¿½-:", self._token_keyboard("send_tok"))

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
                    self.send(chat_id, "ן¿½O ׳-ן¿½T ׳-׳₪׳©׳¨ ן¿½o׳©ן¿½oן¿½.ן¿½- ן¿½o׳¢׳¦ן¿½zן¿½s.")
                    return True
                data["to_user"] = to_user
                state["step"] = "enter_amount"
                self.send(chat_id,
                    f"ן¿½Y'ן¿½ <b>ן¿½>ן¿½zן¿½" {data['token']} ן¿½o׳©ן¿½oן¿½.ן¿½-?</b>\n"
                    f"ן¿½"ן¿½T׳×׳¨ן¿½" ׳©ן¿½oן¿½s: {self._get_balance_for(chat_id, data['token']):.4f}\n\n"
                    f"ן¿½"ן¿½>׳ ׳¡ ׳¡ן¿½>ן¿½.׳ (ן¿½z׳¡׳₪׳¨ ן¿½'ן¿½oן¿½'ן¿½"):")
            except ValueError:
                self.send(chat_id, "ן¿½O User ID ן¿½o׳- ׳×׳§ן¿½Tן¿½Y. ן¿½"ן¿½>׳ ׳¡ ן¿½z׳¡׳₪׳¨ ן¿½'ן¿½oן¿½'ן¿½" (ן¿½oן¿½"ן¿½.ן¿½'ן¿½zן¿½": 224223270)")
            return True

        if step == "enter_amount":
            try:
                amount = float(text.strip())
                if amount <= 0:
                    raise ValueError
                bal = self._get_balance_for(chat_id, data["token"])
                if amount > bal:
                    self.send(chat_id, f"ן¿½O ן¿½T׳×׳¨ן¿½" ן¿½o׳- ן¿½z׳¡׳₪ן¿½T׳§ן¿½". ן¿½T׳© ן¿½oן¿½s {bal:.4f} {data['token']}")
                    return True
                data["amount"] = amount
                state["step"] = "confirm"
                self.send(chat_id,
                    f"ן¿½o. <b>׳-ן¿½T׳©ן¿½.׳¨ ן¿½"׳¢ן¿½'׳¨ן¿½"</b>\n\n"
                    f"ן¿½Y"ן¿½ ׳©ן¿½.ן¿½oן¿½-: <b>{amount} {data['token']}</b>\n"
                    f"ן¿½Y'ן¿½ ן¿½oן¿½z׳©׳×ן¿½z׳© ID: <code>{data['to_user']}</code>\n\n"
                    f"׳©ן¿½oן¿½- <b>ן¿½>ן¿½Y</b> ן¿½o׳-ן¿½T׳©ן¿½.׳¨ ׳-ן¿½. <b>ן¿½o׳-</b> ן¿½oן¿½'ן¿½Tן¿½~ן¿½.ן¿½o:")
            except ValueError:
                self.send(chat_id, "ן¿½O ׳¡ן¿½>ן¿½.׳ ן¿½o׳- ׳×׳§ן¿½Tן¿½Y. ן¿½"ן¿½>׳ ׳¡ ן¿½z׳¡׳₪׳¨ (ן¿½oן¿½"ן¿½.ן¿½'ן¿½zן¿½": 10.5)")
            return True

        if step == "confirm":
            if text.strip().lower() in ("ן¿½>ן¿½Y", "yes", "׳-ן¿½T׳©ן¿½.׳¨", "ן¿½o."):
                self._p2p_execute_send(chat_id, data)
            else:
                del self._pending_p2p[chat_id]
                self.send(chat_id, "ן¿½O ן¿½"׳¢ן¿½'׳¨ן¿½" ן¿½'ן¿½.ן¿½~ן¿½oן¿½".", self.main_reply_keyboard())
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
                    f"ן¿½o. <b>׳ ׳©ן¿½oן¿½- ן¿½'ן¿½"׳¦ן¿½oן¿½-ן¿½"!</b>\n\n"
                    f"ן¿½Y'ן¿½ <b>{data['amount']} {data['token']}</b> ן¿½?' ן¿½z׳©׳×ן¿½z׳© <code>{data['to_user']}</code>\n"
                    f"ן¿½Yן¿½ן¿½ TX: #{result.get('transfer_id', 'ן¿½?"')}\n\n"
                    f"ן¿½Y'ן¿½ /wallet ן¿½o׳¦׳₪ן¿½Tן¿½Tן¿½" ן¿½'ן¿½T׳×׳¨ן¿½"", self.main_reply_keyboard())
                # Notify receiver
                self.send(data["to_user"],
                    f"ן¿½Y'ן¿½ <b>׳§ן¿½Tן¿½'ן¿½o׳× {data['amount']} {data['token']}!</b>\n\n"
                    f"ן¿½Y'ן¿½ ן¿½z: ן¿½z׳©׳×ן¿½z׳© {chat_id}\n"
                    f"ן¿½Y'ן¿½ /wallet ן¿½o׳¦׳₪ן¿½Tן¿½Tן¿½" ן¿½'ן¿½T׳×׳¨ן¿½"")
            else:
                err = result.get("detail", result.get("error", "׳©ן¿½'ן¿½T׳-ן¿½" ן¿½o׳- ן¿½Tן¿½"ן¿½.׳¢ן¿½""))
                self.send(chat_id, f"ן¿½O {err}", self.main_reply_keyboard())
        except Exception as e:
            logger.error(f"P2P send error: {e}")
            self.send(chat_id, "ן¿½O ׳©ן¿½'ן¿½T׳-ן¿½" ן¿½'׳©ן¿½oן¿½Tן¿½-ן¿½". ׳ ׳¡ן¿½" ׳©ן¿½.ן¿½'.", self.main_reply_keyboard())
        finally:
            self._pending_p2p.pop(chat_id, None)

    # ן¿½"?ן¿½"? SELL FLOW ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
    def p2p_start_sell(self, chat_id):
        self._refresh_balances(chat_id)
        user = _get_user(chat_id)
        if user["slh_balance"] <= 0 and user["zvk_balance"] <= 0 and user.get("mnh_balance", 0) <= 0:
            self.send(chat_id, "ן¿½O ׳-ן¿½Tן¿½Y ן¿½oן¿½s ן¿½~ן¿½.׳§׳ ן¿½T׳ ן¿½oן¿½zן¿½>ן¿½T׳¨ן¿½".", self.main_reply_keyboard())
            return
        self._pending_p2p[chat_id] = {"flow": "sell", "step": "choose_token", "data": {}}
        self.send(chat_id, "ן¿½Y'ן¿½ <b>׳₪׳¨׳¡׳ ן¿½zן¿½>ן¿½T׳¨ן¿½"</b>\n\nן¿½'ן¿½-׳¨ ׳-ן¿½Tן¿½-ן¿½" ן¿½~ן¿½.׳§ן¿½Y ן¿½oן¿½zן¿½>ן¿½.׳¨:", self._token_keyboard("sell_tok"))

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
                    self.send(chat_id, f"ן¿½O ן¿½T׳×׳¨ן¿½" ן¿½o׳- ן¿½z׳¡׳₪ן¿½T׳§ן¿½". ן¿½T׳© ן¿½oן¿½s {bal:.4f} {data['token']}")
                    return True
                data["amount"] = amount
                state["step"] = "enter_price"
                self.send(chat_id,
                    f"ן¿½Y'ן¿½ <b>ן¿½zן¿½-ן¿½T׳¨ ן¿½oן¿½>ן¿½o {data['token']} (ן¿½'׳©׳§ן¿½oן¿½T׳ ן¿½,ן¿½)</b>\n\n"
                    f"ן¿½oן¿½"ן¿½.ן¿½'ן¿½zן¿½": ׳-׳ SLH = 444ן¿½,ן¿½, ן¿½"ן¿½>׳ ׳¡ <b>444</b>\n"
                    f"ן¿½"ן¿½>׳ ׳¡ ן¿½zן¿½-ן¿½T׳¨:")
            except ValueError:
                self.send(chat_id, "ן¿½O ׳¡ן¿½>ן¿½.׳ ן¿½o׳- ׳×׳§ן¿½Tן¿½Y.")
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
                    f"ן¿½Y'ן¿½ <b>׳©ן¿½Tן¿½~׳× ׳×׳©ן¿½oן¿½.׳ ן¿½zן¿½.׳¢ן¿½"׳₪׳×</b>\n\n"
                    f"׳×׳§ן¿½'ן¿½o: <b>{total:.2f} ן¿½,ן¿½</b> ׳¢ן¿½'ן¿½.׳¨ {data['amount']} {data['token']}\n\n"
                    f"ן¿½'ן¿½-׳¨ ׳-ן¿½Tן¿½s ן¿½o׳§ן¿½'ן¿½o ׳×׳©ן¿½oן¿½.׳:", self._payment_keyboard())
            except ValueError:
                self.send(chat_id, "ן¿½O ן¿½zן¿½-ן¿½T׳¨ ן¿½o׳- ׳×׳§ן¿½Tן¿½Y.")
            return True

        if step == "confirm":
            if text.strip().lower() in ("ן¿½>ן¿½Y", "yes", "׳-ן¿½T׳©ן¿½.׳¨", "ן¿½o."):
                self._p2p_execute_sell(chat_id, data)
            else:
                del self._pending_p2p[chat_id]
                self.send(chat_id, "ן¿½O ן¿½zן¿½>ן¿½T׳¨ן¿½" ן¿½'ן¿½.ן¿½~ן¿½oן¿½".", self.main_reply_keyboard())
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
                    f"ן¿½o. <b>ן¿½"ן¿½-ן¿½z׳ ׳× ן¿½zן¿½>ן¿½T׳¨ן¿½" ׳ ן¿½.׳¦׳¨ן¿½"!</b>\n\n"
                    f"ן¿½Y?" ן¿½"ן¿½-ן¿½z׳ ן¿½": <b>#{order['id']}</b>\n"
                    f"ן¿½Y'ן¿½ ן¿½zן¿½.ן¿½>׳¨: <b>{order['amount']} {order['token']}</b>\n"
                    f"ן¿½Y'ן¿½ ן¿½zן¿½-ן¿½T׳¨: <b>{order['price_per_unit']} ן¿½,ן¿½</b> ן¿½oן¿½Tן¿½-ן¿½Tן¿½"ן¿½"\n"
                    f"ן¿½Y"S ׳¡ן¿½"\"ן¿½>: <b>{order['amount'] * order['price_per_unit']:.2f} ן¿½,ן¿½</b>\n"
                    f"ן¿½Y'ן¿½ ׳×׳©ן¿½oן¿½.׳: <b>{order['payment_method']}</b>\n\n"
                    f"ן¿½Y"' ן¿½"ן¿½~ן¿½.׳§׳ ן¿½T׳ ׳ ׳ ׳¢ן¿½oן¿½. ן¿½'-escrow ן¿½?" ן¿½Tן¿½.׳¢ן¿½'׳¨ן¿½. ן¿½o׳§ן¿½.׳ ן¿½" ׳-ן¿½.ן¿½~ן¿½.ן¿½zן¿½~ן¿½T׳×.\n"
                    f"ן¿½oן¿½'ן¿½Tן¿½~ן¿½.ן¿½o: ן¿½Y"< ן¿½"ן¿½"ן¿½-ן¿½z׳ ן¿½.׳× ׳©ן¿½oן¿½T", self.main_reply_keyboard())
                # Refresh balance (tokens were escrowed)
                self._refresh_balances(chat_id)
            else:
                err = result.get("detail", "׳©ן¿½'ן¿½T׳-ן¿½" ן¿½o׳- ן¿½Tן¿½"ן¿½.׳¢ן¿½"")
                self.send(chat_id, f"ן¿½O {err}", self.main_reply_keyboard())
        except Exception as e:
            logger.error(f"P2P sell error: {e}")
            self.send(chat_id, "ן¿½O ׳©ן¿½'ן¿½T׳-ן¿½" ן¿½'ן¿½T׳¦ן¿½T׳¨׳× ן¿½"ן¿½-ן¿½z׳ ן¿½".", self.main_reply_keyboard())
        finally:
            self._pending_p2p.pop(chat_id, None)

    # ן¿½"?ן¿½"? BROWSE + BUY ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
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
                    "ן¿½Y>' <b>ן¿½oן¿½.ן¿½- ן¿½zן¿½>ן¿½T׳¨ן¿½.׳×</b>\n\n׳-ן¿½Tן¿½Y ן¿½"ן¿½-ן¿½z׳ ן¿½.׳× ׳₪׳×ן¿½.ן¿½-ן¿½.׳× ן¿½>׳¨ן¿½'׳¢.\n"
                    "ן¿½"ן¿½Tן¿½" ן¿½"׳¨׳-׳©ן¿½.ן¿½Y ן¿½o׳₪׳¨׳¡׳! ן¿½?' ן¿½Y'ן¿½ ׳₪׳¨׳¡׳ ן¿½zן¿½>ן¿½T׳¨ן¿½"", self.main_reply_keyboard())
                return

            text = "ן¿½Y>' <b>ן¿½oן¿½.ן¿½- ן¿½zן¿½>ן¿½T׳¨ן¿½.׳× ן¿½?" ן¿½"ן¿½-ן¿½z׳ ן¿½.׳× ׳₪׳×ן¿½.ן¿½-ן¿½.׳×</b>\nן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½\n\n"
            buttons = []
            for o in orders[:8]:
                total = o["amount"] * o["price_per_unit"]
                text += (
                    f"ן¿½Y"- <b>#{o['id']}</b> | {o['token']} | {o['amount']:.4f} ן¿½Tן¿½-ן¿½Tן¿½"ן¿½.׳×\n"
                    f"   ן¿½Y'ן¿½ {o['price_per_unit']} ן¿½,ן¿½/ן¿½Tן¿½-ן¿½Tן¿½"ן¿½" | ׳¡ן¿½"\"ן¿½>: <b>{total:.2f} ן¿½,ן¿½</b>\n"
                    f"   ן¿½Y'ן¿½ {o['payment_method']} | ן¿½Y'ן¿½ ן¿½zן¿½.ן¿½>׳¨: {o['seller_id']}\n\n"
                )
                if o["seller_id"] != chat_id:
                    buttons.append([{"text": f"ן¿½Y>' ׳§׳ ן¿½" #{o['id']} ({o['amount']:.2f} {o['token']})",
                                     "callback_data": f"p2p_buy_{o['id']}"}])

            buttons.append([{"text": "ן¿½Y'ן¿½ ׳₪׳¨׳¡׳ ן¿½zן¿½>ן¿½T׳¨ן¿½"", "callback_data": "p2p_sell"},
                             {"text": "ן¿½Y"T P2P", "callback_data": "p2p_menu"}])
            self.send(chat_id, text, {"inline_keyboard": buttons})
        except Exception as e:
            logger.error(f"P2P browse error: {e}")
            self.send(chat_id, "ן¿½O ׳©ן¿½'ן¿½T׳-ן¿½" ן¿½'ן¿½~׳¢ן¿½T׳ ׳× ן¿½oן¿½.ן¿½- ן¿½zן¿½>ן¿½T׳¨ן¿½.׳×.", self.main_reply_keyboard())

    def p2p_buy(self, chat_id, order_id):
        """Fill an order (buy from seller)."""
        try:
            # Fetch order details first
            resp = self.session.get(f"{self.API_BASE}/api/p2p/orders",
                                    params={"status": "active", "limit": 50}, timeout=8)
            orders = {o["id"]: o for o in resp.json().get("orders", [])}
            order = orders.get(order_id)
            if not order:
                self.send(chat_id, "ן¿½O ן¿½"ן¿½-ן¿½z׳ ן¿½" ן¿½o׳- ׳ ן¿½z׳¦׳-ן¿½" ׳-ן¿½. ן¿½>ן¿½'׳¨ ׳ ׳¡ן¿½'׳¨ן¿½".", self.main_reply_keyboard())
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
                    f"ן¿½o. <b>׳¨ן¿½>ן¿½T׳©ן¿½" ן¿½"ן¿½.׳©ן¿½oן¿½zן¿½"!</b>\n\n"
                    f"ן¿½Y'ן¿½ ׳§ן¿½Tן¿½'ן¿½o׳×: <b>{order['amount']:.4f} {order['token']}</b>\n"
                    f"ן¿½Y'ן¿½ ן¿½o׳©ן¿½o׳: <b>{total:.2f} ן¿½,ן¿½</b>\n"
                    f"ן¿½Y'ן¿½ ׳©ן¿½Tן¿½~ן¿½": <b>{order['payment_method']}</b>\n"
                    f"ן¿½Y'ן¿½ ן¿½zן¿½.ן¿½>׳¨ ID: <code>{order['seller_id']}</code>\n\n"
                    f"ן¿½sן¿½ן¸ <b>׳©ן¿½o׳ ן¿½oן¿½zן¿½.ן¿½>׳¨ ן¿½T׳©ן¿½T׳¨ן¿½.׳×!</b>\n"
                    f"׳©ן¿½oן¿½- ן¿½oן¿½. ן¿½"ן¿½.ן¿½"׳¢ן¿½" ן¿½'-Telegram ׳¢׳ ID: <code>{order['seller_id']}</code>\n"
                    f"ן¿½"ן¿½~ן¿½.׳§׳ ן¿½T׳ ן¿½>ן¿½'׳¨ ן¿½-ן¿½.ן¿½>ן¿½. ן¿½oן¿½-׳©ן¿½'ן¿½.׳ ן¿½s ן¿½?" /wallet ן¿½o׳¦׳₪ן¿½Tן¿½Tן¿½".",
                    self.main_reply_keyboard())
                # Notify seller
                self.send(order["seller_id"],
                    f"ן¿½YZ? <b>ן¿½"ן¿½-ן¿½z׳ ן¿½" #{order_id} ׳ ן¿½zן¿½>׳¨ן¿½"!</b>\n\n"
                    f"ן¿½Y'ן¿½ {order['amount']:.4f} {order['token']}\n"
                    f"ן¿½Y'ן¿½ ן¿½o׳§ן¿½'ן¿½o: <b>{total:.2f} ן¿½,ן¿½</b> ן¿½z-{order['payment_method']}\n"
                    f"ן¿½Y'ן¿½ ׳§ן¿½.׳ ן¿½" ID: <code>{chat_id}</code>\n\n"
                    f"ן¿½zן¿½z׳×ן¿½Tן¿½Y ן¿½o׳×׳©ן¿½oן¿½.׳ ן¿½zן¿½z׳ ן¿½.!")
                self._refresh_balances(chat_id)
            else:
                err = result.get("detail", "׳©ן¿½'ן¿½T׳-ן¿½" ן¿½o׳- ן¿½Tן¿½"ן¿½.׳¢ן¿½"")
                self.send(chat_id, f"ן¿½O {err}", self.main_reply_keyboard())
        except Exception as e:
            logger.error(f"P2P buy error: {e}")
            self.send(chat_id, "ן¿½O ׳©ן¿½'ן¿½T׳-ן¿½" ן¿½'׳¨ן¿½>ן¿½T׳©ן¿½".", self.main_reply_keyboard())

    # ן¿½"?ן¿½"? MY ORDERS ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
    def p2p_my_orders(self, chat_id):
        try:
            resp = self.session.get(f"{self.API_BASE}/api/p2p/orders",
                                    params={"status": "active", "limit": 50}, timeout=8)
            all_orders = resp.json().get("orders", [])
            mine = [o for o in all_orders if o["seller_id"] == chat_id]

            if not mine:
                self.send(chat_id,
                    "ן¿½Y"< <b>ן¿½"ן¿½"ן¿½-ן¿½z׳ ן¿½.׳× ׳©ן¿½oן¿½T</b>\n\n׳-ן¿½Tן¿½Y ן¿½oן¿½s ן¿½"ן¿½-ן¿½z׳ ן¿½.׳× ׳₪׳×ן¿½.ן¿½-ן¿½.׳×.\nן¿½Y'ן¿½ ׳¨ן¿½.׳¦ן¿½" ן¿½oן¿½zן¿½>ן¿½.׳¨? ן¿½?' ׳₪׳¨׳¡׳ ן¿½zן¿½>ן¿½T׳¨ן¿½"",
                    self._p2p_keyboard())
                return

            text = "ן¿½Y"< <b>ן¿½"ן¿½"ן¿½-ן¿½z׳ ן¿½.׳× ׳©ן¿½oן¿½T</b>\nן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½\n\n"
            buttons = []
            for o in mine:
                total = o["amount"] * o["price_per_unit"]
                text += (
                    f"ן¿½Y"- <b>#{o['id']}</b> | {o['token']}\n"
                    f"   ן¿½Y'ן¿½ {o['amount']:.4f} | {o['price_per_unit']} ן¿½,ן¿½/ן¿½Tן¿½-' | ׳¡ן¿½"\"ן¿½> {total:.2f} ן¿½,ן¿½\n"
                    f"   ן¿½Y'ן¿½ {o['payment_method']}\n\n"
                )
                buttons.append([{"text": f"ן¿½O ן¿½'ן¿½~ן¿½o ן¿½"ן¿½-ן¿½z׳ ן¿½" #{o['id']}",
                                  "callback_data": f"p2p_cancel_order_{o['id']}"}])

            buttons.append([{"text": "ן¿½Y"T P2P", "callback_data": "p2p_menu"}])
            self.send(chat_id, text, {"inline_keyboard": buttons})
        except Exception as e:
            logger.error(f"P2P my_orders error: {e}")
            self.send(chat_id, "ן¿½O ׳©ן¿½'ן¿½T׳-ן¿½" ן¿½'ן¿½~׳¢ן¿½T׳ ׳× ן¿½"ן¿½-ן¿½z׳ ן¿½.׳×.", self.main_reply_keyboard())

    def p2p_cancel_order(self, chat_id, order_id):
        try:
            resp = self.session.delete(
                f"{self.API_BASE}/api/p2p/cancel-order/{order_id}",
                params={"seller_id": chat_id}, timeout=10
            )
            result = resp.json()
            if resp.status_code == 200 and result.get("ok"):
                self.send(chat_id,
                    f"ן¿½o. <b>ן¿½"ן¿½-ן¿½z׳ ן¿½" #{order_id} ן¿½'ן¿½.ן¿½~ן¿½oן¿½"</b>\n\n"
                    f"ן¿½Y"" ן¿½"ן¿½.ן¿½-ן¿½-׳¨: <b>{result['refunded_amount']} {result['refunded_token']}</b>\n"
                    f"ן¿½Y'ן¿½ /wallet ן¿½o׳¦׳₪ן¿½Tן¿½Tן¿½" ן¿½'ן¿½T׳×׳¨ן¿½"", self.main_reply_keyboard())
                self._refresh_balances(chat_id)
            else:
                err = result.get("detail", "׳©ן¿½'ן¿½T׳-ן¿½"")
                self.send(chat_id, f"ן¿½O {err}", self.main_reply_keyboard())
        except Exception as e:
            logger.error(f"P2P cancel order error: {e}")
            self.send(chat_id, "ן¿½O ׳©ן¿½'ן¿½T׳-ן¿½" ן¿½'ן¿½'ן¿½Tן¿½~ן¿½.ן¿½o.", self.main_reply_keyboard())

    # ן¿½"?ן¿½"? P2P CALLBACK DISPATCHER ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
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
            self.send(chat_id, "ן¿½O ן¿½'ן¿½.ן¿½~ן¿½o.", self.main_reply_keyboard())

        # Token selection for send
        elif data.startswith("send_tok_"):
            token = data.split("_")[-1]
            state = self._pending_p2p.get(chat_id, {})
            if state.get("flow") == "send":
                state["data"]["token"] = token
                state["step"] = "enter_recipient"
                self.send(chat_id,
                    f"ן¿½Y"ן¿½ <b>׳©ן¿½oן¿½- {token}</b>\n\n"
                    f"ן¿½"ן¿½>׳ ׳¡ ׳-׳× ן¿½"-Telegram User ID ׳©ן¿½o ן¿½"׳ ן¿½z׳¢ן¿½Y:\n"
                    f"(ן¿½"׳ ן¿½z׳¢ן¿½Y ן¿½Tן¿½>ן¿½.ן¿½o ן¿½o׳©ן¿½oן¿½.ן¿½- /myid ן¿½>ן¿½"ן¿½T ן¿½oן¿½"׳¢׳× ׳-׳× ן¿½"-ID ׳©ן¿½oן¿½.)")

        # Token selection for sell
        elif data.startswith("sell_tok_"):
            token = data.split("_")[-1]
            state = self._pending_p2p.get(chat_id, {})
            if state.get("flow") == "sell":
                bal = self._get_balance_for(chat_id, token)
                if bal <= 0:
                    self.send(chat_id, f"ן¿½O ׳-ן¿½Tן¿½Y ן¿½oן¿½s {token} ן¿½oן¿½zן¿½>ן¿½T׳¨ן¿½".")
                    return
                state["data"]["token"] = token
                state["step"] = "enter_amount"
                self.send(chat_id,
                    f"ן¿½Y'ן¿½ <b>ן¿½>ן¿½zן¿½" {token} ן¿½oן¿½zן¿½>ן¿½.׳¨?</b>\n"
                    f"ן¿½"ן¿½T׳×׳¨ן¿½" ׳©ן¿½oן¿½s: <b>{bal:.4f}</b>\n\n"
                    f"ן¿½"ן¿½>׳ ׳¡ ן¿½>ן¿½zן¿½.׳×:")

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
                    f"ן¿½o. <b>׳-ן¿½T׳©ן¿½.׳¨ ׳₪׳¨׳¡ן¿½.׳ ן¿½zן¿½>ן¿½T׳¨ן¿½"</b>\n\n"
                    f"ן¿½Y'ן¿½ ן¿½zן¿½.ן¿½>׳¨: <b>{d['amount']} {d['token']}</b>\n"
                    f"ן¿½Y'ן¿½ ן¿½zן¿½-ן¿½T׳¨: <b>{d['price']} ן¿½,ן¿½</b> ן¿½oן¿½Tן¿½-ן¿½Tן¿½"ן¿½"\n"
                    f"ן¿½Y"S ׳¡ן¿½"\"ן¿½>: <b>{total:.2f} ן¿½,ן¿½</b>\n"
                    f"ן¿½Y'ן¿½ ׳×׳©ן¿½oן¿½.׳: <b>{method}</b>\n\n"
                    f"ן¿½Y"' ן¿½"ן¿½~ן¿½.׳§׳ ן¿½T׳ ן¿½T׳ ׳¢ן¿½oן¿½. ן¿½'-escrow ׳¢ן¿½" ן¿½oן¿½zן¿½>ן¿½T׳¨ן¿½".\n\n"
                    f"׳©ן¿½oן¿½- <b>ן¿½>ן¿½Y</b> ן¿½o׳-ן¿½T׳©ן¿½.׳¨ ׳-ן¿½. <b>ן¿½o׳-</b> ן¿½oן¿½'ן¿½Tן¿½~ן¿½.ן¿½o:")

        # Buy order
        elif data.startswith("p2p_buy_"):
            order_id = int(data.split("_")[-1])
            self.p2p_buy(chat_id, order_id)

        # Cancel own order
        elif data.startswith("p2p_cancel_order_"):
            order_id = int(data.split("_")[-1])
            self.p2p_cancel_order(chat_id, order_id)

    # ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½ן¿½.ן¿½

    def handle_text(self, chat_id, text, first_name, username):
        """Handle non-command text and legacy reply keyboard buttons.

        STRICT rules ן¿½?" no more 'any text = payment':
        - Valid username: 3ן¿½?"32 chars of [A-Za-z0-9_], and user is in username-collection state
        - Valid BSC/ETH TX hash: '0x' + exactly 64 hex chars (66 total)
        - Valid TON TX hash: 44 base64 chars OR 64 hex chars
        - Anything else ן¿½?' polite fallback (no false "payment received")
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
                f"ן¿½o. <b>׳ ׳¨׳©ן¿½z׳×!</b> @{text}\n\n"
                f"ן¿½Y'ן¿½ ן¿½o׳¨ן¿½>ן¿½T׳©ן¿½" ׳©ן¿½oן¿½- ן¿½o׳-׳¨׳ ׳§ TON:\n<code>{TON_WALLET}</code>\n\n"
                "ן¿½Y"ן¿½ ׳©ן¿½oן¿½- ׳¦ן¿½Tן¿½oן¿½.׳ ן¿½z׳¡ן¿½s ׳-ן¿½. Transaction Hash",
                self.back_keyboard())
            if str(chat_id) != ADMIN_ID:
                self.send(int(ADMIN_ID), f"ן¿½Y'ן¿½ <b>ן¿½z׳©׳×ן¿½z׳© ן¿½-ן¿½"׳©:</b> @{text} ({chat_id})")
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
                "ן¿½Y"ן¿½ <b>׳×׳©ן¿½oן¿½.׳ ן¿½"׳×׳§ן¿½'ן¿½o ן¿½oן¿½'ן¿½"ן¿½T׳§ן¿½"!</b>\n\n"
                "ן¿½Y"- Hash: <code>" + text[:20] + "...</code>\n"
                "ג³ ׳¡ן¿½~ן¿½~ן¿½.׳¡: <b>ן¿½zן¿½z׳×ן¿½Tן¿½Y ן¿½o׳-ן¿½T׳©ן¿½.׳¨ ׳-ן¿½"ן¿½zן¿½Tן¿½Y</b>\n\n"
                "׳×׳§ן¿½'ן¿½o ן¿½"׳×׳¨׳-ן¿½" ן¿½'׳¨ן¿½'׳¢ ׳©ן¿½"׳×׳©ן¿½oן¿½.׳ ן¿½T׳-ן¿½.ן¿½z׳× (׳¢ן¿½" 24 ׳©׳¢ן¿½.׳×).\n"
                "ן¿½Y'ן¿½ ן¿½'ן¿½T׳ ׳×ן¿½Tן¿½T׳, ן¿½"׳¦ן¿½~׳¨׳£: @SLH_Community",
                self.back_keyboard())
            if str(chat_id) != ADMIN_ID:
                self.send(int(ADMIN_ID),
                    f"ן¿½Y'ן¿½ <b>׳¢׳¡׳§ן¿½" ן¿½-ן¿½"׳©ן¿½" ן¿½o׳-ן¿½T׳©ן¿½.׳¨!</b>\n"
                    f"User: {chat_id} (@{user.get('username','?')})\n"
                    f"Hash: <code>{text}</code>\n"
                    f"/approve_{chat_id} ׳-ן¿½. /reject_{chat_id}")
            return

        # --- 3) TX hash received OUT OF state ן¿½?' tell user to start flow ---
        if is_tx_hash and state != "awaiting_payment":
            self.send(chat_id,
                "ן¿½sן¿½ן¸ ׳§ן¿½Tן¿½'ן¿½o׳×ן¿½T Hash ׳-ן¿½'ן¿½o ׳-ן¿½Tן¿½Y ן¿½'׳§׳©׳× ׳×׳©ן¿½oן¿½.׳ ׳₪׳×ן¿½.ן¿½-ן¿½".\n\n"
                "ן¿½o׳×׳©ן¿½oן¿½.׳ ן¿½-ן¿½"׳©, ן¿½oן¿½-׳¥ /start ן¿½?' ן¿½Y'ן¿½ ן¿½"׳₪׳¢ן¿½oן¿½"",
                self.main_reply_keyboard())
            return

        # --- 4) Wallet address (informational only, no payment assumed) ---
        if re.match(r'^(0x[0-9a-fA-F]{40}|[UE]Q[A-Za-z0-9_-]{46})$', text):
            self.send(chat_id,
                "ן¿½Y"< ׳§ן¿½Tן¿½'ן¿½o׳×ן¿½T ן¿½>׳×ן¿½.ן¿½'׳× ׳-׳¨׳ ׳§. ן¿½o׳©ן¿½oן¿½.ן¿½- ן¿½>׳¡׳£ ׳-ן¿½o ן¿½>׳×ן¿½.ן¿½'׳× ן¿½-ן¿½.? ן¿½oן¿½-׳¥ /start ן¿½?' ן¿½Y'ן¿½ ׳-׳¨׳ ׳§\n\n"
                "ן¿½sן¿½ן¸ ׳©ן¿½T׳ ן¿½oן¿½': ׳©ן¿½oן¿½Tן¿½-׳× ן¿½>׳×ן¿½.ן¿½'׳× ן¿½oן¿½'ן¿½" ן¿½o׳- ׳₪ן¿½.׳×ן¿½-׳× ׳×׳©ן¿½oן¿½.׳.",
                self.main_reply_keyboard())
            return

        # --- 5) Fallback (no more false payment confirmations) ---
        # If user is in payment state but didn't send TX hash or photo ן¿½?" remind them
        if state == "awaiting_payment":
            self.send(chat_id,
                "ן¿½sן¿½ן¸ <b>׳©ן¿½oן¿½' ן¿½"׳×׳©ן¿½oן¿½.׳ ׳₪׳×ן¿½.ן¿½-!</b>\n\n"
                "ן¿½>ן¿½"ן¿½T ן¿½oן¿½"׳©ן¿½oן¿½T׳:\n"
                "1ן¸ן¿½fן¿½ ן¿½"׳¢ן¿½'׳¨ TON ן¿½oן¿½>׳×ן¿½.ן¿½'׳×:\n<code>" + TON_WALLET + "</code>\n\n"
                "2ן¸ן¿½fן¿½ ׳©ן¿½oן¿½- ן¿½oן¿½T <b>׳¦ן¿½Tן¿½oן¿½.׳ ן¿½z׳¡ן¿½s</b> ׳©ן¿½o ן¿½"ן¿½"׳¢ן¿½'׳¨ן¿½"\n"
                "   ׳-ן¿½. <b>Transaction Hash</b>\n\n"
                "ן¿½Y"ן¿½ ׳-׳₪׳©׳¨ ן¿½o׳©ן¿½oן¿½.ן¿½- ׳×ן¿½zן¿½.׳ ן¿½" ן¿½T׳©ן¿½T׳¨ן¿½.׳× ן¿½o׳¦'׳-ן¿½~ ן¿½"ן¿½-ן¿½"!\n\n"
                "ן¿½" ׳¦׳¨ן¿½Tן¿½s ׳¢ן¿½-׳¨ן¿½"? ׳¦ן¿½.׳¨ ׳§׳©׳¨: @osifeu_prog",
                self.back_keyboard())
            return

        self.send(chat_id, "ן¿½Yן¿½- ן¿½o׳- ן¿½"ן¿½'׳ ׳×ן¿½T. ן¿½oן¿½-׳¥ /start ן¿½o׳×׳₪׳¨ן¿½Tן¿½~ ן¿½"׳¨׳-׳©ן¿½T", self.main_reply_keyboard())

    # ן¿½"?ן¿½"? Main loop ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
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
                        self.send(chat_id, "ן¿½Y"ן¿½ ׳§ן¿½'ן¿½o׳ ן¿½.! ׳ ן¿½'ן¿½"ן¿½.׳§ ן¿½.׳ ׳¢ן¿½"ן¿½>ן¿½Y ן¿½'ן¿½"׳§ן¿½"׳.", self.back_keyboard())
                        if str(chat_id) != ADMIN_ID:
                            self.send(int(ADMIN_ID), f"ן¿½Y"ן¿½ <b>ן¿½"ן¿½.ן¿½>ן¿½-׳× ׳×׳©ן¿½oן¿½.׳!</b>\nUser: {chat_id} (@{username})")
                    continue

                logger.info(f"ן¿½Y"ן¿½ {first_name}: {text}")

                # ן¿½"?ן¿½"? Slash commands ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
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
                        self.send(chat_id, "׳©ן¿½Tן¿½zן¿½.׳©: /send TOKEN USER_ID AMOUNT\nן¿½"ן¿½.ן¿½'ן¿½zן¿½": /send ZVK 123456789 50")
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
                    self.send(chat_id, "ן¿½Y"z <b>׳×ן¿½zן¿½Tן¿½>ן¿½"</b>\n\n׳₪׳ ן¿½" ן¿½o-@Osif83 ן¿½oן¿½>ן¿½o ׳©׳-ן¿½oן¿½".", self.main_reply_keyboard())
                elif text == "/myid":
                    self.send(chat_id, f"ן¿½Y?" <b>ן¿½"ן¿½zן¿½-ן¿½"ן¿½" ׳©ן¿½oן¿½s:</b> <code>{chat_id}</code>", self.main_reply_keyboard())
                elif text == "/hub":
                    user = _get_user(chat_id)
                    vip_badge = "ן¿½Y'' VIP" if user["vip"] else "ן¿½Y?" Free"
                    self.send(chat_id,
                        f"ן¿½Ys? <b>SLH HUB SYSTEM</b>\n\n"
                        f"ן¿½Y'ן¿½ <b>{first_name}</b> | {vip_badge}\n"
                        f"ן¿½Y'ן¿½ ן¿½T׳×׳¨ן¿½": <b>{user['hub_points']}</b> ׳ ׳§ן¿½.ן¿½"ן¿½.׳×\n"
                        f"ן¿½Y'Z SLH: <b>{user['slh_balance']:.2f}</b>\n"
                        f"ן¿½Y'ן¿½ ן¿½"׳₪׳ ן¿½Tן¿½.׳×: <b>{user['referral_count']}</b>\n\nן¿½Y'? ן¿½'ן¿½-׳¨ ׳₪׳¢ן¿½.ן¿½oן¿½":",
                        self.hub_inline_keyboard())

                # ן¿½"?ן¿½"? Reply keyboard buttons (text buttons at bottom) ן¿½"?ן¿½"?
                elif text == "ן¿½Y"S ן¿½"׳©ן¿½.׳§ ׳¢ן¿½>׳©ן¿½Tן¿½.":
                    self.handle_prices(chat_id)
                elif text == "ן¿½Y'ן¿½ ן¿½"׳©׳§׳¢ן¿½.׳×":
                    self.handle_investments(chat_id)
                elif text == "ן¿½Y'ן¿½ ׳-׳¨׳ ׳§":
                    self.handle_wallet(chat_id)
                elif text == "ן¿½Y"" P2P ן¿½z׳¡ן¿½-׳¨":
                    self.handle_p2p_menu(chat_id)
                elif text == "ן¿½Y"- On-Chain":
                    self.handle_onchain_balance(chat_id)
                elif text == "ן¿½Y>ן¿½ ׳¡ן¿½Tן¿½>ן¿½.ן¿½Y ן¿½.ן¿½'׳§׳¨ן¿½"":
                    self.handle_risk(chat_id)
                elif text == "ן¿½YZן¿½ ן¿½'ן¿½.׳ ן¿½.׳¡ן¿½T׳":
                    self.handle_bonuses(chat_id)
                elif text == "ן¿½Y'ן¿½ ן¿½"ן¿½-ן¿½zן¿½Y":
                    self.handle_invite(chat_id)
                elif text == "ן¿½Y"S ן¿½"׳©ן¿½'ן¿½.׳¨ן¿½"":
                    self.handle_dashboard(chat_id)
                elif text == "ן¿½Y'ן¿½ ן¿½"׳₪׳¢ן¿½oן¿½"":
                    self.handle_activate(chat_id)
                elif text == "ן¿½Y"ן¿½ ׳©ן¿½T׳×ן¿½.׳£":
                    self.handle_share(chat_id)
                elif text == "ן¿½Y"s ן¿½zן¿½"׳¨ן¿½Tן¿½>ן¿½T׳":
                    self.handle_guides(chat_id)
                elif text == "ן¿½Y"ן¿½ ן¿½zן¿½'׳¦׳¢ן¿½T׳":
                    self.handle_deals_text(chat_id)
                elif text == "ן¿½Yן¿½T ׳¨ן¿½>ן¿½T׳©׳× SLH":
                    self.handle_buy_slh_text(chat_id)

                # ן¿½"?ן¿½"? Swap commands ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?ן¿½"?
                elif text.startswith("/swap "):
                    self.handle_swap_text(chat_id)
                elif text.startswith("/limit "):
                    self.send(chat_id, "ן¿½Y"ן¿½ ׳₪׳§ן¿½.ן¿½"׳× Limit ׳ ׳¨׳©ן¿½zן¿½". ׳×׳§ן¿½'ן¿½o ן¿½"׳×׳¨׳-ן¿½" ן¿½>׳©ן¿½"ן¿½zן¿½-ן¿½T׳¨ ן¿½Tן¿½'ן¿½T׳¢ ן¿½oן¿½T׳¢ן¿½".", self.main_reply_keyboard())
                elif text.startswith("/alert "):
                    self.handle_alerts(chat_id)
                elif text == "/orders":
                    self.send(chat_id, "ן¿½Y"< <b>׳₪׳§ן¿½.ן¿½"ן¿½.׳× ׳₪׳×ן¿½.ן¿½-ן¿½.׳×:</b>\n\n׳-ן¿½Tן¿½Y ׳₪׳§ן¿½.ן¿½"ן¿½.׳× ׳₪׳×ן¿½.ן¿½-ן¿½.׳×.", self.main_reply_keyboard())
                elif text == "/ai" or text == "ן¿½Yן¿½ן¿½ ׳ ן¿½T׳×ן¿½.ן¿½- AI":
                    self.handle_ai_analysis(chat_id)

                elif not text.startswith("/"):
                    self.handle_text(chat_id, text, first_name, username)
                else:
                    self.send(chat_id, "ן¿½Yן¿½- ׳₪׳§ן¿½.ן¿½"ן¿½" ן¿½o׳- ן¿½zן¿½.ן¿½>׳¨׳×. ן¿½oן¿½-׳¥ /start", self.main_reply_keyboard())

        except Exception as e:
            logger.error(f"Update error: {e}")

    def run(self):
        logger.info("=" * 50)
        logger.info("ן¿½Ys? SLH Investment House + HUB BOT ן¿½?" Starting...")
        logger.info("=" * 50)

        try:
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe", timeout=10)
            if r.status_code == 200 and r.json().get("ok"):
                logger.info(f"ן¿½o. Bot: @{r.json()['result']['username']}")
            else:
                logger.error("ן¿½O Bot connection failed")
                return
        except Exception as e:
            logger.error(f"ן¿½O Bot test error: {e}")
            return

        logger.info("ן¿½Y"" Running ן¿½?" Investment House + HUB + Buy SLH")

        while True:
            try:
                self.process_updates()
                time.sleep(0.5)
            except KeyboardInterrupt:
                logger.info("ן¿½Y>' Bot stopped")
                break
            except Exception as e:
                logger.error(f"ן¿½O Main loop error: {e}")
                time.sleep(5)


def main():
    bot = SLHInvestmentBot()
    bot.run()


if __name__ == "__main__":
    main()



