import requests
import time

def fetch_new_pairs(limit=10):
    """מביא את המטבעות החדשים ביותר ברשת BSC מ-DexPaprika (חינמי, ללא מפתח)"""
    # DexPaprika API – אין צורך במפתח
    url = f"https://api.dexpaprika.com/v1/tokens?network=bsc&sort=created_at&order=desc&limit={limit}"
    
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            # מחזיר רשימה של כתובות חוזה
            if 'data' in data and isinstance(data['data'], list):
                return [item['address'] for item in data['data'] if 'address' in item]
            else:
                print(f"Unexpected response format: {data.keys() if isinstance(data, dict) else type(data)}")
                return []
        else:
            print(f"API error: {resp.status_code} - {resp.text[:200]}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == '__main__':
    print("Fetching new BSC tokens from DexPaprika...")
    tokens = fetch_new_pairs(10)
    print(f"Found {len(tokens)} tokens:")
    for token in tokens:
        print(f"  - {token}")