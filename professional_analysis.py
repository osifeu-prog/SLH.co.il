import pandas as pd
import numpy as np
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

returns = []  # will store percentage returns (as decimals)
for idx, row in df.iterrows():
    addr = row['address']
    old_price = row['price_usd']
    new_price = get_current_price(addr)
    if new_price and old_price:
        ret = (new_price - old_price) / old_price
        returns.append(ret)
        print(f"{row['symbol']}: {ret:.1%}")
    else:
        print(f"{row['symbol']}: no current price")
    time.sleep(0.5)

if not returns:
    print("No valid returns collected.")
    exit()

returns = np.array(returns)
wins = returns[returns > 0]
losses = returns[returns < 0]
total_trades = len(returns)
win_rate = len(wins) / total_trades
avg_win = wins.mean() if len(wins) > 0 else 0
avg_loss = losses.mean() if len(losses) > 0 else 0
rr_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else 0
expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
total_pnl = returns.sum()
cagr = (1 + total_pnl) ** (365 / 1) - 1 if total_pnl > -1 else -1  # assuming 1 day holding period, annualized
risk_free_rate = 0.02  # 2% annual
sharpe = (returns.mean() * 252 - risk_free_rate) / (returns.std() * np.sqrt(252)) if returns.std() != 0 else 0

# Sortino: only downside deviation
downside_returns = returns[returns < 0]
downside_std = downside_returns.std() if len(downside_returns) > 0 else returns.std()
sortino = (returns.mean() * 252 - risk_free_rate) / (downside_std * np.sqrt(252)) if downside_std != 0 else 0

# Max Drawdown
cumulative = (1 + returns).cumprod()
running_max = cumulative.cummax()
drawdown = (cumulative - running_max) / running_max
max_drawdown = drawdown.min()

# Calmar Ratio
calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0

print("\n" + "="*60)
print("PROFESSIONAL PERFORMANCE METRICS")
print("="*60)
print(f"Total Trades:                {total_trades}")
print(f"Win Rate:                    {win_rate:.1%}")
print(f"Avg Win:                     {avg_win:.1%}")
print(f"Avg Loss:                    {avg_loss:.1%}")
print(f"Risk/Reward Ratio:           {rr_ratio:.2f}")
print(f"Expectancy per Trade:        {expectancy:.2%}")
print(f"Total PnL (over period):     {total_pnl:.1%}")
print(f"CAGR (annualized):           {cagr:.1%}")
print(f"Sharpe Ratio (annual):       {sharpe:.2f}")
print(f"Sortino Ratio (annual):      {sortino:.2f}")
print(f"Max Drawdown:                {max_drawdown:.1%}")
print(f"Calmar Ratio:                {calmar:.2f}")
print("="*60)

# Optional: Save report
report = {
    'date': datetime.now().isoformat(),
    'total_trades': total_trades,
    'win_rate': win_rate,
    'avg_win': avg_win,
    'avg_loss': avg_loss,
    'rr_ratio': rr_ratio,
    'expectancy': expectancy,
    'total_pnl': total_pnl,
    'cagr': cagr,
    'sharpe': sharpe,
    'sortino': sortino,
    'max_drawdown': max_drawdown,
    'calmar': calmar
}
pd.DataFrame([report]).to_csv('performance_report.csv', index=False)
print("\n✅ Report saved to performance_report.csv")
