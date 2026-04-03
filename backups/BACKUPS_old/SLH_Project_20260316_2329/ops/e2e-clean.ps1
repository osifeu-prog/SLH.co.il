param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Ensure-Dir([string]$Path) {
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Kill-OldProcessByPidFile([string]$PidFile) {
    if (Test-Path $PidFile) {
        $raw = Get-Content $PidFile -Raw
        $pidText = ($raw | Out-String).Trim()
        if ($pidText -match '^\d+$') {
            $oldPid = [int]$pidText
            try {
                $p = Get-Process -Id $oldPid -ErrorAction Stop
                Stop-Process -Id $oldPid -Force -ErrorAction Stop
                Write-Host "Stopped old PID $oldPid from $PidFile" -ForegroundColor Yellow
            } catch {
            }
        }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    }
}

function Wait-HttpOk([string]$Url, [int]$TimeoutSec = 20) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    do {
        try {
            $r = Invoke-RestMethod $Url -TimeoutSec 3
            return $r
        } catch {
            Start-Sleep -Milliseconds 700
        }
    } while ((Get-Date) -lt $deadline)
    throw "Health check failed: $Url"
}

$root = Get-Location
$logDir = Join-Path $root "logs"
$runDir = Join-Path $root "run"
Ensure-Dir $logDir
Ensure-Dir $runDir

$workerOut = Join-Path $logDir "worker.console.log"
$workerErr = Join-Path $logDir "worker.error.log"
$webhookOut = Join-Path $logDir "webhook.console.log"
$webhookErr = Join-Path $logDir "webhook.error.log"

$workerPidFile = Join-Path $runDir "worker.pid"
$webhookPidFile = Join-Path $runDir "webhook.pid"

Kill-OldProcessByPidFile $workerPidFile
Kill-OldProcessByPidFile $webhookPidFile

Write-Host "`n=== ENSURE DOCKER SERVICES ===" -ForegroundColor Cyan
docker start slhb_postgres | Out-Null
docker compose -f .\docker-compose.redis.yml up -d | Out-Null

Write-Host "`n=== CHECK PORTS ===" -ForegroundColor Cyan
docker ps --filter "name=slhb_postgres" --format "table {{.Names}}`t{{.Ports}}`t{{.Status}}"
docker ps --filter "name=slh_redis" --format "table {{.Names}}`t{{.Ports}}`t{{.Status}}"

Write-Host "`n=== RESET LOGS ===" -ForegroundColor Cyan
"" | Set-Content $workerOut
"" | Set-Content $workerErr
"" | Set-Content $webhookOut
"" | Set-Content $webhookErr

Write-Host "`n=== START WORKER (HIDDEN) ===" -ForegroundColor Cyan
$worker = Start-Process -FilePath ".\venv\Scripts\python.exe" `
    -ArgumentList "worker.py" `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $workerOut `
    -RedirectStandardError $workerErr `
    -PassThru
$worker.Id | Set-Content $workerPidFile

Write-Host "`n=== START WEBHOOK (HIDDEN) ===" -ForegroundColor Cyan
$webhook = Start-Process -FilePath ".\venv\Scripts\python.exe" `
    -ArgumentList "webhook_server.py" `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $webhookOut `
    -RedirectStandardError $webhookErr `
    -PassThru
$webhook.Id | Set-Content $webhookPidFile

Write-Host "`n=== WAIT FOR HEALTH ===" -ForegroundColor Cyan
$health = Wait-HttpOk "http://127.0.0.1:8080/healthz" 25

Write-Host "`n=== E2E CLEAN STATUS ===" -ForegroundColor Green
$health | Format-Table -AutoSize

Write-Host "`nWorker PID:  $($worker.Id)"
Write-Host "Webhook PID: $($webhook.Id)"

Write-Host "`n=== LAST WORKER LOG ===" -ForegroundColor Cyan
Get-Content $workerOut -Tail 20 -ErrorAction SilentlyContinue

Write-Host "`n=== LAST WEBHOOK LOG ===" -ForegroundColor Cyan
Get-Content $webhookOut -Tail 20 -ErrorAction SilentlyContinue