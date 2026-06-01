# SLH Spark · Executor Agent Prompt · 2026-04-24
**Purpose:** Paste this ENTIRE file into a new Claude Code / ChatGPT / Cursor session to spawn an executor agent that can work productively from minute 1 without needing to re-learn everything.
**Source conversation ended:** 2026-04-24. 9 commits on slh-api master + 4 on website main since 2026-04-21 night.

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
- **Website:** slh-nft.com (43 HTML pages, GitHub Pages, repo `osifeu-prog/osifeu-prog.github.io`, branch `main`)
- **API:** slh-api-production.up.railway.app (FastAPI, 113+ endpoints, Railway, repo `osifeu-prog/slh-api`, branch `master`, builds from ROOT `main.py` not `api/main.py`)
- **Bots:** 25 Telegram bots via `docker-compose.yml` at `D:\SLH_ECOSYSTEM\`
- **Blockchain:** SLH BEP-20 on BSC `0xACb0A09414CEA1C879c67bB7A877E4e19480f022` · PancakeSwap V2 pool live
- **DB:** Postgres 15 + Redis 7 (Railway-managed prod + local docker)
- **5 + 1 tokens:** SLH (₪444), MNH (stablecoin), ZVK (activity, ~₪4.4), REP (reputation), ZUZ (anti-fraud), AIC (AI credits ~$0.001)
- **Legal:** עוסק פטור in Zvika Kaufman's hi-tech account + close accountant (names not published). Sufficient for current fiat inflow; future expansion planned.
- **Customers:** **0 real paying customers.** Genesis raised 0.08 BNB (~$50, Osif's own). Our north star = first real customer #1.

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

---

## §3 · OUTSTANDING BLOCKERS (User-only)

| # | Blocker | Who | Time | Impact if unblocked |
|---|---------|-----|------|---------------------|
| 1 | **Railway auto-deploy stuck** | Osif | 30s (Redeploy btn) | 9 commits (b48a1b1 → c3fdb47) go live — CRM endpoints, Tzvika founder fix, control layer — currently 404 |
| 2 | **Git config global** still `Your Name <your.email@example.com>` | Osif | `git config --global user.name/email` | Future commits attribute correctly |
| 3 | **4 personal Telegram DMs** (not bot) to Zvika/Eliezer/Rami/Zohar | Osif | 5-7 min copy-paste from `ops/OUTREACH_BATCH_20260424.md` | 30-50% response rate vs. 0% for bot DM |
| 4 | **ESP32 firmware v3 flash** (hardware) | Osif | 5 min + USB | Device pairing goes live |
| 5 | **Eliezer CSV of 130 investors** | Osif → Eliezer | whenever | CRM Phase 0 activates |
| 6 | **Yahav `/start @SLH_AIR_bot`** | Osif → Yahav (manual) | 1 min | Re-deliverable for DM |

DO NOT try to solve these from code. They need human action. Flag status in every session report.

---

## §4 · WHAT WORKS RIGHT NOW (VERIFIED LIVE)

- `/api/health` → 200 · `db:connected` · version 1.1.0 (pre-Railway-redeploy)
- `/api/community/posts` → real data (10 posts, 0 today — honest zero, not fake)
- `/api/community/stats` → real counts (phantom `|| 47` fixed 2026-04-21)
- `/api/broadcast/send` → tested, 5/6 DMs delivered yesterday via `target=custom, custom_ids=[id]`, admin_key=`slh-broadcast-2026-change-me`
- `/api/ops/reality` → auth via `X-Broadcast-Key: slh-broadcast-2026-change-me` header · returns full admin dump
- Website community.html + 12 stat pages → serving `--` not fake numbers
- Pre-commit guard (`.githooks/pre-commit`, `core.hooksPath` set locally)
- Messages delivered (via bot yesterday): Zvika, Eliezer, Zohar, Yaara, Rami. Bounced: Yahav.
- Yaara got personal WhatsApp from Osif today — awaiting reply as of 2026-04-24.

---

## §5 · WHAT'S BUILT BUT NOT LIVE (queued in git for Railway)

Commits pending deploy (all on `origin/master`, API still v1.1.0):
- `b48a1b1` fix(reality): Tzvika → founders
- `7c06bbc` feat(ambassador-crm): Phase 0 — 5 endpoints (`/api/ambassador/contacts*`, `/api/ambassador/stats/<id>`)
- `b60cec2` fix(syntax): curly-quote revert + re-add Tzvika + CRM
- `8e18c15` feat: admin-bot FSM + ESP32 firmware v3 + Independence Day broadcast
- `e12cbe6` ops(control-layer): slh-start + audit + SYSTEM_ARCHITECTURE
- `e49a57b` docs(control-layer): INCIDENTS + API_REFERENCE
- `6892556` docs(ops): SESSION_FULL_CLOSURE_20260422
- `c3fdb47` feat(outreach): bulk message generator + OUTREACH_BATCH

Root cause: commit `097eafe` (parallel session, before 2026-04-21) inserted 473 curly-quote characters as string delimiters. Every Railway build failed silently. `b60cec2` fixed the source but Railway requires manual Redeploy click (blocker #1).

---

## §6 · REPO LAYOUT

```
D:\SLH_ECOSYSTEM\                    ← root repo (slh-api, Railway)
├── api/main.py                      ← mirror for review
├── main.py                          ← ROOT — Railway deploys from HERE
├── routes/                          ← APIRouter plugins (set_pool pattern)
│   ├── ambassador_crm.py            ← NEW 2026-04-21 — Eliezer's CRM
│   ├── broadcast.py
│   ├── payments_auto.py
│   ├── treasury.py
│   └── ... ~20 modules
├── shared/
│   └── bot_template.py              ← reads BOT_TOKEN from env
├── docker-compose.yml               ← 25 bots + postgres + redis
├── website/                         ← SEPARATE git repo (GitHub Pages)
│   ├── pay-creator-package.html     ← creator funnel
│   ├── creator-intake.html          ← intake form
│   ├── invest-preview.html          ← investor funnel
│   ├── community-beta.html          ← community funnel
│   ├── js/shared.js                 ← nav/auth/i18n/theme
│   ├── js/analytics.js              ← SLH_Analytics.trackEvent
│   ├── js/ai-assistant.js           ← floating chat widget
│   └── ... 47 HTML files
├── ops/                             ← handoffs + docs (THIS file lives here)
├── scripts/                         ← ad-hoc automation
├── .githooks/pre-commit             ← drift guard (active via core.hooksPath)
└── slh-start.ps1                    ← one-command orchestrator
```

---

## §7 · STATE SNAPSHOT — run this first when you start

```powershell
# Full orchestrator health check:
cd D:\SLH_ECOSYSTEM
.\slh-start.ps1 -StatusOnly

