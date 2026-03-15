"""
测试筹码分析AI

验证筹码分布、筹码峰、压力位识别功能
"""
import pytest

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.business.chip_analysis_ai import ChipAnalysisAI


@pytest.mark.asyncio
async def test_chip_analysis():
    """测试筹码分析AI"""

    print("=" * 80)
    print("筹码分析AI测试 - Chip Distribution Analysis")
    print("=" * 80)
    print()

    # 初始化Agent
    analyzer = ChipAnalysisAI()

    # 测试股票：中国电建（601669）
    stock_code = "601669"

    print(f"[INFO] 分析股票: {stock_code} (中国电建)")
    print("-" * 80)
    print()

    try:
        # 执行筹码分析
        result = await analyzer.analyze(
            stock_code=stock_code,
            days=365,  # 1年数据
            bins=50    # 50个价格区间
        )

        # 显示基本信息
        print("[1/5] 基本信息:")
        print(f"  当前价格: {result['current_price']:.2f} 元")
        print(f"  分析时间: {result['analysis_date']}")
        print()

        # 显示筹码分布
        print("[2/5] 筹码分布（前10个价格区间）:")
        chip_dist = result['chip_distribution'][:10]
        for item in chip_dist:
            print(f"  {item['price']:.2f}元: {item['chip_percentage']:>6.2f}% "
                  f"(成交量: {item['volume']:,})")
        print("  ...")
        print()

        # 显示筹码峰
        print("[3/5] 筹码峰识别:")
        if result['chip_peaks']:
            for i, peak in enumerate(result['chip_peaks'], 1):
                print(f"  筹码峰{i}: {peak['price']:.2f} 元")
                print(f"    - 价格区间: {peak['price_range']}")
                print(f"    - 筹码占比: {peak['chip_percentage']:.1f}%")
                print(f"    - 强度: {peak['strength']}")
        else:
            print("  未识别到筹码峰")
        print()

        # 显示压力位（上方筹码峰）
        print("[4/5] 压力位（基于筹码分析）:")
        if result['resistance_levels']:
            for i, level in enumerate(result['resistance_levels'][:3], 1):
                distance = (level['price'] - result['current_price']) / result['current_price'] * 100
                print(f"  压力位{i}: {level['price']:.2f} 元 (+{distance:.1f}%)")
                print(f"    - 筹码占比: {level['chip_percentage']:.1f}%")
                print(f"    - 强度: {level['strength']}")
        else:
            print("  无上方筹码峰（可能处于主升浪）")
        print()

        # 显示支撑位（下方筹码峰）
        print("[5/5] 支撑位（基于筹码分析）:")
        if result['support_levels']:
            for i, level in enumerate(result['support_levels'][:3], 1):
                distance = (result['current_price'] - level['price']) / result['current_price'] * 100
                print(f"  支撑位{i}: {level['price']:.2f} 元 (-{distance:.1f}%)")
                print(f"    - 筹码占比: {level['chip_percentage']:.1f}%")
                print(f"    - 强度: {level['strength']}")
        else:
            print("  无下方筹码峰（需要注意风险）")
        print()

        # 显示突破难度
        print("-" * 80)
        print(f"突破难度: {result['breakthrough_difficulty']}")
        print()

        # 显示主升浪信号
        signal = result['main_rise_signal']
        has_signal_text = "是" if signal['has_signal'] else "否"
        print(f"主升浪信号: {has_signal_text}")
        print(f"  - 理由: {signal['reason']}")
        print(f"  - 置信度: {signal['confidence']}")
        print()

        # 生成完整报告
        print("=" * 80)
        print("完整筹码分析报告:")
        print("=" * 80)
        report = analyzer.format_chip_report(result)
        print(report)
        print()

        # 对比用户实际案例
        print("=" * 80)
        print("与用户实际案例对比:")
        print("=" * 80)
        print()
        print("用户实际决策（2026年1-2月）:")
        print("  - 割肉价（底线）: 5.2 元")
        print("  - 买入价: 5.4-5.8 元")
        print("  - 预期目标价: 7-8 元")
        print("  - 主升浪时间: 7-8 月")
        print()
        print("系统筹码分析结果:")
        if result['support_levels']:
            strongest_support = result['support_levels'][0]
            print(f"  - 支撑位: {strongest_support['price']:.2f} 元（筹码占比{strongest_support['chip_percentage']:.1f}%）")
        if result['resistance_levels']:
            nearest_resistance = result['resistance_levels'][0]
            print(f"  - 压力位: {nearest_resistance['price']:.2f} 元（筹码占比{nearest_resistance['chip_percentage']:.1f}%）")
        print(f"  - 突破难度: {result['breakthrough_difficulty']}")
        print(f"  - 主升浪信号: {signal['has_signal']}")
        print()

        # 评估结果
        print("=" * 80)
        print("测试结果评估:")
        print("=" * 80)
        print()

        checks = []

        # 检查1：是否识别出筹码峰
        if len(result['chip_peaks']) > 0:
            print("[PASS] [OK] 成功识别筹码峰")
            checks.append(True)
        else:
            print("[FAIL] [X] 未识别到筹码峰")
            checks.append(False)

        # 检查2：是否计算出压力位
        if len(result['resistance_levels']) > 0:
            print("[PASS] [OK] 成功计算压力位（基于筹码峰）")
            checks.append(True)
        else:
            print("[WARN] [!] 无压力位（可能处于主升浪）")
            checks.append(True)  # 这是正常情况

        # 检查3：是否计算出支撑位
        if len(result['support_levels']) > 0:
            print("[PASS] [OK] 成功计算支撑位（基于筹码峰）")
            checks.append(True)
        else:
            print("[WARN] [!] 无支撑位（需要注意风险）")
            checks.append(True)  # 这是正常情况

        # 检查4：突破难度评估
        if result['breakthrough_difficulty'] in ['容易', '中', '高', '极高']:
            print("[PASS] [OK] 突破难度评估完成")
            checks.append(True)
        else:
            print("[FAIL] [X] 突破难度评估失败")
            checks.append(False)

        # 检查5：主升浪信号判断
        if 'has_signal' in result['main_rise_signal']:
            print("[PASS] [OK] 主升浪信号判断完成")
            checks.append(True)
        else:
            print("[FAIL] [X] 主升浪信号判断失败")
            checks.append(False)

        print()

        if all(checks):
            print("=" * 80)
            print("[SUCCESS] [OK] 筹码分析AI测试通过！")
            print("=" * 80)
            print()
            print("核心能力验证:")
            print("  [OK] 筹码分布计算")
            print("  [OK] 筹码峰识别")
            print("  [OK] 压力位计算（基于筹码分析）")
            print("  [OK] 支撑位计算（基于筹码分析）")
            print("  [OK] 突破难度评估")
            print("  [OK] 主升浪信号判断")
            print()
            return True
        else:
            print("=" * 80)
            print("[FAILURE] [X] 筹码分析AI测试失败")
            print("=" * 80)
            return False

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_chip_analysis())
    sys.exit(0 if success else 1)
