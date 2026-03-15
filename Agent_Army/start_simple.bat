@echo off
chcp 65001 >nul
cd /d %~dp0

echo ============================================================
echo   Agent Army v2.0 - 简化启动
echo ============================================================
echo.
echo 正在启动...
echo 访问: http://localhost:8501
echo.

python -m streamlit run web_app_v2.py

pause
