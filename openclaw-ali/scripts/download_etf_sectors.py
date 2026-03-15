#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过板块ETF获取成分股列表
ETF的成分股公开透明，数据稳定可靠
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import time
import re
import json

# 输出目录
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "sector_constituents"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 主要板块ETF列表
SECTOR_ETFS = [
    # 金融类
    {'code': '512880', 'name': '证券ETF', 'sector': '证券'},
    {'code': '512000', 'name': '证券ETF', 'sector': '证券'},
    {'code': '512690', 'name': '酒ETF', 'sector': '白酒'},
    {'code': '159940', 'name': '银行ETF', 'sector': '银行'},

    # 科技类
    {'code': '512480', 'name': '半导体ETF', 'sector': '半导体'},
    {'code': '512760', 'name': '芯片ETF', 'sector': '芯片'},
    {'code': '515000', 'name': '5GETF', 'sector': '5G'},
    {'code': '159994', 'name': '芯片ETF', 'sector': '芯片'},
    {'code': '515880', 'name': '通信ETF', 'sector': '通信'},

    # 医药类
    {'code': '512170', 'name': '医疗ETF', 'sector': '医疗'},
    {'code': '512010', 'name': '医药ETF', 'sector': '医药'},
    {'code': '159992', 'name': '创新药ETF', 'sector': '创新药'},
    {'code': '512290', 'name': '生物医药ETF', 'sector': '生物医药'},

    # 消费类
    {'code': '159928', 'name': '消费ETF', 'sector': '消费'},
    {'code': '512200', 'name': '消费ETF', 'sector': '消费'},

    # 新能源
    {'code': '516160', 'name': '新能源ETF', 'sector': '新能源'},
    {'code': '515030', 'name': '新能源ETF', 'sector': '新能源'},
    {'code': '159806', 'name': '新能源车ETF', 'sector': '新能源汽车'},

    # 军工
    {'code': '512660', 'name': '军工ETF', 'sector': '军工'},
    {'code': '512670', 'name': '国防ETF', 'sector': '国防军工'},

    # 周期类
    {'code': '515220', 'name': '煤炭ETF', 'sector': '煤炭'},
    {'code': '515180', 'name': '有色ETF', 'sector': '有色金属'},
    {'code': '516780', 'name': '钢铁ETF', 'sector': '钢铁'},

    # 其他
    {'code': '512980', 'name': '传媒ETF', 'sector': '传媒'},
    {'code': '512410', 'name': '科技ETF', 'sector': '科技'},
    {'code': '515000', 'name': '5GETF', 'sector': '5G'},
]

def get_etf_holdings(etf_code, etf_name):
    """
    从东方财富获取ETF持仓明细
    URL格式：http://fundf10.eastmoney.com/ccmx_{etf_code}.html
    """
    url = f"http://fundf10.eastmoney.com/ccmx_{etf_code}.html"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'http://fundf10.eastmoney.com/ccmx_{etf_code}.html'
    }

    try:
        # 获取网页
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'

        html = response.text

        # 提取JavaScript中的持仓数据
        # 数据格式通常是：var Data_PositionGather = [...]
        pattern = r'var\s+Data_PositionGather\s*=\s*(\[[\s\S]*?\]);'
        match = re.search(pattern, html)

        if match:
            data_str = match.group(1)
            holdings_data = json.loads(data_str)

            stocks = []
            for item in holdings_data:
                # 提取股票信息
                stock_code = item.get('SDATE', '').split('|')[0] if item.get('SDATE') else ''
                stock_name = item.get('SNAME', '')
                weight = item.get('FREQ', '').replace('%', '') if item.get('FREQ') else '0'
                shares = item.get('ISHARES', '') if item.get('ISHARES') else ''

                if stock_code and stock_name:
                    stocks.append({
                        '代码': stock_code,
                        '名称': stock_name,
                        '权重(%)': float(weight) if weight else 0,
                        '持仓股数': shares,
                        'ETF代码': etf_code,
                        'ETF名称': etf_name,
                        '更新时间': datetime.now().strftime('%Y-%m-%d')
                    })

            return pd.DataFrame(stocks)

        return pd.DataFrame()

    except Exception as e:
        print(f"  ✗ {etf_name}({etf_code}): {e}")
        return pd.DataFrame()

