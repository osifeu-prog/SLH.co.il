#!/usr/bin/env python3
"""
קובץ אתחול מסד נתונים - Crypto-Class
"""

import os
import sys

# הוסף את התיקייה הנוכחית ל-PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔧 Crypto-Class - אתחול מסד נתונים")
print("=" * 50)

try:
    from database.db import init_database
    from config import get_app_info
    
    info = get_app_info()
    print(f"📱 אפליקציה: {info['name']} v{info['version']}")
    print(f"👤 מפתח: {info['author']}")
    print(f"💾 מסד נתונים: {info['database_path']}")
    print()
    
    try:
        init_database()
        print("✅ מסד הנתונים אותחל בהצלחה!")
        print()
        
        print("📊 טבלאות שנוצרו:")
        print("   • users - טבלת משתמשים")
        print("   • attendance - טבלת נוכחות")
        print("   • tasks - טבלת משימות")
        print("   • task_completions - טבלת השלמת משימות")
        print("   • user_daily_stats - טבלת סטטיסטיקות יומיות")
        print("   • referrals - טבלת הפניות")
        print()
        
        print("🎯 משימות ברירת מחדל שנוספו:")
        print("   • צ'ק-אין יומי (1 טוקן)")
        print("   • תרומה לפורום (3 טוקנים)")
        print("   • סיוע לתלמיד (5 טוקנים)")
        print("   • הפניה של חבר (10 טוקנים)")
        print()
        
        print("👤 משתמש דמו שנוסף:")
        print("   • מזהה: 123456789")
        print("   • שם: משתמש דמו")
        print("   • טוקנים התחלתיים: 100")
        print("   • רמה התחלתית: 3")
        print("   • הפניות: 2")
        print()
        
        print("🚀 המערכת מוכנה להפעלה!")
        print()
        print("📝 הוראות:")
        print("   1. הגדר את משתני הסביבה ב-.env")
        print("   2. הפעל את השרת עם: python bot/main.py")
        print("   3. פתח את הדפדפן בכתובת: http://localhost:5000")
        print("   4. היכנס לבוט הטלגרם והתחל להשתמש!")
        
    except Exception as e:
        print(f"❌ שגיאה באתחול מסד הנתונים: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
except ImportError as e:
    print(f"❌ שגיאה ביבוא מודולים: {e}")
    print("📦 ודא שהתלויות מותקנות: pip install -r requirements.txt")
    sys.exit(1)

