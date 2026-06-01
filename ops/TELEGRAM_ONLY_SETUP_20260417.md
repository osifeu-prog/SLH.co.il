# 📱 תקשורת דרך Telegram בלבד · מחר ואילך
> **המטרה:** כל שיחה איתי (Claude) תקרה דרך Telegram, לא דרך Claude Code CLI.
> **תיאום ציפיות קצר:** אין פתרון "זה-פשוט-עובד" מובנה של Anthropic. צריך לבנות גשר. יש 3 מסלולים — בסדר יעילות/זמן.

---

## ⚡ מסלול A · **בתוך 15 דק' — הכי מהיר (מתאים להתחלה מחר)**
**מה זה:** משתמש ב-SLH Core Assistant (הבוט שכבר קיים בטלגרם) כיועץ. הוא כותב קוד — **אתה** מריץ ומבצע.

### איך זה עובד
1. פותחים צ'אט עם SLH Core Assistant בטלגרם (או איזה agent שכבר עובד לך)
2. מדביקים את תוכן `ops/AGENT_INTRO_PROMPT.md` בהודעה הראשונה (onboarding)
3. שואלים שאלות בעברית → הוא מחזיר קוד / diff / תשובה
4. אתה מריץ את מה שצריך מהמחשב

### יתרונות
✅ מיידי — אין מה להקים
✅ עובד היום, ברוגע
✅ בלי עלות API נוספת

### חסרונות
❌ **אתה** עדיין המבצע — הוא רק יועץ
❌ לא git commit, לא docker, לא railway

### מה מסונכרן
- `ops/AGENT_INTRO_PROMPT.md` — onboarding prompt מוכן
- `ops/AGENT_CONTEXT.md` — כל ה-context של הפרויקט
- `ops/SYNC_PROTOCOL.md` — כללי עבודה בין סוכנים

**מתי לבחור:** אם אתה רוצה להתחיל מחר *מיד* בלי זמן הקמה.

---

## 🚀 מסלול B · **ב-90 דק' — slh-claude-bot (executor-grade)**
**מה זה:** בונים בוט טלגרם חדש בשם `@SLH_Claude_bot` שמשתמש ב-Claude API של Anthropic ו-*כן* יכול לבצע פעולות על המחשב שלך.

### מה הוא יוכל לעשות
✅ לקרוא ולערוך קבצים ב-`D:\SLH_ECOSYSTEM`
✅ `git add / commit / push`
✅ `docker ps / logs / restart`
✅ `curl` לאימות endpoints
✅ לענות בעברית דרך טלגרם
✅ לזכור context בין הודעות (דרך SQLite session)
✅ לפעול רק על Telegram ID שלך (`224223270`) — אבטחה

