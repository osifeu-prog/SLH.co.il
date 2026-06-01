# מה לעשות עכשיו — 2026-04-25
**Simple Hebrew checklist, step-by-step.**

אני (Claude) סיימתי את כל מה שאפשר אוטומטית. יש 4 דברים שאני לא יכול לעשות בלי הידיים שלך.

**כל המערכת מוכנה וחיה.** אחרי שתעשה את ה-4 דברים האלה, הבוט `@SLH_Claude_bot` יתחיל לעבוד ותוכל לשלוט על הכל מטלגרם.

---

## שלב 1 — Anthropic API Key (5 דקות) 🔑

**למה צריך:** בלי זה הבוט @SLH_Claude_bot לא יכול לעבוד. הוא צריך מפתח כדי לדבר עם Claude AI.

### מה לעשות:

1. לחץ כאן: **https://console.anthropic.com/**
2. התחבר או צור חשבון (אם עדיין אין לך)
3. בתפריט שמאל → **Settings** → **API Keys**
4. לחץ **"Create Key"**
5. תן שם: `SLH_Claude_Bot`
6. לחץ **"Create"**
7. **חשוב:** העתק את המפתח מיד! הוא מתחיל ב-`sk-ant-...` — אפשר לראות אותו רק פעם אחת.
8. פתח את הקובץ הזה ב-Notepad:
   ```
   D:\SLH_ECOSYSTEM\slh-claude-bot\.env
   ```
9. מצא את השורה:
   ```
   ANTHROPIC_API_KEY=
   ```
10. הדבק את המפתח אחרי ה-`=`. התוצאה:
    ```
    ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxx...
    ```
11. שמור (Ctrl+S) וסגור.

✅ **סיימת את שלב 1.**

---

## שלב 2 — הפעל את Docker Desktop (2 דקות) 🐳

**למה צריך:** ה-bot fleet רץ ב-Docker. בלי Docker אין בוטים.

### מה לעשות:

1. לחץ **Start** (כפתור Windows)
2. הקלד **Docker Desktop**
3. לחץ Enter
4. חכה 60-90 שניות עד שהאייקון של Docker בשורת המשימות (ליד השעון) הופך למוצק לבן (לא מהבהב)
5. אם קופץ לך חלון שמבקש לעדכן / לאשר רישיון — תלחץ **Accept / Update**
6. בסוף — לחץ ימני על האייקון → **Dashboard** → וודא שכתוב "Engine running"

✅ **סיימת את שלב 2.**

---

## שלב 3 — הפעל את ה-bot fleet (1 דקה) 🤖

**למה צריך:** עכשיו כשיש Docker + Anthropic Key, נפעיל את הבוטים.

### מה לעשות:

1. לחץ **Start** → הקלד **PowerShell** → לחץ Enter
2. העתק והדבק את הפקודה הזו (לחץ Enter אחרי):
   ```powershell
   cd D:\SLH_ECOSYSTEM
   docker compose up -d postgres redis
   ```
3. חכה 15 שניות
4. הדבק את זה:
   ```powershell
   docker compose up -d claude-bot guardian-bot
   ```
5. חכה 10 שניות
6. הדבק את זה לבדוק:
   ```powershell
   docker ps --format "table {{.Names}}\t{{.Status}}"
   ```

אתה אמור לראות 4 שורות:
```
slh-postgres      Up 30 seconds (healthy)
slh-redis         Up 30 seconds (healthy)
slh-claude-bot    Up 5 seconds
slh-guardian-bot  Up 5 seconds
```

### אם claude-bot נכבה מיד:
```powershell
docker logs slh-claude-bot --tail 20
```
תדביק לי את הפלט ונתקן.

✅ **סיימת את שלב 3.**

---

## שלב 4 — בדיקת שהבוט עונה (30 שניות) 📱

### מה לעשות:

1. פתח טלגרם
2. חפש: **@SLH_Claude_bot**
3. לחץ **Start** או שלח: `/start`
4. שלח הודעה: **"בדוק אילו בוטים רצים עכשיו"**
5. חכה 10-30 שניות

**אם הבוט עונה** = המערכת פועלת. השליטה עברה אליך מטלגרם. 🎉

**אם לא עונה** = בדוק את הלוגים:
```powershell
docker logs slh-claude-bot --tail 30
```
ותדביק לי את הפלט.

✅ **סיימת הכל.**

---

## שלבים עתידיים (לא דחופים, אבל מומלצים)

### שלב 5 — Railway Redeploy (30 שניות)
**למה:** יש commits שלא הסתנכרנו עם Railway בגלל פריסה תקועה מ-21.4.

1. לחץ: **https://railway.app/**
2. כנס לפרויקט `slh-api`
3. לחץ **Deployments** (בתפריט)
4. לחץ **"Redeploy"** על הפריסה האחרונה
5. חכה 2-3 דקות

### שלב 6 — סיבוב טוקני בוטים (30 דקות)
**למה:** 31 טוקנים נחשפו בהיסטוריית הצ'אט ודולפים. צריך לחדש.

קרא את [COMMAND_CENTER_SETUP_20260424.md חלק ז](/ops-viewer.html?file=COMMAND_CENTER_SETUP_20260424.md) — שם יש הנחיות מלאות לכל 25 הבוטים.

### שלב 7 — Alignment של סוכן Guardian ESP (אם עדיין פעיל)
**למה:** היה לך סוכן מקביל שבנה מערכת preorder עם חפיפה לעבודה שלי.

1. פתח: [/ops/AGENT_ALIGNMENT_PROMPT_GUARDIAN_ESP.md](/ops-viewer.html?file=AGENT_ALIGNMENT_PROMPT_GUARDIAN_ESP.md)
2. העתק את הבלוק `Copy-paste block starts here ↓`
3. הדבק לסוכן הזה (טלגרם / צ'אט)
4. הוא יתאם או יעצור

---

## בדיקה סופית — המערכת המלאה פועלת

אחרי שלבים 1-4, תוודא:

- [ ] [https://slh-nft.com/command-center.html](https://slh-nft.com/command-center.html) — נפתח, 6 sections, 24 tiles
- [ ] לחיצה על preset "Overview" → 5 חלונות נפתחים למסכים שונים
- [ ] @SLH_Claude_bot בטלגרם → `/start` → עונה
- [ ] שליחת פקודה → הבוט מריץ ועונה
- [ ] `docker ps` → לפחות 4 containers רצים

**אם כל אלו ✅ — המערכת מושלמת.**

---

## מה אני סיימתי אוטונומי (סה"כ עד כה)

✅ Website: voice.html, swarm.html, command-center.html, ops-viewer.html — LIVE
✅ Network/Roadmap/Project-map — מעודכנים
✅ 8 ops docs פומביים עכשיו ב-/ops/ (viewable דרך ops-viewer)
✅ תיקון באג שעון ב-admin.html (שעון מלא עם תאריך, TZ, ו-sync vs server)
✅ כל ה-commits נדחפו ל-2 ה-git repos
✅ Alignment prompt מוכן לסוכן המקביל

**9 commits בסה"כ**, 5 דפים חדשים/מעודכנים, 8 ops docs.

**הבלוקרים הנותרים דורשים רק את הידיים שלך. אחרי 8-10 דקות של עבודה — הכל יהיה LIVE.**

---

**עדכן אותי אחרי שעשית את 4 השלבים הראשונים.** אם משהו לא עובד — תדביק לי את הפלט של הפקודה ונתקן.

*Claude Opus 4.7 · 2026-04-25*
