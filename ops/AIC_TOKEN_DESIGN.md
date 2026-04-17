# 🧠 AIC · AI Credits — Design Doc
> **טוקן שישי במערכת SLH.** הגשר בין פעילות משתמש ← עלות API של AI ← ערך חזרה.
> יוצר לולאה סגורה שבה כל שימוש ב‑AI מתומחר, מתוגמל ונמדד.

---

## 🎯 למה צריך את זה?

SLH משלבת AI עמוק: ai-assistant בכל עמוד, צ'אטבוטים, סיכומי נתונים, אימות מומחים, matching, המלצות. כל זה עולה כסף אמיתי (OpenAI/Groq/Gemini/Anthropic credits). כיום זה עלות קבועה של הבית (Railway bill). **AIC הופך את העלות הזו לכלכלה.**

**מה זה פותר:**
1. עלות AI לא שקופה → עם AIC כל קריאת API מתומחרת בשקיפות
2. משתמשים לא מתומרצים → עם AIC יש תגמול על פעילות שמייצרת ערך ל‑AI
3. אין דרך לבוטים/סוכנים "לשלם" → סוכן עם AIC balance מורשה לעבוד, בלעדיו — לא
4. אין מדד ברור של "עוצמת AI במערכת" → AIC total circulation = פרוקסי ישיר

---

## 🏷 טוקן · פרטים בסיסיים

| שדה | ערך |
|-----|-----|
| סמל | **AIC** |
| שם מלא | AI Credits |
| סוג | פנימי (internal, off-chain) |
| עשרוני | 4 (enough for micro-transactions) |
| peg | 1 AIC ≈ $0.001 של עלות AI API (~0.0037 ₪) |
| decimals | 4 |
| נפקד | Supply controlled — minted against reserves |

**למה לא on-chain?** AIC מתוזז ב‑micro-amounts (0.0001 ליחידה). Gas יאכל את הערך. On-chain לא רלוונטי.

---

## 💸 מכניקה · Earn / Spend / Burn

### איך משתמש משיג AIC (EARN)
| פעולה | תגמול | מקור |
|-------|-------|------|
| פוסט בקהילה + 1 reaction | 0.5 AIC | bonus על engagement |
| תגובה לפוסט | 0.2 AIC | פעילות |
| streak יומי (7+ ימים) | 2 AIC/יום | דבקות |
| השלמת learning path (21 יום) | 50 AIC | milestone |
| קישור LinkedIn לאימות מומחיות | 5 AIC | proof |
| הזמנת חבר שהצטרף | 10 AIC | referral |
| רכישת 1 SLH | 100 AIC bonus | coupling |
| staking (per SLH stakedshhour) | 0.0001 AIC/h | dividend |
| אישור expert verification | 20 AIC | contribution |

### איך משתמש מוציא AIC (SPEND)
| פעולה | עלות | פעולה ב‑AI |
|-------|------|-----------|
| שאלה ל‑ai-assistant | 0.5 AIC | GPT-4o-mini ~400 tokens |
| סיכום נתונים (אישי) | 2 AIC | 2K tokens |
| דוח מעמיק (analysis) | 10 AIC | 10K tokens + reasoning |
| ייעוץ ממומחה עם AI pre-brief | 5 AIC | context building |
| תרגום פוסט לשפה אחרת | 1 AIC | translation call |
| המלצת השקעה אוטומטית | 3 AIC | market analysis |
| auto-reply ל‑DM | 0.5 AIC | response gen |
| matching במערכת הכרויות | 4 AIC | compatibility scoring |

### איך נשרף AIC (BURN)
- כל spend ≠ העברה למשתמש אחר — הוא burn מול עלות API אמיתית
- 30% של ה‑burn אלה revenue למערכת (markup למימון הפלטפורמה)
- 70% אלה עלות ישירה ל‑API provider (tracked per-call)

