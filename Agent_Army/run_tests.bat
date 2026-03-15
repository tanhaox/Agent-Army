@echo off
chcp 65001 > nul
REM Agent Army - Integration Test Runner

echo ============================================================
echo   Agent Army Web v2.0 - Integration Tests
echo ============================================================
echo.

REM Set Python path
set PYTHONPATH=C:\AI-Agent-Local\Agent_Army
set PYTHONIOENCODING=utf-8

REM Run tests
python tests\test_integration_v2.py

echo.
echo ============================================================
echo   Tests Completed
echo ============================================================

pause
