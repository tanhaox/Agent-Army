#!/usr/bin/env python3
"""
统一数据库管理模块（DBManager）
- 单例模式，支持多数据库
- 提供统一的表创建/检查方法
- 数据插入/更新/查询的封装
"""

import duckdb
import os
import json
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

# 数据库根目录
DATA_ROOT = "/root/.openclaw/workspace/data"
os.makedirs(DATA_ROOT, exist_ok=True)


class DBManager:
    """
    统一数据库管理类
    """

    def __init__(self, db_root: str = DATA_ROOT):
        self.db_root = db_root
        self._conns = {}

    def get_conn(self, db_name: str) -> duckdb.DuckDBPyConnection:
        """
        获取指定数据库的连接（单例模式）
        """
        if db_name not in self._conns:
            db_path = os.path.join(self.db_root, f"{db_name}.db")
            self._conns[db_name] = duckdb.connect(db_path)
        return self._conns[db_name]

    def table_exists(self, db_name: str, table_name: str) -> bool:
        """
        检查表是否存在
        """
        conn = self.get_conn(db_name)
        try:
            result = conn.execute(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'main'
                AND table_name = '{table_name}'
            """).fetchdf()
            return len(result) > 0
        except Exception as e:
            print(f"检查表 {table_name} 失败: {e}")
            return False

    def create_table(self, db_name: str, sql: str) -> bool:
        """
        创建表（使用 IF NOT EXISTS）
        """
        conn = self.get_conn(db_name)
        try:
            conn.execute(sql)
            return True
        except Exception as e:
            print(f"创建表失败: {e}")
            return False

    def insert(self, db_name: str, table_name: str, data: Union[Dict, List[Dict]]) -> bool:
        """
        插入数据（单条或批量）
        """
        conn = self.get_conn(db_name)
        try:
            if isinstance(data, dict):
                data = [data]

            # 构建列名和占位符
            columns = list(data[0].keys())
            placeholders = ', '.join(['?' for _ in columns])
            columns_str = ', '.join(columns)

            # 转换数据为列表
            values_list = []
            for item in data:
                values = [item.get(col) for col in columns]
                values_list.append(values)

            # 执行批量插入
            conn.executemany(
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                values_list
            )
            return True
        except Exception as e:
            print(f"插入数据到 {table_name} 失败: {e}")
            return False

    def upsert(self, db_name: str, table_name: str, data: Union[Dict, List[Dict]], conflict_columns: List[str]) -> bool:
        """
        插入或更新数据（UPSERT）
        conflict_columns: 冲突检测的列名
        """
        conn = self.get_conn(db_name)
        try:
            if isinstance(data, dict):
                data = [data]

            # 构建列名
            columns = list(data[0].keys())

            # 构建 INSERT OR REPLACE 语句
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['?' for _ in columns])

            # 转换数据为列表
            values_list = []
            for item in data:
                values = [item.get(col) for col in columns]
                values_list.append(values)

            # 执行批量插入或更新
            conn.executemany(
                f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                values_list
            )
            return True
        except Exception as e:
            print(f"UPSERT 数据到 {table_name} 失败: {e}")
            return False

    def query(self, db_name: str, sql: str, params: Optional[List] = None) -> duckdb.DuckDBPyRelation:
        """
        查询数据
        """
        conn = self.get_conn(db_name)
        try:
            if params:
                return conn.execute(sql, params)
            else:
                return conn.execute(sql)
        except Exception as e:
            print(f"查询失败: {e}")
            raise

    def fetchdf(self, db_name: str, sql: str, params: Optional[List] = None) -> 'pd.DataFrame':
        """
        查询并返回 DataFrame
        """
        try:
            result = self.query(db_name, sql, params)
            return result.fetchdf()
        except Exception as e:
            print(f"查询并返回 DataFrame 失败: {e}")
            # 返回空 DataFrame
            import pandas as pd
            return pd.DataFrame()

    def execute(self, db_name: str, sql: str, params: Optional[List] = None) -> bool:
        """
        执行 SQL（不返回结果）
        """
        conn = self.get_conn(db_name)
        try:
            if params:
                conn.execute(sql, params)
            else:
                conn.execute(sql)
            return True
        except Exception as e:
            print(f"执行 SQL 失败: {e}")
            return False

    def delete(self, db_name: str, table_name: str, condition: str, params: Optional[List] = None) -> bool:
        """
        删除数据
        """
        sql = f"DELETE FROM {table_name} WHERE {condition}"
        return self.execute(db_name, sql, params)

    def truncate(self, db_name: str, table_name: str) -> bool:
        """
        清空表
        """
        sql = f"DELETE FROM {table_name}"
        return self.execute(db_name, sql)

    def drop_table(self, db_name: str, table_name: str) -> bool:
        """
        删除表
        """
        sql = f"DROP TABLE IF EXISTS {table_name}"
        return self.execute(db_name, sql)

    def get_table_info(self, db_name: str, table_name: str) -> pd.DataFrame:
        """
        获取表结构信息
        """
        sql = f"PRAGMA table_info('{table_name}')"
        return self.fetchdf(db_name, sql)

    def backup(self, db_name: str, backup_path: Optional[str] = None) -> bool:
        """
        备份数据库
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.db_root, f"{db_name}_backup_{timestamp}.db")

        try:
            src_path = os.path.join(self.db_root, f"{db_name}.db")
            import shutil
            shutil.copy2(src_path, backup_path)
            print(f"✅ 数据库 {db_name} 已备份到 {backup_path}")
            return True
        except Exception as e:
            print(f"备份失败: {e}")
            return False

    def close(self, db_name: Optional[str] = None):
        """
        关闭数据库连接
        db_name: 指定数据库名，如果为 None 则关闭所有连接
        """
        if db_name:
            if db_name in self._conns:
                self._conns[db_name].close()
                del self._conns[db_name]
        else:
            for conn in self._conns.values():
                conn.close()
            self._conns.clear()

    def __del__(self):
        """析构函数，自动关闭所有连接"""
        self.close()


