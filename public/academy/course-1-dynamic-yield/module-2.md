# מודול 2 — Revenue Engine vs Reward Engine
**The Core Distinction**

*זמן לימוד: 45 דקות · רמה: חינם · תנאי קדם: מודול 1*

---

## הרעיון המרכזי

```
Revenue Engine = מערכת שמייצרת כסף חיצוני.
Reward Engine  = מערכת שמחלקת את מה שנכנס.
```

**99% מהקריסות בקריפטו הן Reward Engines שהתחזו ל-Revenue Engines.**
הבחנה נכונה בין השניים חוסכת לך את ההונאה הבאה.

---

## 1. מה זה Revenue

Revenue (הכנסה) הוא **כסף שמישהו הסכים לשלם לך בתמורה לשירות.**
לא: הפקדה של משתמש. לא: הלוואה. לא: מכירת טוקנים חדשים.

### דוגמאות ל-Revenue אמיתי בקריפטו:

| סוג | מקור | Verifiable? |
|---|---|---|
| עמלת swap (DEX) | כל trade שעובר ב-AMM | ✅ On-chain |
| עמלת הלוואה (Aave) | ריבית מלווים | ✅ On-chain |
| עמלת marketplace | % מכל מכירה | ✅ On-chain אם contract |
| SaaS subscription | תשלום חודשי על bot / tool | ✅ בלגר פנימי |
| מכירת תוכן (Academia) | קורס, webinar, ebook | ✅ בלגר פנימי |
| Gas / Tx fees (L1/L2) | כל טרנזקציה | ✅ On-chain |

### דוגמאות ל"Revenue" מזויף:

| מתחזה | למה זה לא Revenue |
|---|---|
| הפקדות משתמשים | זו התחייבות, לא הכנסה |
| Referral fees שחוזרים למערכת | זה חלוקה פנימית של אותו כסף |
| "Trading profits" בלתי-מבוקרים | לא ניתן לאימות בלי דוחות on-chain |
| מכירת טוקנים חדשים | זה מימון, לא revenue |
| "Liquidity provider rewards" מ-pool עצמי | סיבוב כסף של המערכת בתוך עצמה |

---

## 2. החלוקה הטהורה

```
┌────────────────────────────────────────┐
│  REVENUE ENGINE (המוצר)                │
│                                         │
│  user → pays → external_service         │
│           ↓                             │
│        revenue                          │
└────────────────────────────────────────┘
                  ↓
┌────────────────────────────────────────┐
│  REWARD ENGINE (החלוקה)                 │
│                                         │
│  revenue → distributed → stakers        │
│                       → team            │
│                       → treasury        │
│                       → buffer          │
└────────────────────────────────────────┘
```

שתי המערכות חייבות להיות:
1. **מופרדות** (accounting separate)
2. **שקופות** (ניתנות לביקורת בנפרד)
3. **עם חוק**: Reward ≤ Revenue - Costs - Buffer.

אם Reward > Revenue — המערכת משלמת ממקור אחר: הפקדות משתמשים חדשים. זה Ponzi.

---

## 3. Decision Tree — זיהוי בשדה

כשאתה בודק פרוטוקול:

```
[ש1] מהו מקור הרווח העיקרי המוצהר?
    │
    ├── עמלות שוק / הלוואות / marketplace / SaaS
    │   └── [ש2] האם ניתן לאמת on-chain / בדוחות חתומים?
    │         ├── כן → Revenue Engine (המשך לבדיקה כמותית)
    │         └── לא → "ידיעה פרטית" — חשוד, בקש קישורים
    │
    ├── Staking rewards
    │   └── [ש3] מאיפה ה-reward pool ממומן?
    │         ├── עמלות רשת / inflation קבועה ידועה → מקובל
    │         ├── הפקדות משתמשים → Ponzi structure
    │         └── "Trading bot / arbitrage סודי" → דגל אדום
    │
    ├── Token appreciation
    │   └── [ש4] האם הטוקן מחזיק שווי מחוץ למערכת?
    │         ├── utility אמיתי בפרוטוקול אחר → ייתכן
    │         └── רק אצלנו → Reward Engine טהור
    │
    └── "זה מורכב" / "סודי" / "עדיין לא פורסם"
        └── ❌ צא
```

---

## 4. המבחן הכלכלי ב-2 שאלות

שאל את עצמך על הפרוטוקול:

### שאלה 1: "מי משלם?"
- מי האדם / הישות שמעביר כסף אל המערכת בתמורה לשירות?
- *לא* מי מפקיד. לא מי קונה טוקן. **מי משלם על שירות.**

אם אין תשובה ברורה → אין Revenue Engine.

### שאלה 2: "מה יקרה אם לא יגיעו משתמשים חדשים 90 יום?"

- אם התשובה: "המערכת תמשיך להתפקד באותה רמת תשואה מעמלות מסחר קיימות" → Revenue Engine.
- אם התשובה: "תהיה האטה בתשואות" → Hybrid (עדיין אפשרי).
- אם התשובה: "אי אפשר לחלק תשואות" → Reward Engine (Ponzi structure).

---

