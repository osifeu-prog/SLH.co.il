# Test Payment Flow · How-to
**Purpose:** End-to-end verification of SLH payment system without needing a real customer. Use for: proving the flow works, smoke-testing after deploys, demoing to prospects.

**Cost:** ₪0.06 (six agorot) per test. Uses real mainnet (not testnet) — so produces real payment records, real receipts, real Premium grants.

---

## 🎯 The page

`https://slh-nft.com/pay-test.html`

One-page, one-button. No distractions. Pre-fills `uid` if passed as query param:

```
https://slh-nft.com/pay-test.html?uid=224223270
```

---

## 🧪 Scenario A · Osif tests himself (recommended first)

Fastest sanity check. You send money from your own wallet to yourself.

### Step 1 · Setup
- MetaMask or Trust Wallet installed with **BSC network** + 0.01 BNB (for gas + 0.0005 payment)
- OR Tonkeeper/wallet with **0.02 TON** (for gas + 0.01 payment)
- Your own Telegram ID: `224223270`

### Step 2 · Run
1. Open `https://slh-nft.com/pay-test.html?uid=224223270` on phone (easier for TON wallet).
2. Click **"שלם 0.0005 BNB עם MetaMask"** (or TON variant).
3. Wallet opens with amount pre-filled — confirm.
4. Back on page — status changes to "⏳ מאמת" → within 30s to "✅ אומת!"
5. Receipt number appears.

### Step 3 · Verify in 4 places
```powershell
# 1. User now has Premium:
curl.exe https://slh-api-production.up.railway.app/api/user/224223270

# 2. Payment record in DB:
curl.exe -H "X-Broadcast-Key: slh-broadcast-2026-change-me" `
  https://slh-api-production.up.railway.app/api/ops/reality | `
  python -c "import sys,json; d=json.load(sys.stdin); print('payments:', d.get('payments'))"

# 3. Analytics event:
# https://slh-nft.com/admin/funnel-dashboard.html — see `pay_test_verified`

# 4. On-chain:
# BSC: https://bscscan.com/tx/<tx_hash>
# TON: https://tonviewer.com/transaction/<tx_hash>
```

Expected on success:
- User object has `is_premium: true` or similar flag
- Payment record with status `verified`/`confirmed`
- Analytics event logged
- On-chain transaction confirmed

---

## 🧪 Scenario B · Sending to a trusted customer

Send the test link to someone you trust (a friend, early adopter). Verifies the flow from their environment.

### Before sending
- Confirm they have MetaMask OR Tonkeeper with ≥ ₪0.20 in BNB/TON
- Confirm they know their Telegram ID (or have @userinfobot easy access)
- Prepare to cover their "loss" — it's your test, not theirs

### Message template
```
היי [שם],

מבקש ממך עזרה קטנטנה (30 שניות).
רוצה לבדוק את מערכת התשלומים שלנו לפני שנפתח ללקוחות אמיתיים.

הקישור הזה יבקש ממך להעביר **0.01 TON** (זה שש אגורות, 
כאילו לא קיים) — המערכת שלנו מאמתת את זה תוך 30 שניות 
ומפיקה קבלה.

🔗 https://slh-nft.com/pay-test.html?uid=[TG_ID]&src=friend&campaign=smoketest-1

מבטיח שאפצה אותך על ה-0.06 ₪ 😅
אם נוח לך — חזור אליי עם תוצאה (עובד / לא עובד / מתקע איפשהו).

תודה!
```

Their payment flows through → your end-to-end is verified.

---

## 🧪 Scenario C · "Demo during Zoom"

If you're on a sales call and want to show the system works — this is the right moment.

1. Share screen.
2. Go to `https://slh-nft.com/pay-test.html?uid=<your_tg_id>&src=zoom`
3. Click button live on camera.
4. Show them the wallet popup, confirm the tiny amount.
5. Show them the verification happens live (30s).
6. "That's exactly what your customers will see — just with a real amount."

**This is the strongest proof you can offer a prospect.**

---

## ⚠️ If something fails

### Symptom: "Verification failed" after wallet confirm
**Cause:** `/api/payment/{ton|bsc}/auto-verify` couldn't find the tx within 30s.
**Fix:**
1. Click "אמת שוב" or refresh and paste tx hash manually.
2. Wait 60 more seconds (blockchain sometimes slow to propagate).
3. Check `curl.exe -s https://slh-api-production.up.railway.app/api/health` — if `status:"degraded"`, something's wrong server-side.
4. Check Railway Dashboard → Logs for errors.

### Symptom: MetaMask opens but wrong network
**Fix:** The code auto-switches to BSC (chainId `0x38`). If user declines the switch prompt → they need to approve before clicking the button again.

### Symptom: TON deeplink doesn't open
**Cause:** Tonkeeper/wallet app not installed, or browser blocked custom protocol.
**Fix:** On desktop → use MetaMask-BNB variant instead. On mobile → ensure Tonkeeper installed and default for `ton://` URLs.

### Symptom: "user_id invalid" after clicking
**Cause:** `uid` field empty or malformed.
**Fix:** Ensure `?uid=<numeric>` in URL OR user types their Telegram ID (9-10 digits) manually.

---

## 📊 Metrics to track

After 5 test payments land, you'll have:
- 5 real payment records (proof to investors/partners)
- 5 receipts (proof for bookkeeping)
- 5 Premium-granted users (proof flow completes)
- Full analytics trail (`pay_test_view` → `pay_test_click_{bnb,ton}` → `pay_test_verified`)

Dashboard: `https://slh-nft.com/admin/funnel-dashboard.html`

---

## 🚦 When you're ready to scale up

Once test flow works reliably (3-5 successful tests):
1. Update `pay.html` to remove "test" as a visible option (or keep for QA).
2. Use `pay-creator-package.html` with real ₪22,221 for Yaara-class customers.
3. For retail at ₪49 (Premium) / ₪179 (Course Pro) / ₪549 (Course VIP) — reuse `pay.html` with those product pre-selected.
4. Monitor `/api/payments` daily via `daily_digest.py`.

---

## 🧬 Testnet (future)

To test WITHOUT real money — requires adding testnet toggle to `pay.html` + config. Not implemented as of 2026-04-25. Path:

1. Add env: `PAYMENT_TESTNET_MODE=true` on Railway.
2. `/api/payment/config` returns `is_testnet: true` + testnet addresses.
3. Pay page uses BSC Chapel (chainId `0x61`) + TON testnet.
4. Faucets for tokens: https://testnet.binance.org/faucet-smart · https://t.me/testgiver_ton_bot

Estimated effort: 2-3 hours of focused work. Deferrable until post-customer-5.

---

Last updated: 2026-04-25. When scenarios above pass 5x successfully, delete this file's "If something fails" section (it means the failures no longer happen).
