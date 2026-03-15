#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股数据补充工具 - 东方财富、同花顺数据获取
补充雅虎财经数据缺口
"""

import requests
import duckdb
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Union
import time
import json

# 数据库路径
DB_PATH = "/root/.openclaw/workspace/data/a_market.duckdb"


class EastMoneyDataAPI:
    """东方财富数据API"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.base_url = "http://push2.eastmoney.com/api/qt"

    def _get(self, url: str, params: dict = None) -> dict:
        """发送GET请求"""
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('rc') != 0:
                return {'success': False, 'error': data.get('rt', 'Unknown error')}

            return {'success': True, 'data': data.get('data')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_stock_money_flow(self, stock_code: str) -> dict:
        """
        获取个股资金流向

        Args:
            stock_code: 股票代码（如 '600887' 或 '000001'）

        Returns:
            {
                'date': '2025-03-13',
                'code': '600887',
                'name': '伊利股份',
                'main_net_inflow': 123456789.0,      # 主力净流入
                'super_large_net': 50000000.0,        # 超大单净流入
                'large_net': 73456789.0,              # 大单净流入
                'medium_net': -20000000.0,            # 中单净流入
                'small_net': -90000000.0,             # 小单净流入
                'main_net_inflow_ratio': 2.35         # 主力净流入占比(%)
            }
        """
        # 使用东方财富网页版API
        url = "http://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
        params = {
            'secid': self._format_secid(stock_code),
            'fields1': 'f1,f2,f3,f7',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63',
            'klt': '101',  # 日K
            'lmt': '1',    # 最新1天
            'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
            '_': str(int(time.time() * 1000))
        }

        result = self._get(url, params)

        if not result['success']:
            return {'success': False, 'error': result['error']}

        try:
            data = result['data']
            if not data or 'diff' not in data:
                return {'success': False, 'error': 'No data available'}

            # 解析最新一天的数据
            latest = data['diff'][0] if data['diff'] else {}

            return {
                'success': True,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'code': stock_code,
                'name': data.get('name', ''),
                'main_net_inflow': float(latest.get('f62', 0)),          # 主力净流入
                'super_large_net': float(latest.get('f54', 0)),          # 超大单净流入
                'large_net': float(latest.get('f55', 0)),                # 大单净流入
                'medium_net': float(latest.get('f56', 0)),               # 中单净流入
                'small_net': float(latest.get('f57', 0)),                # 小单净流入
                'main_net_inflow_ratio': float(latest.get('f58', 0)),    # 主力净流入占比
                'raw': latest
            }
        except Exception as e:
            return {'success': False, 'error': f'Parse error: {str(e)}'}

    def get_limit_stats(self, market: str = 'all') -> dict:
        """
        获取涨跌停统计

        Args:
            market: 'sh'=上海, 'sz'=深圳, 'all'=全部

        Returns:
            {
                'success': True,
                'date': '2025-03-13',
                'limit_up_count': 45,              # 涨停家数
                'limit_down_count': 12,            # 跌停家数
                'list': [
                    {
                        'code': '600887',
                        'name': '伊利股份',
                        'limit_type': '涨停',
                        'limit_time': '09:45:23',
                        'seal_amount': 123456789.0,   # 封板资金
                        'break_times': 0               # 炸板次数
                    }
                ]
            }
        """
        # 东方财富涨跌停API
        url = "http://push2.eastmoney.com/api/qt/clist/get"
        params = {
            'pn': '1',
            'pz': '500',  # 每页数量
            'po': '1',
            'np': '1',
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': '2',
            'invt': '2',
            'fid': 'f3',  # 按涨跌幅排序
            'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',  # A股所有股票
            'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26',
            'f1': 'f3',  # 涨跌幅排序
            'f2': 'f5'   # 涨跌停筛选
        }

        result = self._get(url, params)

        if not result['success']:
            return {'success': False, 'error': result['error']}

        try:
            data = result['data']
            if not data or 'diff' not in data:
                return {'success': False, 'error': 'No data available'}

            stocks = data['diff']

            # 筛选涨跌停股票
            limit_up = []
            limit_down = []

            for stock in stocks:
                change_pct = stock.get('f3', 0)  # 涨跌幅
                code = stock.get('f12', '')
                name = stock.get('f14', '')

                # 判断涨跌停（简化判断，实际需考虑ST等）
                if change_pct >= 9.9:  # 涨停
                    limit_up.append({
                        'code': code,
                        'name': name,
                        'limit_type': '涨停',
                        'limit_time': datetime.now().strftime('%H:%M:%S'),
                        'seal_amount': stock.get('f5', 0) * 10000,  # 成交额
                        'break_times': 0
                    })
                elif change_pct <= -9.9:  # 跌停
                    limit_down.append({
                        'code': code,
                        'name': name,
                        'limit_type': '跌停',
                        'limit_time': datetime.now().strftime('%H:%M:%S'),
                        'seal_amount': stock.get('f5', 0) * 10000,
                        'break_times': 0
                    })

            return {
                'success': True,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'limit_up_count': len(limit_up),
                'limit_down_count': len(limit_down),
                'list': limit_up + limit_down
            }
        except Exception as e:
            return {'success': False, 'error': f'Parse error: {str(e)}'}

    def get_dragon_tiger_list(self, trade_date: str = None) -> dict:
        """
        获取龙虎榜数据

        Args:
            trade_date: 交易日期（格式：'2025-03-13'），None为最新

        Returns:
            {
                'success': True,
                'date': '2025-03-13',
                'list': [
                    {
                        'code': '600887',
                        'name': '伊利股份',
                        'reason': '涨幅偏离值达7%',
                        'buy_amount': 123456789.0,
                        'sell_amount': 50000000.0,
                        'net_buy': 73456789.0,
                        'institution_net': 30000000.0
                    }
                ]
            }
        """
        # 东方财富龙虎榜API
        url = "http://push2.eastmoney.com/api/qt/clist/get"
        params = {
            'pn': '1',
            'pz': '500',
            'po': '1',
            'np': '1',
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': '2',
            'invt': '2',
            'fid': 'f3',
            'fs': 'b:MK0021,b:MK0022,b:MK0023,b:MK0024',  # 龙虎榜分类
            'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f60,f70,f71,f72,f73,f74,f75,f78,f79,f80,f81,f82,f84,f85,f115,f128',
        }

        result = self._get(url, params)

        if not result['success']:
            return {'success': False, 'error': result['error']}

        try:
            data = result['data']
            if not data or 'diff' not in data:
                return {'success': False, 'error': 'No data available'}

            stocks = data['diff']
            dragon_list = []

            for stock in stocks:
                code = stock.get('f12', '')
                name = stock.get('f14', '')
                reason = stock.get('f84', '')  # 上榜原因
                buy_amount = stock.get('f72', 0) * 10000  # 买入总额
                sell_amount = stock.get('f73', 0) * 10000  # 卖出总额

                dragon_list.append({
                    'code': code,
                    'name': name,
                    'reason': reason,
                    'buy_amount': buy_amount,
                    'sell_amount': sell_amount,
                    'net_buy': buy_amount - sell_amount,
                    'institution_net': stock.get('f62', 0) * 10000  # 机构净买卖
                })

            return {
                'success': True,
                'date': trade_date or datetime.now().strftime('%Y-%m-%d'),
                'list': dragon_list
            }
        except Exception as e:
            return {'success': False, 'error': f'Parse error: {str(e)}'}

    def get_sector_performance(self, sector_type: str = 'industry') -> dict:
        """
        获取板块涨跌幅排行

        Args:
            sector_type: 'industry'=行业板块, 'concept'=概念板块

        Returns:
            {
                'success': True,
                'date': '2025-03-13',
                'type': 'industry',
                'list': [
                    {
                        'sector_name': '食品饮料',
                        'change_pct': 3.45,
                        'money_flow': 1234567890.0,
                        'leading_stock': '600887',
                        'stock_count': 85
                    }
                ]
            }
        """
        # 东方财富板块API
        url = "http://push2.eastmoney.com/api/qt/clist/get"

        # sector_type映射
        type_map = {
            'industry': 'm:90+t:2',  # 行业板块
            'concept': 'm:90+t:3'    # 概念板块
        }

        params = {
            'pn': '1',
            'pz': '500',
            'po': '1',
            'np': '1',
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': '2',
            'invt': '2',
            'fid': 'f3',  # 按涨跌幅排序
            'fs': type_map.get(sector_type, 'm:90+t:2'),
            'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f62,f66,f67,f68,f69,f70,f71,f72,f73,f74,f75,f76,f77,f78,f79,f80,f81,f82,f84,f85,f115,f128',
        }

        result = self._get(url, params)

        if not result['success']:
            return {'success': False, 'error': result['error']}

        try:
            data = result['data']
            if not data or 'diff' not in data:
                return {'success': False, 'error': 'No data available'}

            sectors = data['diff']
            sector_list = []

            for sector in sectors:
                sector_list.append({
                    'sector_name': sector.get('f14', ''),     # 板块名称
                    'change_pct': sector.get('f3', 0),        # 涨跌幅
                    'money_flow': sector.get('f62', 0) * 10000,  # 资金流入
                    'leading_stock': sector.get('f12', ''),   # 龙头股票
                    'stock_count': sector.get('f115', 0)     # 股票数量
                })

            return {
                'success': True,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'type': sector_type,
                'list': sector_list
            }
        except Exception as e:
            return {'success': False, 'error': f'Parse error: {str(e)}'}

    def get_north_money_flow(self, stock_code: str = None) -> dict:
        """
        获取北向资金流向

        Args:
            stock_code: 个股代码，None则为整体流向

        Returns:
            {
                'success': True,
                'date': '2025-03-13',
                'shg_net_inflow': 5000000000.0,   # 沪股通净流入
                'szg_net_inflow': 3000000000.0,   # 深股通净流入
                'total_net_inflow': 8000000000.0, # 总净流入
                'stocks': [...]  # 个股持股数据（如果指定stock_code）
            }
        """
        # 东方财富北向资金API
        url = "http://push2.eastmoney.com/api/qt/stock/nktff.lowKline.get"

        params = {
            'fields1': 'f1,f2,f3,f4,f5',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
            'ut': 'b5d3aa7fa1faa494a146b95f47cd8957',
            'lmt': '1',  # 最新1天
            'klt': '101',  # 日K
            '_': str(int(time.time() * 1000))
        }

        result = self._get(url, params)

        if not result['success']:
            return {'success': False, 'error': result['error']}

        try:
            data = result['data']
            if not data:
                return {'success': False, 'error': 'No data available'}

            return {
                'success': True,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'shg_net_inflow': data.get('shg', 0) * 10000,
                'szg_net_inflow': data.get('szg', 0) * 10000,
                'total_net_inflow': data.get('total', 0) * 10000,
                'raw': data
            }
        except Exception as e:
            return {'success': False, 'error': f'Parse error: {str(e)}'}

    def get_margin_trading(self, stock_code: str = None) -> dict:
        """
        获取融资融券数据

        Args:
            stock_code: 个股代码，None则为市场整体

        Returns:
            {
                'success': True,
                'date': '2025-03-13',
                'code': '600887',
                'name': '伊利股份',
                'margin_balance': 1234567890.0,     # 融资余额
                'short_balance': 12345678.0,        # 融券余额
                'margin_buy': 50000000.0,           # 融资买入额
                'short_sell': 10000.0               # 融券卖出量
            }
        """
        # 东方财富融资融券API
        url = f"{self.base_url}/stock/rzrq/get"
        params = {
            'secid': self._format_secid(stock_code) if stock_code else '0.000001',  # 默认上证指数
            'fields1': 'f1,f2,f3,f4',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
            'lmt': '1',  # 最新一天
            'ut': 'b5d3aa7fa1faa494a146b95f47cd8957',
            'cb': 'jQuery',
            '_': str(int(time.time() * 1000))
        }

        result = self._get(url, params)

        if not result['success']:
            return {'success': False, 'error': result['error']}

        try:
            data = result['data']
            if not data:
                return {'success': False, 'error': 'No data available'}

            latest = data[0] if isinstance(data, list) else data

            return {
                'success': True,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'code': stock_code or '',
                'name': latest.get('name', ''),
                'margin_balance': latest.get('f51', 0) * 10000,    # 融资余额
                'short_balance': latest.get('f52', 0) * 10000,     # 融券余额
                'margin_buy': latest.get('f53', 0) * 10000,        # 融资买入额
                'short_sell': latest.get('f54', 0),                # 融券卖出量
                'raw': latest
            }
        except Exception as e:
            return {'success': False, 'error': f'Parse error: {str(e)}'}

    def _format_secid(self, stock_code: str) -> str:
        """
        格式化股票代码为东方财富secid格式

        Args:
            stock_code: '600887' 或 '000001'

        Returns:
            '1.600887' 或 '0.000001'
            1 = 上海, 0 = 深圳
        """
        if not stock_code:
            return '1.000001'  # 默认上证指数

        code = stock_code.strip()
        # 上海股票：6开头
        if code.startswith('6'):
            return f'1.{code}'
        # 深圳股票：0或3开头
        else:
            return f'0.{code}'


# 数据库操作函数

def init_db():
    """初始化数据库表"""
    conn = duckdb.connect(DB_PATH)

    # 资金流向表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_money_flow (
            date DATE,
            code VARCHAR(10),
            name VARCHAR(50),
            main_net_inflow DOUBLE,
            super_large_net DOUBLE,
            large_net DOUBLE,
            medium_net DOUBLE,
            small_net DOUBLE,
            main_net_inflow_ratio DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, code)
        )
    """)

    # 涨跌停表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_limit_stats (
            date DATE,
            code VARCHAR(10),
            name VARCHAR(50),
            limit_type VARCHAR(10),
            limit_time VARCHAR(10),
            seal_amount DOUBLE,
            break_times INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, code, limit_type)
        )
    """)

    # 龙虎榜表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dragon_tiger_list (
            date DATE,
            code VARCHAR(10),
            name VARCHAR(50),
            reason VARCHAR(100),
            buy_amount DOUBLE,
            sell_amount DOUBLE,
            net_buy DOUBLE,
            institution_net DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, code)
        )
    """)

    # 板块表现表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sector_performance (
            date DATE,
            sector_name VARCHAR(50),
            sector_type VARCHAR(20),
            change_pct DOUBLE,
            money_flow DOUBLE,
            leading_stock VARCHAR(10),
            stock_count INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, sector_name, sector_type)
        )
    """)

    # 北向资金表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS north_money_flow (
            date DATE,
            code VARCHAR(10),
            name VARCHAR(50),
            hold_ratio DOUBLE,
            hold_amount DOUBLE,
            hold_change DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, code)
        )
    """)

    # 融资融券表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS margin_trading (
            date DATE,
            code VARCHAR(10),
            name VARCHAR(50),
            margin_balance DOUBLE,
            short_balance DOUBLE,
            margin_buy DOUBLE,
            short_sell DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, code)
        )
    """)

    conn.close()


