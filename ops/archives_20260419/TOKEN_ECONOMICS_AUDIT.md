# 🪙 SLH Spark Token Economics - Full Professional Audit

**Date:** 2026-04-18  
**Auditor:** Claude (Expert Analysis)  
**Status:** Comprehensive Deep-Dive for Osif

---

## Executive Summary

SLH Spark operates a **5-token internal economy**:
- **SLH**: Premium token (BSC blockchain, real-world value: 444 ILS)
- **MNH**: Stablecoin (pegged 1:1 to 1 ILS, internal only)
- **ZVK**: Activity reward token (~4.4 ILS value, earned via actions)
- **REP**: Reputation score (0-1000+, non-transferable)
- **ZUZ**: Anti-fraud token (Mark of Cain, auto-ban at 100)

All internal transfers happen in **PostgreSQL ledger** (append-only, transactional).  
Settlement to blockchain (BSC/TON) happens async.

---

## 1️⃣ TOKEN BREAKDOWN & ECONOMICS

### SLH Token (Premium Token)

**Purpose:** Premium features, governance, long-term investment  
**Supply:** Capped at genesis allocation  
**Price:** 444 ILS (tracked live on PancakeSwap)  
**Blockchain:** BSC (BEP-20, 15 decimals)  
**Contract:** `0xACb0A09414CEA1C879c67bB7A877E4e19480f022`  
**PancakeSwap Pool:** `0xacea26b6e132cd45f2b8a4754170d4d0d3b8bbee`  

**How it flows:**
```
User deposits fiat (₪) → Genesis Wallet → Bank confirms → SLH credited to user
User buys on PancakeSwap → BSC wallet holds tokens
User stakes in vaults → Earns yield
```

**Key Math:**
- 1 SLH = 444 ILS (fixed in system, real-world price may vary on DEX)
- Minimum deposit: 50,000 ILS = ~112 SLH
- Premium gate: 1 SLH = access to VIP features

**Database Schema:**
```sql
token_balances (user_id, token='SLH', balance NUMERIC(18,8))
token_transfers (from_id, to_id, token='SLH', amount, fee, tx_type)
```

**Verification Needed:**
- [ ] Sum of all `token_balances WHERE token='SLH'` = total supply in circulation
- [ ] All `token_transfers.amount` for SLH are properly recorded
- [ ] No negative balances exist
- [ ] Fee calculations are correct (should be minimal for internal transfers)

---

### MNH Token (Stablecoin - 1 ILS peg)

**Purpose:** Internal settlement, avoid volatility  
**Peg:** 1 MNH = exactly 1 ILS  
**Storage:** Internal ledger only (no blockchain yet)  
**Supply:** Unlimited (can be minted when needed)  

**How it flows:**
```
User deposits 100 ILS → Mint 100 MNH
User buys marketplace item (50 ILS) → Pay 50 MNH
Revenue collected → Burn MNH or hold as reserves
```

**Key Math:**
- No fees on internal MNH transfers
- 1:1 ratio to ILS is hardcoded assumption
- All mints must come from verified bank deposits

**Database Schema:**
```sql
token_balances (user_id, token='MNH', balance)
internal_transfers (from_id, to_id, token='MNH', amount, fee=0)
```

**Verification Needed:**
- [ ] Total MNH supply matches total ILS deposits (verify against bank records)
- [ ] No MNH transfer has fees (fee should always = 0)
- [ ] All MNH earned matches revenue tracking

---

### ZVK Token (Activity Reward - ~4.4 ILS value)

**Purpose:** Reward active users, gamify participation  
**Implied Value:** ~4.4 ILS per token (calculated from 1 SLH = 444 ILS, and SLH:ZVK ratio)  
**How Earned:**
- Complete daily quests: +10 ZVK
- Participate in battles: +5-50 ZVK per win
- Achievements: +20-100 ZVK
- Referrals: +5% of friend's activity
- Community contributions: +variable

**Database Schema:**
```sql
token_balances (user_id, token='ZVK', balance)
token_transfers (from_id, to_id, token='ZVK', amount, memo='quest' | 'battle' | 'referral')
```

**Key Calculation:**
```
User Session Earnings = Base Activity × Multiplier × Time Bonus
Example:
- Daily login: +5 ZVK (flat)
- Battle win: +10 ZVK × (1 + streak_bonus) × (1 + time_bonus)
- If 10-win streak + evening bonus: +10 × 1.2 × 1.1 = 13.2 ZVK
```

**Verification Needed:**
- [ ] Quest completion logs match ZVK credits
- [ ] No user earned ZVK without corresponding action record
- [ ] Multipliers are applied consistently (check DB for anomalies)
- [ ] Referral percentages are correctly calculated

