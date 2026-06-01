# 🔷 SLH ECOSYSTEM — Handoff מלא + המלצות
**תאריך:** 05/05/2026  
**גרסה:** v30 (Admin Bot) | Docker Compose 20+ שירותים

---

## 📊 מצב הפרויקט עכשיו

### ✅ מה עובד
- **Guardian Bot** (`@Grdian_bot`) — פעיל ועונה
- **postgres** — תשתית DB פעילה
- **redis** — cache פעיל
- **docker-compose.yml** — תקין ומלא (20+ שירותים)
- **Admin Bot** (`@MY_SUPER_ADMIN_bot`) — הקוד קיים ושלם, צריך להיות built

### ❌ הבעיה שגרמה לכל הכאב
```
רצת docker compose build מ-C:\Windows\system32
במקום D:\SLH_ECOSYSTEM
```
זה כל מה שהיה. ה-`docker-compose.yml` שלך **לא היה שבור** — פשוט Docker לא מצא אותו.

---

## 🚀 הרצת ה-Restore

### שלב אחד בלבד:
```powershell
# הדבק ב-PowerShell כמנהל:
Set-ExecutionPolicy Bypass -Scope Process -Force
& "D:\SLH_ECOSYSTEM\SLH_RESTORE.ps1"
```

הסקריפט יעשה הכל אוטומטית.

---

## 🏗️ מבנה הפרויקט (מה שיש לך)

```
D:\SLH_ECOSYSTEM\
├── docker-compose.yml          ← 20+ שירותים, תקין
├── .env                        ← טוקנים וסיסמאות
├── dockerfiles\
│   ├── Dockerfile.admin        ← Admin Bot
│   ├── Dockerfile.guardian     ← Guardian
│   ├── Dockerfile.core         ← Academia Bot
│   └── ... (15 dockerfiles)
├── admin-bot\
│   └── main.py                 ← קוד מלא + FSM + Control Center
├── shared\
│   └── slh_payments\           ← לוגיקת תשלומים משותפת
├── factory\                    ← Staking Engine
├── wallet\                     ← TON Wallet
├── airdrop\                    ← Airdrop Bot
└── ... (20+ תיקיות בוטים)
```

---

## 🤖 רשימת הבוטים שלך

| שירות | Bot | Container | סטטוס |
|-------|-----|-----------|-------|
| Admin | @MY_SUPER_ADMIN_bot | slh-admin | ⚠️ צריך build |
| Academia | @SLH_Academia_bot | slh-core-bot | ? |
| Guardian | @Grdian_bot | slh-guardian-bot | ✅ פעיל |
| BotShop | @Buy_My_Shop_bot | slh-botshop | ? |
| Wallet | @SLH_Wallet_bot | slh-wallet | ? |
| Factory | @Osifs_Factory_bot | slh-factory | ? |
| Airdrop | - | slh-airdrop | ? |
| Campaign | - | slh-campaign | ? |
| Fun/Community | - | slh-fun | ? |

---

## ⚡ פקודות Admin Bot (לאחר שיעלה)

### פקודות בסיסיות:
```
/start       - תפריט ראשי עם ASCII logo
/dashboard   - סטטיסטיקות מלאות (משתמשים, הכנסות)
/payments    - תשלומים ממתינים לאישור
/users       - רשימת משתמשים רשומים
/stats       - נתוני מכירות
/bots        - רשימת בוטים + מחירים
/revenue     - דוח הכנסות לפי בוט
```

### Control Center (חדש):
```
/status      - snapshot מלא (API health, DB, devices)
/control     - קישורים לדוקס מבצעיים
/agents      - רשימת agents פעילים
/devices     - ESP32 fleet
/git_log     - 5 commits אחרונים מ-GitHub
/audit_status - ממצאי audit
/customer    - סטטוס outreach ל-6 לקוחות פוטנציאלים
```

### שידורים:
```
/broadcast   - שלח הודעה + מתנה לכל המשתמשים (FSM flow)
/airdrop     - חלוקת טוקנים מהירה
/gift <id> <amount> <TOKEN> - מתנה לאדם ספציפי
```

---

## 🔧 המלצות לשיפור (לפי עדיפות)

### P0 — מיידי (חייב לפני IDO)
1. **JWT_SECRET** — עדיין ריק ב-.env → הגדר random string חזק
2. **ADMIN_API_KEYS** — החלף מ-default
3. **הוצאת Bot Tokens מהמסמכים** — הטוקנים שלך חשופים בהיסטוריית השיחה! צור טוקנים חדשים דרך @BotFather עכשיו

