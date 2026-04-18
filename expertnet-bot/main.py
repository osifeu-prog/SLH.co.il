"""
SLH Investment House - Telegram Investment Operating System
5 Layers: UI | Market Intelligence | Execution | Risk | Business
Powered by SPARK IND | SLH Ecosystem
"""
import os, sys, asyncio, logging, random, math, hashlib
from datetime import datetime, timedelta
from base64 import b64encode, b64decode

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB,
    ReplyKeyboardMarkup as RKM, KeyboardButton as KB,
)

sys.path.insert(0, "/app/shared")
sys.path.insert(0, "/app")
from slh_payments import db as pay_db
from slh_payments.config import ADMIN_USER_ID

try:
    from slh_payments.ledger import (transfer, get_balance, get_all_balances as get_internal_balances,
                                      get_history, mint, burn, ensure_balance)
    HAS_LEDGER = True
except ImportError:
    HAS_LEDGER = False

try:
    from blockchain import get_all_balances
    HAS_CHAIN = True
except ImportError:
    HAS_CHAIN = False

try:
    from transfer import transfer_slh, get_gas_price, format_gas_info
    HAS_TRANSFER = True
except ImportError:
    HAS_TRANSFER = False

# === CONFIG ===
TON_WALLET = "UQDhfyUPSJ8x9xnoeccTl55PEny7zUvDW8UabZ7PdDo52noF"
BNB_WALLET = "0x82815fA224Dd57FC009754cD55438f6a1C020252"
SUPPORT_PHONE = "0584203384"
ACTIVATION_ILS = 22.221
ACTIVATION_TON = 1.5

try:
    from market_data import get_prices, get_market_summary, get_full_prices_text, get_single_price, ton_to_ils
    HAS_MARKET = True
except ImportError:
    HAS_MARKET = False

try:
    from banking import (create_deposit, confirm_deposit, get_user_deposits,
                         request_withdrawal, approve_withdrawal, get_bank_stats,
                         generate_statement, start_kyc, submit_kyc_doc, approve_kyc,
                         get_kyc_status, get_pending_kyc, get_all_deposits, get_balance as bank_balance,
                         PLANS as BANK_PLANS, pool as bank_pool)
    HAS_BANK = True
except ImportError:
    HAS_BANK = False
SLH_REWARD = 100

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

# Crypto for PIN
encrypted_keys = {}
pending_pins = {}

# Trading stores (in-memory)
price_alerts = {}  # {uid: [{coin, direction, target, created}]}
limit_orders = {}  # {uid: [{id, coin, side, target_price, amount, created}]}
_order_counter = 0

def _encrypt(key, pin):
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 100000)
    encrypted = bytes(a ^ b for a, b in zip(key.encode().ljust(128, b'\0'), dk * 4))
    return b64encode(encrypted).decode(), b64encode(salt).decode()

def _decrypt(enc_data, salt_b64, pin):
    salt = b64decode(salt_b64)
    dk = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 100000)
    encrypted = b64decode(enc_data)
    return bytes(a ^ b for a, b in zip(encrypted, dk * 4)).rstrip(b'\0').decode()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("slh_inv")

TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not TOKEN: raise SystemExit("BOT_TOKEN missing")

bot = Bot(TOKEN)
dp = Dispatcher()

# === DATA ===
users = {}

PLANS = {
    "m1": {"name": "\U0001f331 \u05e4\u05e7\u05d3\u05d5\u05df \u05d7\u05d5\u05d3\u05e9\u05d9", "min": 1, "apy": 48, "monthly": 4, "lock": 30},
    "m3": {"name": "\U0001f4c8 \u05e4\u05e7\u05d3\u05d5\u05df \u05e8\u05d1\u05e2\u05d5\u05e0\u05d9", "min": 5, "apy": 55, "monthly": 4.5, "lock": 90},
    "m6": {"name": "\U0001f48e \u05e4\u05e7\u05d3\u05d5\u05df \u05d7\u05e6\u05d9-\u05e9\u05e0\u05ea\u05d9", "min": 10, "apy": 60, "monthly": 5, "lock": 180},
    "y1": {"name": "\U0001f451 \u05e4\u05e7\u05d3\u05d5\u05df \u05e9\u05e0\u05ea\u05d9", "min": 25, "apy": 65, "monthly": 5.4, "lock": 365},
}

PLAN_DESCRIPTIONS = {
    "m1": (
        "\U0001f331 \u05e4\u05e7\u05d3\u05d5\u05df \u05d7\u05d5\u05d3\u05e9\u05d9 - \u05de\u05d5\u05e9\u05dc\u05dd \u05dc\u05de\u05ea\u05d7\u05d9\u05dc\u05d9\u05dd\n\n"
        "\u05ea\u05e9\u05d5\u05d0\u05d4: 4% \u05db\u05dc \u05d7\u05d5\u05d3\u05e9 \u05e2\u05dc \u05d4\u05d4\u05e4\u05e7\u05d3\u05d4\n"
        "\u05d3\u05d5\u05d2\u05de\u05d4: 10 TON = 0.4 TON \u05e8\u05d5\u05d5\u05d7 \u05d1\u05d7\u05d5\u05d3\u05e9\n"
        "\u05ea\u05e7\u05d5\u05e4\u05d4: 30 \u05d9\u05d5\u05dd | \u05de\u05d9\u05e0\u05d9\u05de\u05d5\u05dd: 1 TON\n"
        "\u05de\u05e9\u05d9\u05db\u05d4 \u05de\u05d5\u05e7\u05d3\u05de\u05ea: \u05e2\u05de\u05dc\u05d4 5%"
    ),
    "m3": (
        "\U0001f4c8 \u05e4\u05e7\u05d3\u05d5\u05df \u05e8\u05d1\u05e2\u05d5\u05e0\u05d9 - \u05ea\u05e9\u05d5\u05d0\u05d4 \u05d2\u05d1\u05d5\u05d4\u05d4 \u05d9\u05d5\u05ea\u05e8\n\n"
        "\u05ea\u05e9\u05d5\u05d0\u05d4: 4.5% \u05db\u05dc \u05d7\u05d5\u05d3\u05e9 \u05e2\u05dc \u05d4\u05d4\u05e4\u05e7\u05d3\u05d4\n"
        "\u05d3\u05d5\u05d2\u05de\u05d4: 25 TON = 1.125 TON \u05e8\u05d5\u05d5\u05d7 \u05d1\u05d7\u05d5\u05d3\u05e9\n"
        "\u05ea\u05e7\u05d5\u05e4\u05d4: 90 \u05d9\u05d5\u05dd | \u05de\u05d9\u05e0\u05d9\u05de\u05d5\u05dd: 5 TON\n"
        "\u05de\u05e9\u05d9\u05db\u05d4 \u05de\u05d5\u05e7\u05d3\u05de\u05ea: \u05e2\u05de\u05dc\u05d4 5%"
    ),
    "m6": (
        "\U0001f48e \u05e4\u05e7\u05d3\u05d5\u05df \u05d7\u05e6\u05d9-\u05e9\u05e0\u05ea\u05d9 - \u05dc\u05de\u05e9\u05e7\u05d9\u05e2\u05d9\u05dd \u05e8\u05e6\u05d9\u05e0\u05d9\u05d9\u05dd\n\n"
        "\u05ea\u05e9\u05d5\u05d0\u05d4: 5% \u05db\u05dc \u05d7\u05d5\u05d3\u05e9 \u05e2\u05dc \u05d4\u05d4\u05e4\u05e7\u05d3\u05d4\n"
        "\u05d3\u05d5\u05d2\u05de\u05d4: 50 TON = 2.5 TON \u05e8\u05d5\u05d5\u05d7 \u05d1\u05d7\u05d5\u05d3\u05e9\n"
        "\u05ea\u05e7\u05d5\u05e4\u05d4: 180 \u05d9\u05d5\u05dd | \u05de\u05d9\u05e0\u05d9\u05de\u05d5\u05dd: 10 TON\n"
        "\u05de\u05e9\u05d9\u05db\u05d4 \u05de\u05d5\u05e7\u05d3\u05de\u05ea: \u05e2\u05de\u05dc\u05d4 5%"
    ),
    "y1": (
        "\U0001f451 \u05e4\u05e7\u05d3\u05d5\u05df \u05e9\u05e0\u05ea\u05d9 - \u05d4\u05ea\u05e9\u05d5\u05d0\u05d4 \u05d4\u05de\u05e7\u05e1\u05d9\u05de\u05dc\u05d9\u05ea\n\n"
        "\u05ea\u05e9\u05d5\u05d0\u05d4: 5.4% \u05db\u05dc \u05d7\u05d5\u05d3\u05e9 (65% \u05e9\u05e0\u05ea\u05d9!)\n"
        "\u05d3\u05d5\u05d2\u05de\u05d4: 100 TON = 5.4 TON \u05e8\u05d5\u05d5\u05d7 \u05d1\u05d7\u05d5\u05d3\u05e9\n"
        "\u05ea\u05e7\u05d5\u05e4\u05d4: 365 \u05d9\u05d5\u05dd | \u05de\u05d9\u05e0\u05d9\u05de\u05d5\u05dd: 25 TON\n"
        "\u05de\u05e9\u05d9\u05db\u05d4 \u05de\u05d5\u05e7\u05d3\u05de\u05ea: \u05e2\u05de\u05dc\u05d4 5%"
    ),
}

LOGO = (
    "\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557\n"
    "\u2551  \U0001f3ae  ExpertNet          \u2551\n"
    "\u2551  Premium Trading Hub     \u2551\n"
    "\u2551  \U0001f48e SLH \u00b7 SPARK IND      \u2551\n"
    "\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d"
)

SHARE_TEXT = (
    "\U0001f48e SLH - \u05d1\u05d9\u05ea \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea \u05d3\u05d9\u05d2\u05d9\u05d8\u05dc\u05d9\n\n"
    "\u2705 \u05ea\u05e9\u05d5\u05d0\u05d4 4% \u05d7\u05d5\u05d3\u05e9\u05d9 / 65% \u05e9\u05e0\u05ea\u05d9\n"
    "\u2705 \u05d0\u05e8\u05e0\u05e7 \u05de\u05dc\u05d0 (TON/BNB/SLH)\n"
    "\u2705 \u05d4\u05e2\u05d1\u05e8\u05d5\u05ea \u05de\u05d9\u05d9\u05d3\u05d9\u05d5\u05ea + blockchain\n"
    "\u2705 \u05e0\u05d9\u05ea\u05d5\u05d7 \u05e9\u05d5\u05e7 + \u05e1\u05d9\u05d2\u05e0\u05dc\u05d9\u05dd\n"
    "\U0001f381 +100 ZVK \u05de\u05ea\u05e0\u05d4!\n\n"
    "\U0001f4b0 22.221\u20aa \u05d1\u05dc\u05d1\u05d3!\n"
    "\U0001f449 https://t.me/SLH_AIR_bot\n\n"
    "\U0001f4a1 SPARK IND | SLH Ecosystem"
)


def g(uid, uname=""):
    if uid not in users:
        users[uid] = {
            "n": uname, "j": datetime.now().isoformat(),
            "ton": None, "bnb": None,
            "slh": 0.0, "zvk": 3, "pts": 0.0,
            "portfolio": [], "refs": [], "gp": 0, "gw": 0,
            "paid": False, "mode": "beginner",
            "risk": {"max_daily_loss": 10, "max_position": 50, "stop_loss": True},
        }
    if uname: users[uid]["n"] = uname
    return users[uid]

async def load_paid_users_from_db():
    """Load all approved expertnet users from DB into memory cache on startup."""
    try:
        pool = await pay_db.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT user_id FROM premium_users WHERE bot_name='expertnet' AND payment_status='approved'"
            )
        count = 0
        for row in rows:
            uid = row["user_id"]
            d = g(uid)
            d["paid"] = True
            count += 1
        log.info("Loaded %d paid users from DB", count)
    except Exception as e:
        log.error("Failed to load paid users from DB: %s", e)


async def save_paid_to_db(uid, admin_id=None):
    """Persist paid status to premium_users table."""
    try:
        pool = await pay_db.get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """UPDATE premium_users
                   SET payment_status='approved', approved_by=$2, approved_at=CURRENT_TIMESTAMP
                   WHERE user_id=$1 AND bot_name='expertnet'""",
                uid, admin_id,
            )
    except Exception as e:
        log.error("Failed to save paid status for %s: %s", uid, e)


def paid(uid):
    if uid == ADMIN_USER_ID: return True
    d = users.get(uid)
    return d.get("paid", False) if d else False

def lock_msg():
    return f"\U0001f512 \u05dc\u05de\u05e9\u05dc\u05de\u05d9\u05dd ({ACTIVATION_ILS}\u20aa)\n\U0001f4b3 \u05d4\u05e4\u05e2\u05dc\u05d4"


# ═══════════════════════════════════
# LAYER 1: USER INTERFACE
# ═══════════════════════════════════

def home_kb():
    return RKM(keyboard=[
        [KB(text="\U0001f4ca \u05d4\u05e9\u05d5\u05e7 \u05e2\u05db\u05e9\u05d9\u05d5"), KB(text="\U0001f4bc \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea")],
        [KB(text="\U0001f4b0 \u05d0\u05e8\u05e0\u05e7"), KB(text="\U0001f4ca \u05d3\u05e9\u05d1\u05d5\u05e8\u05d3")],
        [KB(text="\U0001f6e1 \u05e1\u05d9\u05db\u05d5\u05df \u05d5\u05d1\u05e7\u05e8\u05d4"), KB(text="\U0001f3ae \u05d1\u05d5\u05e0\u05d5\u05e1\u05d9\u05dd")],
        [KB(text="\U0001f465 \u05d4\u05d6\u05de\u05df"), KB(text="\U0001f4da \u05de\u05d3\u05e8\u05d9\u05db\u05d9\u05dd")],
        [KB(text="\U0001f4b3 \u05d4\u05e4\u05e2\u05dc\u05d4"), KB(text="\U0001f4e4 \u05e9\u05d9\u05ea\u05d5\u05e3")],
    ], resize_keyboard=True)


