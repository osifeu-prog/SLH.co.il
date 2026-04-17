# 🔄 n8n · Open-Source Auto-Broadcast (free forever)
> **חלופה ל‑IFTTT · ללא CC · רץ על Railway או מחשב מקומי · 30+ שירותים.**

---

## 🎯 מה זה n8n

- Open-source workflow automation · MIT license
- UI ויזואלי (nodes + connections · כמו IFTTT אבל יפה יותר)
- 30+ integrations מובנות: Twitter, LinkedIn, Facebook, Instagram, Telegram, Discord, RSS, Email, Webhooks, WordPress, Reddit, TikTok...
- רץ self-hosted → **אפס תלות ב‑IFTTT/Zapier**

---

## 🚀 Setup עם docker-compose (20 דק')

### אופציה 1 · הוסף ל‑SLH docker-compose.yml

```yaml
# הוסף בסוף services:
  n8n:
    image: n8nio/n8n:latest
    container_name: slh-n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      N8N_HOST: localhost
      N8N_PORT: 5678
      N8N_PROTOCOL: http
      NODE_ENV: production
      WEBHOOK_URL: http://localhost:5678/
      GENERIC_TIMEZONE: Asia/Jerusalem
      N8N_BASIC_AUTH_ACTIVE: "true"
      N8N_BASIC_AUTH_USER: osif
      N8N_BASIC_AUTH_PASSWORD: ${N8N_PASSWORD}
    volumes:
      - n8n-data:/home/node/.n8n

# בסוף volumes:
volumes:
  n8n-data:
```

### אופציה 2 · הרץ ישירות (ללא docker)

```powershell
# Windows
npm install n8n -g
n8n start
# פתח http://localhost:5678
```

---

## 🎨 הגדרת Workflow ראשון · RSS → Twitter

1. http://localhost:5678 → login (osif + הסיסמה שתגדיר)
2. **New Workflow** → בחר trigger: **RSS Feed Trigger**
   - URL: `https://slh-api-production.up.railway.app/api/community/rss`
   - Polling: `Every 15 minutes`
3. הוסף node: **Twitter** → Action: `Post Tweet`
4. אישור OAuth עם חשבון Twitter שלך (פעם אחת)
5. בגוף הפוסט:
   ```
   🚀 {{$json.title}}

   {{$json.link}}

   #SLH #Crypto #Israel
   ```
6. **Save + Activate**

---

## 📡 Integrations מומלצות ל‑SLH

| Node | מה עושה | רמת קושי |
|------|---------|----------|
| **RSS Feed Trigger** | קורא את `/api/community/rss` | קל |
| **Twitter** | פוסט אוטומטי לטוויטר | קל |
| **LinkedIn** | פוסט לפרופיל או לדף חברה | קל |
| **Facebook Pages** | פוסט לעמוד facebook | קל |
| **Telegram** | שלח לערוץ `@slhniffty` | קל |
| **Discord Webhook** | הודעה לשרת Discord | קל |
| **Reddit** | פוסט לsubreddit | בינוני (OAuth) |
| **Email** (SMTP) | email notification | קל |
| **Webhook** | קבל/שלח HTTP | קל |
| **Schedule** | זמן קבוע (cron) | קל |

---

## 💡 Workflow מתקדם שאפשר לבנות

### 1. "Daily SLH Broadcast"
```
Schedule (כל יום 10:00)
  → HTTP: GET /api/stats + /api/aic/stats + /api/sudoku/stats
  → Format: "היום: 19 users, 10 TON staked, X AIC circulating, Y sudoku solves"
  → Twitter + LinkedIn + Telegram channel
```

### 2. "New Expert Alert"
```
Schedule (כל שעה)
  → HTTP: GET /api/admin/experts/pending
  → IF count > 0:
      → Telegram: אזהרה לאוסיף לאשר
```

### 3. "Revenue Alert"
```
Webhook trigger (SLH API posts to n8n on new payment)
  → Discord webhook: "💰 נכנסה עסקה: X TON"
  → Email: invoice
  → Sheets: log the tx
```

---

## 🔐 אבטחה

- n8n רץ על `localhost:5678` (לא חשוף לאינטרנט)
- Basic auth חובה (env vars: `N8N_BASIC_AUTH_USER` + `PASSWORD`)
- אם תרצה גישה מרחוק → הוסף VPN או Cloudflare Tunnel (לא reverse proxy פתוח)
- ה‑OAuth tokens נשמרים encrypted ב‑volume `n8n-data`

---

## ⚡ הצעד הבא

**אם תרצה שאתקין n8n עכשיו:**
1. תספק לי סיסמה ל‑n8n (`N8N_PASSWORD`) — רק אתה תדע
2. אני אוסיף שירות ל‑`docker-compose.yml`
3. אתה מריץ `docker compose up -d n8n`
4. נכנס ל‑http://localhost:5678 → builds workflows ביחד

**Time: ~20 דק' setup · 10 דק' per workflow · חינמי לנצח.**

---

## 📚 Docs רשמיים
- https://docs.n8n.io/
- https://n8n.io/integrations/rss-feed-trigger/
- https://n8n.io/integrations/twitter/
