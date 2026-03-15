"""
Tushare Pro 新闻爬虫 - 测试版
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from bs4 import BeautifulSoup
from datetime import datetime
import re

# 读取保存的HTML文件
try:
    with open('tushare_news.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    news_list = []

    # 查找所有新闻项
    news_items = soup.find_all('div', class_='news_item')

    print("="*60)
    print("Tushare Pro News Parser")
    print("="*60)
    print(f"Found {len(news_items)} news items\n")

    for item in news_items:
        try:
            # 提取时间
            datetime_div = item.find('div', class_='news_datetime')
            time_str = datetime_div.get_text().strip() if datetime_div else ''

            # 提取内容
            content_div = item.find('div', class_='news_content')
            content = content_div.get_text().strip() if content_div else ''

            # 提取标题（内容可能被【】括起来）
            title_match = re.search(r'【(.+?)】', content)
            if title_match:
                title = title_match.group(1)
            else:
                # 取前50个字作为标题
                title = content[:50] + '...' if len(content) > 50 else content

            news_list.append({
                'title': title,
                'content': content,
                'time': time_str,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Tushare Pro - 新浪财经'
            })

        except Exception as e:
            continue

    print(f"Successfully extracted {len(news_list)} news items\n")

    # 显示前20条
    print("-"*60)
    print("[Latest News] (First 20)")
    print("-"*60 + "\n")

    for i, news in enumerate(news_list[:20], 1):
        print(f"{i}. [{news['time']}] {news['title']}")
        print()

    print("-"*60)
    print(f"Total: {len(news_list)} news items")
    print("-"*60 + "\n")

    print("[SUCCESS] Tushare Pro news scraping works!")
    print("\nNext steps:")
    print("1. Fetch news from different sources (雪球, 第一财经, etc.)")
    print("2. Filter by channel (央行, 宏观, 两会, etc.)")
    print("3. Implement auto-update functionality")
    print("4. Save to database")

except FileNotFoundError:
    print("ERROR: tushare_news.html not found")
    print("\nPlease:")
    print("1. Open https://tushare.pro/news in your browser")
    print("2. Save the page (Ctrl+S) as 'tushare_news.html'")
    print("3. Place it in: C:/AI-Agent-Local/")
    print("4. Run this script again")
