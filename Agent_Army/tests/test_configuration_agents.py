"""
配置部Agent测试

测试资产配置AI和机会筛选AI的基本功能
"""

import asyncio
import sys
import pytest
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.business.configuration.asset_allocation_ai import AssetAllocationAI
from src.agents.business.configuration.opportunity_screening_ai import OpportunityScreeningAI


@pytest.mark.asyncio
async def test_asset_allocation_ai():
    """测试资产配置AI"""
    print("\n" + "="*60)
    print("测试资产配置AI")
    print("="*60)

    ai = AssetAllocationAI()

    # 测试场景1：稳健型中期投资
    print("\n场景1：稳健型中期投资（100万）")
    result = await ai.analyze(
        stock_code="600519",  # 贵州茅台
        portfolio_size=1000000,
        risk_tolerance="稳健",
        investment_horizon="中期"
    )

    print(f"结论: {result.conclusion}")
    print(f"置信度: {result.confidence:.1%}")
    print(f"\n建议:")
    for rec in result.recommendations[:3]:
        print(f"  - {rec}")

    print(f"\n风险提示:")
    for risk in result.risks[:3]:
        print(f"  - {risk}")

    # 测试场景2：激进型长期投资
    print("\n场景2：激进型长期投资（500万）")
    result2 = await ai.analyze(
        stock_code="600519",
        portfolio_size=5000000,
        risk_tolerance="激进",
        investment_horizon="长期"
    )

    print(f"结论: {result2.conclusion}")
    print(f"股票配置: {result2.details['strategic_allocation']['equity']['ratio']:.1%}")
    print(f"预期收益: {result2.details['risk_analysis']['expected_annual_return']:.1%}")

    print("\n[OK] 资产配置AI测试通过")


@pytest.mark.asyncio
async def test_opportunity_screening_ai():
    """测试机会筛选AI"""
    print("\n" + "="*60)
    print("测试机会筛选AI")
    print("="*60)

    ai = OpportunityScreeningAI()

    # 测试场景：筛选投资机会
    print("\n场景：筛选优质投资机会（前5名）")

    # 模拟股票池
    stock_universe = [
        "600519",  # 贵州茅台
        "000858",  # 五粮液
        "600036",  # 招商银行
        "000001",  # 平安银行
        "601318",  # 中国平安
        "000333",  # 美的集团
        "600276",  # 恒瑞医药
        "300750",  # 宁德时代
        "688981",  # 中芯国际
        "601012"   # 隆基绿能
    ]

    result = await ai.analyze(
        stock_code="600519",
        stock_universe=stock_universe,
        top_n=5
    )

    print(f"结论: {result.conclusion}")
    print(f"置信度: {result.confidence:.1%}")

    print(f"\n前5名投资机会:")
    for i, opp in enumerate(result.details['ranked_opportunities'], 1):
        print(f"\n  {i}. {opp['stock_name']} ({opp['stock_code']})")
        print(f"     综合评分: {opp['final_score']:.1f}")
        print(f"     投资建议: {opp['investment_suggestion']}")
        print(f"     推荐理由:")
        for reason in opp['reasons'][:2]:
            print(f"       - {reason}")

    print(f"\n市场热点: {result.details['hot_spots']['suggested_focus']}")

    print(f"\n建议:")
    for rec in result.recommendations[:3]:
        print(f"  - {rec}")

    print("\n[OK] 机会筛选AI测试通过")


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("配置部Agent测试")
    print("="*60)

    try:
        # 测试资产配置AI
        await test_asset_allocation_ai()

        # 测试机会筛选AI
        await test_opportunity_screening_ai()

        print("\n" + "="*60)
        print("[OK] 所有测试通过")
        print("="*60)

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
