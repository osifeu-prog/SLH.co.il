# SLH_PROJECT_V2 :: PROJECT_SCAN

Updated at: 2026-03-09 17:19:54

## Purpose
Single-file operational and architectural scan for fast future handoff.

## Repository
- Root: D:\SLH_PROJECT_V2
- Remote: https://github.com/osifeu-prog/SLH_PROJECT_V2.git
- Branch: main
- Current commit: 53acfca

## Current Understanding
- Telegram production webhook points to Railway
- Local stack exists for hardening and diagnostics
- Runtime architecture is webhook -> redis -> worker -> postgres
- Ledger-backed finance layer exists
- Withdrawal hardening is documented as verified
- Bot domain includes rewards, invites, tasks, profile, admin, withdrawals

## Working Protocol
- No guessing
- Always inspect code or runtime state before proposing changes
- First provide PowerShell commands to expose the needed data
- User runs the commands and returns the output
- Only after enough evidence exists, provide exact PowerShell patch commands
- Preserve UTF-8 without BOM and LF endings
- Prefer minimal patches and clean commit scope
- Target: safe path toward 100K registered users

## Local Health
{"ok":true,"mode":"webhook->redis->worker","release":"3f22873"}

## Running Local Python Processes

ProcessId CommandLine                                                                     
--------- -----------                                                                     
    27856 "D:\SLH_PROJECT_V2\venv\Scripts\python.exe" D:\SLH_PROJECT_V2\webhook_server.py 
    16876 "D:\SLH_PROJECT_V2\venv\Scripts\python.exe" D:\SLH_PROJECT_V2\worker.py

## Git Status
 M ops/doctor.ps1
 M ops/session-end.ps1
 M ops/session-start.ps1
 M slh.ps1
 M state/ANCHOR.md
 M worker.py
?? ops/morning-start.ps1
?? ops/restart-safe.ps1

## Handlers
claim.py
invite.py
task_verifications.py
tasks.py
ton_admin.py
withdraw.py.bak_20260307_161237
withdrawals.py
withdrawals.py.bak_20260307_161237

## Services
bootstrap.py
bootstrap.py.bak_20260307_153714
daily.py
daily.py.bak_20260307_145124
economy.py
profile.py
task_verifications.py
task_verifications.py.bak_20260307_153714
tasks.py
tasks.py.bak_20260307_151726
tasks.py.bak_20260307_152645
ton_gateway.py
withdrawals.py
withdrawals.py.bak_20260307_143155
withdrawals_exec.py
withdrawals_query.py
withdrawals_query.py.bak_20260307_143155
xp.py

## Ops Files
_fix_health_route_order.py
_patch_health_aliases.py
admin-console.ps1
apply_user_tasks_hardening.sql
ast_check_tasks.py
ast_check_tasks_handler_fix.py
backup.ps1
check-queue.ps1
clear-pending-updates.ps1
common.ps1
create_task_verifications.sql
db-report.ps1
debug_task1_service_check.py
doctor.ps1
fix_integrity_economy_xp_v1.py
fix_integrity_growth_v1.py
fix_task_lock_bigint_singlekey.py
fix_task_lock_signature.py
fix_tasks_handler_ux_v1.py
forensic_read_sources.py
get-tunnel-url.ps1
get-webhook-info.ps1
maintain.ps1
midday-check.ps1
morning-start.ps1
patch_admin_v1.py
patch_ascii_only_mode.py
patch_leaderboard_v1.py
patch_main_dedup_bot_online.py
patch_main_force_line114.py
patch_main_remove_escaped_unicode_prints.py
patch_main_remove_rocket.py
patch_main_remove_rocket_prints.py
patch_main_remove_u0001f680.py
patch_main_repair_and_neutralize.py
patch_main_strip_nonascii_prints.py
patch_main_utf8.py
patch_profile_render_v1.py
patch_profile_render_v2.py
patch_referral_xp_v1.py
patch_referral_xp_v2.py
patch_tasks_stage_a2_v1.py
patch_worker_task_verifications_router.py
queue-health.ps1
reconciliation_smoke.ps1
ref-report.ps1
refresh-project-scan.ps1
reset_core_only.py
reset_main.py
reset_referral_test_user.sql
restart.ps1
restart-safe.ps1
restore_core_handlers_v1.py
restore_worker_init_v1.py
rotate_bot_token.ps1
run_claim_daily_test.py
run_daily_and_task3_test.py
run_referral_manual_task_test.py
run_task3_claim_test.py
run_withdraw_e2e_test.py
run_withdraw_fail_e2e_test.py
runbook-manual-stable.ps1
run-cloudflared.cmd
run-supervised.ps1
run-tunnel.ps1
run-webhook.ps1
run-worker.ps1
safe-stop-and-close-day.ps1
session-end.ps1
session-report.ps1
session-start.ps1
set-webhook.ps1
set-webhook-from-tunnel.ps1
smoke.ps1
snapshot.ps1
stack-down.ps1
stack-logs.ps1
stack-restart.ps1
stack-status.ps1
stack-up.ps1
start.ps1
start-core.ps1
start-full-auto.ps1
start-local-stack.ps1
start-redis.ps1
start-stable.ps1
start-stable.ps1.bak_20260308_000242
start-stack.ps1
start-tunnel.ps1
start-tunnel-manual.ps1
start-webhook.ps1
start-worker.ps1
status.ps1
status-core.ps1
status-stable.ps1
status-stack.ps1
stop.ps1
stop-core.ps1
stop-stable.ps1
stop-stack.ps1
tail-logs.ps1
tail-stack.ps1
wait-tunnel-ready.ps1
write_core_only_fixed.py