# Or manual:
git log --oneline -5
curl.exe https://slh-api-production.up.railway.app/api/health
docker ps --filter name=slh- --format "table {{.Names}}\t{{.Status}}"

# Data integrity:
python scripts\audit_data_integrity.py --severity HIGH

# Recent broadcasts (via API):
curl.exe -H "X-Broadcast-Key: slh-broadcast-2026-change-me" `
   https://slh-api-production.up.railway.app/api/ops/reality | `
   python -c "import sys,json; d=json.load(sys.stdin); print('users:', sum(len(v) for v in d['users'].values() if isinstance(v,list))); print('broadcasts logged:', len(d.get('recent_broadcasts',[])))"
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

Pre-commit guard active. Bypass with `GUARD_CONFIRMED=1 git commit ...` only for legitimate large commits with `feat|refactor|docs|ops|chore|test(<scope>):` prefix.

Git author identity: Osif's global config still defaults to "Your Name <your.email@example.com>". Use env vars per commit:
```bash
GIT_AUTHOR_NAME="Osif Kaufman Ungar" GIT_AUTHOR_EMAIL="osif.erez.ungar@gmail.com" \
GIT_COMMITTER_NAME="Osif Kaufman Ungar" GIT_COMMITTER_EMAIL="osif.erez.ungar@gmail.com" \
git commit -m "..."
```

---

## §9 · AUTHENTICATION CHEAT SHEET

| Header / field | Secret | Used by |
|---------------|--------|---------|
| `X-Admin-Key: slh_admin_2026_rotated_04_20` | `ADMIN_API_KEYS` env (Railway) | admin endpoints |
| `X-Broadcast-Key: slh-broadcast-2026-change-me` | `ADMIN_BROADCAST_KEY` env | `/api/ops/*`, some `/api/broadcast/*` |
| `admin_key` body field, same values | legacy | `POST /api/broadcast/send` |
| `localStorage.slh_admin_password` | browser-set | admin.html panel |
| `localStorage.slh_broadcast_key` | browser-set | admin/reality.html |

