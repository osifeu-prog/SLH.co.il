# DROP OFF · CRM / Business · 2026-04-24

**קהל יעד:** Eliezer (@P22PPPPPP, Telegram ID: 8088324234) + בעלי תפקידים בעסקי
**זמן ביצוע כולל:** 1–2 שעות (אם ה-CSV מוכן) או 4-8 שעות (אם צריך לבנות)
**דרישות מקדימות:**
- ✅ CRM Phase 0 קיים (5 endpoints — ambassador/contacts)
- ⏳ Railway redeploy של commit `6892556` (DROP_OSIF #1)
- ⏳ קובץ CSV של 130 המשקיעים
- ⏳ ADMIN_BROADCAST_KEY מ-Osif (בחדר)

---

## 🎯 מטרה כללית

Eliezer מחזיק רשת של ~130 משקיעים שמעוניינים ב-SLH. בנינו CRM שיאפשר לו:
1. לייבא את ה-CSV למערכת
2. לצפות בדשבורד עם סטטוס מול כל איש קשר
3. לסמן מי "contacted", "interested", "meeting scheduled", "closed"
4. לשלב את זה עם broadcast system של הבוטים

---

## 📋 שלב 1: הכנת ה-CSV (Eliezer — 30-60 דק')

**פורמט נדרש:**
```csv
full_name,phone,email,source,notes,stage
"ישראל ישראלי","0501234567","israel@example.com","whatsapp_group_A","מעוניין ב-VIP","interested"
"שרה כהן","0509876543","sarah@gmail.com","referral_from_eli","קבוצה ב'","new"
```

**עמודות חובה:**
- `full_name` — שם מלא
- `phone` — טלפון ישראלי (עם 0 או +972)
- `stage` — אחד מ: `new`, `contacted`, `interested`, `meeting_scheduled`, `closed_won`, `closed_lost`

**עמודות רשות (מומלץ):**
- `email`
- `source` — איך הגיע (whatsapp_A, referral_eli, facebook_ad, וכו')
- `notes` — כל הערה רלוונטית (מומלץ 100 תווים מקסימום לכל איש)
- `expected_amount_ils` — כמה מתכנן להשקיע
- `meeting_date` — תאריך פגישה אם קבוע

**כלים להכנה:**
- Excel / Google Sheets → Save as CSV (UTF-8!)
- חשוב: encoding UTF-8 בלבד (עברית לא עובדת ב-ANSI)

**שמור כ:** `ambassador_eliezer_contacts_2026-04-24.csv`
**שלח ל:** Osif (WhatsApp או Telegram @osifeu_prog) — הוא יעלה ל-API.

---

## 📋 שלב 2: ייבוא ל-API (Osif מריץ — 5 דק')

**Prerequisites:**
- ✅ Railway deployed commit `6892556` (חובה — אחרת endpoints לא קיימים)
- ✅ ADMIN_BROADCAST_KEY ידוע
- ✅ CSV מ-Eliezer זמין

**פעולה (PowerShell על D:\SLH_ECOSYSTEM):**
```powershell
# אופציה A — שימוש ב-helper script
python scripts\import_ambassador_csv.py `
  --csv "C:\path\to\ambassador_eliezer_contacts_2026-04-24.csv" `
  --ambassador-telegram-id 8088324234 `
  --api-key $env:ADMIN_BROADCAST_KEY

# אופציה B — ידני דרך curl
curl.exe -X POST https://slh-api-production.up.railway.app/api/ambassador/import `
  -H "X-Admin-Key: $env:ADMIN_BROADCAST_KEY" `
  -H "Content-Type: multipart/form-data" `
  -F "csv=@ambassador_eliezer_contacts_2026-04-24.csv" `
  -F "ambassador_id=1"
```

**מה מצפים לראות:**
```json
{
  "success": true,
  "imported": 130,
  "duplicates_skipped": 0,
  "errors": []
}
```

**וידוא:**
```bash
curl "https://slh-api-production.up.railway.app/api/ambassador/contacts?ambassador_id=1&limit=5"
```

---

## 📋 שלב 3: פעולות יומיומיות (Eliezer — מתמשך)

### 3.1 צפייה ברשימה
כל עוד אין UI — יש 2 אפשרויות:
**אופציה A (מהירה):** Osif שולח ל-Eliezer excel export:
```bash
curl "https://slh-api-production.up.railway.app/api/ambassador/contacts?ambassador_id=1&format=csv" \
  -H "X-Admin-Key: <KEY>" \
  -o eliezer_contacts_today.csv
```

**אופציה B (עתידי):** דף ייעודי באתר — `ambassador.html`. טרם קיים (P2).

### 3.2 עדכון סטטוס איש קשר
```bash
# לאחר פגישה / שיחה
curl -X PATCH "https://slh-api-production.up.railway.app/api/ambassador/contacts/<contact_id>" \
  -H "X-Admin-Key: <KEY>" \
  -H "Content-Type: application/json" \
  -d '{"stage":"meeting_scheduled","notes":"פגישה 28.4 ב-10:00","meeting_date":"2026-04-28"}'
```

### 3.3 הוספת איש קשר חדש (במהלך השבוע)
```bash
curl -X POST "https://slh-api-production.up.railway.app/api/ambassador/contacts" \
  -H "X-Admin-Key: <KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "ambassador_id": 1,
    "full_name": "רפאל לוי",
    "phone": "0507654321",
    "stage": "new",
    "source": "referral_post_meeting"
  }'
```

### 3.4 סטטיסטיקה שבועית
```bash
curl "https://slh-api-production.up.railway.app/api/ambassador/stats?ambassador_id=1"
```
מחזיר:
```json
{
  "total_contacts": 130,
  "by_stage": {"new":23, "contacted":67, "interested":28, "meeting_scheduled":8, "closed_won":3, "closed_lost":1},
  "conversion_rate": 2.3,
  "avg_time_to_close_days": 14
}
```

---

## 📋 שלב 4: שילוב עם broadcast system (בעלי תפקיד בעסקי)

אחרי ש-contacts יובאו, אפשר לשלוח מסרים מדורגים לפי stage:

**דוגמה — הודעה לכל "interested":**
```bash
curl -X POST https://slh-api-production.up.railway.app/api/broadcast/send \
  -H "X-Admin-Key: <KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "message":"שלום! רצינו לעדכן שעלה קורס #1 ב-Academia. ניתן לרכוש ב-₪179 Pro.",
    "segment":"ambassador_stage",
    "ambassador_id":1,
    "stage":"interested"
  }'
```

**רצפי follow-up מומלצים:**
| סטטוס | כמה זמן מאז | פעולה |
|--------|--------------|--------|
| `new` | 48 שעות | Eliezer שולח הודעה אישית |
| `contacted` | 5 ימים | תזכורת עם לינק ל-Academia |
| `interested` | 3 ימים | הצעת פגישה |
| `meeting_scheduled` | יום לפני | תזכורת |
| `closed_lost` | 30 ימים | "האם השתנה משהו?" |

---

## 📋 שלב 5: דוח שבועי ל-Osif (Eliezer — ראשון בשבוע, 15 דק')

פורמט מוצע:
```
CRM שבועי — שבוע X (DD.MM–DD.MM)

• סה"כ אנשי קשר: 130
• סטאטוס: New 20 | Contacted 60 | Interested 30 | Meeting 10 | Closed-Won 5 | Closed-Lost 5
• נכנסו השבוע: 3 אנשים חדשים
• יצאו לסטטוס Closed-Won: 2 אנשים
• פגישות מתוכננות השבוע: 5
• אתגרים:
  - [...]
• בקשות ל-Osif:
  - [...]
```

שלח ל: @osifeu_prog

---

## 🔒 אבטחה — חשוב

**אל תחלוק את ה-ADMIN_BROADCAST_KEY:**
- לא ב-WhatsApp
- לא ב-Telegram
- לא בצ'אט עם AI (כולל Claude, ChatGPT, וכו')

**אם דלף בטעות:** דווח מיד ל-Osif והוא יסובב (30 שניות).

**CSV מכיל מידע אישי (טלפונים, אימיילים):**
- אחסן ב-Google Drive פרטי או Dropbox בלבד
- אל תשלח ב-WhatsApp לאחרים
- אחרי שה-CSV יובא — מחק את הקובץ המקומי (המידע כבר במערכת)

---

## 🆘 מה לעשות אם משהו נתקע

| בעיה | מה לעשות |
|------|-----------|
| `404 Not Found` על `/api/ambassador/*` | Railway לא נפרס — פנה ל-Osif (DROP_OSIF #1) |
| `403 Forbidden` | מפתח API לא נכון — בדוק עם Osif |
| CSV import נכשל עם `encoding error` | שמור כ-UTF-8 (לא Windows-1255) |
| שמות בעברית מוצגים כ-`????` | אותו סיפור — UTF-8 |
| טלפון עם פורמט שגוי | תקן ל-`0501234567` או `+972501234567` |

---

## 📋 Checklist סיום

**Eliezer:**
- [ ] CSV של 130 אנשי קשר מוכן בפורמט UTF-8
- [ ] נשלח ל-Osif
- [ ] אחרי ייבוא — קיבלתי אישור שכולם ב-DB
- [ ] הרצתי שאילתת סטאטוס ראשונה ווידאתי שהמספרים נכונים

**Osif:**
- [ ] Railway פרוס (commit `6892556` או יותר חדש)
- [ ] CSV עבר ייבוא בהצלחה ({"imported":130,"errors":[]})
- [ ] Eliezer קיבל גישה לצפייה (דרך export או ambassador.html עתידי)

**עסקי (כל שבוע):**
- [ ] דוח שבועי נשלח ל-Osif
- [ ] סטטוסים מתעדכנים כל פגישה

---

**צריך עזרה?** פנה ל-Osif (@osifeu_prog, 0584203384) — הוא הגשר בינך לבין המערכת הטכנית.
