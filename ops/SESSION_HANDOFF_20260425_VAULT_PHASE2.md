# Session Handoff — 2026-04-25 Vault Phase 2
**Owner:** Osif Kaufman Ungar (אוסיף, @osifeu_prog, Telegram 224223270)
**Lead agent:** Claude Opus 4.7 (1M context)
**Session theme:** Vault Phase 2 — scheduled health, Telegram alerts, unified Security Hub, /my secrets strip.

This handoff covers work landing AFTER `SESSION_HANDOFF_20260425_LATE.md`. Picks up from the live `Secrets Vault` (commit `a636d56`) and adds the four pieces it was still missing: continuous monitoring, alerting, aggregate visibility, and a beacon on /my.

---

## ⚡ TL;DR

1. **Vault is now reactive → proactive.** A new `POST /api/admin/secrets/sweep` runs all 5 health probes, detects status transitions (ok → bad_key/missing/service_error) and overdue rotations, and fires Hebrew Telegram alerts to Osif (with 24h cooldown to prevent storms). Designed to run every 6h via Windows Task Scheduler.
2. **Daily digest at 21:05.** `POST /api/admin/secrets/digest/send` composes a single Hebrew Telegram message: total/broken/overdue counts + last-24h alert volume + per-secret breakdown of broken & overdue. Independent of immediate alerts.
3. **`/admin/security-hub.html` ships** — single page, two tabs (🔐 Secrets / 🤖 Bots), live stats from `/api/admin/secrets/stats` + `/api/admin/bots/stats`, top-5 broken/overdue + last-24h alerts. Brand-new file; existing Vault + Tokens pages untouched.
4. **`/my.html` gets a security beacon** — 4-card strip immediately after Live Status: `מוגדרים / חסרים-ברירת-מחדל / לסיבוב / התראות 24ש`. Reads `/api/public/security/summary` (no auth required, returns aggregate counts only — never key names or values).
5. **Six-line audit-trail extension.** New `secret_alerts` table + 3 new columns on `secrets_catalog` (`last_alert_at`, `last_alert_result`, `alert_cooldown_hours`). Every fired alert records: prev_status, new_status, alert_type, notified_via. No secret values anywhere.

---

## 📦 Commits this batch

### slh-api master (Railway auto-deploy)

| Commit | Title |
|---|---|
| TBD | feat(secrets): extract _run_probe + add alert columns + secret_alerts table |
| TBD | feat(secrets): scheduled sweep + telegram alerts + daily digest endpoints |
| TBD | feat(security): public sanitized summary endpoint |
| TBD | docs(ops): vault phase 2 handoff + new executor agent prompt |

### osifeu-prog.github.io main (GitHub Pages auto-deploy)

| Commit | Title |
|---|---|
| TBD | feat(admin): security-hub.html unified Secrets+Bots dashboard |
| TBD | feat(my): secrets-status strip + 🛡 Hub topbar links |

(Hashes filled in after commit creation.)

---

## 🟢 Live + verified (curl 25.4 evening — pre-deploy syntax verification)

```
# All Python parses cleanly
ast.parse(api/admin_secrets_catalog.py)   → OK (refactored, _run_probe extracted)
ast.parse(api/admin_secret_alerts.py)     → OK (220 lines, NEW)
ast.parse(api/public_security_status.py)  → OK (110 lines, NEW)
ast.parse(scripts/secrets_health_sweep.py)  → OK (95 lines, NEW)
ast.parse(scripts/secrets_daily_digest.py)  → OK (75 lines, NEW)
ast.parse(main.py)                          → OK (registrations added)
ast.parse(api/main.py)                      → OK (synced)

# Existing endpoints still respond (sanity)
GET  /api/health                          → 200 {db:connected, v1.1.0}
GET  /api/admin/secrets                   → 403 (auth gate intact)

# NEW endpoints — will return 200 after Railway redeploys from master
GET  /api/public/security/summary         → 404 (currently — until next deploy)
POST /api/admin/secrets/sweep             → 404 (currently — until next deploy)
POST /api/admin/secrets/digest/send       → 404 (currently — until next deploy)
GET  /api/admin/secrets/alerts/recent     → 404 (currently — until next deploy)
POST /api/admin/secrets/alerts/test       → 404 (currently — until next deploy)

# No hardcoded secrets in any of the 5 new files
grep -E 'sk-[a-z0-9]{20,}|key-[a-z0-9]{20,}|gAA[A-Za-z0-9_-]{20,}' on all NEW files → 0 hits
```

