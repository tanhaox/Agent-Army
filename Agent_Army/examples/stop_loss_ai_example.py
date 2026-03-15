"""
止损止盈AI使用示例

展示如何使用止损止盈AI进行风险管理

创建日期: 2026-03-15
版本: v1.0
"""

import asyncio
import json
from src.agents.business.strategy.stop_loss_ai import StopLossAI


async def example_fixed_stop_loss():
    """示例1：固定止损策略"""
    print("\n" + "="*60)
    print("示例1：固定止损策略")
    print("="*60)

    ai = StopLossAI()

    result = await ai.fixed_stop_loss(
        stock_code="601669",
        current_price=20.50,
        stop_ratio=0.08  # 8%止损
    )

    print(f"\n股票代码: {result['stock_code']}")
    print(f"当前价格: {result['current_price']}元")
    print(f"止损价格: {result['stop_loss']['price']}元")
    print(f"止损幅度: {result['stop_loss']['ratio']}%")
    print(f"策略类型: {result['stop_loss']['type']}")
    print(f"\n优势: {', '.join(result['advantages'])}")
    print(f"风险提示: {result['risk_warning']}")


async def example_trailing_stop_loss():
    """示例2：移动止损策略"""
    print("\n" + "="*60)
    print("示例2：移动止损策略")
    print("="*60)

    ai = StopLossAI()

    result = await ai.trailing_stop_loss(
        stock_code="601669",
        current_price=20.50,
        trailing_ratio=0.05  # 5%移动止损
    )

    print(f"\n当前价格: {result['current_price']}元")
    print(f"初始止损: {result['stop_loss']['price']}元")
    print(f"\n移动规则:")
    for rule in result['trailing_rules']:
        print(f"  - {rule}")

    print(f"\n调整示例:")
    for example in result['adjustment_examples']:
        print(f"  价格涨到{example['price']}元时 → 止损移至{example['new_stop']}元")


async def example_atr_stop_loss():
    """示例3：ATR波动率止损"""
    print("\n" + "="*60)
    print("示例3：ATR波动率止损")
    print("="*60)

    ai = StopLossAI()

    result = await ai.atr_stop_loss(
        stock_code="601669",
        current_price=20.50,
        atr_multiplier=2.0
    )

    print(f"\n当前价格: {result['current_price']}元")

    # 检查是否有ATR数据
    if 'atr' in result:
        print(f"ATR值: {result['atr']}元")
        print(f"止损价格: {result['stop_loss']['price']}元")
        print(f"止损幅度: {result['stop_loss']['ratio']}%")
        print(f"\n计算公式: {result['stop_loss']['formula']}")
        print(f"\n适用场景: {result['recommended_for']}")
    else:
        # ATR计算失败，回退到固定止损
        print(f"注意: ATR计算失败，使用固定止损")
        print(f"止损价格: {result['stop_loss']['price']}元")
        print(f"止损幅度: {result['stop_loss']['ratio']}%")


async def example_multi_level_take_profit():
    """示例4：多级别止盈"""
    print("\n" + "="*60)
    print("示例4：多级别止盈策略")
    print("="*60)

    ai = StopLossAI()

    result = await ai.multi_level_take_profit(
        stock_code="601669",
        current_price=20.50,
        investment_horizon="medium_term"
    )

    print(f"\n当前价格: {result['current_price']}元")
    print(f"投资周期: {result['investment_horizon']}")
    print(f"\n止盈目标:")

    for tp in result['take_profit']:
        print(f"\n  第{tp['level']}目标:")
        print(f"    目标价: {tp['price']}元")
        print(f"    收益率: {tp['ratio']}%")
        print(f"    止盈比例: {tp['position_ratio']}%")

    print(f"\n执行策略:")
    for strategy in result['execution_strategy']:
        print(f"  [OK] {strategy}")


