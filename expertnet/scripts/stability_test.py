import os, sqlite3, time
from cryptography.fernet import Fernet
from web3 import Web3

def run_diagnostic():
    print(" מריץ אבחון מערכת מקיף (V13)...")
    results = []

    # 1. בדיקת שלמות הצפנה
    try:
        with open(r"D:\ExpertNet_Core\vault\master.key", "rb") as f:
            key = f.read()
            f_obj = Fernet(key)
            test_str = "ExpertNet_Safety_Test"
            encrypted = f_obj.encrypt(test_str.encode())
            decrypted = f_obj.decrypt(encrypted).decode()
            results.append(("הצפנה ופענוח Vault", decrypted == test_str))
    except: results.append(("הצפנה ופענוח Vault", False))

    # 2. בדיקת עומס בסיס נתונים
    try:
        conn = sqlite3.connect(r"D:\ExpertNet_Core\vault\expertnet.db")
        start = time.time()
        for _ in range(10): conn.execute("SELECT 1")
        end = time.time()
        results.append(("ביצועי DB (Latency)", (end-start) < 0.1))
    except: results.append(("בסיס נתונים", False))

    # 3. בדיקת יציבות רשת (BSC)
    try:
        w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))
        results.append(("חיבור BSC Mainnet", w3.is_connected()))
    except: results.append(("חיבור BSC Mainnet", False))

    print("\n--- דוח סופי ---")
    for test, status in results:
        icon = "" if status else ""
        print(f"{icon} {test}")

run_diagnostic()