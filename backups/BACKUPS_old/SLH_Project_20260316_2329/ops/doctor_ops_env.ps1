$ErrorActionPreference = "Stop"

Set-Location (Split-Path $PSScriptRoot -Parent)

function Section([string]$title) {
    Write-Host ""
    Write-Host ("=" * 12 + " " + $title + " " + "=" * 12) -ForegroundColor Cyan
}

function Mask-Value([string]$value) {
    if ([string]::IsNullOrEmpty($value)) { return "" }
    if ($value.Length -le 10) { return $value }
    return $value.Substring(0,4) + "..." + $value.Substring($value.Length-4)
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path (Get-Location) ("state\doctor_ops_env_" + $stamp)
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Section "PROJECT ROOT"
Get-Location | Tee-Object -FilePath (Join-Path $outDir "project_root.txt")

Section "OPS FILES"
Get-ChildItem .\ops -Recurse -File |
    Select-Object FullName, Length, LastWriteTime |
    Format-Table -AutoSize |
    Tee-Object -FilePath (Join-Path $outDir "ops_files.txt")

Section "OPS POWERSHELL FILES"
Get-ChildItem .\ops -Recurse -File -Filter *.ps1 |
    Select-Object FullName |
    Format-Table -AutoSize |
    Tee-Object -FilePath (Join-Path $outDir "ops_ps1_files.txt")

Section "NEW FILES CHECK"

$newFilesLines = @()

if (Test-Path .\ops\switch-bot-token.ps1) {
    Write-Host "--- ops\switch-bot-token.ps1 ---" -ForegroundColor Yellow
    $newFilesLines += "--- ops\switch-bot-token.ps1 ---"
    $content = Get-Content .\ops\switch-bot-token.ps1
    $content | ForEach-Object { $newFilesLines += $_ }
    $content
} else {
    Write-Host "ops\switch-bot-token.ps1 NOT FOUND" -ForegroundColor Red
    $newFilesLines += "ops\switch-bot-token.ps1 NOT FOUND"
}

if (Test-Path .\ops\load-env.ps1) {
    Write-Host "--- ops\load-env.ps1 ---" -ForegroundColor Yellow
    $newFilesLines += "--- ops\load-env.ps1 ---"
    $content = Get-Content .\ops\load-env.ps1
    $content | ForEach-Object { $newFilesLines += $_ }
    $content
} else {
    Write-Host "ops\load-env.ps1 NOT FOUND" -ForegroundColor Red
    $newFilesLines += "ops\load-env.ps1 NOT FOUND"
}

if (Test-Path .\app\core\admin_guard.py) {
    Write-Host "--- app\core\admin_guard.py ---" -ForegroundColor Yellow
    $newFilesLines += "--- app\core\admin_guard.py ---"
    $content = Get-Content .\app\core\admin_guard.py
    $content | ForEach-Object { $newFilesLines += $_ }
    $content
} else {
    Write-Host "app\core\admin_guard.py NOT FOUND" -ForegroundColor Red
    $newFilesLines += "app\core\admin_guard.py NOT FOUND"
}

$newFilesLines | Set-Content -Path (Join-Path $outDir "new_files_check.txt") -Encoding utf8

Section "WORKER KEY LINES"
$workerKeyLines = Select-String -Path .\worker.py -Pattern 'admin_console|admin_console_v2|admin_guard|include_router|BOT_TOKEN|ADMIN_USER_ID|load_dotenv|tail_log' |
ForEach-Object {
    "{0}:{1}: {2}" -f $_.Path, $_.LineNumber, $_.Line.Trim()
}
$workerKeyLines | Tee-Object -FilePath (Join-Path $outDir "worker_key_lines.txt")

Section "WORKER FIRST 140"
Get-Content .\worker.py | Select-Object -First 140 |
    Tee-Object -FilePath (Join-Path $outDir "worker_first_140.txt")

Section "PURCHASES ADMIN KEY LINES"
$purchasesKeyLines = Select-String -Path .\app\services\purchases_admin.py -Pattern 'fraud_guard_payment_ref|external_payment_ref|mark_purchase_order_paid_admin|fulfill_purchase_order_admin|set_system_setting_text_admin' |
ForEach-Object {
    "{0}:{1}: {2}" -f $_.Path, $_.LineNumber, $_.Line.Trim()
}
$purchasesKeyLines | Tee-Object -FilePath (Join-Path $outDir "purchases_admin_key_lines.txt")

Section "PURCHASES ADMIN LAST 160"
Get-Content .\app\services\purchases_admin.py | Select-Object -Last 160 |
    Tee-Object -FilePath (Join-Path $outDir "purchases_admin_last_160.txt")

Section "ENV KEYS ONLY"
$envMasked = @()
if (Test-Path .\.env) {
    Get-Content .\.env | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
        $parts = $_ -split '=', 2
        if ($parts.Count -eq 2) {
            $k = $parts[0].Trim()
            $v = $parts[1]
            $line = "$k=$(Mask-Value $v)"
            $envMasked += $line
        }
    }
} else {
    $envMasked += "ENV FILE NOT FOUND"
}
$envMasked | Tee-Object -FilePath (Join-Path $outDir "env_masked.txt")

