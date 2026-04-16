@echo off
REM ============================================================
REM SLH ECOSYSTEM - Backup Script
REM Creates timestamped backup of all critical files
REM ============================================================

title SLH Backup
echo ============================================================
echo  SLH ECOSYSTEM - System Backup
echo  %date% %time%
echo ============================================================

REM --- Setup ---
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_ROOT=D:\SLH_BACKUPS
set BACKUP_DIR=%BACKUP_ROOT%\backup_%TIMESTAMP%

if not exist "%BACKUP_ROOT%" mkdir "%BACKUP_ROOT%"
mkdir "%BACKUP_DIR%"
mkdir "%BACKUP_DIR%\ecosystem"
mkdir "%BACKUP_DIR%\bots"
mkdir "%BACKUP_DIR%\database"
mkdir "%BACKUP_DIR%\guardian"

echo.
echo Backup directory: %BACKUP_DIR%
echo.

REM --- Step 1: Backup ops folder (documentation) ---
echo [1/6] Backing up ops documentation...
xcopy /E /I /Y "D:\SLH_ECOSYSTEM\ops" "%BACKUP_DIR%\ecosystem\ops" >NUL 2>&1
echo       Done.

REM --- Step 2: Backup API ---
echo [2/6] Backing up API...
xcopy /E /I /Y "D:\SLH_ECOSYSTEM\api" "%BACKUP_DIR%\ecosystem\api" >NUL 2>&1
echo       Done.

REM --- Step 3: Backup website ---
echo [3/6] Backing up website...
xcopy /E /I /Y "D:\SLH_ECOSYSTEM\website" "%BACKUP_DIR%\ecosystem\website" >NUL 2>&1
echo       Done.

REM --- Step 4: Backup Docker configs ---
echo [4/6] Backing up Docker configs...
copy /Y "D:\SLH_ECOSYSTEM\docker-compose.yml" "%BACKUP_DIR%\ecosystem\" >NUL 2>&1
copy /Y "D:\SLH_ECOSYSTEM\.env" "%BACKUP_DIR%\ecosystem\" >NUL 2>&1
xcopy /E /I /Y "D:\SLH_ECOSYSTEM\dockerfiles" "%BACKUP_DIR%\ecosystem\dockerfiles" >NUL 2>&1
echo       Done.

REM --- Step 5: Backup NFTY bot ---
echo [5/6] Backing up NFTY Bot...
xcopy /E /I /Y "D:\SLH_BOTS\handlers" "%BACKUP_DIR%\bots\handlers" >NUL 2>&1
copy /Y "D:\SLH_BOTS\run_tamagotchi_advanced.py" "%BACKUP_DIR%\bots\" >NUL 2>&1
if exist "D:\SLH_BOTS\tamagotchi.db" copy /Y "D:\SLH_BOTS\tamagotchi.db" "%BACKUP_DIR%\bots\" >NUL 2>&1
echo       Done.

REM --- Step 6: PostgreSQL database dump ---
echo [6/6] Dumping PostgreSQL database...
docker exec slh-postgres pg_dump -U postgres slh_main > "%BACKUP_DIR%\database\slh_main_%TIMESTAMP%.sql" 2>NUL
if errorlevel 1 (
    echo       WARNING: Database dump failed (is PostgreSQL running?)
) else (
    echo       Done.
)

REM --- Summary ---
echo.
echo ============================================================
echo  BACKUP COMPLETE
echo  Location: %BACKUP_DIR%
echo
echo  Contents:
echo    ecosystem\ops\     - Project documentation
echo    ecosystem\api\     - FastAPI backend
echo    ecosystem\website\ - GitHub Pages site
echo    ecosystem\         - Docker configs
echo    bots\              - NFTY Bot (handlers + DB)
echo    database\          - PostgreSQL dump
echo ============================================================
echo.

REM --- Cleanup old backups (keep last 10) ---
set /a keep=0
for /f "skip=10 delims=" %%d in ('dir /B /O-D "%BACKUP_ROOT%\backup_*" 2^>NUL') do (
    echo Cleaning old backup: %%d
    rmdir /S /Q "%BACKUP_ROOT%\%%d" >NUL 2>&1
)

echo Press any key to close...
pause >NUL
