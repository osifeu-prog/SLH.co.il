import requests
import time
import statistics

def get_trending_tokens():
    url = "https://api.geckoterminal.com/api/v2/networks/bsc/trending_pools"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            tokens = []
            for item in data.get("data", []):
                attrs = item.get("attributes", {})
                token = attrs.get("token", {})
                tokens.append({
                    "address": token.get("address"),
                    "symbol": token.get("symbol"),
                    "name": token.get("name"),
                    "price_usd": float(token.get("price_usd", 0)),
                    "liquidity_usd": float(attrs.get("liquidity_usd", 0)),
                    "volume_usd_24h": float(attrs.get("volume_usd", {}).get("h24", 0))
                })
            return tokens
        else:
            print(f"API error {resp.status_code}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    print("=== טרנדים חמים ב-BSC ===\n")
    tokens = get_trending_tokens()[:5]
    for t in tokens:
        print(f"{t['symbol']} ({t['name']})")
        print(f"  מחיר: ${t['price_usd']:.6f}")
        print(f"  נזילות: ${t['liquidity_usd']:,.0f}")
        print(f"  נפח 24h: ${t['volume_usd_24h']:,.0f}")
        print("-" * 40)
