Write-Host "=== SLH DAILY DIGEST ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd')`n"

& "D:\SLH_ECOSYSTEM\core\slh.ps1" status
& "D:\SLH_ECOSYSTEM\core\slh.ps1" report

Write-Host "`n✅ Daily digest complete"
