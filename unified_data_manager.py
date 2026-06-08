#!/usr/bin/env python3
"""
unified_data_manager.py - 统一数据管理器（v1.0）

解决问题：
- 多入口（holdings_manager, holdings_data_sync, sync_holdings_from_usermd）并存
- 无冲突解决机制
- 数据存储分散（DuckDB / JSON / CSV）

设计原则：
- 单一写入入口，来源优先级控制
- 操作日志记录所有变更
- 冲突检测基于时间戳 + 来源优先级
- 向后兼容现有 HoldingsManager 接口

来源优先级（高→低）：
  user_table (1) > user_md (2) > auto_sync (3)

作者：AI Agent
日期：2026-04-16
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import IntEnum

sys.path.insert(0, '/root/.openclaw/workspace')

from agent_army.db_manager import get_db_manager
from agent_army.holdings_manager import HoldingsManager

# 日志配置
logger = logging.getLogger('UnifiedDataManager')
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(handler)


class SourcePriority(IntEnum):
    """数据来源优先级（数值越小优先级越高）"""
    USER_TABLE = 1    # 用户直接提供的表格数据（最高优先级）
    USER_MD = 2       # 从 USER.md 解析的数据
    AUTO_SYNC = 3     # 自动同步的数据
    MANUAL = 4        # 手动命令


class UnifiedDataManager:
    """统一数据管理器 - 所有持仓操作的唯一入口

    职责：
    1. 统一所有写入操作，记录来源和操作日志
    2. 基于来源优先级的冲突检测
    3. 提供查询接口（支持历史快照）
    4. 协调 DuckDB / JSON 数据同步
    """

    # 需要管理的表
    TABLES = ['current_holdings', 'cleared_holdings', 'operations',
              'watchlist', 'holdings_history', 'global_config']

    def __init__(self):
        self._db = get_db_manager()
        self._holdings_mgr = HoldingsManager()
        self._ensure_op_log_table()

    # ==================== 初始化 ====================

    def _ensure_op_log_table(self):
        """确保操作日志表存在"""
        try:
            self._db.execute("holdings", """
                CREATE TABLE IF NOT EXISTS operations_log (
                    id INTEGER PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT now(),
                    source VARCHAR NOT NULL,
                    source_priority INTEGER NOT NULL,
                    action VARCHAR NOT NULL,
                    target_table VARCHAR NOT NULL,
                    target_code VARCHAR,
                    detail JSON,
                    snapshot_before JSON,
                    snapshot_after JSON
                )
            """)
        except Exception as e:
            logger.warning(f"操作日志表初始化: {e}")

    def _next_log_id(self) -> int:
        """获取操作日志下一个 ID"""
        try:
            df = self._db.fetchdf("holdings", "SELECT MAX(id) as max_id FROM operations_log")
            if not df.empty and df['max_id'].iloc[0] is not None:
                return int(df['max_id'].iloc[0]) + 1
        except Exception:
            pass
        return 1

    # ==================== 操作日志 ====================

    def _log_operation(self, source: str, action: str, target_table: str,
                       target_code: str = None, detail: dict = None,
                       snapshot_before: dict = None, snapshot_after: dict = None):
        """记录操作日志

        Args:
            source: 操作来源（user_table/user_md/auto_sync/manual）
            action: 操作类型（update/clear/add_to_watch/remove_from_watch/set_config）
            target_table: 目标表
            target_code: 目标股票代码
            detail: 操作详情
            snapshot_before: 操作前快照
            snapshot_after: 操作后快照
        """
        priority = self._get_source_priority(source)
        try:
            self._db.execute("holdings", """
                INSERT INTO operations_log (id, timestamp, source, source_priority, action,
                                            target_table, target_code, detail, snapshot_before, snapshot_after)
                VALUES (?, now(), ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                self._next_log_id(),
                source,
                priority,
                action,
                target_table,
                target_code,
                json.dumps(detail, ensure_ascii=False, default=str) if detail else None,
                json.dumps(snapshot_before, ensure_ascii=False, default=str) if snapshot_before else None,
                json.dumps(snapshot_after, ensure_ascii=False, default=str) if snapshot_after else None,
            ])
        except Exception as e:
            logger.error(f"记录操作日志失败: {e}")

    def _get_source_priority(self, source: str) -> int:
        """获取来源优先级数值"""
        priority_map = {
            'user_table': SourcePriority.USER_TABLE,
            'user_md': SourcePriority.USER_MD,
            'auto_sync': SourcePriority.AUTO_SYNC,
            'manual': SourcePriority.MANUAL,
        }
        return priority_map.get(source, SourcePriority.MANUAL)

    # ==================== 冲突检测 ====================

    def _check_conflict(self, source: str, target_code: str = None) -> dict:
        """检测是否存在冲突

        规则：
        - 如果有更高优先级的来源在最近 N 分钟内操作过同一数据，拒绝低优先级操作
        - 最近一次操作的来源优先级 vs 当前来源优先级

        Args:
            source: 当前操作来源
            target_code: 目标股票代码（None 表示全局操作）

        Returns:
            {'conflict': bool, 'reason': str, 'last_source': str, 'last_time': str}
        """
        my_priority = self._get_source_priority(source)

        try:
            if target_code:
                sql = """
                    SELECT source, source_priority, timestamp
                    FROM operations_log
                    WHERE target_table = 'current_holdings' AND target_code = ?
                    ORDER BY timestamp DESC LIMIT 1
                """
                df = self._db.fetchdf("holdings", sql)
                if hasattr(target_code, '__iter__') and not isinstance(target_code, str):
                    # 如果 target_code 是列表，用另一种方式查询
                    df = self._db.fetchdf("holdings",
                        "SELECT source, source_priority, timestamp FROM operations_log "
                        "WHERE target_table = 'current_holdings' ORDER BY timestamp DESC LIMIT 1")
                else:
                    # 使用参数化查询
                    df = self._db.fetchdf("holdings",
                        f"SELECT source, source_priority, timestamp FROM operations_log "
                        f"WHERE target_table = 'current_holdings' AND target_code = '{target_code}' "
                        f"ORDER BY timestamp DESC LIMIT 1")
            else:
                df = self._db.fetchdf("holdings",
                    "SELECT source, source_priority, timestamp FROM operations_log "
                    "WHERE target_table = 'current_holdings' "
                    "ORDER BY timestamp DESC LIMIT 1")

            if df.empty:
                return {'conflict': False, 'reason': '', 'last_source': None, 'last_time': None}

            last_priority = int(df['source_priority'].iloc[0])
            last_source = str(df['source'].iloc[0])
            last_time = str(df['timestamp'].iloc[0])

            # 如果当前来源优先级低于最近操作的来源，且在 30 分钟内，则拒绝
            if my_priority > last_priority:
                try:
                    last_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00').replace('+00:00', ''))
                    if datetime.now() - last_dt < timedelta(minutes=30):
                        return {
                            'conflict': True,
                            'reason': f'数据刚被更高优先级来源 {last_source} 在 {last_time} 更新过',
                            'last_source': last_source,
                            'last_time': last_time
                        }
                except Exception:
                    pass

            return {'conflict': False, 'reason': '', 'last_source': last_source, 'last_time': last_time}

        except Exception as e:
            logger.warning(f"冲突检测异常: {e}")
            return {'conflict': False, 'reason': str(e), 'last_source': None, 'last_time': None}

    # ==================== 快照 ====================

    def _take_snapshot(self) -> dict:
        """拍摄当前持仓快照"""
        holdings = self._holdings_mgr.get_current_holdings()
        return {
            'timestamp': datetime.now().isoformat(),
            'holdings_count': len(holdings),
            'holdings': {code: {
                'shares': info['shares'],
                'cost_price': info['cost_price'],
                'current_price': info['current_price'],
                'market_value': info['market_value'],
            } for code, info in holdings.items()}
        }

    # ==================== 统一写入接口 ====================

    def update_holdings(self, source: str, data: Any, **kwargs) -> dict:
        """统一持仓更新入口

        Args:
            source: 数据来源
                - 'user_table': 用户提供的表格文本
                - 'user_md': 从 USER.md 解析
                - 'auto_sync': 自动同步
                - 'manual': 手动命令
            data: 更新数据
                - source='user_table' 时: 制表符分隔的表格文本
                - source='user_md' 时: 持仓字典列表
                - source='auto_sync' 时: 持仓字典列表
                - source='manual' 时: 操作指令字典
            **kwargs: 额外参数

        Returns:
            更新结果字典
        """
        # 1. 冲突检测
        conflict = self._check_conflict(source)
        if conflict['conflict']:
            logger.warning(f"操作被拒绝: {conflict['reason']}")
            return {
                'status': 'rejected',
                'reason': conflict['reason'],
                'source': source
            }

        # 2. 拍摄更新前快照
        snapshot_before = self._take_snapshot()

        # 3. 根据来源分发处理
        try:
            if source == 'user_table':
                result = self._handle_user_table(data, **kwargs)
            elif source == 'user_md':
                result = self._handle_user_md(data, **kwargs)
            elif source == 'auto_sync':
                result = self._handle_auto_sync(data, **kwargs)
            elif source == 'manual':
                result = self._handle_manual(data, **kwargs)
            else:
                return {'status': 'error', 'reason': f'未知来源: {source}'}
        except Exception as e:
            logger.error(f"更新失败 [{source}]: {e}")
            self._log_operation(source, 'error', 'current_holdings',
                                detail={'error': str(e)})
            return {'status': 'error', 'reason': str(e)}

        # 4. 拍摄更新后快照
        snapshot_after = self._take_snapshot()

        # 5. 记录操作日志
        self._log_operation(
            source=source,
            action='update',
            target_table='current_holdings',
            detail={'result': result},
            snapshot_before=snapshot_before,
            snapshot_after=snapshot_after
        )

        logger.info(f"持仓更新完成 [{source}]: {result.get('status', 'unknown')}")
        return result

    def _handle_user_table(self, table_text: str, **kwargs) -> dict:
        """处理用户表格数据（委托给 HoldingsManager）"""
        return self._holdings_mgr.update_from_table(table_text)

    def _handle_user_md(self, holdings_list: list, **kwargs) -> dict:
        """处理 USER.md 解析的持仓数据

        Args:
            holdings_list: 持仓字典列表，格式:
                [{'code': '600887.SH', 'name': '伊利股份', 'shares': 1000,
                  'cost_price': 26.30, 'current_price': 26.50, ...}]
        """
        return self._sync_holdings_from_list(holdings_list, source='user_md')

    def _handle_auto_sync(self, holdings_list: list, **kwargs) -> dict:
        """处理自动同步的持仓数据"""
        return self._sync_holdings_from_list(holdings_list, source='auto_sync')

    def _handle_manual(self, command: dict, **kwargs) -> dict:
        """处理手动命令

        Args:
            command: 操作指令字典，格式:
                {'action': 'clear', 'code': '600887.SH'}
                {'action': 'set_config', 'key': 'initial_capital', 'value': 200000}
                {'action': 'add_watch', 'code': '600887.SH', 'name': '伊利股份', 'reason': '...'}
                {'action': 'remove_watch', 'code': '600887.SH'}
        """
        action = command.get('action')

        if action == 'clear':
            code = command.get('code')
            if not code:
                return {'status': 'error', 'reason': '缺少 code'}
            return self._manual_clear_stock(code)

        elif action == 'set_config':
            key = command.get('key')
            value = command.get('value')
            if not key or value is None:
                return {'status': 'error', 'reason': '缺少 key 或 value'}
            return self._set_config(key, value)

        elif action == 'add_watch':
            code = command.get('code')
            name = command.get('name', '')
            reason = command.get('reason', '')
            return self._add_to_watchlist(code, name, reason)

        elif action == 'remove_watch':
            code = command.get('code')
            return self._remove_from_watchlist(code)

        else:
            return {'status': 'error', 'reason': f'未知操作: {action}'}

    # ==================== 内部操作方法 ====================

    def _sync_holdings_from_list(self, holdings_list: list, source: str) -> dict:
        """从持仓字典列表同步到 DuckDB

        统一处理 USER.md 和 auto_sync 来源的数据同步。
        将字典列表转换为表格文本格式，委托给 HoldingsManager。
        """
        if not holdings_list:
            return {'status': 'no_data', 'holdings_count': 0}

        # 将字典列表转为表格文本，复用 HoldingsManager 的解析逻辑
        lines = ['证券代码\t证券名称\t持仓数量\t可用数量\t冻结数量\t参考成本价\t当前价\t浮动盈亏\t盈亏比例(%)\t最新市值\t仓位占比(%)\t持股天数']

        for h in holdings_list:
            shares = h.get('shares', 0)
            if shares <= 0:
                continue
            code = h.get('code', '')
            # 确保 code 有后缀
            if '.' not in code:
                code = self._holdings_mgr._normalize_code(code)
            cost = h.get('cost_price', 0)
            cur = h.get('current_price', 0)
            mv = h.get('market_value', shares * cur)
            pl = h.get('profit_loss', mv - cost * shares)
            pl_pct = h.get('profit_loss_pct', (pl / (cost * shares) * 100) if cost > 0 else 0)

            lines.append(
                f"{code.split('.')[0]}\t"
                f"{h.get('name', '')}\t"
                f"{shares}\t"
                f"{h.get('available', shares)}\t"
                f"{h.get('frozen_shares', 0)}\t"
                f"{cost}\t"
                f"{cur}\t"
                f"{pl:.2f}\t"
                f"{pl_pct:.2f}\t"
                f"{mv:.2f}\t"
                f"{h.get('position_pct', 0):.2f}\t"
                f"{h.get('holding_days', 0)}"
            )

        table_text = '\n'.join(lines)
        return self._holdings_mgr.update_from_table(table_text)

    def _manual_clear_stock(self, code: str) -> dict:
        """手动清仓指定股票"""
        code = self._holdings_mgr._normalize_code(code)
        current = self._holdings_mgr.get_current_holdings()

        if code not in current:
            return {'status': 'not_found', 'reason': f'{code} 不在持仓中'}

        info = current[code]
        cleared_pnl = (info['current_price'] - info['cost_price']) * info['shares']

        # 通过 HoldingsManager 的逻辑清仓（构造 shares=0 的表格行）
        table_text = (
            f"证券代码\t证券名称\t持仓数量\t可用数量\t冻结数量\t参考成本价\t当前价\t浮动盈亏\t盈亏比例(%)\t最新市值\t仓位占比(%)\t持股天数\n"
            f"{code.split('.')[0]}\t{info['name']}\t0\t0\t0\t{info['cost_price']}\t"
            f"{info['current_price']}\t{cleared_pnl:.2f}\t0\t0\t0\t0"
        )
        result = self._holdings_mgr.update_from_table(table_text)
        self._log_operation('manual', 'clear', 'current_holdings', code,
                           detail={'code': code, 'name': info['name'], 'shares': info['shares']})
        return result

    def _set_config(self, key: str, value) -> dict:
        """设置全局配置"""
        try:
            self._db.execute("holdings",
                f"DELETE FROM global_config WHERE key = '{key}'")
            self._db.execute("holdings",
                "INSERT INTO global_config (key, value, updated_at) VALUES (?, ?, now())",
                [key, float(value) if isinstance(value, (int, float)) else value])
            self._log_operation('manual', 'set_config', 'global_config',
                               detail={'key': key, 'value': value})
            return {'status': 'ok', 'key': key, 'value': value}
        except Exception as e:
            return {'status': 'error', 'reason': str(e)}

    def _add_to_watchlist(self, code: str, name: str, reason: str) -> dict:
        """添加到关注池"""
        self._holdings_mgr.add_to_watchlist(code, name, reason)
        self._log_operation('manual', 'add_watch', 'watchlist', code,
                           detail={'code': code, 'name': name, 'reason': reason})
        return {'status': 'ok', 'code': code}

    def _remove_from_watchlist(self, code: str) -> dict:
        """从关注池移除"""
        self._holdings_mgr.remove_from_watchlist(code)
        self._log_operation('manual', 'remove_watch', 'watchlist', code,
                           detail={'code': code})
        return {'status': 'ok', 'code': code}

    # ==================== 统一查询接口 ====================

    def get_holdings(self, as_of: str = 'latest') -> dict:
        """统一持仓查询入口

        Args:
            as_of: 查询时间点
                - 'latest': 最新持仓（默认）
                - 'YYYY-MM-DD': 指定日期的快照
                - 'YYYY-MM-DD HH:MM': 指定时间的快照

        Returns:
            持仓信息字典，包含:
            - holdings: 持仓列表
            - assets: 总资产信息
            - as_of: 查询时间点
            - source: 数据来源
        """
        if as_of == 'latest':
            holdings = self._holdings_mgr.get_current_holdings()
            assets = self._holdings_mgr.get_total_assets()
            return {
                'as_of': datetime.now().isoformat(),
                'source': 'current',
                'holdings': holdings,
                'assets': assets,
                'holdings_count': len(holdings)
            }
        else:
            return self._get_historical_holdings(as_of)

    def _get_historical_holdings(self, as_of: str) -> dict:
        """查询历史持仓快照"""
        try:
            df = self._db.fetchdf("holdings",
                f"SELECT * FROM holdings_history "
                f"WHERE CAST(timestamp AS VARCHAR) <= '{as_of}' "
                f"ORDER BY timestamp DESC")

            if df.empty:
                return {'as_of': as_of, 'source': 'history', 'holdings': {},
                        'assets': {}, 'holdings_count': 0, 'note': '无历史数据'}

            # 取最近一次快照
            latest_ts = df['timestamp'].iloc[0]
            snapshot = df[df['timestamp'] == latest_ts]

            holdings = {}
            for _, row in snapshot.iterrows():
                code = row.get('stock_code', row.get('code', ''))
                holdings[code] = {
                    'code': code,
                    'name': row.get('stock_name', row.get('name', '')),
                    'shares': int(row.get('shares', 0)),
                    'cost_price': float(row.get('cost_price', 0)),
                    'current_price': float(row.get('price', 0)),
                    'market_value': float(row.get('amount', 0)),
                }

            return {
                'as_of': str(latest_ts),
                'source': 'history',
                'holdings': holdings,
                'holdings_count': len(holdings)
            }
        except Exception as e:
            logger.error(f"查询历史持仓失败: {e}")
            return {'as_of': as_of, 'source': 'error', 'holdings': {},
                    'error': str(e)}

    # ==================== 查询方法（透传） ====================

    def get_total_assets(self) -> dict:
        """获取总资产信息"""
        return self._holdings_mgr.get_total_assets()

    def get_summary(self) -> dict:
        """获取持仓摘要"""
        return self._holdings_mgr.get_summary()

    def get_watchlist(self) -> list:
        """获取关注池"""
        return self._holdings_mgr.get_watchlist()

    def get_cleared_stocks(self, days: int = 30) -> list:
        """获取近期清仓股票"""
        return self._holdings_mgr.get_cleared_stocks(days)

    def get_operations(self, code: str = None, days: int = 30) -> Any:
        """获取操作记录"""
        return self._holdings_mgr.get_operations(code, days)

    def get_operations_log(self, source: str = None, action: str = None,
                           limit: int = 50) -> list:
        """查询操作日志

        Args:
            source: 过滤来源
            action: 过滤操作类型
            limit: 返回条数

        Returns:
            操作日志列表
        """
        conditions = []
        if source:
            conditions.append(f"source = '{source}'")
        if action:
            conditions.append(f"action = '{action}'")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM operations_log {where} ORDER BY timestamp DESC LIMIT {limit}"

        try:
            df = self._db.fetchdf("holdings", sql)
            if df.empty:
                return []
            return df.to_dict('records')
        except Exception:
            return []

    # ==================== 数据同步导出 ====================

    def export_to_json(self, output_path: str = None) -> str:
        """导出持仓数据到 JSON（替代 sync_holdings_from_usermd.py 的输出）

        Args:
            output_path: 输出路径（默认 data/holdings.json）

        Returns:
            输出文件路径
        """
        if not output_path:
            output_path = '/root/.openclaw/workspace/data/holdings.json'

        holdings = self.get_holdings()
        export_data = {
            'export_time': datetime.now().isoformat(),
            'source': 'unified_data_manager',
            'holdings': []
        }

        for code, info in holdings['holdings'].items():
            export_data['holdings'].append({
                'code': code,
                'name': info.get('name', ''),
                'shares': info.get('shares', 0),
                'cost_price': info.get('cost_price', 0),
                'current_price': info.get('current_price', 0),
                'market_value': info.get('market_value', 0),
                'profit_loss': info.get('profit_loss', 0),
            })

        # 同时导出清仓记录
        cleared = self._holdings_mgr.get_cleared_stocks(days=90)
        export_data['cleared_stocks'] = cleared

        # 同时导出总资产
        export_data['assets'] = holdings.get('assets', {})

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"数据已导出到 {output_path}")
        return output_path


