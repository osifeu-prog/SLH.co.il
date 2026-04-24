# DROP OFF · Community / Telegram · 2026-04-24

**קהל יעד:** Elazar (community leader) + כל מי שמנהל תקשורת עם משתמשים
**זמן ביצוע כולל:** 2–3 שעות ראשוניות, +30 דק'/יום תחזוקה
**דרישות מקדימות:**
- Telegram account פעיל
- גישה ל-DM דרך @osifeu_prog לקבלת ADMIN_BROADCAST_KEY
- (אופציונלי) יכולת להריץ curl מ-terminal

---

## 🎯 מטרה כללית

SLH Spark כרגע ב-**phase pre-launch**:
- 9–11 משתמשים רשומים (רובם contributors, לא משקיעים אמיתיים)
- אין עדיין לקוחות משלמים אמיתיים (הרבה הדגמות)
- Dynamic Yield Academia Course #1 LIVE במערכת

תפקיד Community:
1. **Onboarding** — להבטיח שכל משתמש רשום התחיל את הבוט
2. **Activation** — להעביר אותם מ-lurker ל-active contributor
3. **Retention** — עדכונים שבועיים על מה שחדש
4. **Support** — תמיכה ראשונית בשאלות בסיסיות

---

## 🔴 1. Yahav Onboarding Bounce — לתיקון מיידי

**הבעיה:** ב-22.4 נשלחה הודעת onboarding ל-6 משתמשים. 5 קיבלו, Yahav (7940057720) bounced כי עוד לא עשה `/start` ל-@SLH_AIR_bot.

**פעולה:**
1. חפש את Yahav בטלגרם (ID 7940057720) — אם אין קשר ישיר, שאל את Osif מי הוא.
2. שלח לו בטלגרם:
   ```
   היי! כדי לקבל עדכונים מ-SLH Spark, בבקשה התחל את הבוט שלנו:
   👉 @SLH_AIR_bot
   פשוט לחץ /start ותחתום. אחרי זה נוכל לשלוח עדכונים חשובים.
   ```
3. אחרי שעשה /start, תדווח ל-Osif והוא ישלח שוב את ה-onboarding DM:
   ```bash
   curl -X POST https://slh-api-production.up.railway.app/api/broadcast/send \
     -H "X-Admin-Key: <KEY>" \
     -d '{"segment":"user","telegram_id":7940057720,"message":"<הודעת onboarding>"}'
   ```

**הודעת Onboarding המקורית (לנוסח דומה):**
> 🌟 ברוך הבא ל-SLH Spark!
>
> SLH היא מערכת אקוסיסטם קריפטו ישראלית עם 5 טוקנים (SLH/MNH/ZVK/REP/ZUZ).
>
> 📚 קורס #1 "Dynamic Yield Economics" — מוסבר הכלכלה מאחורי המערכת שלנו.
> 🎯 3 רמות: Free / Pro ₪179 / VIP ₪549
>
> התחל פה: https://slh-nft.com/academia.html
>
> שאלות? כתוב ל-@osifeu_prog

---

## 🔴 2. Monitoring Daily — מי פעיל / מי לא

