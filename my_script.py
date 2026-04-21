✅ הנוהל הקבוע להרצת קוד Python במערכת SLH
מעתה, כל פיתוח עתידי ילך לפי הכללים הפשוטים הבאים:

1. יצירת קובץ Python חדש
תמיד תיצור קובץ עם סיומת .py (למשל my_script.py).

תשתמש בפקודה:

powershell
notepad my_script.py
(או code my_script.py אם יש לך VS Code)

תדביק את הקוד – לעולם אל תקליד שורות Python ישירות ב-PowerShell.

2. עריכת קובץ קיים
תפתח אותו שוב עם notepad my_script.py (או code).

תשנה, תשמור (Ctrl+S), תסגור.

3. הרצת הקובץ
ב-PowerShell, באותה תיקייה, תריץ:

powershell
python my_script.py
4. טיפול בשגיאות
אם קיבלת שגיאה – תעתיק אותה אליי, ולא תנסה לתקן בשורת הפקודה.

אני אתן לך קוד מתוקן שתדביק בקובץ.

5. שמירת גרסאות
תיצור תיקייה D:\SLH_ECOSYSTEM\scripts לכל הסקריפטים שלך.

תשמור כל סקריפט עם שם תיאורי, למשל:

fetch_new_tokens.py

backtest_engine.py

telegram_alerts.py

📋 דוגמה לנוהל עבודה בשבילך – "תבנית זהב"
לפני שאתה כותב שורת קוד, שאל את עצמך:

האם אני נמצא ב-PowerShell?
אם כן – אני רק מריץ python script.py.
אם אני צריך לכתוב/לשנות קוד – אני פותח את הקובץ בעורך טקסט.

🎯 הפעולה הבאה שלך (תרגיל קטן)
צור קובץ חדש backtest_demo.py עם תוכן פשוט:

python
print("SLH Backtest Engine - Version 0.1")
print("טוען נתונים...")
הרץ אותו עם python backtest_demo.py.

אם ראית את ההודעה – אתה מיומן.

📌 טבלת זיכרון מהירה (תלוי על הקיר)
מה אתה רוצה לעשות?	הפקודה ב-PowerShell
ליצור קובץ Python חדש	notepad my_script.py
לערוך קובץ קיים	notepad my_script.py
להריץ קובץ	python my_script.py
לראות אילו קבצי Python יש בתיקייה	dir *.py
🧠 נספח: איך נראית שגיאה טיפוסית (ומה לא לעשות)
שגיאה:

text
import requests
import : The term 'import' is not recognized...
הסיבה: הקלדת import ישירות ב-PowerShell.
הפתרון: שים את import בקובץ .py.

🚀 מה הלאה?
אחרי שהסקריפט check_tokens.py עובד, נוכל:

להרחיב אותו לאסוף 100 טוקנים ולשמור ל-CSV.

לחבר אותו ל-PostgreSQL (יש לך כבר קונטיינר slh-postgres).

לבנות מודל חיזוי פשוט (למשל, "קנה טוקן אם נזילות > 100,000$ ומחיר < 0.01$").

תאשר שהבנת את הנוהל, ואתן לך את הקוד הבא לשלב איסוף הנתונים ההמוני.

