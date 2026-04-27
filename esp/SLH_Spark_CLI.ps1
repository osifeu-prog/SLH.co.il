$global:SLH_BASE = "https://slh-api-production.up.railway.app"
$global:ESP_DIR = "D:\SLH_ECOSYSTEM\esp"
$global:API_DIR = "D:\SLH_ECOSYSTEM\api"

function slh-health { Invoke-RestMethod "$global:SLH_BASE/api/health" }
function slh-stats  { Invoke-RestMethod "$global:SLH_BASE/api/stats" }
function slh-openapi { Invoke-RestMethod "$global:SLH_BASE/api/openapi.json" }

function slh-register-device {
    param(
        [string]$device_id = "ESP32_001",
        [string]$phone = "+000000000",
        [string]$device_type = "esp32"
    )

    $body = @{
        device_id = $device_id
        phone = $phone
        device_type = $device_type
    } | ConvertTo-Json

    Invoke-RestMethod -Method POST `
        -Uri "$global:SLH_BASE/api/device/register" `
        -ContentType "application/json" `
        -Body $body
}

function slh-esp-dir { Set-Location $global:ESP_DIR }
function slh-esp-build { Set-Location $global:ESP_DIR; pio run }
function slh-esp-clean { Set-Location $global:ESP_DIR; pio run -t clean }
function slh-esp-flash { Set-Location $global:ESP_DIR; pio run -t upload }
function slh-esp-monitor { Set-Location $global:ESP_DIR; pio device monitor }

function slh-status {
    [PSCustomObject]@{
        base = $global:SLH_BASE
        esp_dir = $global:ESP_DIR
        api_dir = $global:API_DIR
        health = (slh-health).status
    }
}

Set-Alias shl slh-health
Set-Alias sst slh-stats
Set-Alias sreg slh-register-device

Write-Host "SLH Spark CLI loaded"
