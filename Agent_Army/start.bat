@echo off
REM Agent Army Dashboard Launcher - Simplified Version
REM No Chinese characters to avoid encoding issues

cd /d "%~dp0"

echo ========================================
echo   Agent Army v2.0 Dashboard
echo ========================================
echo.

REM Check if web_app.py exists
if not exist "web_app.py" (
    echo [ERROR] web_app.py not found!
    echo Current directory: %CD%
    echo Please run this script from Agent_Army folder.
    pause
    exit /b 1
)

REM Kill any existing process on port 8501
netstat -aon | findstr ":8501.*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo Port 8501 is in use. Killing existing process...
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501.*LISTENING" 2^>nul') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul 2>&1
)

echo Starting Dashboard...
echo Access URL: http://localhost:8501
echo Press Ctrl+C to stop
echo.

python -m streamlit run web_app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

if errorlevel 1 (
    echo.
    echo [FAILED] Check:
    echo   1. Python installed: python --version
    echo   2. Streamlit installed: pip install streamlit
    echo   3. Dependencies: pip install -r requirements.txt
    pause
)
