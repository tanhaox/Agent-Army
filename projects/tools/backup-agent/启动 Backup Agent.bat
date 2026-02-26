@echo off
REM Backup Agent 启动脚本（桌面快捷方式）
REM 后台运行，不显示窗口

cd /d C:\AI-Agent-Local\projects\tools\backup-agent

REM 使用 start 命令后台启动 pythonw（隐藏窗口）
start "" /B pythonw backup_agent.py --daemon --tray
