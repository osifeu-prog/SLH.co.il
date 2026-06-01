# SLH Ecosystem — Full Agent Handoff Prompt
## Copy this entire file as the first message to the new session

---

אתה ממשיך פיתוח של SLH Spark Ecosystem — פלטפורמת קריפטו עם 7+ בוטים של טלגרם, אתר עם 42 דפים, API עם 91 endpoints, ו-Pool חי על PancakeSwap.

## קרא את הקבצים האלה לפני שתתחיל:
1. `D:\SLH_ECOSYSTEM\ops\SESSION_HANDOFF_20260412.md` — handoff מלא עם סטטוס כל המשימות
2. `D:\SLH_ECOSYSTEM\ops\UPGRADE_PLAN_20260412.md` — תוכנית שדרוג 11 פאזות
3. `D:\SLH_ECOSYSTEM\ops\SECURITY_AUDIT_20260412.md` — דוח אבטחה

---

## מה בוצע ב-Session האחרון (Session 9)

### P0a: launch-event.html — תוקן (מקומי, לא נדחף לגיטהאב)
**קובץ:** `D:\SLH_ECOSYSTEM\website\launch-event.html`
- הוסר מקסימום 0.05 BNB מהטופס (שדה input — הוסר max="0.05", שונה ל-placeholder="0.1")
- שונה סטטוס מ-FILLED ל-OPEN (בתצוגה + ב-JS שמקבל מ-API)
- Badge עודכן מ-"Live Event · 11 אפריל 2026" ל-"OPEN · Genesis Pool פעיל"
- הטקסט "מינימום 0.01 BNB, מקסימום 0.05 BNB" שונה ל-"מינימום 0.01 BNB, ללא הגבלת מקסימום" (בשני מקומות: step-card + warning box)
- Progress target שונה מ-"יעד: 0.05 BNB" ל-"הוסיפו liquidity ל-Pool!"
- ב-JS: `stat-status` fallback שונה מ-'LIVE' ל-'OPEN', ו-FILLED מתורגם ל-OPEN

### P0b: referral.html — תוקן (מקומי, לא נדחף)
**קובץ:** `D:\SLH_ECOSYSTEM\website\referral.html`
- **הבאג:** הלינקים הציגו `ref_User` או `ref_username` במקום `ref_224223270` (telegram_id אמיתי)
- **הפתרון:** שינוי `getRefUsername()` ל-`getRefId()` — משתמש ב-`user.id` במקום `user.username`
- שונו כל הפונקציות: `generateLink()`, `updateShareLinks()`, `renderBotLinks()` — כולן מקבלות `refId` (מספרי) במקום `username`
- Init section שונה: `if (user && user.id)` במקום `if (user && user.username)`
- Prefill שדה input: `user.id` במקום `user.username`
- Placeholder עודכן: "Telegram ID (e.g. 224223270)" במקום "Enter your Telegram username"
- הלינקים כעת: `https://t.me/SLH_AIR_bot?start=ref_224223270` (נכון!)

### P0c: ניווט אחיד — תוקן חלקית (מקומי)
**קבצים שתוקנו:**
- `roadmap.html` — שונה `<div id="topnav">` ל-`<div id="topnav-root">`, נוספו ticker-root, footer-root, bottomnav-root
- `daily-blog.html` — נוספו footer-root, bottomnav-root (לפני </body>)
- `getting-started.html` — נוסף bottomnav-root (אחרי footer-root הקיים)
- `onboarding.html` — נוספו footer-root, bottomnav-root (לפני </body>)
- `invite.html` — נוסף footer-root (לפני </body>)

**קבצים שעדיין חסר להם ניווט:**
- `broadcast-composer.html` — חסר הכל (topnav, bottomnav, footer) + חסר shared.js
- `partner-launch-invite.html` — חסר הכל + חסר shared.js
- `rotate.html` — קובץ טסט
- `test-bots.html` — קובץ טסט

