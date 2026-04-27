# SESSION HANDOFF — Token Rotation Pipeline (2026-04-26)

**Session goal:** בניית מערכת סיבוב טוקנים אוטומטית ומאובטחת — מהאתר, מהבוט, ומה-API — שמסבבת את 31 הבוטים + 6 secrets במערכת SLH דרך Railway GraphQL, עם audit log מלא, רמות אבטחה (4 tiers), ו-`setMyCommands` sync ל-BotFather.

**Status:** ✅ **מימוש מלא הושלם.** ממתין ל-2 פעולות ידניות של Osif לפני סיבוב חי ראשון.

---

## 1. Executive Summary

| מדד | ערך |
|-----|-----|
| Commits נכתבו (לא נדחפו) | 0 (לא בוצע push בכוונה — לא התבקש) |
| קבצים חדשים | **8** |
| קבצים שעודכנו | **6** |
| שורות קוד חדש | ~2,156 שורות (Python) + ~860 שורות (HTML/JS) + ~360 שורות (config + docs) |
| Endpoints חדשים | **3** (`POST /api/admin/rotate-bot-token-pipeline`, `GET /api/admin/rotation-history`, `GET /api/admin/rotation-pipeline/health`) |
| DB migrations | **2** (idempotent: `bot_catalog.tier` column + check constraint, `rotation_confirm_tokens` table) |
| Bots ב-config | **31** (8 critical, 5 high, 19 medium, 5 low) |
| Non-bot secrets ב-config | **6** (ADMIN_API_KEYS, ADMIN_BROADCAST_KEY, DATABASE_URL, ANTHROPIC_API_KEY, JWT_SECRET, RAILWAY_API_TOKEN) |
| Bot admin handlers נוספו | **12** (2 message, 10 callback) |
| Browser preview verification | ✅ tokens.html, rotate-token.html, rotation-history.html — נטענים נקי, אין שגיאות console |
| Module import smoke test | ✅ `routes.railway_client` + `routes.rotation_pipeline` + `slh-claude-bot/rotation_panel` יבוא נקי |

---

## 2. הרציונל — למה צריך את זה

**הבעיה לפני:** סיבוב טוקן אחד דרש 4 שלבים ידניים (BotFather → ‎`.env` מקומי → Railway Dashboard → restart). פגיעות ידועה: 10 סודות דלפו ב-chat (K-1 ב-`KNOWN_ISSUES.md`), 1/11 בלבד סובב. כל סיבוב = 5 דק' עבודה רגישה לשגיאות × 31 בוטים = ~2.5 שעות עבודה.

**הפתרון:** Pipeline אטומי שמבצע את כל השלבים בלחיצה אחת מ-3 משטחים זהים (Web modal / dedicated page / Telegram bot), כולל healthcheck post-deploy ו-`setMyCommands` sync. הטוקן לא נשמר בשום מקום — רק 4 ספרות אחרונות ל-audit.

**ההכרעה הארכיטקטונית הקריטית:** Railway CLI לא נגיש מתוך ה-API container בייצור. במקום CLI — **Railway GraphQL API** (`backboard.railway.app/graphql/v2`) עם `RAILWAY_API_TOKEN`. אומת לפי תיעוד Railway ב-`/integrations/api/manage-variables` (mutation `variableUpsert`) ו-`/integrations/api/manage-deployments` (mutation `deploymentRedeploy`).

---

## 3. קבצים — חדשים ומעודכנים

### 🆕 קבצים חדשים (8)

