"""
龙虎榜AI测试

测试核心功能：
1. 龙虎榜分析
2. 机构动向追踪
3. 游资动向追踪
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
from src.agents.business.hot_spot.dragon_tiger_ai import DragonTigerAI


@pytest.mark.asyncio
async def test_initialization():
    """测试1：初始化"""
    print("\n" + "="*60)
    print("测试1：龙虎榜AI初始化")
    print("="*60)

    ai = DragonTigerAI()

    print(f"✅ AI名称: {ai.name}")
    print(f"✅ AI角色: {ai.role}")
    print(f"✅ 能力数量: {len(ai.capabilities)}")
    print(f"✅ 工具数量: {len(ai.tools)}")

    # 检查核心能力
    capability_names = [cap.name for cap in ai.capabilities]
    assert "dragon_tiger_analysis" in capability_names, "缺少龙虎榜分析能力"
    assert "institution_tracking" in capability_names, "缺少机构追踪能力"
    assert "hot_money_tracking" in capability_names, "缺少游资追踪能力"

    print("✅ 初始化测试通过")


@pytest.mark.asyncio
async def test_dragon_tiger_analysis():
    """测试2：龙虎榜分析"""
    print("\n" + "="*60)
    print("测试2：龙虎榜分析")
    print("="*60)

    ai = DragonTigerAI()

    # 分析贵州茅台的龙虎榜
    result = await ai.execute(
        "analyze_dragon_tiger",
        stock_code="600519",
        days=5
    )

    print(f"\n📊 龙虎榜分析结果:")
    print(f"   股票代码: {result['stock_code']}")
    print(f"   分析周期: {result['analysis_period']}")
    print(f"   上榜次数: {result['上榜次数']}")
    print(f"   买卖模式: {result['balance_analysis']['pattern']}")
    print(f"   行为描述: {result['balance_analysis']['behavior']}")
    print(f"   净买入: {result['balance_analysis']['net_total']}万元")
    print(f"   摘要: {result['summary']}")
    print(f"   建议: {result['recommendation']}")

    # 验证结果
    assert result['stock_code'] == "600519", "股票代码不对"
    assert result['上榜次数'] >= 0, "上榜次数应该>=0"
    assert 'balance_analysis' in result, "应该有买卖力量分析"
    assert 'pattern' in result['balance_analysis'], "应该有买卖模式"

    print("\n✅ 龙虎榜分析测试通过")


@pytest.mark.asyncio
async def test_institution_tracking():
    """测试3：机构动向追踪"""
    print("\n" + "="*60)
    print("测试3：机构动向追踪")
    print("="*60)

    ai = DragonTigerAI()

    # 追踪机构动向
    result = await ai.execute(
        "track_institution",
        stock_code="600519",
        days=10
    )

    print(f"\n🏦 机构动向追踪结果:")
    print(f"   股票代码: {result['stock_code']}")
    print(f"   追踪周期: {result['tracking_period']}")
    print(f"   机构行为: {result['analysis']['behavior']}")
    print(f"   净买入: {result['analysis']['net']}万元")
    print(f"   摘要: {result['summary']}")

    # 验证结果
    assert result['stock_code'] == "600519", "股票代码不对"
    assert 'behavior' in result['analysis'], "应该有机构行为分析"
    assert 'net' in result['analysis'], "应该有净买入数据"

    print("\n✅ 机构动向追踪测试通过")


@pytest.mark.asyncio
async def test_hot_money_tracking():
    """测试4：游资动向追踪"""
    print("\n" + "="*60)
    print("测试4：游资动向追踪")
    print("="*60)

    ai = DragonTigerAI()

    # 追踪游资动向
    result = await ai.execute(
        "track_hot_money",
        stock_code="600519",
        days=5
    )

    print(f"\n💰 游资动向追踪结果:")
    print(f"   股票代码: {result['stock_code']}")
    print(f"   追踪周期: {result['tracking_period']}")
    print(f"   游资行为: {result['analysis']['behavior']}")
    print(f"   净买入: {result['analysis']['net']}万元")
    print(f"   摘要: {result['summary']}")

    # 验证结果
    assert result['stock_code'] == "600519", "股票代码不对"
    assert 'behavior' in result['analysis'], "应该有游资行为分析"
    assert 'net' in result['analysis'], "应该有净买入数据"

    print("\n✅ 游资动向追踪测试通过")


@pytest.mark.asyncio
async def test_dragon_tiger_scenarios():
    """测试5：不同龙虎榜场景"""
    print("\n" + "="*60)
    print("测试5：不同龙虎榜场景")
    print("="*60)

    ai = DragonTigerAI()

    # 场景1：强买入
    print("\n场景1：模拟强买入")
    strong_buy_data = [
        {"net_buy": 3000},
        {"net_buy": 2500},
        {"net_buy": 2800}
    ]
    analysis = ai._analyze_buy_sell_balance(strong_buy_data)
    print(f"   买卖模式: {analysis['pattern']}")
    print(f"   行为: {analysis['behavior']}")
    print(f"   净买入: {analysis['net_total']}万元")
    assert analysis['pattern'] == "strong_buy", "应该是强买入"

    # 场景2：强卖出
    print("\n场景2：模拟强卖出")
    strong_sell_data = [
        {"net_buy": -3000},
        {"net_buy": -2500},
        {"net_buy": -2800}
    ]
    analysis = ai._analyze_buy_sell_balance(strong_sell_data)
    print(f"   买卖模式: {analysis['pattern']}")
    print(f"   行为: {analysis['behavior']}")
    print(f"   净买入: {analysis['net_total']}万元")
    assert analysis['pattern'] == "strong_sell", "应该是强卖出"

    # 场景3：平衡
    print("\n场景3：模拟平衡市场")
    balanced_data = [
        {"net_buy": 100},
        {"net_buy": -50},
        {"net_buy": 80}
    ]
    analysis = ai._analyze_buy_sell_balance(balanced_data)
    print(f"   买卖模式: {analysis['pattern']}")
    print(f"   行为: {analysis['behavior']}")
    print(f"   净买入: {analysis['net_total']}万元")
    assert analysis['pattern'] in ["mild_buy", "mild_sell"], "应该是小幅买入或卖出"

    print("\n✅ 龙虎榜场景测试通过")


async def main():
    """运行所有测试"""
    print("\n" + "╔"+"═"*58+"╗")
    print("║" + " "*18 + "龙虎榜AI测试套件" + " "*18 + "║")
    print("╚"+"═"*58+"╝")

    try:
        await test_initialization()
        await test_dragon_tiger_analysis()
        await test_institution_tracking()
        await test_hot_money_tracking()
        await test_dragon_tiger_scenarios()

        print("\n" + "╔"+"═"*58+"╗")
        print("║" + " "*21 + "🎉 所有测试通过！" + " "*21 + "║")
        print("╚"+"═"*58+"╝")

        print("\n✅ 测试总结:")
        print("   - ✅ 初始化测试通过")
        print("   - ✅ 龙虎榜分析测试通过")
        print("   - ✅ 机构动向追踪测试通过")
        print("   - ✅ 游资动向追踪测试通过")
        print("   - ✅ 龙虎榜场景测试通过")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
