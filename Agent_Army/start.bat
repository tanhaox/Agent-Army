@echo off
cd /d "%~dp0"

echo ========================================
echo   Agent Army v2.0
echo ========================================
echo.

REM 强制终止所有占用8501端口的进程
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501.*LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM 等待端口释放
timeout /t 1 /nobreak >nul 2>&1

echo 正在启动...
echo.

python -m streamlit run web_app.py --server.port 8501

if errorlevel 1 (
    echo.
    echo [启动失败]
    echo 请运行 start-debug.bat 查看详情
    pause
)
