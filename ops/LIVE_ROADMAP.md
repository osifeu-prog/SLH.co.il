# 🎯 SLH · LIVE ROADMAP
> **מסמך חי אחד — הכל מתעדכן פה.** לא לסמוך על מסמכים אחרים לתכנון, רק על זה.
> Last updated: 2026-04-17 12:45 by Claude Code

---

## 🧭 5 יעדים ראשיים (מה SLH באמת נועד לעשות)

| # | יעד | למה חשוב | סטטוס |
|---|-----|----------|-------|
| 1 | 💰 **הכנסה חיה מחר** | תשלומים אוטומטיים, גלובליים, מכל מטבע | 🟢 70% |
| 2 | 🎓 **רשת מומחים מאומתים** | לא "אני אומר" — הוכחות, וידאו, LinkedIn, קרדיטים | 🟡 30% |
| 3 | 💝 **בוט הכרויות איכותי (@G4meb0t_bot_bot)** | בת זוג + משפחה + בית | 🔴 5% |
| 4 | 🚪 **תנועה בלי פייסבוק** | Google SEO, IG/LinkedIn/X אוטומציה, Telegram Ads, Meetup | 🔴 10% |
| 5 | 🏘 **רשת חברתית איכותית לישראל** | הבלוג האישי + Feed קהילתי במקום פייסבוק | 🟡 40% |

---

## ✅ Track 1 · Payments (70% → 100% עד סוף יום)

### Done היום
- [x] `/api/payment/ton/auto-verify` — toncenter אימות TX ל‑30ש
- [x] `/api/payment/bsc/auto-verify` — bscscan אימות BNB ל‑30ש
- [x] `/api/payment/external/record` — Stripe/PayPal/Bit/PayBox/iCount/Cardcom/Meshulam/Isracard/GrowClub/manual_bank
- [x] `/api/payment/receipt` — קבלה דיגיטלית אוטומטית `SLH-YYYYMMDD-NNNNNN`
- [x] `/api/payment/status/{user_id}` + `/api/payment/receipts/{user_id}`
- [x] `/api/payment/config` + `/api/payment/geography/summary`
- [x] buy.html — UI של "כבר שילמת? אמת עכשיו"
- [x] 10 ספקים חיצוניים רשומים במערכת

