@echo off
title Stock Analyst
setlocal

set BACKEND_DIR=C:\AI-Agent-Local\Stock\backend
set FRONTEND_DIR=C:\AI-Agent-Local\Stock\frontend
set BACKEND_PORT=8000
set FRONTEND_PORT=5173
set LOG_DIR=C:\AI-Agent-Local\Stock\logs

REM Workers config (default: 4 workers for parallel TG scan)
set NUM_WORKERS=%1
if "%NUM_WORKERS%"=="" set NUM_WORKERS=4
set SKIP_DOWNLOAD=%2

echo.
echo ========================================
echo   Stock Analyst Launcher (v4.9)
echo   Workers: %NUM_WORKERS%
echo ========================================
echo.

REM Kill stale (强化版: 端口 + 标题 + 兜底, 不误杀其他 python/node)
echo  [0] Cleaning...
REM 1. 按端口精准杀 (8000=uvicorn, 5173=vite)
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (
    taskkill /F /PID %%P >NUL 2>&1
)
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5173.*LISTENING"') do (
    taskkill /F /PID %%P >NUL 2>&1
)
REM 2. 按窗口标题精准杀 (本 bat 启动的窗口)
taskkill /F /FI "WINDOWTITLE eq StockAnalyst-Backend*" >NUL 2>&1
taskkill /F /FI "WINDOWTITLE eq StockAnalyst-Frontend*" >NUL 2>&1
ping -n 3 127.0.0.1 >NUL
echo       Done

REM PostgreSQL
echo  [1] PostgreSQL...
docker start stock-postgres >NUL 2>&1
ping -n 4 127.0.0.1 >NUL
echo       Ready

REM Backend: single process + ProcessPoolExecutor workers
echo  [2] Backend (workers=%NUM_WORKERS%)...
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set UVI_CMD=python -B -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%
REM NOTE: NUM_WORKERS controls ProcessPoolExecutor, NOT uvicorn workers
REM /MIN 最小化窗口 + 标题"StockAnalyst-Backend" 便于精准清理, 且独立窗口不抢 bat 的 stdin (修复 pause 失效)

start "StockAnalyst-Backend" /MIN cmd /c "cd /d %BACKEND_DIR% && set NUM_WORKERS=%NUM_WORKERS% && %UVI_CMD% > %LOG_DIR%\backend.log 2>&1"

echo       Waiting...
for /l %%n in (1,1,30) do (
    curl -s http://127.0.0.1:%BACKEND_PORT%/api/health >NUL 2>&1
    if !errorlevel!==0 goto be_ready
    ping -n 2 127.0.0.1 >NUL
)
echo       [WARN] Backend timeout
goto backend_done

:be_ready
echo       Backend ready

:backend_done
REM Frontend
echo  [3] Frontend :%FRONTEND_PORT%...

if not exist "%FRONTEND_DIR%\node_modules" (
    echo       Installing deps...
    cd /d "%FRONTEND_DIR%" && call npm install
)

REM /MIN 最小化窗口 + 标题"StockAnalyst-Frontend" 便于精准清理, 独立窗口不抢 stdin

start "StockAnalyst-Frontend" /MIN cmd /c "cd /d %FRONTEND_DIR% && npx vite --port %FRONTEND_PORT% --host 127.0.0.1 --no-open > %LOG_DIR%\frontend.log 2>&1"

echo       Waiting...
for /l %%n in (1,1,15) do (
    curl -s http://127.0.0.1:%FRONTEND_PORT% >NUL 2>&1
    if !errorlevel!==0 goto fe_ready
    ping -n 2 127.0.0.1 >NUL
)
echo       [WARN] Frontend timeout
goto open_browser

:fe_ready
echo       Frontend ready

:open_browser
echo  [4] Opening browser...
start http://127.0.0.1:%FRONTEND_PORT%

echo.
echo ========================================
echo   Stock Analyst Running
echo   Frontend : http://127.0.0.1:%FRONTEND_PORT%
echo   Backend  : http://127.0.0.1:8000/api
echo ========================================
echo.
echo   Press any key to stop...
pause >NUL

echo   Stopping services...

REM 1. 按端口精准杀 (不误杀其他 python/node 进程)
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (
    taskkill /F /PID %%P >NUL 2>&1
)
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5173.*LISTENING"') do (
    taskkill /F /PID %%P >NUL 2>&1
)

REM 2. 给子进程 1 秒自然退出 (ProcessPoolExecutor worker 清理 pool)
ping -n 2 127.0.0.1 >NUL

REM 3. 按窗口标题精准杀 (本 bat 启动的最小化窗口)
taskkill /F /FI "WINDOWTITLE eq StockAnalyst-Backend*" >NUL 2>&1
taskkill /F /FI "WINDOWTITLE eq StockAnalyst-Frontend*" >NUL 2>&1

REM 4. 兜底: 镜像名扫射 (仅前 3 步失败时执行, postgres 在 docker 容器内安全不受影响)
taskkill /F /IM node.exe >NUL 2>&1
taskkill /F /IM python.exe >NUL 2>&1

REM 5. 验证端口已释放
netstat -ano | findstr ":8000.*LISTENING" >NUL 2>&1 && echo       [WARN] port 8000 still in use
netstat -ano | findstr ":5173.*LISTENING" >NUL 2>&1 && echo       [WARN] port 5173 still in use

echo   Done.