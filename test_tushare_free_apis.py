"""
测试Tushare可用接口
"""

import os
import sys
sys.path.insert(0, 'C:/AI-Agent-Local/Agent_Army')

# 加载.env文件
env_path = 'C:/AI-Agent-Local/Agent_Army/.env'
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('TUSHARE_API_KEY='):
                api_key = line.split('=', 1)[1]
                os.environ['TUSHARE_API_KEY'] = api_key
                break

import tushare as ts

api_key = os.getenv("TUSHARE_API_KEY")
pro = ts.pro_api(api_key)

print("="*60)
print("Testing Tushare Free APIs")
print("="*60)
print()

# 测试一些常见的免费接口
test_apis = [
    ("Trade Calendar", lambda: pro.trade_cal(exchange='SSE', start_date='20260301', end_date='20260315')),
    ("Stock List", lambda: pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name')),
    ("Market Data", lambda: pro.daily(ts_code='000001.SZ', start_date='20260301', end_date='20260315')),
]

for name, api_func in test_apis:
    print(f"Testing: {name}")
    print("-"*40)
    try:
        df = api_func()
        print(f"SUCCESS! Got {len(df)} records")
        print(f"Columns: {list(df.columns)[:5]}...")
        print()
    except Exception as e:
        error_msg = str(e)
        if "积分" in error_msg:
            print(f"NEEDS POINTS - Not available")
        else:
            print(f"ERROR: {error_msg[:100]}")
        print()

print("="*60)
print("Test Complete")
print("="*60)
