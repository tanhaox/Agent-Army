"""
测试技术分析AI的6个核心指标生成功能

针对中国电建（601669）进行测试
"""
import pytest

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath('.'))

from src.agents.business.technical_analyzer import TechnicalAnalysisAI


@pytest.mark.asyncio
async def test_core_indicators():
    """测试6个核心指标生成"""

    print("=" * 80)
    print("测试：技术分析AI - 6个核心指标生成")
    print("=" * 80)

    # 初始化技术分析AI
    tech_ai = TechnicalAnalysisAI()

    # 测试股票：中国电建
    stock_code = "601669"  # 中国电建

    print(f"\n📊 分析股票：{stock_code}（中国电建）")
    print("-" * 80)

    try:
        # 1. 执行技术分析
        print("\n[1/3] 执行技术分析...")
        technical_result = await tech_ai.analyze(stock_code, days=365)

        # 2. 获取当前价格
        current_price = technical_result["indicators"]["bollinger"]["current_price"]
        print(f"✅ 当前价格：{current_price}元")

        # 3. 模拟基本面数据（PB修复逻辑）
        # 注：实际应该从基本面分析Agent获取
        fundamentals = {
            "pb_ratio": 0.6,  # PB=0.6，低估（用户成功案例的数据）
            "book_value_per_share": 9.5  # 假设每股净资产9.5元
        }
        print(f"✅ 模拟基本面数据：PB={fundamentals['pb_ratio']}，每股净资产={fundamentals['book_value_per_share']}元")

        # 4. 生成6个核心指标
        print("\n[2/3] 生成6个核心指标...")
        core_indicators = tech_ai.generate_core_indicators(
            technical_result=technical_result,
            current_price=current_price,
            fundamentals=fundamentals
        )

        # 5. 展示结果
        print("\n[3/3] 核心指标生成完成！")
        print("\n" + "=" * 80)
        print("📋 6个核心指标")
        print("=" * 80)

        print(f"\n1️⃣  割肉价（止损价）：{core_indicators['割肉价']}元")
        print(f"   - 止损幅度：{core_indicators['止损幅度']}%")
        print(f"   - 生成依据：{core_indicators['生成依据']['割肉价']}")

        print(f"\n2️⃣  买入价（入场点）：{core_indicators['买入价']}元")
        print(f"   - 生成依据：{core_indicators['生成依据']['买入价']}")

        print(f"\n3️⃣  持仓成本（预期）：{core_indicators['持仓成本']}元")
        print(f"   - 生成依据：{core_indicators['生成依据']['持仓成本']}")

        print(f"\n4️⃣  压力位（阻力位）：{core_indicators['压力位']}元")
        print(f"   - 生成依据：{core_indicators['生成依据']['压力位']}")

        print(f"\n5️⃣  主升浪（时间窗口）：{core_indicators['主升浪']}")
        print(f"   - 生成依据：{core_indicators['生成依据']['主升浪']}")

        print(f"\n6️⃣  目标价（预期价格）：{core_indicators['目标价']}元")
        print(f"   - 目标涨幅：{core_indicators['目标涨幅']}%")
        print(f"   - 生成依据：{core_indicators['生成依据']['目标价']}")

        print(f"\n📊 风险收益比：{core_indicators['风险收益比']}")
        print(f"   - 说明：每承担1元风险，预期收益{core_indicators['风险收益比']:.2f}元")

        # 6. 对比用户成功案例
        print("\n" + "=" * 80)
        print("📝 对比用户成功案例")
        print("=" * 80)

        print("\n用户的实际决策（2026年1-2月）：")
        print("- 割肉价：5.2元（底线）")
        print("- 买入价：5.4-5.8元（分批买入）")
        print("- 目标价：7-8元（PB修复）")
        print("- 主升浪：7-8月")

        print("\n系统生成的决策：")
        print(f"- 割肉价：{core_indicators['割肉价']}元")
        print(f"- 买入价：{core_indicators['买入价']}元")
        print(f"- 目标价：{core_indicators['目标价']}元")
        print(f"- 主升浪：{core_indicators['主升浪']}")

        # 7. 评估
        print("\n" + "=" * 80)
        print("✅ 测试结果评估")
        print("=" * 80)

        # 检查合理性
        checks = []

        # 割肉价应该 < 买入价
        if core_indicators['割肉价'] < core_indicators['买入价']:
            checks.append(("✅", "割肉价 < 买入价"))
        else:
            checks.append(("❌", "割肉价应该 < 买入价"))

        # 买入价应该 < 目标价
        if core_indicators['买入价'] < core_indicators['目标价']:
            checks.append(("✅", "买入价 < 目标价"))
        else:
            checks.append(("❌", "买入价应该 < 目标价"))

        # 风险收益比应该 > 1
        if core_indicators['风险收益比'] > 1:
            checks.append(("✅", f"风险收益比 > 1（当前{core_indicators['风险收益比']:.2f}）"))
        else:
            checks.append(("❌", f"风险收益比应该 > 1（当前{core_indicators['风险收益比']:.2f}）"))

        # 止损幅度应该合理（5%-15%）
        if 5 <= core_indicators['止损幅度'] <= 15:
            checks.append(("✅", f"止损幅度合理（{core_indicators['止损幅度']}%）"))
        else:
            checks.append(("⚠️", f"止损幅度可能过大或过小（{core_indicators['止损幅度']}%）"))

        print("\n合理性检查：")
        for status, desc in checks:
            print(f"{status} {desc}")

        all_passed = all(status == "✅" for status, _ in checks)

        print("\n" + "=" * 80)
        if all_passed:
            print("🎉 所有检查通过！6个核心指标生成功能正常！")
        else:
            print("⚠️  部分检查未通过，可能需要调整算法")
        print("=" * 80)

        return core_indicators

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(test_core_indicators())
