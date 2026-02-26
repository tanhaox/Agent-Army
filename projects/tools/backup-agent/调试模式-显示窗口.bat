@echo off
chcp 65001 >nul
cd /d C:\AI-Agent-Local\projects\tools\backup-agent
echo ========================================
echo Starting Backup Agent (DEBUG MODE)...
echo ========================================
python backup_agent.py --daemon --tray
echo ========================================
echo Process exited with code: %errorlevel%
pause