@dp.message(Command("start"))
async def start(m: types.Message, command: CommandObject = None):
    uid = m.from_user.id
    d = g(uid, m.from_user.username or "")

    if command and command.args and command.args.isdigit():
        ref = int(command.args)
        if ref != uid and uid not in g(ref).get("refs", []):
            g(ref)["refs"].append(uid)
            g(ref)["zvk"] += 5
            g(ref)["pts"] += 10
            # Register in referral API
            try:
                import aiohttp as _aio
                async with _aio.ClientSession() as _s:
                    await _s.post(f"https://slh-api-production.up.railway.app/api/referral/register?user_id={uid}&referrer_id={ref}")
            except Exception:
                pass

    name = m.from_user.first_name
    is_p = paid(uid)
    status = "\u2705 \u05de\u05e9\u05e7\u05d9\u05e2 \u05e4\u05e2\u05d9\u05dc" if is_p else "\U0001f512 \u05d7\u05e9\u05d1\u05d5\u05df \u05d7\u05d9\u05e0\u05dd"

    total_inv = 0.0
    total_earn = 0.0
    if HAS_BANK and is_p:
        deps = await get_user_deposits(uid)
        active = [x for x in deps if x["status"] == "active"]
        total_inv = sum(float(x["amount"]) for x in active)
        total_earn = sum(x.get("earned", 0) for x in active)
    elif d["portfolio"]:
        total_inv = sum(p["amt"] for p in d["portfolio"])
        total_earn = sum(
            p["amt"] * PLANS[p["plan"]]["monthly"] / 100 * max(1, (datetime.now() - datetime.fromisoformat(p["start"])).days) / 30
            for p in d["portfolio"]
        )

    # Real ledger balances
    zvk_bal = d['zvk']
    slh_bal = d['slh']
    if HAS_LEDGER:
        try:
            await ensure_balance(uid, "SLH")
            await ensure_balance(uid, "ZVK")
            i_bals = await get_internal_balances(uid)
            zvk_bal = i_bals.get("ZVK", d['zvk'])
            slh_bal = i_bals.get("SLH", d['slh'])
        except: pass

    await m.answer(
        f"{LOGO}\n\n"
        f"\u05e9\u05dc\u05d5\u05dd {name}! \U0001f44b\n\n"
        f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\U0001f4bc {status}\n"
        f"\U0001f4b0 \u05de\u05d5\u05e9\u05e7\u05e2: {total_inv:.2f} TON\n"
        f"\U0001f4c8 \u05e8\u05d5\u05d5\u05d7: +{total_earn:.4f} TON\n"
        f"\U0001f48e SLH: {slh_bal:.2f} | \U0001f3ae ZVK: {zvk_bal:.0f}\n"
        f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "\U0001f3ae *ExpertNet Premium* - \u05d0\u05e8\u05e7\u05d9\u05d9\u05d3, \u05de\u05e9\u05d7\u05e7\u05d9\u05dd, ZVK\n"
        "\U0001f4ca *\u05e9\u05d5\u05e7 \u05d7\u05d9* - \u05de\u05d7\u05d9\u05e8\u05d9\u05dd, \u05de\u05d2\u05de\u05d5\u05ea, \u05e1\u05d9\u05d2\u05e0\u05dc\u05d9\u05dd\n"
        "\U0001f4bc *\u05d4\u05e9\u05e7\u05e2\u05d5\u05ea* - 4 \u05ea\u05d5\u05db\u05e0\u05d9\u05d5\u05ea, 4%-5.4% \u05d7\u05d5\u05d3\u05e9\u05d9\n"
        "\U0001f4b0 *\u05d0\u05e8\u05e0\u05e7* - TON/BNB/SLH + \u05d4\u05e2\u05d1\u05e8\u05d5\u05ea\n"
        "\U0001f6e1 *\u05e1\u05d9\u05db\u05d5\u05df* - \u05d4\u05d2\u05d3\u05e8\u05d5\u05ea, \u05de\u05d2\u05d1\u05dc\u05d5\u05ea, vaults\n"
        "\U0001f465 *\u05d4\u05d6\u05de\u05df* - +5 ZVK + \u05e2\u05de\u05dc\u05d5\u05ea\n\n"
        "_ExpertNet \u00b7 Premium Trading Hub_\n"
        "_Powered by SLH \u00b7 SPARK IND_",
        reply_markup=home_kb(),
    )
    await pay_db.log_event("user.start", "expertnet", uid)


# ═══════════════════════════════════
# LAYER 2: MARKET INTELLIGENCE
# ═══════════════════════════════════
@dp.message(F.text == "\U0001f4ca \u05d4\u05e9\u05d5\u05e7 \u05e2\u05db\u05e9\u05d9\u05d5")
async def market_now(m: types.Message):
    kb = IKM(inline_keyboard=[
        [IKB(text="\U0001f4b1 \u05de\u05d7\u05d9\u05e8\u05d9\u05dd \u05de\u05dc\u05d0\u05d9\u05dd", callback_data="mkt:prices")],
        [IKB(text="\U0001f501 \u05e1\u05d5\u05d5\u05d0\u05e4", callback_data="mkt:swap"),
         IKB(text="\U0001f4cb \u05d4\u05d6\u05de\u05e0\u05d5\u05ea", callback_data="mkt:orders")],
        [IKB(text="\U0001f514 \u05d4\u05ea\u05e8\u05d0\u05d5\u05ea", callback_data="mkt:alert"),
         IKB(text="\U0001f9e0 AI", callback_data="mkt:ai")],
        [IKB(text="\U0001f4ca \u05ea\u05d9\u05e7 \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea", callback_data="mkt:portfolio")],
    ])

    if HAS_MARKET:
        summary = await get_market_summary()
        prices = await get_prices()
        if summary and prices:
            ton_p = prices.get("TON", {})
            await m.answer(
                "\U0001f4ca \u05d4\u05e9\u05d5\u05e7 \u05e2\u05db\u05e9\u05d9\u05d5 (\u05de\u05d7\u05d9\u05e8\u05d9\u05dd \u05d7\u05d9\u05d9\u05dd!)\n"
                "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
                f"{summary}\n\n"
                f"\U0001f4b1 1 TON = {ton_p.get('ils', 0):.1f}\u20aa | ${ton_p.get('usd', 0):.2f}\n\n"
                f"\u23f0 {datetime.now().strftime('%H:%M %d/%m/%Y')}\n\n"
                "\U0001f4a1 SLH Investment House",
                reply_markup=kb,
            )
            return

    await m.answer(
        "\U0001f4ca \u05d4\u05e9\u05d5\u05e7 \u05e2\u05db\u05e9\u05d9\u05d5\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "\u26a0\ufe0f \u05de\u05d7\u05d9\u05e8\u05d9\u05dd \u05dc\u05d0 \u05d6\u05de\u05d9\u05e0\u05d9\u05dd \u05db\u05e8\u05d2\u05e2.\n"
        "\u05e0\u05e1\u05d4 \u05e9\u05d5\u05d1 \u05d1\u05e2\u05d5\u05d3 \u05e8\u05d2\u05e2.\n\n"
        f"\u23f0 {datetime.now().strftime('%H:%M %d/%m/%Y')}",
        reply_markup=kb,
    )

@dp.callback_query(F.data == "mkt:deep")
async def mkt_deep(cb: types.CallbackQuery):
    await cb.message.answer(
        "\U0001f4ca \u05e0\u05d9\u05ea\u05d5\u05d7 \u05de\u05e2\u05de\u05d9\u05e7\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "\U0001f4c8 \u05de\u05d2\u05de\u05d4: \u05e9\u05d5\u05e7 \u05d1\u05de\u05d2\u05de\u05ea \u05e2\u05dc\u05d9\u05d9\u05d4\n"
        "\U0001f4ca \u05e0\u05e4\u05d7: \u05d2\u05d1\u05d5\u05d4 \u05de\u05d4\u05de\u05de\u05d5\u05e6\u05e2\n"
        "\U0001f6a8 \u05d7\u05d3\u05e9\u05d5\u05ea: \u05d0\u05d9\u05e8\u05d5\u05e2\u05d9 \u05de\u05d0\u05e7\u05e8\u05d5 \u05d4\u05e9\u05d1\u05d5\u05e2\n"
        "\U0001f4b0 \u05d4\u05de\u05dc\u05e6\u05d4: \u05d4\u05d9\u05d5\u05dd \u05d8\u05d5\u05d1 \u05dc\u05d4\u05e4\u05e7\u05d3\u05d5\u05ea\n\n"
        "\u26a0\ufe0f \u05d6\u05d4 \u05dc\u05d0 \u05d9\u05d9\u05e2\u05d5\u05e5 \u05d4\u05e9\u05e7\u05e2\u05d4.\n"
        "\u05d4\u05e9\u05ea\u05de\u05e9 \u05d1\u05e9\u05d9\u05e7\u05d5\u05dc \u05d3\u05e2\u05ea\u05da."
    )
    await cb.answer()

@dp.callback_query(F.data == "mkt:ai")
async def mkt_ai(cb: types.CallbackQuery):
    scenarios = [
        "\U0001f4c8 \u05ea\u05e8\u05d7\u05d9\u05e9 \u05e9\u05d5\u05e8\u05d9: \u05d0\u05dd BTC \u05e9\u05d5\u05d1\u05e8 70K, \u05e6\u05e4\u05d5\u05d9 \u05de\u05d4\u05dc\u05da \u05dc-75K",
        "\U0001f534 \u05ea\u05e8\u05d7\u05d9\u05e9 \u05d3\u05d5\u05d1\u05d9: \u05d0\u05dd BTC \u05e9\u05d5\u05d1\u05e8 65K, \u05d0\u05e4\u05e9\u05e8\u05d9 \u05e0\u05e4\u05d9\u05dc\u05d4 \u05dc-60K",
        "\U0001f7e1 \u05ea\u05e8\u05d7\u05d9\u05e9 \u05e0\u05d9\u05d9\u05d8\u05e8\u05dc\u05d9: \u05e6\u05e4\u05d5\u05d9 \u05d3\u05d7\u05d9\u05e1\u05d4 \u05e6\u05d3\u05d3\u05d9\u05ea",
    ]
    await cb.message.answer(
        "\U0001f9e0 \u05e0\u05d9\u05ea\u05d5\u05d7 AI\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        + "\n\n".join(scenarios) +
        "\n\n\u26a0\ufe0f \u05d6\u05d4 \u05dc\u05d0 \u05d9\u05d9\u05e2\u05d5\u05e5 \u05d4\u05e9\u05e7\u05e2\u05d4."
    )
    await cb.answer()

@dp.callback_query(F.data == "mkt:alert")
async def mkt_alert(cb: types.CallbackQuery):
    await cb.message.answer(
        "\U0001f514 \u05d4\u05ea\u05e8\u05d0\u05d5\u05ea \u05de\u05d7\u05d9\u05e8\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "\u05d1\u05e7\u05e8\u05d5\u05d1! \u05ea\u05d5\u05db\u05dc \u05dc\u05d4\u05d2\u05d3\u05d9\u05e8 \u05d4\u05ea\u05e8\u05d0\u05d5\u05ea \u05e2\u05dc:\n"
        "\u2022 \u05de\u05d7\u05d9\u05e8 \u05e9\u05e2\u05d5\u05d1\u05e8 \u05e8\u05de\u05d4\n"
        "\u2022 \u05e0\u05e4\u05d7 \u05d7\u05e8\u05d9\u05d2\n"
        "\u2022 \u05d7\u05d3\u05e9\u05d5\u05ea \u05e9\u05d5\u05e7\n"
        "\u2022 \u05e9\u05d9\u05e0\u05d5\u05d9 \u05d1\u05ea\u05d9\u05e7"
    )
    await cb.answer()


# ═══════════════════════════════════
# LAYER 3: INVESTMENT PORTFOLIO
# ═══════════════════════════════════
@dp.message(F.text == "\U0001f4bc \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea")
async def invest_menu(m: types.Message):
    uid = m.from_user.id
    if not paid(uid):
        txt = (
            "\U0001f4bc \u05ea\u05d5\u05db\u05e0\u05d9\u05d5\u05ea \u05e4\u05e7\u05d3\u05d5\u05df\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
            "\U0001f4a1 \u05d4\u05e4\u05e7\u05d3 \u05d5\u05d4\u05e8\u05d5\u05d5\u05d7 \u05db\u05dc \u05d7\u05d5\u05d3\u05e9!\n\n"
        )
        for k, p in PLANS.items():
            txt += f"{p['name']}: {p['monthly']}% \u05d7\u05d5\u05d3\u05e9\u05d9 | {p['apy']}% \u05e9\u05e0\u05ea\u05d9\n"
        txt += f"\n{lock_msg()}"
        await m.answer(txt)
        return

    d = g(uid)
    kb = IKM(inline_keyboard=[
        [IKB(text="\U0001f331 \u05d7\u05d5\u05d3\u05e9\u05d9 4%", callback_data="p:m1"),
         IKB(text="\U0001f4c8 \u05e8\u05d1\u05e2\u05d5\u05e0\u05d9 4.5%", callback_data="p:m3")],
        [IKB(text="\U0001f48e \u05d7\u05e6\u05d9-\u05e9\u05e0\u05ea\u05d9 5%", callback_data="p:m6"),
         IKB(text="\U0001f451 \u05e9\u05e0\u05ea\u05d9 65%!", callback_data="p:y1")],
        [IKB(text="\U0001f4cb \u05d4\u05ea\u05d9\u05e7 \u05e9\u05dc\u05d9", callback_data="p:my")],
    ])

    txt = "\U0001f4bc \u05ea\u05d5\u05db\u05e0\u05d9\u05d5\u05ea \u05d4\u05e9\u05e7\u05e2\u05d4\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
    for k, p in PLANS.items():
        txt += (
            f"{p['name']}\n"
            f"  \U0001f4b0 {p['monthly']}% \u05d7\u05d5\u05d3\u05e9\u05d9 | {p['apy']}% \u05e9\u05e0\u05ea\u05d9\n"
            f"  \u05de\u05d9\u05e0\u05d9\u05de\u05d5\u05dd {p['min']} TON | {p['lock']} \u05d9\u05d5\u05dd\n\n"
        )
    txt += "\U0001f4b3 \u05d0\u05d9\u05da \u05dc\u05d4\u05e4\u05e7\u05d9\u05d3:\n1. \u05d1\u05d7\u05e8 \u05ea\u05d5\u05db\u05e0\u05d9\u05ea\n2. \u05e9\u05dc\u05d7 TON \u05de-@wallet\n3. \u05e9\u05dc\u05d7 \u05e6\u05d9\u05dc\u05d5\u05dd \u05de\u05e1\u05da\n4. \u05d4\u05e4\u05e7\u05d3\u05d5\u05df \u05e0\u05e4\u05ea\u05d7!"
    await m.answer(txt, reply_markup=kb)


