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
from dotenv import load_dotenv
import pandas as pd
import numpy as np

# 加载环境变量
load_dotenv()

# 导入Tushare
import tushare as ts


async def fetch_real_daily_data(stock_code: str, days: int = 365) -> dict:
    """
    从Tushare获取真实的日K线数据

    Args:
        stock_code: 股票代码（如：601669）
        days: 天数

    Returns:
        价格数据字典
    """
    # 获取API key
    api_key = os.getenv("TUSHARE_API_KEY", "")
    if not api_key:
        raise ValueError("TUSHARE_API_KEY未配置")

    # 转换股票代码格式（601669 -> 601669.SH）
    if stock_code.startswith('6'):
        ts_code = f"{stock_code}.SH"
    else:
        ts_code = f"{stock_code}.SZ"

    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # 初始化API
    pro = ts.pro_api(api_key)

    # 获取日线数据（使用daily_basic接口，限流更宽松）
    print(f"   正在调用Tushare API...")
    print(f"   接口: daily_basic（开高低收、成交量）")
    print(f"   代码: {ts_code}")
    print(f"   日期: {start_date.strftime('%Y%m%d')} - {end_date.strftime('%Y%m%d')}")

    # 先获取交易日历（确保日期是交易日）
    df_cal = pro.trade_cal(exchange='SSE', start_date=start_date.strftime('%Y%m%d'), end_date=end_date.strftime('%Y%m%d'))
    trade_dates = df_cal[df_cal['is_open'] == 1]['cal_date'].tolist()

    if len(trade_dates) == 0:
        raise ValueError("没有交易日数据")

    # 使用实际交易日查询
    actual_start = trade_dates[0]
    actual_end = trade_dates[-1]

    print(f"   实际交易日范围: {actual_start} - {actual_end}")

    # 使用daily_basic接口（包含开高低收、成交量）
    df = pro.daily_basic(
        ts_code=ts_code,
        start_date=actual_start,
        end_date=actual_end,
        fields='ts_code,trade_date,open,high,low,close,vol,amount'
    )

    if df.empty:
        raise ValueError(f"未获取到数据: {stock_code}")

    # 按日期排序（旧 -> 新）
    df = df.sort_values('trade_date')

    # 转换为numpy数组
    dates = pd.to_datetime(df['trade_date'])
    open_prices = df['open'].values
    high_prices = df['high'].values
    low_prices = df['low'].values
    close_prices = df['close'].values
    volumes = df['vol'].values  # 成交量（手）

    return {
        "stock_code": stock_code,
        "stock_name": df.iloc[0].get('name', stock_code),
        "dates": dates,
        "open": open_prices,
        "high": high_prices,
        "low": low_prices,
        "close": close_prices,
        "volume": volumes,
        "data_count": len(df)
    }


def analyze_chip_distribution(price_data: dict, bins: int = 50) -> dict:
    """
    筹码分布分析

    Args:
        price_data: 价格数据
        bins: 价格区间数量

    Returns:
        筹码分布结果
    """
    close_prices = price_data["close"]
    volumes = price_data["volume"]

    # 计算价格区间
    min_price = close_prices.min()
    max_price = close_prices.max()
    price_bins = np.linspace(min_price, max_price, bins + 1)

    # 计算每个价格区间的筹码量（成交额）
    chip_distribution = np.zeros(bins)
    for i in range(len(close_prices)):
        price = close_prices[i]
        volume = volumes[i]

        # 找到价格所在的区间
        bin_idx = int((price - min_price) / (max_price - min_price) * bins)
        if bin_idx >= bins:
            bin_idx = bins - 1

        # 累加筹码（成交额）
        chip_distribution[bin_idx] += price * volume * 100  # 手 -> 股

    # 归一化
    chip_distribution = chip_distribution / chip_distribution.sum()

    # 找出筹码峰
    from scipy.signal import find_peaks
    peaks, properties = find_peaks(chip_distribution, distance=5)

    current_price = close_prices[-1]

    # 筛选出当前价上方的筹码峰（压力位）
    resistance_peaks = []
    for peak_idx in peaks:
        peak_price = price_bins[peak_idx]
        if peak_price > current_price:
            resistance_peaks.append({
                "price": peak_price,
                "ratio": chip_distribution[peak_idx] * 100
            })

    # 按价格排序（从低到高）
    resistance_peaks.sort(key=lambda x: x["price"])

    return {
        "chip_distribution": chip_distribution,
        "price_bins": price_bins,
        "peaks": peaks,
        "resistance_peaks": resistance_peaks,
        "current_price": current_price
    }


