# 📦 SLH Spark · Session Handoff · 2026-04-17 Evening

**שיחה זו מועברת לארכיון.** הקובץ הזה מחליף את השיחה.

---

## 🎯 מה בוצע בסשן הזה

### Track 1 · Payments (BSC QR + tolerance + auto-monitor)

**בעיה:** Osif שלח 0.0005 BNB דרך בינאנס, קיבל שגיאת "amount too low: got 0.000490" כי בינאנס מנכה עמלת משיכה.

**תיקונים שעלו לייצור (commit `4c9d8a8`):**

1. **BSC QR format מתוקן** (`website/pay.html`):
   - לפני: QR הכיל רק כתובת גולמית (wallets ברירת מחדל ל-Ethereum → שליחה ברשת שגויה)
   - אחרי: EIP-681 format → `ethereum:0xd061...@56?value={wei}`
   - `@56` = BSC chain ID (auto-switch ברשת) · `value=` = סכום אוטומטי
   - תומך: MetaMask Mobile, Trust Wallet, SafePal, TokenPocket, imToken

2. **TON QR format מתוקן** (אותו קובץ):
   - לפני: כתובת בלבד
   - אחרי: `ton://transfer/{addr}?amount={nanoton}&text=SLH-{product}`
   - Tonkeeper/Wallet ממלאים סכום אוטומטית

3. **Tolerance של 0.00002 BNB** (`routes/payments_auto.py` + `api/routes/payments_auto.py`):
   - קולט עמלות משיכה מבורסות (Binance = 0.00001 · Kraken = 0.0005)
   - `min_acceptable = expected_min - 0.00002`
   - Osif TX יעבור אימות ברגע ש-Railway יסיים deploy

4. **Auto-monitor scaffold** (`routes/payments_monitor.py`):
   - Background task שעושה polling לכתובת Genesis כל 30 שניות
   - טבלאות חדשות: `pending_payment_intents` + `unmatched_deposits`
   - API חדש: `POST /api/payment/monitor/intent` · `GET /api/payment/monitor/status`
   - רשום ב-main.py (שורות 24, 154, 202-203)

**צעד הבא:** `pay.html` צריך לקרוא ל-`/intent` לפני הצגת QR כדי ש-auto-match יעבוד.

### Track 2 · Content (5/5 blog posts)

כל הפוסטים ב-`website/blog/`:

| # | File | נושא |
|---|------|------|
| 1 | `neurology-meets-meditation.html` | נוירולוגיה + מדיטציה |
| 2 | `crypto-yoga-attention.html` | קריפטו + יוגה + תשומת לב |
| 3 | `verified-experts-not-influencers.html` | REP token · מומחים אמיתיים |
| 4 | `slh-ecosystem-map.html` | 6 שכבות המערכת |
| 5 | `anti-facebook-manifesto.html` | 7 עקרונות · אנטי-פייסבוק |

כל פוסט: RSS link, OG tags, SEO, abstract באנגלית, internal links, CTAs.

### Track 3 · UI/UX (U.1 + U.2 + U.5)

- **U.1** Design System: `website/css/slh-design-system.css` — tokens, 5 themes (dark/light/zen/sunset/ocean), prefers-reduced-motion, sr-only-focusable
- **U.2** Unified Nav: `website/js/slh-nav.js` — role-based (guest/user/admin), theme dropdown, language picker (HE/EN + auto-RTL), mobile hamburger
- **U.5** Skeleton Loaders: `website/js/slh-skeleton.js` — API: `show/hide/withSkeleton/fetchJson/track/apply/reveal` · types: text/title/avatar/card/list

### Track 4 · Tour + Agent Tracker

- **`website/tour.html`** — 8-station onboarding: userinfobot → dashboard → community → sudoku → learning-path → experts → settings → pay
- **`website/agent-tracker.html`** — לוח מרכזי של 6 הסוכנים (Content Writer, UI/UX, Social Automation, ESP, Master Executor, G4meb0t) · סטטוסים (פעיל/ממתין/חסום/סיים)

### Track 5 · E2E Test Suite

- **`scripts/e2e-smoke-test.ps1`** — PowerShell script שבודק 13 endpoints ב-6 tracks
- שימוש: `.\scripts\e2e-smoke-test.ps1 -AdminKey "slh2026admin"`

---

## 🤖 סטטוס סוכני משנה

| סוכן | סטטוס | חסם |
|------|-------|-----|
| #1 Content Writer | ✅ סיים W.1 (5/5 פוסטים) | — |
| #2 UI/UX | ✅ סיים U.1/U.2/U.5 · פעיל U.3/U.4 | — |
| #3 Social Automation | ⏸ חסום | `N8N_PASSWORD=...` + "מאשר docker compose" |
| #4 ESP Firmware | ⏸ חסום · מסך שחור | colorTest מ-PowerShell · אימות TFT_BL pin |
| #5 Master Executor | 🟢 פעיל שוטף | — |
| #6 G4meb0t | ⏸ ממתין | BotFather token |

---

## 🚦 מה שהתגלה בזמן הסשן

### 1. ESP CYD (agent #4)
- ESP32-2432S028 = CYD עם TFT ILI9341 (לא OLED)
- הקבצים נכתבו ל-`D:\SLH_ECOSYSTEM\esp-firmware\src` אבל `pio run` רץ מ-`C:\Users\USER\Desktop\SLH\ESP32-2432S028` → ESP עלה עם קוד ישן
- פתרון שנשלח: overwrite הקבצים ב-C: folder + הוספת colorTest + backlight כפול (GPIO 21 + 27 במקרה CYD v2)
- ממתין לתגובה

