# 🤝 Session Handoff — 2026-04-20 Evening — Chain Close

**Session scope:** Close the ESP ↔ TG ↔ Guardian ↔ Ledger ↔ API loop end-to-end.
**Result:** Done + verified live on Railway. 6 commits across 3 repos.
**Next session starts with:** Execute `ops/OSIF_CHECKLIST_POST_CHAIN_20260420.md` items #1–#3.

---

## Deliverables shipped

### Code (all committed + pushed)

| Repo | Branch | Commits | Effect |
|------|--------|---------|--------|
| `osifeu-prog/slh-api` | `master` | `340b771`, `3afad0e`, `b06c632`, `4ce9862` | New `/api/esp/*`, `/api/device/claim`, `/api/academia/license/status`, `/api/academia/earnings/mark-paid`. ZUZ gate on wallet/staking. Event bus. Ledger listener. Academia payment timeout fix. |
| `osifeu-prog/osifeu-prog.github.io` | `main` | `b732f7a` | `device-pair.html` + `chain-status.html` |
| `osifeu-prog/slh-guardian` | `main` | `fcd2afb` | `slh_api_client.py` + 7 `/gr_*` admin commands |

### Docs
- `ops/UNIFIED_CHAIN_DESIGN_20260420.md` — the approved design (what I proposed)
- `ops/UNIFIED_CHAIN_LAUNCH_20260420.md` — execution notes + verification checklist
- `ops/OSIF_CHECKLIST_POST_CHAIN_20260420.md` — 9 action items for Osif (⚠️ key source of truth for next steps)
- `ops/firmware/slh-device-v3/FLASH_INSTRUCTIONS.md` — how to flash the device

### Firmware (source tracked, binary not flashed)
- `ops/firmware/slh-device-v3/` — full PlatformIO project. First-boot QR pair, NVS token persistence, Railway Bearer heartbeat w/ local fallback, balance display.

---

## Verification done in this session

| Check | Method | Result |
|-------|--------|--------|
| `/api/health` | curl | 200 ✓ |
| `/api/device/register` → `/api/device/verify` → signing_token | full flow with test phone 0500000088 | user_id=3 ✓ |
| `/api/esp/heartbeat` with bearer | curl + real token | heartbeat_id=1 ✓ |
| `/api/esp/heartbeat` without bearer | curl | 401 ✓ |
| `/api/device/claim` proper order (before HB) | curl | `paired:true, user_id:3` ✓ |
| `/api/device/claim` reverse order (after HB) | curl | `paired:false, note:"already claimed"` ✓ |
| `/api/academia/license/status` | curl | 200 graceful (note:"table_unavailable" when tables on remote DB) ✓ |
| `/api/staking/stake` clean user | curl | reaches plan validation, no false 403 ✓ |
| `chain-status.html` loads | curl -I | 200 ✓ |
| `device-pair.html` loads | curl -I | 200 ✓ |

---

## Verification NOT done (requires Osif physical access)

1. **Device flash** — firmware v3 exists but the device at 10.0.0.4 still runs v2 (`esp32-heartbeat.ino`). Needs USB + `pio run -t upload`.
2. **Guardian bot runtime test** — new `/gr_ping` / `/gr_report` commands exist in code but the container needs rebuild + restart + `SLH_ADMIN_KEY` env.
3. **Ledger-listener fanout** — code wired, but needs `LEDGER_WORKERS_CHAT_ID` set + ledger-bot restart.
4. **ZUZ block on real flagged user** — gate code is live, but I didn't flag a real user to verify end-to-end 403. Safe to do in prod: flag user 999999999 (test), try stake, see 403, unflag.

---

## Architecture notes for next Claude

- **Two Postgres DBs coexist:** Railway DB (the Railway API reads from this) vs docker-compose local DB (the bots write here). `academy_licenses` lives on the LOCAL DB because the academia-bot is a docker container next to the postgres container. Don't assume cross-DB visibility. Each endpoint that reads tables like `academy_licenses`, `token_balances`, `staking_positions` needs to handle "relation does not exist" gracefully (see my `license/status` pattern).
- **`main.py` and `api/main.py` sync:** Repo cleanup commit `99d4ce9` (not mine, appeared between my pushes) removed the `api/routes/` stale mirror dir. Now there is only ROOT `routes/`. Fine. `main.py` at the root is still duplicated with `api/main.py` — I synced both in my commits.
- **The shared/ folder is reused by 20+ bots** — my `ledger_listener.py` is gated by `BOT_KEY=="ledger"` so other bots are unaffected. `guardian_gate.py` is lazy-imported inside endpoints so a shared/-level bug can't break startup.
- **Event bus is DB-polled** (no Redis dep). Poll interval 3s. Cursor persisted per-consumer in a JSON file. Scale limit: fine up to ~30 events/sec; if traffic grows, swap to Redis Streams.

---

## Known issues still open

| # | Issue | Impact | Next step |
|---|-------|--------|-----------|
| 1 | 5 prompt injections seen in session | Could corrupt future work | Screenshot one in next session + share source |
| 2 | Stuck ACAD payments for user 8789977826 | Lost sales | Manual license insert per checklist #2 |
| 3 | `GUARDIAN_BOT_TOKEN` still exposed | Security | BotFather rotation per checklist #1 |
| 4 | `/api/esp/heartbeat` claim heuristic edge case | Device re-pair after heartbeat returns "already claimed" | Consider a separate `token_issued_at` column if re-pairing becomes common |
| 5 | 2 mystery commits appeared mid-session (`99d4ce9`, `9774a78`) | Unknown provenance | Check `git log` and identify author next session |

---

## How to start the next session

1. Read this file + `ops/OSIF_CHECKLIST_POST_CHAIN_20260420.md`.
2. `curl https://slh-api-production.up.railway.app/api/health` — sanity check.
3. Ask Osif which checklist item to tackle.
4. If Osif completed items #1–#3 in between sessions, next-priority work is probably: item #5 (flash) OR start on a new feature (he'll specify).

---

## Rollback one-liner (emergency only)

```bash
cd /d/SLH_ECOSYSTEM && git revert 340b771 && git push
```
Railway autodeploys within 90s. Other 2 repos don't affect production runtime.
