# CLAUDE.md — SLH.co.il Repository

**מחייב לכל סוכן AI (Claude / GPT / אחר) שעורך את ה-repo הזה.**

---

## 🚨 חוקים קשיחים — לא נושא למשא ומתן

### 1. אין APY/ROI ללא SIG+σ+disclaimer
כל הצגה של `%` תשואה / APY / yield / ROI בכל קובץ HTML, קוד, bot reply, post — חייבת:
- המילה **"Target"** / **"יעד"** לפני המספר (לא "Earn", לא "Guaranteed")
- Badge עם `SIG=X · σ=0.0049%`
- Disclaimer `Forward-looking projection, not guaranteed`
- Reference ל-`/docs/SIG_STATISTICAL_DEFENSE.md`

**פירוט**: ראה `docs/SIG_STATISTICAL_DEFENSE.md`.

### 2. אין מכירת טוקנים לרטייל
הסיכון המשפטי הזה נסגר ב-20.4.2026. אסור:
- `"Buy X SLH for $Y"` / `"רוכש טוקנים"` / `"token sale"`
- `"Mint and distribute N tokens"` לרטייל
- כל flow שמכניס ILS/USD ומחזיר SLH/ZVK/MNH/REP/ZUZ כ-proceeds

מותר:
- **Mining reward** — utility token שהמשתמש מרוויח דרך הפעלת מכשיר / השלמת קורס / השתתפות בקהילה
- **Bundled utility credits** — טוקנים preloaded בחומרה (תשלום על החומרה, הטוקנים בונוס utility)
- **Earned-via-activity** — השלמת quests, referrals, academia completion

אם משתמש מבקש flow שנראה כמו token sale → הצע mining/bundled/earned variant.

### 3. ללא סודות בקוד
אין hardcoded tokens / API keys / passwords. הכל דרך `os.getenv()` + Railway shared variables.
Pre-commit hook `.githooks/pre-commit` סורק 8 דפוסי סודות וחוסם commit. אל תעקוף.

### 4. Verify prod schema before SQL
לפני עריכת כל SQL — הרץ `railway run python -c "..."` על הסכמה החיה. אל תניח columns / types. `first_seen` ו-`feedback.timestamp` הם TEXT (ISO-8601), לא TIMESTAMP.

---

## 🛠 פקודות סטנדרטיות

```bash
# בריאות מלאה
pwsh ops/verify.ps1

# deploy
git add <files>
git commit -m "..."
git push origin main   # → Railway auto-deploys

# בדיקת סכמה חיה (לפני שינוי SQL!)
railway run python -c "import os,psycopg2; c=psycopg2.connect(os.getenv('DATABASE_URL')).cursor(); c.execute('SELECT column_name,data_type FROM information_schema.columns WHERE table_name=%s',('<table>',)); [print(r) for r in c.fetchall()]"
```

ראה `ops/runbook.md` למדריך מלא.

---

## 📐 מבנה

```
SLH.co.il/
├── bot.py              # Telegram bot (@SLH_macro_bot) — פקודות + DB
├── docs/               # Static site מוגש ע"י Railway fallback
│   ├── index.html      # בית
│   ├── guardian.html   # מכשיר Guardian — early bird pre-order + 2 SLH mining
│   └── SIG_STATISTICAL_DEFENSE.md   # מתודולוגיה canonical
├── monitor/            # Dashboard
├── ops/                # Runbooks + verify scripts + rotate-token
├── .githooks/          # Pre-commit secret scanner
├── railway.json        # Railway deploy config
└── CLAUDE.md           # ← הקובץ הזה
```

---

## 🧭 לסוכן שנכנס ל-repo פעם ראשונה

1. קרא את הקובץ הזה (`CLAUDE.md`) — עד הסוף.
2. קרא `docs/SIG_STATISTICAL_DEFENSE.md` — כל מספר APY בקוד חייב להיות קומפליאנטי.
3. קרא `ops/runbook.md` — פקודות deploy + health.
4. `git log --oneline -10` — מה קרה לאחרונה.
5. `railway status` — באיזה service אתה עובד.

אם חוק כאן מתנגש עם מה שהמשתמש מבקש — **תפסיק ותשאל**. אל תוציא commit שעוקף את החוקים.

---

## 📞 איש קשר

- **בעלים / מפתח ראשי:** Osif (Telegram: `@osifeu_prog`)
- **בוט פרודקשן:** `@SLH_macro_bot`
- **Railway project:** `diligent-radiance` / service `monitor.slh`
- **GitHub:** https://github.com/osifeu-prog/SLH.co.il

---

## 📜 רגולציה

Israel: חוק ניירות ערך התשכ"ח-1968 — כל "promise of return" לרטייל = הצעה ציבורית לא רשומה. אחריות פלילית אישית.
US (אם יש משתמשים): Howey Test — investment of money + common enterprise + expectation of profit + from others' efforts = security.

**כל שינוי copy שקשור ל-APY / tokens / investment → עובר דרך `SIG_STATISTICAL_DEFENSE.md` או חוסם.**
