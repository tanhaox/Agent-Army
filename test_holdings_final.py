#!/usr/bin/env python3
"""
test_holdings_final.py - 资金计算逻辑最终验证
测试场景：
1. 初始无持仓，20万现金
2. 买入格力电器 → 验证资金计算
3. 清仓格力 + 买入京东方 → 验证清仓盈亏影响流动资金
4. 多次更新后 → 总资产 = 初始 + 浮动盈亏 + 已实现盈亏
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace')

import duckdb
from datetime import datetime

DB_PATH = '/root/.openclaw/workspace/data/holdings.db'
INITIAL_CAPITAL = 200000


def backup_tables():
    """备份当前数据"""
    conn = duckdb.connect(DB_PATH)
    backups = {}
    for table in ['current_holdings', 'cleared_holdings', 'operations', 'holdings_history']:
        try:
            backups[table] = conn.execute(f"SELECT * FROM {table}").fetchdf()
        except Exception:
            backups[table] = None
    # global_config
    try:
        backups['global_config'] = conn.execute("SELECT * FROM global_config").fetchdf()
    except Exception:
        backups['global_config'] = None
    conn.close()
    return backups


def restore_tables(backups):
    """恢复备份数据"""
    conn = duckdb.connect(DB_PATH)
    # 清空测试数据
    conn.execute("DELETE FROM current_holdings")
    conn.execute("DELETE FROM operations")
    conn.execute("DELETE FROM holdings_history")
    # 恢复原始数据
    for table in ['current_holdings', 'cleared_holdings']:
        if backups[table] is not None and not backups[table].empty:
            for _, row in backups[table].iterrows():
                cols = list(row.index)
                vals = list(row.values)
                placeholders = ','.join(['?'] * len(cols))
                try:
                    conn.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})", vals)
                except Exception:
                    pass
    # 恢复global_config
    if backups['global_config'] is not None and not backups['global_config'].empty:
        conn.execute("DELETE FROM global_config")
        for _, row in backups['global_config'].iterrows():
            conn.execute("INSERT INTO global_config VALUES (?, ?, ?)", list(row.values))
    conn.close()


def clear_for_test():
    """清空所有持仓和清仓记录，保留初始资金配置"""
    conn = duckdb.connect(DB_PATH)
    conn.execute("DELETE FROM current_holdings")
    conn.execute("DELETE FROM cleared_holdings")
    conn.execute("DELETE FROM operations")
    conn.execute("DELETE FROM holdings_history")
    # 确保初始资金正确
    conn.execute("DELETE FROM global_config WHERE key = 'cash_balance'")
    conn.execute("DELETE FROM global_config WHERE key = 'initial_capital'")
    conn.execute("INSERT INTO global_config (key, value, updated_at) VALUES ('initial_capital', 200000, now())")
    conn.close()
    print("  测试环境已清空，初始资金 = 200000\n")


def verify(label, expected, actual, tolerance=0.5):
    """验证数值是否匹配"""
    diff = abs(expected - actual)
    ok = diff <= tolerance
    symbol = "OK" if ok else "FAIL"
    print(f"    {symbol} {label}: 期望={expected:.2f}, 实际={actual:.2f}, 差={diff:.2f}")
    return ok


def test_scenario_1():
    """场景1：初始无持仓，验证20万现金"""
    print("=" * 60)
    print("场景1：初始状态（无持仓）")
    print("=" * 60)

    # 需要 import 前先 reload 确保拿到新代码
    import importlib
    import agent_army.holdings_manager as hm
    importlib.reload(hm)
    manager = hm.get_holdings_manager()

    assets = manager.get_total_assets()
    print(f"  初始资金: {assets['initial_capital']}")
    print(f"  持仓成本: {assets['total_holdings_cost']}")
    print(f"  持仓市值: {assets['total_market_value']}")
    print(f"  流动资金: {assets['cash_balance']}")
    print(f"  总资产: {assets['total_assets']}")

    all_ok = True
    all_ok &= verify("初始资金", 200000, assets['initial_capital'])
    all_ok &= verify("持仓成本(无持仓)", 0, assets['total_holdings_cost'])
    all_ok &= verify("流动资金(无持仓)", 200000, assets['cash_balance'])
    all_ok &= verify("总资产(无持仓)", 200000, assets['total_assets'])
    all_ok &= verify("总盈亏", 0, assets['total_pnl'])
    return all_ok


def test_scenario_2():
    """场景2：买入格力电器1100股"""
    print("\n" + "=" * 60)
    print("场景2：买入格力电器 1100股, 成本37.602, 当前37.80")
    print("=" * 60)

    import importlib
    import agent_army.holdings_manager as hm
    importlib.reload(hm)
    manager = hm.get_holdings_manager()

    # 格力电器 1100股 × 37.602 = 41362.2 成本
    # 当前价 37.80 × 1100 = 41580 市值
    # 浮动盈亏 = 41580 - 41362.2 = 217.8
    # 流动资金 = 200000 - 41362.2 + 0 = 158637.8
    # 总资产 = 41580 + 158637.8 = 200217.8

    table_text = """证券代码\t证券名称\t持仓数量\t可用数量\t冻结数量\t参考成本价\t当前价\t浮动盈亏\t盈亏比例(%)\t最新市值\t仓位占比(%)\t持股天数
