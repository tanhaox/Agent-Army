#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web服务基础测试 - 仅测试基础功能，不测试API调用
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_syntax():
    """测试1: 语法检查"""
    print("=" * 60)
    print("测试1: Python语法检查")
    print("=" * 60)

    try:
        import py_compile

        files_to_check = [
            "web_app.py",
            "src/workflows/investment_analysis_workflow.py",
            "src/agents/business/industry_analyzers.py",
            "src/agents/business/fundamental_analyzer.py",
            "src/core/tools/data_source/financial_tool.py",
        ]

        for file in files_to_check:
            filepath = project_root / file
            print(f"  检查 {file}...")
            try:
                py_compile.compile(str(filepath), doraise=True)
                print(f"    [OK] 语法正确")
            except py_compile.PyCompileError as e:
                print(f"    [ERROR] 语法错误: {str(e)}")
                return False

        print("\n[OK] 所有文件语法检查通过\n")
        return True

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {str(e)}\n")
        return False


def test_imports():
    """测试2: 导入检查"""
    print("=" * 60)
    print("测试2: 模块导入检查")
    print("=" * 60)

    try:
        print("  1. 导入 streamlit...")
        import streamlit as st
        print("     [OK]")

        print("  2. 导入 workflow...")
        from src.workflows.investment_analysis_workflow import InvestmentAnalysisWorkflow
        print("     [OK]")

        print("  3. 导入 agents...")
        from src.agents.business.industry_analyzers import IndustryChainAnalyzer
        from src.agents.business.fundamental_analyzer import FundamentalAnalyzer
        print("     [OK]")

        print("  4. 导入 tools...")
        from src.core.tools.data_source.financial_tool import FinancialTool
        print("     [OK]")

        print("\n[OK] 所有模块导入成功\n")
        return True

    except Exception as e:
        print(f"\n[ERROR] 导入失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_web_service():
    """测试3: Web服务检查"""
    print("=" * 60)
    print("测试3: Web服务状态检查")
    print("=" * 60)

    try:
        import urllib.request
        import urllib.error

        print("  检查服务端口8501...")
        try:
            response = urllib.request.urlopen("http://localhost:8501", timeout=5)
            html = response.read().decode('utf-8')

            if "Streamlit" in html:
                print("    [OK] Web服务正常运行")
                print("    - 访问地址: http://localhost:8501")
                print("    - 状态: 响应正常\n")
                return True
            else:
                print("    [WARN] 服务响应异常\n")
                return False

        except urllib.error.URLError as e:
            print(f"    [ERROR] 无法连接到服务: {str(e)}\n")
            print("    请先启动服务: streamlit run web_app.py\n")
            return False

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {str(e)}\n")
        return False


def main():
    """运行基础测试"""
    print("\n" + "=" * 60)
    print("  Agent Army - Web服务基础测试")
    print("=" * 60)
    print()

    results = []

    # 测试1: 语法检查
    results.append(("语法检查", test_syntax()))

    # 测试2: 导入检查
    results.append(("导入检查", test_imports()))

    # 测试3: Web服务
    results.append(("Web服务", test_web_service()))

    # 汇总结果
    print("=" * 60)
    print("  测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name:20s} {status}")

    print()
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)

    if passed == total:
        print("\n[SUCCESS] 所有基础测试通过！")
        print("\n下一步:")
        print("  1. 访问 http://localhost:8501")
        print("  2. 进入'系统配置'配置API密钥")
        print("  3. 进入'任务管理'测试投资分析\n")
        return 0
    else:
        print(f"\n[WARN] 有 {total - passed} 个测试失败\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
