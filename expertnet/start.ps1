function runbot { py scripts/telegram_bot.py }
function check-all { 
    Write-Host '--- System Check ---' -ForegroundColor Yellow
    Test-Path vault/expertnet.db
    Write-Host 'Check Complete.' -ForegroundColor Green
}
Write-Host 'SLH MASTER ENVIRONMENT LOADED' -ForegroundColor Cyan
