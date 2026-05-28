#!/usr/bin/env python3
"""
מסד נתונים משודרג עם תכונות חדשות
גרסה מלאה ומוכנה להפעלה
"""

import logging
from .models import Session, User, Attendance, Task, TaskCompletion, UserDailyStats, Referral
from .models import TaskStatus, TaskFrequency, TaskType
from datetime import datetime, date, timedelta
import random
import string
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# ========== פונקציות עזר ==========

def generate_referral_code(length=8):
    """יצירת קוד הפניה ייחודי עם בדיקת כפילויות"""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        # בדוק אם הקוד כבר קיים
        session = Session()
        try:
            existing = session.query(User).filter_by(referral_code=code).first()
            if not existing:
                return code
        finally:
            session.close()

# ========== פונקציות אתחול ==========

def init_database():
    """אתחול מסד הנתונים עם נתונים ראשוניים"""
    from .models import Base, engine
    
    try:
        Base.metadata.create_all(engine)
        logger.info("✅ טבלאות נוצרו בהצלחה")
        
        session = Session()
        try:
            # משימות ברירת מחדל
            default_tasks = [
                {
                    "name": "צ'ק-אין יומי",
                    "description": "התחבר כל יום וקבל טוקן",
                    "task_type": TaskType.CLASS,
                    "frequency": TaskFrequency.DAILY,
                    "tokens_reward": 1,
                    "exp_reward": 10,
                    "is_active": True
                },
                {
                    "name": "תרומה לפורום",
                    "description": "פרסם תשובה או שאלה בפורום הקורס",
                    "task_type": TaskType.FORUM,
                    "frequency": TaskFrequency.DAILY,
                    "tokens_reward": 3,
                    "exp_reward": 25,
                    "requires_proof": True,
                    "is_active": True
                },
                {
                    "name": "סיוע לתלמיד",
                    "description": "עזור לתלמיד אחר בשאלה או בעיה",
                    "task_type": TaskType.HELP,
                    "frequency": TaskFrequency.DAILY,
                    "tokens_reward": 5,
                    "exp_reward": 50,
                    "requires_proof": True,
                    "is_active": True
                },
                {
                    "name": "הפניה של חבר",
                    "description": "הזמן חבר חדש למערכת",
                    "task_type": TaskType.REFERRAL,
                    "frequency": TaskFrequency.ONE_TIME,
                    "tokens_reward": 10,
                    "exp_reward": 100,
                    "is_active": True
                },
                {
                    "name": "השתתפות בשיעור",
                    "description": "השתתף בשיעור הקבוצתי",
                    "task_type": TaskType.CLASS,
                    "frequency": TaskFrequency.WEEKLY,
                    "tokens_reward": 15,
                    "exp_reward": 75,
                    "is_active": True
                },
                {
                    "name": "משימת אתגר שבועי",
                    "description": "השלם את האתגר השבועי",
                    "task_type": TaskType.QUIZ,
                    "frequency": TaskFrequency.WEEKLY,
                    "tokens_reward": 25,
                    "exp_reward": 150,
                    "requires_proof": True,
                    "is_active": True
                }
            ]
            
            for task_data in default_tasks:
                existing_task = session.query(Task).filter_by(name=task_data["name"]).first()
                if not existing_task:
                    task = Task(**task_data)
                    session.add(task)
                    logger.info(f"✅ משימה נוצרה: {task_data['name']}")
            
            session.commit()
            logger.info("✅ מסד הנתונים אותחל בהצלחה עם משימות ברירת מחדל")
            
            # הוספת משתמש דמו אם אין משתמשים
            user_count = session.query(User).count()
            if user_count == 0:
                demo_user = User(
                    telegram_id=123456789,
                    username="demo_user",
                    first_name="משתמש",
                    last_name="דמו",
                    tokens=100,
                    level=3,
                    experience=150,
                    next_level_exp=200,
                    referral_code=generate_referral_code(),
                    total_referrals=2,
                    referral_tokens=20
                )
                session.add(demo_user)
                
                # הוספת צ'ק-אין לדמו
                for i in range(5):
                    checkin_date = date.today() - timedelta(days=i)
                    attendance = Attendance(
                        telegram_id=123456789,
                        date=checkin_date,
                        tokens_earned=1
                    )
                    session.add(attendance)
                
                session.commit()
                logger.info("✅ משתמש דמו נוסף עם היסטוריית צ'ק-אין")
                
        except Exception as e:
            session.rollback()
            logger.error(f"❌ שגיאה באתחול משימות: {e}")
            raise
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"❌ שגיאה ביצירת טבלאות: {e}")
        raise

