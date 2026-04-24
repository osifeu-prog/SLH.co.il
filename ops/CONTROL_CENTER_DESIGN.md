# SLH Control Center — Design Spec
**Author:** Claude (Opus 4.7) working on `D:\SLH.co.il\`
**Date:** 2026-04-25
**Status:** Spec only — implementation requires a "central agent" with read+write across all 3 projects
**Purpose:** Any agent picking this up can build it end-to-end from this doc alone.

---

## 1. Mission
Give Osif one place to:
1. **Know** — current health of all services, tokens, users, revenue
2. **Act** — rotate tokens, deploy, approve preorders, broadcast messages, cancel runaway jobs
3. **Investigate** — tail logs, query DB, see history

Constraint: **must work across 3 projects** without Osif logging into 3 dashboards:
- `D:\SLH.co.il\` (`diligent-radiance` on Railway, `@SLH_macro_bot`, `slh.co.il`)
- `D:\SLH_ECOSYSTEM\` (`slh-api` on Railway, 20+ bots, `slh-nft.com`)
- `D:\AISITE\` (local Windows lab — ESP32 bridge, Mission Control)

---

## 2. Users & personas
| Persona | What they do | Frequency |
|---------|--------------|-----------|
| Osif (founder, primary) | Health check, incident response, daily digest, approve preorders, rotate tokens | Daily → multiple times |
| Osif (strategic mode) | Weekly revenue review, user growth, product decisions | Weekly |
| Future ops staff (Eliezer, Zvika) | Approve specific preorders, respond to feedback | On-demand |
| Future automation (crons) | Trigger daily digest, rotate stale tokens, backup DB | Scheduled |

**Design implication:** prioritize Osif's daily flows. Admin granularity (who can do what) is phase 2.

---

## 3. Core features (MVP = Phase 1)

### 3.1 Health dashboard
```
╔══════════════════════════════════════════════════╗
║  SLH Control Center · 2026-04-25 14:30 UTC+3    ║
╠══════════════════════════════════════════════════╣
║  SLH.co.il         SLH_ECOSYSTEM   AISITE        ║
║  ─────────         ──────────────  ──────         ║
║  bot     🟢         api     🟢       lab    ⚪    ║
║  site    🟢         site    🟢       esp    ⚪    ║
║  db      🟢         db      🟢       —           ║
║  token   🟢         token×6 ⚠(1)                 ║
║                                                  ║
║  Users total: 2 · Preorders: 0 · Revenue: ₪0    ║
╚══════════════════════════════════════════════════╝
```
- 🟢 = responding + recent activity
- 🟡 = responding but degraded
- 🔴 = down
- ⚪ = not checked / offline by design (local lab)
- ⚠ = needs attention (e.g. token expiring soon)

### 3.2 Token management
**The #1 pain point this session.**
```
[T] Tokens
  SLH_macro_bot         ...umhw  valid   last rotated 2026-04-24
  @Grdian_bot           ...(tbd) unknown last rotated 2026-04-21
  @WEWORK_teamviwer_bot ...(tbd) unknown last rotated ?
  ...
Commands:
  rotate <bot_name>              → steps user through BotFather + auto-updates Railway env
  check <bot_name>                → getMe + reports valid/401
  check-all                       → runs getMe on every registered token
```
Auth for rotation: require explicit confirmation — never do it silently.

### 3.3 Deploys
```
[D] Deploys
  monitor.slh    current: 68339c2   last deploy 2026-04-25 12:06 ✅
  slh-api        current: e49a57b   last deploy 2026-04-22 23:15 ⚠ (4d old)
  ...
Commands:
  deploy <service>                → triggers redeploy
  rollback <service>              → reverts to previous successful build
  logs <service> --tail 50        → stream
```

### 3.4 Data views
```
[U] Users         list · search · promote_admin · ban
[P] Preorders     list · approve · mark_shipped · cancel
[F] Feedback      list (by sentiment) · reply_bot · mark_handled
[R] ROI records   list · export_csv
[$] Revenue       daily/weekly/monthly rollup
```

### 3.5 Broadcast
```
[B] Broadcast
  → choose audience (all users / preorder subscribers / admins)
  → type message
  → preview
  → confirm
  → sends via bot, logs to broadcasts table, tracks deliveries
