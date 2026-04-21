import requests
import time
import csv
from datetime import datetime

def get_token_details(token_address):
    url = f"https://api.dexpaprika.com/networks/bsc/tokens/{token_address}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            summary = data.get('summary', {})
            return {
                'address': token_address,
                'symbol': data.get('symbol'),
                'price_usd': summary.get('price_usd'),
                'liquidity_usd': summary.get('liquidity_usd'),
                'volume_24h': summary.get('24h', {}).get('volume_usd'),
                'created_at': data.get('added_at')
            }
        else:
            return None
    except:
        return None

# רשימת כתובות לדוגמה (החלף בכתובות אמיתיות)
test_addresses = [
    "0x4c3c902bfe07857c7d6abd5e983847a6e4247f16",
    "0xf3dfad315321eb786e0617641df808697b38253b"
]

print("בודק טוקנים...")
for addr in test_addresses:
    details = get_token_details(addr)
    if details:
        print(f"{details['symbol']}: ${details['price_usd']:.6f}, נזילות: ${details['liquidity_usd']:,.0f}")
    else:
        print(f"שגיאה ב-{addr[:10]}...")
    time.sleep(0.5)