#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Eastmoney Sector Fund Flow API"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time

print("=" * 70)
print("  Test Eastmoney Sector Fund Flow API")
print("=" * 70)
print()

# 东方财富板块资金流向API（推测）
url = "http://push2.eastmoney.com/api/qt/stock/hsxn/get"

params = {
    'fields1': 'f1,f2,f3,f4,f5',
    'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63',
    'ut': 'b5d3aa7fa1faa494a146b95f47cd8957',
    '_': str(int(time.time() * 1000))
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print(f"Testing API: {url}")
print(f"Params: {params}")
print()

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print()

    if response.status_code == 200:
        data = response.json()
        print("Response Keys:", list(data.keys()))
        print()

        if 'data' in data and 'diff' in data['data']:
            sectors = data['data']['diff']
            print(f"Got {len(sectors)} sectors")
            print()

            # Find construction sector
            for sector in sectors[:5]:
                print(f"  {sector}")
        else:
            print("Unexpected response structure")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
    else:
        print(f"Request failed: {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
