# 🤖 פרומפטים מוכנים לסוכני AI חיצוניים

> **מתי להשתמש:** כשאתה רוצה שסוכן AI אחר (ChatGPT, Gemini, DeepSeek, Copilot) יעבוד על SLH.
> **העתק-הדבק.** הפרומפטים מתחילים באותה הקדמה שגם Claude Code משתמש בה, כדי שהתוצאה תהיה עקבית.

---

## 📚 פרומפט בסיסי · "אני סוכן חדש, מה לעשות?"

העתק את כל הטקסט הבא לכל AI:

```
אני עובד על פרויקט SLH Spark של אוסיף קאופמן-אונגר (Telegram: @osifeu_prog, ID: 224223270).

לפני שאתה עונה, קרא:
1. https://github.com/osifeu-prog/slh-api/blob/master/CLAUDE.md — הוראות עבודה
2. https://github.com/osifeu-prog/slh-api/blob/master/ops/SESSION_STATUS.md — מצב פתוח עכשיו
3. https://github.com/osifeu-prog/slh-api/blob/master/ops/ALPHA_READINESS.md — מפת המשימות לאלפא
4. https://slh-nft.com/agent-brief.html — תקציר חי עם סטטיסטיקות

אחרי שקראת, ענה:
1. "מוכן" + השם שלך + איזה מודל אתה
2. בחר משימה אחת מ-ops/ALPHA_READINESS.md (5 הפריטים ה-🔴)
3. תן לי הערכת זמן ותכנית ביצוע ב-3 bullets

חובות:
- קוד בעברית בהערות הממשק, אנגלית בקומיטים
- כל שינוי ב-routes/*.py חייב גם ב-api/routes/*.py
- לא לגעת ב-.env, סיסמאות, מפתחות API
- לא ל-force push, לא למחוק branches
- כל commit עם conventional message (feat:, fix:, docs:, chore:)

אם אתה לא בטוח — עדיף לשאול מראש מאשר לעשות טעות שצריך לתקן.
```

---

## 🐛 פרומפט · "תקן את הבאג X"

```
אני צריך שתתקן באג ב-SLH Spark.

פרטי הבאג:
- תיאור: [תיאור]
- דף/endpoint: [URL]
- מה אני מצפה: [מה צריך לקרות]
- מה קורה בפועל: [מה רואים]
- תדירות: [תמיד / לפעמים]

רקע:
- Repo: github.com/osifeu-prog/slh-api
- Stack: FastAPI + PostgreSQL + Railway (backend), GitHub Pages (frontend)

התהליך שאני מבקש:
1. קרא את ops/SESSION_STATUS.md וחפש אם הבאג כבר ידוע
2. אם לא ידוע — פתח issue ב-GitHub עם כל הפרטים
3. זהה את הקובץ(ים) המתאימ(ים) (routes/ או api/routes/ או website/)
4. תקן עם commit בסגנון: `fix(<module>): <תיאור בקיצור>`
5. אם זה משפיע על backend — סנכרן גם ב-api/routes/
6. סבא למה הבאג קרה ב-PR description

הסיפור מתחיל עכשיו. ענה "מוכן" + חזור עם תוצאה.
```

---

## ✨ פרומפט · "הוסף פיצ'ר חדש"

```
פיצ'ר שאני רוצה ב-SLH Spark:

מה: [תיאור המשתמש רואה]
איפה: [דף / bot / endpoint]
למה: [בעיה שזה פותר או הזדמנות]

הנחיות:
1. קרא CLAUDE.md + agent-brief.html
2. תכנן לפני שתקודד:
   - איזה טבלאות DB נצרכות (השתמש ב-CREATE TABLE IF NOT EXISTS)
   - איזה endpoints (GET/POST/PATCH) + schema
   - איזה דפים באתר
   - איזה עדכונים ב-sitemap.xml אם רלוונטי
3. פתח branch: feature/<short-name>
4. commits קטנים ושפים (commit על כל "רגע מובן")
5. PR description צריכה לכלול:
   - what: מה נוסף
   - why: למה
   - how to test: שלבים לאימות
   - screenshots/logs אם רלוונטי

אל תשכח — SLH עובד בעברית. UI strings בעברית, comments באנגלית.

תחזיר לי דיאגרמה, קוד, ותצפית על סיכון לפני שמתחילים.
```

