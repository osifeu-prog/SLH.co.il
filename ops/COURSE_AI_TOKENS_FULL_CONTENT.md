# קורס: איך מחושבים טוקנים ב-AI?
**מספר NFT Card:** #001
**מחיר:** ₪149 (השקה)
**גרסה:** 1.0 · 27 באפריל 2026

---

## פתיחה — למה זה חשוב

כל מי שעובד עם AI משלם בכל פעולה. אם לא יודעים איך נוצרת העלות, הופכים מהר לבזבזנים. הקורס הזה מלמד אותך לחשוב כמו המודל - לראות את העולם דרך טוקנים, ולחתוך את העלות שלך ב-50-80% בלי לאבד איכות.

מתאים ל: מפתחים שבונים אפליקציות AI, יזמים שמשלמים על API, אנשי מוצר שמתכננים מערכת AI.

---

## פרק 1: מה זה בכלל טוקן? (~12 דקות)

המודל לא קורא מילים. הוא קורא **נתחים של טקסט** (sub-words) שנקראים טוקנים. רוב המודלים משתמשים בטכניקה שנקראת **BPE — Byte Pair Encoding**: היא מפרקת טקסט ליחידות קטנות שחוזרות הרבה.

**מספרים מעשיים:**
- באנגלית: 1 טוקן ≈ 4 תווים, או ≈ 0.75 מילים
- 1,000 טוקנים ≈ 750 מילים
- בעברית: בגלל שהטוקנייזרים אומנו על אנגלית בעיקר, מילה ממוצעת בעברית = 2-4 טוקנים
- "והילדים" עשוי להתפרק ל: "ו" + "ה" + "ילד" + "ים" = 4 טוקנים. "Children" = 1 טוקן

**משמעות:** אותו תוכן בעברית עולה פי 2-3 מאשר באנגלית. אם זה לא חיוני, כתוב prompts באנגלית גם אם המשתמש מקבל תשובה בעברית.

---

## פרק 2: טוקני קלט (Input Tokens) (~22 דקות)

כל מה שאתה שולח למודל בכל פעם:

1. **ההודעה הנוכחית של המשתמש**
2. **כל ההיסטוריה של השיחה** — כן, נשלחת כולה בכל פעם!
3. **System prompt** — ההוראות הקבועות שאתה נותן למודל
4. **מסמכים מצורפים, RAG context, או נתונים שאתה דוחף לתוך הפרומפט**
5. **הגדרת הכלים (Tool definitions / Function schemas)** — אם אתה משתמש ב-function calling, ה-JSON schema של הכלים נספר כטוקנים בכל פנייה

**טריק החיסכון:** את ה-system prompt הקבוע + הגדרת הכלים → שים ב-Cache. אנתרופיק וגוגל נותנים עד 90% הנחה על תוכן שחוזר על עצמו.

**Python דוגמה:**
```python
import tiktoken
enc = tiktoken.encoding_for_model("gpt-4o")
prompt = "אני רוצה לבנות מערכת..."
print(f"Token count: {len(enc.encode(prompt))}")
```

---

## פרק 3: טוקני פלט (Output Tokens) (~18 דקות)

אלה הטוקנים שהמודל מייצר. **הם יקרים פי 3-8 מטוקני קלט.**

| מודל | קלט | פלט | יחס |
|------|-----|------|-----|
| GPT-5.4 | $2.50/M | $15/M | 6× |
| Claude Opus 4.6 | $5/M | $25/M | 5× |
| Claude Sonnet 4.6 | $3/M | $15/M | 5× |
| Gemini 2.5 Pro | $2.50/M | $20/M | 8× |

**משמעות אסטרטגית:**
- אל תבקש "תכתוב לי מאמר של 5,000 מילים" אם אתה לא צריך
- בקש סיכום קצר תחילה, ואז להרחיב רק את החלקים החשובים
- השתמש ב-`max_tokens` כדי להגביל בכוח את אורך הפלט

**טוקני "מחשבה" (Reasoning Tokens):**
במודלים חדשים כמו o1 או Claude Extended Thinking, יש טוקנים פנימיים של "חשיבה" שלא נראים בפלט הסופי **אבל אתה משלם עליהם כעל פלט.** זה יכול להיות פי 5-10 יותר ממה שראית. תזהיר את עצמך.

