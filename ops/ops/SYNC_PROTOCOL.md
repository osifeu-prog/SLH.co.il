# 🔄 SLH Agent Sync Protocol
> **Compatible with "SLH Core Assistant" agent introduced 2026-04-17.**

## 📜 Single Source of Truth (SSoT)
**File:** `D:\SLH_ECOSYSTEM\ops\SESSION_STATUS.md`

Every agent in every session:
1. **Reads** SESSION_STATUS.md first
2. **Updates** it before ending session (overwrite sections, don't append)
3. **Commits** the update with `docs(ops): <agent-name> session sync`
4. **Pushes** to `github.com/osifeu-prog/slh-api.git` (master)

## 🤝 Agent Roles & Boundaries

| Agent | Scope | Tools | Can commit? |
|-------|-------|-------|------------|
| **Claude Opus** (Anthropic, Giga Store local) | Full-stack: api/, website/, shared/, docs | All Claude Code tools | ✅ direct commits |
| **SLH Core Assistant** (code-gen advisor) | Generates PS1/bash/Python/Dockerfile code | Returns code blocks only | ❌ user runs |
| **Giga Store (Osif)** | ESP32, Docker local, `.env`, BotFather | Physical access | ✅ manual |
| **ESP32 device** | Sensor + signature | MQTT/HTTP to device-registry:8090 | ❌ |

## 🚦 Work Coordination Rules
1. **Only one agent touches a file at a time.** If another agent committed to a file, wait for their commit before editing.
2. **`api/main.py` edits must sync to root `main.py`** immediately: `cp api/main.py main.py` → commit both.
3. **Never commit `.env`, `*_MAP_*.txt` with tokens, or backup snapshots** (covered by .gitignore).
4. **Never push directly to `master` with force.** Use PRs or `--no-force`.
5. **Secret values** live ONLY in `~/.claude/slh-secrets.json` (Osif's local) + Railway Variables.

## ✅ Ready signals (report in Telegram #slh-ops)
After each successful action:
- `BOT READY <bot_name>` — bot container healthy + responding
- `ESP READY <device_id>` — ESP32 registered + verified
- `API READY <endpoint>` — new endpoint deployed + smoke-tested
- `WEB READY <page>` — page deployed to GitHub Pages
- `DOC READY <file>` — docs/handoff updated in ops/

## 🔧 Command Conventions
- PowerShell: `-Encoding utf8NoBom`, always have a `-WhatIf` flag, backup before overwrite
- Git: `git add <specific files>` — never `-A`/`.`
- Docker: `docker compose up -d <service>` (targeted), not bare `up -d`
- Python: aiogram 3.x, asyncpg for DB, aiohttp for HTTP

## 🆘 Escalation
If stuck for >15 min on same error:
1. Paste full error + last 3 commands in Telegram @osifeu_prog
2. Reference SESSION_STATUS.md section
3. Don't try destructive fixes (force push, reset --hard, drop table) without confirmation

## 📋 Session Open Checklist
```bash
# 1. Sync
git -C D:/SLH_ECOSYSTEM pull --rebase
git -C D:/SLH_ECOSYSTEM/website pull --rebase

# 2. Read state
cat D:/SLH_ECOSYSTEM/ops/SESSION_STATUS.md

# 3. Health check
curl -s https://slh-api-production.up.railway.app/api/health

# 4. Container status
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 📋 Session Close Checklist
```bash
# 1. Update SESSION_STATUS.md (overwrite "Active blockers" and "Next priorities")
# 2. Commit
git -C D:/SLH_ECOSYSTEM add ops/SESSION_STATUS.md
git -C D:/SLH_ECOSYSTEM commit -m "docs(ops): <agent> <date> session sync"
git -C D:/SLH_ECOSYSTEM push origin master

# 3. Telegram ping: "Session closed. Status updated. Next agent can take over."
```
