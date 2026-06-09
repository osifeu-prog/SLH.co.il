# מודול 4 — Treasury & Coverage Ratio
**Treasury Engineering**

*זמן לימוד: 90 דקות · רמה: Pro · תנאי קדם: מודולים 1-3*

---

## הרעיון המרכזי

Treasury של פרוטוקול היא **מערכת חיסכון שלוש-שכבתית**. לא ארנק אחד, לא מספר אחד.
שכבה חסרה = סיכון מערכתי.

אחרי המודול תדע:
1. לבנות Treasury רב-שכבתי נכון
2. לכייל Buffer ליחס לסיכון שאתה מוכן לספוג
3. לקרוא `/status` של כל פרוטוקול ולזהות אם ה-Treasury אמיתי
4. לנתח את Treasury של SLH עצמה כ-Case Study

---

## 1. שלוש שכבות Treasury

```
┌────────────────────────────────────────────┐
│  Layer 1: Operating (10-20% of TVL)        │
│  Purpose: payouts, daily ops                │
│  Form: hot wallets, PSP balances            │
│  Access: automated (Risk Engine)            │
│  Reaction time: seconds                     │
└────────────────────────────────────────────┘
┌────────────────────────────────────────────┐
│  Layer 2: Buffer (30-50% of TVL)           │
│  Purpose: bank-run absorption               │
│  Form: stablecoin reserves, liquid crypto   │
│  Access: multi-sig (2-of-3+)                │
│  Reaction time: hours                       │
└────────────────────────────────────────────┘
┌────────────────────────────────────────────┐
│  Layer 3: Deep Reserve (20-40% of TVL)     │
│  Purpose: long-term stability, capex        │
│  Form: staked ETH/BTC, RWAs, index funds    │
│  Access: cold storage, multisig + delay     │
│  Reaction time: days                        │
└────────────────────────────────────────────┘
```

**כלל יסוד:**
- סך כל השכבות ≥ 80% מ-TVL בסיטואציה נורמלית
- Layer 1 + Layer 2 ≥ 50% — מספיק ל-bank run של 30%
- Layer 3 לא נוגעים בו ל-operations שוטפות

---

## 2. איך מחשבים את ה-Buffer הנכון

### 2.1 שאלות הליבה
1. **מהו הסיכון המקסימלי לקריסה שאני מוכן לקבל?** (למשל: 1 ל-1000 שנים)
2. **מה תרחיש ה-stress הסביר?** (bank run של כמה אחוזים?)
3. **מה מהירות התגובה של הצוות?** (שעות? ימים? שבועות?)

### 2.2 הנוסחה

```
Buffer_required = Expected_stress_outflow + Operating_runway
                = (P(stress) × outflow) + (burn_rate × reaction_days)

Where:
  P(stress) = 0.15 (typical: 15% probability of ≥20% withdrawal in 30d)
  outflow   = 0.30 × TVL (typical stress test)
  burn_rate = monthly C_t + P_t
  reaction_days = 7 (safe default)
```

### 2.3 דוגמה מספרית

```
TVL = $500,000
Monthly C_t = $12,000
Monthly P_t = $9,500 (expected)
Burn_rate = $21,500 / month = $717 / day

Expected_stress_outflow = 0.30 × 500000 = $150,000
Operating_runway = 717 × 7 = $5,019

Buffer_required ≈ $155,000 (31% of TVL)
```

**יעד:** Buffer ≥ 31% of TVL. כל מה שפחות = מערכת פגיעה.

---

## 3. Multi-Sig Architecture (איך ארנקי ה-Treasury חייבים להיות בנויים)

### 3.1 הבעיה של ארנק יחיד

ארנק פרטי אחד עם 50% מה-TVL = single point of failure.
אם מפתח נפרץ / נאבד / האדם נפטר → הכסף אבוד.

### 3.2 הפתרון: Gnosis Safe / TON MultiSig

Layer 2 חייב להיות **multi-sig של 3-of-5 לפחות.**

```
Signers:
  1. Founder (primary signer)
  2. Technical lead
  3. Community-elected representative
  4. Legal advisor / auditor
  5. Emergency signer (cold, time-locked)
```

**Quorum:** 3 מתוך 5 חייבים לחתום על כל טרנזקציה מעל סכום מסוים.
**Time-lock:** החתימות תקפות רק אחרי 24-48 שעות (למנוע הלם-חתימות).

