#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雅虎财经数据同步工具 - OpenClaw Skill
提供K线数据和个股信息的同步功能
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# 设置UTF-8输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(SCRIPT_DIR))

import duckdb

# 数据库路径（支持从skill目录或openclaw-ali目录运行）
def get_db_path():
    """获取数据库路径"""
    # 尝试多个可能的位置
    possible_paths = [
        # 如果skill在openclaw-ali/skills下
        Path(__file__).parent.parent.parent / 'data' / 'stock_market_v2.db',
        # 如果skill在~/.openclaw/skills下
        Path(__file__).parent.parent / 'data' / 'stock_market_v2.db',
        # 绝对路径（开发环境）
        Path('C:/AI-Agent-Local/openclaw-ali/data/stock_market_v2.db'),
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # 默认路径（可能不存在）
    return Path(__file__).parent.parent.parent / 'data' / 'stock_market_v2.db'

DB_PATH = get_db_path()

def sync_yahoo_kline(code, name, exchange, period='1mo'):
    """
    同步雅虎财经K线数据

    Args:
        code: 股票代码（如 "600519"）
        name: 股票名称（如 "贵州茅台"）
        exchange: 交易所代码（"SS" 或 "SZ"）
        period: 时间范围（默认 "1mo"）

    Returns:
        dict: 同步结果
    """
    try:
        # 导入yfinance
        try:
            import yfinance as yf
        except ImportError:
            os.system('pip install yfinance -q')
            import yfinance as yf

        # 获取数据
        ticker_code = f'{code}.{exchange}'
        ticker = yf.Ticker(ticker_code)
        df = ticker.history(period=period)

        if df is None or len(df) == 0:
            return {
                "status": "error",
                "message": f"{name} 无数据",
                "code": code
            }

        # 连接数据库
        con = duckdb.connect(str(DB_PATH))
        inserted = 0

        for idx, row in df.iterrows():
            date_str = idx.strftime('%Y-%m-%d')

            # 计算涨跌幅
            pct_change = None
            if idx != df.index[0]:
                prev_close = df.loc[df.index[df.index.get_loc(idx) - 1], 'Close']
                pct_change = (row['Close'] - prev_close) / prev_close * 100

            # DELETE + INSERT
            con.execute('DELETE FROM stock_kline_unified WHERE source = ? AND code = ? AND date = ?',
                       ('yahoo', code, date_str))

            con.execute('''
                INSERT INTO stock_kline_unified
                (source, source_type, code, name, date, time,
                 open, high, low, close, adj_close, volume,
                 dividends, stock_splits, pct_change, turnover_rate, amount,
                 pe_ratio, market_cap,
                 main_net_inflow, super_large_net_inflow, large_net_inflow,
                 medium_net_inflow, small_net_inflow,
                 crawl_time, crawl_url, crawl_status,
                 data_quality, completeness, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'yahoo', 'api', code, name, date_str, None,
                row['Open'], row['High'], row['Low'], row['Close'],
                row.get('Adj Close'), int(row['Volume']) if row['Volume'] else None,
                row['Dividends'], row['Stock Splits'], pct_change,
                None, None, None, None,
                None, None, None, None, None,
                None, None, None,
                'good', 100.0, datetime.now(), datetime.now()
            ))
            inserted += 1

        con.close()

        return {
            "status": "success",
            "message": f"{name} K线数据同步完成",
            "code": code,
            "inserted": inserted,
            "period": period
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"{name} K线数据同步失败: {str(e)}",
            "code": code
        }

def sync_yahoo_info(code, name, exchange):
    """
    同步雅虎财经个股信息

    Args:
        code: 股票代码
        name: 股票名称
        exchange: 交易所代码

    Returns:
        dict: 同步结果
    """
    try:
        # 导入yfinance
        try:
            import yfinance as yf
        except ImportError:
            os.system('pip install yfinance -q')
            import yfinance as yf

        # 获取信息
        ticker_code = f'{code}.{exchange}'
        ticker = yf.Ticker(ticker_code)
        info = ticker.info

        if info is None or len(info) == 0:
            return {
                "status": "error",
                "message": f"{name} 无个股信息",
                "code": code
            }

        # 连接数据库
        con = duckdb.connect(str(DB_PATH))

        # 删除旧记录
        con.execute('DELETE FROM stock_info_unified WHERE code = ?', (code,))

        # 插入新记录（简化版，只包含关键字段）
        now = datetime.now()

        # 统计有效字段
        valid_count = sum(1 for v in [
            info.get('shortName'), info.get('longName'), info.get('industry'),
            info.get('sector'), info.get('marketCap'), info.get('trailingPE'),
            info.get('totalRevenue'), info.get('dividendRate'), info.get('beta')
        ] if v is not None)

        con.execute('''
            INSERT INTO stock_info_unified (
                code, source, source_type,
                name, short_name, long_name, industry, sector,
                market_cap, trailing_pe, forward_pe, price_to_book,
                total_revenue, profit_margins, operating_margins,
                dividend_rate, dividend_yield, payout_ratio,
                beta, average_volume,
                fifty_two_week_low, fifty_two_week_high,
                target_high_price, target_low_price, target_mean_price,
                recommendation_key,
                created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        ''', (
            code,
            'yahoo',
            'api',
            info.get('shortName') or name,
            info.get('shortName'),
            info.get('longName'),
            info.get('industry'),
            info.get('sector'),
            info.get('marketCap'),
            info.get('trailingPE'),
            info.get('forwardPE'),
            info.get('priceToBook'),
            info.get('totalRevenue'),
            info.get('profitMargins'),
            info.get('operatingMargins'),
            info.get('dividendRate'),
            info.get('dividendYield'),
            info.get('payoutRatio'),
            info.get('beta'),
            info.get('averageVolume'),
            info.get('fiftyTwoWeekLow'),
            info.get('fiftyTwoWeekHigh'),
            info.get('targetHighPrice'),
            info.get('targetLowPrice'),
            info.get('targetMeanPrice'),
            info.get('recommendationKey'),
            now,
            now
        ))

        con.close()

        return {
            "status": "success",
            "message": f"{name} 个股信息同步完成",
            "code": code,
            "valid_fields": valid_count
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"{name} 个股信息同步失败: {str(e)}",
            "code": code
        }

def sync_yahoo_complete():
    """
    同步默认股票列表的K线和个股信息

    Returns:
        dict: 同步结果
    """
    try:
        # 导入同步脚本
        import sync_yahoo_complete as sync_module

        # 执行主函数（会捕获输出）
        import io
        import contextlib

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            sync_module.main()

        return {
            "status": "success",
            "message": "完整版同步完成",
            "output": output.getvalue()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"完整版同步失败: {str(e)}"
        }

def query_stock_data(sql):
    """
    查询股票数据

    Args:
        sql: SQL查询语句

    Returns:
        dict: 查询结果
    """
    try:
        if not DB_PATH.exists():
            return {
                "status": "error",
                "message": "数据库不存在"
            }

        con = duckdb.connect(str(DB_PATH))
        result = con.execute(sql).fetchall()
        con.close()

        # 获取列名
        columns = [desc[0] for desc in con.execute(sql).description]

        # 转换为字典列表
        rows = []
        for row in result:
            row_dict = {}
            for i, val in enumerate(row):
                if val is not None and isinstance(val, float):
                    row_dict[columns[i]] = round(val, 2)
                else:
                    row_dict[columns[i]] = val
            rows.append(row_dict)

        return {
            "status": "success",
            "columns": columns,
            "rows": rows,
            "count": len(rows)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"查询失败: {str(e)}"
        }

# 命令行接口
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法:")
        print("  python tool.py sync_kline <code> <name> <exchange> [period]")
        print("  python tool.py sync_info <code> <name> <exchange>")
        print("  python tool.py sync_complete")
        print("  python tool.py query <sql>")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'sync_kline':
        if len(sys.argv) < 5:
            print("错误: 缺少参数")
            print("用法: python tool.py sync_kline <code> <name> <exchange> [period]")
            sys.exit(1)

        code = sys.argv[2]
        name = sys.argv[3]
        exchange = sys.argv[4]
        period = sys.argv[5] if len(sys.argv) > 5 else '1mo'

        result = sync_yahoo_kline(code, name, exchange, period)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == 'sync_info':
        if len(sys.argv) < 5:
            print("错误: 缺少参数")
            print("用法: python tool.py sync_info <code> <name> <exchange>")
            sys.exit(1)

        code = sys.argv[2]
        name = sys.argv[3]
        exchange = sys.argv[4]

        result = sync_yahoo_info(code, name, exchange)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == 'sync_complete':
        result = sync_yahoo_complete()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == 'query':
        if len(sys.argv) < 3:
            print("错误: 缺少SQL语句")
            print("用法: python tool.py query <sql>")
            sys.exit(1)

        sql = sys.argv[2]
        result = query_stock_data(sql)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        print(f"错误: 未知命令 '{command}'")
        sys.exit(1)
