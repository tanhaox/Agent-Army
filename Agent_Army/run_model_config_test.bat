@echo off
chcp 65001 > nul
REM Agent Army - Model Config Test Runner

set PYTHONPATH=C:\AI-Agent-Local\Agent_Army
set PYTHONIOENCODING=utf-8

echo ============================================================
echo   Agent Army - Model Configuration Test
echo ============================================================
echo.

python tests\test_model_config.py

echo.
pause
