# 🤝 Broker Onboarding — Tzvika + Elazar

**Date:** April 15, 2026 (יום רביעי, כ"ח בניסן תשפ"ו)
**Status:** System deployed · Ready for first real deposits

---

## 🎯 What's Built

### 1. Broker Accounts System
- `broker_accounts` DB table — Tzvika, Elazar, future brokers
- Each broker has:
  - Unique `user_id` (Telegram)
  - Limited permissions (view own only by default)
  - Commission percentage
  - `owner_visible_to` — who can see them (Osif = 224223270, Tzvika = 7757102350)

### 2. Investment Deposits with Compound Interest
- `deposits` table
- Monthly rate (e.g. 4.0%) + term (e.g. 2 months)
- Compounding: monthly / daily / simple
- Live calculation API: `GET /api/deposits/{id}/status`
- Returns: principal, interest_accrued, current_value, months_elapsed

### 3. ESP Preorders with Auto 2 SLH Gift
- `esp_preorders` table
- `POST /api/esp/preorder` — anyone can place order
- `POST /api/esp/preorder/{id}/approve` — admin approves → auto 2 SLH from Tzvika (user 7757102350)

### 4. Credit Card Payments
- `credit_card_payments` table
- `POST /api/payment/credit-card/submit`
- Only stores last 4 digits of card + CVV flag (NOT full card)
- Status: pending → approved by manual admin review (until provider integration)

### 5. Expenses Tracking
- `expenses` table
- `POST /api/expenses/add` (admin only)
- Scope: `company` / `personal` / `claude`
- VAT tracking + tax deductible flag

### 6. Pages Live
- `/broker-dashboard.html` — per-broker view
- `/investment-tracker.html` — client view of their deposits
- `/card-payment.html` — credit card form
- `/expenses.html` — expense management

---

## 🚀 Step-by-Step: Onboard Tzvika & Elazar

### Step 1 — Create Tzvika's broker account (Osif does this)

```bash
curl -X POST "https://slh-api-production.up.railway.app/api/brokers/create" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: slh2026admin" \
  --data-binary @- <<'JSON'
{
  "user_id": 7757102350,
  "display_name": "Tzvika Kaufman",
  "tg_username": "Osif83",
  "role": "senior_broker",
  "commission_pct": 15.0,
  "permissions": ["view_own_referrals","view_own_deposits","view_own_commissions","view_esp_preorders","approve_esp","view_other_brokers"],
  "visible_to": [224223270, 7757102350],
  "notes": "Co-founder + ESP SLH gifter (sends 2 SLH per preorder)"
}
JSON
```

### Step 2 — Create Elazar's broker account

```bash
curl -X POST "https://slh-api-production.up.railway.app/api/brokers/create" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: slh2026admin" \
  --data-binary @- <<'JSON'
{
  "user_id": 0,
  "display_name": "Elazar Bloy",
  "role": "broker",
  "commission_pct": 10.0,
  "permissions": ["view_own_referrals","view_own_deposits","view_own_commissions"],
  "visible_to": [224223270, 7757102350],
  "notes": "Financial broker · Haredi market · First deposit test week of April 15"
}
JSON
```

Remember to update Elazar's user_id once he connects to @Grdian_bot with `/whoami`.

### Step 3 — Elazar's $1 test deposit (7-day trial)

```bash
# After Elazar sends $1 and Tzvika gifts 0.00225 SLH (=$1 worth at $444 internal rate)
curl -X POST "https://slh-api-production.up.railway.app/api/deposits/create" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: slh2026admin" \
  --data-binary @- <<'JSON'
{
  "user_id": <ELAZAR_USER_ID>,
  "broker_id": <ELAZAR_BROKER_ID>,
  "amount_usd": 1.0,
  "monthly_rate_pct": 4.0,
  "term_months": 0.23,
  "compounding": "daily",
  "slh_received": 0.00225,
  "is_test": true,
  "notes": "7-day test deposit — demonstrate compound interest before $999 main deposit"
}
JSON
```

### Step 4 — After 7 days, Elazar's main deposit ($999 + $1 = $1,000 for 2 months)

