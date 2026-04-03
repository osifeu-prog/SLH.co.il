$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT

function Info([string]$m) { Write-Host $m -ForegroundColor Cyan }
function Good([string]$m) { Write-Host ("OK   " + $m) -ForegroundColor Green }
function Warn([string]$m) { Write-Host ("WARN " + $m) -ForegroundColor Yellow }
function Bad([string]$m)  { Write-Host ("FAIL " + $m) -ForegroundColor Red }

function Read-EnvValue([string]$Name) {
  $envFile = Join-Path $ROOT ".env"
  if (-not (Test-Path $envFile)) { return $null }
  $txt = Get-Content $envFile -Raw
  $pat = '(?m)^\s*' + [Regex]::Escape($Name) + '\s*=\s*(.*?)\s*$'
  if ($txt -match $pat) { return $matches[1] }
  return $null
}

function Read-PidFile([string]$Path) {
  if (-not (Test-Path $Path)) { return $null }
  $raw = (Get-Content $Path -Raw).Trim()
  if (-not $raw) { return $null }
  $n = 0
  if ([int]::TryParse($raw, [ref]$n)) { return $n }
  return $null
}

function Get-ProcMeta([int]$ProcId) {
  Get-CimInstance Win32_Process -Filter "ProcessId = $ProcId" -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "SLH PROJECT V2 :: DOCTOR" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$pythonExe = Join-Path $ROOT "venv\Scripts\python.exe"
if (Test-Path $pythonExe) { Good "venv python: $pythonExe" } else { Bad "venv python missing: $pythonExe" }

$envPath = Join-Path $ROOT ".env"
if (Test-Path $envPath) { Good ".env found" } else { Bad ".env missing" }

foreach ($name in "BOT_TOKEN","WEBHOOK_SECRET","WEBHOOK_URL","REDIS_URL","DATABASE_URL") {
  $v = Read-EnvValue $name
  if ([string]::IsNullOrWhiteSpace($v)) { Warn "$name missing in .env" } else { Good "$name present" }
}

foreach ($file in "webhook_server.py","worker.py","slh.ps1","ops\start-stable.ps1","ops\stop-stable.ps1","ops\status-stable.ps1") {
  $p = Join-Path $ROOT $file
  if (Test-Path $p) { Good "$file found" } else { Bad "$file missing" }
}

Write-Host ""
Info "PID FILES"
$pidDir = Join-Path $ROOT "runtime\pids"
foreach ($name in "webhook.supervisor.pid","webhook.wrapper.pid","worker.supervisor.pid","worker.wrapper.pid") {
  $pf = Join-Path $pidDir $name
  $pidNum = Read-PidFile $pf
  if ($null -eq $pidNum) {
    Warn "$name missing/empty"
    continue
  }
  $meta = Get-ProcMeta $pidNum
  if ($meta) {
    Good "$name => PID $pidNum alive"
  } else {
    Warn "$name => PID $pidNum not running"
  }
}

Write-Host ""
Info "PROJECT PYTHON"
$py = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object {
    $_.Name -match '^python(\.exe)?$' -and
    $_.CommandLine -like "*D:\SLH_PROJECT_V2*"
  } |
  Sort-Object ProcessId

if ($py) {
  foreach ($p in $py) {
    Good ("PID {0} :: {1}" -f $p.ProcessId, $p.CommandLine)
  }
} else {
  Warn "No project python processes found"
}

Write-Host ""
Info "PORTS"
foreach ($port in 8080, 5432, 6380) {
  $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  if ($listeners) {
    $owners = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
    Good "Port $port LISTEN => $($owners -join ', ')"
  } else {
    Warn "Port $port not listening"
  }
}

Write-Host ""
Info "LOCAL HEALTH"
try {
  $h = Invoke-RestMethod "http://127.0.0.1:8080/health" -TimeoutSec 5
  if ($h.ok -eq $true) {
    Good ("health ok, mode=" + $h.mode)
  } else {
    Warn "health returned but ok != true"
  }
} catch {
  Bad $_.Exception.Message
}

Write-Host ""
Info "LOG FILES"
$logDir = Join-Path $ROOT "runtime\logs"
if (Test-Path $logDir) {
  $logs = Get-ChildItem $logDir -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 6
  if ($logs) {
    foreach ($f in $logs) {
      Good ("{0} | {1} bytes | {2}" -f $f.Name, $f.Length, $f.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"))
    }
  } else {
    Warn "no log files found"
  }
} else {
  Warn "runtime\logs missing"
}