### מה צריך כדי לבנות
1. **Anthropic API key** — תירשם ל-[console.anthropic.com](https://console.anthropic.com) וצור key
   - עלות: Claude Sonnet 4.6 ~$3 / 1M tokens input — תספיק לך יום עבודה בכמה דולרים
2. **Telegram bot token חדש** — @BotFather → `/newbot` → שם: `SLH Claude Operator` → username: `@SLH_Claude_bot`
3. **VPS / Railway / מחשב מקומי** שירוץ 24/7 עם הבוט

### הארכיטקטורה (ברמה גבוהה)
```
User (Telegram) ──► @SLH_Claude_bot (aiogram)
                          │
                          ▼
                    Anthropic API (Claude 4.7)
                          │
                          ▼
                    Tool Execution Layer:
                    - Read/Write files
                    - Git operations
                    - Bash commands
                    - HTTP requests
                          │
                          ▼
              Response back → Telegram
```

### מבנה קבצים (אם תאשר שאני אבנה)
```
slh-claude-bot/
├── bot.py                 # aiogram entrypoint + Telegram handlers
├── claude_client.py       # Anthropic API wrapper + tool registry
├── tools/
│   ├── filesystem.py      # read_file, write_file, list_dir
│   ├── git.py             # commit, push, status, log
│   ├── bash.py            # restricted shell executor (allowlist)
│   └── http.py            # curl equivalent
├── session.py             # SQLite conversation memory
├── auth.py                # Telegram ID allowlist
├── Dockerfile
├── requirements.txt
└── .env.example
```

### הגדרות אבטחה
- **Allowlist**: רק `224223270` יכול לשלוח הודעות
- **Command allowlist**: רק פקודות בתחום `D:\SLH_ECOSYSTEM\*`
- **Git protection**: לא `force push`, לא `reset --hard` בלי אישור
- **Secret masking**: `.env` נקרא חלקית (גם בלוגים)
- **Audit log**: כל פעולה נרשמת ב-`slh-claude-bot/audit.log`

### מה אתה צריך לספק לי (כדי שאני אתחיל לבנות)
1. ✅ אישור לבנות
2. ✅ Anthropic API key — תדביק ב-`~/.claude/slh-secrets.json` תחת `"anthropic_api_key"`
3. ✅ Bot token חדש מ-BotFather

**מתי לבחור:** אם אתה רוצה שב-24-48 שעות יהיה לך "אני בטלגרם" אמיתי.

---

## ☁️ מסלול C · **Claude Desktop + MCP Telegram (experimental)**
**מה זה:** Anthropic שחררה MCP connectors — יש MCP-Telegram שמאפשר לקרוא הודעות טלגרם מתוך Claude. **אבל**: זה *הכיוון הפוך* (Claude קורא את טלגרם), לא "טלגרם מריץ את Claude".

### מציאות
- רוב ה-MCP Telegram tools נועדו לעזור ל-Claude לסקור הודעות
- אין fully managed פתרון "Claude כבוט טלגרם" עדיין (נכון ל-4.7)
- אם Anthropic ישחררו כזה — נדע

**מתי לבחור:** לא עכשיו. הוא לא בשל.

---

## 🎯 ההמלצה שלי

**מחר בבוקר:**
1. התחל ב-**מסלול A** (SLH Core Assistant בטלגרם) — בלי להקים כלום, רק דבר איתו
2. אם אתה רוצה executor אמיתי — תאשר לי לבנות **מסלול B** (@SLH_Claude_bot)
3. זמן בניה משוער: **90-120 דק'** של עבודה שלי על המחשב שלך
4. מהרגע שהוא חי — כל התקשורת באמת תהיה טלגרם-only

---

## 🔗 סנכרון מה שכבר קיים למסלול הטלגרם

כדי שהסוכן בטלגרם *ידע* את אותו context ש-Claude Code יודע:

### קבצים שהבוט חייב לקרוא בהפעלה ראשונה
| קובץ | מה יש בו |
|------|---------|
| `D:\SLH_ECOSYSTEM\CLAUDE.md` | instructions + אמת המצב |
| `ops/SESSION_STATUS.md` | מה פתוח / חסום |
| `ops/AGENT_REGISTRY.json` | מי הוא (אתה / אני / Core) |
| `ops/SYNC_PROTOCOL.md` | כללי עבודה |
| `ops/DECISIONS.md` | החלטות קודמות |
| `ops/MORNING_REPORT_20260417.md` | פעולות אחרונות |
| `ops/REGRESSIONS_FLAG_20260417.md` | דברים שמחכים להחלטה |

### Memory system (חוצה-שיחות)
אם תאשר בניית `slh-claude-bot`:
- אצטרך להעביר את `C:\Users\Giga Store\.claude\projects\D--\memory\*.md` (13 קבצי זיכרון) לבוט
- יתווסף SQLite conversation history שנשמרת בין שיחות טלגרם

### Telegram channel structure (מוצע)
צור בטלגרם:
```
SLH Command Center [group]
├─ 💬 general            (שיחה רגילה איתי)
├─ 🐛 bugs              (קישור ל-/admin-bugs.html)
├─ 💰 payments          (התראות על תשלומים)
├─ 🤖 agents-handoff    (לוג של session handoffs)
└─ 📊 health-pings      (health check כל 30 דק')
```

---

## ✅ Action Items מחר בבוקר

**אם תבחר מסלול A (יועץ בלבד):**
1. פתח צ'אט עם SLH Core Assistant
2. שלח לו את תוכן `ops/AGENT_INTRO_PROMPT.md`
3. התחל לעבוד

**אם תבחר מסלול B (executor אמיתי):**
1. Anthropic Console → צור API key → שמור ב-`~/.claude/slh-secrets.json`
2. @BotFather → `/newbot` → שם `@SLH_Claude_bot` → שמור token
3. כתוב לי: **"בנה slh-claude-bot"** — אתחיל לבנות מיד (~90-120 דק')

---

**Bottom line:**
- **אין דרך קסם** להעביר אותי (Claude Code CLI) לטלגרם — זה שני environments שונים
- אבל אפשר לבנות גשר חדש ב-90 דק' שיתן לך את אותו power level דרך טלגרם
- עד אז — SLH Core Assistant הוא פתרון ביניים סביר