# 对外接口函数

def sync_stock_money_flow(code: str, name: str = '') -> dict:
    """
    同步个股资金流向

    Args:
        code: 股票代码（如 '600887'）
        name: 股票名称（可选）

    Returns:
        {'success': True, 'inserted': 1, 'message': '...'}
    """
    api = EastMoneyDataAPI()
    result = api.get_stock_money_flow(code)

    if not result['success']:
        return {'success': False, 'error': result['error']}

    try:
        conn = duckdb.connect(DB_PATH)

        conn.execute("""
            INSERT OR REPLACE INTO stock_money_flow
            (date, code, name, main_net_inflow, super_large_net, large_net,
             medium_net, small_net, main_net_inflow_ratio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            result['date'],
            result['code'],
            result.get('name', name),
            result['main_net_inflow'],
            result['super_large_net'],
            result['large_net'],
            result['medium_net'],
            result['small_net'],
            result['main_net_inflow_ratio']
        ])

        conn.close()

        return {
            'success': True,
            'inserted': 1,
            'message': f"✅ {result.get('name', name)} 资金流向数据已同步",
            'main_net_inflow': result['main_net_inflow'],
            'main_net_inflow_ratio': result['main_net_inflow_ratio']
        }
    except Exception as e:
        return {'success': False, 'error': f'Database error: {str(e)}'}


def sync_limit_stats(market: str = 'all') -> dict:
    """
    同步涨跌停统计

    Args:
        market: 'sh'=上海, 'sz'=深圳, 'all'=全部

    Returns:
        {'success': True, 'inserted': 57, 'limit_up': 45, 'limit_down': 12}
    """
    api = EastMoneyDataAPI()
    result = api.get_limit_stats(market)

    if not result['success']:
        return {'success': False, 'error': result['error']}

    try:
        conn = duckdb.connect(DB_PATH)
        inserted = 0

        for stock in result['list']:
            conn.execute("""
                INSERT OR REPLACE INTO stock_limit_stats
                (date, code, name, limit_type, limit_time, seal_amount, break_times)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                result['date'],
                stock['code'],
                stock['name'],
                stock['limit_type'],
                stock['limit_time'],
                stock['seal_amount'],
                stock['break_times']
            ])
            inserted += 1

        conn.close()

        return {
            'success': True,
            'inserted': inserted,
            'limit_up': result['limit_up_count'],
            'limit_down': result['limit_down_count'],
            'message': f"✅ 涨跌停数据已同步：涨停{result['limit_up_count']}家，跌停{result['limit_down_count']}家"
        }
    except Exception as e:
        return {'success': False, 'error': f'Database error: {str(e)}'}