# ========== פונקציות משתמשים ==========

def register_user(telegram_id, username=None, first_name=None, last_name=None, referral_code=None):
    """רישום משתמש חדש עם הפניה"""
    session = Session()
    try:
        existing_user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if existing_user:
            logger.info(f"ℹ️ משתמש {telegram_id} כבר קיים")
            return False
        
        # יצירת קוד הפניה ייחודי
        user_referral_code = generate_referral_code()
        
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            tokens=10,  # בונוס הרשמה
            referral_code=user_referral_code,
            level=1,
            experience=0,
            next_level_exp=100,
            total_referrals=0,
            referral_tokens=0,
            created_at=datetime.now()
        )
        session.add(user)
        
        # טיפול בהפניה אם קיים
        if referral_code:
            referrer = session.query(User).filter_by(referral_code=referral_code).first()
            if referrer and referrer.telegram_id != telegram_id:
                # בדוק אם כבר קיימת הפניה
                existing_ref = session.query(Referral).filter_by(
                    referrer_id=referrer.telegram_id,
                    referred_id=telegram_id
                ).first()
                
                if not existing_ref:
                    referral = Referral(
                        referrer_id=referrer.telegram_id,
                        referred_id=telegram_id,
                        referral_code=referral_code,
                        status='active',
                        created_at=datetime.now()
                    )
                    session.add(referral)
                    
                    # עדכון המזמין
                    referrer.total_referrals += 1
                    referrer.tokens += 10
                    referrer.referral_tokens += 10
                    
                    # הודעה למזמין
                    user.tokens += 5  # בונוס למצטרף דרך הפניה
        
        session.commit()
        logger.info(f"✅ משתמש נרשם: {telegram_id} עם קוד הפניה: {user_referral_code}")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה ברישום משתמש: {e}")
        return False
    finally:
        session.close()

def checkin_user(telegram_id):
    """צ'ק-אין יומי"""
    session = Session()
    try:
        today = date.today()
        
        # בדוק אם כבר ביצע צ'ק-אין היום
        existing_checkin = session.query(Attendance).filter_by(
            telegram_id=telegram_id,
            date=today
        ).first()
        
        if existing_checkin:
            return False, "כבר ביצעת צ'ק-אין היום!"
        
        # קבל את המשתמש
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return False, "משתמש לא נמצא. שלח /start כדי להירשם"
        
        # חישוב טוקנים לפי רצף
        yesterday = today - timedelta(days=1)
        yesterday_checkin = session.query(Attendance).filter_by(
            telegram_id=telegram_id,
            date=yesterday
        ).first()
        
        # חשב את הרצף הנוכחי
        recent_attendances = session.query(Attendance).filter(
            Attendance.telegram_id == telegram_id,
            Attendance.date >= today - timedelta(days=30)
        ).order_by(Attendance.date.desc()).all()
        
        streak = 1
        last_date = today
        for attendance in recent_attendances:
            if attendance.date == last_date - timedelta(days=1):
                streak += 1
                last_date = attendance.date
            else:
                break
        
        # חישוב בונוסים
        base_tokens = 1
        streak_bonus = 0
        
        if streak >= 7:
            streak_bonus = 3
        elif streak >= 3:
            streak_bonus = 1
        
        # בונוס רמה
        level_bonus = user.level // 3  # כל 3 רמות בונוס נוסף
        
        total_tokens = base_tokens + streak_bonus + level_bonus
        
        # יצירת רשומת נוכחות
        attendance = Attendance(
            telegram_id=telegram_id,
            date=today,
            tokens_earned=total_tokens,
            checkin_time=datetime.now()
        )
        session.add(attendance)
        
        # עדכון המשתמש
        user.tokens += total_tokens
        user.last_checkin = today
        user.experience += (total_tokens * 10)
        user.total_experience += (total_tokens * 10)
        
        # עדכון רמה אם צריך
        update_user_level(user)
        
        # עדכון סטטיסטיקות יומיות
        update_daily_stats(telegram_id, today, total_tokens)
        
        session.commit()
        
        # יצירת הודעה עם פירוט
        message = f"🎉 צ'ק-אין נרשם בהצלחה!\n\n"
        message += f"💰 קיבלת: {total_tokens} טוקנים\n"
        if streak_bonus > 0:
            message += f"   • בסיס: 1\n"
            message += f"   • רצף ({streak} ימים): +{streak_bonus}\n"
        if level_bonus > 0:
            message += f"   • רמה ({user.level}): +{level_bonus}\n"
        message += f"\n🔥 הרצף שלך: {streak} ימים\n"
        message += f"🏆 הרמה שלך: {user.level}\n"
        message += f"📊 ניסיון: {user.experience}/{user.next_level_exp}"
        
        return True, message
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה ברישום צ'ק-אין: {e}")
        return False, f"שגיאה: {str(e)}"
    finally:
        session.close()