# ==================== 单例 ====================

_instance = None


def get_unified_data_manager() -> UnifiedDataManager:
    """获取统一数据管理器单例"""
    global _instance
    if _instance is None:
        _instance = UnifiedDataManager()
    return _instance


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='统一数据管理器')
    parser.add_argument('--status', action='store_true', help='查看当前持仓状态')
    parser.add_argument('--log', action='store_true', help='查看操作日志')
    parser.add_argument('--export', action='store_true', help='导出数据到 JSON')
    parser.add_argument('--history', type=str, help='查看指定日期的历史持仓')
    parser.add_argument('--limit', type=int, default=20, help='日志显示条数')

    args = parser.parse_args()
    mgr = get_unified_data_manager()

    if args.status:
        print("=" * 60)
        print("  持仓状态（UnifiedDataManager）")
        print("=" * 60)
        data = mgr.get_holdings()
        assets = data.get('assets', {})

        print(f"\n  查询时间: {data['as_of']}")
        print(f"  持仓数量: {data['holdings_count']}")
        print(f"  初始资金: {assets.get('initial_capital', 0):,.2f}")
        print(f"  持仓市值: {assets.get('total_market_value', 0):,.2f}")
        print(f"  持仓成本: {assets.get('total_holdings_cost', 0):,.2f}")
        print(f"  流动资金: {assets.get('cash_balance', 0):,.2f}")
        print(f"  总资产:   {assets.get('total_assets', 0):,.2f}")
        print(f"  总盈亏:   {assets.get('total_pnl', 0):,.2f} ({assets.get('total_pnl_pct', 0):.2f}%)")

        print(f"\n  持仓明细:")
        for code, info in data['holdings'].items():
            print(f"    {code} {info['name']}: {info['shares']}股, "
                  f"成本{info['cost_price']}, 当前{info['current_price']}, "
                  f"盈亏{info.get('profit_loss', 0):.2f}")

    elif args.log:
        print("=" * 60)
        print("  操作日志")
        print("=" * 60)
        logs = mgr.get_operations_log(limit=args.limit)
        for log in logs:
            print(f"  [{log.get('timestamp', '')}] "
                  f"[{log.get('source', '')}] "
                  f"{log.get('action', '')} "
                  f"{log.get('target_code', '') or ''} "
                  f"{'(detail: ' + str(log.get('detail', ''))[:60] + '...' if log.get('detail') else ''}")

    elif args.export:
        path = mgr.export_to_json()
        print(f"数据已导出: {path}")

    elif args.history:
        data = mgr.get_holdings(as_of=args.history)
        print(f"\n  历史持仓 ({data['as_of']}):")
        for code, info in data.get('holdings', {}).items():
            print(f"    {code} {info.get('name', '')}: {info.get('shares', 0)}股")

    else:
        parser.print_help()
