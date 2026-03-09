@echo off
REM 测试运行脚本 - Windows
REM 运行所有测试并生成覆盖率报告

echo ========================================
echo AI-Agent-Local 测试运行器
echo ========================================
echo.

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
)

REM 检查依赖
echo 检查测试依赖...
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo 安装测试依赖...
    pip install pytest pytest-cov pytest-html pytest-xdist
)

echo.
echo ========================================
echo 运行测试并生成覆盖率报告
echo ========================================
echo.

REM 运行测试
pytest -v --cov=. --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml --html=pytest_report.html --self-contained-html

echo.
echo ========================================
echo 测试完成！
echo ========================================
echo.
echo 覆盖率报告: htmlcov\index.html
echo 测试报告: pytest_report.html
echo.

REM 打开覆盖率报告（可选）
if exist "htmlcov\index.html" (
    choice /C YN /M "是否打开覆盖率报告"
    if errorlevel 2 goto end
    start htmlcov\index.html
)

:end
pause
