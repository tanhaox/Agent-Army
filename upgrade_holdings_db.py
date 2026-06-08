#!/usr/bin/env python3
"""
upgrade_holdings_db.py - 持仓数据库升级脚本
功能：
1. current_holdings 表添加缺失字段
2. 创建 global_config 表（初始资金跟踪）
3. 确保 holdings_history 表结构正确

日期：2026-04-12
"""

import duckdb
import sys

DB_PATH = '/root/.openclaw/workspace/data/holdings.db'


def get_connection():
    return duckdb.connect(DB_PATH)


def check_column_exists(conn, table, column):
    """检查表中是否存在指定列"""
    result = conn.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'").fetchall()
    return len(result) > 0


def upgrade():
    conn = get_connection()

    # ========== 1. current_holdings 添加缺失字段 ==========
    print("=== 升级 current_holdings 表 ===")

    new_columns = [
        ('frozen_shares', 'INTEGER DEFAULT 0'),
        ('daily_profit_loss', 'REAL DEFAULT 0'),
        ('daily_profit_loss_pct', 'REAL DEFAULT 0'),
        ('buy_today', 'INTEGER DEFAULT 0'),
        ('sell_today', 'INTEGER DEFAULT 0'),
        ('market', "VARCHAR(10) DEFAULT ''"),
    ]

    for col_name, col_type in new_columns:
        if not check_column_exists(conn, 'current_holdings', col_name):
            conn.execute(f"ALTER TABLE current_holdings ADD COLUMN {col_name} {col_type}")
            print(f"  + 添加列: {col_name} ({col_type})")
        else:
            print(f"  = 已存在: {col_name}")

    # ========== 2. 创建 global_config 表 ==========
    print("\n=== 创建 global_config 表 ===")

    if not conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='global_config'").fetchone()[0]:
        conn.execute("""
            CREATE TABLE global_config (
                key VARCHAR(50) PRIMARY KEY,
                value REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  + 创建 global_config 表")
    else:
        print("  = global_config 表已存在")

    # 插入初始资金配置
    conn.execute("""
        INSERT INTO global_config (key, value, updated_at)
        VALUES ('initial_capital', 200000, now())
        ON CONFLICT (key) DO UPDATE SET updated_at = now()
    """)
    print("  + 设置 initial_capital = 200000")

    # 插入现金余额配置（如果不存在）
    conn.execute("""
        INSERT INTO global_config (key, value, updated_at)
        VALUES ('cash_balance', 0, now())
        ON CONFLICT (key) DO NOTHING
    """)
    print("  + 初始化 cash_balance")

    # ========== 3. 确保 holdings_history 表结构正确 ==========
    print("\n=== 检查 holdings_history 表 ===")

    if not conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='holdings_history'").fetchone()[0]:
        conn.execute("""
            CREATE TABLE holdings_history (
                id INTEGER PRIMARY KEY,
                code VARCHAR(20),
                name VARCHAR(50),
                shares INTEGER,
                available INTEGER,
                frozen_shares INTEGER DEFAULT 0,
                cost_price REAL,
                current_price REAL,
                profit_loss REAL,
                profit_loss_pct REAL,
                daily_profit_loss REAL DEFAULT 0,
                daily_profit_loss_pct REAL DEFAULT 0,
                market_value REAL,
                position_pct REAL,
                holding_days INTEGER,
                buy_today INTEGER DEFAULT 0,
                sell_today INTEGER DEFAULT 0,
                market VARCHAR(10) DEFAULT '',
                snapshot_date DATE,
                source VARCHAR(20) DEFAULT 'user_update',
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  + 创建 holdings_history 表")
    else:
        # 检查并添加缺失列
        history_new_cols = [
            ('frozen_shares', 'INTEGER DEFAULT 0'),
            ('daily_profit_loss', 'REAL DEFAULT 0'),
            ('daily_profit_loss_pct', 'REAL DEFAULT 0'),
            ('buy_today', 'INTEGER DEFAULT 0'),
            ('sell_today', 'INTEGER DEFAULT 0'),
            ('market', "VARCHAR(10) DEFAULT ''"),
            ('source', "VARCHAR(20) DEFAULT 'user_update'"),
            ('archived_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ]
        for col_name, col_type in history_new_cols:
            if not check_column_exists(conn, 'holdings_history', col_name):
                conn.execute(f"ALTER TABLE holdings_history ADD COLUMN {col_name} {col_type}")
                print(f"  + 添加列: {col_name} ({col_type})")
        print("  = holdings_history 表已存在，已检查字段")

    # ========== 4. 验证 ==========
    print("\n=== 验证表结构 ===")

    # current_holdings
    cols = conn.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='current_holdings' ORDER BY ordinal_position").fetchall()
    print(f"\ncurrent_holdings ({len(cols)} 列):")
    for col_name, col_type in cols:
        print(f"  {col_name}: {col_type}")

    # global_config
    configs = conn.execute("SELECT * FROM global_config").fetchall()
    print(f"\nglobal_config ({len(configs)} 条):")
    for key, value, updated_at in configs:
        print(f"  {key} = {value} (更新于 {updated_at})")

    # holdings_history
    cols = conn.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='holdings_history' ORDER BY ordinal_position").fetchall()
    print(f"\nholdings_history ({len(cols)} 列):")
    for col_name, col_type in cols:
        print(f"  {col_name}: {col_type}")

    conn.close()
    print("\n=== 升级完成 ===")


if __name__ == '__main__':
    upgrade()
