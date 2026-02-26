@echo off
chcp 65001 >nul
echo ============================================================
echo  检查 Backup Agent 运行状态
echo ============================================================
echo.
echo 正在查找 Backup Agent 进程...
echo.
tasklist /FI "IMAGENAME eq python.exe" /V | findstr python
echo.
if errorlevel 1 (
    echo [!] 未找到 Backup Agent 进程
) else (
    echo [✓] 找到 Backup Agent 进程
)
echo.
echo ============================================================
echo  系统托盘提示
echo ============================================================
echo.
echo 1. 查看任务栏右下角的 ^ 图标
echo 2. 点击展开，查找 Backup Agent 图标
echo 3. 或者：任务栏设置 → 系统托盘图标 → 显示所有图标
echo.
pause