def update_user_level(user):
    """עדכון רמת המשתמש לפי הניסיון"""
    # נוסחת רמות מורכבת יותר
    level_thresholds = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 
                       3600, 4500, 5500, 6600, 7800, 9100, 10500]
    
    new_level = 1
    for i, threshold in enumerate(level_thresholds[1:], 1):
        if user.experience >= threshold:
            new_level = i + 1
        else:
            break
    
    if new_level > user.level:
        user.level = new_level
        user.next_level_exp = level_thresholds[new_level] if new_level < len(level_thresholds) else level_thresholds[-1] * 1.5
        # בונוס עלייה ברמה
        user.tokens += new_level * 5
        return True, new_level
    
    return False, user.level

def update_daily_stats(telegram_id, date, tokens_earned):
    """עדכון סטטיסטיקות יומיות"""
    session = Session()
    try:
        stats = session.query(UserDailyStats).filter_by(
            telegram_id=telegram_id,
            date=date
        ).first()
        
        if not stats:
            stats = UserDailyStats(
                telegram_id=telegram_id,
                date=date,
                tasks_completed=0,
                tokens_earned=tokens_earned,
                streak_days=1
            )
            session.add(stats)
        else:
            stats.tokens_earned += tokens_earned
        
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה בעדכון סטטיסטיקות יומיות: {e}")
    finally:
        session.close()

def get_balance(telegram_id):
    """קבלת יתרת טוקנים"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        return user.tokens if user else 0
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת יתרה: {e}")
        return 0
    finally:
        session.close()

def get_user(telegram_id):
    """קבלת משתמש לפי ID"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        return user
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת משתמש: {e}")
        return None
    finally:
        session.close()

def get_all_users(limit=None, offset=0):
    """קבלת כל המשתמשים"""
    session = Session()
    try:
        query = session.query(User).order_by(desc(User.created_at))
        if limit:
            query = query.limit(limit).offset(offset)
        users = query.all()
        return users
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת כל המשתמשים: {e}")
        return []
    finally:
        session.close()

def get_user_level_info(telegram_id):
    """קבלת מידע על רמת המשתמש"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return None
        
        # חישוב דירוג
        rank = session.query(User).filter(User.tokens > user.tokens).count() + 1
        
        # חישוב אחוזי התקדמות
        progress_percentage = int((user.experience / user.next_level_exp) * 100) if user.next_level_exp > 0 else 0
        
        # סטטיסטיקות נוספות
        total_tasks = session.query(TaskCompletion).filter_by(telegram_id=telegram_id).count()
        completed_tasks = session.query(TaskCompletion).filter_by(
            telegram_id=telegram_id,
            status=TaskStatus.COMPLETED
        ).count()
        
        return {
            'level': user.level,
            'experience': user.experience,
            'next_level_exp': user.next_level_exp,
            'total_experience': user.total_experience,
            'progress_percentage': progress_percentage,
            'rank': rank,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת מידע רמה: {e}")
        return None
    finally:
        session.close()

def get_top_users(limit=10, order_by='tokens'):
    """קבלת רשימת המשתמשים המובילים"""
    session = Session()
    try:
        if order_by == 'tokens':
            users = session.query(User).order_by(desc(User.tokens)).limit(limit).all()
        elif order_by == 'level':
            users = session.query(User).order_by(desc(User.level), desc(User.experience)).limit(limit).all()
        elif order_by == 'referrals':
            users = session.query(User).order_by(desc(User.total_referrals)).limit(limit).all()
        elif order_by == 'streak':
            # חישוב רצף מורכב יותר
            users = session.query(User).all()
            users_with_streak = []
            for user in users:
                streak = calculate_user_streak(user.telegram_id)
                users_with_streak.append((user, streak))
            users_with_streak.sort(key=lambda x: x[1], reverse=True)
            users = [u[0] for u in users_with_streak[:limit]]
        else:
            users = session.query(User).order_by(desc(User.tokens)).limit(limit).all()
        
        return users
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת מובילים: {e}")
        return []
    finally:
        session.close()

def calculate_user_streak(telegram_id):
    """חישוב רצף צ'ק-אין של משתמש"""
    session = Session()
    try:
        attendances = session.query(Attendance).filter_by(
            telegram_id=telegram_id
        ).order_by(Attendance.date.desc()).all()
        
        if not attendances:
            return 0
        
        streak = 0
        current_date = date.today()
        
        for attendance in attendances:
            if attendance.date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    except Exception as e:
        logger.error(f"❌ שגיאה בחישוב רצף: {e}")
        return 0
    finally:
        session.close()

