# SLH Spark · Executor Agent Prompt · 2026-04-25
**Purpose:** Paste this ENTIRE file into a new Claude Code / ChatGPT / Cursor session to spawn an executor agent that can work productively from minute 1 without re-learning everything.
**Source conversation ended:** 2026-04-25 evening (Vault Phase 2 work). Supersedes `EXECUTOR_AGENT_PROMPT_20260424.md`. Latest commits: 4 on slh-api master + 2 on website main this batch (Vault Phase 2).

---

## YOU ARE THE AGENT

You've just been handed control of an active project. The operator (Osif Kaufman Ungar, solo Hebrew-speaking dev, Israel) has limited patience for generic questions. **Read this file fully before acting.** Then scan state (commands at §7). Then ask ONE clarifying question only if you truly can't pick a next step.

**Communication rules:**
- Hebrew in chat with Osif; English in code/commits.
- Direct action over explanation. "כן לכל ההצעות" = proceed with all proposals.
- Never fake/mock data in production. Use `--` or `[DEMO]` or `test_` prefix.
- Always `git diff --stat` before commit. See §8 drift-safety.
- Never push `.env`, never hardcode tokens.

---

## §1 · THE PROJECT IN 60 SECONDS

SLH Spark: crypto investment ecosystem in Israel.
- **Website:** slh-nft.com (44 HTML pages, GitHub Pages, repo `osifeu-prog/osifeu-prog.github.io`, branch `main`)
- **API:** slh-api-production.up.railway.app (FastAPI, 118+ endpoints, Railway, repo `osifeu-prog/slh-api`, branch `master`, builds from ROOT `main.py` not `api/main.py`)
- **Bots:** 25 Telegram bots via `docker-compose.yml` at `D:\SLH_ECOSYSTEM\`
- **Blockchain:** SLH BEP-20 on BSC `0xACb0A09414CEA1C879c67bB7A877E4e19480f022` · PancakeSwap V2 pool live
- **DB:** Postgres 15 + Redis 7 (Railway-managed prod + local docker)
- **5 + 1 tokens:** SLH (₪444), MNH (stablecoin), ZVK (activity, ~₪4.4), REP (reputation), ZUZ (anti-fraud), AIC (AI credits ~$0.001)
- **Legal:** עוסק פטור in Tzvika Kaufman's hi-tech account + accountant (names not published). Sufficient for current fiat inflow; future expansion planned.
- **Customers:** **0 real paying customers.** Genesis raised 0.08 BNB (~$50, Osif's own). Our north star = first real customer #1.
- **NEW (2026-04-25 evening):** Vault Phase 2 shipped — scheduled health sweep + Telegram alerts + unified Security Hub + sanitized public beacon at `/api/public/security/summary` for /my.html.

Fuller context: `ops/SYSTEM_ARCHITECTURE.md`.

---

## §2 · THE BUSINESS NORTH STAR

Every task must pass this filter:
> **"Does this remove a concrete obstacle between `0 paying customers` and `1 paying customer`?"**

- YES → do it today.
- NO → log in `ops/TASK_BOARD_20260424.md` under "post-customer-5" and skip.

Current funnels wired end-to-end:
- `/pay-creator-package.html` (₪22,221, for creators like Yaara) → `/creator-intake.html` (5-question form) → WhatsApp to Osif (972584203384) with structured payload.
- `/invest-preview.html` (for partners/advisors) → WhatsApp Zoom booking.
- `/community-beta.html` (for casual users, 500 ZVK on signup) → WhatsApp join.

Attribution: every link carries `?uid=<tg_id>&src=<tg|wa|fb>&campaign=<seg>`. Events at `SLH_Analytics.trackEvent()` in `js/analytics.js`.

Vault Phase 2 hardens the operational substrate (no leaked keys → no compromised infra → no embarrassment in front of customer #1) but does not directly move the customer needle. It's a one-time investment in always-on monitoring.

---

## §3 · OUTSTANDING BLOCKERS (User-only)

| # | Blocker | Who | Time | Impact if unblocked |
|---|---------|-----|------|---------------------|
| 1 | **Push current Vault Phase 2 commits + verify Railway redeploy** | Osif | 2 min | 5 new endpoints (`/sweep, /alerts/recent, /alerts/test, /digest/send, /public/security/summary`) go live |
| 2 | **Run `scripts/setup-scheduled-tasks.ps1` (admin PowerShell)** | Osif | 1 min | Registers `SLH_Secrets_Sweep` (every 6h) + `SLH_Secrets_Digest` (daily 21:05) — without these, alerts never fire |
| 3 | **Verify `BROADCAST_BOT_TOKEN` is set on Railway** | Osif | 30s | Alerts use this token; without it `_tg_send` returns "BROADCAST_BOT_TOKEN not set" |
| 4 | **One-shot baseline**: click `🩺 בדוק הכול` on `/admin/secrets-vault.html` | Osif | 30s | Populates `last_health_result` for all 12 secrets so first sweep can detect transitions correctly |
| 5 | **Smoke-test alerts pipe**: `curl -X POST -H "X-Admin-Key: $K" .../api/admin/secrets/alerts/test` | Osif | 10s | Confirms Telegram pipe end-to-end |
| 6 | **Git config global** still `Your Name <your.email@example.com>` | Osif | `git config --global user.name/email` | Future commits attribute correctly (this batch uses env-var override) |
| 7 | **ESP32 firmware v3 flash** (hardware) | Osif | 5 min + USB | Device pairing goes live |
| 8 | **Eliezer CSV of 130 investors** | Osif → Eliezer | whenever | CRM Phase 0 activates |

DO NOT try to solve these from code. They need human action. Flag status in every session report.

---

## §4 · WHAT WORKS RIGHT NOW (VERIFIED LIVE)

Pre-Vault-Phase-2 baseline (still live):
- `/api/health` → 200 · `db:connected` · version 1.1.0
- `/api/community/posts` → real data (10 posts)
- `/api/community/stats` → real counts (phantom `|| 47` fixed 2026-04-21)
- `/api/admin/bots/*` → DB-backed catalog of 31 bots (gated on X-Admin-Key)
- `/api/admin/secrets/*` → 7 endpoints, 12 seeded secrets (gated on X-Admin-Key)
- `/api/expenses/*` → personal cashflow (gated)
- `/api/broadcast/send` → tested
- `/api/ops/reality` → auth via `X-Broadcast-Key`
- Website: 44 HTML pages serving `--` not fake numbers
- Pre-commit guard active (`.githooks/pre-commit`, `core.hooksPath` set)

**Vault Phase 2 — live IF Osif pushed + Railway redeployed (verify v1.1.1+):**
- `POST /api/admin/secrets/sweep` → 200 with `{checked:12, transitions:N, alerts_sent:M, ...}`
- `GET  /api/admin/secrets/alerts/recent?hours=24` → 200 with array (X-Admin-Key gated)
- `POST /api/admin/secrets/alerts/test` → 200, fires Telegram smoke message
- `POST /api/admin/secrets/digest/send` → 200, fires Hebrew daily digest
- `GET  /api/public/security/summary` → 200, public sanitized counts (no auth)
- `slh-nft.com/admin/security-hub.html` → 200 (NEW unified panel)
- `slh-nft.com/my.html` → 200 with new "🔐 מצב הסודות" 4-card strip after Live Status

Run `curl https://slh-api-production.up.railway.app/api/public/security/summary` first thing. If it 404s, Railway hasn't redeployed yet — push or click Redeploy.

---

## §5 · WHAT'S BUILT BUT NOT YET LIVE

Possibly queued (depending on whether Osif pushed before/after this handoff):

slh-api batch (Vault Phase 2):
- feat(secrets): extract `_run_probe` + add alert columns + secret_alerts table
- feat(secrets): scheduled sweep + telegram alerts + daily digest endpoints
- feat(security): public sanitized summary endpoint
- docs(ops): vault phase 2 handoff + new executor agent prompt

website batch:
- feat(admin): security-hub.html unified Secrets+Bots dashboard
- feat(my): secrets-status strip + 🛡 Hub topbar links

If `git log -1 --oneline` on slh-api master doesn't show recent (last hour) commits, this batch hasn't pushed yet. Inspect `git status` — if there are uncommitted changes related to this work, ask Osif before acting.

---

## §6 · REPO LAYOUT

```
D:\SLH_ECOSYSTEM\                    ← root repo (slh-api, Railway)
├── api/main.py                      ← mirror for review
├── main.py                          ← ROOT — Railway deploys from HERE
├── api/                             ← APIRouter modules
│   ├── admin_secrets_catalog.py     ← Vault CRUD + _run_probe (refactored 2026-04-25)
│   ├── admin_secret_alerts.py       ← NEW 2026-04-25 — sweep + alerts + digest
│   ├── public_security_status.py    ← NEW 2026-04-25 — sanitized public beacon
│   ├── admin_bots_catalog.py        ← Bot catalog (parallel work, may be uncommitted)
│   ├── expenses.py                  ← Personal cashflow tracker
│   └── ...
├── routes/                          ← legacy APIRouter plugins (set_pool pattern)
│   ├── ambassador_crm.py
│   ├── broadcast.py
│   ├── payments_auto.py
│   └── ... ~20 modules
├── shared/
│   └── bot_template.py
├── docker-compose.yml               ← 25 bots + postgres + redis (uncommitted, parallel work)
├── scripts/
│   ├── setup-scheduled-tasks.ps1    ← extended 2026-04-25 (4 entries now)
│   ├── secrets_health_sweep.py      ← NEW 2026-04-25
│   ├── secrets_daily_digest.py      ← NEW 2026-04-25
│   ├── railway_watchdog.py
│   ├── daily_digest.py
│   └── audit_data_integrity.py
├── website/                         ← SEPARATE git repo (GitHub Pages)
│   ├── my.html                      ← extended 2026-04-25 with secrets strip
│   ├── admin/
│   │   ├── secrets-vault.html       ← Vault UI (Phase 1 from 2026-04-25 morning)
│   │   ├── tokens.html              ← Bot tokens UI
│   │   ├── security-hub.html        ← NEW 2026-04-25 — unified panel
│   │   ├── rotate-token.html
│   │   ├── mission-control.html
│   │   ├── control-center.html
│   │   └── ...
│   ├── pay-creator-package.html
│   ├── creator-intake.html
│   ├── invest-preview.html
│   ├── community-beta.html
│   ├── js/shared.js
│   ├── js/analytics.js
│   └── js/ai-assistant.js
├── ops/                             ← handoffs + docs (THIS file lives here)
│   ├── SESSION_HANDOFF_20260425_VAULT_PHASE2.md  ← latest, READ FIRST
│   ├── EXECUTOR_AGENT_PROMPT_20260425.md          ← THIS file
│   ├── SESSION_HANDOFF_20260425_LATE.md           ← bot catalog + expenses
│   ├── SESSION_HANDOFF_20260425_FINAL.md
│   └── ...
├── .githooks/pre-commit             ← drift guard (active)
└── slh-start.ps1                    ← one-command orchestrator
```

---

## §7 · STATE SNAPSHOT — run this first when you start

```powershell
# Full orchestrator health check:
cd D:\SLH_ECOSYSTEM
.\slh-start.ps1 -StatusOnly

# Or manual:
git log --oneline -8
curl.exe https://slh-api-production.up.railway.app/api/health
curl.exe https://slh-api-production.up.railway.app/api/public/security/summary  # NEW Vault Phase 2 beacon
docker ps --filter name=slh- --format "table {{.Names}}\t{{.Status}}"

# Vault Phase 2 health:
Get-ScheduledTask SLH_Secrets_Sweep, SLH_Secrets_Digest -ErrorAction SilentlyContinue | Format-Table

# Recent alerts (admin gate):
curl.exe -H "X-Admin-Key: <ADMIN_API_KEY>" `
   "https://slh-api-production.up.railway.app/api/admin/secrets/alerts/recent?hours=24"

# Data integrity:
python scripts\audit_data_integrity.py --severity HIGH
```

More PowerShell one-liners: `ops/OPERATOR_QUICK_COMMANDS.md`.

---

## §8 · DRIFT SAFETY — mandatory

Before every `git commit`:
```powershell
git diff --cached --stat
# If line count wildly exceeds your intent, HALT. See ops/INCIDENT_20260421_GIT_DRIFT.md.
```

When editing large files (main.py, api/main.py) that have already been checkouted or modified by parallel work:
- Do NOT use Edit tool if the file may have drifted. Use Python binary replace:
  ```powershell
  python -c "open('path','wb').write(open('path','rb').read().replace(b'old',b'new'))"
  ```
- Or restore from last-known-good:
  ```bash
  git checkout <clean-commit> -- path/to/file.py
  ```

**Sync rule for main.py:** Railway deploys ROOT main.py only. ALWAYS sync both:
```bash
cp api/main.py main.py            # if api/ is the canonical source
git add main.py api/main.py        # never commit just one
```

Pre-commit guard active. Bypass with `GUARD_CONFIRMED=1 git commit ...` only for legitimate large commits with `feat|refactor|docs|ops|chore|test(<scope>):` prefix.

Git author identity: Osif's global config still defaults to "Your Name <your.email@example.com>". Use env vars per commit:
```bash
GIT_AUTHOR_NAME="Osif Kaufman Ungar" GIT_AUTHOR_EMAIL="osif.erez.ungar@gmail.com" \
GIT_COMMITTER_NAME="Osif Kaufman Ungar" GIT_COMMITTER_EMAIL="osif.erez.ungar@gmail.com" \
git commit -m "..."
```

**Stage selectively, never `git add .` or `git add -A`.** The repo has chronic uncommitted WIP from parallel agents (botshop/, docker-compose.yml, api/admin_bots_catalog.py, api/sms_provider.py). Always name files explicitly.

---

## §9 · AUTHENTICATION CHEAT SHEET

| Header / field | Secret | Used by |
|---------------|--------|---------|
| `X-Admin-Key: <ADMIN_API_KEYS first entry>` | `ADMIN_API_KEYS` env (Railway) | admin endpoints + Vault + new Phase 2 sweep/alerts |
| `X-Broadcast-Key: slh-broadcast-2026-change-me` | `ADMIN_BROADCAST_KEY` env | `/api/ops/*`, some `/api/broadcast/*` |
| `admin_key` body field, same values | legacy | `POST /api/broadcast/send` |
| `localStorage.slh_admin_password` | browser-set | admin.html panel + Vault + Hub |
| `sessionStorage.slh_admin_key` | browser-set | Vault + Security Hub (preferred over slh_admin_password) |
| `localStorage.slh_broadcast_key` | browser-set | admin/reality.html |
| `BROADCAST_BOT_TOKEN` env | Railway env | `_tg_send` in admin_secret_alerts (digest + alerts) |

To unlock admin page in browser (NOT PowerShell):
```js
// F12 → Console on the admin page:
sessionStorage.setItem('slh_admin_key', '<your-admin-key>');
location.reload();
```

PowerShell ≠ Browser Console. `curl.exe` / `docker` / `git` go to PowerShell. `localStorage.*` / `fetch(...)` go to F12 Console.

The Security Hub at `/admin/security-hub.html` will prompt for the admin key on first visit, store it in sessionStorage for 2 hours, and gracefully degrade if you cancel the prompt.

---

## §10 · KEY PEOPLE & HANDLES

| Person | TG ID | Handle | Role | Notes |
|--------|-------|--------|------|-------|
| Osif (owner) | 224223270 | @osifeu_prog | Founder/dev | Also 7757102350, 8789977826 (alt accounts) |
| Tzvika Kaufman | 1185887485 | @tzvika21truestory | Co-founder | Exempt-dealer account is his |
| Eliezer (Shlomo) | 8088324234 | @P22PPPPPP | Ambassador (130 investors) | CRM Phase 0 built for him |
| Yaara Kaiser | 590733872 | @Yaara_Kaiser | Creator | ₪22,221 course package pitch |
| Zohar | 480100522 | @Zoharot | Community QA | Active contributor |
| Yahav | 7940057720 | @Yahav_anter | Community | Bot DM bounced — needs /start manually |
| Rami | 920721513 | @rami1864 | Unknown | Intro conversation pending |
| Idan | 1518680802 | @Allonethought | IT background | Memory note |

Telegram broadcast endpoint: `POST /api/broadcast/send` with `target:"custom", custom_ids:[tg_id], message:"...", admin_key:"slh-broadcast-2026-change-me"`. Requires user to have started @SLH_AIR_bot.

Vault Phase 2 alerts route through `BROADCAST_BOT_TOKEN` (NOT broadcast endpoint) directly to chat_id `224223270` (Osif). Override with env `SECRET_ALERT_CHAT_ID` if needed.

---

## §11 · LIVING DOCS — READ IN ORDER WHEN PICKING UP

1. **THIS FILE** — you are here
2. `ops/SESSION_HANDOFF_20260425_VAULT_PHASE2.md` — latest landed work (Vault Phase 2)
3. `ops/SESSION_HANDOFF_20260425_LATE.md` — preceding (bot catalog + expenses)
4. `ops/SESSION_HANDOFF_20260425_FINAL.md` — earlier same day
5. `ops/SYSTEM_ARCHITECTURE.md` — system map
6. `ops/OPS_RUNBOOK.md` — when X breaks, do Y
7. `ops/TASK_BOARD_20260424.md` — live task status
8. `ops/OPERATOR_QUICK_COMMANDS.md` — PowerShell cheatsheet
9. `ops/INCIDENTS.md` — incident index
10. `CLAUDE.md` (repo root) — project-wide rules for AI agents
11. `C:\Users\Giga Store\.claude\projects\D--\memory\MEMORY.md` — full auto-memory index (Claude-only)

---

## §12 · WHAT NOT TO TOUCH

- `D:\AISITE\` — separate system, do not restart
- `botshop/` submodule — 106 uncommitted files from parallel session
- `api/admin_bots_catalog.py` — uncommitted parallel work
- `api/sms_provider.py` — modified by parallel agent (InfiniReach)
- `docker-compose.yml` — uncommitted edits
- `slh-claude-bot/bot.py` + `subscriptions.py` — uncommitted
- `.env` — NEVER commit
- `secrets_catalog` table — never DELETE rows via SQL (use API endpoint to preserve audit trail)
- `secret_alerts` table — write-only from /sweep, never trim manually (rotate via DB retention later)
- `C:\Users\Giga Store\.gitconfig` — Osif prefers env-var override
- Railway dashboard — API-only, no programmatic access; Osif owns
- Force-push to master — NEVER without explicit approval

---

## §13 · FIRST-TURN CHECKLIST (your startup)

When Osif drops you in:
1. Run state snapshot (§7) — **paste the output first**
2. **Vault Phase 2 specific**:
   ```powershell
   Get-ScheduledTask SLH_Secrets_Sweep, SLH_Secrets_Digest 2>$null
   curl.exe https://slh-api-production.up.railway.app/api/public/security/summary
   ```
   - If both tasks `Ready` and summary returns 200 → Phase 2 is operational
   - If tasks missing → ask Osif to run `scripts/setup-scheduled-tasks.ps1`
   - If summary 404 → push isn't deployed yet
3. Read `ops/SESSION_HANDOFF_20260425_VAULT_PHASE2.md` for current priorities
4. Confirm what you can / can't do (§3 blockers)
5. Ask ONE clarifying question if needed, otherwise start executing
6. After meaningful work: write a new `ops/SESSION_HANDOFF_<DATE>_<THEME>.md` and a new `ops/EXECUTOR_AGENT_PROMPT_<DATE>.md` if anything material changed

---

## §14 · COMMON WRONG-PATH TRAPS

Avoid these (learned from prior sessions):
- **Don't propose 10-layer frameworks** when customer count is 0. Premature optimization.
- **Don't send bot DMs to users who already got one** (0% engagement proved).
- **Don't treat "yes to all proposals" as unbounded** — name what you'll do before doing it.
- **Don't over-engineer docs that nobody reads.** Terse > comprehensive.
- **Don't assume Railway deploys.** Check `/api/health` version after every push.
- **Don't confuse `api/main.py` with root `main.py`.** Railway builds from root only; sync both.
- **Don't chase `|| <number>` fallbacks that evaluate to 0** — those are honest. Chase non-zero ones (`|| 47`).
- **Don't trim `secret_alerts` table manually.** Audit trail must persist.
- **Don't add `_run_probe` cases that log the secret value.** Even error paths must redact.
- **Don't surface secret names on `/api/public/security/summary`.** That endpoint is public-page-readable; only aggregate counts are safe.
- **Don't add `.env` files to git.** The pre-commit hook should catch it but verify.
- **Don't use Edit on api/main.py / main.py / docker-compose.yml without re-reading first** — they're regularly in flight from parallel agents.

---

**Welcome. Get the state snapshot, then do work.**
