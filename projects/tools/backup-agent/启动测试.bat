@echo off
REM 简单启动脚本 - 直接运行 pythonw
cd /d "%~dp0"
echo 正在启动 Backup Agent...
pythonw backup_agent.py --daemon --tray
echo Backup Agent 已启动
