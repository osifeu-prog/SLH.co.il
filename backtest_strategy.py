import backtrader as bt
import pandas as pd
from datetime import datetime

# --------------------------------------
# 1. אסטרטגיה פשוטה (RSI)
# --------------------------------------
class RSIStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)

    def next(self):
        if not self.position:
            if self.rsi[0] < self.params.rsi_oversold:
                self.buy()
        else:
            if self.rsi[0] > self.params.rsi_overbought:
                self.sell()

# --------------------------------------
# 2. טעינת נתונים (מקובץ CSV או יצירת דמה)
# --------------------------------------
def load_data_from_csv(filename='tokens_history.csv'):
    """טוען נתונים מקובץ CSV (אם קיים)"""
    try:
        df = pd.read_csv(filename)
        # נניח שיש עמודות: date, close, open, high, low, volume
        # אם אין – ניצור נתונים לדוגמה
        if 'date' not in df.columns:
            df['date'] = pd.date_range(start='2024-01-01', periods=len(df))
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        data = bt.feeds.PandasData(dataname=df)
        return data
    except Exception as e:
        print(f"לא נמצא קובץ CSV אמיתי, יוצר נתוני דמה: {e}")
        # נתוני דמה
        dates = pd.date_range(start='2024-01-01', periods=100)
        df = pd.DataFrame({
            'open': [100 + i for i in range(100)],
            'high': [102 + i for i in range(100)],
            'low': [98 + i for i in range(100)],
            'close': [101 + i for i in range(100)],
            'volume': [1000000] * 100
        }, index=dates)
        return bt.feeds.PandasData(dataname=df)

# --------------------------------------
# 3. הרצת Backtest
# --------------------------------------
if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.addstrategy(RSIStrategy)

    data = load_data_from_csv('tokens_history.csv')
    cerebro.adddata(data)

    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% עמלה

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.plot()