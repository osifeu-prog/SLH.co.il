# Token Monitor — מודול מוניטור טוקנים בין-בוטים

## למה זה קיים
- ב-`@SLH_macro_bot`: באג אחד שגרם לטוקן להיות revoked = הבוט מת לחלוטין. גילוי בוצע כש-Osif שלח הודעה ולא קיבל תגובה.
- ב-25 בוטים: זה לא מתרחב. צריך מוניטור מרכזי.

המודול הזה הוא הליבה של "always-on token health" שאתה ביקשת.

## מה יש כבר עכשיו

### 1. Registry — `ops/tokens.json`
12 בוטים ברשומה (SLH_macro_bot כפעיל היחיד מתוך D:/SLH.co.il, 11 אחרים מ-SLH_ECOSYSTEM כ-placeholders). הוסף/שנה לפי הצורך — זה JSON רגיל. **ערכי הטוקנים לא נשמרים כאן** — רק שמות של env vars. הסורק קורא את הערך מ-`os.environ` בזמן ריצה.

### 2. Module — `ops/token_monitor.py`
- `check_all()` — async, בודק את כל הבוטים ב-registry במקביל
- `render_table(statuses)` — טבלה צבעונית לטרמינל
- `render_telegram(statuses)` — Markdown להודעת Telegram
- CLI: `python ops/token_monitor.py` (text) או `--json`
- Exit code 1 אם יש בוט revoked (שימושי ל-CI / cron alerting)

### 3. Bot command — `/tokens` ב-`@SLH_macro_bot`
Admin only. מחזיר דוח סטטוס בטלגרם. **מוגבל**: בוט זה רואה רק את הטוקן של עצמו (`TELEGRAM_BOT_TOKEN`). שאר 11 הבוטים יסומנו ⚪ (`no_token_in_env`) כי ה-env vars שלהם לא מוגדרים בשירות הזה.

### 4. CLI manual — `pwsh ops/verify.ps1` (מהסשן הקודם)
מבצע את אותה בדיקה לטוקן הנוכחי בלבד. ה-`token_monitor.py` הוא הרחבה רב-בוטית.

## איך להפעיל דרך הבוט המרכזי שלך (`@SLH_Claude_bot`)

זה השלב שדורש שאישור גישה ל-`D:\SLH_ECOSYSTEM\slh-claude-bot\`. עד שזה יקרה, התשתית מחכה.

### מה הסוכן עם הגישה צריך לעשות:

1. **העתק את המודול:**
```bash
cp D:/SLH.co.il/ops/token_monitor.py D:/SLH_ECOSYSTEM/slh-claude-bot/token_monitor.py
cp D:/SLH.co.il/ops/tokens.json D:/SLH_ECOSYSTEM/slh-claude-bot/tokens.json
```
(או symlink — עדיף, כדי שעדכון ב-`SLH.co.il/ops/tokens.json` יתפשט אוטומטית.)

2. **הוסף את כל ה-env vars לשירות `slh-claude-bot` ב-Railway**:
```
GUARDIAN_BOT_TOKEN=<token של @Grdian_bot>
ACADEMIA_BOT_TOKEN=<token של @SLH_Academia_bot>
WALLET_BOT_TOKEN=...
EXPERTNET_BOT_TOKEN=...
FACTORY_BOT_TOKEN=...
BOTSHOP_BOT_TOKEN=...
TON_MNH_BOT_TOKEN=...
ADMIN_BOT_TOKEN=...
COMMUNITY_BOT_TOKEN=...
CAMPAIGN_BOT_TOKEN=...
TELEGRAM_BOT_TOKEN=<token של @SLH_macro_bot>  (כדי שגם זה ייבדק)
```
(כן, כל ה-12 על שירות אחד. זה Trade-off: השירות הזה הופך ל-vault ולכן צריך הקשחה — admin-only access, audit log.)

3. **הוסף command ל-`@SLH_Claude_bot`:**
```python
from token_monitor import check_all, render_telegram

async def tokens(update, context):
    statuses = await check_all()
    await update.message.reply_text(render_telegram(statuses), parse_mode='Markdown')