@dp.callback_query(F.data.startswith("p:"))
async def plan_action(cb: types.CallbackQuery):
    uid = cb.from_user.id
    key = cb.data.split(":")[1]

    if key == "my":
        if HAS_BANK:
            deps = await get_user_deposits(uid)
            if not deps:
                await cb.message.answer("\u05d0\u05d9\u05df \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea. /deposit \u05dc\u05d4\u05ea\u05d7\u05dc\u05d4!")
                await cb.answer()
                return
            txt = "\U0001f4cb \u05d4\u05ea\u05d9\u05e7 \u05e9\u05dc\u05d9\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
            total_v = 0
            for d in deps:
                status_e = {
                    "pending_payment": "\u23f3 \u05de\u05de\u05ea\u05d9\u05df",
                    "active": "\u2705 \u05e4\u05e2\u05d9\u05dc",
                    "closed": "\u2705 \u05e0\u05e1\u05d2\u05e8",
                    "rejected": "\u274c \u05e0\u05d3\u05d7\u05d4",
                }.get(d["status"], d["status"])
                earned = d.get("earned", 0)
                total_v += float(d["amount"]) + earned
                end_str = str(d.get("end_date", ""))[:10]
                lock_s = "\U0001f512" if d["status"] == "active" else ""
                txt += (
                    f"#{d['id']} | {d['plan_key']} | {float(d['amount']):.2f} TON\n"
                    f"  {status_e} {lock_s} | +{earned:.4f} TON\n"
                    f"  \u05e2\u05d3: {end_str}\n\n"
                )
            txt += f"\U0001f4b0 \u05e1\u05d4\"\u05db: {total_v:.4f} TON"
            await cb.message.answer(txt)
        else:
            d = g(uid)
            if not d["portfolio"]:
                await cb.message.answer("\u05d0\u05d9\u05df \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea \u05e2\u05d3\u05d9\u05d9\u05df.")
                await cb.answer()
                return
            txt = "\U0001f4cb \u05d4\u05ea\u05d9\u05e7 \u05e9\u05dc\u05d9\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
            total_v = 0
            for i, p in enumerate(d["portfolio"], 1):
                plan = PLANS[p["plan"]]
                days = max(1, (datetime.now() - datetime.fromisoformat(p["start"])).days)
                earned = p["amt"] * plan["monthly"] / 100 * days / 30
                total_v += p["amt"] + earned
                locked_until = datetime.fromisoformat(p["start"]) + timedelta(days=plan["lock"])
                lock_s = "\U0001f512" if datetime.now() < locked_until else "\U0001f513"
                txt += f"{i}. {plan['name']} | {p['amt']} TON\n   +{earned:.4f} | {lock_s} {locked_until.strftime('%d/%m')}\n\n"
            txt += f"\U0001f4b0 \u05e1\u05d4\"\u05db: {total_v:.4f} TON"
            await cb.message.answer(txt)
        await cb.answer()
        return

    plan = PLANS.get(key)
    if not plan:
        await cb.answer()
        return

    monthly = plan["monthly"]
    ex = max(10, plan["min"])
    m_earn = ex * monthly / 100
    t_earn = ex * plan["apy"] / 100 * plan["lock"] / 365

    kb = IKM(inline_keyboard=[
        [IKB(text=f"{plan['min']} TON", callback_data=f"inv:{key}:{plan['min']}"),
         IKB(text=f"{plan['min']*2} TON", callback_data=f"inv:{key}:{plan['min']*2}")],
        [IKB(text=f"{plan['min']*5} TON", callback_data=f"inv:{key}:{plan['min']*5}"),
         IKB(text=f"{plan['min']*10} TON", callback_data=f"inv:{key}:{plan['min']*10}")],
    ])

    desc = PLAN_DESCRIPTIONS.get(key, "")
    await cb.message.answer(
        f"{desc}\n\n"
        f"\U0001f4a1 \u05d3\u05d5\u05d2\u05de\u05d4: {ex} TON\n"
        f"  \u05d7\u05d5\u05d3\u05e9\u05d9: ~{m_earn:.2f} TON\n"
        f"  \u05dc\u05ea\u05e7\u05d5\u05e4\u05d4: ~{t_earn:.2f} TON\n\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "\U0001f4b3 \u05d0\u05d9\u05da \u05dc\u05d4\u05e4\u05e7\u05d9\u05d3:\n\n"
        "1\ufe0f\u20e3 \u05e4\u05ea\u05d7 @wallet \u05d1\u05d8\u05dc\u05d2\u05e8\u05dd\n"
        "2\ufe0f\u20e3 \u05dc\u05d7\u05e5 Buy \u05d5\u05e8\u05db\u05d5\u05e9 TON\n"
        "3\ufe0f\u20e3 \u05dc\u05d7\u05e5 Send \u05d5\u05e9\u05dc\u05d7 \u05dc\u05db\u05ea\u05d5\u05d1\u05ea:\n\n"
        f"\U0001f3e6 \u05e7\u05e8\u05df \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea SLH:\n<code>{TON_WALLET}</code>\n\n"
        "4\ufe0f\u20e3 \u05e9\u05dc\u05d7 \u05e6\u05d9\u05dc\u05d5\u05dd \u05de\u05e1\u05da \u05db\u05d0\u05df\n"
        "5\ufe0f\u20e3 \u05d4\u05d4\u05e4\u05e7\u05d3\u05d4 \u05ea\u05d0\u05d5\u05e9\u05e8 \u05ea\u05d5\u05da \u05d3\u05e7\u05d5\u05ea!",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("inv:"))
async def invest_action(cb: types.CallbackQuery):
    parts = cb.data.split(":")
    key, amt = parts[1], float(parts[2])
    plan = PLANS.get(key)
    if not plan: return
    uid = cb.from_user.id

    if HAS_BANK:
        dep_id, err = await create_deposit(uid, key, amt)
        if err:
            await cb.message.answer(f"\u274c {err}")
            await cb.answer()
            return
        monthly_earn = amt * plan["monthly"] / 100
        locked = datetime.now() + timedelta(days=plan["lock"])
        await cb.message.answer(
            f"\u2705 \u05d4\u05e4\u05e7\u05d3\u05d4 #{dep_id} \u05e0\u05d5\u05e6\u05e8\u05d4!\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
            f"{plan['name']} | {amt} TON\n"
            f"\u05ea\u05e9\u05d5\u05d0\u05d4 \u05d7\u05d5\u05d3\u05e9\u05d9\u05ea: ~{monthly_earn:.2f} TON\n"
            f"\u05e0\u05e2\u05d5\u05dc \u05e2\u05d3: {locked.strftime('%d/%m/%Y')}\n\n"
            f"\U0001f4b0 \u05e9\u05dc\u05d7 {amt} TON \u05dc:\n{TON_WALLET}\n\n"
            "\u05d5\u05e9\u05dc\u05d7 \u05e6\u05d9\u05dc\u05d5\u05dd \u05de\u05e1\u05da \u05dc\u05d0\u05d9\u05e9\u05d5\u05e8."
        )
        uname = cb.from_user.username or str(uid)
        admin_kb = IKM(inline_keyboard=[
            [IKB(text="\u2705 \u05d0\u05e9\u05e8", callback_data=f"adep:{dep_id}"),
             IKB(text="\u274c \u05d3\u05d7\u05d4", callback_data=f"rdep:{dep_id}")]
        ])
        try:
            await bot.send_message(ADMIN_USER_ID,
                f"\U0001f4b3 \u05d4\u05e4\u05e7\u05d3\u05d4 \u05d7\u05d3\u05e9\u05d4 #{dep_id}\n"
                f"\U0001f464 @{uname} ({uid})\n"
                f"\U0001f4bc {plan['name']} | {amt} TON\n"
                f"\U0001f4b0 {plan['monthly']}% \u05d7\u05d5\u05d3\u05e9\u05d9 | {plan['lock']} \u05d9\u05de\u05d9\u05dd",
                reply_markup=admin_kb)
        except: pass
    else:
        d = g(uid)
        d["portfolio"].append({"plan": key, "amt": amt, "start": datetime.now().isoformat()})
        total = sum(p["amt"] for p in d["portfolio"])
        locked = datetime.now() + timedelta(days=plan["lock"])
        monthly_earn = amt * plan["monthly"] / 100
        await cb.message.answer(
            f"\u2705 \u05d4\u05e4\u05e7\u05d3\u05d5\u05df \u05e0\u05e4\u05ea\u05d7!\n\n"
            f"{plan['name']} | {amt} TON\n"
            f"\u05ea\u05e9\u05d5\u05d0\u05d4 \u05d7\u05d5\u05d3\u05e9\u05d9\u05ea: ~{monthly_earn:.2f} TON\n"
            f"\u05e0\u05e2\u05d5\u05dc \u05e2\u05d3: {locked.strftime('%d/%m/%Y')}\n"
            f"\U0001f4bc \u05e1\u05d4\"\u05db \u05d1\u05ea\u05d9\u05e7: {total:.2f} TON"
        )
    await cb.answer()


# Admin inline deposit approve/reject
@dp.callback_query(F.data.startswith("adep:"))
async def admin_approve_dep(cb: types.CallbackQuery):
    if cb.from_user.id != ADMIN_USER_ID: return
    dep_id = int(cb.data.split(":")[1])
    ok, tx = await confirm_deposit(dep_id, cb.from_user.id)
    if ok:
        await cb.message.edit_text(cb.message.text + f"\n\n\u2705 \u05d0\u05d5\u05e9\u05e8! TX: {tx}")
        async with (await bank_pool()).acquire() as c:
            dep = await c.fetchrow("SELECT user_id, amount, plan_key FROM deposits WHERE id=$1", dep_id)
        if dep:
            try:
                await bot.send_message(dep["user_id"],
                    f"\u2705 \u05d4\u05e4\u05e7\u05d3\u05d4 #{dep_id} \u05d0\u05d5\u05e9\u05e8\u05d4!\n"
                    f"\U0001f4b0 {float(dep['amount']):.2f} TON \u05e0\u05e7\u05dc\u05d8\u05d5 \u05dc\u05d7\u05e9\u05d1\u05d5\u05e0\u05da.\n"
                    f"\u05d4\u05e4\u05e7\u05d3\u05d5\u05df \u05e4\u05e2\u05d9\u05dc!")
            except: pass
    else:
        await cb.message.edit_text(cb.message.text + f"\n\n\u274c {tx}")
    await cb.answer()


@dp.callback_query(F.data.startswith("rdep:"))
async def admin_reject_dep(cb: types.CallbackQuery):
    if cb.from_user.id != ADMIN_USER_ID: return
    dep_id = int(cb.data.split(":")[1])
    async with (await bank_pool()).acquire() as c:
        dep = await c.fetchrow("SELECT user_id FROM deposits WHERE id=$1", dep_id)
        await c.execute("UPDATE deposits SET status='rejected' WHERE id=$1", dep_id)
    await cb.message.edit_text(cb.message.text + "\n\n\u274c \u05e0\u05d3\u05d7\u05d4!")
    if dep:
        try:
            await bot.send_message(dep["user_id"],
                f"\u274c \u05d4\u05e4\u05e7\u05d3\u05d4 #{dep_id} \u05e0\u05d3\u05d7\u05ea\u05d4.\n\u05e0\u05e1\u05d4 \u05e9\u05d5\u05d1 \u05d0\u05d5 \u05e4\u05e0\u05d4 \u05dc\u05ea\u05de\u05d9\u05db\u05d4.")
        except: pass
    await cb.answer()


# ═══════════════════════════════════
# LAYER 4: RISK & CONTROL
# ═══════════════════════════════════
@dp.message(F.text == "\U0001f6e1 \u05e1\u05d9\u05db\u05d5\u05df \u05d5\u05d1\u05e7\u05e8\u05d4")
async def risk_menu(m: types.Message):
    d = g(m.from_user.id)
    risk = d.get("risk", {})
    sl_status = "\u2705 \u05e4\u05e2\u05d9\u05dc" if risk.get("stop_loss") else "\u274c \u05db\u05d1\u05d5\u05d9"
    mdl = risk.get("max_daily_loss", 10)
    mpos = risk.get("max_position", 50)
    await m.answer(
        "\U0001f6e1 \u05e1\u05d9\u05db\u05d5\u05df \u05d5\u05d1\u05e7\u05e8\u05d4\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "\U0001f4a1 \u05d4\u05d2\u05d3\u05e8\u05d5\u05ea \u05d4\u05e1\u05d9\u05db\u05d5\u05df \u05e9\u05dc\u05da:\n\n"
        f"\U0001f6a8 \u05d4\u05e4\u05e1\u05d3 \u05d9\u05d5\u05de\u05d9: {mdl}%\n"
        f"\U0001f4ca \u05e4\u05d5\u05d6\u05d9\u05e6\u05d9\u05d4 \u05de\u05e7\u05e1\u05d9\u05de\u05dc\u05d9\u05ea: {mpos}%\n"
        f"\U0001f6d1 Stop Loss: {sl_status}\n\n"
        "\U0001f4dd \u05e2\u05e7\u05e8\u05d5\u05e0\u05d5\u05ea:\n"
        "\u2022 \u05dc\u05d0 \u05dc\u05d4\u05e9\u05e7\u05d9\u05e2 \u05d9\u05d5\u05ea\u05e8 \u05de\u05de\u05d4 \u05e9\u05de\u05d5\u05db\u05e0\u05d9\u05dd \u05dc\u05d4\u05e4\u05e1\u05d9\u05d3\n"
        "\u2022 \u05dc\u05d4\u05e4\u05e8\u05d9\u05d3 \u05d1\u05d9\u05df \u05de\u05e1\u05e4\u05e8 \u05ea\u05d5\u05db\u05e0\u05d9\u05d5\u05ea\n"
        "\u2022 \u05dc\u05d0 \u05dc\u05e9\u05d9\u05dd \u05d4\u05db\u05dc \u05e2\u05dc \u05e7\u05dc\u05e3 \u05d0\u05d7\u05d3\n"
        "\u2022 \u05dc\u05d4\u05e9\u05d0\u05d9\u05e8 \u05e0\u05d6\u05d9\u05dc\u05d5\u05ea \u05dc\u05de\u05e7\u05e8\u05d4 \u05d7\u05d9\u05e8\u05d5\u05dd\n\n"
        "\U0001f6e1 \u05d4\u05de\u05e2\u05e8\u05db\u05ea \u05e9\u05d5\u05de\u05e8\u05ea \u05e2\u05dc\u05d9\u05da!"
    )


