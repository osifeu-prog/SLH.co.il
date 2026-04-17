# 📡 SLH Command Center · Telegram Group Setup
> **הקבוצה החדשה שלך = מוח השליטה.** מאיזה בוטים לצרף, מה ההרשאות, ואיך להעביר עבודה לסוכנים חדשים.

---

## 🤖 איזה בוטים לצרף לקבוצה

### 👑 Admin (הרשאה מלאה — kick/ban/pin)
| בוט | Username | למה |
|-----|----------|-----|
| Guardian | `@slh_guardian_bot` | security alerts, scan reports, audit chain — יוצר התראות חשובות |
| Admin Console | `@slh_admin_control_bot` | פקודות אדמין ישירות: `/stats`, `/users`, `/ban`, `/premium` |

### 👂 Member (רק קורא + שולח התראות)
| בוט | Username | למה |
|-----|----------|-----|
| Ledger | `@SLH_Ledger_bot` | התראות תשלום בזמן אמת (כשמישהו קונה/שילם/אישר TX) |
| Campaign | `@Campaign_SLH_bot` | סטטוס קמפיינים, כמה קליקים/המרות |
| Core (Academia) | `@SLH_Academia_bot` | הרשמות חדשות, משתמשים חדשים |

### ❌ **אל תצרף לקבוצה הזו** (הם צריכים להישאר פרטיים/ממוקדים)
- `@G4meb0t_bot_bot` — בוט הכרויות, צריך להישאר דיסקרטי
- `@SLH_AIR_bot` — airdrops, נפרד
- כל 20 הבוטים האחרים — spam לא רצוי

**סה"כ מומלץ:** **2 admin + 3 members = 5 בוטים** בקבוצה. לא יותר.

---

## 🔐 איך לצרף בוט לקבוצה (step-by-step)

### לכל בוט:
1. **הגדרות הקבוצה** → **חברים** → **הוסף חבר**
2. חפש את ה‑username (למשל `@slh_guardian_bot`)
3. לחץ **הוסף**
4. **לבוטים של Admin:** לחץ על שם הבוט אחרי הצירוף → **Promote to Admin** →
   - ✅ Change Group Info
   - ✅ Delete Messages
   - ✅ Ban Users
   - ✅ Invite Users (עם/בלי קישור)
   - ❌ Remain Anonymous (כבוי)
   - ❌ Add New Admins (כבוי — רק אתה ממנה)
5. **לבוטים של Member:** אחרי הצירוף, ודא שהם יכולים לשלוח הודעות (default=כן)

