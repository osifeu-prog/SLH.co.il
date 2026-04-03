param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("webhook","worker","tunnel")]
  [string]$Role
)

$ErrorActionPreference = "Continue"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $ROOT)

function LogLine([string]$m) {
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Write-Host "[$ts][$Role] $m"
}

if (-not (Test-Path ".\runtime")) {
  New-Item -ItemType Directory -Force -Path ".\runtime" | Out-Null
}

$py = Join-Path (Get-Location) "venv\Scripts\python.exe"
if ($Role -ne "tunnel" -and -not (Test-Path $py)) {
  throw "venv python not found: $py"
}

function Get-EnvValue([string]$name) {
  $envText = Get-Content ".\.env" -Raw
  return ([regex]::Match($envText, "(?m)^$name=(.+)$")).Groups[1].Value.Trim()
}

function Set-WebhookUrl([string]$newWebhook) {
  $envPath = ".\.env"
  $txt = Get-Content $envPath -Raw
  if ($txt -match '(?m)^WEBHOOK_URL=') {
    $txt = [regex]::Replace($txt, '(?m)^WEBHOOK_URL=.*$', "WEBHOOK_URL=$newWebhook")
  } else {
    $txt = $txt.TrimEnd() + "`nWEBHOOK_URL=$newWebhook`n"
  }
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText((Resolve-Path $envPath), ($txt -replace "`r`n","`n"), $enc)
}

function Refresh-TelegramWebhook([string]$webhookUrl) {
  $botToken = Get-EnvValue "BOT_TOKEN"
  $webhookSecret = Get-EnvValue "WEBHOOK_SECRET"

  if (-not $botToken) { throw "BOT_TOKEN missing in .env" }
  if (-not $webhookUrl) { throw "WEBHOOK_URL missing in .env" }

  LogLine "deleteWebhook"
  Invoke-RestMethod -Uri ("https://api.telegram.org/bot{0}/deleteWebhook?drop_pending_updates=true" -f $botToken) | Out-Null

  $body = @{ url = $webhookUrl }
  if ($webhookSecret) { $body["secret_token"] = $webhookSecret }

  $ok = $false
  $lastErr = $null

  for ($i = 0; $i -lt 40; $i++) {
    try {
      LogLine "setWebhook try $($i+1)"
      $resp = Invoke-RestMethod -Method Post -Uri ("https://api.telegram.org/bot{0}/setWebhook" -f $botToken) -Body $body
      if ($resp.ok) {
        $ok = $true
        break
      }
    } catch {
      $lastErr = $_
      Start-Sleep -Seconds 3
    }
  }

  if (-not $ok) {
    throw "setWebhook failed after retries. Last error: $lastErr"
  }

  $wh = Invoke-RestMethod -Uri ("https://api.telegram.org/bot{0}/getWebhookInfo" -f $botToken)
  if ($wh.result.url -ne $webhookUrl) {
    throw "Webhook mismatch. env=$webhookUrl api=$($wh.result.url)"
  }

  LogLine "Webhook registered OK: $webhookUrl"
}

switch ($Role) {
  "webhook" {
    while ($true) {
      try {
        LogLine "Starting webhook_server.py"
        & $py ".\webhook_server.py"
        $exitCode = $LASTEXITCODE
        LogLine "webhook_server.py exited. code=$exitCode"
      } catch {
        LogLine "webhook_server.py crashed: $($_.Exception.Message)"
      }
      Start-Sleep -Seconds 2
    }
  }

  "worker" {
    while ($true) {
      try {
        LogLine "Starting worker.py"
        & $py ".\worker.py"
        $exitCode = $LASTEXITCODE
        LogLine "worker.py exited. code=$exitCode"
      } catch {
        LogLine "worker.py crashed: $($_.Exception.Message)"
      }
      Start-Sleep -Seconds 2
    }
  }

  "tunnel" {
    while ($true) {
      $p = $null
      try {
        $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $stdout = Join-Path (Get-Location) "runtime\tunnel_stdout_$stamp.log"
        $stderr = Join-Path (Get-Location) "runtime\tunnel_stderr_$stamp.log"

        LogLine "Starting cloudflared quick tunnel"
        $p = Start-Process cloudflared `
          -ArgumentList @("tunnel","--url","http://127.0.0.1:8080") `
          -RedirectStandardOutput $stdout `
          -RedirectStandardError $stderr `
          -PassThru

        $found = $null
        for ($i = 0; $i -lt 60; $i++) {
          Start-Sleep -Seconds 1

          $logText = ""
          if (Test-Path $stdout) {
            $tmp = Get-Content $stdout -Raw -ErrorAction SilentlyContinue
            if ($tmp) { $logText += $tmp }
          }
          if (Test-Path $stderr) {
            $tmp = Get-Content $stderr -Raw -ErrorAction SilentlyContinue
            if ($tmp) { $logText += "`n" + $tmp }
          }

          if (-not [string]::IsNullOrWhiteSpace($logText)) {
            $m = [regex]::Match($logText, 'https://[a-z0-9-]+\.trycloudflare\.com')
            if ($m.Success) {
              $found = $m.Value
              break
            }
          }

          if ($p.HasExited) { break }
        }

        if (-not $found) {
          try { if ($p -and -not $p.HasExited) { Stop-Process -Id $p.Id -Force } } catch {}
          throw "Could not extract tunnel URL"
        }

        $newWebhook = "$found/tg/webhook"
        LogLine "Tunnel URL found: $found"

        Set-WebhookUrl -newWebhook $newWebhook
        Refresh-TelegramWebhook -webhookUrl $newWebhook

        LogLine "Tunnel is supervised. Waiting for process exit."
        Wait-Process -Id $p.Id
        LogLine "cloudflared exited. restarting in 3 sec"
      } catch {
        LogLine "tunnel supervisor error: $($_.Exception.Message)"
        try { if ($p -and -not $p.HasExited) { Stop-Process -Id $p.Id -Force } } catch {}
      }

      Start-Sleep -Seconds 3
    }
  }
}