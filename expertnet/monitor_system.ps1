Write-Host "🛡️ ExpertNet Watchdog Activated..." -ForegroundColor Cyan
$botPath = "D:\ExpertNet_Core\scripts\telegram_bot.py"

while ($true) {
    # בדיקה האם הבוט רץ
    $process = Get-Process python* -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*telegram_bot.py*" }
    
    if (-not $process) {
        Write-Host "⚠️ Bot is down! Restarting..." -ForegroundColor Red
        Start-Process py -ArgumentList "$botPath" -NoNewWindow
    } else {
        Write-Host "✅ System Healthy: 01:46:00" -ForegroundColor Green
    }
    
    Start-Sleep -Seconds 30 # בדיקה כל 30 שניות
}