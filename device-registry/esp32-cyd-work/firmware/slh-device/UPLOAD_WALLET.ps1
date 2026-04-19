# =====================================================================
# UPLOAD_WALLET.ps1 - flash main_wallet.cpp to the ESP32 CYD
# =====================================================================
# What it does:
#   1. Verifies wifi_secrets.h exists and SSID is not a placeholder
#   2. Backs up any existing main.cpp / main_advanced.cpp to *.bak
#   3. Moves main_advanced.cpp out of src/ (prevents duplicate setup/loop)
#   4. Copies main_wallet.cpp -> src/main.cpp (PlatformIO default)
#   5. Runs: pio run -e esp32dev --target upload --upload-port COM5
#   6. On failure -> restores the backups so the tree is never half-done
# =====================================================================
# Usage:
#   cd D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device
#   .\UPLOAD_WALLET.ps1                 # default COM5
#   .\UPLOAD_WALLET.ps1 -Port COM7      # override port
#   .\UPLOAD_WALLET.ps1 -Revert         # restore main_advanced.cpp
# =====================================================================

param(
    [string]$Port = "COM5",
    [switch]$Revert
)

$ErrorActionPreference = "Stop"

# Anchor every path to the directory of this script so CWD doesn't matter.
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SrcDir    = Join-Path $ScriptDir "src"
$IncDir    = Join-Path $ScriptDir "include"

$MainCpp          = Join-Path $SrcDir "main.cpp"
$MainAdvanced     = Join-Path $SrcDir "main_advanced.cpp"
$MainWallet       = Join-Path $SrcDir "main_wallet.cpp"
$MainCppBak       = Join-Path $SrcDir "main.cpp.bak"
$MainAdvancedBak  = Join-Path $SrcDir "main_advanced.cpp.bak"
$MainAdvancedPark = Join-Path $ScriptDir "main_advanced.cpp.parked"
$SecretsH         = Join-Path $IncDir "wifi_secrets.h"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Restore-Backups {
    Write-Step "Restoring backups..."
    if (Test-Path $MainCppBak) {
        Copy-Item $MainCppBak $MainCpp -Force
        Write-Host "    main.cpp restored from backup"
    } elseif (Test-Path $MainCpp) {
        Remove-Item $MainCpp -Force
        Write-Host "    main.cpp removed (had no backup)"
    }
    if (Test-Path $MainAdvancedPark) {
        Move-Item $MainAdvancedPark $MainAdvanced -Force
        Write-Host "    main_advanced.cpp un-parked"
    } elseif ((Test-Path $MainAdvancedBak) -and (-not (Test-Path $MainAdvanced))) {
        Copy-Item $MainAdvancedBak $MainAdvanced -Force
        Write-Host "    main_advanced.cpp restored from .bak"
    }
}

# ---------- Revert mode ----------
if ($Revert) {
    Restore-Backups
    Write-Host ""
    Write-Host "Revert complete. You can re-flash main_advanced.cpp with:" -ForegroundColor Green
    Write-Host "    pio run -e esp32dev --target upload --upload-port $Port"
    exit 0
}

# ---------- 1. Sanity: wifi_secrets.h ----------
Write-Step "Checking wifi_secrets.h"
if (-not (Test-Path $SecretsH)) {
    Write-Host "ERROR: $SecretsH not found." -ForegroundColor Red
    Write-Host "       Create it from the template, fill in SSID + password, then retry."
    exit 1
}
$secrets = Get-Content $SecretsH -Raw
if ($secrets -match "PLACEHOLDER_SSID" -or $secrets -match "PLACEHOLDER_PASSWORD") {
    Write-Host "ERROR: wifi_secrets.h still has PLACEHOLDER values." -ForegroundColor Red
    Write-Host "       Edit $SecretsH and replace WIFI_SSID / WIFI_PASSWORD, then retry."
    exit 1
}
Write-Host "    OK - credentials look filled in"

# ---------- 2. Verify main_wallet.cpp exists ----------
Write-Step "Checking main_wallet.cpp"
if (-not (Test-Path $MainWallet)) {
    Write-Host "ERROR: $MainWallet not found." -ForegroundColor Red
    exit 1
}
Write-Host "    OK"

# ---------- 3. Back up current main.cpp / main_advanced.cpp ----------
Write-Step "Backing up existing sources"
if (Test-Path $MainCpp) {
    Copy-Item $MainCpp $MainCppBak -Force
    Write-Host "    main.cpp           -> main.cpp.bak"
} else {
    Write-Host "    main.cpp           (none)"
}
if (Test-Path $MainAdvanced) {
    Copy-Item $MainAdvanced $MainAdvancedBak -Force
    Write-Host "    main_advanced.cpp  -> main_advanced.cpp.bak"
}

# ---------- 4. Park main_advanced.cpp outside src/ so it isn't compiled ----------
Write-Step "Parking main_advanced.cpp outside src/ to avoid dup setup()/loop()"
if (Test-Path $MainAdvanced) {
    Move-Item $MainAdvanced $MainAdvancedPark -Force
    Write-Host "    moved to $MainAdvancedPark"
}

# ---------- 5. Copy main_wallet.cpp -> main.cpp ----------
Write-Step "Installing main_wallet.cpp as src/main.cpp"
Copy-Item $MainWallet $MainCpp -Force
Write-Host "    OK"

# ---------- 6. Build + upload ----------
Write-Step "Running pio run -e esp32dev --target upload --upload-port $Port"
$pioOk = $false
try {
    & pio run -e esp32dev --target upload --upload-port $Port
    if ($LASTEXITCODE -eq 0) {
        $pioOk = $true
    }
} catch {
    Write-Host "ERROR during pio run: $_" -ForegroundColor Red
}

if (-not $pioOk) {
    Write-Host ""
    Write-Host "UPLOAD FAILED - reverting tree to previous state..." -ForegroundColor Red
    Restore-Backups
    Write-Host "Tree restored. Check the pio output above for the root cause." -ForegroundColor Yellow
    exit 1
}

# ---------- 7. Success: un-park main_advanced.cpp so it lives next to main.cpp ----------
Write-Step "Upload succeeded - un-parking main_advanced.cpp (kept, not built)"
if (Test-Path $MainAdvancedPark) {
    # Rename to .cpp.bak so PlatformIO ignores it on future builds,
    # but the source is still here next to main_wallet.cpp.
    if (Test-Path $MainAdvancedBak) {
        Remove-Item $MainAdvancedPark -Force
        Write-Host "    parked copy dropped (main_advanced.cpp.bak already holds the source)"
    } else {
        Move-Item $MainAdvancedPark $MainAdvancedBak -Force
        Write-Host "    moved to main_advanced.cpp.bak (preserved for later revert)"
    }
}

Write-Host ""
Write-Host "SUCCESS. Open serial monitor with:" -ForegroundColor Green
Write-Host "    pio device monitor -e esp32dev --port $Port -b 115200"
Write-Host ""
Write-Host "To go back to the old admin firmware:" -ForegroundColor Green
Write-Host "    .\UPLOAD_WALLET.ps1 -Revert"
Write-Host "    pio run -e esp32dev --target upload --upload-port $Port"