def get_user_referrals(telegram_id, limit=10):
    """קבלת רשימת ההפניות של משתמש"""
    session = Session()
    try:
        referrals = session.query(Referral).filter_by(
            referrer_id=telegram_id
        ).order_by(desc(Referral.created_at)).limit(limit).all()
        return referrals
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת הפניות: {e}")
        return []
    finally:
        session.close()

def get_total_referrals(telegram_id):
    """קבלת מספר ההפניות הכולל של משתמש"""
    session = Session()
    try:
        count = session.query(Referral).filter_by(referrer_id=telegram_id).count()
        return count
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת מספר הפניות: {e}")
        return 0
    finally:
        session.close()

def get_referred_users(telegram_id):
    """קבלת רשימת המוזמנים של משתמש"""
    session = Session()
    try:
        referrals = session.query(Referral).filter_by(referrer_id=telegram_id).all()
        referred_ids = [r.referred_id for r in referrals]
        
        if not referred_ids:
            return []
        
        users = session.query(User).filter(User.telegram_id.in_(referred_ids)).all()
        return users
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת מוזמנים: {e}")
        return []
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
        ).order_by(desc(Attendance.date)).all()
        
        return attendances
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת היסטוריית נוכחות: {e}")
        return []
    finally:
        session.close()

# ========== פונקציות משימות ==========

def get_available_tasks(telegram_id):
    """קבלת רשימת משימות זמינות למשתמש"""
    session = Session()
    try:
        # קבל את כל המשימות הפעילות
        tasks = session.query(Task).filter_by(is_active=True).all()
        
        # סינון משימות שכבר הושלמו היום/השבוע/החודש
        available_tasks = []
        today = date.today()
        
        for task in tasks:
            # בדוק אם המשתמש כבר השלים את המשימה בתדירות המתאימה
            if task.frequency == TaskFrequency.DAILY:
                # בדוק אם השלים היום
                completed_today = session.query(TaskCompletion).filter(
                    TaskCompletion.telegram_id == telegram_id,
                    TaskCompletion.task_id == task.id,
                    func.date(TaskCompletion.completed_at) == today
                ).first()
                if not completed_today:
                    available_tasks.append(task)
                    
            elif task.frequency == TaskFrequency.WEEKLY:
                # תחילת השבוע
                start_of_week = today - timedelta(days=today.weekday())
                completed_this_week = session.query(TaskCompletion).filter(
                    TaskCompletion.telegram_id == telegram_id,
                    TaskCompletion.task_id == task.id,
                    TaskCompletion.completed_at >= start_of_week
                ).first()
                if not completed_this_week:
                    available_tasks.append(task)
                    
            elif task.frequency == TaskFrequency.MONTHLY:
                # תחילת החודש
                start_of_month = date(today.year, today.month, 1)
                completed_this_month = session.query(TaskCompletion).filter(
                    TaskCompletion.telegram_id == telegram_id,
                    TaskCompletion.task_id == task.id,
                    TaskCompletion.completed_at >= start_of_month
                ).first()
                if not completed_this_month:
                    available_tasks.append(task)
                    
            elif task.frequency == TaskFrequency.ONE_TIME:
                # בדוק אם אי פעם השלים
                ever_completed = session.query(TaskCompletion).filter(
                    TaskCompletion.telegram_id == telegram_id,
                    TaskCompletion.task_id == task.id
                ).first()
                if not ever_completed:
                    available_tasks.append(task)
        
        return available_tasks
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת משימות: {e}")
        return []
    finally:
        session.close()

def get_user_tasks(telegram_id):
    """קבלת רשימת המשימות של משתמש"""
    session = Session()
    try:
        tasks = session.query(TaskCompletion).filter_by(
            telegram_id=telegram_id
        ).order_by(desc(TaskCompletion.completed_at)).all()
        return tasks
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת משימות משתמש: {e}")
        return []
    finally:
        session.close()

