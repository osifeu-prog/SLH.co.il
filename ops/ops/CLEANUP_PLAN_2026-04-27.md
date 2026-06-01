# SLH Ecosystem — Cleanup Plan
**Date:** 2026-04-27
**Author:** Claude
**Goal:** Reduce noise, save disk, move backups to a sensible structure WITHOUT losing important data.

---

## TL;DR

Your repo has **3 categories** of cruft:

| Category | What | Action | Risk |
|----------|------|--------|------|
| 🔴 **Recursive backup nesting** | `backups/_restore/.../pre_mainnet/backups/pre_mainnet/...` (10+ levels deep) | DELETE entirely | Zero — these are infinite copies of the same content |
| 🟡 **Project-root backup files** | `*.backup-*`, `*.bak_*`, `.env.backup-*`, `docker-compose.yml.backup-*` (~15 files) | Move to `_backups/2026-04-27-pre-cleanup/` | Low — they're old, but might contain context |
| 🟢 **Useful historical state** | `backups/BACKUPS_old/SLH_Project_20260316_2329/`, `db_backup.sql`, `users_backup.csv` | Keep but compress to a single `.7z` | Low |

**Estimated savings: 200-500 MB** of disk + huge cognitive load reduction.

---

## What I found (concrete)

### 1. Catastrophic recursive nesting (DELETE-SAFE)
The folder `D:\SLH_ECOSYSTEM\backups\_restore\20260322_074442\TerminalCommandCenter\backups\` contains:
```
backups\
  pre_mainnet_20260313_171438\
    backups\
      pre_mainnet_20260313_171438\
        backups\
          pre_mainnet_20260313_171438\
            ...10+ more levels...
              full_copy\
                backups\
                  full_copy\
                    backups\
                      ...even more nesting...
```
Same files (`STATE.md`, `RUNBOOK.md`, `CHANGELOG.md`, `TelegramBot_Core_backup.py`) repeated 8-15 times along the path.

**Safe to delete entirely** — no information is lost. Run:
```powershell
# Estimate size first
Get-ChildItem -Recurse "D:\SLH_ECOSYSTEM\backups\_restore\20260322_074442\TerminalCommandCenter" |
  Measure-Object -Property Length -Sum | Select-Object Sum, Count

# If it's hundreds of MB / thousands of files, delete:
Remove-Item -Recurse -Force "D:\SLH_ECOSYSTEM\backups\_restore\20260322_074442\TerminalCommandCenter"
```

### 2. Old backup files in project root (15 files — CONSOLIDATE)
```
.env.backup-20260416-192749
.env.backup.20260417_004938
.env.bak_20260422_160522
.env.corrupted_20260417_020926
docker-compose.yml.backup-20260416-192200
docker-compose.yml.backup-20260416-220545
docker-compose.yml.backup.20260417_004938
docker-compose.yml.bak-secure-fix
docker-compose.yml.before-fix
docker-compose.yml.regressed-58lines.bak
main.py.bak_20260422_162309
+ 4 .env.* variants
```
**Action**:
```powershell
$archive = "D:\SLH_ECOSYSTEM\_backups\2026-04-27-pre-cleanup"
New-Item -ItemType Directory -Path $archive -Force
Move-Item -Path "D:\SLH_ECOSYSTEM\.env.backup-*" -Destination $archive
Move-Item -Path "D:\SLH_ECOSYSTEM\.env.backup.*" -Destination $archive
Move-Item -Path "D:\SLH_ECOSYSTEM\.env.bak_*" -Destination $archive
Move-Item -Path "D:\SLH_ECOSYSTEM\.env.corrupted_*" -Destination $archive
Move-Item -Path "D:\SLH_ECOSYSTEM\docker-compose.yml.backup*" -Destination $archive
Move-Item -Path "D:\SLH_ECOSYSTEM\docker-compose.yml.bak*" -Destination $archive
Move-Item -Path "D:\SLH_ECOSYSTEM\docker-compose.yml.before-fix" -Destination $archive
Move-Item -Path "D:\SLH_ECOSYSTEM\docker-compose.yml.regressed-58lines.bak" -Destination $archive
Move-Item -Path "D:\SLH_ECOSYSTEM\main.py.bak_*" -Destination $archive
```

### 3. Old website backup files (~15 files — DELETE if current versions look good)
```
website\admin.html.backup_20260425_131059
website\blog-legacy-code.html.backup_20260425_131201
website\blog.html.backup_20260425_131200
website\control-center.html.backup_20260425_131331
website\dashboard.html.backup_20260425_131058
website\healing-vision.html.backup_20260425_131332
website\liquidity.html.backup_20260425_131201
website\member.html.backup_20260425_130658
website\miniapp\dashboard.html.backup_20260425_131058
website\ops-report-20260411.html.backup_20260425_131332
website\promo-shekel.html.backup_20260425_131201
website\roadmap.html.backup_20260425_131332
website\wallet.html.backup_20260425_130658
website\about.html.backup
website\js\shared.js.backup_20260425_220656
website\js\shared.js.backup_20260425_130658
website\js\translations.js.backup_20260425_220659
```
**Action** (after verifying current versions work in browser):
```powershell
Get-ChildItem -Recurse "D:\SLH_ECOSYSTEM\website" -Include "*.backup*", "*.bak_*" |
  Move-Item -Destination "D:\SLH_ECOSYSTEM\_backups\2026-04-27-pre-cleanup\website-backups\"