```
Auth: only admin IDs. Rate limit: max 1 broadcast/10 minutes to avoid spam.

### 3.6 Quick actions (one-key)
- `h` → health refresh
- `d` → daily digest
- `l` → latest logs
- `q` → quit

---

## 4. Auth model

### 4.1 Who can access
- Admin list in env var `CONTROL_CENTER_ADMIN_IDS` (Telegram IDs, comma-separated)
- Default: `224223270` (Osif)
- Other IDs: Eliezer (8088324234), Zvika (1185887485) — for future phase

### 4.2 How it authenticates
Per Telegram-First Architecture (21.4 memory): use the **Mini App initData HMAC-SHA256 validation** pattern.
- User opens the control center via `@SLH_Claude_bot` (or dedicated `@SLH_control_bot`)
- Bot generates a Mini App link with signed initData
- Control center validates initData against bot token
- Session token (JWT) stored in localStorage, 24h TTL
- API calls include `X-Admin-Token` header — server validates JWT

### 4.3 What admins can NOT do
- Cannot see other admins' actions (only their own audit log)
- Cannot rotate user passwords (no passwords in this system)
- Cannot delete commits (git is immutable; Railway rollback only)
- Cannot change their own admin status (Osif retains super-admin)

---

## 5. Tech stack — 3 options

### Option A: CLI-first (recommended for Phase 1)
**Stack:** Python + `rich` (TUI) + `click` (commands)
**Run:** `python ops/control.py` in a terminal window, splittable via Windows Terminal tabs
**Pros:**
- 1-2h to MVP
- No auth complexity (runs on Osif's machine with env vars)
- Easy to script / automate
- No UI framework to maintain
**Cons:**
- Not accessible from phone
- Not shareable with non-technical staff

### Option B: Web-first (recommended for Phase 2)
**Stack:** FastAPI backend + HTML/htmx frontend + Mini App auth
**Hosted on:** `control.slh-nft.com` or `admin.slh.co.il`
**Pros:**
- Accessible from any device
- Multi-monitor (open in 3 tabs, drag to different monitors)
- Can use Windows window-manager or 3rd-party apps (Rectangle, FancyZones)
- Multi-user (Eliezer, Zvika)
**Cons:**
- 14-16h to MVP
- Requires the Mini App auth wiring (which itself is blocked on `telegram_gateway.py` integration)

### Option C: Hybrid (recommended long-term)
**Stack:** shared Python backend exposed both as:
- CLI (`python ops/control.py` — fast, local)
- Web (FastAPI + htmx — accessible, multi-user)
- Bot (`@SLH_control_bot` — notifications, quick actions)
**Total:** 20-25h work, but no surface wins over the other after that

**Recommendation:** Start with Option A (CLI). Graduate to Option C hybrid when justified.

---

## 6. File layout (Option A CLI-first)

```
D:\SLH_ECOSYSTEM\ops\control\
├── __init__.py
├── control.py                 # entry point: python -m ops.control
├── config.py                  # reads env, loads project registry
├── projects.json              # registry: paths, Railway project IDs, deploy service names
│
├── commands/
│   ├── __init__.py
│   ├── health.py              # all health checks
│   ├── tokens.py              # rotate / check tokens
│   ├── deploys.py             # railway wrappers
│   ├── data.py                # DB query views (users / preorders / feedback)
│   ├── broadcast.py           # bot broadcast flows
│   └── logs.py                # tail / search logs
│
├── integrations/
│   ├── railway.py             # railway CLI wrapper
│   ├── telegram.py            # BotFather-adjacent (link to rotation URL)
│   ├── postgres.py            # connection pool for each project's DB
│   └── github.py              # commit metadata
│
├── ui/
│   ├── dashboard.py           # main grid view
│   ├── forms.py               # rotation confirmation, broadcast compose
│   └── theme.py               # colors, symbols
│
└── tests/
    ├── test_tokens.py
    └── test_projects.json
```

---

## 7. `projects.json` — the registry
```json
{
  "projects": [
    {
      "name": "SLH.co.il",
      "local_path": "D:/SLH.co.il",
      "railway_project_id": "97070988-27f9-4e0f-b76c-a75b5a7c9673",
      "bot": {
        "username": "SLH_macro_bot",
        "bot_id": "8724910039",
        "service": "monitor.slh"
      },
      "site_url": "https://www.slh.co.il",
      "db_service": "Postgres"
    },
    {
      "name": "SLH_ECOSYSTEM",
      "local_path": "D:/SLH_ECOSYSTEM",
      "railway_project_id": "<TBD by central agent>",
      "bots": [
        { "username": "WEWORK_teamviwer_bot", "role": "primary academia" },
        { "username": "Grdian_bot", "bot_id": "8521882513", "role": "guardian" },
        { "username": "SLH_AIR_bot", "role": "air" },
        { "username": "SLH_Wallet_bot", "role": "wallet" },
        { "username": "SLH_ton_bot", "role": "ton" },
        { "username": "TON_MNH_bot", "role": "affiliate" },
        { "username": "SLH_Claude_bot", "role": "executor" }
      ],
      "site_url": "https://slh-nft.com"
    },
    {
      "name": "AISITE",
      "local_path": "D:/AISITE",
      "type": "local_lab",
      "notes": "Windows-native Flask services + ESP bridge — not Railway"
    }
  ]
}
```

---

## 8. Sample command implementations

### 8.1 `control health` (Option A)
```python
# commands/health.py (sketch)
import asyncio
from integrations import railway, postgres, telegram