def complete_task(telegram_id, task_id, proof_text=None):
    """השלמת משימה עם ולידציה"""
    session = Session()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task or not task.is_active:
            return False, "המשימה לא קיימת או לא פעילה"
        
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return False, "משתמש לא נמצא"
        
        # בדוק אם ניתן להשלים את המשימה
        today = date.today()
        
        if task.frequency == TaskFrequency.DAILY:
            completed_today = session.query(TaskCompletion).filter(
                TaskCompletion.telegram_id == telegram_id,
                TaskCompletion.task_id == task_id,
                func.date(TaskCompletion.completed_at) == today
            ).first()
            if completed_today:
                return False, "כבר השלמת משימה זו היום"
                
        elif task.frequency == TaskFrequency.WEEKLY:
            start_of_week = today - timedelta(days=today.weekday())
            completed_this_week = session.query(TaskCompletion).filter(
                TaskCompletion.telegram_id == telegram_id,
                TaskCompletion.task_id == task_id,
                TaskCompletion.completed_at >= start_of_week
            ).first()
            if completed_this_week:
                return False, "כבר השלמת משימה זו השבוע"
                
        elif task.frequency == TaskFrequency.ONE_TIME:
            ever_completed = session.query(TaskCompletion).filter(
                TaskCompletion.telegram_id == telegram_id,
                TaskCompletion.task_id == task_id
            ).first()
            if ever_completed:
                return False, "כבר השלמת משימה זו בעבר"
        
        # אם המשימה דורשת הוכחה, סמן כממתינה לאישור
        status = TaskStatus.PENDING if task.requires_proof else TaskStatus.COMPLETED
        
        completion = TaskCompletion(
            telegram_id=telegram_id,
            task_id=task_id,
            tokens_earned=task.tokens_reward,
            exp_earned=task.exp_reward,
            status=status,
            proof_text=proof_text,
            completed_at=datetime.now()
        )
        
        # אם לא דורש אישור, הוסף את הטוקנים מיד
        if status == TaskStatus.COMPLETED:
            user.tokens += task.tokens_reward
            user.experience += task.exp_reward
            user.total_experience += task.exp_reward
            update_user_level(user)
        
        session.add(completion)
        session.commit()
        
        if status == TaskStatus.COMPLETED:
            return True, f"🎉 השלמת משימה! קיבלת {task.tokens_reward} טוקנים!"
        else:
            return True, f"✅ הגשת משימה לאישור! המנהל יאשר בקרוב."
            
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה בהשלמת משימה: {e}")
        return False, f"שגיאה: {str(e)}"
    finally:
        session.close()

def get_pending_tasks():
    """קבלת משימות ממתינות לאישור"""
    session = Session()
    try:
        tasks = session.query(TaskCompletion).filter_by(
            status=TaskStatus.PENDING
        ).order_by(TaskCompletion.completed_at).all()
        return tasks
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת משימות ממתינות: {e}")
        return []
    finally:
        session.close()

def approve_task(task_completion_id, admin_id):
    """אישור משימה על ידי מנהל"""
    session = Session()
    try:
        completion = session.query(TaskCompletion).filter_by(id=task_completion_id).first()
        if not completion:
            return False, "השלמת משימה לא נמצאה"
        
        if completion.status != TaskStatus.PENDING:
            return False, "המשימה כבר אושרה או נדחתה"
        
        task = session.query(Task).filter_by(id=completion.task_id).first()
        user = session.query(User).filter_by(telegram_id=completion.telegram_id).first()
        
        if not task or not user:
            return False, "שגיאה בנתונים"
        
        # עדכן סטטוס והוסף טוקנים
        completion.status = TaskStatus.COMPLETED
        completion.verified_by = admin_id
        
        user.tokens += completion.tokens_earned
        user.experience += completion.exp_earned
        user.total_experience += completion.exp_earned
        update_user_level(user)
        
        session.commit()
        return True, f"✅ המשימה אושרה! המשתמש קיבל {completion.tokens_earned} טוקנים."
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה באישור משימה: {e}")
        return False, f"שגיאה: {str(e)}"
    finally:
        session.close()

def reject_task(task_completion_id, admin_id, reason=None):
    """דחיית משימה על ידי מנהל"""
    session = Session()
    try:
        completion = session.query(TaskCompletion).filter_by(id=task_completion_id).first()
        if not completion:
            return False, "השלמת משימה לא נמצאה"
        
        if completion.status != TaskStatus.PENDING:
            return False, "המשימה כבר אושרה או נדחתה"
        
        completion.status = TaskStatus.LOCKED
        completion.verified_by = admin_id
        if reason:
            completion.proof_text = f"נדחה: {reason}\n\n{completion.proof_text}"
        
        session.commit()
        return True, "❌ המשימה נדחתה."
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה בדחיית משימה: {e}")
        return False, f"שגיאה: {str(e)}"
    finally:
        session.close()