```

### 4. Old "backtest" scripts in root (8 files — possibly experimental)
```
backtest.py, backtest_full.py, backtest_strategy.py, daily_backtest.py,
dex_backtest.py, full_backtest.py, improved_backtest.py, simple_backtest.py
+ backtest_20260421_140932.csv, backtest_20260421_151442.csv
```
**Question for you:** Are these in active use? If experimental:
```powershell
Move-Item -Path "D:\SLH_ECOSYSTEM\*backtest*" -Destination "D:\SLH_ECOSYSTEM\scripts\experiments\"
```

### 5. Stale top-level files
```
FILES.txt (2.2 MB) — auto-generated file listing, regenerate when needed
GIT_LOG.txt (8 KB), GIT_STATUS.txt (2.5 KB) — git output snapshots
STRUCTURE.txt (2 MB) — auto-generated tree listing
api_project_status_endpoints.py (10 KB) — looks like a one-off audit script
```
**Action**: Move to `ops/snapshots/2026-04-25/`:
```powershell
Move-Item FILES.txt, STRUCTURE.txt, GIT_LOG.txt, GIT_STATUS.txt, api_project_status_endpoints.py `
  -Destination "D:\SLH_ECOSYSTEM\ops\snapshots\2026-04-25\"
```

### 6. The `tonmnh-bot/src/TelegramBot_Core_backup.py` family
```
tonmnh-bot\src\TelegramBot_Core_backup.py
tonmnh-bot\src\TelegramBot_Core_backup.ps1
tonmnh-bot\src\TelegramBot_Core_backup_20260313_165011.py
```
These are inside an active bot folder. **Do not delete** without first checking if they're imported by anything. Run:
```powershell
Select-String -Path "D:\SLH_ECOSYSTEM\tonmnh-bot\*.py" -Pattern "TelegramBot_Core_backup" -SimpleMatch
```
If no matches → safe to move to `_backups/`.

---

## What to keep (the actually useful stuff)

These files contain real historical context. **Keep them but compress**:

```
backups/BACKUPS_old/SLH_Project_20260316_2329/  (the LATEST clean backup before chaos)
  ├── slh_db_backup.sql       ← real DB snapshot, useful
  ├── db_backup.sql            ← another DB snapshot
  ├── users_backup.csv         ← user data, possibly useful for migration
  ├── main_backup_20260305.py  ← old API code
  └── (skip the deeply nested *_backup* duplicates)
```

**Compress to a single archive**:
```powershell
# Requires 7-Zip installed (https://www.7-zip.org/)
& "C:\Program Files\7-Zip\7z.exe" a -t7z `
  "D:\SLH_ECOSYSTEM\_backups\historical-20260316.7z" `
  "D:\SLH_ECOSYSTEM\backups\BACKUPS_old\SLH_Project_20260316_2329\slh_db_backup.sql" `
  "D:\SLH_ECOSYSTEM\backups\BACKUPS_old\SLH_Project_20260316_2329\db_backup.sql" `
  "D:\SLH_ECOSYSTEM\backups\BACKUPS_old\SLH_Project_20260316_2329\users_backup.csv" `
  "D:\SLH_ECOSYSTEM\backups\BACKUPS_old\SLH_Project_20260316_2329\main_backup_20260305.py"

# Then delete the original folder
Remove-Item -Recurse -Force "D:\SLH_ECOSYSTEM\backups\BACKUPS_old"
```

---

## Suggested final folder structure

```
D:\SLH_ECOSYSTEM\
├── api/                    # Production API code
├── website/                # Production website
├── ops/
│   ├── snapshots/          # ← NEW: auto-generated audits land here
│   │   └── 2026-04-25/     # FILES.txt, STRUCTURE.txt etc.
│   ├── SECURITY_FIX_PLAN_*.md
│   ├── SLH_NEURAL_MIGRATION_*.md
│   ├── STRATEGIC_ROADMAP_*.md
│   └── SESSION_HANDOFF_*.md
├── scripts/
│   └── experiments/        # ← NEW: backtest_*.py and other one-offs
├── _backups/               # ← Single source for ALL backups
│   ├── 2026-04-27-pre-cleanup/  # Today's pre-cleanup snapshot
│   └── historical-20260316.7z   # Compressed old backups
├── shared/                 # Shared Python modules
├── *-bot/ (25 dirs)        # Bot codebases
├── docker-compose.yml      # Single canonical version
├── main.py                 # Production root API
├── CLAUDE.md
└── ... (no .bak files anywhere in root!)
```

---

## Safety checklist BEFORE running any cleanup

- [ ] Make a fresh full backup first: `7z a "_backups/pre-cleanup-FULL-20260427.7z" .` (excludes _backups/ and .git/)
- [ ] Confirm git is clean: `cd D:\SLH_ECOSYSTEM && git status` (don't lose uncommitted work)
- [ ] Verify production API is up: `curl https://slhcoil-production.up.railway.app/api/health`
- [ ] Verify Railway has env vars set (if not, leave .env files in place until they are)

---

## Recommended order

1. **Run the SAFETY checklist** (5 min)
2. **Delete recursive nesting** in TerminalCommandCenter — biggest disk win, zero risk (1 min)
3. **Move root backup files** to `_backups/2026-04-27-pre-cleanup/` (1 min)
4. **Move snapshot files** to `ops/snapshots/2026-04-25/` (1 min)
5. **Move backtest scripts** to `scripts/experiments/` (1 min)
6. **Compress historical backups** with 7-Zip (5 min)
7. **Move website backup files** AFTER you visually verify pages still work (10 min — but worth it)
8. **Update `.gitignore`** to prevent future buildup:
   ```
   # Backup files (don't commit)
   *.bak
   *.bak_*
   *.backup
   *.backup-*
   *.backup_*
   *.before-fix
   *.regressed-*
   _backups/
   ```

---

## What I can do for you in the next session

1. Generate an automated PowerShell cleanup script that does steps 2-6 with safety prompts
2. Re-run the audit to show how much disk was reclaimed
3. Suggest additional patterns I missed (after you run this round)
