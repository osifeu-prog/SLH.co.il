param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$envMap = @{}
Get-Content .\.env | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    if ($_ -match '^\s*([^=]+?)\s*=\s*(.*)\s*$') {
        $envMap[$matches[1]] = $matches[2]
    }
}

$BOT_TOKEN = $envMap["BOT_TOKEN"]
if (-not $BOT_TOKEN) { throw "BOT_TOKEN missing in .env" }

$r = Invoke-RestMethod "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"
$r | ConvertTo-Json -Depth 8