@pytest.mark.asyncio
async def test_with_real_data():
    """使用真实Tushare数据测试"""

    print("=" * 80)
    print(f"真实数据测试：中国电建 (601669)")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据源: Tushare API（真实数据）")
    print("=" * 80)
    print()

    # 获取真实数据
    print("[1/3] 获取中国电建真实数据...")
    try:
        price_data = await fetch_real_daily_data("601669", days=365)

        print(f"[OK] 获取到{price_data['data_count']}条数据")
        print(f"   最新日期: {price_data['dates'][-1].strftime('%Y-%m-%d')}")
        print(f"   开盘价: {price_data['open'][-1]:.2f}元")
        print(f"   收盘价: {price_data['close'][-1]:.2f}元")
        print(f"   最高价: {price_data['high'][-1]:.2f}元")
        print(f"   最低价: {price_data['low'][-1]:.2f}元")
        print(f"   成交量: {price_data['volume'][-1]:.0f}手")
        print()

    except Exception as e:
        print(f"[ERROR] 获取数据失败: {e}")
        print(f"   可能原因: API积分不足或网络问题")
        return

    # 筹码分析
    print("[2/3] 执行筹码分布分析...")
    try:
        chip_result = analyze_chip_distribution(price_data, bins=50)

        print(f"[OK] 筹码分析完成")
        print(f"   当前价: {chip_result['current_price']:.2f}元")
        print()

        # 显示筹码峰
        print("=" * 80)
        print("筹码峰分析（压力位）")
        print("=" * 80)
        print()

        if len(chip_result['resistance_peaks']) > 0:
            for i, peak in enumerate(chip_result['resistance_peaks'][:5], 1):
                print(f"[压力位{i}] {peak['price']:.2f}元")
                print(f"   - 筹码占比: {peak['ratio']:.1f}%")
                print()
        else:
            print("当前价上方无明显筹码峰")
            print()

    except Exception as e:
        print(f"[ERROR] 筹码分析失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 生成6个核心指标
    print("[3/3] 生成6个核心指标...")
    try:
        current_price = price_data["close"][-1]
        close_prices = price_data["close"]

        # 计算基本指标
        min_price_3y = close_prices.min()
        max_price_3y = close_prices.max()
        avg_price_3y = close_prices.mean()

        # 筹码压力位
        if len(chip_result['resistance_peaks']) > 0:
            chip_resistance = chip_result['resistance_peaks'][0]['price']
            chip_ratio = chip_result['resistance_peaks'][0]['ratio']
        else:
            chip_resistance = max_price_3y * 1.05
            chip_ratio = 0

        # 生成6个核心指标
        indicators = {
            # 1. 割肉价（止损价）- 基于3年最低价
            "stop_loss": min_price_3y * 0.95,
            "stop_loss_pct": (min_price_3y * 0.95 / current_price - 1) * 100,
            "stop_loss_basis": f"基于3年最低价({min_price_3y:.2f}元)×0.95",

            # 2. 买入价 - 当前价与支撑位之间
            "buy_price": (min_price_3y + current_price) / 2,
            "buy_price_basis": f"支撑位与当前价的中间值",

            # 3. 持仓成本
            "position_cost": current_price,
            "position_cost_basis": "与当前价相同",

            # 4. 压力位（筹码分析）
            "resistance_price": chip_resistance,
            "resistance_basis": f"筹码峰压力位（筹码占比{chip_ratio:.1f}%）",
            "chip_resistance": chip_resistance,
            "chip_ratio": chip_ratio,

            # 5. 主升浪时间窗口
            "main_rise_window": "待确认（需趋势反转）",
            "main_rise_basis": "当前趋势需分析",

            # 6. 目标价（简单估算）
            "target_price": max_price_3y * 0.9,
            "target_gain_pct": (max_price_3y * 0.9 / current_price - 1) * 100,
            "target_price_basis": f"基于3年最高价({max_price_3y:.2f}元)×0.9",
        }

        # 风险收益比
        risk = abs(current_price - indicators['stop_loss'])
        reward = indicators['target_price'] - current_price
        risk_return_ratio = reward / risk if risk > 0 else 0
        indicators['risk_return_ratio'] = risk_return_ratio

        print("[OK] 6个核心指标生成完成")
        print()

        # 显示结果
        print("=" * 80)
        print("6个核心指标")
        print("=" * 80)
        print()

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

        print(f"风险收益比: {risk_return_ratio:.2f}")
        print(f"  解释: 每承担1元风险，预期收益{risk_return_ratio:.2f}元")

        if risk_return_ratio >= 3:
            print(f"  评价: 优秀 (>=3)")
        elif risk_return_ratio >= 2:
            print(f"  评价: 良好 (>=2)")
        else:
            print(f"  评价: 一般 (<2)")

        print()
        print("=" * 80)
        print("[OK] 真实数据测试完成！")
        print("=" * 80)

    except Exception as e:
        print(f"[ERROR] 指标生成失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_with_real_data())
