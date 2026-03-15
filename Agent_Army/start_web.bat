@echo off
chcp 65001 >nul
echo ============================================================
echo   Agent Army v2.0 - Web界面启动
echo ============================================================
echo.

cd /d %~dp0

REM 检查Python是否安装
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查Streamlit是否安装
python -m streamlit --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ 错误: 未找到Streamlit，正在安装...
    pip install streamlit
    if %ERRORLEVEL% neq 0 (
        echo ❌ Streamlit安装失败
        pause
        exit /b 1
    )
)

REM 步骤1：杀死旧的Streamlit进程（释放8501端口）
echo [1/2] 正在关闭旧的Streamlit进程...
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *streamlit*" 2>NUL | find /I "python.exe" >NUL
if %ERRORLEVEL% equ 0 (
    echo 发现旧的Streamlit进程，正在关闭...
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq *streamlit*" >NUL 2>&1
    timeout /t 2 /nobreak >NUL
    echo ✅ 旧进程已关闭
) else (
    echo ℹ️ 没有发现旧进程
)

REM 额外检查8501端口是否被占用
netstat -ano | findstr ":8501" >NUL 2>&1
if %ERRORLEVEL% equ 0 (
    echo ⚠️ 端口8501仍被占用，强制释放...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501"') do (
        taskkill /F /PID %%a >NUL 2>&1
    )
    timeout /t 2 /nobreak >NUL
    echo ✅ 端口8501已释放
)

echo.
echo [2/2] 正在启动Streamlit Web界面 v2.0...
echo       访问地址: http://localhost:8501
echo       🤖 24个Agent | 6大军团 | 扁平化设计
echo.
echo 提示: 关闭此窗口将停止Web服务
echo.

REM 启动Streamlit v2.0 (使用python -m避免PATH问题)
python -m streamlit run web_app_v2.py --server.port 8501 --server.address localhost
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 启动失败，尝试使用Python启动脚本...
    echo.
    python start_web.py
)

pause
