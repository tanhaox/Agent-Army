#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个股数据补充工具 - 基于AKShare
从东方财富等数据源获取个股级别的独有数据
补充雅虎财经的个股信息缺口
"""

import akshare as ak
import duckdb
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

# 数据库路径
DB_PATH = "/root/.openclaw/workspace/data/stock_detail.duckdb"


class AKShareStockAPI:
    """AKShare个股数据API"""

    def get_stock_money_flow(self, stock_code: str, market: str = 'sh') -> dict:
        """
        获取个股资金流向

        Args:
            stock_code: 股票代码（如 '601669'）
            market: 市场 ('sh'=上海, 'sz'=深圳, 'bj'=北京)

        Returns:
            {
                'success': True,
                'data': DataFrame,  # 近120天资金流向数据
                'latest': dict      # 最新一天数据
            }
        """
        try:
            df = ak.stock_individual_fund_flow(stock=stock_code, market=market)
            if df.empty:
                return {'success': False, 'error': 'No data available'}

            latest = df.iloc[0].to_dict()

            return {
                'success': True,
                'data': df,
                'latest': {
                    'date': str(latest.get('日期', '')),
                    'close': float(latest.get('收盘价', 0)),
                    'change_pct': float(latest.get('涨跌幅', 0)),
                    'main_net_inflow': float(latest.get('主力净流入-净额', 0)),
                    'main_net_inflow_ratio': float(latest.get('主力净流入-净占比', 0)),
                    'super_large_net': float(latest.get('超大单净流入-净额', 0)),
                    'large_net': float(latest.get('大单净流入-净额', 0)),
                    'medium_net': float(latest.get('中单净流入-净额', 0)),
                    'small_net': float(latest.get('小单净流入-净额', 0))
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_stock_shareholders(self, stock_code: str) -> dict:
        """
        获取个股股东户数

        Returns:
            {
                'success': True,
                'data': dict
            }
        """
        try:
            # 获取最新股东户数
            df = ak.stock_zh_a_gdhs(symbol="最新")
            if df.empty:
                return {'success': False, 'error': 'No data available'}

            # 筛选指定股票
            stock_df = df[df['代码'] == stock_code]
            if stock_df.empty:
                return {'success': False, 'error': 'Stock not found'}

            latest = stock_df.iloc[0]

            return {
                'success': True,
                'latest': {
                    'code': str(latest.get('代码', stock_code)),
                    'name': str(latest.get('名称', '')),
                    'shareholder_count': int(latest.get('股东户数-本次', 0)),
                    'shareholder_count_prev': int(latest.get('股东户数-上次', 0)),
                    'count_change': int(latest.get('股东户数-增减', 0)),
                    'count_change_ratio': float(latest.get('股东户数-增减比例', 0)),
                    'shares_per_holder': float(latest.get('户均持股数量', 0)),
                    'value_per_holder': float(latest.get('户均持股市值', 0)),
                    'stat_date': str(latest.get('股东户数统计截止日-本次', '')),
                    'stat_date_prev': str(latest.get('股东户数统计截止日-上次', '')),
                    'announce_date': str(latest.get('公告日期', ''))
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_stock_unlock(self, stock_code: str, days: int = 365) -> dict:
        """
        获取个股限售解禁

        Args:
            stock_code: 股票代码
            days: 查询未来多少天

        Returns:
            {
                'success': True,
                'list': [...]
            }
        """
        try:
            end_date = (datetime.now() + timedelta(days=days)).strftime('%Y%m%d')
            start_date = datetime.now().strftime('%Y%m%d')

            df = ak.stock_restricted_release_detail_em(start_date=start_date, end_date=end_date)
            if df.empty:
                return {'success': True, 'list': []}

            # 筛选指定股票
            stock_df = df[df['代码'] == stock_code]
            if stock_df.empty:
                return {'success': True, 'list': []}

            unlock_list = []
            for _, row in stock_df.iterrows():
                unlock_list.append({
                    'unlock_date': str(row.get('解禁日期', '')),
                    'code': str(row.get('代码', stock_code)),
                    'name': str(row.get('名称', '')),
                    'unlock_shares': float(row.get('解禁数量', 0)),
                    'unlock_value': float(row.get('解禁市值', 0)),
                    'ratio_to_total': float(row.get('占总股本比例', 0)),
                    'unlock_type': str(row.get('解禁类型', ''))
                })

            return {
                'success': True,
                'list': unlock_list
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_stock_north_holdings(self, stock_code: str) -> dict:
        """
        获取个股港股通持股数据

        Returns:
            {
                'success': True,
                'data': dict or None
            }
        """
        try:
            # 获取港股通持股统计
            df = ak.stock_hsgt_stock_statistics_em()
            if df.empty:
                return {'success': True, 'data': None, 'note': 'Not in HK stock connect'}

            # 筛选指定股票
            stock_df = df[df['代码'] == stock_code]
            if stock_df.empty:
                return {'success': True, 'data': None, 'note': 'Not in HK stock connect'}

            latest = stock_df.iloc[0]

            return {
                'success': True,
                'data': {
                    'code': str(latest.get('代码', stock_code)),
                    'name': str(latest.get('名称', '')),
                    'hold_ratio': float(latest.get('持股比例', 0)),
                    'hold_amount': float(latest.get('持股数量', 0)),
                    'hold_value': float(latest.get('持股市值', 0)),
                    'date': str(latest.get('统计日期', ''))
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_stock_margin_trading(self, stock_code: str, date: str = None) -> dict:
        """
        获取个股融资融券数据

        注意：AKShare的融资融券接口需要按日期查询全市场数据，然后筛选

        Returns:
            {
                'success': True,
                'data': dict or None
            }
        """
        try:
            # 由于AKShare的融资融券接口不支持按股票代码查询，
            # 这里返回提示信息
            return {
                'success': False,
                'error': 'AKShare margin trading API requires date parameter and returns market-wide data. Please use alternative data source.'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# 数据库操作

def init_db():
    """初始化数据库表"""
    conn = duckdb.connect(DB_PATH)

    # 个股资金流向
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_money_flow (
            date DATE,
            code VARCHAR(10),
            name VARCHAR(50),
            close DOUBLE,
            change_pct DOUBLE,
            main_net_inflow DOUBLE,
            main_net_inflow_ratio DOUBLE,
            super_large_net DOUBLE,
            large_net DOUBLE,
            medium_net DOUBLE,
            small_net DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, code)
        )
    """)

    # 个股股东数据
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_shareholders (
            code VARCHAR(10) PRIMARY KEY,
            name VARCHAR(50),
            shareholder_count INT,
            shareholder_count_prev INT,
            count_change INT,
            count_change_ratio DOUBLE,
            shares_per_holder DOUBLE,
            value_per_holder DOUBLE,
            stat_date VARCHAR(20),
            stat_date_prev VARCHAR(20),
            announce_date VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 个股限售解禁
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_unlock (
            unlock_date DATE,
            code VARCHAR(10),
            name VARCHAR(50),
            unlock_shares DOUBLE,
            unlock_value DOUBLE,
            ratio_to_total DOUBLE,
            unlock_type VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (unlock_date, code)
        )
    """)

    # 个股北向持股
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_north_holdings (
            code VARCHAR(10) PRIMARY KEY,
            name VARCHAR(50),
            hold_ratio DOUBLE,
            hold_amount DOUBLE,
            hold_value DOUBLE,
            stat_date VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.close()


# 对外接口函数

def sync_stock_money_flow(code: str, name: str = '') -> dict:
    """同步个股资金流向"""
    # 判断市场
    if code.startswith('6'):
        market = 'sh'
    elif code.startswith('0') or code.startswith('3'):
        market = 'sz'
    else:
        market = 'bj'

    api = AKShareStockAPI()
    result = api.get_stock_money_flow(code, market)

    if not result['success']:
        return {'success': False, 'error': result['error']}

    try:
        conn = duckdb.connect(DB_PATH)
        latest = result['latest']

        # 插入最新一天的数据
        conn.execute("""
            INSERT OR REPLACE INTO stock_money_flow
            (date, code, name, close, change_pct, main_net_inflow,
             main_net_inflow_ratio, super_large_net, large_net, medium_net, small_net)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            latest['date'], code, name or '',
            latest['close'], latest['change_pct'],
            latest['main_net_inflow'], latest['main_net_inflow_ratio'],
            latest['super_large_net'], latest['large_net'],
            latest['medium_net'], latest['small_net']
        ])

        conn.close()

        return {
            'success': True,
            'code': code,
            'date': latest['date'],
            'main_net_inflow': latest['main_net_inflow'],
            'main_net_inflow_ratio': latest['main_net_inflow_ratio'],
            'message': f"✅ {name} 资金流向已同步（{latest['date']}）"
        }
    except Exception as e:
        return {'success': False, 'error': f'DB error: {str(e)}'}


