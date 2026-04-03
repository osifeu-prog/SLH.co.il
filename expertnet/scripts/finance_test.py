import sqlite3

DB_PATH = r'D:\ExpertNet_Core\vault\expertnet.db'

def test_finance():
    print(" בודק תשתיות פיננסיות...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # בדיקת עמודות חדשות
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    features = {
        "Staking": "staked_balance" in columns,
        "Balance": "balance" in columns,
        "P2P Table": False
    }
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
    if cursor.fetchone(): features["P2P Table"] = True
    
    for f, status in features.items():
        print(f"{'' if status else ''} {f}")

test_finance()