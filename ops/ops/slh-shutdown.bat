@echo off
REM ============================================================
REM SLH ECOSYSTEM - Clean Shutdown Script
REM Run before shutting down / rebooting the computer
REM ============================================================

title SLH Clean Shutdown
echo ============================================================
echo  SLH ECOSYSTEM - Clean Shutdown
echo  %date% %time%
echo ============================================================

set LOGDIR=D:\SLH_ECOSYSTEM\ops\logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set LOGFILE=%LOGDIR%\shutdown_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log

echo [%date% %time%] === CLEAN SHUTDOWN BEGIN === >> "%LOGFILE%"

REM --- Step 1: Log current state ---
echo.
echo [1/4] Logging current state...
echo [%date% %time%] Container states: >> "%LOGFILE%"
docker ps --format "{{.Names}}: {{.Status}}" >> "%LOGFILE%" 2>&1

REM --- Step 2: Quick PostgreSQL backup ---
echo [2/4] Quick database backup...
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%
docker exec slh-postgres pg_dump -U postgres slh_main > "%LOGDIR%\db_shutdown_%TIMESTAMP%.sql" 2>NUL
if errorlevel 1 (
    echo       Database backup skipped (not critical)
    echo [%date% %time%] DB backup skipped >> "%LOGFILE%"
) else (
    echo       Database backed up.
    echo [%date% %time%] DB backed up to db_shutdown_%TIMESTAMP%.sql >> "%LOGFILE%"
)

REM --- Step 3: Stop Docker Compose gracefully ---
echo [3/4] Stopping Docker services gracefully...
echo [%date% %time%] Stopping Docker Compose >> "%LOGFILE%"
cd /d D:\SLH_ECOSYSTEM
docker compose stop >> "%LOGFILE%" 2>&1
echo [%date% %time%] Docker Compose stopped >> "%LOGFILE%"
echo       Services stopped.

REM --- Step 4: Verify all stopped ---
echo [4/4] Verifying...
for /f %%i in ('docker ps -q ^| find /c /v ""') do set RUNNING=%%i
echo       %RUNNING% containers still running
echo [%date% %time%] %RUNNING% containers remaining >> "%LOGFILE%"

echo.
echo ============================================================
echo  SHUTDOWN COMPLETE - Safe to power off
echo  Log: %LOGFILE%
echo ============================================================
echo [%date% %time%] === SHUTDOWN COMPLETE === >> "%LOGFILE%"
echo.
echo Press any key to close...
pause >NUL