## 5. Hybrid Systems — איפה רוב הקריפטו

רוב הפרוטוקולים הם לא טהורים. הם מעורבים:
- **חלק Revenue** (עמלות אמיתיות)
- **חלק Reward** (inflation של הטוקן, subsidies, liquidity mining)

**זה לגיטימי — אם המערכת שקופה לגבי היחס.**

דוגמה:
```
Protocol X:
  Revenue (real fees):     $200K/month
  Token inflation subsidy: $150K/month
  Total "APY" paid out:    $350K/month

  Revenue share:   57%
  Subsidy share:   43%

  Subsidy runway:  18 months (based on current treasury)
```

**כלל מעשי:**
- Revenue share ≥ 70% → מערכת בריאה
- Revenue share 40-70% → בסיכון, צריך runway ברור
- Revenue share < 40% → Reward Engine בתחפושת

---

## 6. Case Study: איך SLH מסווגת את עצמה

כרגע (ליל 2026-04-20 ערב overhaul):

| מקור | סטטוס | תרומה ל-R_t |
|---|---|---|
| Academia (הקורס הזה) | מושק היום | 0% → 40% target |
| Marketplace 5% fee | LIVE (5 items) | <5% |
| @WEWORK bot subscriptions | LIVE | ~15% |
| Ambassador SaaS | ספק'ד | 0% → 10% |
| Primary ZVK sales | חלקי | ~10% |
| DEX fees (SLH) | עתידי | 0% |

**Revenue share כרגע:** נמוך מאוד (~10-15%)
**ETA ל-70%:** 6-9 חודשים, תלוי ב-Course #1 traction + Ambassador program

זה מצב Hybrid עם **הצהרה פומבית**. הסיבה שהמערכת לא מתפרקת עכשיו: **ה-Dynamic Yield לא הבטחה של מספר, אלא חלוקה של מה שיש.**
אם Revenue = $0 חודש מסוים → חלוקה = $0. Buffer נגזר מהפקדות קיימות בלי לפגוע בקרן.

זה לא מושלם. זה *הגון*.

---

## 7. Red Flag Combos (קטלניים במיוחד)

הצירופים הבאים = אזהרה כפולה:

| Combo | למה קטלני |
|---|---|
| Fixed APY + No Public Treasury | כסף הולך לאן-שהוא, לא יודעים מאיפה משולם |
| Deep Referral + Token Inflation | שכבה על שכבה של דילול |
| "Trading bot" + Concentrated Supply | האלגוריתם יכול "להפסיד" ל-wallets של המייסד |
| High APY + New Chain | אין Liquidity חיצונית לבחון |
| Lock-up periods + No Circuit Breaker | לכוד בלי יציאת חירום |

---

## 8. מה Dynamic Yield עושה אחרת

בניגוד ל-APY קבוע, Dynamic Yield **לא מבטיח מספר** — הוא מתאר **מנגנון**:

```
Yield_you = (balance_you / TVL_total) × (k × max(0, Revenue - Costs - Referrals))
```

תוצאות:
- Revenue עלה → Yield עלה (פרופורציונלי)
- Revenue ירד → Yield ירד (פרופורציונלי)
- Revenue = 0 → Yield = 0. **אין חוב חדש שנצבר.**
- Costs עלו → Yield ירד (כולם חולקים)

זה **הופך את המשתמשים לשותפים**, לא ללקוחות. כל משתמש יודע את הנוסחה, רואה את המספרים, ויכול לחזות על סמך ביצועי המערכת.

**המעבר ממוצר-הבטחה למוצר-שקיפות הוא כל הפואנטה של SLH.**

---

## 9. תרגול מודול

קח את 3 הפרוטוקולים הגדולים שאתה עוקב אחריהם. עבור עליהם:

```
Protocol A: ______________
  Source of revenue: _______________
  Verifiable? Y / N
  Revenue share estimate: ____%
  Classification: [ ] Revenue Engine [ ] Hybrid [ ] Reward Engine

Protocol B: ...
Protocol C: ...
```

לא צריך לעזוב פרוטוקולים שהם Hybrid. רק להבין את הסיווג ולחשוב על ה-runway.

---

## סיכום

- Revenue = כסף חיצוני תמורת שירות. **לא הפקדות, לא inflation.**
- Reward Engine טהור = Ponzi structure.
- רוב הקריפטו הוא Hybrid. זה בסדר אם שקוף.
- מבחן הזהב: "מה יקרה ללא משתמשים חדשים 90 יום?"
- SLH מסווגת כיום כ-Hybrid עם Revenue share נמוך ובתהליך גידול. גלוי.

**המודול הבא (בתשלום Pro):** המתמטיקה של Dynamic Yield — הנוסחאות המלאות, המחשבון האינטראקטיבי, ותרגולים מספריים.

[→ המשך למודול 3: The Formulas (Pro)](/academy/course-1-dynamic-yield/module-3.html)

---

*תרגיל בונוס: חפש את הפרוטוקול הגדול ביותר שאתה מחזיק. באיזה דגלי מודול 1 הוא נופל? מה ה-Revenue share שלך מעריך? שלח בקהילת הקורס.*
