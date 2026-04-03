# SLH_PROJECT_V2 :: STATE_CURRENT

## Current known-good ports
- DB: 127.0.0.1:55432
- Redis: 127.0.0.1:6380
- Webhook: http://127.0.0.1:8080

## Startup
- .\ops\e2e-clean.ps1

## Shutdown
- .\ops\e2e-stop.ps1

## Health
- Invoke-RestMethod http://127.0.0.1:8080/healthz

## Logs
- logs/worker.console.log
- logs/worker.error.log
- logs/webhook.console.log
- logs/webhook.error.log

## Rules
- Do not use TerminalCommandCenter for SLH_PROJECT_V2 E2E
- Do not use DB port 5432 for this project
- Use DB port 55432
- Use Redis port 6380

## Current confirmed status
- e2e-clean.ps1 starts successfully
- /healthz returns ok=true
- worker started successfully
- webhook started successfully

## Next goal
- Verify bot/store/purchase flow on clean local stack