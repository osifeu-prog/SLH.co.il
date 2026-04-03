param()
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "common.ps1")
Set-Location $ProjectRoot

Show-Section "STACK DOWN"

$state = Read-State
foreach($name in @("worker_pid","webhook_pid","tunnel_pid")) {
    $procId = $state.$name
    if ($procId) {
        try {
            Stop-Process -Id ([int]$procId) -Force -ErrorAction Stop
            Write-Host "$name stopped (PID=$procId)" -ForegroundColor Green
        } catch {
            Write-Host "$name already stopped or not found" -ForegroundColor Yellow
        }
        Remove-StateValue $name
    }
}

try {
    docker compose -f .\docker-compose.redis.yml down --remove-orphans
    Write-Host "redis stopped" -ForegroundColor Green
} catch {
    Write-Host "redis stop failed or already down" -ForegroundColor Yellow
}