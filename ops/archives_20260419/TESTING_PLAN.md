# SLH Ecosystem - Comprehensive Testing Plan
## Wallets, Deposits & Payment Systems

**Version:** 1.0 | **Date:** April 2026 | **Author:** SPARK IND

---

## 1. Test Environment Setup

### Prerequisites
- Docker Compose running locally with all services
- PostgreSQL 15 + Redis 7 healthy
- Test Telegram accounts (at least 2: admin + regular user)
- Testnet TON wallet with test coins
- BSC testnet wallet with test SLH tokens
- CoinGecko API accessible

### Test Database
```sql
-- Create isolated test schema
CREATE SCHEMA IF NOT EXISTS test_slh;
-- Seed test users
INSERT INTO users (telegram_id, username, balance_ton, balance_slh)
VALUES (999999901, 'test_user_1', 10.0, 1000),
       (999999902, 'test_user_2', 5.0, 500);
```

### Environment Variables for Testing
```env
ENV=test
DATABASE_URL=postgresql://postgres:slh_secure_2026@localhost:5432/slh_test
TON_NETWORK=testnet
TON_API_KEY=<testnet_key>
```

---

## 2. Unit Tests

### 2.1 Payment Gateway (`shared/slh_payments/payment_gate.py`)

| # | Test Case | Input | Expected | Priority |
|---|-----------|-------|----------|----------|
| U1 | Create payment intent | user_id, amount, currency | Returns payment_id, status=pending | CRITICAL |
| U2 | Validate TON amount | amount=0.001 | Reject (below minimum 0.01) | HIGH |
| U3 | Validate TON amount | amount=10000 | Reject (above maximum) | HIGH |
| U4 | Validate negative amount | amount=-5 | Reject with error | CRITICAL |
| U5 | Currency normalization | "ton", "TON", "Ton" | All normalize to "TON" | MEDIUM |
| U6 | Payment expiry | payment older than 30min | Status = expired | HIGH |
| U7 | Duplicate payment detection | same user_id + amount within 60s | Warning/block | HIGH |
| U8 | Fee calculation | amount=10 TON, fee=0.5% | fee=0.05, net=9.95 | CRITICAL |

### 2.2 TON Service (`wallet/app/ton_service.py`)

| # | Test Case | Input | Expected | Priority |
|---|-----------|-------|----------|----------|
| U9 | Generate wallet address | user_id | Valid TON address (0: or EQ prefix) | CRITICAL |
| U10 | Validate TON address | valid address | True | HIGH |
| U11 | Validate TON address | "invalid_string" | False | HIGH |
| U12 | Get balance | known address | Returns numeric >= 0 | HIGH |
| U13 | Get balance | non-existent address | Returns 0 | MEDIUM |
| U14 | Parse transaction | raw tx data | Correct sender, receiver, amount | CRITICAL |

### 2.3 Deposit Watcher (`botshop/app/services/deposit_watcher.py`)

| # | Test Case | Input | Expected | Priority |
|---|-----------|-------|----------|----------|
| U15 | Detect new deposit | new tx on monitored address | Trigger deposit_received event | CRITICAL |
| U16 | Ignore old transactions | tx older than 1hr | No event triggered | HIGH |
| U17 | Handle duplicate tx | same tx_hash twice | Process only once | CRITICAL |
| U18 | Minimum deposit check | tx amount < minimum | Reject, notify user | HIGH |
| U19 | Confirmation count | tx with 0 confirmations | Wait for minimum confirmations | HIGH |

### 2.4 Wallet Engine (`botshop/app/services/wallet_engine.py`)

| # | Test Case | Input | Expected | Priority |
|---|-----------|-------|----------|----------|
| U20 | Credit wallet | user_id, +10 TON | Balance increases by 10 | CRITICAL |
| U21 | Debit wallet | user_id, -5 TON | Balance decreases by 5 | CRITICAL |
| U22 | Insufficient funds | debit > balance | Reject with error | CRITICAL |
| U23 | Concurrent operations | 2 debits simultaneously | No race condition, correct balance | CRITICAL |
| U24 | Double-entry ledger | any transaction | Debit entry + Credit entry = 0 | CRITICAL |
| U25 | Transaction log | any wallet op | Entry in transaction_log table | HIGH |

---

