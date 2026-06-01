# 🌙 NIGHT BRIEF — 2026-04-17
> **Read this first. Then execute. No role debates.**
> Goal: maximize SLH token adoption + revenue by morning.

## 🎯 המטרה היחידה הלילה
**הזזת הזרם הכלכלי.** לא בניית כלים חדשים. לא דיון על תפקידים. לסגור 1 רכישה חדשה היום + לתקן את ה-bottleneck שחסם את זה.

---

## 📊 מצב אמיתי (DB facts — לא ניחושים)
```
18 users | 9 premium approved | 10 TON staked | 0 deposits | 20 bots live
```
- **יש הכנסות.** יש 9 משלמים. אל תתייחס לזה כ"אין קניות" — יש.
- **הגידול עצר.** כי ה-flow שבור:
  `user → TON → screenshot → 24h manual wait → forgotten`

## 🚫 מה לא לעשות הלילה (anti-patterns שראיתי)
1. **אל תבנה Agents Control Plane.** ה-Core Assistant עובד על זה. אני לא.
2. **אל תדון בתפקידי סוכנים.** יש כבר AGENT_REGISTRY.json + SYNC_PROTOCOL.md. די.
3. **אל תחזור בוטים שהפסקתי** (core/admin/ton-mnh/campaign/nifti/nfty) — הם עוד שבורים.
4. **אל תבקש את admin key של Railway.** אם הוא סוד — אוסיף יריץ את ה-queries עצמו.
5. **אל תוסיף תכונות.** רק תקן את ה-flow הקיים.
6. **אל תשלח הודעות טלגרם יזומות** (SILENT_MODE=1 ב-Railway אם עדיין לא הוגדר).

## ✅ סדר עדיפויות הלילה (3 פעולות, לפי סדר)

### 1. מצא את הpending payments (10 דק')
- אוסיף: הרץ זה ב-PowerShell עם admin key מ-Railway:
  ```bash
  curl -s "https://slh-api-production.up.railway.app/api/admin/bank-transfers" -H "X-Admin-Key: <REAL_KEY>" | jq .
  curl -s "https://slh-api-production.up.railway.app/api/admin/payments/list" -H "X-Admin-Key: <REAL_KEY>" | jq .
  ```
- הדבק את הפלט לסשן → נדע כמה תקועים + מי + כמה זמן

### 2. סגור backlog ידנית (20 דק')
- כל תשלום ש-TX בתי התקבל בפועל → אשר ב-`/admin.html`
- כל אחד שמחכה מעל 2 ימים — שלח לו הודעה: "הפעלנו לך + בונוס 50 ZVK על ההמתנה"
- **זו המכירה הראשונה של הלילה** — 0 code נדרש

### 3. תקן את ה-bottleneck לצמיתות (20 דק')
- `POST /api/payment/ton/auto-verify` endpoint חדש
  - Input: `{ user_id, tx_hash, amount_ton }`
  - מאמת on-chain דרך toncenter.com API
  - מאשר premium אוטומטית תוך 30 שניות
- במקום "24 שעות" → "אישור מיידי אחרי ששלחת TON"

---

## 📏 כללי יעילות טוקנים (אני + כל סוכן)
1. **תגובות מתחת ל-150 מילים** אלא אם התבקש אחרת
2. **אל תחזור על מה שכבר נאמר** בשיחה
3. **אל תצטט חזרה פרומפטים** של סוכנים אחרים — אתה יודע את התפקיד שלך
4. **קובץ אחד לא 5** — אם יש 5 files עם אותו מידע, נתק את הכי טרי ומחק האחרים
5. **לפני שיוצרים file חדש** — בדוק אם יש דומה ב-ops/
6. **פעולה לפני דיון** — אם אפשר לעשות ב-30 שניות, תעשה. תסביר אחרי.

## 🧠 מה שהסוכן המרכזי חייב לדעת
1. **השליטה אצל אוסיף.** לא אצלי, לא אצל Core, לא אצל ChatGPT-Architect. אוסיף מחליט.
2. **DB עכשיו = source of truth** — לא mental models ישנים.
3. **ה-admin key הדיפולטי לא עובד** (Railway יש מפתח חדש). אוסיף צריך להזין ידנית את ה-commands החשובים.
4. **שני repos:** root (api/railway) + website (gh-pages). **ה-root תוקן היום**, master tracking נכון.
5. **SILENT_MODE = kill switch** אם משהו יתחיל לשלוח הודעות.
6. **Ledger bot עובד** (Premium flow — seen in Telegram). **שאר 19 בוטים:** 6 עצורים, 14 עולים + חלקם בעייתיים.

## ✅ Exit criteria (מתי אפשר להגיד "הלילה הצליח")
- [ ] 1+ תשלום חדש שחכה שאושר
- [ ] /api/payment/ton/auto-verify חי או לפחות spec מאושר לבוקר
- [ ] אוסיף רואה את מספר המכירות עולה ב-/api/stats
- [ ] לא נוסף ספאם טלגרם

## 🛑 Exit criteria (מתי לעצור הלילה)
- אוסיף אומר "עוצר"
- שעה 04:00 בבוקר
- Railway down
- שגיאה קריטית בפרודקשן לא מתוקנת תוך 15 דק'

---

**מעודכן:** 2026-04-17 02:25
**עדכון הבא:** אחרי שאוסיף מריץ את curl + מדביק פלט.