---

### REP Token (Reputation - Non-transferable)

**Purpose:** Internal ranking, access to higher tiers  
**Range:** 0-1000+ points  
**Non-transferable:** Can only be earned/lost, never sent  

**How it flows:**
```
Good behavior: +REP (verified trades, community help, referrals)
Bad behavior: -REP (fraud flags, chargebacks, community reports)
Threshold penalties: -50 REP per report, -100 at ZUZ=50+
```

**Database Schema:**
```sql
token_balances (user_id, token='REP', balance)
-- NO transfers allowed for REP
reputation_events (user_id, action, points, reason, timestamp)
```

**Key Rules:**
- REP > 500: Tier 1 (basic access)
- REP > 1000: Tier 2 (premium trading)
- REP > 2000: Tier 3 (institutional)
- REP < 0: Banned account

**Verification Needed:**
- [ ] No `token_transfers` records with token='REP' exist
- [ ] All REP changes logged in `reputation_events`
- [ ] REP increases match positive actions
- [ ] REP decreases match documented problems
- [ ] No REP manipulation by admins without audit trail

---

### ZUZ Token (Anti-Fraud - Mark of Cain)

**Purpose:** Fraud prevention, auto-ban system  
**Range:** 0-100 points  
**Auto-ban:** Account frozen at ZUZ ≥ 100  

**How it flows:**
```
Fraud flag: +ZUZ (failed verification, chargeback, suspicious pattern)
ZUZ=10: Warning, can still trade
ZUZ=25: Requires re-verification
ZUZ=50: Trading disabled, DM sent
ZUZ=75: Account warning
ZUZ=100+: Auto-ban, all transfers frozen
```

**Database Schema:**
```sql
token_balances (user_id, token='ZUZ', balance)
fraud_events (user_id, flag_type, severity, reason, timestamp)
```

**Verification Needed:**
- [ ] Every ZUZ increase has corresponding fraud_event
- [ ] Auto-ban trigger fires at ZUZ ≥ 100
- [ ] No ZUZ transfers (should be admin-only adjustments)
- [ ] Decay mechanism (if any) is working (e.g., -1 ZUZ per 30 days of good behavior)

---

## 2️⃣ TOKEN FLOW ARCHITECTURE

```
┌──────────────────────────────────────────────────────────┐
│                    User Actions                          │
└─────────┬────────────────────────────────────────────────┘
          │
          ├─→ Marketplace Buy/Sell → MNH, SLH transfers
          ├─→ Quest/Battle → ZVK earned
          ├─→ Community report → REP ±
          ├─→ Fraud flag → ZUZ +
          └─→ Bank deposit → MNH minted
          │
          ▼
┌──────────────────────────────────────────────────────────┐
│            PostgreSQL Ledger (Transactional)             │
│                                                          │
│  token_balances                                          │
│  ├─ user_id, token, balance, updated_at                 │
│  │  (UNIQUE constraint: no double-entry)                │
│  │                                                       │
│  token_transfers (append-only)                           │
│  ├─ from_user_id, to_user_id, token, amount, fee        │
│  ├─ memo (reason), tx_type (transfer/mint/burn)          │
│  └─ created_at (immutable timestamp)                     │
│                                                          │
│  [Internal state = single source of truth]              │
└─────────┬────────────────────────────────────────────────┘
          │
          ├─→ Nightly: Settlement to blockchain (BSC/TON)
          ├─→ Weekly: Reconciliation report
          └─→ Monthly: Investor statements
```

---

## 3️⃣ KEY FORMULAS & CALCULATIONS

### A. Balance Calculation
```python
User_Total_Value = (SLH_balance × 444) + (MNH_balance × 1) + (ZVK_balance × 4.4) + (REP_balance × 0) + (ZUZ_balance × -1)
# ZVK value is implied (can be made explicit)
# REP is non-monetary (tier access)
# ZUZ subtracts value (fraud cost)
```

### B. Transaction Fee Calculation
```python
Fee = amount × fee_rate + fixed_fee

Example (buying marketplace item for 50 MNH):
- Fee rate: 2% = 1 MNH
- Fixed fee: 0.1 MNH
- Total fee: 1.1 MNH
- Seller receives: 50 - 1.1 = 48.9 MNH
- Platform keeps: 1.1 MNH (burned or kept as revenue)
```

