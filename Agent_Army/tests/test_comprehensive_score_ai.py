"""
综合评分AI测试

测试核心功能：
1. 综合评分计算
2. 维度分析
3. 投资建议生成
"""
import pytest

import sys
import os
from pathlib import Path

# Windows控制台UTF-8编码支持
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    os.system('chcp 65001 > nul 2>&1')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.agents.business.target.comprehensive_score_ai import ComprehensiveScoreAI


@pytest.mark.asyncio
async def test_initialization():
    """测试1：初始化"""
    print("\n" + "="*60)
    print("测试1：综合评分AI初始化")
    print("="*60)

    ai = ComprehensiveScoreAI()

    print(f"✅ AI名称: {ai.name}")
    print(f"✅ AI角色: {ai.role}")
    print(f"✅ 能力数量: {len(ai.capabilities)}")
    print(f"✅ 工具数量: {len(ai.tools)}")

    # 检查核心能力
    capability_names = [cap.name for cap in ai.capabilities]
    assert "comprehensive_scoring" in capability_names, "缺少综合评分能力"
    assert "dimension_analysis" in capability_names, "缺少维度分析能力"
    assert "investment_recommendation" in capability_names, "缺少投资建议能力"

    print("✅ 初始化测试通过")


@pytest.mark.asyncio
async def test_comprehensive_scoring():
    """测试2：综合评分计算"""
    print("\n" + "="*60)
    print("测试2：综合评分计算")
    print("="*60)

    ai = ComprehensiveScoreAI()

    # 计算贵州茅台的综合评分
    result = await ai.execute(
        "calculate_score",
        stock_code="600519"
    )

    print(f"\n⭐ 综合评分结果:")
    print(f"   股票代码: {result['stock_code']}")
    print(f"   综合评分: {result['comprehensive_score']}")
    print(f"   评级: {result['rating']}")
    print(f"\n   各维度评分:")

    for dim_name, dim_data in result['dimension_scores'].items():
        print(f"      {dim_name}: {dim_data['score']}分 (权重{dim_data['weight']*100:.0f}%)")

    print(f"\n   摘要: {result['summary']}")
    print(f"   建议: {result['recommendation']}")

    # 验证结果
    assert result['stock_code'] == "600519", "股票代码不对"
    assert 0 <= result['comprehensive_score'] <= 100, "评分应该在0-100之间"
    assert result['rating'] in ["强烈推荐", "推荐", "中性", "谨慎", "不推荐"], "评级不对"

    print("\n✅ 综合评分测试通过")


@pytest.mark.asyncio
async def test_dimension_analysis():
    """测试3：维度分析"""
    print("\n" + "="*60)
    print("测试3：维度分析")
    print("="*60)

    ai = ComprehensiveScoreAI()

    # 分析各维度
    result = await ai.execute(
        "analyze_dimensions",
        stock_code="600519"
    )

    print(f"\n📊 维度分析结果:")
    print(f"   股票代码: {result['stock_code']}")
    print(f"   维度数量: {result['dimension_count']}")
    print(f"\n   各维度详情:")

    for dim_name, dim_info in result['dimensions'].items():
        print(f"\n   【{dim_name}】")
        print(f"      分析: {dim_info['analysis']}")
        print(f"      数据: {dim_info['data']}")

    # 验证结果
    assert result['stock_code'] == "600519", "股票代码不对"
    assert result['dimension_count'] == 4, "应该有4个维度"

    print("\n✅ 维度分析测试通过")


@pytest.mark.asyncio
async def test_investment_recommendation():
    """测试4：投资建议"""
    print("\n" + "="*60)
    print("测试4：投资建议")
    print("="*60)

    ai = ComprehensiveScoreAI()

    # 获取投资建议
    result = await ai.execute(
        "get_recommendation",
        stock_code="600519"
    )

    print(f"\n💡 投资建议:")
    print(f"   股票代码: {result['stock_code']}")
    print(f"   综合评分: {result['score']}")
    print(f"   评级: {result['rating']}")
    print(f"   操作建议: {result['action']}")
    print(f"   置信度: {result['confidence']}%")
    print(f"\n   推荐理由:")
    for reason in result['reasons']:
        print(f"      - {reason}")
    print(f"\n   风险提示:")
    for risk in result['risks']:
        print(f"      - {risk}")
    print(f"\n   详细建议:\n{result['suggestion']}")

    # 验证结果
    assert result['stock_code'] == "600519", "股票代码不对"
    assert result['action'] in ["强烈买入", "买入", "持有", "观望", "卖出"], "操作建议不对"
    assert 0 <= result['confidence'] <= 100, "置信度应该在0-100之间"

    print("\n✅ 投资建议测试通过")