## Markdown Sources
_snapshot_state_20260307_172453\ARCHITECTURE.md
_snapshot_state_20260307_172453\ROADMAP.md
_snapshot_state_20260307_172453\RUNBOOK.md
_snapshot_state_20260307_172453\STATE.md
_snapshot_state_20260307_215057\ARCHITECTURE.md
_snapshot_state_20260307_215057\ROADMAP.md
_snapshot_state_20260307_215057\RUNBOOK.md
_snapshot_state_20260307_215057\STATE.md
ARCHITECTURE.md
backups\freeze_legacy_20260306_105319\RUNBOOK.md
backups\freeze_legacy_20260306_105319\STATE.md
NEXT_STEPS.md
state\ANCHOR.md
state\ARCHITECTURE.md
state\PROJECT_BRIEF.md
state\PROJECT_SCAN.md
state\ROADMAP.md
state\RUNBOOK.md
state\STATE.md
STATE_RUNBOOK.md

## Telegram Webhook Info
{
    "ok":  true,
    "result":  {
                   "url":  "https://slhprojectv2-production.up.railway.app/tg/webhook",
                   "has_custom_certificate":  false,
                   "pending_update_count":  0,
                   "max_connections":  40,
                   "ip_address":  "151.101.66.15",
                   "allowed_updates":  [
                                           "message",
                                           "callback_query"
                                       ]
               }
}

---

## ROOT ARCHITECTURE.md
# SLH_PROJECT_V2 ARCHITECTURE

Core Flow

Telegram
↓
Cloudflare Tunnel
↓
Webhook Server
↓
Redis Queue
↓
Worker
↓
PostgreSQL

---

Components

webhook_server.py
Receives Telegram updates

worker.py
Processes queue events

Redis
Message queue

PostgreSQL
State and balances

Cloudflared
Public endpoint tunnel

---

Health Endpoint

/healthz

Returns:

{"ok":true,"mode":"webhook->redis->worker"}

---

Operational Scripts

slh.ps1
Main control interface

morning-start.ps1
Startup validation

stop-stable.ps1
Safe shutdown

tail-stack.ps1
Live logs

session-start.ps1
Begin work session

session-end.ps1
Close work session

---

Key Tables

user_balances
audit_log
withdrawals
tasks
invites

---

Design Goals

Operational stability  
Financial correctness  
Auditability  
Scalable worker model

---

## ROOT NEXT_STEPS.md
# SLH_PROJECT_V2 NEXT STEPS

Goal:
Reach first 100K users safely.

---

PHASE 1
Operational stability

- Stable startup workflow
- Safe shutdown
- Session tracking
- Restart snapshots
- Monitoring

---

PHASE 2
Financial correctness

- Withdrawal validation
- Balance invariants
- Audit consistency
- Retry safety

---

PHASE 3
Observability

- startup timing
- restart reports
- failure analysis
- worker health

---

PHASE 4
Operator tooling

Admin commands
System reports
Failure summaries

---

PHASE 5
Growth engine

Referral system
Campaign system
Invite tracking
Retention metrics

---

PHASE 6
Scale readiness

Queue stability
Worker concurrency
Webhook resilience
Rate limiting
Idempotency

---

## ROOT STATE_RUNBOOK.md
# SLH_PROJECT_V2 — OPERATIONAL RUNBOOK