def get_etf_holdings_api(etf_code, etf_name):
    """
    使用东方财富API获取ETF持仓明细（备用方法）
    """
    url = "http://fundf10.eastmoney.com/FundDataPortfolioDistributionNewAJAX.ashx"

    params = {
        'fundcode': etf_code,
        'type': 'ccmx',
        '_': str(int(time.time() * 1000))
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'http://fundf10.eastmoney.com/ccmx_{etf_code}.html'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        # 解析返回的JSON数据
        data = response.json()

        if data and isinstance(data, list):
            stocks = []
            for item in data:
                stock_code = item.get('code', '')
                stock_name = item.get('name', '')
                weight = item.get('weight', '0').replace('%', '') if item.get('weight') else '0'

                if stock_code and stock_name:
                    stocks.append({
                        '代码': stock_code,
                        '名称': stock_name,
                        '权重(%)': float(weight) if weight else 0,
                        'ETF代码': etf_code,
                        'ETF名称': etf_name,
                        '更新时间': datetime.now().strftime('%Y-%m-%d')
                    })

            return pd.DataFrame(stocks)

        return pd.DataFrame()

    except Exception as e:
        print(f"  ✗ {etf_name}({etf_code}): {e}")
        return pd.DataFrame()

def backup_existing_files():
    """备份现有的CSV文件"""
    backup_date = datetime.now().strftime('%Y%m%d')
    backup_count = 0

    for csv_file in OUTPUT_DIR.glob("*_latest.csv"):
        backup_name = f"{csv_file.stem}.backup{backup_date}{csv_file.suffix}"
        backup_path = OUTPUT_DIR / backup_name

        if backup_path.exists():
            continue

        import shutil
        shutil.copy2(csv_file, backup_path)
        print(f"  ✓ 备份: {csv_file.name} -> {backup_name}")
        backup_count += 1

    if backup_count == 0:
        print(f"  ℹ 无需备份（今日已备份或无文件）")

def download_etf_sectors():
    """通过板块ETF下载成分股"""
    print("=" * 70)
    print("  通过板块ETF获取成分股列表")
    print("=" * 70)
    print()

    print(f"准备获取 {len(SECTOR_ETFS)} 个板块ETF的成分股数据")
    print()

    all_stocks = []
    sector_summary = []

    for idx, etf in enumerate(SECTOR_ETFS):
        etf_code = etf['code']
        etf_name = etf['name']
        sector = etf['sector']

        print(f"[{idx+1}/{len(SECTOR_ETFS)}] {sector} - {etf_name}({etf_code})...", end=' ', flush=True)

        # 尝试两种方法获取数据
        df = get_etf_holdings_api(etf_code, etf_name)

        if df.empty:
            df = get_etf_holdings(etf_code, etf_name)

        if not df.empty:
            all_stocks.append(df)
            print(f"✓ {len(df)} 只股票")

            # 记录板块汇总信息
            sector_summary.append({
                '板块名称': sector,
                'ETF代码': etf_code,
                'ETF名称': etf_name,
                '成分股数量': len(df),
                '更新时间': datetime.now().strftime('%Y-%m-%d')
            })
        else:
            print(f"✗ 无数据")

        # 避免请求过快
        time.sleep(0.5)

    if not all_stocks:
        print("\n✗ 未获取到任何成分股数据")
        return None

    # 合并所有数据
    print(f"\n合并数据...")
    df_all = pd.concat(all_stocks, ignore_index=True)

    # 保存完整数据
    output_file = OUTPUT_DIR / f"etf_sectors_{datetime.now().strftime('%Y%m%d')}.csv"
    df_all.to_csv(output_file, index=False, encoding='utf-8-sig')

    latest_file = OUTPUT_DIR / "etf_sectors_latest.csv"
    df_all.to_csv(latest_file, index=False, encoding='utf-8-sig')

    print(f"\n✓ 保存成功:")
    print(f"  - {output_file}")
    print(f"  - {latest_file} (最新版)")

    # 保存板块汇总
    summary_df = pd.DataFrame(sector_summary)
    summary_file = OUTPUT_DIR / f"etf_sectors_summary_{datetime.now().strftime('%Y%m%d')}.csv"
    summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')

    print(f"  - {summary_file} (板块汇总)")
    print(f"\n数据统计:")
    print(f"  - 板块数: {df_all['ETF名称'].nunique()}")
    print(f"  - 股票数: {df_all['代码'].nunique()}")
    print(f"  - 总记录: {len(df_all)}")

    # 显示板块汇总
    print(f"\n板块汇总:")
    print(summary_df.to_string(index=False))

    return df_all

def main():
    """主函数"""
    print()
    print("=" * 70)
    print("  板块ETF成分股下载工具")
    print("=" * 70)
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 备份现有文件
    print("[步骤 0] 备份现有文件...")
    backup_existing_files()
    print()

    # 下载ETF成分股
    download_etf_sectors()

    print()
    print("=" * 70)
    print("  ✓ 下载完成!")
    print("=" * 70)
    print()
    print("说明:")
    print("  1. 通过板块ETF获取成分股，数据来源公开透明")
    print("  2. 每个ETF代表一个行业/主题板块")
    print("  3. 权重数据反映了成分股在板块中的重要性")
    print("  4. 建议每月更新一次")
    print()

if __name__ == '__main__':
    main()
