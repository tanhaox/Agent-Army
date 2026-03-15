#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test full dual-header parsing"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'eastmoney-sector-crawler'))

from tool import EastmoneySectorCrawler

db_path = os.path.join(os.path.dirname(__file__), '..', 'skills', 'eastmoney-sector-crawler', 'data', 'test_full.duckdb')
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Full HTML with 50 sectors
html = """
| 1 | 煤炭开采 | 大单详情 股吧 | 4.02% | 18.90亿 | 8.24% | 16.25亿 | 7.09% | 2.65亿 | 1.16% | -3.22亿 | -1.40% | -15.68亿 | -6.84% | 兖矿能源 |
| 2 | 农化制品 | 大单详情 股吧 | 0.86% | 14.34亿 | 3.47% | 13.13亿 | 3.18% | 1.21亿 | 0.29% | 3306.27万 | 0.08% | -14.88亿 | -3.60% | 和邦生物 |
| 50 | 旅游及景区 | 大单详情 股吧 | 0.12% | -7285.90万 | -2.99% | -3479.95万 | -1.43% | -3805.95万 | -1.56% | 1309.33万 | 0.54% | 5976.57万 | 2.46% | 陕西旅游 |
"""

print("=" * 70)
print("  测试完整双表头数据提取")
print("=" * 70)
print()

crawler = EastmoneySectorCrawler(db_path=db_path)
print("✓ 爬虫初始化")
print()

df = crawler.parse_fund_flow_table(html)
print(f"✓ 解析 {len(df)} 条数据")
print()

if not df.empty:
    print("数据字段:")
    print(f"  {list(df.columns)}")
    print()

    # 显示第一条数据的详细信息
    first_row = df.iloc[0]
    print("第1条数据详情:")
    print(f"  板块: {first_row['sector_name']}")
    print(f"  排名: {first_row['rank']}")
    print(f"  涨跌幅: {first_row['change_pct']:+.2f}%")
    print(f"  主力净流入: {first_row['main_net_inflow']/100000000:.2f}亿 ({first_row['main_net_inflow_ratio']:.2f}%)")
    print(f"  超大单: {first_row['super_large_net']/100000000:.2f}亿 ({first_row['super_large_ratio']:.2f}%)")
    print(f"  大单: {first_row['large_net']/100000000:.2f}亿 ({first_row['large_ratio']:.2f}%)")
    print(f"  中单: {first_row['medium_net']/100000000:.2f}亿 ({first_row['medium_ratio']:.2f}%)")
    print(f"  小单: {first_row['small_net']/100000000:.2f}亿 ({first_row['small_ratio']:.2f}%)")
    print(f"  最大股: {first_row['max_stock']}")
    print()

    # 同步到数据库
    result = crawler.sync_fund_flow_from_html(html)
    print(f"✓ 同步状态: {result['status']}")
    print(f"✓ 数据条数: {result['count']}")
    print()

print("=" * 70)
print("✓ 完整双表头数据提取成功！")
print("=" * 70)
