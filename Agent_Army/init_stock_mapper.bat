@echo off
REM ==========================================
REM 股票代码映射初始化脚本
REM ==========================================

echo.
echo ========================================
echo   Stock Code Mapper Initializer
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] Installing AKShare...
pip install akshare
echo.

echo [2/2] Initializing stock code mapping...
python scripts\init_stock_mapper.py
echo.

pause
