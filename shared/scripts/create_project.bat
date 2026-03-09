@echo off
REM AI-Agent-Local 项目生成器启动脚本
chcp 65001 >nul

echo.
echo =========================================================
echo   AI-Agent-Local 项目生成器
echo =========================================================
echo.

set SCRIPT_ROOT=%~dp0
cd /d "%SCRIPT_ROOT%"

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或不在 PATH 中
    pause
    exit /b 1
)

REM 运行项目生成器
python create_project.py %*

pause
