# 🧪 SLH Ecosystem — מדריך בדיקות מלא
> Date: 2026-04-09 (ערב)
> Scope: כל מה שנבנה היום + כל הקישורים לבדיקה

---

## ⚡ מה הופעל היום בפרודקשן

### 🔴 תיקונים קריטיים
1. **SLH_AIR bot (`slh-airdrop`)** — תיקון באג קריטי: כל הודעה ≥40 תווים התקבלה כ"תשלום התקבל". עכשיו:
   - דורש regex מדויק של TX hash (BSC/ETH hex64 או TON base64-44)
   - דורש `state == "awaiting_payment"` (לא יקבל תשלום מחוץ לזרימה)
   - מבדיל בין username / כתובת ארנק / TX hash
   - אין יותר "תשלום התקבל!" אוטומטי על הודעות טקסט רגילות
2. **i18n Collision** — `const T` בתוך 5 דפים (dashboard, guides, staking, whitepaper, referral-card) התנגש עם `T` הגלובלי מ-`translations.js`. כל דף עבר לשם `PAGE_T` עם fallback ל-`T` הגלובלי.

### 🟠 פיצ'רים חדשים
3. **Marketplace (חנות) מלא** — ב-`community.html` תחת טאב "חנות":
   - העלאת פריטים (כותרת, תיאור, מחיר, מטבע SLH/TON/ILS/USD, מלאי)
   - **העלאת תמונה base64 מהמכשיר** (עד 2MB, JPG/PNG/WebP) + preview
   - **טיר קידום**: חינם / מומלץ (5 SLH/day) / בולט (15) / בעמוד הבית (50)
   - סינון לפי קטגוריה: דיגיטלי / פיזי / קורסים / שירותים / NFT / כללי
   - רכישה עם FOR UPDATE lock (אטומי), הורדת מלאי אוטומטית
   - מוכרים לא יכולים לקנות מעצמם
   - מיון לפי תיר קידום (homepage > top > featured > none) → תאריך
4. **פיד קהילה משופר**:
   - העלאת תמונות לפוסטים (עמודת `image_data` ב-DB, עד 2MB)
   - **11 קטגוריות חדשות**: general, investments, slh, proposals, experts, news, **events, guides, questions, success, alerts**, updates
   - האמוג'ים מוטמעים בכפתורי הסינון ובבחירת הקטגוריה
5. **עמוד `/invite.html`** — מנגנון הפצה חוקי 100%:
   - 4 תבניות הודעה (קצר / ארוך / אישי / עסקי)
   - שיתוף לוואטסאפ, טלגרם, אימייל, FB, X, LinkedIn, native share
   - QR code אוטומטי מ-api.qrserver.com
   - **אפס אוטומציה / אפס scraping / אפס risk חסימה**
   - המשתמש לוחץ → האפליקציה הרשמית נפתחת → הוא בוחר למי לשלוח
6. **עמוד `/daily-blog.html`** — היה קיים אבל לא commited. עכשיו חי.
7. **Web3 Wallet Linking**:
   - `POST /api/user/link-wallet` — מקשר כתובת BSC/ETH (אימות 0x + 40hex)
   - `GET /api/user/wallet/{id}` / `POST /api/user/unlink-wallet`
   - עמודות חדשות: `eth_wallet`, `ton_wallet` ב-`web_users`
8. **Unified User Endpoint** — `GET /api/user/full/{id}`:
   - פרופיל + הרשמה + ארנקים מקושרים
   - כל יתרות הטוקנים (internal + bank account)
   - deposits, staking positions, referrals, transfers
   - marketplace activity (listings + orders bought/sold)
   - premium status + price info
   - **המקור היחיד של האמת** — bot/website/mini-app יציגו אותם המספרים
9. **מחיר הרשמה אחוד**: `22.221 ILS` (היה 44.4) בכל המערכת:
   - API: `REGISTRATION_PRICE_ILS = 22.221`
   - translations.js (HE/EN/RU)
   - dashboard.html (5 שפות)
   - community.html sidebar
