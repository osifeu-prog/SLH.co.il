param()

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $ROOT)

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$OUT = Join-Path (Get-Location) "_snapshot_state_$ts"
New-Item -ItemType Directory -Force -Path $OUT | Out-Null

$py = Join-Path (Get-Location) "venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "venv python not found: $py" }

Copy-Item ".\state\STATE.md"        "$OUT\STATE.md"        -ErrorAction SilentlyContinue
Copy-Item ".\state\RUNBOOK.md"      "$OUT\RUNBOOK.md"      -ErrorAction SilentlyContinue
Copy-Item ".\state\ROADMAP.md"      "$OUT\ROADMAP.md"      -ErrorAction SilentlyContinue
Copy-Item ".\state\ARCHITECTURE.md" "$OUT\ARCHITECTURE.md" -ErrorAction SilentlyContinue

& $py -m pip freeze | Out-File -FilePath "$OUT\requirements.txt" -Encoding utf8

Get-ChildItem -Recurse -Force |
Where-Object {
  $_.FullName -notmatch '\\venv(\\|$)' -and
  $_.FullName -notmatch '\\__pycache__(\\|$)' -and
  $_.FullName -notmatch '\\logs(\\|$)'
} |
ForEach-Object {
  $_.FullName.Replace((Get-Location).Path,'')
} | Out-File -FilePath "$OUT\tree.txt" -Encoding utf8

Write-Host "SNAPSHOT READY => $OUT" -ForegroundColor Green