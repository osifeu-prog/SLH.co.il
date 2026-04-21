import requests
import time
import statistics

def fetch_new_pairs(limit=10):
    """שליפת כתובות של טוקנים חדשים ב-BSC"""
    url = f"https://api.dexpaprika.com/networks/bsc/tokens/filter?sort_by=created_at&sort_dir=desc&limit={limit}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if 'results' in data:
                return [item['address'] for item in data['results'] if 'address' in item]
            else:
                return []
        else:
            return []
    except:
        return []

def get_token_details(token_address):
    """שליפת פרטי טוקן (מחיר, נזילות וכו')"""
    url = f"https://api.dexpaprika.com/v1/tokens/bsc/{token_address}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                'address': token_address,
                'name': data.get('name'),
                'symbol': data.get('symbol'),
                'price_usd': data.get('price_usd'),
                'liquidity_usd': data.get('liquidity_usd'),
                'volume_24h': data.get('volume_24h'),
                'created_at': data.get('created_at'),
            }
        else:
            return None
    except:
        return None

if __name__ == '__main__':
    print("=== שלב 1: שליפת טוקנים חדשים ===\n")
    tokens = fetch_new_pairs(5)  # ניקח 5 לדוגמה
    print(f"מצאתי {len(tokens)} טוקנים.\n")
    
    print("=== שלב 2: שליפת פרטים ===\n")
    all_details = []
    for addr in tokens:
        details = get_token_details(addr)
        if details:
            all_details.append(details)
            print(f"טוקן: {details['symbol']} ({details['name']})")
            print(f"  מחיר: ${details['price_usd']:.6f}" if details['price_usd'] else "  מחיר: N/A")
            print(f"  נזילות: ${details['liquidity_usd']:,.0f}" if details['liquidity_usd'] else "  נזילות: N/A")
            print(f"  נפח 24h: ${details['volume_24h']:,.0f}" if details['volume_24h'] else "  נפח 24h: N/A")
            print("-" * 40)
        time.sleep(0.5)
    
    # === שלב 3: ניתוח בסיסי (Backtest פשוט) ===
    print("\n=== שלב 3: ניתוח בסיסי ===")
    prices = [d['price_usd'] for d in all_details if d.get('price_usd') is not None]
    if prices:
        avg_price = statistics.mean(prices)
        print(f"מחיר ממוצע: ${avg_price:.6f}")
        print(f"מחיר מינימלי: ${min(prices):.6f}")
        print(f"מחיר מקסימלי: ${max(prices):.6f}")
        print(f"סטיית תקן: ${statistics.stdev(prices):.6f}")
    else:
        print("אין נתוני מחיר להצגה.")