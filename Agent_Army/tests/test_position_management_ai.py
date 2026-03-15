"""
仓位管理AI测试

测试核心功能：
1. 仓位配置建议
2. 风险预算管理
3. 动态仓位调整
4. 分批建仓策略
5. 止盈止损策略
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
from src.agents.business.strategy.position_management_ai import PositionManagementAI


@pytest.mark.asyncio
async def test_initialization():
    """测试1：初始化"""
    print("\n" + "="*60)
    print("测试1：仓位管理AI初始化")
    print("="*60)

    ai = PositionManagementAI()

    print(f"✅ AI名称: {ai.name}")
    print(f"✅ AI角色: {ai.role}")
    print(f"✅ 能力数量: {len(ai.capabilities)}")
    print(f"✅ 工具数量: {len(ai.tools)}")

    # 检查核心能力
    capability_names = [cap.name for cap in ai.capabilities]
    assert "position_sizing" in capability_names, "缺少仓位配置能力"
    assert "risk_budgeting" in capability_names, "缺少风险预算能力"
    assert "dynamic_adjustment" in capability_names, "缺少动态调整能力"
    assert "stop_loss_take_profit" in capability_names, "缺少止盈止损能力"

    print("✅ 初始化测试通过")


@pytest.mark.asyncio
async def test_position_sizing():
    """测试2：仓位配置建议"""
    print("\n" + "="*60)
    print("测试2：仓位配置建议")
    print("="*60)

    ai = PositionManagementAI()

    result = await ai.execute(
        "analyze",
        stock_code="600519",
        current_price=1800.0,
        total_capital=100000,
        risk_tolerance="中等"
    )

    print(f"\n📊 仓位配置建议:")
    print(f"   股票代码: {result['stock_code']}")
    print(f"   当前价格: ¥{result['current_price']:.2f}")
    print(f"   总资金: ¥{result['total_capital']:.2f}")
    print(f"   风险偏好: {result['risk_tolerance']}")

    position_sizing = result['position_sizing']
    print(f"\n   仓位配置:")
    print(f"      建议仓位: {position_sizing['position_percentage']:.1f}%")
    print(f"      仓位价值: ¥{position_sizing['position_value']:.2f}")
    print(f"      建议股数: {position_sizing['shares']}股")
    print(f"      质量评分: {position_sizing['quality_score']:.1f}")
    print(f"      波动评分: {position_sizing['volatility_score']:.1f}")
    print(f"      风险系数: {position_sizing['risk_multiplier']:.1f}")

    print(f"\n   说明: {position_sizing['description']}")

    # 验证结果
    assert result['stock_code'] == "600519", "股票代码不对"
    assert 0 < position_sizing['position_percentage'] <= 25, "仓位应该在0-25%之间"
    assert position_sizing['shares'] > 0, "股数应该大于0"
    assert 0 <= position_sizing['quality_score'] <= 100, "质量评分应该在0-100之间"

    print("\n✅ 仓位配置测试通过")


@pytest.mark.asyncio
async def test_risk_budgeting():
    """测试3：风险预算管理"""
    print("\n" + "="*60)
    print("测试3：风险预算管理")
    print("="*60)

    ai = PositionManagementAI()

    result = await ai.execute(
        "analyze",
        stock_code="600519",
        current_price=1800.0,
        total_capital=100000,
        risk_tolerance="中等"
    )

    risk_budgeting = result['risk_budgeting']

    print(f"\n💰 风险预算管理:")
    print(f"   单股最大风险: {risk_budgeting['single_risk_limit']:.1f}%")
    print(f"   最大可接受损失: ¥{risk_budgeting['max_acceptable_loss']:.2f}")
    print(f"   止损价格: ¥{risk_budgeting['stop_loss_price']:.2f}")
    print(f"   止损比例: {risk_budgeting['stop_loss_percentage']:.1f}%")
    print(f"   基于风险的股数: {risk_budgeting['risk_based_shares']}股")
    print(f"   基于风险的价值: ¥{risk_budgeting['risk_based_value']:.2f}")
    print(f"   总风险预算: {risk_budgeting['total_risk_budget']:.1f}%")

    print(f"\n   说明: {risk_budgeting['description']}")

    # 验证结果
    assert 0 < risk_budgeting['single_risk_limit'] <= 5, "单股风险应该在0-5%之间"
    assert risk_budgeting['max_acceptable_loss'] > 0, "最大损失应该大于0"
    assert risk_budgeting['stop_loss_price'] < 1800.0, "止损价应该低于当前价"
    assert risk_budgeting['risk_based_shares'] > 0, "股数应该大于0"

    print("\n✅ 风险预算测试通过")


@pytest.mark.asyncio
async def test_dynamic_adjustment():
    """测试4：动态仓位调整"""
    print("\n" + "="*60)
    print("测试4：动态仓位调整")
    print("="*60)

    ai = PositionManagementAI()

    result = await ai.execute(
        "analyze",
        stock_code="600519",
        current_price=1800.0,
        total_capital=100000,
        risk_tolerance="中等"
    )

    dynamic_adjustment = result['dynamic_adjustment']

    print(f"\n🔄 动态仓位调整:")
    print(f"\n   市场环境:")
    print(f"      市场状况: {dynamic_adjustment['market_environment']['condition']}")
    print(f"      市场趋势: {dynamic_adjustment['market_environment']['trend']}")
    print(f"      置信度: {dynamic_adjustment['market_environment']['confidence']:.1f}")

    print(f"\n   个股表现:")
    print(f"      趋势: {dynamic_adjustment['stock_performance']['trend']}")
    print(f"      动量: {dynamic_adjustment['stock_performance']['momentum']}")
    print(f"      相对强度: {dynamic_adjustment['stock_performance']['relative_strength']:.1f}")

    print(f"\n   调整建议:")
    for adj in dynamic_adjustment['adjustments']:
        print(f"      因素: {adj['factor']}")
        print(f"      操作: {adj['action']}")
        print(f"      幅度: {adj['percentage']:+.1f}%")
        print(f"      理由: {adj['reason']}")

    print(f"\n   总调整幅度: {dynamic_adjustment['total_adjustment']:+.1f}%")
    print(f"   调整后仓位: {dynamic_adjustment['adjusted_position']:.1f}%")

    # 验证结果
    assert 'market_environment' in dynamic_adjustment, "缺少市场环境"
    assert 'stock_performance' in dynamic_adjustment, "缺少个股表现"
    assert 'adjustments' in dynamic_adjustment, "缺少调整建议"
    assert 0 <= dynamic_adjustment['adjusted_position'] <= 25, "调整后仓位应该在0-25%之间"

    print("\n✅ 动态调整测试通过")


@pytest.mark.asyncio
async def test_batch_strategy():
    """测试5：分批建仓策略"""
    print("\n" + "="*60)
    print("测试5：分批建仓策略")
    print("="*60)

    ai = PositionManagementAI()

    result = await ai.execute(
        "analyze",
        stock_code="600519",
        current_price=1800.0,
        total_capital=100000,
        risk_tolerance="中等"
    )

    batch_strategy = result['batch_strategy']

    print(f"\n📦 分批建仓策略:")

    print(f"\n   买入策略:")
    buy_strategy = batch_strategy['buy_strategy']
    print(f"      分批数量: {buy_strategy['batch_count']}批")
    print(f"      说明: {buy_strategy['description']}")
    for batch in buy_strategy['batches']:
        print(f"      第{batch['batch']}批: {batch['shares']}股, "
              f"¥{batch['price']:.2f}, {batch['timing']}")

    print(f"\n   卖出策略:")
    sell_strategy = batch_strategy['sell_strategy']
    print(f"      分批数量: {sell_strategy['batch_count']}批")
    print(f"      说明: {sell_strategy['description']}")
    for batch in sell_strategy['batches']:
        print(f"      第{batch['batch']}批: {batch['shares']}股, "
              f"¥{batch['price']:.2f}, {batch['timing']}")

    # 验证结果
    assert buy_strategy['batch_count'] == 3, "买入应该分3批"
    assert sell_strategy['batch_count'] == 3, "卖出应该分3批"
    assert len(buy_strategy['batches']) == 3, "买入批次不对"
    assert len(sell_strategy['batches']) == 3, "卖出批次不对"

    print("\n✅ 分批建仓测试通过")


@pytest.mark.asyncio
async def test_stop_strategy():
    """测试6：止盈止损策略"""
    print("\n" + "="*60)
    print("测试6：止盈止损策略")
    print("="*60)

    ai = PositionManagementAI()

    result = await ai.execute(
        "analyze",
        stock_code="600519",
        current_price=1800.0,
        total_capital=100000,
        risk_tolerance="中等"
    )

    stop_strategy = result['stop_strategy']

    print(f"\n🛡️ 止盈止损策略:")

    print(f"\n   止损策略:")
    stop_loss = stop_strategy['stop_loss']
    print(f"      止损价格: ¥{stop_loss['price']:.2f}")
    print(f"      止损比例: {stop_loss['percentage']:.1f}%")
    print(f"      类型: {stop_loss['type']}")
    print(f"      说明: {stop_loss['description']}")

    print(f"\n   止盈策略:")
    take_profit = stop_strategy['take_profit']
    print(f"      分级止盈:")
    for level in take_profit['levels']:
        print(f"         第{level['level']}级: ¥{level['price']:.2f} "
              f"({level['percentage']:.0f}%), {level['action']}")

    trailing_stop = take_profit['trailing_stop']
    print(f"      跟踪止盈:")
    print(f"         激活价格: ¥{trailing_stop['activation']:.2f}")
    print(f"         回撤比例: {trailing_stop['trail_percentage']:.1f}%")
    print(f"         说明: {trailing_stop['description']}")

    # 验证结果
    assert stop_loss['price'] < 1800.0, "止损价应该低于当前价"
    assert len(take_profit['levels']) == 3, "应该有3级止盈"
    assert all(level['price'] > 1800.0 for level in take_profit['levels']), \
        "止盈价应该高于当前价"

    print("\n✅ 止盈止损测试通过")


@pytest.mark.asyncio
async def test_risk_tolerance_levels():
    """测试7：不同风险偏好级别"""
    print("\n" + "="*60)
    print("测试7：不同风险偏好级别")
    print("="*60)

    ai = PositionManagementAI()

    risk_levels = ["保守", "中等", "激进"]

    for tolerance in risk_levels:
        result = await ai.execute(
            "analyze",
            stock_code="600519",
            current_price=1800.0,
            total_capital=100000,
            risk_tolerance=tolerance
        )

        position_sizing = result['position_sizing']
        risk_budgeting = result['risk_budgeting']

        print(f"\n🎯 风险偏好: {tolerance}")
        print(f"   建议仓位: {position_sizing['position_percentage']:.1f}%")
        print(f"   单股风险: {risk_budgeting['single_risk_limit']:.1f}%")
        print(f"   风险系数: {position_sizing['risk_multiplier']:.1f}")

        # 验证风险偏好影响
        if tolerance == "保守":
            assert position_sizing['risk_multiplier'] <= 0.7, "保守型风险系数应该较低"
            assert risk_budgeting['single_risk_limit'] <= 2.5, "保守型单股风险应该较低"
        elif tolerance == "激进":
            assert position_sizing['risk_multiplier'] >= 1.3, "激进型风险系数应该较高"
            assert risk_budgeting['single_risk_limit'] >= 4.5, "激进型单股风险应该较高"

    print("\n✅ 风险偏好级别测试通过")


@pytest.mark.asyncio
async def test_optimization_suggestions():
    """测试8：优化建议"""
    print("\n" + "="*60)
    print("测试8：优化建议")
    print("="*60)

    ai = PositionManagementAI()

    result = await ai.execute(
        "analyze",
        stock_code="600519",
        current_price=1800.0,
        total_capital=100000,
        risk_tolerance="中等"
    )

    optimization = result['optimization_suggestion']

    print(f"\n💡 仓位优化建议:")
    print(f"   优先级: {optimization['priority']}")
    print(f"\n   具体建议:")
    for i, suggestion in enumerate(optimization['suggestions'], 1):
        print(f"      {i}. {suggestion}")

    # 验证结果
    assert len(optimization['suggestions']) > 0, "应该有优化建议"
    assert optimization['priority'] in ["高", "中", "低"], "优先级不对"

    print("\n✅ 优化建议测试通过")


@pytest.mark.asyncio
async def test_extreme_conditions():
    """测试9：极端条件测试"""
    print("\n" + "="*60)
    print("测试9：极端条件测试")
    print("="*60)

    ai = PositionManagementAI()

    # 测试高股价低资金
    result = await ai.execute(
        "analyze",
        stock_code="600519",
        current_price=1800.0,
        total_capital=10000,  # 较低资金
        risk_tolerance="保守"
    )

    position_sizing = result['position_sizing']
    print(f"\n📉 高股价低资金测试:")
    print(f"   总资金: ¥10,000")
    print(f"   股价: ¥1,800")
    print(f"   建议股数: {position_sizing['shares']}股")
    print(f"   仓位价值: ¥{position_sizing['position_value']:.2f}")

    # 即使资金少，也应该能给出建议
    assert position_sizing['shares'] >= 0, "股数应该>=0"

    # 测试低股价高资金
    result = await ai.execute(
        "analyze",
        stock_code="600519",
        current_price=10.0,  # 较低股价
        total_capital=1000000,  # 较高资金
        risk_tolerance="激进"
    )

    position_sizing = result['position_sizing']
    print(f"\n📈 低股价高资金测试:")
    print(f"   总资金: ¥1,000,000")
    print(f"   股价: ¥10")
    print(f"   建议股数: {position_sizing['shares']}股")
    print(f"   仓位价值: ¥{position_sizing['position_value']:.2f}")

    # 应该有合理的股数限制
    assert position_sizing['shares'] > 0, "股数应该大于0"

    print("\n✅ 极端条件测试通过")


@pytest.mark.asyncio
async def test_data_completeness():
    """测试10：数据完整性"""
    print("\n" + "="*60)
    print("测试10：数据完整性")
    print("="*60)

    ai = PositionManagementAI()

    result = await ai.execute(
        "analyze",
        stock_code="600519",
        current_price=1800.0,
        total_capital=100000,
        risk_tolerance="中等"
    )

    # 检查所有必需字段
    required_fields = [
        'analysis_type', 'timestamp', 'stock_code', 'current_price',
        'total_capital', 'risk_tolerance', 'position_sizing',
        'risk_budgeting', 'dynamic_adjustment', 'batch_strategy',
        'stop_strategy', 'optimization_suggestion'
    ]

    for field in required_fields:
        assert field in result, f"缺少字段: {field}"

    # 检查position_sizing的子字段
    position_sizing = result['position_sizing']
    required_position_fields = [
        'position_percentage', 'position_value', 'shares',
        'quality_score', 'volatility_score', 'risk_multiplier',
        'description', 'update_time'
    ]

    for field in required_position_fields:
        assert field in position_sizing, f"position_sizing缺少字段: {field}"

    # 检查risk_budgeting的子字段
    risk_budgeting = result['risk_budgeting']
    required_risk_fields = [
        'single_risk_limit', 'max_acceptable_loss', 'stop_loss_price',
        'stop_loss_percentage', 'risk_based_shares', 'risk_based_value',
        'total_risk_budget', 'description', 'update_time'
    ]

    for field in required_risk_fields:
        assert field in risk_budgeting, f"risk_budgeting缺少字段: {field}"

    print(f"\n✅ 所有必需字段都存在")
    print(f"   分析类型: {result['analysis_type']}")
    print(f"   时间戳: {result['timestamp']}")
    print(f"   更新时间: {position_sizing['update_time']}")

    print("\n✅ 数据完整性测试通过")


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("仓位管理AI测试套件")
    print("="*60)

    try:
        # 运行所有测试
        await test_initialization()
        await test_position_sizing()
        await test_risk_budgeting()
        await test_dynamic_adjustment()
        await test_batch_strategy()
        await test_stop_strategy()
        await test_risk_tolerance_levels()
        await test_optimization_suggestions()
        await test_extreme_conditions()
        await test_data_completeness()

        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