**בדיקה יומית (5 דק'):**
```bash
# כמה משתמשים רשומים
curl https://slh-api-production.up.railway.app/api/stats

# רשימת פעילים 7 ימים אחרונים (admin)
curl -H "X-Admin-Key: <KEY>" \
  https://slh-api-production.up.railway.app/api/admin/dashboard
```

**תמונת מצב צפויה (2026-04-22):**
- `total_users: 11` (גדל לאחרונה מ-9 ל-11)
- `active_7d: ~5` (רק Tzvika + Osif + Zohar)
- `posts_today: 0` (community feed לא פעיל)

**מטרות Community:**
| מדד | יעד שבוע הבא | יעד חודש |
|-----|--------------|-----------|
| Active 7d | 8 מתוך 11 | 15 מתוך 25 |
| Community posts/day | 2 | 5 |
| Academia enrollments | 2 Pro | 5 Pro + 1 VIP |

---

## 🔴 3. Broadcast יומי/שבועי — עדכון הקהילה

### 3.1 תבנית עדכון שבועי (ימי ראשון 10:00)
**למי:** `segment: "approved"` (כל משתמש רשום ומאומת)

**Template:**
```
📰 SLH Spark — עדכון שבועי

השבוע:
• <feature חדש או fix>
• <חדשות מעולם הקריפטו הרלוונטי>
• <צילום מסך של graph / מספר מעניין>

מספרים:
• משתמשים פעילים: <X>
• פוסטים בקהילה: <Y>
• רישומים לקורס #1: <Z>

השבוע הבא:
• <מה מתוכנן>

כתבו לי במידה ויש שאלות 🙏
— SLH Spark Team
```

**שליחה:**
```bash
curl -X POST https://slh-api-production.up.railway.app/api/broadcast/send \
  -H "X-Admin-Key: <KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "message":"<הטקסט מעל>",
    "segment":"approved"
  }'
```

### 3.2 הודעות ad-hoc (כל יום לפי צורך)
**חדשות חשובות (deploy חדש, feature live):**
```bash
# רק לאדמינים תחילה
curl -X POST .../api/broadcast/send \
  -d '{"segment":"admins","message":"..."}'

# אחרי אימות — כל המשתמשים
curl -X POST .../api/broadcast/send \
  -d '{"segment":"all","message":"..."}'
```

---

## 🟡 4. קבוצות Telegram — ניהול ופיקוח

**קבוצות קיימות (לפי memory):**
| קבוצה | לינק | מטרה |
|---------|-------|-------|
| DATING | `+nKgRnWEkHSIxYWM0` | @G4meb0t_bot dating network — **לא לעבודה!** |
| WORKERS (TBD) | עדיין לא קיימת | עתידית — לעובדים בלבד |
| אחרים | — | בירור מול Osif |

**אחריות Community:**
- **אל תערבב** DATING עם עבודה. גם אל תפרסם פרוייקטים ב-DATING.
- הקבוצת WORKERS עתידית — כשתיווצר, Osif יוסיף אותך.
- צ'אטים פרטיים עם משתמשים = סבבה (ואפילו מעודד).

---

## 🟡 5. תמיכה ראשונית (common questions)

### Q: "איך אני קונה SLH?"
**תשובה:**
> כרגע SLH נסחר ב-PancakeSwap (BSC). לינק ישיר:
> https://pancakeswap.finance/swap?outputCurrency=0xACb0A09414CEA1C879c67bB7A877E4e19480f022
>
> (הערה: זה על BSC chain — תוודא ש-MetaMask שלך מוגדר ל-BSC).

### Q: "מה ההבדל בין SLH, MNH, ZVK?"
**תשובה:**
> SLH = טוקן פרימיום (מטרה: ₪444)
> MNH = stablecoin צמוד לשקל (1 MNH = 1 ₪)
> ZVK = תגמול פעילות (~₪4.4, מרוויחים דרך contribution)
> REP = מוניטין אישי (0-1000, לא נסחר)
> ZUZ = "אות קין" נגד הונאות (Guardian system)

### Q: "איך לרשום טלפון שלי?"
**תשובה:**
> דרך @SLH_AIR_bot — /start → Share phone. אם יש בעיה, פנה ל-@osifeu_prog.

### Q: "שכחתי את הסיסמה לאדמין"
**תשובה:**
> לא — אדמין.html עם סיסמה מקומית. לא אנחנו מנהלים. פנה ל-@osifeu_prog.

### Q: "מתי יהיה App ל-iOS/Android?"
**תשובה:**
> Mobile MVP במפה — אחד משבועות הקרובים. בינתיים, האתר עובד גם במובייל ויש Mini Apps דרך Telegram.

### Q: "למה Course #1 עולה ₪179?"
**תשובה:**
> Free tier (בלי שאלות) חינם. Pro (₪179) פותח את כל 6 המודולים + calculator + Python simulator. VIP (₪549) כולל ייעוץ 1-on-1.

### Q: "יש הצעה של ₪99 — למה ה-API מחזיר ₪549?"
**תשובה (baseline — יתעדכן אחרי תיקון):**
> יש אי-עקביות זמנית. המחיר הנכון הוא ₪549 ל-VIP. תיקון ב-UI מגיע בימים הקרובים.

---

## 🟢 6. פוסטים בקהילה — שיפור engagement

**אתר community:** https://slh-nft.com/community.html

**אחריות:**
- פעם ביום — בדוק אם יש פוסט חדש (נכון ל-22.4 — 0 פוסטים היום)
- עודד משתמשים פעילים (Tzvika, Zohar, Yakir) לפרסם
- תוכן מוצע:
  - "איך אני מרוויח ZVK" (tutorial)
  - "Screenshot של התיק שלי" (social proof)
  - "שאלת השבוע: מה המטרה ל-SLH?"

---

## 🟢 7. דוח שבועי ל-Osif

**ימי ראשון 18:00, שלח ב-Telegram:**
```
📊 Community Report — שבוע X

• New users this week: <X>
• Total active (7d): <Y> / <total>
• Broadcast sent: 1 (weekly update)
• Community posts: <Z>
• Support questions answered: <N>

Highlights:
• <משתמש חשוב שעשה משהו טוב>

Issues:
• <משהו שצריך תיקון / תמיכה>

Plan next week:
• <משהו מתוכנן>
```

---

## 🔒 אבטחה — חשוב

- **אל תכיל את ה-ADMIN_BROADCAST_KEY** — קבל מ-Osif דרך ערוץ מאובטח
- **אל תשתמש ב-`segment:"all"`** בלי לבדוק עם Osif
- **אסור broadcast מעל 3 ליום** — משתמשים מסמנים spam, Telegram חוסם את הבוט
- **גישה לבוטים עצמם דרך BotFather** — רק ל-Osif

---

## 📋 Checklist סיום (ראשוני)

- [ ] Yahav (7940057720) נוצר לו קשר, עשה /start ל-@SLH_AIR_bot
- [ ] Osif שלח לו DM onboarding חוזר
- [ ] יש לי ADMIN_BROADCAST_KEY (מ-Osif)
- [ ] שלחתי broadcast בדיקה ל-`segment: "admins"` בלבד — קיבלתי
- [ ] בדקתי /api/stats — המספרים הגיוניים
- [ ] נגשתי ל-community.html ואני מכיר את הדף
- [ ] שלחתי דוח שבועי ראשון ל-Osif ביום ראשון

---

## 🆘 מצבי חירום

| מצב | פעולה |
|-----|-------|
| משתמש מדווח על תשלום שלא התקבל | אסוף: user_id, amount, screenshot. שלח ל-Osif. |
| Guardian banned משתמש בטעות | Osif יכול לעשות reset מהאדמין |
| Bot לא מגיב (לא שולח /start reply) | דווח מייד ל-Osif — Docker container אולי נפל |
| עברית מוצגת מוזר (mojibake) | ידוע (K-12 ב-KNOWN_ISSUES). תיקון בתהליך. |
| משתמש שולח תלונה | תרגם אותה לאנגלית/עברית תקין, שלח ל-Osif |

**קשר ישיר:** @osifeu_prog (0584203384)
