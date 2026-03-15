@echo off
REM Agent Army Integration Test Runner
REM Runs tests with clean output (suppresses Streamlit warnings)

REM Suppress encoding issues
chcp 65001 > nul

echo ============================================================
echo   Agent Army Web v2.0 - Integration Tests
echo ============================================================
echo.

REM Change to Agent_Army directory
cd /d "%~dp0"
REM Already in Agent_Army directory - no need to cd ..

REM Run test with Python's built-in filtering
python tests\test_integration_v2.py 2>&1 | findstr /C:"✅" /C:"❌" /C:"===" /C:"[" /C:"]"

echo.
echo ============================================================
echo   Test Complete
echo ============================================================
pause