### 2. Osif's BNB TX (**חסום · צריך טיפול ידני**)
- Hash: `0x2a9d5da99172b7e6c758ea07457d419be891df68b539b9966f092ec0f17a262a`
- From: `0xeb2d2f1b8c558a40207669291fda468e50c8a0bb` (Binance hot wallet)
- To: `0xd061de73b06d5e91bfa46b35efb7b08b16903da4` ✅ Genesis
- Value: 0.000490 BNB (שלח 0.0005, בינאנס ניכה 0.00001)
- **Status:** Tolerance fix deployed, אבל `/bsc/auto-verify` מחזיר **500 Internal Server Error** על ה-TX הזה
- **Debug:** Fake TX → `404: TX not found` (flow OK) · real TX → 500 ב-`_grant_premium` או `_issue_receipt`
- **חשוד:** עמודה `plan_key` בטבלת `deposits` בייצור לא קיימת, או schema drift אחר
- **תיקון ידני לסשן הבא:**
  ```sql
  -- בדוק schema
  \d deposits
  \d payment_receipts
  -- אם plan_key חסר:
  ALTER TABLE deposits ADD COLUMN IF NOT EXISTS plan_key TEXT DEFAULT 'premium';
  -- הזן ידנית את ה-deposit של Osif:
  INSERT INTO deposits (user_id, amount, currency, tx_hash, status, plan_key)
  VALUES (224223270, 0.000490, 'BNB', '0x2a9d5da99172b7e6c758ea07457d419be891df68b539b9966f092ec0f17a262a', 'approved', 'test_min');
  INSERT INTO premium_users (user_id, bot_name, payment_status)
  VALUES (224223270, 'ecosystem', 'approved')
  ON CONFLICT (user_id, bot_name) DO UPDATE SET payment_status = 'approved';
  ```

### 3. Dating group boundary (חשוב)
- `t.me/+nKgRnWEkHSIxYWM0` = קבוצת **הכרויות אישית** של Osif
- **לא** לפרסום ציבורי, **לא** לקטינים
- בעבר הוצגה ב-join-guide.html כ"Command Center" — הוסרה

---

## 📬 משימות פתוחות (המשך בסשן הבא)

### דחוף
1. **תיקון schema drift ב-deposits** — /bsc/auto-verify מחזיר 500 על Osif TX. בדוק עמודה plan_key קיימת. הוסף ידנית עם SQL שלמעלה. (5 דקות)
2. **לשלוח `N8N_PASSWORD`** → סוכן #3 מתחיל להרכיב את n8n
3. **ESP CYD** → הרץ את colorTest שנשלח, שלח תוצאה (אילו צבעים נראו?)
4. **monitor router 404** — `/api/payment/monitor/status` לא זמין בייצור למרות שקוד קיים. בדוק Railway logs למצוא crash בזמן startup.

### חשוב
4. חיבור pay.html לאוטו-מוניטור: להוסיף קריאה ל-`POST /api/payment/monitor/intent` לפני הצגת QR
5. G4meb0t BotFather token
6. U.3 Typography audit + U.4 Responsive audit (סוכן #2)
7. Railway env vars: `JWT_SECRET` ריק, `ADMIN_API_KEYS` עדיין default

### נחמד שיהיה
8. W.2: 30 פוסטים לרשתות חברתיות (סוכן #1)
9. W.3: Email templates (סוכן #1)
10. `/blog.html` — index של 5 הפוסטים החדשים
11. i18n על 27 דפים נוספים
12. Theme switcher על 25 דפים נוספים

---

## 🔑 Credentials + Addresses

- **Admin key:** `slh2026admin` (Railway ADMIN_API_KEYS) + משני מותאם
- **Genesis wallet (BSC):** `0xd061de73B06d5E91bfA46b35EfB7B08b16903da4`
- **SLH contract:** `0xACb0A09414CEA1C879c67bB7A877E4e19480f022`
- **Telegram channels:** `@slhniffty` (ציבורי), DATING `t.me/+nKgRnWEkHSIxYWM0` (פרטי)
- **Phone #2:** +972 53-314-5747 (ל-2FA)

---

## 🎬 פרומפט לסשן הבא (העתק-הדבק)

```
שלום. זהו Session Handoff של סשן ערב 17.4.
קרא קודם: ops/SESSION_HANDOFF_2026-04-17_evening.md

עדיפויות:
1. אמת tolerance fix על ה-TX של Osif (hash + user_id בקובץ)
2. בדוק monitor status: curl slh-api-production.up.railway.app/api/payment/monitor/status
3. אם Osif שלח N8N_PASSWORD → סוכן #3 מתחיל S.1
4. אם Osif ענה על ה-CYD (colorTest) → סוכן #4 עובר ל-E.2
5. הוסף קריאה ל-intent register ב-pay.html לפני הצגת QR

כללים:
- עברית ב-UI, אנגלית ב-code/commits
- אל תעביר טוקנים/סיסמאות ל-HTML
- Railway בונה מ-ROOT main.py — סנכרן עם api/main.py
- הקבוצה `t.me/+nKgRnWEkHSIxYWM0` פרטית (הכרויות), אסור לקטינים
- BETA banner + bug FAB בכל דף
```

---

**Session owner:** Osif Kaufman Ungar (@osifeu_prog · 224223270)
**Session closed:** 2026-04-17 · ערב
**Commits pushed:** `4c9d8a8` (API) · website commits קיימים ב-origin/main
