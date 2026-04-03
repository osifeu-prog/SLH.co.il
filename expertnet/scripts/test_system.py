import os, sqlite3
from web3 import Web3

DB_PATH = r'D:\ExpertNet_Core\vault\expertnet.db'
KEY_PATH = r'D:\ExpertNet_Core\vault\master.key'

def run_tests():
    print(" מריץ בדיקות מערכת...")
    
    # 1. בדיקת קבצים
    for p in [DB_PATH, KEY_PATH]:
        exists = "" if os.path.exists(p) else ""
        print(f"{exists} קובץ: {os.path.basename(p)}")
    
    # 2. בדיקת DB
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT * FROM users LIMIT 1")
        print(" בסיס נתונים תקין ונגיש")
    except: print(" שגיאה בגישה ל-DB")

    # 3. בדיקת בלוקצ'יין
    w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))
    if w3.is_connected():
        print(f" מחובר ל-BSC (Block: {w3.eth.block_number})")
    else: print(" אין חיבור לבלוקצ'יין")

run_tests()