@echo off
chcp 65001 >nul
echo ============================================================
echo  测试 pythonw 启动
echo ============================================================
echo.

cd /d C:\AI-Agent-Local\projects\tools\backup-agent

echo [1] 检查 pythonw.exe...
where pythonw
if errorlevel 1 (
    echo [!] 未找到 pythonw.exe
    pause
    exit /b 1
)
echo [√] pythonw.exe 可用
echo.

echo [2] 启动 Backup Agent（pythonw，窗口隐藏）...
echo     请检查系统托盘是否出现图标
echo.

start "" /B pythonw backup_agent.py --daemon --tray

echo [3] 等待 3 秒...
timeout /t 3 /nobreak >nul

echo.
echo [4] 检查 pythonw 进程...
tasklist | findstr pythonw
if errorlevel 1 (
    echo [!] 未找到 pythonw.exe 进程 - 启动失败
) else (
    echo [√] pythonw.exe 进程正在运行
    echo.
    echo ============================================================
    echo  启动成功！
    echo  请检查系统托盘（右下角）的 Backup Agent 图标
    echo  按任意键关闭此窗口（程序继续运行）
    echo ============================================================
)

pause