To unlock admin page in browser (NOT PowerShell):
```js
// F12 → Console on the admin page:
localStorage.setItem('slh_admin_password', 'slh_admin_2026_rotated_04_20');
// Or for reality.html:
localStorage.setItem('slh_broadcast_key', 'slh-broadcast-2026-change-me');
location.reload();
```

PowerShell ≠ Browser Console. `curl.exe` / `docker` / `git` go to PowerShell. `localStorage.*` / `fetch(...)` go to F12 Console.

---

## §10 · KEY PEOPLE & HANDLES

| Person | TG ID | Handle | Role | Notes |
|--------|-------|--------|------|-------|
| Osif (owner) | 224223270 | @osifeu_prog | Founder/dev | Also 7757102350, 8789977826 (alt accounts) |
| Tzvika Kaufman | 1185887485 | @tzvika21truestory | Co-founder | Exempt-dealer account is his. Memory: `project_expertnet.md` |
| Eliezer (Shlomo) | 8088324234 | @P22PPPPPP | Ambassador (130 investors) | CRM Phase 0 built for him |
| Yaara Kaiser | 590733872 | @Yaara_Kaiser | Creator | ₪22,221 course package pitch. WhatsApp sent 2026-04-24. |
| Zohar | 480100522 | @Zoharot | Community QA | Active contributor |
| Yahav | 7940057720 | @Yahav_anter | Community | Bot DM bounced — needs /start manually |
| Rami | 920721513 | @rami1864 | Unknown | Intro conversation pending |
| Idan | 1518680802 | @Allonethought | IT background | Memory note |

Telegram broadcast endpoint: `POST /api/broadcast/send` with `target:"custom", custom_ids:[tg_id], message:"...", admin_key:"slh-broadcast-2026-change-me"`. Requires user to have started @SLH_AIR_bot.

---

## §11 · LIVING DOCS — READ IN ORDER WHEN PICKING UP

1. **THIS FILE** — you are here
2. `ops/SESSION_FULL_CLOSURE_20260422.md` — what shipped on 2026-04-21 night arc
3. `ops/SYSTEM_ARCHITECTURE.md` — system map
4. `ops/OPS_RUNBOOK.md` — when X breaks, do Y
5. `ops/TASK_BOARD_20260424.md` — live task status (current priorities)
6. `ops/OPERATOR_QUICK_COMMANDS.md` — PowerShell cheatsheet
7. `ops/INCIDENTS.md` — incident index (include the curly-quote one!)
8. `CLAUDE.md` (repo root) — project-wide rules for AI agents
9. `C:\Users\Giga Store\.claude\projects\D--\memory\MEMORY.md` — full auto-memory index (Claude-only, per-session)

---

## §12 · WHAT NOT TO TOUCH

- `D:\AISITE\` — separate system, do not restart (see `reference_system_map.md`)
- `botshop/` submodule — from parallel session, not this context
- `.env` — NEVER commit
- `C:\Users\Giga Store\.gitconfig` — Osif prefers not to have AI modify it (uses env-var override instead)
- Railway dashboard — API-only, no programmatic access; Osif owns that
- Force-push to master — NEVER without explicit approval

---

## §13 · FIRST-TURN CHECKLIST (your startup)

When Osif drops you in:
1. Run state snapshot (§7) — **paste the output first**
2. Read `ops/TASK_BOARD_20260424.md` for current priorities
3. Confirm what you can / can't do (§3 blockers)
4. Ask ONE clarifying question if needed, otherwise start executing
5. After meaningful work: update `ops/TASK_BOARD_20260424.md` + commit docs before end of session

---

## §14 · COMMON WRONG-PATH TRAPS

Avoid these (learned from 2026-04-21/22 session):
- **Don't propose 10-layer frameworks** (Design System / State Graph / Neural Map). The customer count is 0. Premature optimization.
- **Don't send bot DMs to users who already got one** (0% engagement proved).
- **Don't treat "yes to all proposals" as unbounded** — name what you'll do before doing it.
- **Don't over-engineer docs that nobody reads.** Terse > comprehensive.
- **Don't assume Railway deploys.** Check `/api/health` version after every push.
- **Don't confuse `api/main.py` with root `main.py`.** Railway builds from root only; sync both.
- **Don't chase `|| <number>` fallbacks that evaluate to 0** — those are honest. Chase non-zero ones (`|| 47`).

---

**Welcome. Get the state snapshot, then do work.**
