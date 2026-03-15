# -*- coding: utf-8 -*-
"""
测试不同股票代码的数据获取
"""
import akshare as ak
from datetime import datetime
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

end_date = datetime.now().strftime('%Y%m%d')

# 测试股票列表
test_stocks = [
    {
        'name': '中国电建',
        'code': '601669',
        'exchange': '上海证券交易所',
        'industry': '建筑装饰'
    },
    {
        'name': '贵州茅台',
        'code': '600519',
        'exchange': '上海证券交易所',
        'industry': '食品饮料'
    },
    {
        'name': '比亚迪',
        'code': '002594',
        'exchange': '深圳证券交易所',
        'industry': '汽车'
    },
    {
        'name': '宁德时代',
        'code': '300750',
        'exchange': '深圳证券交易所(创业板)',
        'industry': '电池'
    },
    {
        'name': '工商银行',
        'code': '601398',
        'exchange': '上海证券交易所',
        'industry': '银行'
    },
]

print('=' * 80)
print('多只股票历史数据获取测试')
print('=' * 80)
print()

results = []

for stock in test_stocks:
    print(f'正在测试: {stock["name"]} ({stock["code"]})')
    print(f'交易所: {stock["exchange"]}')
    print(f'所属行业: {stock["industry"]}')
    print('-' * 80)

    try:
        # 获取历史数据
        df = ak.stock_zh_a_hist(
            symbol=stock['code'],
            period='daily',
            start_date='20250201',
            end_date=end_date,
            adjust='qfq'
        )

        if df is not None and len(df) > 0:
            latest = df.iloc[-1]

            print(f'[OK] 成功获取 {len(df)} 条数据')
            print()
            print(f'最新交易日: {latest["日期"]}')
            print(f'  收盘价: {latest["收盘"]:.2f} 元')
            print(f'  涨跌幅: {latest["涨跌幅"]:.2f}%')
            print(f'  成交量: {latest["成交量"]/10000:.1f} 万手')
            print(f'  成交额: {latest["成交额"]/100000000:.2f} 亿元')
            print(f'  换手率: {latest["换手率"]:.2f}%')

            results.append({
                'name': stock['name'],
                'code': stock['code'],
                'status': 'OK',
                'count': len(df),
                'price': latest['收盘'],
                'change': latest['涨跌幅']
            })
        else:
            print(f'[FAIL] 数据为空')
            results.append({
                'name': stock['name'],
                'code': stock['code'],
                'status': 'FAIL',
                'count': 0,
                'price': 0,
                'change': 0
            })

    except Exception as e:
        print(f'[FAIL] 获取失败: {e}')
        results.append({
            'name': stock['name'],
            'code': stock['code'],
            'status': 'ERROR',
            'count': 0,
            'price': 0,
            'change': 0
        })

    print()

# 汇总结果
print('=' * 80)
print('测试结果汇总')
print('=' * 80)
print()
print(f'{'股票名称':<12} {'代码':<8} {'状态':<8} {'数据量':<8} {'最新价':<10} {'涨跌幅':<8}')
print('-' * 80)

for r in results:
    status_mark = '[OK]' if r['status'] == 'OK' else '[FAIL]'
    if r['status'] == 'OK':
        print(f'{r["name"]:<12} {r["code"]:<8} {status_mark:<8} {r["count"]:>6} 条   {r["price"]:>8.2f}   {r["change"]:>6.2f}%')
    else:
        print(f'{r["name"]:<12} {r["code"]:<8} {status_mark:<8} {'-':>6}       {'-':>8}    {'-':>6}')

print()
print('=' * 80)