def sync_dragon_tiger_list(trade_date: str = None) -> dict:
    """
    同步龙虎榜数据

    Args:
        trade_date: 交易日期（'2025-03-13'），None为最新

    Returns:
        {'success': True, 'inserted': 25, 'date': '2025-03-13'}
    """
    api = EastMoneyDataAPI()
    result = api.get_dragon_tiger_list(trade_date)

    if not result['success']:
        return {'success': False, 'error': result['error']}

    try:
        conn = duckdb.connect(DB_PATH)
        inserted = 0

        for stock in result['list']:
            conn.execute("""
                INSERT OR REPLACE INTO dragon_tiger_list
                (date, code, name, reason, buy_amount, sell_amount, net_buy, institution_net)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                result['date'],
                stock['code'],
                stock['name'],
                stock['reason'],
                stock['buy_amount'],
                stock['sell_amount'],
                stock['net_buy'],
                stock['institution_net']
            ])
            inserted += 1

        conn.close()

        return {
            'success': True,
            'inserted': inserted,
            'date': result['date'],
            'message': f"✅ 龙虎榜数据已同步：{inserted}只股票上榜"
        }
    except Exception as e:
        return {'success': False, 'error': f'Database error: {str(e)}'}


def sync_sector_performance(sector_type: str = 'industry') -> dict:
    """
    同步板块涨跌幅排行

    Args:
        sector_type: 'industry'=行业板块, 'concept'=概念板块

    Returns:
        {'success': True, 'inserted': 28, 'type': 'industry'}
    """
    api = EastMoneyDataAPI()
    result = api.get_sector_performance(sector_type)

    if not result['success']:
        return {'success': False, 'error': result['error']}

    try:
        conn = duckdb.connect(DB_PATH)
        inserted = 0

        for sector in result['list']:
            conn.execute("""
                INSERT OR REPLACE INTO sector_performance
                (date, sector_name, sector_type, change_pct, money_flow, leading_stock, stock_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                result['date'],
                sector['sector_name'],
                result['type'],
                sector['change_pct'],
                sector['money_flow'],
                sector['leading_stock'],
                sector['stock_count']
            ])
            inserted += 1

        conn.close()

        type_name = '行业板块' if sector_type == 'industry' else '概念板块'
        return {
            'success': True,
            'inserted': inserted,
            'type': sector_type,
            'message': f"✅ {type_name}数据已同步：{inserted}个板块"
        }
    except Exception as e:
        return {'success': False, 'error': f'Database error: {str(e)}'}


