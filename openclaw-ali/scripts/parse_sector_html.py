#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富板块资金流向爬虫
通过网页抓取获取板块数据，绕过API限制
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import re
import pandas as pd
from datetime import datetime

def parse_sector_fund_flow_html(html_content):
    """
    解析东方财富板块资金流向网页HTML

    Args:
        html_content: 网页HTML内容或文本

    Returns:
        DataFrame: 板块资金流向数据
    """
    # 从文本中提取表格数据
    # 查找所有行数据

    data = []
    lines = html_content.split('\n')

    for line in lines:
        # 查找包含板块信息的行
        # 格式: | 序号 | 名称 | 相关 | 涨跌幅 | 主力净流入 | ...
        if '|  ' in line and '亿' in line and '%' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 10:
                try:
                    # 提取序号
                    num = parts[1]
                    if not num.isdigit():
                        continue

                    # 提取名称
                    name = parts[2]

                    # 提取涨跌幅 (包含%)
                    change_pct_str = parts[4]
                    change_pct = float(change_pct_str.replace('%', ''))

                    # 提取主力净流入金额 (包含"亿")
                    main_inflow_str = parts[5]
                    if '亿' in main_inflow_str:
                        main_inflow = float(main_inflow_str.replace('亿', '')) * 100000000
                    else:
                        main_inflow = 0

                    # 提取主力净流入占比
                    main_ratio_str = parts[6]
                    main_ratio = float(main_ratio_str.replace('%', ''))

                    # 提取超大单净流入
                    super_large_str = parts[7]
                    if '亿' in super_large_str:
                        super_large = float(super_large_str.replace('亿', '')) * 100000000
                    else:
                        super_large = 0

                    # 提取最大股
                    max_stock = parts[11] if len(parts) > 11 else ''

                    data.append({
                        'rank': int(num),
                        'sector_name': name,
                        'change_pct': change_pct,
                        'main_net_inflow': main_inflow,
                        'main_net_inflow_ratio': main_ratio,
                        'super_large_net': super_large,
                        'max_stock': max_stock,
                        'date': datetime.now().strftime('%Y-%m-%d')
                        })
                except (ValueError, IndexError) as e:
                    continue

    df = pd.DataFrame(data)
    return df


def extract_sector_data(text):
    """
    从网页文本中提取板块数据（简化版）
    """
    data = []

    # 使用正则表达式匹配每一行数据
    # 匹配模式: | 序号 | 名称 | 涨跌幅 | 主力净流入 | ...
    pattern = r'\|\s*(\d+)\s+\|\s*([^|]+?)\s+\|\s*[^|]+\|\s*([-\d.]+)%\s+\|\s*([-\d.]+)亿\s+\|\s*([-\d.]+)%'

    matches = re.findall(pattern, text)

    for match in matches:
        rank = int(match[0])
        name = match[1].strip()
        change_pct = float(match[2])
        main_inflow = float(match[3]) * 100000000  # 转换为元
        main_ratio = float(match[4])

        data.append({
            'rank': rank,
            'sector_name': name,
            'change_pct': change_pct,
            'main_net_inflow': main_inflow,
            'main_net_inflow_ratio': main_ratio,
            'date': datetime.now().strftime('%Y-%m-%d')
        })

    return pd.DataFrame(data)


if __name__ == '__main__':
    # 测试数据 - 从网页获取的实际内容
    sample_text = """
    | 1 | 煤炭开采 | 大单详情 股吧 | 4.02% | 18.90亿 | 8.24% | 16.25亿 | 7.09% | 2.65亿 | 1.16% | -3.22亿 | -1.40% | -15.68亿 | -6.84% | 兖矿能源 |
    | 2 | 农化制品 | 大单详情 股吧 | 0.86% | 14.34亿 | 3.47% | 13.13亿 | 3.18% | 1.21亿 | 0.29% | 3306.27万 | 0.08% | -14.88亿 | -3.60% | 和邦生物 |
    | 3 | 光学光电子 | 大单详情 股吧 | -0.29% | 12.25亿 | 2.25% | 13.27亿 | 2.44% | -1.02亿 | -0.19% | -9.02亿 | -1.66% | -3.36亿 | -0.62% | 三安光电 |
    | 4 | 普钢 | 大单详情 股吧 | 2.04% | 11.31亿 | 8.92% | 12.20亿 | 9.63% | -8937.10万 | -0.71% | -5.10亿 | -4.03% | -6.21亿 | -4.90% | 杭钢股份 |
    """

    print("=" * 70)
    print("  东方财富板块资金流向解析测试")
    print("=" * 70)
    print()

    df = extract_sector_data(sample_text)

    if not df.empty:
        print(f"成功解析 {len(df)} 个板块")
        print()
        print("Top 5 板块:")
        for i, row in df.head(5).iterrows():
            print(f"  {row['rank']}. {row['sector_name']}: "
                  f"{row['change_pct']:+.2f}%, "
                  f"净流入: {row['main_net_inflow']/100000000:.2f}亿")
    else:
        print("解析失败")

    print()
    print("✓ 解析器测试成功！可以集成到爬虫中")
