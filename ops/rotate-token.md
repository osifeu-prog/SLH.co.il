# רוטציית TELEGRAM_BOT_TOKEN — מדריך שלב-אחר-שלב

**מתי להשתמש:**
- הטוקן נחשף (בצ'אט, בלוג, בקוד, ב-screenshot)
- `/getMe` מחזיר 401
- חשד לגישה זדונית

**זמן ביצוע:** ~3 דקות אם עוקבים בסדר.

---

## לפני שמתחילים

⚠️ **כללים שאסור לעבור:**
1. הטוקן החדש **לעולם לא** נכנס לצ'אט, לא ל-commit, לא ל-HTML, לא ל-log.
2. הטוקן החדש נכנס **רק** ל-Railway Variables (או ל-env lokaal אם אתה רץ `python bot.py`).
3. אם טעית פעם אחת → רוטציה נוספת מיד. אין "חבל, נרוץ עם זה".

---

## שלבים

### 1. ב-BotFather (Telegram)
1. פתח https://t.me/BotFather
2. `/mybots` → בחר `SLH_macro_bot`
3. **API Token** → **Revoke current token**
4. אשר
5. BotFather יציג טוקן חדש — **העתק** (Clipboard או Save As Plaintext במקום מאובטח)
6. **אל תדביק אותו בצ'אט Claude.** גם לא כדי "להראות שעבד".

### 2. ב-Railway
1. פתח https://railway.app/project/97070988-27f9-4e0f-b76c-a75b5a7c9673
2. לחץ על **Settings** של הפרויקט (לא של service ספציפי)
3. **Shared Variables** → מצא `TELEGRAM_BOT_TOKEN`
4. לחץ על ה-pencil icon → **Edit**
5. הדבק את הטוקן החדש → **Update**
6. Railway יפעיל אוטומטית redeploy של `monitor.slh` (הוא היחיד שצורך את המשתנה).

אם אין Shared Variable ולא מופיע:
- Railway → `monitor.slh` service → **Variables** tab → מצא `TELEGRAM_BOT_TOKEN` → Edit → Update.

### 3. חכה 30-90 שניות ל-redeploy
```powershell
cd D:\SLH.co.il
railway logs --build | Select-Object -Last 5
# חפש "image push" — זה אומר שהבנייה נגמרה
```

### 4. אמת שהכל חזר לאוויר
```powershell
pwsh ops\verify.ps1
```
**צפוי:** `[2] Token validity (getMe) → PASS getMe returned @SLH_macro_bot`

### 5. טסט בטלגרם
- פתח `@SLH_macro_bot` בטלגרם
- שלח `/status`
- צפוי לקבל "✅ System Online ..."

אם אחד השלבים נכשל → עצור, צלם screenshot, שלח לסוכן עם "rotation failed at step X".

---

## למה זה חשוב עוד פעם
- Revoke ב-BotFather לא "מבטל" את הקיים — הוא מייצר *חדש* ומפיל את הישן.
- כל דקה שעוברת עם טוקן ישן = זמן שמישהו אחר יכול לעשות getUpdates ולקרוא הודעות של משתמשים.
- לכן: Revoke → Update env → Verify — **ברצף, לא לפרק על פני שעות.**
