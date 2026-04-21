import requests
import time
import csv
from datetime import datetime

def fetch_new_token_addresses(limit=20):
    url = f"https://api.dexpaprika.com/networks/bsc/tokens/filter?sort=created_at&order=desc&limit={limit}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            tokens = data.get('results', [])
            return [t.get('address') for t in tokens if t.get('address')]
        else:
            print(f"Failed: {r.status_code}")
            return []
    except Exception as e:
        print(f"Error: {e}")
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
                'name': data.get('name'),
                'price_usd': summary.get('price_usd'),
                'liquidity_usd': summary.get('liquidity_usd'),
                'volume_usd_24h': summary.get('24h', {}).get('volume_usd'),
                'txns_24h': summary.get('24h', {}).get('txns'),
                'created_at': data.get('added_at'),
                'collected_at': datetime.utcnow().isoformat()
            }
        else:
            return None
    except Exception as e:
        print(f"Error {address[:10]}: {e}")
        return None

def save_to_csv(data, filename='tokens_history.csv'):
    if not data:
        return
    keys = data[0].keys()
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        if f.tell() == 0:
            writer.writeheader()
        writer.writerows(data)
    print(f"Saved {len(data)} tokens to {filename}")

if __name__ == '__main__':
    print("Fetching new BSC tokens...")
    addresses = fetch_new_token_addresses(20)
    print(f"Found {len(addresses)} addresses.")
    
    details_list = []
    for addr in addresses:
        details = get_token_details(addr)
        if details and details.get('price_usd') and details['price_usd'] > 0:
            details_list.append(details)
            print(f"✓ {details['symbol']}: ${details['price_usd']:.6f}")
        else:
            print(f"✗ {addr[:10]}... no price")
        time.sleep(0.5)
    
    if details_list:
        save_to_csv(details_list)
        print(f"\n✅ Done. Collected {len(details_list)} tokens.")
    else:
        print("❌ No data collected.")