param(
  [switch]$SkipStart
)

$ErrorActionPreference = "Stop"

$ROOT = "D:\SLH_PROJECT_V2"
Set-Location $ROOT

function Info([string]$m)  { Write-Host $m -ForegroundColor Cyan }
function Good([string]$m)  { Write-Host $m -ForegroundColor Green }
function Warn([string]$m)  { Write-Host $m -ForegroundColor Yellow }
function Bad([string]$m)   { Write-Host $m -ForegroundColor Red }

function Step([string]$m) {
  Write-Host ""
  Write-Host "=== $m ===" -ForegroundColor Magenta
}

function Test-CommandExists([string]$cmd) {
  return $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Test-TcpPort([string]$HostName, [int]$Port) {
  try {
    $r = Test-NetConnection -ComputerName $HostName -Port $Port -WarningAction SilentlyContinue
    return [bool]$r.TcpTestSucceeded
  } catch {
    return $false
  }
}

$summary = [System.Collections.Generic.List[string]]::new()

Step "PROJECT ROOT"
if (-not (Test-Path $ROOT)) {
  Bad "Project root not found: $ROOT"
  exit 1
}
Good "Project root: $ROOT"

Step "CRITICAL FILES"
$requiredFiles = @(
  ".\slh.ps1",
  ".\webhook_server.py",
  ".\worker.py",
  ".\.env",
  ".\docker-compose.redis.yml"
)

$missing = @()
foreach ($f in $requiredFiles) {
  if (Test-Path $f) {
    Good "Found $f"
  } else {
    Warn "Missing $f"
    $missing += $f
  }
}
if ($missing.Count -gt 0) {
  $summary.Add("WARN: missing critical files: $($missing -join ', ')")
}

Step "VENV PYTHON"
$py = ".\venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  Bad "venv python missing: $py"
  exit 1
}
& $py --version
Good "venv python OK"

Step "PYTHON COMPILE CHECK"
$pyFiles = @(
  ".\main.py",
  ".\webhook_server.py",
  ".\worker.py"
)
foreach ($pf in $pyFiles) {
  if (Test-Path $pf) {
    & $py -m py_compile $pf
    Good "Compiled $pf"
  } else {
    Warn "Skipped missing $pf"
  }
}

Step "LOCAL PORT CHECK"
$port8080 = Test-TcpPort "127.0.0.1" 8080
$port6380 = Test-TcpPort "127.0.0.1" 6380
$port5432 = Test-TcpPort "127.0.0.1" 5432

if ($port8080) { Good "Port 8080 reachable" } else { Warn "Port 8080 not reachable yet" }
if ($port6380) { Good "Port 6380 reachable" } else { Warn "Port 6380 not reachable yet" }
if ($port5432) { Good "Port 5432 reachable" } else { Warn "Port 5432 not reachable yet" }

Step "POSTGRES CHECK"
if (Test-CommandExists "psql") {
  try {
    & psql -h 127.0.0.1 -p 5432 -U postgres -d slh_db -c "SELECT NOW();" | Out-Host
    Good "Postgres connection OK"
  } catch {
    Warn "Postgres check failed"
    $summary.Add("WARN: postgres connection failed")
  }
} else {
  Warn "psql not found in PATH; skipping SQL connectivity check"
  $summary.Add("WARN: psql missing from PATH")
}

Step "REDIS CHECK"
try {
  if (Test-CommandExists "docker") {
    $redisContainer = docker ps --format "{{.Names}}" | Select-String -Pattern "redis" -SimpleMatch
    if ($redisContainer) {
      Good "Redis container appears to be running"
    } else {
      Warn "Redis container not detected by docker ps"
    }
  } else {
    Warn "docker not found in PATH; skipping docker redis check"
  }
} catch {
  Warn "Redis/docker check failed"
  $summary.Add("WARN: redis/docker check failed")
}

if (-not $SkipStart) {
  Step "START STACK"
  if (Test-Path ".\slh.ps1") {
    & powershell -ExecutionPolicy Bypass -File ".\slh.ps1" up
    Good "slh.ps1 up finished"
  } else {
    Bad "slh.ps1 not found"
    exit 1
  }
} else {
  Warn "SkipStart enabled; not starting stack"
}

Step "WAIT FOR SERVICES"
Start-Sleep -Seconds 5

Step "STATUS"
try {
  & powershell -ExecutionPolicy Bypass -File ".\slh.ps1" status
  Good "status command finished"
} catch {
  Warn "status command failed"
  $summary.Add("WARN: status command failed")
}

Step "HEALTH CHECK"
try {
  $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8080/health" -UseBasicParsing -TimeoutSec 10
  Good "Health endpoint returned HTTP $($resp.StatusCode)"
  $body = $resp.Content
  if ($body) {
    Write-Host $body
  }
} catch {
  Warn "Health endpoint check failed"
  $summary.Add("WARN: health endpoint failed")
}

Step "TELEGRAM QUICK MANUAL TEST PLAN"
Write-Host "1) /start" -ForegroundColor Gray
Write-Host "2) Profile" -ForegroundColor Gray
Write-Host "3) Balance" -ForegroundColor Gray
Write-Host "4) Health" -ForegroundColor Gray
Write-Host "5) Withdraw 1  (only if ready for withdrawal test)" -ForegroundColor Gray

Step "FINAL SUMMARY"
if ($summary.Count -eq 0) {
  Good "Morning startup completed cleanly"
} else {
  Warn "Morning startup completed with warnings:"
  foreach ($s in $summary) {
    Warn " - $s"
  }
}

Write-Host ""
Write-Host "DONE." -ForegroundColor Green