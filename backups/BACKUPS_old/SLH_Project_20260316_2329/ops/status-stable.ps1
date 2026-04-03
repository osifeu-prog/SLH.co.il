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

function Show-OnePid([string]$Label, [string]$Path) {
  $pidNum = Read-PidFile $Path
  if ($null -eq $pidNum) {
    Write-Host "$Label => MISSING/EMPTY" -ForegroundColor DarkYellow
    return
  }

  $meta = Get-ProcMeta -ProcId $pidNum
  if (-not $meta) {
    Write-Host "$Label => $pidNum (not running)" -ForegroundColor Yellow
    return
  }

  Write-Host "$Label => $pidNum" -ForegroundColor Green
  Write-Host "  exe: $([string]$meta.ExecutablePath)"
  Write-Host "  cmd: $([string]$meta.CommandLine)"
  Write-Host "  parent: $([string]$meta.ParentProcessId)"
}

function Get-ProjectPython {
  Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
      $_.Name -match '^python(\.exe)?$' -and
      $_.CommandLine -like "*D:\SLH_PROJECT_V2*"
    } |
    Sort-Object ProcessId
}

$pidDir = Join-Path $ROOT "runtime\pids"

Info "`n=== PID FILES ==="
Show-OnePid "webhook.supervisor.pid" (Join-Path $pidDir "webhook.supervisor.pid")
Show-OnePid "webhook.wrapper.pid"    (Join-Path $pidDir "webhook.wrapper.pid")
Show-OnePid "worker.supervisor.pid"  (Join-Path $pidDir "worker.supervisor.pid")
Show-OnePid "worker.wrapper.pid"     (Join-Path $pidDir "worker.wrapper.pid")

Info "`n=== PROJECT PYTHON ==="
$allPy = Get-ProjectPython
if (-not $allPy) {
  Warn "No project python processes found"
} else {
  foreach ($p in $allPy) {
    Write-Host ("PID {0} -> {1}" -f $p.ProcessId, $p.ExecutablePath) -ForegroundColor Green
    Write-Host ("  Parent: {0}" -f $p.ParentProcessId)
    Write-Host ("  CMD: {0}" -f $p.CommandLine)
  }
}

Info "`n=== PORTS ==="
foreach ($port in 8080, 5432, 6380) {
  $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  if ($listeners) {
    $owners = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
    Write-Host "Port $port LISTEN => PIDs: $($owners -join ', ')" -ForegroundColor Green
  } else {
    Warn "Port $port not listening"
  }
}

Info "`n=== LOCAL HEALTH ==="
try {
  $h = Invoke-RestMethod "http://127.0.0.1:8080/health" -TimeoutSec 5
  $json = $h | ConvertTo-Json -Depth 8
  Good $json
} catch {
  Warn $_.Exception.Message
}

Info "`n=== REDIS STREAM ==="
try {
  $type = docker exec slh_redis redis-cli TYPE slh:updates
  Write-Host ("slh:updates TYPE = {0}" -f (($type | Out-String).Trim())) -ForegroundColor Green
} catch {
  Warn "redis TYPE check failed: $($_.Exception.Message)"
}

Info "`n=== .ENV WEBHOOK_URL ==="
$envFile = Join-Path $ROOT ".env"
if (Test-Path $envFile) {
  $envText = Get-Content $envFile -Raw
  if ($envText -match '(?m)^\s*WEBHOOK_URL\s*=\s*(.+?)\s*$') {
    Write-Host ("WEBHOOK_URL = {0}" -f $matches[1].Trim()) -ForegroundColor Green
  } else {
    Warn "WEBHOOK_URL not found in .env"
  }
} else {
  Warn ".env file missing"
}

Info "`n=== LOG FILES ==="
$logDir = Join-Path $ROOT "runtime\logs"
if (Test-Path $logDir) {
  Get-ChildItem $logDir -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 8 |
    ForEach-Object {
      Write-Host ("{0} | {1} bytes | {2}" -f $_.Name, $_.Length, $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")) -ForegroundColor Gray
    }
} else {
  Warn "runtime\logs missing"
}