10. **החלפת @userinfobot** — login hint ב-dashboard.html משתמש כעת ב-deep link:
    `https://t.me/SLH_AIR_bot?start=get_id` במקום בוט צד שלישי
11. **Sitemap Footer אחיד** — `renderFooter()` ב-`shared.js` מייצר פוטר 5-עמודות לכל דף:
    ראשי / קהילה / מוצרים / למד / התחברות
12. **Admin Bootstrap** — startup מבטיח שמשתמש אדמין (224223270) קיים עם:
    - `username: osifeu_prog` (מ-env var `ADMIN_USERNAME`)
    - `first_name: Osif` (מ-env var `ADMIN_FIRST_NAME`)
    - `is_registered: true`

---

## 🔗 קישורים — כל נקודות הקצה

### 🌐 Website (GitHub Pages — `slh-nft.com`)

| עמוד | URL | מה לבדוק |
|-----|-----|----------|
| Landing | https://slh-nft.com/ | נטען, topnav מתורגם, footer sitemap קיים |
| Dashboard | https://slh-nft.com/dashboard.html | login עובד, reg_* מתורגם, "קבל ID מהבוט שלנו" מקשר ל-SLH_AIR_bot |
| Community (פיד) | https://slh-nft.com/community.html | 11 קטגוריות, העלאת תמונה לפוסט, View switch פיד↔חנות |
| Community (חנות) | https://slh-nft.com/community.html (טאב חנות) | "פריט חדש", העלאת תמונה base64, קידום, רכישה |
| Invite | https://slh-nft.com/invite.html ⭐ **חדש** | 7 כפתורי שיתוף, 4 תבניות, QR, העתקת קישור |
| Daily Blog | https://slh-nft.com/daily-blog.html ⭐ **חדש** | הבלוג שלא נראה קודם |
| Guides | https://slh-nft.com/guides.html | nav_* מתורגם כעת (היה raw) |
| Staking | https://slh-nft.com/staking.html | nav_* מתורגם, 4 תוכניות |
| Whitepaper | https://slh-nft.com/whitepaper.html | nav_* מתורגם |
| Referral Card | https://slh-nft.com/referral-card.html | יצירת כרטיס, canvas, download PNG |
| Wallet | https://slh-nft.com/wallet.html | Web3 Connect button |
| Earn | https://slh-nft.com/earn.html | 4 תוכניות staking |
| Bots | https://slh-nft.com/bots.html | 20+ בוטים |
| Blockchain | https://slh-nft.com/blockchain.html | - |
| Analytics | https://slh-nft.com/analytics.html | - |
| Roadmap | https://slh-nft.com/roadmap.html | - |
| Privacy | https://slh-nft.com/privacy.html | - |
| Terms | https://slh-nft.com/terms.html | - |
| Wallet Guide | https://slh-nft.com/wallet-guide.html | - |
| Admin | https://slh-nft.com/admin.html | - |

### 🔌 API (Railway — `slh-api-production.up.railway.app`)

