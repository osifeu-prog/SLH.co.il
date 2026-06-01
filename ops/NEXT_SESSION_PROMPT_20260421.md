# Next Session Handoff Prompt — 2026-04-21 → Next

Copy-paste the block below into the next Claude session:

---

## HANDOFF PROMPT

You are continuing the SLH Ecosystem Phase 0 (System Control & Trust) rollout.

### Where we are now

Phase 0 DB Core **IS LIVE** on Railway as of 2026-04-21:
- Commit `cfc98e4 Phase 0 DB Core + 2-tier referral enforcement` pushed to `origin/master`
- Commit `162a7f4 feat(treasury+audit): wire revenue recording into live sales flows` also live
- Treasury/health endpoint verified live: `curl https://slh-api-production.up.railway.app/api/treasury/health` returns real JSON with breakeven block
- My files (`shared_db_core.py`, `main.py`, `api/main.py` + mirror) are byte-identical to origin/master — no local reconciliation needed

Read the full audit report: `D:\SLH_ECOSYSTEM\ops\NIGHT_20260421_PHASE0_DB_CORE.md`
D:\ system map + cleanup plan: `D:\SLH_ECOSYSTEM\ops\SYSTEM_MAP_AUDIT_20260421.md`

Read the full audit report first: `D:\SLH_ECOSYSTEM\ops\NIGHT_20260421_PHASE0_DB_CORE.md`

### First action (do before anything else)

Ask Osif which path to take:

**A. Deploy what's local now (Phase 0 foundation only).**
   - Review diff, `git add` 4 files, commit, push.
   - Watch Railway logs for first deploy.
   - Verify `/api/health` returns the new structured response.
   - Risk: if Railway has no working DB, `/api/health` will return 503 and any
     external monitor expecting 200 will alert. Confirm with Osif that's OK.

**B. Phase 0B — migrate bot fleet to shared_db_core before deploying.**
   - 22 bots still call `asyncpg.create_pool` directly.
   - Batch-migrate 5 highest-traffic first: academia, wallet, expertnet, school, admin.
   - Each bot: `from shared_db_core import init_db_pool` + replace `create_pool`.
   - Test locally via `D:\SLH_CONTROL.ps1 restart`, then deploy all together.

**C. Phase 2 — Identity Proxy `/api/verify-trust`.**
   - Defer bot migration. Build centralized trust endpoint instead.
   - Spec: accept `{bot_id, session_token, action_hash}` → `{trusted: bool, reason: str}`.
   - Every bot must call this before sensitive actions (transfers, admin ops).
   - New table `trust_sessions` required.

**D. Phase 3 — Ledger unification.**
   - Merge `love_token_transfers` into unified `token_ledger` table.
   - Requires schema migration + `routes/love_tokens.py` rewrite.
   - Higher risk — touches real balance data.

### Non-negotiables (from memory + CLAUDE.md)

- **Railway syncs root `main.py`.** Every edit must also go to `api/main.py`. Use `cp` + `diff` to verify.
- **Hebrew UI, English code/commits.**
- **Never fake data** in production pages.
- **Never hardcode passwords in HTML** — use `localStorage.slh_admin_password`.
- **Work Rules memory** (`feedback_work_rules.md`) — Railway syncs root main.py, never fake data, Hebrew UI, real-time verification.

### Pre-existing blockers (not owned by next session)

- `JWT_SECRET` not set on Railway (needs Osif's dashboard access)
- `ADMIN_BROADCAST_KEY` default still — use `slh-broadcast-2026-change-me`, NOT `slh2026admin`
- 4 contributors still haven't logged into website for ZVK
- Wallet.html: no on-chain balance calls yet

### Memory files worth reading first

- `MEMORY.md` index (auto-loaded)
- `project_night_20260420_late.md` — last night's audit
- `feedback_work_rules.md` — DO/DON'T rules
- `project_ecosystem.md` — 113 endpoints, 43 pages, 25 bots context

### Verification checklist when done

After any deploy:
```bash
curl https://slh-api-production.up.railway.app/api/health
```
Expected (DB up): `{"status":"ok","db":"connected","version":"1.1.0"}`
Expected (DB down): HTTP 503 + `{"status":"error","db":"pool_unavailable",...}`

After any bot migration:
```powershell
D:\SLH_CONTROL.ps1 restart
D:\SLH_CONTROL.ps1 health
```

### Do not do

- Don't force-push to master.
- Don't skip pre-commit hooks.
- Don't introduce new features (agents, arbitrage, NFT identity) before Phase 0 is production-verified.
- Don't enable P2P settlement with real funds.
- Don't hardcode passwords in HTML.
- Don't assume the user wants a multi-hour refactor — ask before widening scope.

### How to talk to Osif

Hebrew, direct, action-first. Short explanations. "כן לכל ההצעות" = proceed with all.
If a plan affects Railway production, **stop and confirm** before deploy. Local edits are safe by default.

---

## END HANDOFF PROMPT
