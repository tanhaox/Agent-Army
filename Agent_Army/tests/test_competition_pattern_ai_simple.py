"""
测试竞争格局AI (CompetitionPatternAI) - 简化版
"""
import pytest

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.business.industry_analysis.competition_pattern_ai import CompetitionPatternAI


@pytest.mark.asyncio
async def test_competition_pattern_ai():
    """测试竞争格局AI的基本功能"""

    print("=" * 80)
    print("测试竞争格局AI - CompetitionPatternAI")
    print("=" * 80)

    # 初始化AI
    ai = CompetitionPatternAI()
    print("\n[OK] 竞争格局AI初始化成功")

    # 测试用例：贵州茅台（白酒行业）
    test_stock_code = "600519"

    print(f"\n[TEST] 测试股票: {test_stock_code} (贵州茅台 - 白酒行业)")
    print("-" * 80)

    try:
        # 执行竞争格局分析
        print("\n[1/4] 执行竞争格局综合分析...")
        result = await ai.analyze(stock_code=test_stock_code)

        print("\n[OK] 分析完成！\n")
        print("分析结果摘要：")
        print(f"  - 股票代码: {result.get('stock_code', 'N/A')}")
        print(f"  - 股票名称: {result.get('stock_name', 'N/A')}")
        print(f"  - 所属行业: {result.get('industry', 'N/A')}")

        # 集中度指标
        concentration = result.get('concentration', {})
        print(f"\n[INFO] 市场集中度:")
        print(f"  - CR4: {concentration.get('cr4', 0):.2%}")
        print(f"  - CR8: {concentration.get('cr8', 0):.2%}")
        print(f"  - HHI: {concentration.get('hhi', 0):.4f}")
        print(f"  - 集中度等级: {concentration.get('concentration_level', 'N/A')}")

        # 龙头企业
        leaders = result.get('leaders', {})
        top_leaders = leaders.get('leaders', [])[:3]
        print(f"\n[INFO] 龙头企业 (前3名):")
        for leader in top_leaders:
            print(f"  {leader.get('rank', 0)}. {leader.get('name', 'N/A')} ({leader.get('stock_code', 'N/A')}) - 市场份额: {leader.get('market_share', 0):.1f}%")

        # 竞争地位
        position = result.get('competitive_position', {})
        print(f"\n[INFO] 竞争地位:")
        print(f"  - 地位: {position.get('position', 'N/A')}")
        print(f"  - 描述: {position.get('position_desc', 'N/A')}")
        print(f"  - 排名: {position.get('rank', 0)}")
        print(f"  - 市场份额: {position.get('market_share', 0):.1f}%")

        # LLM分析
        llm_analysis = result.get('llm_analysis', {})
        print(f"\n[INFO] LLM深度分析:")
        print(f"  - 竞争态势: {llm_analysis.get('competition_status', 'N/A')}")
        print(f"  - 竞争趋势: {llm_analysis.get('competition_trend', 'N/A')}")
        key_factors = llm_analysis.get('key_success_factors', [])
        if key_factors:
            print(f"  - 关键成功因素: {', '.join(key_factors)}")

        # 综合评分
        overall_score = result.get('overall_score', {})
        print(f"\n[INFO] 综合评分:")
        print(f"  - 评分: {overall_score.get('score', 0)}/100")
        print(f"  - 评级: {overall_score.get('rating', 'N/A')}")
        print(f"  - 描述: {overall_score.get('description', 'N/A')}")

        print("\n" + "=" * 80)
        print("[SUCCESS] 测试完成！竞争格局AI功能正常")
        print("=" * 80)

        return result

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


@pytest.mark.asyncio
async def test_individual_functions():
    """测试各个独立功能"""

    print("\n\n" + "=" * 80)
    print("测试独立功能")
    print("=" * 80)

    ai = CompetitionPatternAI()
    test_stock_code = "600519"

    # 测试1: 集中度评估
    try:
        print(f"\n[2/4] 测试市场集中度评估...")
        result = await ai.evaluate_concentration(stock_code=test_stock_code)
        print(f"[OK] CR4={result.get('cr4', 0):.2%}, CR8={result.get('cr8', 0):.2%}, HHI={result.get('hhi', 0):.4f}")
    except Exception as e:
        print(f"[ERROR] 集中度评估失败: {str(e)}")

    # 测试2: 龙头企业识别
    try:
        print(f"\n[3/4] 测试龙头企业识别...")
        result = await ai.identify_leaders(stock_code=test_stock_code, top_n=5)
        print(f"[OK] 识别出{len(result.get('leaders', []))}家龙头企业")
        print(f"[INFO] {result.get('summary', 'N/A')}")
    except Exception as e:
        print(f"[ERROR] 龙头企业识别失败: {str(e)}")

    # 测试3: 竞争地位评估
    try:
        print(f"\n[4/4] 测试竞争地位评估...")
        result = await ai.assess_competitive_position(stock_code=test_stock_code)
        print(f"[OK] 竞争地位: {result.get('position', 'N/A')}")
        print(f"[INFO] {result.get('position_desc', 'N/A')}")
    except Exception as e:
        print(f"[ERROR] 竞争地位评估失败: {str(e)}")

    print("\n" + "=" * 80)
    print("[SUCCESS] 所有功能测试完成")
    print("=" * 80)


async def main():
    """主测试函数"""
    print("\n[START] 开始测试竞争格局AI\n")

    # 测试1：综合分析
    await test_competition_pattern_ai()

    # 测试2：独立功能
    await test_individual_functions()

    print("\n\n[COMPLETE] 所有测试完成！\n")


if __name__ == "__main__":
    asyncio.run(main())
