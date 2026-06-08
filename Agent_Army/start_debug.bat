@echo off
REM ==========================================
REM 调试模式启动脚本
REM ==========================================

echo.
echo ========================================
echo   DEBUG MODE - Investment Analysis
echo ========================================
echo.

cd /d "%~dp0"

echo [INFO] This script will:
echo   1. Start Streamlit in DEBUG mode
echo   2. Show all execution logs in console
echo   3. Show all execution logs in UI
echo.

echo [STEP 1] Killing existing processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo [STEP 2] Starting Debug Dashboard...
echo.
echo ========================================
echo   IMPORTANT:
echo.
echo   1. Open browser: http://localhost:8501
echo   2. Press Ctrl+Shift+R to refresh
echo   3. Enter stock: 601669
echo   4. Click "Start Analysis"
echo   5. Watch BOTH:
echo      - Browser window (UI logs)
echo      - This console (Console logs)
echo.
echo   You will see:
echo   - [HH:MM:SS] Detailed execution logs
echo   - Progress updates
echo   - Error details (if any)
echo ========================================
echo.

timeout /t 5 /nobreak >nul

REM 启动调试版本（强制刷新控制台）
python -u -m streamlit run debug_analysis.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

pause
