# SLH_PROJECT_V2 :: PROJECT_BRIEF

Updated at: 2026-03-09 17:19:54

## Repository
- Root: D:\SLH_PROJECT_V2
- Remote: https://github.com/osifeu-prog/SLH_PROJECT_V2.git
- Branch: main
- Commit: 53acfca

## Current Runtime Shape
- Production Telegram webhook points to Railway
- Local stack exists for hardening and diagnostics
- Runtime flow: webhook -> redis -> worker -> postgres

## Verified System Direction
- Ledger-backed finance layer exists
- Withdrawal hardening is documented as verified
- Bot domain includes rewards, invites, tasks, profile, admin, withdrawals

## Local Health
{"ok":true,"mode":"webhook->redis->worker","release":"3f22873"}

## Local Python Processes

ProcessId CommandLine                                                                     
--------- -----------                                                                     
    27856 "D:\SLH_PROJECT_V2\venv\Scripts\python.exe" D:\SLH_PROJECT_V2\webhook_server.py 
    16876 "D:\SLH_PROJECT_V2\venv\Scripts\python.exe" D:\SLH_PROJECT_V2\worker.py

## Current Git Status
 M ops/doctor.ps1
 M ops/session-end.ps1
 M ops/session-start.ps1
 M slh.ps1
 M state/ANCHOR.md
 M worker.py
?? ops/morning-start.ps1
?? ops/restart-safe.ps1

## Working Protocol
- No guessing
- Always inspect code or runtime state before proposing changes
- First provide PowerShell commands to expose the needed data
- User runs the commands and returns the output
- Only after enough evidence exists, provide exact PowerShell patch commands
- Preserve UTF-8 without BOM and LF endings
- Prefer minimal patches and clean commit scope
- Target: safe path toward 100K registered users

## Primary State Sources
- state\PROJECT_SCAN.md
- state\ANCHOR.md
- state\STATE.md
- state\ARCHITECTURE.md
- state\ROADMAP.md
- state\RUNBOOK.md