function Show-SLH-Header {
    param($title = "SLH SPARK SYSTEM", $color = "Cyan")
    Write-Host ""
    Write-Host " =================================================" -ForegroundColor $color
    Write-Host "   $title" -ForegroundColor White
    Write-Host " =================================================" -ForegroundColor $color
    Write-Host ""
}

function slh-start     { & "D:\SLH_ECOSYSTEM\ops\slh-control.ps1" -Action startall }
function slh-up        { param($Target) & "D:\SLH_ECOSYSTEM\ops\slh-control.ps1" -Action up -Target $Target }
function slh-stop      { param($Target) & "D:\SLH_ECOSYSTEM\ops\slh-control.ps1" -Action stop -Target $Target }
function slh-restart   { param($Target) & "D:\SLH_ECOSYSTEM\ops\slh-control.ps1" -Action restart -Target $Target }
function slh-status    { & "D:\SLH_ECOSYSTEM\ops\slh-control.ps1" -Action status }
function slh-logs      { param($Target,[switch]$Follow) & "D:\SLH_ECOSYSTEM\ops\slh-control.ps1" -Action logs -Target $Target -Follow:$Follow }
function slh-health    { & "D:\SLH_ECOSYSTEM\ops\slh-control.ps1" -Action health }
function slh-build     { param($Target) & "D:\SLH_ECOSYSTEM\ops\slh-control.ps1" -Action build -Target $Target }
function slh-doctor    { & "D:\SLH_ECOSYSTEM\ops\slh-control.ps1" -Action doctor }
function slh-preflight { param($Target="ledger-bot") & "D:\SLH_ECOSYSTEM\ops\slh-preflight.ps1" -Target $Target }
function slh-release   { param($Target="ledger-bot",[switch]$SkipBuild) & "D:\SLH_ECOSYSTEM\ops\slh-release.ps1" -Target $Target -SkipBuild:$SkipBuild }
function slh-cd        { Set-Location "D:\SLH_ECOSYSTEM" }

Write-Host ""
Write-Host " =================================================" -ForegroundColor Cyan
Write-Host "   SLH SPARK SYSTEM | Ready" -ForegroundColor White
Write-Host " =================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " Commands: slh-start, slh-up, slh-stop, slh-restart, slh-status, slh-logs, slh-health, slh-build, slh-doctor, slh-preflight, slh-release, slh-cd" -ForegroundColor DarkGray
Write-Host ""
