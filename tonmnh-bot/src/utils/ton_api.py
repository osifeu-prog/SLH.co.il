# utils/ton_api.py
import logging
import aiohttp
from config import TONCENTER_API_KEY, RPC_URL

async def get_ton_balance(address: str) -> float | None:
    if not TONCENTER_API_KEY:
        logging.error("TONCENTER_API_KEY missing")
        return None
    url = f"{RPC_URL}/getAddressInformation"
    params = {'address': address, 'api_key': TONCENTER_API_KEY}
    logging.info(f"Request URL: {url}")
    logging.info(f"Request Params: {params}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                logging.info(f"Response status: {resp.status}")
                if resp.status != 200:
                    logging.error(f"HTTP error {resp.status}")
                    return None
                data = await resp.json()
                logging.info(f"Response data: {data}")
                if data.get('ok'):
                    balance_nano = int(data['result']['balance'])
                    return balance_nano / 1_000_000_000
                else:
                    logging.error(f"TON Center error: {data}")
                    return None
    except Exception as e:
        logging.exception(f"Exception in get_ton_balance: {e}")
        return None
