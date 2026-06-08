@echo off
REM ==========================================
REM 强制重启Dashboard（清理所有缓存）
REM ==========================================

echo.
echo ========================================
echo   Force Restart Dashboard
echo ========================================
echo.

cd /d "%~dp0"

echo [STEP 1] Killing all Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo [STEP 2] Clearing Streamlit cache...
if exist "%USERPROFILE%\.streamlit\cache" (
    rmdir /s /q "%USERPROFILE%\.streamlit\cache" 2>nul
)
if exist ".streamlit\cache" (
    rmdir /s /q ".streamlit\cache" 2>nul
)

echo [STEP 3] Clearing Python cache...
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "src\__pycache__" rmdir /s /q "src\__pycache__"
for /r %%i in (__pycache__) do @if exist "%%i" rmdir /s /q "%%i" 2>nul

echo [STEP 4] Reinstalling dependencies (if needed)...
pip install -q streamlit akshare tushare 2>nul

echo [STEP 5] Starting Dashboard...
echo.
echo ========================================
echo   Dashboard Starting...
echo   URL: http://localhost:8501
echo
echo   IMPORTANT: Press Ctrl+F5 in browser!
echo ========================================
echo.

timeout /t 3 /nobreak >nul

REM 启动Dashboard（禁用文件监视，避免自动刷新）
python -m streamlit run web_app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false --server.fileWatcherType none

pause
