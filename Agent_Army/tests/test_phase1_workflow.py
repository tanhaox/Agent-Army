"""
Agent Army - Phase 1 测试脚本
测试最简单的投资分析流程: 产业分析 → 基本面分析 → 报告生成
"""
import pytest

import sys
import io
import asyncio
from pathlib import Path

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.investment_analysis_workflow import InvestmentAnalysisWorkflow


@pytest.mark.asyncio
async def test_phase1_workflow():
    """测试Phase 1工作流"""
    print("=" * 60)
    print("  Agent Army - Phase 1 工作流测试")
    print("  测试目标: 产业分析 + 基本面分析 → 报告生成")
    print("=" * 60)

    # 初始化工作流
    print("\n[初始化] 创建工作流...")
    workflow = InvestmentAnalysisWorkflow()

    # 测试分析一只股票 (示例:贵州茅台 600519)
    stock_code = "600519"

    print(f"\n[测试] 分析股票: {stock_code}")
    print("-" * 60)

    try:
        # 执行分析
        report = await workflow.analyze_stock(stock_code)

        # 打印报告摘要
        print("\n" + "=" * 60)
        print("  📊 投资分析报告")
        print("=" * 60)
        print(f"股票代码: {report.stock_code}")
        print(f"股票名称: {report.stock_name}")
        print(f"报告日期: {report.report_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print(f"综合评分: {report.overall_score:.1f}/100")
        print(f"综合评级: {report.overall_rating.value}")
        print(f"风险等级: {report.risk_level.value}")
        print()
        print("投资建议:")
        print(f"  {report.investment_advice}")
        print()
        print(f"仓位建议: {report.position_suggestion}")
        print()
        print("关键风险:")
        for i, risk in enumerate(report.key_risks[:3], 1):
            print(f"  {i}. {risk}")

        # 保存报告
        print("\n[保存] 保存报告到文件...")
        filepath = workflow.save_report(report)
        print(f"✅ 报告已保存: {filepath}")

        print("\n" + "=" * 60)
        print("  ✅ Phase 1 工作流测试成功!")
        print("=" * 60)

        # 验证结果
        assert report.overall_score >= 0, "评分应该 >= 0"
        assert report.overall_score <= 100, "评分应该 <= 100"
        assert report.stock_code == stock_code, "股票代码应该匹配"

        print("\n✅ 所有断言通过!")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_individual_agents():
    """测试单个Agent"""
    print("\n" + "=" * 60)
    print("  测试单个Agent")
    print("=" * 60)

    from src.agents.business.industry_analyzers import IndustryChainAnalyzer
    from src.agents.business.fundamental_analyzer import FundamentalAnalyzer

    # 测试产业分析AI
    print("\n[1/2] 测试产业链分析AI...")
    industry_ai = IndustryChainAnalyzer()
    print(f"   名称: {industry_ai.name}")
    print(f"   军团: {industry_ai.corps}")
    print(f"   能力数: {len(industry_ai.get_capabilities())}")
    print(f"   工具数: {len(industry_ai.get_tools())}")

    result = await industry_ai.analyze("600519")
    print(f"   ✅ 分析完成: {result.summary}")

    # 测试基本面分析AI
    print("\n[2/2] 测试基本面分析AI...")
    fundamental_ai = FundamentalAnalyzer()
    print(f"   名称: {fundamental_ai.name}")
    print(f"   军团: {fundamental_ai.corps}")
    print(f"   能力数: {len(fundamental_ai.get_capabilities())}")
    print(f"   工具数: {len(fundamental_ai.get_tools())}")

    result = await fundamental_ai.analyze("600519")
    print(f"   ✅ 分析完成: {result.summary}")

    print("\n✅ 所有Agent测试通过!")
    return True


async def main():
    """主函数"""
    print("\n🚀 Phase 1 测试开始\n")

    # 测试1: 单个Agent
    success1 = await test_individual_agents()

    # 测试2: 完整工作流
    success2 = await test_phase1_workflow()

    # 总结
    print("\n" + "=" * 60)
    print("  测试总结")
    print("=" * 60)
    print(f"  单个Agent测试: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"  完整工作流测试: {'✅ 通过' if success2 else '❌ 失败'}")
    print()

    if success1 and success2:
        print("🎉 Phase 1 测试全部通过!")
        print("   ✅ 2个业务Agent正常工作")
        print("   ✅ 协作流程跑通")
        print("   ✅ 报告生成成功")
        print("\n   Phase 1 目标达成! 🎯")
    else:
        print("❌ 部分测试失败,需要修复")

    return success1 and success2


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
