"""
Tushare Pro 新闻爬虫 - 使用Cookie
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json

def scrape_tushare_with_cookie():
    """使用Cookie爬取Tushare Pro新闻"""

    print("="*60)
    print("Tushare Pro News Scraper (with Cookie)")
    print("="*60)
    print("\n[1/4] Setting up request with cookie...\n")

    # 用户提供Cookie
    cookie = 'uid="2|1:0|10:1773285186|3:uid|12:MTAxNjY1NA==|afb938f4200448d1cf591d21cb4bd80a35bd3c3b087f4c27e041c9a3819dc8c8"; username=2|1:0|10:1773285186|8:username|12:MTM0KioqNTUy|222f214d539962e529bdf7cc055d3ed59d7ef8ad13c700aaff2fafa7bbf3ea77; session-id=f2b1682f-14f6-4f74-b5cd-16a302e0cd24'

    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cookie': cookie,
        'Referer': 'https://tushare.pro/'
    }

    try:
        print("[2/4] Requesting Tushare Pro news page...")

        response = requests.get(
            'https://tushare.pro/news',
            headers=headers,
            timeout=15
        )

        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)} characters\n")

        if response.status_code != 200:
            print(f"ERROR: Failed to fetch page")
            return []

        print("[3/4] Parsing news data...")

        soup = BeautifulSoup(response.text, 'html.parser')

        news_list = []

        # 查找所有新闻项
        news_items = soup.find_all('div', class_='news_item')

        print(f"Found {len(news_items)} news items\n")

        for item in news_items:
            try:
                # 提取时间
                datetime_div = item.find('div', class_='news_datetime')
                time_str = datetime_div.get_text().strip() if datetime_div else ''

                # 提取内容
                content_div = item.find('div', class_='news_content')
                content = content_div.get_text().strip() if content_div else ''

                if not content:
                    continue

                # 提取标题
                title_match = re.search(r'【(.+?)】', content)
                if title_match:
                    title = title_match.group(1)
                else:
                    title = content[:50] + '...' if len(content) > 50 else content

                news_list.append({
                    'title': title,
                    'content': content,
                    'time': time_str,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'source': 'Tushare Pro',
                    'url': 'https://tushare.pro/news'
                })

            except Exception as e:
                continue

        print(f"[4/4] Successfully extracted {len(news_list)} news items\n")

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

        # 保存到JSON文件
        output_file = 'C:/AI-Agent-Local/tushare_news_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(news_list, f, ensure_ascii=False, indent=2)

        print(f"[SUCCESS] News data saved to: {output_file}")
        print(f"\nTotal items: {len(news_list)}")

        return news_list

    except Exception as e:
        print(f"\n[ERROR] {str(e)}\n")
        import traceback
        traceback.print_exc()
        return []


if __name__ == '__main__':
    scrape_tushare_with_cookie()
