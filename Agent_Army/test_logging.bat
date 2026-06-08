@echo off
REM ==========================================
REM 日志系统测试脚本
REM ==========================================

echo.
echo ========================================
echo   Logging System Test
echo ========================================
echo.

cd /d "%~dp0"

echo [STEP 1] Killing existing processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo [STEP 2] Clearing old logs...
if exist "logs\agent-army.log" del /f /q "logs\agent-army.log" 2>nul
if exist "logs\error.log" del /f /q "logs\error.log" 2>nul

echo [STEP 3] Starting Dashboard with logging...
echo.
echo ========================================
echo   Dashboard Starting...
echo   URL: http://localhost:8501
echo.
echo   IMPORTANT:
echo   1. Open browser to http://localhost:8501
echo   2. Press Ctrl+Shift+R to refresh
echo   3. Go to Investment Analysis
echo   4. Enter stock: 601669
echo   5. Click Start Analysis
echo   6. Watch logs below...
echo ========================================
echo.

timeout /t 3 /nobreak >nul

REM 启动Dashboard（后台）
start /min python -m streamlit run web_app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false --server.fileWatcherType none

echo.
echo [STEP 4] Waiting for logs...
timeout /t 5 /nobreak >nul

echo.
echo [STEP 5] Viewing real-time logs...
echo Press Ctrl+C to stop
echo.

REM 实时显示日志
:Get-Content logs\agent-army.log -Wait 2>nul || (
    echo Waiting for log file to be created...
    timeout /t 10 /nobreak >nul
    Get-Content logs\agent-army.log -Wait
)

pause
