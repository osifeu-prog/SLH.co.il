# -*- coding: utf-8 -*-
import requests
import time
import statistics

def fetch_new_pairs(limit=10):
    """????? ?????? ?? ?????? ????? ?-BSC"""
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
    """????? ???? ???? (????, ?????? ???')"""
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
    print("=== ??? 1: ????? ?????? ????? ===\n")
    tokens = fetch_new_pairs(5)  # ???? 5 ??????
    print(f"????? {len(tokens)} ??????.\n")
    
    print("=== ??? 2: ????? ????? ===\n")
    all_details = []
    for addr in tokens:
        details = get_token_details(addr)
        if details:
            all_details.append(details)
            print(f"????: {details['symbol']} ({details['name']})")
            print(f"  ????: ${details['price_usd']:.6f}" if details['price_usd'] else "  ????: N/A")
            print(f"  ??????: ${details['liquidity_usd']:,.0f}" if details['liquidity_usd'] else "  ??????: N/A")
            print(f"  ??? 24h: ${details['volume_24h']:,.0f}" if details['volume_24h'] else "  ??? 24h: N/A")
            print("-" * 40)
        time.sleep(0.5)
    
    # === ??? 3: ????? ????? (Backtest ????) ===
    print("\n=== ??? 3: ????? ????? ===")
    prices = [d['price_usd'] for d in all_details if d.get('price_usd') is not None]
    if prices:
        avg_price = statistics.mean(prices)
        print(f"???? ?????: ${avg_price:.6f}")
        print(f"???? ???????: ${min(prices):.6f}")
        print(f"???? ???????: ${max(prices):.6f}")
        print(f"????? ???: ${statistics.stdev(prices):.6f}")
    else:
        print("??? ????? ???? ?????.")


