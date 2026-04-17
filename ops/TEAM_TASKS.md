# 📋 SLH Team Tasks — Telegram-Shareable

> **Copy-paste each task below to the responsible team member.**
> Last update: 2026-04-17 | Status: Active

---

## 🎯 Tasks by Role

### 👤 For Osif (Owner — ~30 min total)
```
שלום אוסיף, 4 משימות שחוסמות את המערכת:

1️⃣ ROTATE ADMIN KEY (5 דק')
   • לך ל-Railway → slh-api → Variables
   • ערוך ADMIN_API_KEYS והוסף (בנוסף ל-slh2026admin):
     slh_admin_hgaBj2T9k8T8Hmm5pC_794J-4UaDG6ce
   • Save. Railway יפרוס אוטומטי (~2 דק')
   • פתח /admin.html → Logout → התחבר עם המפתח החדש
   • אחרי 24 שעות עבודה תקינה, מחק את slh2026admin מ-Railway

2️⃣ SET BOTFATHER COMMANDS (10 דק')
   לכל בוט — @BotFather → /setcommands → בחר בוט → הדבק:
   
   ללא SLH_Ledger / SLH_AIR / Campaign_SLH:
   start - התחלה
   help - עזרה
   status - מצב חשבון
   mylink - קישור הפניה
   
   הוסף לכל בוט רק את הפקודות שרלוונטיות לו

3️⃣ BLOCK BOT BLEEDING (15 דק')
   יש באג: @Campaign_SLH_bot שולח פקודה → SLH_AIR עונה "פקודה לא מוכרת"
   התיקון: בכל handler בכל בוט, בדוק בתחילת הפונקציה:
   if message.text and '@' in message.text:
       addressed_bot = message.text.split('@')[1].split()[0]
       if addressed_bot.lower() != BOT_USERNAME.lower():
           return  # לא בשבילי
   (אעשה PR אם תאשר)

4️⃣ ROTATE 31 BOT TOKENS (חופשי)
   כל הטוקנים ב-.env נחשפו בצ'אט היסטוריה → חובה סיבוב.
   לכל בוט: @BotFather → /revoke → /token → עדכן .env →
   docker compose up -d --force-recreate <service>
   
   רשימה ב-ops/SECURITY_TOKEN_ROTATION.md
```

---

### 🔧 For "SLH Core Assistant" (AI advisor agent)
```
אתה סוכן ייעוץ. המשימות שלך — לייצר קוד לביצוע ע"י אוסיף:

1️⃣ Bot bleeding fix
   כתוב patch ל-shared/bot_template.py שבודק @botname_suffix ומתעלם
   מהודעות לא-מוכוונות. תחזיר diff מלא.

2️⃣ ESP32 register/verify wiring
   /register ESP001 <phone> ו-/verify ESP001 <code> לא מגיבים.
   כתוב handler מלא ל-campaign-bot או ל-device-registry:8090 שכולל:
   • POST /register  → יוצר device ב-DB + שולח SMS/קוד בטלגרם
   • POST /verify    → מאמת קוד + מחזיר signing token
   תחזיר הן את ה-Python handler והן את ה-SQL migration.

3️⃣ SYNC_PROTOCOL.md integration
   קרא את D:\SLH_ECOSYSTEM\ops\SYNC_PROTOCOL.md
   אשר שאתה עובד לפי הכללים שם. אם לא — הצע שינויים.

עדכן SESSION_STATUS.md בסוף session.
```

---

### 💻 For any other AI agent joining
העתק את `D:\SLH_ECOSYSTEM\ops\AGENT_INTRO_PROMPT.md` כהודעה ראשונה.
הוא יעשה onboarding לבד.

---

## 🚨 Critical Blockers (נכון ל-17.4 01:45)

| # | בעיה | אחראי | דחיפות |
|---|------|-------|-------|
| 1 | Bot command collision (SLH_AIR עונה ל-Campaign) | Osif + AI agent | 🔴 UX |
| 2 | ESP32 flow לא מגיב | AI agent → Osif | 🔴 |
| 3 | Admin key = default | Osif | 🟡 |
| 4 | 31 bot tokens exposed | Osif | 🟡 אבטחה |
| 5 | 56 uncommitted code files | Claude Opus | 🟢 |

## 📈 Progress Tracker
- [x] Bug debug system (דשבורד + FAB + Telegram alerts) — **DONE 17.4**
- [x] Git remote fix + push — **DONE 17.4**
- [x] Auto-approve settings.json — **DONE 17.4**
- [x] Agent sync protocol docs — **DONE 17.4**
- [x] Device onboarding API live (3 endpoints) — **DONE 17.4 night, verified 17.4 morning**
- [x] Bot-to-bot filter middleware (shared/bot_filters.py) — **DONE 17.4 night**
- [x] AI Assistant coverage 16% → ~100% — **DONE 17.4 night**
- [x] join.html + CONTRIBUTOR_GUIDE + FB post — **DONE 17.4 night**
- [x] SILENT_MODE kill switch + alert rate-limit — **DEPLOYED 17.4 night** (var still needs to be set in Railway)
- [x] TOKEN_AUDIT.md secured via .gitignore — **DONE 17.4 morning closure**
- [x] Morning verification (API + device/register) — **DONE 17.4 morning closure**
- [ ] Admin key rotation in Railway — **Osif** (blocked on Railway UI access)
- [ ] SILENT_MODE=1 in Railway — **Osif** (blocked on Railway UI access)
- [ ] Twilio SMS key — **Osif** (external signup)
- [ ] Bot command collision fix — **AI + Osif** (PR pending)
- [ ] ESP32 flow (Telegram side) — **AI advisor**
- [ ] 31 token rotation — **Osif** (BotFather only)
- [ ] Campaign bot naming consistency — **Osif + AI**
- [ ] docker-compose.yml + shared/bot_template.py regression review — **Osif** (see REGRESSIONS_FLAG_20260417.md)

## 📡 Links for sharing
- Live status: `D:\SLH_ECOSYSTEM\ops\SESSION_STATUS.md`
- Agent intro: `D:\SLH_ECOSYSTEM\ops\AGENT_INTRO_PROMPT.md`
- Sync rules: `D:\SLH_ECOSYSTEM\ops\SYNC_PROTOCOL.md`
- Bug dashboard: https://slh-nft.com/admin-bugs.html
- Admin panel: https://slh-nft.com/admin.html
