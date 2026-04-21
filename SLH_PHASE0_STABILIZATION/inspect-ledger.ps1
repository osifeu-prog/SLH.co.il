$ErrorActionPreference = "Continue"

"=== LEDGER LOCAL INSPECTION ==="
"Time: $(Get-Date -Format s)"
""

"---- docker ps / status ----"
docker ps -a --filter "name=slh-ledger"
""

"---- restart state ----"
docker inspect slh-ledger --format "{{.State.Status}} | ExitCode={{.State.ExitCode}} | RestartCount={{.RestartCount}}"
""

"---- selected env ----"
docker inspect slh-ledger --format "{{range .Config.Env}}{{println .}}{{end}}" | findstr /i "TOKEN KEY SECRET ADMIN JWT DATABASE REDIS BOT_"
""

"---- last logs ----"
docker logs --tail 120 slh-ledger
""

"---- quick diagnosis ----"
"Expected issue:"
"- app log shows TOKEN=None"
"- container env shows BOT_TOKEN exists"
"- likely fix is to align TOKEN and BOT_TOKEN in compose/env or patch code to read BOT_TOKEN"
