# מודול 5 — Circuit Breakers ומניעת ריצה
**Run Protection**

*זמן לימוד: 90 דקות · רמה: Pro · תנאי קדם: מודולים 1-4*

---

## למה המודול הזה הוא הלב של הקורס

Dynamic Yield, Coverage Ratio, Treasury — כולם חסרי ערך אם המערכת קורסת בתרחיש קיצון.
**Circuit Breakers הם ההבדל בין "נעים תיאורטית" ל"עומד בלחץ אמיתי".**

אחרי המודול הזה תוכל:
1. להטמיע 5 Circuit Breakers במערכת שלך
2. להריץ סימולציות Python של תרחישי קיצון
3. לתעדף הפעלת breakers לפי חומרה
4. לכתוב פרוטוקול תגובה למצבי חירום

---

## 1. מהו Circuit Breaker

Circuit Breaker (מתג נתיך) הוא **מנגנון אוטומטי שעוצר פעילות כשתנאי-סף מופרים.**
השם מהבנקאות המסורתית (NYSE trading halts, Fed emergency rate cuts).

**עקרונות:**
- **אוטומטי** — לא מצריך החלטת אדם
- **הפיך** — כשהתנאי מתוקן, הפעילות חוזרת
- **שקוף** — המשתמש רואה מיידית מה נדלק ולמה
- **הדרגתי** — לא "on/off" אלא רמות תגובה

---

## 2. חמשת המנגנונים ב-Dynamic Yield

### Breaker 1: Coverage Guardrail
```
IF CR_t < 1.0:
    k_new = k × 0.8       (reduce distribution by 20%)
    pause_new_deposits = True
    notify_users("Coverage guardrail active")
    log_event("CR_BREACH", CR_t, P_t, W_t)
```

**מה זה עושה:** אם יחס הכיסוי יורד מ-1.0, מקטין את החלוקה ומעצור הפקדות חדשות. משיכות ממשיכות.

**למה:** הפקדה חדשה תגדיל את U_t, יגדיל את ההתחייבויות עתידיות. אסור במצב זה.

### Breaker 2: Withdrawal Throttle
```
IF W_t_24h > 0.15 × U_t:
    per_wallet_limit = 0.01 × balance_user  (1% per day)
    enforce_for_days = 7
    notify_users("High-volume withdrawal regime — pro-rata limits")
```

**מה זה עושה:** אם יותר מ-15% מה-TVL נמשך ב-24 שעות, מגביל כל ארנק ל-1% מיתרתו ליום.

**למה:** מונע cascade של bank run. מעניק זמן ל-Treasury להתאושש ולהיות מחולק פרופורציונלית.

**דוגמה:**
```
User balance: $10,000
Normal: can withdraw all $10,000 immediately
Throttle active: max $100/day → 100 days to drain fully
  (In practice: user might want only $500, so throttling rarely bites casual users)
```

### Breaker 3: Deposit Freeze
```
IF CR_t < 0.5:
    pause_new_deposits = True
    pause_referral_signups = True
    withdrawals = remain_open (but throttled if #2 active)
    lock_period = until CR > 1.2 for 7 consecutive days
```

**מה זה עושה:** במצב קיצוני, סוגרים הפקדות לגמרי. משיכות נשארות פתוחות.

**למה:** אם CR < 0.5, כל דולר חדש שנכנס הופך ל-liability שאין כיסוי לו. אסור לקבל יותר.

### Breaker 4: Buffer Recovery Mode
```
IF B_t < 0.10 × U_t:
    k = 0                     (no distribution to users)
    all_Net → B_t             (100% of net goes to buffer)
    duration = until B_t ≥ 0.15 × U_t
    notify_users("Buffer recovery mode — yields paused, buffer rebuilding")
```

**מה זה עושה:** אם Buffer ירד מתחת ל-10% של TVL, כל ההכנסות הנטו עוברות לחיזוק Buffer. אפס חלוקה.

**למה:** Buffer נמוך = מערכת שברירית. עדיף להפסיק חלוקות זמנית ולחזק, מאשר להמשיך לחלק ולקרוס.

**הערה חשובה:** המשתמשים מקבלים התראה מראש ואת ההצדקה. זה לא "חוזה נשבר" — זה **המנגנון עובד בדיוק כמתוכנן.**

