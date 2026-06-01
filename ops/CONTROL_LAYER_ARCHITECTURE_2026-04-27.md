# SLH Control Layer — The Architecture
**Date:** 2026-04-27
**Author:** Claude (Cowork mode)
**Trigger:** External analysis correctly identified the core issue:
> "אתה כבר בנית מערכת מורכבת — אבל היא עדיין לא 'מערכת', אלא אוסף רכיבים שלא מדברים בצורה נשלטת."

This document answers the 3 critical questions that diagnosis raised, and describes the
**Control Layer that I just built in this session** to solve them.

---

## The 3 questions, answered

### Q1: Who is the source of truth (SoT)?

**Answer:** **PostgreSQL on Railway is the single source of truth for ALL system state.**

Until today, state was scattered:
- Bot status: only known via "is the docker container running on Osif's laptop?"
- User data: in PostgreSQL (good)
- Device data: partially in PostgreSQL, partially in ESP32 firmware
- Operational state: in PowerShell windows and chat history (terrible)
- Control intents: nowhere — actions were verbal commands

**As of today**, two new tables become the SoT for control + status:
```sql
bot_heartbeats          -- live status of every bot (updated every 30s)
bot_control_intents     -- queue of admin actions, executed by orchestrator
```
Combined with the existing tables, **everything is now in one DB**:

| Domain | Table | Updated by |
|--------|-------|------------|
| Users | `web_users` | Telegram login flow |
| Wallets | `web_users.eth_wallet` | `/api/user/link-wallet` |
| Balances | `token_balances`, `account_balances` | All bots + API |
| Transactions | `transactions`, `ledger`, `deposits` | All bots + API |
| **Bots (NEW)** | **`bot_heartbeats`** | **Each bot every 30s** |
| **Control (NEW)** | **`bot_control_intents`** | **Command Center UI → Orchestrator** |
| Devices | `devices` (or `device_registry`) | ESP32 sync API |
| Audit | SHA-256 chain in main.py | Every state-change endpoint |

**Verification:** From now on, the Command Center's KPIs are pulled from this DB,
not from Osif's laptop. If the laptop is off, the dashboard still tells the truth.

---

### Q2: How do agents communicate?

**Answer:** **Three channels, each with a clear purpose.**

| Channel | Used for | Latency | Reliability |
|---------|----------|---------|-------------|
| **HTTP → API** | bot ↔ central state (read/write users, balances, etc.) | ~100ms | High (Railway is up 99.9%) |
| **PostgreSQL LISTEN/NOTIFY** *(future)* | bot ↔ bot pub/sub events | <50ms | Same as DB |
| **Telegram Bot API** | bot ↔ user | ~500ms | Depends on Telegram |

**As of today, a 4th channel exists:**

| Channel | Used for | Latency | Reliability |
|---------|----------|---------|-------------|
| **Heartbeat → API** | bot → "I'm alive" every 30s | ~200ms | High |
| **Intent ← API** | orchestrator → "execute this action on bot X" | 15s poll cycle | High |

**The flow looks like this:**
```
                                ┌──────────────────┐
                  ┌─────────────┤  Command Center  │  (admin in browser)
                  │ POST intent │                  │
                  ▼             └──────────────────┘
        ┌────────────────────┐
        │  API on Railway    │  (FastAPI + asyncpg)
        └────────┬───────────┘
                 │
                 ▼
        ┌────────────────────┐
        │  PostgreSQL        │  (bot_heartbeats + bot_control_intents)
        └────────┬───────────┘
                 │ poll every 15s
                 ▼
        ┌────────────────────┐
        │  Orchestrator      │  (runs locally on Osif's machine OR a VPS)
        │  slh-orchestrator  │
        └────────┬───────────┘
                 │ docker compose restart <bot>
                 ▼
        ┌────────────────────┐
        │  Bot containers    │  (any Docker host)
        └────────────────────┘
                 │
                 │ POST heartbeat every 30s
                 ▼
            (back to API)
```

**Why this design?**
- **Stateless API** — Railway can scale horizontally
- **Orchestrator is the only thing that needs Docker access** — keeps API layer clean
- **DB-backed queue** — if orchestrator crashes, intents wait safely until it restarts
- **Eventually consistent** — bot is "down" the moment its heartbeat is >90s old, no manual marking

---

### Q3: Who controls in practice?

