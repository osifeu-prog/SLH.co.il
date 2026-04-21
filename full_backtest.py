import pandas as pd
import numpy as np
import requests
import time
import csv
from datetime import datetime

# --------------------------------------
# 1. שליפת טוקנים חדשים מ-DexPaprika
# --------------------------------------
def fetch_new_token_addresses(limit=30):
    url = f"https://api.dexpaprika.com/networks/bsc/tokens/filter?sort=created_at&order=desc&limit={limit}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            tokens = data.get('results', [])
            return [t.get('address') for t in tokens if t.get('address')]
        else:
            print(f"Failed to fetch token list: {r.status_code}")
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
                'price_usd': summary.get('price_usd'),
                'liquidity_usd': summary.get('liquidity_usd'),
                'volume_usd_24h': summary.get('24h', {}).get('volume_usd'),
                'txns_24h': summary.get('24h', {}).get('txns'),
                'collected_at': datetime.utcnow().isoformat()
            }
        else:
            return None
    except Exception as e:
        print(f"Error {address[:10]}: {e}")
        return None

# --------------------------------------
# 2. הרצת איסוף ושמירה
# --------------------------------------
def collect_tokens(limit=30):
    addresses = fetch_new_token_addresses(limit)
    if not addresses:
        print("No addresses found.")
        return []
    
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

# --------------------------------------
# 3. סימולציית מסחר (משופרת)
# --------------------------------------
def simulate_trade(row, liquidity_threshold=50000, volume_threshold=25000):
    liquidity = row.get('liquidity_usd')
    volume = row.get('volume_usd_24h')
    if (liquidity and liquidity > liquidity_threshold) and (volume and volume > volume_threshold):
        # הסתברות 40% לרווח 30%, 60% להפסד 20%
        if np.random.random() < 0.4:
            return 0.30
        else:
            return -0.20
    return None

# --------------------------------------
# 4. ניתוח תוצאות
# --------------------------------------
def analyze_results(pnls):
    if not pnls:
        return None
    wins = sum(1 for p in pnls if p > 0)
    losses = sum(1 for p in pnls if p < 0)
    total = len(pnls)
    win_rate = wins / total if total > 0 else 0
    avg_win = np.mean([p for p in pnls if p > 0]) if wins > 0 else 0
    avg_loss = np.mean([p for p in pnls if p < 0]) if losses > 0 else 0
    rr_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else 0
    total_pnl = sum(pnls)
    expectancy = np.mean(pnls) if pnls else 0
    return {
        'trades': total,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'rr_ratio': rr_ratio,
        'total_pnl': total_pnl,
        'expectancy': expectancy
    }

# --------------------------------------
# 5. הרצה ראשית
# --------------------------------------
if __name__ == '__main__':
    print("=== 1. Collecting tokens from DexPaprika ===\n")
    tokens = collect_tokens(limit=30)
    if not tokens:
        print("No tokens collected. Exiting.")
        exit()
    
    print(f"\n=== 2. Running simulation on {len(tokens)} tokens ===\n")
    df = pd.DataFrame(tokens)
    pnls = []
    for idx, row in df.iterrows():
        pnl = simulate_trade(row, liquidity_threshold=50000, volume_threshold=25000)
        if pnl is not None:
            pnls.append(pnl)
    
    stats = analyze_results(pnls)
    if stats:
        print("\n=== Backtest Results ===")
        print(f"Total trades: {stats['trades']}")
        print(f"Wins: {stats['wins']}, Losses: {stats['losses']}")
        print(f"Win Rate: {stats['win_rate']:.1%}")
        print(f"Average Win: {stats['avg_win']:.1%}, Average Loss: {stats['avg_loss']:.1%}")
        print(f"Risk/Reward Ratio: {stats['rr_ratio']:.2f}")
        print(f"Total PnL: {stats['total_pnl']:.1%}")
        print(f"Expectancy per trade: {stats['expectancy']:.2%}")
    else:
        print("No trades triggered. Try lowering thresholds.")