### ⚠️ חובה לפני הכל:
ב‑[@BotFather](https://t.me/BotFather) → `/mybots` → בחר את הבוט → **Bot Settings** → **Allow Groups?** → **Turn on**.
ללא זה, הבוט לא יקבל הודעות מהקבוצה.

---

## 📝 איך להעביר עבודה לסוכנים אחרים (Handoff Protocol)

### 🎯 עיקרון מרכזי
**כל סוכן חדש מתחיל אותו דבר:**
1. פותח **Agent Brief** → [slh-nft.com/agent-brief.html](https://slh-nft.com/agent-brief.html)
2. מעתיק את הפרומפט (כפתור "העתק") → מדביק כהודעה ראשונה
3. בוחר משימה מתוך 7 המשימות הפנויות
4. עובד
5. מדווח חזרה לפי התבנית ב‑Agent Brief

זה **הפרוטוקול היחיד.** אין מסלול אחר.

---

### 🔄 6 שלבי Handoff (מפורט)

#### שלב 1: **זהות הסוכן**
לפני שהסוכן מתחיל, תחליט אם הוא:
- **Executor** (יכול להריץ קוד/פקודות/git/docker) — למשל Claude Code עם גישה למחשב, Cursor, Copilot Agent
- **Advisor** (רק טקסט/קוד, לא מריץ) — כמו ChatGPT רגיל, Gemini, DeepSeek

זה קריטי — advisor לא יכול לעשות commit, executor כן.

#### שלב 2: **שליחת הפרומפט**
שלח לסוכן:
```
https://slh-nft.com/agent-brief.html

תעתיק את הפרומפט המלא מהעמוד הזה, תדביק אותך כהודעה ראשונה, ותתחיל לעבוד.
```
ואם זה בוט בטלגרם או AI אחר — הפרומפט שם, מוכן להעתקה (הכפתור "העתק").

#### שלב 3: **בחירת משימה**
הסוכן יגיד: "אני בוחר משימה #N" (מתוך 7 הפנויות ב‑Agent Brief).
אתה מאשר ("כן, קח אותה") או מפנה למשימה אחרת.

#### שלב 4: **עדכון SESSION_STATUS**
הסוכן צריך לעדכן את [ops/SESSION_STATUS.md](https://github.com/osifeu-prog/slh-api/blob/master/ops/SESSION_STATUS.md):
- להוסיף שורה: `🔄 Task #3 — in progress by <agent name>`
- זה מונע כפילויות — סוכנים אחרים רואים שהמשימה תפוסה

#### שלב 5: **עבודה + קומיטים**
- **Executor:** git branch `feature/<task-name>` → commit → PR to master
- **Advisor:** מחזיר patches / diffs בצ'אט → אתה או אני מריצים git commit

כל קומיט חייב:
- Message בפורמט: `feat(task-3): short description`
- Co-Authored-By: <agent name> <noreply>

#### שלב 6: **דיווח סופי**
הסוכן מעתיק את "תבנית הדיווח" מ‑Agent Brief (כפתור "העתק" השני) וממלא:
- ✅ Completed
- 🚧 In progress
- 🛑 Blockers
- 📊 Verification
- 📝 Next recommended
- 💰 Revenue impact

שולח לך ב‑Telegram לקבוצת SLH Command Center. אתה מאשר, או מזרים למישהו אחר.

---

### 🧪 איך לבדוק שהכל עובד (Test Run)

**ניסוי פשוט עם סוכן חדש:**

1. פתח ChatGPT / Claude בחלון חדש (או בוט AI כלשהו)
2. הדבק את הפרומפט מ‑[agent-brief.html](https://slh-nft.com/agent-brief.html)
3. תגיד לו: **"קח את משימה #5 (Theme switcher). עבוד על עמוד אחד — liquidity.html. תחזיר לי unified diff."**
4. הוא אמור:
   - להבין את המשימה (קרא את liquidity.html, השווה ל‑dashboard.html או admin.html שיש להם theme switcher)
   - לכתוב patch
   - לחזור עם diff + דיווח לפי התבנית
5. אתה מריץ את ה‑patch → פוש → בודק בדפדפן

אם זה עובד → פרוטוקול handoff מוכח.

---

## 📋 תיעוד נוסף שכדאי לשמור

| קובץ | מה יש בו | מתי לעדכן |
|------|---------|-----------|
| [ops/SESSION_STATUS.md](https://github.com/osifeu-prog/slh-api/blob/master/ops/SESSION_STATUS.md) | מה פתוח, מה תפוס, מי עובד על מה | לפני+אחרי כל session |
| [ops/LIVE_ROADMAP.md](https://github.com/osifeu-prog/slh-api/blob/master/ops/LIVE_ROADMAP.md) | 5 tracks + סטטוס + מה הבא | אחרי כל milestone |
| [ops/DECISIONS.md](https://github.com/osifeu-prog/slh-api/blob/master/ops/DECISIONS.md) | לוג החלטות (append-only) | כל החלטה טכנית/עסקית |
| [ops/AGENT_REGISTRY.json](https://github.com/osifeu-prog/slh-api/blob/master/ops/AGENT_REGISTRY.json) | מי הסוכנים הפעילים | כשמצטרף סוכן חדש |
| [slh-nft.com/agent-brief.html](https://slh-nft.com/agent-brief.html) | דף הכניסה לסוכנים | אחרי שינויים גדולים |
| [slh-nft.com/mission-control.html](https://slh-nft.com/mission-control.html) | מצב המערכת LIVE | אוטומטי |

---

## 🎭 דוגמאות: איך לכתוב הודעה לסוכן

### 📝 הודעה 1: סוכן חדש מוחלט (לא מכיר כלום)
```
שלום! אני אוסיף, הבעלים של SLH Spark.

תעתיק את הפרומפט המלא מהקישור הזה:
https://slh-nft.com/agent-brief.html

ואחרי שתקרא — תחזיר לי:
1. באיזו משימה אתה רוצה לעבוד (#1–#7)
2. האם אתה executor (יכול להריץ קוד) או advisor (רק טקסט)
3. הערכת זמן
```

### 📝 הודעה 2: מושיב מהירות (סוכן שכבר מכיר)
```
יש לנו עכשיו 7 endpoints חדשים ל-Payment API (ראה agent-brief).
אני צריך:
- משימה #6 (PancakeSwap TX tracker) נסגרה
- משימה #3 (Twilio) ברגע שאשיג API key

תוכל לקחת משימה #7 (TON deep-link)? הנה context: [רשימה של 3-5 קבצים רלוונטיים].
```

### 📝 הודעה 3: להפוך בוט טלגרם AI לסוכן
```
אתה עכשיו סוכן AI של SLH Spark. אני אוסיף, הבעלים.
תקרא את הפרומפט המלא שאשלח בהודעה הבאה ותחזור עם "מוכן".

[הדבק את כל הפרומפט מ-agent-brief.html]
```

---

## 💡 חוקי זהב ל‑Handoff מוצלח

1. **פרומפט אחד לכל הסוכנים** — agent-brief.html הוא ה‑source of truth. לא שולחים מסמכים ארוכים אחרים.
2. **משימה אחת לכל סוכן** — אם סוכן רוצה שתי משימות, תגיד "סגור את הראשונה קודם".
3. **דיווח לפי תבנית** — בלי דיווח → לא מתקדמים.
4. **עדכון SESSION_STATUS.md** — לפני ואחרי, לא באמצע. אין עדכונים-בזמן-אמת שמבלבלים.
5. **קומיטים קטנים** — כל משימה = commit אחד או שניים (לא 20).
6. **Co-Authored-By** — כל קומיט צריך לציין את הסוכן (לשקיפות).
7. **Security first** — אף סוכן לא נוגע ב‑.env, secrets, Railway, או BotFather בלעדיך.

---

## 🔐 הסמכה (Authorization) — מי רשאי לעשות מה

| פעולה | Executor | Advisor | Osif בלבד |
|-------|:--------:|:-------:|:---------:|
| קריאת קוד | ✅ | ✅ | ✅ |
| כתיבת patches | ✅ | ✅ | ✅ |
| `git commit` | ✅ | ❌ | ✅ |
| `git push` | ✅ | ❌ | ✅ |
| שינוי .env | ❌ | ❌ | ✅ |
| שינוי Railway vars | ❌ | ❌ | ✅ |
| יצירת בוט ב‑BotFather | ❌ | ❌ | ✅ |
| מחיקת data production | ❌ | ❌ | ✅ |
| כתיבת קבלות / יצירת תשלום | ✅ | ❌ | ✅ |

---

## 📞 לוגיסטיקה

- **קבוצת SLH Command Center** (זו שיצרת) → כל ה‑bots + אתה + סוכנים חדשים שמגיעים
- **אתה מוסיף סוכנים ידנית** (לא אוטומטי) — כדי שלא יהיה ספאם
- **סוכנים שנחקרו ונמצאו אמינים** מקבלים Invite Link (`t.me/+...`) שפועל לפעם אחת
- **Session handoff** מתועד ב‑SESSION_STATUS.md עם שם הסוכן שעובד

---

**🤖 Claude Code · מוכן לעבור handoff / לקבל סוכנים חדשים.**
