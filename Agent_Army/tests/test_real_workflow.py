#!/usr/bin/env python3
"""
完整工作流测试 - 真实测试
"""

import pytest
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.investment_analysis_workflow import InvestmentAnalysisWorkflow


@pytest.mark.asyncio
async def test_real_analysis():
    """真实测试完整分析流程"""
    print("=" * 60)
    print("Agent Army - 完整工作流真实测试")
    print("=" * 60)

    try:
        # 初始化
        print("\n[1/2] 初始化工作流...")
        workflow = InvestmentAnalysisWorkflow()
        print("[OK] 工作流初始化成功")
        print(f"   - 产业分析: {workflow.industry_analyzer.name}")
        print(f"   - 基本面分析: {workflow.fundamental_analyzer.name}")
        print(f"   - 质量审核: {workflow.commander.name}")

        # 分析股票
        print("\n[2/2] 开始分析股票 600519...")
        report = await workflow.analyze_stock("600519")

        print("\n" + "=" * 60)
        print("[OK] 分析成功！")
        print("=" * 60)
        print(f"股票: {report.stock_name} ({report.stock_code})")
        print(f"综合评分: {report.overall_score:.1f}/100")
        print(f"投资评级: {report.overall_rating.value}")
        print(f"风险等级: {report.risk_level.value}")
        print(f"投资建议: {report.investment_advice[:100]}...")
        print("=" * 60)

        # 保存报告
        filepath = workflow.save_report(report)
        print(f"\n报告已保存: {filepath}")

        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"[ERROR] 测试失败")
        print("=" * 60)
        print(f"错误信息: {str(e)}")
        print("\n完整错误堆栈:")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_real_analysis())
    sys.exit(0 if success else 1)
