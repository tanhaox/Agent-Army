"""
测试Tushare免费接口
专注于可用的基础数据接口
"""
import pytest

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载.env文件
env_path = project_root / '.env'
load_dotenv(env_path)


@pytest.mark.asyncio
async def test_daily_interface():
    """测试日线数据接口（免费）"""
    print("=" * 60)
    print("测试Tushare免费接口 - 日线数据")
    print("=" * 60)

    try:
        import tushare as ts

        api_key = os.getenv("TUSHARE_API_KEY", "")
        if not api_key:
            print("[ERROR] TUSHARE_API_KEY未配置")
            return False

        pro = ts.pro_api(api_key)

        # 测试参数
        ts_code = "601669.SH"  # 中国电建
        start_date = "20250101"
        end_date = "20260315"

        print(f"\n测试参数:")
        print(f"  股票代码: {ts_code}")
        print(f"  起始日期: {start_date}")
        print(f"  结束日期: {end_date}")

        # 调用daily接口（免费）
        def call_tushare():
            return pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

        df = await asyncio.get_event_loop().run_in_executor(None, call_tushare)

        if df.empty:
            print("\n[WARNING] 返回空数据")
            return False

        print(f"\n[SUCCESS] 获取到 {len(df)} 条日线数据")
        print(f"\n数据列: {', '.join(df.columns.tolist())}")

        print(f"\n最新5条数据:")
        print(df.head().to_string())

        # 数据质量检查
        print(f"\n数据质量检查:")
        print(f"  - 开盘价: {df['open'].notna().sum()}/{len(df)} 有效")
        print(f"  - 最高价: {df['high'].notna().sum()}/{len(df)} 有效")
        print(f"  - 最低价: {df['low'].notna().sum()}/{len(df)} 有效")
        print(f"  - 收盘价: {df['close'].notna().sum()}/{len(df)} 有效")
        print(f"  - 成交量: {df['vol'].notna().sum()}/{len(df)} 有效")

        return True

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        return False


@pytest.mark.asyncio
async def test_daily_basic_interface():
    """测试日线基础数据接口（免费）"""
    print("\n" + "=" * 60)
    print("测试Tushare免费接口 - 日线基础数据")
    print("=" * 60)

    try:
        import tushare as ts

        api_key = os.getenv("TUSHARE_API_KEY", "")
        if not api_key:
            print("[ERROR] TUSHARE_API_KEY未配置")
            return False

        pro = ts.pro_api(api_key)

        # 测试参数
        ts_code = "601669.SH"
        start_date = "20260101"
        end_date = "20260315"

        print(f"\n测试参数:")
        print(f"  股票代码: {ts_code}")
        print(f"  起始日期: {start_date}")
        print(f"  结束日期: {end_date}")

        # 调用daily_basic接口（免费）
        def call_tushare():
            return pro.daily_basic(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

        df = await asyncio.get_event_loop().run_in_executor(None, call_tushare)

        if df.empty:
            print("\n[WARNING] 返回空数据")
            return False

        print(f"\n[SUCCESS] 获取到 {len(df)} 条日线基础数据")
        print(f"\n数据列: {', '.join(df.columns.tolist())}")

        print(f"\n最新数据:")
        latest = df.iloc[0]
        print(f"  - 交易日期: {latest['trade_date']}")
        print(f"  - 总市值: {latest['total_mv']:.2f}亿元")
        print(f"  - 流通市值: {latest['circ_mv']:.2f}亿元")
        print(f"  - 市盈率PE: {latest['pe']:.2f}")
        print(f"  - 市净率PB: {latest['pb']:.2f}")
        print(f"  - 换手率: {latest['turnover_rate']:.2f}%")

        return True

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        return False


@pytest.mark.asyncio
async def test_income_interface():
    """测试业绩数据接口（免费）"""
    print("\n" + "=" * 60)
    print("测试Tushare免费接口 - 业绩数据")
    print("=" * 60)

    try:
        import tushare as ts

        api_key = os.getenv("TUSHARE_API_KEY", "")
        if not api_key:
            print("[ERROR] TUSHARE_API_KEY未配置")
            return False

        pro = ts.pro_api(api_key)

        # 测试参数
        ts_code = "601669.SH"
        start_date = "20230101"
        end_date = "20251231"

        print(f"\n测试参数:")
        print(f"  股票代码: {ts_code}")
        print(f"  起始日期: {start_date}")
        print(f"  结束日期: {end_date}")

        # 调用income接口（免费）
        def call_tushare():
            return pro.income(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

        df = await asyncio.get_event_loop().run_in_executor(None, call_tushare)

        if df.empty:
            print("\n[WARNING] 返回空数据")
            return False

        print(f"\n[SUCCESS] 获取到 {len(df)} 条业绩数据")
        print(f"\n数据列: {', '.join(df.columns.tolist())}")

        print(f"\n最新业绩数据:")
        latest = df.iloc[0]
        print(f"  - 公告日期: {latest.get('ann_date', 'N/A')}")
        print(f"  - 报告期: {latest.get('end_date', 'N/A')}")
        print(f"  - 营业收入: {latest.get('total_revenue', 0):.2f}元")
        print(f"  - 营业成本: {latest.get('total_cost', 0):.2f}元")

        return True

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Tushare免费接口测试")
    print("=" * 60)

    results = {}

    # 测试三个免费接口
    results['daily'] = await test_daily_interface()
    results['daily_basic'] = await test_daily_basic_interface()
    results['income'] = await test_income_interface()

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for test_name, result in results.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"  - {test_name}: {status}")

    passed = sum(results.values())
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n[SUCCESS] 所有免费接口测试通过！")
        print("  可以开始集成真实数据")
    elif passed > 0:
        print("\n[INFO] 部分接口可用，可以继续开发")
    else:
        print("\n[ERROR] 所有接口测试失败，请检查配置")


if __name__ == "__main__":
    asyncio.run(main())
