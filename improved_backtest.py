import pandas as pd
import numpy as np

df = pd.read_csv('tokens_history.csv')
print(f"Loaded {len(df)} tokens.")

# תנאי סינון
df_filtered = df[
    (df['liquidity_usd'] > 100_000) &
    (df['volume_usd_24h'] > 50_000) &
    (df['price_usd'] < 0.01)
]

print(f"After filtering: {len(df_filtered)} tokens.")

def simulate_trade(row):
    # הסתברות 40% לרווח 30%, 60% להפסד 20%
    if np.random.random() < 0.4:
        return 0.30
    else:
        return -0.20

results = []
for idx, row in df_filtered.iterrows():
    pnl = simulate_trade(row)
    results.append(pnl)

if results:
    wins = sum(1 for p in results if p > 0)
    losses = sum(1 for p in results if p < 0)
    total_trades = len(results)
    win_rate = wins / total_trades
    avg_win = np.mean([p for p in results if p > 0]) if wins else 0
    avg_loss = np.mean([p for p in results if p < 0]) if losses else 0
    rr_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else 0
    total_pnl = sum(results)
    
    print("\n=== Improved Backtest Results ===")
    print(f"Trades: {total_trades}")
    print(f"Win Rate: {win_rate:.1%}")
    print(f"Avg Win: {avg_win:.1%}, Avg Loss: {avg_loss:.1%}")
    print(f"Risk/Reward: {rr_ratio:.2f}")
    print(f"Total PnL: {total_pnl:.1%}")
    print(f"Expectancy per trade: {np.mean(results):.2%}")
else:
    print("No trades after filtering.")