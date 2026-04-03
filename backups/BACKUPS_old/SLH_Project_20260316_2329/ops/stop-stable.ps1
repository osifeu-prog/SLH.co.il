$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT

function Info([string]$m) { Write-Host $m -ForegroundColor Cyan }
function Good([string]$m) { Write-Host $m -ForegroundColor Green }
function Warn([string]$m) { Write-Host $m -ForegroundColor Yellow }

function Get-ProcMeta([int]$ProcId) {
  Get-CimInstance Win32_Process -Filter "ProcessId = $ProcId" -ErrorAction SilentlyContinue
}

function Read-PidFile([string]$Path) {
  if (-not (Test-Path $Path)) { return $null }
  $raw = (Get-Content $Path -Raw).Trim()
  if (-not $raw) { return $null }
  $pidNum = 0
  if ([int]::TryParse($raw, [ref]$pidNum)) { return $pidNum }
  return $null
}

function Stop-IfRunning([int]$ProcId, [string]$Label) {
  $meta = Get-ProcMeta -ProcId $ProcId
  if (-not $meta) {
    Warn "$Label => PID $ProcId not running"
    return
  }

  try {
    Stop-Process -Id $ProcId -Force -ErrorAction Stop
    Good "$Label => stopped PID $ProcId"
  } catch {
    Warn "$Label => failed stopping PID $ProcId : $($_.Exception.Message)"
  }
}

function Stop-ManagedPair([string]$Name) {
  $pidDir = Join-Path $ROOT "runtime\pids"
  $actualPath  = Join-Path $pidDir "$Name.supervisor.pid"
  $wrapperPath = Join-Path $pidDir "$Name.wrapper.pid"

  $actualPid  = Read-PidFile $actualPath
  $wrapperPid = Read-PidFile $wrapperPath

  if ($null -ne $actualPid) {
    Stop-IfRunning -ProcId $actualPid -Label "$Name.actual"
  } else {
    Warn "$Name.actual => pidfile missing/empty"
  }

  Start-Sleep -Milliseconds 800

  if ($null -ne $wrapperPid) {
    if ($wrapperPid -ne $actualPid) {
      Stop-IfRunning -ProcId $wrapperPid -Label "$Name.wrapper"
    }
  } else {
    Warn "$Name.wrapper => pidfile missing/empty"
  }

  Remove-Item $actualPath  -Force -ErrorAction SilentlyContinue
  Remove-Item $wrapperPath -Force -ErrorAction SilentlyContinue
}

Info "`n=== STOP FROM PID FILES ==="
Stop-ManagedPair "webhook"
Stop-ManagedPair "worker"

Start-Sleep -Seconds 2

Info "`n=== CLEAN LEFTOVER PROJECT PYTHON ==="
$leftovers = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object {
    $_.Name -match '^python(\.exe)?$' -and
    $_.CommandLine -like "*D:\SLH_PROJECT_V2*"
  }

if (-not $leftovers) {
  Good "no leftover project python processes"
} else {
  foreach ($p in $leftovers) {
    try {
      Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
      Good "stopped leftover PID $($p.ProcessId)"
    } catch {
      Warn "failed stopping leftover PID $($p.ProcessId): $($_.Exception.Message)"
    }
  }
}

Info "`n=== FINAL PID FILE CLEANUP ==="
$pidDir = Join-Path $ROOT "runtime\pids"
if (Test-Path $pidDir) {
  Get-ChildItem $pidDir -Filter "*.pid" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    Write-Host "removed $($_.Name)" -ForegroundColor DarkYellow
  }
}

Good "`nstop-stable completed"