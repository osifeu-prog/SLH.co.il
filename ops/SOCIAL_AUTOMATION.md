# 📢 SLH · Social Auto-Broadcast Setup
> **RSS → כל רשת חברתית · חינמי.** פוסט בפיד הקהילה → אוטומטית נשלח לטוויטר/LinkedIn/פייסבוק/וכו'.

---

## 🎯 איך זה עובד

```
אתה מפרסם פוסט ב-community.html
          ↓
/api/community/rss (RSS 2.0, עדכון מיידי)
          ↓
IFTTT/Zapier/Buffer reads RSS every 15 min
          ↓
פוסט אוטומטי ב: Twitter · LinkedIn · Facebook · Instagram · Telegram channel · Reddit
```

**ה‑RSS URL:**
```
https://slh-api-production.up.railway.app/api/community/rss
```

---

## ⚡ IFTTT · המסלול הכי מהיר (חינמי · 2 applets)

### שלב 1 · הרשמה
1. פתח [ifttt.com](https://ifttt.com) → Sign up (חינם)
2. Connect accounts לרשתות שלך (Twitter/LinkedIn/Facebook/etc.)

### שלב 2 · יצירת Applet
1. **Create** → **If This** → **RSS Feed**
2. Choose trigger: **"New feed item"**
3. Feed URL:
   ```
   https://slh-api-production.up.railway.app/api/community/rss
   ```
4. **Then That** → בחר רשת (Twitter / LinkedIn / Facebook Page)
5. Tweet / Post template:
   ```
   🚀 {{EntryTitle}}

   {{EntryUrl}}

   #SLH #Crypto #Israel
   ```
6. **Create action** → שמור

### Applets מומלצות:
1. **RSS → Twitter** (הכי פופולרי · טקסט חופשי)
2. **RSS → LinkedIn** (יותר מקצועי · מגיע לקהל יזמים)

**IFTTT חינמי = עד 2 applets פעילים.** לרשת שלישית → Zapier.

---

## 🔄 Zapier · אם צריך יותר מ‑2 רשתות ($19.99/חודש)

1. [zapier.com](https://zapier.com) → Create Zap
2. **Trigger:** "RSS by Zapier" → "New Item in Feed" → ה‑URL של RSS
3. **Action 1:** Twitter → Create Tweet
4. **Action 2:** LinkedIn → Create Share
5. **Action 3:** Facebook Pages → Create Page Post
6. **Action 4:** Instagram → Publish (דורש business account)
7. **Action 5:** Discord / Slack / Telegram channel

**Zapier Starter = 750 tasks/month.** מספיק לפוסט יומי ב‑5 רשתות.

---

## 🆓 Buffer · נוח לבחירת טיימינג (free tier · 3 channels, 10 posts/month)

1. [buffer.com](https://buffer.com) → signup
2. Connect channels
3. **Automation → IFTTT integration** או URL-based scheduling
4. BUFFER לא קורא RSS אוטומטית — צריך לחבר דרך IFTTT (RSS → Buffer)

---

## 🔧 ידני · Manual broadcast endpoint (כבר קיים)

אם תרצה להעיף פוסט לכל הרשתות *מיידית*, יש כבר endpoint פנימי:
```bash
curl -X POST https://slh-api-production.up.railway.app/api/community/posts \
  -H "Content-Type: application/json" \
  -d '{"username":"SLH_System","telegram_id":"224223270","text":"...","category":"updates"}'
```

כל IFTTT applet יזהה את הפוסט החדש תוך 15 דקות ויפרוס לרשתות.

---

## 📋 רשימת רשתות חברתיות · מה צריך ממך

לכל רשת שאתה רוצה לאוטומט, ספק:

| רשת | מה צריך | מי מחזיק? |
|-----|---------|-----------|
| Twitter/X | @handle שלך + IFTTT OAuth | אתה |
| LinkedIn | personal profile + IFTTT OAuth | אתה |
| Facebook | Page (לא profile) + FB page access | אתה |
| Instagram | Business account (לא personal) | אתה |
| Telegram channel | `t.me/slhniffty` · bot token posting | יצרת כבר ✓ |
| Reddit | /r/slh subreddit + OAuth | צריך subreddit |
| Discord | server + webhook URL | אם יש |
| Mastodon | server + API key | אם יש |

**תגיד לי בדיוק באילו רשתות אתה רוצה להתחיל + מה שמות הפרופילים שלך** ואני אכין template exact ל‑IFTTT לכל אחת.

---

## 🎨 Template פוסט מותאם לSLH

עבור IFTTT/Zapier, השתמש ב‑template הזה:

```
🚀 {{EntryTitle}}

🔗 {{EntryUrl}}

💎 SLH Spark — Israel's crypto ecosystem
• 25 Telegram bots
• BSC + TON payments auto-verified
• AI Credits economy
• 6 tokens: SLH, MNH, ZVK, REP, ZUZ, AIC

#SLH #Crypto #Israel #DeFi #Web3
```

אפשר שונה לכל רשת (LinkedIn יותר מקצועי, Twitter יותר קצר).

---

## 📊 בדיקת תקינות

לאחר ההקמה:
1. פרסם פוסט בדיקה ב-community.html: "🧪 Test automation"
2. תוך 15 דק' → בדוק שהוא מופיע בכל רשת
3. אם לא → IFTTT dashboard → Log → מחפש error
4. תגיד לי מה השגיאה ואעזור לפענח

---

## 🔐 אבטחה

- ❌ אל תשתף את ה‑API keys של Zapier/IFTTT
- ✅ ה‑RSS ציבורי (אין בעיה — אין secrets)
- ✅ תוכן הפוסטים מסוננים (SLH_System posts = ordained broadcasts)
- ⚠️ כל משתמש יכול לפרסם בקהילה = יופיע ב‑RSS. אם תרצה רק SLH_System → נסנן.

**רוצה סינון?** תגיד ואני אשנה את ה‑RSS להחזיר רק פוסטים מ‑SLH_System (broadcasts רשמיים בלבד).