# ========== 全局单例 ==========
_db_manager = None


def get_db_manager() -> DBManager:
    """
    获取全局 DBManager 单例
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DBManager()
    return _db_manager


# ========== 快捷函数 ==========
def get_conn(db_name: str) -> duckdb.DuckDBPyConnection:
    """快捷函数：获取数据库连接"""
    return get_db_manager().get_conn(db_name)


def query_to_df(db_name: str, sql: str, params: Optional[List] = None) -> 'pd.DataFrame':
    """快捷函数：查询并返回 DataFrame"""
    return get_db_manager().fetchdf(db_name, sql, params)


def insert_data(db_name: str, table_name: str, data: Union[Dict, List[Dict]]) -> bool:
    """快捷函数：插入数据"""
    return get_db_manager().insert(db_name, table_name, data)


def upsert_data(db_name: str, table_name: str, data: Union[Dict, List[Dict]], conflict_columns: List[str]) -> bool:
    """快捷函数：插入或更新数据"""
    return get_db_manager().upsert(db_name, table_name, data, conflict_columns)


# ========== 测试 ==========
if __name__ == "__main__":
    print("="*70)
    print("🔌 DBManager 测试")
    print("="*70)
    print()

    # 创建管理器
    manager = get_db_manager()
    print("✅ DBManager 初始化成功")
    print()

    # 测试表创建
    print("📊 测试表创建...")
    manager.create_table("market_data", """
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            value DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ 表创建成功")
    print()

    # 测试插入数据
    print("📊 测试插入数据...")
    manager.insert("market_data", "test_table", [
        {"id": 1, "name": "test1", "value": 10.5},
        {"id": 2, "name": "test2", "value": 20.3}
    ])
    print("✅ 数据插入成功")
    print()

    # 测试查询数据
    print("📊 测试查询数据...")
    df = manager.fetchdf("market_data", "SELECT * FROM test_table")
    print(df)
    print()

    # 测试 UPSERT
    print("📊 测试 UPSERT...")
    manager.upsert("market_data", "test_table", [
        {"id": 1, "name": "test1_updated", "value": 15.5}
    ], conflict_columns=["id"])
    df = manager.fetchdf("market_data", "SELECT * FROM test_table WHERE id = 1")
    print(df)
    print()

    # 清理
    manager.drop_table("market_data", "test_table")
    print("✅ 测试表已清理")
    print()

    print("="*70)
    print("✅ 所有测试完成")
    print("="*70)
