# DROP OFF · QA / Testing · 2026-04-24

**קהל יעד:** Zohar Shefa Dror, Yakir Lisha, אחיין (ID 6466974138, 13yo), כל חבר צוות שיכול לבדוק
**זמן ביצוע כולל:** 1–2 שעות לכל סבב QA, אפשר לחלק בין אנשים
**דרישות מקדימות:**
- חשבון Telegram
- דפדפן עדכני (Chrome/Edge/Firefox)
- טלפון עם WhatsApp (לקבלת OTP / קוד אימות)
- לא נדרשת גישת אדמין

---

## 🎯 מטרה כללית

אחרי ~8 לילות עבודה, יש המון פיצ'רים שצריכים בדיקה **מחיי משתמש**. אין בדיקות אוטומטיות (K-21 ב-KNOWN_ISSUES) — בדיקה אנושית היא הדרך היחידה לאמת איכות.

**המטרה:** לעבור על 5 "golden paths" + לתעד כל באג / UX-issue שאתם מוצאים.

---

## 🔴 Golden Path #1 — Registration & Onboarding (15 דק')

**המטרה:** לוודא שמשתמש חדש יכול להירשם ולהתחיל עבודה.

### צעדים:
1. פתח Telegram, חפש `@SLH_AIR_bot`
2. לחץ `/start`
3. הבוט אמור להגיב עם:
   - הודעת welcome בעברית
   - כפתור Share Phone
