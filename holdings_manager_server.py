#!/usr/bin/env python3
"""
holdings_manager.py - 持仓数据持久化管理器（DuckDB 版本）
解决记不住、更新乱的问题

功能：
- 从用户提供的表格数据中解析持仓
- 将持仓数据保存到 DuckDB 数据库
- 支持增量更新（新增、修改、清仓删除）
- 记录操作历史（包括 T 操作、买入卖出）
- 提供查询接口（当前持仓、历史清仓股、关注池等）

作者：魔力宝贝
日期：2026-04-03
版本：v2.0（DuckDB 版本）
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

# 添加工作目录到 Python 路径
sys.path.insert(0, '/root/.openclaw/workspace')

from agent_army.db_manager import get_db_manager


class HoldingsManager:
    """持仓数据持久化管理器（DuckDB 版本）"""

    def __init__(self):
        """初始化持仓管理器"""
        self.manager = get_db_manager()

    def _load_holdings(self) -> Dict:
        """从数据库加载持仓数据

        Returns:
            当前持仓字典（代码 -> 信息）
        """
        df = self.manager.fetchdf("holdings", "SELECT * FROM current_holdings")

        if df.empty:
            return {}

        # 转换为字典格式
        holdings = {}
        for _, row in df.iterrows():
            code = row['code']
            holdings[code] = {
                'code': code,
                'name': row['name'],
                'shares': int(row['shares']),
                'available': int(row['available']),
                'cost_price': float(row['cost_price']),
                'current_price': float(row['current_price']),
                'profit_loss': float(row['profit_loss']),
                'profit_loss_pct': float(row['profit_loss_pct']),
                'market_value': float(row['market_value']),
                'position_pct': float(row['position_pct']),
                'holding_days': int(row['holding_days']),
                'last_update': str(row['last_update'])
            }

        return holdings

    def update_from_table(self, table_text: str) -> Dict:
        """从用户提供的表格文本更新持仓

        Args:
            table_text: 表格文本（制表符分隔）

        Returns:
            更新结果字典

        表格格式示例：
        证券代码  证券名称  持仓数量  可用数量  冻结数量  参考成本价  当前价  浮动盈亏  盈亏比例(%)  ...
        """
        lines = table_text.strip().split('\n')
        if len(lines) < 2:
            return {"error": "表格数据不足"}

        headers = lines[0].split('\t')

        # 必需字段映射
        required = {
            '证券代码': 'code',
            '证券名称': 'name',
            '持仓数量': 'shares',
            '可用数量': 'available',
            '参考成本价': 'cost_price',
            '当前价': 'current_price',
            '浮动盈亏': 'profit_loss',
            '盈亏比例(%)': 'profit_loss_pct',
            '最新市值': 'market_value',
            '仓位占比(%)': 'position_pct',
            '持股天数': 'holding_days'
        }

        col_map = {}
        for i, h in enumerate(headers):
            if h in required:
                col_map[required[h]] = i

        current_holdings = self._load_holdings()
        new_holdings = {}
        timestamp = datetime.now()
        t_trade_count = 0
        position_change_count = 0
        cleared_count = 0

        for line in lines[1:]:
            if not line.strip():
                continue

            cells = line.split('\t')
            if len(cells) < len(headers):
                continue

            code = cells[col_map['code']]
            shares = int(float(cells[col_map['shares']]))

            # 检查是否清仓
            if shares == 0:
                # 清仓：记录到历史
                if code in current_holdings:
                    # 插入清仓记录到 operations 表
                    op_date = timestamp.date()
                    self.manager.execute("holdings", "INSERT INTO cleared_holdings (code, name, cleared_date, shares, cost_price, final_price, profit_loss, profit_loss_pct, holding_days, trade_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
                        code,
                        current_holdings[code]['name'],
                        op_date,
                        current_holdings[code]['shares'],
                        current_holdings[code]['cost_price'],
                        float(cells[col_map['current_price']]),
                        float(cells[col_map['profit_loss']]),
                        float(cells[col_map['profit_loss_pct']]),
                        int(cells[col_map['holding_days']]),
                        1  # trade_count
                    ])

                    # 从 current_holdings 删除
                    self.manager.execute("holdings", f"DELETE FROM current_holdings WHERE code = '{code}'")
                    cleared_count += 1
                continue

            # 更新持仓
            new_holdings[code] = {
                'code': code,
                'name': cells[col_map['name']],
                'shares': shares,
                'available': int(cells[col_map['available']]),
                'cost_price': float(cells[col_map['cost_price']]),
                'current_price': float(cells[col_map['current_price']]),
                'profit_loss': float(cells[col_map['profit_loss']]),
                'profit_loss_pct': float(cells[col_map['profit_loss_pct']]),
                'market_value': float(cells[col_map['market_value']]),
                'position_pct': float(cells[col_map['position_pct']]),
                'holding_days': int(cells[col_map['holding_days']]),
                'last_update': timestamp
            }

            # 检查是否有T操作：对比上次持仓数量变化但成本价变化小
            if code in current_holdings:
                old_shares = current_holdings[code]['shares']
                if old_shares != shares:
                    cost_diff = abs(new_holdings[code]['cost_price'] - current_holdings[code]['cost_price'])
                    if cost_diff < 0.01:
                        # T操作（成本价几乎不变）
                        op_type = 't_sell' if shares < old_shares else 't_buy'
                        self._add_operation(code, op_date=timestamp.date(), op_type=op_type,
                                          shares=abs(shares - old_shares), price=new_holdings[code]['cost_price'],
                                          cost_after=new_holdings[code]['cost_price'], notes='T操作')
                        t_trade_count += 1
                    else:
                        # 持仓变化（可能是加仓或减仓）
                        op_type = 'sell' if shares < old_shares else 'buy'
                        self._add_operation(code, op_date=timestamp.date(), op_type=op_type,
                                          shares=abs(shares - old_shares), price=new_holdings[code]['cost_price'],
                                          cost_after=new_holdings[code]['cost_price'], notes='仓位变化')
                        position_change_count += 1
            else:
                # 新买入的股票
                self._add_operation(code, op_date=timestamp.date(), op_type='buy',
                                  shares=shares, price=new_holdings[code]['cost_price'],
                                  cost_after=new_holdings[code]['cost_price'], notes='新买入')

        # 写入数据库
        # 获取当前最大 ID
        max_id_result = self.manager.fetchdf("holdings", "SELECT MAX(id) as max_id FROM current_holdings")
        if not max_id_result.empty and not pd.isna(max_id_result['max_id'].iloc[0]):
            max_id = int(max_id_result['max_id'].iloc[0])
        else:
            max_id = 0

        for code, holding in new_holdings.items():
            # 先删除旧记录
            self.manager.execute("holdings", f"DELETE FROM current_holdings WHERE code = '{code}'")

            # 插入新记录
            max_id += 1
            self.manager.execute("holdings", """
                INSERT INTO current_holdings (id, code, name, shares, available, cost_price, current_price,
                                             profit_loss, profit_loss_pct, market_value, position_pct,
                                             holding_days, last_update)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                int(max_id),
                holding['code'],
                holding['name'],
                holding['shares'],
                holding['available'],
                holding['cost_price'],
                holding['current_price'],
                holding['profit_loss'],
                holding['profit_loss_pct'],
                holding['market_value'],
                holding['position_pct'],
                holding['holding_days'],
                timestamp
            ])

        return {
            "status": "updated",
            "holdings_count": len(new_holdings),
            "cleared": cleared_count,
            "t_trades": t_trade_count,
            "position_changes": position_change_count
        }

    def _add_operation(self, code: str, op_date, op_type: str, shares: int, price: float, cost_after: float, notes: str = ''):
        """添加操作记录

        Args:
            code: 股票代码
            op_date: 操作日期
            op_type: 操作类型（buy, sell, t_buy, t_sell）
            shares: 数量
            price: 价格
            cost_after: 操作后成本
            notes: 备注
        """
        # 获取当前最大 ID
        max_id_result = self.manager.fetchdf("holdings", "SELECT MAX(id) as max_id FROM operations")
        if not max_id_result.empty and not pd.isna(max_id_result['max_id'].iloc[0]):
            max_id = int(max_id_result['max_id'].iloc[0])
        else:
            max_id = 0
        max_id += 1

        self.manager.execute("holdings", """
            INSERT INTO operations (id, code, op_date, op_type, shares, price, cost_after, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [int(max_id), code, op_date, op_type, shares, price, cost_after, notes])

    def get_current_holdings(self) -> Dict:
        """获取当前持仓（供分析使用）

        Returns:
            当前持仓字典
        """
        return self._load_holdings()

    def get_current_holdings_df(self) -> pd.DataFrame:
        """获取当前持仓（DataFrame 格式）

        Returns:
            当前持仓 DataFrame
        """
        return self.manager.fetchdf("holdings", "SELECT * FROM current_holdings")

    def get_cleared_stocks(self, days: int = 30) -> List:
        """获取近期清仓的股票（默认30天内）

        Args:
            days: 天数

        Returns:
            清仓股票代码列表
        """
        cutoff_date = datetime.now().date() - pd.Timedelta(days=days)
        df = self.manager.fetchdf(
            "holdings",
            f"SELECT DISTINCT code FROM cleared_holdings WHERE cleared_date >= '{cutoff_date}'"
        )

        if df.empty:
            return []

        return df['code'].tolist()

    def add_to_watchlist(self, code: str, name: Optional[str] = None, reason: str = ''):
        """添加股票到关注池

        Args:
            code: 股票代码
            name: 股票名称（可选）
            reason: 关注原因（可选）
        """
        # 检查是否已存在
        df = self.manager.fetchdf("holdings", f"SELECT * FROM watchlist WHERE stock_code = '{code}'")

        if df.empty:
            # Get max id
            max_id_df = self.manager.fetchdf("holdings", "SELECT MAX(id) as max_id FROM watchlist")
            max_id = int(max_id_df['max_id'].iloc[0]) if not max_id_df.empty and not pd.isna(max_id_df['max_id'].iloc[0]) else 0
            max_id += 1
            self.manager.execute("holdings", """
                INSERT INTO watchlist (id, stock_code, stock_name, added_date, reason)
                VALUES (?, ?, ?, ?, ?)
            """, [int(max_id), code, name or '', datetime.now().date(), reason])

    def remove_from_watchlist(self, code: str):
        """从关注池中删除股票

        Args:
            code: 股票代码
        """
        self.manager.execute("holdings", f"DELETE FROM watchlist WHERE stock_code = '{code}'")

    def get_watchlist(self) -> List:
        """获取关注池

        Returns:
            关注池列表
        """
        df = self.manager.fetchdf("holdings", "SELECT * FROM watchlist")

        if df.empty:
            return []

        watchlist = []
        for _, row in df.iterrows():
            watchlist.append({
                'code': row['stock_code'],
                'name': row['stock_name'],
                'added': str(row['added_date']),
                'reason': row['reason']
            })

        return watchlist

    def get_watchlist_df(self) -> pd.DataFrame:
        """获取关注池（DataFrame 格式）

        Returns:
            关注池 DataFrame
        """
        return self.manager.fetchdf("holdings", "SELECT * FROM watchlist")

    def get_operations(self, code: Optional[str] = None, days: int = 30) -> pd.DataFrame:
        """获取操作记录

        Args:
            code: 股票代码（可选）
            days: 天数

        Returns:
            操作记录 DataFrame
        """
        cutoff_date = datetime.now().date() - pd.Timedelta(days=days)

        if code:
            sql = f"""
                SELECT * FROM operations
                WHERE code = '{code}' AND op_date >= '{cutoff_date}'
                ORDER BY op_date DESC
            """
        else:
            sql = f"""
                SELECT * FROM operations
                WHERE op_date >= '{cutoff_date}'
                ORDER BY op_date DESC
            """

        return self.manager.fetchdf("holdings", sql)

    def get_summary(self) -> Dict:
        """获取持仓摘要

        Returns:
            持仓摘要字典
        """
        holdings = self._load_holdings()

        # 计算总市值
        total_market_value = sum(h.get('market_value', 0) for h in holdings.values())

        # 计算总盈亏
        total_profit_loss = sum(h.get('profit_loss', 0) for h in holdings.values())

        # 获取最近的T操作
        cutoff_date = datetime.now().date() - pd.Timedelta(days=7)
        df = self.manager.fetchdf(
            "holdings",
            f"SELECT COUNT(*) as count FROM operations WHERE op_type IN ('t_buy', 't_sell') AND op_date >= '{cutoff_date}'"
        )

        recent_t_trades = int(df['count'].iloc[0]) if not df.empty else 0

        return {
            "holdings_count": len(holdings),
            "total_market_value": total_market_value,
            "total_profit_loss": total_profit_loss,
            "recent_t_trades": recent_t_trades,
            "last_update": datetime.now().isoformat()
        }


# 单例模式
_manager = None


def get_holdings_manager() -> HoldingsManager:
    """获取持仓管理器单例

    Returns:
        HoldingsManager实例
    """
    global _manager
    if _manager is None:
        _manager = HoldingsManager()
    return _manager


# 使用示例
if __name__ == "__main__":
    # 测试持仓管理器
    manager = get_holdings_manager()

    # 测试数据
    table_text = """证券代码	证券名称	持仓数量	可用数量	冻结数量	参考成本价	当前价	浮动盈亏	盈亏比例(%)	最新市值	仓位占比(%)	持股天数
000725	京东方A	4900	4900	0	3.929	3.95	+103.90	+0.54	19355.00	9.88	2
600887	伊利股份	1100	1100	0	26.400	26.43	+33.00	+0.12	29073.00	14.95	3
600893	航发动力	2500	1500	1000	48.533	49.80	+3167.50	+2.58	124500.00	61.99	5"""

    # 更新持仓
    result = manager.update_from_table(table_text)
    print("更新结果：")
    for key, value in result.items():
        print(f"  {key}: {value}")

    # 获取当前持仓
    holdings = manager.get_current_holdings()
    print(f"\n当前持仓（{len(holdings)}只）：")
    for code, info in holdings.items():
        print(f"  {code} {info['name']}: {info['shares']}股, 成本{info['cost_price']}")

    # 获取摘要
    summary = manager.get_summary()
    print(f"\n持仓摘要：")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # 获取操作记录
    print(f"\n操作记录：")
    ops = manager.get_operations(days=7)
    print(ops.to_string(index=False))
