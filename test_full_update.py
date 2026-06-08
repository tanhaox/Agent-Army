#!/usr/bin/env python3
"""test_full_update.py - 完整更新流程测试"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace')
import duckdb
from agent_army.holdings_manager import get_holdings_manager

m = get_holdings_manager()

# 模拟用户粘贴的表格数据
table_text = """证券代码\t证券名称\t持仓数量\t可用数量\t冻结数量\t参考成本价\t当前价\t浮动盈亏\t盈亏比例(%)\t最新市值\t仓位占比(%)\t持股天数
000651\t格力电器\t1200\t1200\t0\t37.587\t37.50\t-384.00\t-0.85\t45000.00\t22.50\t15
000725\t京东方A\t8400\t8400\t0\t3.913\t4.05\t+1162.00\t+3.53\t34020.00\t17.01\t12
002340\t格林美\t700\t700\t0\t7.941\t8.12\t+125.30\t+2.25\t5684.00\t2.84\t8
600728\t佳都科技\t7400\t7400\t0\t5.691\t5.70\t+66.60\t+0.16\t42180.00\t21.09\t6
600887\t伊利股份\t2000\t2000\t0\t26.279\t26.20\t-158.00\t-0.30\t52400.00\t26.20\t4"""

print('=== 更新前持仓 ===')
holdings = m.get_current_holdings()
for code, info in holdings.items():
    print(f'  {code} {info["name"]}: {info["shares"]}股')

print()
print('=== 执行更新 ===')
result = m.update_from_table(table_text)
for key, value in result.items():
    print(f'  {key}: {value}')

print()
print('=== 更新后持仓 ===')
holdings2 = m.get_current_holdings()
for code, info in holdings2.items():
    frozen = info.get('frozen_shares', 0)
    daily = info.get('daily_profit_loss', 0)
    print(f'  {code} {info["name"]}: {info["shares"]}股, 冻结={frozen}, 当日盈亏={daily}')

print()
print('=== 总资产检查 ===')
assets = m.get_total_assets()
for key, value in assets.items():
    print(f'  {key}: {value}')

print()
print('=== 历史归档检查 ===')
conn = duckdb.connect('/root/.openclaw/workspace/data/holdings.db')
count = conn.execute('SELECT COUNT(*) FROM holdings_history').fetchone()[0]
print(f'  历史记录数: {count}')
if count > 0:
    rows = conn.execute('SELECT stock_code, stock_name, shares, source FROM holdings_history').fetchall()
    for r in rows:
        print(f'  {r[0]} {r[1]}: {r[2]}股 ({r[3]})')

# 验证字段完整性
print()
print('=== 字段完整性验证 ===')
df = conn.execute("SELECT * FROM current_holdings LIMIT 1").fetchdf()
for col in df.columns:
    val = df[col].iloc[0]
    print(f'  {col}: {val}')

conn.close()

print()
print('=== 测试完成 ===')
