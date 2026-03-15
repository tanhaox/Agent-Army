@echo off
REM Agent Army Black-box Test Runner
REM Runs all black-box tests

chcp 65001 > nul

echo ============================================================
echo   Agent Army - Black-box Test Suite
echo ============================================================
echo.

REM 切换到本脚本所在目录（Agent_Army/）
cd /d "%~dp0"

echo Running black-box tests...
echo.

REM 使用验证脚本（更稳定）
python verify_blackbox_tests.py

echo.
echo ============================================================
echo   Test Complete
echo ============================================================
echo.
echo Reports saved to: tests\blackbox\reports\
pause
