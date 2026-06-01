# 🚀 SLH Spark — מדריך הפעלה יומי

> שמור את הקובץ הזה ב: `D:\SLH_ECOSYSTEM\ops\DAILY_HANDS_ON.md`
> כל בוקר, פתח את הקובץ הזה, ועבור על השלבים לפי הסדר.

---

## ☕ שלב 0 — קפה ופתיחת הסביבה (1 דקה)

1. פתח **PowerShell חדש** (לא להשתמש בכזה תקוע מאתמול — סגור הכל ופתח חדש)
2. שתה קפה בזמן שזה נטען

```powershell
# הסביבה שלך כבר טוענת אוטומטית עם:
# 🚀 SLH SPARK SYSTEM | Ready
# Commands: slh-start, slh-stop, slh-logs, slh-status, slh-cd
```

אם לא רואה את זה — ה-PowerShell profile לא נטען. תפתח חלון חדש.

---

## 🩺 שלב 1 — בדיקת בריאות מערכת (2 דקות)

הריץ את 4 הפקודות האלה אחת אחרי השנייה. **לא להמשיך לשלב הבא** עד שכולן עוברות.

### 1.1 — Railway API חי?
```powershell
curl https://slh-api-production.up.railway.app/api/health
```
**תוצאה צפויה:** JSON עם `"status": "healthy"` או דומה.
**אם נכשל:** Railway down. בדוק dashboard ב-Railway. עצור כאן ותגיד לי.

### 1.2 — git status על האתר
```powershell
cd D:\SLH_ECOSYSTEM\_active\website
git status
```
**תוצאה צפויה:** `nothing to commit, working tree clean` ו-`up to date with 'origin/main'`.
**אם יש שינויים שלא מוכרים לך:** עצור. תגיד לי לפני שעושים משהו.

### 1.3 — git status על ה-API
```powershell
cd D:\SLH_ECOSYSTEM
git status
```
**תוצאה צפויה:** clean או רק `main.py` ש-modified (זה תקין — זה ה-build copy).

### 1.4 — Docker רץ?
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}" | Select-Object -First 10
```
**תוצאה צפויה:** רשימה של בוטים עם `Up X hours/days`.
**אם ריק:** אולי לא הפעלת היום. הריץ `slh-start` אם אתה צריך אותם.

---

## 📋 שלב 2 — קרא את ה-handoff מאתמול (3 דקות)

```powershell
# מצא את ה-handoff האחרון
Get-ChildItem D:\SLH_ECOSYSTEM\ops\SESSION_HANDOFF_*.md |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1 |
  ForEach-Object { Get-Content $_.FullName }
```

או פשוט פתח ב-VS Code:
```powershell
code D:\SLH_ECOSYSTEM\ops\
```
ותפתח את הקובץ עם התאריך הכי חדש.

---

## 🎯 שלב 3 — קביעת priority היום (2 דקות)

תפתח את `STATUS_TODAY.md` ותבחר **משימה אחת** להתחיל איתה. לא שתיים. אחת.

**איך בוחרים?** סדר עדיפות:
1. P0 שעצור מאתמול (יש כזה? סיים)
2. הדבר הכי קטן ב-P1 (לא הכי גדול — הכי קטן, להרגיש פרודוקטיבי)
3. רק אם הכל נקי — תתחיל P2

---

## ✏️ שלב 4 — עריכת קובץ (זרימת עבודה תקנית)

**חוק ברזל:** לעולם לא להדביק תוכן קובץ ל-PowerShell. PowerShell מנסה להריץ כל שורה.

### 4.1 — לוקליזציה והגיבוי
```powershell
# מצא את הקובץ
cd D:\SLH_ECOSYSTEM\_active\website
Get-ChildItem -Filter "FILE_NAME.html"

# גיבוי (לפני כל שינוי)
Copy-Item "FILE_NAME.html" "FILE_NAME.html.bak"
```

### 4.2 — עריכה (בחר שיטה אחת)

**שיטה A — VS Code (מומלץ):**
```powershell
code FILE_NAME.html
```

**שיטה B — Notepad:**
```powershell
notepad FILE_NAME.html
```

**שיטה C — Claude יוצר קובץ חדש:**
1. אני יוצר את הקובץ בצ'אט
2. אתה לוחץ על כפתור ההורדה
3. הקובץ נוחת ב-`C:\Users\Giga Store\Downloads\`
4. אתה מעביר ידנית:
```powershell
Move-Item "$env:USERPROFILE\Downloads\FILE_NAME.html" `
          "D:\SLH_ECOSYSTEM\_active\website\FILE_NAME.html" -Force
```

