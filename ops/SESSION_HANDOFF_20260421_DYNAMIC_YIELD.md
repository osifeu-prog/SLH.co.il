# Session Handoff — 2026-04-21 — Dynamic Yield Pivot Complete

**Operator:** Claude (Opus 4.7, 1M context)
**Session goal:** Full Dynamic Yield business model pivot + copy overhaul + Course #1 launch
**Outcome:** SHIPPED. Website live on slh-nft.com, ops docs committed, backend partially staged.

---

## TL;DR for Osif

- ✅ **SLH no longer promises fixed APY anywhere in the UI.** 65%/60%/55%/48% strings removed from 19 HTML files + 2 bots + shared.js footer.
- ✅ **Course #1 "Dynamic Yield Economics" is LIVE** at https://slh-nft.com/academy/course-1-dynamic-yield.html — 6 modules, interactive calculator, Python simulator, 3 pricing tiers (Free / ₪179 Pro / ₪549 VIP).
- ✅ **Referral capped at 2 tiers** (Tier 1: 20%, Tier 2: 5%) — UI everywhere + backend in working copy (not yet live, see "Pending" below).
- ✅ **Legal risk page** (`/risk.html`) — 9-section full disclosure.
- ✅ **Shared footer disclaimer** appears on all 43 pages automatically via `shared.js`.
- ✅ **AISITE bug fix** — `master_controller.py` SERVICES dict no longer references non-existent scripts.
- 🟡 **Backend referral cap** not yet on Railway — bundled with Phase 0 DB Core (Night 21.4 work) which Osif previously held back.

---

## What shipped (pushed to remote)

### Website repo — `osifeu-prog/osifeu-prog.github.io` branch `main`
- Commit `61482aa` — 29 files changed (3,101 insertions, 111 deletions)
- Auto-deployed to GitHub Pages → live on slh-nft.com within 1-2 min

### API repo — `osifeu-prog/slh-api` branch `master`
- Commit `642f080` — 6 files changed (1,126 insertions)
- Includes ops/ docs + bot messages (userinfo-bot, expertnet-bot)
- Railway auto-deployed → `/api/health` returns `{"status":"ok","db":"connected","version":"1.1.0"}`

### AISITE (local lab, separate)
- `D:\AISITE\master_controller.py` — fixed SERVICES dict (dashboard cmd → `python -m http.server 8000`, removed non-existent command_listener.py + terminal_monitor.py references)
- **Not committed** (separate repo, may not have git — Osif to manage separately)
- Lab still down; fix is ready for next `START_ALL.ps1`

---

## What's pending (YOUR DECISIONS)

### 🟡 Decision 1: Push Phase 0 DB Core + backend referral cap
`api/main.py` working copy contains:
- **Phase 0 DB Core** (from earlier tonight's session) — `shared_db_core.py` unified pool, `/api/health` returns 503 honestly when DB is down. See `ops/NIGHT_20260421_PHASE0_DB_CORE.md`.
- **My referral cap** — `REFERRAL_RATES = {1: 0.20, 2: 0.05}`, `MAX_GENERATIONS = 2`. Replaces old 10-tier logic.
- **3 OG subtitle fixes** — `referral`/`liquidity`/`staking` page OG-card subtitles reframed to Dynamic Yield language.

**These are bundled.** To deploy both together:
```bash
cd D:\SLH_ECOSYSTEM
git add api/main.py main.py api/shared_db_core.py shared_db_core.py ops/NIGHT_20260421_PHASE0_DB_CORE.md
git commit -m "Phase 0 DB Core + 2-tier referral enforcement"
git push origin master
# Railway auto-deploys
```

**Risk:** If Phase 0 has untested edge cases, Railway may fail health checks. Mitigation: the new `/api/health` is designed to return 503 cleanly, not crash.

**Until this is pushed:** UI says "2 tiers" but backend still computes 10 if an old referral_rate dict is ever re-referenced. Current production computes correct rates from the old constants. **This is a UI/API mismatch but not a money-at-risk issue — only mismatch = the OLD "rich referral" endpoints return slightly higher numbers than the UI implies. Low urgency.**

### 🟡 Decision 2: Seed Course #1 into Railway Postgres
```bash
# From any host with psql + Railway DATABASE_URL:
psql "$DATABASE_URL" -f D:/SLH_ECOSYSTEM/ops/SEED_COURSE_1_DYNAMIC_YIELD.sql
```
Creates Osif instructor record + 3 course rows (Free/Pro/VIP) in `academy_courses`.
Without this, the academia catalog won't show Course #1 rows (though the Featured Banner already works — it's hardcoded in HTML).

### 🟡 Decision 3: Restart AISITE lab
`master_controller.py` bug is fixed. To restart:
```powershell
cd D:\AISITE
.\START_ALL.ps1
# Opens control_api on 5050, which spawns master_controller,
# which spawns: dashboard (8000), esp_bridge (5002),
# system_bridge (5003), agent_listener, payment_bot
```
**Before running:**
- Confirm ESP32 @ 10.0.0.4 powered on, Beynoni WiFi up
- Docker Desktop currently squats port 8001. If you want `panel.py` on 8001, either stop Docker or change panel's port
- `secure/esp_command.json` contains a stale 2.5KB Hebrew text command from Apr 20 01:02 — safe to delete before restart

