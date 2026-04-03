$ErrorActionPreference = "Stop"

Set-Location (Split-Path $PSScriptRoot -Parent)

$envPath = ".env"

if (!(Test-Path $envPath)) {
    throw ".env not found"
}

$newToken = Read-Host "Enter NEW BOT_TOKEN"
if ([string]::IsNullOrWhiteSpace($newToken)) {
    throw "Token cannot be empty"
}

$text = Get-Content $envPath -Raw

if ($text -match "(?m)^BOT_TOKEN=") {
    $text = $text -replace "(?m)^BOT_TOKEN=.*$", "BOT_TOKEN=$newToken"
} else {
    if ($text -and -not $text.EndsWith("`n")) {
        $text += "`n"
    }
    $text += "BOT_TOKEN=$newToken`n"
}

$enc = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path (Get-Location) $envPath), ($text -replace "`r`n","`n"), $enc)

Write-Host "BOT_TOKEN updated in .env" -ForegroundColor Green