### P1 — החודש הקרוב
4. **docker volume backups** — הוסף cron job לגיבוי postgres_data
5. **Docker socket security** — `privileged: true` הוא סיכון אבטחה. שנה ל-socket group בלבד
6. **Health monitoring** — הוסף `/health` endpoint לכל בוט עם alerting
7. **סתירות באתר** — Total Supply (110.75M vs 1B), מחיר Wallet (₪444 vs ₪0.05)
8. **SSL ל-nft.co.il** — האתר חסום בגלל self-signed cert

### P2 — Q3 2026
9. **Docker Swarm / K8s** — כשיגיע עומס משמעותי, Docker Compose לא יספיק
10. **Centralized logging** — לוגים כרגע מפוזרים. שקול ELK Stack
11. **CI/CD** — GitHub Actions שיבנה ויעלה אוטומטית בכל push
12. **Rate limiting** — Admin bot ללא rate limiting — פוטנציאל ל-spam

### P3 — עתיד
13. **Web Dashboard** — GUI להחלפת הטלגרם ל-ops
14. **Multi-admin support** — כרגע רק Telegram ID אחד. הוסף role-based access
15. **Audit log** — כל פקודת admin צריכה להיכתב ל-DB

---

## 🔑 מה צריך להיות ב-.env שלך

```env
# ⚠️ בדוק שכל אלו קיימים:
DB_PASSWORD=slh_secure_2026
ADMIN_USER_ID=224223270

ADMIN_BOT_TOKEN=7644371589:AAE0...      # @MY_SUPER_ADMIN_bot
CORE_BOT_TOKEN=8521882513:AAEZ...       # @SLH_Academia_bot
GUARDIAN_BOT_TOKEN=...                   # @Grdian_bot
WALLET_BOT_TOKEN=...
FACTORY_BOT_TOKEN=...
FUN_BOT_TOKEN=...
BOTSHOP_BOT_TOKEN=...
AIRDROP_BOT_TOKEN=...

# Control Center:
ADMIN_API_KEY=slh_admin_2026_rotated_04_20
ADMIN_BROADCAST_KEY=slh-broadcast-2026-change-me  # ⚠️ שנה!

# Railway (אם רלוונטי):
RAILWAY_DATABASE_URL=postgresql://...
```

---

## 🛠️ פתרון בעיות נפוצות

### admin-bot לא עולה:
```powershell
docker logs slh-admin --tail 50
# אם: "BOT_TOKEN missing" → בדוק .env
# אם: "Cannot connect to Docker" → socket לא mounted
# אם: "asyncpg error" → postgres לא מוכן, המתן 10 שניות
```

### docker compose נותן שגיאות YAML:
```powershell
# בדוק שאתה בתיקייה הנכונה!
Get-Location   # חייב להיות D:\SLH_ECOSYSTEM
```

### Guardian bot לא מגיב:
```powershell
docker logs slh-guardian-bot --tail 30
docker compose restart guardian-bot
```

### DB לא נגיש:
```powershell
docker exec -it slh-postgres psql -U postgres -d slh_main -c "\dt"
```

---

## 📱 בדיקת בריאות מהירה

אחרי שהמערכת עולה, שלח לבוט:
1. `/start` — אמור להציג ASCII + תפריט
2. `/status` — אמור להציג API health + users
3. `/dashboard` — אמור להציג סטטיסטיקות DB
4. `/payments` — רשימת תשלומים ממתינים

---

## 🔐 אזהרת אבטחה חשובה

**הטוקנים שלך נחשפו בהיסטוריית שיחה עם Claude.** עשה זאת עכשיו:

1. פתח @BotFather בטלגרם
2. `/mybots` → בחר כל בוט → API Token → Revoke current token
3. עדכן את ה-.env עם הטוקנים החדשים
4. הפעל מחדש את הקונטיינרים

---

**מצב לאחר הרצת הסקריפט:**
- Admin Bot מוצג ועובד ✅
- Guardian Bot ממשיך לעבוד ✅  
- Postgres + Redis פעילים ✅
- שאר הבוטים — הפעל לפי צורך

---
*נוצר אוטומטית | SLH Ecosystem Analysis 05/05/2026*
