"""
测试技术分析AI的6个核心指标生成功能

针对中国电建（601669）进行测试
"""
import pytest

import asyncio
import sys
import os

# 设置UTF-8编码（如果可能）
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath('.'))

from src.agents.business.technical_analyzer import TechnicalAnalysisAI


@pytest.mark.asyncio
async def test_core_indicators():
    """测试6个核心指标生成"""

    print("=" * 80)
    print("TEST: Technical Analysis AI - 6 Core Indicators Generation")
    print("=" * 80)

    # 初始化技术分析AI
    tech_ai = TechnicalAnalysisAI()

    # 测试股票：中国电建
    stock_code = "601669"  # 中国电建

    print(f"\n[INFO] Analyzing stock: {stock_code} (China Energy Engineering Group)")
    print("-" * 80)

    try:
        # 1. 执行技术分析
        print("\n[1/3] Running technical analysis...")
        technical_result = await tech_ai.analyze(stock_code, days=365)

        # 2. 获取当前价格
        current_price = technical_result["indicators"]["bollinger"]["current_price"]
        print(f"[OK] Current price: {current_price} RMB")

        # 3. 模拟基本面数据（PB修复逻辑）
        # 注：实际应该从基本面分析Agent获取
        fundamentals = {
            "pb_ratio": 0.6,  # PB=0.6，低估（用户成功案例的数据）
            "book_value_per_share": 9.5  # 假设每股净资产9.5元
        }
        print(f"[OK] Simulated fundamentals: PB={fundamentals['pb_ratio']}, Book Value={fundamentals['book_value_per_share']} RMB")

        # 4. 生成6个核心指标
        print("\n[2/3] Generating 6 core indicators...")
        core_indicators = tech_ai.generate_core_indicators(
            technical_result=technical_result,
            current_price=current_price,
            fundamentals=fundamentals
        )

        # 5. 展示结果
        print("\n[3/3] Core indicators generated!")
        print("\n" + "=" * 80)
        print("6 CORE INDICATORS")
        print("=" * 80)

        print(f"\n[1] Stop Loss Price: {core_indicators['割肉价']} RMB")
        print(f"    - Stop Loss %: {core_indicators['止损幅度']}%")
        print(f"    - Basis: {core_indicators['生成依据']['割肉价']}")

        print(f"\n[2] Buy Price: {core_indicators['买入价']} RMB")
        print(f"    - Basis: {core_indicators['生成依据']['买入价']}")

        print(f"\n[3] Position Cost: {core_indicators['持仓成本']} RMB")
        print(f"    - Basis: {core_indicators['生成依据']['持仓成本']}")

        print(f"\n[4] Resistance Price: {core_indicators['压力位']} RMB")
        print(f"    - Basis: {core_indicators['生成依据']['压力位']}")

        print(f"\n[5] Main Rise Window: {core_indicators['主升浪']}")
        print(f"    - Basis: {core_indicators['生成依据']['主升浪']}")

        print(f"\n[6] Target Price: {core_indicators['目标价']} RMB")
        print(f"    - Target Gain %: {core_indicators['目标涨幅']}%")
        print(f"    - Basis: {core_indicators['生成依据']['目标价']}")

        print(f"\n[RISK/REWARD RATIO]: {core_indicators['风险收益比']}")
        print(f"    - Explanation: For every 1 RMB risk, expect {core_indicators['风险收益比']:.2f} RMB return")

        # 6. 对比用户成功案例
        print("\n" + "=" * 80)
        print("COMPARISON WITH USER'S SUCCESS CASE")
        print("=" * 80)

        print("\nUser's actual decision (Jan-Feb 2026):")
        print("- Stop Loss: 5.2 RMB (bottom line)")
        print("- Buy Price: 5.4-5.8 RMB (batch buying)")
        print("- Target Price: 7-8 RMB (PB recovery)")
        print("- Main Rise: July-August")

        print("\nSystem generated decision:")
        print(f"- Stop Loss: {core_indicators['割肉价']} RMB")
        print(f"- Buy Price: {core_indicators['买入价']} RMB")
        print(f"- Target Price: {core_indicators['目标价']} RMB")
        print(f"- Main Rise: {core_indicators['主升浪']}")

        # 7. 评估
        print("\n" + "=" * 80)
        print("TEST RESULT EVALUATION")
        print("=" * 80)

        # 检查合理性
        checks = []

        # 割肉价应该 < 买入价
        if core_indicators['割肉价'] < core_indicators['买入价']:
            checks.append(("PASS", "Stop Loss < Buy Price"))
        else:
            checks.append(("FAIL", "Stop Loss should < Buy Price"))

        # 买入价应该 < 目标价
        if core_indicators['买入价'] < core_indicators['目标价']:
            checks.append(("PASS", "Buy Price < Target Price"))
        else:
            checks.append(("FAIL", "Buy Price should < Target Price"))

        # 风险收益比应该 > 1
        if core_indicators['风险收益比'] > 1:
            checks.append(("PASS", f"Risk/Reward Ratio > 1 (current {core_indicators['风险收益比']:.2f})"))
        else:
            checks.append(("FAIL", f"Risk/Reward Ratio should > 1 (current {core_indicators['风险收益比']:.2f})"))

        # 止损幅度应该合理（5%-15%）
        if 5 <= core_indicators['止损幅度'] <= 15:
            checks.append(("PASS", f"Stop Loss % reasonable ({core_indicators['止损幅度']}%)"))
        else:
            checks.append(("WARN", f"Stop Loss % may be too large/small ({core_indicators['止损幅度']}%)"))

        print("\nRationality Checks:")
        for status, desc in checks:
            print(f"[{status}] {desc}")

        all_passed = all(status == "PASS" for status, _ in checks)

        print("\n" + "=" * 80)
        if all_passed:
            print("[SUCCESS] All checks passed! 6 core indicators generation works correctly!")
        else:
            print("[WARNING] Some checks failed, algorithm may need adjustment")
        print("=" * 80)

        return core_indicators

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(test_core_indicators())
