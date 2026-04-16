# SLH API - Complete Endpoint Testing Guide
> Base URL: https://slh-api-production.up.railway.app
> PowerShell note: use `curl.exe` not `curl` (which is alias for Invoke-WebRequest)

## Quick Health Check
```powershell
curl.exe -s https://slh-api-production.up.railway.app/api/health
# Expected: {"status":"ok","db":"connected","version":"1.0.0"}
```

---

## 1. AUTH & USERS

### Login (via Telegram Widget - automatic)
```
POST /api/auth/telegram
Body: {id, first_name, auth_date, hash}
Returns: {success, user: {is_registered, ...}, token: "JWT...", balances: {...}}
```

### Get User Profile
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/user/224223270"
# Returns: {user: {...}, balances: {TON_available, SLH, ZVK, ...}, premium: bool}
```

---

## 2. REGISTRATION (NEW - requires JWT)

### Check Registration Status
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/registration/status/224223270"
# Expected: {"is_registered": true, "payment_status": "approved"}
```

### Initiate Registration
```powershell
curl.exe -X POST "https://slh-api-production.up.railway.app/api/registration/initiate" -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_JWT" -d "{\"referrer_id\": null}"
# Returns: {status: "pending", price_ils: 44.4, ton_wallet: "UQCr743g...", ...}
```

### Submit Payment Proof
```powershell
curl.exe -X POST "https://slh-api-production.up.railway.app/api/registration/submit-proof" -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_JWT" -d "{\"tx_hash\": \"your_tx_hash_here\"}"
# Returns: {status: "submitted"}
```

### List Pending Registrations (Admin)
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/registration/pending?admin_key=osif_slh_admin_2024"
# Returns: [{user_id, payment_status, ...}, ...]
```

### Approve Registration (Admin)
```powershell
curl.exe -X POST "https://slh-api-production.up.railway.app/api/registration/approve" -H "Content-Type: application/json" -d "{\"admin_key\": \"osif_slh_admin_2024\", \"user_id\": 123456}"
# Returns: {success: true, slh_credited: 0.1}
# Side effects: credits 0.1 SLH, sets is_registered=true, distributes referral commissions
```

---

## 3. WALLET & TOKENS

### Get Balances
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/wallet/224223270/balances" -H "Authorization: Bearer YOUR_JWT"
```

### Get Wallet Info
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/wallet/224223270"
```

### Transfer Tokens
```powershell
curl.exe -X POST "https://slh-api-production.up.railway.app/api/transfer" -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_JWT" -d "{\"to_user_id\": 999, \"amount\": 0.5, \"token\": \"SLH\"}"
```

### Wallet Price
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/wallet/price"
```

---

## 4. STAKING

### List Plans
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/staking/plans"
```

### Create Stake
```powershell
curl.exe -X POST "https://slh-api-production.up.railway.app/api/staking/stake" -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_JWT" -d "{\"plan_key\": \"basic_30\", \"amount\": 1.0, \"token\": \"TON\"}"
```

### My Positions
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/staking/positions/224223270"
```

---

## 5. REFERRALS

### My Referral Link
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/referral/link/224223270"
```

### My Stats
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/referral/stats/224223270"
```

### My Tree
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/referral/tree/224223270"
```

### Leaderboard
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/referral/leaderboard"
```

---

## 6. COMMUNITY

### List Posts
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/community/posts"
```

### Create Post (registered users only)
```powershell
curl.exe -X POST "https://slh-api-production.up.railway.app/api/community/posts" -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_JWT" -d "{\"content\": \"Hello SLH!\", \"category\": \"general\"}"
```

### Like Post
```powershell
curl.exe -X POST "https://slh-api-production.up.railway.app/api/community/posts/1/like" -H "Authorization: Bearer YOUR_JWT"
```

### Community Stats
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/community/stats"
```

---

## 7. ADMIN

### Dashboard
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/admin/dashboard?admin_key=osif_slh_admin_2024"
```

### Activity Log
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/admin/activity?admin_key=osif_slh_admin_2024"
```

### Site Stats (public)
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/stats"
```

### Analytics
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/analytics/stats?admin_key=osif_slh_admin_2024"
```

---

## 8. AI CHAT

### Send Message
```powershell
curl.exe -X POST "https://slh-api-production.up.railway.app/api/ai/chat" -H "Content-Type: application/json" -d "{\"message\": \"What is SLH?\", \"user_id\": 224223270}"
```

### List Providers
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/ai/providers"
```

---

## 9. PRICES & DATA

### Live Prices
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/prices"
```

### User Activity
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/activity/224223270"
```

### User Transactions
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/transactions/224223270"
```

### XP Leaderboard
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/leaderboard"
```

---

## Full Test Flow (Step by Step)

1. **Health**: GET /api/health -> ok
2. **Stats**: GET /api/stats -> total users, volume
3. **Prices**: GET /api/prices -> BTC, ETH, TON, SLH prices
4. **Login**: POST /api/auth/telegram -> save JWT token
5. **Profile**: GET /api/user/YOUR_ID -> balances, level, XP
6. **Reg Status**: GET /api/registration/status/YOUR_ID
7. **Community**: GET /api/community/posts -> forum posts
8. **Referral**: GET /api/referral/stats/YOUR_ID
9. **Staking**: GET /api/staking/plans -> available plans
10. **AI Chat**: POST /api/ai/chat -> test AI response
