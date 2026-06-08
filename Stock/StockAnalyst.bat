@echo off
title Stock Analyst
setlocal enabledelayedexpansion

set "BACKEND_DIR=C:\AI-Agent-Local\Stock\backend"
set "FRONTEND_DIR=C:\AI-Agent-Local\Stock\frontend"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=3456"
set "LOG_DIR=C:\AI-Agent-Local\Stock\logs"

echo.
echo  ========================================
echo    Stock Analyst Launcher
echo  ========================================
echo.

REM === Kill stale ===
echo  [0] Cleaning...
taskkill /F /IM node.exe >NUL 2>&1
taskkill /F /IM python.exe >NUL 2>&1
timeout /t 2 /nobreak >NUL
echo       Done

REM === PostgreSQL ===
echo  [1] PostgreSQL...
docker ps --filter "name=stock-postgres" --format "{{.Names}}" 2>NUL | findstr "stock-postgres" >NUL 2>&1
if errorlevel 1 (
    echo       Starting stock-postgres...
    docker start stock-postgres >NUL 2>&1
    if errorlevel 1 (
        echo       [ERROR] Docker not running
        pause
        exit /b 1
    )
    timeout /t 5 /nobreak >NUL
)
echo       Ready

REM === Backend ===
echo  [2] Backend...
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

start /b "" cmd /c "cd /d %BACKEND_DIR% && python -B -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT% > %LOG_DIR%\backend.log 2>&1"

echo       Waiting...
set /a n=0
:wait_be
    timeout /t 2 /nobreak >NUL 2>&1
    powershell -NoProfile -Command "try{$r=Invoke-WebRequest -Uri http://127.0.0.1:%BACKEND_PORT%/api/health -UseBasicParsing -TimeoutSec 10;if($r.StatusCode -eq 200){exit 0}}catch{exit 1}" >NUL 2>&1
    if not errorlevel 1 goto be_ready
    set /a n+=1
    if !n! lss 20 goto wait_be
    echo       [WARN] Backend timeout
    goto backend_done
:be_ready
echo       Backend ready
:backend_done

REM === Frontend ===
echo  [3] Frontend :%FRONTEND_PORT%...

if not exist "%FRONTEND_DIR%\node_modules" (
    echo       Installing deps...
    cd /d "%FRONTEND_DIR%" && call npm install
)

start /b "" cmd /c "cd /d %FRONTEND_DIR% && npx vite --port %FRONTEND_PORT% --host 127.0.0.1 --no-open > %LOG_DIR%\frontend.log 2>&1"

echo       Waiting...
set /a n=0
:wait_fe
    timeout /t 2 /nobreak >NUL 2>&1
    powershell -NoProfile -Command "try{$r=Invoke-WebRequest -Uri http://127.0.0.1:%FRONTEND_PORT% -UseBasicParsing -TimeoutSec 5;if($r.StatusCode -eq 200){exit 0}}catch{exit 1}" >NUL 2>&1
    if not errorlevel 1 goto fe_ready
    set /a n+=1
    if !n! lss 15 goto wait_fe
    echo       [WARN] Frontend timeout - check %LOG_DIR%\frontend.log
    goto open_browser
:fe_ready
echo       Frontend ready

REM === Browser ===
:open_browser
echo  [4] Opening browser...
start http://127.0.0.1:%FRONTEND_PORT%

echo.
echo  ========================================
echo    Stock Analyst Running
echo    Frontend : http://127.0.0.1:%FRONTEND_PORT%
echo    Backend  : http://127.0.0.1:8000/api
echo  ========================================
echo.
echo    Press any key to stop...
pause >NUL

echo    Stopping...
taskkill /F /IM node.exe >NUL 2>&1
taskkill /F /IM python.exe >NUL 2>&1
echo    Done.
timeout /t 2 /nobreak >NUL
