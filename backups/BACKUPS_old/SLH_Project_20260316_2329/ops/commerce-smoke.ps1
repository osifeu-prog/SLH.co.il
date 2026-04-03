param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

function Info([string]$m) { Write-Host $m -ForegroundColor Cyan }
function Good([string]$m) { Write-Host $m -ForegroundColor Green }
function Warn([string]$m) { Write-Host $m -ForegroundColor Yellow }

Info "=== COMMERCE SMOKE CHECKLIST ==="
Write-Host ""
Write-Host "1) Telegram user flow"
Write-Host "   /buy"
Write-Host "   Buy VIP_MONTH"
Write-Host "   /my_orders"
Write-Host "   /submit_payment <order_id> TESTREF123"
Write-Host ""
Write-Host "2) Telegram admin flow"
Write-Host "   /purchase_queue"
Write-Host "   /purchase_order <order_id>"
Write-Host "   /purchase_mark_paid <order_id> TESTREF123 paid_by_admin"
Write-Host "   /purchase_fulfill <order_id> delivered"
Write-Host ""
Write-Host "3) DB verification"
Write-Host "   railway connect"
Write-Host "   Then verify purchase_orders + audit_log"
Write-Host ""
Write-Host "4) Remote app logs"
Write-Host "   railway ssh"
Write-Host "   tail -n 120 /app/logs/worker.log"
Write-Host ""

Info "=== POWER SHELL REMINDER ==="
Warn "SQL runs only inside psql after railway connect"
Warn "tail works only inside railway ssh Linux shell"

Good "`nCOMMERCE SMOKE GUIDE READY"