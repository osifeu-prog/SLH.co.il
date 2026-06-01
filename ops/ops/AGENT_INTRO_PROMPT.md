# 🤝 Agent Onboarding Prompt (paste-ready)

> Copy this block and send it as the FIRST message to any new AI agent working on the SLH ecosystem.
> Works with Claude Code, Cursor, Aider, Codex, local Claude, etc.

---

## Prompt to paste:

```
אתה מצטרף לצוות מפתחים של SLH Spark — מערכת השקעות קריפטו ישראלית של אוסיף אונגר (סולו-דיוולופר).
הצוות כולל מספר סוכני AI שעובדים במקביל. קריטי לסנכרון.

לפני שאתה עושה שום דבר:
1. קרא את: D:\SLH_ECOSYSTEM\ops\AGENT_CONTEXT.md  ← מפת דרכים + מצב חי
2. קרא את: D:\SLH_ECOSYSTEM\CLAUDE.md             ← כללי עבודה + סודות
3. הרץ: curl https://slh-api-production.up.railway.app/api/health
4. הרץ בשני ה-repos: git status --short  +  git log -1 --oneline
   - D:\SLH_ECOSYSTEM (root → Railway)
   - D:\SLH_ECOSYSTEM\website (→ GitHub Pages)

תקשורת:
- הבעלים (אוסיף) מדבר עברית. תשובות שלך בעברית קצרות וישירות.
- קוד + commits באנגלית.
- "כן לכל ההצעות" = המשך עם כל ההצעות.

כללים קריטיים:
- אל תגע בקבצי .env — הם gitignored ומכילים 31 טוקנים
- Railway בונה מ-ROOT main.py, לא מ-api/main.py. כל edit ב-api/main.py → cp api/main.py main.py
- אל תקומיט 128 הקבצים הלא-מתוייגים ב-root repo — הם reports וgabackups שצריכים triage ידני
- אל תעשה mock data בדפי production — תמיד נתונים אמיתיים מה-API
- UI בעברית, קוד באנגלית

דיבוג משתמשים:
- טופס: /bug-report.html
- דשבורד: /admin-bugs.html (מפתח: slh2026admin — יש לסובב!)
- FAB + auto-capture ב-shared.js תופסים JS errors + 500s אוטומטית
- התראות טלגרם נשלחות ל-ADMIN_USER_ID=224223270 על כל באג חדש

עדכון "Live State" ב-AGENT_CONTEXT.md חובה לפני סיום session.

אם יש ספק — שאל את אוסיף. לא לנחש.
```

---

## איך להשתמש

### 1. עבור סוכן חדש
פתח שיחה ריקה, העתק את הבלוק למעלה, הדבק. הסוכן יעשה את ה-onboarding לבד.

### 2. עבור סוכן קיים שאבד לו ההקשר
שלח: `קרא שוב את D:\SLH_ECOSYSTEM\ops\AGENT_CONTEXT.md ועדכן אותי אם יש שינוי במצב החי.`

### 3. עבור סנכרון בין סוכנים
כל סוכן בסיום session:
- מעדכן את הסקשן "Live State" ב-AGENT_CONTEXT.md
- מקומיט עם `docs(ops): agent-name session handoff`
- דוחף ל-repo המרכזי (root)

סוכנים אחרים יראו את העדכון ב-session הבא שלהם.

### 4. הרצה במקביל של מספר סוכנים
1. סוכן A על `website/` — UI + frontend
2. סוכן B על `api/main.py` — backend + DB
3. סוכן C על `*-bot/` — Telegram bots
4. כל סוכן: branch משלו, merge ל-main/master בסוף, עדכון Live State.

**כלל זהב:** רק סוכן אחד נוגע ב-`main.py` ברגע נתון (המיזוג שלו עם api/main.py עלול להתנגש).
