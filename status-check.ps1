Write-Host "=== SLH STATUS ===" -ForegroundColor Cyan
railway status
Write-Host "`n=== LOGS ===" -ForegroundColor Cyan
railway logs --service slh-AI-bot --tail 5
