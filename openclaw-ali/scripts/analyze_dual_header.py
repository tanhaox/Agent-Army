#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test parsing with full dual-header structure"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import re
import pandas as pd

# Sample HTML showing dual header structure
sample = """
| 序号 | 名称 | 相关 | 今 日 涨跌幅 | 今 日主力净流入 | 今 日超大单净流入 | 今 日大单净流入 | 今 日中单净流入 | 今 日小单净流入 | 今 日主力净 流入最大股 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 净额 | 净占比 | 净额 | 净占比 | 净额 | 净占比 | 净额 | 净占比 | 净额 | 净占比 |
| 1 | 煤炭开采 | 大单详情 股吧 | 4.02% | 18.90亿 | 8.24% | 16.25亿 | 7.09% | 2.65亿 | 1.16% | -3.22亿 | -1.40% | -15.68亿 | -6.84% | 兖矿能源 |
| 2 | 农化制品 | 大单详情 股吧 | 0.86% | 14.34亿 | 3.47% | 13.13亿 | 3.18% | 1.21亿 | 0.29% | 3306.27万 | 0.08% | -14.88亿 | -3.60% | 和邦生物 |
"""

print("=" * 70)
print("  双表头结构分析")
print("=" * 70)
print()

print("表头结构:")
print("┌─────────────────────────────────────────────────────────────────┐")
print("│ 序号 │ 名称 │ 今日涨跌幅 │ 今日主力净流入 │ 今日超大单净流入 │ ... │")
print("├─────────────────────────────────────────────────────────────────┤")
print("│      │      │            │ 净额   │净占比 │ 净额   │净占比 │ ... │")
print("├─────────────────────────────────────────────────────────────────┤")
print("│  1   │煤炭  │   4.02%    │18.90亿 │ 8.24% │16.25亿 │ 7.09% │ ... │")
print("└─────────────────────────────────────────────────────────────────┘")
print()

# 解析方案
print("解析方案：")
print()
print("字段对应关系：")
print("  1. 序号        → rank")
print("  2. 名称        → sector_name")
print("  3. 涨跌幅      → change_pct")
print("  4. 主力净流入   → main_net_inflow")
print("  5. 主力净流入占比 → main_net_inflow_ratio")
print("  6. 超大单净流入  → super_large_net")
print("  7. 超大单占比   → super_large_ratio")
print("  8. 大单净流入    → large_net")
print("  9. 大单占比      → large_ratio")
print(" 10. 中单净流入   → medium_net")
print(" 11. 中单占比     → medium_ratio")
print(" 12. 小单净流入   → small_net")
print(" 13. 小单占比     → small_ratio")
print(" 14. 最大股       → max_stock")
print()

# 改进的正则表达式
print("改进后的正则表达式：")
pattern = r'\|\s*(\d+)\s+\|\s*([^|]+?)\s+\|\s*[^|]*\|\s*([-\d.]+)%\s+\|\s*([-\d.]+)([亿万])\s+\|\s*([-\d.]+)%\s+\|\s*([-\d.]+)([亿万])\s+\|\s*([-\d.]+)%\s+\|\s*([-\d.]+)([亿万])\s+\|\s*([-\d.]+)%\s+\|\s*([-\d.]+)([亿万])\s+\|\s*([-\d.]+)%\s+\|\s*([-\d.]+)([亿万])\s+\|\s*([-\d.]+)%\s+\|\s*([^|]+?)\s*\|'

print(pattern)
print()

# 测试解析
print("测试解析：")
matches = re.findall(pattern, sample)
print(f"匹配到 {len(matches)} 行数据")
print()

if matches:
    for i, match in enumerate(matches[:2]):
        print(f"第{i+1}行数据:")
        print(f"  序号: {match[0]}")
        print(f"  名称: {match[1].strip()}")
        print(f"  涨跌幅: {match[2]}%")
        print(f"  主力净流入: {match[3]}{match[4]}")
        print(f"  主力占比: {match[5]}%")
        print(f"  超大单: {match[6]}{match[7]}")
        print(f"  大单: {match[9]}{match[10]}")
        print(f"  中单: {match[12]}{match[13]}")
        print(f"  小单: {match[15]}{match[16]}")
        print(f"  最大股: {match[18].strip()}")
        print()

print("=" * 70)
print("建议：更新解析器以提取完整数据")
print("=" * 70)