# ═══════════════════════════════════
# WALLET + TRANSFERS
# ═══════════════════════════════════
@dp.message(F.text == "\U0001f4b0 \u05d0\u05e8\u05e0\u05e7")
@dp.message(Command("wallet"))
async def wallet(m: types.Message):
    uid = m.from_user.id
    if not paid(uid):
        await m.answer(
            "\U0001f512 \u05d0\u05e8\u05e0\u05e7 - \u05dc\u05de\u05e9\u05dc\u05de\u05d9\u05dd\n\n"
            "\u05de\u05d4 \u05ea\u05e7\u05d1\u05dc:\n"
            "\u2022 \u05d9\u05ea\u05e8\u05d5\u05ea \u05d1\u05d6\u05de\u05df \u05d0\u05de\u05ea\n"
            "\u2022 \u05d4\u05e2\u05d1\u05e8\u05d5\u05ea \u05de\u05d9\u05d9\u05d3\u05d9\u05d5\u05ea + blockchain\n"
            "\u2022 \u05de\u05d7\u05e9\u05d1\u05d5\u05df \u05d4\u05de\u05e8\u05d4\n\n"
            f"{lock_msg()}"
        )
        return
    d = g(uid)
    ton_a = d.get("ton") or "\u05dc\u05d0 \u05de\u05d7\u05d5\u05d1\u05e8"
    bnb_a = d.get("bnb") or "\u05dc\u05d0 \u05de\u05d7\u05d5\u05d1\u05e8"

    # Bank balance
    bank_txt = ""
    if HAS_BANK:
        bal = await bank_balance(uid)
        bank_txt = (
            f"\n\U0001f3e6 \u05d7\u05e9\u05d1\u05d5\u05df \u05d1\u05e0\u05e7:\n"
            f"  \U0001f4b0 \u05d6\u05de\u05d9\u05df: {bal['available']:.4f} TON\n"
            f"  \U0001f512 \u05e0\u05e2\u05d5\u05dc: {bal['locked']:.4f} TON\n"
            f"  \U0001f4b0 \u05e1\u05d4\"\u05db: {bal['total']:.4f} TON\n"
        )

    # Blockchain balance
    chain_txt = ""
    if HAS_CHAIN and (d.get("ton") or d.get("bnb")):
        await m.answer("\u23f3 \u05d8\u05d5\u05e2\u05df \u05d9\u05ea\u05e8\u05d5\u05ea...")
        bals = await get_all_balances(d.get("ton"), d.get("bnb"))
        if bals["ton"] is not None: chain_txt += f"\n  \U0001f4a0 TON: {bals['ton']:.4f}"
        if bals["bnb"] is not None: chain_txt += f"\n  \U0001f7e1 BNB: {bals['bnb']:.6f}"
        if bals["slh"] is not None: chain_txt += f"\n  \U0001f48e SLH: {bals['slh']:.4f}"
        if chain_txt: chain_txt = "\n\U0001f517 \u05d1\u05dc\u05d5\u05e7\u05e6'\u05d9\u05d9\u05df:" + chain_txt + "\n"

    kb = IKM(inline_keyboard=[
        [IKB(text="\U0001f4e4 \u05d4\u05e2\u05d1\u05e8 SLH", callback_data="w:transfer_slh"),
         IKB(text="\U0001f4e4 \u05d4\u05e2\u05d1\u05e8 ZVK", callback_data="w:transfer_zvk")],
        [IKB(text="\U0001f517 \u05d7\u05d1\u05e8 TON", callback_data="w:ton"),
         IKB(text="\U0001f517 \u05d7\u05d1\u05e8 BNB", callback_data="w:bnb")],
        [IKB(text="\U0001f4b3 \u05d4\u05e4\u05e7\u05d3\u05d5\u05ea \u05e9\u05dc\u05d9", callback_data="p:my")],
        [IKB(text="\U0001f4ca \u05ea\u05d9\u05e7 \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea", callback_data="mkt:portfolio")],
    ])

    # Internal balances
    ledger_txt = ""
    if HAS_LEDGER:
        await ensure_balance(uid, "SLH")
        await ensure_balance(uid, "ZVK")
        i_bals = await get_internal_balances(uid)
        ledger_txt = f"\U0001f48e SLH: {i_bals.get('SLH', 0):.4f}\n\U0001f3ae ZVK: {i_bals.get('ZVK', 0):.0f}\n"

    await m.answer(
        f"\U0001f4b0 \u05d0\u05e8\u05e0\u05e7\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        f"{ledger_txt}"
        f"{bank_txt}{chain_txt}\n"
        f"\U0001f517 TON: {ton_a}\n"
        f"\U0001f517 BNB: {bnb_a}\n\n"
        "\U0001f4b3 \u05e4\u05e7\u05d5\u05d3\u05d5\u05ea:\n"
        "/deposit - \u05d4\u05e4\u05e7\u05d3\u05d4 \u05d7\u05d3\u05e9\u05d4\n"
        "/mydeposits - \u05d4\u05d4\u05e4\u05e7\u05d3\u05d5\u05ea \u05e9\u05dc\u05d9\n"
        "/withdraw - \u05de\u05e9\u05d9\u05db\u05d4\n"
        "/statement - \u05d3\u05e3 \u05d7\u05e9\u05d1\u05d5\u05df\n"
        "/pay - \u05d4\u05e2\u05d1\u05e8\u05d4 \u05e4\u05e0\u05d9\u05de\u05d9\u05ea\n"
        "/send - \u05d4\u05e2\u05d1\u05e8\u05d4 blockchain\n"
        "/portfolio - \u05ea\u05d9\u05e7 \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea",
        reply_markup=kb,
    )


@dp.callback_query(F.data == "w:ton")
async def w_ton(cb: types.CallbackQuery):
    await cb.message.answer("\u05e9\u05dc\u05d7:\n/set_ton <\u05db\u05ea\u05d5\u05d1\u05ea TON>")
    await cb.answer()

@dp.callback_query(F.data == "w:bnb")
async def w_bnb(cb: types.CallbackQuery):
    await cb.message.answer("\u05e9\u05dc\u05d7:\n/set_bnb <\u05db\u05ea\u05d5\u05d1\u05ea BNB>")
    await cb.answer()

@dp.callback_query(F.data == "w:calc")
async def w_calc(cb: types.CallbackQuery):
    await cb.message.answer(
        "\U0001f4b1 \u05de\u05d7\u05e9\u05d1\u05d5\u05df\n\n"
        "1 TON = ~14.8\u20aa | $3.85\n"
        "1 BNB = ~2,200\u20aa | $600\n\n"
        f"\u05d4\u05e4\u05e2\u05dc\u05d4: {ACTIVATION_TON} TON = ~{ACTIVATION_ILS}\u20aa\n\n"
        "\u05dc\u05e7\u05e0\u05d9\u05d9\u05ea TON: \u05e4\u05ea\u05d7 @wallet"
    )
    await cb.answer()

@dp.message(Command("set_ton"))
async def set_ton(m: types.Message, command: CommandObject = None):
    if command and command.args:
        g(m.from_user.id)["ton"] = command.args.strip()
        await m.answer(f"\u2705 TON \u05e0\u05e9\u05de\u05e8!")
    else:
        await m.answer("/set_ton <\u05db\u05ea\u05d5\u05d1\u05ea>")

@dp.message(Command("set_bnb"))
async def set_bnb(m: types.Message, command: CommandObject = None):
    if command and command.args:
        g(m.from_user.id)["bnb"] = command.args.strip()
        await m.answer(f"\u2705 BNB \u05e0\u05e9\u05de\u05e8!")
    else:
        await m.answer("/set_bnb <\u05db\u05ea\u05d5\u05d1\u05ea>")


# Internal transfers
@dp.message(Command("pay"))
async def pay_cmd(m: types.Message, command: CommandObject = None):
    if not paid(m.from_user.id):
        await m.answer(lock_msg()); return
    if not HAS_LEDGER:
        await m.answer("\u274c"); return
    if not command or not command.args:
        await m.answer("/pay <user_id> <\u05e1\u05db\u05d5\u05dd> [SLH/ZVK]"); return
    args = command.args.strip().split()
    if len(args) < 2:
        await m.answer("/pay <user_id> <\u05e1\u05db\u05d5\u05dd> [SLH/ZVK]"); return
    try:
        to_uid = int(args[0]); amount = float(args[1])
    except ValueError:
        await m.answer("\u274c"); return
    token = args[2].upper() if len(args) > 2 else "SLH"
    uid = m.from_user.id
    await ensure_balance(uid, token); await ensure_balance(to_uid, token)
    ok, msg, fb, tb = await transfer(uid, to_uid, token, amount)
    if ok:
        await m.answer(f"\u2705 {amount} {token} \u05d4\u05d5\u05e2\u05d1\u05e8\u05d5!\n\u05d9\u05ea\u05e8\u05ea\u05da: {fb:.4f}")
        try: await bot.send_message(to_uid, f"\U0001f4e5 \u05e7\u05d9\u05d1\u05dc\u05ea {amount} {token}!")
        except: pass
    else:
        await m.answer(f"\u274c {msg}")

@dp.message(Command("mybalance"))
async def mybal(m: types.Message):
    if not paid(m.from_user.id):
        await m.answer(lock_msg()); return
    if not HAS_LEDGER: return
    uid = m.from_user.id
    await ensure_balance(uid, "SLH"); await ensure_balance(uid, "ZVK")
    bals = await get_internal_balances(uid)
    await m.answer(f"\U0001f4b0 SLH: {bals.get('SLH',0):.4f}\n\U0001f3ae ZVK: {bals.get('ZVK',0):.4f}")

@dp.message(Command("txhistory"))
async def txhist(m: types.Message):
    if not HAS_LEDGER: return
    hist = await get_history(m.from_user.id, 10)
    if not hist: await m.answer("\u05d0\u05d9\u05df \u05d4\u05d9\u05e1\u05d8\u05d5\u05e8\u05d9\u05d4"); return
    uid = m.from_user.id
    lines = ["\U0001f4cb \u05d4\u05d9\u05e1\u05d8\u05d5\u05e8\u05d9\u05d4\n"]
    for tx in hist:
        d = "\U0001f4e4" if tx["from_user_id"] == uid else "\U0001f4e5"
        lines.append(f"{d} {tx['amount']:.4f} {tx['token']} | {str(tx['created_at'])[:16]}")
    await m.answer("\n".join(lines))

@dp.message(Command("gas"))
async def gas_cmd(m: types.Message):
    if not HAS_TRANSFER: return
    gp = await get_gas_price()
    info = format_gas_info(gp)
    await m.answer(f"\u26fd Gas: {info['gwei']} Gwei | {info['bnb']} BNB | {info['ils']}")

# Blockchain transfers with PIN
@dp.message(Command("setkey"))
async def setkey(m: types.Message, command: CommandObject = None):
    if not paid(m.from_user.id): await m.answer(lock_msg()); return
    if not command or not command.args:
        await m.answer("/setkey <\u05de\u05e4\u05ea\u05d7 \u05e4\u05e8\u05d8\u05d9>"); return
    key = command.args.strip()
    if not key.startswith("0x"): key = "0x" + key
    if len(key) != 66: await m.answer("\u274c 64 \u05ea\u05d5\u05d5\u05d9\u05dd"); return
    try: await m.delete()
    except: pass
    pending_pins[m.from_user.id] = {"step": "pin", "key": key}
    await m.answer("\u2705 \u05de\u05e4\u05ea\u05d7 \u05d4\u05ea\u05e7\u05d1\u05dc!\n\u05e9\u05dc\u05d7 PIN (4-6 \u05e1\u05e4\u05e8\u05d5\u05ea):")

@dp.message(F.text.regexp(r"^\d{4,6}$"))
async def pin_handler(m: types.Message):
    uid = m.from_user.id
    if uid not in pending_pins: return
    pin = m.text.strip()
    try: await m.delete()
    except: pass
    enc, salt = _encrypt(pending_pins[uid]["key"], pin)
    encrypted_keys[uid] = {"key": enc, "salt": salt}
    del pending_pins[uid]
    await m.answer(f"\u2705 \u05de\u05d5\u05e6\u05e4\u05df!\n/send <\u05db\u05ea\u05d5\u05d1\u05ea> <\u05e1\u05db\u05d5\u05dd> <PIN>")