def sync_stock_shareholders(code: str, name: str = '') -> dict:
    """同步个股股东数据"""
    api = AKShareStockAPI()
    result = api.get_stock_shareholders(code)

    if not result['success']:
        return {'success': False, 'error': result['error']}

    try:
        conn = duckdb.connect(DB_PATH)
        data = result['latest']

        conn.execute("""
            INSERT OR REPLACE INTO stock_shareholders
            (code, name, shareholder_count, shareholder_count_prev, count_change,
             count_change_ratio, shares_per_holder, value_per_holder,
             stat_date, stat_date_prev, announce_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            data['code'], data['name'], data['shareholder_count'],
            data['shareholder_count_prev'], data['count_change'],
            data['count_change_ratio'], data['shares_per_holder'],
            data['value_per_holder'], data['stat_date'],
            data['stat_date_prev'], data['announce_date']
        ])

        conn.close()

        return {
            'success': True,
            'code': code,
            'shareholder_count': data['shareholder_count'],
            'shares_per_holder': data['shares_per_holder'],
            'count_change_ratio': data['count_change_ratio'],
            'message': f"✅ {data['name']} 股东数据已同步（{data['stat_date']}）"
        }
    except Exception as e:
        return {'success': False, 'error': f'DB error: {str(e)}'}


def sync_stock_unlock(code: str, name: str = '') -> dict:
    """同步个股限售解禁"""
    api = AKShareStockAPI()
    result = api.get_stock_unlock(code, days=365)

    if not result['success']:
        return {'success': False, 'error': result['error']}

    try:
        conn = duckdb.connect(DB_PATH)
        inserted = 0

        for item in result['list']:
            conn.execute("""
                INSERT OR REPLACE INTO stock_unlock
                (unlock_date, code, name, unlock_shares, unlock_value, ratio_to_total, unlock_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                item['unlock_date'], item['code'], item['name'] or name,
                item['unlock_shares'], item['unlock_value'],
                item['ratio_to_total'], item['unlock_type']
            ])
            inserted += 1

        conn.close()

        return {
            'success': True,
            'code': code,
            'inserted': inserted,
            'message': f"✅ {name} 限售解禁数据已同步（{inserted}条）"
        }
    except Exception as e:
        return {'success': False, 'error': f'DB error: {str(e)}'}


