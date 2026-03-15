@echo off
chcp 65001 > nul
REM Agent Army Smoke Test Runner
REM Usage: run_smoke_test.bat

cd /d "%~dp0"
REM Already in Agent_Army directory - no need to cd ..

echo ============================================================
echo   Agent Army - Smoke Test
echo ============================================================
echo.
echo Running automated tests...
echo.

python tests\smoke_test.py %*

echo.
echo ============================================================
echo   Test Complete
echo ============================================================
echo.

if errorlevel 1 (
    echo Status: FAILED
    echo.
    echo Please:
    echo   1. Check error messages above
    echo   2. Fix issues
    echo   3. Run test again
    echo.
) else (
    echo Status: PASSED
    echo.
    echo Next steps:
    echo   1. Start app: start_ps1.bat
    echo   2. Open browser: http://localhost:8501
    echo   3. Run manual tests
    echo.
)

pause
