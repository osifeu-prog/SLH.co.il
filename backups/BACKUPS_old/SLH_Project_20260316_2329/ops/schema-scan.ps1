Set-Location D:\SLH_PROJECT_V2
$ErrorActionPreference = "Stop"

$out = New-Object System.Collections.Generic.List[string]

$out.Add("=== DB TABLES ===")
$tables = docker exec slhb_postgres psql -U slh_user -d slh_database -P pager=off -c "\dt public.*" 2>&1
$out.Add(($tables | Out-String))

$out.Add("=== USERS DDL LIVE ===")
$users = docker exec slhb_postgres psql -U slh_user -d slh_database -P pager=off -c "\d+ public.users" 2>&1
$out.Add(($users | Out-String))

$out.Add("=== SCHEMA CANDIDATES ===")
$targets = @('users','system_settings','products','product_groups','purchase_orders')

$rows = Get-ChildItem -Recurse -File |
Where-Object {
  $_.FullName -notmatch '\\.git(\\|$)' -and
  $_.FullName -notmatch '\\venv(\\|$)' -and
  $_.FullName -notmatch '\\__pycache__(\\|$)' -and
  $_.Extension -in '.sql','.py','.md','.txt'
} |
ForEach-Object {
  $path = $_.FullName
  $raw = Get-Content $path -Raw -ErrorAction SilentlyContinue
  if ($null -eq $raw) { return }

  $score = 0
  foreach ($t in $targets) {
    if ($raw -match "(?is)\bCREATE\s+TABLE\b[^(;)]*\b$t\b") { $score++ }
  }

  if ($score -gt 0) {
    [PSCustomObject]@{
      Score = $score
      Path  = $path
    }
  }
} |
Sort-Object -Property @{Expression='Score';Descending=$true}, @{Expression='Path';Descending=$false} |
Format-Table -AutoSize | Out-String

$out.Add($rows)

$report = $out -join "`n"
$reportPath = "state\schema_scan_report.txt"
$enc = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path (Get-Location) $reportPath), ($report -replace "`r`n","`n"), $enc)
Write-Host "REPORT WRITTEN: $reportPath" -ForegroundColor Green
Get-Content $reportPath -Raw