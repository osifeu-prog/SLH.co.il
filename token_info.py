import requests, time
r = requests.get("https://api.dexpaprika.com/networks/bsc/tokens/0x4c3c902bfe07857c7d6abd5e983847a6e4247f16")
if r.status_code == 200:
    data = r.json()
    print("Symbol:", data.get("symbol"))
    print("Price USD:", data.get("summary", {}).get("price_usd"))
    print("Liquidity USD:", data.get("summary", {}).get("liquidity_usd"))
else:
    print("Error", r.status_code)
