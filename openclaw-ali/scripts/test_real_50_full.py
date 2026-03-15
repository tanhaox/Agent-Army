#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test parsing real 50 sectors with full dual-header data"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'eastmoney-sector-crawler'))

from tool import EastmoneySectorCrawler

db_path = os.path.join(os.path.dirname(__file__), '..', 'skills', 'eastmoney-sector-crawler', 'data', 'test_50_full.duckdb')
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# 完整的50条数据
html = """
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
| 25 | 教育 | 大单详情 股吧 | -0.30% | 1292.42万 | 0.62% | -1538.22万 | -0.74% | 2830.64万 | 1.37% | -877.82万 | -0.42% | -414.60万 | -0.20% | 中公教育 |
| 48 | 航空机场 | 大单详情 股吧 | -0.41% | -5401.11万 | -1.05% | -7948.72万 | -1.55% | 2547.61万 | 0.50% | 1.07亿 | 2.09% | -5293.53万 | -1.03% | 中国东航 |
| 49 | 出版 | 大单详情 股吧 | -0.18% | -5464.47万 | -1.40% | -2897.26万 | -0.74% | -2567.21万 | -0.66% | 1153.67万 | 0.30% | 4310.80万 | 1.11% | 中国科传 |
| 50 | 旅游及景区 | 大单详情 股吧 | 0.12% | -7285.90万 | -2.99% | -3479.95万 | -1.43% | -3805.95万 | -1.56% | 1309.33万 | 0.54% | 5976.57万 | 2.46% | 陕西旅游 |
"""

print("=" * 70)
print("  完整双表头数据测试（50条）")
print("=" * 70)
print()

crawler = EastmoneySectorCrawler(db_path=db_path)

# 解析
df = crawler.parse_fund_flow_table(html)
print(f"✓ 解析 {len(df)} 条数据")
print()

# 检查字段完整性
required_fields = ['date', 'rank', 'sector_name', 'change_pct',
                   'main_net_inflow', 'main_net_inflow_ratio',
                   'super_large_net', 'super_large_ratio',
                   'large_net', 'large_ratio',
                   'medium_net', 'medium_ratio',
                   'small_net', 'small_ratio',
                   'max_stock']

missing_fields = [f for f in required_fields if f not in df.columns]
if missing_fields:
    print(f"✗ 缺少字段: {missing_fields}")
else:
    print("✓ 所有字段完整")

print()

# 显示前3条和后3条
print("前3条数据:")
for i, row in df.head(3).iterrows():
    print(f"  {row['rank']}. {row['sector_name']:12s} "
          f"涨:{row['change_pct']:+5.2f}% "
          f"主力:{row['main_net_inflow']/100000000:8.2f}亿 "
          f"超大:{row['super_large_net']/100000000:7.2f}亿 "
          f"大:{row['large_net']/100000000:7.2f}亿 "
          f"中:{row['medium_net']/100000000:7.2f}亿 "
          f"小:{row['small_net']/100000000:7.2f}亿 "
          f"最大股:{row['max_stock']}")

print()
print("后3条数据:")
for i, row in df.tail(3).iterrows():
    print(f"  {row['rank']}. {row['sector_name']:12s} "
          f"涨:{row['change_pct']:+5.2f}% "
          f"主力:{row['main_net_inflow']/100000000:8.2f}亿 "
          f"超大:{row['super_large_net']/100000000:7.2f}亿 "
          f"大:{row['large_net']/100000000:7.2f}亿 "
          f"中:{row['medium_net']/100000000:7.2f}亿 "
          f"小:{row['small_net']/100000000:7.2f}亿 "
          f"最大股:{row['max_stock']}")

print()

# 同步到数据库
result = crawler.sync_fund_flow_from_html(html)
print(f"✓ 同步状态: {result['status']}")
print(f"✓ 同步条数: {result['count']}")

print()
print("=" * 70)
print("✓ 完整双表头数据提取测试通过！")
print("=" * 70)
