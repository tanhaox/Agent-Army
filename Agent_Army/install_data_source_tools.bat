@echo off
REM ============================================================================
REM 新数据源工具安装脚本
REM
REM 功能：
REM - 安装 yfinance（Yahoo Finance数据）
REM - 安装 akshare（中国金融数据）
REM - 安装 playwright（动态网页爬虫）
REM ============================================================================

echo ======================================================================
echo   新数据源工具安装
echo ======================================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [1/4] 升级pip...
python -m pip install --upgrade pip -q

echo.
echo [2/4] 安装yfinance（Yahoo Finance数据）...
pip install yfinance -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [3/4] 安装akshare（中国金融数据）...
pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [4/4] 安装playwright（动态网页爬虫）...
pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [5/5] 安装playwright浏览器（chromium）...
playwright install chromium

echo.
echo ======================================================================
echo   安装完成！
echo ======================================================================
echo.
echo 新增工具：
echo 1. YahooFinanceTool - 国际标准股票数据
echo 2. AKShareTool      - 中国金融数据
echo 3. EastMoneyScraper - 动态网页爬虫
echo.
echo 运行测试：
echo   python tests\test_data_source_tools.py
echo.
pause