Section "GIT STATUS"
git status --short | Tee-Object -FilePath (Join-Path $outDir "git_status.txt")

Section "GIT DIFF TARGETS"
git diff -- .\ops .\app\core .\app\services .\app\handlers .\worker.py |
    Tee-Object -FilePath (Join-Path $outDir "git_diff_targets.txt")

Section "PY COMPILE CRITICAL"
$compileTargets = @(
    ".\worker.py",
    ".\app\core\admin_guard.py",
    ".\app\handlers\admin_console_v2.py",
    ".\app\handlers\ton_admin.py",
    ".\app\handlers\withdrawals.py",
    ".\app\handlers\task_verifications.py",
    ".\app\services\purchases_admin.py"
)

$compileLog = @()
foreach ($target in $compileTargets) {
    if (Test-Path $target) {
        try {
            & .\venv\Scripts\python.exe -m py_compile $target
            $msg = "OK  $target"
            Write-Host $msg -ForegroundColor Green
            $compileLog += $msg
        } catch {
            $msg = "ERR $target :: $($_.Exception.Message)"
            Write-Host $msg -ForegroundColor Red
            $compileLog += $msg
        }
    } else {
        $msg = "MISS $target"
        Write-Host $msg -ForegroundColor Yellow
        $compileLog += $msg
    }
}
$compileLog | Set-Content -Path (Join-Path $outDir "py_compile.txt") -Encoding utf8

Section "STATIC WARNINGS"
$warnings = @()

if (-not (Test-Path .\ops\load-env.ps1)) {
    $warnings += "ops\load-env.ps1 missing"
}

if (Test-Path .\ops\switch-bot-token.ps1) {
    $switchText = Get-Content .\ops\switch-bot-token.ps1 -Raw
    if ($switchText -notmatch 'BOT_TOKEN=\$newToken') {
        $warnings += "switch-bot-token.ps1 may not replace BOT_TOKEN correctly"
    }
    if (
        $switchText -notmatch '\(\?m\)\^BOT_TOKEN=\.\*\$' -and
        $switchText -notmatch 'BOT_TOKEN=\$newToken'
    ) {
        $warnings += "switch-bot-token.ps1 replace pattern not detected"
    }
    if ($switchText -notmatch 'Get-Content \$envPath -Raw') {
        $warnings += "switch-bot-token.ps1 missing raw env read"
    }
    if ($switchText -notmatch 'WriteAllText') {
        $warnings += "switch-bot-token.ps1 missing safe write"
    }
}

if (Test-Path .\app\services\purchases_admin.py) {
    $purchasesText = Get-Content .\app\services\purchases_admin.py -Raw
    if ($purchasesText -match 'async def fraud_guard_payment_ref') {
        if ($purchasesText -notmatch 'fraud_guard_payment_ref\(conn,\s*final_ref\)') {
            $warnings += "fraud_guard_payment_ref exists but is not wired into mark_purchase_order_paid_admin"
        }
    }
}

if (Test-Path .\worker.py) {
    $workerText = Get-Content .\worker.py -Raw
    if ($workerText -notmatch 'from app\.core\.admin_guard import ADMIN_USER_ID, is_admin') {
        $warnings += "worker.py is not importing admin_guard centrally"
    }
    if ($workerText -notmatch 'dp\.include_router\(admin_console_v2_router\)') {
        $warnings += "worker.py is not loading admin_console_v2_router"
    }
}

if ($warnings.Count -eq 0) {
    $warnings += "No obvious static warnings detected"
}

$warnings | Tee-Object -FilePath (Join-Path $outDir "warnings.txt")

Section "SUMMARY"
"Doctor output saved to: $outDir"
"Warnings:"
$warnings | ForEach-Object { " - $_" }

"Doctor output saved to: $outDir" | Set-Content -Path (Join-Path $outDir "SUMMARY.txt") -Encoding utf8
Add-Content -Path (Join-Path $outDir "SUMMARY.txt") -Value ""
Add-Content -Path (Join-Path $outDir "SUMMARY.txt") -Value "Warnings:"
$warnings | ForEach-Object { Add-Content -Path (Join-Path $outDir "SUMMARY.txt") -Value (" - " + $_) }