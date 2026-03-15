#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富板块数据爬虫 Skill
通过网页抓取获取板块资金流向、成分股等数据
"""

import re
import pandas as pd
from datetime import datetime
from duckdb import connect

# 数据库路径
DB_PATH = "data/stocks.duckdb"

class EastmoneySectorCrawler:
    """东方财富板块数据爬虫"""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = connect(db_path)
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sector_fund_flow (
                date VARCHAR,
                rank INT,
                sector_name VARCHAR,
                change_pct DOUBLE,
                main_net_inflow DOUBLE,
                main_net_inflow_ratio DOUBLE,
                super_large_net DOUBLE,
                super_large_ratio DOUBLE,
                large_net DOUBLE,
                large_ratio DOUBLE,
                medium_net DOUBLE,
                medium_ratio DOUBLE,
                small_net DOUBLE,
                small_ratio DOUBLE,
                max_stock VARCHAR(20),
                PRIMARY KEY (date, sector_name)
            )
        """)

    def parse_fund_flow_table(self, text):
        """解析板块资金流向表格（完整双表头结构）

        字段对应：
        - 序号, 名称, 涨跌幅
        - 主力净流入(净额+占比)
        - 超大单净流入(净额+占比)
        - 大单净流入(净额+占比)
        - 中单净流入(净额+占比)
        - 小单净流入(净额+占比)
        - 最大股
        """
        data = []

        # 完整的双表头正则表达式
        pattern = r'\|\s*(\d+)\s+\|\s*([^|]+?)\s+\|\s*[^|]*\|\s*([-\d.]+)%\s+\|\s*([-\d.]+)([亿万])\s+\|\s*([-\d.]+)%\s+\|\s*([-\d.]+)([亿万])\s+\|\s*([-\d.]+)%\s+\|\s*([-\d.]+)([亿万])\s+\|\s*([-\d.]+)%\s+\|\s*([-\d.]+)([亿万])\s+\|\s*([-\d.]+)%\s+\|\s*([-\d.]+)([亿万])\s+\|\s*([-\d.]+)%\s+\|\s*([^|]+?)\s*\|'

        matches = re.findall(pattern, text)

        for match in matches:
            try:
                def convert_amount(amount, unit):
                    """转换金额单位"""
                    amt = float(amount)
                    if unit == '亿':
                        return amt * 100000000
                    else:  # 万
                        return amt * 10000

                rank = int(match[0])
                name = match[1].strip()
                change_pct = float(match[2])

                # 主力净流入
                main_net = convert_amount(match[3], match[4])
                main_ratio = float(match[5])

                # 超大单净流入
                super_large_net = convert_amount(match[6], match[7])
                super_large_ratio = float(match[8])

                # 大单净流入
                large_net = convert_amount(match[9], match[10])
                large_ratio = float(match[11])

                # 中单净流入
                medium_net = convert_amount(match[12], match[13])
                medium_ratio = float(match[14])

                # 小单净流入
                small_net = convert_amount(match[15], match[16])
                small_ratio = float(match[17])

                # 最大股
                max_stock = match[18].strip()

                data.append({
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'rank': rank,
                    'sector_name': name,
                    'change_pct': change_pct,
                    'main_net_inflow': main_net,
                    'main_net_inflow_ratio': main_ratio,
                    'super_large_net': super_large_net,
                    'super_large_ratio': super_large_ratio,
                    'large_net': large_net,
                    'large_ratio': large_ratio,
                    'medium_net': medium_net,
                    'medium_ratio': medium_ratio,
                    'small_net': small_net,
                    'small_ratio': small_ratio,
                    'max_stock': max_stock
                })
            except (ValueError, IndexError) as e:
                print(f"Warning: Failed to parse row: {e}")
                continue

        return pd.DataFrame(data)

    def sync_fund_flow_from_html(self, html_text):
        """从HTML文本同步板块资金流向数据

        Args:
            html_text: 网页文本内容（由WebReader获取）

        Returns:
            dict: 同步结果
        """
        df = self.parse_fund_flow_table(html_text)

        if df.empty:
            return {
                'status': 'failed',
                'error': 'No data parsed from HTML',
                'count': 0
            }

        # 删除当日旧数据
        today = datetime.now().strftime('%Y-%m-%d')
        self.conn.execute("DELETE FROM sector_fund_flow WHERE date = ?", [today])

        # 插入新数据
        for _, row in df.iterrows():
            self.conn.execute("""
                INSERT INTO sector_fund_flow VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [row['date'], row['rank'], row['sector_name'],
                  row['change_pct'], row['main_net_inflow'], row['main_net_inflow_ratio'],
                  row['super_large_net'], row['super_large_ratio'],
                  row['large_net'], row['large_ratio'],
                  row['medium_net'], row['medium_ratio'],
                  row['small_net'], row['small_ratio'],
                  row['max_stock']])

        return {
            'status': 'success',
            'count': len(df),
            'date': today,
            'top_sector': df.iloc[0]['sector_name'] if len(df) > 0 else None
        }

    def sync_sector_fund_flow(self):
        """同步板块资金流向数据"""
        # 这里需要调用WebReader，暂时返回模拟数据
        # 实际使用时需要通过HTTP请求获取网页内容

        sample_data = """
        | 1 | 煤炭开采 | 详情 | 4.02% | 18.90亿 | 8.24% |
        | 2 | 农化制品 | 详情 | 0.86% | 14.34亿 | 3.47% |
        | 3 | 光学光电子 | 详情 | -0.29% | 12.25亿 | 2.25% |
        """

        df = self.parse_fund_flow_table(sample_data)

        if not df.empty:
            # 写入数据库
            self.conn.execute("CREATE TABLE IF NOT EXISTS sector_fund_flow AS SELECT * FROM df LIMIT 0")
            self.conn.execute("INSERT OR REPLACE INTO sector_fund_flow SELECT * FROM df")

            return {
                'status': 'success',
                'count': len(df),
                'date': datetime.now().strftime('%Y-%m-%d')
            }
        else:
            return {'status': 'failed', 'error': 'No data parsed'}

    def get_sector_fund_flow(self, sector_name=None, date=None, top_n=None):
        """查询板块资金流向数据

        Args:
            sector_name: 板块名称（可选）
            date: 日期（可选）
            top_n: 返回前N名（可选）

        Returns:
            list: 板块数据列表
        """
        query = "SELECT * FROM sector_fund_flow WHERE 1=1"
        params = []

        if sector_name:
            query += " AND sector_name = ?"
            params.append(sector_name)

        if date:
            query += " AND date = ?"
            params.append(date)

        query += " ORDER BY rank"

        if top_n:
            query += f" LIMIT {top_n}"

        if params:
            df = self.conn.execute(query, params).fetchdf()
        else:
            df = self.conn.execute(query).fetchdf()

        return df.to_dict('records')

    def get_top_gainers(self, top_n=10):
        """获取涨幅榜前N名"""
        df = self.conn.execute(f"""
            SELECT * FROM sector_fund_flow
            WHERE date = (SELECT MAX(date) FROM sector_fund_flow)
            ORDER BY change_pct DESC
            LIMIT {top_n}
        """).fetchdf()
        return df.to_dict('records')

    def get_top_inflows(self, top_n=10):
        """获取资金流入前N名"""
        df = self.conn.execute(f"""
            SELECT * FROM sector_fund_flow
            WHERE date = (SELECT MAX(date) FROM sector_fund_flow)
            ORDER BY main_net_inflow DESC
            LIMIT {top_n}
        """).fetchdf()
        return df.to_dict('records')

    def close(self):
        """关闭数据库连接"""
        self.conn.close()


# 全局实例
_crawler = None

def _get_crawler():
    """获取爬虫实例"""
    global _crawler
    if _crawler is None:
        _crawler = EastmoneySectorCrawler()
    return _crawler


def init_db():
    """初始化数据库"""
    crawler = _get_crawler()
    return {'status': 'success', 'message': 'Database initialized'}


def sync_sector_fund_flow_from_html(html_text):
    """从HTML文本同步板块资金流向数据

    Args:
        html_text: 网页文本内容（使用WebReader获取）

    Returns:
        dict: 同步结果
    """
    crawler = _get_crawler()
    return crawler.sync_fund_flow_from_html(html_text)


def sync_sector_fund_flow():
    """同步板块资金流向数据"""
    global _crawler
    if _crawler is None:
        _crawler = EastmoneySectorCrawler()
    return _crawler.sync_sector_fund_flow()


def get_sector_fund_flow(sector_name=None, date=None, top_n=None):
    """获取板块资金流向数据"""
    crawler = _get_crawler()
    return crawler.get_sector_fund_flow(sector_name, date, top_n)


def get_top_gainers(top_n=10):
    """获取涨幅榜前N名"""
    crawler = _get_crawler()
    return crawler.get_top_gainers(top_n)


def get_top_inflows(top_n=10):
    """获取资金流入前N名"""
    crawler = _get_crawler()
    return crawler.get_top_inflows(top_n)


def query_sector_data(sector_name):
    """查询指定板块的完整数据"""
    crawler = _get_crawler()
    fund_flow = crawler.get_sector_fund_flow(sector_name=sector_name)

    return {
        'sector_name': sector_name,
        'data': fund_flow,
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


def batch_update_from_webreader(web_reader_func):
    """批量更新数据（使用WebReader函数）

    Args:
        web_reader_func: WebReader函数，接受URL返回HTML文本

    Returns:
        dict: 更新结果
    """
    url = "https://data.eastmoney.com/bkzj/hy.html"
    html_text = web_reader_func(url)

    return sync_sector_fund_flow_from_html(html_text)