async def example_comprehensive_plan():
    """示例5：综合方案"""
    print("\n" + "="*60)
    print("示例5：综合止损止盈方案")
    print("="*60)

    ai = StopLossAI()

    result = await ai.comprehensive_plan(
        stock_code="601669",
        investment_horizon="medium_term"
    )

    print(f"\n{'='*60}")
    print(f"投资方案摘要")
    print(f"{'='*60}")
    print(f"\n{result['summary']}")

    print(f"\n{'='*60}")
    print(f"详细方案")
    print(f"{'='*60}")

    print(f"\n【止损设置】")
    print(f"止损价: {result['stop_loss']['price']}元")
    print(f"止损幅度: {result['stop_loss']['ratio']}%")
    print(f"策略: {result['stop_loss']['description']}")

    print(f"\n【止盈设置】")
    for tp in result['take_profit']:
        print(f"第{tp['level']}目标: {tp['price']}元 ({tp['ratio']}%)")

    print(f"\n【风险分析】")
    ra = result['risk_analysis']
    print(f"风险金额: {ra['risk_amount']}元")
    print(f"预期收益: {ra['potential_reward']}元")
    print(f"风险收益比: {ra['risk_reward_ratio']}")
    print(f"评价: {ra['evaluation']}")

    print(f"\n【执行清单】")
    for i, item in enumerate(result['execution_checklist'], 1):
        print(f"{i}. {item}")

    print(f"\n【调整规则】")
    for rule in result['adjustment_rules']:
        print(f"  • {rule}")


async def example_dynamic_adjustment():
    """示例6：动态调整"""
    print("\n" + "="*60)
    print("示例6：动态调整止损止盈")
    print("="*60)

    ai = StopLossAI()

    # 初始方案
    initial_plan = await ai.comprehensive_plan(
        stock_code="601669",
        investment_horizon="medium_term"
    )

    print(f"\n初始方案:")
    print(f"  当前价: {initial_plan['current_price']}元")
    print(f"  止损价: {initial_plan['stop_loss']['price']}元")

    # 模拟价格上涨到23.00元
    print(f"\n股价上涨至23.00元，重新评估...")
    adjusted_plan = await ai.dynamic_adjustment(
        stock_code="601669",
        current_plan=initial_plan,
        current_price=23.00
    )

    print(f"\n调整后方案:")
    print(f"  新价格: {adjusted_plan['current_price']}元")
    print(f"  价格变化: {adjusted_plan['price_change']:+.2f}%")
    print(f"  原止损: {adjusted_plan['old_stop_loss']}元")
    print(f"  新止损: {adjusted_plan['new_stop_loss']}元")
    print(f"  状态: {adjusted_plan['action_required']}")

    if adjusted_plan['adjustment_reason']:
        print(f"\n调整原因:")
        for reason in adjusted_plan['adjustment_reason']:
            print(f"  • {reason}")


async def example_different_horizons():
    """示例7：不同投资周期的方案对比"""
    print("\n" + "="*60)
    print("示例7：不同投资周期方案对比")
    print("="*60)

    ai = StopLossAI()
    horizons = ["short_term", "medium_term", "long_term"]

    print(f"\n{'周期':<12} {'止损幅度':<10} {'第一目标':<10} {'持仓周期':<15}")
    print("-" * 60)

    for horizon in horizons:
        result = await ai.comprehensive_plan(
            stock_code="601669",
            investment_horizon=horizon
        )

        stop_ratio = result['stop_loss']['ratio']
        first_target = result['take_profit'][0]['ratio']
        holding_period = result['holding_period']

        print(f"{horizon:<12} {stop_ratio:<10.1f}% {first_target:<10.1f}% {holding_period:<15}")


async def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("止损止盈AI - 功能演示")
    print("="*60)

    try:
        await example_fixed_stop_loss()
        await example_trailing_stop_loss()
        await example_atr_stop_loss()
        await example_multi_level_take_profit()
        await example_comprehensive_plan()
        await example_dynamic_adjustment()
        await example_different_horizons()

        print("\n" + "="*60)
        print("所有示例运行完成！")
        print("="*60)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
