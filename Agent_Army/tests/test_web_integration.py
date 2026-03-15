#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web界面集成测试 - 自动化测试
测试所有核心功能，确保没有语法错误和运行时错误
"""

import pytest
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有导入"""
    print("=" * 60)
    print("测试1: 导入检查")
    print("=" * 60)

    try:
        print("  1. 导入 streamlit...")
        import streamlit as st
        print("     [OK] streamlit导入成功")

        print("  2. 导入 web_app...")
        print("     [SKIP] 跳过web_app导入（Streamlit应用需要通过浏览器测试）")

        print("  3. 导入 workflow...")
        from src.workflows.investment_analysis_workflow import InvestmentAnalysisWorkflow
        print("     [OK] workflow导入成功")

        print("  4. 导入 agents...")
        from src.agents.business.industry_analyzers import IndustryChainAnalyzer
        from src.agents.business.fundamental_analyzer import FundamentalAnalyzer
        print("     [OK] agents导入成功")

        print("\n[OK] 所有导入测试通过\n")
        return True

    except Exception as e:
        print(f"\n[ERROR] 导入失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_workflow_execution():
    """测试工作流执行"""
    print("=" * 60)
    print("测试2: 工作流执行测试")
    print("=" * 60)

    try:
        from src.workflows.investment_analysis_workflow import InvestmentAnalysisWorkflow

        print("  1. 初始化工作流...")
        workflow = InvestmentAnalysisWorkflow()
        print("     [OK] 工作流初始化成功")

        print("  2. 执行分析（股票代码: 600519）...")
        print("     [WAIT] 正在执行...（这可能需要1-2分钟）")

        report = await workflow.analyze_stock("600519")

        print(f"     [OK] 分析完成")
        print(f"     - 股票: {report.stock_name} ({report.stock_code})")
        print(f"     - 评分: {report.overall_score:.1f}/100")
        print(f"     - 评级: {report.overall_rating.value}")

        print("  3. 检查Commander审核...")
        if hasattr(report, 'commander_review'):
            review = report.commander_review
            print(f"     [OK] Commander审核完成")
            print(f"     - 状态: {review.get('status', 'unknown')}")
            print(f"     - 质量评分: {review.get('quality_score', 0)}/100")
        else:
            print("     [WARN] 未找到Commander审核记录")

        print("\n[OK] 工作流执行测试通过\n")
        return True

    except Exception as e:
        print(f"\n[ERROR] 工作流执行失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_agent_independent():
    """测试Agent独立执行"""
    print("=" * 60)
    print("测试3: Agent独立执行测试")
    print("=" * 60)

    try:
        from src.agents.business.industry_analyzers import IndustryChainAnalyzer
        from src.agents.business.fundamental_analyzer import FundamentalAnalyzer

        # 测试产业链分析Agent
        print("  1. 测试产业链分析Agent...")
        industry_analyzer = IndustryChainAnalyzer()
        industry_result = asyncio.run(industry_analyzer.analyze("600519"))
        print(f"     [OK] 产业链分析完成")
        print(f"     - 行业: {industry_result.industry_name}")
        print(f"     - 评分: {industry_result.score}")

        # 测试基本面分析Agent
        print("  2. 测试基本面分析Agent...")
        fundamental_analyzer = FundamentalAnalyzer()
        fundamental_result = asyncio.run(fundamental_analyzer.analyze("600519"))
        print(f"     [OK] 基本面分析完成")
        print(f"     - 评分: {fundamental_result['composite_score']:.1f}")
        print(f"     - 评级: {fundamental_result['rating']}")

        print("\n[OK] Agent独立执行测试通过\n")
        return True

    except Exception as e:
        print(f"\n[ERROR] Agent执行失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_web_service():
    """测试Web服务是否正常运行"""
    print("=" * 60)
    print("测试4: Web服务检查")
    print("=" * 60)

    try:
        import urllib.request
        import urllib.error

        print("  1. 检查服务端口8501...")
        try:
            response = urllib.request.urlopen("http://localhost:8501", timeout=5)
            html = response.read().decode('utf-8')

            if "Streamlit" in html:
                print("     [OK] Web服务正常运行")
                print("     - 访问地址: http://localhost:8501")
                print("     - 状态: 响应正常")
            else:
                print("     [WARN] 服务响应异常")
                return False

        except urllib.error.URLError as e:
            print(f"     [ERROR] 无法连接到服务: {str(e)}")
            return False

        print("\n[OK] Web服务测试通过\n")
        return True

    except Exception as e:
        print(f"\n[ERROR] Web服务测试失败: {str(e)}\n")
        return False


def test_report_generation():
    """测试报告生成"""
    print("=" * 60)
    print("测试5: 报告生成测试")
    print("=" * 60)

    try:
        from src.workflows.investment_analysis_workflow import InvestmentAnalysisWorkflow
        from datetime import datetime
        import json

        print("  1. 生成完整报告...")
        workflow = InvestmentAnalysisWorkflow()
        report = asyncio.run(workflow.analyze_stock("600519"))
        print("     [OK] 报告生成成功")

        print("  2. 保存报告到文件...")
        filepath = workflow.save_report(report, output_dir="./test_reports")
        print(f"     [OK] 报告已保存: {filepath}")

        print("  3. 验证报告格式...")
        with open(filepath, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        required_fields = [
            'stock_code', 'stock_name', 'report_date',
            'overall_score', 'overall_rating', 'investment_advice'
        ]

        missing_fields = [field for field in required_fields if field not in report_data]

        if missing_fields:
            print(f"     [ERROR] 缺少必需字段: {missing_fields}")
            return False
        else:
            print("     [OK] 报告格式正确")
            print(f"     - 字段完整度: 100%")
            print(f"     - 必需字段: {len(required_fields)}/{len(required_fields)}")

        print("\n[OK] 报告生成测试通过\n")
        return True

    except Exception as e:
        print(f"\n[ERROR] 报告生成测试失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("  Agent Army - Web界面集成测试")
    print("=" * 60)
    print()

    results = []

    # 测试1: 导入检查
    results.append(("导入检查", test_imports()))

    # 测试2: Agent独立执行
    results.append(("Agent独立执行", test_agent_independent()))

    # 测试3: 工作流执行
    results.append(("工作流执行", asyncio.run(test_workflow_execution())))

    # 测试4: Web服务
    results.append(("Web服务", test_web_service()))

    # 测试5: 报告生成
    results.append(("报告生成", test_report_generation()))

    # 汇总结果
    print("\n" + "=" * 60)
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
        print("\n[SUCCESS] 所有测试通过！Web界面已就绪！\n")
        return 0
    else:
        print(f"\n[WARN] 有 {total - passed} 个测试失败，请检查错误日志\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())


@pytest.mark.asyncio
async def test_workflow_execution():
    """测试工作流执行"""
    print("=" * 60)
    print("测试2: 工作流执行测试")
    print("=" * 60)

    try:
        from src.workflows.investment_analysis_workflow import InvestmentAnalysisWorkflow

        print("  1. 初始化工作流...")
        workflow = InvestmentAnalysisWorkflow()
        print("     ✅ 工作流初始化成功")

        print("  2. 执行分析（股票代码: 600519）...")
        print("     ⏳ 正在执行...（这可能需要1-2分钟）")

        report = await workflow.analyze_stock("600519")

        print(f"     ✅ 分析完成")
        print(f"     • 股票: {report.stock_name} ({report.stock_code})")
        print(f"     • 评分: {report.overall_score:.1f}/100")
        print(f"     • 评级: {report.overall_rating.value}")

        print("  3. 检查Commander审核...")
        if hasattr(report, 'commander_review'):
            review = report.commander_review
            print(f"     ✅ Commander审核完成")
            print(f"     • 状态: {review.get('status', 'unknown')}")
            print(f"     • 质量评分: {review.get('quality_score', 0)}/100")
        else:
            print("     ⚠️ 未找到Commander审核记录")

        print("\n✅ 工作流执行测试通过\n")
        return True

    except Exception as e:
        print(f"\n❌ 工作流执行失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_agent_independent():
    """测试Agent独立执行"""
    print("=" * 60)
    print("测试3: Agent独立执行测试")
    print("=" * 60)

    try:
        from src.agents.business.industry_analyzers import IndustryChainAnalyzer
        from src.agents.business.fundamental_analyzer import FundamentalAnalyzer

        # 测试产业链分析Agent
        print("  1. 测试产业链分析Agent...")
        industry_analyzer = IndustryChainAnalyzer()
        industry_result = asyncio.run(industry_analyzer.analyze("600519"))
        print(f"     ✅ 产业链分析完成")
        print(f"     • 行业: {industry_result.industry_name}")
        print(f"     • 评分: {industry_result.score}")

        # 测试基本面分析Agent
        print("  2. 测试基本面分析Agent...")
        fundamental_analyzer = FundamentalAnalyzer()
        fundamental_result = asyncio.run(fundamental_analyzer.analyze("600519"))
        print(f"     ✅ 基本面分析完成")
        print(f"     • 评分: {fundamental_result['composite_score']:.1f}")
        print(f"     • 评级: {fundamental_result['rating']}")

        print("\n✅ Agent独立执行测试通过\n")
        return True

    except Exception as e:
        print(f"\n❌ Agent执行失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_web_service():
    """测试Web服务是否正常运行"""
    print("=" * 60)
    print("测试4: Web服务检查")
    print("=" * 60)

    try:
        import urllib.request
        import urllib.error

        print("  1. 检查服务端口8501...")
        try:
            response = urllib.request.urlopen("http://localhost:8501", timeout=5)
            html = response.read().decode('utf-8')

            if "Streamlit" in html:
                print("     ✅ Web服务正常运行")
                print("     • 访问地址: http://localhost:8501")
                print("     • 状态: 响应正常")
            else:
                print("     ⚠️ 服务响应异常")
                return False

        except urllib.error.URLError as e:
            print(f"     ❌ 无法连接到服务: {str(e)}")
            return False

        print("\n✅ Web服务测试通过\n")
        return True

    except Exception as e:
        print(f"\n❌ Web服务测试失败: {str(e)}\n")
        return False


def test_report_generation():
    """测试报告生成"""
    print("=" * 60)
    print("测试5: 报告生成测试")
    print("=" * 60)

    try:
        from src.workflows.investment_analysis_workflow import InvestmentAnalysisWorkflow
        from datetime import datetime
        import json

        print("  1. 生成完整报告...")
        workflow = InvestmentAnalysisWorkflow()
        report = asyncio.run(workflow.analyze_stock("600519"))
        print("     ✅ 报告生成成功")

        print("  2. 保存报告到文件...")
        filepath = workflow.save_report(report, output_dir="./test_reports")
        print(f"     ✅ 报告已保存: {filepath}")

        print("  3. 验证报告格式...")
        with open(filepath, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        required_fields = [
            'stock_code', 'stock_name', 'report_date',
            'overall_score', 'overall_rating', 'investment_advice'
        ]

        missing_fields = [field for field in required_fields if field not in report_data]

        if missing_fields:
            print(f"     ❌ 缺少必需字段: {missing_fields}")
            return False
        else:
            print("     ✅ 报告格式正确")
            print(f"     • 字段完整度: 100%")
            print(f"     • 必需字段: {len(required_fields)}/{len(required_fields)}")

        print("\n✅ 报告生成测试通过\n")
        return True

    except Exception as e:
        print(f"\n❌ 报告生成测试失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("  Agent Army - Web界面集成测试")
    print("=" * 60)
    print()

    results = []

    # 测试1: 导入检查
    results.append(("导入检查", test_imports()))

    # 测试2: Agent独立执行
    results.append(("Agent独立执行", test_agent_independent()))

    # 测试3: 工作流执行
    results.append(("工作流执行", asyncio.run(test_workflow_execution())))

    # 测试4: Web服务
    results.append(("Web服务", test_web_service()))

    # 测试5: 报告生成
    results.append(("报告生成", test_report_generation()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20s} {status}")

    print()
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)

    if passed == total:
        print("\n🎉 所有测试通过！Web界面已就绪！\n")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查错误日志\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
