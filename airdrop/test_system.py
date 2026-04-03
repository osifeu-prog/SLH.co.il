#!/usr/bin/env python3
"""
Test Script for TON Airdrop System
"""

import requests
import sys
import os
from datetime import datetime

def test_backend():
    """בדוק שהבאקנד עובד"""
    try:
        base_url = os.getenv("API_URL", "http://localhost:8000")
        response = requests.get(f"{base_url}/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to backend: {e}")
        return False

def test_bot_connection():
    """בדוק חיבור לבוט"""
    try:
        import asyncio
        import aiohttp
        
        async def check_bot():
            base_url = os.getenv("API_URL", "http://localhost:8000")
            headers = {"X-API-Key": os.getenv("API_KEY", "test")}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/api/health", headers=headers) as response:
                    return response.status == 200
            
        result = asyncio.run(check_bot())
        
        if result:
            print("✅ Bot API connection is working")
            return True
        else:
            print("❌ Bot API connection failed")
            return False
    except Exception as e:
        print(f"❌ Bot test failed: {e}")
        return False

def test_database():
    """בדוק חיבור למסד נתונים"""
    try:
        from sqlalchemy import create_engine, text
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            print("⚠️ DATABASE_URL not set, skipping database test")
            return True
        
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                print("✅ Database connection is working")
                return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    return False

def main():
    """הרץ את כל הבדיקות"""
    print("🚀 Starting TON Airdrop System Tests")
    print("=" * 50)
    
    tests = [
        ("Backend", test_backend),
        ("Database", test_database),
        ("Bot Connection", test_bot_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🌟 All tests passed! System is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
