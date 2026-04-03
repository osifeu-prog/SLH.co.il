param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Stop-ByPidFile([string]$PidFile) {
    if (Test-Path $PidFile) {
        $raw = Get-Content $PidFile -Raw
        $pidText = ($raw | Out-String).Trim()
        if ($pidText -match '^\d+$') {
            $targetPid = [int]$pidText
            try {
                Stop-Process -Id $targetPid -Force -ErrorAction Stop
                Write-Host "Stopped PID $targetPid" -ForegroundColor Yellow
            } catch {
            }
        }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    }
}

$runDir = Join-Path (Get-Location) "run"

Stop-ByPidFile (Join-Path $runDir "worker.pid")
Stop-ByPidFile (Join-Path $runDir "webhook.pid")

docker compose -f .\docker-compose.redis.yml down | Out-Null

Write-Host "E2E clean stop complete." -ForegroundColor Green