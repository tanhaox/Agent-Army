@echo off
REM ==========================================
REM 实时日志查看器
REM ==========================================

echo.
echo ========================================
echo   Real-time Log Viewer
echo ========================================
echo.

cd /d "%~dp0"

echo [SELECT LOG FILE]
echo.
echo   1. Main Log (agent-army.log)
echo   2. Error Log (error.log)
echo   3. Both (merged)
echo.

set /p choice="Enter choice (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo [VIEWING] logs\agent-army.log
    echo Press Ctrl+C to exit
    echo.
    Get-Content logs\agent-army.log -Wait
) else if "%choice%"=="2" (
    echo.
    echo [VIEWING] logs\error.log
    echo Press Ctrl+C to exit
    echo.
    Get-Content logs\error.log -Wait
) else if "%choice%"=="3" (
    echo.
    echo [VIEWING] All Logs (merged)
    echo Press Ctrl+C to exit
    echo.
    Get-Content logs\*.log -Wait
) else (
    echo.
    echo [ERROR] Invalid choice
    pause
    exit /b 1
)

pause
