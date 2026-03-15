"""
Tushare Pro 新闻爬虫 - 直接解析HTML
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from bs4 import BeautifulSoup
from datetime import datetime
import re

# 您提供的HTML内容
html_content = """
[请将您提供的HTML内容粘贴到这里]
"""

def parse_tushare_news():
    """解析Tushare Pro新闻HTML"""

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
                'source': 'Tushare Pro'
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

    return news_list


if __name__ == '__main__':
    # 从文件读取HTML（假设您保存了HTML）
    try:
        with open('tushare_news.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        parse_tushare_news()

    except FileNotFoundError:
        print("Please save the HTML to 'tushare_news.html' first")
        print("\nHow to use:")
        print("1. Open https://tushare.pro/news in browser")
        print("2. Right click -> Save Page As...")
        print("3. Save as 'tushare_news.html' in the same directory")
        print("4. Run this script again")
