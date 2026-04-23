import requests
import pandas as pd
import numpy as np
from datetime import datetime
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL")

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 100
    rsi = np.zeros_like(prices)
    rsi[:period] = np.nan
    rsi[period] = 100 - 100 / (1 + rs)
    
    for i in range(period+1, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0
        else:
            upval = 0
            downval = -delta
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 100
        rsi[i] = 100 - 100 / (1 + rs)
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    exp1 = pd.Series(prices).ewm(span=fast, adjust=False).mean()
    exp2 = pd.Series(prices).ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]

async def get_btc_prices():
    """Fetch BTC prices from Binance"""
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=100"
    response = requests.get(url)
    data = response.json()
    prices = [float(candle[4]) for candle in data]  # Close prices
    return prices

async def check_signals():
    """Check for trading signals"""
    prices = await get_btc_prices()
    
    if len(prices) < 50:
        return {"error": "Not enough data"}
    
    rsi = calculate_rsi(prices)
    last_rsi = rsi[-1]
    macd_line, signal_line, histogram = calculate_macd(prices)
    
    signals = []
    
    # RSI signals
    if last_rsi < 30:
        signals.append({"indicator": "RSI", "signal": "BUY", "reason": f"Oversold (RSI={last_rsi:.1f})", "strength": "high"})
    elif last_rsi > 70:
        signals.append({"indicator": "RSI", "signal": "SELL", "reason": f"Overbought (RSI={last_rsi:.1f})", "strength": "high"})
    elif last_rsi < 40:
        signals.append({"indicator": "RSI", "signal": "BUY", "reason": f"Approaching oversold (RSI={last_rsi:.1f})", "strength": "medium"})
    elif last_rsi > 60:
        signals.append({"indicator": "RSI", "signal": "SELL", "reason": f"Approaching overbought (RSI={last_rsi:.1f})", "strength": "medium"})
    
    # MACD signals
    if macd_line > signal_line and histogram > 0:
        signals.append({"indicator": "MACD", "signal": "BUY", "reason": "Bullish crossover", "strength": "high"})
    elif macd_line < signal_line and histogram < 0:
        signals.append({"indicator": "MACD", "signal": "SELL", "reason": "Bearish crossover", "strength": "high"})
    
    return {
        "timestamp": datetime.now().isoformat(),
        "btc_price": prices[-1],
        "rsi": round(last_rsi, 1),
        "macd": {"line": round(macd_line, 2), "signal": round(signal_line, 2), "histogram": round(histogram, 2)},
        "signals": signals
    }

async def save_signal_to_db(signal_data):
    """Save signal to database"""
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS trading_signals (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP,
            btc_price DECIMAL(12,2),
            rsi DECIMAL(5,1),
            signals JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    await conn.execute(
        "INSERT INTO trading_signals (timestamp, btc_price, rsi, signals) VALUES ($1, $2, $3, $4)",
        signal_data["timestamp"], signal_data["btc_price"], signal_data["rsi"], 
        json.dumps(signal_data["signals"])
    )
    await conn.close()

if __name__ == "__main__":
    import asyncio
    import json
    result = asyncio.run(check_signals())
    print(json.dumps(result, indent=2, ensure_ascii=False))
