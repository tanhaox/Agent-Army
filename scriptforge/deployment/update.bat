@echo off
chcp 65001 >nul
title ScriptForge 更新

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║     ScriptForge 系统更新                 ║
echo   ╚══════════════════════════════════════════╝
echo.

:: ── Step 1: Backup ────────────────────────────────────
echo   [1/3] 备份当前版本...
for /f "tokens=*" %%d in ('powershell -command "Get-Date -Format yyyyMMdd_HHmmss"') do set BACKUP_TS=%%d
set BACKUP_DIR=backups\backup_%BACKUP_TS%
mkdir %BACKUP_DIR% 2>nul
if exist "backend" xcopy /E /I /Y /Q backend %BACKUP_DIR%\backend >nul 2>&1
if exist "frontend\dist" xcopy /E /I /Y /Q frontend\dist %BACKUP_DIR%\frontend_dist >nul 2>&1
echo   已备份到 %BACKUP_DIR%
echo.

:: ── Step 2: Stop ──────────────────────────────────────
echo   [2/3] 停止当前服务...
docker compose down
echo.

:: ── Step 3: Rebuild & Start ───────────────────────────
echo   [3/3] 应用更新并重新构建...
docker compose up -d --build
if %errorlevel% neq 0 (
    echo.
    echo   [错误] 更新失败！
    echo   正在从备份恢复...
    docker compose down 2>nul
    xcopy /E /I /Y /Q %BACKUP_DIR%\backend backend >nul 2>&1
    xcopy /E /I /Y /Q %BACKUP_DIR%\frontend_dist frontend\dist >nul 2>&1
    docker compose up -d
    echo   已从备份恢复
    pause
    exit /b 1
)

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║     更新完成！                           ║
echo   ║   如需回滚: 从 %BACKUP_DIR% 恢复后重新运行  ║
echo   ╚══════════════════════════════════════════╝
echo.
pause
