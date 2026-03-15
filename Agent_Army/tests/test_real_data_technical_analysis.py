"""
真实数据测试：技术分析和筹码分析
使用Tushare API获取中国电建(601669)的真实数据
"""
import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, timedelta
from src.core.tools.data_source.financial_tool import FinancialTool
from src.agents.business.technical_analyzer import TechnicalAnalysisAI

# 常量
STOCK_CODE = "601669"  # 中国电建
STOCK_NAME = "中国电建"


@pytest.mark.asyncio
async def test_with_real_data():
    """使用真实Tushare数据测试"""

    print("=" * 80)
    print(f"真实数据测试：{STOCK_NAME} ({STOCK_CODE})")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据源: Tushare API（真实数据）")
    print("=" * 80)
    print()

    # 初始化工具
    print("[1/4] 初始化FinancialTool...")
    financial_tool = FinancialTool()
    print("[OK] FinancialTool初始化完成")
    print()

    # 获取真实数据
    print(f"[2/4] 获取{STOCK_NAME}真实数据...")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1年数据

        print(f"   时间范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        print(f"   查询接口: daily（日线数据）")

        data = await financial_tool.get_daily_data(
            ts_code=STOCK_CODE,
            start_date=start_date.strftime('%Y%m%d'),
            end_date=end_date.strftime('%Y%m%d')
        )

        if data is None or len(data) == 0:
            print("[ERROR] 未获取到数据")
            return

        print(f"[OK] 获取到{len(data)}条数据")
        print(f"   最新日期: {data.iloc[-1]['trade_date']}")
        print(f"   开盘价: {data.iloc[-1]['open']:.2f}元")
        print(f"   收盘价: {data.iloc[-1]['close']:.2f}元")
        print(f"   最高价: {data.iloc[-1]['high']:.2f}元")
        print(f"   最低价: {data.iloc[-1]['low']:.2f}元")
        print(f"   成交量: {data.iloc[-1]['vol']:.0f}手")
        print()

    except Exception as e:
        print(f"[ERROR] 获取数据失败: {e}")
        print(f"   可能原因: API积分不足或网络问题")
        return

    # 初始化技术分析Agent
    print("[3/4] 初始化技术分析Agent...")
    try:
        analyzer = TechnicalAnalysisAI(financial_tool=financial_tool)
        print("[OK] 技术分析Agent初始化完成")
        print()

        # 执行技术分析
        print(f"[4/4] 执行技术分析...")
        print(f"   分析代码: {STOCK_CODE}")
        print()

        result = await analyzer.analyze(STOCK_CODE)

        print("=" * 80)
        print("技术分析结果")
        print("=" * 80)
        print()

        # 基本信息
        print("[基本信息]")
        print(f"股票代码: {result.stock_code}")
        print(f"当前价格: {result.current_price:.2f}元")
        print(f"趋势方向: {result.trend_direction}")
        print(f"趋势强度: {result.trend_strength:.1f}%")
        print()

        # 6个核心指标
        print("=" * 80)
        print("6个核心指标")
        print("=" * 80)
        print()

        indicators = result.core_indicators

        print(f"[1] 割肉价（止损价）: {indicators['stop_loss']:.2f}元")
        print(f"    - 止损幅度: {indicators['stop_loss_pct']:.2f}%")
        print(f"    - 依据: {indicators['stop_loss_basis']}")
        print()

        print(f"[2] 买入价: {indicators['buy_price']:.2f}元")
        print(f"    - 依据: {indicators['buy_price_basis']}")
        print()

        print(f"[3] 持仓成本: {indicators['position_cost']:.2f}元")
        print(f"    - 依据: {indicators['position_cost_basis']}")
        print()

        print(f"[4] 压力位（阻力位）: {indicators['resistance_price']:.2f}元")
        print(f"    - 依据: {indicators['resistance_basis']}")
        if 'chip_resistance' in indicators:
            print(f"    - 筹码压力位: {indicators['chip_resistance']:.2f}元")
            print(f"    - 筹码占比: {indicators['chip_ratio']:.1f}%")
        print()

        print(f"[5] 主升浪时间窗口: {indicators['main_rise_window']}")
        print(f"    - 依据: {indicators['main_rise_basis']}")
        print()

        print(f"[6] 目标价: {indicators['target_price']:.2f}元")
        print(f"    - 预期收益: {indicators['target_gain_pct']:.2f}%")
        print(f"    - 依据: {indicators['target_price_basis']}")
        print()

        # 风险收益比
        print("=" * 80)
        print("风险收益评估")
        print("=" * 80)
        print()

        risk_reward = indicators.get('risk_return_ratio', 0)
        print(f"风险收益比: {risk_reward:.2f}")
        print(f"  解释: 每承担1元风险，预期收益{risk_reward:.2f}元")

        if risk_reward >= 3:
            print(f"  评价: 优秀 (≥3)")
        elif risk_reward >= 2:
            print(f"  评价: 良好 (≥2)")
        else:
            print(f"  评价: 一般 (<2)")

        print()
        print("=" * 80)
        print("[OK] 真实数据测试完成！")
        print("=" * 80)

    except Exception as e:
        print(f"[ERROR] 技术分析失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_with_real_data())
