#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地测试A股数据补充Skill"""
import sys
from pathlib import Path

# Windows UTF-8输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加skill路径
skill_path = Path('C:/AI-Agent-Local/openclaw-ali/skills/eastmoney-data-claude')
sys.path.insert(0, str(skill_path))

from tool import EastMoneyDataAPI

print("=" * 70)
print("  A股数据补充 Skill - 本地测试")
print("=" * 70)
print()

api = EastMoneyDataAPI()

# 测试1: 获取资金流向
print("📊 测试1: 获取伊利股份资金流向")
print("-" * 70)
result = api.get_stock_money_flow('600887')
if result['success']:
    print(f"✅ 成功")
    print(f"  日期: {result['date']}")
    print(f"  股票: {result['name']} ({result['code']})")
    print(f"  主力净流入: {result['main_net_inflow']:.0f} 元")
    print(f"  超大单: {result['super_large_net']:.0f} 元")
    print(f"  大单: {result['large_net']:.0f} 元")
    print(f"  主力净流入占比: {result['main_net_inflow_ratio']:.2f}%")
else:
    print(f"❌ 失败: {result['error']}")

print()

# 测试2: 获取板块排行
print("🏭 测试2: 获取行业板块涨跌幅排行")
print("-" * 70)
result = api.get_sector_performance('industry')
if result['success']:
    print(f"✅ 成功")
    print(f"  日期: {result['date']}")
    print(f"  板块数量: {len(result['list'])} 个")
    if result['list']:
        print(f"  TOP5:")
        for i, sector in enumerate(result['list'][:5], 1):
            print(f"    {i}. {sector['sector_name']}: {sector['change_pct']:+.2f}%")
else:
    print(f"❌ 失败: {result['error']}")

print()

# 测试3: 获取北向资金
print("💰 测试3: 获取北向资金流向")
print("-" * 70)
result = api.get_north_money_flow()
if result['success']:
    print(f"✅ 成功")
    print(f"  日期: {result['date']}")
    print(f"  沪股通净流入: {result['shg_net_inflow']/100000000:.2f} 亿元")
    print(f"  深股通净流入: {result['szg_net_inflow']/100000000:.2f} 亿元")
    print(f"  总净流入: {result['total_net_inflow']/100000000:.2f} 亿元")
else:
    print(f"❌ 失败: {result['error']}")

print()
print("=" * 70)
print("  测试完成！")
print("=" * 70)