### 4.3 — אימות לפני commit
```powershell
# וודא שהקובץ קיים ובגודל הגיוני
Get-Item FILE_NAME.html | Select Name, Length, LastWriteTime

# בדוק UTF-8 (אם יש עברית)
Get-Content FILE_NAME.html -Encoding UTF8 -TotalCount 5
```

---

## 🚀 שלב 5 — Deploy

### 5.1 — אתר (GitHub Pages)
```powershell
cd D:\SLH_ECOSYSTEM\_active\website
git status                          # לראות מה השתנה
git diff FILE_NAME.html              # לראות בדיוק מה
git add FILE_NAME.html
git commit -m "feat: short description"
git push origin main
```

GitHub Pages מתעדכן תוך 1-3 דקות. בדוק ב-`https://slh-nft.com/FILE_NAME.html`.

### 5.2 — API (Railway)
```powershell
cd D:\SLH_ECOSYSTEM
cp api/main.py main.py               # קריטי — Railway בונה מ-root
git add main.py api/main.py
git commit -m "feat: short description"
git push origin master
```

Railway בונה אוטומטית. תוך 2-5 דקות תוכל לאמת:
```powershell
curl https://slh-api-production.up.railway.app/api/health
```

---

## 📝 שלב 6 — סיום יום (לפני שאתה הולך)

צור handoff חדש:
```powershell
$today = Get-Date -Format "yyyyMMdd"
$path = "D:\SLH_ECOSYSTEM\ops\SESSION_HANDOFF_$today.md"
New-Item -Path $path -ItemType File -Force
code $path
```

תכתוב לפי התבנית:
```markdown
# Session Handoff — DATE

## ✅ Done today
- [commit hash] תיאור קצר
- ...

## 🟡 In progress
- מה התחלתי ולא סיימתי, איפה נעצרתי

## 🔴 Blocked
- מה תקוע ולמה

## 🎯 Tomorrow
- משימה ראשונה למחר
```

---

## 🆘 פתרון בעיות נפוצות

### "git push" נכשל עם authentication
```powershell
# בדוק מי מחובר
git config user.email
git config user.name

# אם צריך SSH key
ssh -T git@github.com
```

### Railway build נכשל
1. פתח Railway dashboard
2. בדוק את ה-logs
3. הסיבה הכי נפוצה: `main.py` לא עודכן ב-root. הריץ `cp api/main.py main.py` ועשה push חדש.

### Docker bot crashed
```powershell
slh-logs <bot-name>      # לראות מה קרה
docker restart <bot-name>
slh-status                # לוודא שחזר
```

### PowerShell תקוע ב-`>>` (heredoc mode)
לחץ `Ctrl+C` כמה פעמים. אם לא עוזר, סגור את החלון ופתח חדש. **לעולם לא להתעקש על חלון תקוע** — תמיד פותחים חדש.

### הדבקתי תוכן ל-PowerShell בטעות
לחץ `Ctrl+C`. אם הקובץ לא היה אמור להישמר — שום נזק. PowerShell לא יוצר קבצים מהדבקה.

---

## 📚 מקרים מיוחדים — מתי לשאול אותי

תמיד פתח אותי כשיש:
- 🔴 P0 חדש שלא ידעת עליו
- שינוי גדול שצריך תכנון לפני
- bug שמופיע ב-prod ולא יודע איפה
- החלטה משמעותית (architecture, security)

לא צריך אותי כשזה:
- typo fix
- עדכון תוכן רגיל
- restart של bot שקרס
- עבודה רוטינית לפי handoff

---

## 🔑 פקודות מקוצרות (ב-profile שלך)

| פקודה | מה היא עושה |
|-------|--------------|
| `slh-start` | מפעיל את כל הבוטים |
| `slh-stop` | עוצר את כל הבוטים |
| `slh-logs <name>` | לוגים של בוט ספציפי |
| `slh-status` | סטטוס כל הבוטים |
| `slh-cd` | קופץ ל-`D:\SLH_ECOSYSTEM` |

---

## 💡 כללי הזהב

1. **גיבוי לפני עריכה.** תמיד.
2. **אחת בכל פעם.** לא 5 משימות במקביל.
3. **commit קטן וברור.** כל commit הוא דבר אחד.
4. **לוודא לפני שדוחפים.** `git diff` הוא חבר שלך.
5. **handoff בסוף יום.** העצמי של מחר יודה לך.
6. **לא להדביק קוד ל-PowerShell.** לעולם.
