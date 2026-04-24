param(
    [string]$Target = "",
    [switch]$SkipBuild
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

function Require-Target {
    if ([string]::IsNullOrWhiteSpace($Target)) {
        throw "Usage: .\\slh-release.ps1 -Target <compose-service> [-SkipBuild]"
    }
}

function Invoke-Checked {
    param([scriptblock]$Block)
    & $Block
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

function Get-ContainerName {
    param([string]$Service)
    try {
        $name = docker compose ps -q $Service
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($name)) {
            $resolved = docker inspect --format '{{.Name}}' $name 2>$null
            if ($LASTEXITCODE -eq 0 -and $resolved) {
                return $resolved.TrimStart('/')
            }
        }
    } catch {}

    switch ($Service) {
        "ledger-bot" { return "slh-ledger" }
        "guardian-bot" { return "slh-guardian-bot" }
        "admin-bot" { return "slh-admin" }
        "factory-bot" { return "slh-factory" }
        default { return $Service }
    }
}

Require-Target
$Container = Get-ContainerName -Service $Target

Show-Section "SLH RELEASE [$Target]"
Write-Host "Service   : $Target" -ForegroundColor Yellow
Write-Host "Container : $Container" -ForegroundColor Yellow

if (-not $SkipBuild) {
    Show-Section "BUILD"
    Invoke-Checked { docker compose build $Target }
}

Show-Section "DEPLOY"
Invoke-Checked { docker compose up -d $Target }

Start-Sleep -Seconds 8

Show-Section "HEALTH SNAPSHOT"
docker ps --format "table {{.Names}}`t{{.Status}}" | findstr /I $Container
Write-Host ""
docker exec slh-postgres pg_isready
Write-Host ""
docker exec slh-redis redis-cli ping

Show-Section "RECENT LOGS [$Container]"
docker logs --tail 80 $Container

Show-Section "ERROR SCAN [$Container]"
$err = docker logs --since 3m $Container 2>&1 | Select-String -Pattern "Traceback|ERROR|Exception|UndefinedTableError|ModuleNotFoundError|RemoteProtocolError|NetworkError"
if ($err) {
    $err | ForEach-Object { $_.Line }
} else {
    Write-Host "OK: no critical errors in last 3 minutes." -ForegroundColor Green
}
