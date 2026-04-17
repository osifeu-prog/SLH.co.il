# 📡 SLH · Telegram Groups Setup
> **2 קבוצות נפרדות.** אל תערבב ביניהן.

---

## ⚠️ 2 קבוצות — אל תשלח את הקישורים הלא-נכונים!

### 1. 💝 קבוצת "המפקדה" — **הכרויות / פרטית**
- **NEVER share publicly.** לא באתר, לא במדריך, לא לילדים
- רק שותפים בוגרים שאוסיף מאשר אישית
- Invite: ידוע לאוסיף בלבד
- מטרה: חיי אישי, הכרויות רציניות

### 2. 🔧 קבוצת עובדים/סוכנים — **עוד לא נוצרה**
**Osif עדיין לא יצר את הקבוצה הזו.** כשהוא יצור — היא תהיה:
- **שם מוצע:** `SLH Workers` / `SLH Builders` / `צוות SLH`
- **חברים:**
  - אוסיף (מנהל)
  - צביקה (Co-founder)
  - אליעזר (Broker)
  - 5 בוטים (ראה למטה)
  - סוכני AI מאומתים
- **מטרה:** תיאום עבודה, התראות בוטים, handoff בין סוכנים

---

## 🔧 כשתיצור את קבוצת העובדים — מה לצרף

### 👑 Admin (הרשאה מלאה)
| בוט | Username | למה |
|-----|----------|-----|
| Guardian | `@slh_guardian_bot` | security alerts, scan reports |
| Admin Console | `@slh_admin_control_bot` | פקודות אדמין: `/stats`, `/premium` |

### 👂 Member (רק קורא + שולח התראות)
| בוט | Username | למה |
|-----|----------|-----|
| Ledger | `@SLH_Ledger_bot` | התראות תשלום בזמן אמת |
| Campaign | `@Campaign_SLH_bot` | סטטוס קמפיינים |
| Core | `@SLH_Academia_bot` | הרשמות חדשות |

### ❌ **אל תצרף** לקבוצת העובדים:
- `@G4meb0t_bot_bot` — בוט הכרויות פרטי
- `@SLH_AIR_bot` — פומבי, משתמשים רגילים

---

## 🔐 איך לצרף בוט לקבוצה

1. ב‑[@BotFather](https://t.me/BotFather) → `/mybots` → בחר בוט → **Bot Settings** → **Allow Groups?** → **Turn on**
2. בקבוצה: **הגדרות** → **חברים** → **הוסף**
3. חפש username → **הוסף**
4. לבוטים Admin: לחץ על שמם → **Promote to Admin** → סמן:
   - ✅ Change Group Info
   - ✅ Delete Messages
   - ✅ Invite Users
   - ❌ Add New Admins (רק אתה)

---

## 📝 Handoff לסוכנים AI — 6 שלבים

### שלב 1: זהות הסוכן
- **Executor** (git/docker/bash) — Claude Code, Cursor, Copilot Agent
- **Advisor** (רק טקסט) — ChatGPT, Gemini, DeepSeek

### שלב 2: שליחת הפרומפט
```
https://slh-nft.com/agent-brief.html
תעתיק את הפרומפט המלא, תדביק כהודעה ראשונה.
```

### שלב 3: בחירת משימה
הסוכן בוחר מבין 7 המשימות הפנויות ומחזיר: "אני על #N"

### שלב 4: עדכון SESSION_STATUS
הסוכן מוסיף: `🔄 Task #3 — in progress by <agent name>`

### שלב 5: עבודה + קומיטים
- **Executor:** `git branch feature/<task>` → commit → PR
- **Advisor:** מחזיר patch → אתה מריץ

כל commit: `Co-Authored-By: <agent> <noreply>`

### שלב 6: דיווח סופי
הסוכן מעתיק את תבנית הדיווח מ‑agent-brief.html וממלא ✅🚧🛑📊📝💰

---

## 🧪 בדיקת Handoff — test run

1. פתח ChatGPT/Claude בחלון חדש
2. הדבק פרומפט מ‑[agent-brief.html](https://slh-nft.com/agent-brief.html)
3. תן: "קח משימה #5 (Theme switcher). עבוד על liquidity.html. תחזיר diff."
4. הוא יחזור עם patch + דיווח
5. אתה מריץ → פוש → בודק
6. ✅ אם עבד → הפרוטוקול מוכח

---

## 📋 תיעוד שכדאי לשמור

| קובץ | מה | מתי לעדכן |
|------|-----|-----------|
| [ops/SESSION_STATUS.md](https://github.com/osifeu-prog/slh-api/blob/master/ops/SESSION_STATUS.md) | מי עובד על מה | לפני+אחרי session |
| [ops/LIVE_ROADMAP.md](https://github.com/osifeu-prog/slh-api/blob/master/ops/LIVE_ROADMAP.md) | 5 tracks | כל milestone |
| [ops/DECISIONS.md](https://github.com/osifeu-prog/slh-api/blob/master/ops/DECISIONS.md) | החלטות | כל החלטה |
| [ops/AGENT_REGISTRY.json](https://github.com/osifeu-prog/slh-api/blob/master/ops/AGENT_REGISTRY.json) | סוכנים פעילים | כשמצטרף |
| [slh-nft.com/agent-brief.html](https://slh-nft.com/agent-brief.html) | פרומפט שיתוף | אחרי שינויים גדולים |
| [slh-nft.com/mission-control.html](https://slh-nft.com/mission-control.html) | LIVE | אוטומטי |

---

## 🔐 Authorization Matrix

| פעולה | Executor | Advisor | Osif |
|-------|:--------:|:-------:|:----:|
| קריאת קוד | ✅ | ✅ | ✅ |
| כתיבת patches | ✅ | ✅ | ✅ |
| `git commit` | ✅ | ❌ | ✅ |
| `git push` | ✅ | ❌ | ✅ |
| שינוי .env | ❌ | ❌ | ✅ |
| Railway vars | ❌ | ❌ | ✅ |
| BotFather | ❌ | ❌ | ✅ |
| מחיקת data | ❌ | ❌ | ✅ |
| צירוף לקבוצות הכרויות | ❌ | ❌ | ✅ |

---

## 💡 חוקי זהב

1. **2 קבוצות נפרדות** — dating group לא מוזכרת במדריכים פומביים, לעולם
2. **פרומפט אחד לסוכנים** — agent-brief.html
3. **משימה אחת לסוכן בזמן**
4. **דיווח לפי תבנית** — בלי דיווח, לא מתקדמים
5. **קומיטים קטנים** עם Co-Authored-By
6. **Security first** — אף סוכן לא נוגע ב‑secrets בלעדיך
7. **קטינים** — nephew (ID 6466974138, 13yo) לא נחשף לתוכן בוגרים/הכרויות
