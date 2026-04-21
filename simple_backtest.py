import pandas as pd
import numpy as np

# --------------------------------------
# 1. טעינת הנתונים שלך
# --------------------------------------
try:
    df = pd.read_csv('tokens_history.csv')
    print(f"Loaded {len(df)} tokens from CSV.")
except Exception as e:
    print(f"Error loading CSV: {e}")
    exit()

# נבדוק שיש את העמודות הנחוצות
required_cols = ['price_usd', 'liquidity_usd']
if not all(col in df.columns for col in required_cols):
    print("Missing required columns. Found:", df.columns.tolist())
    exit()

# --------------------------------------
# 2. סימולציית מסחר פשוטה
# --------------------------------------
def simulate_trade(row):
    liquidity = row['liquidity_usd']
    if pd.notna(liquidity) and liquidity > 100_000:
        # symulate outcome: 40% chance of +30% profit, 60% chance of -20% loss
        if np.random.random() < 0.4:
            pnl = 0.30   # +30%
            return 'win', pnl
        else:
            pnl = -0.20  # -20%
            return 'loss', pnl
    return 'skip', 0.0

results = []
for idx, row in df.iterrows():
    outcome, pnl = simulate_trade(row)
    if outcome != 'skip':
        results.append(pnl)

# --------------------------------------
# 3. חישוב סטטיסטיקות
# --------------------------------------
if results:
    wins = sum(1 for p in results if p > 0)
    losses = sum(1 for p in results if p < 0)
    total_trades = len(results)
    win_rate = wins / total_trades if total_trades > 0 else 0
    avg_win = np.mean([p for p in results if p > 0]) if wins > 0 else 0
    avg_loss = np.mean([p for p in results if p < 0]) if losses > 0 else 0
    rr_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else 0
    total_pnl = sum(results)
    
    print("\n=== Backtest Results ===")
    print(f"Total trades: {total_trades}")
    print(f"Wins: {wins}, Losses: {losses}")
    print(f"Win Rate: {win_rate:.1%}")
    print(f"Average Win: {avg_win:.1%}, Average Loss: {avg_loss:.1%}")
    print(f"Risk/Reward Ratio: {rr_ratio:.2f}")
    print(f"Total PnL (assuming equal position size): {total_pnl:.1%}")
    print(f"Expectancy per trade: {np.mean(results):.2%}")
else:
    print("No trades triggered (no token with liquidity > 100k).")