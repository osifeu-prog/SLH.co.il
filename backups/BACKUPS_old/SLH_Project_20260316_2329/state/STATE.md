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

Lead step by step with PowerShell only and verify every patch before moving on.