---

## פרק 4: היסטוריית שיחה (~16 דקות)

זה החלק שתופס את רוב היזמים בהפתעה. בכל הודעה חדשה, **כל ההיסטוריה נשלחת שוב**:

| הודעה | טוקני קלט |
|-------|-----------|
| הודעה 1 | 100 |
| הודעה 2 | 100 (מקור) + 100 (היסטוריה) = 200 |
| הודעה 3 | 100 + 200 = 300 |
| הודעה 4 | 100 + 300 = 400 |
| הודעה 10 | ~5,500 |
| הודעה 20 | ~21,000 |

**זו צמיחה ריבועית, לא ליניארית.** שיחה של 20 הודעות תעלה פי 13 משיחה של הודעה אחת × 20.

**מה לעשות:**
1. **סיכום אוטומטי**: אחרי X הודעות, סכם את ההיסטוריה לכמה משפטים והחלף אותה
2. **קיצוץ אגרסיבי**: שמור רק את N ההודעות האחרונות
3. **Cache the prefix**: אם יש system prompt קבוע, ה-cache יחסוך לך את החלק הזה

---

## פרק 5: חלון הקשר (Context Window) (~24 דקות)

זה המספר המקסימלי של טוקנים שהמודל יכול לעבד בבת אחת.

| מודל | חלון הקשר |
|------|-----------|
| GPT-5.4 | 272K (extended: 1M) |
| Claude Opus 4.6 | 1M |
| Claude Sonnet 4.6 | 1M |
| Gemini 2.5 Pro | 1M |
| GPT-3.5 (legacy) | 16K |

**אם חורגים מהגבול:**
- חלק מהמודלים פשוט יזרקו את ההודעות הישנות
- חלק יזרקו שגיאה
- חלק יסכם אוטומטית (פחות מומלץ - הם מקצרים את החלקים הלא נכונים)

**יותר חלון = יותר עלות.** תוכל לשים 1M טוקנים בפרומפט אחד? כן. זה יעלה ~$2-5? גם כן.

---

## פרק 6: שפות שונות (~14 דקות)

| שפה | טוקנים למילה ממוצעת |
|-----|---------------------|
| אנגלית | 0.75 |
| ספרדית | 1.2 |
| עברית | 2.5 |
| ערבית | 2.8 |
| סינית | 0.5 (כל תו = יחידה) |
| יפנית | 0.6 |

**אסטרטגיות לעברית:**
1. **System prompt באנגלית, תשובה לפי בקשה**: "Respond in Hebrew"
2. **Few-shot examples בעברית** רק כשצריך
3. **שימוש ב-models שאומנו על עברית**: Claude מצוין, GPT-4o טוב, Gemini פחות

---

## פרק 7: Prompt Caching (~28 דקות)

ההפתעה הגדולה של 2024-2026: הנחה של 50-90% על תוכן שחוזר על עצמו.

| חברה | הנחה | מינימום | תוקף Cache |
|------|------|---------|------------|
| Anthropic | 90% | 1,024 טוקנים | 5 דקות (auto-extends) |
| Google | 90% | 32,768 טוקנים | 1 שעה (configurable) |
| OpenAI | 50% | 1,024 טוקנים | 5-10 דקות |

**מתי זה עובד:**
- מערכת RAG עם אותו corpus
- Chat application עם system prompt קבוע
- API שמבצע אותה פעולה עם נתונים שונים

**Anthropic example (Python):**
```python
from anthropic import Anthropic
client = Anthropic()
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are a helpful Hebrew tutor...",
            "cache_control": {"type": "ephemeral"}  # ← THIS
        }
    ],
    messages=[{"role": "user", "content": "שאלה ראשונה"}],
)
```

**חיסכון אמיתי:** במערכת SLH, בוט עם system prompt של ~3,000 טוקנים שעונה ל-100 שיחות ביום: בלי cache = $0.45/יום. עם cache = $0.05/יום. **חיסכון של 90%.**

---

## פרק 8: tiktoken — מחשב טוקנים בפועל (~32 דקות)

**התקנה:**
```bash
pip install tiktoken
```