| Endpoint | מטרה | בדיקה |
|----------|------|-------|
| `GET /api/health` | Health check | `curl https://slh-api-production.up.railway.app/api/health` → `{"status":"ok","db":"connected"}` |
| `GET /docs` | Swagger docs | https://slh-api-production.up.railway.app/docs |
| **`GET /api/user/full/{id}`** ⭐ | כל המידע על משתמש | `curl .../api/user/full/224223270` |
| `GET /api/user/{id}` | פרופיל + יתרות | `curl .../api/user/224223270` |
| `GET /api/user/wallet/{id}` | Web3 wallet מקושר | `curl .../api/user/wallet/224223270` |
| `POST /api/user/link-wallet` | לקשר ארנק BSC/ETH | `curl -X POST .../api/user/link-wallet -d '{"user_id":224223270,"address":"0x..."}' -H "Content-Type: application/json"` |
| `POST /api/auth/telegram` | Telegram Login Widget | (via Login Widget in browser) |
| **`GET /api/marketplace/stats`** ⭐ | סטטיסטיקות חנות | `curl .../api/marketplace/stats` |
| **`GET /api/marketplace/items`** ⭐ | רשימת פריטים | `curl .../api/marketplace/items` |
| **`POST /api/marketplace/list`** ⭐ | יצירת פריט | `curl -X POST .../api/marketplace/list -d '{"seller_id":224223270,"title":"...","price":10}' -H "Content-Type: application/json"` |
| **`POST /api/marketplace/buy`** ⭐ | רכישת פריט | - |
| **`GET /api/marketplace/admin/pending?admin_id=224223270`** ⭐ | פריטים ממתינים לאישור | - |
| **`POST /api/marketplace/admin/approve`** ⭐ | אישור/דחייה | - |
| `GET /api/community/posts` | פוסטים בקהילה | `curl .../api/community/posts?limit=5` |
| `POST /api/community/posts` | יצירת פוסט (עם תמונה) | - |
| `POST /api/community/posts/{id}/like` | Like | - |
| `POST /api/community/posts/{id}/comments` | Comment | - |
| `GET /api/community/stats` | סטטיסטיקות קהילה | - |
| `GET /api/staking/plans` | 4 תוכניות staking | - |
| `POST /api/staking/stake` | יצירת position | - |
| `GET /api/referral/tree/{id}` | עץ הפניות | - |
| `GET /api/referral/leaderboard` | לידרבורד הפניות | - |
| `GET /api/wallet/{id}/balances` | יתרות | - |
| `POST /api/wallet/send` | שליחת טוקנים | - |
| `GET /api/analytics/stats` | אנליטיקה | - |
| `GET /api/admin/dashboard` | אדמין | - |

### 🤖 Telegram Bots

