@echo off
cd /d "%~dp0"

echo ========================================
echo   Agent Army v2.0 - 调试模式
echo ========================================
echo.

echo 第1步：检查端口8501...
netstat -ano | findstr ":8501"
if errorlevel 1 (
    echo [结果] 端口8501未被占用
) else (
    echo [发现] 端口8501被占用！
    echo.
    echo 正在终止占用进程...
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501.*LISTENING"') do (
        echo 终止进程 %%a
        taskkill /F /PID %%a
    )
    echo.
    echo 第2步：等待2秒...
    timeout /t 2 /nobreak
)

echo.
echo 第3步：再次检查端口...
netstat -ano | findstr ":8501"
if errorlevel 1 (
    echo [结果] 端口已释放
) else (
    echo [警告] 端口仍被占用！
)

echo.
echo 第4步：启动Streamlit...
echo ========================================
python -m streamlit run web_app.py --server.port 8501

echo.
echo ========================================
echo 服务已停止
echo ========================================
echo 按任意键关闭窗口...
pause >nul
