#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用AKShare正确方式测试采集中国电建数据"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

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
    df = ak.stock_individual_fund_flow(stock=stock_code, market="sh")
    if not df.empty:
        latest = df.iloc[0]
        print(f"✅ 成功获取 {len(df)} 条记录")
        print(f"  列名: {list(df.columns)[:10]}...")
        print(f"  最新记录:")
        for col in df.columns[:8]:
            val = latest[col]
            print(f"    {col}: {val}")
    else:
        print("⚠️  无数据")
except Exception as e:
    print(f"❌ 失败: {str(e)}")

print()

# 2. 股东户数（最新）
print("👥 [2/7] 股东户数（最新）")
print("-" * 70)
try:
    df = ak.stock_zh_a_gdhs(symbol="最新")
    # 筛选中国电建
    if not df.empty and '代码' in df.columns:
        stock_df = df[df['代码'] == stock_code]
        if not stock_df.empty:
            latest = stock_df.iloc[0]
            print(f"✅ 成功获取")
            print(f"  列名: {list(df.columns)}")
            print(f"  数据:")
            for col in df.columns:
                print(f"    {col}: {latest[col]}")
        else:
            print(f"⚠️  未找到{stock_code}的数据")
    else:
        print("⚠️  无数据")
except Exception as e:
    print(f"❌ 失败: {str(e)}")

print()

# 3. 北向资金持股明细
print("💰 [3/7] 北向资金持股明细")
print("-" * 70)
try:
    # stock_hsgt_individual_detail_em 参数是 stock
    df = ak.stock_hsgt_individual_detail_em(stock=stock_code)
    if not df.empty:
        latest = df.iloc[0]
        print(f"✅ 成功获取 {len(df)} 条记录")
        print(f"  列名: {list(df.columns)[:10]}...")
        print(f"  最新记录:")
        for col in df.columns[:8]:
            val = latest[col]
            print(f"    {col}: {val}")
    else:
        print("⚠️  无数据")
except Exception as e:
    print(f"❌ 失败: {str(e)}")

print()

# 4. 限售解禁（查询最近一年）
print("🔓 [4/7] 限售解禁")
print("-" * 70)
try:
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    df = ak.stock_restricted_release_detail_em(start_date=start_date, end_date=end_date)
    # 筛选中国电建
    if not df.empty and '代码' in df.columns:
        stock_df = df[df['代码'] == stock_code]
        if not stock_df.empty:
            print(f"✅ 成功获取 {len(stock_df)} 条记录")
            print(f"  列名: {list(df.columns)}")
            for i, row in stock_df.head(3).iterrows():
                print(f"  [{i+1}]")
                for col in ['解禁日期', '解禁数量', '解禁市值', '代码', '名称']:
                    if col in df.columns:
                        print(f"    {col}: {row[col]}")
        else:
            print(f"⚠️  {stock_code} 无近期限售解禁")
    else:
        print("⚠️  无数据")
except Exception as e:
    print(f"❌ 失败: {str(e)}")

print()

# 5. 港股通持股统计（简化版）
print("💰 [5/7] 港股通持股统计")
print("-" * 70)
try:
    df = ak.stock_hsgt_stock_statistics_em()
    # 筛选中国电建
    if not df.empty and '代码' in df.columns:
        stock_df = df[df['代码'] == stock_code]
        if not stock_df.empty:
            latest = stock_df.iloc[0]
            print(f"✅ 成功获取")
            print(f"  列名: {list(df.columns)[:10]}...")
            print(f"  数据:")
            for col in df.columns[:8]:
                print(f"    {col}: {latest[col]}")
        else:
            print(f"⚠️  未找到{stock_code}的数据（可能不是港股通标的）")
    else:
        print("⚠️  无数据")
except Exception as e:
    print(f"❌ 失败: {str(e)}")

print()
print("=" * 70)
print("  采集完成！")
print("=" * 70)
print()
print("📝 说明:")
print("  - AKShare的数据接口大部分是返回全市场数据")
print("  - 需要在返回的数据中筛选特定股票")
print("  - 部分数据（如融资融券）需要按日期查询，不支持按股票代码查询")