000651\t格力电器\t1100\t1100\t0\t37.602\t37.80\t217.80\t0.53\t41580.00\t20.79\t1"""

    result = manager.update_from_table(table_text)
    print(f"  更新结果:")
    for k, v in result.items():
        if isinstance(v, float):
            print(f"    {k}: {v:.2f}")
        else:
            print(f"    {k}: {v}")

    assets = manager.get_total_assets()
    print(f"\n  验证:")
    all_ok = True
    all_ok &= verify("持仓成本", 41362.2, assets['total_holdings_cost'])
    all_ok &= verify("持仓市值", 41580.0, assets['total_market_value'])
    all_ok &= verify("流动资金", 158637.8, assets['cash_balance'])
    all_ok &= verify("总资产", 200217.8, assets['total_assets'])
    all_ok &= verify("浮动盈亏", 217.8, assets['floating_pnl'])
    all_ok &= verify("总盈亏", 217.8, assets['total_pnl'])
    all_ok &= verify("总盈亏%", 0.11, assets['total_pnl_pct'])
    return all_ok


def test_scenario_3():
    """场景3：清仓格力 + 买入京东方A"""
    print("\n" + "=" * 60)
    print("场景3：清仓格力电器 + 买入京东方A 5000股")
    print("=" * 60)

    import importlib
    import agent_army.holdings_manager as hm
    importlib.reload(hm)
    manager = hm.get_holdings_manager()

    # 清仓格力：1100股 × 37.80 = 41580 卖出价
    # 格力成本 37.602，清仓盈亏 = (37.80 - 37.602) × 1100 = 217.8
    # 京东方A 5000股 × 3.90 = 19500 成本
    # 当前价 4.00 × 5000 = 20000 市值
    # 浮动盈亏 = 20000 - 19500 = 500
    # 流动资金 = 200000 - 19500 + 217.8 = 180717.8
    # 总资产 = 20000 + 180717.8 = 200717.8

    table_text = """证券代码\t证券名称\t持仓数量\t可用数量\t冻结数量\t参考成本价\t当前价\t浮动盈亏\t盈亏比例(%)\t最新市值\t仓位占比(%)\t持股天数
000651\t格力电器\t0\t0\t0\t37.602\t37.80\t217.80\t0.53\t0\t0\t0
000725\t京东方A\t5000\t5000\t0\t3.90\t4.00\t500.00\t2.56\t20000.00\t9.97\t1"""

    result = manager.update_from_table(table_text)
    print(f"  更新结果:")
    for k, v in result.items():
        if isinstance(v, float):
            print(f"    {k}: {v:.2f}")
        else:
            print(f"    {k}: {v}")

    assets = manager.get_total_assets()
    print(f"\n  验证:")
    all_ok = True
    all_ok &= verify("持仓成本", 19500.0, assets['total_holdings_cost'])
    all_ok &= verify("持仓市值", 20000.0, assets['total_market_value'])
    all_ok &= verify("累计清仓盈亏", 217.8, assets['realized_pnl'])
    all_ok &= verify("流动资金", 180717.8, assets['cash_balance'])
    all_ok &= verify("总资产", 200717.8, assets['total_assets'])
    all_ok &= verify("浮动盈亏", 500.0, assets['floating_pnl'])
    all_ok &= verify("总盈亏", 717.8, assets['total_pnl'])
    return all_ok


def test_scenario_4():
    """场景4：多次更新后，再次加仓京东方 + 新买入伊利"""
    print("\n" + "=" * 60)
    print("场景4：加仓京东方A + 新买入伊利股份")
    print("=" * 60)

    import importlib
    import agent_army.holdings_manager as hm
    importlib.reload(hm)
    manager = hm.get_holdings_manager()

    # 上次状态：京东方 5000股 × 3.90 成本 = 19500，清仓盈亏 217.8
    # 本次：京东方加仓到 8000股 × 3.95 = 31600 成本
    #        伊利 1000股 × 26.30 = 26300 成本
    # 总成本 = 31600 + 26300 = 57900
    # 京东方市值 = 8000 × 4.05 = 32400
    # 伊利市值 = 1000 × 26.50 = 26500
    # 总市值 = 32400 + 26500 = 58900
    # 浮动盈亏 = 58900 - 57900 = 1000
    # 累计清仓盈亏仍为 217.8
    # 流动资金 = 200000 - 57900 + 217.8 = 142317.8
    # 总资产 = 58900 + 142317.8 = 201217.8
    # 总盈亏 = 1000 + 217.8 = 1217.8

    table_text = """证券代码\t证券名称\t持仓数量\t可用数量\t冻结数量\t参考成本价\t当前价\t浮动盈亏\t盈亏比例(%)\t最新市值\t仓位占比(%)\t持股天数
