@echo off
chcp 65001 >nul
cd /d C:\AI-Agent-Local\projects\tools\backup-agent
echo ========================================
echo Starting Backup Agent...
echo ========================================
C:\Python313\pythonw.exe backup_agent.py --daemon --tray
echo ========================================
echo Process exited with code: %errorlevel%
pause