### סריקה מלאה של הפרויקט — הושלמה
4 סוכני חקירה רצו במקביל וסרקו:

**סריקת HTML (42 דפים):**
- 38/42 דפים עם ניווט תקין
- 22/42 דפים עם data-i18n
- ~25/42 דפים עם theme support
- כתובת ארנק 0xd061de73B06d5E91bfA46b35EfB7B08b16903da4 נמצאה ב-5 קבצים: launch-event.html, partner-launch-invite.html, ecosystem-guide.html, broadcast-composer.html, morning-checklist.html

**סריקת JS/CSS:**
- shared.js (40KB, 1157 שורות): nav, auth, i18n, theme, utils — ארכיטקטורה נקייה
- translations.js (80KB, 2207 שורות): 1000+ מפתחות, 5 שפות (he, en, ru, ar, fr)
- shared.css (100KB, 2320 שורות): 7 themes (dark, terminal, crypto, cyberpunk, ocean, sunset, light), responsive, RTL
- web3.js + web3-wallet.js: MetaMask/Trust Wallet, BSC/TON connect
- ai-assistant.js: floating chat widget, 4 LLM providers (Groq→Gemini→Together→OpenAI)
- analytics.js: visitor tracking, events, heartbeat
- getCurrentUser() מחזיר: { id, username, photo, wallets: {bsc, ton}, profilePhoto, coverPhoto, avatarGrad }
- localStorage keys: slh_user, slh_jwt, slh_lang, slh_theme, slh_ref, slh_wallets_backup, slh_cookie_consent

**סריקת API (91 endpoints, main.py 4600 שורות):**
- Auth: Telegram OAuth → JWT (12h expiry)
- Admin: X-Admin-Key header OR JWT where user_id == 224223270
- 4 default admin keys hardcoded: slh2026admin, slh_admin_2026, slh-spark-admin, slh-institutional
- COMPANY_BSC_WALLET = "0xd061de73B06d5E91bfA46b35EfB7B08b16903da4" (line 4924)
- BNB price hardcoded to $608 (outdated)
- SLH internal price: 444 ILS / $121.64
- No Redis — in-memory cache only (prices 60s, holders 5min)
- CoinGecko for prices, BitQuery/BSCScan for holders, 4 LLM providers for AI chat
- CEX integration: Bybit V5 + Binance V3 (encrypted API keys via AES-GCM)

**סריקת תשתית:**
- 25+ בוטים ב-docker-compose.yml (465 שורות)
- PostgreSQL 15: 5 databases (slh_main, slh_guardian, slh_botshop, slh_wallet, slh_factory)
- Redis 7: 3 databases + streams
- D:\SLH_PROJECT_V2 — deployment נפרד על Railway (webhook-based), לא backup! עלול להתנגש עם ECOSYSTEM
- D:\SLH — React Native mobile app (incomplete, last modified Feb 2026)

---

## ממצאי אבטחה קריטיים (טפל קודם!)

### SEC-1: סיסמאות אדמין חשופות ב-HTML ציבורי
- broadcast-composer.html (line 201) — 4 סיסמאות גלויות
- ecosystem-guide.html (line 290) — אותן 4 סיסמאות
- חפש: slh2026admin, slh_admin_2026, slh-spark-admin, slh-institutional
- **פעולה:** מחק מ-HTML, העבר ל-server-side auth

### SEC-2: API endpoints ללא הגנה
- `POST /api/tokenomics/burn` — כל אחד יכול לשרוף טוקנים
- `POST /api/tokenomics/reserves/add` — כל אחד יכול להוסיף reserves
- `POST /api/tokenomics/internal-transfer` — כל אחד יכול להעביר טוקנים
- **פעולה:** הוסף admin_key או JWT auth

### SEC-3: Railway env vars חסרים
- JWT_SECRET: ❌ ריק
- ADMIN_API_KEYS: ❌ defaults
- ADMIN_BROADCAST_KEY: ❌ default
- BOT_SYNC_SECRET: ❌ default
- BITQUERY_API_KEY: ❌ dummy "1123123"

