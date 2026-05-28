# -*- coding: utf-8 -*-
"""
SLH Investment House + HUB BOT
Full-featured investment house with HUB economic engine.

Features:
- �Y"S Live prices (12 coins)
- �Y'� Investment plans (4 tiers, 4%-5.4% monthly)
- �Y'� Wallet (TON/BNB/SLH/ZVK)
- �YZ� Bonuses & games (slots, dice, basketball, darts)
- �Y>� Risk management
- �Y"� Swap/DEX
- �Y�� AI analysis
- �Y"S Dashboard
- �Y'� Referrals (15% commission in SLH points)
- �Y�T Buy SLH (444�,� per coin)
- �Y'' VIP membership
- �YZ� Airdrop
- �Y'� Earn (daily tasks)
- �Y"� Deals & promotions
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

# �"?�"? Add shared module to path �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
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

# �"?�"? Price API �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
COINS = {
    "BTC": {"symbol": "bitcoin", "emoji": "�YY�", "name": "BTC"},
    "ETH": {"symbol": "ethereum", "emoji": "�Y"�", "name": "ETH"},
    "TON": {"symbol": "the-open-network", "emoji": "�Y'�", "name": "TON"},
    "BNB": {"symbol": "binancecoin", "emoji": "�YY�", "name": "BNB"},
    "SOL": {"symbol": "solana", "emoji": "�YY�", "name": "SOL"},
    "DOGE": {"symbol": "dogecoin", "emoji": "�Y��", "name": "DOGE"},
    "XRP": {"symbol": "ripple", "emoji": "�s�", "name": "XRP"},
    "ADA": {"symbol": "cardano", "emoji": "�Y"�", "name": "ADA"},
    "DOT": {"symbol": "polkadot", "emoji": "�YY�", "name": "DOT"},
    "AVAX": {"symbol": "avalanche-2", "emoji": "❤️", "name": "AVAX"},
    "LINK": {"symbol": "chainlink", "emoji": "�Y"-", "name": "LINK"},
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


# �"?�"? In-memory user state �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
_user_data = {}

# Investment plans
INVESTMENT_PLANS = [
    {"name": "�YO� פק�"�.�Y �-�.�"ש�T", "rate": 4, "annual": 48, "min_ton": 1, "days": 30},
    {"name": "�Y"^ פק�"�.�Y ר�'ע�.נ�T", "rate": 4.5, "annual": 55, "min_ton": 5, "days": 90},
    {"name": "�Y'Z פק�"�.�Y �-צ�T-שנת�T", "rate": 5, "annual": 60, "min_ton": 10, "days": 180},
    {"name": "�Y'' פק�"�.�Y שנת�T", "rate": 5.4, "annual": 65, "min_ton": 25, "days": 365},
]

VIP_PLANS = {
    "basic": {"name": "VIP Basic", "price_ils": 41, "features": ["�"תרא�.ת �z�-�Tר�Tם", "�'�Tש�" �oער�.ץ VIP", "5 �zש�T�z�.ת נ�.ספ�.ת �'�T�.ם"]},
    "pro": {"name": "VIP Pro", "price_ils": 99, "features": ["�"�>�o �'-Basic", "ס�T�'נ�o�Tם �o�zס�-ר", "�'�Tש�" �o-1-on-1", "ע�z�oת רפר�o �>פ�.�o�" (30%)"]},
    "elite": {"name": "VIP Elite", "price_ils": 199, "features": ["�"�>�o �'-Pro", "ק�'�.צת �.�.�Tס�~ �'�oע�"�Tת", "NFT �-�Tנם �>�o �-�.�"ש", "�'�Tש�" �z�.ק�"�zת �o�>�o �z�.צר �-�"ש"]},
}

SLH_BUY_TIERS = [
    {"amount": 0.0001, "price": 0.044},
    {"amount": 0.001, "price": 0.444},
    {"amount": 0.01, "price": 4.44},
    {"amount": 0.1, "price": 44.4},
    {"amount": 1, "price": 444},
]

_daily_tasks = [
    {"id": "join_channel", "title": "�Y"� �"צ�~רף �oער�.ץ @SLH_Community", "reward": 50},
    {"id": "share_bot", "title": "�Y"� שתף את �"�'�.�~ עם �-�'ר", "reward": 100},
    {"id": "visit_site", "title": "�YO� �'קר �'אתר slh-nft.com", "reward": 30},
    {"id": "follow_fb", "title": "�Y'� עק�.�' א�-ר�T Facebook SLH", "reward": 40},
    {"id": "daily_login", "title": "�o. �>נ�Tס�" �T�.�z�Tת", "reward": 10},
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

        # �"?�"? Async event loop in background thread (for WalletEngine) �"?�"?
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._loop_thread.start()

        # �"?�"? WalletEngine (blockchain wallets) �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
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
            logger.info("�o. WalletEngine connected �?" DB + Redis + BSC + TON")
        except Exception as e:
            logger.warning(f"�s�️ WalletEngine init failed (falling back to mock): {e}")

        logger.info("�Ys? SLH Investment House + HUB initialized")

    def _run_async(self, coro, timeout=10):
        """Run an async coroutine from synchronous code via the background loop."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    # �"?�"? Telegram API �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
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

    # �"?�"? Reply keyboard (main menu buttons at bottom) �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
    def main_reply_keyboard(self):
        return {"keyboard": [
            [{"text": "�Y"S �"ש�.ק ע�>ש�T�."}, {"text": "�Y'� �"שקע�.ת"}],
            [{"text": "�Y'� ארנק"}, {"text": "�Y"" P2P �zס�-ר"}],
            [{"text": "�YZ� �'�.נ�.ס�Tם"}, {"text": "�Y'� �"�-�z�Y"}],
            [{"text": "�Y"S �"ש�'�.ר�""}, {"text": "�Y�T ר�>�Tשת SLH"}],
            [{"text": "�Y'� �"פע�o�""}, {"text": "�Y"� ש�Tת�.ף"}],
            [{"text": "�Y"s �z�"ר�T�>�Tם"}, {"text": "�Y"� �z�'צע�Tם"}],
        ], "resize_keyboard": True, "one_time_keyboard": False}

    # �"?�"? Inline keyboards �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
    def hub_inline_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "�Y'� Earn", "callback_data": "menu_earn"}, {"text": "�Y"" Swap", "callback_data": "menu_swap"}],
            [{"text": "�Y'' VIP", "callback_data": "menu_vip"}, {"text": "�YZ� Airdrop", "callback_data": "menu_airdrop"}],
            [{"text": "�Y�T Buy SLH", "callback_data": "menu_buy_slh"}],
            [{"text": "�Y'� �"פנ�T�.ת ש�o�T", "callback_data": "menu_referral"}, {"text": "�Y"S �"ת�Tק ש�o�T", "callback_data": "menu_portfolio"}],
            [{"text": "�Y"� �z�'צע�Tם", "callback_data": "menu_deals"}, {"text": "�" ע�-ר�"", "callback_data": "menu_help"}],
        ]}

    def back_keyboard(self):
        return {"inline_keyboard": [[{"text": "�Y"T �-�-ר�" �oתפר�T�~", "callback_data": "menu_main"}]]}

    def earn_keyboard(self):
        rows = []
        for t in _daily_tasks:
            rows.append([{"text": f"{t['title']} (+{t['reward']})", "callback_data": f"task_{t['id']}"}])
        rows.append([{"text": "�Y"T �-�-ר�" �oתפר�T�~", "callback_data": "menu_main"}])
        return {"inline_keyboard": rows}

    def vip_keyboard(self):
        return {"inline_keyboard": [
            [{"text": f"⭐ Basic �?" {VIP_PLANS['basic']['price_ils']}�,�", "callback_data": "vip_basic"}],
            [{"text": f"�Y'Z Pro �?" {VIP_PLANS['pro']['price_ils']}�,�", "callback_data": "vip_pro"}],
            [{"text": f"�Y'' Elite �?" {VIP_PLANS['elite']['price_ils']}�,�", "callback_data": "vip_elite"}],
            [{"text": "�Y"T �-�-ר�" �oתפר�T�~", "callback_data": "menu_main"}],
        ]}

    def buy_slh_keyboard(self):
        rows = []
        for tier in SLH_BUY_TIERS:
            rows.append([{"text": f"�Y�T {tier['amount']} SLH = {tier['price']}�,�", "callback_data": f"buy_slh_{tier['amount']}"}])
        rows.append([{"text": "�o�️ ס�>�.ם �z�.תאם א�Tש�Tת", "callback_data": "buy_slh_custom"}])
        rows.append([{"text": "�Y"T �-�-ר�" �oתפר�T�~", "callback_data": "menu_main"}])
        return {"inline_keyboard": rows}

    def invest_keyboard(self):
        rows = []
        for i, plan in enumerate(INVESTMENT_PLANS):
            rows.append([{"text": f"{plan['name']} | {plan['rate']}% | {plan['min_ton']} TON", "callback_data": f"invest_{i}"}])
        rows.append([{"text": "�Y"T �-�-ר�"", "callback_data": "menu_main"}])
        return {"inline_keyboard": rows}

    def games_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "�YZ� ס�o�.�~�Tם", "callback_data": "game_slots"}, {"text": "�YZ� ק�.�'�T�.ת", "callback_data": "game_dice"}],
            [{"text": "�Y�? �>�"�.רס�o", "callback_data": "game_basketball"}, {"text": "�YZ� �-צ�Tם", "callback_data": "game_darts"}],
            [{"text": "�Y'� �"�zר ZVK �?' TON", "callback_data": "game_convert"}],
            [{"text": "�Y"T �-�-ר�"", "callback_data": "menu_main"}],
        ]}

    # �.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�
    # INVESTMENT HOUSE HANDLERS (original reply-keyboard buttons)
    # �.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�

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
                    self.send(referrer_id, f"�YZ? <b>�"פנ�T�" �-�"ש�"!</b>\n\n@{username or first_name} �"צ�~רף �"ר�>�s!\n+50 נק�.�"�.ת SLH �YZ�")
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
                logger.info(f"[bot-sync] �o. Synced {chat_id} (@{username}) to website �?" registered={sync_data.get('is_registered')}")
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
                logger.info(f"[bal-sync] �o. {chat_id}: SLH={user['slh_balance']}, ZVK={user['zvk_balance']}")
        except Exception as e:
            logger.warning(f"[bal-sync] failed for {chat_id}: {e}")

        invested = user["ton_locked"]
        profit = user["ton_locked"] * 0.04 if user["ton_locked"] > 0 else 0
        status = "�o. �zשק�Tע פע�T�o" if user["activated"] else "⏳ �z�zת�T�Y �o�"פע�o�""

        # Personal login link for the website (comes from auto-sync)
        login_url = user.get("web_login_url") or f"https://slh-nft.com/dashboard.html?uid={chat_id}"

        # Professional ASCII branding �?" clean, monospace-safe, SLH colors
        text = (
            f"<b>�o� SLH SPARK �o�</b>\n"
            f"<i>Digital Investment House</i>\n"
            f"<code>�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�</code>\n"
            f"        �Y'Z  S L H\n"
            f"   Investment Ecosystem\n"
            f"      by SPARK IND\n"
            f"<code>�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�</code>\n\n"
            f"ש�o�.ם <b>{first_name}</b>! �Y'<\n"
            f"�Y?" <b>�"�z�-�"�" ש�o�s:</b> <code>{chat_id}</code>\n"
            f"�Y'� <b>Username:</b> @{username or '�oא �"�.�'�"ר'}\n\n"
            f"�YO� <b><a href=\"{login_url}\">�"�T�>נס �oאתר �"א�Tש�T ש�o�s �?�</a></b>\n"
            f"   <i>(�o�-�Tצ�" א�-ת · �o�oא ס�Tס�z�")</i>\n\n"
            f"<code>�"��"� �"ס�~�~�.ס ש�o�s �"��"�</code>\n"
            f"�Y'� {status}\n"
            f"�Y'� �z�.שקע: <b>{invested:.2f} TON</b>\n"
            f"�Y"^ ר�.�.�-: <b>+{profit:.4f} TON</b>\n"
            f"�Y'Z SLH: <b>{user['slh_balance']:,.2f}</b>\n"
            f"�YZ� ZVK: <b>{user['zvk_balance']}</b>\n\n"
            f"<code>�"��"� �z�" תרצ�" �oעש�.ת? �"��"�</code>\n"
            f"�Y"S <b>�"ש�.ק ע�>ש�T�.</b> �?" �z�-�Tר�Tם, �z�'�z�.ת, ס�T�'נ�o�Tם\n"
            f"�Y'� <b>�"שקע�.ת</b> �?" 4 ת�.�>נ�T�.ת, 4%-5.4% �-�.�"ש�T\n"
            f"�Y'� <b>ארנק</b> �?" TON/BNB/SLH + �"ע�'ר�.ת\n"
            f"�Y>� <b>ס�T�>�.�Y</b> �?" �"�'�"ר�.ת ס�T�>�.�Y א�Tש�T�.ת\n"
            f"�YZ� <b>�'�.נ�.ס�Tם</b> �?" �zש�-ק�Tם + ZVK\n"
            f"�Y'� <b>�"�-�z�Y</b> �?" +5 ZVK + ע�z�o�.ת 10 �"�.ר�.ת\n"
            f"�Y�� <b>�-נ�.ת ק�"�T�oת�Tת</b> �?" �z�>�.ר/קנ�" �'�zער�>ת\n"
            f"�Y"� <b>�'�o�.�' �T�.�z�T</b> �?" �z�" �-�"ש �"�T�.ם\n"
            f"�YZ" <b>אק�"�z�T�"</b> �?" �z�"ר�T�>�Tם �.ק�.רס�Tם\n\n"
            f"<code>�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�</code>\n"
            f"�Y'� <b>SLH Investment House</b>\n"
            f"�s� <i>Powered by SPARK IND</i>\n"
            f"�Y?��Y?� <i>Built in Israel · 2026</i>"
        )
        # Inline keyboard with direct website button
        inline_kb = {
            "inline_keyboard": [
                [{"text": "�YO� �"�T�>נס �oאתר �"א�Tש�T", "url": login_url}],
                [
                    {"text": "�Y�� �-נ�.ת", "url": "https://slh-nft.com/community.html"},
                    {"text": "�Y"� �'�o�.�'", "url": "https://slh-nft.com/daily-blog.html"},
                ],
                [
                    {"text": "�YZ� �"�-�z�Y �-�'ר�Tם", "url": "https://slh-nft.com/invite.html"},
                    {"text": "�Y"- �z�"ר�T�>�Tם", "url": "https://slh-nft.com/guides.html"},
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
        self.send(chat_id, "�Y'? <i>תפר�T�~ �z�"�Tר:</i>", self.main_reply_keyboard())

    def handle_prices(self, chat_id):
        prices = fetch_prices()
        now = datetime.now()
        ts = now.strftime("%H:%M %d/%m/%Y")

        if not prices:
            self.send(chat_id, "�Y"S <b>�z�-�Tר�Tם �-�T�Tם</b>\n�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n⏳ �~�.ע�Y �z�-�Tר�Tם...\nנס�" ש�.�' �'ע�.�" ר�'ע.",
                      self.main_reply_keyboard())
            return

        top = ["BTC", "ETH", "TON", "BNB", "SOL"]
        alts = ["DOGE", "XRP", "ADA", "DOT", "AVAX", "LINK"]

        text = "�Y"S <b>�z�-�Tר�Tם �-�T�Tם</b>\n�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n�Y'' <b>�z�~�'ע�.ת �z�.�'�T�o�.ת:</b>\n"
        for coin in top:
            if coin in prices:
                p = prices[coin]
                info = COINS[coin]
                text += f"  {info['emoji']} {coin}: ${p['usd']:,.2f} | {p['ils']:,.1f}�,�\n"

        text += "\n�Y'� <b>Altcoins:</b>\n"
        for coin in alts:
            if coin in prices:
                p = prices[coin]
                info = COINS[coin]
                text += f"  {info['emoji']} {coin}: ${p['usd']:.4f} | {p['ils']:.2f}�,�\n"

        ton_price = prices.get("TON", {})
        if ton_price:
            text += f"\n�Y'� 1 TON = {ton_price['ils']}�,� | ${ton_price['usd']}\n"

        text += f"\n⏰ {ts}\n\n�Y'� SLH Investment House"
        self.send(chat_id, text, self.main_reply_keyboard())

    def wallet_inline_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "�Y"� �"פק�"�"", "callback_data": "wallet_deposit"}, {"text": "�Y"� ש�o�-", "callback_data": "wallet_send"}],
            [{"text": "�Y"o �"�Tס�~�.ר�T�"", "callback_data": "wallet_history"}, {"text": "�Y"" רענ�Y", "callback_data": "wallet_refresh"}],
            [{"text": "�Y"T �-�-ר�" �oתפר�T�~", "callback_data": "menu_main"}],
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

        # �"?�"? Try real blockchain wallet �"?�"?
        if self._wallet_ready and self.wallet:
            try:
                portfolio = self._run_async(self.wallet.get_user_portfolio(chat_id), timeout=12)
                if "error" not in portfolio:
                    bal = portfolio["balances"]
                    usd = portfolio["usd_values"]
                    prices = portfolio.get("prices", {})
                    bsc_addr = portfolio.get("bsc_address", "�?"")

                    text = (
                        f"�Y'� <b>ארנק SLH</b>\n"
                        f"�.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�\n\n"
                        f"�Y'Z <b>SLH:</b> {bal['SLH']}\n"
                        f"�YY� <b>BNB:</b> {bal['BNB']}\n"
                        f"�Y'� <b>TON:</b> {bal['TON']}\n"
                        f"�YZ� <b>ZVK:</b> {bal['ZVK']}\n\n"
                        f"�Y'� <b>ש�.�.�T �'�"�.�oר:</b>\n"
                        f"  SLH: ${usd.get('SLH', 0):,.2f}\n"
                        f"  BNB: ${usd.get('BNB', 0):,.2f}\n"
                        f"  TON: ${usd.get('TON', 0):,.2f}\n"
                        f"  �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n"
                        f"  �Y'� ס�"\"�>: <b>${usd.get('total', 0):,.2f}</b>\n\n"
                        f"�Y"- <b>�>ת�.�'ת BSC:</b>\n<code>{bsc_addr}</code>\n\n"
                        f"�Y'� <b>פק�.�"�.ת:</b>\n"
                        f"/deposit_address �?" �>ת�.�'ת �"פק�"�"\n"
                        f"/send_slh USER_ID AMOUNT �?" ש�o�- SLH\n"
                        f"/send_ton USER_ID AMOUNT �?" ש�o�- TON\n"
                        f"/tx_history �?" �"�Tס�~�.ר�T�Tת עסקא�.ת\n"
                        f"/verify TX_HASH CHAIN �?" א�zת �"פק�"�""
                    )
                    if message_id:
                        self.edit_message(chat_id, message_id, text, self.wallet_inline_keyboard())
                    else:
                        self.send(chat_id, text, self.wallet_inline_keyboard())
                    return
            except Exception as e:
                logger.warning(f"Wallet fetch failed for {chat_id}: {e}")

        # �"?�"? Fallback to in-memory �"?�"?
        ton_total = user["ton_available"] + user["ton_locked"]
        text = (
            f"�Y'� <b>ארנק</b>\n"
            f"�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
            f"�Y'Z SLH: {user['slh_balance']:.4f}\n"
            f"�YZ� ZVK: {user['zvk_balance']}\n\n"
            f"�Y�� <b>�-ש�'�.�Y �'נק:</b>\n"
            f"  �Y'� �-�z�T�Y: {user['ton_available']:.4f} TON\n"
            f"  �Y"' נע�.�o: {user['ton_locked']:.4f} TON\n"
            f"  �Y'� ס�"\"�>: {ton_total:.4f} TON\n\n"
            f"�s�️ <i>ארנק blockchain �zת�-�'ר... נס�" ש�.�' �'ע�.�" ר�'ע</i>\n\n"
            f"�Y'� <b>פק�.�"�.ת:</b>\n"
            f"/deposit - �"פק�"�" �-�"ש�"\n"
            f"/send_slh USER_ID AMOUNT �?" ש�o�- SLH\n"
            f"/tx_history �?" �"�Tס�~�.ר�T�Tת עסקא�.ת"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.wallet_inline_keyboard())
        else:
            self.send(chat_id, text, self.wallet_inline_keyboard())

    # �.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�
    # BLOCKCHAIN WALLET HANDLERS (wallet_engine integration)
    # �.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�

    def handle_deposit_address(self, chat_id):
        """Generate and show deposit addresses for BSC + TON."""
        if not self._wallet_ready:
            self.send(chat_id, "�s�️ �zער�>ת �"ארנק�Tם �zת�-�'רת... נס�" ש�.�' �'ע�.�" ר�'ע.", self.main_reply_keyboard())
            return
        try:
            addrs = self._run_async(self.wallet.generate_deposit_address(chat_id))
            text = (
                f"�Y"� <b>�>ת�.�'�.ת �"פק�"�"</b>\n"
                f"�.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�\n\n"
                f"�YY� <b>BSC (BNB / SLH Token):</b>\n"
                f"<code>{addrs['bsc_address']}</code>\n\n"
                f"�Y'� <b>TON:</b>\n"
                f"<code>{addrs['ton_address']}</code>\n"
                f"�Y"� <b>Memo:</b> <code>{addrs['memo']}</code>\n\n"
                f"�s�️ <b>�-ש�.�':</b>\n"
                f"�?� BSC �?" ש�o�- BNB א�. SLH Token �o�>ת�.�'ת �o�zע�o�"\n"
                f"�?� TON �?" ש�o�- TON �o�>ת�.�'ת + �"�.סף את �"-Memo\n"
                f"�?� א�-ר�T �"ש�o�T�-�": /verify TX_HASH bsc (א�. ton)\n\n"
                f"�Y'� <i>�"�"פק�"�" ת�T�-קף א�.�~�.�z�~�Tת א�-ר�T א�T�z�.ת</i>"
            )
            self.send(chat_id, text, self.wallet_inline_keyboard())
        except Exception as e:
            logger.error(f"Deposit address error: {e}")
            self.send(chat_id, "�O ש�'�Tא�" �'�Tצ�Tרת �>ת�.�'ת. נס�" ש�.�'.", self.main_reply_keyboard())

    def handle_verify_deposit(self, chat_id, args):
        """Verify a deposit tx on-chain: /verify TX_HASH bsc|ton"""
        if not self._wallet_ready:
            self.send(chat_id, "�s�️ �zער�>ת �"ארנק�Tם �zת�-�'רת...", self.main_reply_keyboard())
            return
        parts = args.strip().split()
        if len(parts) < 2:
            self.send(chat_id,
                "�Y"< <b>א�T�z�.ת �"פק�"�"</b>\n\n"
                "ש�T�z�.ש: /verify TX_HASH CHAIN\n\n"
                "�"�.�'�z�" BSC:\n<code>/verify 0xabc123... bsc</code>\n\n"
                "�"�.�'�z�" TON:\n<code>/verify abc123... ton</code>",
                self.main_reply_keyboard())
            return

        tx_hash = parts[0]
        chain = parts[1].lower()
        if chain not in ("bsc", "ton"):
            self.send(chat_id, "�O Chain �-�T�T�' �o�"�T�.ת bsc א�. ton", self.main_reply_keyboard())
            return

        self.send(chat_id, f"⏳ �zא�zת עסק�" ע�o {chain.upper()}...", self.main_reply_keyboard())
        try:
            result = self._run_async(self.wallet.process_deposit(chat_id, tx_hash, chain), timeout=20)
            if "error" in result:
                self.send(chat_id, f"�O {result['error']}", self.wallet_inline_keyboard())
            else:
                self.send(chat_id,
                    f"�o. <b>�"פק�"�" א�.�zת�"!</b>\n\n"
                    f"�Y'� ס�>�.ם: <b>{result['amount']} {result['token']}</b>\n"
                    f"�Y"- Chain: {result['chain'].upper()}\n"
                    f"�Y"� ID: #{result['deposit_id']}\n\n"
                    f"�"�Tתר�" ע�.�"�>נ�". /wallet �oצפ�T�T�"",
                    self.wallet_inline_keyboard())
                # Notify admin
                if str(chat_id) != ADMIN_ID:
                    user = _get_user(chat_id)
                    self.send(int(ADMIN_ID),
                        f"�Y'� <b>�"פק�"�" �-�"ש�"!</b>\n"
                        f"�Y'� @{user['username']} ({chat_id})\n"
                        f"�Y'� {result['amount']} {result['token']} ({chain.upper()})\n"
                        f"�Y"- TX: <code>{tx_hash[:30]}...</code>")
        except Exception as e:
            logger.error(f"Verify deposit error: {e}")
            self.send(chat_id, "�O ש�'�Tא�" �'א�T�z�.ת. נס�" ש�.�'.", self.main_reply_keyboard())

    def handle_send_internal(self, chat_id, args, token="SLH"):
        """Internal transfer: /send_slh USER_ID AMOUNT �?" uses bot-transfer API directly."""
        parts = args.strip().split()
        if len(parts) < 2:
            self.send(chat_id,
                f"�Y"� <b>�"ע�'רת {token}</b>\n\n"
                f"ש�T�z�.ש: /send_{token.lower()} USER_ID AMOUNT\n\n"
                f"�"�.�'�z�":\n<code>/send_{token.lower()} 123456789 10</code>\n\n"
                f"�Y'� �"-USER_ID ש�o �"נ�zע�Y: �'קש �z�zנ�. �oש�o�.�- /myid\n"
                f"�Y'� א�. �"שת�zש �'תפר�T�~: �Y"" P2P �zס�-ר",
                self.main_reply_keyboard())
            return
        try:
            to_user = int(parts[0])
            amount  = float(parts[1])
        except (ValueError, IndexError):
            self.send(chat_id, "�O פ�.ר�z�~ ש�'�.�T. ש�o�- USER_ID �.א�- ס�>�.ם.", self.main_reply_keyboard())
            return

        if to_user == chat_id:
            self.send(chat_id, "�O א�T אפשר �oש�o�.�- �oעצ�z�s", self.main_reply_keyboard())
            return

        # Use bot-transfer API (no JWT needed)
        self._p2p_execute_send(chat_id, {"token": token, "to_user": to_user, "amount": amount})

    def handle_tx_history(self, chat_id):
        """Show transaction history from DB."""
        if not self._wallet_ready:
            self.send(chat_id, "�s�️ �zער�>ת �"ארנק�Tם �zת�-�'רת...", self.main_reply_keyboard())
            return
        try:
            history = self._run_async(self.wallet.get_transaction_history(chat_id, limit=10))
            if not history:
                self.send(chat_id, "�Y"o <b>�"�Tס�~�.ר�T�Tת עסקא�.ת</b>\n\nא�T�Y עסקא�.ת ע�"�T�T�Y.", self.wallet_inline_keyboard())
                return
            text = "�Y"o <b>�"�Tס�~�.ר�T�Tת עסקא�.ת (10 א�-ר�.נ�.ת)</b>\n�.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�\n\n"
            for tx in history:
                direction = "�Y"�" if tx["from_user_id"] == chat_id else "�Y"�"
                other = tx["to_user_id"] if tx["from_user_id"] == chat_id else tx["from_user_id"]
                dt = tx["created_at"][:16].replace("T", " ") if tx["created_at"] else "�?""
                text += (
                    f"{direction} <b>{tx['amount']} {tx['token']}</b> "
                    f"{'�?'' if direction == '�Y"�' else '�?�'} {other or 'system'} "
                    f"| {tx['type']} | {dt}\n"
                )
            self.send(chat_id, text, self.wallet_inline_keyboard())
        except Exception as e:
            logger.error(f"TX history error: {e}")
            self.send(chat_id, "�O ש�'�Tא�" �'�~ע�Tנת �"�Tס�~�.ר�T�".", self.main_reply_keyboard())

    def handle_onchain_balance(self, chat_id):
        """Read on-chain balance for the ecosystem master wallets."""
        if not self._wallet_ready:
            self.send(chat_id, "�s�️ �zער�>ת �"ארנק�Tם �zת�-�'רת...", self.main_reply_keyboard())
            return
        try:
            self.send(chat_id, "⏳ ק�.רא �Tתר�.ת �z�"-blockchain...", self.main_reply_keyboard())
            slh_bal = self._run_async(self.wallet.get_slh_balance(BSC_CONTRACT), timeout=15)
            ton_bal = self._run_async(self.wallet.get_ton_balance(TON_WALLET), timeout=15)
            prices = self._run_async(self.wallet.get_live_prices())
            text = (
                f"�Y"- <b>�Tתר�.ת On-Chain</b>\n"
                f"�.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�\n\n"
                f"�Y'Z <b>SLH Token (BSC):</b>\n"
                f"  Contract: <code>{BSC_CONTRACT[:20]}...</code>\n"
                f"  �Tתר�": {slh_bal}\n\n"
                f"�Y'� <b>TON Wallet:</b>\n"
                f"  �>ת�.�'ת: <code>{TON_WALLET[:20]}...</code>\n"
                f"  �Tתר�": {ton_bal} TON\n\n"
                f"�Y"S <b>�z�-�Tר�Tם:</b>\n"
                f"  BTC: ${prices.get('btc_usd', 0):,.0f}\n"
                f"  ETH: ${prices.get('eth_usd', 0):,.0f}\n"
                f"  TON: ${prices.get('ton_usd', 0):.2f}\n"
                f"  BNB: ${prices.get('bnb_usd', 0):,.0f}\n"
                f"  SLH: {prices.get('slh_ils', 444)}�,� (${prices.get('slh_usd', 0):.2f})"
            )
            self.send(chat_id, text, self.wallet_inline_keyboard())
        except Exception as e:
            logger.error(f"On-chain balance error: {e}")
            self.send(chat_id, "�O ש�'�Tא�" �'קר�Tא�" �z�"-blockchain.", self.main_reply_keyboard())

    def handle_investments(self, chat_id, message_id=None):
        text = "�Y'� <b>ת�.�>נ�T�.ת �"שקע�"</b>\n�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
        for plan in INVESTMENT_PLANS:
            text += (
                f"{plan['name']}\n"
                f"  �Y'� {plan['rate']}% �-�.�"ש�T | {plan['annual']}% שנת�T\n"
                f"  �z�Tנ�T�z�.ם {plan['min_ton']} TON | {plan['days']} �T�.ם\n\n"
            )
        text += (
            "�Y'� <b>א�T�s �o�"פק�T�":</b>\n"
            "1. �'�-ר ת�.�>נ�Tת\n"
            "2. ש�o�- TON �z-@wallet\n"
            "3. ש�o�- צ�T�o�.ם �zס�s\n"
            "4. �"פק�"�.�Y נפת�-!"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.invest_keyboard())
        else:
            self.send(chat_id, text, self.invest_keyboard())

    def handle_risk(self, chat_id):
        user = _get_user(chat_id)
        text = (
            f"�Y>� <b>ס�T�>�.�Y �.�'קר�"</b>\n"
            f"�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
            f"�Y'� <b>�"�'�"ר�.ת �"ס�T�>�.�Y ש�o�s:</b>\n\n"
            f"�Ys� �"פס�" �T�.�z�T: {user['risk_daily_loss']}%\n"
            f"�Y"S פ�.�-�Tצ�T�" �zקס�T�z�o�Tת: {user['risk_max_position']}%\n"
            f"�Y>' Stop Loss: {'�o. פע�T�o' if user['risk_stop_loss'] else '�O �>�'�.�T'}\n\n"
            f"�Y"� <b>עקר�.נ�.ת:</b>\n"
            f"�?� �oא �o�"שק�Tע �T�.תר �z�z�" ש�z�.�>נ�Tם �o�"פס�T�"\n"
            f"�?� �o�"פר�T�" �'�T�Y �zספר ת�.�>נ�T�.ת\n"
            f"�?� �oא �oש�Tם �"�>�o ע�o ק�oף א�-�"\n"
            f"�?� �o�"שא�Tר נ�-�T�o�.ת �o�zקר�" �-�Tר�.ם\n\n"
            f"�Y>� <b>�"�zער�>ת ש�.�zרת ע�o�T�s!</b>"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_invite(self, chat_id):
        user = _get_user(chat_id)
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            f"�Y'� <b>�"�-�z�Y �-�'ר�Tם</b>\n\n"
            f"�Y"- <code>{ref_link}</code>\n\n"
            f"�"�-�zנ�.ת: {user['referral_count']} | +5 ZVK �o�>�o �-�'ר"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_activate(self, chat_id):
        user = _get_user(chat_id)
        user["activated"] = True
        self.send(chat_id, "�o. �z�.פע�o!", self.main_reply_keyboard())

    def handle_share(self, chat_id):
        user = _get_user(chat_id)
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            f"�Y'Z SLH - �'�Tת �"שקע�.ת �"�T�'�T�~�o�T\n\n"
            f"�o. תש�.א�" 4% �-�.�"ש�T / 65% שנת�T\n"
            f"�o. ארנק �z�oא (TON/BNB/SLH)\n"
            f"�o. �"ע�'ר�.ת �z�T�T�"�T�.ת + blockchain\n"
            f"�o. נ�Tת�.�- ש�.ק + ס�T�'נ�o�Tם\n"
            f"�YZ� +100 ZVK �zתנ�"!\n\n"
            f"�Y'� 22.221�,� �'�o�'�"!\n"
            f"�Y'? {ref_link}\n\n"
            f"�Y'� SPARK IND | SLH Ecosystem"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_guides(self, chat_id):
        text = (
            "�Y"s <b>�z�"ר�T�>�Tם</b>\n"
            "�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
            "�Y"- <b>�z�"ר�T�>�T SLH:</b>\n"
            "�?� <a href='https://slh-nft.com/guides.html'>�z�"ר�T�s �z�oא �'אתר</a>\n\n"
            "�Y"< <b>נ�.שא�Tם:</b>\n"
            "1️�f� א�T�s �o�"ת�-�T�o עם SLH\n"
            "2️�f� א�T�s �oפת�.�- ארנק TON\n"
            "3️�f� א�T�s �o�"פק�T�" �.�o�"שק�Tע\n"
            "4️�f� א�T�s �o�"שת�zש �'ס�.�.אפ\n"
            "5️�f� �z�"ר�T�s א�'�~�-�"\n"
            "6️�f� שא�o�.ת נפ�.צ�.ת\n\n"
            "�Y'� �o�>�o שא�o�": /support"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_bonuses(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        text = (
            f"�YZ� <b>�'�.נ�.ס�Tם</b> | ZVK: {user['zvk_balance']}\n"
            f"�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
            f"�>�o �zש�-ק = 1 ZVK\n"
            f"�YZ� ס�o�.�~�Tם: פרס �'�"�.�o ע�" 25 ZVK!\n"
            f"�YZ� ק�.�'�T�.ת: 6=5 ZVK, 4-5=2 ZVK\n"
            f"�Y�? �>�"�.רס�o: 4+=3 ZVK\n"
            f"�YZ� �-צ�Tם: 6=5 ZVK, 4-5=2 ZVK\n\n"
            f"�Y'� 10 ZVK = 1 TON | 50 = 4 | 100 = 7"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.games_keyboard())
        else:
            self.send(chat_id, text, self.games_keyboard())

    def handle_game(self, chat_id, game_type, callback_id, message_id):
        user = _get_user(chat_id)
        if user["zvk_balance"] < 1:
            self.answer_callback(callback_id, "�O א�T�Y �zספ�Tק ZVK!", True)
            return

        user["zvk_balance"] -= 1
        user["games_played"] += 1

        if game_type == "slots":
            symbols = ["�Y�'", "�Y�<", "�Y�S", "�Y'Z", "7️�f�", "�Y"""]
            s1, s2, s3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)
            if s1 == s2 == s3:
                win = 25 if s1 == "�Y'Z" else 15
                user["zvk_balance"] += win
                user["games_won"] += 1
                result = f"�YZ� {s1}{s2}{s3}\n\n�YZ? �''קפ�.�~! +{win} ZVK!"
            elif s1 == s2 or s2 == s3:
                win = 3
                user["zvk_balance"] += win
                user["games_won"] += 1
                result = f"�YZ� {s1}{s2}{s3}\n\n�YZ? נ�Tצ�-ת! +{win} ZVK!"
            else:
                result = f"�YZ� {s1}{s2}{s3}\n\n�O �oא �"פעם"
        elif game_type == "dice":
            roll = random.randint(1, 6)
            if roll == 6:
                user["zvk_balance"] += 5
                user["games_won"] += 1
                result = f"�YZ� {roll}\n\n�YZ? �z�.ש�oם! +5 ZVK!"
            elif roll >= 4:
                user["zvk_balance"] += 2
                user["games_won"] += 1
                result = f"�YZ� {roll}\n\n�YZ? נ�Tצ�-ת! +2 ZVK!"
            else:
                result = f"�YZ� {roll}\n\n�O �oא �"פעם"
        elif game_type == "basketball":
            score = random.randint(1, 6)
            if score >= 4:
                user["zvk_balance"] += 3
                user["games_won"] += 1
                result = f"�Y�? {score} נק�.�"�.ת!\n\n�YZ? נ�Tצ�-ת! +3 ZVK!"
            else:
                result = f"�Y�? {score} נק�.�"�.ת\n\n�O �oא �"פעם"
        elif game_type == "darts":
            score = random.randint(1, 6)
            if score == 6:
                user["zvk_balance"] += 5
                user["games_won"] += 1
                result = f"�YZ� �zר�>�-! {score}\n\n�YZ? נ�Tצ�-ת! +5 ZVK!"
            elif score >= 4:
                user["zvk_balance"] += 2
                user["games_won"] += 1
                result = f"�YZ� {score}\n\n�YZ? נ�Tצ�-ת! +2 ZVK!"
            else:
                result = f"�YZ� {score}\n\n�O �oא �"פעם"
        else:
            result = "�""

        result += f"\n�YZ� ZVK: {user['zvk_balance']}"
        self.edit_message(chat_id, message_id, result, self.games_keyboard())
        self.answer_callback(callback_id)

    def handle_game_convert(self, chat_id, callback_id, message_id):
        text = (
            "�Y'� <b>�"�zרת ZVK �?' TON</b>\n\n"
            "10 ZVK = 1 TON\n"
            "50 ZVK = 4 TON\n"
            "100 ZVK = 7 TON\n\n"
            f"ש�o�- �o:\n<code>{TON_WALLET}</code>"
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
            f"�Y"S <b>�"ש�'�.ר�"</b>\n"
            f"�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
            f"�Y�� <b>�-ש�'�.�Y �'נק:</b>\n"
            f"  �Y'� �-�z�T�Y: {user['ton_available']:.4f} TON\n"
            f"  �Y"' נע�.�o: {user['ton_locked']:.4f} TON\n"
            f"  �Y'� ס�"\"�>: {ton_total:.4f} TON\n\n"
            f"�Y'� �"שקע�.ת פע�T�o�.ת: {active_deposits}\n"
            f"⏳ �z�zת�Tנ�.ת �oא�Tש�.ר: {pending_deposits}\n"
            f"�Y'� �z�.שקע: {invested:.2f} TON\n"
            f"�Y"^ ר�.�.�-: +{profit:.4f} TON\n\n"
            f"�YZ� ZVK: {user['zvk_balance']} | �zש�-ק�Tם: {user['games_played']} ({win_rate}%)\n"
            f"�Y'� �"�-�zנ�.ת: {user['referral_count']}\n\n"
            f"SLH Investment House"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_swap_text(self, chat_id):
        text = (
            "�Y"" <b>SLH Swap �?" �"�zרת �z�~�'ע�.ת</b>\n\n"
            "�"�z�Tר�. �'�T�Y 4,500+ �z�~�'ע�.ת קר�Tפ�~�. �'ק�o�.ת!\n\n"
            "�Y'� <b>�Tתר�.נ�.ת:</b>\n"
            "�?� �o�oא �"רש�z�"\n"
            "�?� ע�z�o�.ת נ�z�.�>�.ת\n"
            "�?� �"�zר�" �Tש�Tר�" �zארנק �oארנק\n"
            "�?� ת�z�T�>�" �'-TON, BTC, ETH, BNB �.ע�.�"\n\n"
            "�Y"� <b>�z�'צע:</b> Cashback 0.5% ע�o �>�o עסק�"!\n\n"
            "�Y'? �o�-ץ �o�"ת�-�o�":"
        )
        kb = {"inline_keyboard": [
            [{"text": "�Y"" �"�zר ע�>ש�T�.", "url": f"https://letsexchange.io/?ref={LETSEXCHANGE_REF}"}],
            [{"text": "�Y'� TON �?' USDT", "url": f"https://letsexchange.io/?from=TON&to=USDT&ref={LETSEXCHANGE_REF}"}],
            [{"text": "�Y'� BTC �?' TON", "url": f"https://letsexchange.io/?from=BTC&to=TON&ref={LETSEXCHANGE_REF}"}],
        ]}
        self.send(chat_id, text, kb)

    def handle_ai_analysis(self, chat_id):
        prices = fetch_prices()
        btc = prices.get("BTC", {}).get("usd", 67000)
        text = (
            f"�Y�� <b>נ�Tת�.�- AI</b>\n"
            f"�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
            f"�Y"^ <b>תר�-�Tש ש�.ר�T:</b> אם BTC ש�.�'ר ${int(btc/1000)*1000+3000:,}, צפ�.�T �z�"�o�s �o-${int(btc/1000)*1000+8000:,}\n\n"
            f"�Y"� <b>תר�-�Tש �"�.�'�T:</b> אם BTC ש�.�'ר ${int(btc/1000)*1000-2000:,}, אפשר�T נפ�T�o�" �o-${int(btc/1000)*1000-7000:,}\n\n"
            f"�YY� <b>תר�-�Tש נ�T�T�~ר�o�T:</b> צפ�.�T �"�-�Tס�" צ�"�"�Tת\n\n"
            f"�s�️ �-�" �oא �T�Tע�.ץ �"שקע�"."
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_alerts(self, chat_id):
        text = (
            "�Y"" <b>�"תרא�.ת �z�-�Tר</b>\n"
            "�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
            "�'קר�.�'! ת�.�>�o �o�"�'�"�Tר �"תרא�.ת ע�o:\n"
            "�?� �z�-�Tר שע�.�'ר ר�z�"\n"
            "�?� נפ�- �-ר�T�'\n"
            "�?� �-�"ש�.ת ש�.ק\n"
            "�?� ש�Tנ�.�T �'ת�Tק"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_deals_text(self, chat_id):
        text = (
            "�Y"� <b>�z�'צע�Tם פע�T�o�Tם</b>\n\n"
            "�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n\n"
            "�Y"� <b>�z�'צע �"שק�" �?" 30% �"נ�-�"!</b>\n"
            "  �Y'� �>�o �"�'�.�~�Tם �'-30% �"נ�-�"\n"
            "  �Y��️ ק�.�": <code>LAUNCH30</code>\n"
            "  ⏰ �-�z�Y �z�.�'�'�o\n\n"
            "�Y'Z <b>�-�'�T�o�" �z�oא�" �?" 6 �'�.�~�Tם</b>\n"
            "  �Y'� �z�-�Tר: <b>199�,�</b>\n"
            "  �Y"� �>�o 6 �'�.�~�T �"פר�T�z�T�.ם\n\n"
            "�Y�� <b>�"�-�z�Y 3 = פר�T�z�T�.ם �-�Tנם!</b>\n"
            "  �Y'� �"�-�z�Y 3 �-�'ר�Tם\n"
            "  �YZ� ק�'�o Community Premium �'�-�Tנם\n\n"
            "�Y>�️ <b>�-�'�T�oת א�'�~�-�"</b>\n"
            "  �Y'� Guardian + Wallet = <b>99�,�</b>\n\n"
            "�YZ" <b>�z�'צע ס�~�.�"נ�~�Tם</b>\n"
            "  �Y'� 50% �"נ�-�" ע�o Academia\n"
            "  �Y��️ ק�.�": <code>STUDENT50</code>\n"
            "�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_buy_slh_text(self, chat_id):
        text = (
            f"�Y�T <b>ר�>�Tשת SLH Coin</b>\n\n"
            f"�Y'� <b>�z�-�Tר:</b> 1 SLH = {SLH_PRICE_ILS}�,�\n"
            f"�Y"� �z�Tנ�T�z�.ם: 0.00004 SLH (0.018�,�)\n\n"
            f"�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n"
            f"�Y"S <b>�z�"ר�'�.ת �z�-�Tר:</b>\n\n"
        )
        for tier in SLH_BUY_TIERS:
            text += f"  �Y�T {tier['amount']} SLH = {tier['price']}�,�\n"
        text += (
            f"\n�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n"
            f"�Y'� <b>ארנק TON:</b>\n<code>{TON_WALLET}</code>\n\n"
            f"�Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            f"�Y"� ש�o�- צ�T�o�.ם �zס�s א�. Transaction Hash\n"
            f"א�. צ�.ר קשר עם @Osif83"
        )
        self.send(chat_id, text, self.buy_slh_keyboard())

    # �"?�"? Banking commands �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
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
            f"�o. <b>�"פק�"�" #{deposit_id} נ�.צר�"!</b>\n"
            f"�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
            f"{plan['name']} | {amount} TON\n"
            f"תש�.א�" �-�.�"ש�Tת: ~{monthly_return} TON\n"
            f"נע�.�o ע�": {unlock_date}\n\n"
            f"�Y'� ש�o�- {amount} TON �o:\n"
            f"<code>{TON_WALLET}</code>\n\n"
            f"�.ש�o�- צ�T�o�.ם �zס�s �oא�Tש�.ר."
        )
        self.send(chat_id, text, self.main_reply_keyboard())

        # Notify admin
        if str(chat_id) != ADMIN_ID:
            admin_text = (
                f"�Y'� <b>�"פק�"�" �-�"ש�" #{deposit_id}</b>\n"
                f"�Y'� @{user['username']} ({chat_id})\n"
                f"�Y'� {plan['name']} | {amount} TON\n"
                f"�Y'� {plan['rate']}% �-�.�"ש�T | {plan['days']} �T�z�Tם"
            )
            kb = {"inline_keyboard": [
                [{"text": "�o. אשר", "callback_data": f"admin_approve_{chat_id}_{deposit_id}"},
                 {"text": "�O �"�-�"", "callback_data": f"admin_reject_{chat_id}_{deposit_id}"}],
            ]}
            self.send(int(ADMIN_ID), admin_text, kb)

    def handle_mydeposits(self, chat_id):
        user = _get_user(chat_id)
        if not user["deposits"]:
            self.send(chat_id, "�Y"< א�T�Y �"פק�"�.ת פע�T�o�.ת.\n\n�o�"פק�"�" �-�"ש�": /deposit", self.main_reply_keyboard())
            return

        text = "�Y"< <b>�"�"פק�"�.ת ש�o�T</b>\n�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
        for d in user["deposits"]:
            status = "�o." if d["status"] == "active" else "⏳" if d["status"] == "pending" else "�O"
            text += f"{status} #{d['id']} | {d['plan']} | {d['amount']} TON | {d['rate']}%\n"
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_withdraw(self, chat_id, args=""):
        if not args:
            self.send(chat_id,
                "�Y'� <b>�zש�T�>�"</b>\n\nש�T�z�.ש: /withdraw <�zספר �"פק�"�"> <�>ת�.�'ת TON>\n\n�"�.�'�z�": /withdraw 1 UQDhfy...\n\n�oרש�T�z�": /mydeposits",
                self.main_reply_keyboard())
            return
        self.send(chat_id, "�Y"� �'קשת �"�zש�T�>�" נש�o�-�" �oא�Tש�.ר. נע�"�>�Y �'�"ק�"ם.", self.main_reply_keyboard())
        if str(chat_id) != ADMIN_ID:
            user = _get_user(chat_id)
            self.send(int(ADMIN_ID), f"�Y'� <b>�'קשת �zש�T�>�"!</b>\nUser: @{user['username']} ({chat_id})\nArgs: {args}")

    def handle_statement(self, chat_id):
        user = _get_user(chat_id)
        ton_total = user["ton_available"] + user["ton_locked"]
        text = (
            f"�Y"< <b>�"ף �-ש�'�.�Y (30 �T�.ם)</b>\n"
            f"�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
            f"�Y'� �-�z�T�Y: {user['ton_available']:.4f} TON\n"
            f"�Y"' נע�.�o: {user['ton_locked']:.4f} TON\n"
            f"�Y'� ס�"\"�>: {ton_total:.4f} TON\n\n"
            f"�Y"^ �"פק�"�.ת: {len(user['deposits'])}\n"
            f"�Y'� �zש�T�>�.ת: {user['withdrawals']}\n"
            f"�Y"� תנ�.ע�.ת: {user['transactions']}\n\n"
            f"SLH Investment House"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_kyc(self, chat_id, args=""):
        if args:
            self.send(chat_id, f"�o. ש�o�' 1 �"�.ש�oם: {args}\n\nש�o�- צ�T�o�.ם ת.�-. (�>ת�z�.נ�")", self.main_reply_keyboard())
        else:
            text = (
                "�Y"< <b>KYC - �-�T�"�.�T</b>\n�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
                "ש�o�' 1: /kyc <שם �z�oא>\n"
                "ש�o�' 2: ש�o�- צ�T�o�.ם ת.�-. (�>ת�z�.נ�")\n"
                "ש�o�' 3: �"�zת�Y �oא�Tש�.ר"
            )
            self.send(chat_id, text, self.main_reply_keyboard())

    def handle_faq(self, chat_id):
        text = (
            "�" <b>FAQ</b>\n\n"
            "Q: �>�z�" ע�.�o�"?\nA: 22.221�,� �-�" פע�z�T\n\n"
            "Q: א�T�s �zש�o�z�Tם?\nA: @wallet �?' Buy TON �?' Send\n\n"
            "Q: �'�~�.�-?\nA: �zפת�-�.ת פר�~�T�Tם �oא נש�zר�Tם\n\n"
            "Q: ת�z�T�>�"?\nA: /support"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_help(self, chat_id, message_id=None):
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            "�" <b>SLH Investment House</b>\n"
            "�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
            "�Y"S <b>�"ש�.ק</b> - 12 �z�~�'ע�.ת, ס�.�.אפ, �"תרא�.ת\n"
            "�Y'� <b>�"שקע�.ת</b> - 4 פק�"�.נ�.ת, 4%-65%\n"
            "�Y'� <b>ארנק</b> - TON/BNB/SLH + �"ע�'ר�.ת\n"
            "�Y"� <b>�zס�-ר</b> - ס�.�.אפ, Limit, �"תרא�.ת\n\n"
            "�Y'� <b>�'נק:</b>\n"
            "/deposit /mydeposits /withdraw /statement\n\n"
            "�Y'� <b>�zס�-ר:</b>\n"
            "/prices /swap /limit /orders /alert /portfolio\n\n"
            "�Y'� <b>ארנק:</b>\n"
            "/pay /send /mybalance /myid /gas\n\n"
            "�Y�T <b>SLH Coin:</b>\n"
            "/buyslh - ר�>�Tשת �z�~�'ע SLH\n\n"
            "�Y"s <b>ע�.�":</b>\n"
            "/share /faq /support /kyc /help\n\n"
            f"�Y'� <b>שתף �.�"ר�.�.�T�- 15% �'נק�.�"�.ת SLH!</b>\n"
            f"�Y"- <code>{ref_link}</code>\n\n"
            "SLH Investment House | SPARK IND"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.back_keyboard())
        else:
            self.send(chat_id, text, self.main_reply_keyboard())

    def _format_invest_plans(self):
        text = "�Y'� <b>ת�.�>נ�T�.ת �"שקע�"</b>\n�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?\n\n"
        for i, plan in enumerate(INVESTMENT_PLANS, 1):
            text += (
                f"{plan['name']}\n"
                f"  �Y'� {plan['rate']}% �-�.�"ש�T | {plan['annual']}% שנת�T\n"
                f"  �z�Tנ�T�z�.ם {plan['min_ton']} TON | {plan['days']} �T�.ם\n\n"
            )
        return text

    # �.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�
    # HUB HANDLERS (inline keyboard callbacks)
    # �.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�

    def handle_earn(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        done = len(user["tasks_done"])
        total = len(_daily_tasks)
        total_reward = sum(t["reward"] for t in _daily_tasks)
        done_reward = sum(t["reward"] for t in _daily_tasks if t["id"] in user["tasks_done"])
        text = (
            f"�Y'� <b>�"ר�.�.�T�- נק�.�"�.ת SLH</b>\n\n"
            f"�Y"S �"תק�"�z�.ת: {done}/{total} �zש�T�z�.ת\n"
            f"�Y'Z שנצ�'ר �"�T�.ם: {done_reward}/{total_reward} נק�.�"�.ת\n"
            f"�Y'� �Tתר�": {user['hub_points']} נק�.�"�.ת\n\n"
            f"�Y'? <b>�zש�T�z�.ת �-�z�Tנ�.ת:</b>"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.earn_keyboard())
        else:
            self.send(chat_id, text, self.earn_keyboard())

    def handle_task(self, chat_id, task_id, callback_id, message_id):
        user = _get_user(chat_id)
        task = next((t for t in _daily_tasks if t["id"] == task_id), None)
        if not task:
            self.answer_callback(callback_id, "�O �zש�T�z�" �oא נ�zצא�"")
            return
        if task_id in user["tasks_done"]:
            self.answer_callback(callback_id, "�o. �>�'ר �'�Tצעת �zש�T�z�" �-�. �"�T�.ם!", True)
            return
        user["tasks_done"].append(task_id)
        user["hub_points"] += task["reward"]
        user["total_earned"] += task["reward"]
        self.answer_callback(callback_id, f"�o. +{task['reward']} נק�.�"�.ת!", True)
        self.handle_earn(chat_id, message_id)

    def handle_swap_inline(self, chat_id, message_id=None):
        text = (
            "�Y"" <b>SLH Swap �?" �"�zרת �z�~�'ע�.ת</b>\n\n"
            "�"�z�Tר�. �'�T�Y 4,500+ �z�~�'ע�.ת קר�Tפ�~�. �'ק�o�.ת!\n\n"
            "�Y'� <b>�Tתר�.נ�.ת:</b>\n"
            "�?� �o�oא �"רש�z�"\n�?� ע�z�o�.ת נ�z�.�>�.ת\n"
            "�?� �"�zר�" �Tש�Tר�" �zארנק �oארנק\n"
            "�?� ת�z�T�>�" �'-TON, BTC, ETH, BNB �.ע�.�"\n\n"
            "�Y"� <b>�z�'צע:</b> Cashback 0.5% ע�o �>�o עסק�"!"
        )
        kb = {"inline_keyboard": [
            [{"text": "�Y"" �"�zר ע�>ש�T�.", "url": f"https://letsexchange.io/?ref={LETSEXCHANGE_REF}"}],
            [{"text": "�Y'� TON �?' USDT", "url": f"https://letsexchange.io/?from=TON&to=USDT&ref={LETSEXCHANGE_REF}"}],
            [{"text": "�Y'� BTC �?' TON", "url": f"https://letsexchange.io/?from=BTC&to=TON&ref={LETSEXCHANGE_REF}"}],
            [{"text": "�Y"T �-�-ר�" �oתפר�T�~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_vip(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        current = user["vip"]
        status = f"�o. {VIP_PLANS[current]['name']}" if current else "�Y?" �-�Tנם"
        text = f"�Y'' <b>VIP Membership</b>\n\nס�~�~�.ס: <b>{status}</b>\n\n�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n"
        for key, plan in VIP_PLANS.items():
            marker = "�o." if current == key else "⭐"
            text += f"\n{marker} <b>{plan['name']}</b> �?" {plan['price_ils']}�,�\n"
            for f in plan["features"]:
                text += f"  �?� {f}\n"
        text += f"\n�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n�Y'� <b>תש�o�.ם:</b> �"ע�'ר �oארנק + צ�T�o�.ם �zס�s\n�Y"� <b>�-�'�T�o�" �z�oא�":</b> �>�o �"-VIP + 6 �'�.�~�Tם = 199�,� �'�o�'�"!"
        if message_id:
            self.edit_message(chat_id, message_id, text, self.vip_keyboard())
        else:
            self.send(chat_id, text, self.vip_keyboard())

    def handle_vip_select(self, chat_id, plan_key, callback_id, message_id):
        plan = VIP_PLANS.get(plan_key)
        if not plan:
            self.answer_callback(callback_id, "�O")
            return
        text = (
            f"�Y'' <b>{plan['name']}</b>\n\n"
            f"�Y'� <b>�z�-�Tר:</b> {plan['price_ils']}�,�\n\n"
            f"<b>פ�Tצ'ר�Tם:</b>\n" +
            "\n".join(f"  �o. {f}" for f in plan["features"]) +
            f"\n\n�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n"
            f"�Y'� <b>ש�o�- {plan['price_ils']}�,� �oארנק TON:</b>\n\n"
            f"<code>{TON_WALLET}</code>\n\nא�. צ�.ר קשר עם @Osif83\n\n"
            f"�Y"� ש�o�- צ�T�o�.ם �zס�s ש�o �"עסק�" �>א�Y\n�o. תק�'�o �'�Tש�" ת�.�s �"ק�.ת"
        )
        kb = {"inline_keyboard": [
            [{"text": "�Y'� �"עתק �>ת�.�'ת ארנק", "callback_data": f"copy_wallet_{plan_key}"}],
            [{"text": "�Y"T �-�-ר�" �o-VIP", "callback_data": "menu_vip"}],
        ]}
        self.edit_message(chat_id, message_id, text, kb)
        self.answer_callback(callback_id)

    def handle_airdrop(self, chat_id, message_id=None):
        text = (
            "�YZ� <b>SLH Airdrop</b>\n\n"
            f"�Y'� <b>�z�'צע �"שק�":</b>\n1,000 �~�.קנ�T SLH = <b>444,000�,�</b>\n\n"
            f"�Y"S <b>ס�~�~�.ס:</b>\n�Y'� �zשת�zש�Tם: 38\n�Y'� עסקא�.ת: 22\n�YZ� �zק�.�z�.ת פנ�.�T�Tם: 978/1,000\n\n"
            f"�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n"
            f"�Y'� <b>�oר�>�Tש�" ש�o�- �oארנק TON:</b>\n<code>{TON_WALLET}</code>\n\n"
            f"�Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            "�Y"� ש�o�- צ�T�o�.ם �zס�s / Transaction Hash\n�o. ק�'�o�" ת�.�s 24 שע�.ת"
        )
        kb = {"inline_keyboard": [
            [{"text": "�Y'� ש�o�- תש�o�.ם", "callback_data": "airdrop_pay"}],
            [{"text": "�Y"S ס�~�~�.ס ש�o�T", "callback_data": "airdrop_status"}],
            [{"text": "�Y"T �-�-ר�" �oתפר�T�~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_referral(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            f"�Y'� <b>�"�"פנ�T�.ת ש�o�s</b>\n\n"
            f"�Y"- <b>�"ק�Tש�.ר �"א�Tש�T ש�o�s:</b>\n<code>{ref_link}</code>\n\n"
            f"�Y"S <b>ס�~�~�Tס�~�Tק�":</b>\n"
            f"�Y'� �"פנ�T�.ת: <b>{user['referral_count']}</b>\n"
            f"�Y'� נצ�'ר �z�"פנ�T�.ת: <b>{user['referral_count'] * 50}</b> נק�.�"�.ת SLH\n\n"
            f"�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n"
            f"�Y'� <b>א�T�s �o�"ר�.�.�T�-?</b>\n"
            f"1️�f� שתף את �"ק�Tש�.ר ש�o�s\n"
            f"2️�f� �-�'ר�Tם נרש�z�Tם �"ר�>�s\n"
            f"3️�f� �zק�'�o <b>50 נק�.�"�.ת SLH</b> + <b>15% ע�z�o�" �'נק�.�"�.ת SLH</b> �z�>�o ר�>�Tש�"\n\n"
            f"�YZ� �"�-�z�Y 3 �-�'ר�Tם = <b>Community Premium �'�-�Tנם!</b>\n\n"
            f"�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n"
            f"�Y"- <b>ק�Tש�.ר�Tם �o�>�o �"�'�.�~�Tם:</b>\n"
            f"�?� �YZ� Airdrop: <code>https://t.me/SLH_AIR_bot?start=ref_{chat_id}</code>\n"
            f"�?� �Y>�️ Guardian: <code>https://t.me/Grdian_bot?start=ref_{chat_id}</code>\n"
            f"�?� �Y>' BotShop: <code>https://t.me/BotShop_bot?start=ref_{chat_id}</code>\n"
            f"�?� �Y'� Wallet: <code>https://t.me/SLH_Wallet_bot?start=ref_{chat_id}</code>\n"
            f"�?� �YZ" Academia: <code>https://t.me/SLH_Academia_bot?start=ref_{chat_id}</code>\n"
            f"�?� �Y'� Community: <code>https://t.me/SLH_community_bot?start=ref_{chat_id}</code>"
        )
        kb = {"inline_keyboard": [
            [{"text": "�Y"< �"עתק ק�Tש�.ר �"פנ�T�"", "callback_data": "copy_ref"}],
            [{"text": "�Y"� שתף עם �-�'ר", "url": f"https://t.me/share/url?url={ref_link}&text=�Ys? �"צ�~רפ�. �o-SLH - �'�Tת �"שקע�.ת �"�T�'�T�~�o�T!"}],
            [{"text": "�Y"T �-�-ר�" �oתפר�T�~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_portfolio(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        vip_str = VIP_PLANS[user["vip"]]["name"] if user["vip"] else "�Y?" Free"
        text = (
            f"�Y"S <b>�"ת�Tק ש�o�T</b>\n\n"
            f"�Y'Z SLH: {user['slh_balance']:.2f}\n"
            f"�YZ� ZVK: {user['zvk_balance']}\n"
            f"�Y'� Hub נק�.�"�.ת: {user['hub_points']}\n"
            f"�Y'' ס�~�~�.ס: {vip_str}\n"
            f"�Y'� �"פנ�T�.ת: {user['referral_count']}\n"
            f"�o. �zש�T�z�.ת ש�'�.צע�.: {len(user['tasks_done'])}\n"
            f"�Y". �"צ�~רף: {user['joined'][:10]}\n\n"
            f"�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n"
            f"�Y'� <b>�"�zרת נק�.�"�.ת:</b>\n"
            f"1,000 נק�.�"�.ת = 1 SLH Token\n"
            f"5,000 נק�.�"�.ת = 1 �-�.�"ש VIP Basic"
        )
        kb = {"inline_keyboard": [
            [{"text": "�Y'� �"ר�.�.�T�- ע�.�"", "callback_data": "menu_earn"}, {"text": "�Y'' ש�"ר�' VIP", "callback_data": "menu_vip"}],
            [{"text": "�Y"T �-�-ר�" �oתפר�T�~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_deals_inline(self, chat_id, message_id=None):
        text = (
            "�Y"� <b>�z�'צע�Tם פע�T�o�Tם</b>\n\n�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n\n"
            "�Y"� <b>�z�'צע �"שק�" �?" 30% �"נ�-�"!</b>\n  �Y'� �>�o �"�'�.�~�Tם �'-30% �"נ�-�"\n  �Y��️ ק�.�": <code>LAUNCH30</code>\n  ⏰ �-�z�Y �z�.�'�'�o\n\n"
            "�Y'Z <b>�-�'�T�o�" �z�oא�" �?" 6 �'�.�~�Tם</b>\n  �Y'� �z�-�Tר: <b>199�,�</b>\n\n"
            "�Y�� <b>�"�-�z�Y 3 = פר�T�z�T�.ם �-�Tנם!</b>\n\n"
            "�Y>�️ <b>�-�'�T�oת א�'�~�-�"</b>\n  �Y'� Guardian + Wallet = <b>99�,�</b>\n\n"
            "�YZ" <b>�z�'צע ס�~�.�"נ�~�Tם</b>\n  �Y'� 50% �"נ�-�" �?" ק�.�": <code>STUDENT50</code>\n�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�"
        )
        kb = {"inline_keyboard": [
            [{"text": "�Y'Z ר�>�.ש �-�'�T�o�" �z�oא�"", "callback_data": "vip_elite"}],
            [{"text": "�Y>�️ �-�'�T�oת א�'�~�-�"", "callback_data": "vip_basic"}],
            [{"text": "�Y'� �"�-�z�Y �-�'ר�Tם", "callback_data": "menu_referral"}],
            [{"text": "�Y"T �-�-ר�" �oתפר�T�~", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_buy_slh_inline(self, chat_id, message_id=None):
        text = (
            f"�Y�T <b>ר�>�Tשת SLH Coin</b>\n\n"
            f"�Y'� <b>�z�-�Tר:</b> 1 SLH = {SLH_PRICE_ILS}�,�\n"
            f"�Y"� �z�Tנ�T�z�.ם: 0.00004 SLH (0.018�,�)\n\n�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n�Y"S <b>�z�"ר�'�.ת �z�-�Tר:</b>\n\n"
        )
        for tier in SLH_BUY_TIERS:
            text += f"  �Y�T {tier['amount']} SLH = {tier['price']}�,�\n"
        text += (
            f"\n�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n"
            f"�Y'� <b>ארנק TON:</b>\n<code>{TON_WALLET}</code>\n\n"
            f"�Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            "�Y"� ש�o�- צ�T�o�.ם �zס�s א�. Transaction Hash\nא�. צ�.ר קשר עם @Osif83"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.buy_slh_keyboard())
        else:
            self.send(chat_id, text, self.buy_slh_keyboard())

    def handle_buy_slh_select(self, chat_id, amount_str, callback_id, message_id):
        if amount_str == "custom":
            text = (
                f"�o�️ <b>ס�>�.ם �z�.תאם א�Tש�Tת</b>\n\n"
                f"�Y'� �z�-�Tר: 1 SLH = {SLH_PRICE_ILS}�,�\n"
                f"�Y"� �z�Tנ�T�z�.ם: 0.00004 SLH (0.018�,�)\n\n"
                "ש�o�- את �"ס�>�.ם שתרצ�" �oר�>�.ש (�'SLH).\n�o�"�.�'�z�": <code>0.005</code>\n\n"
                f"�Y'� <b>ארנק TON:</b>\n<code>{TON_WALLET}</code>\n\n"
                f"�Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\nא�. צ�.ר קשר עם @Osif83"
            )
            self.edit_message(chat_id, message_id, text, self.back_keyboard())
            self.answer_callback(callback_id)
            return
        try:
            amount = float(amount_str)
        except ValueError:
            self.answer_callback(callback_id, "�O ש�'�Tא�"")
            return
        price = round(amount * SLH_PRICE_ILS, 3)
        text = (
            f"�Y�T <b>ר�>�Tשת {amount} SLH</b>\n\n�Y'� <b>�z�-�Tר:</b> {price}�,�\n\n�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n"
            f"�Y'� <b>ש�o�- {price}�,� �oארנק TON:</b>\n\n<code>{TON_WALLET}</code>\n\n"
            f"�Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            f"�Y"� ש�o�- צ�T�o�.ם �zס�s א�. Transaction Hash\nא�. צ�.ר קשר עם @Osif83\n\n�o. תק�'�o {amount} SLH ת�.�s 24 שע�.ת"
        )
        kb = {"inline_keyboard": [
            [{"text": "�Y'� �"עתק �>ת�.�'ת ארנק", "callback_data": "copy_wallet_slh"}],
            [{"text": "�Y"T �-�-ר�" �oר�>�Tש�"", "callback_data": "menu_buy_slh"}],
        ]}
        self.edit_message(chat_id, message_id, text, kb)
        self.answer_callback(callback_id)

    def handle_help_inline(self, chat_id, message_id=None):
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            "�" <b>SLH HUB �?" ע�-ר�"</b>\n\n"
            "<b>פק�.�"�.ת:</b>\n"
            "/start �?" תפר�T�~ ראש�T\n/earn �?" �zש�T�z�.ת �.�"ר�.�.�-�"\n/swap �?" �"�zרת �z�~�'ע�.ת\n/vip �?" �zנ�.�T פר�T�z�T�.ם\n"
            "/airdrop �?" ר�>�Tשת �~�.קנ�Tם\n/buyslh �?" �Y�T ר�>�Tשת SLH Coin\n/referral �?" ק�Tש�.ר �"פנ�T�"\n"
            "/deals �?" �z�'צע�Tם\n/portfolio �?" �"ת�Tק ש�o�T\n/help �?" ע�-ר�"\n\n"
            "<b>ת�z�T�>�":</b> @Osif83\n<b>אתר:</b> slh-nft.com\n\n"
            f"�"��"��"��"��"��"��"��"��"��"��"��"��"��"��"�\n�Y'� <b>שתף �.�"ר�.�.�T�- 15% �'נק�.�"�.ת SLH!</b>\n�Y"- <code>{ref_link}</code>"
        )
        kb = {"inline_keyboard": [[{"text": "�Y"T �-�-ר�" �oתפר�T�~", "callback_data": "menu_main"}]]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    # �"?�"? Admin �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
    def handle_admin(self, chat_id):
        if str(chat_id) != ADMIN_ID:
            return
        total_users = len(_user_data)
        total_vip = sum(1 for u in _user_data.values() if u.get("vip"))
        total_points = sum(u.get("hub_points", 0) for u in _user_data.values())
        total_refs = sum(u["referral_count"] for u in _user_data.values())
        text = (
            f"�Y>� <b>ADMIN PANEL</b>\n\n"
            f"�Y'� �zשת�zש�Tם: <b>{total_users}</b>\n�Y'' VIP: <b>{total_vip}</b>\n"
            f"�Y'� נק�.�"�.ת ש�-�.�oק�.: <b>{total_points}</b>\n�Y'� �"פנ�T�.ת: <b>{total_refs}</b>\n\n"
            f"<b>פק�.�"�.ת:</b>\n/stats �?" ס�~�~�Tס�~�Tק�.ת\n/broadcast TEXT �?" ש�o�- �"�.�"ע�" �o�>�.�oם\n"
            f"/approve USER_ID PLAN �?" אשר VIP\n/admin �?" פאנ�o �-�""
        )
        self.send(chat_id, text)

    def handle_broadcast(self, chat_id, text):
        if str(chat_id) != ADMIN_ID:
            return
        sent = 0
        for uid in _user_data:
            if self.send(uid, f"�Y"� <b>�"�.�"ע�" �z�"�zער�>ת:</b>\n\n{text}"):
                sent += 1
        self.send(chat_id, f"�o. נש�o�- �o-{sent} �zשת�zש�Tם")

    def handle_approve(self, chat_id, args):
        if str(chat_id) != ADMIN_ID:
            return
        parts = args.split()
        if len(parts) < 2:
            self.send(chat_id, "ש�T�z�.ש: /approve USER_ID PLAN\n�o�"�.�'�z�": /approve 123456 pro")
            return
        try:
            uid = int(parts[0])
            plan = parts[1]
            if plan in VIP_PLANS:
                user = _get_user(uid)
                user["vip"] = plan
                self.send(chat_id, f"�o. א�.שר VIP {VIP_PLANS[plan]['name']} �o�zשת�zש {uid}")
                self.send(uid, f"�YZ? <b>VIP �"�.פע�o!</b>\n\nש�"ר�'ת �o-{VIP_PLANS[plan]['name']}! �Y''")
            else:
                self.send(chat_id, f"�O ת�.�>נ�Tת �oא ק�T�T�zת. אפשר�.�T�.ת: {', '.join(VIP_PLANS.keys())}")
        except:
            self.send(chat_id, "�O ש�'�Tא�". ש�T�z�.ש: /approve USER_ID PLAN")

    # �"?�"? Callback handler �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
    def handle_callback(self, callback):
        data = callback.get("data", "")
        chat_id = callback["message"]["chat"]["id"]
        message_id = callback["message"]["message_id"]
        callback_id = callback["id"]
        first_name = callback["from"].get("first_name", "")

        # �"?�"? P2P callbacks (delegate to handle_p2p_callback) �"?�"?�"?�"?�"?�"?�"?�"?�"?
        if (data.startswith("p2p_") or data.startswith("send_tok_") or
                data.startswith("sell_tok_") or data.startswith("pay_")):
            self.handle_p2p_callback(chat_id, data, callback_id, message_id)
            return

        if data == "menu_main":
            user = _get_user(chat_id)
            vip_badge = "�Y'' VIP" if user["vip"] else "�Y?" Free"
            self.edit_message(chat_id, message_id,
                f"�Ys? <b>SLH HUB SYSTEM</b>\n\n"
                f"�Y'� <b>{first_name}</b> | {vip_badge}\n"
                f"�Y'� �Tתר�": <b>{user['hub_points']}</b> נק�.�"�.ת\n"
                f"�Y'Z SLH: <b>{user['slh_balance']:.2f}</b>\n"
                f"�Y'� �"פנ�T�.ת: <b>{user['referral_count']}</b>\n\n�Y'? �'�-ר פע�.�o�":",
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
            self.answer_callback(callback_id, f"�Y'� {TON_WALLET}", True)
        elif data.startswith("task_"):
            self.handle_task(chat_id, data[5:], callback_id, message_id)
        elif data.startswith("vip_"):
            self.handle_vip_select(chat_id, data[4:], callback_id, message_id)
        elif data == "airdrop_pay":
            self.send(chat_id,
                f"�Y'� <b>ש�o�- תש�o�.ם �oארנק TON:</b>\n\n<code>{TON_WALLET}</code>\n\n"
                f"�Y"- <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
                "�Y"� א�-ר�T �"תש�o�.ם, ש�o�- �>א�Y:\n�?� צ�T�o�.ם �zס�s, א�.\n�?� Transaction Hash",
                self.back_keyboard())
            self.answer_callback(callback_id)
        elif data == "airdrop_status":
            user = _get_user(chat_id)
            self.answer_callback(callback_id, f"�Y'� �Tתר�": {user['hub_points']} נק�.�"�.ת | VIP: {'�>�Y' if user['vip'] else '�oא'}", True)
        elif data == "copy_ref":
            self.answer_callback(callback_id, f"�Y"- https://t.me/SLH_AIR_bot?start=ref_{chat_id}", True)
        elif data.startswith("copy_wallet_"):
            self.answer_callback(callback_id, f"�Y'� {TON_WALLET}", True)
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
                "�Y"� <b>ש�o�T�-ת �z�~�'ע�.ת</b>\n\n"
                "�Y'Z SLH: <code>/send_slh USER_ID AMOUNT</code>\n"
                "�Y'� TON: <code>/send_ton USER_ID AMOUNT</code>\n"
                "�YY� BNB: <code>/send_bnb USER_ID AMOUNT</code>\n"
                "�YZ� ZVK: <code>/send_zvk USER_ID AMOUNT</code>\n\n"
                "�Y'� ק�'�o את �"-USER_ID ש�o �"נ�zע�Y: �'קש �z�zנ�. /myid",
                self.wallet_inline_keyboard())
            self.answer_callback(callback_id)
        elif data == "wallet_history":
            self.handle_tx_history(chat_id)
            self.answer_callback(callback_id)
        elif data == "wallet_refresh":
            self.handle_wallet(chat_id, message_id)
            self.answer_callback(callback_id, "�Y"" �zרענ�Y...")
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
                self.send(uid, f"�o. �"פק�"�" #{dep_id} א�.שר�"! �"פק�"�.�Y פע�T�o.")
                self.answer_callback(callback_id, "�o. א�.שר!", True)
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
                self.send(uid, f"�O �"פק�"�" #{dep_id} נ�"�-ת�".\nנס�" ש�.�' א�. פנ�" �oת�z�T�>�".")
                self.answer_callback(callback_id, "�O נ�"�-�"", True)
        else:
            self.answer_callback(callback_id)

    # �"?�"? Text message handler �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
    # �.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�
    # P2P TRADING MODULE
    # �.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�
    API_BASE = "https://slh-api-production.up.railway.app"

    def _p2p_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "�Y"� ש�o�- �~�.ק�Y", "callback_data": "p2p_send"},
             {"text": "�Y>' �o�.�- �z�>�Tר�.ת", "callback_data": "p2p_browse"}],
            [{"text": "�Y'� פרסם �z�>�Tר�"", "callback_data": "p2p_sell"},
             {"text": "�Y"< �"�"�-�zנ�.ת ש�o�T", "callback_data": "p2p_myorders"}],
            [{"text": "�Y"T תפר�T�~ ראש�T", "callback_data": "menu_main"}],
        ]}

    def _token_keyboard(self, prefix):
        return {"inline_keyboard": [
            [{"text": "�Y'Z SLH", "callback_data": f"{prefix}_SLH"},
             {"text": "�YZ� ZVK", "callback_data": f"{prefix}_ZVK"},
             {"text": "�Y'� MNH", "callback_data": f"{prefix}_MNH"}],
            [{"text": "�O �'�T�~�.�o", "callback_data": "p2p_cancel"}],
        ]}

    def _payment_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "�Y"� Bit", "callback_data": "pay_Bit"},
             {"text": "�Y"� PayBox", "callback_data": "pay_PayBox"}],
            [{"text": "�Y�� Bank", "callback_data": "pay_Bank"},
             {"text": "�Y'� MNH", "callback_data": "pay_MNH"}],
            [{"text": "�O �'�T�~�.�o", "callback_data": "p2p_cancel"}],
        ]}

    def handle_p2p_menu(self, chat_id):
        self._refresh_balances(chat_id)
        user = _get_user(chat_id)
        self.send(chat_id,
            f"�Y"" <b>P2P �zס�-ר �?" SLH Spark</b>\n"
            f"�.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�\n\n"
            f"�Y'Z SLH: <b>{user['slh_balance']:,.4f}</b>\n"
            f"�YZ� ZVK: <b>{user['zvk_balance']}</b>\n"
            f"�Y'� MNH: <b>{user.get('mnh_balance', 0):.2f}</b>\n\n"
            f"�Y"� <b>ש�o�- �~�.ק�Y</b> �?" �"ע�'ר�" �Tש�Tר�" �o�zשת�zש\n"
            f"�Y>' <b>�o�.�- �z�>�Tר�.ת</b> �?" קנ�" �z�"ק�"�T�o�"\n"
            f"�Y'� <b>פרסם �z�>�Tר�"</b> �?" �z�>�.ר את �"�~�.קנ�Tם ש�o�s\n"
            f"�Y"< <b>�"�"�-�zנ�.ת ש�o�T</b> �?" נ�T�"�.�o �"�-�zנ�.ת פת�.�-�.ת",
            self._p2p_keyboard())

    # �"?�"? SEND FLOW �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
    def p2p_start_send(self, chat_id):
        self._pending_p2p[chat_id] = {"flow": "send", "step": "choose_token", "data": {}}
        self.send(chat_id, "�Y"� <b>ש�o�- �~�.ק�Y</b>\n\n�'�-ר א�T�-�" �~�.ק�Y �oש�o�.�-:", self._token_keyboard("send_tok"))

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
                    self.send(chat_id, "�O א�T אפשר �oש�o�.�- �oעצ�z�s.")
                    return True
                data["to_user"] = to_user
                state["step"] = "enter_amount"
                self.send(chat_id,
                    f"�Y'� <b>�>�z�" {data['token']} �oש�o�.�-?</b>\n"
                    f"�"�Tתר�" ש�o�s: {self._get_balance_for(chat_id, data['token']):.4f}\n\n"
                    f"�"�>נס ס�>�.ם (�zספר �'�o�'�"):")
            except ValueError:
                self.send(chat_id, "�O User ID �oא תק�T�Y. �"�>נס �zספר �'�o�'�" (�o�"�.�'�z�": 224223270)")
            return True

        if step == "enter_amount":
            try:
                amount = float(text.strip())
                if amount <= 0:
                    raise ValueError
                bal = self._get_balance_for(chat_id, data["token"])
                if amount > bal:
                    self.send(chat_id, f"�O �Tתר�" �oא �zספ�Tק�". �Tש �o�s {bal:.4f} {data['token']}")
                    return True
                data["amount"] = amount
                state["step"] = "confirm"
                self.send(chat_id,
                    f"�o. <b>א�Tש�.ר �"ע�'ר�"</b>\n\n"
                    f"�Y"� ש�.�o�-: <b>{amount} {data['token']}</b>\n"
                    f"�Y'� �o�zשת�zש ID: <code>{data['to_user']}</code>\n\n"
                    f"ש�o�- <b>�>�Y</b> �oא�Tש�.ר א�. <b>�oא</b> �o�'�T�~�.�o:")
            except ValueError:
                self.send(chat_id, "�O ס�>�.ם �oא תק�T�Y. �"�>נס �zספר (�o�"�.�'�z�": 10.5)")
            return True

        if step == "confirm":
            if text.strip().lower() in ("�>�Y", "yes", "א�Tש�.ר", "�o."):
                self._p2p_execute_send(chat_id, data)
            else:
                del self._pending_p2p[chat_id]
                self.send(chat_id, "�O �"ע�'ר�" �'�.�~�o�".", self.main_reply_keyboard())
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
                    f"�o. <b>נש�o�- �'�"צ�o�-�"!</b>\n\n"
                    f"�Y'� <b>{data['amount']} {data['token']}</b> �?' �zשת�zש <code>{data['to_user']}</code>\n"
                    f"�Y�� TX: #{result.get('transfer_id', '�?"')}\n\n"
                    f"�Y'� /wallet �oצפ�T�T�" �'�Tתר�"", self.main_reply_keyboard())
                # Notify receiver
                self.send(data["to_user"],
                    f"�Y'� <b>ק�T�'�oת {data['amount']} {data['token']}!</b>\n\n"
                    f"�Y'� �z: �zשת�zש {chat_id}\n"
                    f"�Y'� /wallet �oצפ�T�T�" �'�Tתר�"")
            else:
                err = result.get("detail", result.get("error", "ש�'�Tא�" �oא �T�"�.ע�""))
                self.send(chat_id, f"�O {err}", self.main_reply_keyboard())
        except Exception as e:
            logger.error(f"P2P send error: {e}")
            self.send(chat_id, "�O ש�'�Tא�" �'ש�o�T�-�". נס�" ש�.�'.", self.main_reply_keyboard())
        finally:
            self._pending_p2p.pop(chat_id, None)

    # �"?�"? SELL FLOW �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
    def p2p_start_sell(self, chat_id):
        self._refresh_balances(chat_id)
        user = _get_user(chat_id)
        if user["slh_balance"] <= 0 and user["zvk_balance"] <= 0 and user.get("mnh_balance", 0) <= 0:
            self.send(chat_id, "�O א�T�Y �o�s �~�.קנ�Tם �o�z�>�Tר�".", self.main_reply_keyboard())
            return
        self._pending_p2p[chat_id] = {"flow": "sell", "step": "choose_token", "data": {}}
        self.send(chat_id, "�Y'� <b>פרסם �z�>�Tר�"</b>\n\n�'�-ר א�T�-�" �~�.ק�Y �o�z�>�.ר:", self._token_keyboard("sell_tok"))

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
                    self.send(chat_id, f"�O �Tתר�" �oא �zספ�Tק�". �Tש �o�s {bal:.4f} {data['token']}")
                    return True
                data["amount"] = amount
                state["step"] = "enter_price"
                self.send(chat_id,
                    f"�Y'� <b>�z�-�Tר �o�>�o {data['token']} (�'שק�o�Tם �,�)</b>\n\n"
                    f"�o�"�.�'�z�": אם SLH = 444�,�, �"�>נס <b>444</b>\n"
                    f"�"�>נס �z�-�Tר:")
            except ValueError:
                self.send(chat_id, "�O ס�>�.ם �oא תק�T�Y.")
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
                    f"�Y'� <b>ש�T�~ת תש�o�.ם �z�.ע�"פת</b>\n\n"
                    f"תק�'�o: <b>{total:.2f} �,�</b> ע�'�.ר {data['amount']} {data['token']}\n\n"
                    f"�'�-ר א�T�s �oק�'�o תש�o�.ם:", self._payment_keyboard())
            except ValueError:
                self.send(chat_id, "�O �z�-�Tר �oא תק�T�Y.")
            return True

        if step == "confirm":
            if text.strip().lower() in ("�>�Y", "yes", "א�Tש�.ר", "�o."):
                self._p2p_execute_sell(chat_id, data)
            else:
                del self._pending_p2p[chat_id]
                self.send(chat_id, "�O �z�>�Tר�" �'�.�~�o�".", self.main_reply_keyboard())
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
                    f"�o. <b>�"�-�zנת �z�>�Tר�" נ�.צר�"!</b>\n\n"
                    f"�Y?" �"�-�zנ�": <b>#{order['id']}</b>\n"
                    f"�Y'� �z�.�>ר: <b>{order['amount']} {order['token']}</b>\n"
                    f"�Y'� �z�-�Tר: <b>{order['price_per_unit']} �,�</b> �o�T�-�T�"�"\n"
                    f"�Y"S ס�"\"�>: <b>{order['amount'] * order['price_per_unit']:.2f} �,�</b>\n"
                    f"�Y'� תש�o�.ם: <b>{order['payment_method']}</b>\n\n"
                    f"�Y"' �"�~�.קנ�Tם ננע�o�. �'-escrow �?" �T�.ע�'ר�. �oק�.נ�" א�.�~�.�z�~�Tת.\n"
                    f"�o�'�T�~�.�o: �Y"< �"�"�-�zנ�.ת ש�o�T", self.main_reply_keyboard())
                # Refresh balance (tokens were escrowed)
                self._refresh_balances(chat_id)
            else:
                err = result.get("detail", "ש�'�Tא�" �oא �T�"�.ע�"")
                self.send(chat_id, f"�O {err}", self.main_reply_keyboard())
        except Exception as e:
            logger.error(f"P2P sell error: {e}")
            self.send(chat_id, "�O ש�'�Tא�" �'�Tצ�Tרת �"�-�zנ�".", self.main_reply_keyboard())
        finally:
            self._pending_p2p.pop(chat_id, None)

    # �"?�"? BROWSE + BUY �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
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
                    "�Y>' <b>�o�.�- �z�>�Tר�.ת</b>\n\nא�T�Y �"�-�zנ�.ת פת�.�-�.ת �>ר�'ע.\n"
                    "�"�T�" �"ראש�.�Y �oפרסם! �?' �Y'� פרסם �z�>�Tר�"", self.main_reply_keyboard())
                return

            text = "�Y>' <b>�o�.�- �z�>�Tר�.ת �?" �"�-�zנ�.ת פת�.�-�.ת</b>\n�.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�\n\n"
            buttons = []
            for o in orders[:8]:
                total = o["amount"] * o["price_per_unit"]
                text += (
                    f"�Y"- <b>#{o['id']}</b> | {o['token']} | {o['amount']:.4f} �T�-�T�"�.ת\n"
                    f"   �Y'� {o['price_per_unit']} �,�/�T�-�T�"�" | ס�"\"�>: <b>{total:.2f} �,�</b>\n"
                    f"   �Y'� {o['payment_method']} | �Y'� �z�.�>ר: {o['seller_id']}\n\n"
                )
                if o["seller_id"] != chat_id:
                    buttons.append([{"text": f"�Y>' קנ�" #{o['id']} ({o['amount']:.2f} {o['token']})",
                                     "callback_data": f"p2p_buy_{o['id']}"}])

            buttons.append([{"text": "�Y'� פרסם �z�>�Tר�"", "callback_data": "p2p_sell"},
                             {"text": "�Y"T P2P", "callback_data": "p2p_menu"}])
            self.send(chat_id, text, {"inline_keyboard": buttons})
        except Exception as e:
            logger.error(f"P2P browse error: {e}")
            self.send(chat_id, "�O ש�'�Tא�" �'�~ע�Tנת �o�.�- �z�>�Tר�.ת.", self.main_reply_keyboard())

    def p2p_buy(self, chat_id, order_id):
        """Fill an order (buy from seller)."""
        try:
            # Fetch order details first
            resp = self.session.get(f"{self.API_BASE}/api/p2p/orders",
                                    params={"status": "active", "limit": 50}, timeout=8)
            orders = {o["id"]: o for o in resp.json().get("orders", [])}
            order = orders.get(order_id)
            if not order:
                self.send(chat_id, "�O �"�-�zנ�" �oא נ�zצא�" א�. �>�'ר נס�'ר�".", self.main_reply_keyboard())
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
                    f"�o. <b>ר�>�Tש�" �"�.ש�o�z�"!</b>\n\n"
                    f"�Y'� ק�T�'�oת: <b>{order['amount']:.4f} {order['token']}</b>\n"
                    f"�Y'� �oש�oם: <b>{total:.2f} �,�</b>\n"
                    f"�Y'� ש�T�~�": <b>{order['payment_method']}</b>\n"
                    f"�Y'� �z�.�>ר ID: <code>{order['seller_id']}</code>\n\n"
                    f"�s�️ <b>ש�oם �o�z�.�>ר �Tש�Tר�.ת!</b>\n"
                    f"ש�o�- �o�. �"�.�"ע�" �'-Telegram עם ID: <code>{order['seller_id']}</code>\n"
                    f"�"�~�.קנ�Tם �>�'ר �-�.�>�. �o�-ש�'�.נ�s �?" /wallet �oצפ�T�T�".",
                    self.main_reply_keyboard())
                # Notify seller
                self.send(order["seller_id"],
                    f"�YZ? <b>�"�-�zנ�" #{order_id} נ�z�>ר�"!</b>\n\n"
                    f"�Y'� {order['amount']:.4f} {order['token']}\n"
                    f"�Y'� �oק�'�o: <b>{total:.2f} �,�</b> �z-{order['payment_method']}\n"
                    f"�Y'� ק�.נ�" ID: <code>{chat_id}</code>\n\n"
                    f"�z�zת�T�Y �oתש�o�.ם �z�zנ�.!")
                self._refresh_balances(chat_id)
            else:
                err = result.get("detail", "ש�'�Tא�" �oא �T�"�.ע�"")
                self.send(chat_id, f"�O {err}", self.main_reply_keyboard())
        except Exception as e:
            logger.error(f"P2P buy error: {e}")
            self.send(chat_id, "�O ש�'�Tא�" �'ר�>�Tש�".", self.main_reply_keyboard())

    # �"?�"? MY ORDERS �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
    def p2p_my_orders(self, chat_id):
        try:
            resp = self.session.get(f"{self.API_BASE}/api/p2p/orders",
                                    params={"status": "active", "limit": 50}, timeout=8)
            all_orders = resp.json().get("orders", [])
            mine = [o for o in all_orders if o["seller_id"] == chat_id]

            if not mine:
                self.send(chat_id,
                    "�Y"< <b>�"�"�-�zנ�.ת ש�o�T</b>\n\nא�T�Y �o�s �"�-�zנ�.ת פת�.�-�.ת.\n�Y'� ר�.צ�" �o�z�>�.ר? �?' פרסם �z�>�Tר�"",
                    self._p2p_keyboard())
                return

            text = "�Y"< <b>�"�"�-�zנ�.ת ש�o�T</b>\n�.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�\n\n"
            buttons = []
            for o in mine:
                total = o["amount"] * o["price_per_unit"]
                text += (
                    f"�Y"- <b>#{o['id']}</b> | {o['token']}\n"
                    f"   �Y'� {o['amount']:.4f} | {o['price_per_unit']} �,�/�T�-' | ס�"\"�> {total:.2f} �,�\n"
                    f"   �Y'� {o['payment_method']}\n\n"
                )
                buttons.append([{"text": f"�O �'�~�o �"�-�zנ�" #{o['id']}",
                                  "callback_data": f"p2p_cancel_order_{o['id']}"}])

            buttons.append([{"text": "�Y"T P2P", "callback_data": "p2p_menu"}])
            self.send(chat_id, text, {"inline_keyboard": buttons})
        except Exception as e:
            logger.error(f"P2P my_orders error: {e}")
            self.send(chat_id, "�O ש�'�Tא�" �'�~ע�Tנת �"�-�zנ�.ת.", self.main_reply_keyboard())

    def p2p_cancel_order(self, chat_id, order_id):
        try:
            resp = self.session.delete(
                f"{self.API_BASE}/api/p2p/cancel-order/{order_id}",
                params={"seller_id": chat_id}, timeout=10
            )
            result = resp.json()
            if resp.status_code == 200 and result.get("ok"):
                self.send(chat_id,
                    f"�o. <b>�"�-�zנ�" #{order_id} �'�.�~�o�"</b>\n\n"
                    f"�Y"" �"�.�-�-ר: <b>{result['refunded_amount']} {result['refunded_token']}</b>\n"
                    f"�Y'� /wallet �oצפ�T�T�" �'�Tתר�"", self.main_reply_keyboard())
                self._refresh_balances(chat_id)
            else:
                err = result.get("detail", "ש�'�Tא�"")
                self.send(chat_id, f"�O {err}", self.main_reply_keyboard())
        except Exception as e:
            logger.error(f"P2P cancel order error: {e}")
            self.send(chat_id, "�O ש�'�Tא�" �'�'�T�~�.�o.", self.main_reply_keyboard())

    # �"?�"? P2P CALLBACK DISPATCHER �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
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
            self.send(chat_id, "�O �'�.�~�o.", self.main_reply_keyboard())

        # Token selection for send
        elif data.startswith("send_tok_"):
            token = data.split("_")[-1]
            state = self._pending_p2p.get(chat_id, {})
            if state.get("flow") == "send":
                state["data"]["token"] = token
                state["step"] = "enter_recipient"
                self.send(chat_id,
                    f"�Y"� <b>ש�o�- {token}</b>\n\n"
                    f"�"�>נס את �"-Telegram User ID ש�o �"נ�zע�Y:\n"
                    f"(�"נ�zע�Y �T�>�.�o �oש�o�.�- /myid �>�"�T �o�"עת את �"-ID ש�o�.)")

        # Token selection for sell
        elif data.startswith("sell_tok_"):
            token = data.split("_")[-1]
            state = self._pending_p2p.get(chat_id, {})
            if state.get("flow") == "sell":
                bal = self._get_balance_for(chat_id, token)
                if bal <= 0:
                    self.send(chat_id, f"�O א�T�Y �o�s {token} �o�z�>�Tר�".")
                    return
                state["data"]["token"] = token
                state["step"] = "enter_amount"
                self.send(chat_id,
                    f"�Y'� <b>�>�z�" {token} �o�z�>�.ר?</b>\n"
                    f"�"�Tתר�" ש�o�s: <b>{bal:.4f}</b>\n\n"
                    f"�"�>נס �>�z�.ת:")

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
                    f"�o. <b>א�Tש�.ר פרס�.ם �z�>�Tר�"</b>\n\n"
                    f"�Y'� �z�.�>ר: <b>{d['amount']} {d['token']}</b>\n"
                    f"�Y'� �z�-�Tר: <b>{d['price']} �,�</b> �o�T�-�T�"�"\n"
                    f"�Y"S ס�"\"�>: <b>{total:.2f} �,�</b>\n"
                    f"�Y'� תש�o�.ם: <b>{method}</b>\n\n"
                    f"�Y"' �"�~�.קנ�Tם �Tנע�o�. �'-escrow ע�" �o�z�>�Tר�".\n\n"
                    f"ש�o�- <b>�>�Y</b> �oא�Tש�.ר א�. <b>�oא</b> �o�'�T�~�.�o:")

        # Buy order
        elif data.startswith("p2p_buy_"):
            order_id = int(data.split("_")[-1])
            self.p2p_buy(chat_id, order_id)

        # Cancel own order
        elif data.startswith("p2p_cancel_order_"):
            order_id = int(data.split("_")[-1])
            self.p2p_cancel_order(chat_id, order_id)

    # �.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.��.�

    def handle_text(self, chat_id, text, first_name, username):
        """Handle non-command text and legacy reply keyboard buttons.

        STRICT rules �?" no more 'any text = payment':
        - Valid username: 3�?"32 chars of [A-Za-z0-9_], and user is in username-collection state
        - Valid BSC/ETH TX hash: '0x' + exactly 64 hex chars (66 total)
        - Valid TON TX hash: 44 base64 chars OR 64 hex chars
        - Anything else �?' polite fallback (no false "payment received")
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
                f"�o. <b>נרש�zת!</b> @{text}\n\n"
                f"�Y'� �oר�>�Tש�" ש�o�- �oארנק TON:\n<code>{TON_WALLET}</code>\n\n"
                "�Y"� ש�o�- צ�T�o�.ם �zס�s א�. Transaction Hash",
                self.back_keyboard())
            if str(chat_id) != ADMIN_ID:
                self.send(int(ADMIN_ID), f"�Y'� <b>�zשת�zש �-�"ש:</b> @{text} ({chat_id})")
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
                "�Y"� <b>תש�o�.ם �"תק�'�o �o�'�"�Tק�"!</b>\n\n"
                "�Y"- Hash: <code>" + text[:20] + "...</code>\n"
                "⏳ ס�~�~�.ס: <b>�z�zת�T�Y �oא�Tש�.ר א�"�z�T�Y</b>\n\n"
                "תק�'�o �"תרא�" �'ר�'ע ש�"תש�o�.ם �Tא�.�zת (ע�" 24 שע�.ת).\n"
                "�Y'� �'�Tנת�T�Tם, �"צ�~רף: @SLH_Community",
                self.back_keyboard())
            if str(chat_id) != ADMIN_ID:
                self.send(int(ADMIN_ID),
                    f"�Y'� <b>עסק�" �-�"ש�" �oא�Tש�.ר!</b>\n"
                    f"User: {chat_id} (@{user.get('username','?')})\n"
                    f"Hash: <code>{text}</code>\n"
                    f"/approve_{chat_id} א�. /reject_{chat_id}")
            return

        # --- 3) TX hash received OUT OF state �?' tell user to start flow ---
        if is_tx_hash and state != "awaiting_payment":
            self.send(chat_id,
                "�s�️ ק�T�'�oת�T Hash א�'�o א�T�Y �'קשת תש�o�.ם פת�.�-�".\n\n"
                "�oתש�o�.ם �-�"ש, �o�-ץ /start �?' �Y'� �"פע�o�"",
                self.main_reply_keyboard())
            return

        # --- 4) Wallet address (informational only, no payment assumed) ---
        if re.match(r'^(0x[0-9a-fA-F]{40}|[UE]Q[A-Za-z0-9_-]{46})$', text):
            self.send(chat_id,
                "�Y"< ק�T�'�oת�T �>ת�.�'ת ארנק. �oש�o�.�- �>סף א�o �>ת�.�'ת �-�.? �o�-ץ /start �?' �Y'� ארנק\n\n"
                "�s�️ ש�Tם �o�': ש�o�T�-ת �>ת�.�'ת �o�'�" �oא פ�.ת�-ת תש�o�.ם.",
                self.main_reply_keyboard())
            return

        # --- 5) Fallback (no more false payment confirmations) ---
        # If user is in payment state but didn't send TX hash or photo �?" remind them
        if state == "awaiting_payment":
            self.send(chat_id,
                "�s�️ <b>ש�o�' �"תש�o�.ם פת�.�-!</b>\n\n"
                "�>�"�T �o�"ש�o�Tם:\n"
                "1️�f� �"ע�'ר TON �o�>ת�.�'ת:\n<code>" + TON_WALLET + "</code>\n\n"
                "2️�f� ש�o�- �o�T <b>צ�T�o�.ם �zס�s</b> ש�o �"�"ע�'ר�"\n"
                "   א�. <b>Transaction Hash</b>\n\n"
                "�Y"� אפשר �oש�o�.�- ת�z�.נ�" �Tש�Tר�.ת �oצ'א�~ �"�-�"!\n\n"
                "�" צר�T�s ע�-ר�"? צ�.ר קשר: @osifeu_prog",
                self.back_keyboard())
            return

        self.send(chat_id, "�Y�- �oא �"�'נת�T. �o�-ץ /start �oתפר�T�~ �"ראש�T", self.main_reply_keyboard())

    # �"?�"? Main loop �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
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
                        self.send(chat_id, "�Y"� ק�'�oנ�.! נ�'�"�.ק �.נע�"�>�Y �'�"ק�"ם.", self.back_keyboard())
                        if str(chat_id) != ADMIN_ID:
                            self.send(int(ADMIN_ID), f"�Y"� <b>�"�.�>�-ת תש�o�.ם!</b>\nUser: {chat_id} (@{username})")
                    continue

                logger.info(f"�Y"� {first_name}: {text}")

                # �"?�"? Slash commands �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
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
                        self.send(chat_id, "ש�T�z�.ש: /send TOKEN USER_ID AMOUNT\n�"�.�'�z�": /send ZVK 123456789 50")
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
                    self.send(chat_id, "�Y"z <b>ת�z�T�>�"</b>\n\nפנ�" �o-@Osif83 �o�>�o שא�o�".", self.main_reply_keyboard())
                elif text == "/myid":
                    self.send(chat_id, f"�Y?" <b>�"�z�-�"�" ש�o�s:</b> <code>{chat_id}</code>", self.main_reply_keyboard())
                elif text == "/hub":
                    user = _get_user(chat_id)
                    vip_badge = "�Y'' VIP" if user["vip"] else "�Y?" Free"
                    self.send(chat_id,
                        f"�Ys? <b>SLH HUB SYSTEM</b>\n\n"
                        f"�Y'� <b>{first_name}</b> | {vip_badge}\n"
                        f"�Y'� �Tתר�": <b>{user['hub_points']}</b> נק�.�"�.ת\n"
                        f"�Y'Z SLH: <b>{user['slh_balance']:.2f}</b>\n"
                        f"�Y'� �"פנ�T�.ת: <b>{user['referral_count']}</b>\n\n�Y'? �'�-ר פע�.�o�":",
                        self.hub_inline_keyboard())

                # �"?�"? Reply keyboard buttons (text buttons at bottom) �"?�"?
                elif text == "�Y"S �"ש�.ק ע�>ש�T�.":
                    self.handle_prices(chat_id)
                elif text == "�Y'� �"שקע�.ת":
                    self.handle_investments(chat_id)
                elif text == "�Y'� ארנק":
                    self.handle_wallet(chat_id)
                elif text == "�Y"" P2P �zס�-ר":
                    self.handle_p2p_menu(chat_id)
                elif text == "�Y"- On-Chain":
                    self.handle_onchain_balance(chat_id)
                elif text == "�Y>� ס�T�>�.�Y �.�'קר�"":
                    self.handle_risk(chat_id)
                elif text == "�YZ� �'�.נ�.ס�Tם":
                    self.handle_bonuses(chat_id)
                elif text == "�Y'� �"�-�z�Y":
                    self.handle_invite(chat_id)
                elif text == "�Y"S �"ש�'�.ר�"":
                    self.handle_dashboard(chat_id)
                elif text == "�Y'� �"פע�o�"":
                    self.handle_activate(chat_id)
                elif text == "�Y"� ש�Tת�.ף":
                    self.handle_share(chat_id)
                elif text == "�Y"s �z�"ר�T�>�Tם":
                    self.handle_guides(chat_id)
                elif text == "�Y"� �z�'צע�Tם":
                    self.handle_deals_text(chat_id)
                elif text == "�Y�T ר�>�Tשת SLH":
                    self.handle_buy_slh_text(chat_id)

                # �"?�"? Swap commands �"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?�"?
                elif text.startswith("/swap "):
                    self.handle_swap_text(chat_id)
                elif text.startswith("/limit "):
                    self.send(chat_id, "�Y"� פק�.�"ת Limit נרש�z�". תק�'�o �"תרא�" �>ש�"�z�-�Tר �T�'�Tע �o�Tע�".", self.main_reply_keyboard())
                elif text.startswith("/alert "):
                    self.handle_alerts(chat_id)
                elif text == "/orders":
                    self.send(chat_id, "�Y"< <b>פק�.�"�.ת פת�.�-�.ת:</b>\n\nא�T�Y פק�.�"�.ת פת�.�-�.ת.", self.main_reply_keyboard())
                elif text == "/ai" or text == "�Y�� נ�Tת�.�- AI":
                    self.handle_ai_analysis(chat_id)

                elif not text.startswith("/"):
                    self.handle_text(chat_id, text, first_name, username)
                else:
                    self.send(chat_id, "�Y�- פק�.�"�" �oא �z�.�>רת. �o�-ץ /start", self.main_reply_keyboard())

        except Exception as e:
            logger.error(f"Update error: {e}")

    def run(self):
        logger.info("=" * 50)
        logger.info("�Ys? SLH Investment House + HUB BOT �?" Starting...")
        logger.info("=" * 50)

        try:
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe", timeout=10)
            if r.status_code == 200 and r.json().get("ok"):
                logger.info(f"�o. Bot: @{r.json()['result']['username']}")
            else:
                logger.error("�O Bot connection failed")
                return
        except Exception as e:
            logger.error(f"�O Bot test error: {e}")
            return

        logger.info("�Y"" Running �?" Investment House + HUB + Buy SLH")

        while True:
            try:
                self.process_updates()
                time.sleep(0.5)
            except KeyboardInterrupt:
                logger.info("�Y>' Bot stopped")
                break
            except Exception as e:
                logger.error(f"�O Main loop error: {e}")
                time.sleep(5)


def main():
    bot = SLHInvestmentBot()
    bot.run()


if __name__ == "__main__":
    main()



