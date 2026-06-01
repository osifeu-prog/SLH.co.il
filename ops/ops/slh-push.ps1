# slh-push.ps1 — SLH Ecosystem deploy wrapper for website + api commits.
#
# Stages a specific file list, commits, pushes, and notifies @SLH_Claude_bot
# via the existing /api/broadcast/send endpoint. There is NO native git
# post-push hook in git, so this wrapper IS the post-push hook.
#
# Usage (from inside a repo working dir):
#   D:\SLH_ECOSYSTEM\ops\slh-push.ps1 -Files "daily-blog.html" -Message "fix(daily-blog): theme bootstrap"
#   D:\SLH_ECOSYSTEM\ops\slh-push.ps1 -Files "a.html","b.html" -Message "feat: ..." -Branch main
#   D:\SLH_ECOSYSTEM\ops\slh-push.ps1 -Files "x" -Message "..." -SkipNotify
#
# Pre-conditions:
#   - $env:SLH_ADMIN_BROADCAST_KEY set in the current shell (else notification skipped, push still runs).
#   - Working dir is the git repo (run from D:\SLH_ECOSYSTEM\website for website pushes).
#
# Safety:
#   - Only stages files passed in -Files (never `git add -A` or `.`).
#   - Never uses --no-verify (pre-commit hooks run normally).
#   - Notification failure does NOT abort or revert the push (push already happened).
#   - Throws (non-zero exit) on git failures so callers can detect.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string[]] $Files,
    [Parameter(Mandatory=$true)] [string]   $Message,
    [string] $Branch = "main",
    [string] $ApiBase = "https://slh-api-production.up.railway.app",
    [switch] $SkipNotify
)

$ErrorActionPreference = "Stop"

# 1. Stage the explicit file list. Never -A or `.` — see Git Safety Protocol.
foreach ($f in $Files) {
    if (-not (Test-Path -LiteralPath $f)) {
        throw "File not found: $f (cwd=$(Get-Location))"
    }
    git add -- $f
    if ($LASTEXITCODE -ne 0) { throw "git add failed for $f (exit $LASTEXITCODE)" }
}

# 2. Commit. Pre-commit hooks must succeed; on failure, fix and rerun (don't --no-verify).
git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    throw "Commit failed (exit $LASTEXITCODE) — pre-commit hook may have rejected. Fix and rerun."
}

# 3. Push.
git push origin $Branch
if ($LASTEXITCODE -ne 0) { throw "Push failed (exit $LASTEXITCODE)" }

# 4. Capture commit SHA + remote URL for the notification body.
$sha  = (git rev-parse --short HEAD).Trim()
$repo = ((git config --get remote.origin.url).Trim()) -replace '\.git$',''
# Normalize SSH form to https for clickable link in Telegram.
if ($repo -match '^git@github\.com:(.+)$') { $repo = "https://github.com/$($Matches[1])" }

Write-Host "OK Pushed $($Files.Count) file(s) to origin/$Branch (sha=$sha)" -ForegroundColor Green

# 5. Notify @SLH_Claude_bot via existing API (no new tokens, no hardcoded secrets).
if ($SkipNotify) {
    Write-Host "Notification skipped (-SkipNotify)" -ForegroundColor Yellow
    return
}

$key = $env:SLH_ADMIN_BROADCAST_KEY
if (-not $key) {
    Write-Warning "SLH_ADMIN_BROADCAST_KEY env var not set — notification skipped. Push succeeded."
    return
}

$fileList = ($Files | ForEach-Object { "  - $_" }) -join "`n"
$body = @"
[deploy] $Message

Branch: $Branch
Commit: $sha
Repo:   $repo/commit/$sha
Files:
$fileList
"@

$payload = @{
    message = $body
    target  = "admins"
} | ConvertTo-Json -Compress

try {
    Invoke-RestMethod -Method POST `
        -Uri  "$ApiBase/api/broadcast/send" `
        -Headers @{ "X-Admin-Key" = $key; "Content-Type" = "application/json" } `
        -Body $payload | Out-Null
    Write-Host "OK Telegram notification sent (sha=$sha)" -ForegroundColor Green
} catch {
    Write-Warning "Notification failed: $($_.Exception.Message) — push succeeded, alert manually if needed."
}