### Pending (מחכה לך 🔴 או לי 🟢)
- [x] 🔴 **TON_PAY_ADDRESS ב‑Railway** ✅ הוספת עכשיו (מחכה ל‑deploy)
- [ ] 🔴 **BSCSCAN_API_KEY** — דרך Etherscan v2 (bscscan התאחד)
- [ ] 🔴 **SILENT_MODE=1** ב‑Railway
- [ ] 🟢 **PancakeSwap TX tracker** — event-stream ל‑SLH/WBNB pair, זיהוי קונים אוטומטי (~90 דק')
- [ ] 🟢 **Stripe webhook endpoint** — ברגע שיש Stripe account (~60 דק')
- [ ] 🟢 **Bit/PayBox integration** — ישראלי (~45 דק')
- [ ] 🟢 **admin.html → Payments Geography dashboard** — תשלומים לפי מדינה/מטבע (~40 דק')
- [ ] 🟢 **Dashboard KPI: "Today's Revenue"** — ₪+₪+TON+BNB+ILS בזמן אמת (~30 דק')

---

## 🎓 Track 2 · Verified Experts (30%)

### Done
- [x] `experts.html` — עמוד בסיסי קיים
- [x] `/api/experts/register`, `/api/experts/consult`, `/api/experts/review`, `/api/experts/domains/propose`, `/api/experts/domains/vote`
- [x] רשת מומחים כבר הוגדרה ב‑30 תחומים

### Planned
- [ ] 🟢 **טופס הוכחת-מומחיות משופר** ב‑experts.html:
  - שדות חובה: LinkedIn / YouTube / אתר / תעודות / שנות ניסיון / דוגמאות פרויקטים
  - סטטוס: `pending_verification` / `verified` / `rejected`
- [ ] 🟢 **ממשק אישור מנהל** ב‑admin.html — אתה מאשר/דוחה מומחים ידנית (שלב ראשון)
- [ ] 🟢 **"Verified Expert" badge** עם תג זהב
- [ ] 🟢 **תגמול אוטומטי** — מומחה מאומת מקבל בונוס SLH + חשיפה בדף הבית
- [ ] 🟢 **גלריית מומחים** עם פילטר לפי תחום, אזור, שנות ניסיון
- [ ] 🟣 **AI אימות אוטומטי (Phase 2)** — סקר LinkedIn/YouTube/Google Search עם GPT, מחזיר ציון אמינות

**משימה מיידית:** אני יכול להרחיב את experts.html + לבנות את תהליך האישור ב‑admin.html. ~120 דק'.

---

## 💝 Track 3 · Dating Bot `@G4meb0t_bot_bot` (5%)

### Status
- [ ] הבוט קיים ב‑BotFather, token נוצר
- [ ] קוד ריק / לא פעיל
- [ ] לא משולב עם SLH ecosystem

### Planned (build from scratch)
- [ ] 🟢 **Bot skeleton** — aiogram 3.x, /start, /profile, /match (~60 דק')
- [ ] 🟢 **Profile schema** — גיל, מיקום, תחומי עניין, "רוצה ילדים", הוכחות (~30 דק')
- [ ] 🟢 **DB tables** — `dating_profiles`, `dating_matches`, `dating_messages` (~20 דק')
- [ ] 🟢 **Matching algorithm** — overlap של תחומי עניין + מיקום + גיל (~45 דק')
- [ ] 🟢 **Ice-breaker questions** — שאלות עמוקות: "מה הפילוסופיה שלך בחיים?", "איזה ריטריט יוגה זכור לך?" (~30 דק')
- [ ] 🟢 **Privacy** — רק בתוך הבוט, חשיפה הדרגתית (~30 דק')
- [ ] 🟢 **Integration עם experts verification** — מחפש יוגיני → מוצא רק *מאומתים* (~20 דק')
- [ ] 🟢 **Deep-link מהאתר** — כפתור "הכרויות" ב‑profile.html → פותח הבוט (~15 דק')

**משימה מיידית:** אני יכול לבנות את ה‑skeleton של הבוט + DB + integration. דורש ~4 שעות רצופות של עבודה שלי.

---

## 🚪 Track 4 · No-Facebook Traffic (10%)

### Done
- [x] SEO בסיסי ב‑meta tags
- [x] daily-blog.html קיים

### Planned
- [ ] 🟢 **Blog redesign** — SEO-friendly, structured data, sitemap אוטומטי (~60 דק')
- [ ] 🟢 **Content calendar** — 10 פוסטים ראשונים:
  - "נוירולוגיה פוגשת מדיטציה"
  - "פילוסופיה מעשית של מנצח תזמורת"
  - "קריפטו + יוגה = חיים שלווים"
  - "אימות מומחיות אמיתית בעידן הרשתות"
  - + 6 עוד (AI יכתוב טיוטות, אתה מאשר)
- [ ] 🟢 **n8n automation setup** — בלוג → אוטומטי ל‑Instagram/LinkedIn/X/Telegram channel (~90 דק')
- [ ] 🟢 **Telegram public channel** @SLH_Community — תוכן יומי
- [ ] 🟢 **Meetup.com events** — ריטריטים וירטואליים בתחומים שלך (~30 דק' setup)
- [ ] 🟢 **Reddit auto-posting** — r/yoga, r/meditation, r/Israel, r/CryptoCurrency
- [ ] 🟢 **Google Business** — אם תרצה כתובת פיזית (כפר יונה?)

**משימה מיידית:** אני יכול לבנות את ה‑blog redesign + לכתוב 10 פוסטים ראשוניים. ~180 דק'.

---

## 🏘 Track 5 · Social Network of Israel (40%)

### Done
- [x] community.html — Feed + Marketplace
- [x] 13 posts published, 5 members, categories, likes, comments
- [x] post #14 published היום (system update)
- [x] trending categories + leaderboard
- [x] Multi-lang prepared (HE/EN/RU/AR/FR meta)

### Planned
- [ ] 🟢 **Personal profile redesign** (dashboard.html → profile.html) — SOCIAL profile:
  - תמונת רקע + avatar
  - ביו + "הסיפור שלי"
  - תחומי מומחיות + הוכחות
  - Feed אישי — רק פוסטים שלי
  - עוקבים / עוקבים אחרי
- [ ] 🟢 **"Follow" system** — עוקבים מקבלים התראות על פוסטים חדשים
- [ ] 🟢 **DM / private messaging** בתוך האתר
- [ ] 🟢 **Groups / Spaces** — "יוגה + מדיטציה", "פילוסופיה", "אקסטרים", "קריפטו + יזמים"
- [ ] 🟢 **Events system** — אירועים וירטואליים + פיזיים
- [ ] 🟢 **Rewards for content** — פוסט עם X לייקים → Y SLH (~30 דק')
- [ ] 🟢 **Zen mode** — עיצוב מינימליסטי עם טבע/מוזיקה ברקע
- [ ] 🟢 **Kosher Wallet ESP32 integration ב‑feed** — מי שיש לו מכשיר כשר רואה סימון מיוחד

---

## 🔴 מה עוד **עליך** לעשות (בסדר עדיפות)

### ⚡ עכשיו (דקות)
1. ✅ **TON_PAY_ADDRESS** — הוספת! (מחכה לדפלוי Railway)
2. ⏱ **SILENT_MODE=1** — 30 שניות ב‑Railway
3. ⏱ **BSCSCAN_API_KEY** — [etherscan.io/register](https://etherscan.io/register) → myapikey → Railway (2 דק')

### 🎯 היום (שעות)
4. **להחליט על 2 regressions** מ‑[REGRESSIONS_FLAG_20260417.md](https://github.com/osifeu-prog/slh-api/blob/master/ops/REGRESSIONS_FLAG_20260417.md)
5. **אישור לבנות dating bot** — "כן, תבנה את @G4meb0t_bot_bot" (אני דורש ~4 שעות)
6. **אישור לעדכן experts.html** — טופס הוכחה משופר + admin approval flow

### 🏗 השבוע (ימים)
7. **Stripe account + API key** (אם אתה רוצה לקבל כרטיסי אשראי גלובליים) — [stripe.com](https://stripe.com)
8. **Twilio account** — ל‑SMS אמיתי על `/api/device/register`
9. **Anthropic API key** (אם אתה רוצה לבנות @SLH_Claude_bot — תקשורת בטלגרם איתי)
10. **Meetup.com organizer account** — אירועים וירטואליים

### 🌱 החודש (שבועות)
11. **BotFather: הגדרת `/setcommands`** ל‑12 בוטים (15 דק' ידני)
12. **סיבוב 31 bot tokens** (חשוב לאבטחה)
13. **LinkedIn Premium** (אם אתה רוצה לחפש מומחים אוטומטית)

---

## 📊 איך אתה רואה את העדכונים ה‑LIVE

| כלי | מה רואים | URL |
|------|----------|-----|
| **Mission Control** | מצב חי של כל המערכת | [slh-nft.com/mission-control.html](https://slh-nft.com/mission-control.html) |
| **Agent Brief** | דף שיתוף לסוכני AI | [slh-nft.com/agent-brief.html](https://slh-nft.com/agent-brief.html) |
| **LIVE_ROADMAP.md** | **המסמך הזה** — מעודכן אחרי כל session | [GitHub](https://github.com/osifeu-prog/slh-api/blob/master/ops/LIVE_ROADMAP.md) |
| **Project Map** | כל 68 העמודים | [slh-nft.com/project-map.html](https://slh-nft.com/project-map.html) |
| **Ops Dashboard** | 171 endpoints + feature coverage | [slh-nft.com/ops-dashboard.html](https://slh-nft.com/ops-dashboard.html) |
| **Community Feed** | פוסטים יומיים | [slh-nft.com/community.html](https://slh-nft.com/community.html) |

---

## 🎯 הצעד הבא (תגיד לי באיזה כיוון)

**A.** תתחיל לבנות את **@G4meb0t_bot_bot** לפי המפרט למעלה (~4 שעות)
**B.** תעדכן את **experts.html** עם טופס הוכחות + admin approval (~2 שעות)
**C.** תבנה **PancakeSwap TX tracker** — Revenue (~1.5 שעות)
**D.** תתכנן את **blog redesign + 10 פוסטים ראשונים** (~3 שעות)
**E.** משהו אחר (תכתוב)

**או אם אתה רוצה שאני אעבוד רצוף בסדר מסוים → תן לי רצף** (למשל "C → B → A").

---

**🤖 Claude Code · ממשיך עד שתגיד עצור.**