# ========== פונקציות סטטיסטיקה ==========

def get_system_stats():
    """קבלת סטטיסטיקות מערכת מקיפות"""
    session = Session()
    try:
        from sqlalchemy import func
        
        # סטטיסטיקות בסיסיות
        total_users = session.query(User).count()
        
        # משתמשים פעילים היום (עשו צ'ק-אין)
        today = date.today()
        active_today = session.query(Attendance).filter(
            Attendance.date == today
        ).distinct(Attendance.telegram_id).count()
        
        total_tokens = session.query(func.sum(User.tokens)).scalar() or 0
        
        # סטטיסטיקות מתקדמות
        total_referrals = session.query(Referral).count()
        total_tasks_completed = session.query(TaskCompletion).filter_by(
            status=TaskStatus.COMPLETED
        ).count()
        
        # חישוב ממוצעים
        avg_tokens = total_tokens / total_users if total_users > 0 else 0
        avg_level_result = session.query(func.avg(User.level)).scalar()
        avg_level = round(avg_level_result, 2) if avg_level_result else 0
        
        # התפלגות רמות
        level_distribution = {}
        for i in range(1, 11):
            count = session.query(User).filter_by(level=i).count()
            level_distribution[f'level_{i}'] = count
        
        # משימות פופולריות
        popular_tasks = session.query(
            TaskCompletion.task_id,
            func.count(TaskCompletion.task_id).label('count')
        ).filter_by(status=TaskStatus.COMPLETED).group_by(
            TaskCompletion.task_id
        ).order_by(desc('count')).limit(5).all()
        
        popular_tasks_data = []
        for task_id, count in popular_tasks:
            task = session.query(Task).filter_by(id=task_id).first()
            if task:
                popular_tasks_data.append({
                    'name': task.name,
                    'count': count
                })
        
        # סטטיסטיקות נוספות
        total_checkins = session.query(Attendance).count()
        avg_daily_active = session.query(
            func.date(Attendance.date),
            func.count(func.distinct(Attendance.telegram_id))
        ).group_by(func.date(Attendance.date)).all()
        
        avg_daily = sum(count for _, count in avg_daily_active) / len(avg_daily_active) if avg_daily_active else 0
        
        return {
            'total_users': total_users,
            'active_today': active_today,
            'total_tokens': total_tokens,
            'total_referrals': total_referrals,
            'total_tasks_completed': total_tasks_completed,
            'total_checkins': total_checkins,
            'avg_tokens': round(avg_tokens, 2),
            'avg_level': avg_level,
            'avg_daily_active': round(avg_daily, 2),
            'level_distribution': level_distribution,
            'popular_tasks': popular_tasks_data,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת סטטיסטיקות: {e}")
        return {
            'total_users': 0,
            'active_today': 0,
            'total_tokens': 0,
            'total_referrals': 0,
            'total_tasks_completed': 0,
            'total_checkins': 0,
            'avg_tokens': 0,
            'avg_level': 0,
            'avg_daily_active': 0,
            'level_distribution': {},
            'popular_tasks': [],
            'timestamp': datetime.now().isoformat()
        }
    finally:
        session.close()

def get_checkin_data(days=7):
    """קבלת נתוני צ'ק-אין לימים אחרונים"""
    session = Session()
    try:
        data = []
        for i in range(days):
            day = date.today() - timedelta(days=i)
            count = session.query(Attendance).filter(Attendance.date == day).count()
            data.append({
                'date': day.strftime('%Y-%m-%d'),
                'day_name': day.strftime('%a'),
                'count': count
            })
        return list(reversed(data))
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת נתוני צ'ק-אין: {e}")
        return []
    finally:
        session.close()

def get_activity_count():
    """קבלת מספר הפעילים היום"""
    session = Session()
    try:
        today = date.today()
        count = session.query(Attendance).filter(
            Attendance.date == today
        ).distinct(Attendance.telegram_id).count()
        return count
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת מספר פעילים: {e}")
        return 0
    finally:
        session.close()

def get_user_activity_report(telegram_id, days=30):
    """קבלת דוח פעילות של משתמש"""
    session = Session()
    try:
        start_date = date.today() - timedelta(days=days)
        
        # צ'ק-אין
        checkins = session.query(Attendance).filter(
            Attendance.telegram_id == telegram_id,
            Attendance.date >= start_date
        ).all()
        
        # משימות
        tasks = session.query(TaskCompletion).filter(
            TaskCompletion.telegram_id == telegram_id,
            TaskCompletion.completed_at >= start_date
        ).all()
        
        # הפניות
        referrals = session.query(Referral).filter(
            Referral.referrer_id == telegram_id,
            Referral.created_at >= start_date
        ).all()
        
        return {
            'checkins': len(checkins),
            'tasks': len(tasks),
            'referrals': len(referrals),
            'tokens_earned': sum(c.tokens_earned for c in checkins) + sum(t.tokens_earned for t in tasks),
            'days_active': len(set(c.date for c in checkins))
        }
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת דוח פעילות: {e}")
        return {}
    finally:
        session.close()

# ========== פונקציות אדמין ==========

def add_tokens_to_user(telegram_id, amount, reason=None):
    """הוספת טוקנים למשתמש עם סיבה"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return False, 0, "משתמש לא נמצא"
        
        user.tokens += amount
        
        # רישום לעקביות
        if reason:
            # ניתן ליצור כאן טבלת היסטוריית טרנזקציות
            pass
        
        session.commit()
        
        return True, user.tokens, f"✅ נוספו {amount} טוקנים ל{user.first_name}"
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה בהוספת טוקנים: {e}")
        return False, 0, f"שגיאה: {str(e)}"
    finally:
        session.close()

def reset_user_checkin(telegram_id):
    """איפוס צ'ק-אין של משתמש"""
    session = Session()
    try:
        today = date.today()
        
        # מחק את רשומת הצ'ק-אין של היום
        attendance = session.query(Attendance).filter_by(
            telegram_id=telegram_id,
            date=today
        ).first()
        
        if attendance:
            # החזר את הטוקנים
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                user.tokens -= attendance.tokens_earned
                if user.tokens < 0:
                    user.tokens = 0
            
            session.delete(attendance)
            session.commit()
            return True, "✅ צ'ק-אין אופס בהצלחה"
        
        return False, "לא נמצא צ'ק-אין לאיפוס"
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה באיפוס צ'ק-אין: {e}")
        return False, f"שגיאה: {str(e)}"
    finally:
        session.close()

def broadcast_message_to_all():
    """קבלת כל משתמשי המערכת לשידור"""
    session = Session()
    try:
        users = session.query(User).all()
        user_ids = [user.telegram_id for user in users]
        
        return user_ids
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת רשימת משתמשים: {e}")
        return []
    finally:
        session.close()

def create_new_task(task_data):
    """יצירת משימה חדשה"""
    session = Session()
    try:
        task = Task(**task_data)
        session.add(task)
        session.commit()
        return True, task.id, "✅ משימה נוצרה בהצלחה"
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה ביצירת משימה: {e}")
        return False, None, f"שגיאה: {str(e)}"
    finally:
        session.close()

def get_user_leaderboard_position(telegram_id, category='tokens'):
    """קבלת מיקום המשתמש בטבלת המובילים"""
    session = Session()
    try:
        if category == 'tokens':
            # ספור כמה משתמשים עם יותר טוקנים
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if not user:
                return None
            
            position = session.query(User).filter(User.tokens > user.tokens).count() + 1
            total = session.query(User).count()
            
            return {
                'position': position,
                'total': total,
                'percentage': int((position / total) * 100) if total > 0 else 0
            }
        
        elif category == 'level':
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if not user:
                return None
            
            position = session.query(User).filter(
                or_(
                    User.level > user.level,
                    and_(User.level == user.level, User.experience > user.experience)
                )
            ).count() + 1
            
            total = session.query(User).count()
            
            return {
                'position': position,
                'total': total,
                'percentage': int((position / total) * 100) if total > 0 else 0
            }
        
        return None
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת מיקום בטבלה: {e}")
        return None
    finally:
        session.close()

# ========== פונקציות API ==========

def get_api_stats():
    """נתונים עבור API"""
    stats = get_system_stats()
    
    return {
        'status': 'success',
        'data': {
            'users': {
                'total': stats.get('total_users', 0),
                'active_today': stats.get('active_today', 0),
                'avg_tokens': stats.get('avg_tokens', 0),
                'avg_level': stats.get('avg_level', 0)
            },
            'tokens': {
                'total': stats.get('total_tokens', 0),
                'distribution': stats.get('level_distribution', {})
            },
            'activity': {
                'referrals': stats.get('total_referrals', 0),
                'tasks_completed': stats.get('total_tasks_completed', 0),
                'popular_tasks': stats.get('popular_tasks', [])
            },
            'timestamp': stats.get('timestamp', datetime.now().isoformat())
        }
    }

def search_users(query, limit=20):
    """חיפוש משתמשים לפי שם, שם משתמש או מזהה"""
    session = Session()
    try:
        from sqlalchemy import cast, String
        
        users = session.query(User).filter(
            or_(
                User.first_name.ilike(f"%{query}%"),
                User.last_name.ilike(f"%{query}%"),
                User.username.ilike(f"%{query}%"),
                cast(User.telegram_id, String).ilike(f"%{query}%")
            )
        ).limit(limit).all()
        
        return users
    except Exception as e:
        logger.error(f"❌ שגיאה בחיפוש משתמשים: {e}")
        return []
    finally:
        session.close()

def get_today_stats():
    """סטטיסטיקות להיום"""
    session = Session()
    try:
        today = date.today()
        
        # משתמשים חדשים היום
        new_users_today = session.query(User).filter(
            func.date(User.created_at) == today
        ).count()
        
        # צ'ק-אין היום
        checkins_today = session.query(Attendance).filter(
            Attendance.date == today
        ).count()
        
        # משימות שהושלמו היום
        tasks_completed_today = session.query(TaskCompletion).filter(
            func.date(TaskCompletion.completed_at) == today,
            TaskCompletion.status == TaskStatus.COMPLETED
        ).count()
        
        # הפניות חדשות היום
        new_referrals_today = session.query(Referral).filter(
            func.date(Referral.created_at) == today
        ).count()
        
        return {
            'new_users_today': new_users_today,
            'checkins_today': checkins_today,
            'tasks_completed_today': tasks_completed_today,
            'new_referrals_today': new_referrals_today
        }
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת סטטיסטיקות היום: {e}")
        return {
            'new_users_today': 0,
            'checkins_today': 0,
            'tasks_completed_today': 0,
            'new_referrals_today': 0
        }
    finally:
        session.close()

def get_streak_stats():
    """סטטיסטיקות רצפים"""
    session = Session()
    try:
        # רצף ממוצע
        all_users = session.query(User).all()
        streaks = []
        for user in all_users:
            streak = calculate_user_streak(user.telegram_id)
            streaks.append(streak)
        
        avg_streak = sum(streaks) / len(streaks) if streaks else 0
        
        # רצף מירבי
        max_streak = max(streaks) if streaks else 0
        
        # משתמשים עם רצף 7+ ימים
        users_with_7plus_streak = len([s for s in streaks if s >= 7])
        
        return {
            'avg_streak': round(avg_streak, 1),
            'max_streak': max_streak,
            'users_with_7plus_streak': users_with_7plus_streak
        }
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת סטטיסטיקות רצפים: {e}")
        return {
            'avg_streak': 0,
            'max_streak': 0,
            'users_with_7plus_streak': 0
        }
    finally:
        session.close()

def get_activity_stats():
    """סטטיסטיקות פעילות"""
    try:
        # שעות פעילות (הדמיית נתונים)
        return {
            'peak_hour': '09:00',
            'morning_activity': 35,
            'afternoon_activity': 45,
            'evening_activity': 20
        }
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת סטטיסטיקות פעילות: {e}")
        return {
            'peak_hour': '09:00',
            'morning_activity': 35,
            'afternoon_activity': 45,
            'evening_activity': 20
        }

# ========== פונקציות עזר נוספות ==========

def get_daily_stats():
    """סטטיסטיקות יומיות (alias ל-get_today_stats)"""
    return get_today_stats()

# ========== ייצוא פונקציות ==========
__all__ = [
    'init_database',
    'register_user', 'checkin_user', 'get_user', 'get_all_users',
    'get_balance', 'get_user_level_info', 'update_user_level',
    'get_top_users', 'calculate_user_streak',
    'get_user_referrals', 'get_total_referrals', 'get_referred_users',
    'get_user_attendance_history',
    'get_available_tasks', 'get_user_tasks', 'complete_task',
    'get_pending_tasks', 'approve_task', 'reject_task',
    'get_system_stats', 'get_checkin_data', 'get_activity_count',
    'get_user_activity_report',
    'add_tokens_to_user', 'reset_user_checkin', 'broadcast_message_to_all',
    'create_new_task', 'get_user_leaderboard_position',
    'get_api_stats', 'search_users',
    'get_today_stats', 'get_streak_stats', 'get_activity_stats',
    'get_daily_stats'
]

