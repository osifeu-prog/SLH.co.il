Write-Host "`n=== RUN TODAY START ===`n" -ForegroundColor Cyan

Write-Host "1) Running ledger inspection..." -ForegroundColor Yellow
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\inspect-ledger.ps1" | Tee-Object -FilePath "$PSScriptRoot\output_ledger.txt"

Write-Host "`n2) Running admin API tests..." -ForegroundColor Yellow
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\test-admin-api.ps1" | Tee-Object -FilePath "$PSScriptRoot\output_admin.txt"

Write-Host "`n3) Summary files created:" -ForegroundColor Green
Get-ChildItem "$PSScriptRoot" | Select-Object Name,Length,LastWriteTime

Write-Host "`nNext chat should start from:" -ForegroundColor Cyan
Write-Host "$PSScriptRoot\SESSION_HANDOFF_NEXT_CHAT.md" -ForegroundColor White
