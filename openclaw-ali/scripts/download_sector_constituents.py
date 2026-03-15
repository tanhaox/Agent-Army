#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富板块成分股下载 - 使用公开API接口
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import re
import time

# 输出目录
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "sector_constituents"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_sector_list(sector_type='dy'):
    """
    获取板块列表
    sector_type: dy=行业, gn=概念
    """
    url = "http://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': 1,
        'pz': 500,
        'po': 1,
        'np': 1,
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': 2,
        'invt': 2,
        'fid': 'f3',  # 涨跌幅排序
        'fs': f'b:{sector_type}BK0900',  # 行业/概念板块
        'fields': 'f12,f14',  # 板块代码,板块名称
        '_': str(int(time.time() * 1000))
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'http://data.eastmoney.com/bkzj/hy.html'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get('data') and data['data'].get('diff'):
            sectors = []
            for item in data['data']['diff']:
                sectors.append({
                    '板块代码': item.get('f12', ''),
                    '板块名称': item.get('f14', '')
                })

            return pd.DataFrame(sectors)
        return pd.DataFrame()
    except Exception as e:
        print(f"✗ 获取板块列表失败: {e}")
        return pd.DataFrame()

def get_sector_constituents(sector_code, sector_name):
    """获取指定板块的成分股"""
    url = "http://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': 1,
        'pz': 2000,  # 每个板块最多2000只股票
        'po': 1,
        'np': 1,
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': 2,
        'invt': 2,
        'fid': 'f62',  # 最新价排序
        'fs': f'm:{int(sector_code)}+t:{sector_code}',  # 板块成分股
        'fields': 'f12,f13,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205',  # 股票代码,名称,价格等
        '_': str(int(time.time() * 1000))
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'http://data.eastmoney.com/bkzj/hy.html'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get('data') and data['data'].get('diff'):
            stocks = []
            for item in data['data']['diff']:
                stock_code = item.get('f12', '')
                market = item.get('13', 0)  # 0=深圳, 1=上海

                # 格式化股票代码
                if market == 1:
                    full_code = f"{stock_code}.SH" if stock_code[:3] in ['688', '601', '603', '605'] else stock_code
                else:
                    full_code = f"{stock_code}.SZ" if stock_code[:2] in ['00', '30'] else stock_code

                stocks.append({
                    '代码': stock_code,
                    '名称': item.get('f14', ''),
                    '最新价': item.get('f2', 0) / 100 if item.get('f2') else 0,
                    '涨跌幅': item.get('f3', 0) / 100 if item.get('f3') else 0,
                    '板块名称': sector_name,
                    '板块代码': sector_code,
                    '更新时间': datetime.now().strftime('%Y-%m-%d')
                })

            return pd.DataFrame(stocks)
        return pd.DataFrame()
    except Exception as e:
        print(f"  ✗ {sector_name}: {e}")
        return pd.DataFrame()

def backup_existing_files():
    """备份现有的CSV文件"""
    backup_date = datetime.now().strftime('%Y%m%d')
    backup_count = 0

    for csv_file in OUTPUT_DIR.glob("*_latest.csv"):
        backup_name = f"{csv_file.stem}.backup{backup_date}{csv_file.suffix}"
        backup_path = OUTPUT_DIR / backup_name

        # 如果备份已存在，跳过
        if backup_path.exists():
            continue

        # 复制文件
        import shutil
        shutil.copy2(csv_file, backup_path)
        print(f"  ✓ 备份: {csv_file.name} -> {backup_name}")
        backup_count += 1

    if backup_count == 0:
        print(f"  ℹ 无需备份（今日已备份或无文件）")

def download_industry_sectors():
    """下载行业板块成分股"""
    print("=" * 70)
    print("  下载行业板块成分股（使用公开API）")
    print("=" * 70)
    print()

    # 1. 获取行业板块列表
    print("[1/3] 获取行业板块列表...")
    sectors_df = get_sector_list('dy')

    if sectors_df.empty:
        print("✗ 未获取到板块列表")
        return None

    print(f"✓ 找到 {len(sectors_df)} 个行业板块")
    print(f"  示例: {', '.join(sectors_df.head(5)['板块名称'].tolist())}")
    print()

    # 2. 获取每个板块的成分股
    print(f"[2/3] 获取板块成分股...")
    all_stocks = []

    for idx, row in sectors_df.iterrows():
        sector_name = row['板块名称']
        sector_code = row['板块代码']

        print(f"  [{idx+1}/{len(sectors_df)}] {sector_name}...", end=' ', flush=True)

        stocks_df = get_sector_constituents(sector_code, sector_name)

        if not stocks_df.empty:
            all_stocks.append(stocks_df)
            print(f"✓ {len(stocks_df)} 只股票")
        else:
            print(f"✗ 无数据")

        # 避免请求过快
        time.sleep(0.1)

    if not all_stocks:
        print("\n✗ 未获取到任何成分股数据")
        return None

    # 3. 合并并保存
    print(f"\n[3/3] 保存数据...")
    df = pd.concat(all_stocks, ignore_index=True)

    # 保存为CSV
    output_file = OUTPUT_DIR / f"industry_sectors_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    # 同时保存一份最新版本（固定文件名）
    latest_file = OUTPUT_DIR / "industry_sectors_latest.csv"
    df.to_csv(latest_file, index=False, encoding='utf-8-sig')

    print(f"\n✓ 保存成功:")
    print(f"  - {output_file}")
    print(f"  - {latest_file} (最新版)")
    print(f"\n数据统计:")
    print(f"  - 板块数: {df['板块名称'].nunique()}")
    print(f"  - 股票数: {df['代码'].nunique()}")
    print(f"  - 总记录: {len(df)}")

    return df

def main():
    """主函数"""
    print()
    print("=" * 70)
    print("  东方财富板块成分股下载工具 v2")
    print("=" * 70)
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 备份现有文件
    print("[步骤 0] 备份现有文件...")
    backup_existing_files()
    print()

    # 下载行业板块
    industry_df = download_industry_sectors()

    print()
    print("=" * 70)
    print("  ✓ 下载完成!")
    print("=" * 70)
    print()
    print("提示:")
    print("  1. 板块成分股变化很慢，建议每周或每月更新一次")
    print("  2. CSV文件可用Excel直接打开")
    print("  3. 可导入DuckDB/SQLite进行查询")
    print()

if __name__ == '__main__':
    main()
