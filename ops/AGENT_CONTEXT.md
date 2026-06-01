# 🤝 SLH Ecosystem — Agent Shared Context

> **מסמך סנכרון לכל הסוכנים העובדים על הפרויקט.**
> קרא את זה בתחילת כל session. עדכן את החלק "Live state" לפני סיום.

**מעודכן:** 2026-04-17 | **גרסה:** 1.0

---

## 👤 Owner (single source of authority)
- **Osif Kaufman Ungar** (@osifeu_prog, TG 224223270, osif.erez.ungar@gmail.com)
- Solo dev. עברית בתקשורת, English in code/commits.
- Prefers direct action, short explanations, no scope minimization.

## 🎯 Project mission (one sentence)
SLH Spark — Israeli crypto investment ecosystem with 25 Telegram bots, 5 tokens, 45 web pages, PostgreSQL + Railway deployment.

---

## 🌐 Live Endpoints (must-verify before claiming feature works)
| What | URL |
|------|-----|
| API | `https://slh-api-production.up.railway.app` |
| Health check | `/api/health` → `{"status":"ok","db":"connected"}` |
| Website | `https://slh-nft.com` |
| Admin panel | `/admin.html` (password in localStorage) |
| Bug dashboard | `/admin-bugs.html` (NEW — 2026-04-17) |
| User bug form | `/bug-report.html` |

## 🔑 Auth & Secrets (NEVER in git)
- **Admin API key** → localStorage `slh_admin_password` + Railway env `ADMIN_API_KEYS`
- **Bot tokens** → `.env` file (31 tokens, gitignored)
- **Current default:** `slh2026admin` (🔴 must rotate — see "Pending")

## 🗺 Repo Map
```
D:\SLH_ECOSYSTEM\              ← root (deploys to Railway)
├── api/main.py                ← canonical FastAPI (~9700 lines)
├── main.py                    ← MIRROR — Railway builds this; always `cp api/main.py main.py`
├── website/                   ← separate git repo (GitHub Pages)
│   └── js/shared.js           ← loaded by every page (nav, FAB, auto-capture)
├── docker-compose.yml         ← 25 bots + postgres + redis
├── ops/                       ← handoffs, logs, this file
└── *-bot/                     ← per-bot codebases
```

## 📡 Deploy Flow
| From | To | Trigger |
|------|-----|---------|
| `github.com/osifeu-prog/slh-api` (master) | Railway | `git push origin master` |
| `github.com/osifeu-prog/osifeu-prog.github.io` (main) | GitHub Pages | `git push origin main` |

⚠️ **CRITICAL:** Railway reads ROOT `main.py`, not `api/main.py`. Always sync both.

---

## 🧱 Current Infrastructure (discover-before-recreate)
Before building new helpers, check these exist:
- `_tg_send_message(bot_token, chat_id, text)` @ main.py:5052 — Telegram send
- `BROADCAST_BOT_TOKEN` — primary send channel
- `ADMIN_USER_ID = 224223270` — owner TG ID
- `_require_admin(authorization, x_admin_key)` — admin auth check
- `_ensure_bug_reports_table(conn)` — bugs table DDL
- `pool.acquire()` — asyncpg connection
- `window.slhReportBug(payload)` — client-side bug report (shared.js)

## 📊 Data Conventions
| Marker | Meaning |
|--------|---------|
| `test_` prefix | Test/demo data |
| `[DEMO]` tag | Placeholder content |
| `[SEED]` tag | Initial seed |
| `[AUTO]` prefix | Auto-captured JS/API error (from shared.js) |
| `--` / `N/A` | No data / Not applicable |

## ❌ Never Do
1. Hardcode passwords/tokens in HTML — use localStorage + `X-Admin-Key` header
2. Mock data in production pages — real API or `[DEMO]` tag
3. `git add -A` / `git add .` — stage specific files (128 untracked files!)
4. Push `.env` or `.env.*` — all gitignored
5. Drop a table with user data without backup
6. Give away 50 SLH as reward (too expensive at ₪444 each)
7. Skip main.py sync after api/main.py edits
8. Claim a feature "works" without hitting `/api/health` + testing the flow

## ✅ Always Do
1. `curl https://slh-api-production.up.railway.app/api/health` at session start
2. `git status --short` in both repos before claiming done
3. Update **Live state** section below when you change deployment state
4. Write Hebrew UI, English code
5. Use `[AUTO]` prefix for automated reports so admin knows they're not user-submitted

---

## 🟢 Live State (EDIT THIS SECTION — overwrite, don't append)
**Last updated:** 2026-04-17 by Claude Opus 4.6

### Recently deployed (last 48h)
- ✅ website `cd54d24` — admin-bugs dashboard + auto-capture + FAB button (PUSHED)
- ⏳ root `74cdcb7` — Telegram alerts + resolve endpoint (COMMITTED, NOT PUSHED — remote broken)

### Active blockers (from SESSION_STATUS.md 17.4 00:30)
1. 🔴 root repo git remote = placeholder `github.com/your-username/slh-ecosystem.git` — must be `github.com/osifeu-prog/slh-api`
2. 🔴 `BOT_TOKEN` not passed to ledger-bot container
3. 🟡 `.env` file missing/not used
4. 🟡 128 uncommitted files in root repo (reports, backups, new dirs — need triage)
5. 🟡 Admin key `slh2026admin` = default, never rotated

### Next priorities (in order)
1. Fix root repo git remote → push pending bugs commit
2. Rotate admin key + set Railway `ADMIN_API_KEYS`
3. Triage 128 untracked files
4. Add `bug-pending-badge` live count in admin.html sidebar
5. Fix ledger-bot BOT_TOKEN wiring

### Known API Version
- Production: `1.0.0` (verified via `/api/health`)
- Local: `1.1.0` with bugs endpoints ready to deploy

---

## 🧠 Conventions for Agent Handoff
When YOU end a session:
1. Run health check — paste result
2. `git status` + `git log -1 --oneline` in both repos — paste
3. Update **Live State** section above
4. If you left uncommitted work: list files + reason
5. Mark any new blockers with 🔴, in-progress with 🟡

When you START a session:
1. Read this file first
2. Read `ops/SESSION_HANDOFF_*.md` (latest) for details
3. Verify "Recently deployed" is still accurate via git log
4. Ask owner what's priority if unclear
