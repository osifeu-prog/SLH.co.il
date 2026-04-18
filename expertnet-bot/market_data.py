"""
Real Market Data - CoinGecko free API
12 coins tracked: BTC, ETH, TON, BNB, SOL, DOGE, XRP, ADA, DOT, AVAX, MATIC, LINK
"""
import logging
import time

log = logging.getLogger("slh.market")

_cache = {}
_cache_ttl = 60  # 60 seconds

try:
    import aiohttp
    HAS_HTTP = True
except ImportError:
    HAS_HTTP = False

COINGECKO_URL = "https://api.coingecko.com/api/v3"

# CoinGecko ID -> (symbol, emoji)
COIN_MAP = {
    "bitcoin": ("BTC", "\U0001f7e1"),
    "ethereum": ("ETH", "\U0001f535"),
    "the-open-network": ("TON", "\U0001f4a0"),
    "binancecoin": ("BNB", "\U0001f7e0"),
    "solana": ("SOL", "\U0001f7e3"),
    "dogecoin": ("DOGE", "\U0001f436"),
    "ripple": ("XRP", "\u26aa"),
    "cardano": ("ADA", "\U0001f534"),
    "polkadot": ("DOT", "\U0001f7e4"),
    "avalanche-2": ("AVAX", "\u2764\ufe0f"),
    "matic-network": ("MATIC", "\U0001f7e3"),
    "chainlink": ("LINK", "\U0001f517"),
}

COIN_IDS = ",".join(COIN_MAP.keys())

# Reverse: symbol -> coingecko_id
SYMBOL_TO_ID = {v[0]: k for k, v in COIN_MAP.items()}


async def get_prices():
    """Get all coin prices in USD and ILS."""
    if not HAS_HTTP:
        return None

    now = time.time()
    if _cache.get("prices") and now - _cache.get("prices_time", 0) < _cache_ttl:
        return _cache["prices"]

    try:
        url = f"{COINGECKO_URL}/simple/price?ids={COIN_IDS}&vs_currencies=usd,ils"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    prices = {}
                    for cg_id, (symbol, _emoji) in COIN_MAP.items():
                        coin_data = data.get(cg_id, {})
                        prices[symbol] = {
                            "usd": coin_data.get("usd", 0),
                            "ils": coin_data.get("ils", 0),
                        }
                    _cache["prices"] = prices
                    _cache["prices_time"] = now
                    return prices
                elif resp.status == 429:
                    log.warning("CoinGecko rate limited")
                    return _cache.get("prices")
    except Exception as e:
        log.warning("Price fetch failed: %s", e)

    return _cache.get("prices")


def _fmt_price(usd):
    """Format price based on magnitude."""
    if usd >= 1000:
        return f"${usd:,.0f}"
    elif usd >= 1:
        return f"${usd:.2f}"
    else:
        return f"${usd:.4f}"


async def get_market_summary():
    """Get formatted market summary - major coins."""
    prices = await get_prices()
    if not prices:
        return None

    lines = []
    for cg_id, (symbol, emoji) in COIN_MAP.items():
        p = prices.get(symbol, {})
        usd = p.get("usd", 0)
        ils = p.get("ils", 0)
        if usd == 0:
            continue
        usd_s = _fmt_price(usd)
        if ils >= 1000:
            ils_s = f"{ils:,.0f}"
        elif ils >= 1:
            ils_s = f"{ils:.1f}"
        else:
            ils_s = f"{ils:.4f}"
        lines.append(f"{emoji} {symbol}: {usd_s} ({ils_s}\u20aa)")

    return "\n".join(lines)


async def get_full_prices_text():
    """Full 12-coin price table for /prices command."""
    prices = await get_prices()
    if not prices:
        return "\u26a0\ufe0f \u05de\u05d7\u05d9\u05e8\u05d9\u05dd \u05dc\u05d0 \u05d6\u05de\u05d9\u05e0\u05d9\u05dd"

    major = ["BTC", "ETH", "TON", "BNB", "SOL"]
    alts = ["DOGE", "XRP", "ADA", "DOT", "AVAX", "MATIC", "LINK"]

    lines = ["\U0001f4ca \u05de\u05d7\u05d9\u05e8\u05d9\u05dd \u05d7\u05d9\u05d9\u05dd", "\u2500" * 20, ""]
    lines.append("\U0001f451 \u05de\u05d8\u05d1\u05e2\u05d5\u05ea \u05de\u05d5\u05d1\u05d9\u05dc\u05d5\u05ea:")
    for sym in major:
        p = prices.get(sym, {})
        if p.get("usd"):
            emoji = dict((v[0], v[1]) for v in COIN_MAP.values()).get(sym, "")
            lines.append(f"  {emoji} {sym}: {_fmt_price(p['usd'])} | {p['ils']:.1f}\u20aa")

    lines.append("")
    lines.append("\U0001f4a1 Altcoins:")
    for sym in alts:
        p = prices.get(sym, {})
        if p.get("usd"):
            emoji = dict((v[0], v[1]) for v in COIN_MAP.values()).get(sym, "")
            usd_s = _fmt_price(p["usd"])
            ils_s = f"{p['ils']:.2f}" if p["ils"] < 10 else f"{p['ils']:.1f}"
            lines.append(f"  {emoji} {sym}: {usd_s} | {ils_s}\u20aa")

    return "\n".join(lines)


async def get_single_price(symbol):
    """Get a single coin's USD price."""
    prices = await get_prices()
    if prices and symbol in prices:
        return prices[symbol].get("usd", 0)
    return 0


async def ton_to_ils():
    """Get TON/ILS rate."""
    prices = await get_prices()
    if prices and prices.get("TON"):
        return prices["TON"].get("ils", 14.8)
    return 14.8