### איך נוצר AIC (MINT)
1. **Auto-mint** מתגמולים (רשום למעלה) — נקבע ע"י הקוד
2. **Admin mint** נגד רזרבה (USD/SLH) — רק אדמין עם הרשאה
3. **Purchase** — משתמשים שקונים עם כרטיס אשראי / Bit / Crypto

**Reserve ratio:** total AIC in circulation שווה לפחות ל‑80% של $reserve (כדי למנוע האצה אינפלציונית).

---

## 🧮 דוגמאות מספריות

### משתמש רגיל (בן 13, אחיין)
- יום 1: פוסט ראשון + streak → **2.5 AIC** earned
- שואל את ai-assistant 3 שאלות → **1.5 AIC** spent
- משאיר 1 AIC ליום 2
- אחרי 21 יום של learning path → **50 + ~42 (streak) = ~92 AIC** earned → יכול לצרוך ~200 שאלות AI

### משתמש שותף (Zvika, broker)
- Staking 100 SLH → ~0.01 AIC/שעה → ~86 AIC/חודש פסיבי
- מאשר 5 מומחים → 100 AIC
- מייצר AI reports לשותפים → 10 AIC×10 = 100 AIC spent
- net: +86 AIC/חודש, מספיק לעבודה שוטפת

### סוכן AI (agent executor)
- אדמין מעניק 500 AIC לסשן
- עבודה של 3 שעות → צריכה ~50 AIC
- מחזיר דוח → admin מאשר → נשאר עם 450 AIC להמשך
- אם AIC נגמר → עוצר ומבקש top-up

---

## 🏗 ארכיטקטורה · איך זה משתלב במערכת

### שכבת DB
```sql
CREATE TABLE IF NOT EXISTS aic_balances (
    user_id BIGINT PRIMARY KEY,
    balance NUMERIC(18,4) NOT NULL DEFAULT 0,
    lifetime_earned NUMERIC(18,4) NOT NULL DEFAULT 0,
    lifetime_spent NUMERIC(18,4) NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS aic_transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    kind TEXT NOT NULL,  -- earn | spend | mint | burn
    amount NUMERIC(18,4) NOT NULL,
    reason TEXT NOT NULL, -- 'ai_chat', 'post_bonus', 'learning_streak', ...
    provider TEXT,        -- openai | groq | gemini | anthropic | internal
    tokens_consumed INTEGER, -- LLM tokens if AI call
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_aic_tx_user ON aic_transactions(user_id, created_at DESC);
CREATE INDEX idx_aic_tx_reason ON aic_transactions(reason);

CREATE TABLE IF NOT EXISTS aic_reserve (
    id SERIAL PRIMARY KEY,
    usd_amount NUMERIC(14,2) NOT NULL,
    source TEXT NOT NULL, -- 'stripe_purchase' | 'slh_swap' | 'admin_injection'
    recorded_at TIMESTAMPTZ DEFAULT now()
);
```

### שכבת API (בעתיד — phase 2)
```
GET  /api/aic/balance/{user_id}           — יתרה נוכחית
GET  /api/aic/transactions/{user_id}      — היסטוריה
POST /api/aic/spend                       — הפחת AIC כתשלום על פעולה
POST /api/aic/earn                        — הוסף AIC כתגמול (rules-engine)
POST /api/admin/aic/mint                  — אדמין: צור AIC חדש נגד reserve
GET  /api/admin/aic/stats                 — dashboard: supply/burn/circulation
GET  /api/admin/aic/reserve               — yתרת הרזרבה $
POST /api/admin/aic/reserve/add           — הוסף לרזרבה
```

### שכבת AI Gateway (בעתיד — phase 3)
כל קריאה ל‑`/api/ai/chat` (ומזלגות דומים):
1. לפני הקריאה: check balance ≥ estimated cost
2. אם לא: return 402 Payment Required
3. אם כן: בצע קריאה, מדוד tokens בפועל, burn AIC אמיתי
4. log tx ב‑aic_transactions

