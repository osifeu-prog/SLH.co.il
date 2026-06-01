# SLH Full Deploy Script
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
nssm stop SLH_Bot 2>
Write-Host '📦 יוצר bot.py...' -ForegroundColor Yellow
# (הקוד המלא יוטמע כאן מתוך הסקריפט  נשתמש בקובץ קיים)
if (-not (Test-Path bot.py)) { Write-Host '❌ bot.py חסר!' -ForegroundColor Red; exit 1 }
railway up --service slh-AI-bot
Write-Host '✅ הועלה! חכה 40 שניות.' -ForegroundColor Green
Start-Sleep -Seconds 40
Write-Host '🎉 שלח /start  הלוגו חי.' -ForegroundColor Green
