param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Read-Text([string]$Path) {
  if (Test-Path $Path) {
    return Get-Content $Path -Raw -Encoding UTF8
  }
  return "[missing] $Path"
}

function Try-Run([scriptblock]$Block, [string]$Fallback = "[unavailable]") {
  try { return (& $Block | Out-String).TrimEnd() } catch { return $Fallback }
}

$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$repoUrl = "https://github.com/osifeu-prog/SLH_PROJECT_V2.git"
$rootPath = (Get-Location).Path

$gitCommit = Try-Run { git rev-parse --short HEAD }
$gitBranch = Try-Run { git branch --show-current }
$gitStatus = Try-Run { git status --short }
$pythonProcs = Try-Run {
  Get-CimInstance Win32_Process |
    Where-Object { $_.Name -eq 'python.exe' -and $_.ExecutablePath -like '*SLH_PROJECT_V2*' } |
    Select-Object ProcessId, CommandLine |
    Format-Table -AutoSize
}

$healthLocal = Try-Run {
  (Invoke-WebRequest "http://127.0.0.1:8080/healthz" -UseBasicParsing -TimeoutSec 5).Content
}

$handlers = Try-Run {
  Get-ChildItem .\app\handlers -File -ErrorAction Stop |
    Select-Object -ExpandProperty Name |
    Sort-Object
}

$services = Try-Run {
  Get-ChildItem .\app\services -File -ErrorAction Stop |
    Select-Object -ExpandProperty Name |
    Sort-Object
}

$opsFiles = Try-Run {
  Get-ChildItem .\ops -File -ErrorAction Stop |
    Select-Object -ExpandProperty Name |
    Sort-Object
}

$mdFiles = Try-Run {
  Get-ChildItem -Recurse -File -Include *.md |
    Where-Object {
      $_.FullName -notmatch '\\venv(\\|$)' -and
      $_.FullName -notmatch '\\__pycache__(\\|$)'
    } |
    ForEach-Object { $_.FullName.Replace((Get-Location).Path + "\", "") } |
    Sort-Object
}

$webhookInfo = Try-Run {
  $envText = Get-Content .\.env -Raw -Encoding UTF8
  if ($envText -match '(?m)^BOT_TOKEN=(.+)$') {
    $botToken = $matches[1].Trim()
    Invoke-RestMethod "https://api.telegram.org/bot$botToken/getWebhookInfo" | ConvertTo-Json -Depth 8
  } else {
    "[BOT_TOKEN missing]"
  }
}

$workProtocol = @"
## Working Protocol
- No guessing
- Always inspect code or runtime state before proposing changes
- First provide PowerShell commands to expose the needed data
- User runs the commands and returns the output
- Only after enough evidence exists, provide exact PowerShell patch commands
- Preserve UTF-8 without BOM and LF endings
- Prefer minimal patches and clean commit scope
- Target: safe path toward 100K registered users
"@

$brief = @"
# SLH_PROJECT_V2 :: PROJECT_BRIEF

Updated at: $stamp

## Repository
- Root: $rootPath
- Remote: $repoUrl
- Branch: $gitBranch
- Commit: $gitCommit

## Current Runtime Shape
- Production Telegram webhook points to Railway
- Local stack exists for hardening and diagnostics
- Runtime flow: webhook -> redis -> worker -> postgres

## Verified System Direction
- Ledger-backed finance layer exists
- Withdrawal hardening is documented as verified
- Bot domain includes rewards, invites, tasks, profile, admin, withdrawals

## Local Health
$healthLocal

## Local Python Processes
$pythonProcs

## Current Git Status
$gitStatus

$workProtocol

## Primary State Sources
- state\PROJECT_SCAN.md
- state\ANCHOR.md
- state\STATE.md
- state\ARCHITECTURE.md
- state\ROADMAP.md
- state\RUNBOOK.md
"@

$scan = @"
# SLH_PROJECT_V2 :: PROJECT_SCAN

Updated at: $stamp

## Purpose
Single-file operational and architectural scan for fast future handoff.

## Repository
- Root: $rootPath
- Remote: $repoUrl
- Branch: $gitBranch
- Current commit: $gitCommit

## Current Understanding
- Telegram production webhook points to Railway
- Local stack exists for hardening and diagnostics
- Runtime architecture is webhook -> redis -> worker -> postgres
- Ledger-backed finance layer exists
- Withdrawal hardening is documented as verified
- Bot domain includes rewards, invites, tasks, profile, admin, withdrawals

$workProtocol

## Local Health
$healthLocal

## Running Local Python Processes
$pythonProcs

## Git Status
$gitStatus

## Handlers
$handlers

## Services
$services

## Ops Files
$opsFiles

## Markdown Sources
$mdFiles

## Telegram Webhook Info
$webhookInfo

---

## ROOT ARCHITECTURE.md
$(Read-Text ".\ARCHITECTURE.md")

---

## ROOT NEXT_STEPS.md
$(Read-Text ".\NEXT_STEPS.md")

---

## ROOT STATE_RUNBOOK.md
$(Read-Text ".\STATE_RUNBOOK.md")

---

## state\ANCHOR.md
$(Read-Text ".\state\ANCHOR.md")

---

## state\ARCHITECTURE.md
$(Read-Text ".\state\ARCHITECTURE.md")

---

## state\ROADMAP.md
$(Read-Text ".\state\ROADMAP.md")

---

## state\RUNBOOK.md
$(Read-Text ".\state\RUNBOOK.md")

---

## state\STATE.md
$(Read-Text ".\state\STATE.md")
"@

$enc = New-Object System.Text.UTF8Encoding($false)

$briefLf = $brief -replace "`r`n", "`n"
[System.IO.File]::WriteAllText((Join-Path (Get-Location) "state\PROJECT_BRIEF.md"), $briefLf, $enc)

$scanLf = $scan -replace "`r`n", "`n"
[System.IO.File]::WriteAllText((Join-Path (Get-Location) "state\PROJECT_SCAN.md"), $scanLf, $enc)

Write-Host "WROTE state\PROJECT_BRIEF.md" -ForegroundColor Green
Write-Host "WROTE state\PROJECT_SCAN.md" -ForegroundColor Green