#!/usr/bin/env python3
"""
测试工作流初始化 - 验证Unicode编码问题修复
"""

import pytest
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.investment_analysis_workflow import InvestmentAnalysisWorkflow


def test_workflow_init():
    """测试工作流初始化"""
    print("测试工作流初始化...")

    try:
        workflow = InvestmentAnalysisWorkflow()
        print("[OK] 工作流初始化成功！")
        print(f"   - 产业分析: {workflow.industry_analyzer.name}")
        print(f"   - 基本面分析: {workflow.fundamental_analyzer.name}")
        print(f"   - 质量审核: {workflow.commander.name}")
        return True
    except Exception as e:
        print(f"[ERROR] 初始化失败: {str(e)}")
        return False


@pytest.mark.asyncio
async def test_analyze():
    """测试股票分析"""
    print("\n测试股票分析...")

    try:
        workflow = InvestmentAnalysisWorkflow()
        report = await workflow.analyze_stock("600519")
        print(f"\n[OK] 分析成功！")
        print(f"   - 股票: {report.stock_name} ({report.stock_code})")
        print(f"   - 综合评分: {report.overall_score:.1f}")
        print(f"   - 投资评级: {report.overall_rating.value}")
        return True
    except Exception as e:
        print(f"\n[ERROR] 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Agent Army - Unicode编码修复测试")
    print("=" * 60)

    # 测试1: 初始化
    init_ok = test_workflow_init()

    # 测试2: 分析（可选）
    if init_ok:
        print("\n是否测试股票分析？(y/n): ", end="")
        choice = input().strip().lower()
        if choice == 'y':
            asyncio.run(test_analyze())

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
