import pandas as pd
import numpy as np
import requests
import time
import csv
import os
from datetime import datetime, timedelta

def fetch_new_token_addresses(limit=30):
    url = f"https://api.dexpaprika.com/networks/bsc/tokens/filter?sort=created_at&order=desc&limit={limit}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            tokens = data.get('results', [])
            return [t.get('address') for t in tokens if t.get('address')]
        else:
            return []
    except:
        return []

def get_token_details(address):
    url = f"https://api.dexpaprika.com/networks/bsc/tokens/{address}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            summary = data.get('summary', {})
            return {
                'address': address,
                'symbol': data.get('symbol'),
                'price_usd': summary.get('price_usd'),
                'liquidity_usd': summary.get('liquidity_usd'),
                'volume_usd_24h': summary.get('24h', {}).get('volume_usd'),
                'collected_at': datetime.utcnow().isoformat()
            }
        else:
            return None
    except:
        return None

def collect_tokens(limit=30):
    addresses = fetch_new_token_addresses(limit)
    tokens = []
    for addr in addresses:
        details = get_token_details(addr)
        if details and details.get('price_usd') and details['price_usd'] > 0:
            tokens.append(details)
            print(f"✓ {details['symbol']}: ${details['price_usd']:.6f}")
        else:
            print(f"✗ {addr[:10]}... no price")
        time.sleep(0.5)
    return tokens

if __name__ == '__main__':
    print("=== Collecting fresh tokens for 24h backtest ===\n")
    tokens = collect_tokens(limit=30)
    if not tokens:
        print("No tokens collected.")
        exit()
    
    # Save with timestamp
    filename = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df = pd.DataFrame(tokens)
    df.to_csv(filename, index=False)
    print(f"\nSaved {len(tokens)} tokens to {filename}")
    print("Run this script again tomorrow to calculate actual PnL.")
