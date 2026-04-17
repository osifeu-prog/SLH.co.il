# 🛌 לפני שאתה הולך לישון · Checklist מינימלי
> **12 דקות סך הכל. אחרי זה אתה חופשי.**
> אוסיף, עשה רק את אלו — כל השאר יכול לחכות או אני אטפל בזה.

---

## ⏱ Phase 1 · חסמי-מערכת (5 דק') — חובה

### ☐ 1. Railway · סיבוב ADMIN_API_KEYS (2 דק')
1. פתח [railway.app](https://railway.app) → פרויקט **slh-api** → Variables
2. ערוך `ADMIN_API_KEYS` והוסף את המפתח החדש לפני הישן (פסיק ביניהם):
   ```
   slh_admin_hgaBj2T9k8T8Hmm5pC_794J-4UaDG6ce,slh2026admin
   ```
3. **Save** — Railway יפרוס אוטומטית (~2 דק')
4. ✅ סיום

### ☐ 2. Railway · SILENT_MODE=1 kill-switch (1 דק')
באותו מסך Variables, הוסף משתנה חדש:
```
SILENT_MODE = 1
```
**Save**. זה ישתיק התראות טלגרם עד שתחזיר ל-`0`.

### ☐ 3. localStorage · עדכן דפדפן (2 דק')
1. פתח [slh-nft.com/admin.html](https://slh-nft.com/admin.html)
2. Logout → Login עם המפתח החדש: `slh_admin_hgaBj2T9k8T8Hmm5pC_794J-4UaDG6ce`
3. ✅ אם נכנסת, הרוטציה עובדת. עברה.

---

## ⏱ Phase 2 · החלטות מהירות (3 דק')

### ☐ 4. שני קבצים ב-working tree
פתח: [ops/REGRESSIONS_FLAG_20260417.md](https://github.com/osifeu-prog/slh-api/blob/master/ops/REGRESSIONS_FLAG_20260417.md)

ענה לי על שתי שאלות (בשורה אחת כל אחת, אשאל בבוקר):
- **docker-compose.yml** (ירד מ-25 שירותים ל-3): **revert** / **keep-minimal** / **split-to-two-files**?
- **shared/bot_template.py** (ירד ל-52 שורות, עם באג): **revert** / **keep** / **rename-to-ledger-bot.py**?

### ☐ 5. טוקן-סדר-עדיפויות לילה הבא
בחר סדר **1-4**, יכול להיות גם רק אחד:
- [ ] **SLH #1** — TON auto-verify + premium approve backlog
- [ ] **MNH #2** — peg dashboard + מסלול exchange
- [ ] **ZVK #3** — mass-gift + referrals + daily cron
- [ ] **REP #4** — tier rules + community voting UI

ברירת מחדל אם לא תענה: **SLH #1 exclusive** (הכי דחוף, מכניס כסף).

---

## ⏱ Phase 3 · רשות — אם יש לך עוד 4 דקות

### ☐ 6. BotFather — הגדרת פקודות ל-3 בוטים הפעילים (4 דק')
פתח [t.me/BotFather](https://t.me/BotFather) → `/setcommands` → בחר בוט → הדבק:

**SLH_Ledger / Campaign_SLH / SLH_AIR** (אותן פקודות לשלושתם):
```
start - התחלה
help - עזרה
status - מצב חשבון
mylink - קישור הפניה
premium - שדרוג
```

---

## ❌ אל תעשה עכשיו (זה יחכה):
- ❌ סיבוב 31 טוקני בוט (יקח 30+ דק' — מחר)
- ❌ קומיט של 56 הקבצים הלא-מקומטים (סיכון, בלי בדיקה)
- ❌ Twilio signup (צריך כרטיס אשראי — מחר)
- ❌ ESP32 debugging (Core Assistant יעבוד על זה)

---

## 🎛 איך תבדוק את המצב כשאתה מתעורר

**פאנל אחד לכל המערכת:** [slh-nft.com/mission-control.html](https://slh-nft.com/mission-control.html)

- מציג Live API / DB / Railway / Git
- KPIs חיים (users / premium / bots / endpoints)
- 5 טוקנים + התקדמות
- חסמים פתוחים
- Kernel Orders (הפקודות שמזינות את הלב)
- פעולות מהירות

**כל הקבצים שעניינו אותך:**
- [SESSION_STATUS.md](https://github.com/osifeu-prog/slh-api/blob/master/ops/SESSION_STATUS.md) — Single Source of Truth
- [MORNING_REPORT_20260417](https://github.com/osifeu-prog/slh-api/blob/master/ops/MORNING_REPORT_20260417.md)
- [TEAM_TASKS.md](https://github.com/osifeu-prog/slh-api/blob/master/ops/TEAM_TASKS.md)

---

## 🤖 לגבי "אתה עובד על טוקן 1 במשך 19 שעות"

**תיאום ציפיות — אני לא רץ אוטונומית בזמן שאתה ישן.**

Claude Code עובד רק כש-CLI פתוח ואתה מקליד / מאשר. כשתסגור את המסוף — אני נעצר עד שתחזור.

**3 דרכים אפשריות ל-autonomous night:**

### אופציה A · Auto-approve + השארת המסוף פתוח (הכי קל)
- השאר את Claude Code רץ
- אני אעבוד על רשימת משימות מוגדרת מראש
- תסכן ~2-5% שגיאה שתדרוש אישור — המסוף יחכה עד שתחזור

### אופציה B · Scheduled Cron (Claude Code יש)
- אני יוצר Cron שירוץ כל 30-60 דק'
- בכל ריצה: health check + קומיט אם יש משהו מוכן + לוג
- לא טוב ליצירת תוכן גדול, טוב לניטור

### אופציה C · לעבוד רצוף עכשיו במשך 90-120 דק' עד שתירדם
- אני סוגר עכשיו SLH #1 tasks מקסימום בכמות שאפשר
- אתה רואה את זה קורה
- כשתירדם אני עוצר — אבל הרבה כבר יהיה סגור

**המלצה שלי:** אופציה C. אתה חוסך 19 שעות של דאגה — מה שסגרתי אני סגרתי, מה שלא — בבוקר נמשיך.

---

**תגיד לי מה בחרת ואני זז.** אין חובה לענות על הכל — רק מה שרלוונטי לך.