**Answer:** **The Command Center is the single control plane.** Anything that controls the system is callable from there.

| Action | Who can do it | How |
|--------|---------------|-----|
| Restart a bot | Admin (via X-Admin-Key) | Click "Restart" on bot tile in Command Center |
| Stop all bots | Admin (with double-confirm) | Click "Emergency Pause", type "PAUSE ALL" |
| View bot logs | Admin | Click "Logs" — last 100 lines via orchestrator |
| Inspect API health | Anyone | The "API" tab in Command Center |
| See user activity | Admin | The "Users" tab |
| Trigger a deploy | Admin | (via Railway dashboard for now — later via CC) |

**Crucially:** No one needs to SSH into Osif's machine, no one needs to know
PowerShell commands, no one needs to read docker-compose.yml. **One URL = full control.**

URL: `https://slh-nft.com/command-center.html`
Or after migration: `https://www.slh.co.il/command-center.html`

---

## Components delivered in this session

### 1. `routes/system_status.py` (NEW)
A FastAPI router with 8 endpoints — the **API contract** for the Control Layer:

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/system/status` | GET | none | Overall health snapshot |
| `/api/system/bots` | GET | none | Live bot status array |
| `/api/system/stats` | GET | none | Aggregated KPIs |
| `/api/system/bots/heartbeat` | POST | `X-Bot-Key` | Bots register liveness |
| `/api/system/bots/restart` | POST | `X-Admin-Key` | Queue restart intent |
| `/api/system/bots/stop` | POST | `X-Admin-Key` | Queue stop intent |
| `/api/system/bots/logs` | POST | `X-Admin-Key` | Queue logs request |
| `/api/system/emergency-pause` | POST | `X-Admin-Key` | Pause ALL bots |
| `/api/system/intents/pending` | GET | `X-Orchestrator-Key` | Orchestrator polls here |
| `/api/system/intents/result` | POST | `X-Orchestrator-Key` | Orchestrator reports back |

Wired into `main.py` (and `api/main.py`) at the same place as other routers.
Tables auto-create on first request.

### 2. `website/command-center.html` (REWRITTEN)
Single-page command center:
- **Sidebar nav**: Overview / Bots / API / Devices / Users / On-chain / Logs
- **6 KPI tiles**: API health · Bots online · Users 24h · Devices · SLH price · Pool TVL
- **Live bot grid** (25 bots) with status dots + per-bot Restart/Logs/Stop
- **Activity log** (in-browser, last 100 events)
- **Emergency pause button** with double-confirm
- **Auto-refresh every 15s** via polling
- **Graceful degradation** when API is down (shows fallback values, doesn't crash)
- **Neural design system** (consistent with rest of site)

### 3. `scripts/slh-orchestrator.py` (NEW)
The local agent that bridges API ↔ Docker:
- Polls `/api/system/intents/pending` every 15s
- For each intent: runs the matching `docker compose ...` command
- Reports back via `/api/system/intents/result`
- ALSO: pushes heartbeats for any running container (so even bots that don't yet
  implement heartbeat themselves get a status)
- CLI flags: `--once`, `--check` (sanity test), `--heartbeats-only`
- **Pure stdlib** — no extra Python deps needed

### 4. `scripts/slh-orchestrator.ps1` (NEW)
PowerShell wrapper that:
- Loads `.env` automatically
- Verifies Python is installed
- Runs the Python orchestrator
- Has `-Install` flag to register as a Windows scheduled task (auto-starts at boot)
- Has `-Uninstall` to remove the task

### 5. Bot heartbeat client snippet (FOR EACH BOT)
Each bot needs ~10 lines of code added so it self-reports. Template (Python):
```python
import os, requests, time, threading
def heartbeat_loop():
    while True:
        try:
            requests.post(
                os.environ["SLH_API_BASE"] + "/api/system/bots/heartbeat",
                headers={"X-Bot-Key": os.environ.get("BOT_HEARTBEAT_KEY", "")},
                json={"bot_name": "<your-bot-name>", "status": "up", "version": "1.0"},
                timeout=5,
            )
        except Exception as e:
            print(f"[heartbeat] {e}")
        time.sleep(30)
