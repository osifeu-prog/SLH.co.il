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