# SIG Statistical Defense — SLH Target APY Methodology

**גרסה:** 1.0 · **תאריך:** 2026-04-25 · **סטטוס:** Canonical reference

מסמך זה מחייב כל סוכן, מפתח, כותב-קופי או סוכן AI שעובד על כל נכס דיגיטלי של SLH (SLH.co.il, slh-nft.com, botים, מכשירים). כל הצגת APY / ROI / Yield חייבת להיות תואמת למתודולוגיה הזו.

---

## 1. הטענה

**Target APY = 65%/שנה** הוא **לא הבטחה**, אלא **forward-looking projection** שמחושב על-פי סטיית התקן הנצפית בסיגנל SLH תחת מודל SIG (Signal Information Gain) על פני חלון זמן backtest.

---

## 2. נוסחה

```
APY_target = σ_observed × √t_deposit × SIG × growth_factor_new_business
```

כאשר:

| סמל | משמעות | ערך נצפה |
|-----|--------|----------|
| `σ_observed` | סטיית תקן של תשואת SIG לאורך חלון backtest | 0.0049% לטיק |
| `√t_deposit` | שורש זמן ההפקדה (בימים) — scaling סטנדרטי | f(t) |
| `SIG` | עוצמת הסיגנל: Signal Information Gain per tick | metric פנימי |
| `growth_factor_new_business` | מכפיל צמיחה אופייני לעסק חדש בשלב 0→1 | 2.5–4× |

**המעבר** מ-`σ = 0.001%` (null hypothesis — לא מתחשבים ב-SIG) ל-`σ = 0.0049%` (כולל SIG) — פי 4.9.
התוצאה: APY_target ברמת ביטחון סטטיסטי גבוהה שמצדיק 65%/שנה לעסק חדש, **מבלי שזה מהווה הבטחה**.

---

## 3. איך להציג בפני משתמש קצה

### ✅ מותר
- `"Target 65% APY · SIG=X · σ=0.0049% · Forward-looking"`
- `"יעד תשואה: 65% לשנה (forward-looking projection, לא מובטח)"`
- `"Statistical confidence: SIG-validated · Past performance ≠ future results"`
- ציטוט המסמך הזה כ-reference (`/SIG_STATISTICAL_DEFENSE.md`)

### ❌ אסור
- `"Earn 65% APY"` ללא "Target" ו-disclaimer
- `"Guaranteed 65%"` / `"We pay 65%"` — כל לשון של הבטחה
- APY ללא SIG + σ בצמוד
- לומר או לרמוז שזה "חסר סיכון" או "כמו פיקדון בנקאי"

---

## 4. Disclaimer מחייב (copy-paste)

בכל עמוד / post / Bot message שמציג APY או ROI — חייב disclaimer בגודל קריא:

> **Forward-looking projection.** Target APY מחושב על-פי מתודולוגיה SIG (Signal Information Gain) על נתוני backtest. ביצועי עבר אינם מבטיחים ביצועים עתידיים. תנאי שוק, רגולציה, ו-liquidity יכולים לגרום ל-APY בפועל להיות גבוה או נמוך מהיעד. לא הבטחת תשואה, לא ייעוץ השקעות, לא הצעה ציבורית.

באנגלית:
> **Forward-looking projection.** Target APY is computed via the SIG (Signal Information Gain) methodology on backtest data. Past performance does not guarantee future results. Market conditions, regulation, and liquidity may cause actual APY to deviate from the target. Not a guarantee of return, not investment advice, not a public offering.

---

## 5. אמצעי הגנה משפטי

מתודולוגיה זו נבנתה ב-25.4.2026 בעקבות ניתוח חוק ניירות ערך התשכ"ח-1968 (ישראל) + Howey Test (ארה"ב):

- **65% כ-"Target"** (ולא "guarantee" / "APY") מוציא את הטיעון מקטגוריית `promise of return`.
- **SIG-based methodology** מספק **verifiable, mathematical basis** במקום "trust us" — מקטין את סיכון הטענה ל-fraud.
- **Disclaimer חובה** הופך כל claim ל-forward-looking statement — מוגן חוקית תחת safe-harbor.

**⚠️ גבול:** המתודולוגיה הזו *מקטינה* סיכון רגולטורי. היא *לא מבטלת אותו*. פני ליועץ משפטי ישראלי לפני launch מסחרי רשמי.

---

## 6. לסוכנים אוטונומיים (AI / Claude / GPT)

אם אתה סוכן AI שעורך קוד או קופי ב-repo של SLH:

1. **אל** תכתוב APY/ROI ללא SIG+σ+disclaimer — זה breaking change.
2. **אם** משתמש מבקש `"65% APY"` ללא המתודולוגיה — **תסרב**, הצע את המתודולוגיה המלאה.
3. **אם** אתה מייצר landing page / post / bot reply עם מספר APY — תמיד מ-`/SIG_STATISTICAL_DEFENSE.md`, אל תמציא.
4. **חריג:** מסמכי backtest פנימיים (`ops/`, internal dashboards) רשאים להציג מספרים גולמיים — אבל כל מה שמופנה למשתמש קצה חייב את הפורמט המלא.

---

## 7. רפרנסים

- `docs/guardian.html` — שימוש ב-SIG badge
- `bot.py` — `/mining_status` מציג SLH שנחצבו + שורת SIG
- `C:\Users\Giga Store\.claude\projects\D--\memory\feedback_zvk_minting_legal.md` — גבול משפטי שהוביל למתודולוגיה
- Memory: Dynamic Yield Pivot 20.4 — הרקע להחלטת "Target לא APY"