| Path | Lines | Bytes | Role |
|------|------:|------:|------|
| `config/railway_services.json` | 58 | 9,372 | מיפוי env_var → Railway (project/service/environment IDs + tier). 37 entries (31 bots + 6 secrets). IDs ריקים — `scripts/railway_resolve_ids.py` ימלא אוטומטית. |
| `config/bot_commands.json` | 67 | 3,327 | רישום `setMyCommands` per-handle. 3 default + 11 בוטים עם פקודות מותאמות (Hebrew descriptions). |
| `routes/railway_client.py` | 238 | 8,110 | async httpx GraphQL client. 4 פונקציות: `variable_upsert`, `service_redeploy`, `latest_deployment_id`, `health_probe`. כולל `_redact_value` belt-and-braces. |
| `routes/rotation_pipeline.py` | 584 | 24,793 | Pipeline אטומי בן 10 שלבים. 3 endpoints. כולל confirm-token table (60s TTL), tier-based cooldowns, security headers (`Cache-Control: no-store`, `X-Robots-Tag: noindex`), audit-log integration. |
| `website/admin/rotation-history.html` | 275 | 12,686 | viewer ל-audit log. 4 stats boxes, 7-column table, סינון לפי env_var/action/limit, CSV export, hash chain display. RTL, theme זהה ל-tokens.html. |
| `slh-claude-bot/rotation_panel.py` | 566 | 24,121 | aiogram inline-keyboard panel. 12 handlers. Token DM auto-delete, live progress streaming via edit_text, Critical-tier confirm flow. **CRITICAL FIX:** filter `_has_pending_rotation` מאפשר ל-AI conversation לעבוד נורמלית כשאין flow פעיל. |
| `scripts/railway_resolve_ids.py` | 198 | 6,717 | bootstrap script. שולף את כל הפרויקטים/שירותים/סביבות מ-Railway GraphQL וממלא את ה-IDs ב-`railway_services.json`. דרישה: `RAILWAY_API_TOKEN` ב-env. דגל `--write` לשמירה. |
| `ops/TOKEN_ROTATION_RUNBOOK.md` | 228 | 10,865 | runbook תפעולי מלא: setup חד-פעמי, 3 משטחי הפעלה, tier model, security model, failure modes + recovery, rotation order, endpoint reference, audit chain verification. |

### ✏️ קבצים שעודכנו (6)

| Path | שינוי |
|------|-------|
| `api/admin_bots_catalog.py` | + עמודת `tier TEXT NOT NULL DEFAULT 'medium'` עם CHECK constraint, idempotent ALTER + DO $$ block, אינדקס `ix_bot_catalog_tier`, seed automation לפי handle (critical: SLH_Claude/WEWORK_teamviwer; high: BotShop/Wallet/Spark/Admin/macro; low: Test/swap-targets). מודלים `BotIn`/`BotUpdate` קיבלו tier field. `_row_to_dict` מחזיר tier. `/stats` מחזיר `by_tier` dict. |
| `website/admin/tokens.html` | + עמודת Tier (4 ערכי badge צבעוניים), כפתור inline 🔄 Rotate שפותח modal pipeline (במקום redirect), modal עם token input + swap checkbox + live progress streaming, Critical-tier confirm flow, ESC לסגירת modal, לינק 📜 Audit ב-topbar. |
| `website/admin/rotate-token.html` | + bloc "מצב סיבוב" עם 2 רדיו: ⚡ Pipeline (default) / 🛡 PowerShell מקומי. כשמצב Pipeline נבחר — אחרי validate, מציג כפתור "🚀 בצע סיבוב מלא" שקורא לאותו endpoint כמו ה-modal של tokens.html. tier hint מוצג אחרי בחירת בוט (אם בוט מ-API). |
| `main.py` | + שני שורות (115, 309): `from routes.rotation_pipeline import router as rotation_pipeline_router` + `app.include_router(rotation_pipeline_router)` |
| `api/main.py` | identical to main.py — סונכרן per CLAUDE.md (Railway בונה מ-root, אבל api/main.py הוא dev copy). |
| `slh-claude-bot/bot.py` | + ייבוא + register של `rotation_panel`, **לפני** railway_ops, **לפני** ה-`F.text` handler של AI. Filter cascade fix מאפשר ל-AI handler לרוץ כשאין rotation pending. |

---

## 4. ארכיטקטורה — תרשים זרימה

