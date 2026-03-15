@echo off
chcp 65001 > nul
REM ============================================================
REM 创建Windows定时任务
REM 每天上午9点和下午3点执行政策新闻采集
REM ============================================================

echo.
echo ══════════════════════════════════════════════════════════
echo    创建Windows任务计划程序 - 政策新闻自动采集
echo ══════════════════════════════════════════════════════════
echo.

REM 检查是否以管理员身份运行
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ 错误：需要管理员权限
    echo 请右键点击此文件，选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)

echo ✓ 已获取管理员权限
echo.

REM 删除旧任务（如果存在）
echo [1/3] 删除旧任务...
schtasks /Delete /TN "PolicyNews_Fetch_Morning" /F >nul 2>&1
schtasks /Delete /TN "PolicyNews_Fetch_Afternoon" /F >nul 2>&1
echo ✓ 旧任务已清理
echo.

REM 创建上午9点的任务
echo [2/3] 创建上午9点的采集任务...
schtasks /Create /TN "PolicyNews_Fetch_Morning" /TR "C:\AI-Agent-Local\fetch_policy_news.bat" /SC DAILY /ST 09:00 /RU SYSTEM /F
if %errorLevel% equ 0 (
    echo ✓ 上午任务创建成功（每天 09:00）
) else (
    echo ❌ 上午任务创建失败
)
echo.

REM 创建下午3点的任务
echo [3/3] 创建下午3点的采集任务...
schtasks /Create /TN "PolicyNews_Fetch_Afternoon" /TR "C:\AI-Agent-Local\fetch_policy_news.bat" /SC DAILY /ST 15:00 /RU SYSTEM /F
if %errorLevel% equ 0 (
    echo ✓ 下午任务创建成功（每天 15:00）
) else (
    echo ❌ 下午任务创建失败
)
echo.

echo ══════════════════════════════════════════════════════════
echo    定时任务设置完成
echo ══════════════════════════════════════════════════════════
echo.
echo 📅 已创建以下任务：
echo    - 上午采集：每天 09:00
echo    - 下午采集：每天 15:00
echo.
echo 💡 查看任务：schtasks /Query /TN "PolicyNews_Fetch_Morning"
echo    删除任务：schtasks /Delete /TN "PolicyNews_Fetch_Morning" /F
echo.
pause