---

## 🔒 פרומפט · "בצע audit אבטחה"

```
אני צריך audit אבטחה על SLH Spark.

מה לבדוק:
1. סודות שנחשפו ב-git history (git log --all | grep -i token|secret|key)
2. SQL injection בpoints עם user input
3. XSS בstring templates
4. CSRF הגנה על POST endpoints
5. Rate limiting מופעל?
6. Secrets ב-environment vs hardcoded
7. CORS — האם דרוש tightening?
8. JWT rotation policy
9. Password hashing (bcrypt round count)
10. Admin endpoints — האם דורשים X-Admin-Key?

תחזיר דוח בפורמט:
- 🔴 Critical (patch תוך 24 שעות)
- 🟡 High (patch תוך שבוע)
- 🟢 Medium (להוסיף ל-TEAM_TASKS.md)
- 🔵 Observations (רשומים, לא דורשים פעולה מיידית)

לכל ממצא: קובץ + מספר שורה + patch מוצע.

אל תפרסם ממצאים בציבור. תחזיר לי במסר פרטי בלבד.
```

---

## 📝 פרומפט · "ערוך דף HTML"

```
אני רוצה לערוך את [שם-הדף].html.

מה לשנות:
[תיאור]

הנחיות:
1. הדף נמצא ב-D:\SLH_ECOSYSTEM\website\ (או github.com/osifeu-prog/osifeu-prog.github.io)
2. השתמש ב-/css/slh-design-system.css עבור tokens (אל תהארדקוד צבעים)
3. הוסף dir="rtl" lang="he" אם חסר
4. תמיד עם `<link rel="stylesheet" href="/css/shared.css?v=20260417">`
5. אם יש data-i18n attributes — עדכן גם את js/translations.js
6. אם הדף חדש לגמרי — הוסף ל-sitemap.xml + blog/index.html אם רלוונטי

אל תשנה שאינך מבין. אם יש קטע שלא ברור — שאל אותי.
```

---

## 🤝 פרומפט · "עזור למישהו חדש להתחיל לתרום"

```
לתלמיד/מפתח חדש שמצטרף ל-SLH Spark:

הדרך הקצרה להתחיל:

1. קרא את 5 המסמכים האלה (~15 דקות):
   - CLAUDE.md (שורש של slh-api)
   - ops/ALPHA_READINESS.md (מה צריך כדי לצאת לאלפא)
   - ops/SESSION_STATUS.md (מה פתוח)
   - ops/DECISIONS.md (אל תדיין מחדש)
   - agent-brief.html (סטטיסטיקות חיות)

2. בחר משימה מרשימת 🟡 "2 שבועות" ב-ALPHA_READINESS.md

3. clone:
   git clone https://github.com/osifeu-prog/slh-api.git
   git checkout -b feature/<short-name>

4. בצע. commit בכל צעד מובן. push.

5. פתח PR → master. תייג את @osifeu-prog.

6. אוסיף בודק (5 דק') → merge → Railway auto-deploy.

חוקים:
- לא לגעת ב-.env
- לא ל-force push ל-master
- לא למחוק branches של אחרים
- שאל לפני rotation של secrets

תמיכה: @osifeu_prog ב-Telegram, או דווח באג ב-https://slh-nft.com/bug-report.html
```

---

## 📋 פרומפט · "תעזור לי לתעדף"