```
┌────────────────────────────────────────────────────────────────────┐
│  3 משטחי משתמש (זהים מבחינת backend)                             │
│                                                                    │
│  /admin/         /admin/tokens.html          @SLH_Claude_bot      │
│  rotate-token    inline 🔄 Rotate            /admin → 🔐 Tokens   │
│  (mode toggle)   button per row              inline keyboard      │
└──────────────┬───────────────┬────────────────────┬───────────────┘
               │               │                    │
               └───────────────┴────────────────────┘
                               │
                               ▼
   ┌──────────────────────────────────────────────────────────────┐
   │  POST /api/admin/rotate-bot-token-pipeline                  │
   │  routes/rotation_pipeline.py — 10 שלבים אטומיים             │
   │                                                              │
   │  0. Lookup tier מ-bot_catalog OR services config            │
   │  0a. Cooldown check (per-tier: 0/60/300/900s)               │
   │  1. Critical tier? Issue confirm_token (60s TTL)            │
   │  2. Telegram getMe(new_token) — validate                    │
   │  3. Audit: secret.rotate.initiated                          │
   │  4. Railway GraphQL: variableUpsert (skipDeploys=true)      │
   │  5. Railway GraphQL: deploymentRedeploy (latest deploy)     │
   │  6. asyncio.sleep(8) + healthcheck getMe(new_token)         │
   │  7. UPDATE bot_catalog SET last_rotated_at = NOW()          │
   │  8. setMyCommands sync (best-effort, non-blocking)          │
   │  9. Audit: secret.rotate.pushed                             │
   │ 10. Broadcast ל-ADMIN_TELEGRAM_IDS                          │
   └────────────────────────────────────────┬─────────────────────┘
                                            │
                                            ▼
        ┌──────────────────────────────────────────────────┐
        │  Side-effects                                    │
        │  • institutional_audit (hash-chained)            │
        │  • bot_catalog.last_rotated_at + telegram_bot_id │
        │  • events table → /api/events/public             │
        │  • Railway: variable updated + redeploy          │
        │  • BotFather: setMyCommands echoed               │
        │  • Telegram: broadcast sent                      │
        └──────────────────────────────────────────────────┘
```

---

## 5. Tier Model — שכבות אבטחה

| Tier | דוגמאות | Confirm | Cooldown | Audit | Broadcast |
|------|---------|---------|----------|-------|-----------|
| 🚨 **critical** | `SLH_CLAUDE_BOT_TOKEN`, `ACADEMIA_BOT_TOKEN`, `ADMIN_API_KEYS`, `DATABASE_URL`, `ANTHROPIC_API_KEY`, `JWT_SECRET`, `ADMIN_BROADCAST_KEY`, `RAILWAY_API_TOKEN` | 60s window | 15 min | מלא | כל ADMIN_TELEGRAM_IDS |
| ⚠️ **high** | `BOTSHOP_BOT_TOKEN`, `WALLET_BOT_TOKEN`, `CORE_BOT_TOKEN`, `ADMIN_BOT_TOKEN`, `TELEGRAM_BOT_TOKEN` (macro) | אין | 5 min | מלא | כן |
| 🔹 **medium** | רוב הבוטים האופרטיביים (19 בוטים) | אין | 1 min | מלא | אין |
| ⚪ **low** | `TEST_BOT_TOKEN`, swap-targets (Match, Wellness, UserInfo, TS_Set) | אין | אין | בסיסי | אין |

ה-tier נשמר ב-`bot_catalog.tier` (לבוטים) ובתוך `config/railway_services.json` (לכולם). ניתן לעריכה דרך `PATCH /api/admin/bots/{id}` או SQL ידני.

---

## 6. אבטחה — מה לא יוצא מהזיכרון, מה כן נשמר