### C. ZVK Earning Rate
```python
Daily_ZVK = base_activity_zeta × (1 + streak_multiplier) × (1 + time_bonus) × (1 + tier_bonus)

Example (10-win streak, evening session, Tier 2):
Daily_ZVK = 5 × (1 + 0.2) × (1 + 0.1) × (1 + 0.15)
         = 5 × 1.2 × 1.1 × 1.15
         = 7.59 ZVK/day
```

### D. REP Decay / Growth
```python
# Positive actions
REP += 1 per day if account_age > 30 days AND no_fraud_flags
REP += 5 per successful referral
REP += 10 per community_contribution

# Negative actions
REP -= 50 per fraud_report
REP -= 100 per chargeback
REP -= 20 per ZUZ_flag
```

---

## 4️⃣ TRANSACTION TYPES & AUDIT TRAIL

Every transfer is logged with tx_type:

| tx_type | From | To | Amount | Fee | Example |
|---------|------|----|---------|----|---------|
| `transfer` | user_id | user_id | amount | varies | marketplace buy/sell |
| `mint` | 0 (system) | user_id | amount | 0 | bank deposit → MNH |
| `burn` | user_id | 0 (system) | amount | 0 | token destruction |
| `quest` | 0 | user_id | amount | 0 | daily quest completion |
| `battle` | battle_winner | loser | amount | 0 | pvp reward |
| `referral` | referred_user | referrer | amount | 0 | friend signup bonus |
| `admin_adjustment` | admin | user | amount | 0 | manual correction |

**Query all transactions for a user:**
```sql
SELECT * FROM token_transfers 
WHERE from_user_id = $1 OR to_user_id = $1
ORDER BY created_at DESC;
```

---

## 5️⃣ CRITICAL VERIFICATION TESTS

### Test Suite A: Data Integrity

```sql
-- 1. No negative balances
SELECT user_id, token, balance FROM token_balances WHERE balance < 0;
-- Expected: 0 rows

-- 2. No orphaned transfers (from_user has no balance row)
SELECT DISTINCT t.from_user_id FROM token_transfers t
LEFT JOIN token_balances b ON b.user_id = t.from_user_id AND b.token = t.token
WHERE b.user_id IS NULL AND t.from_user_id > 0;
-- Expected: 0 rows (or only from user_id=0 for mints)

-- 3. Sum of all transfers = sum of all balances (per token)
SELECT 
  'SLH' as token,
  (SELECT SUM(amount) FROM token_transfers WHERE token='SLH' AND tx_type IN ('transfer','mint','battle','quest','referral')) as total_issued,
  (SELECT SUM(balance) FROM token_balances WHERE token='SLH') as total_balance;
-- Expected: total_issued ≥ total_balance (allows for fees/burns)

-- 4. Consistency check: for each transfer, receiver balance increased
-- (Cannot easily query, but audit historical state)

-- 5. REP token has no transfers
SELECT COUNT(*) FROM token_transfers WHERE token='REP';
-- Expected: 0 rows

-- 6. ZUZ has only mint/burn/admin (no transfers)
SELECT DISTINCT tx_type FROM token_transfers WHERE token='ZUZ';
-- Expected: ['mint', 'burn', 'admin_adjustment'] only
```

### Test Suite B: Economic Correctness

```sql
-- 7. Total ZVK issued matches documented quests/battles
SELECT 
  (SELECT SUM(amount) FROM token_transfers WHERE token='ZVK' AND tx_type='quest') as zv_from_quests,
  (SELECT COUNT(*) FROM daily_quests WHERE completed=true) as quest_count,
  (SELECT AVG(xp_reward) FROM daily_quests WHERE completed=true) as avg_xp_per_quest;

-- 8. MNH supply = tracked ILS in bank
SELECT 
  (SELECT SUM(balance) FROM token_balances WHERE token='MNH') as total_mnh,
  (SELECT SUM(amount_ils) FROM bank_deposits WHERE status='confirmed') as total_ils_deposited,
  (SELECT SUM(amount_ils) FROM bank_withdrawals WHERE status='completed') as total_ils_withdrawn;
-- Expected: total_mnh ≈ (total_ils_deposited - total_ils_withdrawn)

-- 9. ZVK average per active user
SELECT 
  COUNT(DISTINCT user_id) as active_users,
  AVG(balance) as avg_zvk_per_user,
  SUM(balance) as total_zvk_in_circulation
FROM token_balances WHERE token='ZVK' AND balance > 0;

-- 10. Top 10 SLH holders (whale distribution check)
SELECT user_id, balance, 
  ROUND(100.0 * balance / (SELECT SUM(balance) FROM token_balances WHERE token='SLH'), 2) as pct_of_total
FROM token_balances 
WHERE token='SLH'
ORDER BY balance DESC
LIMIT 10;
-- Expected: No single whale should hold >20% (concentration risk)
```

