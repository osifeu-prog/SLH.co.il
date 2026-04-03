from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import sqlite3
import os
import json

app = FastAPI(title="SLH Airdrop API", version="2.0")

# ====================
# MODELS
# ====================
class UserRegister(BaseModel):
    telegram_id: str
    username: str
    first_name: str
    phone: Optional[str] = None

class WalletSubmit(BaseModel):
    telegram_id: str
    wallet_address: str
    wallet_type: str = "TON"

class TransactionSubmit(BaseModel):
    telegram_id: str
    transaction_hash: str
    amount: float
    currency: str = "TON"

class AdminLogin(BaseModel):
    admin_key: str

# ====================
# DATABASE SETUP
# ====================
def init_database():
    """מאתחל את מסד הנתונים"""
    conn = sqlite3.connect('data/airdrop.db')
    cursor = conn.cursor()
    
    # טבלת משתמשים
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            username TEXT,
            first_name TEXT,
            phone TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # טבלת ארנקים
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT,
            wallet_address TEXT UNIQUE,
            wallet_type TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
        )
    ''')
    
    # טבלת עסקאות
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT,
            transaction_hash TEXT UNIQUE,
            amount REAL,
            currency TEXT,
            status TEXT DEFAULT 'pending',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confirmed_at TIMESTAMP,
            tokens_awarded INTEGER DEFAULT 0,
            FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
        )
    ''')
    
    # טבלת סטטיסטיקות
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_users INTEGER DEFAULT 0,
            total_transactions INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            total_ton_received REAL DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# ====================
# DATABASE FUNCTIONS
# ====================
def get_db_connection():
    conn = sqlite3.connect('data/airdrop.db')
    conn.row_factory = sqlite3.Row
    return conn