threading.Thread(target=heartbeat_loop, daemon=True).start()
```
**Until each bot implements this**, the orchestrator's heartbeats-only mode handles it.

---

## Required env vars for the new system

Add to **Railway** (service `SLH.co.il`):
```
ORCHESTRATOR_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
BOT_HEARTBEAT_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
```

Add to **local .env** (D:\SLH_ECOSYSTEM\.env), MUST match Railway exactly:
```
SLH_API_BASE=https://slhcoil-production.up.railway.app
ORCHESTRATOR_KEY=<same value as Railway>
BOT_HEARTBEAT_KEY=<same value as Railway>
ORCHESTRATOR_POLL_SECONDS=15
DOCKER_COMPOSE_FILE=D:/SLH_ECOSYSTEM/docker-compose.yml
DOCKER_COMPOSE_CMD=docker compose
```

---

## Activation steps (in order)

### Phase 1: Deploy the API changes (5 min)
```powershell
cd D:\SLH_ECOSYSTEM
# Verify the system_status.py imports correctly
python -c "from routes.system_status import router; print('OK')"

# Sync main.py copies
fc D:\SLH_ECOSYSTEM\main.py D:\SLH_ECOSYSTEM\api\main.py

# Commit
git add main.py api/main.py routes/system_status.py website/command-center.html `
        website/index.html website/about.html website/wallet.html website/admin.html `
        website/js/shared.js scripts/slh-orchestrator.py scripts/slh-orchestrator.ps1 `
        ops/CONTROL_LAYER_ARCHITECTURE_2026-04-27.md
git commit -m "feat: control layer + 5-page neural migration + theme switcher"
git push origin master
```

### Phase 2: Add the env vars to Railway (5 min)
1. Open Railway dashboard → service `SLH.co.il` → Variables
2. Add `ORCHESTRATOR_KEY` and `BOT_HEARTBEAT_KEY` (random 32-byte strings)
3. Wait for auto-redeploy (~2 min)
4. Verify: `curl https://slhcoil-production.up.railway.app/api/system/status`
   Expected: `{"ok": true, "api_up": true, "db_up": true, ...}`

### Phase 3: Run the orchestrator locally (5 min)
```powershell
cd D:\SLH_ECOSYSTEM

# First check
.\scripts\slh-orchestrator.ps1 -Check
# Expected: ✓ API reachable, ✓ Docker, ✓ Compose file, ✓ ORCHESTRATOR_KEY

# Run one cycle to test
.\scripts\slh-orchestrator.ps1 -Once

# Open command-center.html — bot tiles should now show GREEN dots for running bots
start https://slh-nft.com/command-center.html

# If satisfied, install as auto-start scheduled task
.\scripts\slh-orchestrator.ps1 -Install

# Then trigger it (or reboot)
Start-ScheduledTask -TaskName SLH-Orchestrator
```

### Phase 4: Test the control loop (5 min)
1. Open Command Center in browser
2. Hover over a bot tile → click "Restart"
3. Confirm → check the activity log: should say "intent queued"
4. Within ~15s, the orchestrator picks it up, runs `docker compose restart <bot>`,
   and reports back. Check the bot tile turns GREEN with fresh heartbeat.

If this works → **you have unified control. Mission accomplished.**

---

## What this DOES NOT solve (yet — see STRATEGIC_ROADMAP)

- **Bot hosting**: bots still run on Osif's Docker. The orchestrator works the same
  whether they run locally or on a VPS. To move them: see Pillar 1 in STRATEGIC_ROADMAP.
- **ESP32 ledger**: still untouched. Phase E1-E4 in STRATEGIC_ROADMAP.
- **Multi-domain sync**: subdomain setup is DNS work, see Pillar 3 in STRATEGIC_ROADMAP.
- **Bot heartbeats**: until each bot adds the 10-line snippet, the orchestrator
  pushes heartbeats on their behalf based on Docker container state. This is fine
  for now — full bot-side heartbeats can come in the next session.

---

## TL;DR for the impatient

**Before today**: 25 bots that don't talk to each other, no central status, no central control.

**After today**:
- One DB (Railway PostgreSQL) is the single source of truth.
- One API endpoint (`/api/system/*`) is the gateway for all status + control.
- One UI page (`command-center.html`) shows everything and controls everything.
- One local script (`slh-orchestrator`) bridges the API to Docker.
- One env var pair (`ORCHESTRATOR_KEY` + `BOT_HEARTBEAT_KEY`) unlocks it all.

**You went from "an aggregate of components" → "a system."**
