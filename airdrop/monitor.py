import requests
import time
from datetime import datetime

def monitor_system():
    print("📊 TON Airdrop System Monitor")
    print("=" * 50)
    
    while True:
        try:
            # בדוק בריאות
            health = requests.get("http://localhost:8000/health", timeout=3).json()
            
            # בדוק סטטיסטיקות (אם יש endpoint)
            try:
                stats = requests.get("http://localhost:8000/api/stats", timeout=3).json()
                users = stats.get('total_users', 0)
                transactions = stats.get('total_transactions', 0)
            except:
                users = "N/A"
                transactions = "N/A"
            
            # הצג מידע
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Status: {health.get('status', 'unknown')} | Users: {users} | TX: {transactions}")
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {e}")
        
        time.sleep(10)

if __name__ == "__main__":
    try:
        monitor_system()
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped")