# ב-main():
app.add_handler(CommandHandler("tokens", tokens))
```

4. **הוסף scheduled check** (Railway cron / Windows Task / GitHub Actions):
```python
# ops/scheduled_token_check.py
import asyncio
from token_monitor import check_all
from telegram import Bot

async def run():
    statuses = await check_all()
    revoked = [s for s in statuses if s.state == "revoked"]
    if revoked:
        bot = Bot(token=os.getenv("CLAUDE_BOT_TOKEN"))
        msg = "🚨 *Token rotation needed:*\n" + "\n".join(f"• @{s.username}" for s in revoked)
        await bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=msg, parse_mode='Markdown')

asyncio.run(run())
```
הרץ דרך Railway cron (`*/5 * * * *` = כל 5 דקות) או Windows Scheduler.

5. **הוסף `/rotate <bot>` command** — interactive walkthrough:
```python
async def rotate(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /rotate <bot_name>\nExample: /rotate Grdian_bot")
        return
    target = context.args[0]
    # 1. Find in registry
    # 2. Open BotFather link
    # 3. Wait for user to paste new token (next message)
    # 4. Validate via getMe
    # 5. Update Railway env via Railway GraphQL API
    # 6. Verify post-update
    # 7. Audit log
    ...
```
**תכנון מפורט יותר ב-`ops/CONTROL_CENTER_DESIGN.md` Section 8.2** (כבר כתוב).

## שלבי המעבר ל-"always-on indication"

| שלב | מה צריך | זמן |
|-----|---------|-----|
| ✅ Phase 0 (זה) | tokens.json + token_monitor.py + `/tokens` ב-SLH_macro_bot | בוצע |
| ⏸ Phase 1 | אישור Osif לגישה ל-SLH_ECOSYSTEM/slh-claude-bot/ | 5 שניות |
| ⏸ Phase 2 | העברת המודול ל-Claude bot + הוספת כל הטוקנים כ-env vars שם | 30 דקות |
| ⏸ Phase 3 | scheduled cron כל 5 דקות + DM כשמישהו revoked | 1 שעה |
| ⏸ Phase 4 | `/rotate <bot>` interactive walkthrough כולל Railway API | 2-3 שעות (ראה Control Center spec) |
| ⏸ Phase 5 | Web dashboard `control.slh-nft.com/tokens` עם live grid | 4-6 שעות |

## הערות אבטחה

- ⚠️ **שירות עם כל הטוקנים = יעד תקיפה.** אם `@SLH_Claude_bot` נחשף — כל ה-25 בוטים נחשפים. הקשחות חובה:
  1. `ADMIN_TELEGRAM_IDS` env var — רק `224223270` (Osif) מורשה לפקודות (`/tokens`, `/rotate`)
  2. Railway service — לא לחשוף לפומבי (אין domain), polling-only
  3. Logs — לפלטר httpx logs כדי לא לכתוב tokens ל-Railway logs (זה כבר באג קיים)
  4. Pre-commit hook — כבר חוסם token patterns בכל commit (`.githooks/pre-commit`)

- ⚠️ **Railway API token** (`RAILWAY_API_TOKEN`) — נדרש כדי ש-`/rotate` יעדכן env vars אוטומטית. צור ב-https://railway.com/account/tokens, scope = workspace. שמור רק כ-env var, לא ב-code.

- ⚠️ **Audit log** — כל rotation חייב להיכתב ל-`token_rotations` table (`bot_name`, `rotated_by`, `rotated_at`, `success`). Phase 4.

## TL;DR לסוכן הבא

```
1. קרא: D:/SLH.co.il/ops/CONTROL_CENTER_DESIGN.md (Section 3.2 + 8.2)
2. קרא: D:/SLH.co.il/ops/TOKEN_MONITOR_README.md (זה)
3. קבל מ-Osif: אישור גישה ל-D:/SLH_ECOSYSTEM/slh-claude-bot/
4. קבל מ-Osif: רשימת ערכי env vars לטוקנים (אל תפרסם בצ'אט!)
5. הרץ Phase 1 → Phase 2 → Phase 3 בסדר.
6. דווח ל-Osif: רשימת בוטים שעובדים + רשימת בוטים שצריכים rotation.
```

המודול נבנה כדי לאפשר לכל סוכן עם הגישה המתאימה להמשיך מכאן בלי כתיבה מאפס.
