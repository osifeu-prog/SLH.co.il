param(
    [switch]$IncludeRailway,
    [switch]$IncludeDb
)

$ErrorActionPreference = "Stop"
$script:HasIssue = $false

function Warn-Step([string]$Text){
    Write-Host $Text -ForegroundColor Yellow
    $script:HasIssue = $true
}

function Get-EnvValue([string]$Name, [string]$EnvText){
    $m = [regex]::Match($EnvText, "(?m)^$([regex]::Escape($Name))=(.*)$")
    if (-not $m.Success) { return $null }
    return $m.Groups[1].Value.Trim().Trim('"')
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " SLH PROJECT MORNING CHECK" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Welcome back Osif." -ForegroundColor Green
Write-Host "Build carefully. Verify before changing production." -ForegroundColor DarkCyan
Write-Host ""

Set-Location $PSScriptRoot\..

Write-Host "Project: $(Get-Location)"
Write-Host ""

Write-Host "---- GIT STATUS ----" -ForegroundColor Cyan
git fetch origin | Out-Null

$head   = (git rev-parse HEAD).Trim()
$origin = (git rev-parse origin/main).Trim()

Write-Host "HEAD:        $head"
Write-Host "origin/main: $origin"

if ($head -ne $origin) {
    Warn-Step "WARNING: local HEAD differs from origin/main"
} else {
    Write-Host "Git sync OK" -ForegroundColor Green
}

Write-Host ""
Write-Host "Recent commits:" -ForegroundColor Cyan
git log --oneline -n 5

Write-Host ""
Write-Host "Local changes:" -ForegroundColor Cyan
git status --short

Write-Host ""
Write-Host "---- PYTHON CHECK ----" -ForegroundColor Cyan
if (Test-Path ".\venv\Scripts\python.exe") {
    .\venv\Scripts\python.exe --version
    .\venv\Scripts\python.exe -m py_compile .\app\handlers\ton_admin.py
    .\venv\Scripts\python.exe -m py_compile .\app\services\purchases.py
    .\venv\Scripts\python.exe -m py_compile .\app\services\purchases_admin.py
    Write-Host "Python compile OK" -ForegroundColor Green
} else {
    Warn-Step "WARNING: venv python missing"
}

if ($IncludeRailway) {
    Write-Host ""
    Write-Host "---- RAILWAY ----" -ForegroundColor Cyan
    railway status
}

if ($IncludeDb) {
    Write-Host ""
    Write-Host "---- DB CHECK ----" -ForegroundColor Cyan

    if (-not (Test-Path ".\.env")) {
        Warn-Step "WARNING: .env file missing"
    } else {
        $envText = Get-Content .\.env -Raw

        $dbHost = Get-EnvValue "DB_HOST" $envText
        $dbPort = Get-EnvValue "DB_PORT" $envText
        $dbName = Get-EnvValue "DB_NAME" $envText
        $dbUser = Get-EnvValue "DB_USER" $envText
        $dbPass = Get-EnvValue "DB_PASS" $envText

        if (-not $dbPort) { $dbPort = "5432" }

        if (-not $dbHost -or -not $dbName -or -not $dbUser) {
            Warn-Step "WARNING: missing DB settings in .env"
        } else {
            $env:PGHOST = $dbHost
            $env:PGPORT = $dbPort
            $env:PGDATABASE = $dbName
            $env:PGUSER = $dbUser
            $env:PGPASSWORD = $dbPass

            try {
                psql -v ON_ERROR_STOP=1 -c "select current_user,current_database();"
                psql -v ON_ERROR_STOP=1 -c "SELECT code, price_amount, price_currency FROM products WHERE code='FRIENDS_SUPPORT_ACCESS';"
                Write-Host "DB check OK" -ForegroundColor Green
            }
            catch {
                Warn-Step "WARNING: DB check failed"
                Write-Host $_.Exception.Message -ForegroundColor Yellow
            }
        }
    }
}

Write-Host ""
Write-Host "-----------------------------------------" -ForegroundColor Cyan
if ($script:HasIssue) {
    Write-Host " SYSTEM CHECK COMPLETED WITH WARNINGS" -ForegroundColor Yellow
} else {
    Write-Host " SYSTEM READY" -ForegroundColor Green
}
Write-Host "-----------------------------------------" -ForegroundColor Cyan
Write-Host ""