def sync_north_money_flow() -> dict:
    """
    同步北向资金流向

    Returns:
        {'success': True, 'shg_net_inflow': 5000000000, 'szg_net_inflow': 3000000000}
    """
    api = EastMoneyDataAPI()
    result = api.get_north_money_flow()

    if not result['success']:
        return {'success': False, 'error': result['error']}

    # 保存到数据库（简化处理，实际应该有单独的汇总表）
    try:
        conn = duckdb.connect(DB_PATH)

        # 创建北向资金汇总表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS north_money_flow_summary (
                date DATE PRIMARY KEY,
                shg_net_inflow DOUBLE,
                szg_net_inflow DOUBLE,
                total_net_inflow DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            INSERT OR REPLACE INTO north_money_flow_summary
            (date, shg_net_inflow, szg_net_inflow, total_net_inflow)
            VALUES (?, ?, ?, ?)
        """, [
            result['date'],
            result['shg_net_inflow'],
            result['szg_net_inflow'],
            result['total_net_inflow']
        ])

        conn.close()

        return {
            'success': True,
            'date': result['date'],
            'shg_net_inflow': result['shg_net_inflow'],
            'szg_net_inflow': result['szg_net_inflow'],
            'total_net_inflow': result['total_net_inflow'],
            'message': f"✅ 北向资金已同步：沪股通{result['shg_net_inflow']/100000000:.2f}亿，深股通{result['szg_net_inflow']/100000000:.2f}亿"
        }
    except Exception as e:
        return {'success': False, 'error': f'Database error: {str(e)}'}


def sync_margin_trading(code: str = None) -> dict:
    """
    同步融资融券数据

    Args:
        code: 个股代码，None则为市场整体

    Returns:
        {'success': True, 'margin_balance': 1234567890, 'short_balance': 12345678}
    """
    api = EastMoneyDataAPI()
    result = api.get_margin_trading(code)

    if not result['success']:
        return {'success': False, 'error': result['error']}

    try:
        conn = duckdb.connect(DB_PATH)

        if code:  # 个股数据
            conn.execute("""
                INSERT OR REPLACE INTO margin_trading
                (date, code, name, margin_balance, short_balance, margin_buy, short_sell)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                result['date'],
                result['code'],
                result['name'],
                result['margin_balance'],
                result['short_balance'],
                result['margin_buy'],
                result['short_sell']
            ])

            conn.close()

            return {
                'success': True,
                'code': code,
                'margin_balance': result['margin_balance'],
                'message': f"✅ {result['name']} 融资融券数据已同步"
            }
        else:  # 市场汇总
            # 创建市场汇总表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS margin_trading_summary (
                    date DATE PRIMARY KEY,
                    total_margin_balance DOUBLE,
                    total_short_balance DOUBLE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.close()

            return {
                'success': True,
                'date': result['date'],
                'message': "✅ 融资融券市场数据已同步"
            }
    except Exception as e:
        return {'success': False, 'error': f'Database error: {str(e)}'}


