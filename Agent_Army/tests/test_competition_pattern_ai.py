"""
测试竞争格局AI (CompetitionPatternAI)
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
    print("\n✅ 竞争格局AI初始化成功")

    # 测试用例：贵州茅台（白酒行业）
    test_stock_code = "600519"

    print(f"\n📊 测试股票: {test_stock_code}（贵州茅台 - 白酒行业）")
    print("-" * 80)

    try:
        # 执行竞争格局分析
        print("\n1️⃣ 执行竞争格局综合分析...")
        result = await ai.analyze(stock_code=test_stock_code)

        print("\n✅ 分析完成！\n")
        print("分析结果摘要：")
        print(f"  - 股票代码: {result.get('stock_code', 'N/A')}")
        print(f"  - 股票名称: {result.get('stock_name', 'N/A')}")
        print(f"  - 所属行业: {result.get('industry', 'N/A')}")

        # 集中度指标
        concentration = result.get('concentration', {})
        print(f"\n📈 市场集中度:")
        print(f"  - CR4: {concentration.get('cr4', 0):.2%}")
        print(f"  - CR8: {concentration.get('cr8', 0):.2%}")
        print(f"  - HHI: {concentration.get('hhi', 0):.4f}")
        print(f"  - 集中度等级: {concentration.get('concentration_level', 'N/A')}")

        # 龙头企业
        leaders = result.get('leaders', {})
        top_leaders = leaders.get('leaders', [])[:3]
        print(f"\n🏆 龙头企业 (前3名):")
        for leader in top_leaders:
            print(f"  {leader.get('rank', 0)}. {leader.get('name', 'N/A')} ({leader.get('stock_code', 'N/A')}) - 市场份额: {leader.get('market_share', 0):.1f}%")

        # 竞争地位
        position = result.get('competitive_position', {})
        print(f"\n⚔️ 竞争地位:")
        print(f"  - 地位: {position.get('position', 'N/A')}")
        print(f"  - 描述: {position.get('position_desc', 'N/A')}")
        print(f"  - 排名: {position.get('rank', 0)}")
        print(f"  - 市场份额: {position.get('market_share', 0):.1f}%")

        # LLM分析
        llm_analysis = result.get('llm_analysis', {})
        print(f"\n🤖 LLM深度分析:")
        print(f"  - 竞争态势: {llm_analysis.get('competition_status', 'N/A')}")
        print(f"  - 竞争趋势: {llm_analysis.get('competition_trend', 'N/A')}")
        key_factors = llm_analysis.get('key_success_factors', [])
        if key_factors:
            print(f"  - 关键成功因素: {', '.join(key_factors)}")

        # 综合评分
        overall_score = result.get('overall_score', {})
        print(f"\n⭐ 综合评分:")
        print(f"  - 评分: {overall_score.get('score', 0)}/100")
        print(f"  - 评级: {overall_score.get('rating', 'N/A')}")
        print(f"  - 描述: {overall_score.get('description', 'N/A')}")

        print("\n" + "=" * 80)
        print("✅ 测试完成！竞争格局AI功能正常")
        print("=" * 80)

        return result

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


@pytest.mark.asyncio
async def test_concentration_evaluation():
    """测试市场集中度评估"""
    print("\n\n" + "=" * 80)
    print("测试市场集中度评估")
    print("=" * 80)

    ai = CompetitionPatternAI()
    test_stock_code = "600519"

    try:
        print(f"\n📊 评估股票: {test_stock_code}")
        result = await ai.evaluate_concentration(stock_code=test_stock_code)

        print("\n✅ 评估完成！")
        print(f"  - 行业: {result.get('industry', 'N/A')}")
        print(f"  - CR4: {result.get('cr4', 0):.2%}")
        print(f"  - CR8: {result.get('cr8', 0):.2%}")
        print(f"  - HHI: {result.get('hhi', 0):.4f}")
        print(f"  - 集中度等级: {result.get('concentration_level', 'N/A')}")
        print(f"  - 影响: {result.get('implication', 'N/A')}")

        return result

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


@pytest.mark.asyncio
async def test_leader_identification():
    """测试龙头企业识别"""
    print("\n\n" + "=" * 80)
    print("测试龙头企业识别")
    print("=" * 80)

    ai = CompetitionPatternAI()
    test_stock_code = "600519"

    try:
        print(f"\n📊 识别龙头企业: {test_stock_code}")
        result = await ai.identify_leaders(stock_code=test_stock_code, top_n=5)

        print("\n✅ 识别完成！")
        print(f"  - 行业: {result.get('industry', 'N/A')}")
        print(f"  - 前{result.get('top_n', 0)}名企业总市场份额: {result.get('total_market_share', 0):.1f}%")
        print(f"  - 摘要: {result.get('summary', 'N/A')}")

        print(f"\n🏆 龙头企业列表:")
        for leader in result.get('leaders', []):
            print(f"  {leader.get('rank', 0)}. {leader.get('name', 'N/A')} - 市场份额: {leader.get('market_share', 0):.1f}%")

        leader_analysis = result.get('leader_analysis', {})
        print(f"\n📊 龙头特征:")
        print(f"  - 格局: {leader_analysis.get('pattern', 'N/A')}")
        print(f"  - 描述: {leader_analysis.get('description', 'N/A')}")

        return result

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


@pytest.mark.asyncio
async def test_position_assessment():
    """测试竞争地位评估"""
    print("\n\n" + "=" * 80)
    print("测试竞争地位评估")
    print("=" * 80)

    ai = CompetitionPatternAI()
    test_stock_code = "600519"

    try:
        print(f"\n📊 评估竞争地位: {test_stock_code}")
        result = await ai.assess_competitive_position(stock_code=test_stock_code)

        print("\n✅ 评估完成！")
        print(f"  - 行业: {result.get('industry', 'N/A')}")
        print(f"  - 股票名称: {result.get('stock_name', 'N/A')}")
        print(f"  - 竞争地位: {result.get('position', 'N/A')}")
        print(f"  - 地位描述: {result.get('position_desc', 'N/A')}")
        print(f"  - 排名: {result.get('rank', 0)}")
        print(f"  - 市场份额: {result.get('market_share', 0):.1f}%")

        advantage = result.get('competitive_advantage', {})
        print(f"\n💪 竞争优势:")
        print(f"  - 优势: {', '.join(advantage.get('advantages', []))}")
        print(f"  - 实力: {advantage.get('overall_strength', 'N/A')}")

        return result

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """主测试函数"""
    print("\n[START] 开始测试竞争格局AI\n")

    # 测试1：综合分析
    await test_competition_pattern_ai()

    # 测试2：集中度评估
    await test_concentration_evaluation()

    # 测试3：龙头企业识别
    await test_leader_identification()

    # 测试4：竞争地位评估
    await test_position_assessment()

    print("\n\n✅ 所有测试完成！\n")


if __name__ == "__main__":
    asyncio.run(main())
