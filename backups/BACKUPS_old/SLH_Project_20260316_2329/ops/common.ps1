$Script:ProjectRoot = Split-Path $PSScriptRoot -Parent
$Script:StateDir    = Join-Path $ProjectRoot "state"
$Script:LogsDir     = Join-Path $ProjectRoot "logs"
$Script:PidFile     = Join-Path $StateDir "STACK_STATE.json"

function Ensure-Dirs {
    New-Item -ItemType Directory -Force -Path $StateDir, $LogsDir | Out-Null
}

function Read-State {
    Ensure-Dirs
    if (Test-Path $PidFile) {
        try { return Get-Content $PidFile -Raw | ConvertFrom-Json }
        catch { return [pscustomobject]@{} }
    }
    return [pscustomobject]@{}
}

function Write-State([hashtable]$obj) {
    Ensure-Dirs
    ($obj | ConvertTo-Json -Depth 6) | Set-Content -Path $PidFile -Encoding utf8
}

function Set-StateValue([string]$key, $value) {
    $state = @{}
    $old = Read-State
    if ($old) {
        $old.psobject.Properties | ForEach-Object { $state[$_.Name] = $_.Value }
    }
    $state[$key] = $value
    Write-State $state
}

function Remove-StateValue([string]$key) {
    $state = @{}
    $old = Read-State
    if ($old) {
        $old.psobject.Properties | ForEach-Object { $state[$_.Name] = $_.Value }
    }
    if ($state.ContainsKey($key)) { $state.Remove($key) }
    Write-State $state
}

function Test-ProcessAlive([int]$procId) {
    try {
        $p = Get-Process -Id $procId -ErrorAction Stop
        return $null -ne $p
    } catch {
        return $false
    }
}

function Get-PythonExe {
    $venvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"
    if (Test-Path $venvPython) { return $venvPython }
    throw "venv python not found at $venvPython"
}

function Test-TcpPort([int]$Port) {
    try {
        $c = Get-NetTCPConnection -LocalPort $Port -ErrorAction Stop
        return ($c | Measure-Object).Count -gt 0
    } catch {
        return $false
    }
}

function Get-EnvMap {
    $envFile = Join-Path $ProjectRoot ".env"
    $map = @{}
    if (Test-Path $envFile) {
        foreach ($line in Get-Content $envFile) {
            if ($line -match '^\s*#') { continue }
            if ($line -match '^\s*$') { continue }
            if ($line -match '^\s*([^=]+?)\s*=\s*(.*)\s*$') {
                $map[$matches[1]] = $matches[2]
            }
        }
    }
    return $map
}

function Get-RedisUrl {
    $envMap = Get-EnvMap
    if ($envMap.ContainsKey("REDIS_URL")) { return $envMap["REDIS_URL"] }
    return "redis://127.0.0.1:6380/0"
}

function Show-Section([string]$title) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor DarkGray
    Write-Host $title -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor DarkGray
}

function Start-BackgroundPowerShell([string]$Title, [string]$Command, [string]$LogPath) {
    $wrapped = @"
`$Host.UI.RawUI.WindowTitle = '$Title'
Set-Location '$ProjectRoot'
$Command 2>&1 | Tee-Object -FilePath '$LogPath' -Append
"@
    $p = Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", $wrapped
    ) -PassThru
    return $p.Id
}

function Invoke-ExternalCommand {
    param(
        [string]$FilePath,
        [string]$Arguments,
        [int]$TimeoutMs = 4000
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = $Arguments
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi

    [void]$p.Start()

    if (-not $p.WaitForExit($TimeoutMs)) {
        try { $p.Kill() } catch {}
        return [pscustomobject]@{
            TimedOut = $true
            ExitCode = -1
            StdOut   = ""
            StdErr   = "timeout"
        }
    }

    return [pscustomobject]@{
        TimedOut = $false
        ExitCode = $p.ExitCode
        StdOut   = $p.StandardOutput.ReadToEnd()
        StdErr   = $p.StandardError.ReadToEnd()
    }
}

function Get-DockerExe {
    $cmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }
    return "docker"
}

function Test-DockerResponsive {
    $dockerExe = Get-DockerExe
    $r = Invoke-ExternalCommand -FilePath $dockerExe -Arguments 'ps --format "{{.ID}}"' -TimeoutMs 4000
    return (-not $r.TimedOut -and $r.ExitCode -eq 0)
}

function Invoke-Docker {
    param(
        [string]$Arguments,
        [int]$TimeoutMs = 5000
    )
    $dockerExe = Get-DockerExe
    return Invoke-ExternalCommand -FilePath $dockerExe -Arguments $Arguments -TimeoutMs $TimeoutMs
}
function Check-DB {
    try {
        if ($env:DATABASE_URL -and $env:DATABASE_URL.Trim().Length -gt 0) { return "CONFIGURED" }
        if ($env:DB_HOST -and $env:DB_HOST.Trim().Length -gt 0) { return "CONFIGURED" }
        return "NOT CONFIGURED"
    }
    catch {
        return "ERROR"
    }
}
