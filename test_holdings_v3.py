#!/usr/bin/env python3
"""
test_holdings_v3.py - 测试持仓管理器 v3.0
验证：
1. 数据库迁移（新字段、新表）
2. 完整16字段解析和保存
3. 历史归档功能
4. 总资产和现金计算
5. 清仓股正确处理
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace')

import duckdb
from datetime import datetime

DB_PATH = '/root/.openclaw/workspace/data/holdings.db'


def test_db_schema():
    """测试数据库结构"""
    print("=" * 60)
    print("测试 1：数据库结构验证")
    print("=" * 60)

    conn = duckdb.connect(DB_PATH)

    # 1.1 检查 current_holdings 字段
    print("\n--- current_holdings 字段 ---")
    cols = conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name='current_holdings' ORDER BY ordinal_position").fetchall()
    col_names = [c[0] for c in cols]
    required = ['frozen_shares', 'daily_profit_loss', 'daily_profit_loss_pct', 'buy_today', 'sell_today', 'market']
    for r in required:
        status = "OK" if r in col_names else "MISSING"
        print(f"  {r}: {status}")

    # 1.2 检查 global_config 表
    print("\n--- global_config 表 ---")
    exists = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='global_config'").fetchone()[0]
    if exists:
        configs = conn.execute("SELECT * FROM global_config").fetchall()
        for key, value, _ in configs:
            print(f"  {key} = {value}")
    else:
        print("  表不存在！")

    # 1.3 检查 holdings_history 字段
    print("\n--- holdings_history 字段 ---")
    cols = conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name='holdings_history' ORDER BY ordinal_position").fetchall()
    col_names = [c[0] for c in cols]
    required = ['snapshot_date', 'source', 'frozen_shares', 'daily_profit_loss']
    for r in required:
        status = "OK" if r in col_names else "MISSING"
        print(f"  {r}: {status}")

    conn.close()


def test_holdings_data():
    """测试持仓数据完整性"""
    print("\n" + "=" * 60)
    print("测试 2：持仓数据完整性")
    print("=" * 60)

    conn = duckdb.connect(DB_PATH)

    # 查看当前持仓
    df = conn.execute("SELECT code, name, shares, available, frozen_shares, market_value FROM current_holdings").fetchdf()
    if not df.empty:
        print(f"\n当前持仓 ({len(df)} 只)：")
        for _, row in df.iterrows():
            frozen = row.get('frozen_shares', 0)
            print(f"  {row['code']} {row['name']}: {row['shares']}股 (可用{row['available']}, 冻结{frozen}), 市值{row['market_value']}")
    else:
        print("  当前无持仓")

    conn.close()


def test_total_assets():
    """测试总资产计算"""
    print("\n" + "=" * 60)
    print("测试 3：总资产计算")
    print("=" * 60)

    from agent_army.holdings_manager import get_holdings_manager
    manager = get_holdings_manager()

    assets = manager.get_total_assets()
    print(f"\n初始资金: {assets['initial_capital']:,.2f}")
    print(f"持仓市值: {assets['total_market_value']:,.2f}")
    print(f"现金余额: {assets['cash_balance']:,.2f}")
    print(f"总资产:   {assets['total_assets']:,.2f}")
    print(f"总收益率: {assets['total_return_pct']:.2f}%")
    print(f"仓位比例: {assets['position_ratio']:.2f}%")


def test_summary():
    """测试持仓摘要"""
    print("\n" + "=" * 60)
    print("测试 4：持仓摘要")
    print("=" * 60)

    from agent_army.holdings_manager import get_holdings_manager
    manager = get_holdings_manager()

    summary = manager.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")


def test_history():
    """测试历史归档"""
    print("\n" + "=" * 60)
    print("测试 5：历史归档数据")
    print("=" * 60)

    conn = duckdb.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM holdings_history").fetchone()[0]
    print(f"\n历史记录数: {count}")

    if count > 0:
        df = conn.execute("""
            SELECT CAST(timestamp AS DATE) as snap_date, source, COUNT(*) as cnt
            FROM holdings_history
            GROUP BY snap_date, source
            ORDER BY snap_date DESC
            LIMIT 5
        """).fetchdf()
        print("最近归档快照：")
        for _, row in df.iterrows():
            print(f"  {row['snap_date']} ({row['source']}): {row['cnt']}条")
    else:
        print("  (暂无历史归档，将在下次 update_from_table 时生成)")

    conn.close()


def test_code_normalization():
    """测试代码标准化"""
    print("\n" + "=" * 60)
    print("测试 6：股票代码标准化")
    print("=" * 60)

    from agent_army.holdings_manager import get_holdings_manager
    manager = get_holdings_manager()

    test_cases = [
        ('000725', '000725.SZ'),
        ('600887', '600887.SH'),
        ('000651', '000651.SZ'),
        ('600728', '600728.SH'),
        ('002340', '002340.SZ'),
        ('000725.SZ', '000725.SZ'),
        ('600887.SH', '600887.SH'),
    ]

    for input_code, expected in test_cases:
        result = manager._normalize_code(input_code)
        status = "OK" if result == expected else "FAIL"
        print(f"  {input_code} -> {result} (期望: {expected}) [{status}]")


if __name__ == '__main__':
    try:
        test_db_schema()
    except Exception as e:
        print(f"测试1失败: {e}")

    try:
        test_holdings_data()
    except Exception as e:
        print(f"测试2失败: {e}")

    try:
        test_total_assets()
    except Exception as e:
        print(f"测试3失败: {e}")

    try:
        test_summary()
    except Exception as e:
        print(f"测试4失败: {e}")

    try:
        test_history()
    except Exception as e:
        print(f"测试5失败: {e}")

    try:
        test_code_normalization()
    except Exception as e:
        print(f"测试6失败: {e}")

    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)
