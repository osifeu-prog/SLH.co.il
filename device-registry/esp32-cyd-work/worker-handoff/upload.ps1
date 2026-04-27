Write-Host "=== SLH ESP32 UPLOAD ===" -ForegroundColor Cyan

# בדוק שהמכשיר מחובר
Write-Host "Checking connection..." -ForegroundColor Yellow
python -m esptool --port COM5 chip-id

if ($LASTEXITCODE -ne 0) {
    Write-Host "ESP32 not found on COM5!" -ForegroundColor Red
    exit 1
}

Write-Host "Uploading main.py..." -ForegroundColor Yellow
mpremote connect COM5 cp main.py :main.py

Write-Host "Soft resetting..." -ForegroundColor Yellow
mpremote connect COM5 soft-reset

Write-Host "Starting REPL (press Ctrl+] to exit)..." -ForegroundColor Green
mpremote connect COM5 repl