| בוט | Username | תפקיד | בדיקה |
|-----|----------|-------|-------|
| **Airdrop/HUB** ⭐ | @SLH_AIR_bot | בוט ראשי — השקעות, ארנק, סטייקינג, הפניות | `/start`, שלח טקסט רגיל (לא אמור להחזיר "תשלום התקבל") |
| Academia | @SLH_Academia_bot | אקדמיה | - |
| Community | @SLH_community_bot | קהילה | - |
| Guardian | @Grdian_bot | אבטחה | - |
| Wallet | @SLH_Wallet_bot | ארנק | - |
| BotShop | @Buy_My_Shop_bot | חנות בוטים | - |
| Factory | @Osifs_Factory_bot | פקטורי | - |
| OsifShop | @OsifShop_bot | מלאי עם ברקוד | - |
| Admin | @MY_SUPER_ADMIN_bot | אדמין | - |
| NFTY | @NFTY_madness_bot | Tamagotchi | - |
| NIFTI | @NIFTI_Publisher_Bot | Wellness | - |
| TON MNH | @TON_MNH_bot | TON | - |
| SLH TON | @SLH_ton_bot | TON | - |
| Ledger | @SLH_Ledger_bot | Ledger | - |
| Campaign | @Campaign_SLH_bot | שיווק | - |
| Game | @G4meb0t_bot_bot | משחקים | - |
| Chance | @Chance_Pais_bot | צ'אנס | - |
| TS Set | @ts_set_bot | Set | - |
| Selha | @Slh_selha_bot | - | - |
| Crazy Panel | @My_crazy_panel_bot | פאנל | - |
| ExpertNet | (Zvika's) | ארקייד | - |
| BeynoniBank | - | - | - |
| NFT Shop | @MY_NFT_SHOP_bot | חנות NFT | - |

---

## ✅ תרחישי בדיקה (Step-by-Step)

### Test 1: 🤖 SLH_AIR Bot — Payment False-Positive Fix
**קריטי** — לוודא שהבאג שתיקנו לא חוזר.

1. פתח https://t.me/SLH_AIR_bot
2. `/start` — צריך להראות את התפריט הראשי
3. שלח הודעה רגילה: `שלום מה קורה`
   - **ציפייה**: "🤖 לא הבנתי. לחץ /start לתפריט הראשי"
   - **לא צריך לראות**: "🎉 תשלום התקבל!"
4. שלח כתובת ארנק: `0xD0617B54FB4b6b66307846f217b4D685800E3dA4`
   - **ציפייה**: "📋 קיבלתי כתובת ארנק..."
5. שלח tx hash בלי state: `0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef`
   - **ציפייה**: "⚠️ קיבלתי Hash אבל אין בקשת תשלום פתוחה..."

### Test 2: 🏪 Marketplace — End-to-End
1. https://slh-nft.com/community.html
2. לחץ על טאב "🏬 חנות"
3. ציפייה: "אין פריטים להצגה עדיין" + סטטיסטיקות (0/0/0)
4. לחץ "➕ פריט חדש"
5. מלא:
   - כותרת: "מדריך Claude Code" (≥3 תווים)
   - תיאור: "מדריך מקיף..."
   - מחיר: 50
   - מטבע: SLH
   - קטגוריה: קורסים
   - מלאי: 10
   - **העלה תמונה** מהמכשיר (≤2MB) → Preview יוצג
   - קידום: מומלץ / בולט / בעמוד הבית
6. לחץ "פרסם"
7. ציפייה: alert "פריט הועלה לאישור" (למשתמש רגיל) או "פרסם בהצלחה" (לאדמין)
8. **כאדמין**: אשר ידנית דרך `POST /api/marketplace/admin/approve`
9. רענן → הפריט מופיע ב-grid

### Test 3: 💬 Community Feed — Image Upload
1. https://slh-nft.com/community.html — טאב "פיד"
2. כתוב פוסט + בחר קטגוריה (למשל "🎉 אירועים")
3. לחץ על "🖼️ תמונה" → בחר תמונה
4. לחץ "פרסום"
5. רענן → הפוסט עם התמונה מופיע

### Test 4: 🎁 Invite Page
1. https://slh-nft.com/invite.html
2. צריך לראות קישור אישי (עם username או "friend")
3. העתק קישור → לחיצה על "✓ הועתק!"
4. שנה טאב: קצר / ארוך / אישי / עסקי → הטקסט משתנה
5. לחץ WhatsApp → נפתח `wa.me/?text=...`
6. לחץ Telegram → נפתח `t.me/share/url?url=...`
7. QR code נטען מ-api.qrserver.com

### Test 5: 🔗 Unified User Endpoint
```bash
curl https://slh-api-production.up.railway.app/api/user/full/224223270
```
**ציפייה**: JSON עם `profile`, `wallets`, `balances`, `deposits`, `staking`, `referrals`, `transactions`, `marketplace`, `premium`, `price_info`.

### Test 6: 📖 Guides Page (i18n Fix)
1. https://slh-nft.com/guides.html
2. **ציפייה**: topnav מראה "ראשי", "מסחר", "הרוויח" (לא `nav_home`)
3. **ציפייה**: footer מציג "© 2026 SLH Spark. כל הזכויות שמורות" (לא `footer_rights`)
4. שנה שפה → כל הטקסטים מתורגמים

### Test 7: 💰 Registration Price
1. https://slh-nft.com/dashboard.html (לחוץ כמשתמש לא רשום)
2. פאנל הרשמה: **₪22.221** (לא 44.4)
3. כתובת TON להעברה: `UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`

### Test 8: 🗺️ Sitemap Footer
1. פתח כל דף באתר (index, community, staking, wallet, guides, invite, dashboard...)
2. גלול לתחתית
3. ציפייה: 5 עמודות: ראשי / קהילה / מוצרים / למד / התחברות
4. כל קישור עובד

---

---

## 🚀 פיצ'ר חדש אחרון — Auto-Registration דרך הבוט

**הרעיון שלך נכון ב-100%**. יישמתי את זה:

### מה קורה עכשיו כשמשתמש לוחץ `/start` ב-`@SLH_AIR_bot`:

1. הבוט מזהה את ה-`chat_id`, `username`, `first_name`
2. הבוט קורא אוטומטית ל-`POST https://slh-api-production.up.railway.app/api/auth/bot-sync`
3. ה-API יוצר שורה חדשה ב-`web_users` (או מעדכן קיימת):
   ```sql
   INSERT INTO web_users (telegram_id, username, first_name, ...) VALUES (...)
   ON CONFLICT (telegram_id) DO UPDATE SET ...
   ```
4. ה-API מחזיר `login_url` — קישור אישי שהמשתמש יכול ללחוץ כדי להיכנס לדשבורד בלי סיסמה
5. הבוט מציג את ה-`login_url` בהודעת `/start` (קישור HTML bold)
6. משתמש לוחץ → מגיע לדשבורד מחובר מיידית

### אבטחה:
- ה-endpoint מוגן ע"י `BOT_SYNC_SECRET` (שער מפתח שרק הבוט יודע)
- אם שולחים בלי secret → 403 Forbidden
- בעל הבוט יכול לשנות את המפתח ב-env var בפרודקשן

### Referral tracking אוטומטי:
- משתמש לוחץ קישור הפניה: `https://t.me/SLH_AIR_bot?start=ref_224223270`
- הבוט מזהה `ref_` prefix, מחלץ את ה-referrer_id
- השולח `referrer_id` ל-`/api/auth/bot-sync`
- ה-API שומר ב-טבלת `referrals` אוטומטית

### מה זה פותר?
- ✅ חיסול ההרשמה המסורבלת (לא צריך `@userinfobot`)
- ✅ חיסור מחסומים בין הבוט לאתר
- ✅ כל משתמש בוט הוא *כבר* משתמש באתר
- ✅ אחרי התשלום, אותה שורת `web_users` מקבלת `is_registered=true` → פתוח כל האזור פרימיום
- ✅ Referrals מסונכרנים אוטומטית בין הבוט למערכת ההפניות של האתר

### ✅ מה שעבד בבדיקה חיה:
```
[bot-sync] ✅ Synced 224223270 (@osifeu_prog) to website — registered=True
```

---

## 📰 הבלוג שלא ראית

הבלוג כבר קיים ב-navigation העליון — `nav_blog` (אייקון עיתון). הסיבה שלא ראית אותו:
1. `daily-blog.html` לא היה committed ב-git עד עכשיו — **תוקן, עולה ב-deploy הנוכחי**
2. ה-`T` collision ב-`guides.html` וכו' גרם ל-topnav להראות `nav_blog` כ-raw text — **תוקן**

**קישור ישיר**: https://slh-nft.com/daily-blog.html

אחרי הפריסה הבאה, הבלוג יופיע:
- ב-topnav כל הדפים (דרך `shared.js`)
- ב-sitemap footer (עמודה "קהילה" → "בלוג יומי")
- בתפריט הבוט (`/start` יציג "📰 בלוג יומי")

---

## 🚨 בעיות ידועות שטרם תוקנו

### High Priority
1. **יתרות משתמש לא מופיעות באתר**: למרות שה-bot מציג 199,788 SLH למשתמש, ה-`web_users` + `token_balances` ב-Railway DB ריקים. **הסיבה**: הבוט משתמש ב-`_user_data` **בזיכרון RAM בלבד** (לא נשמר ל-DB כלל). צריך לאחד את הבוט עם אותו DB של ה-API. ראה "תוכנית איחוד יתרות" למטה.

2. **Mini App לא מסונכרן**: "0.00 TON, 0 SLH" — אותו מקור בעיה. ה-mini-app קורא לRailway API שלא מכיר את המשתמש.

3. **פעולות אדמין ל-marketplace חסרות UI**: `POST /api/marketplace/admin/approve` קיים ב-API אבל אין כפתור באתר. צריך UI ב-`admin.html`.

4. **PAGE_T namespacing טרם יושם ב**: `bots.html`, `index.html`, `trade.html`, `earn.html`, `wallet.html`, `blockchain.html`, `analytics.html`, `roadmap.html`, `admin.html`, `privacy.html`, `terms.html` — אם משתמשים שם ב-`const T` הם יסבלו מאותו collision. צריך לבדוק כל אחד ולתקן.

### Medium Priority
5. **ASCII art לא אחיד בבוטים** — כל בוט עם פורמט משלו (משימת יום מחר)
6. **7 themes לא עקביים** — המשתמש דיווח שאיבדו מהיופי (בדיקה + שחזור)
7. **Real Analytics** — אין dashboard של באמת כמה משתמשים נכנסים היום
8. **Sales funnel analytics** — חסר (איפה משתמשים נושרים)
9. **Paywall gating** — הבלוג ועמודי קהילה פתוחים לכולם (אמור להיות Paid Only)

### Low Priority
10. **אנימציות טקסט בכפתורים** (typing effect)
11. **7 themes visual refinement**

---

## 🏗️ תוכניות טכניות לבדיקה שלך

### 💰 תוכנית 1: איחוד יתרות (המשך מחר)

**הבעיה**: 3 מקורות נתונים לא מסונכרנים:
- `slh-airdrop` bot → `_user_data` dict ב-RAM (ניתן לאיפוס כל הפעלה)
- Railway DB → `web_users`, `token_balances` (האמת של האתר + mini-app)
- Blockchain אמיתי → BSC + TON (אמת חיצונית)

**ההצעה**: 3 רבדים של אמת עם resolver אחד:
```
┌──────────────────────────────────────────┐
│  GET /api/user/full/{id}                 │
│  (single source of truth)                │
└──────────┬───────────────────────────────┘
           │
    ┌──────┴───────┐
    │              │
    ▼              ▼
┌─────────┐  ┌──────────────┐
│  DB     │  │  Blockchain  │
│internal │  │  readers     │
│balances │  │  (BSC+TON)   │
└────┬────┘  └──────┬───────┘
     │              │
     └──────┬───────┘
            ▼
    ┌───────────────┐
    │ merge +       │
    │ reconcile     │
    │ (DB is cache) │
    └───────────────┘
```

**שלבים**:
1. **יום 1**: המר את `slh-airdrop` לקרוא/כתוב ל-Railway DB במקום ל-RAM. כל `_get_user()` → SQL query. כל עדכון → SQL update.
2. **יום 2**: הוסף `sync_balances_from_chain.py` job שרץ כל 30 שניות:
   - קורא את `web_users.eth_wallet` של כל משתמש
   - קורא את היתרה האמיתית מ-BSC (דרך web3.py)
   - מעדכן `web_users.eth_slh_balance` + `eth_bnb_balance` + `eth_usdt_balance`
   - אותו דבר לקריאת TON
3. **יום 3**: ב-`/api/user/full/{id}` החזר את שני הערכים: `internal_balance` ו-`onchain_balance`. הדשבורד יציג אותם זה לצד זה.

**יתרון**: כל הנתונים תמיד טריים, ה-DB הוא cache חכם, הלקוח רואה גם פנימי וגם on-chain.

### 🌐 תוכנית 2: DAG של Proof-of-Holding

**הרעיון**: במקום לסמוך על DB מרכזי, כל פעולה כלכלית (deposit, transfer, staking, purchase) יוצרת **node ב-DAG** שמקושר ל-nodes קודמים בהאש. המשתמש יכול "להוכיח אחזקה" על ידי הצגת שרשרת ה-nodes שלו.

**מבנה node**:
```python
{
  "id": "uuid",
  "type": "deposit|transfer|stake|purchase|reward",
  "user_id": 224223270,
  "amount": 10.5,
  "token": "SLH",
  "parent_hashes": ["hash1", "hash2"],  # מצביע ל-nodes קודמים
  "timestamp": 1712656800,
  "signature": "ed25519_sig",            # חתום ע"י מפתח פרטי של המשתמש
  "merkle_root": "hash_of_user_state_after_this_node"
}
```

**שימושים**:
1. **Proof-of-Holding**: משתמש ציבורית מראה את השרשרת של ה-nodes שלו — כולם יכולים לאמת שהוא אכן החזיק X טוקנים בתאריך מסוים
2. **Proof-of-Work (כלכלי)**: כל staking/deposit מוסיף "משקל" ל-node → דירוג משתמשים לפי פעילות
3. **Audit Trail**: אי אפשר למחוק היסטוריה (append-only)
4. **Cross-bot economy**: כל בוט יכול לכתוב nodes לאותו DAG — שקיפות מלאה
5. **Recovery**: אם הDB נפגע, אפשר לשחזר ממחסן הnodes המבוזר

**מבנה DB**:
```sql
CREATE TABLE dag_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    amount NUMERIC(18,8),
    token TEXT,
    parent_hashes TEXT[],
    metadata JSONB,
    signature TEXT,
    merkle_root TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_dag_user (user_id, created_at DESC)
);
```

**API**:
- `POST /api/dag/append` — הוספת node חדש (צריך חתימה)
- `GET /api/dag/chain/{user_id}` — כל ה-nodes של משתמש
- `GET /api/dag/proof/{user_id}?asset=SLH&timestamp=X` — הוכחה שהחזיק X SLH בזמן מסוים
- `GET /api/dag/verify/{node_id}` — אימות ש-node תקף (parent_hashes קיימים + חתימה חוקית)

**זמן מימוש**: 3-5 ימי פיתוח.

### 🎨 תוכנית 3: שחזור 7 ה-Themes

1. **אבחון**: פתח כל דף עם כל theme ובדוק מה נשבר
2. **מצא את `shared.css`** — וודא שיש `.theme-1` עד `.theme-7` עם `--accent`, `--bg`, `--surface`, `--text` מוגדרים היטב
3. **בדוק שהפוטר החדש (sitemap)** מגיב לכל theme (משתמש ב-`var(--accent)`, `var(--surface)`, `var(--border)`)
4. **הוסף ברירות מחדל לצבעים שחסרים** ב-theme spec

**זמן מימוש**: 2-3 שעות.

### 📊 תוכנית 4: Real Analytics Dashboard

**מקורות נתונים קיימים**:
- `POST /api/analytics/event` — כבר קיים
- `GET /api/analytics/stats` — כבר קיים

**מה חסר**:
- הפעלת tracking בכל דף (`/js/analytics.js` קיים אבל אולי לא פעיל בכל העמודים)
- דף `analytics.html` שמחבר לנתונים אמיתיים (כעת מראה mock)
- פאנל אדמין שמראה:
  - משתמשים היום / 7 ימים / חודש
  - Top 10 pages
  - Referrer sources
  - Funnel: Landing → Register → Pay → Use
  - Drop-off points

**זמן מימוש**: יום עבודה.

### 💎 תוכנית 5: Paywall Gating

**Logic**:
```js
if (page in ['community.html', 'daily-blog.html', 'analytics.html']) {
  const user = getUser();
  if (!user || !user.is_registered) {
    window.location.href = '/dashboard.html#register';
  }
}
```
+ בדיקה בצד ה-API לכל endpoint רגיש.

**זמן מימוש**: 1-2 שעות.

---

## 🗓️ Roadmap למחר (2026-04-10)

### Priority 1 (קריטי)
1. ✅ שחזור 7 Themes
2. ✅ ssync יתרות — המר את slh-airdrop מ-RAM ל-DB (תוכנית 1 שלב 1)
3. ✅ בדיקה + תיקון של שאר העמודים שיש להם `const T` collision (ראה "Medium Priority" מעל)
4. ✅ Paywall Gating על community.html + daily-blog.html

### Priority 2 (חשוב)
5. ✅ Marketplace admin UI ב-`admin.html` (אישור/דחיית פריטים)
6. ✅ On-chain balance sync (תוכנית 1 שלב 2)
7. ✅ Real Analytics dashboard

### Priority 3 (שיפורים)
8. ASCII art unified in all bots
9. Animations + typing effects
10. DAG prototype (תוכנית 2)

---

## 📞 דיווח באגים
- הוסף ל-`ops/DAILY_BLOG.md` כל תוצאה של בדיקה
- צלם screenshot של כל בעיה
- נסה לשחזר לפני שמדווח

---

*דוח נוצר אוטומטית — 2026-04-09*
*Status: Marketplace + Web3 + i18n fixes LIVE on production*
