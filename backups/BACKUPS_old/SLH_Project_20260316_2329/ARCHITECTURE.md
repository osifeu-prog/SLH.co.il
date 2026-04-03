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