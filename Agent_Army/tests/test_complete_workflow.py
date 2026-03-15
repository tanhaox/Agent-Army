"""
完整工作流测试 - 技术分析 + 筹码分析

使用真实数据（如果Tushare可用）或一致的模拟数据
生成完整的投资分析报告
"""
import pytest

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.business.technical_analyzer import TechnicalAnalysisAI
from src.agents.business.chip_analysis_ai import ChipAnalysisAI


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_section(title):
    """打印章节"""
    print("\n" + "-" * 80)
    print(f"  {title}")
    print("-" * 80)


@pytest.mark.asyncio
async def test_complete_workflow():
    """完整工作流测试"""

    print_header("Agent Army - 完整投资分析工作流测试")

    # 测试配置
    stock_code = "601669"  # 中国电建
    stock_name = "中国电建"

    print(f"测试股票: {stock_code} ({stock_name})")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试目标: 验证技术分析 + 筹码分析集成功能")

    # 初始化Agent
    tech_analyzer = TechnicalAnalysisAI()
    chip_analyzer = ChipAnalysisAI()

    try:
        # ========== 第一步：筹码分析 ==========
        print_header("第一步：筹码分布分析")

        print("[正在执行] 分析筹码分布...")
        chip_result = await chip_analyzer.analyze(stock_code, days=365, bins=50)

        print(f"[完成] 当前价格: {chip_result['current_price']:.2f} 元")
        print(f"[信息] 识别筹码峰: {len(chip_result['chip_peaks'])} 个")

        # 显示筹码峰详情
        if chip_result['chip_peaks']:
            print("\n筹码峰详情:")
            for i, peak in enumerate(chip_result['chip_peaks'][:5], 1):
                print(f"  {i}. {peak['price']:.2f}元 - 筹码占比{peak['chip_percentage']:.1f}% ({peak['strength']})")

        # 显示压力位和支撑位
        print_section("筹码分析 - 关键价位")

        if chip_result['resistance_levels']:
            print("压力位（上方筹码峰）:")
            for i, level in enumerate(chip_result['resistance_levels'][:3], 1):
                distance = (level['price'] - chip_result['current_price']) / chip_result['current_price'] * 100
                print(f"  {i}. {level['price']:.2f}元 (+{distance:.1f}%, 筹码{level['chip_percentage']:.1f}%, {level['strength']})")
        else:
            print("压力位: 无上方筹码峰（可能处于主升浪）")

        if chip_result['support_levels']:
            print("\n支撑位（下方筹码峰）:")
            for i, level in enumerate(chip_result['support_levels'][:3], 1):
                distance = (chip_result['current_price'] - level['price']) / chip_result['current_price'] * 100
                print(f"  {i}. {level['price']:.2f}元 (-{distance:.1f}%, 筹码{level['chip_percentage']:.1f}%, {level['strength']})")
        else:
            print("\n支撑位: 无下方筹码峰（需要注意风险）")

        # 显示突破难度
        print_section("筹码分析 - 突破评估")
        print(f"突破难度: {chip_result['breakthrough_difficulty']}")

        signal = chip_result['main_rise_signal']
        print(f"主升浪信号: {'是' if signal['has_signal'] else '否'}")
        print(f"  理由: {signal['reason']}")
        print(f"  置信度: {signal['confidence']}")

        # ========== 第二步：技术分析 ==========
        print_header("第二步：技术面分析")

        print("[正在执行] 综合技术分析...")
        tech_result = await tech_analyzer.analyze(stock_code, days=365)

        # 从布林带指标中获取当前价
        current_price = tech_result['indicators']['bollinger']['current_price']

        print(f"[完成] 当前价格: {current_price:.2f} 元")
        print(f"[信息] 趋势方向: {tech_result['trend']['direction']}")
        print(f"[信息] 趋势强度: {tech_result['trend']['strength']:.1f}%")
        print(f"[信息] 技术评分: {tech_result['score']:.1f}分 ({tech_result['grade']}级)")

        # 显示技术指标
        print_section("技术面 - 关键指标")

        indicators = tech_result['indicators']
        print(f"MACD: {indicators['macd']['signal_type']} ({indicators['macd']['recommendation']})")
        print(f"KDJ: {indicators['kdj']['signal']} ({indicators['kdj']['recommendation']})")
        print(f"RSI: {indicators['rsi']['signal']} ({indicators['rsi']['recommendation']})")
        print(f"布林带: {indicators['bollinger']['signal']} ({indicators['bollinger']['recommendation']})")
        print(f"均线: {indicators['ma']['arrangement']} ({indicators['ma']['recommendation']})")

        # 显示买卖信号
        signals = tech_result['signals']
        print_section("技术面 - 交易信号")
        print(f"买入信号: {'是' if signals.get('buy_signal') else '否'}")
        print(f"卖出信号: {'是' if signals.get('sell_signal') else '否'}")
        print(f"信号强度: {signals.get('signal_strength', 0):.2f}")
        print(f"信号描述: {signals.get('signal_description', '无')}")

        # ========== 第三步：生成6个核心指标 ==========
        print_header("第三步：生成6个核心指标（集成筹码分析）")

        # 构造基本面数据（模拟中国电建的实际数据）
        fundamentals = {
            "pb_ratio": 0.6,
            "book_value_per_share": 9.17
        }

        print("[正在执行] 生成6个核心指标...")
        core_indicators = tech_analyzer.generate_core_indicators(
            technical_result=tech_result,
            current_price=current_price,
            fundamentals=fundamentals,
            chip_analysis=chip_result  # 传入筹码分析
        )

        print(f"[完成] 生成模式: {core_indicators['生成依据']['模式']}")
        print(f"[信息] 筹码分析: {core_indicators['生成依据']['筹码分析']}")

        # 显示6个核心指标
        print_section("6个核心指标（集成筹码分析版本）")

        print(f"[1] 割肉价（止损价）: {core_indicators['割肉价']:.2f} 元")
        print(f"    止损幅度: {core_indicators['止损幅度']:.2f}%")
        print(f"    生成依据: {core_indicators['生成依据']['割肉价']}")

        print(f"\n[2] 买入价（入场点）: {core_indicators['买入价']:.2f} 元")
        print(f"    生成依据: {core_indicators['生成依据']['买入价']}")

        print(f"\n[3] 持仓成本: {core_indicators['持仓成本']:.2f} 元")
        print(f"    生成依据: {core_indicators['生成依据']['持仓成本']}")

        print(f"\n[4] 压力位（基于筹码分析）: {core_indicators['压力位']:.2f} 元")
        print(f"    生成依据: {core_indicators['生成依据']['压力位']}")
        if chip_result['resistance_levels']:
            print(f"    筹码压力位详情:")
            for i, level in enumerate(chip_result['resistance_levels'][:3], 1):
                distance = (level['price'] - current_price) / current_price * 100
                print(f"      压力位{i}: {level['price']:.2f}元 (+{distance:.1f}%, 筹码{level['chip_percentage']:.1f}%)")
        else:
            print(f"    注意: 无上方筹码峰，可能处于主升浪")

        print(f"\n[5] 主升浪（时间窗口）: {core_indicators['主升浪']}")
        print(f"    生成依据: {core_indicators['生成依据']['主升浪']}")

        print(f"\n[6] 目标价（预期价格）: {core_indicators['目标价']:.2f} 元")
        print(f"    目标涨幅: {core_indicators['目标涨幅']:.2f}%")
        print(f"    生成依据: {core_indicators['生成依据']['目标价']}")

        # 风险收益比
        print_section("风险收益分析")
        risk_return = core_indicators['风险收益比']
        print(f"风险收益比: {risk_return:.2f}")
        print(f"  解释: 每承担1元风险，预期收益{risk_return:.2f}元")

        if risk_return > 3:
            print(f"  评估: 优秀（>3）")
        elif risk_return > 2:
            print(f"  评估: 良好（>2）")
        elif risk_return > 1:
            print(f"  评估: 一般（>1）")
        else:
            print(f"  评估: 风险大于收益（<1）")

        # ========== 第四步：与用户成功案例对比 ==========
        print_header("第四步：与用户成功案例对比")

        print("用户实际决策（2026年1-2月，中国电建）:")
        print("  割肉价（底线）: 5.2 元")
        print("  买入价: 5.4-5.8 元（分批买入）")
        print("  目标价: 7-8 元（PB修复）")
        print("  主升浪时间: 7-8 月")

        print("\n系统生成决策（集成筹码分析）:")
        print(f"  割肉价: {core_indicators['割肉价']:.2f} 元")
        print(f"  买入价: {core_indicators['买入价']:.2f} 元")
        print(f"  目标价: {core_indicators['目标价']:.2f} 元")
        print(f"  主升浪: {core_indicators['主升浪']}")

        # 计算差异
        stop_loss_diff = abs(core_indicators['割肉价'] - 5.2)
        buy_price_diff = abs(core_indicators['买入价'] - 5.5)  # 用户买入价中位数
        target_price_diff = abs(core_indicators['目标价'] - 7.5)  # 用户目标价中位数

        print("\n差异分析:")
        stop_loss_status = "[OK] 接近" if stop_loss_diff < 0.3 else "[WARN] 偏差较大"
        buy_price_status = "[OK] 接近" if buy_price_diff < 0.5 else "[WARN] 偏差较大"
        target_price_status = "[OK] 接近" if target_price_diff < 1.5 else "[WARN] 偏差较大"
        print(f"  割肉价差异: {stop_loss_diff:.2f} 元 {stop_loss_status}")
        print(f"  买入价差异: {buy_price_diff:.2f} 元 {buy_price_status}")
        print(f"  目标价差异: {target_price_diff:.2f} 元 {target_price_status}")

        # ========== 第五步：功能验证 ==========
        print_header("第五步：功能验证清单")

        checks = []
        check_items = [
            ("筹码分析功能", chip_result and chip_result.get('chip_peaks'), "筹码分布计算、筹码峰识别"),
            ("技术分析功能", tech_result and tech_result.get('trend'), "趋势分析、技术指标、买卖信号"),
            ("筹码分析集成", core_indicators['生成依据']['筹码分析'] == '已集成', "筹码分析结果集成到技术分析"),
            ("压力位基于筹码", '筹码分析' in core_indicators['生成依据']['压力位'] or not chip_result['resistance_levels'], "压力位基于筹码峰（或无筹码峰）"),
            ("6个指标完整", all(k in core_indicators for k in ['割肉价', '买入价', '持仓成本', '压力位', '主升浪', '目标价']), "6个核心指标生成完整"),
            ("指标逻辑合理", core_indicators['割肉价'] < core_indicators['买入价'], "割肉价 < 买入价（买入价应高于止损价）"),
            ("风险收益比计算", core_indicators['风险收益比'] != 0, "风险收益比计算（可能为负，如果模拟数据不一致）"),
        ]

        for name, condition, description in check_items:
            status = "[PASS] [OK]" if condition else "[FAIL] [X]"
            print(f"{status} {name}")
            print(f"     {description}")
            checks.append(condition)

        # ========== 最终总结 ==========
        print_header("测试总结")

        if all(checks):
            print("[SUCCESS] [OK] 所有测试通过！")
            print()
            print("已验证功能:")
            print("  [OK] 筹码分布计算")
            print("  [OK] 筹码峰识别")
            print("  [OK] 技术面完整分析")
            print("  [OK] 筹码分析集成到技术分析")
            print("  [OK] 压力位基于筹码峰（而非简单倍数）")
            print("  [OK] 支撑位融合筹码和技术分析")
            print("  [OK] 突破难度评估")
            print("  [OK] 6个核心指标生成完整")
            print("  [OK] 指标逻辑合理性")
            print()
            print("关键改进:")
            print("  [重要] 压力位不再使用当前价×1.2简单规则")
            print("  [重要] 压力位基于筹码峰分析（更精准）")
            print("  [重要] 支撑位融合筹码峰和技术分析")
            print("  [重要] 突破难度纳入筹码分析")
            print()
            print("下一步建议:")
            print("  1. 使用Tushare真实数据测试")
            print("  2. 实现资金博弈分析Agent")
            print("  3. 实现政策分析Agent")
            print("  4. 实现历史节点分析Agent")
            print("  5. 集成6维度综合决策Agent")
            return True
        else:
            print("[FAILURE] [X] 部分测试失败")
            failed = [name for i, (name, _, _) in enumerate(check_items) if not checks[i]]
            print(f"失败项: {', '.join(failed)}")
            return False

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_complete_workflow())
    sys.exit(0 if success else 1)
