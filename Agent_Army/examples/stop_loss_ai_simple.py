"""
止损止盈AI简化演示

展示核心功能

创建日期: 2026-03-15
"""

import asyncio
from src.agents.business.strategy.stop_loss_ai import StopLossAI


async def main():
    """运行简化演示"""
    print("\n" + "="*60)
    print("止损止盈AI - 核心功能演示")
    print("="*60)

    ai = StopLossAI()

    # 使用固定的当前价格进行演示
    current_price = 20.50
    stock_code = "601669"

    print(f"\n演示股票: {stock_code}")
    print(f"当前价格: {current_price}元")

    # 1. 固定止损
    print("\n" + "-"*60)
    print("1. 固定止损策略 (8%)")
    print("-"*60)

    result1 = await ai.fixed_stop_loss(
        stock_code=stock_code,
        current_price=current_price,
        stop_ratio=0.08
    )

    print(f"止损价格: {result1['stop_loss']['price']}元")
    print(f"止损幅度: {result1['stop_loss']['ratio']}%")
    print(f"策略说明: {result1['stop_loss']['description']}")

    # 2. 移动止损
    print("\n" + "-"*60)
    print("2. 移动止损策略 (5%)")
    print("-"*60)

    result2 = await ai.trailing_stop_loss(
        stock_code=stock_code,
        current_price=current_price,
        trailing_ratio=0.05
    )

    print(f"初始止损: {result2['stop_loss']['price']}元")
    print(f"移动规则: 止损价随价格上涨上移，不随下跌下移")
    print(f"优势: {', '.join(result2['advantages'][:2])}")

    # 3. 多级别止盈
    print("\n" + "-"*60)
    print("3. 多级别止盈策略")
    print("-"*60)

    result3 = await ai.multi_level_take_profit(
        stock_code=stock_code,
        current_price=current_price,
        investment_horizon="medium_term"
    )

    print("止盈目标:")
    for tp in result3['take_profit']:
        print(f"  第{tp['level']}目标: {tp['price']}元 (收益{tp['ratio']}%, 止盈{tp['position_ratio']}仓位)")

    # 4. 综合方案（手动构建）
    print("\n" + "-"*60)
    print("4. 综合方案演示")
    print("-"*60)

    # 手动构建综合方案
    stop_price = result1['stop_loss']['price']
    take_profits = result3['take_profit']

    print(f"入场价格: {current_price}元")
    print(f"止损价格: {stop_price}元 (8%)")
    print(f"止盈目标:")
    for tp in take_profits:
        print(f"  第{tp['level']}目标: {tp['price']}元")

    # 计算风险收益比
    risk = current_price - stop_price
    reward1 = take_profits[0]['price'] - current_price
    risk_reward_ratio = reward1 / risk if risk > 0 else 0

    print(f"\n风险分析:")
    print(f"  风险金额: {risk:.2f}元")
    print(f"  预期收益: {reward1:.2f}元 (第一目标)")
    print(f"  风险收益比: {risk_reward_ratio:.2f}")
    print(f"  评价: {'优秀' if risk_reward_ratio >= 3 else '良好' if risk_reward_ratio >= 2 else '一般'}")

    # 5. 动态调整演示
    print("\n" + "-"*60)
    print("5. 动态调整演示")
    print("-"*60)

    # 构建一个简单的当前方案
    current_plan = {
        "current_price": current_price,
        "stop_loss": {"price": stop_price},
        "take_profit": take_profits
    }

    # 模拟价格上涨
    new_price = 23.00
    print(f"原方案: 入场{current_price}元, 止损{stop_price}元")
    print(f"价格上涨到: {new_price}元")

    result5 = await ai.dynamic_adjustment(
        stock_code=stock_code,
        current_plan=current_plan,
        current_price=new_price
    )

    print(f"调整后止损: {result5['new_stop_loss']}元")
    print(f"调整原因: {', '.join(result5['adjustment_reason']) if result5['adjustment_reason'] else '无需调整'}")

    # 总结
    print("\n" + "="*60)
    print("功能总结")
    print("="*60)
    print("""
止损止盈AI提供以下核心功能:

1. 多种止损策略
   - 固定止损: 简单明确,易于执行
   - 移动止损: 保护利润,让盈利奔跑
   - ATR止损: 考虑波动性,更科学
   - 技术止损: 基于支撑位,符合技术分析

2. 多级别止盈
   - 分批止盈,锁定利润
   - 降低心理压力
   - 平衡风险收益

3. 动态调整
   - 根据市场变化调整点位
   - 保护已有利润
   - 适应趋势变化

4. 风险管理
   - 计算风险收益比
   - 提供执行清单
   - 给出调整规则
    """)

    print("\n演示完成!")


if __name__ == "__main__":
    asyncio.run(main())
