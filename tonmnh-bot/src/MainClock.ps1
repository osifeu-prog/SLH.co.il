$ascii = @{'0'=@("  ","   ","   ","   ","  "); '1'=@("    ","   ","    ","    ","  "); '2'=@("  ","    ","  ","    ","  "); '3'=@("  ","    ","  ","    ","  "); '4'=@("   ","   "," ","    ","    "); '5'=@(" ","    ","  ","    ","  "); '6'=@("  ","    "," ","   ","  "); '7'=@(" ","    ","    ","    ","    "); '8'=@("  ","   ","  ","   ","  "); '9'=@("  ","   "," ","    ","  "); ':'=@("   ","  ","   ","  ","   ")}
$todoPath = "D:\TerminalCommandCenter\TODO.md"

# פונקציה למשיכת המשימה הבאה בבטחה
function Get-NextTask {
    if (Test-Path $todoPath) {
        $line = Get-Content $todoPath | Where-Object { $_ -match "- \[ \]" } | Select-Object -First 1
        if ($line) { return ($line -replace "- \[ \] ", "").Trim() }
    }
    return "System Idle"
}

$task = Get-NextTask
$start = [DateTime]::Now; $base = New-TimeSpan; $running = $true; $mode = "WORK"

try {
    while($true) {
        if ($Host.UI.RawUI.KeyAvailable) {
            $k = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown"); $c = $k.Character.ToString().ToLower()
            if ($c -eq 'q') { break }
            if ($c -eq 'p') {
                if($running){ $base += ([DateTime]::Now - $start); $running = $false }
                else { $start = [DateTime]::Now; $running = $true }
            }
        }
        
        [Console]::SetCursorPosition(0, 0)
        $ts = $base + (if($running){[DateTime]::Now - $start}else{New-TimeSpan})
        $timeStr = "{0:D2}:{1:D2}:{2:D2}" -f [int]$ts.TotalHours, $ts.Minutes, $ts.Seconds
        
        Write-Host "`n  [ ACTIVE: $task ] " -Fore Cyan
        Write-Host "  STATUS: $(if($running){'RUNNING'}else{'PAUSED'})" -Fore (if($running){"Green"}else{"Yellow"})
        Write-Host "  " + ("-" * 45) -Fore Gray
        
        for($i=0; $i -lt 5; $i++) {
            Write-Host "  " -NoNewline
            foreach($char in $timeStr.ToCharArray()){
                Write-Host $ascii[[string]$char][$i] -NoNewline -Fore (if($running){"Green"}else{"Gray"})
                Write-Host " " -NoNewline
            }
            Write-Host ""
        }
        Write-Host "  " + ("-" * 45) -Fore Gray
        Write-Host "  [P] Pause | [Q] Exit" -Fore Gray
        Start-Sleep -Milliseconds 250
    }
} finally { Stop-Process -Id $PID }
