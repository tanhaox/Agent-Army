@echo off
REM ==========================================
REM 修复进度提示问题
REM ==========================================

echo.
echo ========================================
echo   Fix Progress Display Issue
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] Progress display has been improved!
echo.
echo Changes:
echo   - Added progress bars (0%% - 100%%)
echo   - Added real-time status updates
echo   - Added error details
echo   - Added timing estimates
echo.
echo [2/2] Please restart Dashboard to see changes:
echo.
echo   1. Close current Dashboard (Ctrl+C)
echo   2. Run: start.bat
echo   3. Test with stock: 601669 or 600519
echo.

pause
