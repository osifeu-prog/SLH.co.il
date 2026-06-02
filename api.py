from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

class CalcRequest(BaseModel):
    users: int = 20000
    profit_per_user: float = 15
    investor_share: float = 10
    investment: float = 50000

@app.post("/api/calculate")
async def calculate(data: CalcRequest):
    net_monthly = data.users * data.profit_per_user
    investor_monthly = net_monthly * (data.investor_share / 100)
    months_to_break_even = data.investment / investor_monthly if investor_monthly > 0 else 0
    return {
        "net_monthly": net_monthly,
        "investor_monthly": investor_monthly,
        "months_to_break_even": round(months_to_break_even, 1)
    }

@app.get("/api/wallet/{user_id}")
async def get_wallet(user_id: int):
    conn = sqlite3.connect("slh_local.db")
    cur = conn.cursor()
    cur.execute("SELECT ils, ton, usdt FROM wallets WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return {"ils": row[0] if row else 0, "ton": row[1] if row else 0, "usdt": row[2] if row else 0}

@app.get("/api/products")
async def get_products():
    conn = sqlite3.connect("slh_local.db")
    cur = conn.cursor()
    cur.execute("SELECT p.id, p.name, p.price, p.currency, m.name as merchant FROM products p JOIN merchants m ON m.id = p.merchant_id")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "price": r[2], "currency": r[3], "merchant": r[4]} for r in rows]