Project Root:
D:\SLH_PROJECT_V2

Architecture:
webhook -> redis -> worker

Local health endpoint:
http://127.0.0.1:8080/healthz

---

# MORNING START

cd D:\SLH_PROJECT_V2

Start work session:

.\ops\session-start.ps1 -Type "development" -Notes "daily startup"

Run validation:

powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\morning-start.ps1 -SkipStart

If stack not running:

powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\morning-start.ps1

Check status:

.\slh.ps1 status

Health check:

Invoke-WebRequest "http://127.0.0.1:8080/healthz" -UseBasicParsing

Expected:

{"ok":true,"mode":"webhook->redis->worker"}

---

# TELEGRAM TEST FLOW

/start
Profile
Balance
Health

Optional:

Withdraw 1

---

# DATABASE CHECK

psql -U postgres -d slh_db -c "
SELECT user_id, available, locked, updated_at
FROM user_balances
ORDER BY user_id;
"

Audit:

psql -U postgres -d slh_db -c "
SELECT id, user_id, event_type, created_at
FROM audit_log
ORDER BY id DESC
LIMIT 20;
"

---

# LOG MONITOR

.\ops\tail-stack.ps1

---

# SAFE STOP

.\ops\stop-stable.ps1

---

# END SESSION

.\ops\session-end.ps1 -Status "completed" -Notes "work finished"

---

# STATE DIRECTORIES

runtime/
session tracking

state/
restart snapshots

logs/
stack logs

---

# SOURCE OF TRUTH

Stack status:
slh.ps1 status

Health:
http://127.0.0.1:8080/healthz

DB:
PostgreSQL queries

Sessions:
runtime/work_sessions.csv