@pytest.mark.asyncio
async def test_score_scenarios():
    """测试5：不同评分场景"""
    print("\n" + "="*60)
    print("测试5：不同评分场景")
    print("="*60)

    ai = ComprehensiveScoreAI()

    # 场景1：优秀股票
    print("\n场景1：模拟优秀股票")
    excellent_dimensions = {
        "基本面": {"财务健康": 85, "盈利能力": 80, "成长性": 75, "估值水平": 70},
        "技术面": {"趋势强度": 75, "成交量": 80, "技术指标": 70},
        "资金面": {"主力资金": 80, "北向资金": 75, "融资余额": 70},
        "情绪面": {"市场热度": 85, "机构评级": 80, "舆情情感": 75}
    }
    scores = ai._calculate_dimension_scores(excellent_dimensions)
    score = ai._calculate_comprehensive_score(scores)
    rating = ai._get_rating(score)
    print(f"   综合评分: {score}分")
    print(f"   评级: {rating}")
    assert score >= 75, "优秀股票评分应该>=75"

    # 场景2：中等股票
    print("\n场景2：模拟中等股票")
    average_dimensions = {
        "基本面": {"财务健康": 65, "盈利能力": 60, "成长性": 55, "估值水平": 50},
        "技术面": {"趋势强度": 60, "成交量": 65, "技术指标": 55},
        "资金面": {"主力资金": 55, "北向资金": 60, "融资余额": 65},
        "情绪面": {"市场热度": 50, "机构评级": 55, "舆情情感": 60}
    }
    scores = ai._calculate_dimension_scores(average_dimensions)
    score = ai._calculate_comprehensive_score(scores)
    rating = ai._get_rating(score)
    print(f"   综合评分: {score}分")
    print(f"   评级: {rating}")
    assert 55 <= score <= 75, "中等股票评分应该在55-75之间"

    # 场景3：较差股票
    print("\n场景3：模拟较差股票")
    poor_dimensions = {
        "基本面": {"财务健康": 40, "盈利能力": 35, "成长性": 30, "估值水平": 25},
        "技术面": {"趋势强度": 35, "成交量": 40, "技术指标": 30},
        "资金面": {"主力资金": 30, "北向资金": 35, "融资余额": 40},
        "情绪面": {"市场热度": 25, "机构评级": 30, "舆情情感": 35}
    }
    scores = ai._calculate_dimension_scores(poor_dimensions)
    score = ai._calculate_comprehensive_score(scores)
    rating = ai._get_rating(score)
    print(f"   综合评分: {score}分")
    print(f"   评级: {rating}")
    assert score < 55, "较差股票评分应该<55"

    print("\n✅ 评分场景测试通过")


async def main():
    """运行所有测试"""
    print("\n" + "╔"+"═"*58+"╗")
    print("║" + " "*18 + "综合评分AI测试套件" + " "*18 + "║")
    print("╚"+"═"*58+"╝")

    try:
        await test_initialization()
        await test_comprehensive_scoring()
        await test_dimension_analysis()
        await test_investment_recommendation()
        await test_score_scenarios()

        print("\n" + "╔"+"═"*58+"╗")
        print("║" + " "*21 + "🎉 所有测试通过！" + " "*21 + "║")
        print("╚"+"═"*58+"╝")

        print("\n✅ 测试总结:")
        print("   - ✅ 初始化测试通过")
        print("   - ✅ 综合评分测试通过")
        print("   - ✅ 维度分析测试通过")
        print("   - ✅ 投资建议测试通过")
        print("   - ✅ 评分场景测试通过")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