async def check_all(projects):
    results = []
    for p in projects:
        bot_ok = await telegram.getMe_ok(p.bot.token_env_name)
        db_ok = postgres.ping(p.db_url)
        site_ok = http.head_ok(p.site_url)
        results.append({
            "name": p.name,
            "bot": bot_ok,
            "db": db_ok,
            "site": site_ok,
        })
    return results
```

### 8.2 `control rotate <bot>` (interactive)
```
$ python -m ops.control rotate SLH_macro_bot
→ Open BotFather: https://t.me/BotFather  (opens in default browser)
→ /mybots → SLH_macro_bot → API Token → Revoke
→ Paste new token here (input is masked):  ***
→ [validating via getMe] … valid ✓ @SLH_macro_bot
→ Updating Railway Shared Variable TELEGRAM_BOT_TOKEN …
→ Triggering redeploy of monitor.slh …
→ [waiting for deploy, ~60s] … done ✓
→ Post-verify getMe … 200 OK ✓
→ Token rotation complete. Audit entry written.
```

### 8.3 `control approve-preorder <id>` (interactive)
```
$ python -m ops.control approve-preorder 1
→ Preorder #1: @someone · SLH Guardian · 2026-04-25 13:47
→ Status change: interested → approved
→ Send confirmation DM to user? [Y/n]: Y
→ Payment method (TON/BANK/PAYPAL): TON
→ Amount (₪): 888
→ [generating TON payment request]
→ TON address: UQDhfyUPSJ8...
→ Memo: SLH-GUARDIAN-1-888
→ DM sent to user. Preorder status=approved, awaiting_payment.
```

---

## 9. Integration points

| From | To | Via |
|------|----|----|
| Control Center | Railway | `railway` CLI + Railway GraphQL API (env variables, deploys, logs) |
| Control Center | Telegram | Bot API (getMe, sendMessage) + deep-links to BotFather |
| Control Center | Postgres (each project) | per-project `DATABASE_URL` from each project's env |
| Control Center | GitHub | `gh` CLI (commit history, PR status) |
| Control Center | ESP32 | via `D:\SLH_ECOSYSTEM\` endpoints `/api/device/command/{id}` |
| Control Center | Users (broadcast) | via each bot's `sendMessage` |

---

## 10. Phasing

| Phase | Scope | Time | Owner | Prereq |
|-------|-------|------|-------|--------|
| Phase 1 | CLI (Option A), health + tokens + deploys only | 2-3h | Central agent | Projects.json filled in |
| Phase 2 | CLI + data views (users/preorders/feedback) | +3-4h | Central agent | Phase 1 + DB connection strings collected |
| Phase 3 | CLI + broadcast + approve-preorder flows | +3-4h | Central agent | Phase 2 + bot permissions confirmed |
| Phase 4 | Web UI (Option B skeleton) calling Phase 1-3 backend | +8-10h | Central agent + frontend-ready agent | Phase 3 done, Mini App auth wired |
| Phase 5 | Multi-monitor polish, responsive, mobile | +4-6h | Frontend agent | Phase 4 done |

**Total:** 20-27h to a production-quality multi-monitor control center.

---

## 11. What a "central agent" needs to have before starting

- [ ] Read+write authorization to all 3 project directories from Osif
- [ ] Railway CLI linked to all relevant projects (`railway link` × each)
- [ ] Collected list of DATABASE_URL + bot token env var names per project (not the values — just the names)
- [ ] List of admin Telegram IDs
- [ ] Agreement from Osif on which tech stack (Option A/B/C)
- [ ] Empty `ops/control/` folder created in `D:\SLH_ECOSYSTEM\` to hold implementation

---

## 12. Handoff text for whoever picks this up

> **Hi — you're building the SLH Control Center. Read `ops/CONTROL_CENTER_DESIGN.md` in `D:\SLH.co.il\` first. Then confirm with Osif: which of Options A/B/C he wants for Phase 1. Then fill in the `projects.json` registry with the actual Railway project IDs and env var names. Then start with Phase 1 CLI only — no web, no broadcasts, no data views in Phase 1. Ship health + tokens + deploys first. Get Osif using it before adding more.**

That's it. Everything else is in this doc.
