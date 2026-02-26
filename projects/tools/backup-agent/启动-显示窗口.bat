@echo off
REM Backup Agent 启动脚本（显示窗口版）
chcp 65001 >nul
echo ============================================================
echo  Backup Agent - 调试启动
echo ============================================================
echo.

cd /d C:\AI-Agent-Local\projects\tools\backup-agent

echo 正在启动 Backup Agent（显示窗口模式）...
echo 提示：如果启动成功，请保持此窗口打开
echo 提示：如果要隐藏窗口，请使用 pythonw 版本
echo.

python backup_agent.py --daemon --tray

echo.
echo ============================================================
echo  Backup Agent 已停止
echo ============================================================
pause