After Osif pushes + Railway redeploys, run V1-V4 from `ops/.../plans/secrets-vault-crystalline-honey.md`.

---

## 🆕 New API surface (this batch)

### `/api/admin/secrets/sweep` & alerts (X-Admin-Key gated)

| Method+Path | Purpose |
|---|---|
| `POST /api/admin/secrets/sweep` | Iterate all 12 secrets, run `_run_probe` per row, detect transitions, fire Telegram alerts (24h cooldown). Returns `{checked, transitions, alerts_sent, overdue_alerts, skipped_cooldown, skipped_no_probe, errors}`. Idempotent. |
| `GET  /api/admin/secrets/alerts/recent?hours=24&limit=50` | Last N hours of fired alerts joined with secret metadata. Used by Security Hub. |
| `POST /api/admin/secrets/alerts/test` | Smoke test: fires one throwaway Telegram message to confirm the pipe works. |
| `POST /api/admin/secrets/digest/send` | Composes Hebrew daily digest, sends single Telegram. Returns `{ok, summary:{total,broken,overdue,alerts_24h}}`. |

### `/api/public/security/summary` — sanitized public beacon (NO AUTH)

| Method+Path | Purpose |
|---|---|
| `GET /api/public/security/summary` | Aggregate counts ONLY: `{total, configured, missing_or_default, overdue, alerts_24h, last_sweep_at, any_broken, any_overdue, ok}`. Never returns key names, categories, or per-secret detail. Safe for /my.html and any non-admin page. Falls back to `unavailable:true` if catalog isn't initialized. |

### Schema changes (additive, idempotent via `_ensure_schema`)

```sql
ALTER TABLE secrets_catalog ADD COLUMN IF NOT EXISTS last_alert_at TIMESTAMPTZ;
ALTER TABLE secrets_catalog ADD COLUMN IF NOT EXISTS last_alert_result TEXT;
ALTER TABLE secrets_catalog ADD COLUMN IF NOT EXISTS alert_cooldown_hours INT NOT NULL DEFAULT 24;

CREATE TABLE IF NOT EXISTS secret_alerts (
    id          BIGSERIAL PRIMARY KEY,
    secret_id   BIGINT REFERENCES secrets_catalog(id) ON DELETE CASCADE,
    alert_type  TEXT NOT NULL,        -- 'bad_key' | 'missing' | 'service_error' | 'overdue'
    prev_status TEXT,
    new_status  TEXT,
    detail      TEXT,
    notified_via TEXT,                -- 'telegram' | 'failed'
    fired_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_secret_alerts_fired  ON secret_alerts (fired_at DESC);
CREATE INDEX IF NOT EXISTS ix_secret_alerts_secret ON secret_alerts (secret_id);
```

### New audit events (emit to `event_log`)

- `secret.alert.fired` — per-secret transition, includes `key_name + alert_type + notified` (no value)
- `secret.sweep.completed` — per-sweep aggregate counts (used by `/api/public/security/summary` to compute `last_sweep_at`)
- `secret.digest.sent` — daily digest fire event with summary

---

## 🛑 Pending blockers (Osif-only)

