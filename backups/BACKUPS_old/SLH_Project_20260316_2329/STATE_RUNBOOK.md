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