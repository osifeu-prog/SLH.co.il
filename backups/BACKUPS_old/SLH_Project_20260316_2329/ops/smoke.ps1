param()
$ErrorActionPreference = "Continue"
$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ROOT

Write-Host "=== SLH SMOKE TEST ===" -ForegroundColor Cyan

Write-Host "`n[1] status" -ForegroundColor Cyan
powershell -ExecutionPolicy Bypass -File .\slh.ps1 status

Write-Host "`n[2] local /healthz" -ForegroundColor Cyan
try { irm http://127.0.0.1:8080/healthz | ConvertTo-Json -Depth 6 } catch { Write-Host $_.Exception.Message -ForegroundColor Yellow }

Write-Host "`n[3] local /health" -ForegroundColor Cyan
try { irm http://127.0.0.1:8080/health | ConvertTo-Json -Depth 6 } catch { Write-Host $_.Exception.Message -ForegroundColor Yellow }

Write-Host "`n[4] local /readyz" -ForegroundColor Cyan
try { irm http://127.0.0.1:8080/readyz | ConvertTo-Json -Depth 6 } catch { Write-Host $_.Exception.Message -ForegroundColor Yellow }

Write-Host "`n[5] webhook info" -ForegroundColor Cyan
try { .\ops\get-webhook-info.ps1 } catch { Write-Host $_.Exception.Message -ForegroundColor Yellow }

Write-Host "`n[6] redis stream len" -ForegroundColor Cyan
try { docker exec slh_redis redis-cli XLEN slh:updates } catch { Write-Host $_.Exception.Message -ForegroundColor Yellow }

Write-Host "`nSMOKE_DONE" -ForegroundColor Green