### SEC-4: כתובת ארנק — צריך אישור מהמשתמש
- בקוד: 0xd061de73B06d5E91bfA46b35EfB7B08b16903da4
- ב-AI chat: 0xD0617B54FB4b6b66307846f217b4D685800E3dA4 (שונה!)
- שאל את המשתמש מה הכתובת הנכונה

---

## מה צריך לעשות (סדר עדיפויות)

### מיידי — לפני הכל:
1. **שאל את המשתמש מה כתובת הארנק הנכונה** — עדכן ב-5 קבצי HTML + API
2. **מחק סיסמאות אדמין מ-HTML** — broadcast-composer.html, ecosystem-guide.html
3. **Push לגיטהאב** — כל השינויים המקומיים (launch-event, referral, nav fixes)
   - Website repo: `D:\SLH_ECOSYSTEM\website\` → github.com/osifeu-prog/osifeu-prog.github.io (branch: main)
   - API repo: `D:\SLH_ECOSYSTEM\api\` → github.com/osifeu-prog/slh-api (branch: master)

### Phase 1: Launch-Event Upgrade
- הוסף כפתור "Add Liquidity" ישיר ל-PancakeSwap: `https://pancakeswap.finance/v2/add/BNB/0xACb0A09414CEA1C879c67bB7A877E4e19480f022`
- הוסף dropdown לבחירת מטבע (BNB/USDT/BUSD) בטופס contribute
- שקול Swap widget embed בדף trade.html
- עדכן מחיר BNB מ-$608 hardcoded ל-live feed מ-CoinGecko

### Phase 4: Blockchain Page
- blockchain.html מציג "Loading..." לנצח
- חבר ל-BSCScan API: `?module=account&action=tokentx&contractaddress=0xACb0A09414CEA1C879c67bB7A877E4e19480f022`
- הוסף גרפים עם Chart.js
- הצג את כל 4 הטוקנים: SLH, MNH, ZVK, REP

### Phase 5: Community Image Upload
- community.html — כפתור upload קיים אבל תמונות לא נשמרות
- צריך: file → canvas resize → base64 → API POST → display

### Phase 7: P2P
- 4 endpoints כבר קיימים ב-API: create-order, list, fill, cancel
- p2p.html — החלף "Coming Soon" בלוח הזמנות חי

### Phase 8-11: ראה UPGRADE_PLAN_20260412.md

---

## מבנה הפרויקט — מידע חיוני

**URLs:**
- Website: https://slh-nft.com (GitHub Pages)
- API: https://slh-api-production.up.railway.app
- Pool: https://bscscan.com/address/0xacea26b6e132cd45f2b8a4754170d4d0d3b8bbee
- SLH Contract: 0xACb0A09414CEA1C879c67bB7A877E4e19480f022
- Swap: https://pancakeswap.finance/swap?outputCurrency=0xACb0A09414CEA1C879c67bB7A877E4e19480f022&chain=bsc

**Token Info:**
- SLH: max supply 111,186,328, BSC BEP-20
- MNH: ILS-pegged stablecoin (1 MNH = 1 ILS)
- ZVK: activity rewards (100 ZVK = 1 SLH)
- REP: reputation points

**Co-Founders (verified):**
- Tzvika (0.02 BNB) — @tzvika
- Eli (0.03 BNB)
- Zohar Shefa Dror (0.01 BNB)
- Total raised: 0.06 BNB

**Admin:**
- Telegram ID: 224223270 (Osif)
- Language: Hebrew (direct, action-oriented, no long explanations)

**שים לב:**
- המשתמש מדבר עברית, מעדיף פעולה ישירה ולא הסברים ארוכים
- אל תמעיט בהיקף — תן כבוד למערכת הגדולה שהוא בונה
- שמור על handoff מעודכן אחרי כל session
- כתובת הארנק בדף launch-event עשויה להיות לא נכונה — שאל לפני שינוי
