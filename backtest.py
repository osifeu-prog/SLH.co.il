import requests
import time
import json

def fetch_new_pairs(chain='bsc', limit=10):
    """מביא את המטבעות החדשים ביותר ב-DEX לפי DexScreener"""
    url = f"https://api.dexscreener.com/token-profiles/latest/{chain}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return [item['tokenAddress'] for item in data[:limit]]
        else:
            print(f"API error: {resp.status_code}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == '__main__':
    tokens = fetch_new_pairs('bsc', 10)
    print(f"Found {len(tokens)} new tokens:")
    for token in tokens:
        print(token)