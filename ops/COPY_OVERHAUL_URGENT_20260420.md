# COPY OVERHAUL — Urgent Website Changes (Legal Shield)
**Date:** 2026-04-20
**Priority:** P0 — BLOCKER
**Estimated effort:** 2-4 hours
**Risk if delayed:** Active legal/regulatory exposure every hour the current copy is live

---

## Why this document exists

Current SLH website copy contains multiple patterns that:
1. Represent securities offerings under Israeli Securities Law + MiCA (EU)
2. Match classic Ponzi structure patterns (fixed APY + deep referral)
3. Create direct personal liability for Osif (no legal entity shield yet)

**This file lists every exact string that must change, its location, and the replacement.**

---

## The Four Changes (Severity Order)

### Change #1 — Remove Fixed APY Claims (P0, BLOCKING)

**Find these strings and remove/replace across ALL pages:**

| Before | After |
|---|---|
| `48% תשואה שנתית` | `חלוקת הכנסות לפי ביצועי המערכת — לא מובטח מראש` |
| `55% לנעילה חצי שנתית` | `Revenue Share Pool — פרו-רטה מהכנסות חודשיות` |
| `60% APY` | *(delete)* — replace with *"Dynamic Yield"* |
| `65% APY מובטח` | `APY משתנה לפי ביצועי המערכת. ראה /status לחלוקה האחרונה` |
| `תשואה מובטחת` | `חלוקת הכנסות מותנית` |
| `עד X% בשנה` | *(delete all claims of specific percentages)* |

**Files to search:**
- `D:\SLH_ECOSYSTEM\website\index.html`
- `D:\SLH_ECOSYSTEM\website\staking.html` (if exists)
- `D:\SLH_ECOSYSTEM\website\invest.html` (if exists)
- `D:\SLH_ECOSYSTEM\website\wallet.html`
- All bot welcome messages (search `.py` files in `*-bot/` dirs)
- `README.md`, `PROJECT_GUIDE.md` if public

**Grep commands to find remaining:**
```bash
cd D:\SLH_ECOSYSTEM\website
grep -rn "48%\|55%\|60%\|65%" --include="*.html"
grep -rn "APY" --include="*.html"
grep -rn "תשואה מובטחת" --include="*.html"
grep -rn "עד.*%" --include="*.html"
```

**Acceptance:** Zero hits for fixed APY percentages in user-facing pages.

---

### Change #2 — Reduce Referral Depth (P0)

**Find:**
- `10 דורות`
- `10 דרגות`
- `10 generations`
- `referral עמוק`
- `רשת הפניות עמוקה`

**Replace:**
- "תכנית שותפים 2 רמות — Tier 1 = 20%, Tier 2 = 5%"
- "Two-tier affiliate program"

**Files:**
- `D:\SLH_ECOSYSTEM\website\index.html`
- `D:\SLH_ECOSYSTEM\website\referrals.html` (if exists)
- `D:\SLH_ECOSYSTEM\website\invite.html` (if exists)
- Bot conversation scripts: search `*-bot/**/*.py` for "generation", "referral"

**Update backend logic:**
- Referral payout logic in API — cap at 2 levels
- ZVK reward computation — stop rewarding beyond Tier 2

**Acceptance:** Zero references to ≥3-level referral anywhere. Database enforcement in `/api/referral/*` endpoints.

---

### Change #3 — FOMO Marketing Removal (P1)

**Find and DELETE (not replace):**
- `פספסתם את הביטקוין`
- `פספסתם את הביטקויין`
- `מי שישן על האף לא ירוויח`
- `אלפי משקיעים כבר הצטרפו` (unless verifiable)
- `יש לכם כסף להשקיע?`
- `אל תפספסו`
- `הזדמנות של פעם בחיים`
- `ללא סיכון חסימה`
- `לא נחשבת ספאם בשום מקרה`

**Why:** Aggressive FOMO copy is a classic marker for regulatory scrutiny. Also poor fit with the Dynamic Yield ethos ("no promises").