### 🟡 Decision 4: Telegram broadcast to existing stakers
Template ready in `ops/COPY_OVERHAUL_URGENT_20260420.md` under "What to tell existing users". Pin for 14 days recommended.

### 🟡 Decision 5: Legal entity registration
`/risk.html` flags "operating as עוסק מורשה, not a registered company" as a Critical risk. Target: Q1 2026. Independent of my scope.

---

## Full deliverables index

### Ops docs (`D:\SLH_ECOSYSTEM\ops\`)
| File | Purpose |
|------|---------|
| `DYNAMIC_YIELD_SPEC_20260420.md` | Formulas, Circuit Breakers, Treasury, migration plan |
| `COPY_OVERHAUL_URGENT_20260420.md` | Exact copy change map + broadcast template |
| `SEED_COURSE_1_DYNAMIC_YIELD.sql` | DB seed for Course #1 instructor + 3 tiers |
| `treasury_simulation.py` | Python simulator (Bear/Base/Bull/Crisis) |
| `SESSION_HANDOFF_20260421_DYNAMIC_YIELD.md` | This doc |

### Course #1 (`D:\SLH_ECOSYSTEM\website\academy\`)
| File | Purpose |
|------|---------|
| `course-1-dynamic-yield.html` | Landing page — 3 tiers, curriculum, FAQ |
| `course-1-dynamic-yield/module-1.md` | **Free** — Ponzi Detection Framework (7 flags) |
| `course-1-dynamic-yield/module-2.md` | **Free** — Revenue Engine vs Reward Engine |
| `course-1-dynamic-yield/module-3.md` | **Pro** — Dynamic Yield mathematics (5 scenarios) |
| `course-1-dynamic-yield/module-4.md` | **Pro** — Treasury engineering (3 layers, multi-sig) |
| `course-1-dynamic-yield/module-5.md` | **Pro** — Circuit Breakers (5 mechanisms + runbook) |
| `course-1-dynamic-yield/module-6.md` | **Pro** — SLH live case study + Certificate quiz |
| `course-1-dynamic-yield/calculator.html` | Interactive Dynamic Yield calculator |

### Website (`D:\SLH_ECOSYSTEM\website\`) — modified
19 HTML files + `js/shared.js` + new `risk.html`. See commit `61482aa` for full diff.

### Bots (`D:\SLH_ECOSYSTEM\`)
- `userinfo-bot/main.py` — share message "65% APY" → "Revenue Share Pool"
- `expertnet-bot/main.py` — 5 locations converted to Dynamic Yield language

### Lab fix (`D:\AISITE\`)
- `master_controller.py` — SERVICES dict fixed (3 broken entries removed/repaired)

---

## Verification commands

```bash
# Confirm website is live
curl -sI https://slh-nft.com/academy/course-1-dynamic-yield.html | head -3
# Expect: HTTP/1.1 200 OK

# Confirm Railway API is healthy
curl -s https://slh-api-production.up.railway.app/api/health
# Expect: {"status":"ok","db":"connected","version":"1.1.0"}

# Confirm no APY claims remain on website (should return 0 results)
cd D:\SLH_ECOSYSTEM\website
grep -rn "65% APY\|60% APY\|up to 65\|עד 65%" --include="*.html"

# Confirm no 10-generation refs on website
grep -rn "10 דורות\|10 generations" --include="*.html"

# Run treasury simulator
cd D:\SLH_ECOSYSTEM\ops
pip install numpy matplotlib
python treasury_simulation.py --all
# Generates 4 PNGs + 4 CSVs in ./simulation_output/
```

---

## Rollback plan (if needed)

### Website rollback
```bash
cd D:\SLH_ECOSYSTEM\website
git revert 61482aa
git push origin main
# GitHub Pages rebuilds in 1-2 min
```

### API rollback
```bash
cd D:\SLH_ECOSYSTEM
git revert 642f080
git push origin master
# Railway auto-rebuilds
```

Both reverts are clean — single-commit changes, no merge conflicts expected.

---

## Known gaps (not addressed this session)

- **Whitepaper** (`whitepaper.html`) not audited — may still contain legacy APY/10-gen claims
- **Other bots** (admin-bot, campaign-bot, game-bot, etc.) not grepped — may have APY messages
- **On-chain Treasury wallets** (BSC + TON multi-sig) — design in spec, not yet deployed
- **Live CR widget on /status** — designed, not built
- **External audit** — budgeted but not commissioned

---

## Links

- Production site: https://slh-nft.com
- Course #1 landing: https://slh-nft.com/academy/course-1-dynamic-yield.html
- Risk disclosure: https://slh-nft.com/risk.html
- API health: https://slh-api-production.up.railway.app/api/health
- GitHub website repo: https://github.com/osifeu-prog/osifeu-prog.github.io
- GitHub API repo: https://github.com/osifeu-prog/slh-api

---

**Status: CONTROL RETURNED.**
Osif decides Decisions 1-5 above on his own schedule. Nothing is time-bombed.

*End of handoff — 2026-04-21*