# ====================
# API ENDPOINTS
# ====================
@app.post("/api/users/register")
async def register_user(user: UserRegister):
    """רושם משתמש חדש"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO users (telegram_id, username, first_name, phone)
            VALUES (?, ?, ?, ?)
        ''', (user.telegram_id, user.username, user.first_name, user.phone))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            return {"status": "success", "message": "User registered", "user_id": user.telegram_id}
        else:
            return {"status": "exists", "message": "User already exists"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/users/submit_wallet")
async def submit_wallet(wallet: WalletSubmit):
    """מקבל כתובת ארנק"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # בדוק אם המשתמש קיים
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (wallet.telegram_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # הוסף את הארנק
        cursor.execute('''
            INSERT OR REPLACE INTO wallets (telegram_id, wallet_address, wallet_type)
            VALUES (?, ?, ?)
        ''', (wallet.telegram_id, wallet.wallet_address, wallet.wallet_type))
        
        conn.commit()
        
        return {
            "status": "success", 
            "message": "Wallet saved",
            "wallet": wallet.wallet_address[:10] + "..."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/users/submit_transaction")
async def submit_transaction(transaction: TransactionSubmit):
    """מקבל עסקת תשלום"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # בדוק אם המשתמש קיים
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (transaction.telegram_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # הוסף את העסקה
        cursor.execute('''
            INSERT INTO transactions (telegram_id, transaction_hash, amount, currency, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (transaction.telegram_id, transaction.transaction_hash, transaction.amount, transaction.currency))
        
        # עדכן סטטיסטיקות
        cursor.execute('''
            INSERT OR REPLACE INTO stats (id, total_users, total_transactions, total_ton_received)
            VALUES (1, 
                (SELECT COUNT(*) FROM users),
                (SELECT COUNT(*) FROM transactions),
                (SELECT SUM(amount) FROM transactions WHERE currency = 'TON')
            )
        ''')
        
        conn.commit()
        
        # שלח התראה למנהל
        admin_alert = {
            "user": transaction.telegram_id,
            "transaction": transaction.transaction_hash[:20] + "...",
            "amount": transaction.amount,
            "time": datetime.now().isoformat()
        }
        
        return {
            "status": "success", 
            "message": "Transaction received",
            "transaction_id": transaction.transaction_hash,
            "tokens_pending": 1000
        }
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Transaction already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/users/{telegram_id}/status")
async def get_user_status(telegram_id: str):
    """מחזיר סטטוס משתמש"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # נתוני משתמש
        cursor.execute('''
            SELECT u.*, 
                   w.wallet_address,
                   COUNT(t.id) as total_transactions,
                   SUM(CASE WHEN t.status = 'confirmed' THEN t.tokens_awarded ELSE 0 END) as total_tokens
            FROM users u
            LEFT JOIN wallets w ON u.telegram_id = w.telegram_id
            LEFT JOIN transactions t ON u.telegram_id = t.telegram_id
            WHERE u.telegram_id = ?
            GROUP BY u.telegram_id
        ''', (telegram_id,))
        
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # עסקאות אחרונות
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE telegram_id = ? 
            ORDER BY submitted_at DESC 
            LIMIT 5
        ''', (telegram_id,))
        
        transactions = cursor.fetchall()
        
        return {
            "user": dict(user),
            "transactions": [dict(tx) for tx in transactions]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/stats")
async def get_system_stats():
    """מחזיר סטטיסטיקות מערכת"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM stats WHERE id = 1")
        stats = cursor.fetchone()
        
        if not stats:
            stats = {
                "total_users": 0,
                "total_transactions": 0,
                "total_tokens": 0,
                "total_ton_received": 0
            }
        else:
            stats = dict(stats)
        
        # הוסף מידע נוסף
        cursor.execute("SELECT COUNT(*) as active_users FROM users WHERE status = 'active'")
        active = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as pending_tx FROM transactions WHERE status = 'pending'")
        pending = cursor.fetchone()
        
        return {
            "stats": stats,
            "active_users": active["active_users"],
            "pending_transactions": pending["pending_tx"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/admin/dashboard")
async def admin_dashboard(admin_key: str):
    """פאנל ניהול"""
    if admin_key != "airdrop_admin_2026":
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # סטטיסטיקות
        cursor.execute("SELECT * FROM stats WHERE id = 1")
        stats = cursor.fetchone()
        
        # משתמשים אחרונים
        cursor.execute('''
            SELECT u.*, 
                   COUNT(t.id) as transactions_count,
                   MAX(t.submitted_at) as last_transaction
            FROM users u
            LEFT JOIN transactions t ON u.telegram_id = t.telegram_id
            GROUP BY u.telegram_id
            ORDER BY u.registered_at DESC
            LIMIT 20
        ''')
        
        users = cursor.fetchall()
        
        # עסקאות אחרונות
        cursor.execute('''
            SELECT t.*, u.username, u.first_name
            FROM transactions t
            JOIN users u ON t.telegram_id = u.telegram_id
            ORDER BY t.submitted_at DESC
            LIMIT 20
        ''')
        
        transactions = cursor.fetchall()
        
        return {
            "system_status": "online",
            "stats": dict(stats) if stats else {},
            "recent_users": [dict(user) for user in users],
            "recent_transactions": [dict(tx) for tx in transactions],
            "server_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ====================
# INITIALIZATION
# ====================
@app.on_event("startup")
async def startup_event():
    """אתחול עם הפעלת השרת"""
    # צור תיקיית data אם לא קיימת
    os.makedirs("data", exist_ok=True)
    
    # אתחל את מסד הנתונים
    init_database()
    
    print("✅ Database initialized")
    print("🚀 API Ready: http://localhost:8000")
    print("📊 Admin: http://localhost:8000/admin/dashboard?admin_key=airdrop_admin_2026")

@app.get("/")
async def root():
    """דף הבית"""
    return {
        "message": "🚀 SLH Airdrop API",
        "version": "2.0",
        "status": "operational",
        "endpoints": {
            "register": "/api/users/register",
            "submit_wallet": "/api/users/submit_wallet", 
            "submit_transaction": "/api/users/submit_transaction",
            "user_status": "/api/users/{id}/status",
            "stats": "/api/stats",
            "admin": "/admin/dashboard?admin_key=...",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """בדיקת בריאות"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "version": "2.0"
    }

