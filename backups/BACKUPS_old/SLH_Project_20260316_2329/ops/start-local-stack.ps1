param(
    [switch]$NoTunnel
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$python = Join-Path (Get-Location) "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "venv python not found"
}

Write-Host ""
Write-Host "=== STEP 1: REDIS ===" -ForegroundColor Cyan
docker compose -f .\docker-compose.redis.yml up -d
Start-Sleep -Seconds 2
docker exec slh_redis redis-cli PING

Write-Host ""
Write-Host "=== STEP 2: WORKER WINDOW ===" -ForegroundColor Cyan
$workerCmd = @"
Set-Location '$(Get-Location)'
& '$python' -u '.\worker.py'
"@
Start-Process powershell.exe -ArgumentList "-NoExit","-ExecutionPolicy","Bypass","-Command",$workerCmd

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "=== STEP 3: WEBHOOK WINDOW ===" -ForegroundColor Cyan
$webhookCmd = @"
Set-Location '$(Get-Location)'
& '$python' -u '.\webhook_server.py'
"@
Start-Process powershell.exe -ArgumentList "-NoExit","-ExecutionPolicy","Bypass","-Command",$webhookCmd

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "=== STEP 4: HEALTH CHECK ===" -ForegroundColor Cyan
try {
    irm http://127.0.0.1:8080/healthz | Format-Table -AutoSize
} catch {
    Write-Host "healthz failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

if (-not $NoTunnel) {
    Write-Host ""
    Write-Host "=== STEP 5: TUNNEL WINDOW ===" -ForegroundColor Cyan
    $tunnelCmd = @"
Set-Location '$(Get-Location)'
cloudflared tunnel --url http://127.0.0.1:8080
"@
    Start-Process powershell.exe -ArgumentList "-NoExit","-ExecutionPolicy","Bypass","-Command",$tunnelCmd
    Write-Host "Tunnel window opened. Copy the trycloudflare URL and run:" -ForegroundColor Yellow
    Write-Host ".\ops\set-webhook.ps1 -BaseUrl 'https://YOUR-URL.trycloudflare.com'" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "START_LOCAL_STACK_OK" -ForegroundColor Green