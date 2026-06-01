# DROP OFF · Osif / Owner · 2026-04-24

**קהל יעד:** Osif Kaufman Ungar בלבד
**זמן ביצוע כולל:** ~45 דק' (רובו על מסכים של Railway + GitHub + BotFather)
**למה רק אתה:** דורש גישה למסכי dashboard, סודות API, וקבלת החלטות.

---

## 🔴 1. Railway Redeploy — חוסם הכל (30 שניות)

**הבעיה:** 5 commits (`b48a1b1` → `e49a57b`) ב-`origin/master` אבל Railway משרת v1.1.0 ישן. סיבה: commit `097eafe` ב-19.4 הכניס curly-quotes ששברו את ה-build. תוקן ב-`b60cec2`, אבל Railway הפסיק auto-deploy.

**פעולה:**
1. `https://railway.app/project/slh-api` → Deployments
2. **אם הכי עליון = `Failed`** → צלם 3 שורות של stack trace ושלח לי
3. **אם `Paused` או `Outdated`** → לחץ `Redeploy` על commit `6892556` (האחרון)
4. **אם `Building`** → חכה 2-3 דק'

**וידוא הצלחה (אחרי 2 דק'):**
```bash
curl.exe https://slh-api-production.up.railway.app/api/health
# צפוי: version חדש יותר מ-1.1.0

curl.exe "https://slh-api-production.up.railway.app/api/ambassador/contacts?ambassador_id=1"
# צפוי: 200 או 403 (auth), לא 404
```

---

## 🔴 2. Push Website — 3 דפים + תיקייה חסרים (5 דק')

**הבעיה:** מקומית יש קבצים שלמים ב-`D:\SLH_ECOSYSTEM\website\` אבל לא נדחפו:
- `website/miniapp/` (4 קבצים: dashboard, wallet, device, css, js)
- `website/marketplace.html` (לפי memory 20.4 אמור LIVE)
- `website/team.html` (לפי memory 18.4 עודכן עם 10 חברים)

**פעולה (PowerShell):**
```powershell
cd D:\SLH_ECOSYSTEM\website

# ודא מה חסר
git status

# הוסף ודחוף
git add miniapp/ marketplace.html team.html
git commit -m "website: add miniapp dashboard + publish marketplace + team page"
git push
```

**וידוא (60 שניות אחרי push):**
```bash
curl.exe -I https://slh-nft.com/miniapp/dashboard.html    # צפוי 200
curl.exe -I https://slh-nft.com/marketplace.html          # צפוי 200
curl.exe -I https://slh-nft.com/team.html                 # צפוי 200
```

**אם marketplace.html/team.html לא קיים מקומית** — memory לא תואם מציאות. שלח לי הודעה ונמצא את הקבצים האמיתיים או נבנה מחדש.

---

## 🔴 3. Git Config — תיקון authorship גלובלי (1 דק')

**הבעיה:** 2 commits (`097eafe`, `a94e682`) נשמרו עם `"Your Name <your.email@example.com>"`. הסיבה: `git config --global` לא הוגדר מעולם.

**פעולה:**
```powershell
git config --global user.name "Osif Kaufman Ungar"
git config --global user.email "osif.erez.ungar@gmail.com"

# ודא
git config --global --get user.name
git config --global --get user.email
```

**הערה:** הסשן האחרון כבר דחף עם env-var override, אז commits חדשים מכאן והלאה יהיו תקינים אוטומטית.

---

## 🔴 4. סיבוב 10 סודות דלופים (20 דק')

**הבעיה:** ב-night 21.4 audit זוהו ~10 סודות בשיחות AI/צילומי מסך.

| # | סוד | איפה לסובב | בדיקה | סטטוס |
|---|-----|-------------|--------|--------|
| 1 | OpenAI API key | platform.openai.com → API Keys → Revoke + Create new | ✅ העתק ל-.env | ⏳ |
| 2 | Gemini API key | aistudio.google.com → API key | ✅ .env | ⏳ |
| 3 | Groq API key | console.groq.com → API keys | ✅ .env | ⏳ |
| 4 | BSCScan API key | bscscan.com → My Account → API Keys | ✅ Railway `BSCSCAN_API_KEY` | ⏳ |
| 5 | Bot token #1 (חשוד) | @BotFather → /mybots → בחר → API Token → Revoke | ✅ .env + Railway | ⏳ |
| 6 | Bot token #2 (חשוד) | @BotFather → /mybots → בחר → API Token → Revoke | ✅ .env + Railway | ⏳ |
| 7 | JWT_SECRET | Railway → Variables → JWT_SECRET → value חדש (32+ chars random) | ✅ Railway | ⏳ |
| 8 | ENCRYPTION key | כנ"ל | ✅ Railway | ⏳ |
| 9 | ADMIN_API_KEYS | שנה ל-2 ערכים חדשים: `slh_admin_2026_rotated_04_24,slh_ops_2026_rotated_04_24` | ✅ Railway + shared | ⏳ |
| 10 | ADMIN_BROADCAST_KEY | שנה מ-`slh-broadcast-2026-change-me` לערך חדש | ✅ Railway + curl tests | ⏳ |

**אחרי רוטציה:** Railway יריץ restart אוטומטי עם המפתחות החדשים. בדוק:
```bash
curl.exe -H "X-Admin-Key: <NEW_ADMIN_KEY>" https://slh-api-production.up.railway.app/api/admin/devices/list
```

**⚠️ חוק ברזל:** לעולם אל תדביק את המפתחות החדשים בצ'אט איתי. רק אמור "done" כשסיימת. אם טעית והדבקת — פתח לי הודעה ואני אסמן שוב כ-exposed.

---

## 🟡 5. ANTHROPIC_API_KEY ל-@SLH_Claude_bot (2 דק')

**הבעיה:** `D:\SLH_ECOSYSTEM\slh-claude-bot\.env` בשורה 8 — `ANTHROPIC_API_KEY=` (ריק).
**אימפקט:** הבוט עובד חלקית (health/price/devices/task OK) אבל free-text handler נופל.

**פעולה:**
1. `console.anthropic.com` → Settings → API Keys → Create Key → Name: "SLH_Claude_bot"
2. העתק את המפתח
3. פתח `D:\SLH_ECOSYSTEM\slh-claude-bot\.env` בעורך
4. תחליף שורה 8: `ANTHROPIC_API_KEY=sk-ant-...`
5. שמור, סגור
6. `cd D:\SLH_ECOSYSTEM && docker compose restart slh-claude-bot`

---

## 🟡 6. SQL Review למשתמש 8789977826 (10 דק')

**הבעיה:** משלם ₪196 (4×₪49), 0 רישיונות. תוקן ב-commit `b4da6b1` (schema mismatch) אבל היסטורית 3 כפילויות עדיין פתוחות.

**החלטה שלך:**
- **אופציה A:** החזר ₪147 (3 הכפילויות)
- **אופציה B:** שדרוג ל-VIP ב-+₪353 (מקבל את כל הקורס)

**ה-SQL לביצוע (אחרי שתחליט):**

אופציה A — refund:
```sql
UPDATE deposits
SET refund_status = 'refunded', refunded_at = NOW()
WHERE user_telegram_id = 8789977826
  AND created_at >= '2026-04-21'
  AND refund_status = 'pending_review';
-- צפוי: 3 שורות
```

אופציה B — upgrade:
```sql
INSERT INTO academy_licenses (user_id, course_id, tier, activated_at)
VALUES (
  (SELECT id FROM users WHERE telegram_id = 8789977826),
  1, 'VIP', NOW()
);
UPDATE deposits SET refund_status = 'credited_vip' WHERE user_telegram_id = 8789977826 AND refund_status = 'pending_review';
```

**הרצה:**
```bash
# Railway → Database → Query או via psql
railway run psql $DATABASE_URL -c "<SQL>"
```

**ניוטיפיקציה אחרי:**
```bash
curl.exe -X POST https://slh-api-production.up.railway.app/api/broadcast/send \
  -H "X-Admin-Key: <ADMIN_BROADCAST_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"message":"תודה על הסבלנות. הטיפול בתשלומים הושלם.","segment":"user","telegram_id":8789977826}'
```

---

## 🟢 7. החלטות אסטרטגיות — לא דחוף היום

תקרא, חשוב, חזור עם תשובות בזמן שלך:

| # | שאלה | למה חשוב |
|---|------|-----------|
| A | **Legal entity** — ח.פ. / חברה בע"מ / פטור? | חוסם גביית כסף אמיתי |
| B | **Phase 2 Identity Proxy** — Gateway אחיד לכל הבוטים? | מונע 25 קוד כפילות |
| C | **Phase 3 Ledger unification** — מספר ledgers ל-1? | מונע drift |
| D | **Webhook migration** — 22 בוטים מ-polling ל-webhook? | חוסך CPU + Railway dyno |
| E | **BSC DEX web3** — מסחר אוטומטי על PancakeSwap? | מקדים paper trading |
| F | **Mobile app MVP** — React Native? Flutter? PWA? | 2-3 שבועות פיתוח |
| G | **Trading strategy** — RSI + whale detector + volume anomaly? | דורש 24h calc_pnl data |
| H | **GUARDIAN_AUDIT** — ריץ בסשן נפרד? | refactor proposal (`ops/GUARDIAN_AUDIT_AGENT_PROMPT_20260421.md`) |

---

## 📋 Checklist סיום

- [ ] Railway Redeploy → `/api/health` מחזיר version > 1.1.0
- [ ] Website push → 3 דפים חוזרים 200
- [ ] git config global → user.name + user.email תקינים
- [ ] 10 סודות מסובבים → `.env` + Railway מעודכנים
- [ ] ANTHROPIC_API_KEY → @SLH_Claude_bot עובד על free-text
- [ ] SQL למשתמש 8789977826 → החלטה A או B, בוצע, משתמש יודע
- [ ] שאלות A-H → תחזור אלי עם תשובות מתי שנוח

---

**אחרי שסיימת את #1-3:** שלח ל-Infra/IT את `DROP_INFRA_DEVOPS.md`. כל השאר יכול לרוץ במקביל.
