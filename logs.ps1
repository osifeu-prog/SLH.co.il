# SLH ECOSYSTEM - View logs
param(
    [string]$Service = "",
    [int]$Tail = 50
)
Set-Location $PSScriptRoot

if ($Service) {
    docker compose logs --tail $Tail -f $Service
} else {
    docker compose logs --tail $Tail -f
}
