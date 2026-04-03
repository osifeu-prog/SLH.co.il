param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

function Info([string]$m) { Write-Host $m -ForegroundColor Cyan }
function Good([string]$m) { Write-Host $m -ForegroundColor Green }
function Warn([string]$m) { Write-Host $m -ForegroundColor Yellow }

Info "=== COMMERCE DOCTOR :: LOCAL FILES ==="

$requiredFiles = @(
  ".\app\services\purchases.py",
  ".\app\services\purchases_admin.py",
  ".\app\handlers\purchases.py",
  ".\app\handlers\ton_admin.py",
  ".\worker.py",
  ".\slh.ps1",
  ".\ops\sql\patch_commerce_foundation_v1.sql",
  ".\ops\sql\seed_products_v1.sql",
  ".\ops\sql\patch_commerce_groups_and_flags_v1.sql",
  ".\ops\sql\patch_commerce_product_controls_v1.sql"
)

foreach ($f in $requiredFiles) {
  if (Test-Path $f) { Good "OK  $f" } else { Warn "MISS $f" }
}

Info "`n=== PY_COMPILE ==="
.\venv\Scripts\python.exe -m py_compile .\app\services\purchases.py
.\venv\Scripts\python.exe -m py_compile .\app\services\purchases_admin.py
.\venv\Scripts\python.exe -m py_compile .\app\handlers\purchases.py
.\venv\Scripts\python.exe -m py_compile .\app\handlers\ton_admin.py
.\venv\Scripts\python.exe -m py_compile .\worker.py
Good "Python compile passed"

Info "`n=== KEY CODE HINTS ==="
$patterns = @(
  "purchase.order_created",
  "purchase.payment_submitted",
  "purchase.order_paid",
  "purchase.order_fulfilled",
  "_first_line_text",
  "purchase_mark_paid",
  "purchase_fulfill",
  "inventory_mode",
  "is_featured",
  "purchase_limit_per_user"
)

foreach ($p in $patterns) {
  $hits = Get-ChildItem .\app -Recurse -File -Include *.py | Select-String -Pattern $p -SimpleMatch
  if ($hits) {
    Good "HIT $p"
  } else {
    Warn "MISS $p"
  }
}

Info "`n=== GIT STATUS ==="
git status --short

Info "`n=== LAST 8 COMMITS ==="
git log --oneline -n 8

Good "`nCOMMERCE DOCTOR DONE"