000725\t京东方A\t8000\t8000\t0\t3.95\t4.05\t800.00\t2.53\t32400.00\t16.10\t3
600887\t伊利股份\t1000\t1000\t0\t26.30\t26.50\t200.00\t0.76\t26500.00\t13.17\t1"""

    result = manager.update_from_table(table_text)
    print(f"  更新结果:")
    for k, v in result.items():
        if isinstance(v, float):
            print(f"    {k}: {v:.2f}")
        else:
            print(f"    {k}: {v}")

    assets = manager.get_total_assets()
    print(f"\n  验证:")
    all_ok = True
    all_ok &= verify("持仓成本", 57900.0, assets['total_holdings_cost'])
    all_ok &= verify("持仓市值", 58900.0, assets['total_market_value'])
    all_ok &= verify("累计清仓盈亏", 217.8, assets['realized_pnl'])
    all_ok &= verify("流动资金", 142317.8, assets['cash_balance'])
    all_ok &= verify("总资产", 201217.8, assets['total_assets'])
    all_ok &= verify("浮动盈亏", 1000.0, assets['floating_pnl'])
    all_ok &= verify("总盈亏", 1217.8, assets['total_pnl'])
    all_ok &= verify("总盈亏%", 0.61, assets['total_pnl_pct'])

    # 验证恒等式：总资产 = 初始资金 + 总盈亏
    identity = assets['initial_capital'] + assets['total_pnl']
    all_ok &= verify("总资产 = 初始+总盈亏", 201217.8, identity)

    return all_ok


def test_scenario_5():
    """场景5：验证表格中消失的股票自动清仓"""
    print("\n" + "=" * 60)
    print("场景5：表格中消失的股票 → 自动清仓")
    print("=" * 60)

    import importlib
    import agent_army.holdings_manager as hm
    importlib.reload(hm)
    manager = hm.get_holdings_manager()

    # 上次有京东方 + 伊利。这次只提交伊利（京东方消失）
    # 京东方应自动清仓
    # 京东方清仓盈亏 = (4.05 - 3.95) × 8000 = 800
    # 伊利 1000股 × 26.30 = 26300 成本, 市值 26500

    table_text = """证券代码\t证券名称\t持仓数量\t可用数量\t冻结数量\t参考成本价\t当前价\t浮动盈亏\t盈亏比例(%)\t最新市值\t仓位占比(%)\t持股天数
600887\t伊利股份\t1000\t1000\t0\t26.30\t26.50\t200.00\t0.76\t26500.00\t100\t5"""

    result = manager.update_from_table(table_text)
    print(f"  更新结果:")
    for k, v in result.items():
        if isinstance(v, float):
            print(f"    {k}: {v:.2f}")
        else:
            print(f"    {k}: {v}")

    # 验证清仓记录
    conn = duckdb.connect(DB_PATH)
    cleared = conn.execute("SELECT code, name, profit_loss, clear_reason FROM cleared_holdings").fetchall()
    print(f"\n  清仓记录 ({len(cleared)}条):")
    for r in cleared:
        print(f"    {r[0]} {r[1]}: 盈亏={r[2]}, 原因={r[3]}")
    conn.close()

    assets = manager.get_total_assets()
    print(f"\n  验证:")
    all_ok = True
    all_ok &= verify("持仓成本", 26300.0, assets['total_holdings_cost'])
    all_ok &= verify("持仓市值", 26500.0, assets['total_market_value'])
    # 累计清仓盈亏 = 217.8(格力) + 800(京东方) = 1017.8
    all_ok &= verify("累计清仓盈亏", 1017.8, assets['realized_pnl'])
    # 流动资金 = 200000 - 26300 + 1017.8 = 174717.8
    all_ok &= verify("流动资金", 174717.8, assets['cash_balance'])
    # 总资产 = 26500 + 174717.8 = 201217.8
    all_ok &= verify("总资产", 201217.8, assets['total_assets'])

    return all_ok


if __name__ == '__main__':
    print("=" * 60)
    print("持仓管理器资金计算 - 最终验证测试")
    print("公式: 流动资金 = 初始资金 - 持仓成本 + 累计清仓盈亏")
    print("=" * 60)

    # 备份
    backups = backup_tables()

    # 清空测试环境
    clear_for_test()

    results = {}
    try:
        results['场景1'] = test_scenario_1()
        results['场景2'] = test_scenario_2()
        results['场景3'] = test_scenario_3()
        results['场景4'] = test_scenario_4()
        results['场景5'] = test_scenario_5()
    finally:
        # 恢复备份数据
        print("\n" + "=" * 60)
        print("恢复原始数据...")
        restore_tables(backups)
        print("已恢复")

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    total_pass = sum(1 for v in results.values() if v)
    total = len(results)
    for name, ok in results.items():
        symbol = "PASS" if ok else "FAIL"
        print(f"  {symbol} {name}")
    print(f"\n  通过: {total_pass}/{total}")
    print("=" * 60)
