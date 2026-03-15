#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试采集中国电建数据"""
import sys
from pathlib import Path

# Windows UTF-8输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加skill路径
skill_path = Path('C:/AI-Agent-Local/openclaw-ali/skills/eastmoney-stock-claude')
sys.path.insert(0, str(skill_path))

from tool import EastMoneyStockAPI

print("=" * 70)
print("  采集中国电建（601669）个股补充数据")
print("=" * 70)
print()

api = EastMoneyStockAPI()

# 测试1: 资金流向
print("📊 [1/7] 资金流向")
print("-" * 70)
result = api.get_stock_money_flow('601669')
if result['success']:
    print(f"✅ 成功")
    print(f"  日期: {result['date']}")
    print(f"  股票: {result['name']} ({result['code']})")
    print(f"  主力净流入: {result['main_net_inflow']:,.0f} 元")
    print(f"  超大单: {result['super_large_net']:,.0f} 元")
    print(f"  大单: {result['large_net']:,.0f} 元")
    print(f"  中单: {result['medium_net']:,.0f} 元")
    print(f"  小单: {result['small_net']:,.0f} 元")
    print(f"  主力净流入占比: {result['main_net_inflow_ratio']:.2f}%")
else:
    print(f"❌ 失败: {result['error']}")

print()

# 测试2: 北向持股
print("💰 [2/7] 北向持股")
print("-" * 70)
result = api.get_stock_north_holdings('601669')
if result['success']:
    print(f"✅ 成功")
    print(f"  日期: {result['date']}")
    print(f"  股票: {result['name']} ({result['code']})")
    print(f"  北向持股比例: {result['hold_ratio']:.2f}%")
    print(f"  北向持股市值: {result['hold_amount']:,.0f} 元")
    print(f"  持股变化: {result['hold_change']:+.2f}%")
    print(f"  持股数量: {result['hold_shares']:,.0f} 股")
    if 'note' in result:
        print(f"  备注: {result['note']}")
else:
    print(f"❌ 失败: {result['error']}")

print()

# 测试3: 融资融券
print("💳 [3/7] 融资融券")
print("-" * 70)
result = api.get_stock_margin_trading('601669')
if result['success']:
    print(f"✅ 成功")
    print(f"  日期: {result['date']}")
    print(f"  股票: {result['name']} ({result['code']})")
    print(f"  融资余额: {result['margin_balance']:,.0f} 元")
    print(f"  融券余额: {result['short_balance']:,.0f} 元")
    print(f"  融资买入额: {result['margin_buy']:,.0f} 元")
    print(f"  融券卖出量: {result['short_sell']:,.0f} 股")
else:
    print(f"❌ 失败: {result['error']}")

print()

# 测试4: 股东数据
print("👥 [4/7] 股东数据")
print("-" * 70)
result = api.get_stock_shareholders('601669')
if result['success']:
    print(f"✅ 成功")
    print(f"  日期: {result['date']}")
    print(f"  股票: {result['name']} ({result['code']})")
    print(f"  股东户数: {result['shareholder_count']:,} 户")
    print(f"  户均持股: {result['shares_per_holder']:,.0f} 股")
    print(f"  户数变化: {result['count_change']:+.2f}%")
    print(f"  十大股东持股比例: {result['top10_ratio']:.2f}%")
else:
    print(f"❌ 失败: {result['error']}")

print()

# 测试5: 限售解禁
print("🔓 [5/7] 限售解禁")
print("-" * 70)
result = api.get_stock_unlock('601669')
if result['success']:
    print(f"✅ 成功")
    print(f"  找到 {len(result['list'])} 条解禁记录")
    if result['list']:
        for i, item in enumerate(result['list'][:5], 1):  # 只显示前5条
            print(f"  [{i}] {item['unlock_date']}")
            print(f"      解禁数量: {item['unlock_shares']:,.0f} 股")
            print(f"      解禁市值: {item['unlock_value']:,.0f} 元")
            print(f"      占总股本: {item['ratio_to_total']:.2f}%")
            print(f"      解禁类型: {item['unlock_type']}")
    else:
        print(f"  无近期解禁数据")
else:
    print(f"❌ 失败: {result['error']}")

print()

# 测试6: 大宗交易
print("📦 [6/7] 大宗交易")
print("-" * 70)
result = api.get_stock_block_trading('601669')
if result['success']:
    print(f"✅ 成功")
    print(f"  找到 {len(result['list'])} 条大宗交易记录")
    if result['list']:
        for i, item in enumerate(result['list'][:5], 1):  # 只显示前5条
            print(f"  [{i}] {item['trade_date']}")
            print(f"      成交价: {item['trade_price']:.2f} 元")
            print(f"      溢价率: {item['premium_rate']:+.2f}%")
            print(f"      成交量: {item['trade_volume']:,.0f} 股")
            print(f"      成交额: {item['trade_amount']:,.0f} 元")
            print(f"      买方: {item['buyer_seat']}")
            print(f"      卖方: {item['seller_seat']}")
    else:
        print(f"  无近期大宗交易数据")
else:
    print(f"❌ 失败: {result['error']}")

print()

# 测试7: 个股事件
print("📰 [7/7] 个股事件")
print("-" * 70)
result = api.get_stock_events('601669')
if result['success']:
    print(f"✅ 成功")
    print(f"  找到 {len(result['list'])} 条事件记录")
    if result['list']:
        for i, item in enumerate(result['list'][:5], 1):  # 只显示前5条
            print(f"  [{i}] {item['event_date']} - {item['event_type']}")
            print(f"      标题: {item['event_title']}")
            print(f"      重要性: {item['importance']}")
    else:
        print(f"  无近期事件数据")
else:
    print(f"❌ 失败: {result['error']}")

print()
print("=" * 70)
print("  采集完成！")
print("=" * 70)
