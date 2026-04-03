$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT

function Info([string]$m) { Write-Host $m -ForegroundColor Cyan }
function Good([string]$m) { Write-Host $m -ForegroundColor Green }
function Warn([string]$m) { Write-Host $m -ForegroundColor Yellow }

Info "`n=== SAFE RESTART :: DOWN ==="
powershell -NoProfile -ExecutionPolicy Bypass -File ".\ops\stop-stable.ps1"

Start-Sleep -Seconds 2

Info "`n=== SAFE RESTART :: UP ==="
powershell -NoProfile -ExecutionPolicy Bypass -File ".\ops\start-stable.ps1"

Start-Sleep -Seconds 2

Info "`n=== SAFE RESTART :: DOCTOR ==="
powershell -NoProfile -ExecutionPolicy Bypass -File ".\ops\doctor.ps1"

Info "`n=== SAFE RESTART :: HEALTH VERIFY ==="
try {
  $h = Invoke-RestMethod "http://127.0.0.1:8080/health" -TimeoutSec 5
  if ($h.ok -eq $true) {
    Good ("health ok, mode=" + $h.mode)
  } else {
    throw "health returned but ok != true"
  }
} catch {
  Warn $_.Exception.Message
  exit 1
}

Good "`nrestart-safe completed successfully"