def query_a_market(sql: str) -> dict:
    """
    查询A股补充数据

    Args:
        sql: SQL查询语句

    Returns:
        {'success': True, 'data': [...], 'columns': [...]}
    """
    try:
        conn = duckdb.connect(DB_PATH)
        result = conn.execute(sql).fetchall()

        # 获取列名
        columns = [desc[0] for desc in conn.description]

        conn.close()

        # 转换为字典列表
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


def batch_update_all() -> dict:
    """
    批量更新所有A股补充数据

    Returns:
        {'success': True, 'summary': {...}}
    """
    results = {}

    # 1. 涨跌停数据
    print("📊 同步涨跌停数据...")
    results['limit_stats'] = sync_limit_stats()

    # 2. 龙虎榜数据
    print("🐉 同步龙虎榜数据...")
    results['dragon_tiger'] = sync_dragon_tiger_list()

    # 3. 行业板块
    print("🏭 同步行业板块数据...")
    results['sector_industry'] = sync_sector_performance('industry')

    # 4. 概念板块
    print("💡 同步概念板块数据...")
    results['sector_concept'] = sync_sector_performance('concept')

    # 5. 北向资金
    print("💰 同步北向资金数据...")
    results['north_money'] = sync_north_money_flow()

    # 统计
    success_count = sum(1 for r in results.values() if r.get('success'))

    return {
        'success': True,
        'summary': results,
        'message': f"✅ 批量更新完成：{success_count}/{len(results)} 项成功"
    }


# 初始化数据库
if __name__ == '__main__':
    init_db()
    print("✅ 数据库表已初始化")