### Breaker 5: Oracle Drift Freeze
```
IF |on_chain_price - internal_price| / on_chain_price > 0.05:
    pause_deposits = True
    pause_withdrawals = True  
    pause_distributions = True
    notify_admins("Oracle discrepancy — reconciliation required")
    max_pause_duration = 4h (auto-escalate to governance)
```

**מה זה עושה:** אם המחיר הפנימי סוטה מ-oracle חיצוני ביותר מ-5%, כל הפעילות נעצרת.

**למה:** מונע arbitrage attacks, price manipulation exploits, ו-state corruption. 4 שעות מספיק לבני-אדם להבין מה קורה.

---

## 3. דירוג חומרה ותיעדוף

| חומרה | Breakers שיופעלו | זמן תגובה | משתמש רואה |
|---|---|---|---|
| ירוק | none | - | APY_implied live |
| צהוב | #4 only (buffer) | 0s | "Buffer recovery" |
| כתום | #1 + #2 | 0s | "Coverage guardrail + Throttling" |
| אדום | #1 + #2 + #3 | 0s | "Emergency mode — withdrawals only" |
| שחור | #1-#5 | 0s | "System halt — oracle reconciliation" |

---

## 4. Cascade Logic (מה קורה אם כמה תנאים נפרצים יחד)

```python
def evaluate_breakers(state):
    breakers_active = []
    
    # Order matters — highest priority first
    if abs(state.on_chain_price - state.internal_price) / state.on_chain_price > 0.05:
        breakers_active.append("ORACLE_FREEZE")
        return breakers_active  # stop everything, investigate
    
    if state.CR < 0.5:
        breakers_active.append("DEPOSIT_FREEZE")
    
    if state.CR < 1.0:
        breakers_active.append("COVERAGE_GUARDRAIL")
    
    if state.W_24h > 0.15 * state.U:
        breakers_active.append("WITHDRAWAL_THROTTLE")
    
    if state.B < 0.10 * state.U:
        breakers_active.append("BUFFER_RECOVERY")
    
    return breakers_active
```

**הלוגיקה:** Oracle freeze קודם לכל דבר — אם המחירים לא אמינים, שום החלטה אחרת לא תקפה.

---

## 5. הסימולטור המלא

פתח `treasury_simulation.py` ([download](/academy/course-1-dynamic-yield/treasury_simulation.py)).
הסקריפט כולל:
- **12-month projection** עם month-by-month updates
- **4 תרחישים מוגדרים מראש:** Bear / Base / Bull / Crisis
- **User parameters:** TVL התחלתי, user growth rate, avg stake, withdrawal probability
- **Output:** גרפים של CR, Buffer, APY_implied, ו-breaker activation timeline

### הרצה:
```bash
cd D:\SLH_ECOSYSTEM\ops
python treasury_simulation.py --scenario crisis --tvl 500000 --months 12
```

### פלט צפוי (Crisis):
```
Month  TVL       R_t     Net_t   P_t    CR    Breakers
1      500,000   15,000  2,000   800    0.8   [CG]
2      350,000   8,000      0      0    0.5   [CG, WT, DF]
3      280,000   9,500      0      0    0.4   [CG, WT, DF]
4      260,000  12,000    500    200    0.7   [CG]
5      275,000  18,000  3,500  1,400    1.4   []
6      290,000  22,000  6,500  2,600    2.1   []
...

Final state: TVL $320K, Buffer 28%, no defaults. ✓
```

---

## 6. פרוטוקול תגובה לחירום (Runbook)

כשbreaker מופעל, **הצוות מקבל alert מיידי** וחייב לבצע:

### תוך 15 דקות:
1. ✅ לוודא ש-breaker הופעל כראוי (לא false positive)
2. ✅ לפרסם הודעה פומבית ב-/status, Telegram, Twitter
3. ✅ לתעד timestamp + תנאי שהובילו

### תוך שעה:
4. ✅ לזהות root cause (revenue drop? withdrawal spike? exploit?)
5. ✅ להחליט על intervention — האם נדרשות פעולות ידניות מעבר ל-automatic
6. ✅ לעדכן את הקהילה בפירוט

### תוך 24 שעות:
7. ✅ לפרסם post-mortem preliminary
8. ✅ להתאים פרמטרים אם נדרש (k, thresholds)
9. ✅ לוודא שה-breaker ישוחרר אוטומטית כשהמצב יתוקן

