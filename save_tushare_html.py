"""
保存Tushare Pro新闻页面HTML
"""

import requests

url = "https://tushare.pro/news"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

response = requests.get(url, headers=headers, timeout=15)
response.encoding = 'utf-8'

# 保存到文件
with open('tushare_news_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)

print(f"HTML saved to: tushare_news_page.html")
print(f"File size: {len(response.text)} characters")
print(f"\nFirst 2000 characters:")
print("="*80)
print(response.text[:2000])
print("="*80)
