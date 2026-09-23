# SLH — Status & Handoff

## עדכון אחרון: 2026-09-23

## מה השתנה היום
- Railway: אובחן ותועד שירות `slh-fastapi` (diligent-radiance) כננטש — לא נמחק, יש תעבורה פעילה לא מוסברת (134 בקשות/7 ימים).
- האתר: זוהתה בעיה מהותית — דף הבית ממוקד IDO/משקיעים, לא קהילה. נבנה ופורסם פרוטוטייפ `community.html`.
- Deployment: הוקם pipeline מלא Termux → GitHub (gh auth) → Railway auto-deploy. עובד.
- RBAC בבוט "Me" (SLH_PROJECT_V2): אומת — הרשאה בינארית פשוטה ב-`app/core/admin_guard.py` (`ADMIN_USER_ID` יחיד). צביקה = DEVELOPER (legacy/env), לא OWNER.
- המערכת המתקדמת (`/dev_list`, `/e alpha_status`, OWNER/ADMIN/DEVELOPER) — הקובץ שמריץ אותה עדיין לא אותר בקוד.

## מה פתוח / לא סגור
- קובץ הלוגיקה של `/dev_list` + `/e` + OWNER/DEVELOPER tiers — לא נמצא עדיין ברשימת `find` המלאה.
- `community.html` — המשתמש דיווח "מבולגן" בתצוגה חיה, לא אובחן סופית.
- שאלת "כמה כוכבים הרווחתי" (Telegram Stars) — טרם נבדק (`getStarTransactions`).
- SOW/הצעת מחיר למפתח — טרם נשלחה, ממתין למיפוי scope מול תוצרים.

## הצעד הבא
- להריץ find מלא ב-SLH_PROJECT_V2 כדי לאתר את קובץ ה-authority/roles האמיתי.
