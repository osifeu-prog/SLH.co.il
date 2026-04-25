# Phase B — AI Spark Postgres Mirror (handoff to next session)

**Why:** Right now AI Spark subscription state lives in `slh-claude-bot/sessions.db` (SQLite, local). The Mini App widget on `slh-nft.com/miniapp/dashboard.html` shows STATIC tier comparison + deep-links to bot. Goal of Phase B: show LIVE tier + quota in the Mini App, no bot redirect needed.

**Status:** Not started. ~60 min of careful work. Touches 3 systems.

---

## Architecture

```
                        ┌────────────────────┐
                        │ Telegram user opens │
                        │  Mini App from bot   │
                        └──────────┬───────────┘
                                   │ initData (signed by Telegram)
                                   ▼
                  ┌─────────────────────────────┐
                  │ slh-nft.com/miniapp/        │
                  │   dashboard.html            │
                  │   • parses initData          │
                  │   • fetches /api/ai_spark/   │
                  │     credits/{user_id}        │
                  └──────────┬──────────────────┘
                             │ HTTPS
                             ▼
                  ┌─────────────────────────────┐
                  │ slh-api (FastAPI on Railway) │
                  │   GET /api/ai_spark/credits  │
                  │   • verifies initData (HMAC) │
                  │   • SELECT tier, quota_used  │
                  │     FROM ai_spark_subs       │
                  │     WHERE user_id=X          │
                  └──────────┬──────────────────┘
                             │ psycopg
                             ▼
                  ┌─────────────────────────────┐
                  │ Railway Postgres            │
                  │   table ai_spark_subs        │
                  │   (mirrored from bot SQLite) │
                  └──────────▲──────────────────┘
                             │ dual-write (best-effort)
                             │
                  ┌──────────┴──────────────────┐
                  │ slh-claude-bot              │
                  │   subscriptions.py          │
                  │   • on upgrade/usage:        │
                  │     - SQLite (canonical)     │
                  │     - PG (mirror, can fail)  │
                  └─────────────────────────────┘
```

**Why dual-write (not single source):**
- Bot must keep working if Railway Postgres is unreachable (network issue, redeploy, etc.)
- SQLite stays canonical for quota.check (latency-sensitive)
- Postgres is read-only mirror for the dashboard widget

---

## Step-by-step (estimated 60 min)

### 1. Add table to Postgres (5 min)
```sql
-- run via railway shell on Postgres service
CREATE TABLE IF NOT EXISTS ai_spark_subscriptions (
    user_id                       BIGINT PRIMARY KEY,
    tier                          TEXT NOT NULL DEFAULT 'free',
    current_period_start          TIMESTAMP NOT NULL DEFAULT NOW(),
    current_period_end            TIMESTAMP NOT NULL,
    messages_used_this_period     INTEGER NOT NULL DEFAULT 0,
    quota_total                   INTEGER NOT NULL DEFAULT 10,
    payment_provider              TEXT,
    last_synced_at                TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ai_spark_subs_period_end
    ON ai_spark_subscriptions(current_period_end);
```

### 2. Add Postgres mirror to bot (15 min)
- New file: `slh-claude-bot/subscriptions_pg.py`
  - Async psycopg connection pool
  - `mirror_upgrade(user_id, tier, period_end, ...)` — UPSERT
  - `mirror_increment(user_id)` — UPDATE counter
- Wire into existing `subscriptions.py`:
  - After successful SQLite write, call mirror_* in try/except
  - Log on failure, don't raise
- Add `psycopg2-binary>=2.9` to `requirements.txt`
- Add `DATABASE_URL` to bot's `.env` (or pass via docker-compose env)

### 3. Add API endpoint (15 min)
- File: `D:\SLH_ECOSYSTEM\api\main.py`
- New route: `GET /api/ai_spark/credits/{user_id}`
  - Validates `X-Telegram-Init-Data` header (existing helper)
  - Confirms initData.user.id == user_id (anti-tampering)
  - SELECT from `ai_spark_subscriptions`
  - Return JSON: `{tier, quota_used, quota_total, period_end, status}`
  - If user not in table: return tier='free', quota_used=0, quota_total=10
- **REMEMBER: `cp api/main.py main.py` before commit** (Railway builds from root)
- Push slh-api master → Railway auto-deploys

### 4. Update dashboard.html widget (15 min)
- File: `D:\SLH_ECOSYSTEM\website\miniapp\dashboard.html`
- In the existing `#ai-spark-card` div:
  - Add fetch on page load (use the existing `wrapFetchForGateway` for initData header)
  - Replace static tier cards with: current tier highlighted + quota progress bar
  - Keep static comparison as a "details" expand if user is Free
- Push to `osifeu-prog.github.io` main → GitHub Pages auto-deploys

### 5. End-to-end test (10 min)
- DM `@SLH_Claude_bot` `/grandfather 8789977826 30 vip` (test value)
- Wait 1-2s
- Open `https://slh-nft.com/miniapp/dashboard.html` from bot menu
- Verify widget shows "VIP · 0/350"
- Send a message to bot, refresh page → quota should increment

---

## Risks & gotchas

1. **DATABASE_URL not in claude-bot env yet** — Osif will need to add. But Postgres credentials are sensitive — use Railway's INTERNAL `DATABASE_URL` (not public) so it only works from inside the Railway network. Currently claude-bot is on Osif's local Docker, NOT Railway — so it'd need to use `DATABASE_PUBLIC_URL`. Trade-off: latency + slight security exposure.

2. **api/main.py + main.py sync** — easy to forget. Pre-commit hook should warn.

3. **initData validation** — existing `telegram_gateway.py` has the HMAC verification helper. Use it.

4. **Schema drift** — if bot adds a new column to SQLite `subscriptions`, mirror table needs to follow. Document in CLAUDE.md.

5. **First load shows "Free"** — until bot syncs the user's actual tier, dashboard shows Free. Solve by lazy-creating PG row in API endpoint when not found, calling back to bot via internal API. Out of scope for Phase B; document as Phase C.

---

## Definition of "done"

- [ ] Table `ai_spark_subscriptions` exists on Railway Postgres
- [ ] Bot writes to PG on every upgrade + every quota increment (best-effort)
- [ ] API endpoint returns correct JSON for /api/ai_spark/credits/{user_id}
- [ ] Dashboard widget shows live tier + quota for the logged-in Telegram user
- [ ] /grandfather <user_id> reflects in dashboard within 5 seconds
- [ ] Sending a message to bot increments dashboard quota counter on next refresh
- [ ] Errors in PG mirror don't break bot (verified by stopping PG temporarily)

---

## Why we deferred this

Customer #1 (Tzvika) is the bottleneck for revenue, not data visualization. The current widget already deep-links to bot's `/credits` command which IS live and accurate. Real-time dashboard is "premium feel" — important after we have 5+ paying users, less important now.

When to do this:
- **Trigger:** 3+ paying users OR operator complaint about widget UX
- **Window:** ~60 min uninterrupted, with operator available to test

— Claude (sessionTag: ai-spark-pro)
