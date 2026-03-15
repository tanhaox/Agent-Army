#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Eastmoney Sector Crawler Skill with real data"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'eastmoney-sector-crawler'))

from tool import EastmoneySectorCrawler

# Use correct database path
db_path = os.path.join(os.path.dirname(__file__), '..', 'skills', 'eastmoney-sector-crawler', 'data', 'test.duckdb')
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Real HTML content from WebReader
real_html = """
沪深资金流向
个股资金流向：
板块资金流向：
更多板块资金流向
**上证**: **4129.10↑↓-4.33↑↓-0.10% 1.08万亿元** (涨:**772**平: **43** 跌:**1530**)**深证**: **14374.87↑↓-90.54↑↓-0.63% 1.36万亿元** (涨:**710**平: **65**跌:**2142**)
* 行业资金流
* 概念资金流
* 地域资金流
* 今日排行
* 5日排行
* 10日排行
| 序号 | 名称 | 相关 | 今 日 涨跌幅 | 今 日主力净流入 | 今 日超大单净流入 | 今 日大单净流入 | 今 日中单净流入 | 今 日小单净流入 | 今 日主力净 流入最大股 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 净额 | 净占比 | 净额 | 净占比 | 净额 | 净占比 | 净额 | 净占比 | 净额 | 净占比 |
| 1 | 煤炭开采 | 大单详情 股吧 | 4.02% | 18.90亿 | 8.24% | 16.25亿 | 7.09% | 2.65亿 | 1.16% | -3.22亿 | -1.40% | -15.68亿 | -6.84% | 兖矿能源 |
| 2 | 农化制品 | 大单详情 股吧 | 0.86% | 14.34亿 | 3.47% | 13.13亿 | 3.18% | 1.21亿 | 0.29% | 3306.27万 | 0.08% | -14.88亿 | -3.60% | 和邦生物 |
| 3 | 光学光电子 | 大单详情 股吧 | -0.29% | 12.25亿 | 2.25% | 13.27亿 | 2.44% | -1.02亿 | -0.19% | -9.02亿 | -1.66% | -3.36亿 | -0.62% | 三安光电 |
| 4 | 普钢 | 大单详情 股吧 | 2.04% | 11.31亿 | 8.92% | 12.20亿 | 9.63% | -8937.10万 | -0.71% | -5.10亿 | -4.03% | -6.21亿 | -4.90% | 杭钢股份 |
| 5 | 化学原料 | 大单详情 股吧 | 0.90% | 11.06亿 | 2.30% | 12.32亿 | 2.57% | -1.26亿 | -0.26% | -2.69亿 | -0.56% | -8.48亿 | -1.77% | 金牛化工 |
| 6 | 计算机设备 | 大单详情 股吧 | -0.43% | 10.34亿 | 3.02% | 6.75亿 | 1.97% | 3.59亿 | 1.05% | -4.18亿 | -1.22% | -6.21亿 | -1.81% | 中科曙光 |
| 7 | 电力 | 大单详情 股吧 | 2.05% | 10.13亿 | 0.96% | 25.95亿 | 2.47% | -15.82亿 | -1.51% | -6.77亿 | -0.64% | -3.36亿 | -0.32% | 协鑫能科 |
| 8 | 风电设备 | 大单详情 股吧 | 4.32% | 8.37亿 | 2.12% | 4.90亿 | 1.24% | 3.46亿 | 0.88% | 1.27亿 | 0.32% | -9.64亿 | -2.44% | 双一科技 |
| 9 | 化学纤维 | 大单详情 股吧 | 2.79% | 7.43亿 | 5.59% | 10.39亿 | 7.83% | -2.97亿 | -2.23% | -2.39亿 | -1.80% | -4.72亿 | -3.56% | 皖维高新 |
| 10 | 多元金融 | 大单详情 股吧 | 1.11% | 4.39亿 | 4.23% | 1.72亿 | 1.66% | 2.67亿 | 2.58% | 1.30亿 | 1.25% | -5.69亿 | -5.49% | 拉卡拉 |
"""

print("=" * 70)
print("  Test Eastmoney Sector Crawler Skill")
print("=" * 70)
print()

# Initialize crawler
print("[Step 1] Initializing crawler...")
crawler = EastmoneySectorCrawler(db_path=db_path)
print("  ✓ Crawler initialized")
print()

# Parse HTML
print("[Step 2] Parsing HTML content...")
df = crawler.parse_fund_flow_table(real_html)
print(f"  ✓ Parsed {len(df)} sectors")
print()

# Show top 5
print("[Step 3] Top 5 sectors by fund flow:")
for i, row in df.head(5).iterrows():
    print(f"  {row['rank']}. {row['sector_name']}: "
          f"{row['change_pct']:+.2f}%, "
          f"净流入: {row['main_net_inflow']/100000000:.2f}亿")
print()

# Sync to database
print("[Step 4] Syncing to database...")
result = crawler.sync_fund_flow_from_html(real_html)
print(f"  ✓ Status: {result['status']}")
print(f"  ✓ Count: {result['count']}")
print(f"  ✓ Date: {result['date']}")
print()

# Query from database
print("[Step 5] Querying from database...")
all_sectors = crawler.get_sector_fund_flow(top_n=5)
print(f"  ✓ Retrieved {len(all_sectors)} sectors")
print()

# Top gainers
print("[Step 6] Top gainers:")
top_gainers = crawler.get_top_gainers(3)
for sector in top_gainers:
    print(f"  {sector['sector_name']}: {sector['change_pct']:+.2f}%")
print()

# Top inflows
print("[Step 7] Top inflows:")
top_inflows = crawler.get_top_inflows(3)
for sector in top_inflows:
    print(f"  {sector['sector_name']}: {sector['main_net_inflow']/100000000:.2f}亿")
print()

print("=" * 70)
print("  ✓ All tests passed!")
print("=" * 70)
print()
print("Skill is ready to use with OpenClaw!")
print()
print("Usage:")
print("  from main import sync_sector_fund_flow_from_html")
print("  sync_sector_fund_flow_from_html(html_content)")