## 3. Integration Tests

### 3.1 TON Deposit Flow (End-to-End)

```
User sends /deposit command
  -> Bot generates unique deposit address
  -> User sends TON to address
  -> Deposit watcher detects transaction
  -> Balance credited to user account
  -> User receives confirmation message
  -> Transaction logged in ledger
```

| # | Test Case | Steps | Expected | Priority |
|---|-----------|-------|----------|----------|
| I1 | Full deposit flow | Send 1 TON to deposit address | Balance +1 TON, notification sent | CRITICAL |
| I2 | Multi-coin deposit | Send BNB to BSC address | Balance +BNB, correct conversion | HIGH |
| I3 | Deposit with memo | Send TON with comment/memo | Correctly attributed to user | HIGH |
| I4 | Deposit below minimum | Send 0.001 TON | Error message, no credit | HIGH |
| I5 | Deposit during maintenance | Send while bot restarting | Queued, processed after restart | CRITICAL |

### 3.2 Withdrawal Flow

| # | Test Case | Steps | Expected | Priority |
|---|-----------|-------|----------|----------|
| I6 | Full withdrawal | Request withdraw 2 TON | Balance -2, tx sent on-chain | CRITICAL |
| I7 | Withdraw to invalid address | Bad TON address | Reject before sending | CRITICAL |
| I8 | Withdraw exceeding balance | Request 100 TON with 5 balance | Reject with error | CRITICAL |
| I9 | Withdraw with fee | Withdraw 10 TON | Fee deducted, correct net sent | HIGH |
| I10 | Daily withdrawal limit | Exceed daily limit | Reject, show remaining limit | HIGH |

### 3.3 P2P Transfer

| # | Test Case | Steps | Expected | Priority |
|---|-----------|-------|----------|----------|
| I11 | Transfer between users | User A -> User B, 5 SLH | A: -5, B: +5, both notified | CRITICAL |
| I12 | Transfer to self | User A -> User A | Reject | MEDIUM |
| I13 | Transfer to non-existent user | Invalid user_id | Reject with error | HIGH |
| I14 | Transfer 0 amount | amount = 0 | Reject | HIGH |

### 3.4 Database Integrity

| # | Test Case | Verification | Priority |
|---|-----------|-------------|----------|
| I15 | Ledger balance check | SUM(debits) = SUM(credits) for all accounts | CRITICAL |
| I16 | User balance consistency | user.balance = SUM(transactions) | CRITICAL |
| I17 | No orphan transactions | All tx have valid user_id references | HIGH |
| I18 | Transaction immutability | No UPDATE or DELETE on transaction_log | CRITICAL |

### 3.5 Cross-Bot Economy

| # | Test Case | Steps | Expected | Priority |
|---|-----------|-------|----------|----------|
| I19 | ZVK earn in Game Bot | Play game, win ZVK | ZVK balance visible in all bots | HIGH |
| I20 | SLH spend in BotShop | Purchase with SLH tokens | Deducted from shared ledger | HIGH |
| I21 | Cross-bot balance query | Check balance from any bot | Same balance everywhere | CRITICAL |

---

## 4. Security Tests

| # | Test Case | Attack Vector | Expected | Priority |
|---|-----------|---------------|----------|----------|
| S1 | SQL injection | Deposit amount = "1; DROP TABLE" | Sanitized, no damage | CRITICAL |
| S2 | Negative deposit | Send negative amount via API | Rejected at validation | CRITICAL |
| S3 | Integer overflow | Amount = 999999999999 | Handled gracefully | HIGH |
| S4 | Race condition | 10 concurrent withdrawals | Only succeeds if balance allows | CRITICAL |
| S5 | Replay attack | Resubmit same tx_hash | Rejected (already processed) | CRITICAL |
| S6 | Private key exposure | Check logs, error messages | No private keys in any output | CRITICAL |
| S7 | Admin impersonation | Non-admin sends admin commands | Rejected | HIGH |
| S8 | Rate limiting | 100 deposit requests/minute | Throttled after limit | MEDIUM |

---

## 5. Performance Tests