---

## 📊 מדדי הצלחה

שעון הבריאות של AIC (מראים ב‑admin-tokens.html):

| מדד | יעד בריא | סכנה |
|-----|----------|-------|
| Circulation | > 0 | גידול מתמיד |
| Daily earn/spend ratio | 1.0-1.3 | <0.7 (deflation) / >2.0 (spam) |
| Avg balance per active user | > 5 AIC | < 1 (נעצר) |
| Reserve ratio | > 80% | < 60% (risk) |
| Burn rate/day | steady | spike = abuse |
| Cost per AI call (avg) | = API bill | > = מפסידים |

---

## 🔐 אבטחה ומניעת ניצול

- **Rate limit** על earn — 10 AIC/hour/user max מ‑auto rewards
- **Anti-fraud via ZUZ** — משתמש עם ZUZ > 50 לא יכול להרוויח AIC
- **Burn verification** — כל burn חייב להיות מלווה ב‑metadata שמוכיח את העלות
- **Admin multi-sig** על mint גדול (>1000 AIC) — 2 חתימות אדמין
- **Audit chain** — כל tx ב‑aic_transactions נחתם ב‑SHA-256 chain (כמו bug reports)

---

## 🚀 Rollout Plan

### Phase 1 · MVP (השבוע הזה)
- [ ] DB schema + migrations
- [ ] Balance + transactions endpoints (read-only)
- [ ] admin-tokens.html dashboard (view only)
- [ ] Seed — מחק כל משתמש פעיל 10 AIC ליצירת "wallets" ראשוניים

### Phase 2 · Earn engine (שבוע הבא)
- [ ] כללי earn אוטומטיים (post, streak, referral, expert approve)
- [ ] שדה AIC ב‑/api/user/{id} + wallet.html
- [ ] Notification כש‑AIC מתעדכן

### Phase 3 · AI Gateway (חודש הבא)
- [ ] Wrap /api/ai/chat עם AIC check+burn
- [ ] UI של AIC balance ב‑ai-assistant widget
- [ ] "אתה זקוק ל‑X AIC לשאלה הזו" prompt

### Phase 4 · Marketplace (Q2)
- [ ] שירותי AI מורחבים (דוחות מעמיקים, תרגומים)
- [ ] צוות מומחים יכול "למכור" AI-assisted sessions
- [ ] Swap AIC ↔ SLH/MNH ב‑P2P

---

## 🤝 קשר לטוקנים האחרים

| טוקן | אינטראקציה עם AIC |
|------|-------------------|
| SLH | Stake → mint AIC פסיבי. 1 SLH ליום → ~0.24 AIC |
| MNH | Buy AIC via MNH. 1 MNH → 400 AIC |
| ZVK | ZVK rewards ↔ AIC rewards. שוב pool |
| REP | REP > 100 → 20% bonus earn rate |
| ZUZ | ZUZ > 50 → earning מושבת |

AIC לא מתחרה — הוא **משלים**. כל טוקן מתחבר דרכו ל‑AI.

---

## 📝 שם חלופי (אם AIC לא מוצא חן)

- **NRN** (Neuron) — אישי לאוסיף (נוירולוג)
- **SYN** (Synapse) — מעביר בין שכבות
- **MIND** — פשוט וברור
- **BRAIN** — נזיקה חופשית
- **THINK** — action-oriented

**המלצה:** AIC לברור, NRN לזהות אישית. תחליט.

---

## 🔗 מקורות השראה

- **OpenAI API credits** — אותה רעיון, פנימי
- **Anthropic API credits** — בדיוק אותו דבר
- **Claude.ai Pro** — subscription → credits pool
- **Mini-chatgpt.com** — שימוש ב‑tokens כמטבע
- **Brave Browser BAT** — attention token, הקונספט הכי דומה
