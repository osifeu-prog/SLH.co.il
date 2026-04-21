$ErrorActionPreference = "Continue"
$API = "https://slh-api-production.up.railway.app"

"=== ADMIN API TEST ==="
"Time: $(Get-Date -Format s)"
""

function Test-Url {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Key = ""
    )

    "---- $Name ----"
    "URL: $Url"

    try {
        if ($Key -and $Key -ne "PASTE_HERE" -and $Key -ne "PUT_REAL_KEY_HERE") {
            $r = Invoke-WebRequest -Uri $Url -Headers @{ "X-Admin-Key" = $Key } -Method GET -TimeoutSec 20
        } else {
            $r = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 20
        }
        "Status: $($r.StatusCode)"
        $r.Content
    }
    catch {
        if ($_.Exception.Response) {
            "Status: $([int]$_.Exception.Response.StatusCode)"
            try {
                $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $sr.ReadToEnd()
            } catch {
                $_.Exception.Message
            }
        } else {
            $_.Exception.Message
        }
    }
    ""
}

$envFile = Join-Path $PSScriptRoot ".env.template"
$adminKey = ""
if (Test-Path $envFile) {
    $line = Select-String -Path $envFile -Pattern '^ADMIN_API_KEYS=' | Select-Object -First 1
    if ($line) {
        $raw = ($line.Line -replace '^ADMIN_API_KEYS=','').Trim()
        if ($raw -match ',') {
            $adminKey = ($raw.Split(',')[0]).Trim()
        } else {
            $adminKey = $raw
        }
    }
}

Test-Url "health" "$API/api/health"
Test-Url "tokenomics" "$API/api/tokenomics/stats"
Test-Url "staking" "$API/api/staking/plans"
Test-Url "guardian blacklist (no auth)" "$API/api/guardian/blacklist?limit=3"
Test-Url "admin devices (no auth)" "$API/api/admin/devices/list?limit=3"
Test-Url "admin events (no auth)" "$API/api/admin/events?limit=3"
Test-Url "guardian blacklist (with key)" "$API/api/guardian/blacklist?limit=3" $adminKey
Test-Url "admin devices (with key)" "$API/api/admin/devices/list?limit=3" $adminKey
Test-Url "admin events (with key)" "$API/api/admin/events?limit=3" $adminKey