4. שתף טלפון
5. בדוק שה-DM חוזר עם:
   - מזהה משתמש (SLH ID)
   - לינק לאתר (https://slh-nft.com)
   - הצעה להתחיל עם Academia

### דברים לבדוק:
- [ ] עברית מוצגת נכון (לא `?????` או `ðŸ`)
- [ ] הכפתור "Share Phone" עובד
- [ ] הודעת confirmation מכילה SLH ID
- [ ] הלינק לאתר נפתח ועובד
- [ ] אם ניסיון שני עם אותו טלפון — מזהה שאתה כבר רשום (לא יוצר חדש)

### באגים ידועים (לא צריך לדווח):
- Emoji על dashboard activity feed לפעמים מוצג שגוי (K-12)
- Mini App עדיין 404 עד שהאתר ידחוף (P0 Osif)

---

## 🔴 Golden Path #2 — Academia Course #1 Purchase (15 דק')

**המטרה:** לוודא שאפשר לקנות קורס.

### צעדים:
1. פתח https://slh-nft.com/academia.html
2. גלול למטה ל-Course #1 "Dynamic Yield Economics"
3. צפה ב-3 tiers:
   - Free — ₪0
   - Pro — ₪179
   - VIP — ₪549
4. לחץ "רכוש Pro"
5. עקוב אחרי הוראות תשלום (כרגע דרך @WEWORK_teamviwer_bot)
6. אחרי תשלום, בדוק שהקורס מופיע ב-"הקורסים שלי"

### דברים לבדוק:
- [ ] המחיר המוצג באתר תואם ל-API (⚠️ ידוע: K-10 — ₪99 vs ₪549 אי-עקביות)
- [ ] כפתור "רכוש" עובד
- [ ] זרימת תשלום ברורה
- [ ] אחרי תשלום — access מוענק
- [ ] 6 מודולים נגישים
- [ ] Calculator עובד
- [ ] Python simulator רץ (אם אתה VIP)

**הערה:** אל תשלם באמת בלי אישור מ-Osif — אלא דיווח "ניסיתי, הייתי צריך לשלם ₪179, הפסקתי כאן".

---

## 🔴 Golden Path #3 — Website Navigation (30 דק')

**המטרה:** לעבור על כל 43 דפי האתר ולראות אם הם טוענים + מציגים נתונים.

### רשימה לבדיקה:
אתר ראשי: https://slh-nft.com

| דף | URL | מה לבדוק |
|----|-----|-----------|
| Home | `/index.html` | טוען מהר, עברית תקינה |
| Academia | `/academia.html` | 3 tiers מוצגים, מחירים נכונים |
| Community | `/community.html` | feed נטען, אין "47" fake |
| Buy | `/buy.html` | ⚠️ ידוע: מחיר SLH שגוי 122 (K-11) |
| Marketplace | `/marketplace.html` | ⚠️ יכול להיות 404 עד push |
| Team | `/team.html` | ⚠️ 10 חברים, יכול להיות 404 עד push |
| Blockchain | `/blockchain.html` | BSCScan data (0 עד BSCSCAN key יוגדר) |
| Network | `/network.html` | תצוגה של הרשת |
| Stats | `/stats.html` | מספרים מהאמת |
| Invite | `/invite.html` | ⚠️ "alpha Genesis 49" ולא "אלפי משקיעים" |
| Earn | `/earn.html` | ⚠️ "Dynamic" ולא "65% APY" |
| Admin | `/admin.html` | אל תיכנס, רק בדוק שטוען login |
| Live | `/live.html` | redirect ל-chain-status.html |
| Chain Status | `/chain-status.html` | events panel (⚠️ יכול להיות ריק — K-4) |
| FAB Site Map | (כפתור כחול למטה-שמאל) | תפריט נפתח עם 7-8 לינקים |

**תיעוד:** תבנית מומלצת:
```
דף: academia.html
סטטוס: ✅ עובד / ❌ בעיה
בעיה: <אם יש — תיאור + Screenshot>
```

---

## 🟡 Golden Path #4 — Mobile UX (15 דק')

**המטרה:** לוודא שהאתר עובד טוב במובייל.

### צעדים:
1. פתח את האתר בטלפון (Android/iOS)
2. עבור על 5 דפים עיקריים:
   - Home
   - Academia
   - Community
   - Stats
   - Dashboard (אחרי login)

### דברים לבדוק:
- [ ] הטקסט נקרא (לא קטן מדי)
- [ ] כפתורים ניתנים ללחוץ (לא צמודים)
- [ ] תפריט hamburger פתוח ונסגר
- [ ] אין scrollbar אופקי (horizontal scroll)
- [ ] תמונות נטענות
- [ ] theme switcher (לילה/יום) עובד
- [ ] FAB כחול (Site Map) עובד
- [ ] בעת מילוי טופס, מקלדת לא מכסה את הכפתור Submit

**ידוע:** `website/js/shared.js` קיים ב-`initShared()` אבל לא נקרא ב-121 דפים (K-5). תוצאה: ניווט, theme, וFAB יכולים לא להופיע באופן שונה בין דפים. תדווחו על זה אם תמצאו.

---

## 🟡 Golden Path #5 — Mini App (Telegram) (10 דק')

**דרישות מקדימות:** אחרי ש-Osif push miniapp/ ל-GitHub Pages (DROP_OSIF #2).

### צעדים:
1. פתח @SLH_AIR_bot בטלגרם
2. לחץ על Menu button (אם קיים) או `/app` command
3. Mini App אמור להיפתח בתוך טלגרם
4. עבור על 3 tabs: Dashboard, Wallet, Device

### דברים לבדוק:
- [ ] Mini App נפתח (לא error)
- [ ] טעינה מהירה (< 3 שניות)
- [ ] נתונים מציגים (balance, REP, etc.)
- [ ] Activity feed — ⚠️ ידוע: emoji יכול להיות corrupted (K-12)
- [ ] כפתורי פעולה עובדים
- [ ] סגירה וחזרה — state נשמר

**אם 404:** ה-push של Osif לא בוצע עדיין. דווח לו.

---

## 🐛 איך לדווח באג

**שלב 1:** תיעוד בסיסי
```
דף / פיצ'ר: <איפה קרה>
מה ניסיתי: <תיאור קצר>
מה קרה: <תוצאה לא צפויה>
מה צריך לקרות: <ציפייה>
דפדפן + OS: <Chrome Win10, iPhone Safari, וכו'>
זמן: <שעה מדויקת>
Screenshot: <צרף>
```

**שלב 2:** דיווח
- **אם באג בסיסי** — שלח ל-Osif בטלגרם @osifeu_prog
- **אם באג רציני (security, money, data loss)** — שלח ל-Osif **מיד** ועצור בדיקות
- **אם UX-issue** (דורש חשיבה) — רשום ברשימה שלך, דווח בסוף ה-QA-session

**שלב 3:** באגים ידועים (לא צריך לדווח על אלו):**
קרא את `ops/KNOWN_ISSUES.md` — אם הבאג שלך מופיע שם, רק ציין מספר (למשל "K-12 confirmed in miniapp").

---

## 📊 דוח סיכום QA-session

בסוף כל session, שלח ל-Osif:
```
QA Session — <date>, <שם>

Paths tested:
• Registration: ✅ PASS
• Academia: ❌ FAIL (details below)
• Navigation: ✅ PASS (3/43 pages had issues)
• Mobile: ⚠️ PARTIAL (2 issues)
• Mini App: — (not tested, still 404)

Bugs found:
1. <תיאור> (reproducible: YES/NO)
2. <תיאור>

UX issues (not bugs):
1. <הצעה>

Time spent: <שעה>
Summary: <שורה אחת כללית>
```

---

## 🏆 תגמולים

**למי שמוצא באגים אמיתיים:**
- Badge "Bug Hunter" באתר (בעתיד)
- ZVK tokens — 10-50 לפי חומרה (מוענק ידנית ע"י Osif)
- תיעוד בקרדיטים של release notes

**למי שבוחן ולא מוצא כלום (וזה גם יקר):**
- Badge "QA Verifier"
- 5 ZVK לאישור

---

## 📋 Checklist Session ראשוני

- [ ] קראתי את המסמך הזה במלואו
- [ ] יש לי Telegram + דפדפן + טלפון מוכנים
- [ ] עברתי Golden Path #1 (Registration) ודיווחתי
- [ ] עברתי Golden Path #3 (Navigation) ותיעדתי 43 דפים
- [ ] שלחתי דוח סיכום ל-Osif

**אחרי שה-deploys ירוקים:**
- [ ] עברתי Golden Path #2 (Academia)
- [ ] עברתי Golden Path #4 (Mobile)
- [ ] עברתי Golden Path #5 (Mini App)

---

## 🆘 שאלות ותמיכה

- **Osif** — @osifeu_prog — קשר ישיר לכל שאלה
- **Community page** — עוד משתמשים שבודקים, תוכלו להחליף דעות
- **ops/KNOWN_ISSUES.md** — רשימת באגים ידועים שכבר מתועדים

**תזכורת:** אתם עושים שירות ענק. QA הוא ההפרש בין system שנראה טוב ל-system שעובד באמת. תודה מראש! 🙏
