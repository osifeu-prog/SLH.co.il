param()
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "common.ps1")
Set-Location $ProjectRoot

Show-Section "START REDIS"

if (-not (Test-DockerResponsive)) {
    Write-Host "Docker is not responding. Start Docker Desktop first." -ForegroundColor Red
    return
}

try {
    docker compose -f .\docker-compose.redis.yml up -d
    Start-Sleep -Seconds 2

    $psResult = Invoke-Docker -Arguments 'ps --filter "name=slh_redis"' -TimeoutMs 5000
    if ($psResult.StdOut) {
        Write-Host $psResult.StdOut
    }

    $pingResult = Invoke-Docker -Arguments 'exec slh_redis redis-cli PING' -TimeoutMs 5000
    if ((-not $pingResult.TimedOut) -and $pingResult.ExitCode -eq 0) {
        Write-Host $pingResult.StdOut
    } else {
        Write-Host "Redis ping failed" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Failed to start Redis: $($_.Exception.Message)" -ForegroundColor Red
}