@dp.message(Command("send"))
async def send_cmd(m: types.Message, command: CommandObject = None):
    uid = m.from_user.id
    if not paid(uid): await m.answer(lock_msg()); return
    if not HAS_TRANSFER: await m.answer("\u274c"); return
    if uid not in encrypted_keys: await m.answer("/setkey \u05e7\u05d5\u05d3\u05dd"); return
    if not command or not command.args: await m.answer("/send <\u05db\u05ea\u05d5\u05d1\u05ea> <\u05e1\u05db\u05d5\u05dd> <PIN>"); return
    args = command.args.strip().split()
    if len(args) < 3: await m.answer("/send <\u05db\u05ea\u05d5\u05d1\u05ea> <\u05e1\u05db\u05d5\u05dd> <PIN>"); return
    to_addr, amount_s, pin = args[0], args[1], args[2]
    try: amount = float(amount_s)
    except: await m.answer("\u274c"); return
    try: await m.delete()
    except: pass
    try:
        pk = _decrypt(encrypted_keys[uid]["key"], encrypted_keys[uid]["salt"], pin)
    except: await m.answer("\u274c PIN \u05e9\u05d2\u05d5\u05d9"); return
    d = g(uid)
    from_addr = d.get("bnb", "")
    if not from_addr: await m.answer("/set_bnb \u05e7\u05d5\u05d3\u05dd"); return
    fs = from_addr[:8] + "..." + from_addr[-4:]
    ts = to_addr[:8] + "..." + to_addr[-4:]
    await m.answer(f"\u23f3 {fs} \u2192 {ts} | {amount} SLH")
    ok, result, gas = await transfer_slh(pk, from_addr, to_addr, amount)
    pk = None
    if ok:
        await m.answer(f"\u2705 {amount} SLH \u05d4\u05d5\u05e2\u05d1\u05e8\u05d5!\n\u26fd {gas:.6f} BNB\nhttps://bscscan.com/tx/0x{result}")
    else:
        await m.answer(f"\u274c {str(result)[:80]}")


# ═══════════════════════════════════
# LAYER 5: BUSINESS
# ═══════════════════════════════════
@dp.message(F.text == "\U0001f4ca \u05d3\u05e9\u05d1\u05d5\u05e8\u05d3")
async def dashboard(m: types.Message):
    uid = m.from_user.id
    d = g(uid)

    if HAS_BANK:
        deps = await get_user_deposits(uid)
        bal = await bank_balance(uid)
        active_deps = [x for x in deps if x["status"] == "active"]
        ti = sum(float(x["amount"]) for x in active_deps)
        te = sum(x.get("earned", 0) for x in active_deps)
        n_deps = len(active_deps)
        pending = len([x for x in deps if x["status"] == "pending_payment"])
        avail = bal["available"]
        locked_bal = bal["locked"]

    zvk_dash = d["zvk"]
    if HAS_LEDGER:
        try:
            await ensure_balance(uid, "ZVK")
            i_b = await get_internal_balances(uid)
            zvk_dash = i_b.get("ZVK", d["zvk"])
        except: pass

    if not HAS_BANK:
        ti = sum(p["amt"] for p in d["portfolio"])
        te = sum(p["amt"] * PLANS[p["plan"]]["monthly"] / 100 * max(1, (datetime.now() - datetime.fromisoformat(p["start"])).days) / 30 for p in d["portfolio"]) if d["portfolio"] else 0
        n_deps = len(d["portfolio"])
        pending = 0
        avail = 0
        locked_bal = ti

    wr = (d["gw"] / max(1, d["gp"])) * 100
    await m.answer(
        f"\U0001f4ca \u05d3\u05e9\u05d1\u05d5\u05e8\u05d3\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        f"\U0001f3e6 \u05d7\u05e9\u05d1\u05d5\u05df \u05d1\u05e0\u05e7:\n"
        f"  \U0001f4b0 \u05d6\u05de\u05d9\u05df: {avail:.4f} TON\n"
        f"  \U0001f512 \u05e0\u05e2\u05d5\u05dc: {locked_bal:.4f} TON\n"
        f"  \U0001f4b0 \u05e1\u05d4\"\u05db: {avail + locked_bal:.4f} TON\n\n"
        f"\U0001f4bc \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea \u05e4\u05e2\u05d9\u05dc\u05d5\u05ea: {n_deps}\n"
        f"\u23f3 \u05de\u05de\u05ea\u05d9\u05e0\u05d5\u05ea \u05dc\u05d0\u05d9\u05e9\u05d5\u05e8: {pending}\n"
        f"\U0001f4b0 \u05de\u05d5\u05e9\u05e7\u05e2: {ti:.2f} TON\n"
        f"\U0001f4c8 \u05e8\u05d5\u05d5\u05d7: +{te:.4f} TON\n\n"
        f"\U0001f3ae ZVK: {zvk_dash:.0f} | \u05de\u05e9\u05d7\u05e7\u05d9\u05dd: {d['gp']} ({wr:.0f}%)\n"
        f"\U0001f465 \u05d4\u05d6\u05de\u05e0\u05d5\u05ea: {len(d['refs'])}\n\n"
        "SLH Investment House"
    )


@dp.message(F.text == "\U0001f3ae \u05d1\u05d5\u05e0\u05d5\u05e1\u05d9\u05dd")
async def bonus(m: types.Message):
    uid = m.from_user.id
    zvk_bal = 0
    if HAS_LEDGER:
        await ensure_balance(uid, "ZVK")
        bals = await get_internal_balances(uid)
        zvk_bal = bals.get("ZVK", 0)
    else:
        zvk_bal = g(uid)["zvk"]

    kb = IKM(inline_keyboard=[
        [IKB(text="\U0001f3b0 \u05e1\u05dc\u05d5\u05d8\u05d9\u05dd (1 ZVK)", callback_data="g:sl"),
         IKB(text="\U0001f3b2 \u05e7\u05d5\u05d1\u05d9\u05d5\u05ea (1 ZVK)", callback_data="g:di")],
        [IKB(text="\U0001f3c0 \u05db\u05d3\u05d5\u05e8\u05e1\u05dc (1 ZVK)", callback_data="g:ba"),
         IKB(text="\U0001f3af \u05d7\u05e6\u05d9\u05dd (1 ZVK)", callback_data="g:da")],
        [IKB(text="\U0001f4b5 \u05e7\u05e0\u05d4 ZVK", callback_data="g:buy")],
    ])
    await m.answer(
        f"\U0001f3ae \u05d1\u05d5\u05e0\u05d5\u05e1\u05d9\u05dd | ZVK: {zvk_bal:.0f}\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "\u05db\u05dc \u05de\u05e9\u05d7\u05e7 = 1 ZVK\n"
        "\U0001f3b0 \u05e1\u05dc\u05d5\u05d8\u05d9\u05dd: \u05e4\u05e8\u05e1 \u05d2\u05d3\u05d5\u05dc \u05e2\u05d3 25 ZVK!\n"
        "\U0001f3b2 \u05e7\u05d5\u05d1\u05d9\u05d5\u05ea: 6=5 ZVK, 4-5=2 ZVK\n"
        "\U0001f3c0 \u05db\u05d3\u05d5\u05e8\u05e1\u05dc: 4+=3 ZVK\n"
        "\U0001f3af \u05d7\u05e6\u05d9\u05dd: 6=5 ZVK, 4-5=2 ZVK\n\n"
        "\U0001f4b5 10 ZVK = 1 TON | 50 = 4 | 100 = 7",
        reply_markup=kb,
    )

async def _game(cb, emoji):
    uid = cb.from_user.id
    d = g(uid)

    # Check ZVK balance from real ledger
    if HAS_LEDGER:
        await ensure_balance(uid, "ZVK")
        bals = await get_internal_balances(uid)
        zvk_bal = bals.get("ZVK", 0)
        if zvk_bal < 1:
            await cb.answer("\u274c \u05d0\u05d9\u05df ZVK! \u05e7\u05e0\u05d4 \u05e2\u05dd /buy_zvk", show_alert=True)
            return
        await burn(uid, "ZVK", 1, "game_play")
    else:
        if d["zvk"] < 1:
            await cb.answer("\u274c \u05d0\u05d9\u05df ZVK!", show_alert=True)
            return
        d["zvk"] -= 1

    d["gp"] += 1
    r = await bot.send_dice(cb.message.chat.id, emoji=emoji)
    await asyncio.sleep(3)
    v = r.dice.value
    p = 0
    if emoji == "\U0001f3b0":
        p = 25 if v == 64 else (10 if v in (1,22,43) else (3 if v % 4 == 0 else 0))
    elif emoji == "\U0001f3b2":
        p = 5 if v == 6 else (2 if v >= 4 else 0)
    elif emoji == "\U0001f3c0":
        p = 3 if v >= 4 else 0
    elif emoji == "\U0001f3af":
        p = 5 if v == 6 else (2 if v >= 4 else 0)

    if p > 0:
        d["gw"] += 1
        if HAS_LEDGER:
            await mint(uid, "ZVK", p, "game_win")
            bals = await get_internal_balances(uid)
            new_zvk = bals.get("ZVK", 0)
        else:
            d["zvk"] += p
            new_zvk = d["zvk"]
        await cb.message.answer(f"\U0001f389 \u05e0\u05d9\u05e6\u05d7\u05ea! +{p} ZVK!\n\U0001f3ae ZVK: {new_zvk:.0f}")
    else:
        if HAS_LEDGER:
            bals = await get_internal_balances(uid)
            new_zvk = bals.get("ZVK", 0)
        else:
            new_zvk = d["zvk"]
        await cb.message.answer(f"\u274c \u05dc\u05d0 \u05d4\u05e4\u05e2\u05dd | ZVK: {new_zvk:.0f}")
    await cb.answer()

@dp.callback_query(F.data == "g:sl")
async def gs(cb): await _game(cb, "\U0001f3b0")
@dp.callback_query(F.data == "g:di")
async def gd(cb): await _game(cb, "\U0001f3b2")
@dp.callback_query(F.data == "g:ba")
async def gb(cb): await _game(cb, "\U0001f3c0")
@dp.callback_query(F.data == "g:da")
async def gda(cb): await _game(cb, "\U0001f3af")

@dp.callback_query(F.data == "g:buy")
async def gbuy(cb: types.CallbackQuery):
    await cb.message.answer(f"\U0001f4b5 10=1TON | 50=4TON | 100=7TON\n\n\u05e9\u05dc\u05d7 \u05dc:\n{TON_WALLET}")
    await cb.answer()


# REFERRALS + GUIDES + ACTIVATION
@dp.message(F.text == "\U0001f465 \u05d4\u05d6\u05de\u05df")
async def refs(m: types.Message):
    d = g(m.from_user.id)
    link = f"https://t.me/SLH_AIR_bot?start={m.from_user.id}"
    await m.answer(f"\U0001f465 \u05d4\u05d6\u05de\u05df \u05d7\u05d1\u05e8\u05d9\u05dd\n\n\U0001f517 {link}\n\n\u05d4\u05d6\u05de\u05e0\u05d5\u05ea: {len(d['refs'])} | +5 ZVK \u05dc\u05db\u05dc \u05d7\u05d1\u05e8")

@dp.message(F.text == "\U0001f4da \u05de\u05d3\u05e8\u05d9\u05db\u05d9\u05dd")
async def guides(m: types.Message):
    kb = IKM(inline_keyboard=[
        [IKB(text="\U0001f4b0 \u05de\u05d3\u05e8\u05d9\u05da @wallet", callback_data="i:ton")],
        [IKB(text="\U0001f4a1 \u05dc\u05de\u05d4 \u05d8\u05dc\u05d2\u05e8\u05dd?", callback_data="i:why")],
        [IKB(text="\u2753 FAQ", callback_data="i:faq")],
        [IKB(text="\U0001f4de \u05ea\u05de\u05d9\u05db\u05d4", callback_data="i:sup")],
    ])
    await m.answer("\U0001f4da \u05de\u05d3\u05e8\u05d9\u05db\u05d9\u05dd", reply_markup=kb)

