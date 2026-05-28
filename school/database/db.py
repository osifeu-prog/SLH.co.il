#!/usr/bin/env python3
"""
ממשק מסד הנתונים - Crypto-Class
"""

import os
from .models import Session, User, Attendance, Task, TaskCompletion, UserDailyStats, Referral
from .models import TaskStatus, TaskFrequency, TaskType
from datetime import datetime, date, timedelta
from .queries import init_database

# פונקציות ייצוא
__all__ = [
    'Session', 'User', 'Attendance', 'Task', 'TaskCompletion', 
    'UserDailyStats', 'Referral', 'TaskStatus', 'TaskFrequency', 
    'TaskType', 'init_database', 'get_db_session', 'close_session',
    'get_user_by_referral_code', 'get_user_attendance_history',
    'get_system_health', 'ensure_database_initialized'
]

# פונקציות עזר
def get_db_session():
    """קבלת סשן למסד הנתונים"""
    return Session()

def close_session(session):
    """סגירת סשן"""
    if session:
        session.close()

def get_user_by_referral_code(referral_code):
    """קבלת משתמש לפי קוד הפניה"""
    session = Session()
    try:
        user = session.query(User).filter_by(referral_code=referral_code).first()
        return user
    except Exception as e:
        print(f"❌ שגיאה בקבלת משתמש לפי קוד הפניה: {e}")
        return None
    finally:
        session.close()

def get_user_attendance_history(telegram_id, days=30):
    """קבלת היסטוריית נוכחות של משתמש"""
    session = Session()
    try:
        start_date = date.today() - timedelta(days=days)
        attendances = session.query(Attendance).filter(
            Attendance.telegram_id == telegram_id,
            Attendance.date >= start_date
        ).order_by(Attendance.date.desc()).all()
        
        return attendances
    except Exception as e:
        print(f"❌ שגיאה בקבלת היסטוריית נוכחות: {e}")
        return []
    finally:
        session.close()

def get_system_health():
    """בדיקת בריאות מסד הנתונים"""
    session = Session()
    try:
        # בדיקת חיבור למסד הנתונים
        session.execute("SELECT 1")
        
        # בדיקת מספר טבלאות
        from sqlalchemy import inspect
        inspector = inspect(session.get_bind())
        tables = inspector.get_table_names()
        
        # בדיקת מספר משתמשים
        user_count = session.query(User).count()
        
        return {
            "status": "healthy",
            "tables_count": len(tables),
            "users_count": user_count,
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }
    finally:
        session.close()

def ensure_database_initialized():
    """אתחול מסד נתונים אם לא מאותחל"""
    try:
        # בדיקה אם מסד הנתונים כבר מאותחל
        session = Session()
        user_count = session.query(User).count()
        session.close()
        
        if user_count == 0:
            print("🔧 מאתחל מסד נתונים חדש...")
            init_database()
            return True
        else:
            print(f"✅ מסד נתונים כבר מאותחל: {user_count} משתמשים")
            return False
    except Exception as e:
        print(f"❌ שגיאה בבדיקת אתחול מסד נתונים: {e}")
        # נסה לאתחל בכל מקרה
        init_database()
        return True

# אתחול אוטומטי בעת יבוא המודול
if __name__ != "__main__":
    ensure_database_initialized()