| # | What | Reason | Time |
|---|---|---|---|
| 1 | **Push 4 slh-api commits + 2 website commits** | Code is local-only until pushed | 30 sec |
| 2 | **Verify Railway redeploys** to v1.1.x with the 5 new endpoints | New code is dead until live | 1-2 min for build |
| 3 | **Run `scripts/setup-scheduled-tasks.ps1` from elevated PowerShell** | Registers `SLH_Secrets_Sweep` (every 6h) + `SLH_Secrets_Digest` (daily 21:05) | 1 min |
| 4 | **Ensure `BROADCAST_BOT_TOKEN` is set on Railway** | Alerts route through this token; without it `_tg_send` returns "BROADCAST_BOT_TOKEN not set" | 30 sec |
| 5 | **Once deployed, click `🩺 בדוק הכול` on `/admin/secrets-vault.html`** | Populates baseline `last_health_result` for all 12 secrets so first sweep computes transitions correctly | 30 sec |
| 6 | **Smoke-test alerts pipe**: `curl -X POST -H "X-Admin-Key: $K" .../api/admin/secrets/alerts/test` | Confirms BROADCAST_BOT_TOKEN works end-to-end before relying on it | 10 sec |

---

## 🛤 Phase 3 next-session backlog

1. **7-day pre-rotation reminder** — fire a soft alert when a secret will become overdue in 7 days (currently only post-overdue). Requires extending `_format_alert` + sweep predicate.
2. **Per-secret cooldown override** — UI to set `alert_cooldown_hours` per row from the Vault page (currently DB-only column).
3. **Multi-channel alerts** — Slack webhook in parallel to Telegram. Plug-in style.
4. **Alert ack/snooze** — `POST /api/admin/secrets/alerts/{id}/ack` to suppress repeats for N hours from the Hub UI.
5. **Pre-deploy guard** — `_run_probe` for ENCRYPTION_KEY (round-trip encrypt+decrypt of canary) and JWT_SECRET (sign+verify a canary). Currently both return "skipped".
6. **Webhook for INFORU + Twilio** — extend probes to verify SMS providers (currently "skipped"). Tricky because most SMS APIs charge per call — would need a balance-check or no-op shape.

---

## 🎯 First 3 things to do in the next session

1. **Read this file end-to-end.**
2. `curl https://slh-api-production.up.railway.app/api/public/security/summary | jq .` — confirm 200 with aggregate counts.
3. Ask Osif:
   - האם ה-Scheduled Tasks רצות? (`Get-ScheduledTask SLH_Secrets_Sweep` ב-PowerShell)
   - הגיעו התראות לטלגרם בלילה האחרון? (אם כן — מ-`/sweep`, אם לא — צריך לבדוק את `/alerts/test`)
   - האם להוסיף את 7-day pre-rotation reminder עכשיו (Phase 3 #1)?

---

## 📁 Files touched

### NEW (8 files)
- `api/admin_secret_alerts.py` (220 lines — sweep, alerts/recent, alerts/test, digest/send)
- `api/public_security_status.py` (110 lines — sanitized public summary)
- `scripts/secrets_health_sweep.py` (95 lines — Task Scheduler entry → /sweep)
- `scripts/secrets_daily_digest.py` (75 lines — Task Scheduler entry → /digest/send)
- `website/admin/security-hub.html` (280 lines — unified Secrets+Bots panel)
- `ops/SESSION_HANDOFF_20260425_VAULT_PHASE2.md` (this file)
- `ops/EXECUTOR_AGENT_PROMPT_20260425.md` (supersedes 0424)

### MODIFIED (6 files, surgical)
- `api/admin_secrets_catalog.py` — extracted `_run_probe()` helper, added 3 columns + `secret_alerts` table to `_ensure_schema`
- `main.py` — 2 try-import blocks + 2 `app.include_router` calls
- `api/main.py` — same (synced)
- `scripts/setup-scheduled-tasks.ps1` — appended 2 entries to `$TASKS` + 2 cases to trigger switch
- `website/my.html` — inserted secrets-status section + `loadSecrets()` JS + added to refresh cycle
- `website/admin/secrets-vault.html` — added `🛡 Hub` topbar link
- `website/admin/tokens.html` — added `🛡 Hub` topbar link

### NOT TOUCHED (DO NOT touch from any session)
- `botshop/` (106 uncommitted files, parallel agent)
- `api/admin_bots_catalog.py` (uncommitted parallel work)
- `api/sms_provider.py` (modified 20:53 by parallel agent)
- `docker-compose.yml` (uncommitted)
- `.env` (gitignored, but never edit)

---

End of Vault Phase 2 handoff — 2026-04-25 evening IDT.
