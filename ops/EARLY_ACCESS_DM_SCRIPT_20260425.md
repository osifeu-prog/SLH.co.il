# SLH AI Spark — Early Access DM Script

**Purpose:** Personal DMs to 4-5 community members offering Pro tier free for 30 days in exchange for honest feedback. Real signal > broadcast.

**Goal of the outreach:**
1. 1-2 actual paying users at end of trial (₪29 × 30d = first MRR)
2. 5-10 pieces of feedback on what works / what doesn't
3. 3 case studies for marketing

**Activation flow:** when someone says yes → run in @SLH_Claude_bot:
```
/grandfather <their_telegram_id> 30 pro
```

---

## Recipients (priority order)

Based on `ops/CONTROL.md` § Active Users + memory `project_users_apr2026.md`:

| # | Name | Telegram ID | Why this person |
|---|------|-------------|-----------------|
| 1 | **Tzvika Kaufman** | 1185887485 | Co-founder, crypto trader — knows the ecosystem, will give serious feedback |
| 2 | **Zohar Shefa Dror** | (in DB — `/api/ops/reality.users`) | Active contributor, asks good QA questions |
| 3 | **Eli** | (in DB) | Verified contributor, lower friction to ask |
| 4 | **Yakir Lisha** | (in DB) | Verified contributor |
| 5 | **Idan** | (in DB) | IT — would benefit from executor commands |

For Telegram IDs you don't have ready, look up via:
```bash
docker exec slh-postgres psql -U postgres -d railway -c "SELECT user_id, username, first_name FROM users WHERE first_name ILIKE '%<name>%';"
```

---

## DM Template — Hebrew (copy-paste-ready)

> היי <שם>, מה נשמע?
>
> הוצאתי פרויקט קטן שאני רוצה לבדוק עליו לפני שאני פותח אותו לקהל הרחב — בוט AI אישי בטלגרם, מבוסס Claude (אותו AI מאחורי anthropic), עם גישה ל-tools של בדיקות מערכת, עריכת קבצים, git, ואינטגרציה ישירה למערכת SLH שלי.
>
> זה הולך לעלות ₪29/חודש (חבילת Pro = 70 הודעות עם Claude מלא + tools). אני מחפש 4-5 משתמשים שיקבלו את זה **חינם לחודש** — בתמורה לחוות דעת כנה: מה עבד, מה לא, מה הייתם משדרגים.
>
> אם אתה אוהב — הנה הקישור: https://t.me/SLH_Claude_bot
>
> שלח /start כשתיכנס ואני אגדיר אותך ידנית ל-Pro tier. אחרי 30 יום נדבר.
>
> משוב = 3 הודעות בכל שלב. שווה לך?
>
> — אוסיף

---

## DM Template — alternate version (more casual / for closer friends)

> אחי <שם> 👋
>
> סוג של "alpha test" — בוט AI שיודע לערוך לי את האתר, לעשות deploy, לבדוק health, לרוץ פקודות גיט — הכל מהטלגרם. אני רוצה שתנסה אותו בלי תשלום לחודש.
>
> בתמורה: 3 משובים בכל שלב — מה אהבת, מה לא, מה היית מוסיף.
>
> https://t.me/SLH_Claude_bot
>
> שלח /start ואני אעשה לך אקטיבציה. תפעל איתו, תשבור אותו, תחזור אלי.

---

## Follow-up flow

**אחרי שאדם נכנס לבוט:**
1. קח את ה-`from_user.id` מהלוגים: `docker logs slh-claude-bot --tail 50 | grep "<their_username>"`
2. הענק Pro: `/grandfather <id> 30 pro` (בDM של הבוט)
3. שלח לו DM: *"אקטיבציה הושלמה. שלח /credits לראות שהכל עובד. ספר לי מה עוצר אותך מלהשתמש בכל יום."*

**אחרי שבוע:**
- שלח: *"שבוע ראשון. מה הוא הדבר אחד שאתה רוצה שיעבוד אחרת?"*

**אחרי 30 יום:**
- שלח: *"חבילת ה-Pro חינם נגמרת ב-X. רוצה להמשיך ב-₪29/חודש? או שזה לא בשבילך — ובמה?"*
- אם כן → /upgrade pro (הם משלמים בStars)
- אם לא → תיעד את הסיבה — זה הסיגנל הכי חשוב

---

## Tracking — מה לעקוב

צור קובץ `ops/EARLY_ACCESS_TRACKER.md` (או table ב-`ambassador_contacts` CRM):

| Telegram | DM sent | Replied | Activated | Active days | Feedback rounds | Decision @ d30 | Notes |
|----------|---------|---------|-----------|-------------|-----------------|----------------|-------|
| @tzvika21truestory | 2026-04-?? | | | | | | |
| @zohar_? | | | | | | | |

יעד: 5/5 activated, 3/5 paid at d30, 4/5 left honest feedback.

---

## Scripts to NOT use (anti-patterns)

❌ **Mass broadcast** — bot DMs that don't feel personal get 0% engagement (verified per OUTREACH_BATCH_20260424).
❌ **"This is the future, you have to try it"** — over-selling kills credibility.
❌ **No clear ask** — vague "tell me what you think" gets vague replies. Specify: 3 messages × 3 dimensions.
❌ **Sending all 5 at once** — space them 2-3 hours apart, customize the opener for each.

---

**Operator's job:** copy template, replace `<name>`, send to one person, wait for reply, then `/grandfather` them, then move to next.

**Time budget:** 5 min per send × 5 = 25 min total. Replies trickle in over 24h.

**My job:** when /grandfather is called, the system handles activation + tracking. When /credits is hit by them, log the engagement.
