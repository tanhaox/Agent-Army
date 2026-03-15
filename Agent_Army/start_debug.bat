@echo off
chcp 65001 >nul
title Agent Army v2.0 - 启动日志

echo ============================================================
echo   Agent Army v2.0 - 调试启动
echo ============================================================
echo.

cd /d %~dp0

echo 当前目录: %CD%
echo.

echo [1] 检查 Python...
python --version
if %ERRORLEVEL% neq 0 (
    echo [错误] Python 未安装或不在 PATH 中
    goto :error
)

echo.
echo [2] 检查文件...
if not exist "web_app_v2.py" (
    echo [错误] 找不到 web_app_v2.py
    goto :error
)
echo [OK] web_app_v2.py 存在

echo.
echo [3] 检查 Streamlit...
python -m streamlit --version
if %ERRORLEVEL% neq 0 (
    echo [错误] Streamlit 未安装
    echo.
    echo 正在安装 Streamlit...
    pip install streamlit
    if %ERRORLEVEL% neq 0 (
        goto :error
    )
)

echo.
echo ============================================================
echo   正在启动 Agent Army v2.0
echo ============================================================
echo.
echo 访问地址: http://localhost:8501
echo.
echo 按 Ctrl+C 停止服务
echo ============================================================
echo.

REM 启动并等待
python -m streamlit run web_app_v2.py --server.port 8501 --server.address localhost

echo.
echo ============================================================
echo   服务已停止
echo ============================================================

if %ERRORLEVEL% neq 0 (
    echo.
    echo [错误] 启动失败，错误代码: %ERRORLEVEL%
    echo.
    goto :error
)

goto :end

:error
echo.
echo ============================================================
echo   启动失败
echo ============================================================
echo.
echo 可能的原因:
echo   1. Python 未正确安装
echo   2. streamlit 未安装 (运行: pip install streamlit)
echo   3. 缺少依赖文件
echo.
echo 请检查上述错误信息
echo.

:end
echo.
echo 按任意键退出...
pause >nul