def sync_stock_north_holdings(code: str, name: str = '') -> dict:
    """同步个股北向持股"""
    api = AKShareStockAPI()
    result = api.get_stock_north_holdings(code)

    if not result['success']:
        return {'success': False, 'error': result['error']}

    try:
        conn = duckdb.connect(DB_PATH)

        if result['data'] is None:
            conn.close()
            return {
                'success': True,
                'code': code,
                'note': result.get('note', 'Not in HK stock connect'),
                'message': f"⚠️  {name} 不是港股通标的"
            }

        data = result['data']

        conn.execute("""
            INSERT OR REPLACE INTO stock_north_holdings
            (code, name, hold_ratio, hold_amount, hold_value, stat_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            data['code'], data['name'] or name,
            data['hold_ratio'], data['hold_amount'],
            data['hold_value'], data['date']
        ])

        conn.close()

        return {
            'success': True,
            'code': code,
            'hold_ratio': data['hold_ratio'],
            'hold_amount': data['hold_amount'],
            'message': f"✅ {data['name']} 北向持股已同步（比例{data['hold_ratio']:.2f}%）"
        }
    except Exception as e:
        return {'success': False, 'error': f'DB error: {str(e)}'}


def sync_stock_all(code: str, name: str = '') -> dict:
    """批量同步个股所有补充数据"""
    results = {}
    errors = []

    print(f"🔄 开始同步 {name}({code}) 的所有补充数据...")

    # 1. 资金流向
    print("  [1/4] 资金流向...")
    results['money_flow'] = sync_stock_money_flow(code, name)
    if not results['money_flow']['success']:
        errors.append(f"资金流向: {results['money_flow'].get('error', 'Unknown')}")

    # 2. 股东数据
    print("  [2/4] 股东数据...")
    results['shareholders'] = sync_stock_shareholders(code, name)
    if not results['shareholders']['success']:
        errors.append(f"股东数据: {results['shareholders'].get('error', 'Unknown')}")

    # 3. 限售解禁
    print("  [3/4] 限售解禁...")
    results['unlock'] = sync_stock_unlock(code, name)
    if not results['unlock']['success']:
        errors.append(f"限售解禁: {results['unlock'].get('error', 'Unknown')}")

    # 4. 北向持股
    print("  [4/4] 北向持股...")
    results['north_holdings'] = sync_stock_north_holdings(code, name)
    if not results['north_holdings']['success']:
        errors.append(f"北向持股: {results['north_holdings'].get('error', 'Unknown')}")

    # 统计
    success_count = sum(1 for r in results.values() if r.get('success'))

    return {
        'success': len(errors) == 0,
        'code': code,
        'name': name,
        'success_count': success_count,
        'total_count': 4,
        'results': results,
        'errors': errors,
        'message': f"✅ {name} 数据同步完成：{success_count}/4 项成功" +
                  (f"\n⚠️  失败项: {', '.join(errors)}" if errors else "")
    }


def query_stock_detail(sql: str) -> dict:
    """查询个股补充数据"""
    try:
        conn = duckdb.connect(DB_PATH)
        result = conn.execute(sql).fetchall()
        columns = [desc[0] for desc in conn.description]
        conn.close()

        data = [dict(zip(columns, row)) for row in result]

        return {
            'success': True,
            'data': data,
            'columns': columns,
            'count': len(data),
            'message': f"✅ 查询成功，返回{len(data)}条记录"
        }
    except Exception as e:
        return {'success': False, 'error': f'Query error: {str(e)}'}


# 初始化
if __name__ == '__main__':
    init_db()
    print("✅ 数据库表已初始化")
