@echo off
chcp 65001 >nul
echo ============================================================
echo  Backup Agent 启动脚本（带调试日志）
echo ============================================================
echo.

cd /d C:\AI-Agent-Local\projects\tools\backup-agent

echo [%TIME%] 当前目录: %CD%
echo [%TIME%] 查找 pythonw.exe...

where pythonw >nul 2>&1
if errorlevel 1 (
    echo [%TIME%] [!] 未找到 pythonw.exe
    echo [%TIME%] [*] 尝试使用 python.exe...
    set PYTHON_CMD=python
) else (
    echo [%TIME%] [√] 找到 pythonw.exe
    set PYTHON_CMD=pythonw
)

echo [%TIME%] Python 命令: %PYTHON_CMD% backup_agent.py --daemon --tray
echo [%TIME%] 正在启动...
echo.

REM 创建日志文件
set LOG_FILE=启动日志_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%.log
echo [%TIME%] 日志文件: %LOG_FILE%

REM 启动程序并记录输出
%PYTHON_CMD% backup_agent.py --daemon --tray > %LOG_FILE% 2>&1

echo.
echo [%TIME%] 程序已启动，退出代码: %errorlevel%
echo [%TIME%] 请查看日志文件了解详情
echo ============================================================

REM 显示日志文件内容
if exist %LOG_FILE% (
    echo.
    echo === 日志内容 ===
    type %LOG_FILE%
    echo.
    echo === 日志结束 ===
)

pause
