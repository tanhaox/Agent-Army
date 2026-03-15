#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查AKShare函数的正确参数"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import akshare as ak
import inspect

print("AKShare函数参数检查")
print("=" * 70)

functions_to_check = [
    'stock_individual_fund_flow',
    'stock_margin_detail_sse',
    'stock_zh_a_gdhs',
    'stock_restricted_release_detail_em',
]

for func_name in functions_to_check:
    print(f"\n【{func_name}】")
    try:
        func = getattr(ak, func_name)
        sig = inspect.signature(func)
        print(f"  参数: {sig}")
        doc = func.__doc__
        if doc:
            # 只显示前500字符的文档
            print(f"  文档(前500字): {doc[:500]}...")
    except Exception as e:
        print(f"  错误: {str(e)}")