### ❌ אף פעם לא נשמר / לוגג / מוחזר ב-response
- ערך מלא של הטוקן
- request body של `/api/admin/rotate-bot-token-pipeline` (אין FastAPI access log לזה כברירת מחדל)
- כל substring שדומה ל-token (מכוסה ע"י `_redact()` בכל error path)

### ✅ נרשם ב-`institutional_audit` (hash-chained)
- `actor_user_id` — מי טריגר
- `resource_id` — שם ה-env_var
- `before_state.last_rotated_at` — timestamp קודם
- `after_state.last4` — 4 ספרות אחרונות בלבד
- `after_state.tg_bot_id` — Telegram numeric ID (לא הטוקן)
- `after_state.deploy_id` — Railway deployment id
- `metadata.tier` / `metadata.swap` / `metadata.handle`
- `entry_hash` — קישור ל-row הקודם (תיעודי-תקפות)

### Defense in depth (10 layers)
1. **TLS only** — Railway-managed cert
2. **Admin auth** — `_require_admin` (env keys + DB-rotated hashed)
3. **Critical tier confirm** — 60s `confirm_token` round-trip, one-shot
4. **Per-tier cooldown** — in-memory ‏`_LAST_ROTATION_TS`
5. **Pre-validation** — `getMe` לפני הדחיפה ל-Railway
6. **Post-deploy healthcheck** — `getMe` שוב 8s אחרי redeploy
7. **Output redaction** — `_redact()` בכל raise/return path
8. **Response headers** — `Cache-Control: no-store` + `X-Robots-Tag: noindex` + `Pragma: no-cache` + `X-Content-Type-Options: nosniff` + `Referrer-Policy: no-referrer`
9. **Bot DM auto-delete** — `bot.delete_message()` מיד אחרי קבלת טוקן ב-Telegram
10. **Hash-chained audit** — `institutional_audit.entry_hash`

---

## 7. ⚠️ פעולות ידניות שנותרו לפני סיבוב חי

### Step 1 — Generate Railway API token (חד-פעמי)
1. פתח https://railway.com/account/tokens
2. New Token → name: `slh-rotation-pipeline` → Create
3. העתק את הערך (פעם אחת — לא יוצג שוב)

### Step 2 — הגדר על Railway של slh-api
1. https://railway.com/project/slh-api → Variables → New Variable
2. Key: `RAILWAY_API_TOKEN`, Value: paste from Step 1
3. שמור — Railway יעשה redeploy אוטומטי

### Step 3 — פתור IDs לתוך config (רץ פעם אחת מקומית)
```powershell
$env:RAILWAY_API_TOKEN = "<paste>"
cd D:\SLH_ECOSYSTEM
python scripts\railway_resolve_ids.py            # dry-run, מציג מה ימולא
python scripts\railway_resolve_ids.py --write    # שומר ל-JSON
```
הסקריפט שולף את כל 5 הפרויקטים מ-Railway, מתאים לפי `project` + `service` + `environment` ב-config, ומדפיס diff ל-stdout. שורה לא נפתרה = שם project/service ב-config לא תואם בדיוק לשם ב-Railway — פתור ידנית.

### Step 4 — Commit + push
```powershell
cd D:\SLH_ECOSYSTEM
git add config/railway_services.json config/bot_commands.json `
        routes/railway_client.py routes/rotation_pipeline.py `
        api/admin_bots_catalog.py api/main.py main.py `
        slh-claude-bot/rotation_panel.py slh-claude-bot/bot.py `
        scripts/railway_resolve_ids.py `
        ops/TOKEN_ROTATION_RUNBOOK.md ops/SESSION_HANDOFF_20260426_TOKEN_ROTATION.md

git commit -m "feat(rotation): atomic token rotation pipeline (Railway GraphQL + tier model + bot panel)

Adds:
- routes/rotation_pipeline.py: POST /api/admin/rotate-bot-token-pipeline
- routes/railway_client.py: async GraphQL client (variableUpsert, deploymentRedeploy)
- 4 security tiers (critical/high/medium/low) with confirm-token gate for critical
- tier column on bot_catalog, idempotent migration with seed defaults
- /admin/tokens.html: tier badge + inline rotate modal
- /admin/rotate-token.html: Pipeline / Local mode toggle
- /admin/rotation-history.html: audit log viewer (hash-chained)
- slh-claude-bot/rotation_panel.py: full BotFather-style admin panel (12 handlers)
- config/bot_commands.json: setMyCommands sync registry
- ops/TOKEN_ROTATION_RUNBOOK.md: operations reference

Token never persisted; only last4 + tg_bot_id stored in institutional_audit.
Cache-Control: no-store on all pipeline responses.
"
cd website
git add admin/tokens.html admin/rotate-token.html admin/rotation-history.html
git commit -m "feat(admin): token rotation UI (Pipeline mode + history viewer)"
git push
cd ..
git push
```

### Step 5 — Push website (separate repo)
```powershell
cd D:\SLH_ECOSYSTEM\website
git push  # branch main → GitHub Pages auto-deploy
```

### Step 6 — אימות אחרי deploy
```powershell
# (1) Pipeline health check
$ADMIN = (Get-Content D:\SLH_ECOSYSTEM\.env | Select-String 'ADMIN_API_KEY=').ToString().Split('=')[1]
curl.exe -H "X-Admin-Key: $ADMIN" https://slh-api-production.up.railway.app/api/admin/rotation-pipeline/health
# Expected:
# {
#   "config_loaded": true,
#   "config_entries": 37,
#   "railway_token_ok": true,
#   "railway_me_email": "osif.erez.ungar@gmail.com",
#   "broadcast_bot_token_set": true,
#   "admin_telegram_ids_count": 2
# }

# (2) Verify tier column migrated
curl.exe -H "X-Admin-Key: $ADMIN" https://slh-api-production.up.railway.app/api/admin/bots/stats
# Expected: by_tier breakdown

# (3) Open admin pages — verify they load + show tier badges
start https://slh-nft.com/admin/tokens.html
start https://slh-nft.com/admin/rotation-history.html
```

---

## 8. סיבוב ראשון — איך לבצע (recommended order)

**הזהב הוא:** התחל מ-`TEST_BOT_TOKEN` (Low tier, swap-target — אין סיכון לפרודקשן), אמת שהכל עובד end-to-end, ואז עלה במעלה ה-tiers.

### A. Web (מהיר ביותר):
1. https://slh-nft.com/admin/tokens.html
2. מצא את שורת `@SLH_Test_bot` (TEST_BOT_TOKEN)
3. לחץ **🔄 Rotate**
4. ב-modal: paste טוקן חדש מ-BotFather (אחרי revoke), אל תסמן swap mode
5. לחץ **🚀 בצע סיבוב**
6. צפה ב-progress feed: validate → push → redeploy → healthcheck → setMyCommands → done
7. לאחר הצלחה: https://slh-nft.com/admin/rotation-history.html — רשומה חדשה ב-top

### B. Telegram bot:
1. שלח `/admin` ל-@SLH_Claude_bot
2. tap **🔐 Tokens** → רואה את 31 הבוטים ממוינים tier→staleness
3. tap **@SLH_Test_bot** → רואה bot detail card
4. tap **🔄 סובב טוקן** → הבוט מבקש טוקן בהודעה הבאה
5. paste את הטוקן → ההודעה נמחקת אוטומטית מהצ'אט (אבטחה)
6. הבוט מציג live progress עד הצלחה

### C. curl (לדיבוג):
```powershell
curl.exe -X POST https://slh-api-production.up.railway.app/api/admin/rotate-bot-token-pipeline `
  -H "X-Admin-Key: $ADMIN" `
  -H "Content-Type: application/json" `
  -d '{"env_var":"TEST_BOT_TOKEN","new_token":"<NEW>","expect_handle":"@SLH_Test_bot"}'
```

### Recommended sweep order
1. **Low** (5 בוטים): TEST, MATCH, WELLNESS, USERINFO, TS_SET — בדוק שה-pipeline עובד
2. **Medium** (19 בוטים): GUARDIAN, FACTORY, AIRDROP, CAMPAIGN, FUN, GAME, TON_MNH, SLH_TON, LEDGER, OSIF_SHOP, NIFTI_PUBLISHER, CHANCE_PAIS, NFTY_MADNESS, CRAZY_PANEL, MY_NFT_SHOP, BEYNONIBANK, EXPERTNET, SLH_AIR, G4ME
3. **High** (5 בוטים): BOTSHOP, WALLET, CORE, ADMIN, TELEGRAM (macro)
4. **Critical** (8 secrets): SLH_CLAUDE, ACADEMIA, ADMIN_API_KEYS, DB_URL, ANTHROPIC, JWT, BROADCAST_KEY, RAILWAY_API_TOKEN — צפה ל-60s confirm

⚠️ **DATABASE_URL ו-RAILWAY_API_TOKEN דורשים זהירות נוספת:**
- DATABASE_URL: Postgres credentials. סיבוב דורש שינוי credentials ב-DB עצמו ולא רק ב-Railway env. **המלצה: ידני דרך Railway Dashboard בלבד** (סומן `_warn` ב-config).
- RAILWAY_API_TOKEN: chicken-and-egg — אם תסבב אותו דרך ה-pipeline ויש כשל, ה-pipeline לא יוכל לחזור אחורה. **המלצה: ידני בלבד דרך Dashboard** (גם סומן `_warn`).

---

## 9. Failure Modes — מתי מה קורה

| כשל | מצב מערכת | Audit | Recovery |
|-----|------------|-------|----------|
| Token validation נכשל | ללא שינוי | `phase: validate` | בדוק שהעתקת מ-BotFather נכונה; נסה שוב |
| Handle mismatch | ללא שינוי | `phase: handle_mismatch` | במכוון? סמן `swap_mode: true`. אחרת, בחר את הבוט הנכון |
| Railway push נכשל | ללא שינוי (Variable לא הוחלף) | `phase: railway_push` | בדוק `RAILWAY_API_TOKEN` תקף + IDs מלאים ב-config |
| Railway redeploy נכשל | **Variable כן הוחלף**, deployment ישן | `phase: railway_redeploy` + broadcast `⚠️ סיבוב חלקי` | `railway redeploy --service X --yes` ידני, או Dashboard → Deployments → Redeploy |
| Healthcheck נכשל | Variable + deploy חדשים, בוט down | `secret.rotate.healthcheck_failed` + broadcast רועש | `railway logs --service X --tail 100` → אם הטוקן באמת רע: revoke ב-BotFather + סובב מחדש; או דרך Dashboard החזר deployment קודם |
| setMyCommands נכשל | רוטציה הצליחה, רק התפריט לא סונכרן | warning בלוג | non-blocking; ירוץ שוב בסיבוב הבא |

---

## 10. Endpoint Reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/admin/rotate-bot-token-pipeline` | X-Admin-Key | Pipeline אטומי. Body: `{env_var, new_token, expect_handle?, swap_mode?, confirm_token?, skip_healthcheck?}` |
| `GET` | `/api/admin/rotation-history` | X-Admin-Key | audit log query. Query params: `limit` (1..500, default 50), `env_var?`, `action?` |
| `GET` | `/api/admin/rotation-pipeline/health` | X-Admin-Key | self-check (config + Railway token + bot tokens) |
| `GET` | `/api/admin/bots` | X-Admin-Key | קטלוג עם tier |
| `GET` | `/api/admin/bots/stats` | X-Admin-Key | aggregate counts כולל `by_tier` |
| `PATCH` | `/api/admin/bots/{id}` | X-Admin-Key | update bot fields כולל tier |
| `POST` | `/api/admin/bots/{id}/mark-rotated` | X-Admin-Key | manual mark (legacy, לא דורש pipeline) |

---

## 11. Bot Admin Panel — UX Map

```
@SLH_Claude_bot:
  /admin                    # entry point
    ├── 🔐 Tokens           # paginated bot list, sorted tier→staleness
    │   └── @<bot>          # detail card + actions
    │       ├── 🔄 סובב טוקן    # standard rotation
    │       ├── 🔁 Swap mode    # rotation עם swap_mode=true
    │       ├── ⬅ לרשימת בוטים
    │       └── 🏠 תפריט
    ├── 🚂 Railway          # bridge to /railway_* commands
    ├── 📊 Pipeline status  # config_loaded + railway_token_ok + by_tier
    └── 📜 Audit            # last 10 rotation events
```

**Token input flow (security-hardened):**
1. User taps `🔄 סובב טוקן` → bot prompts for token
2. User pastes token in next message
3. Bot **immediately deletes** the user's message (`bot.delete_message`)
4. Bot validates format + POSTs to pipeline
5. Critical tier? Bot shows `✅ אשר וסובב (60s)` button → tap → execute
6. Live progress streamed via single `edit_text` call

**Pending state TTL:** 5 דקות. אם לא נשלח טוקן בזמן — flow timeout, חזרה ל-AI conversation regular.

**Filter cascade fix:** `_has_pending_rotation` filter מחזיר False אם אין flow פעיל למשתמש, מה שמאפשר ל-`F.text` handler ב-bot.py (AI conversation) לטפל בהודעה רגילה. בלי זה, כל הודעת טקסט הייתה "נבלעת" ע"י ה-rotation handler.

---

## 12. DB Schema Changes

### `bot_catalog` — added column
```sql
ALTER TABLE bot_catalog
ADD COLUMN IF NOT EXISTS tier TEXT NOT NULL DEFAULT 'medium';

-- CHECK constraint via DO block (idempotent across re-deploys)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'bot_catalog_tier_chk'
    ) THEN
        ALTER TABLE bot_catalog
        ADD CONSTRAINT bot_catalog_tier_chk
        CHECK (tier IN ('critical', 'high', 'medium', 'low'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_bot_catalog_tier ON bot_catalog (tier);

-- Seed (idempotent — only updates rows still at default 'medium')
UPDATE bot_catalog SET tier = 'critical' WHERE tier = 'medium' AND handle IN
    ('@SLH_Claude_bot', '@WEWORK_teamviwer_bot');
UPDATE bot_catalog SET tier = 'high' WHERE tier = 'medium' AND handle IN
    ('@SLH_BotShop_bot', '@SLH_Wallet_bot', '@SLH_Spark_bot', '@SLH_Admin_bot', '@SLH_macro_bot');
UPDATE bot_catalog SET tier = 'low' WHERE tier = 'medium' AND
    (handle = '@SLH_Test_bot' OR status = 'swap-target');
```

### New table — `rotation_confirm_tokens` (Critical tier confirm gate)
```sql
CREATE TABLE IF NOT EXISTS rotation_confirm_tokens (
    confirm_token  TEXT PRIMARY KEY,
    env_var        TEXT NOT NULL,
    actor          TEXT NOT NULL,
    expires_at     TIMESTAMPTZ NOT NULL,
    used           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_rotation_confirm_expires ON rotation_confirm_tokens (expires_at);
```

TTL 60 שניות. ניקוי אוטומטי בכל קריאה (`DELETE WHERE expires_at < NOW()`).

### `institutional_audit` — new action types
- `secret.rotate.initiated`
- `secret.rotate.pushed` (success)
- `secret.rotate.failed` (with `phase: validate|handle_mismatch|railway_push|railway_redeploy`)
- `secret.rotate.healthcheck_failed`
- `secret.rotate.setmycommands_synced`
- `secret.rotate.rolled_back` (reserved for future Phase 8 auto-rollback)

---

## 13. Verification — Smoke Test Trace

```
Phase 1 (foundation) verification:
  ✓ config/railway_services.json loaded: 37 entries
    by tier: critical=8, high=5, medium=19, low=5
  ✓ config/bot_commands.json loaded: 3 default + 11 per-bot
  ✓ routes.railway_client imports clean
  ✓ railway_client.lookup_service('TEST_BOT_TOKEN') → returns project/service
    (with empty IDs — needs scripts/railway_resolve_ids.py)

Phase 2 (pipeline) verification:
  ✓ routes.rotation_pipeline imports clean
  ✓ Endpoints registered:
      POST /api/admin/rotate-bot-token-pipeline
      GET  /api/admin/rotation-history
      GET  /api/admin/rotation-pipeline/health
  ✓ Security headers stamped: Cache-Control, Pragma, X-Robots-Tag, ...
  ✓ Cooldowns: critical=900s, high=300s, medium=60s, low=0s
  ✓ Confirm TTL: 60s | Healthcheck delay: 8s
  ✓ main.py + api/main.py both wired (line 115 import, line 309 include)

Phase 3 (web UI) verification (browser preview):
  ✓ /admin/rotation-history.html renders (title, 7-col table, 4 stat boxes, 5 filters)
  ✓ /admin/tokens.html renders (Tier column, modal exists, openRotateModal+executeRotation defined, '📜 Audit' nav link)
  ✓ /admin/rotate-token.html renders (mode toggle: pipeline default, pipeline-card hidden until validate, tier-hint exists)
  ✓ Zero console errors

Phase 4 (bot panel) verification:
  ✓ rotation_panel module loads
  ✓ register() registers 2 message handlers + 10 callback handlers
  ✓ on_token_input has 2 filters (F.text predicate + _has_pending_rotation)
    → AI conversation falls through correctly when no rotation pending
```

---

## 14. ידוע / מגבלות / Phase 8

### ידוע
- IDs ב-`config/railway_services.json` ריקים — חייב לרוץ `railway_resolve_ids.py --write` פעם אחת אחרי setup.
- אין auto-rollback ב-MVP. אם healthcheck נכשל, broadcast רועש לאדמינים, recovery ידני.
- Cooldowns in-memory בלבד — מתאפסים ב-restart. לא בעיה כי ה-audit log הוא source of truth ל-rate limiting היסטורי.
- DATABASE_URL ו-RAILWAY_API_TOKEN מסומנים `_warn: true` ב-config — לא לסבב דרך ה-pipeline (chicken-and-egg).
- Telegram setMyCommands משתמש ב-token החדש (אחרי שאומת). אם token חדש בעייתי באופן עדין שלא נתפס ע"י getMe, setMyCommands ייכשל אבל הרוטציה נחשבת מוצלחת (כי ה-bot כן עונה ל-getMe).

### Phase 8 — שיפורים עתידיים אם הצורך עולה
1. **Auto-rollback** — שמירת hash של old value ב-memory לחלון 30 שניות, אם healthcheck נכשל → restore + redeploy
2. **Webhook for setMyCommands across all bots** — script שמסנכרן את כל ה-31 בוטים בלי סיבוב (נדרש כל הטוקנים לרגע — מסוכן)
3. **Tier editor in `/admin/tokens.html`** — UI dropdown ב-modal העריכה (כעת רק PATCH API)
4. **Slack/Email broadcast** — בנוסף ל-Telegram, לכשל Critical
5. **Rate limit פר-actor** (לא רק פר-env_var) — הגנה מפני actor חמסן

---

## 15. ניצול זמן — Budget Reality

| Phase מתוכנן | זמן מתוכנן | זמן בפועל |
|--------------|-----------|-----------|
| Phase 1: Foundation | 2h | ~1.5h |
| Phase 2: Backend pipeline | 3h | ~1.5h |
| Phase 3: Web UI | 2h | ~1.5h |
| Phase 4: Bot admin panel | 3h | ~1.5h (כולל filter cascade fix) |
| Phase 5: BotFather sync | 1h | ~0.3h |
| Phase 6: Security hardening | 1h | ~0.3h |
| Phase 7: E2E + runbook | 2h | ~1h (כתיבת runbook + handoff זה) |
| **סה"כ** | **14h** | **~7.5h** (סשן יחיד) |

---

## 16. Critical Files — אינדקס מהיר

```
D:\SLH_ECOSYSTEM\
├── config\
│   ├── railway_services.json        ← מיפוי 37 env_vars
│   └── bot_commands.json            ← setMyCommands per-bot
├── routes\
│   ├── railway_client.py            ← GraphQL client
│   ├── rotation_pipeline.py         ← THE pipeline endpoint
│   └── admin_rotate.py              ← (קיים, לא נוגעו) admin key rotation
├── api\
│   ├── admin_bots_catalog.py        ← + tier column migration
│   └── main.py                      ← + include rotation_pipeline_router
├── main.py                          ← + include rotation_pipeline_router (Railway builds from here)
├── website\admin\
│   ├── tokens.html                  ← + tier column + 🔄 Rotate modal
│   ├── rotate-token.html            ← + mode toggle (Pipeline/Local)
│   └── rotation-history.html        ← NEW audit viewer
├── slh-claude-bot\
│   ├── rotation_panel.py            ← NEW bot panel (12 handlers)
│   └── bot.py                       ← + register rotation_panel
├── scripts\
│   └── railway_resolve_ids.py       ← bootstrap helper
└── ops\
    ├── TOKEN_ROTATION_RUNBOOK.md    ← operations reference
    └── SESSION_HANDOFF_20260426_TOKEN_ROTATION.md  ← THIS FILE
```

---

## 17. הבא בתור — אחרי deploy ראשון מוצלח

- [ ] ✅ Set `RAILWAY_API_TOKEN` ב-Railway (Step 2)
- [ ] ✅ Run `railway_resolve_ids.py --write` (Step 3)
- [ ] ✅ Commit + push (Step 4-5)
- [ ] ✅ Verify `/api/admin/rotation-pipeline/health` returns `railway_token_ok: true`
- [ ] 🔄 סיבוב ראשון על `TEST_BOT_TOKEN` (Low tier) — אימות end-to-end
- [ ] 🔄 סיבוב על שאר ה-Low tier (4 בוטים)
- [ ] 🔄 סבב Medium tier (19 בוטים) — יום עבודה
- [ ] 🔄 סיבוב High tier (5 בוטים) — broadcast לאדמינים
- [ ] 🔄 סיבוב Critical tier (8 secrets) — צפה ל-60s confirm
- [ ] 🗒 עדכן `ops/KNOWN_ISSUES.md` — סמן K-1 (10 secrets exposed) כ-resolved
- [ ] 🗒 עדכן `MEMORY.md` — הוסף הפניה ל-handoff זה

---

**Author:** Claude (Sonnet 4.5)
**Date:** 2026-04-26
**Branch:** local (לא נדחף — Osif יבצע commit ו-push דרך Step 4 ב-runbook)
**Plan file:** `C:\Users\Giga Store\.claude\plans\iridescent-popping-lampson.md`
**Successor:** `ops/TOKEN_ROTATION_RUNBOOK.md` — ה-reference התפעולי הקנוני להלן.
