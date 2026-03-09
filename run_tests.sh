#!/bin/bash
# 测试运行脚本 - Linux/Mac

echo "========================================"
echo "AI-Agent-Local 测试运行器"
echo "========================================"
echo ""

# 检查虚拟环境
if [ -f "venv/bin/activate" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 检查依赖
echo "检查测试依赖..."
python -c "import pytest" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装测试依赖..."
    pip install pytest pytest-cov pytest-html pytest-xdist
fi

echo ""
echo "========================================"
echo "运行测试并生成覆盖率报告"
echo "========================================"
echo ""

# 运行测试
pytest -v \
    --cov=. \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    --html=pytest_report.html \
    --self-contained-html

echo ""
echo "========================================"
echo "测试完成！"
echo "========================================"
echo ""
echo "覆盖率报告: htmlcov/index.html"
echo "测试报告: pytest_report.html"
echo ""

# 在 macOS 上自动打开报告
if [[ "$OSTYPE" == "darwin"* ]]; then
    read -p "是否打开覆盖率报告? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open htmlcov/index.html
    fi
fi