```
יש לי יותר מדי פתוח ב-SLH Spark ואני לא יודע מאיפה להתחיל.

קרא את:
1. https://github.com/osifeu-prog/slh-api/blob/master/ops/ALPHA_READINESS.md
2. https://github.com/osifeu-prog/slh-api/blob/master/ops/SESSION_STATUS.md
3. https://github.com/osifeu-prog/slh-api/blob/master/ops/TEAM_TASKS.md

תחזיר:
- 3 משימות שהכי דחופות עם הנמקה (למה, מה קורה אם לא עושים)
- 3 משימות שקל לבצע (quick wins)
- רעיון ל-1 משימה שיכולה לשנות את המשחק (10x)

הקריטריונים שלי:
- זמן שלי קצר (אני הסולו דב)
- רוב הזמן צריך להיות על משהו שמייצר הכנסה או שמונע אסון
- אני אוהב להראות תוצאות מהר

תן לי תשובה ממוקדת. לא כל הרשימה — רק ה-7 הבולטים.
```

---

## 🗣 פרומפט · "תענה כאילו אתה אוסיף"

> לשימוש כשסוכן אחר צריך לתת לי ייעוץ "בגובה העיניים" של הבעלים.

```
אתה אמור לענות לי כאילו אתה Osif Ungar, הבעלים של SLH Spark.

Context על אוסיף:
- מוזיקאי + מפתח סולו בישראל
- הגיע מהטיפ של הר הבית ולמד crypto ב-2026
- בונה קהילת "אנשים עם ערכים" ולא עוד רשת חברתית
- מעדיף תשובות ישרות על polite משקרי
- מדבר עברית ראשית, אנגלית בקוד
- מאמין שה"אלגוריתם הבריא" הוא הקשב, לא ה-engagement
- לא אוהב Facebook; משתמש ב-Telegram בעיקר
- חייב 10+ משקיעים מוסדיים ב-million ILS כל אחד

סגנון תשובה:
- קצר, ישר, ללא הגזמה
- עברית רגילה (לא רשמית)
- עם דוגמאות מחיי היום-יום
- מוכן להגיד "לא יודע" מיד
- אם אתה ממליץ משהו — תגיד למה בביט אחד

ענה לשאלה שלי מהמבט הזה.
```

---

## 🎯 איך להשתמש בפרומפטים האלה בפועל

1. **ChatGPT Web:** פתח `chat.openai.com` → הדבק את הפרומפט → שלח → המתן לתשובה
2. **Claude Web:** `claude.ai` → הדבק → שלח
3. **Gemini:** `gemini.google.com` → הדבק → שלח
4. **DeepSeek:** `chat.deepseek.com` → הדבק → שלח
5. **Local LLM (llama.cpp / Ollama):** הדבק לחלון הצ'אט

**חשוב:** רוב המודלים לא יכולים לכתוב ישירות ל-GitHub שלך. הם יחזירו קוד → אתה מעתיק → שם ב-repo → commit. זה הזרם הרגיל.

**אם מודל מסוים "עייף" (hallucinate, לא מגיב):**
- נסה מודל אחר (בדיוק כמו שאתה רוצה)
- חזור על הפרומפט עם פחות context
- העלה רק את הקובץ הספציפי שאתה רוצה לערוך
- אם באמת תקוע — [פתח issue](https://github.com/osifeu-prog/slh-api/issues) ו-@osifeu-prog יעזור

---

## 🚨 מה _לא_ לשלוח לסוכן זר

- ❌ תוכן של `.env` (אף פעם!)
- ❌ הסיסמה של admin (זו ב-localStorage, לא לשיתוף)
- ❌ Webhooks שמכילים tokens
- ❌ User data של מישהו אחר (GDPR)
- ❌ Database dumps (גם בהצגה)
- ❌ Private keys (seed phrases, wallet keys)

**אם סוכן שואל אותך על אחד מאלה — תגיד "לא" ותמשיך.** מודל מעוצב היטב יתנצל; מודל "עייף" ינסה שוב. זה הסימן לעבור מודל.

---

**עודכן: 2026-04-17 · שחרור ראשון**
