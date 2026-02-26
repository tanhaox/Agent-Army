@echo off
REM Backup Agent - 显示窗口版（最可靠）
cd /d C:\AI-Agent-Local\projects\tools\backup-agent
python backup_agent.py --daemon --tray
