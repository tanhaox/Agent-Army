#!/usr/bin/env python3
"""
holdings_manager.py - 持仓数据持久化管理器（DuckDB 版本 v3.0）

功能：
- 从用户提供的表格数据中解析持仓（支持全部16个字段）
- 将持仓数据保存到 DuckDB 数据库
- 更新前自动归档到 holdings_history
- 支持增量更新（新增、修改、清仓删除）
- 记录操作历史（包括 T 操作、买入卖出）
- 跟踪总资产和现金余额（基于 initial_capital）
- 提供查询接口（当前持仓、历史清仓股、关注池等）

作者：魔力宝贝
日期：2026-04-12
版本：v3.0（完整字段 + 资金跟踪 + 历史归档）
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
    """持仓数据持久化管理器（DuckDB 版本 v3.0）"""

    def __init__(self):
        """初始化持仓管理器"""
        self.manager = get_db_manager()

    def _get_config(self, key: str, default=None):
        """获取全局配置值"""
        try:
            df = self.manager.fetchdf("holdings", f"SELECT value FROM global_config WHERE key = '{key}'")
            if not df.empty:
                return float(df['value'].iloc[0])
        except Exception:
            pass
        return default

    @property
    def initial_capital(self) -> float:
        """获取初始资金（固定值，从 global_config 读取）"""
        return self._get_config('initial_capital', 200000.0)

    def _get_total_holdings_cost(self) -> float:
        """计算当前持仓的总成本（买入总金额）

        持仓成本 = Σ (成本价 × 持仓数量)

        Returns:
            总持仓成本
        """
        df = self.manager.fetchdf("holdings", "SELECT shares, cost_price FROM current_holdings")
        if df.empty:
            return 0.0
        return float((df['shares'] * df['cost_price']).sum())

    def _get_total_market_value(self) -> float:
        """计算当前持仓的总市值

        Returns:
            总市值
        """
        df = self.manager.fetchdf("holdings", "SELECT market_value FROM current_holdings")
        if df.empty:
            return 0.0
        return float(df['market_value'].sum())

    def _get_total_realized_pnl(self) -> float:
        """计算累计清仓盈亏（从 cleared_holdings 表）

        累计已实现盈亏 = Σ profit_loss (所有清仓记录)

        Returns:
            累计已实现盈亏金额
        """
        df = self.manager.fetchdf("holdings", "SELECT profit_loss FROM cleared_holdings WHERE profit_loss IS NOT NULL")
        if df.empty:
            return 0.0
        return float(df['profit_loss'].sum())

    def _calc_cash_balance(self) -> float:
        """动态计算流动资金（不存储，每次计算）

        流动资金 = 初始资金 - 持仓成本 + 累计清仓盈亏

        Returns:
            当前流动资金
        """
        initial = self.initial_capital
        total_cost = self._get_total_holdings_cost()
        realized_pnl = self._get_total_realized_pnl()
        return initial - total_cost + realized_pnl

    def _calc_total_assets(self) -> tuple:
        """动态计算总资产及各项指标（不存储，每次计算）

        总资产 = 持仓市值 + 流动资金
        总盈亏 = (持仓市值 - 持仓成本) + 累计清仓盈亏

        Returns:
            (total_market_value, cash_balance, total_assets, total_pnl, total_cost, realized_pnl)
        """
        total_mv = self._get_total_market_value()
        total_cost = self._get_total_holdings_cost()
        realized_pnl = self._get_total_realized_pnl()
        cash = self.initial_capital - total_cost + realized_pnl
        total_assets = total_mv + cash
        # 浮动盈亏 = 市值 - 成本, 总盈亏 = 浮动盈亏 + 已实现盈亏
        total_pnl = (total_mv - total_cost) + realized_pnl
        return total_mv, cash, total_assets, total_pnl, total_cost, realized_pnl

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
                'frozen_shares': int(row.get('frozen_shares', 0)),
                'cost_price': float(row['cost_price']),
                'current_price': float(row['current_price']),
                'profit_loss': float(row['profit_loss']),
                'profit_loss_pct': float(row['profit_loss_pct']),
                'daily_profit_loss': float(row.get('daily_profit_loss', 0)),
                'daily_profit_loss_pct': float(row.get('daily_profit_loss_pct', 0)),
                'market_value': float(row['market_value']),
                'position_pct': float(row['position_pct']),
                'holding_days': int(row['holding_days']),
                'buy_today': int(row.get('buy_today', 0)),
                'sell_today': int(row.get('sell_today', 0)),
                'market': str(row.get('market', '')),
                'last_update': str(row['last_update'])
            }

        return holdings

    def _archive_holdings(self, source: str = 'user_update'):
        """将当前持仓归档到 holdings_history

        Args:
            source: 归档来源（user_update / auto_sync）
        """
        # 检查是否有当前持仓
        df = self.manager.fetchdf("holdings", "SELECT * FROM current_holdings")
        if df.empty:
            return

        # 获取 holdings_history 最大 ID
        max_id_result = self.manager.fetchdf("holdings", "SELECT MAX(id) as max_id FROM holdings_history")
        if not max_id_result.empty and not pd.isna(max_id_result['max_id'].iloc[0]):
            max_id = int(max_id_result['max_id'].iloc[0])
        else:
            max_id = 0

        snapshot_date = datetime.now().date()

        for _, row in df.iterrows():
            max_id += 1
            # holdings_history 使用 stock_code/stock_name（与 current_holdings 的 code/name 不同）
            self.manager.execute("holdings", """
                INSERT INTO holdings_history (
                    id, timestamp, stock_code, stock_name, action,
                    shares, price, amount, cost_price, reason,
                    created_at, frozen_shares, daily_profit_loss, daily_profit_loss_pct,
                    buy_today, sell_today, market, source, archived_at
                ) VALUES (?, now(), ?, ?, 'snapshot', ?, ?, ?, ?, '持仓归档', now(), ?, ?, ?, ?, ?, ?, ?, now())
            """, [
                int(max_id),
                row['code'],
                row['name'],
                int(row['shares']),
                float(row['current_price']),
                float(row['market_value']),
                float(row['cost_price']),
                int(row.get('frozen_shares', 0)),
                float(row.get('daily_profit_loss', 0)),
                float(row.get('daily_profit_loss_pct', 0)),
                int(row.get('buy_today', 0)),
                int(row.get('sell_today', 0)),
                str(row.get('market', '')),
                source
            ])

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

        # 必需字段映射（完整16个字段）
        required = {
            '证券代码': 'code',
            '证券名称': 'name',
            '持仓数量': 'shares',
            '可用数量': 'available',
            '冻结数量': 'frozen_shares',
            '参考成本价': 'cost_price',
            '当前价': 'current_price',
            '浮动盈亏': 'profit_loss',
            '盈亏比例(%)': 'profit_loss_pct',
            '最新市值': 'market_value',
            '仓位占比(%)': 'position_pct',
            '持股天数': 'holding_days',
        }

        # 可选字段（可能不存在于表格中）
        optional = {
            '当日盈亏': 'daily_profit_loss',
            '当日盈亏比例(%)': 'daily_profit_loss_pct',
            '当日买入': 'buy_today',
            '当日卖出': 'sell_today',
            '市场': 'market',
        }

        col_map = {}
        for i, h in enumerate(headers):
            h_stripped = h.strip()
            if h_stripped in required:
                col_map[required[h_stripped]] = i
            elif h_stripped in optional:
                col_map[optional[h_stripped]] = i

        # 安全读取单元格值
        def safe_float(cells, key, default=0.0):
            if key in col_map and col_map[key] < len(cells):
                try:
                    val = cells[col_map[key]].strip().replace('+', '').replace(',', '')
                    return float(val) if val else default
                except (ValueError, IndexError):
                    return default
            return default

        def safe_int(cells, key, default=0):
            if key in col_map and col_map[key] < len(cells):
                try:
                    val = cells[col_map[key]].strip().replace('+', '').replace(',', '')
                    return int(float(val)) if val else default
                except (ValueError, IndexError):
                    return default
            return default

        def safe_str(cells, key, default=''):
            if key in col_map and col_map[key] < len(cells):
                return cells[col_map[key]].strip()
            return default

        current_holdings = self._load_holdings()

        # 归档当前持仓到 holdings_history（更新前先归档）
        self._archive_holdings(source='user_update')

        new_holdings = {}
        timestamp = datetime.now()
        t_trade_count = 0
        position_change_count = 0
        cleared_count = 0
        explicitly_cleared = set()  # 记录显式清仓(shares=0)的股票代码

        for line in lines[1:]:
            if not line.strip():
                continue

            cells = line.split('\t')
            if len(cells) < len(headers):
                continue

            code = safe_str(cells, 'code')
            if not code:
                continue

            # 标准化代码格式（补全后缀）
            code = self._normalize_code(code)

            shares = safe_int(cells, 'shares')

            # 检查是否清仓
            if shares == 0:
                if code in current_holdings:
                    op_date = timestamp.date()
                    cleared_id = self._next_id('cleared_holdings')
                    self.manager.execute("holdings", """
                        INSERT INTO cleared_holdings (id, code, name, cleared_date, shares, cost_price, final_price,
                                                       profit_loss, profit_loss_pct, holding_days, trade_count,
                                                       created_at, clear_reason, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now(), '用户清仓', 'user_update')
                    """, [
                        cleared_id,
                        code,
                        current_holdings[code]['name'],
                        op_date,
                        current_holdings[code]['shares'],
                        current_holdings[code]['cost_price'],
                        safe_float(cells, 'current_price'),
                        safe_float(cells, 'profit_loss'),
                        safe_float(cells, 'profit_loss_pct'),
                        safe_int(cells, 'holding_days'),
                        1
                    ])

                    # 从 current_holdings 删除
                    self.manager.execute("holdings", f"DELETE FROM current_holdings WHERE code = '{code}'")
                    explicitly_cleared.add(code)
                    cleared_count += 1
                continue

            # 更新持仓
            new_holdings[code] = {
                'code': code,
                'name': safe_str(cells, 'name'),
                'shares': shares,
                'available': safe_int(cells, 'available'),
                'frozen_shares': safe_int(cells, 'frozen_shares'),
                'cost_price': safe_float(cells, 'cost_price'),
                'current_price': safe_float(cells, 'current_price'),
                'profit_loss': safe_float(cells, 'profit_loss'),
                'profit_loss_pct': safe_float(cells, 'profit_loss_pct'),
                'daily_profit_loss': safe_float(cells, 'daily_profit_loss'),
                'daily_profit_loss_pct': safe_float(cells, 'daily_profit_loss_pct'),
                'market_value': safe_float(cells, 'market_value'),
                'position_pct': safe_float(cells, 'position_pct'),
                'holding_days': safe_int(cells, 'holding_days'),
                'buy_today': safe_int(cells, 'buy_today'),
                'sell_today': safe_int(cells, 'sell_today'),
                'market': safe_str(cells, 'market'),
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
        max_id_result = self.manager.fetchdf("holdings", "SELECT MAX(id) as max_id FROM current_holdings")
        if not max_id_result.empty and not pd.isna(max_id_result['max_id'].iloc[0]):
            max_id = int(max_id_result['max_id'].iloc[0])
        else:
            max_id = 0

        for code, holding in new_holdings.items():
            # 先删除旧记录
            self.manager.execute("holdings", f"DELETE FROM current_holdings WHERE code = '{code}'")

            # 插入新记录（完整16个字段）
            max_id += 1
            self.manager.execute("holdings", """
                INSERT INTO current_holdings (
                    id, code, name, shares, available, frozen_shares,
                    cost_price, current_price, profit_loss, profit_loss_pct,
                    daily_profit_loss, daily_profit_loss_pct,
                    market_value, position_pct, holding_days,
                    buy_today, sell_today, market, last_update
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                int(max_id),
                holding['code'],
                holding['name'],
                holding['shares'],
                holding['available'],
                holding['frozen_shares'],
                holding['cost_price'],
                holding['current_price'],
                holding['profit_loss'],
                holding['profit_loss_pct'],
                holding['daily_profit_loss'],
                holding['daily_profit_loss_pct'],
                holding['market_value'],
                holding['position_pct'],
                holding['holding_days'],
                holding['buy_today'],
                holding['sell_today'],
                holding['market'],
                timestamp
            ])

        # 处理表格中消失的股票（曾持仓但本次表格中无此股 = 清仓）
        # 排除已通过 shares=0 显式清仓的股票
        new_codes = set(new_holdings.keys())
        for old_code in list(current_holdings.keys()):
            if old_code in new_codes or old_code in explicitly_cleared:
                continue
            # 这只股票在旧持仓中但不在新表格中，视为清仓
            old_info = current_holdings[old_code]
            # 清仓盈亏 = (当前价 - 成本价) * 股数，使用最后记录的价格
            cleared_pnl = (old_info['current_price'] - old_info['cost_price']) * old_info['shares']
            cleared_pnl_pct = ((old_info['current_price'] / old_info['cost_price']) - 1) * 100 if old_info['cost_price'] > 0 else 0

            self.manager.execute("holdings", """
                INSERT INTO cleared_holdings (id, code, name, cleared_date, shares, cost_price, final_price,
                                               profit_loss, profit_loss_pct, holding_days, trade_count,
                                               created_at, clear_reason, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now(), '表格中消失自动清仓', 'auto_clear')
            """, [
                self._next_id('cleared_holdings'),
                old_code,
                old_info['name'],
                timestamp.date(),
                old_info['shares'],
                old_info['cost_price'],
                old_info['current_price'],
                round(cleared_pnl, 2),
                round(cleared_pnl_pct, 2),
                old_info['holding_days'],
                1
            ])

            # 从 current_holdings 删除
            self.manager.execute("holdings", f"DELETE FROM current_holdings WHERE code = '{old_code}'")
            cleared_count += 1

        # 使用新公式计算资金
        # 流动资金 = 初始资金 - 持仓成本 + 累计清仓盈亏
        total_mv, cash, total_assets, total_pnl, total_cost, realized_pnl = self._calc_total_assets()
        initial = self.initial_capital

        return {
            "status": "updated",
            "holdings_count": len(new_holdings),
            "cleared": cleared_count,
            "t_trades": t_trade_count,
            "position_changes": position_change_count,
            "initial_capital": round(initial, 2),
            "total_holdings_cost": round(total_cost, 2),
            "total_market_value": round(total_mv, 2),
            "realized_pnl": round(realized_pnl, 2),
            "cash_balance": round(cash, 2),
            "total_assets": round(total_assets, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl / initial * 100, 2) if initial > 0 else 0
        }

    def _normalize_code(self, code: str) -> str:
        """标准化股票代码格式

        将纯数字代码转换为带后缀的标准格式：
        - 6开头 -> .SH（上交所）
        - 0/3开头 -> .SZ（深交所）
        - 8/4开头 -> .BJ（北交所）
        """
        code = code.strip()
        # 如果已经有后缀，直接返回
        if '.' in code:
            return code
        # 纯数字，根据规则加后缀
        if code.startswith('6'):
            return code + '.SH'
        elif code.startswith('0') or code.startswith('3'):
            return code + '.SZ'
        elif code.startswith('8') or code.startswith('4'):
            return code + '.BJ'
        return code

    def _next_id(self, table: str) -> int:
        """获取指定表的下一个自增 ID

        Args:
            table: 表名

        Returns:
            下一个 ID 值
        """
        max_id_result = self.manager.fetchdf("holdings", f"SELECT MAX(id) as max_id FROM {table}")
        if not max_id_result.empty and not pd.isna(max_id_result['max_id'].iloc[0]):
            return int(max_id_result['max_id'].iloc[0]) + 1
        return 1

    def _add_operation(self, code: str, op_date, op_type: str, shares: int, price: float, cost_after: float, notes: str = ''):
        """添加操作记录"""
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
        """获取当前持仓（供分析使用）"""
        return self._load_holdings()

    def get_current_holdings_df(self) -> pd.DataFrame:
        """获取当前持仓（DataFrame 格式）"""
        return self.manager.fetchdf("holdings", "SELECT * FROM current_holdings")

    def get_cleared_stocks(self, days: int = 30) -> List:
        """获取近期清仓的股票（默认30天内）"""
        cutoff_date = datetime.now().date() - pd.Timedelta(days=days)
        df = self.manager.fetchdf(
            "holdings",
            f"SELECT DISTINCT code FROM cleared_holdings WHERE cleared_date >= '{cutoff_date}'"
        )

        if df.empty:
            return []

        return df['code'].tolist()

    def get_total_assets(self) -> Dict:
        """获取总资产信息（动态计算，不依赖存储）

        核心公式：
            流动资金 = 初始资金 - 持仓成本 + 累计清仓盈亏
            总资产 = 持仓市值 + 流动资金
            总盈亏 = (持仓市值 - 持仓成本) + 累计清仓盈亏

        Returns:
            总资产详情字典
        """
        total_mv, cash, total_assets, total_pnl, total_cost, realized_pnl = self._calc_total_assets()
        initial = self.initial_capital
        holdings_count_df = self.manager.fetchdf("holdings", "SELECT COUNT(*) as cnt FROM current_holdings")
        holdings_count = int(holdings_count_df['cnt'].iloc[0]) if not holdings_count_df.empty else 0

        # 浮动盈亏 = 市值 - 成本
        floating_pnl = total_mv - total_cost

        return {
            "initial_capital": round(initial, 2),
            "total_holdings_cost": round(total_cost, 2),
            "total_market_value": round(total_mv, 2),
            "cash_balance": round(cash, 2),
            "total_assets": round(total_assets, 2),
            "floating_pnl": round(floating_pnl, 2),
            "realized_pnl": round(realized_pnl, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl / initial * 100, 2) if initial > 0 else 0,
            "holdings_count": holdings_count,
            "position_ratio": round(total_mv / total_assets * 100, 2) if total_assets > 0 else 0
        }

    def add_to_watchlist(self, code: str, name: Optional[str] = None, reason: str = ''):
        """添加股票到关注池"""
        code = self._normalize_code(code)
        df = self.manager.fetchdf("holdings", f"SELECT * FROM watchlist WHERE stock_code = '{code}'")

        if df.empty:
            max_id_df = self.manager.fetchdf("holdings", "SELECT MAX(id) as max_id FROM watchlist")
            max_id = int(max_id_df['max_id'].iloc[0]) if not max_id_df.empty and not pd.isna(max_id_df['max_id'].iloc[0]) else 0
            max_id += 1
            self.manager.execute("holdings", """
                INSERT INTO watchlist (id, stock_code, stock_name, target_price, reason, added_date, priority)
                VALUES (?, ?, ?, 0, ?, ?, 0)
            """, [int(max_id), code, name or '', reason, datetime.now().date()])

    def remove_from_watchlist(self, code: str):
        """从关注池中删除股票"""
        code = self._normalize_code(code)
        self.manager.execute("holdings", f"DELETE FROM watchlist WHERE stock_code = '{code}'")

    def get_watchlist(self) -> List:
        """获取关注池"""
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
        """获取关注池（DataFrame 格式）"""
        return self.manager.fetchdf("holdings", "SELECT * FROM watchlist")

    def get_operations(self, code: Optional[str] = None, days: int = 30) -> pd.DataFrame:
        """获取操作记录"""
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
        """获取持仓摘要（动态计算资金）"""
        holdings = self._load_holdings()
        total_market_value = sum(h.get('market_value', 0) for h in holdings.values())
        total_profit_loss = sum(h.get('profit_loss', 0) for h in holdings.values())

        # 获取最近的T操作
        cutoff_date = datetime.now().date() - pd.Timedelta(days=7)
        df = self.manager.fetchdf(
            "holdings",
            f"SELECT COUNT(*) as count FROM operations WHERE op_type IN ('t_buy', 't_sell') AND op_date >= '{cutoff_date}'"
        )

        recent_t_trades = int(df['count'].iloc[0]) if not df.empty else 0

        # 动态计算总资产
        assets = self.get_total_assets()

        return {
            "holdings_count": len(holdings),
            "total_market_value": round(total_market_value, 2),
            "floating_pnl": round(total_profit_loss, 2),
            "recent_t_trades": recent_t_trades,
            "initial_capital": assets['initial_capital'],
            "total_holdings_cost": assets['total_holdings_cost'],
            "cash_balance": assets['cash_balance'],
            "total_assets": assets['total_assets'],
            "realized_pnl": assets['realized_pnl'],
            "total_pnl": assets['total_pnl'],
            "total_pnl_pct": assets['total_pnl_pct'],
            "position_ratio": assets['position_ratio'],
            "last_update": datetime.now().isoformat()
        }

    def get_holdings_history(self, days: int = 30) -> pd.DataFrame:
        """获取持仓历史快照

        Args:
            days: 查询天数

        Returns:
            历史快照 DataFrame
        """
        cutoff_date = datetime.now().date() - pd.Timedelta(days=days)
        return self.manager.fetchdf(
            "holdings",
            f"SELECT * FROM holdings_history WHERE CAST(timestamp AS DATE) >= '{cutoff_date}' ORDER BY timestamp DESC, stock_code"
        )


# 单例模式
_manager = None


def get_holdings_manager() -> HoldingsManager:
    """获取持仓管理器单例"""
    global _manager
    if _manager is None:
        _manager = HoldingsManager()
    return _manager


# 使用示例
if __name__ == "__main__":
    manager = get_holdings_manager()

    # 获取总资产信息
    assets = manager.get_total_assets()
    print("=== 总资产概览 ===")
    for key, value in assets.items():
        print(f"  {key}: {value}")

    # 获取当前持仓
    holdings = manager.get_current_holdings()
    print(f"\n=== 当前持仓（{len(holdings)}只）===")
    for code, info in holdings.items():
        daily_pl = info.get('daily_profit_loss', 0)
        print(f"  {code} {info['name']}: {info['shares']}股, 成本{info['cost_price']}, "
              f"当前{info['current_price']}, 盈亏{info['profit_loss']}, "
              f"当日盈亏{daily_pl}")

    # 获取摘要
    summary = manager.get_summary()
    print(f"\n=== 持仓摘要 ===")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # 获取持仓历史
    print(f"\n=== 最近持仓历史 ===")
    history = manager.get_holdings_history(days=7)
    if not history.empty:
        print(history.to_string(index=False))
    else:
        print("  (暂无历史记录)")