**שימוש בסיסי:**
```python
import tiktoken

# Per model
enc_gpt5 = tiktoken.encoding_for_model("gpt-4o")  # uses o200k_base
enc_gpt4 = tiktoken.encoding_for_model("gpt-4")   # uses cl100k_base

text = "Hello world"
print(len(enc_gpt5.encode(text)))  # 2 tokens

text_he = "שלום עולם"
print(len(enc_gpt5.encode(text_he)))  # 6 tokens (פי 3!)
```

**מחשב עלות מלא:**
```python
def estimate_cost(prompt: str, expected_output_tokens: int, model: str = "gpt-4o"):
    enc = tiktoken.encoding_for_model(model)
    input_tokens = len(enc.encode(prompt))
    PRICING = {
        "gpt-4o": (2.50, 15.00),       # per 1M tokens (input, output)
        "claude-opus-4-6": (5.00, 25.00),
    }
    in_price, out_price = PRICING.get(model, (3.0, 15.0))
    cost_usd = (input_tokens / 1_000_000) * in_price + (expected_output_tokens / 1_000_000) * out_price
    return {
        "input_tokens": input_tokens,
        "expected_output_tokens": expected_output_tokens,
        "estimated_cost_usd": round(cost_usd, 6),
        "estimated_cost_ils": round(cost_usd * 3.7, 4),
    }

print(estimate_cost("שאלה ארוכה...", 500))
```

**ל-Claude / Anthropic:** אין tiktoken, יש tokenizer של אנתרופיק. Estimate מהיר: ≈ tiktoken × 1.1.

---

## פרק 9: בנייה של AI App חסכוני — Case Study SLH (~36 דקות)

איך מערכת SLH חוסכת 70% מעלות AI:

### לפני האופטימיזציה (חודש 1):
- 25 בוטים, כל אחד שולח full system prompt בכל הודעה
- אין caching
- שיחות לא מסוכמות, היסטוריה מצטברת
- כל בוט מחזיר response באורך מלא
- **עלות: $850/חודש**

### אחרי האופטימיזציה (חודש 3):
1. **System prompt משותף** עם cache_control (Anthropic)
2. **Auto-summarization** של היסטוריה אחרי 10 הודעות
3. **max_tokens=300** ברירת מחדל (אפשר להאריך באקסטרא)
4. **JSON compact**: `json.dumps(data, separators=(',', ':'))` חוסך 10-20% מהמשקל
5. **Tool definitions קבועות → ב-cache**
6. **Routing חכם**: שאלות פשוטות → Haiku ($0.25/M). מורכבות → Opus ($5/M)

**עלות אחרי: $260/חודש. חיסכון של 70%.**

### החלק האסטרטגי
המהלך הכי חזק שעשינו: **Smart routing**. במקום לשלוח הכל ל-Opus, יצרנו classifier זול שמחליט:
- 70% מהשאלות → Haiku
- 25% → Sonnet
- 5% → Opus (רק שאלות באמת מורכבות)

---

## נספח א': Quick Reference Card

הדפס ושמור על השולחן:

```
טוקנים מחשבון מהיר:
- אנגלית:  1 מילה ≈ 0.75 טוקן
- עברית:   1 מילה ≈ 2.5 טוקן
- קוד:     שורה ≈ 5-15 טוקנים
- JSON:    דחוס יותר טוב ב-15%

מחיר ($/1M tokens):
                Input   Output
GPT-5.4:        2.50    15.00
GPT-5 Mini:     0.15    0.60
Claude Opus 4.6: 5.00    25.00
Claude Sonnet:  3.00    15.00
Claude Haiku:   0.25    1.25
Gemini 2.5 Pro: 2.50    20.00

Cache savings:
- Anthropic:  90% off
- Google:     90% off
- OpenAI:     50% off

חוקי אצבע:
- Output יקר פי 5-8 מ-Input
- היסטוריית שיחה גדלה ריבועית
- עברית עולה פי 2.5 מאנגלית
- Cache תמיד אם > 1024 טוקנים חוזרים
```

---

## נספח ב': כלי חישוב אונליין

- https://platform.openai.com/tokenizer (OpenAI)
- https://anthropic.com/tokenizer (Claude)
- https://huggingface.co/spaces/Xenova/the-tokenizer-playground (כל המודלים)

---

**סוף הקורס.** רוצה לחשב על system prompt ספציפי שלך? פנה ב-Telegram: @osifeu_prog
