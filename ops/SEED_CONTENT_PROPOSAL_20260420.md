# 🌱 SEED CONTENT PROPOSAL · 2026-04-20
**Target:** ₪1,000 first week · 3 אפיקים: Academia + Marketplace + Experts
**Instructor/Seller identity:** Osif Kaufman Ungar · telegram_id `224223270`

---

## A · 3 קורסי Academia (70/30 split → Osif מקבל 70%)

### Course 1 · בוט טלגרם בעברית — bootcamp מ-0 ל-deploy
```json
{
  "instructor_user_id": 224223270,
  "slug": "telegram-bot-bootcamp-he",
  "title_he": "בוט טלגרם בעברית — bootcamp מ-0 ל-deploy",
  "description_he": "קורס מעשי בן 5 מודולים: aiogram 3.x · handlers · FSM · middleware · Railway deploy · webhook setup. כולל boilerplate מ-SLH Spark (ecosystem של 25 בוטים בייצור).",
  "price_ils": 99,
  "price_slh": 0,
  "language": "he",
  "materials_url": "TBD — YouTube/Drive",
  "preview_url": "TBD"
}
```
**Revenue @ 10 מכירות:** 990₪ · Osif: 693₪ · Platform: 297₪

### Course 2 · מדריך SLH למשתמש — ecosystem end-to-end
```json
{
  "instructor_user_id": 224223270,
  "slug": "slh-ecosystem-user-guide",
  "title_he": "מדריך SLH למשתמש — ecosystem end-to-end",
  "description_he": "המדריך הרשמי למשתמשי SLH Spark. מה זה SLH/ZVK/MNH/REP/ZUZ. איך עושים P2P. איך פותחים shop. referral. academy. experts. community.",
  "price_ils": 29,
  "price_slh": 0,
  "language": "he",
  "materials_url": "TBD"
}
```
**Revenue @ 50 מכירות:** 1,450₪ · Osif: 1,015₪ · Platform: 435₪
*(upsell טבעי לכל 22-280 משתמשים קיימים)*

### Course 3 · Crypto Wallet לישראלי — MetaMask + BSC
```json
{
  "instructor_user_id": 224223270,
  "slug": "crypto-wallet-israeli",
  "title_he": "Crypto Wallet לישראלי — MetaMask + BSC",
  "description_he": "מ-0 ל-trading: MetaMask setup · BSC network · buy BNB · swap SLH ב-PancakeSwap · security · Israeli tax hints. ⚠️ לא ייעוץ השקעות/חשבונאי.",
  "price_ils": 149,
  "price_slh": 0,
  "language": "he",
  "materials_url": "TBD"
}
```
**Revenue @ 10 מכירות:** 1,490₪ · Osif: 1,043₪ · Platform: 447₪

**סה"כ potential שבוע ראשון (10/50/10 מכירות):** ₪3,930 gross · ₪2,751 לאוסיף

---

## B · 5 Marketplace Items (seller = Osif, auto-approved)

| # | Title | Price | Currency | Category | Stock | Type |
|---|---|---|---|---|---|---|
| 1 | ייעוץ 1:1 — שעה עם Osif (bot dev) | 199 | ILS | services | 10 | service |
| 2 | Custom Telegram bot setup (turnkey) | 499 | SLH | services | 5 | service |
| 3 | SLH API sandbox access (30 days) | 49 | ILS | digital | 50 | digital |
| 4 | Hebrew Crypto Starter Pack (PDF+Discord) | 39 | ILS | digital | 999 | digital |
| 5 | SLH Spark Membership Pack (sticker+badge) | 19 | ILS | physical | 100 | physical |

**Revenue potential:** ₪199×5 + ₪499×3 SLH + ₪49×20 + ₪39×50 + ₪19×30 = ₪4,462 + 1,497 SLH
**Platform cut (5%):** ₪223

---

## C · 2 Experts — דרוש ממך

**אי אפשר לזייף credentials של אנשים אמיתיים.** שלח לי 5 שדות לכל אחד:

### Expert #2 (מוצע: Tzvika)
- [ ] `display_name` (שם שיופיע בדף)
- [ ] `tg_username` (ללא @)
- [ ] `bio` (1-2 משפטים עברית)
- [ ] `linkedin_url` OR `website_url` OR `credentials` (אחד לפחות)
- [ ] `domains` (בחר מ: crypto, security, finance, tech, marketing)
- [ ] `years_experience` (מספר)

### Expert #3 (מוצע: Zohar Shefa Dror)
- אותם 5 שדות

---

## D · מה חסר כדי להתחיל seed חי

1. **Admin API key** — ערך של `ADMIN_API_KEYS` מ-Railway env. בלי זה אני יכול לרשום instructor ולהעלות courses ב-status `pending`, אבל **לא לאשר אותם** → לא יופיעו בקטלוג.
2. **אישור על הטקסטים** — תאשר כמו שהם / תערוך
3. **Materials URLs** — אפשר לדחות. אעלה עם TBD ותחליף מ-admin panel אחרי שתקליט/תכתוב.

---

## E · סדר הסיד (אחרי שאושר)

```bash
# 1. Register Osif as instructor
curl -X POST https://slh-api-production.up.railway.app/api/academia/instructor/register \
  -H "Content-Type: application/json" \
  -d '{"user_id":224223270,"display_name":"Osif Kaufman Ungar","bio_he":"Founder SLH Spark — Solo Dev — Full-stack Blockchain AI DevOps"}'

# 2. Admin approve instructor (needs ADMIN_API_KEY)
curl -X POST https://slh-api-production.up.railway.app/api/academia/instructor/approve \
  -H "X-Admin-Key: $ADMIN_KEY" \
  -d '{"instructor_id":<returned_id>,"approved":true}'

# 3. Create 3 courses (returns pending)
# 4. Admin approve 3 courses → active=TRUE → visible in /academia.html
# 5. Marketplace: POST /api/marketplace/list × 5 (auto-approved since seller_id==ADMIN_USER_ID)
# 6. Experts: POST /api/experts/register × 2 + admin approve
```

---

**ETA:** 15 דקות ריצה אחרי שיש לי admin key + אישור טקסטים.
