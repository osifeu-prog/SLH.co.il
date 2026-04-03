param(
    [switch]$FailOnMissing
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Test-DockerContainer([string]$Name) {
    $id = docker ps -q --filter "name=^${Name}$"
    return -not [string]::IsNullOrWhiteSpace($id)
}

function Invoke-DbSqlText([string]$Sql) {
    $Sql | docker exec -i slhb_postgres psql -U slh_user -d slh_database -At 2>&1
}

Write-Host "`n=== DB ALERT :: PRECHECK ===" -ForegroundColor Cyan

if (-not (Test-DockerContainer "slhb_postgres")) {
    Write-Host "ALERT: slhb_postgres is not running." -ForegroundColor Red
    if ($FailOnMissing) { exit 2 } else { return }
}

$required = @(
    "public.users",
    "public.system_settings",
    "public.products",
    "public.product_groups",
    "public.purchase_orders"
)

Write-Host "`n=== DB ALERT :: TABLES ===" -ForegroundColor Cyan
$tablesText = Invoke-DbSqlText @"
SELECT table_schema || '.' || table_name
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog','information_schema')
ORDER BY table_schema, table_name;
"@

$tables = @()
if ($tablesText) {
    $tables = ($tablesText -split "`n" | ForEach-Object { $_.Trim() }) | Where-Object {
        $_ -and $_ -notmatch '^(ERROR|psql:)'
    }
}

if ($tables.Count -eq 0) {
    Write-Host "ALERT: no app tables detected." -ForegroundColor Red
} else {
    $tables | ForEach-Object { Write-Host $_ }
}

$missing = @()
foreach ($name in $required) {
    if ($tables -notcontains $name) {
        $missing += $name
    }
}

Write-Host "`n=== DB ALERT :: REQUIRED CHECK ===" -ForegroundColor Cyan
if ($missing.Count -gt 0) {
    Write-Host "ALERT: missing required tables:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }

    if ($tables -notcontains "public.users") {
        Write-Host "ROOT CAUSE HINT: commerce foundation depends on public.users." -ForegroundColor Yellow
    }
} else {
    Write-Host "Required tables exist." -ForegroundColor Green
}

Write-Host "`n=== DB ALERT :: WORKER LOG CHECK ===" -ForegroundColor Cyan
$workerLog = ".\logs\worker.console.log"
if (Test-Path $workerLog) {
    $txt = Get-Content $workerLog -Raw -ErrorAction SilentlyContinue

    if ($txt -match "InvalidPasswordError|password authentication failed") {
        Write-Host "ALERT: DB password/auth failure detected in worker log." -ForegroundColor Red
    }

    if ($txt -notmatch "worker started") {
        Write-Host "ALERT: worker readiness text not found." -ForegroundColor Yellow
    } else {
        Write-Host "Worker readiness text found." -ForegroundColor Green
    }
} else {
    Write-Host "Worker log not found yet." -ForegroundColor Yellow
}

Write-Host "`n=== DB ALERT :: HEALTH ===" -ForegroundColor Cyan
try {
    $h = Invoke-RestMethod "http://127.0.0.1:8080/healthz" -TimeoutSec 3
    $h | Format-Table -AutoSize
} catch {
    Write-Host "Webhook health not reachable." -ForegroundColor Yellow
}

if ($missing.Count -gt 0 -and $FailOnMissing) {
    exit 3
}