| # | Test Case | Load | Threshold | Priority |
|---|-----------|------|-----------|----------|
| P1 | Balance query speed | 100 concurrent queries | < 200ms each | HIGH |
| P2 | Deposit processing | 50 deposits/minute | All processed within 5 min | HIGH |
| P3 | Price feed latency | CoinGecko updates | < 2 minute staleness | MEDIUM |
| P4 | Database connections | 22 bot containers | No connection pool exhaustion | CRITICAL |
| P5 | Redis pub/sub | 1000 events/minute | No message loss | HIGH |

---

## 6. Recovery Tests

| # | Test Case | Scenario | Expected | Priority |
|---|-----------|----------|----------|----------|
| R1 | Bot crash recovery | Kill bot container during deposit | Deposit processed after restart | CRITICAL |
| R2 | Database failover | Restart PostgreSQL | Bots reconnect, no data loss | CRITICAL |
| R3 | Redis failure | Stop Redis | Bots degrade gracefully, no crash | HIGH |
| R4 | Network timeout | Block TON API | Queue requests, retry after reconnect | HIGH |
| R5 | Partial transaction | Crash mid-transfer | Rollback, no partial credits | CRITICAL |

---

## 7. User Acceptance Tests (Telegram)

### Manual test script for each bot:

#### Wallet Bot (@SLH_Wallet_bot)
1. [ ] `/start` - Welcome message with wallet options
2. [ ] `/register` - Create new TON + BNB wallet
3. [ ] `/balance` - Show current balances
4. [ ] `/deposit` - Generate deposit address with QR
5. [ ] Send test TON to deposit address
6. [ ] Verify balance updated
7. [ ] `/withdraw <amount> <address>` - Test withdrawal
8. [ ] `/history` - View transaction history
9. [ ] Test with Hebrew, English, Russian, Arabic, French

#### ExpertNet Bot (@SLH_AIR_bot)
1. [ ] `/start` - Welcome + investment options
2. [ ] Select deposit plan (4%, 4.5%, 5%, 5.4%)
3. [ ] Deposit minimum amount
4. [ ] Verify deposit credited
5. [ ] Check yield calculation after 24hrs
6. [ ] `/portfolio` - View holdings
7. [ ] `/swap TON SLH 1` - Token swap
8. [ ] `/withdraw` - Test withdrawal flow
9. [ ] `/referral` - Get referral link
10. [ ] New user joins via referral link
11. [ ] Verify referral bonus credited

#### BotShop (@GATE_BotShop_bot)
1. [ ] `/start` - Store interface
2. [ ] Browse products
3. [ ] Purchase with TON
4. [ ] Verify payment deducted
5. [ ] Verify product delivered

#### TON MNH Bot (@TON_MNH_bot)
1. [ ] `/start` - Check TON balance
2. [ ] Enter wallet address
3. [ ] View transaction history
4. [ ] Product marketplace browse
5. [ ] VIP group access test

---

## 8. Monitoring Checklist (Post-Deploy)

- [ ] PostgreSQL: Connection pool usage < 80%
- [ ] Redis: Memory usage < 50%
- [ ] All 22 Docker containers: status = healthy
- [ ] Deposit watcher: Processing deposits within 2 minutes
- [ ] CoinGecko prices: Updating every 60 seconds
- [ ] No ERROR level logs in any bot
- [ ] Guardian bot: Security alerts working
- [ ] Admin bot: Dashboard metrics accurate
- [ ] Double-entry ledger: Daily balance verification passes

---

## 9. Test Execution Order

### Phase 1: Foundation (Before any real deposits)
1. All Unit Tests (U1-U25)
2. Security Tests (S1-S8)
3. Database Integrity (I15-I18)

### Phase 2: Integration (Testnet only)
4. TON Deposit Flow (I1-I5)
5. Withdrawal Flow (I6-I10)
6. P2P Transfer (I11-I14)
7. Cross-Bot Economy (I19-I21)

### Phase 3: Stress & Recovery
8. Performance Tests (P1-P5)
9. Recovery Tests (R1-R5)

### Phase 4: User Acceptance (Real Telegram, small amounts)
10. Manual UAT for each bot
11. Monitoring verification

---

## 10. Test Results Template

| Test ID | Date | Tester | Result | Notes |
|---------|------|--------|--------|-------|
| U1 | | | PASS/FAIL | |
| U2 | | | PASS/FAIL | |
| ... | | | | |

---

*SPARK IND | SLH Ecosystem | Testing Plan v1.0*
