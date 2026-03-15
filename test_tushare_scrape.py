"""
爬取Tushare Pro网站新闻
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from datetime import datetime


def scrape_tushare_news():
    """爬取Tushare Pro网站新闻"""

    url = "https://tushare.pro/news"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    print(f"\n{'='*60}")
    print(f"Crawling Tushare Pro News")
    print(f"URL: {url}")
    print(f"{'='*60}\n")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'

        print(f"Status Code: {response.status_code}\n")

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找新闻列表
        news_list = []

        # Tushare Pro的新闻通常在特定的div或ul中
        # 查找所有包含新闻的元素
        news_items = soup.find_all('div', class_='news-item') or \
                     soup.find_all('li', class_='news') or \
                     soup.find_all('article')

        print(f"Found {len(news_items)} potential news items\n")

        # 如果没找到，尝试查找所有链接
        if not news_items:
            all_links = soup.find_all('a', href=True)
            print(f"Total links on page: {len(all_links)}\n")

            for link in all_links:
                title = link.get_text().strip()
                href = link['href']

                # 过滤：保留新闻相关链接
                if len(title) < 10:
                    continue

                if 'news' in href or 'article' in href:
                    # 补全链接
                    if href.startswith('/'):
                        full_link = f"https://tushare.pro{href}"
                    elif not href.startswith('http'):
                        continue
                    else:
                        full_link = href

                    news_list.append({
                        'title': title,
                        'link': full_link,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'Tushare Pro'
                    })

        # 去重
        seen = set()
        unique_news = []
        for news in news_list:
            if news['link'] not in seen:
                seen.add(news['link'])
                unique_news.append(news)

        print(f"Successfully extracted {len(unique_news)} news items\n")

        # 显示前20条
        print("-"*60)
        print("[Latest News] (First 20)")
        print("-"*60 + "\n")

        for i, news in enumerate(unique_news[:20], 1):
            print(f"{i}. {news['title']}")
            print(f"   Date: {news['date']}")
            print(f"   Link: {news['link'][:80]}..." if len(news['link']) > 80 else f"   Link: {news['link']}")
            print()

        print("-"*60)
        print(f"Total: {len(unique_news)} news items")
        print("-"*60 + "\n")

        return unique_news

    except Exception as e:
        print(f"Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return []


if __name__ == '__main__':
    scrape_tushare_news()