```bash
curl -X POST "https://slh-api-production.up.railway.app/api/deposits/create" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: slh2026admin" \
  --data-binary @- <<'JSON'
{
  "user_id": <ELAZAR_USER_ID>,
  "broker_id": <ELAZAR_BROKER_ID>,
  "amount_usd": 1000.0,
  "monthly_rate_pct": 4.0,
  "term_months": 2.0,
  "compounding": "monthly",
  "slh_received": 2.252,
  "is_test": false,
  "notes": "Main deposit · 2 months · 4% monthly compound"
}
JSON
```

Expected final value after 2 months compound monthly at 4%:
`1000 × (1.04)^2 = $1,081.60`
Interest: `$81.60` = **8.16% over 2 months**

### Step 5 — Elazar redeems — must return same SLH amount he received

When Elazar withdraws:
1. He returns 2.252 SLH to Tzvika's wallet
2. System transfers him the current value in USD
3. Deposit marked `withdrawn`

---

## 📱 Elazar's Personal Tracker

Once registered, Elazar visits:
`https://slh-nft.com/investment-tracker.html?uid=<HIS_USER_ID>`

He'll see live:
- Current value (with compound interest)
- Days elapsed
- Progress bar (% of term)
- Reminder: "7 days passed — ready for main deposit?"
- Direct link to @Grdian_bot

---

## 🎁 ESP Preorder Flow (2 SLH gift from Tzvika)

```
Buyer → /card-payment.html?product=kosher_wallet&ref=Elazar&broker=2
  ↓
POST /api/payment/credit-card/submit
  ↓
Admin reviews (Osif or Tzvika)
  ↓
POST /api/esp/preorder/{id}/approve
  ↓
AUTO: 2 SLH transferred from user 7757102350 (Tzvika) → buyer
  ↓
token_transfers log + token_balances updated
```

---

## 🔐 Permission Levels

| Permission | Osif | Tzvika | Elazar |
|-----------|------|--------|--------|
| View all brokers | ✅ | ✅ | ❌ |
| View own referrals | ✅ | ✅ | ✅ |
| View own deposits | ✅ | ✅ | ✅ |
| Approve ESP orders | ✅ | ✅ | ❌ |
| Create new broker | ✅ | ❌ | ❌ |
| View expenses | ✅ | ❌ | ❌ |
| View all payments | ✅ | ✅ (commissions) | ❌ |

---

## 💰 Company Bank Account (Reminder)

```
מוטב:   קאופמן צביקה
בנק:    לאומי
סניף:   הרצליה (948)
חשבון:  738009
```

---

## 🧪 Test Checklist for Elazar's $1 test

- [ ] Elazar sends $1 (via BNB 0.00036 / TON 0.73 / bank 3.03 ILS)
- [ ] Osif/Tzvika confirm receipt
- [ ] Tzvika sends 0.00225 SLH gift
- [ ] Create deposit in system (`is_test=true`, 7 days)
- [ ] Elazar gets link to investment-tracker
- [ ] After 7 days: remind Elazar (automated, via Guardian)
- [ ] Elazar decides to do main deposit ($999)
- [ ] Create new deposit ($1000 total, 2 months)
- [ ] Monthly check-ins automated
- [ ] End: Elazar returns 2.252 SLH, gets $1,081.60

**Expected interest after 2 weeks (test + 1st week of main):**
- $1,000 × 1.04^(0.5) ≈ $1,019.80 → +$19.80 earned in 2 weeks

---

## 📞 For Elazar — Exact Messages to Send via Guardian

Use `/say <ELAZAR_USER_ID> <message>`:

**Message 1 (after $1 arrives):**
```
/say <UID> קיבלנו את $1 שלך! תודה על האמון. הגדרנו לך פקדון בדיקה ל-7 ימים ב-4% חודשי. תוכל לעקוב בזמן אמת בקישור: https://slh-nft.com/investment-tracker.html?uid=<UID>
```

**Message 2 (after 7 days):**
```
/say <UID> עברו 7 ימים! הפקדון הבדיקה שלך מראה כבר רווח. עכשיו אם תרצה — תפקיד $999 נוספים להתחלת הפקדון המלא לחודשיים. אעדכן אותך ברגע שהכסף יגיע.
```

**Message 3 (on main deposit):**
```
/say <UID> מזל טוב! הפקדון הראשי שלך פעיל. $1,000 · 4% חודשי · חודשיים. ערך צפוי: $1,081.60. תוכל לעקוב כל יום.
```
