#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查AKShare的股票相关函数"""
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import akshare as ak

print("AKShare版本:", ak.__version__)
print()
print("股票相关函数:")
print("=" * 70)

# 获取所有股票相关的函数
all_funcs = [func for func in dir(ak) if not func.startswith('_') and 'stock' in func.lower()]

# 分类显示
categories = {
    '资金流向': [f for f in all_funcs if 'fund' in f.lower() or 'flow' in f.lower() or 'capital' in f.lower()],
    '融资融券': [f for f in all_funcs if 'margin' in f.lower() or 'rzrq' in f.lower()],
    '股东': [f for f in all_funcs if 'shareholder' in f.lower() or 'holder' in f.lower()],
    '北向': [f for f in all_funcs if 'hk' in f.lower() or 'north' in f.lower() or 'hs' in f.lower()],
    '龙虎榜': [f for f in all_funcs if 'dragon' in f.lower() or 'tiger' in f.lower()],
    '大宗交易': [f for f in all_funcs if 'block' in f.lower()],
    '限售': [f for f in all_funcs if 'lock' in f.lower() or 'restrict' in f.lower()],
}

for category, funcs in categories.items():
    if funcs:
        print(f"\n【{category}】")
        for func in funcs:
            print(f"  - {func}")

print()
print("=" * 70)
print("完整股票函数列表（前50个）:")
for i, func in enumerate(all_funcs[:50], 1):
    print(f"  {i}. {func}")
