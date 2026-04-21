import pandas as pd
import requests
import time
import glob
from datetime import datetime

def get_current_price(address):
    url = f"https://api.dexpaprika.com/networks/bsc/tokens/{address}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            summary = data.get('summary', {})
            return summary.get('price_usd')
        else:
            return None
    except:
        return None

# Find latest backtest file
files = glob.glob("backtest_*.csv")
if not files:
    print("No backtest file found.")
    exit()

latest = max(files)
df = pd.read_csv(latest)
print(f"Loaded {len(df)} tokens from {latest}")

results = []
for idx, row in df.iterrows():
    addr = row['address']
    old_price = row['price_usd']
    new_price = get_current_price(addr)
    if new_price and old_price:
        pct_change = (new_price - old_price) / old_price
        results.append(pct_change)
        print(f"{row['symbol']}: {pct_change:.1%}")
    else:
        print(f"{row['symbol']}: no current price")
    time.sleep(0.5)

if results:
    wins = sum(1 for p in results if p > 0)
    losses = sum(1 for p in results if p < 0)
    win_rate = wins / len(results) if results else 0
    avg_win = sum(p for p in results if p > 0) / wins if wins else 0
    avg_loss = sum(p for p in results if p < 0) / losses if losses else 0
    rr_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else 0
    total_pnl = sum(results)
    
    print("\n=== REAL BACKTEST RESULTS ===")
    print(f"Tokens analyzed: {len(results)}")
    print(f"Wins: {wins}, Losses: {losses}")
    print(f"Win Rate: {win_rate:.1%}")
    print(f"Average Win: {avg_win:.1%}, Average Loss: {avg_loss:.1%}")
    print(f"Risk/Reward Ratio: {rr_ratio:.2f}")
    print(f"Total PnL: {total_pnl:.1%}")
    print(f"Expectancy per trade: {total_pnl/len(results):.2%}")
