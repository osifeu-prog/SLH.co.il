"""
SLH Investment House + HUB BOT
Full-featured investment house with HUB economic engine.

Features:
- 📊 Live prices (12 coins)
- 💼 Investment plans (4 tiers, 4%-5.4% monthly)
- 💰 Wallet (TON/BNB/SLH/ZVK)
- 🎮 Bonuses & games (slots, dice, basketball, darts)
- 🛡 Risk management
- 🔁 Swap/DEX
- 🧠 AI analysis
- 📊 Dashboard
- 👥 Referrals (15% commission in SLH points)
- 🪙 Buy SLH (444₪ per coin)
- 👑 VIP membership
- 🎁 Airdrop
- 💰 Earn (daily tasks)
- 🔥 Deals & promotions
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

# ── Add shared module to path ────────────────────────────────────────
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

# ── Price API ────────────────────────────────────────────────────────
COINS = {
    "BTC": {"symbol": "bitcoin", "emoji": "🟡", "name": "BTC"},
    "ETH": {"symbol": "ethereum", "emoji": "🔵", "name": "ETH"},
    "TON": {"symbol": "the-open-network", "emoji": "💠", "name": "TON"},
    "BNB": {"symbol": "binancecoin", "emoji": "🟠", "name": "BNB"},
    "SOL": {"symbol": "solana", "emoji": "🟣", "name": "SOL"},
    "DOGE": {"symbol": "dogecoin", "emoji": "🐶", "name": "DOGE"},
    "XRP": {"symbol": "ripple", "emoji": "⚪", "name": "XRP"},
    "ADA": {"symbol": "cardano", "emoji": "🔴", "name": "ADA"},
    "DOT": {"symbol": "polkadot", "emoji": "🟤", "name": "DOT"},
    "AVAX": {"symbol": "avalanche-2", "emoji": "❤️", "name": "AVAX"},
    "LINK": {"symbol": "chainlink", "emoji": "🔗", "name": "LINK"},
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


# ── In-memory user state ─────────────────────────────────────────────
_user_data = {}

# Investment plans
INVESTMENT_PLANS = [
    {"name": "🌱 פקדון חודשי", "rate": 4, "annual": 48, "min_ton": 1, "days": 30},
    {"name": "📈 פקדון רבעוני", "rate": 4.5, "annual": 55, "min_ton": 5, "days": 90},
    {"name": "💎 פקדון חצי-שנתי", "rate": 5, "annual": 60, "min_ton": 10, "days": 180},
    {"name": "👑 פקדון שנתי", "rate": 5.4, "annual": 65, "min_ton": 25, "days": 365},
]

VIP_PLANS = {
    "basic": {"name": "VIP Basic", "price_ils": 41, "features": ["התראות מחירים", "גישה לערוץ VIP", "5 משימות נוספות ביום"]},
    "pro": {"name": "VIP Pro", "price_ils": 99, "features": ["הכל ב-Basic", "סיגנלים למסחר", "גישה ל-1-on-1", "עמלת רפרל כפולה (30%)"]},
    "elite": {"name": "VIP Elite", "price_ils": 199, "features": ["הכל ב-Pro", "קבוצת וויסט בלעדית", "NFT חינם כל חודש", "גישה מוקדמת לכל מוצר חדש"]},
}

SLH_BUY_TIERS = [
    {"amount": 0.0001, "price": 0.044},
    {"amount": 0.001, "price": 0.444},
    {"amount": 0.01, "price": 4.44},
    {"amount": 0.1, "price": 44.4},
    {"amount": 1, "price": 444},
]

_daily_tasks = [
    {"id": "join_channel", "title": "📢 הצטרף לערוץ @SLH_Community", "reward": 50},
    {"id": "share_bot", "title": "📤 שתף את הבוט עם חבר", "reward": 100},
    {"id": "visit_site", "title": "🌐 בקר באתר slh-nft.com", "reward": 30},
    {"id": "follow_fb", "title": "👍 עקוב אחרי Facebook SLH", "reward": 40},
    {"id": "daily_login", "title": "✅ כניסה יומית", "reward": 10},
]


def _get_user(user_id: int) -> dict:
    if user_id not in _user_data:
        _user_data[user_id] = {
            "username": "", "first_name": "",
            "slh_balance": 199788.32, "zvk_balance": 1000,
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
        }
    return _user_data[user_id]


class SLHInvestmentBot:
    def __init__(self):
        self.offset = 0
        self.session = requests.Session()
        self.session.timeout = 30

        # ── Async event loop in background thread (for WalletEngine) ──
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._loop_thread.start()

        # ── WalletEngine (blockchain wallets) ─────────────────────────
        self.wallet = None
        self._wallet_ready = False
        self._pending_send = {}  # chat_id -> {step, token, to_user}
        try:
            from wallet_engine import WalletEngine
            self.wallet = WalletEngine()
            future = asyncio.run_coroutine_threadsafe(self.wallet.init(), self._loop)
            future.result(timeout=15)
            self._wallet_ready = True
            logger.info("✅ WalletEngine connected — DB + Redis + BSC + TON")
        except Exception as e:
            logger.warning(f"⚠️ WalletEngine init failed (falling back to mock): {e}")

        logger.info("🚀 SLH Investment House + HUB initialized")

    def _run_async(self, coro, timeout=10):
        """Run an async coroutine from synchronous code via the background loop."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    # ── Telegram API ─────────────────────────────────────────────────
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

    # ── Reply keyboard (main menu buttons at bottom) ──────────────────
    def main_reply_keyboard(self):
        return {"keyboard": [
            [{"text": "📊 השוק עכשיו"}, {"text": "💼 השקעות"}],
            [{"text": "💰 ארנק"}, {"text": "🛡 סיכון ובקרה"}],
            [{"text": "🎮 בונוסים"}, {"text": "👥 הזמן"}],
            [{"text": "📊 דשבורד"}, {"text": "🪙 רכישת SLH"}],
            [{"text": "💳 הפעלה"}, {"text": "📤 שיתוף"}],
            [{"text": "📚 מדריכים"}, {"text": "🔥 מבצעים"}],
        ], "resize_keyboard": True, "one_time_keyboard": False}

    # ── Inline keyboards ─────────────────────────────────────────────
    def hub_inline_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "💰 Earn", "callback_data": "menu_earn"}, {"text": "🔄 Swap", "callback_data": "menu_swap"}],
            [{"text": "👑 VIP", "callback_data": "menu_vip"}, {"text": "🎁 Airdrop", "callback_data": "menu_airdrop"}],
            [{"text": "🪙 Buy SLH", "callback_data": "menu_buy_slh"}],
            [{"text": "👥 הפניות שלי", "callback_data": "menu_referral"}, {"text": "📊 התיק שלי", "callback_data": "menu_portfolio"}],
            [{"text": "🔥 מבצעים", "callback_data": "menu_deals"}, {"text": "❓ עזרה", "callback_data": "menu_help"}],
        ]}

    def back_keyboard(self):
        return {"inline_keyboard": [[{"text": "🔙 חזרה לתפריט", "callback_data": "menu_main"}]]}

    def earn_keyboard(self):
        rows = []
        for t in _daily_tasks:
            rows.append([{"text": f"{t['title']} (+{t['reward']})", "callback_data": f"task_{t['id']}"}])
        rows.append([{"text": "🔙 חזרה לתפריט", "callback_data": "menu_main"}])
        return {"inline_keyboard": rows}

    def vip_keyboard(self):
        return {"inline_keyboard": [
            [{"text": f"⭐ Basic — {VIP_PLANS['basic']['price_ils']}₪", "callback_data": "vip_basic"}],
            [{"text": f"💎 Pro — {VIP_PLANS['pro']['price_ils']}₪", "callback_data": "vip_pro"}],
            [{"text": f"👑 Elite — {VIP_PLANS['elite']['price_ils']}₪", "callback_data": "vip_elite"}],
            [{"text": "🔙 חזרה לתפריט", "callback_data": "menu_main"}],
        ]}

    def buy_slh_keyboard(self):
        rows = []
        for tier in SLH_BUY_TIERS:
            rows.append([{"text": f"🪙 {tier['amount']} SLH = {tier['price']}₪", "callback_data": f"buy_slh_{tier['amount']}"}])
        rows.append([{"text": "✏️ סכום מותאם אישית", "callback_data": "buy_slh_custom"}])
        rows.append([{"text": "🔙 חזרה לתפריט", "callback_data": "menu_main"}])
        return {"inline_keyboard": rows}

    def invest_keyboard(self):
        rows = []
        for i, plan in enumerate(INVESTMENT_PLANS):
            rows.append([{"text": f"{plan['name']} | {plan['rate']}% | {plan['min_ton']} TON", "callback_data": f"invest_{i}"}])
        rows.append([{"text": "🔙 חזרה", "callback_data": "menu_main"}])
        return {"inline_keyboard": rows}

    def games_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "🎰 סלוטים", "callback_data": "game_slots"}, {"text": "🎲 קוביות", "callback_data": "game_dice"}],
            [{"text": "🏀 כדורסל", "callback_data": "game_basketball"}, {"text": "🎯 חצים", "callback_data": "game_darts"}],
            [{"text": "💵 המר ZVK → TON", "callback_data": "game_convert"}],
            [{"text": "🔙 חזרה", "callback_data": "menu_main"}],
        ]}

    # ══════════════════════════════════════════════════════════════════
    # INVESTMENT HOUSE HANDLERS (original reply-keyboard buttons)
    # ══════════════════════════════════════════════════════════════════

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
                    self.send(referrer_id, f"🎉 <b>הפניה חדשה!</b>\n\n@{username or first_name} הצטרף דרכך!\n+50 נקודות SLH 🎁")
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
                logger.info(f"[bot-sync] ✅ Synced {chat_id} (@{username}) to website — registered={sync_data.get('is_registered')}")
            else:
                logger.warning(f"[bot-sync] HTTP {sync_resp.status_code}: {sync_resp.text[:200]}")
        except Exception as e:
            logger.warning(f"[bot-sync] failed for {chat_id}: {e}")

        invested = user["ton_locked"]
        profit = user["ton_locked"] * 0.04 if user["ton_locked"] > 0 else 0
        status = "✅ משקיע פעיל" if user["activated"] else "⏳ ממתין להפעלה"

        # Personal login link for the website (comes from auto-sync)
        login_url = user.get("web_login_url") or f"https://slh-nft.com/dashboard.html?uid={chat_id}"

        # Professional ASCII branding — clean, monospace-safe, SLH colors
        text = (
            f"<b>✨ SLH SPARK ✨</b>\n"
            f"<i>Digital Investment House</i>\n"
            f"<code>━━━━━━━━━━━━━━━━━━━━</code>\n"
            f"        💎  S L H\n"
            f"   Investment Ecosystem\n"
            f"      by SPARK IND\n"
            f"<code>━━━━━━━━━━━━━━━━━━━━</code>\n\n"
            f"שלום <b>{first_name}</b>! 👋\n\n"
            f"🌐 <b><a href=\"{login_url}\">היכנס לאתר האישי שלך ←</a></b>\n"
            f"   <i>(לחיצה אחת · ללא סיסמה · כל הנתונים שלך)</i>\n\n"
            f"<code>━━ הסטטוס שלך ━━</code>\n"
            f"💼 {status}\n"
            f"💰 מושקע: <b>{invested:.2f} TON</b>\n"
            f"📈 רווח: <b>+{profit:.4f} TON</b>\n"
            f"💎 SLH: <b>{user['slh_balance']:,.2f}</b>\n"
            f"🎮 ZVK: <b>{user['zvk_balance']}</b>\n\n"
            f"<code>━━ מה תרצה לעשות? ━━</code>\n"
            f"📊 <b>השוק עכשיו</b> — מחירים, מגמות, סיגנלים\n"
            f"💼 <b>השקעות</b> — 4 תוכניות, 4%-5.4% חודשי\n"
            f"💰 <b>ארנק</b> — TON/BNB/SLH + העברות\n"
            f"🛡 <b>סיכון</b> — הגדרות סיכון אישיות\n"
            f"🎮 <b>בונוסים</b> — משחקים + ZVK\n"
            f"👥 <b>הזמן</b> — +5 ZVK + עמלות 10 דורות\n"
            f"🏪 <b>חנות קהילתית</b> — מכור/קנה במערכת\n"
            f"📰 <b>בלוג יומי</b> — מה חדש היום\n"
            f"🎓 <b>אקדמיה</b> — מדריכים וקורסים\n\n"
            f"<code>━━━━━━━━━━━━━━━━━━━━</code>\n"
            f"💫 <b>SLH Investment House</b>\n"
            f"⚡ <i>Powered by SPARK IND</i>\n"
            f"🇮🇱 <i>Built in Israel · 2026</i>"
        )
        # Inline keyboard with direct website button
        inline_kb = {
            "inline_keyboard": [
                [{"text": "🌐 היכנס לאתר האישי", "url": login_url}],
                [
                    {"text": "🏪 חנות", "url": "https://slh-nft.com/community.html"},
                    {"text": "📰 בלוג", "url": "https://slh-nft.com/daily-blog.html"},
                ],
                [
                    {"text": "🎁 הזמן חברים", "url": "https://slh-nft.com/invite.html"},
                    {"text": "📖 מדריכים", "url": "https://slh-nft.com/guides.html"},
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
        self.send(chat_id, "👇 <i>תפריט מהיר:</i>", self.main_reply_keyboard())

    def handle_prices(self, chat_id):
        prices = fetch_prices()
        now = datetime.now()
        ts = now.strftime("%H:%M %d/%m/%Y")

        if not prices:
            self.send(chat_id, "📊 <b>מחירים חיים</b>\n────────────────────\n\n⏳ טוען מחירים...\nנסה שוב בעוד רגע.",
                      self.main_reply_keyboard())
            return

        top = ["BTC", "ETH", "TON", "BNB", "SOL"]
        alts = ["DOGE", "XRP", "ADA", "DOT", "AVAX", "LINK"]

        text = "📊 <b>מחירים חיים</b>\n────────────────────\n\n👑 <b>מטבעות מובילות:</b>\n"
        for coin in top:
            if coin in prices:
                p = prices[coin]
                info = COINS[coin]
                text += f"  {info['emoji']} {coin}: ${p['usd']:,.2f} | {p['ils']:,.1f}₪\n"

        text += "\n💡 <b>Altcoins:</b>\n"
        for coin in alts:
            if coin in prices:
                p = prices[coin]
                info = COINS[coin]
                text += f"  {info['emoji']} {coin}: ${p['usd']:.4f} | {p['ils']:.2f}₪\n"

        ton_price = prices.get("TON", {})
        if ton_price:
            text += f"\n💱 1 TON = {ton_price['ils']}₪ | ${ton_price['usd']}\n"

        text += f"\n⏰ {ts}\n\n💡 SLH Investment House"
        self.send(chat_id, text, self.main_reply_keyboard())

    def wallet_inline_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "📥 הפקדה", "callback_data": "wallet_deposit"}, {"text": "📤 שלח", "callback_data": "wallet_send"}],
            [{"text": "📜 היסטוריה", "callback_data": "wallet_history"}, {"text": "🔄 רענן", "callback_data": "wallet_refresh"}],
            [{"text": "🔙 חזרה לתפריט", "callback_data": "menu_main"}],
        ]}

    def handle_wallet(self, chat_id, message_id=None):
        user = _get_user(chat_id)

        # ── Try real blockchain wallet ──
        if self._wallet_ready and self.wallet:
            try:
                portfolio = self._run_async(self.wallet.get_user_portfolio(chat_id), timeout=12)
                if "error" not in portfolio:
                    bal = portfolio["balances"]
                    usd = portfolio["usd_values"]
                    prices = portfolio.get("prices", {})
                    bsc_addr = portfolio.get("bsc_address", "—")

                    text = (
                        f"💰 <b>ארנק SLH</b>\n"
                        f"════════════════════\n\n"
                        f"💎 <b>SLH:</b> {bal['SLH']}\n"
                        f"🟠 <b>BNB:</b> {bal['BNB']}\n"
                        f"💠 <b>TON:</b> {bal['TON']}\n"
                        f"🎮 <b>ZVK:</b> {bal['ZVK']}\n\n"
                        f"💵 <b>שווי בדולר:</b>\n"
                        f"  SLH: ${usd.get('SLH', 0):,.2f}\n"
                        f"  BNB: ${usd.get('BNB', 0):,.2f}\n"
                        f"  TON: ${usd.get('TON', 0):,.2f}\n"
                        f"  ────────────\n"
                        f"  💰 סה\"כ: <b>${usd.get('total', 0):,.2f}</b>\n\n"
                        f"🔗 <b>כתובת BSC:</b>\n<code>{bsc_addr}</code>\n\n"
                        f"💳 <b>פקודות:</b>\n"
                        f"/deposit_address — כתובת הפקדה\n"
                        f"/send_slh USER_ID AMOUNT — שלח SLH\n"
                        f"/send_ton USER_ID AMOUNT — שלח TON\n"
                        f"/tx_history — היסטוריית עסקאות\n"
                        f"/verify TX_HASH CHAIN — אמת הפקדה"
                    )
                    if message_id:
                        self.edit_message(chat_id, message_id, text, self.wallet_inline_keyboard())
                    else:
                        self.send(chat_id, text, self.wallet_inline_keyboard())
                    return
            except Exception as e:
                logger.warning(f"Wallet fetch failed for {chat_id}: {e}")

        # ── Fallback to in-memory ──
        ton_total = user["ton_available"] + user["ton_locked"]
        text = (
            f"💰 <b>ארנק</b>\n"
            f"────────────────────\n\n"
            f"💎 SLH: {user['slh_balance']:.4f}\n"
            f"🎮 ZVK: {user['zvk_balance']}\n\n"
            f"🏦 <b>חשבון בנק:</b>\n"
            f"  💰 זמין: {user['ton_available']:.4f} TON\n"
            f"  🔒 נעול: {user['ton_locked']:.4f} TON\n"
            f"  💰 סה\"כ: {ton_total:.4f} TON\n\n"
            f"⚠️ <i>ארנק blockchain מתחבר... נסה שוב בעוד רגע</i>\n\n"
            f"💳 <b>פקודות:</b>\n"
            f"/deposit - הפקדה חדשה\n"
            f"/send_slh USER_ID AMOUNT — שלח SLH\n"
            f"/tx_history — היסטוריית עסקאות"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.wallet_inline_keyboard())
        else:
            self.send(chat_id, text, self.wallet_inline_keyboard())

    # ══════════════════════════════════════════════════════════════════
    # BLOCKCHAIN WALLET HANDLERS (wallet_engine integration)
    # ══════════════════════════════════════════════════════════════════

    def handle_deposit_address(self, chat_id):
        """Generate and show deposit addresses for BSC + TON."""
        if not self._wallet_ready:
            self.send(chat_id, "⚠️ מערכת הארנקים מתחברת... נסה שוב בעוד רגע.", self.main_reply_keyboard())
            return
        try:
            addrs = self._run_async(self.wallet.generate_deposit_address(chat_id))
            text = (
                f"📥 <b>כתובות הפקדה</b>\n"
                f"════════════════════\n\n"
                f"🟠 <b>BSC (BNB / SLH Token):</b>\n"
                f"<code>{addrs['bsc_address']}</code>\n\n"
                f"💠 <b>TON:</b>\n"
                f"<code>{addrs['ton_address']}</code>\n"
                f"📝 <b>Memo:</b> <code>{addrs['memo']}</code>\n\n"
                f"⚠️ <b>חשוב:</b>\n"
                f"• BSC — שלח BNB או SLH Token לכתובת למעלה\n"
                f"• TON — שלח TON לכתובת + הוסף את ה-Memo\n"
                f"• אחרי השליחה: /verify TX_HASH bsc (או ton)\n\n"
                f"💡 <i>ההפקדה תיזקף אוטומטית אחרי אימות</i>"
            )
            self.send(chat_id, text, self.wallet_inline_keyboard())
        except Exception as e:
            logger.error(f"Deposit address error: {e}")
            self.send(chat_id, "❌ שגיאה ביצירת כתובת. נסה שוב.", self.main_reply_keyboard())

    def handle_verify_deposit(self, chat_id, args):
        """Verify a deposit tx on-chain: /verify TX_HASH bsc|ton"""
        if not self._wallet_ready:
            self.send(chat_id, "⚠️ מערכת הארנקים מתחברת...", self.main_reply_keyboard())
            return
        parts = args.strip().split()
        if len(parts) < 2:
            self.send(chat_id,
                "📋 <b>אימות הפקדה</b>\n\n"
                "שימוש: /verify TX_HASH CHAIN\n\n"
                "דוגמה BSC:\n<code>/verify 0xabc123... bsc</code>\n\n"
                "דוגמה TON:\n<code>/verify abc123... ton</code>",
                self.main_reply_keyboard())
            return

        tx_hash = parts[0]
        chain = parts[1].lower()
        if chain not in ("bsc", "ton"):
            self.send(chat_id, "❌ Chain חייב להיות bsc או ton", self.main_reply_keyboard())
            return

        self.send(chat_id, f"⏳ מאמת עסקה על {chain.upper()}...", self.main_reply_keyboard())
        try:
            result = self._run_async(self.wallet.process_deposit(chat_id, tx_hash, chain), timeout=20)
            if "error" in result:
                self.send(chat_id, f"❌ {result['error']}", self.wallet_inline_keyboard())
            else:
                self.send(chat_id,
                    f"✅ <b>הפקדה אומתה!</b>\n\n"
                    f"💰 סכום: <b>{result['amount']} {result['token']}</b>\n"
                    f"🔗 Chain: {result['chain'].upper()}\n"
                    f"📝 ID: #{result['deposit_id']}\n\n"
                    f"היתרה עודכנה. /wallet לצפייה",
                    self.wallet_inline_keyboard())
                # Notify admin
                if str(chat_id) != ADMIN_ID:
                    user = _get_user(chat_id)
                    self.send(int(ADMIN_ID),
                        f"💰 <b>הפקדה חדשה!</b>\n"
                        f"👤 @{user['username']} ({chat_id})\n"
                        f"💰 {result['amount']} {result['token']} ({chain.upper()})\n"
                        f"🔗 TX: <code>{tx_hash[:30]}...</code>")
        except Exception as e:
            logger.error(f"Verify deposit error: {e}")
            self.send(chat_id, "❌ שגיאה באימות. נסה שוב.", self.main_reply_keyboard())

    def handle_send_internal(self, chat_id, args, token="SLH"):
        """Internal transfer: /send_slh USER_ID AMOUNT"""
        if not self._wallet_ready:
            self.send(chat_id, "⚠️ מערכת הארנקים מתחברת...", self.main_reply_keyboard())
            return
        parts = args.strip().split()
        if len(parts) < 2:
            self.send(chat_id,
                f"📤 <b>העברת {token}</b>\n\n"
                f"שימוש: /send_{token.lower()} USER_ID AMOUNT\n\n"
                f"דוגמה:\n<code>/send_{token.lower()} 123456789 10</code>\n\n"
                f"💡 ה-USER_ID של הנמען: בקש ממנו לשלוח /myid",
                self.main_reply_keyboard())
            return
        try:
            to_user = int(parts[0])
            amount = parts[1]
            float(amount)  # validate it's a number
        except (ValueError, IndexError):
            self.send(chat_id, "❌ פורמט שגוי. שלח USER_ID ואז סכום.", self.main_reply_keyboard())
            return

        if to_user == chat_id:
            self.send(chat_id, "❌ אי אפשר לשלוח לעצמך", self.main_reply_keyboard())
            return

        try:
            result = self._run_async(self.wallet.internal_transfer(chat_id, to_user, amount, token))
            if "error" in result:
                self.send(chat_id, f"❌ {result['error']}", self.wallet_inline_keyboard())
            else:
                self.send(chat_id,
                    f"✅ <b>נשלח!</b>\n\n"
                    f"💰 {amount} {token} → משתמש {to_user}\n"
                    f"📝 TX ID: #{result['tx_id']}\n\n"
                    f"/wallet לצפייה ביתרה",
                    self.wallet_inline_keyboard())
                # Notify receiver
                sender = _get_user(chat_id)
                self.send(to_user,
                    f"💰 <b>קיבלת {amount} {token}!</b>\n\n"
                    f"👤 מ: @{sender['username'] or sender['first_name']} ({chat_id})\n"
                    f"/wallet לצפייה ביתרה")
        except Exception as e:
            logger.error(f"Transfer error: {e}")
            self.send(chat_id, "❌ שגיאה בהעברה. נסה שוב.", self.main_reply_keyboard())

    def handle_tx_history(self, chat_id):
        """Show transaction history from DB."""
        if not self._wallet_ready:
            self.send(chat_id, "⚠️ מערכת הארנקים מתחברת...", self.main_reply_keyboard())
            return
        try:
            history = self._run_async(self.wallet.get_transaction_history(chat_id, limit=10))
            if not history:
                self.send(chat_id, "📜 <b>היסטוריית עסקאות</b>\n\nאין עסקאות עדיין.", self.wallet_inline_keyboard())
                return
            text = "📜 <b>היסטוריית עסקאות (10 אחרונות)</b>\n════════════════════\n\n"
            for tx in history:
                direction = "📤" if tx["from_user_id"] == chat_id else "📥"
                other = tx["to_user_id"] if tx["from_user_id"] == chat_id else tx["from_user_id"]
                dt = tx["created_at"][:16].replace("T", " ") if tx["created_at"] else "—"
                text += (
                    f"{direction} <b>{tx['amount']} {tx['token']}</b> "
                    f"{'→' if direction == '📤' else '←'} {other or 'system'} "
                    f"| {tx['type']} | {dt}\n"
                )
            self.send(chat_id, text, self.wallet_inline_keyboard())
        except Exception as e:
            logger.error(f"TX history error: {e}")
            self.send(chat_id, "❌ שגיאה בטעינת היסטוריה.", self.main_reply_keyboard())

    def handle_onchain_balance(self, chat_id):
        """Read on-chain balance for the ecosystem master wallets."""
        if not self._wallet_ready:
            self.send(chat_id, "⚠️ מערכת הארנקים מתחברת...", self.main_reply_keyboard())
            return
        try:
            self.send(chat_id, "⏳ קורא יתרות מה-blockchain...", self.main_reply_keyboard())
            slh_bal = self._run_async(self.wallet.get_slh_balance(BSC_CONTRACT), timeout=15)
            ton_bal = self._run_async(self.wallet.get_ton_balance(TON_WALLET), timeout=15)
            prices = self._run_async(self.wallet.get_live_prices())
            text = (
                f"🔗 <b>יתרות On-Chain</b>\n"
                f"════════════════════\n\n"
                f"💎 <b>SLH Token (BSC):</b>\n"
                f"  Contract: <code>{BSC_CONTRACT[:20]}...</code>\n"
                f"  יתרה: {slh_bal}\n\n"
                f"💠 <b>TON Wallet:</b>\n"
                f"  כתובת: <code>{TON_WALLET[:20]}...</code>\n"
                f"  יתרה: {ton_bal} TON\n\n"
                f"📊 <b>מחירים:</b>\n"
                f"  BTC: ${prices.get('btc_usd', 0):,.0f}\n"
                f"  ETH: ${prices.get('eth_usd', 0):,.0f}\n"
                f"  TON: ${prices.get('ton_usd', 0):.2f}\n"
                f"  BNB: ${prices.get('bnb_usd', 0):,.0f}\n"
                f"  SLH: {prices.get('slh_ils', 444)}₪ (${prices.get('slh_usd', 0):.2f})"
            )
            self.send(chat_id, text, self.wallet_inline_keyboard())
        except Exception as e:
            logger.error(f"On-chain balance error: {e}")
            self.send(chat_id, "❌ שגיאה בקריאה מה-blockchain.", self.main_reply_keyboard())

    def handle_investments(self, chat_id, message_id=None):
        text = "💼 <b>תוכניות השקעה</b>\n────────────────────\n\n"
        for plan in INVESTMENT_PLANS:
            text += (
                f"{plan['name']}\n"
                f"  💰 {plan['rate']}% חודשי | {plan['annual']}% שנתי\n"
                f"  מינימום {plan['min_ton']} TON | {plan['days']} יום\n\n"
            )
        text += (
            "💳 <b>איך להפקיד:</b>\n"
            "1. בחר תוכנית\n"
            "2. שלח TON מ-@wallet\n"
            "3. שלח צילום מסך\n"
            "4. הפקדון נפתח!"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.invest_keyboard())
        else:
            self.send(chat_id, text, self.invest_keyboard())

    def handle_risk(self, chat_id):
        user = _get_user(chat_id)
        text = (
            f"🛡 <b>סיכון ובקרה</b>\n"
            f"────────────────────\n\n"
            f"💡 <b>הגדרות הסיכון שלך:</b>\n\n"
            f"🚨 הפסד יומי: {user['risk_daily_loss']}%\n"
            f"📊 פוזיציה מקסימלית: {user['risk_max_position']}%\n"
            f"🛑 Stop Loss: {'✅ פעיל' if user['risk_stop_loss'] else '❌ כבוי'}\n\n"
            f"📝 <b>עקרונות:</b>\n"
            f"• לא להשקיע יותר ממה שמוכנים להפסיד\n"
            f"• להפריד בין מספר תוכניות\n"
            f"• לא לשים הכל על קלף אחד\n"
            f"• להשאיר נזילות למקרה חירום\n\n"
            f"🛡 <b>המערכת שומרת עליך!</b>"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_invite(self, chat_id):
        user = _get_user(chat_id)
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            f"👥 <b>הזמן חברים</b>\n\n"
            f"🔗 <code>{ref_link}</code>\n\n"
            f"הזמנות: {user['referral_count']} | +5 ZVK לכל חבר"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_activate(self, chat_id):
        user = _get_user(chat_id)
        user["activated"] = True
        self.send(chat_id, "✅ מופעל!", self.main_reply_keyboard())

    def handle_share(self, chat_id):
        user = _get_user(chat_id)
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            f"💎 SLH - בית השקעות דיגיטלי\n\n"
            f"✅ תשואה 4% חודשי / 65% שנתי\n"
            f"✅ ארנק מלא (TON/BNB/SLH)\n"
            f"✅ העברות מיידיות + blockchain\n"
            f"✅ ניתוח שוק + סיגנלים\n"
            f"🎁 +100 ZVK מתנה!\n\n"
            f"💰 22.221₪ בלבד!\n"
            f"👉 {ref_link}\n\n"
            f"💡 SPARK IND | SLH Ecosystem"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_guides(self, chat_id):
        text = (
            "📚 <b>מדריכים</b>\n"
            "────────────────────\n\n"
            "📖 <b>מדריכי SLH:</b>\n"
            "• <a href='https://slh-nft.com/guides.html'>מדריך מלא באתר</a>\n\n"
            "📋 <b>נושאים:</b>\n"
            "1️⃣ איך להתחיל עם SLH\n"
            "2️⃣ איך לפתוח ארנק TON\n"
            "3️⃣ איך להפקיד ולהשקיע\n"
            "4️⃣ איך להשתמש בסוואפ\n"
            "5️⃣ מדריך אבטחה\n"
            "6️⃣ שאלות נפוצות\n\n"
            "💡 לכל שאלה: /support"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_bonuses(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        text = (
            f"🎮 <b>בונוסים</b> | ZVK: {user['zvk_balance']}\n"
            f"────────────────────\n\n"
            f"כל משחק = 1 ZVK\n"
            f"🎰 סלוטים: פרס גדול עד 25 ZVK!\n"
            f"🎲 קוביות: 6=5 ZVK, 4-5=2 ZVK\n"
            f"🏀 כדורסל: 4+=3 ZVK\n"
            f"🎯 חצים: 6=5 ZVK, 4-5=2 ZVK\n\n"
            f"💵 10 ZVK = 1 TON | 50 = 4 | 100 = 7"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.games_keyboard())
        else:
            self.send(chat_id, text, self.games_keyboard())

    def handle_game(self, chat_id, game_type, callback_id, message_id):
        user = _get_user(chat_id)
        if user["zvk_balance"] < 1:
            self.answer_callback(callback_id, "❌ אין מספיק ZVK!", True)
            return

        user["zvk_balance"] -= 1
        user["games_played"] += 1

        if game_type == "slots":
            symbols = ["🍒", "🍋", "🍊", "💎", "7️⃣", "🔔"]
            s1, s2, s3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)
            if s1 == s2 == s3:
                win = 25 if s1 == "💎" else 15
                user["zvk_balance"] += win
                user["games_won"] += 1
                result = f"🎰 {s1}{s2}{s3}\n\n🎉 ג'קפוט! +{win} ZVK!"
            elif s1 == s2 or s2 == s3:
                win = 3
                user["zvk_balance"] += win
                user["games_won"] += 1
                result = f"🎰 {s1}{s2}{s3}\n\n🎉 ניצחת! +{win} ZVK!"
            else:
                result = f"🎰 {s1}{s2}{s3}\n\n❌ לא הפעם"
        elif game_type == "dice":
            roll = random.randint(1, 6)
            if roll == 6:
                user["zvk_balance"] += 5
                user["games_won"] += 1
                result = f"🎲 {roll}\n\n🎉 מושלם! +5 ZVK!"
            elif roll >= 4:
                user["zvk_balance"] += 2
                user["games_won"] += 1
                result = f"🎲 {roll}\n\n🎉 ניצחת! +2 ZVK!"
            else:
                result = f"🎲 {roll}\n\n❌ לא הפעם"
        elif game_type == "basketball":
            score = random.randint(1, 6)
            if score >= 4:
                user["zvk_balance"] += 3
                user["games_won"] += 1
                result = f"🏀 {score} נקודות!\n\n🎉 ניצחת! +3 ZVK!"
            else:
                result = f"🏀 {score} נקודות\n\n❌ לא הפעם"
        elif game_type == "darts":
            score = random.randint(1, 6)
            if score == 6:
                user["zvk_balance"] += 5
                user["games_won"] += 1
                result = f"🎯 מרכז! {score}\n\n🎉 ניצחת! +5 ZVK!"
            elif score >= 4:
                user["zvk_balance"] += 2
                user["games_won"] += 1
                result = f"🎯 {score}\n\n🎉 ניצחת! +2 ZVK!"
            else:
                result = f"🎯 {score}\n\n❌ לא הפעם"
        else:
            result = "❓"

        result += f"\n🎮 ZVK: {user['zvk_balance']}"
        self.edit_message(chat_id, message_id, result, self.games_keyboard())
        self.answer_callback(callback_id)

    def handle_game_convert(self, chat_id, callback_id, message_id):
        text = (
            "💵 <b>המרת ZVK → TON</b>\n\n"
            "10 ZVK = 1 TON\n"
            "50 ZVK = 4 TON\n"
            "100 ZVK = 7 TON\n\n"
            f"שלח ל:\n<code>{TON_WALLET}</code>"
        )
        self.edit_message(chat_id, message_id, text, self.games_keyboard())
        self.answer_callback(callback_id)

    def handle_dashboard(self, chat_id):
        user = _get_user(chat_id)
        ton_total = user["ton_available"] + user["ton_locked"]
        active_deposits = len([d for d in user.get("deposits", []) if d.get("status") == "active"])
        pending_deposits = len([d for d in user.get("deposits", []) if d.get("status") == "pending"])
        invested = user["ton_locked"]
        profit = user["ton_locked"] * 0.04

        win_rate = round(user["games_won"] / user["games_played"] * 100) if user["games_played"] > 0 else 0

        text = (
            f"📊 <b>דשבורד</b>\n"
            f"────────────────────\n\n"
            f"🏦 <b>חשבון בנק:</b>\n"
            f"  💰 זמין: {user['ton_available']:.4f} TON\n"
            f"  🔒 נעול: {user['ton_locked']:.4f} TON\n"
            f"  💰 סה\"כ: {ton_total:.4f} TON\n\n"
            f"💼 השקעות פעילות: {active_deposits}\n"
            f"⏳ ממתינות לאישור: {pending_deposits}\n"
            f"💰 מושקע: {invested:.2f} TON\n"
            f"📈 רווח: +{profit:.4f} TON\n\n"
            f"🎮 ZVK: {user['zvk_balance']} | משחקים: {user['games_played']} ({win_rate}%)\n"
            f"👥 הזמנות: {user['referral_count']}\n\n"
            f"SLH Investment House"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_swap_text(self, chat_id):
        text = (
            "🔄 <b>SLH Swap — המרת מטבעות</b>\n\n"
            "המירו בין 4,500+ מטבעות קריפטו בקלות!\n\n"
            "💡 <b>יתרונות:</b>\n"
            "• ללא הרשמה\n"
            "• עמלות נמוכות\n"
            "• המרה ישירה מארנק לארנק\n"
            "• תמיכה ב-TON, BTC, ETH, BNB ועוד\n\n"
            "🔥 <b>מבצע:</b> Cashback 0.5% על כל עסקה!\n\n"
            "👇 לחץ להתחלה:"
        )
        kb = {"inline_keyboard": [
            [{"text": "🔄 המר עכשיו", "url": f"https://letsexchange.io/?ref={LETSEXCHANGE_REF}"}],
            [{"text": "💱 TON → USDT", "url": f"https://letsexchange.io/?from=TON&to=USDT&ref={LETSEXCHANGE_REF}"}],
            [{"text": "💱 BTC → TON", "url": f"https://letsexchange.io/?from=BTC&to=TON&ref={LETSEXCHANGE_REF}"}],
        ]}
        self.send(chat_id, text, kb)

    def handle_ai_analysis(self, chat_id):
        prices = fetch_prices()
        btc = prices.get("BTC", {}).get("usd", 67000)
        text = (
            f"🧠 <b>ניתוח AI</b>\n"
            f"────────────────────\n\n"
            f"📈 <b>תרחיש שורי:</b> אם BTC שובר ${int(btc/1000)*1000+3000:,}, צפוי מהלך ל-${int(btc/1000)*1000+8000:,}\n\n"
            f"🔴 <b>תרחיש דובי:</b> אם BTC שובר ${int(btc/1000)*1000-2000:,}, אפשרי נפילה ל-${int(btc/1000)*1000-7000:,}\n\n"
            f"🟡 <b>תרחיש נייטרלי:</b> צפוי דחיסה צדדית\n\n"
            f"⚠️ זה לא ייעוץ השקעה."
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_alerts(self, chat_id):
        text = (
            "🔔 <b>התראות מחיר</b>\n"
            "────────────────────\n\n"
            "בקרוב! תוכל להגדיר התראות על:\n"
            "• מחיר שעובר רמה\n"
            "• נפח חריג\n"
            "• חדשות שוק\n"
            "• שינוי בתיק"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_deals_text(self, chat_id):
        text = (
            "🔥 <b>מבצעים פעילים</b>\n\n"
            "━━━━━━━━━━━━━━━\n\n"
            "🔥 <b>מבצע השקה — 30% הנחה!</b>\n"
            "  💰 כל הבוטים ב-30% הנחה\n"
            "  🏷️ קוד: <code>LAUNCH30</code>\n"
            "  ⏰ זמן מוגבל\n\n"
            "💎 <b>חבילה מלאה — 6 בוטים</b>\n"
            "  💰 מחיר: <b>199₪</b>\n"
            "  📦 כל 6 בוטי הפרימיום\n\n"
            "🤝 <b>הזמן 3 = פרימיום חינם!</b>\n"
            "  👥 הזמן 3 חברים\n"
            "  🎁 קבל Community Premium בחינם\n\n"
            "🛡️ <b>חבילת אבטחה</b>\n"
            "  💰 Guardian + Wallet = <b>99₪</b>\n\n"
            "🎓 <b>מבצע סטודנטים</b>\n"
            "  💰 50% הנחה על Academia\n"
            "  🏷️ קוד: <code>STUDENT50</code>\n"
            "━━━━━━━━━━━━━━━"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_buy_slh_text(self, chat_id):
        text = (
            f"🪙 <b>רכישת SLH Coin</b>\n\n"
            f"💰 <b>מחיר:</b> 1 SLH = {SLH_PRICE_ILS}₪\n"
            f"🔹 מינימום: 0.00004 SLH (0.018₪)\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📊 <b>מדרגות מחיר:</b>\n\n"
        )
        for tier in SLH_BUY_TIERS:
            text += f"  🪙 {tier['amount']} SLH = {tier['price']}₪\n"
        text += (
            f"\n━━━━━━━━━━━━━━━\n"
            f"💳 <b>ארנק TON:</b>\n<code>{TON_WALLET}</code>\n\n"
            f"🔗 <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            f"📸 שלח צילום מסך או Transaction Hash\n"
            f"או צור קשר עם @Osif83"
        )
        self.send(chat_id, text, self.buy_slh_keyboard())

    # ── Banking commands ─────────────────────────────────────────────
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
            f"✅ <b>הפקדה #{deposit_id} נוצרה!</b>\n"
            f"────────────────────\n\n"
            f"{plan['name']} | {amount} TON\n"
            f"תשואה חודשית: ~{monthly_return} TON\n"
            f"נעול עד: {unlock_date}\n\n"
            f"💰 שלח {amount} TON ל:\n"
            f"<code>{TON_WALLET}</code>\n\n"
            f"ושלח צילום מסך לאישור."
        )
        self.send(chat_id, text, self.main_reply_keyboard())

        # Notify admin
        if str(chat_id) != ADMIN_ID:
            admin_text = (
                f"💳 <b>הפקדה חדשה #{deposit_id}</b>\n"
                f"👤 @{user['username']} ({chat_id})\n"
                f"💼 {plan['name']} | {amount} TON\n"
                f"💰 {plan['rate']}% חודשי | {plan['days']} ימים"
            )
            kb = {"inline_keyboard": [
                [{"text": "✅ אשר", "callback_data": f"admin_approve_{chat_id}_{deposit_id}"},
                 {"text": "❌ דחה", "callback_data": f"admin_reject_{chat_id}_{deposit_id}"}],
            ]}
            self.send(int(ADMIN_ID), admin_text, kb)

    def handle_mydeposits(self, chat_id):
        user = _get_user(chat_id)
        if not user["deposits"]:
            self.send(chat_id, "📋 אין הפקדות פעילות.\n\nלהפקדה חדשה: /deposit", self.main_reply_keyboard())
            return

        text = "📋 <b>ההפקדות שלי</b>\n────────────────────\n\n"
        for d in user["deposits"]:
            status = "✅" if d["status"] == "active" else "⏳" if d["status"] == "pending" else "❌"
            text += f"{status} #{d['id']} | {d['plan']} | {d['amount']} TON | {d['rate']}%\n"
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_withdraw(self, chat_id, args=""):
        if not args:
            self.send(chat_id,
                "💸 <b>משיכה</b>\n\nשימוש: /withdraw <מספר הפקדה> <כתובת TON>\n\nדוגמה: /withdraw 1 UQDhfy...\n\nלרשימה: /mydeposits",
                self.main_reply_keyboard())
            return
        self.send(chat_id, "📩 בקשת המשיכה נשלחה לאישור. נעדכן בהקדם.", self.main_reply_keyboard())
        if str(chat_id) != ADMIN_ID:
            user = _get_user(chat_id)
            self.send(int(ADMIN_ID), f"💸 <b>בקשת משיכה!</b>\nUser: @{user['username']} ({chat_id})\nArgs: {args}")

    def handle_statement(self, chat_id):
        user = _get_user(chat_id)
        ton_total = user["ton_available"] + user["ton_locked"]
        text = (
            f"📋 <b>דף חשבון (30 יום)</b>\n"
            f"────────────────────\n\n"
            f"💰 זמין: {user['ton_available']:.4f} TON\n"
            f"🔒 נעול: {user['ton_locked']:.4f} TON\n"
            f"💰 סה\"כ: {ton_total:.4f} TON\n\n"
            f"📈 הפקדות: {len(user['deposits'])}\n"
            f"💸 משיכות: {user['withdrawals']}\n"
            f"📝 תנועות: {user['transactions']}\n\n"
            f"SLH Investment House"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_kyc(self, chat_id, args=""):
        if args:
            self.send(chat_id, f"✅ שלב 1 הושלם: {args}\n\nשלח צילום ת.ז. (כתמונה)", self.main_reply_keyboard())
        else:
            text = (
                "📋 <b>KYC - זיהוי</b>\n────────────────────\n\n"
                "שלב 1: /kyc <שם מלא>\n"
                "שלב 2: שלח צילום ת.ז. (כתמונה)\n"
                "שלב 3: המתן לאישור"
            )
            self.send(chat_id, text, self.main_reply_keyboard())

    def handle_faq(self, chat_id):
        text = (
            "❓ <b>FAQ</b>\n\n"
            "Q: כמה עולה?\nA: 22.221₪ חד פעמי\n\n"
            "Q: איך משלמים?\nA: @wallet → Buy TON → Send\n\n"
            "Q: בטוח?\nA: מפתחות פרטיים לא נשמרים\n\n"
            "Q: תמיכה?\nA: /support"
        )
        self.send(chat_id, text, self.main_reply_keyboard())

    def handle_help(self, chat_id, message_id=None):
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            "❓ <b>SLH Investment House</b>\n"
            "────────────────────\n\n"
            "📊 <b>השוק</b> - 12 מטבעות, סוואפ, התראות\n"
            "💼 <b>השקעות</b> - 4 פקדונות, 4%-65%\n"
            "💰 <b>ארנק</b> - TON/BNB/SLH + העברות\n"
            "🔁 <b>מסחר</b> - סוואפ, Limit, התראות\n\n"
            "💳 <b>בנק:</b>\n"
            "/deposit /mydeposits /withdraw /statement\n\n"
            "💱 <b>מסחר:</b>\n"
            "/prices /swap /limit /orders /alert /portfolio\n\n"
            "💰 <b>ארנק:</b>\n"
            "/pay /send /mybalance /myid /gas\n\n"
            "🪙 <b>SLH Coin:</b>\n"
            "/buyslh - רכישת מטבע SLH\n\n"
            "📚 <b>עוד:</b>\n"
            "/share /faq /support /kyc /help\n\n"
            f"👥 <b>שתף והרוויח 15% בנקודות SLH!</b>\n"
            f"🔗 <code>{ref_link}</code>\n\n"
            "SLH Investment House | SPARK IND"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.back_keyboard())
        else:
            self.send(chat_id, text, self.main_reply_keyboard())

    def _format_invest_plans(self):
        text = "💼 <b>תוכניות השקעה</b>\n────────────────────\n\n"
        for i, plan in enumerate(INVESTMENT_PLANS, 1):
            text += (
                f"{plan['name']}\n"
                f"  💰 {plan['rate']}% חודשי | {plan['annual']}% שנתי\n"
                f"  מינימום {plan['min_ton']} TON | {plan['days']} יום\n\n"
            )
        return text

    # ══════════════════════════════════════════════════════════════════
    # HUB HANDLERS (inline keyboard callbacks)
    # ══════════════════════════════════════════════════════════════════

    def handle_earn(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        done = len(user["tasks_done"])
        total = len(_daily_tasks)
        total_reward = sum(t["reward"] for t in _daily_tasks)
        done_reward = sum(t["reward"] for t in _daily_tasks if t["id"] in user["tasks_done"])
        text = (
            f"💰 <b>הרוויח נקודות SLH</b>\n\n"
            f"📊 התקדמות: {done}/{total} משימות\n"
            f"💎 שנצבר היום: {done_reward}/{total_reward} נקודות\n"
            f"💰 יתרה: {user['hub_points']} נקודות\n\n"
            f"👇 <b>משימות זמינות:</b>"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.earn_keyboard())
        else:
            self.send(chat_id, text, self.earn_keyboard())

    def handle_task(self, chat_id, task_id, callback_id, message_id):
        user = _get_user(chat_id)
        task = next((t for t in _daily_tasks if t["id"] == task_id), None)
        if not task:
            self.answer_callback(callback_id, "❌ משימה לא נמצאה")
            return
        if task_id in user["tasks_done"]:
            self.answer_callback(callback_id, "✅ כבר ביצעת משימה זו היום!", True)
            return
        user["tasks_done"].append(task_id)
        user["hub_points"] += task["reward"]
        user["total_earned"] += task["reward"]
        self.answer_callback(callback_id, f"✅ +{task['reward']} נקודות!", True)
        self.handle_earn(chat_id, message_id)

    def handle_swap_inline(self, chat_id, message_id=None):
        text = (
            "🔄 <b>SLH Swap — המרת מטבעות</b>\n\n"
            "המירו בין 4,500+ מטבעות קריפטו בקלות!\n\n"
            "💡 <b>יתרונות:</b>\n"
            "• ללא הרשמה\n• עמלות נמוכות\n"
            "• המרה ישירה מארנק לארנק\n"
            "• תמיכה ב-TON, BTC, ETH, BNB ועוד\n\n"
            "🔥 <b>מבצע:</b> Cashback 0.5% על כל עסקה!"
        )
        kb = {"inline_keyboard": [
            [{"text": "🔄 המר עכשיו", "url": f"https://letsexchange.io/?ref={LETSEXCHANGE_REF}"}],
            [{"text": "💱 TON → USDT", "url": f"https://letsexchange.io/?from=TON&to=USDT&ref={LETSEXCHANGE_REF}"}],
            [{"text": "💱 BTC → TON", "url": f"https://letsexchange.io/?from=BTC&to=TON&ref={LETSEXCHANGE_REF}"}],
            [{"text": "🔙 חזרה לתפריט", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_vip(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        current = user["vip"]
        status = f"✅ {VIP_PLANS[current]['name']}" if current else "🆓 חינם"
        text = f"👑 <b>VIP Membership</b>\n\nסטטוס: <b>{status}</b>\n\n━━━━━━━━━━━━━━━\n"
        for key, plan in VIP_PLANS.items():
            marker = "✅" if current == key else "⭐"
            text += f"\n{marker} <b>{plan['name']}</b> — {plan['price_ils']}₪\n"
            for f in plan["features"]:
                text += f"  • {f}\n"
        text += f"\n━━━━━━━━━━━━━━━\n💡 <b>תשלום:</b> העבר לארנק + צילום מסך\n📦 <b>חבילה מלאה:</b> כל ה-VIP + 6 בוטים = 199₪ בלבד!"
        if message_id:
            self.edit_message(chat_id, message_id, text, self.vip_keyboard())
        else:
            self.send(chat_id, text, self.vip_keyboard())

    def handle_vip_select(self, chat_id, plan_key, callback_id, message_id):
        plan = VIP_PLANS.get(plan_key)
        if not plan:
            self.answer_callback(callback_id, "❌")
            return
        text = (
            f"👑 <b>{plan['name']}</b>\n\n"
            f"💰 <b>מחיר:</b> {plan['price_ils']}₪\n\n"
            f"<b>פיצ'רים:</b>\n" +
            "\n".join(f"  ✅ {f}" for f in plan["features"]) +
            f"\n\n━━━━━━━━━━━━━━━\n"
            f"💳 <b>שלח {plan['price_ils']}₪ לארנק TON:</b>\n\n"
            f"<code>{TON_WALLET}</code>\n\nאו צור קשר עם @Osif83\n\n"
            f"📸 שלח צילום מסך של העסקה כאן\n✅ תקבל גישה תוך דקות"
        )
        kb = {"inline_keyboard": [
            [{"text": "💳 העתק כתובת ארנק", "callback_data": f"copy_wallet_{plan_key}"}],
            [{"text": "🔙 חזרה ל-VIP", "callback_data": "menu_vip"}],
        ]}
        self.edit_message(chat_id, message_id, text, kb)
        self.answer_callback(callback_id)

    def handle_airdrop(self, chat_id, message_id=None):
        text = (
            "🎁 <b>SLH Airdrop</b>\n\n"
            f"💰 <b>מבצע השקה:</b>\n1,000 טוקני SLH = <b>444,000₪</b>\n\n"
            f"📊 <b>סטטוס:</b>\n👥 משתמשים: 38\n💸 עסקאות: 22\n🎯 מקומות פנויים: 978/1,000\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💳 <b>לרכישה שלח לארנק TON:</b>\n<code>{TON_WALLET}</code>\n\n"
            f"🔗 <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            "📸 שלח צילום מסך / Transaction Hash\n✅ קבלה תוך 24 שעות"
        )
        kb = {"inline_keyboard": [
            [{"text": "💳 שלח תשלום", "callback_data": "airdrop_pay"}],
            [{"text": "📊 סטטוס שלי", "callback_data": "airdrop_status"}],
            [{"text": "🔙 חזרה לתפריט", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_referral(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            f"👥 <b>ההפניות שלך</b>\n\n"
            f"🔗 <b>הקישור האישי שלך:</b>\n<code>{ref_link}</code>\n\n"
            f"📊 <b>סטטיסטיקה:</b>\n"
            f"👥 הפניות: <b>{user['referral_count']}</b>\n"
            f"💰 נצבר מהפניות: <b>{user['referral_count'] * 50}</b> נקודות SLH\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 <b>איך להרוויח?</b>\n"
            f"1️⃣ שתף את הקישור שלך\n"
            f"2️⃣ חברים נרשמים דרכך\n"
            f"3️⃣ מקבל <b>50 נקודות SLH</b> + <b>15% עמלה בנקודות SLH</b> מכל רכישה\n\n"
            f"🎯 הזמן 3 חברים = <b>Community Premium בחינם!</b>\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🔗 <b>קישורים לכל הבוטים:</b>\n"
            f"• 🎁 Airdrop: <code>https://t.me/SLH_AIR_bot?start=ref_{chat_id}</code>\n"
            f"• 🛡️ Guardian: <code>https://t.me/Grdian_bot?start=ref_{chat_id}</code>\n"
            f"• 🛒 BotShop: <code>https://t.me/BotShop_bot?start=ref_{chat_id}</code>\n"
            f"• 💼 Wallet: <code>https://t.me/SLH_Wallet_bot?start=ref_{chat_id}</code>\n"
            f"• 🎓 Academia: <code>https://t.me/SLH_Academia_bot?start=ref_{chat_id}</code>\n"
            f"• 👥 Community: <code>https://t.me/SLH_community_bot?start=ref_{chat_id}</code>"
        )
        kb = {"inline_keyboard": [
            [{"text": "📋 העתק קישור הפניה", "callback_data": "copy_ref"}],
            [{"text": "📤 שתף עם חבר", "url": f"https://t.me/share/url?url={ref_link}&text=🚀 הצטרפו ל-SLH - בית השקעות דיגיטלי!"}],
            [{"text": "🔙 חזרה לתפריט", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_portfolio(self, chat_id, message_id=None):
        user = _get_user(chat_id)
        vip_str = VIP_PLANS[user["vip"]]["name"] if user["vip"] else "🆓 Free"
        text = (
            f"📊 <b>התיק שלי</b>\n\n"
            f"💎 SLH: {user['slh_balance']:.2f}\n"
            f"🎮 ZVK: {user['zvk_balance']}\n"
            f"💰 Hub נקודות: {user['hub_points']}\n"
            f"👑 סטטוס: {vip_str}\n"
            f"👥 הפניות: {user['referral_count']}\n"
            f"✅ משימות שבוצעו: {len(user['tasks_done'])}\n"
            f"📅 הצטרף: {user['joined'][:10]}\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 <b>המרת נקודות:</b>\n"
            f"1,000 נקודות = 1 SLH Token\n"
            f"5,000 נקודות = 1 חודש VIP Basic"
        )
        kb = {"inline_keyboard": [
            [{"text": "💰 הרוויח עוד", "callback_data": "menu_earn"}, {"text": "👑 שדרג VIP", "callback_data": "menu_vip"}],
            [{"text": "🔙 חזרה לתפריט", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_deals_inline(self, chat_id, message_id=None):
        text = (
            "🔥 <b>מבצעים פעילים</b>\n\n━━━━━━━━━━━━━━━\n\n"
            "🔥 <b>מבצע השקה — 30% הנחה!</b>\n  💰 כל הבוטים ב-30% הנחה\n  🏷️ קוד: <code>LAUNCH30</code>\n  ⏰ זמן מוגבל\n\n"
            "💎 <b>חבילה מלאה — 6 בוטים</b>\n  💰 מחיר: <b>199₪</b>\n\n"
            "🤝 <b>הזמן 3 = פרימיום חינם!</b>\n\n"
            "🛡️ <b>חבילת אבטחה</b>\n  💰 Guardian + Wallet = <b>99₪</b>\n\n"
            "🎓 <b>מבצע סטודנטים</b>\n  💰 50% הנחה — קוד: <code>STUDENT50</code>\n━━━━━━━━━━━━━━━"
        )
        kb = {"inline_keyboard": [
            [{"text": "💎 רכוש חבילה מלאה", "callback_data": "vip_elite"}],
            [{"text": "🛡️ חבילת אבטחה", "callback_data": "vip_basic"}],
            [{"text": "👥 הזמן חברים", "callback_data": "menu_referral"}],
            [{"text": "🔙 חזרה לתפריט", "callback_data": "menu_main"}],
        ]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    def handle_buy_slh_inline(self, chat_id, message_id=None):
        text = (
            f"🪙 <b>רכישת SLH Coin</b>\n\n"
            f"💰 <b>מחיר:</b> 1 SLH = {SLH_PRICE_ILS}₪\n"
            f"🔹 מינימום: 0.00004 SLH (0.018₪)\n\n━━━━━━━━━━━━━━━\n📊 <b>מדרגות מחיר:</b>\n\n"
        )
        for tier in SLH_BUY_TIERS:
            text += f"  🪙 {tier['amount']} SLH = {tier['price']}₪\n"
        text += (
            f"\n━━━━━━━━━━━━━━━\n"
            f"💳 <b>ארנק TON:</b>\n<code>{TON_WALLET}</code>\n\n"
            f"🔗 <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            "📸 שלח צילום מסך או Transaction Hash\nאו צור קשר עם @Osif83"
        )
        if message_id:
            self.edit_message(chat_id, message_id, text, self.buy_slh_keyboard())
        else:
            self.send(chat_id, text, self.buy_slh_keyboard())

    def handle_buy_slh_select(self, chat_id, amount_str, callback_id, message_id):
        if amount_str == "custom":
            text = (
                f"✏️ <b>סכום מותאם אישית</b>\n\n"
                f"💰 מחיר: 1 SLH = {SLH_PRICE_ILS}₪\n"
                f"🔹 מינימום: 0.00004 SLH (0.018₪)\n\n"
                "שלח את הסכום שתרצה לרכוש (בSLH).\nלדוגמה: <code>0.005</code>\n\n"
                f"💳 <b>ארנק TON:</b>\n<code>{TON_WALLET}</code>\n\n"
                f"🔗 <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\nאו צור קשר עם @Osif83"
            )
            self.edit_message(chat_id, message_id, text, self.back_keyboard())
            self.answer_callback(callback_id)
            return
        try:
            amount = float(amount_str)
        except ValueError:
            self.answer_callback(callback_id, "❌ שגיאה")
            return
        price = round(amount * SLH_PRICE_ILS, 3)
        text = (
            f"🪙 <b>רכישת {amount} SLH</b>\n\n💰 <b>מחיר:</b> {price}₪\n\n━━━━━━━━━━━━━━━\n"
            f"💳 <b>שלח {price}₪ לארנק TON:</b>\n\n<code>{TON_WALLET}</code>\n\n"
            f"🔗 <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
            f"📸 שלח צילום מסך או Transaction Hash\nאו צור קשר עם @Osif83\n\n✅ תקבל {amount} SLH תוך 24 שעות"
        )
        kb = {"inline_keyboard": [
            [{"text": "💳 העתק כתובת ארנק", "callback_data": "copy_wallet_slh"}],
            [{"text": "🔙 חזרה לרכישה", "callback_data": "menu_buy_slh"}],
        ]}
        self.edit_message(chat_id, message_id, text, kb)
        self.answer_callback(callback_id)

    def handle_help_inline(self, chat_id, message_id=None):
        ref_link = f"https://t.me/SLH_AIR_bot?start=ref_{chat_id}"
        text = (
            "❓ <b>SLH HUB — עזרה</b>\n\n"
            "<b>פקודות:</b>\n"
            "/start — תפריט ראשי\n/earn — משימות והרווחה\n/swap — המרת מטבעות\n/vip — מנוי פרימיום\n"
            "/airdrop — רכישת טוקנים\n/buyslh — 🪙 רכישת SLH Coin\n/referral — קישור הפניה\n"
            "/deals — מבצעים\n/portfolio — התיק שלי\n/help — עזרה\n\n"
            "<b>תמיכה:</b> @Osif83\n<b>אתר:</b> slh-nft.com\n\n"
            f"━━━━━━━━━━━━━━━\n👥 <b>שתף והרוויח 15% בנקודות SLH!</b>\n🔗 <code>{ref_link}</code>"
        )
        kb = {"inline_keyboard": [[{"text": "🔙 חזרה לתפריט", "callback_data": "menu_main"}]]}
        if message_id:
            self.edit_message(chat_id, message_id, text, kb)
        else:
            self.send(chat_id, text, kb)

    # ── Admin ────────────────────────────────────────────────────────
    def handle_admin(self, chat_id):
        if str(chat_id) != ADMIN_ID:
            return
        total_users = len(_user_data)
        total_vip = sum(1 for u in _user_data.values() if u.get("vip"))
        total_points = sum(u.get("hub_points", 0) for u in _user_data.values())
        total_refs = sum(u["referral_count"] for u in _user_data.values())
        text = (
            f"🛠 <b>ADMIN PANEL</b>\n\n"
            f"👥 משתמשים: <b>{total_users}</b>\n👑 VIP: <b>{total_vip}</b>\n"
            f"💰 נקודות שחולקו: <b>{total_points}</b>\n👥 הפניות: <b>{total_refs}</b>\n\n"
            f"<b>פקודות:</b>\n/stats — סטטיסטיקות\n/broadcast TEXT — שלח הודעה לכולם\n"
            f"/approve USER_ID PLAN — אשר VIP\n/admin — פאנל זה"
        )
        self.send(chat_id, text)

    def handle_broadcast(self, chat_id, text):
        if str(chat_id) != ADMIN_ID:
            return
        sent = 0
        for uid in _user_data:
            if self.send(uid, f"📢 <b>הודעה מהמערכת:</b>\n\n{text}"):
                sent += 1
        self.send(chat_id, f"✅ נשלח ל-{sent} משתמשים")

    def handle_approve(self, chat_id, args):
        if str(chat_id) != ADMIN_ID:
            return
        parts = args.split()
        if len(parts) < 2:
            self.send(chat_id, "שימוש: /approve USER_ID PLAN\nלדוגמה: /approve 123456 pro")
            return
        try:
            uid = int(parts[0])
            plan = parts[1]
            if plan in VIP_PLANS:
                user = _get_user(uid)
                user["vip"] = plan
                self.send(chat_id, f"✅ אושר VIP {VIP_PLANS[plan]['name']} למשתמש {uid}")
                self.send(uid, f"🎉 <b>VIP הופעל!</b>\n\nשדרגת ל-{VIP_PLANS[plan]['name']}! 👑")
            else:
                self.send(chat_id, f"❌ תוכנית לא קיימת. אפשרויות: {', '.join(VIP_PLANS.keys())}")
        except:
            self.send(chat_id, "❌ שגיאה. שימוש: /approve USER_ID PLAN")

    # ── Callback handler ─────────────────────────────────────────────
    def handle_callback(self, callback):
        data = callback.get("data", "")
        chat_id = callback["message"]["chat"]["id"]
        message_id = callback["message"]["message_id"]
        callback_id = callback["id"]
        first_name = callback["from"].get("first_name", "")

        if data == "menu_main":
            user = _get_user(chat_id)
            vip_badge = "👑 VIP" if user["vip"] else "🆓 Free"
            self.edit_message(chat_id, message_id,
                f"🚀 <b>SLH HUB SYSTEM</b>\n\n"
                f"👤 <b>{first_name}</b> | {vip_badge}\n"
                f"💰 יתרה: <b>{user['hub_points']}</b> נקודות\n"
                f"💎 SLH: <b>{user['slh_balance']:.2f}</b>\n"
                f"👥 הפניות: <b>{user['referral_count']}</b>\n\n👇 בחר פעולה:",
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
            self.answer_callback(callback_id, f"💳 {TON_WALLET}", True)
        elif data.startswith("task_"):
            self.handle_task(chat_id, data[5:], callback_id, message_id)
        elif data.startswith("vip_"):
            self.handle_vip_select(chat_id, data[4:], callback_id, message_id)
        elif data == "airdrop_pay":
            self.send(chat_id,
                f"💳 <b>שלח תשלום לארנק TON:</b>\n\n<code>{TON_WALLET}</code>\n\n"
                f"🔗 <b>BSC Contract:</b>\n<code>{BSC_CONTRACT}</code>\n\n"
                "📸 אחרי התשלום, שלח כאן:\n• צילום מסך, או\n• Transaction Hash",
                self.back_keyboard())
            self.answer_callback(callback_id)
        elif data == "airdrop_status":
            user = _get_user(chat_id)
            self.answer_callback(callback_id, f"💰 יתרה: {user['hub_points']} נקודות | VIP: {'כן' if user['vip'] else 'לא'}", True)
        elif data == "copy_ref":
            self.answer_callback(callback_id, f"🔗 https://t.me/SLH_AIR_bot?start=ref_{chat_id}", True)
        elif data.startswith("copy_wallet_"):
            self.answer_callback(callback_id, f"💳 {TON_WALLET}", True)
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
                "📤 <b>שליחת מטבעות</b>\n\n"
                "💎 SLH: <code>/send_slh USER_ID AMOUNT</code>\n"
                "💠 TON: <code>/send_ton USER_ID AMOUNT</code>\n"
                "🟠 BNB: <code>/send_bnb USER_ID AMOUNT</code>\n"
                "🎮 ZVK: <code>/send_zvk USER_ID AMOUNT</code>\n\n"
                "💡 קבל את ה-USER_ID של הנמען: בקש ממנו /myid",
                self.wallet_inline_keyboard())
            self.answer_callback(callback_id)
        elif data == "wallet_history":
            self.handle_tx_history(chat_id)
            self.answer_callback(callback_id)
        elif data == "wallet_refresh":
            self.handle_wallet(chat_id, message_id)
            self.answer_callback(callback_id, "🔄 מרענן...")
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
                self.send(uid, f"✅ הפקדה #{dep_id} אושרה! הפקדון פעיל.")
                self.answer_callback(callback_id, "✅ אושר!", True)
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
                self.send(uid, f"❌ הפקדה #{dep_id} נדחתה.\nנסה שוב או פנה לתמיכה.")
                self.answer_callback(callback_id, "❌ נדחה", True)
        else:
            self.answer_callback(callback_id)

    # ── Text message handler ─────────────────────────────────────────
    def handle_text(self, chat_id, text, first_name, username):
        """Handle non-command text and legacy reply keyboard buttons.

        STRICT rules — no more 'any text = payment':
        - Valid username: 3–32 chars of [A-Za-z0-9_], and user is in username-collection state
        - Valid BSC/ETH TX hash: '0x' + exactly 64 hex chars (66 total)
        - Valid TON TX hash: 44 base64 chars OR 64 hex chars
        - Anything else → polite fallback (no false "payment received")
        """
        text = (text or "").strip()

        # Ignore group/channel messages (negative chat IDs)
        if chat_id < 0:
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
                f"✅ <b>נרשמת!</b> @{text}\n\n"
                f"💳 לרכישה שלח לארנק TON:\n<code>{TON_WALLET}</code>\n\n"
                "📸 שלח צילום מסך או Transaction Hash",
                self.back_keyboard())
            if str(chat_id) != ADMIN_ID:
                self.send(int(ADMIN_ID), f"👤 <b>משתמש חדש:</b> @{text} ({chat_id})")
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
                "📨 <b>תשלום התקבל לבדיקה!</b>\n\n"
                "🔗 Hash: <code>" + text[:20] + "...</code>\n"
                "⏳ סטטוס: <b>ממתין לאישור אדמין</b>\n\n"
                "תקבל התראה ברגע שהתשלום יאומת (עד 24 שעות).\n"
                "👥 בינתיים, הצטרף: @SLH_Community",
                self.back_keyboard())
            if str(chat_id) != ADMIN_ID:
                self.send(int(ADMIN_ID),
                    f"💸 <b>עסקה חדשה לאישור!</b>\n"
                    f"User: {chat_id} (@{user.get('username','?')})\n"
                    f"Hash: <code>{text}</code>\n"
                    f"/approve_{chat_id} או /reject_{chat_id}")
            return

        # --- 3) TX hash received OUT OF state → tell user to start flow ---
        if is_tx_hash and state != "awaiting_payment":
            self.send(chat_id,
                "⚠️ קיבלתי Hash אבל אין בקשת תשלום פתוחה.\n\n"
                "לתשלום חדש, לחץ /start → 💳 הפעלה",
                self.main_reply_keyboard())
            return

        # --- 4) Wallet address (informational only, no payment assumed) ---
        if re.match(r'^(0x[0-9a-fA-F]{40}|[UE]Q[A-Za-z0-9_-]{46})$', text):
            self.send(chat_id,
                "📋 קיבלתי כתובת ארנק. לשלוח כסף אל כתובת זו? לחץ /start → 💰 ארנק\n\n"
                "⚠️ שים לב: שליחת כתובת לבד לא פותחת תשלום.",
                self.main_reply_keyboard())
            return

        # --- 5) Fallback (no more false payment confirmations) ---
        self.send(chat_id, "🤖 לא הבנתי. לחץ /start לתפריט הראשי", self.main_reply_keyboard())

    # ── Main loop ────────────────────────────────────────────────────
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
                        self.send(chat_id, "📸 קבלנו! נבדוק ונעדכן בהקדם.", self.back_keyboard())
                        if str(chat_id) != ADMIN_ID:
                            self.send(int(ADMIN_ID), f"📸 <b>הוכחת תשלום!</b>\nUser: {chat_id} (@{username})")
                    continue

                logger.info(f"📩 {first_name}: {text}")

                # ── Slash commands ───────────────────────────────────
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
                    self.send(chat_id, "📞 <b>תמיכה</b>\n\nפנה ל-@Osif83 לכל שאלה.", self.main_reply_keyboard())
                elif text == "/myid":
                    self.send(chat_id, f"🆔 <b>המזהה שלך:</b> <code>{chat_id}</code>", self.main_reply_keyboard())
                elif text == "/hub":
                    user = _get_user(chat_id)
                    vip_badge = "👑 VIP" if user["vip"] else "🆓 Free"
                    self.send(chat_id,
                        f"🚀 <b>SLH HUB SYSTEM</b>\n\n"
                        f"👤 <b>{first_name}</b> | {vip_badge}\n"
                        f"💰 יתרה: <b>{user['hub_points']}</b> נקודות\n"
                        f"💎 SLH: <b>{user['slh_balance']:.2f}</b>\n"
                        f"👥 הפניות: <b>{user['referral_count']}</b>\n\n👇 בחר פעולה:",
                        self.hub_inline_keyboard())

                # ── Reply keyboard buttons (text buttons at bottom) ──
                elif text == "📊 השוק עכשיו":
                    self.handle_prices(chat_id)
                elif text == "💼 השקעות":
                    self.handle_investments(chat_id)
                elif text == "💰 ארנק":
                    self.handle_wallet(chat_id)
                elif text == "🔗 On-Chain":
                    self.handle_onchain_balance(chat_id)
                elif text == "🛡 סיכון ובקרה":
                    self.handle_risk(chat_id)
                elif text == "🎮 בונוסים":
                    self.handle_bonuses(chat_id)
                elif text == "👥 הזמן":
                    self.handle_invite(chat_id)
                elif text == "📊 דשבורד":
                    self.handle_dashboard(chat_id)
                elif text == "💳 הפעלה":
                    self.handle_activate(chat_id)
                elif text == "📤 שיתוף":
                    self.handle_share(chat_id)
                elif text == "📚 מדריכים":
                    self.handle_guides(chat_id)
                elif text == "🔥 מבצעים":
                    self.handle_deals_text(chat_id)
                elif text == "🪙 רכישת SLH":
                    self.handle_buy_slh_text(chat_id)

                # ── Swap commands ────────────────────────────────────
                elif text.startswith("/swap "):
                    self.handle_swap_text(chat_id)
                elif text.startswith("/limit "):
                    self.send(chat_id, "📝 פקודת Limit נרשמה. תקבל התראה כשהמחיר יגיע ליעד.", self.main_reply_keyboard())
                elif text.startswith("/alert "):
                    self.handle_alerts(chat_id)
                elif text == "/orders":
                    self.send(chat_id, "📋 <b>פקודות פתוחות:</b>\n\nאין פקודות פתוחות.", self.main_reply_keyboard())
                elif text == "/ai" or text == "🧠 ניתוח AI":
                    self.handle_ai_analysis(chat_id)

                elif not text.startswith("/"):
                    self.handle_text(chat_id, text, first_name, username)
                else:
                    self.send(chat_id, "🤖 פקודה לא מוכרת. לחץ /start", self.main_reply_keyboard())

        except Exception as e:
            logger.error(f"Update error: {e}")

    def run(self):
        logger.info("=" * 50)
        logger.info("🚀 SLH Investment House + HUB BOT — Starting...")
        logger.info("=" * 50)

        try:
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe", timeout=10)
            if r.status_code == 200 and r.json().get("ok"):
                logger.info(f"✅ Bot: @{r.json()['result']['username']}")
            else:
                logger.error("❌ Bot connection failed")
                return
        except Exception as e:
            logger.error(f"❌ Bot test error: {e}")
            return

        logger.info("🔄 Running — Investment House + HUB + Buy SLH")

        while True:
            try:
                self.process_updates()
                time.sleep(0.5)
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped")
                break
            except Exception as e:
                logger.error(f"❌ Main loop error: {e}")
                time.sleep(5)


def main():
    bot = SLHInvestmentBot()
    bot.run()


if __name__ == "__main__":
    main()
