# -*- coding: utf-8 -*-
"""
平安银行历史数据字段详解
"""
import akshare as ak
from datetime import datetime
import sys

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

end_date = datetime.now().strftime('%Y%m%d')
df = ak.stock_zh_a_hist(
    symbol='000001',
    period='daily',
    start_date='20250201',
    end_date=end_date,
    adjust='qfq'
)

latest = df.iloc[-1]

print('=' * 80)
print('平安银行(000001)历史数据字段详解')
print('=' * 80)
print()
print(f'数据期间: {df["日期"].min()} 至 {df["日期"].max()}')
print(f'数据条数: {len(df)} 条')
print()

# 按类别分组
groups = {
    '基本信息': ['日期', '股票代码'],
    '价格数据': ['开盘', '收盘', '最高', '最低'],
    '成交数据': ['成交量', '成交额'],
    '行情指标': ['振幅', '涨跌幅', '涨跌额', '换手率']
}

for group_name, fields in groups.items():
    print('=' * 80)
    print(f'【{group_name}】')
    print('=' * 80)
    print()

    for field in fields:
        if field in df.columns:
            value = latest[field]
            value_type = type(value).__name__

            print(f'字段名: {field}')
            print(f'数据类型: {value_type}')

            # 根据字段类型给出详细说明
            if field == '日期':
                print(f'说明: 交易日期')
                print(f'示例: {value}')
            elif field == '股票代码':
                print(f'说明: 深交所股票代码，6位数字')
                print(f'示例: {value}')
            elif field == '开盘':
                print(f'说明: 当日开盘价（元）')
                print(f'示例: {value:.2f} 元')
            elif field == '收盘':
                print(f'说明: 当日收盘价（元）')
                print(f'示例: {value:.2f} 元')
            elif field == '最高':
                print(f'说明: 当日最高价（元）')
                print(f'示例: {value:.2f} 元')
            elif field == '最低':
                print(f'说明: 当日最低价（元）')
                print(f'示例: {value:.2f} 元')
            elif field == '成交量':
                print(f'说明: 当日成交股票数量（手）')
                print(f'示例: {value:,.0f} 手 = {value/10000:.1f} 万手')
            elif field == '成交额':
                print(f'说明: 当日成交金额（元）')
                print(f'示例: {value:,.0f} 元 = {value/100000000:.2f} 亿元')
            elif field == '振幅':
                print(f'说明: (最高价-最低价)/昨收价*100%')
                print(f'示例: {value:.2f}%')
                print(f'计算: ({latest["最高"]:.2f}-{latest["最低"]:.2f})/{df.iloc[-2]["收盘"]:.2f}*100%')
            elif field == '涨跌幅':
                print(f'说明: (收盘价-昨收价)/昨收价*100%')
                print(f'示例: {value:.2f}%')
                if len(df) > 1:
                    yesterday_close = df.iloc[-2]['收盘']
                    change = (latest['收盘'] - yesterday_close) / yesterday_close * 100
                    print(f'计算: ({latest["收盘"]:.2f}-{yesterday_close:.2f})/{yesterday_close:.2f}*100% = {change:.2f}%')
            elif field == '涨跌额':
                print(f'说明: 收盘价-昨收价')
                print(f'示例: {value:.2f} 元')
                if len(df) > 1:
                    yesterday_close = df.iloc[-2]['收盘']
                    change_amt = latest['收盘'] - yesterday_close
                    print(f'计算: {latest["收盘"]:.2f} - {yesterday_close:.2f} = {change_amt:.2f} 元')
            elif field == '换手率':
                print(f'说明: 成交量/流通股本*100%')
                print(f'示例: {value:.2f}%')
                print(f'含义: 反映股票流通性强弱，换手率越高说明交易越活跃')

            print()

print('=' * 80)
print('完整示例数据（最新5个交易日）')
print('=' * 80)
print()
print(df.tail(5).to_string())