Runtime:
runtime/*.pid

---

## state\ANCHOR.md
# SLH_PROJECT_V2 :: ANCHOR

## Project root
D:\SLH_PROJECT_V2

## Verified local ops state
- Local stack is operational
- Flow: webhook -> redis -> worker
- Local health endpoint returns ok=true
- Telegram bot core flows verified earlier and working
- Audit trail working
- Withdrawals / tasks / profile / leaderboard / balance / invite / health verified

## Stable ops commands
- .\slh.ps1 up
- .\slh.ps1 down
- .\slh.ps1 status
- .\slh.ps1 health
- .\slh.ps1 logs
- .\slh.ps1 doctor
- .\slh.ps1 restart

## Stable ops scripts
- .\slh.ps1
- .\ops\start-stable.ps1
- .\ops\stop-stable.ps1
- .\ops\status-stable.ps1
- .\ops\doctor.ps1
- .\ops\restart-safe.ps1

## Verified env/config state
- .env exists
- DATABASE_URL normalized to local postgres form
- Current DATABASE_URL:
  postgresql://postgres@127.0.0.1:5432/slh_db

## Snapshot
- Latest ops snapshot:
  .\state\ops_snapshot_20260309_133653

## Current runtime pattern on Windows
- webhook has wrapper pid + actual pid
- worker has wrapper pid + actual pid
- This is expected with venv on Windows in current setup

## Current known caveats
- status display formatting was previously messy during manual paste cycles, but runtime behavior is currently healthy
- prefer using fixed scripts and avoid pasting PowerShell prompt text itself into terminal

## Next recommended engineering step
- create/update STATE/NEXT_STEPS.md or continue with product work above ops layer
- if staying in ops/domain tooling, next best step is a compact state handoff file + optional repo cleanup/commit

## Resume instruction for next chat
Continue from D:\SLH_PROJECT_V2 with the local ops layer already stabilized and verified. Start by reading this anchor, then propose the next highest-value step without rebuilding the ops foundation unless a regression is shown by doctor/health.

---

## state\ARCHITECTURE.md
# SLH_PROJECT_V2 — ARCHITECTURE

## Core System

Telegram bot worker architecture.

Main entry:

worker.py

Framework:

aiogram

---

# Main Components

Routers:

claim_router
tasks_router
invite_router
withdrawals_router
ton_admin_router
task_verifications_router

---

# Finance Architecture

Ledger-backed system.

Tables:

users
user_balances
ledger_accounts
ledger_entries
withdrawals
withdrawal_reservations
audit_log

---

# Withdrawal Lifecycle

pending
approved
sent
failed

Reservation states:

reserved
consumed
released

---

# Consistency Model

Invariant:

user_balances.available
==
users.balance
==
ledger_user_available

Locked balances:

user_balances.locked
==
ledger_user_locked

---

# Testing

E2E tests:

ops/run_withdraw_e2e_test.py
ops/run_withdraw_fail_e2e_test.py

Both paths validated.

---

# Worker Responsibilities

Receive updates via Redis stream.

Process Telegram events.

Dispatch handlers.

Write to database.

Maintain financial integrity.

---

# Future Architecture

Queue-based processing.

Microservice separation.

API layer.

Horizontal scaling.

---

## state\ROADMAP.md
# SLH_PROJECT_V2 - ROADMAP

## Current Phase
System hardening and architecture stabilization.

Ledger-backed finance layer is active and verified.
Withdrawal hardening is complete and verified.

---

## Phase 1 - Hardening (Current)

Completed in this phase:

- canonical withdrawal handler consolidated at `app/handlers/withdrawals.py`
- `worker.py` uses only `withdrawals_router` for withdrawal flows
- service-level wallet validation added in `app/services/withdrawals.py`
- canonical withdrawal creation audit event now uses `finance.withdraw.created`
- withdrawal happy path verified end-to-end
- withdrawal failure / release path verified end-to-end
- doctor diagnostics added and verified in `ops/doctor.ps1`
- audit naming DB patch added at `ops/sql/patch_withdraw_audit_naming.sql`

Known nuance:

- runtime code is canonical
- historical legacy audit rows still exist from older runs
- historical rows are not a blocker

Remaining hardening order:

1. reconciliation smoke test
2. admin monitoring improvements
3. withdrawal rate limiting

Selected next implementation target:

- reconciliation smoke test

Why this is next:

- it codifies the verified ledger invariants into a repeatable operator check
- it reduces regression risk before more runtime features are added
- it keeps the next step low-risk and aligned with current repo state

---

## Phase 2 - Operational Safety

Planned after reconciliation smoke test:

- improve admin monitoring visibility
- add operator-facing finance diagnostics where useful
- add withdrawal rate limiting
- strengthen failure detection and operational confidence

---

## Phase 3 - Scalability

After hardening and operational safety:

- introduce queue-oriented job processing where needed
- separate worker responsibilities more cleanly
- optimize DB access patterns
- prepare safe horizontal scaling

---

## Phase 4 - Production Deployment

After stabilization:

- containerization cleanup
- automated deployment workflow
- monitoring and alerts
- high-availability oriented deployment shape

---

## Long Term

- multi-worker architecture
- API layer for external integrations
- financial reporting module
- advanced analytics


---

## state\RUNBOOK.md
# SLH_PROJECT_V2 - RUNBOOK

Operational guide for developers and operators.

---

## Project Root

D:\SLH_PROJECT_V2

---

## Start Worker

python worker.py

---

## Run Withdrawal Success Test

python ops/run_withdraw_e2e_test.py

---

## Run Withdrawal Failure Test

python ops/run_withdraw_fail_e2e_test.py

---

## Run Reconciliation Smoke Test

powershell -ExecutionPolicy Bypass -File .\ops\reconciliation_smoke.ps1

Expected result:

- postgres connection OK
- ledger reconciliation OK
- no finance snapshot drift
- withdrawal reservation sanity OK
- RECON_SMOKE_OK

---

## Run Doctor

.\ops\doctor.ps1

---

## Check Ledger Consistency

Primary operator check:

- run the reconciliation smoke test

Additional SQL reference:

SELECT SUM(available) FROM user_balances;
SELECT SUM(locked) FROM user_balances;
SELECT SUM(balance)::numeric(20,8) FROM users;
SELECT SUM(ledger_available) FROM v_user_finance_snapshot;
SELECT SUM(ledger_locked) FROM v_user_finance_snapshot;

Snapshot drift reference:

SELECT *
FROM v_user_finance_snapshot
WHERE delta_available <> 0 OR delta_locked <> 0;

---

## Git Workflow

Standard cycle:

git add <files>
git commit -m "<message>"
git push

All changes verified locally before commit.

---

## File Encoding Rules

UTF-8
No BOM
LF line endings

Use helper:

Write-FileNoBomLf

---

## state\STATE.md
# SLH_PROJECT_V2 - STATE ANCHOR

## Project Root
D:\SLH_PROJECT_V2

## Repository
https://github.com/osifeu-prog/SLH_PROJECT_V2.git

Main branch: main

---

## Current Verified Status

Withdrawal hardening patch is complete and verified.

Canonical runtime status:

- ledger-backed finance architecture is active
- ledger reconciliation is clean
- withdrawal happy path works end-to-end
- withdrawal failure/release path works end-to-end
- canonical withdrawal handler is `app/handlers/withdrawals.py`
- `worker.py` includes only `withdrawals_router` for withdrawal flows
- service-level wallet validation exists in `app/services/withdrawals.py`
- doctor script exists at `ops/doctor.ps1`
- DB patch file exists at `ops/sql/patch_withdraw_audit_naming.sql`

Latest verified commit:

- `1e5934e` - `Unify withdrawal audit naming and add wallet validation`

Important nuance:

- runtime code is canonical
- new withdrawal flows emit canonical `finance.withdraw.*` events
- historical legacy audit rows still exist in `audit_log` from older runs
- historical rows are not a blocker

---

## Current Architecture Snapshot

Telegram bot worker:
- `worker.py`

Routers loaded:
- `claim_router`
- `tasks_router`
- `invite_router`
- `withdrawals_router`
- `ton_admin_router`
- `task_verifications_router`

Legacy withdrawal router removed from runtime path:
- `app/handlers/withdraw.py`

Canonical withdrawal handler:
- `app/handlers/withdrawals.py`

---

## Finance / Ledger System

Active tables:

- `users`
- `user_balances`
- `ledger_accounts`
- `ledger_entries`
- `withdrawals`
- `withdrawal_reservations`
- `audit_log`

Verified invariants:

- `user_balances.available == users.balance == ledger_user_available`
- `user_balances.locked == ledger_user_locked`

Snapshot drift expectation:

- `v_user_finance_snapshot` must return zero drift rows

Latest verified doctor result:

- postgres connection OK
- ledger reconciliation OK
- no finance snapshot drift
- withdrawal diagnostics query OK
- audit naming diagnostics query OK
- overall status: `DOCTOR_OK`

---

## Withdrawal Flow Status

Verified success path:

- `create_withdrawal`
- `approve_withdrawal`
- `mark_withdraw_sent`
- reservation status becomes `consumed`

Verified failure / release path:

- `create_withdrawal`
- `approve_withdrawal`
- failure/reject path releases reservation
- reservation status becomes `released`

Validated implementation facts:

- runtime handler is `app/handlers/withdrawals.py`
- service validation normalizes wallet input to one line
- service validation rejects invalid wallet format before DB write
- creation audit event uses canonical `finance.withdraw.created`
- historical audit rows may still contain legacy names from older runs

---

## E2E Verification Assets

Verified test scripts:

- `ops/run_withdraw_e2e_test.py`
- `ops/run_withdraw_fail_e2e_test.py`

Operational diagnostics:

- `ops/doctor.ps1`
- `ops/sql/patch_withdraw_audit_naming.sql`

---

## Next Target Order

Preferred next implementation target order:

1. reconciliation smoke test
2. admin monitoring improvements
3. withdrawal rate limiting

Current recommendation:

- do `reconciliation smoke test` next

Reason:

- it locks in the verified ledger invariants with a repeatable command-line check
- it reduces regression risk before adding more operator features
- it strengthens the hardening phase without changing runtime behavior first

---

## Development Rules

All file writes must be:

- UTF-8 without BOM
- LF endings only

Execution mode:

- PowerShell commands only
- verify after each patch before moving on
- no drift from current repo state

---

## Resume Prompt

Load project state from `state/STATE.md`.
Use `state/ARCHITECTURE.md`, `state/RUNBOOK.md`, and `state/ROADMAP.md` as context.

Continue SLH_PROJECT_V2 after completing the withdrawal hardening patch.

Current verified status:
- ledger-backed finance architecture is active and reconciled
- withdrawal happy path works end-to-end
- withdrawal failure/release path works end-to-end
- canonical withdrawal handler is app/handlers/withdrawals.py
- worker.py uses only withdrawals_router
- service-level wallet validation exists in app/services/withdrawals.py
- doctor script exists at ops/doctor.ps1
- DB patch file exists at ops/sql/patch_withdraw_audit_naming.sql
- latest verified commit is 1e5934e
- runtime code is canonical
- historical legacy audit rows are not a blocker

Next target preference:
1. reconciliation smoke test
2. admin monitoring improvements
3. withdrawal rate limiting

Lead step by step with PowerShell only and verify every patch before moving on.L a s t   s u c c e s s f u l   d e p l o y :   V 5 . 3   -   R o u t e r   &   I 1 8 n   f i x .   O M N I - W A T C H D O G   A c t i v e .  
 