@dp.callback_query(F.data == "i:ton")
async def iton(cb: types.CallbackQuery):
    await cb.message.answer(
        "\U0001f4b0 \u05de\u05d3\u05e8\u05d9\u05da @wallet\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "1\ufe0f\u20e3 \u05e4\u05ea\u05d7 @wallet\n2\ufe0f\u20e3 Buy \u2192 TON\n3\ufe0f\u20e3 \u05e9\u05dc\u05dd\n4\ufe0f\u20e3 TON \u05d1\u05d0\u05e8\u05e0\u05e7!\n\n\u05d1\u05dc\u05d9 \u05e2\u05de\u05dc\u05d5\u05ea \u05d1\u05e0\u05e7 | \u05de\u05d9\u05d9\u05d3\u05d9 | 24/7")
    await cb.answer()

@dp.callback_query(F.data == "i:why")
async def iwhy(cb: types.CallbackQuery):
    await cb.message.answer(
        "\U0001f4a1 \u05dc\u05de\u05d4 \u05d8\u05dc\u05d2\u05e8\u05dd > \u05d1\u05d9\u05d8?\n\n"
        "\u2705 \u05d2\u05dc\u05d5\u05d1\u05dc\u05d9 | \u2705 \u05d1\u05dc\u05d9 \u05d1\u05e0\u05e7 | \u2705 \u05de\u05d9\u05d9\u05d3\u05d9\n"
        "\u2705 0.01\u20aa \u05e2\u05de\u05dc\u05d4 | \u2705 24/7 | \u2705 \u05ea\u05e9\u05d5\u05d0\u05d4\n\n"
        "\u05db\u05dc\u05db\u05dc\u05d4 \u05db\u05e9\u05e8\u05d4, \u05dc\u05dc\u05d0 \u05d2\u05d6\u05dc.\n\"\u05d4\u05db\u05e1\u05e3 \u05e9\u05dc\u05da, \u05d4\u05d7\u05d5\u05e4\u05e9 \u05e9\u05dc\u05da\""
    )
    await cb.answer()

@dp.callback_query(F.data == "i:faq")
async def ifaq(cb: types.CallbackQuery):
    await cb.message.answer(
        "\u2753 FAQ\n\n"
        "Q: \u05db\u05de\u05d4 \u05e2\u05d5\u05dc\u05d4?\nA: 22.221\u20aa \u05d7\u05d3 \u05e4\u05e2\u05de\u05d9\n\n"
        "Q: \u05d0\u05d9\u05da \u05de\u05e9\u05dc\u05de\u05d9\u05dd?\nA: @wallet \u2192 Buy TON \u2192 Send\n\n"
        "Q: \u05d1\u05d8\u05d5\u05d7?\nA: \u05de\u05e4\u05ea\u05d7\u05d5\u05ea \u05e4\u05e8\u05d8\u05d9\u05d9\u05dd \u05dc\u05d0 \u05e0\u05e9\u05de\u05e8\u05d9\u05dd\n\n"
        "Q: \u05ea\u05de\u05d9\u05db\u05d4?\nA: /support"
    )
    await cb.answer()

@dp.callback_query(F.data == "i:sup")
async def isup(cb: types.CallbackQuery):
    await cb.message.answer(f"\U0001f4de \u05ea\u05de\u05d9\u05db\u05d4: {SUPPORT_PHONE}\n\U0001f4ac @SLH_AIR_bot\n\nSLH Investment House")
    await cb.answer()

@dp.message(F.text == "\U0001f4e4 \u05e9\u05d9\u05ea\u05d5\u05e3")
async def share(m: types.Message):
    link = f"https://t.me/SLH_AIR_bot?start={m.from_user.id}"
    await m.answer(SHARE_TEXT.replace("https://t.me/SLH_AIR_bot", link))

@dp.message(F.text == "\U0001f4b3 \u05d4\u05e4\u05e2\u05dc\u05d4")
@dp.message(Command("activate"))
async def activate(m: types.Message):
    if paid(m.from_user.id):
        await m.answer("\u2705 \u05de\u05d5\u05e4\u05e2\u05dc!"); return
    await m.answer(
        f"\U0001f48e SLH - \u05d4\u05e4\u05e2\u05dc\u05d4\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        f"\U0001f4b3 {ACTIVATION_ILS}\u20aa ({ACTIVATION_TON} TON)\n\n"
        "\u05de\u05d4 \u05de\u05e7\u05d1\u05dc\u05d9\u05dd:\n"
        "\U0001f4b0 \u05d0\u05e8\u05e0\u05e7 \u05de\u05dc\u05d0\n\U0001f4bc \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea 4%-65%\n\U0001f4e4 \u05d4\u05e2\u05d1\u05e8\u05d5\u05ea\n\U0001f3ae \u05d1\u05d5\u05e0\u05d5\u05e1\u05d9\u05dd\n"
        f"\U0001f381 +{SLH_REWARD} ZVK!\n\n"
        f"1\ufe0f\u20e3 \u05e4\u05ea\u05d7 @wallet\n2\ufe0f\u20e3 \u05e7\u05e0\u05d4 TON\n3\ufe0f\u20e3 \u05e9\u05dc\u05d7 {ACTIVATION_TON} TON \u05dc:\n{TON_WALLET}\n4\ufe0f\u20e3 \u05e6\u05d9\u05dc\u05d5\u05dd \u05de\u05e1\u05da \u05db\u05d0\u05df\n\n"
        f"\u2b50 {ACTIVATION_ILS}\u20aa = \u05d2\u05d9\u05e9\u05d4 \u05dc\u05db\u05dc \u05d4\u05de\u05e2\u05e8\u05db\u05ea!"
    )

# Commands
@dp.message(Command("share"))
async def share_cmd(m: types.Message):
    link = f"https://t.me/SLH_AIR_bot?start={m.from_user.id}"
    await m.answer(SHARE_TEXT.replace("https://t.me/SLH_AIR_bot", link))

@dp.message(Command("tonguide"))
async def tg(m): await iton(types.CallbackQuery(id="0", chat_instance="0", from_user=m.from_user, message=m))
@dp.message(Command("why"))
async def wh(m): await iwhy(types.CallbackQuery(id="0", chat_instance="0", from_user=m.from_user, message=m))
@dp.message(Command("faq"))
async def fq(m): await ifaq(types.CallbackQuery(id="0", chat_instance="0", from_user=m.from_user, message=m))
@dp.message(Command("support"))
async def sp(m): await m.answer(f"\U0001f4de \u05ea\u05de\u05d9\u05db\u05d4: {SUPPORT_PHONE}\n\U0001f4ac @SLH_AIR_bot\n\nSLH Investment House | SPARK IND")
@dp.message(Command("help"))
async def hp(m):
    await m.answer(
        "\u2753 SLH Investment House\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "\U0001f4ca \u05d4\u05e9\u05d5\u05e7 - 12 \u05de\u05d8\u05d1\u05e2\u05d5\u05ea, \u05e1\u05d5\u05d5\u05d0\u05e4, \u05d4\u05ea\u05e8\u05d0\u05d5\u05ea\n"
        "\U0001f4bc \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea - 4 \u05e4\u05e7\u05d3\u05d5\u05e0\u05d5\u05ea, 4%-65%\n"
        "\U0001f4b0 \u05d0\u05e8\u05e0\u05e7 - TON/BNB/SLH + \u05d4\u05e2\u05d1\u05e8\u05d5\u05ea\n"
        "\U0001f501 \u05de\u05e1\u05d7\u05e8 - \u05e1\u05d5\u05d5\u05d0\u05e4, Limit, \u05d4\u05ea\u05e8\u05d0\u05d5\u05ea\n\n"
        "\U0001f4b3 \u05d1\u05e0\u05e7:\n"
        "/deposit /mydeposits /withdraw /statement\n\n"
        "\U0001f4b1 \u05de\u05e1\u05d7\u05e8:\n"
        "/prices /swap /limit /orders /alert /portfolio\n\n"
        "\U0001f4b0 \u05d0\u05e8\u05e0\u05e7:\n"
        "/pay /send /mybalance /myid /gas\n\n"
        "\U0001f4da \u05e2\u05d5\u05d3:\n"
        "/share /faq /support /kyc /help\n\n"
        "SLH Investment House | SPARK IND"
    )

# PHOTO PAYMENT
@dp.message(F.photo)
async def photo(m: types.Message):
    uid = m.from_user.id; uname = m.from_user.username or ""
    fid = m.photo[-1].file_id
    await pay_db.create_payment(uid, uname, "expertnet", 0, "TON")
    await pay_db.submit_proof(uid, "expertnet", fid)
    await m.answer("\u2705 \u05d0\u05d9\u05e9\u05d5\u05e8 \u05d4\u05ea\u05e7\u05d1\u05dc!\n\u05de\u05de\u05ea\u05d9\u05df...")
    kb = IKM(inline_keyboard=[[IKB(text="\u2705", callback_data=f"ok:{uid}"), IKB(text="\u274c", callback_data=f"no:{uid}")]])
    try: await bot.send_photo(ADMIN_USER_ID, fid, caption=f"\U0001f4b3 @{uname} ({uid})", reply_markup=kb)
    except: pass

@dp.callback_query(F.data.startswith("ok:"))
async def ok(cb: types.CallbackQuery):
    if cb.from_user.id != ADMIN_USER_ID: return
    uid = int(cb.data.split(":")[1]); d = g(uid)
    d["paid"] = True; d["zvk"] += SLH_REWARD
    await save_paid_to_db(uid, cb.from_user.id)
    if HAS_LEDGER:
        try: await ensure_balance(uid, "ZVK"); await mint(uid, "ZVK", SLH_REWARD, "purchase")
        except: pass
    try: await bot.send_message(uid, f"\U0001f389 \u05de\u05d5\u05e4\u05e2\u05dc! +{SLH_REWARD} ZVK!\n\u05dc\u05d7\u05e5 \U0001f4bc \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea")
    except: pass
    await cb.message.edit_caption(caption=f"\u2705 {uid}")
    await cb.answer()

@dp.callback_query(F.data.startswith("no:"))
async def no(cb: types.CallbackQuery):
    if cb.from_user.id != ADMIN_USER_ID: return
    uid = int(cb.data.split(":")[1])
    try: await bot.send_message(uid, "\u274c \u05e0\u05d3\u05d7\u05d4. \u05e0\u05e1\u05d4 \u05e9\u05d5\u05d1.")
    except: pass
    await cb.message.edit_caption(caption=f"\u274c {uid}")
    await cb.answer()

# ═══════════════════════════════════
# BANKING COMMANDS
# ═══════════════════════════════════
@dp.message(Command("deposit"))
async def deposit_cmd(m: types.Message, command: CommandObject = None):
    """Start a real deposit. /deposit <plan> <amount>"""
    if not paid(m.from_user.id):
        await m.answer(lock_msg()); return
    if not HAS_BANK:
        await m.answer("\u274c Banking not available"); return
    if not command or not command.args:
        txt = "\U0001f4b3 \u05d4\u05e4\u05e7\u05d3\u05d4 \u05d0\u05de\u05d9\u05ea\u05d9\u05ea\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        for k, p in BANK_PLANS.items():
            txt += f"{p['name']}: {p['monthly']}% \u05d7\u05d5\u05d3\u05e9\u05d9 | \u05de\u05d9\u05e0\u05d9\u05de\u05d5\u05dd {p['min']} TON\n"
        txt += "\n\u05e9\u05d9\u05de\u05d5\u05e9: /deposit m1 10\n(\u05ea\u05d5\u05db\u05e0\u05d9\u05ea + \u05e1\u05db\u05d5\u05dd)"
        await m.answer(txt); return
    args = command.args.strip().split()
    plan_key = args[0]
    amount = float(args[1]) if len(args) > 1 else 0
    dep_id, err = await create_deposit(m.from_user.id, plan_key, amount)
    if err:
        await m.answer(f"\u274c {err}"); return
    plan = BANK_PLANS[plan_key]
    monthly_earn = amount * plan["monthly"] / 100
    await m.answer(
        f"\u2705 \u05d4\u05e4\u05e7\u05d3\u05d4 #{dep_id} \u05e0\u05d5\u05e6\u05e8\u05d4!\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        f"{plan['name']} | {amount} TON\n"
        f"\u05ea\u05e9\u05d5\u05d0\u05d4 \u05d7\u05d5\u05d3\u05e9\u05d9\u05ea: ~{monthly_earn:.2f} TON\n"
        f"\u05ea\u05e7\u05d5\u05e4\u05d4: {plan['lock']} \u05d9\u05de\u05d9\u05dd\n\n"
        "\U0001f4b3 \u05e9\u05dc\u05d7 TON \u05de-@wallet \u05dc\u05e7\u05e8\u05df \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea SLH:\n"
        f"<code>{TON_WALLET}</code>\n\n"
        "\u05d5\u05e9\u05dc\u05d7 \u05e6\u05d9\u05dc\u05d5\u05dd \u05de\u05e1\u05da \u05dc\u05d0\u05d9\u05e9\u05d5\u05e8.",
        parse_mode="HTML",
    )

@dp.message(Command("mydeposits"))
async def mydeposits_cmd(m: types.Message):
    if not paid(m.from_user.id):
        await m.answer(lock_msg()); return
    if not HAS_BANK: return
    deps = await get_user_deposits(m.from_user.id)
    if not deps:
        await m.answer("\u05d0\u05d9\u05df \u05d4\u05e4\u05e7\u05d3\u05d5\u05ea. /deposit \u05dc\u05d4\u05ea\u05d7\u05dc\u05d4!"); return
    txt = "\U0001f4cb \u05d4\u05d4\u05e4\u05e7\u05d3\u05d5\u05ea \u05e9\u05dc\u05da\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
    total = 0
    for d in deps:
        status_e = {
            "pending_payment": "\u23f3 \u05de\u05de\u05ea\u05d9\u05df \u05ea\u05e9\u05dc\u05d5\u05dd",
            "active": "\u2705 \u05e4\u05e2\u05d9\u05dc",
            "closed": "\u2705 \u05e0\u05e1\u05d2\u05e8",
        }.get(d["status"], d["status"])
        earned = d.get("earned", 0)
        total += float(d["amount"]) + earned
        txt += (
            f"#{d['id']} | {d['plan_key']} | {float(d['amount']):.2f} TON\n"
            f"  {status_e} | +{earned:.4f} TON\n"
            f"  \u05e2\u05d3: {str(d.get('end_date',''))[:10]}\n\n"
        )
    txt += f"\U0001f4b0 \u05e1\u05d4\"\u05db: {total:.4f} TON"
    await m.answer(txt)

@dp.message(Command("withdraw"))
async def withdraw_cmd(m: types.Message, command: CommandObject = None):
    if not paid(m.from_user.id):
        await m.answer(lock_msg()); return
    if not HAS_BANK: return
    if not command or not command.args:
        await m.answer(
            "\U0001f4b8 \u05de\u05e9\u05d9\u05db\u05d4\n\n"
            "\u05e9\u05d9\u05de\u05d5\u05e9: /withdraw <\u05de\u05e1\u05e4\u05e8 \u05d4\u05e4\u05e7\u05d3\u05d4> <\u05db\u05ea\u05d5\u05d1\u05ea TON>\n\n"
            "\u05d3\u05d5\u05d2\u05de\u05d4: /withdraw 1 UQDhfy...\n\n"
            "\u05dc\u05e8\u05e9\u05d9\u05de\u05d4: /mydeposits"
        ); return
    args = command.args.strip().split()
    if len(args) < 2:
        await m.answer("/withdraw <deposit_id> <ton_address>"); return
    dep_id = int(args[0])
    to_addr = args[1]
    wid, status = await request_withdrawal(m.from_user.id, dep_id, to_addr)
    if not wid:
        await m.answer(f"\u274c {status}"); return
    early_msg = " (\u05e2\u05de\u05dc\u05ea \u05de\u05e9\u05d9\u05db\u05d4 \u05de\u05d5\u05e7\u05d3\u05de\u05ea 5%)" if status == "early" else ""
    await m.answer(
        f"\u2705 \u05d1\u05e7\u05e9\u05ea \u05de\u05e9\u05d9\u05db\u05d4 #{wid} \u05e0\u05e9\u05dc\u05d7\u05d4!{early_msg}\n\n"
        "\u05de\u05de\u05ea\u05d9\u05df \u05dc\u05d0\u05d9\u05e9\u05d5\u05e8 \u05d0\u05d3\u05de\u05d9\u05df."
    )
    try:
        await bot.send_message(ADMIN_USER_ID,
            f"\U0001f4b8 \u05d1\u05e7\u05e9\u05ea \u05de\u05e9\u05d9\u05db\u05d4 #{wid}\n"
            f"User: {m.from_user.id}\n"
            f"Deposit: #{dep_id}\n"
            f"To: {to_addr}\n"
            f"Status: {status}")
    except: pass

@dp.message(Command("statement"))
async def statement_cmd(m: types.Message):
    if not paid(m.from_user.id):
        await m.answer(lock_msg()); return
    if not HAS_BANK: return
    stmt = await generate_statement(m.from_user.id, 30)
    bal = stmt.get("balance", {})
    avail = float(bal.get("available", 0)) if bal else 0
    locked = float(bal.get("locked", 0)) if bal else 0
    n_deps = len(stmt.get("deposits", []))
    n_wds = len(stmt.get("withdrawals", []))
    n_entries = len(stmt.get("entries", []))
    await m.answer(
        "\U0001f4cb \u05d3\u05e3 \u05d7\u05e9\u05d1\u05d5\u05df (30 \u05d9\u05d5\u05dd)\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        f"\U0001f4b0 \u05d6\u05de\u05d9\u05df: {avail:.4f} TON\n"
        f"\U0001f512 \u05e0\u05e2\u05d5\u05dc: {locked:.4f} TON\n"
        f"\U0001f4b0 \u05e1\u05d4\"\u05db: {avail + locked:.4f} TON\n\n"
        f"\U0001f4c8 \u05d4\u05e4\u05e7\u05d3\u05d5\u05ea: {n_deps}\n"
        f"\U0001f4b8 \u05de\u05e9\u05d9\u05db\u05d5\u05ea: {n_wds}\n"
        f"\U0001f4dd \u05ea\u05e0\u05d5\u05e2\u05d5\u05ea: {n_entries}\n\n"
        "SLH Investment House"
    )

@dp.message(Command("kyc"))
async def kyc_cmd(m: types.Message, command: CommandObject = None):
    if not HAS_BANK: return
    uid = m.from_user.id
    status = await get_kyc_status(uid)
    if status and status.get("status") == "approved":
        await m.answer("\u2705 \u05d6\u05d9\u05d4\u05d5\u05d9 \u05de\u05d0\u05d5\u05e9\u05e8!"); return
    if not command or not command.args:
        await m.answer(
            "\U0001f4cb KYC - \u05d6\u05d9\u05d4\u05d5\u05d9\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
            "\u05e9\u05dc\u05d1 1: /kyc <\u05e9\u05dd \u05de\u05dc\u05d0>\n"
            "\u05e9\u05dc\u05d1 2: \u05e9\u05dc\u05d7 \u05e6\u05d9\u05dc\u05d5\u05dd \u05ea.\u05d6. (\u05db\u05ea\u05de\u05d5\u05e0\u05d4)\n"
            "\u05e9\u05dc\u05d1 3: \u05d4\u05de\u05ea\u05df \u05dc\u05d0\u05d9\u05e9\u05d5\u05e8"
        ); return
    name = command.args.strip()
    await start_kyc(uid, name)
    await m.answer(f"\u2705 {name} \u05e0\u05e8\u05e9\u05dd!\n\u05e2\u05db\u05e9\u05d9\u05d5 \u05e9\u05dc\u05d7 \u05ea\u05de\u05d5\u05e0\u05ea \u05ea.\u05d6. (\u05db\u05ea\u05de\u05d5\u05e0\u05d4)")


# ADMIN
@dp.message(Command("admin"))
async def admin(m: types.Message):
    if m.from_user.id != ADMIN_USER_ID: return
    pc = sum(1 for d in users.values() if d.get("paid"))
    txt = f"\U0001f6e0 SLH Admin\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
    txt += f"\U0001f465 \u05de\u05e9\u05ea\u05de\u05e9\u05d9\u05dd: {len(users)} | \u05de\u05e9\u05dc\u05de\u05d9\u05dd: {pc}\n"
    if HAS_BANK:
        bs = await get_bank_stats()
        txt += (
            f"\n\U0001f3e6 \u05d1\u05e0\u05e7:\n"
            f"  \u05d4\u05e4\u05e7\u05d3\u05d5\u05ea \u05e4\u05e2\u05d9\u05dc\u05d5\u05ea: {bs['active_deposits']}\n"
            f"  \u05d4\u05e4\u05e7\u05d3\u05d5\u05ea \u05de\u05de\u05ea\u05d9\u05e0\u05d5\u05ea: {bs['pending_deposits']}\n"
            f"  \u05e1\u05d4\"\u05db \u05d4\u05e4\u05e7\u05d3\u05d5\u05ea: {bs['total_deposits_ton']:.2f} TON\n"
            f"  \u05de\u05e9\u05d9\u05db\u05d5\u05ea \u05de\u05de\u05ea\u05d9\u05e0\u05d5\u05ea: {bs['pending_withdrawals']}\n"
            f"  KYC \u05de\u05de\u05ea\u05d9\u05e0\u05d9\u05dd: {bs['pending_kyc']}\n"
            f"  \u05ea\u05e0\u05d5\u05e2\u05d5\u05ea \u05d9\u05d5\u05de\u05df: {bs['journal_entries']}\n"
        )
    txt += f"\n\U0001f4b0 \u05d0\u05e8\u05e0\u05e7: {TON_WALLET[:20]}...\n\n"
    txt += "\u05e4\u05e7\u05d5\u05d3\u05d5\u05ea \u05d0\u05d3\u05de\u05d9\u05df:\n"
    txt += "/approve_deposit <id>\n/approve_withdrawal <id>\n/approve_kyc <user_id>\n/pending"
    await m.answer(txt)

@dp.message(Command("pending"))
async def pending_cmd(m: types.Message):
    if m.from_user.id != ADMIN_USER_ID: return
    if not HAS_BANK: return
    deps = await get_all_deposits("pending_payment")
    if deps:
        txt = "\u23f3 \u05d4\u05e4\u05e7\u05d3\u05d5\u05ea \u05de\u05de\u05ea\u05d9\u05e0\u05d5\u05ea:\n\n"
        for d in deps[:10]:
            txt += f"#{d['id']} | {d['user_id']} | {float(d['amount']):.2f} TON | {d['plan_key']}\n"
        txt += "\n/approve_deposit <id>"
    else:
        txt = "\u2705 \u05d0\u05d9\u05df \u05d4\u05e4\u05e7\u05d3\u05d5\u05ea \u05de\u05de\u05ea\u05d9\u05e0\u05d5\u05ea"
    await m.answer(txt)

@dp.message(Command("approve_deposit"))
async def approve_dep_cmd(m: types.Message, command: CommandObject = None):
    if m.from_user.id != ADMIN_USER_ID: return
    if not HAS_BANK or not command or not command.args: return
    dep_id = int(command.args.strip())
    ok, tx = await confirm_deposit(dep_id, m.from_user.id)
    if ok:
        await m.answer(f"\u2705 \u05d4\u05e4\u05e7\u05d3\u05d4 #{dep_id} \u05d0\u05d5\u05e9\u05e8\u05d4! TX: {tx}")
    else:
        await m.answer(f"\u274c {tx}")

@dp.message(Command("approve_withdrawal"))
async def approve_wd_cmd(m: types.Message, command: CommandObject = None):
    if m.from_user.id != ADMIN_USER_ID: return
    if not HAS_BANK or not command or not command.args: return
    parts = command.args.strip().split()
    wid = int(parts[0])
    tx_hash = parts[1] if len(parts) > 1 else None
    ok, msg = await approve_withdrawal(wid, m.from_user.id, tx_hash)
    await m.answer(f"\u2705 {msg}" if ok else f"\u274c {msg}")

@dp.message(Command("approve_kyc"))
async def approve_kyc_cmd(m: types.Message, command: CommandObject = None):
    if m.from_user.id != ADMIN_USER_ID: return
    if not HAS_BANK or not command or not command.args: return
    uid = int(command.args.strip())
    await approve_kyc(uid, m.from_user.id)
    await m.answer(f"\u2705 KYC {uid} \u05d0\u05d5\u05e9\u05e8!")

@dp.message(Command("resetkey"))
async def rk(m: types.Message):
    uid = m.from_user.id
    encrypted_keys.pop(uid, None); pending_pins.pop(uid, None)
    await m.answer("\U0001f511 \u05de\u05e4\u05ea\u05d7 \u05e0\u05de\u05d7\u05e7")


# ═══════════════════════════════════
# PRICES (12 COINS)
# ═══════════════════════════════════
@dp.message(Command("prices"))
async def prices_cmd(m: types.Message):
    if not HAS_MARKET:
        await m.answer("\u274c"); return
    txt = await get_full_prices_text()
    now_s = datetime.now().strftime("%H:%M %d/%m/%Y")
    await m.answer(f"{txt}\n\n\u23f0 {now_s}\n\U0001f3e6 SLH Investment House")


# ═══════════════════════════════════
# MY ID (for transfers)
# ═══════════════════════════════════
@dp.message(Command("myid"))
async def myid_cmd(m: types.Message):
    uid = m.from_user.id
    await m.answer(
        f"\U0001f194 \u05d4\u05de\u05d6\u05d4\u05d4 \u05e9\u05dc\u05da:\n<code>{uid}</code>\n\n"
        "\u05e9\u05ea\u05e3 \u05e2\u05dd \u05d7\u05d1\u05e8\u05d9\u05dd \u05db\u05d3\u05d9 \u05e9\u05d9\u05d5\u05db\u05dc\u05d5 \u05dc\u05e9\u05dc\u05d5\u05d7 \u05dc\u05da\n"
        "/pay <\u05de\u05d6\u05d4\u05d4> <\u05e1\u05db\u05d5\u05dd> SLH",
        parse_mode="HTML",
    )


# ═══════════════════════════════════
# PORTFOLIO
# ═══════════════════════════════════
@dp.message(Command("portfolio"))
async def portfolio_cmd(m: types.Message):
    uid = m.from_user.id
    if not paid(uid):
        await m.answer(lock_msg()); return

    lines = ["\U0001f4ca \u05ea\u05d9\u05e7 \u05d4\u05e9\u05e7\u05e2\u05d5\u05ea", "\u2500" * 20, ""]

    # Bank deposits
    dep_val = 0.0
    dep_earn = 0.0
    if HAS_BANK:
        deps = await get_user_deposits(uid)
        active = [x for x in deps if x["status"] == "active"]
        dep_val = sum(float(x["amount"]) for x in active)
        dep_earn = sum(x.get("earned", 0) for x in active)
        bal = await bank_balance(uid)
        lines.append(f"\U0001f3e6 \u05d7\u05e9\u05d1\u05d5\u05df \u05d1\u05e0\u05e7:")
        lines.append(f"  \u05d6\u05de\u05d9\u05df: {bal['available']:.4f} TON")
        lines.append(f"  \u05e0\u05e2\u05d5\u05dc: {bal['locked']:.4f} TON")
        if active:
            lines.append(f"  \u05e8\u05d5\u05d5\u05d7 \u05e6\u05d1\u05d5\u05e8: +{dep_earn:.4f} TON")
        lines.append("")

    # Internal ledger
    if HAS_LEDGER:
        await ensure_balance(uid, "SLH")
        await ensure_balance(uid, "ZVK")
        bals = await get_internal_balances(uid)
        slh_b = bals.get("SLH", 0)
        zvk_b = bals.get("ZVK", 0)
        lines.append(f"\U0001f48e SLH: {slh_b:.4f}")
        lines.append(f"\U0001f3ae ZVK: {zvk_b:.0f}")
        lines.append("")

    # Market value
    if HAS_MARKET and dep_val > 0:
        prices = await get_prices()
        if prices and prices.get("TON"):
            ton_usd = prices["TON"]["usd"]
            ton_ils = prices["TON"]["ils"]
            total_ton = dep_val + dep_earn
            lines.append(f"\U0001f4b1 \u05e9\u05d5\u05d5\u05d9 \u05e9\u05d5\u05e7:")
            lines.append(f"  {total_ton:.4f} TON = ${total_ton * ton_usd:.2f} / {total_ton * ton_ils:.1f}\u20aa")
            lines.append("")

    lines.append("SLH Investment House")
    await m.answer("\n".join(lines))


# ═══════════════════════════════════
# PRICE ALERTS
# ═══════════════════════════════════
@dp.message(Command("alert"))
async def alert_cmd(m: types.Message, command: CommandObject = None):
    if not paid(m.from_user.id):
        await m.answer(lock_msg()); return
    if not HAS_MARKET:
        await m.answer("\u274c"); return
    if not command or not command.args:
        uid = m.from_user.id
        my_alerts = price_alerts.get(uid, [])
        txt = "\U0001f514 \u05d4\u05ea\u05e8\u05d0\u05d5\u05ea \u05de\u05d7\u05d9\u05e8\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        if my_alerts:
            for i, a in enumerate(my_alerts, 1):
                d_txt = "\u2b06\ufe0f" if a["direction"] == "above" else "\u2b07\ufe0f"
                txt += f"{i}. {a['coin']} {d_txt} ${a['target']:,.2f}\n"
            txt += "\n"
        txt += (
            "\u05e9\u05d9\u05de\u05d5\u05e9:\n"
            "/alert BTC above 100000\n"
            "/alert TON below 3\n"
            "/alert ETH above 4000\n\n"
            "\u05de\u05d8\u05d1\u05e2\u05d5\u05ea: BTC ETH TON BNB SOL DOGE XRP ADA DOT AVAX MATIC LINK"
        )
        await m.answer(txt); return

    args = command.args.strip().upper().split()
    if len(args) < 3:
        await m.answer("/alert <COIN> <above/below> <PRICE>"); return
    coin = args[0]
    direction = args[1].lower()
    if direction not in ("above", "below"):
        await m.answer("\u274c above \u05d0\u05d5 below"); return
    try:
        target = float(args[2].replace(",", ""))
    except ValueError:
        await m.answer("\u274c \u05de\u05d7\u05d9\u05e8 \u05dc\u05d0 \u05ea\u05e7\u05d9\u05df"); return

    uid = m.from_user.id
    if uid not in price_alerts:
        price_alerts[uid] = []
    price_alerts[uid].append({"coin": coin, "direction": direction, "target": target, "created": datetime.now().isoformat()})
    d_txt = "\u05de\u05e2\u05dc" if direction == "above" else "\u05de\u05ea\u05d7\u05ea"
    await m.answer(f"\u2705 \u05d4\u05ea\u05e8\u05d0\u05d4 \u05e0\u05e7\u05d1\u05e2\u05d4!\n{coin} {d_txt} ${target:,.2f}")


# ═══════════════════════════════════
# SWAP QUOTES (STON.fi)
# ═══════════════════════════════════
STONFI_API = "https://api.ston.fi"

async def get_swap_quote(from_token, to_token, amount):
    """Get swap quote from STON.fi."""
    if not HAS_AIOHTTP:
        return None
    try:
        url = f"{STONFI_API}/v1/swap/simulate"
        params = {"offer_address": from_token, "ask_address": to_token, "units": str(int(amount * 1e9))}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
    except Exception as e:
        log.warning("STON.fi quote failed: %s", e)
    return None


@dp.message(Command("swap"))
async def swap_cmd(m: types.Message, command: CommandObject = None):
    if not paid(m.from_user.id):
        await m.answer(lock_msg()); return
    if not command or not command.args:
        await m.answer(
            "\U0001f501 \u05e1\u05d5\u05d5\u05d0\u05e4 DEX\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
            "\u05e7\u05d1\u05dc \u05d4\u05e6\u05e2\u05ea \u05de\u05d7\u05d9\u05e8 \u05de-STON.fi:\n"
            "/swap 10 TON USDT\n/swap 100 USDT TON\n\n"
            "\u26a0\ufe0f \u05d4\u05e6\u05e2\u05ea \u05de\u05d7\u05d9\u05e8 \u05d1\u05dc\u05d1\u05d3 - \u05dc\u05d1\u05d9\u05e6\u05d5\u05e2 \u05d4\u05e9\u05ea\u05de\u05e9 \u05d1-STON.fi",
            reply_markup=IKM(inline_keyboard=[
                [IKB(text="\U0001f310 STON.fi", url="https://app.ston.fi/swap")],
            ]),
        ); return

    args = command.args.strip().upper().split()
    if len(args) < 3:
        await m.answer("/swap <\u05e1\u05db\u05d5\u05dd> <\u05de\u05de\u05d8\u05d1\u05e2> <\u05dc\u05de\u05d8\u05d1\u05e2>"); return

    amount_s, from_t, to_t = args[0], args[1], args[2]
    try:
        amount = float(amount_s)
    except ValueError:
        await m.answer("\u274c"); return

    # Show price-based estimate
    if HAS_MARKET:
        prices = await get_prices()
        from_p = prices.get(from_t, {}).get("usd", 0) if prices else 0
        to_p = prices.get(to_t, {}).get("usd", 0) if prices else 0
        if from_p and to_p:
            est = amount * from_p / to_p
            rate = from_p / to_p
            await m.answer(
                f"\U0001f501 \u05e1\u05d5\u05d5\u05d0\u05e4 {from_t} \u2192 {to_t}\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
                f"\U0001f4b0 {amount} {from_t} = ~{est:.4f} {to_t}\n"
                f"\U0001f4b1 1 {from_t} = {rate:.6f} {to_t}\n\n"
                f"\u26a0\ufe0f \u05d4\u05e6\u05e2\u05ea \u05de\u05d7\u05d9\u05e8 \u05de\u05e9\u05d5\u05e2\u05e8\u05ea\u05d9\u05ea.\n"
                "\u05dc\u05d1\u05d9\u05e6\u05d5\u05e2 \u05d1\u05e4\u05d5\u05e2\u05dc \u05d4\u05e9\u05ea\u05de\u05e9 \u05d1-STON.fi:",
                reply_markup=IKM(inline_keyboard=[
                    [IKB(text="\U0001f310 \u05d1\u05e6\u05e2 \u05d1-STON.fi", url="https://app.ston.fi/swap")],
                ]),
            )
            return

    await m.answer(f"\u274c \u05dc\u05d0 \u05e0\u05d9\u05ea\u05df \u05dc\u05d7\u05e9\u05d1 {from_t}/{to_t}")


# ═══════════════════════════════════
# LIMIT ORDERS (notification-based)
# ═══════════════════════════════════
@dp.message(Command("limit"))
async def limit_cmd(m: types.Message, command: CommandObject = None):
    global _order_counter
    if not paid(m.from_user.id):
        await m.answer(lock_msg()); return
    if not command or not command.args:
        await m.answer(
            "\U0001f4cb \u05d4\u05d6\u05de\u05e0\u05ea Limit\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
            "\u05e7\u05d1\u05dc \u05d4\u05ea\u05e8\u05d0\u05d4 \u05db\u05e9\u05d4\u05de\u05d7\u05d9\u05e8 \u05de\u05d2\u05d9\u05e2:\n\n"
            "/limit buy TON 3.50 10\n"
            "/limit sell BTC 100000 0.5\n\n"
            "/orders - \u05e8\u05e9\u05d9\u05de\u05ea \u05d4\u05d6\u05de\u05e0\u05d5\u05ea"
        ); return

    args = command.args.strip().upper().split()
    if len(args) < 4:
        await m.answer("/limit <buy/sell> <COIN> <PRICE> <AMOUNT>"); return

    side = args[0].lower()
    if side not in ("buy", "sell"):
        await m.answer("\u274c buy \u05d0\u05d5 sell"); return
    coin = args[1]
    try:
        target_price = float(args[2].replace(",", ""))
        amount = float(args[3].replace(",", ""))
    except ValueError:
        await m.answer("\u274c \u05de\u05e1\u05e4\u05e8 \u05dc\u05d0 \u05ea\u05e7\u05d9\u05df"); return

    uid = m.from_user.id
    _order_counter += 1
    oid = _order_counter
    if uid not in limit_orders:
        limit_orders[uid] = []
    limit_orders[uid].append({
        "id": oid, "coin": coin, "side": side,
        "target_price": target_price, "amount": amount,
        "created": datetime.now().isoformat(),
    })
    side_h = "\u05e7\u05e0\u05d9\u05d9\u05d4" if side == "buy" else "\u05de\u05db\u05d9\u05e8\u05d4"
    await m.answer(
        f"\u2705 \u05d4\u05d6\u05de\u05e0\u05d4 #{oid} \u05e0\u05e7\u05d1\u05e2\u05d4!\n\n"
        f"{side_h}: {amount} {coin} \u05d1-${target_price:,.2f}\n\n"
        "\u05ea\u05e7\u05d1\u05dc \u05d4\u05ea\u05e8\u05d0\u05d4 \u05db\u05e9\u05d4\u05de\u05d7\u05d9\u05e8 \u05d9\u05d2\u05d9\u05e2."
    )


@dp.message(Command("orders"))
async def orders_cmd(m: types.Message):
    uid = m.from_user.id
    my_orders = limit_orders.get(uid, [])
    my_alerts_list = price_alerts.get(uid, [])

    if not my_orders and not my_alerts_list:
        await m.answer("\u05d0\u05d9\u05df \u05d4\u05d6\u05de\u05e0\u05d5\u05ea \u05d0\u05d5 \u05d4\u05ea\u05e8\u05d0\u05d5\u05ea \u05e4\u05e2\u05d9\u05dc\u05d5\u05ea.\n/limit \u05d0\u05d5 /alert \u05dc\u05d4\u05ea\u05d7\u05dc\u05d4"); return

    txt = "\U0001f4cb \u05d4\u05d4\u05d6\u05de\u05e0\u05d5\u05ea \u05e9\u05dc\u05d9\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
    if my_orders:
        txt += "\U0001f4b1 Limit Orders:\n"
        for o in my_orders:
            side_e = "\U0001f7e2" if o["side"] == "buy" else "\U0001f534"
            txt += f"  {side_e} #{o['id']} {o['side']} {o['amount']} {o['coin']} @ ${o['target_price']:,.2f}\n"
        txt += "\n"
    if my_alerts_list:
        txt += "\U0001f514 \u05d4\u05ea\u05e8\u05d0\u05d5\u05ea:\n"
        for a in my_alerts_list:
            d_e = "\u2b06\ufe0f" if a["direction"] == "above" else "\u2b07\ufe0f"
            txt += f"  {d_e} {a['coin']} {a['direction']} ${a['target']:,.2f}\n"

    await m.answer(txt)


# ═══════════════════════════════════
# TRANSFER CALLBACKS
# ═══════════════════════════════════
@dp.callback_query(F.data == "w:transfer_slh")
async def w_transfer_slh(cb: types.CallbackQuery):
    await cb.message.answer(
        "\U0001f4e4 \u05d4\u05e2\u05d1\u05e8\u05ea SLH\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "/pay <\u05de\u05d6\u05d4\u05d4> <\u05e1\u05db\u05d5\u05dd> SLH\n\n"
        "\u05d3\u05d5\u05d2\u05de\u05d4: /pay 123456 50 SLH\n\n"
        "\u05dc\u05e7\u05d1\u05dc\u05ea \u05de\u05d6\u05d4\u05d4: \u05d1\u05e7\u05e9 \u05de\u05d4\u05d7\u05d1\u05e8 \u05dc\u05e9\u05dc\u05d5\u05d7 /myid"
    )
    await cb.answer()

@dp.callback_query(F.data == "w:transfer_zvk")
async def w_transfer_zvk(cb: types.CallbackQuery):
    await cb.message.answer(
        "\U0001f4e4 \u05d4\u05e2\u05d1\u05e8\u05ea ZVK\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "/pay <\u05de\u05d6\u05d4\u05d4> <\u05e1\u05db\u05d5\u05dd> ZVK\n\n"
        "\u05d3\u05d5\u05d2\u05de\u05d4: /pay 123456 10 ZVK\n\n"
        "\u05dc\u05e7\u05d1\u05dc\u05ea \u05de\u05d6\u05d4\u05d4: \u05d1\u05e7\u05e9 \u05de\u05d4\u05d7\u05d1\u05e8 \u05dc\u05e9\u05dc\u05d5\u05d7 /myid"
    )
    await cb.answer()


# ═══════════════════════════════════
# ENHANCED MARKET CALLBACKS
# ═══════════════════════════════════
@dp.callback_query(F.data == "mkt:prices")
async def mkt_prices(cb: types.CallbackQuery):
    if HAS_MARKET:
        txt = await get_full_prices_text()
        now_s = datetime.now().strftime("%H:%M %d/%m/%Y")
        await cb.message.answer(f"{txt}\n\n\u23f0 {now_s}")
    else:
        await cb.message.answer("\u274c")
    await cb.answer()

@dp.callback_query(F.data == "mkt:swap")
async def mkt_swap(cb: types.CallbackQuery):
    await cb.message.answer(
        "\U0001f501 \u05e1\u05d5\u05d5\u05d0\u05e4 DEX\n\n"
        "/swap 10 TON USDT\n/swap 100 USDT TON\n/swap 0.01 BTC ETH",
        reply_markup=IKM(inline_keyboard=[
            [IKB(text="\U0001f310 STON.fi", url="https://app.ston.fi/swap")],
        ]),
    )
    await cb.answer()

@dp.callback_query(F.data == "mkt:orders")
async def mkt_orders(cb: types.CallbackQuery):
    await cb.message.answer("/limit buy TON 3.50 10\n/alert BTC above 100000\n/orders")
    await cb.answer()

@dp.callback_query(F.data == "mkt:portfolio")
async def mkt_portfolio(cb: types.CallbackQuery):
    await cb.message.answer("/portfolio")
    await cb.answer()


# ═══════════════════════════════════
# BACKGROUND TASK: CHECK ALERTS & LIMITS
# ═══════════════════════════════════
async def check_alerts_task():
    """Background task checking price alerts and limit orders every 60s."""
    while True:
        try:
            await asyncio.sleep(60)
            if not HAS_MARKET:
                continue
            prices = await get_prices()
            if not prices:
                continue

            # Check price alerts
            to_remove = []
            for uid, alerts in list(price_alerts.items()):
                for alert in alerts[:]:
                    coin_price = prices.get(alert["coin"], {}).get("usd", 0)
                    if not coin_price:
                        continue
                    triggered = False
                    if alert["direction"] == "above" and coin_price >= alert["target"]:
                        triggered = True
                    elif alert["direction"] == "below" and coin_price <= alert["target"]:
                        triggered = True
                    if triggered:
                        d_txt = "\u2b06\ufe0f \u05e2\u05dc\u05d4 \u05de\u05e2\u05dc" if alert["direction"] == "above" else "\u2b07\ufe0f \u05d9\u05e8\u05d3 \u05de\u05ea\u05d7\u05ea"
                        try:
                            await bot.send_message(uid,
                                f"\U0001f514 \u05d4\u05ea\u05e8\u05d0\u05d4!\n\n"
                                f"{alert['coin']} {d_txt} ${alert['target']:,.2f}\n"
                                f"\u05de\u05d7\u05d9\u05e8 \u05e0\u05d5\u05db\u05d7\u05d9: ${coin_price:,.2f}")
                        except: pass
                        alerts.remove(alert)

            # Check limit orders
            for uid, orders in list(limit_orders.items()):
                for order in orders[:]:
                    coin_price = prices.get(order["coin"], {}).get("usd", 0)
                    if not coin_price:
                        continue
                    triggered = False
                    if order["side"] == "buy" and coin_price <= order["target_price"]:
                        triggered = True
                    elif order["side"] == "sell" and coin_price >= order["target_price"]:
                        triggered = True
                    if triggered:
                        side_h = "\u05e7\u05e0\u05d9\u05d9\u05d4" if order["side"] == "buy" else "\u05de\u05db\u05d9\u05e8\u05d4"
                        try:
                            await bot.send_message(uid,
                                f"\U0001f4b1 \u05d4\u05d6\u05de\u05e0\u05ea Limit #{order['id']} \u05d4\u05d2\u05d9\u05e2\u05d4!\n\n"
                                f"{side_h}: {order['amount']} {order['coin']} @ ${order['target_price']:,.2f}\n"
                                f"\u05de\u05d7\u05d9\u05e8 \u05e0\u05d5\u05db\u05d7\u05d9: ${coin_price:,.2f}\n\n"
                                "\u05dc\u05d1\u05d9\u05e6\u05d5\u05e2 \u05d4\u05e9\u05ea\u05de\u05e9 \u05d1-STON.fi",
                                reply_markup=IKM(inline_keyboard=[
                                    [IKB(text="\U0001f310 STON.fi", url="https://app.ston.fi/swap")],
                                ]))
                        except: pass
                        orders.remove(order)
        except Exception as e:
            log.warning("Alert check error: %s", e)


async def main():
    await pay_db.init_schema()
    await load_paid_users_from_db()
    log.info("=" * 40)
    log.info("SLH Investment House")
    log.info("=" * 40)
    asyncio.create_task(check_alerts_task())
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
