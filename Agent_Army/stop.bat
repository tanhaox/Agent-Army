@echo off
REM ========================================
REM Agent Army v2.0 - 停止服务并释放端口
REM ========================================

cd /d "%~dp0"

echo.
echo ========================================
echo   停止 Agent Army 服务
echo ========================================
echo.

REM 查找并终止占用8501端口的进程
echo [1/2] 正在查找占用8501端口的进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501.*LISTENING"') do (
    echo 找到进程 PID: %%a
    echo 正在终止进程...
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 1 (
        echo [WARN] 无法终止进程 %%a（可能已停止）
    ) else (
        echo [OK] 进程 %%a 已终止
    )
)

echo.
echo [2/2] 检查端口状态...
netstat -ano | findstr ":8501" >nul 2>&1
if errorlevel 1 (
    echo [OK] 端口8501已释放
) else (
    echo [WARN] 端口8501仍被占用
    echo.
    echo 当前占用情况：
    netstat -ano | findstr ":8501"
)

echo.
echo ========================================
echo 完成
echo ========================================
echo.
pause
