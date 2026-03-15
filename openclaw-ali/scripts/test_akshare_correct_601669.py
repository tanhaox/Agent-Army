#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用AKShare正确函数测试采集中国电建数据"""
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import akshare as ak
import pandas as pd

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
    # stock_individual_fund_flow 参数: symbol, indicator="个股", market="上海" or "深圳"
    df = ak.stock_individual_fund_flow(symbol=stock_code, indicator="个股", market="上海")
    if not df.empty:
        latest = df.iloc[0]
        print(f"✅ 成功获取 {len(df)} 条记录")
        print(f"  列名: {list(df.columns)}")
        print(f"  最新记录:")
        for col in df.columns:
            val = latest[col]
            print(f"    {col}: {val}")
    else:
        print("⚠️  无数据")
except Exception as e:
    print(f"❌ 失败: {str(e)}")
    import traceback
    traceback.print_exc()

print()

# 2. 融资融券数据
print("💳 [2/7] 融资融券")
print("-" * 70)
try:
    # 上交所融资融券明细
    df = ak.stock_margin_detail_sse(symbol=stock_code)
    if not df.empty:
        latest = df.iloc[0]
        print(f"✅ 成功获取 {len(df)} 条记录")
        print(f"  列名: {list(df.columns)}")
        print(f"  最新记录:")
        for col in df.columns[:10]:  # 只显示前10列
            val = latest[col]
            print(f"    {col}: {val}")
    else:
        print("⚠️  无数据")
except Exception as e:
    print(f"❌ 失败: {str(e)}")
    import traceback
    traceback.print_exc()

print()

# 3. 股东数据
print("👥 [3/7] 股东户数")
print("-" * 70)
try:
    # A股股东户数
    df = ak.stock_zh_a_gdhs(symbol=stock_code, indicator="股东户数")
    if not df.empty:
        latest = df.iloc[0]
        print(f"✅ 成功获取 {len(df)} 条记录")
        print(f"  列名: {list(df.columns)}")
        print(f"  最新记录:")
        for col in df.columns:
            val = latest[col]
            print(f"    {col}: {val}")
    else:
        print("⚠️  无数据")
except Exception as e:
    print(f"❌ 失败: {str(e)}")
    import traceback
    traceback.print_exc()

print()

# 4. 北向资金
print("💰 [4/7] 北向资金持股")
print("-" * 70)
try:
    # 港股通持股明细
    df = ak.stock_hsgt_individual_detail_em(symbol=stock_code)
    if not df.empty:
        latest = df.iloc[0]
        print(f"✅ 成功获取 {len(df)} 条记录")
        print(f"  列名: {list(df.columns)}")
        print(f"  最新记录:")
        for col in df.columns:
            val = latest[col]
            print(f"    {col}: {val}")
    else:
        print("⚠️  无数据（可能不是港股通标的）")
except Exception as e:
    print(f"❌ 失败: {str(e)}")
    import traceback
    traceback.print_exc()

print()

# 5. 限售解禁
print("🔓 [5/7] 限售解禁")
print("-" * 70)
try:
    # 限售解禁明细
    df = ak.stock_restricted_release_detail_em(symbol=stock_code)
    if not df.empty:
        print(f"✅ 成功获取 {len(df)} 条记录")
        print(f"  列名: {list(df.columns)}")
        for i, row in df.head(3).iterrows():
            print(f"  [{i+1}]")
            for col in df.columns:
                print(f"    {col}: {row[col]}")
    else:
        print("⚠️  无近期限售解禁数据")
except Exception as e:
    print(f"❌ 失败: {str(e)}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("  采集完成！")
print("=" * 70)
