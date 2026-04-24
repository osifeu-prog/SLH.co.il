param(
    [ValidateSet("startall","up","stop","restart","status","logs","health","build","doctor")]
    [string]$Action = "status",

    [string]$Target = "",

    [switch]$Follow
)

$ErrorActionPreference = "Stop"
$Root = "D:\SLH_ECOSYSTEM"
Set-Location $Root

function Show-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 64) -ForegroundColor DarkCyan
    Write-Host ("  " + $Title) -ForegroundColor Cyan
    Write-Host ("=" * 64) -ForegroundColor DarkCyan
}

function Run-Step {
    param([scriptblock]$Block)
    & $Block
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

switch ($Action) {
    "startall" {
        Show-Section "SLH START ALL"
        Run-Step { & "$Root\slh-start.ps1" }
        break
    }

    "up" {
        if ([string]::IsNullOrWhiteSpace($Target)) { throw "Usage: slh-up <compose-service>" }
        Show-Section "SLH UP [$Target]"
        Run-Step { docker compose up -d $Target }
        break
    }

    "build" {
        if ([string]::IsNullOrWhiteSpace($Target)) { throw "Usage: slh-build <compose-service>" }
        Show-Section "SLH BUILD [$Target]"
        Run-Step { docker compose build $Target }
        break
    }

    "stop" {
        if ([string]::IsNullOrWhiteSpace($Target)) { throw "Usage: slh-stop <container-name>" }
        Show-Section "SLH STOP [$Target]"
        Run-Step { docker stop $Target }
        break
    }

    "restart" {
        if ([string]::IsNullOrWhiteSpace($Target)) { throw "Usage: slh-restart <container-name>" }
        Show-Section "SLH RESTART [$Target]"
        Run-Step { docker restart $Target }
        break
    }

    "status" {
        Show-Section "SLH STATUS"
        docker ps --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}"
        break
    }

    "logs" {
        if ([string]::IsNullOrWhiteSpace($Target)) { throw "Usage: slh-logs <container-name> [-Follow]" }
        Show-Section "SLH LOGS [$Target]"
        if ($Follow) {
            docker logs -f --tail 120 $Target
        } else {
            docker logs --tail 120 $Target
        }
        break
    }

    "health" {
        Show-Section "SLH HEALTH"

        Write-Host "[Docker]" -ForegroundColor Yellow
        docker ps --format "table {{.Names}}`t{{.Status}}"

        Write-Host ""
        Write-Host "[Postgres]" -ForegroundColor Yellow
        docker exec slh-postgres pg_isready

        Write-Host ""
        Write-Host "[Redis]" -ForegroundColor Yellow
        docker exec slh-redis redis-cli ping

        Write-Host ""
        Write-Host "[Local API 8080 /api/health]" -ForegroundColor Yellow
        try {
            $r = Invoke-RestMethod "http://127.0.0.1:8080/api/health" -TimeoutSec 10
            $r | ConvertTo-Json -Depth 5
        } catch {
            Write-Warning $_.Exception.Message
        }

        Write-Host ""
        Write-Host "[Ledger recent errors]" -ForegroundColor Yellow
        $ledger = docker logs --since 2m slh-ledger 2>&1 | Select-String -Pattern "UndefinedTableError|ledger_listener loop error|shared_db_core unavailable"
        if ($ledger) { $ledger | ForEach-Object { $_.Line } } else { Write-Host "OK" -ForegroundColor Green }

        Write-Host ""
        Write-Host "[Guardian recent errors]" -ForegroundColor Yellow
        $guardian = docker logs --since 2m slh-guardian-bot 2>&1 | Select-String -Pattern "NetworkError|RemoteProtocolError|GLOBAL_ERROR|TypeError"
        if ($guardian) { $guardian | ForEach-Object { $_.Line } } else { Write-Host "OK" -ForegroundColor Green }

        break
    }

    "doctor" {
        Show-Section "SLH DOCTOR"

        Write-Host "[Profile mapping]" -ForegroundColor Yellow
        Get-Command slh-start | Format-List Name,Definition

        Write-Host ""
        Write-Host "[Docker]" -ForegroundColor Yellow
        docker ps --format "table {{.Names}}`t{{.Status}}"

        Write-Host ""
        Write-Host "[Ledger import]" -ForegroundColor Yellow
        docker exec slh-ledger python -c "import importlib.util as u; print(u.find_spec('shared_db_core'))"

        Write-Host ""
        Write-Host "[Event log table]" -ForegroundColor Yellow
        docker exec slh-postgres psql -U postgres -d slh_main -c "SELECT COUNT(*) FROM event_log;"

        break
    }
}