### תוך שבוע:
10. ✅ Post-mortem מלא עם lessons learned
11. ✅ אם breaker דמה חוזר תכוף — לשקול adjustments במודל
12. ✅ לעדכן את Course content אם יש לקחים חדשים

---

## 7. Anti-Patterns (איך **לא** לעשות)

### ❌ Pattern 1: "זה לא יקרה לי"
```python
# רע
if unlikely_event:
    logger.warning("This shouldn't happen")
    pass  # just continue
```

**הנכון:**
```python
if any_breaker_condition_met(state):
    activate_breaker(state)
    halt_affected_operations()
    page_oncall()
```

### ❌ Pattern 2: Manual override בלי audit trail
```python
# רע
if admin.force_override:
    skip_breaker_check()
```

**הנכון:**
```python
if admin.force_override:
    log_override(admin.id, reason, timestamp, full_state)
    require_multi_sig(admins_required=2)
    notify_community(override_event)
    still_apply_safety_limits()
```

### ❌ Pattern 3: Breakers ללא disclosure
```python
# רע
user_sees: "Transaction failed"
```

**הנכון:**
```python
user_sees: "Withdrawal throttled: Coverage Guardrail active since 2026-04-21 14:30. 
           CR_t currently 0.87 (target ≥ 1.0). Per-wallet limit 1%/day. 
           Expected duration: 3-7 days. See /status for live updates."
```

### ❌ Pattern 4: השבתת breaker בלי תיעוד
```python
# רע
ENABLE_BREAKERS = False  # disabled temporarily (forgotten)
```

**הנכון:**
```python
BREAKERS_CONFIG = {
    "coverage_guardrail": {"enabled": True, "threshold": 1.0},
    "withdrawal_throttle": {"enabled": True, "threshold_pct": 0.15},
    # ...
}
# + audit log + quarterly review requirement
```

---

## 8. תרגול: כתוב את ה-Runbook שלך

קח את המערכת שלך (או דמיונית). עבור על 5 ה-Breakers, וכתוב:

```
For each breaker:
  1. Exact trigger condition: ______
  2. Automatic action: ______
  3. User-visible message: ______
  4. On-call alert? Y/N: ______
  5. Expected resolution time: ______
  6. Recovery condition: ______
  7. Post-event action required: ______
```

שמור כ-markdown ב-repo. זה ה-runbook שלך.

---

## 9. Real-World Circuit Breaker Examples

### NYSE (Exchange)
- Level 1: -7% in S&P 500 → 15-min halt
- Level 2: -13% → additional 15-min halt
- Level 3: -20% → trading halted for the day

### Federal Reserve (Banks)
- Emergency lending facility when inter-bank rates spike
- Dollar swap lines with foreign central banks
- QE as "liquidity of last resort"

### Crypto Examples
- **MakerDAO:** Emergency Shutdown → freezes all CDPs, returns collateral
- **Compound:** Market pause per-asset on exploit
- **Aave:** Safety Module (staked AAVE absorbs bad debt)

**מסקנה:** כל מערכת פיננסית רצינית יש לה breakers. אם למערכת שלך אין — היא לא פיננסית, היא ניסוי.

---

## 10. Post-Event Learning Loop

כל הפעלת breaker חייבת לעבור ב-pipeline הזה:

```
Event → Logged → Alert → Response → Resolved → Post-mortem → Model Update
```

אם breaker מסוים נדלק יותר מ-3 פעמים ברבעון — המודל צריך עדכון:
- אולי ה-threshold לא מכויל נכון
- אולי יש דפוס שימוש לא צפוי
- אולי ה-buffer מעוצב לא נכון

**Never leave a repeatedly-triggering breaker unexamined.**

---

## סיכום

- 5 Circuit Breakers: Coverage, Throttle, Freeze, Buffer Recovery, Oracle.
- Cascade logic עם priorities ברורים.
- Runbook לתגובת חירום ב-4 window זמנים.
- Anti-patterns לזהות.
- Breakers = הבדל בין "יציב על הנייר" ל"יציב במציאות".

---

**המודול הבא (האחרון):** יישום חי — איך SLH מיישמת בדיוק את מה שלמדת, איפה זה עובד, איפה זה עדיין לא, ותבנית להעתקה למערכת שלך.

[→ המשך למודול 6: SLH Live Case Study (Pro)](/academy/course-1-dynamic-yield/module-6.html)
