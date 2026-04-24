# SLH.co.il — Runbook

**מטרה:** עמוד אחד להפעלה יומית. לא לקריאה — לפתיחה, להעתקה, להדבקה.

## 🩺 בדיקת בריאות — הפעלה יומית
```powershell
cd D:\SLH.co.il
pwsh ops\verify.ps1
```
מה הוא בודק: token getMe · DB connect · website HTTP 200 · לוגי Railway נקיים מ-409 · preorders table.

## 🚀 Deploy
```powershell
# שיטה ראשית (git push triggers Railway auto-deploy)
cd D:\SLH.co.il
git add <files>
git commit -m "your message"
git push origin main

# שיטה חלופית (deploy ישיר גם בלי commit)
railway up --detach
```
אימות:
```powershell
railway logs --build | Select-Object -Last 5     # בנייה
railway logs | Select-Object -Last 10            # runtime
```

## 🔐 רוטציית טוקן בוט
ראה `ops\rotate-token.md` למדריך שלב-אחר-שלב.
**Quick path**: BotFather → `/mybots` → `SLH_macro_bot` → API Token → Revoke → Railway Shared Variables → עדכן ערך → redeploy אוטומטי.

## 📊 שאילתות DB מהירות
```powershell
# ספירת משתמשים
railway run python -c "import os,psycopg2; c=psycopg2.connect(os.getenv('DATABASE_URL')).cursor(); c.execute('SELECT COUNT(*) FROM users'); print(c.fetchone()[0])"

# הזמנות מוקדמות שלא טופלו
railway run python -c "import os,psycopg2; c=psycopg2.connect(os.getenv('DATABASE_URL')).cursor(); c.execute(\"SELECT id,user_id,username,created_at FROM preorders WHERE status='interested' ORDER BY created_at DESC\"); [print(r) for r in c.fetchall()]"

# משוב אחרון
railway run python -c "import os,psycopg2; c=psycopg2.connect(os.getenv('DATABASE_URL')).cursor(); c.execute('SELECT id,user_id,message,timestamp FROM feedback ORDER BY id DESC LIMIT 10'); [print(r) for r in c.fetchall()]"
```

## 👑 קידום משתמש לאדמין
```powershell
# החלף 123456 ב-telegram_id האמיתי
railway run python -c "import os,psycopg2; c=psycopg2.connect(os.getenv('DATABASE_URL')); cur=c.cursor(); cur.execute('UPDATE users SET is_admin=TRUE WHERE user_id=%s', (123456,)); c.commit(); print('granted')"
```

## 🔄 Rollback (אם deploy חדש שבר משהו)
```powershell
# מצא את ה-commit הקודם שעבד
git log --oneline -10

# חזור בקוד
git revert <bad-commit-sha>
git push origin main

# OR: פריסה ידנית של deploy ישן ב-Railway dashboard (Deployments tab → הפעלה מחדש)
```

## 🧪 הרצה מקומית (debug)
```powershell
cd D:\SLH.co.il
# טען env מ-Railway (בלי להדפיס סודות)
$env:TELEGRAM_BOT_TOKEN = (railway run --service monitor.slh -- powershell -Command "echo `$env:TELEGRAM_BOT_TOKEN")
$env:DATABASE_URL = (railway run --service monitor.slh -- powershell -Command "echo `$env:DATABASE_URL")
python bot.py
# CTRL+C לעצירה
```
⚠️ **אזהרה:** הבוט הלוקלי יתחרה עם הבוט ב-Railway (409 Conflict). הרץ מקומי רק אם עצרת את monitor.slh ב-Railway dashboard תחילה.

## 🧹 ניקוי
```powershell
# עצירת preview servers מקומיים
Get-Process python | Where-Object { $_.StartTime -lt (Get-Date).AddDays(-1) } | Stop-Process -Force

# בדיקת קבצי סודות שוכבים
git status --ignored | Select-String -Pattern "\.env|secret|token|key" -CaseSensitive:$false
```

## 🆘 כשהבוט נפל
1. `pwsh ops\verify.ps1` — מה בדיוק שבור?
2. אם 401: → `ops\rotate-token.md` (כנראה token)
3. אם 409: → בדוק ב-Railway אם יש service נוסף שרץ (צריך להיות רק monitor.slh)
4. אם DB error: → `railway logs | Select-String -Pattern "psycopg|SQL|column"` וחפש את השגיאה המדויקת
5. אם build failed: → `railway logs --build | Select-Object -Last 30` וחפש `error`
6. אם לא אחד מהנ"ל: → שמור screenshot של `railway logs` → שלח ל-Claude (אני) עם "הבוט נפל, הנה הלוגים"

## 📞 משאבים חיצוניים
- BotFather: https://t.me/BotFather
- Railway dashboard: https://railway.app/project/97070988-27f9-4e0f-b76c-a75b5a7c9673
- GitHub repo: https://github.com/osifeu-prog/SLH.co.il
- Status page: https://www.slh.co.il (home) + https://www.slh.co.il/guardian.html (pre-order)
