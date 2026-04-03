import sys
import requests
import json
from pathlib import Path

def check_server():
    print("🔍 בדיקת מערכת Beta...")
    print("=" * 50)
    
    # בדוק אם השרת זמין
    try:
        response = requests.get("http://127.0.0.1:18082/health", timeout=5)
        if response.status_code == 200:
            print("✅ שרת רץ על: http://127.0.0.1:18082")
            return True
        else:
            print(f"❌ שגיאה: {response.status_code}")
            return False
    except:
        print("❌ שרת לא זמין. הרץ את run_server_local.ps1")
        return False

def check_endpoints():
    try:
        # בדוק admin panel
        admin_url = "http://127.0.0.1:18082/admin/dashboard?admin_key=airdrop_admin_2026"
        response = requests.get(admin_url, timeout=5)
        if response.status_code == 200:
            print("✅ Admin panel זמין")
        else:
            print(f"⚠️  Admin panel: {response.status_code}")
        
        # בדוק API docs
        docs_url = "http://127.0.0.1:18082/docs"
        response = requests.get(docs_url, timeout=5)
        if response.status_code == 200:
            print("✅ API documentation זמין")
        
        # בדוק health
        health_url = "http://127.0.0.1:18082/health"
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health status: {data.get('status', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ שגיאה בבדיקת endpoints: {e}")
        return False

def check_files():
    files_to_check = [
        ".env",
        "app/main.py",
        "bot/main_bot.py",
        "data/",
        "requirements_simple.txt"
    ]
    
    print("\n📁 בדיקת קבצים:")
    for file in files_to_check:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - חסר!")
    
    return True

def main():
    print("🚀 TON Airdrop Beta Test - System Check")
    print("=" * 50)
    
    checks = [
        ("קבצים", check_files),
        ("שרת", check_server),
        ("Endpoints", check_endpoints)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n🧪 בודק: {name}")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ שגיאה: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("📊 תוצאות בדיקה:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ עבר" if success else "❌ נכשל"
        print(f"{status}: {name}")
    
    print(f"\n🎯 סיכום: {passed}/{total} בדיקות עברו")
    
    if passed == total:
        print("\n🌟 המערכת מוכנה ל-Beta Test!")
        print("\n📢 שלב הבא:")
        print("1. קבל טוקן בוט מ-@BotFather")
        print("2. עדכן את .env עם הטוקן האמיתי")
        print("3. הרץ את הבוט בפקודה: python bot/main_bot.py")
        print("4. בדוק את המערכת עם 5 משתמשי מבחן")
        return 0
    else:
        print("\n⚠️  יש לתקן את השגיאות לפני Beta Test")
        return 1

if __name__ == "__main__":
    sys.exit(main())
