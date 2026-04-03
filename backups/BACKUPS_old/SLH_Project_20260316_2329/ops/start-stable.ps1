$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT

function Info([string]$m) { Write-Host $m -ForegroundColor Cyan }
function Good([string]$m) { Write-Host $m -ForegroundColor Green }
function Warn([string]$m) { Write-Host $m -ForegroundColor Yellow }

function Find-ChildPython([int]$ParentId, [string]$ScriptPath) {
  $escaped = [Regex]::Escape($ScriptPath)
  Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
      $_.ParentProcessId -eq $ParentId -and
      $_.Name -match '^python(\.exe)?$' -and
      $_.CommandLine -match $escaped
    } |
    Sort-Object ProcessId |
    Select-Object -First 1
}

function Start-ManagedPython(
  [string]$Name,
  [string]$PythonExe,
  [string]$ScriptPath,
  [string]$WorkingDir,
  [string]$OutLog,
  [string]$ErrLog,
  [string]$PidDir
) {
  $proc = Start-Process `
    -FilePath $PythonExe `
    -ArgumentList @($ScriptPath) `
    -WorkingDirectory $WorkingDir `
    -RedirectStandardOutput $OutLog `
    -RedirectStandardError  $ErrLog `
    -PassThru

  $wrapperPid = $proc.Id
  Start-Sleep -Seconds 2

  $child = Find-ChildPython -ParentId $wrapperPid -ScriptPath $ScriptPath
  $actualPid = if ($child) { $child.ProcessId } else { $wrapperPid }

  Set-Content -Path (Join-Path $PidDir "$Name.supervisor.pid") -Value $actualPid -Encoding ascii
  Set-Content -Path (Join-Path $PidDir "$Name.wrapper.pid")    -Value $wrapperPid -Encoding ascii

  if ($child) {
    Good "$Name started => actual PID $actualPid | wrapper PID $wrapperPid"
  } else {
    Warn "$Name started => child not found, using wrapper PID $wrapperPid"
  }
}

$pythonExe = Join-Path $ROOT "venv\Scripts\python.exe"
$pidDir    = Join-Path $ROOT "runtime\pids"
$logDir    = Join-Path $ROOT "runtime\logs"

New-Item -ItemType Directory -Force -Path $pidDir | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

if (-not (Test-Path $pythonExe)) {
  throw "python not found: $pythonExe"
}

$webhookPy = Join-Path $ROOT "webhook_server.py"
$workerPy  = Join-Path $ROOT "worker.py"

if (-not (Test-Path $webhookPy)) { throw "missing file: $webhookPy" }
if (-not (Test-Path $workerPy))  { throw "missing file: $workerPy" }

Info "`n=== PRE-CLEAN ==="
& (Join-Path $ROOT "ops\stop-stable.ps1")

Start-Sleep -Seconds 2

Info "`n=== START WEBHOOK PYTHON ==="
Start-ManagedPython `
  -Name "webhook" `
  -PythonExe $pythonExe `
  -ScriptPath $webhookPy `
  -WorkingDir $ROOT `
  -OutLog (Join-Path $logDir "webhook.out.log") `
  -ErrLog (Join-Path $logDir "webhook.err.log") `
  -PidDir $pidDir

Info "`n=== START WORKER PYTHON ==="
Start-ManagedPython `
  -Name "worker" `
  -PythonExe $pythonExe `
  -ScriptPath $workerPy `
  -WorkingDir $ROOT `
  -OutLog (Join-Path $logDir "worker.out.log") `
  -ErrLog (Join-Path $logDir "worker.err.log") `
  -PidDir $pidDir

Info "`n=== WAIT FOR HEALTH ==="
$ok = $false
for ($i = 1; $i -le 20; $i++) {
  Start-Sleep -Seconds 1
  try {
    $h = Invoke-RestMethod "http://127.0.0.1:8080/health" -TimeoutSec 3
    if ($h.ok -eq $true) {
      Good "health OK on try #$i"
      $ok = $true
      break
    }
  } catch {
  }
}

if (-not $ok) {
  Warn "health endpoint did not become ready in time"
}

Info "`n=== STATUS SNAPSHOT ==="
& (Join-Path $ROOT "ops\status-stable.ps1")