import requests
import time

def fetch_new_pairs(limit=10):
    """מביא את המטבעות החדשים ביותר ברשת BSC מ-DexPaprika (חינמי, ללא מפתח)"""
    url = f"https://api.dexpaprika.com/networks/bsc/tokens/filter?sort_by=created_at&sort_dir=desc&limit={limit}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if 'results' in data:
                return [item['address'] for item in data['results'] if 'address' in item]
            else:
                print("Unexpected response format")
                return []
        else:
            print(f"API error: {resp.status_code}")
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