### Test Suite C: Fraud Detection

```sql
-- 11. Users with REP < 0 (should be banned)
SELECT user_id, balance as rep_score FROM token_balances WHERE token='REP' AND balance < 0;

-- 12. Users with ZUZ ≥ 100 (should be account-locked)
SELECT user_id, balance as zuz_score FROM token_balances WHERE token='ZUZ' AND balance >= 100;
-- Check that these users have NO token_transfers after ZUZ reached 100

-- 13. Suspicious patterns: user transferred ZVK more than earned
SELECT 
  from_user_id,
  (SELECT SUM(amount) FROM token_transfers WHERE from_user_id=$1 AND token='ZVK' AND tx_type IN ('quest','battle','referral')) as earned,
  (SELECT SUM(amount) FROM token_transfers WHERE from_user_id=$1 AND token='ZVK' AND tx_type='transfer') as transferred
FROM (SELECT DISTINCT from_user_id FROM token_transfers WHERE token='ZVK' AND tx_type='transfer') u
WHERE transferred > earned;
-- Expected: 0 rows (should be caught by balance checks)
```

---

## 6️⃣ PERFORMANCE & OPTIMIZATION

### Current Database Schema Issues

**Good:**
✅ Unique constraint on (user_id, token) prevents double-entry  
✅ Append-only transfer log for audit trail  
✅ Transactional transfers prevent race conditions  
✅ NUMERIC(18,8) allows for micro-transactions

**To Optimize:**
⚠️ Missing index on `token_transfers(from_user_id, created_at DESC)` - add for query speed  
⚠️ Missing index on `token_transfers(to_user_id, created_at DESC)` - add for transaction history  
⚠️ Missing index on `token_balances(token)` - add for leaderboard queries  

**Recommended Index Additions:**
```sql
CREATE INDEX IF NOT EXISTS idx_token_transfers_from_time 
  ON token_transfers(from_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_token_transfers_to_time 
  ON token_transfers(to_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_token_transfers_type_time
  ON token_transfers(tx_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_token_balances_by_token
  ON token_balances(token, balance DESC);
```

---

## 7️⃣ RECOMMENDATIONS FOR IMPROVEMENT

### Short-term (This week)
1. ✅ Run Test Suite A (Data Integrity) - verify no corruption
2. ✅ Run Test Suite B (Economics) - check math is correct
3. ✅ Run Test Suite C (Fraud) - identify bad actors
4. ✅ Add missing database indexes (performance)

### Medium-term (This month)
5. Implement automatic REP decay (currently manual?)
6. Implement automatic ZUZ decay (fraud flags should expire)
7. Create daily reconciliation reports (blockchain settlement)
8. Publish token economics dashboard (transparency for investors)

### Long-term (Q2 2026)
9. Migrate to smart contract staking (ZVK → zToken)
10. Implement DAO governance (SLH holders vote on changes)
11. Automated market maker for ZVK trading
12. Cross-chain bridge (BSC/TON/Polygon)

---

## 8️⃣ CURRENT STATE CHECKLIST

- [ ] Database is online and responsive
- [ ] All token_balances have corresponding entries
- [ ] All transfers are logged
- [ ] No negative balances exist
- [ ] MNH supply matches ILS deposits
- [ ] ZVK earnings match quest/battle logs
- [ ] REP scores reflect actions
- [ ] ZUZ fraud flags are accurate
- [ ] Top holders are identified
- [ ] No suspicious transfer patterns

---

## Questions for Osif

1. **Implied vs. Explicit ZVK Value:** ZVK is currently "worth ~4.4 ILS" in assumptions. Should this be:
   - Explicit (mint ZVK at 4.4 ILS = 1 SLH ÷ 100 ZVK)?
   - Flexible (let market price ZVK on DEX)?
   - Fixed in contract (immutable)?

2. **REP Decay:** Is REP currently:
   - Static (never decays)?
   - Manual adjustments only?
   - Should be automatic (+1 per day for good behavior)?

3. **ZUZ Decay:** Should fraud scores auto-recover?
   - Example: -1 ZUZ per 30 days of clean activity?
   - Or permanent until manual admin review?

4. **Blockchain Settlement:** How often should internal ledger settle to BSC?
   - Daily? Weekly? On-demand?
   - Should we reserve tokens in smart contract?

5. **Public Dashboard:** Should investors see:
   - Real-time circulation per token?
   - Top holder distribution?
   - Daily earnings leaderboard?
   - Fraud detection alerts?

---

**End of Audit**
