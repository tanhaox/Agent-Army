#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用AKShare测试采集中国电建数据"""
import sys
from pathlib import Path

# Windows UTF-8输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import akshare as ak
    import pandas as pd
    from datetime import datetime
except ImportError:
    print("❌ 请先安装AKShare: pip install akshare")
    sys.exit(1)

print("=" * 70)
print("  使用AKShare采集中国电建（601669）数据")
print("=" * 70)
print()

stock_code = "601669"
stock_name = "中国电建"

# 1. 资金流向数据
print("📊 [1/7] 个股资金流向")
print("-" * 70)
try:
    # 东方财富个股资金流向
    df = ak.stock_individual_fund_flow(symbol=stock_code, market="sh")
    if not df.empty:
        latest = df.iloc[0]
        print(f"✅ 成功获取 {len(df)} 条记录")
        print(f"  最新日期: {latest.get('date', 'N/A')}")
        print(f"  主力净流入: {latest.get('主力净流入-净额', 0):,.0f} 元")
        print(f"  主力净流入占比: {latest.get('主力净流入-净占比', 0):.2f}%")
        print(f"  超大单净流入: {latest.get('超大单净流入-净额', 0):,.0f} 元")
        print(f"  大单净流入: {latest.get('大单净流入-净额', 0):,.0f} 元")
        print(f"  中单净流入: {latest.get('中单净流入-净额', 0):,.0f} 元")
        print(f"  小单净流入: {latest.get('小单净流入-净额', 0):,.0f} 元")
    else:
        print("⚠️  无数据")
except Exception as e:
    print(f"❌ 失败: {str(e)}")

print()

# 2. 融资融券数据
print("💳 [2/7] 融资融券")
print("-" * 70)
try:
    # 东方财富融资融券明细
    df = ak.stock_margin_stl_detail(symbol=stock_code, market="sh")
    if not df.empty:
        latest = df.iloc[0]
        print(f"✅ 成功获取 {len(df)} 条记录")
        print(f"  最新日期: {latest.get('date', 'N/A')}")
        print(f"  融资余额: {latest.get('融资余额', 0):,.0f} 元")
        print(f"  融券余额: {latest.get('融券余额', 0):,.0f} 元")
        print(f"  融资买入额: {latest.get('融资买入额', 0):,.0f} 元")
        print(f"  融券卖出量: {latest.get('融券卖出量', 0):,.0f} 股")
    else:
        print("⚠️  无数据")
except Exception as e:
    print(f"❌ 失败: {str(e)}")

print()

# 3. 股东数据
print("👥 [3/7] 股东户数")
print("-" * 70)
try:
    # 新浪股东户数
    df = ak.stock_shareholder_zh_a(symbol=stock_code, indicator="股东户数")
    if not df.empty:
        latest = df.iloc[0]
        print(f"✅ 成功获取 {len(df)} 条记录")
        print(f"  最新日期: {latest.get('date', 'N/A')}")
        print(f"  股东户数: {latest.get('股东户数', 0):,} 户")
        if '户均持股数' in latest:
            print(f"  户均持股: {latest.get('户均持股数', 0):,.0f} 股")
    else:
        print("⚠️  无数据")
except Exception as e:
    print(f"❌ 失败: {str(e)}")

print()

# 4. 北向资金
print("💰 [4/7] 北向资金持股")
print("-" * 70)
try:
    # 港股通持股情况
    df = ak.stock_hk_hold_stats_em(symbol=stock_code)
    if not df.empty:
        latest = df.iloc[0]
        print(f"✅ 成功获取 {len(df)} 条记录")
        print(f"  最新日期: {latest.get('hold_date', 'N/A')}")
        print(f"  持股比例: {latest.get('hold_ratio', 0):.2f}%")
        print(f"  持股数量: {latest.get('hold_amount', 0):,.0f} 股")
        if 'hold_ratio_change' in latest:
            print(f"  持股变化: {latest.get('hold_ratio_change', 0):+.2f}%")
    else:
        print("⚠️  无数据（可能不是港股通标的）")
except Exception as e:
    print(f"❌ 失败: {str(e)}")

print()

# 5. 大宗交易
print("📦 [5/7] 大宗交易")
print("-" * 70)
try:
    # 东方财富大宗交易
    df = ak.stock_block_deal_em(symbol=stock_code)
    if not df.empty:
        print(f"✅ 成功获取 {len(df)} 条记录")
        for i, row in df.head(3).iterrows():
            print(f"  [{i+1}] {row.get('交易日', 'N/A')}")
            print(f"      成交价: {row.get('成交价', 0):.2f} 元")
            print(f"      溢价率: {row.get('溢价率', 0):+.2f}%")
            print(f"      成交量: {row.get('成交量', 0):,.0f} 股")
            print(f"      成交额: {row.get('成交额', 0):,.0f} 元")
            print(f"      买方营业部: {row.get('买方营业部', 'N/A')}")
            print(f"      卖方营业部: {row.get('卖方营业部', 'N/A')}")
    else:
        print("⚠️  无近期大宗交易")
except Exception as e:
    print(f"❌ 失败: {str(e)}")

print()

# 6. 龙虎榜
print("🐉 [6/7] 龙虎榜")
print("-" * 70)
try:
    # 东方财富龙虎榜
    df = ak.stock_dragon_tiger_list_em(symbol=stock_code)
    if not df.empty:
        print(f"✅ 成功获取 {len(df)} 条记录")
        for i, row in df.head(3).iterrows():
            print(f"  [{i+1}] {row.get('上榜日', 'N/A')}")
            print(f"      解禁原因: {row.get('龙虎榜解密', 'N/A')}")
            print(f"      买入额: {row.get('买入总额', 0):,.0f} 元")
            print(f"      卖出额: {row.get('卖出总额', 0):,.0f} 元")
    else:
        print("⚠️  无近期龙虎榜记录")
except Exception as e:
    print(f"❌ 失败: {str(e)}")

print()

# 7. 限售解禁
print("🔓 [7/7] 限售解禁")
print("-" * 70)
try:
    # 东方财富限售解禁
    df = ak.stock_locked_shares_em()
    # 筛选特定股票
    df = df[df['代码'] == stock_code] if '代码' in df.columns else pd.DataFrame()
    if not df.empty:
        print(f"✅ 成功获取 {len(df)} 条记录")
        for i, row in df.head(3).iterrows():
            print(f"  [{i+1}] {row.get('解禁日期', 'N/A')}")
            print(f"      解禁数量: {row.get('解禁数量', 0):,.0f} 股")
            print(f"      解禁市值: {row.get('解禁市值', 0):,.0f} 元")
    else:
        print("⚠️  无近期限售解禁数据")
except Exception as e:
    print(f"❌ 失败: {str(e)}")

print()
print("=" * 70)
print("  采集完成！")
print("=" * 70)
print()
print("📝 数据质量评估:")
print("  - AKShare是成熟的开源库，数据来源稳定")
print("  - 直接从东方财富等官网获取")
print("  - 建议使用AKShare替代自行实现API")