**Replacement tone:**
- Pre-launch: *"SLH Spark — אקוסיסטם קריפטו בבנייה. הצטרף ללמוד איך זה עובד."*
- Main CTA: *"למד את המערכת לפני שאתה נוגע בה. הקורס הראשון חינם."* (links to Course #1 free modules)

**Files:** Grep across all HTML + bot message modules.

---

### Change #4 — Add Legal Disclaimers (P0)

**New required pages (create if missing):**

1. `D:\SLH_ECOSYSTEM\website\terms.html` — Terms of Service
2. `D:\SLH_ECOSYSTEM\website\privacy.html` — Privacy Policy
3. `D:\SLH_ECOSYSTEM\website\risk.html` — Risk Disclosure
4. `D:\SLH_ECOSYSTEM\website\legal.html` — Legal entity info (when entity exists)

**Footer disclaimer to add on every page (insert in footer partial or shared.js):**

```html
<div class="legal-disclaimer">
  SLH Spark היא אקוסיסטם קריפטו בשלבים מוקדמים. Dynamic Yield הוא מנגנון חלוקת הכנסות,
  לא מוצר פיננסי מובטח. חלוקות עבר לא מבטיחות חלוקות עתיד. אין זה ייעוץ השקעות.
  <a href="/risk.html">גילוי סיכון מלא</a>
</div>
```

**Header banner (above-the-fold on `/`, `/wallet`, `/status`):**

```html
<div class="pre-launch-banner">
  <strong>Pre-Launch Beta</strong> · System in active development · See <a href="/status.html">live status</a> for current health
</div>
```

---

## Priority / Staging Plan

### Within 4 hours (today):
- [x] ~~Create Dynamic Yield spec~~ (done — `DYNAMIC_YIELD_SPEC_20260420.md`)
- [x] ~~Build Course #1 as alternative revenue~~ (done — `/academy/course-1-dynamic-yield.html`)
- [ ] **Change #1 — Remove all fixed APY from HTML pages** (this is the "stop the bleeding" step)
- [ ] **Change #4a — Add footer disclaimer via `shared.js`** (applies to all 43 pages in one edit)

### Within 48 hours:
- [ ] Change #2 — Referral depth reduction (UI + API)
- [ ] Change #3 — FOMO copy removal
- [ ] Create minimal `terms.html`, `privacy.html`, `risk.html` (use templates below)

### Within 7 days:
- [ ] Register legal entity (עוסק מורשה → חברה בע"מ)
- [ ] Rotate remaining 30 exposed bot tokens
- [ ] Fix empty JWT_SECRET on Railway
- [ ] Build live `/status.html` with Coverage Ratio widget

### Within 30 days:
- [ ] Commission external smart contract audit
- [ ] Setup multi-sig Treasury (BSC + TON)
- [ ] Publish first Treasury transparency report

---

## Minimal Legal Page Templates

### `terms.html` (skeleton — expand per lawyer review)

```markdown
# תנאי שימוש — SLH Spark

**תאריך כניסה לתוקף:** 2026-04-20
**גרסה:** 0.1 (pre-launch)

## 1. מה זה SLH Spark
SLH Spark הוא אקוסיסטם קריפטו בשלבי בנייה, המספק:
- כלים חינוכיים (Academia)
- שירותי SaaS מבוססי-בוט
- שוק לתוכן דיגיטלי (Marketplace)
- מנגנון Revenue Share Pool לבעלי טוקן SLH

## 2. מה זה לא
SLH Spark אינו:
- בנק
- בית השקעות (לפי הגדרת חוק ניירות ערך, התשכ"ח-1968)
- מציע ניירות ערך לציבור
- ערב לתשואה כלשהי

## 3. הסיכונים שלך
- **שוק:** ערך הטוקן יכול לרדת עד 0.
- **נזילות:** ייתכנו תקופות שבהן לא ניתן למשוך או להמיר טוקנים.
- **טכני:** באגים, פריצות, אובדן מפתחות.
- **רגולציה:** המצב הרגולטורי עשוי להשתנות.
- **פרויקט:** SLH Spark נבנה על-ידי דב יחיד בשלב זה. סיכון bus-factor גבוה.

## 4. Dynamic Yield
השתתפות ב-Revenue Share Pool מותנית בביצועי המערכת. כל חלוקה נגזרת מהכנסות אמיתיות
(Fees, Course sales, SaaS). אין הבטחה למספר, תדירות, או המשכיות.

Circuit Breakers אוטומטיים יכולים לעצור חלוקות, להגביל משיכות, או להקפיא הפקדות
לצורך הגנה על המערכת. ראה `/risk.html`.

## 5. אחריות
השימוש בפלטפורמה הוא על אחריותך בלבד. SLH Spark ובעליה אינם אחראים לאובדן כלשהו הנובע
משימוש בפלטפורמה, למעט מקרים של רשלנות גסה שהוכחה משפטית.

## 6. פיקוח משפטי
...
```

### `risk.html` (skeleton)

```markdown
# גילוי סיכון

## סיכוני קריפטו כלליים
- תנודתיות מחיר קיצונית
- סיכון רגולטורי משתנה
- אפשרות של פריצה או ניצול חוזה חכם
- אובדן מפתחות פרטיים = אובדן סופי

## סיכונים ספציפיים ל-SLH
1. **ריכוז Supply:** המייסד מחזיק כ-98% מ-supply SLH. שחרור עתידי עלול להשפיע על מחיר.
2. **Liquidity נמוכה ב-PancakeSwap:** pool נוכחי דק מאוד. משיכות גדולות יגרמו ל-slippage מהותי.
3. **פרויקט בבנייה:** רכיבי המערכת לא הושלמו במלואם. ראה `/status.html` לפערים ידועים.
4. **Bus factor:** הפרויקט מפותח על-ידי אדם אחד. מחלה/תאונה יכולים להשפיע על המשכיות.
5. **ללא audit:** קוד החוזה החכם לא עבר audit מקצועי חיצוני. מתוכנן Q3 2026.

## מה לעשות לפני השתתפות
1. קרא את `/terms.html`
2. סיים את מודול 1 (חינם) של Course #1 — Ponzi Detection Framework
3. הפקד סכום שאתה יכול להפסיד ב-100%
4. שמור מפתחות פרטיים במקום מאובטח
5. הגדר התרעות על /status.html

## אירועי חובת דיווח
אנחנו נדווח בקרב:
- Circuit Breaker פעיל > 48h
- Coverage Ratio מתחת ל-1.0
- שינוי בפרמטר k
- אירוע אבטחה כלשהו

דיווחים ב-/status, Twitter/X @slh_spark, וערוץ Telegram.
```

---

## Execution Checklist

### Editor pass 1 — HTML files
```bash
cd D:\SLH_ECOSYSTEM\website

# Find all APY mentions
grep -rn "APY\|תשואה מובטחת\|מובטח\|65%\|60%\|55%\|48%" --include="*.html" > /tmp/apy_hits.txt

# Review each hit — edit in IDE, don't sed blindly (context matters)
# After each file: git diff to verify changes
```

### Editor pass 2 — Bot scripts
```bash
cd D:\SLH_ECOSYSTEM
grep -rn "APY\|תשואה\|65%\|10 דורות" --include="*.py" > /tmp/bot_hits.txt
# Edit welcome messages, inline keyboards, etc.
```

### Deploy sequence
1. Commit changes to `website/` repo (GitHub Pages auto-deploys)
2. Commit API referral cap changes to root repo → Railway auto-deploys
3. Restart bots with updated messages
4. Post to @SLH_community_channel: *"Site updated — Dynamic Yield model now live. Course #1 released. Fixed APY claims removed. See /risk.html for full disclosure."*

### Smoke test
After deploy:
- [ ] Load `/` — no APY promises visible
- [ ] Load `/status.html` — shows Pre-Launch Banner
- [ ] Footer disclaimer present on all pages (spot-check 5)
- [ ] Course #1 landing loads correctly
- [ ] `/terms.html`, `/risk.html` load (even if minimal)
- [ ] Bot /start message doesn't promise fixed APY

---

## What to tell existing users

**Telegram broadcast (Hebrew):**

> 🔄 **עדכון חשוב — SLH Spark**
>
> האתר עודכן. המודל הכלכלי הוכרז באופן פומבי: Dynamic Yield Revenue Share במקום APY קבוע.
>
> למה? הקורס הראשון שלנו (Dynamic Yield Economics — עכשיו חינם למודולים 1-2) מסביר את הסיבה המלאה, אבל בקיצור: הבטחת APY קבוע בלי הוכחת Revenue = Ponzi structure. אנחנו לא רוצים להיות שם. גם לא בטעות.
>
> מה זה אומר עבורך:
> ✅ כל מה שיש לך — נשאר. ההפקדות שלך בטוחות.
> ✅ חלוקות המשך תהיינה לפי הכנסות אמיתיות (הקורס, Marketplace, Subscriptions).
> ✅ שקיפות מלאה ב-/status (בבנייה — יהיה חי תוך שבוע).
>
> 📚 [הקורס הראשון — חינם לכולם](https://slh-nft.com/academy/course-1-dynamic-yield.html)
> 📊 [/status](https://slh-nft.com/status.html)

**Instructions:**
1. Post to main channel
2. Pin for 14 days
3. Individual DM to top 10 holders with personal note + offer 1:1 call

---

## Success Metrics

Post-overhaul, validate:
- Zero fixed-APY strings in grep scan
- Course #1 landing page traffic (Google Analytics goal: 200+ views week 1)
- Course #1 Free tier signups (goal: 50+ week 1)
- Course #1 Pro purchases (goal: 5+ week 1 = first R_t for Dynamic Yield pool)
- Zero new complaints about "where is my 65%" (they've been warned)
- Legal advisor review scheduled within 14 days

---

## Escalation

If any of these blocks copy overhaul:
- **Technical blocker:** DM @osifeu_prog (solo dev, same person)
- **Design/copy blocker:** Use minimal text — perfection later
- **Legal blocker:** Proceed with safer version; iterate with lawyer within 30 days
- **Emotional blocker (hardest):** Remember — the old copy is legally dangerous NOW. Dynamic Yield is safer AND more honest. This is the upgrade, not a downgrade.

---

*Document owner: Osif*
*Approved for execution: 2026-04-20*
