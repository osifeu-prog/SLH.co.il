param([switch]$Json)

$report = [ordered]@{}

# HTML files check
$htmlPath = "D:\investor-landing"
$required = @("index.html","contracts.html","about.html","faq.html","contact.html")
$missing = @()
foreach ($file in $required) {
    if (!(Test-Path "$htmlPath\$file")) { $missing += $file }
}
$report["missing_files"] = $missing

# Backups
$backupPath = "D:\slh-website\slh-claude-bot\backups"
$backups = Get-ChildItem "$backupPath\*.zip" -ErrorAction SilentlyContinue
$report["backups"] = $backups.Count

# Git
$gitStatus = git status --porcelain
$report["git_clean"] = ($gitStatus -eq "")

# Site
try {
    $resp = Invoke-WebRequest "https://slh-nft.com/investor-landing/" -TimeoutSec 10
    $report["site_status"] = $resp.StatusCode
} catch {
    $report["site_status"] = "DOWN"
}

$report["timestamp"] = (Get-Date).ToString("s")

if ($Json) {
    $report | ConvertTo-Json -Depth 5
} else {
    $report
}
