"""
测试Yahoo Finance对A股的支持情况
"""
import sys
import io
from pathlib import Path

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.tools.data_source.yahoo_tool import YahooFinanceTool

print('=' * 70)
print('Yahoo Finance A股数据测试')
print('=' * 70)

tool = YahooFinanceTool()

if not tool.is_available():
    print('[错误] yfinance未安装')
    print('请运行: pip install yfinance')
    exit(1)

print('[OK] Yahoo Finance工具初始化成功\n')

# ========== 测试1: 股票信息 ==========
print('[1/4] 测试股票基本信息获取: 601669.SS (中国电建)')
print('-' * 70)
info = tool.get_stock_info('601669.SS')

if 'error' not in info:
    print('[成功] 获取到股票信息')
    print(f'  公司名称: {info.get("name")}')
    print(f'  市值: {info.get("market_cap"):,.0f}' if info.get('market_cap') else '  市值: N/A')
    print(f'  行业: {info.get("industry")}')
    print(f'  板块: {info.get("sector")}')
    print(f'  前收盘: {info.get("previous_close")}')
    print(f'  52周变化: {info.get("52_week_change", 0):.2f}%')
else:
    print(f'[失败] {info["error"]}')

# ========== 测试2: 历史K线 ==========
print('\n[2/4] 测试历史K线数据: 601669.SS (最近5天)')
print('-' * 70)
hist = tool.get_historical_data('601669.SS', period='5d', interval='1d')

if not hist.empty:
    print(f'[成功] 获取到 {len(hist)} 条K线记录')
    print(f'  列名: {list(hist.columns)}')
    print(f'  最新数据:')
    for idx, row in hist.tail(2).iterrows():
        print(f'    {idx.strftime("%Y-%m-%d")}: 开{row["Open"]:.2f} 高{row["High"]:.2f} 低{row["Low"]:.2f} 收{row["Close"]:.2f} 量{row["Volume"]:,.0f}')
else:
    print('[失败] 未获取到数据')

# ========== 测试3: 实时行情 ==========
print('\n[3/4] 测试实时行情: 601669.SS')
print('-' * 70)
quote = tool.get_realtime_quote('601669.SS')

if 'error' not in quote:
    print('[成功] 获取到实时行情')
    print(f'  当前价格: {quote.get("current_price", 0):.2f}')
    print(f'  涨跌额: {quote.get("change", 0):.2f}')
    print(f'  涨跌幅: {quote.get("change_percent", 0):.2f}%')
    print(f'  开盘: {quote.get("open", 0):.2f}')
    print(f'  最高: {quote.get("high", 0):.2f}')
    print(f'  最低: {quote.get("low", 0):.2f}')
    print(f'  成交量: {quote.get("volume", 0):,.0f}')
else:
    print(f'[失败] {quote["error"]}')

# ========== 测试4: 财务报表 ==========
print('\n[4/4] 测试财务报表: 601669.SS')
print('-' * 70)
financials = tool.get_financial_statements('601669.SS')

if 'error' not in financials:
    print('[成功] 获取到财务报表')

    if financials.get('income_statement'):
        stmt = financials['income_statement']
        print(f'  利润表: {stmt["shape"][0]}行 x {stmt["shape"][1]}列')
        print(f'    最近数据示例: {stmt["data"][0] if stmt["data"] else "N/A"}')

    if financials.get('balance_sheet'):
        stmt = financials['balance_sheet']
        print(f'  资产负债表: {stmt["shape"][0]}行 x {stmt["shape"][1]}列')

    if financials.get('cash_flow'):
        stmt = financials['cash_flow']
        print(f'  现金流量表: {stmt["shape"][0]}行 x {stmt["shape"][1]}列')
else:
    print(f'[失败] {financials["error"]}')

# ========== 总结 ==========
print('\n' + '=' * 70)
print('测试总结')
print('=' * 70)

tests = [
    ('股票基本信息', 'error' not in info),
    ('历史K线数据', not hist.empty),
    ('实时行情', 'error' not in quote),
    ('财务报表', 'error' not in financials)
]

for name, passed in tests:
    status = '[OK]' if passed else '[FAIL]'
    print(f'{status} {name}')

print('\n结论: Yahoo Finance对A股支持' + ('良好' if all(p for _, p in tests) else '有限'))
print('=' * 70)
