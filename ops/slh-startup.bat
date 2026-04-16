@echo off
REM ============================================================
REM SLH ECOSYSTEM - Auto Startup Script
REM Run after system reboot to bring everything online
REM Place shortcut in: shell:startup (Win+R -> shell:startup)
REM ============================================================

title SLH Ecosystem Startup
echo ============================================================
echo  SLH ECOSYSTEM - System Startup
echo  %date% %time%
echo ============================================================

REM --- Log startup ---
set LOGDIR=D:\SLH_ECOSYSTEM\ops\logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set LOGFILE=%LOGDIR%\startup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log
echo [%date% %time%] === SYSTEM STARTUP BEGIN === >> "%LOGFILE%"

REM --- Step 1: Wait for Docker Desktop ---
echo.
echo [1/5] Waiting for Docker Desktop...
echo [%date% %time%] Waiting for Docker Desktop >> "%LOGFILE%"

REM Check if Docker Desktop is running, if not start it
tasklist /FI "IMAGENAME eq Docker Desktop.exe" 2>NUL | find /I "Docker Desktop.exe" >NUL
if errorlevel 1 (
    echo       Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo [%date% %time%] Docker Desktop started manually >> "%LOGFILE%"
) else (
    echo       Docker Desktop already running.
    echo [%date% %time%] Docker Desktop already running >> "%LOGFILE%"
)

REM Wait for docker daemon to be ready (max 120 seconds)
set /a count=0
:docker_wait
docker info >NUL 2>&1
if errorlevel 1 (
    set /a count+=1
    if %count% GEQ 24 (
        echo       ERROR: Docker not ready after 120 seconds!
        echo [%date% %time%] ERROR: Docker timeout >> "%LOGFILE%"
        goto docker_failed
    )
    echo       Waiting for Docker daemon... (%count%/24)
    timeout /t 5 /nobreak >NUL
    goto docker_wait
)
echo       Docker is ready!
echo [%date% %time%] Docker daemon ready >> "%LOGFILE%"

REM --- Step 2: Start Docker Compose services ---
echo.
echo [2/5] Starting Docker Compose services...
echo [%date% %time%] Starting Docker Compose >> "%LOGFILE%"
cd /d D:\SLH_ECOSYSTEM
docker compose up -d >> "%LOGFILE%" 2>&1
echo [%date% %time%] Docker Compose started >> "%LOGFILE%"

REM --- Step 3: Wait for PostgreSQL health ---
echo.
echo [3/5] Waiting for PostgreSQL...
set /a count=0
:pg_wait
docker exec slh-postgres pg_isready -U postgres >NUL 2>&1
if errorlevel 1 (
    set /a count+=1
    if %count% GEQ 12 (
        echo       WARNING: PostgreSQL not ready after 60 seconds
        echo [%date% %time%] WARNING: PostgreSQL timeout >> "%LOGFILE%"
        goto pg_done
    )
    timeout /t 5 /nobreak >NUL
    goto pg_wait
)
:pg_done
echo       PostgreSQL is healthy!
echo [%date% %time%] PostgreSQL ready >> "%LOGFILE%"

REM --- Step 4: Verify services ---
echo.
echo [4/5] Verifying services...
echo [%date% %time%] Verifying services >> "%LOGFILE%"
docker ps --format "{{.Names}}: {{.Status}}" >> "%LOGFILE%" 2>&1
for /f %%i in ('docker ps -q ^| find /c /v ""') do set RUNNING=%%i
echo       %RUNNING% containers running
echo [%date% %time%] %RUNNING% containers running >> "%LOGFILE%"

REM --- Step 5: Health check Railway API ---
echo.
echo [5/5] Checking Railway API...
curl.exe -s -o NUL -w "%%{http_code}" https://slh-api-production.up.railway.app/api/health > "%TEMP%\slh_api_check.txt" 2>&1
set /p API_STATUS=<"%TEMP%\slh_api_check.txt"
if "%API_STATUS%"=="200" (
    echo       Railway API: OK
    echo [%date% %time%] Railway API: OK >> "%LOGFILE%"
) else (
    echo       Railway API: Status %API_STATUS% (may need a few minutes)
    echo [%date% %time%] Railway API: Status %API_STATUS% >> "%LOGFILE%"
)

echo.
echo ============================================================
echo  STARTUP COMPLETE - %date% %time%
echo  Log saved to: %LOGFILE%
echo ============================================================
echo [%date% %time%] === STARTUP COMPLETE === >> "%LOGFILE%"
echo.
echo Press any key to close this window...
pause >NUL
goto :eof

:docker_failed
echo.
echo ============================================================
echo  STARTUP FAILED - Docker not available
echo  Try starting Docker Desktop manually
echo ============================================================
echo [%date% %time%] === STARTUP FAILED === >> "%LOGFILE%"
pause
