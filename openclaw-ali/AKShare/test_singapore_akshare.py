#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import akshare as ak
from datetime import datetime, timedelta
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print('=' * 100)
print('  AKShare海外服务器测试')
print('=' * 100)
print()

# 显示环境信息
print('[环境信息]')
print(f"  AKShare版本: {ak.__version__}")
print(f"  Python版本: {sys.version.split()[0]}")
print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 测试1: 个股历史K线
print('-' * 100)
print('[测试1] 个股历史K线 (stock_zh_a_hist)')
print('-' * 100)
try:
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

    print(f"  股票: 中国电建 (601669)")
    print(f"  日期范围: {start_date} ~ {end_date}")

    df = ak.stock_zh_a_hist(
        symbol='601669',
        period='daily',
        start_date=start_date,
        end_date=end_date,
        adjust='qfq'
    )

    if df is not None and len(df) > 0:
        print(f"  ✅ 成功! 获取 {len(df)} 条记录")
        print(f"  字段: {list(df.columns)}")
        print()
        print(f'  最新5条数据:')
        print(f"  {'日期':<12} {'收盘':<8} {'成交量':<12} {'涨跌幅':<8}")
        for _, row in df.tail(5).iterrows():
            volume_str = f"{row['成交量']/10000:.1f}万手"
            print(f"  {row['日期']:<12} {row['收盘']:<8.2f} {volume_str:<12} {row['涨跌幅']:<8.2f}%")
    else:
        print(f"  ❌ 失败: 数据为空")
except Exception as e:
    print(f"  ❌ 失败: {e}")

print()

# 测试2: 个股详细信息
print('-' * 100)
print('[测试2] 个股详细信息 (stock_individual_info_em)')
print('-' * 100)
try:
    print(f"  股票: 中国电建 (601669)")

    df = ak.stock_individual_info_em(symbol='601669')

    if df is not None and len(df) > 0:
        print(f"  ✅ 成功! 获取 {len(df)} 项信息")
        print()
        info_dict = dict(zip(df['item'], df['value']))
        for key in ['股票代码', '股票名称', '总市值', '行业', '上市时间']:
            if key in info_dict:
                print(f"    {key}: {info_dict[key]}")
    else:
        print(f"  ❌ 失败: 数据为空")
except Exception as e:
    print(f"  ❌ 失败: {e}")

print()

# 测试3: A股实时行情
print('-' * 100)
print('[测试3] A股实时行情 (stock_zh_a_spot_em)')
print('-' * 100)
try:
    print(f"  正在获取A股实时行情...")

    df = ak.stock_zh_a_spot_em()

    if df is not None and len(df) > 0:
        print(f"  ✅ 成功! 获取 {len(df)} 条记录")
        print()
        print(f'  前5条数据:')
        print(f"  {'代码':<8} {'名称':<12} {'最新价':<10} {'涨跌幅':<8}")
        for _, row in df.head(5).iterrows():
            print(f"  {row['代码']:<8} {row['名称']:<12} {row['最新价']:<10} {row['涨跌幅']:<8}%")
    else:
        print(f"  ❌ 失败: 数据为空")
except Exception as e:
    print(f"  ❌ 失败: {e}")

print()

# 测试4: 宏观经济数据
print('-' * 100)
print('[测试4] CPI宏观数据 (macro_china_cpi)')
print('-' * 100)
try:
    print(f"  正在获取CPI数据...")

    df = ak.macro_china_cpi()

    if df is not None and len(df) > 0:
        print(f"  ✅ 成功! 获取 {len(df)} 条记录")
        print()
        print(f'  最新5条数据:')
        print(f"  {'月份':<12} {'全国当月':<10} {'同比增长':<10} {'环比增长':<10}")
        for _, row in df.tail(5).iterrows():
            print(f"  {row['月份']:<12} {row['全国-当月']:<10} {row['全国-同比增长']:<10} {row['全国-环比增长']:<10}")
    else:
        print(f"  ❌ 失败: 数据为空")
except Exception as e:
    print(f"  ❌ 失败: {e}")

print()
print('=' * 100)
print('  测试完成')
print('=' * 100)