### 3.3 Layer 3 — Cold Storage

```
Storage: hardware wallet (Ledger, Trezor), offline
Signers: 2-of-3 (founder + 2 trusted)
Access: quarterly at most, planned in advance
Purpose: long-term capital, not operating cash
```

### 3.4 Key Management Policy

- **לא** אותו מפתח פרטי במקומות שונים
- **לא** BIP39 seed phrase במייל / Google Docs
- **כן** seed phrase פיזית, במקומות מופרדים גיאוגרפית
- **כן** סימולציה של אובדן מפתח אחת לרבעון

---

## 4. Liquidity Engineering

### 4.1 Composition של Layer 1

```
Target Layer 1 mix:
  50% Stablecoins (USDT, USDC, DAI) — immediately deployable
  30% Major crypto (ETH, BTC) — liquid via DEX
  15% Fiat / PSP balance — for off-ramp
   5% Native token (SLH) — for on-chain ops / emergencies
```

### 4.2 DEX Liquidity Considerations

אם הפרוטוקול שלך מציע שוק ל-token משלו, Liquidity ב-DEX היא **פקטור קריטי**:

```
Recommended DEX liquidity:  ≥ 10% of circulating supply value
Dangerous DEX liquidity:    < 1% of circulating supply value
```

**למה חשוב:** משתמש שמושך $10K ורוצה להמיר token למזומן — אם ה-AMM רדוד, ה-slippage יכול להיות 50%+.

**דוגמה רעה (SLH נוכחי):** $19.56 liquidity ב-PancakeSwap מול market cap $6.17K = 0.3%.
משיכה של $200 תשבור את ה-pool. **צריך להעלות ל-$5,000-$10,000 מינימום.**

---

## 5. Treasury Transparency Dashboard

### מה חייב להופיע ציבורית:

```
┌─────────────────────────────────────────────┐
│  SLH Treasury · Live                         │
│  Last updated: 2 min ago · Next: 5 min      │
├─────────────────────────────────────────────┤
│  Layer 1 (Operating)    $45,000   (15%)     │
│  ├─ Stables:            $22,500              │
│  ├─ ETH:                $13,500              │
│  └─ Fiat/PSP:           $ 9,000              │
│                                              │
│  Layer 2 (Buffer)       $120,000  (40%)     │
│  ├─ Multi-sig BSC:      $ 60,000             │
│  │   0xABC...XYZ  (3-of-5 signed)           │
│  ├─ Multi-sig TON:      $ 35,000             │
│  │   EQD...KFG                               │
│  └─ Stable reserve:     $ 25,000             │
│                                              │
│  Layer 3 (Deep)         $75,000   (25%)     │
│  └─ Cold wallet (2-of-3)                    │
│                                              │
│  TOTAL:                 $240,000  (80%)     │
│  Current TVL:           $300,000             │
│  Buffer Ratio:          80% ✓ Healthy       │
│                                              │
│  Last 30d net flow:     +$12,400            │
│  Last audit:            2026-04-18           │
└─────────────────────────────────────────────┘
```

### מה **אסור** להראות:

- ❌ מספר יחיד "Treasury: $240K" בלי פירוק
- ❌ "Trust us, we have $X"
- ❌ יתרות סטטיות ללא timestamp / refresh
- ❌ PDF מרובע פעם בחודש בלי אפשרות אימות

---

## 6. Case Study: SLH Treasury Walkthrough

**אזהרה גילוי:** SLH Treasury בבנייה. המספרים הבאים הם היעד (לא המצב הנוכחי).

### 6.1 מצב נוכחי (2026-04-20)

```
Layer 1 (Operating): ~$2,500
  └─ WEWORK bot balance + small hot wallet

Layer 2 (Buffer): $0 (לא קיים)
Layer 3 (Deep): נכסים פרטיים של Osif לא מופרדים

Total Treasury: בלתי מוגדר
TVL: נמוך (pre-launch)
```

זה **לא תקין** לפי הקריטריונים שלמדנו. וזה חלק מהסיבה ש-SLH היום לא יכולה לתת APY קבוע.

### 6.2 יעד 6 חודשים

