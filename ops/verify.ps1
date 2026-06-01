Write-Host "=== SLH VERIFICATION ===" -ForegroundColor Cyan

# Check core files
$required = @(
    "D:\SLH_ECOSYSTEM\core\registry.json",
    "D:\SLH_ECOSYSTEM\core\slh.ps1",
    "D:\SLH_ECOSYSTEM\.env"
)

foreach ($file in $required) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file MISSING" -ForegroundColor Red
    }
}

# Test Telegram
$token = [Environment]::GetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "Process")
if (-not $token) {
    $envContent = Get-Content "D:\SLH_ECOSYSTEM\.env" -ErrorAction SilentlyContinue
    $tokenLine = $envContent | Select-String "TELEGRAM_BOT_TOKEN="
    if ($tokenLine) { $token = ($tokenLine -split "=", 2)[1] }
}

if ($token) {
    try {
        $response = Invoke-RestMethod "https://api.telegram.org/bot$token/getMe" -TimeoutSec 5
        Write-Host "✅ Telegram Bot: $($response.result.username)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Telegram Bot: Connection failed" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Telegram Bot: No token" -ForegroundColor Red
}

Write-Host "`n✅ Verification complete"
