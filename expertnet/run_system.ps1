Write-Host "--- EXPERTNET CORE PROTECTIVE LAUNCHER ---" -ForegroundColor Cyan

# 1. בדיקת קבצים קריטיים
if (!(Test-Path "vault/.env")) { 
    Write-Host "CRITICAL ERR: .env missing!" -ForegroundColor Red; exit 
}
if (!(Test-Path "vault/expertnet.db")) {
    Write-Host "NOTICE: Creating fresh database..." -ForegroundColor Yellow
    # כאן אפשר להוסיף קוד ליצירת ה-DB אם הוא נמחק
}

# 2. לולאת אל-פסק (Infinite Loop)
while ($true) {
    Write-Host "Starting System Core..." -ForegroundColor Green
    # הרצת הבוט והמתנה לסיום (קריסה או סגירה)
    py scripts\telegram_bot.py
    
    Write-Host "System process terminated. Restarting in 5 seconds..." -ForegroundColor Red
    Start-Sleep -Seconds 5
}