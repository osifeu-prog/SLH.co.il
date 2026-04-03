$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$py = ".\venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  throw "Python venv not found: $py"
}

Write-Host "=== REVIEW GATE :: PY_COMPILE ===" -ForegroundColor Cyan
& $py -m py_compile .\worker.py
& $py -m py_compile .\app\handlers\purchases.py
& $py -m py_compile .\app\handlers\ton_admin.py
& $py -m py_compile .\app\services\purchases.py
& $py -m py_compile .\app\services\delivery.py
& $py -m py_compile .\app\services\purchases_admin.py
& $py -m py_compile .\app\i18n.py

Write-Host "=== REVIEW GATE :: SECRET SCAN ===" -ForegroundColor Cyan

$badPatterns = @(
  'BOT_TOKEN\s*=\s*[0-9]{6,}:[A-Za-z0-9_-]{20,}',
  'DATABASE_URL\s*=\s*["'']?[^"'']+@'
)

$files = git ls-files
if (-not $files) {
  throw "git ls-files returned no files"
}

foreach ($rel in $files) {
  if (
    $rel -match '(^|/)\.env($|[.])' -or
    $rel -match '(^|/)ops/local/' -or
    $rel -match '(^|/)state/' -or
    $rel -match '(^|/)backups/' -or
    $rel -match '(^|/)_diag_' -or
    $rel -match '(^|/)logs?/' -or
    $rel -match '(^|/)__pycache__/' -or
    $rel -match '(^|/)venv/' -or
    $rel -match '(^|/)review-gate\.ps1$' -or
    $rel -match '(^|/)_patch_' -or
    $rel -match '(^|/)patch_.*\.py$' -or
    $rel -match '\.bak'
  ) {
    continue
  }

  $full = Join-Path (Get-Location) $rel
  if (-not (Test-Path $full)) { continue }

  $text = Get-Content $full -Raw -ErrorAction SilentlyContinue
  if ($null -eq $text) { continue }

  foreach ($pattern in $badPatterns) {
    if ($text -match $pattern) {
      Write-Host "Potential secret pattern in $full" -ForegroundColor Red
      Write-Host "Pattern: $pattern" -ForegroundColor Red
      exit 1
    }
  }
}

Write-Host "=== REVIEW GATE :: DONE ===" -ForegroundColor Green
Write-Host "Compile and tracked-file secret scan passed." -ForegroundColor Green