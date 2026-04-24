param(
    [string]$Target = "ledger-bot"
)

$ErrorActionPreference = "Stop"
Set-Location "D:\SLH_ECOSYSTEM"

Write-Host ""
Write-Host "================================================================" -ForegroundColor DarkCyan
Write-Host "  SLH PREFLIGHT [$Target]" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor DarkCyan

Write-Host "`n[1] Docker status" -ForegroundColor Yellow
docker ps --format "table {{.Names}}`t{{.Status}}"

Write-Host "`n[2] Postgres" -ForegroundColor Yellow
docker exec slh-postgres pg_isready

Write-Host "`n[3] Redis" -ForegroundColor Yellow
docker exec slh-redis redis-cli ping

Write-Host "`n[4] Ledger import check" -ForegroundColor Yellow
docker exec slh-ledger python -c "import importlib.util as u; print(u.find_spec('shared_db_core'))"

Write-Host "`n[5] event_log table" -ForegroundColor Yellow
docker exec slh-postgres psql -U postgres -d slh_main -c "SELECT COUNT(*) FROM event_log;"

Write-Host "`n[6] Recent ledger errors" -ForegroundColor Yellow
$ledger = docker logs --since 3m slh-ledger 2>&1 | Select-String -Pattern "UndefinedTableError|ledger_listener loop error|shared_db_core unavailable"
if ($ledger) { $ledger | ForEach-Object { $_.Line } } else { Write-Host "OK" -ForegroundColor Green }

Write-Host "`n[7] Recent guardian errors" -ForegroundColor Yellow
$guardian = docker logs --since 3m slh-guardian-bot 2>&1 | Select-String -Pattern "NetworkError|RemoteProtocolError|GLOBAL_ERROR|TypeError"
if ($guardian) { $guardian | ForEach-Object { $_.Line } } else { Write-Host "OK" -ForegroundColor Green }

Write-Host "`n[8] Local API /api/health" -ForegroundColor Yellow
try {
    $r = Invoke-RestMethod "http://127.0.0.1:8080/api/health" -TimeoutSec 10
    $r | ConvertTo-Json -Depth 5
} catch {
    Write-Warning $_.Exception.Message
}

Write-Host "`nPreflight complete." -ForegroundColor Green
