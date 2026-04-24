# SLH.co.il — one-shot health check
# Usage: pwsh ops\verify.ps1
# Returns 0 if all green, 1 if any red.
# No secret values printed — just masks.

$ErrorActionPreference = 'Stop'
$script:failures = 0
$script:warnings = 0

function Pass($msg) { Write-Host "  PASS  $msg" -ForegroundColor Green }
function Fail($msg) { Write-Host "  FAIL  $msg" -ForegroundColor Red; $script:failures++ }
function Warn($msg) { Write-Host "  WARN  $msg" -ForegroundColor Yellow; $script:warnings++ }
function Section($title) { Write-Host ""; Write-Host "== $title ==" -ForegroundColor Cyan }

Section "[1] Railway CLI"
try {
    $status = railway status 2>&1 | Select-String -Pattern 'Project:\s+(\S+)'
    if ($status) { Pass "Railway linked: $($status.Matches[0].Groups[1].Value)" }
    else { Fail "Railway not linked. Run: railway link" }
} catch { Fail "railway command not found. Install: npm i -g @railway/cli" }

Section "[2] Token validity (getMe)"
$tokenCheck = @'
import os, json, urllib.request, urllib.error, sys
t = os.getenv('TELEGRAM_BOT_TOKEN','')
if not t:
    print('NO_TOKEN'); sys.exit(1)
try:
    r = urllib.request.urlopen(f'https://api.telegram.org/bot{t}/getMe', timeout=10)
    b = json.loads(r.read())
    if b.get('ok'): print(f"OK:{b['result'].get('username')}")
    else: print(f"FAIL:{b.get('description')}"); sys.exit(2)
except urllib.error.HTTPError as e:
    print(f"HTTP{e.code}"); sys.exit(2)
'@
try {
    $tokenCheck | Out-File -Encoding utf8 -FilePath "$env:TEMP\_slh_tokencheck.py"
    $tokenResult = railway run python "$env:TEMP\_slh_tokencheck.py" 2>&1
    Remove-Item "$env:TEMP\_slh_tokencheck.py" -ErrorAction SilentlyContinue
    $lastLine = ($tokenResult -split "`n")[-1].Trim()
    if ($lastLine -match '^OK:(.+)$') { Pass "getMe returned @$($matches[1])" }
    elseif ($lastLine -match 'HTTP401') { Fail "Token is 401 Unauthorized — rotate or update Railway env" }
    else { Fail "getMe: $lastLine" }
} catch { Fail "token check: $_" }

Section "[3] Database connectivity"
$dbCheck = @'
import os, psycopg2
try:
    c = psycopg2.connect(os.getenv('DATABASE_URL')).cursor()
    c.execute("SELECT COUNT(*) FROM users")
    u = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM preorders")
    p = c.fetchone()[0]
    print(f"OK:users={u},preorders={p}")
except Exception as e:
    print(f"FAIL:{e}")
'@
try {
    $dbCheck | Out-File -Encoding utf8 -FilePath "$env:TEMP\_slh_dbcheck.py"
    $dbResult = railway run python "$env:TEMP\_slh_dbcheck.py" 2>&1
    Remove-Item "$env:TEMP\_slh_dbcheck.py" -ErrorAction SilentlyContinue
    $lastLine = ($dbResult -split "`n")[-1].Trim()
    if ($lastLine -match '^OK:(.+)$') { Pass "DB reachable — $($matches[1])" }
    else { Fail "DB: $lastLine" }
} catch { Fail "db check: $_" }

Section "[4] Website reachability"
foreach ($url in @('https://www.slh.co.il/', 'https://www.slh.co.il/guardian.html')) {
    try {
        $r = Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing -TimeoutSec 10
        if ($r.StatusCode -eq 200) { Pass "$url $(($r.StatusCode))" }
        else { Fail "$url returned $($r.StatusCode)" }
    } catch { Fail "$url unreachable: $($_.Exception.Message.Split("`n")[0])" }
}

Section "[5] Recent 409 Conflicts in logs"
try {
    $logs = railway logs 2>&1 | Select-Object -Last 50
    $conflicts = ($logs | Select-String -Pattern '409 Conflict').Count
    if ($conflicts -eq 0) { Pass "0 conflicts in last 50 log lines" }
    elseif ($conflicts -lt 5) { Warn "$conflicts conflicts in last 50 lines (low)" }
    else { Fail "$conflicts conflicts in last 50 lines — another bot instance running" }
} catch { Warn "could not pull logs: $_" }

Section "Summary"
if ($failures -eq 0 -and $warnings -eq 0) {
    Write-Host "ALL GREEN" -ForegroundColor Green
    exit 0
} elseif ($failures -eq 0) {
    Write-Host "GREEN with $warnings warning(s)" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "$failures failure(s), $warnings warning(s)" -ForegroundColor Red
    exit 1
}
