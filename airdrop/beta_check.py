# -*- coding: utf-8 -*-
import sys
import requests
import json
from pathlib import Path

def check_server():
    print("?? ????? ????? Beta...")
    print("=" * 50)
    
    # ???? ?? ???? ????
    try:
        response = requests.get("http://127.0.0.1:18082/health", timeout=5)
        if response.status_code == 200:
            print("? ??? ?? ??: http://127.0.0.1:18082")
            return True
        else:
            print(f"? ?????: {response.status_code}")
            return False
    except:
        print("? ??? ?? ????. ??? ?? run_server_local.ps1")
        return False

def check_endpoints():
    try:
        # ???? admin panel
        admin_url = "http://127.0.0.1:18082/admin/dashboard?admin_key=airdrop_admin_2026"
        response = requests.get(admin_url, timeout=5)
        if response.status_code == 200:
            print("? Admin panel ????")
        else:
            print(f"??  Admin panel: {response.status_code}")
        
        # ???? API docs
        docs_url = "http://127.0.0.1:18082/docs"
        response = requests.get(docs_url, timeout=5)
        if response.status_code == 200:
            print("? API documentation ????")
        
        # ???? health
        health_url = "http://127.0.0.1:18082/health"
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"? Health status: {data.get('status', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"? ????? ?????? endpoints: {e}")
        return False

def check_files():
    files_to_check = [
        ".env",
        "app/main.py",
        "bot/main_bot.py",
        "data/",
        "requirements_simple.txt"
    ]
    
    print("\n?? ????? ?????:")
    for file in files_to_check:
        if Path(file).exists():
            print(f"? {file}")
        else:
            print(f"? {file} - ???!")
    
    return True

def main():
    print("?? TON Airdrop Beta Test - System Check")
    print("=" * 50)
    
    checks = [
        ("?????", check_files),
        ("???", check_server),
        ("Endpoints", check_endpoints)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n?? ????: {name}")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"? ?????: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("?? ?????? ?????:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "? ???" if success else "? ????"
        print(f"{status}: {name}")
    
    print(f"\n?? ?????: {passed}/{total} ?????? ????")
    
    if passed == total:
        print("\n?? ?????? ????? ?-Beta Test!")
        print("\n?? ??? ???:")
        print("1. ??? ???? ??? ?-@BotFather")
        print("2. ???? ?? .env ?? ????? ??????")
        print("3. ??? ?? ???? ??????: python bot/main_bot.py")
        print("4. ???? ?? ?????? ?? 5 ?????? ????")
        return 0
    else:
        print("\n??  ?? ???? ?? ??????? ???? Beta Test")
        return 1

if __name__ == "__main__":
    sys.exit(main())