```
Layer 1: $10-20K (operating)
Layer 2: Multi-sig BSC + TON, ~30-40% of TVL
Layer 3: Cold wallet, ~25% of TVL
Total Buffer Ratio: 60-80%
Public wallets: 3 addresses, live-refreshing
Audit cycle: quarterly (Q1 2026 first)
```

### 6.3 Treasury funding mechanism

מאיפה יגיע הכסף ל-Buffer?

```
30% of every Revenue flows to Buffer (not distributed)
  - Course #1 sales (70% to instructor, 30% to platform → 20% platform goes to Buffer)
  - Marketplace fees (5% → 2% to Buffer)
  - Bot subscriptions (30% → Buffer)
  - Founder capital contribution (milestone-based)
  
Monthly Buffer target growth: +5% of TVL (until 40%)
```

**No** Buffer funding from:
- New user deposits
- Token inflation
- Referral fees (those ARE payouts)

---

## 7. Risk Stress Tests

### 7.1 Scenario Testing

הרץ כל חודש את התרחישים האלה ותעד:

**Test A: Soft withdrawal (15%)**
```
Simulate: W_t = 0.15 × U_t
Expected: CR stays > 1.0, no throttling, operation continues
Pass criteria: no defaults, buffer reduction ≤ 20%
```

**Test B: Hard withdrawal (30%)**
```
Simulate: W_t = 0.30 × U_t in 48h
Expected: throttling activates, CR drops but stays > 0.5
Pass criteria: withdrawals complete within 7-14 days, no defaults
```

**Test C: Bank run (50%)**
```
Simulate: W_t = 0.50 × U_t attempted in 24h
Expected: full Circuit Breaker lockdown
Pass criteria: operations continue in crippled mode, partial payouts, recovery within 30 days
```

**Test D: Revenue drought (3 months zero R_t)**
```
Simulate: R_t = 0 for 90 days
Expected: P_t = 0 for 3 cycles, Buffer sustains C_t
Pass criteria: Buffer reduction acceptable, team has runway
```

### 7.2 הפעלה

הרץ את [treasury_simulation.py](/academy/course-1-dynamic-yield/treasury_simulation.py) עם הפרמטרים שלך.
הסקריפט מפיק גרפים של Buffer, CR, ו-implied APY לאורך 12 חודשים בכל תרחיש.

---

## 8. Red Flags ב-Treasury של פרוטוקול אחר

| סימן | פירוש |
|---|---|
| "Treasury audit Q3 2024" (עבר שנה) | לא מאומת עדכני |
| רק PDF, אין כתובת ארנק | לא ניתן לאימות |
| יתרה תמיד עגולה (100K בדיוק) | מספרים מסודרים מדי = חשוד |
| Multi-sig עם 2-of-2 | יותר גרוע מ-1 signer |
| Signers כולם באותה מדינה / חברה | לא מבוזר אמיתית |
| אין entry/exit logs | אי אפשר לראות תנועות |
| "כספי הלקוח מופרדים" בלי הוכחה | בלי segregated accounts proof — שקר |

---

## 9. תרגול

קח פרוטוקול שאתה מחזיק. בדוק:

```
Protocol: _______
Treasury pages visible? Y / N
Public wallet addresses? Y / N — list: _______
Multi-sig config? Y / N — quorum: ___-of-___
Refresh frequency? _______ (real-time / daily / weekly / not stated)
Last audit date? _______
Buffer Ratio? _______ %
Run Test 30% survivable? Y / N / Unknown

Score: ___/7
Conclusion: [ ] Trustable [ ] Suspicious [ ] Exit
```

---

## סיכום

- Treasury = מערכת 3-שכבתית, לא ארנק אחד.
- Buffer Ratio ≥ 30% = זכות קיום.
- Multi-sig ≥ 3-of-5, time-locked, מבוזר גיאוגרפית.
- **שקיפות ב-real-time** = חובה, לא תוספת.
- SLH היום לא עומדת בקריטריונים האלה במלואם. זה ה-gap שהקורס הזה חוזה לגשר.

---

**המודול הבא:** Circuit Breakers & Run Protection — 5 מנגנוני עצירה אוטומטיים, סימולטור Python להרצת תרחישים, וחוקי התנהגות למצבי קיצון.

[→ המשך למודול 5: Circuit Breakers (Pro)](/academy/course-1-dynamic-yield/module-5.html)
