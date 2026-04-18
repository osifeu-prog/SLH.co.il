"""
Blockchain balance checker for SLH
- TON balance via TonCenter API
- BNB + SLH balance via BSC public RPC
"""
import os
import logging
import asyncio
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

log = logging.getLogger("slh.chain")

TON_API = "https://toncenter.com/api/v2"
TON_KEY = os.getenv("TONCENTER_API_KEY", "fab6ade5108d472959112b2c2daba07c669826b221def532d8d38d7088cf65cd")
BSC_RPC = "https://bsc-dataseed.binance.org/"
SLH_CONTRACT = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"


async def get_ton_balance(address):
    """Get TON balance for address."""
    if not HAS_AIOHTTP or not address:
        return None
    try:
        url = f"{TON_API}/getAddressBalance?address={address}&api_key={TON_KEY}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if data.get("ok"):
                    nano = int(data["result"])
                    return nano / 1e9  # Convert from nanoTON
    except Exception as e:
        log.warning("TON balance error: %s", e)
    return None


async def get_bnb_balance(address):
    """Get BNB balance via BSC RPC."""
    if not HAS_AIOHTTP or not address:
        return None
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": 1,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(BSC_RPC, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                hex_val = data.get("result", "0x0")
                return int(hex_val, 16) / 1e18
    except Exception as e:
        log.warning("BNB balance error: %s", e)
    return None


async def get_slh_balance(wallet_address):
    """Get SLH token balance on BSC."""
    if not HAS_AIOHTTP or not wallet_address:
        return None
    try:
        # ERC20 balanceOf(address) function signature
        func_sig = "0x70a08231"
        padded_addr = wallet_address.lower().replace("0x", "").zfill(64)
        data_hex = func_sig + padded_addr

        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{"to": SLH_CONTRACT, "data": data_hex}, "latest"],
            "id": 1,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(BSC_RPC, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                result = await resp.json()
                hex_val = result.get("result", "0x0")
                raw = int(hex_val, 16)
                return raw / 1e18  # Assuming 18 decimals
    except Exception as e:
        log.warning("SLH balance error: %s", e)
    return None


async def get_all_balances(ton_addr=None, bnb_addr=None):
    """Get all balances in parallel."""
    results = {"ton": None, "bnb": None, "slh": None}

    tasks = []
    if ton_addr:
        tasks.append(("ton", get_ton_balance(ton_addr)))
    if bnb_addr:
        tasks.append(("bnb", get_bnb_balance(bnb_addr)))
        tasks.append(("slh", get_slh_balance(bnb_addr)))

    for key, coro in tasks:
        try:
            results[key] = await coro
        except Exception:
            pass

    return results
