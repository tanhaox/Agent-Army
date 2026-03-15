"""
Tushare Pro 新闻爬虫
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime
import re


def scrape_tushare_news_html(html_content: str) -> List[Dict]:
    """解析Tushare Pro新闻HTML"""

    soup = BeautifulSoup(html_content, 'html.parser')

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

            # 提取标题（内容可能被【】括起来）
            title_match = re.search(r'【(.+?)】', content)
            if title_match:
                title = title_match.group(1)
                summary = content
            else:
                # 取前50个字作为标题
                title = content[:50] + '...' if len(content) > 50 else content
                summary = content

            news_list.append({
                'title': title,
                'content': summary,
                'time': time_str,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Tushare Pro - 新浪财经',
                'url': 'https://tushare.pro/news/sina'
            })

        except Exception as e:
            continue

    return news_list


def test_tushare_news():
    """测试Tushare Pro新闻爬取"""

    # 从文件读取HTML（您提供的HTML）
    html_file = 'C:/AI-Agent-Local/tushare_news.html'

    # 如果您想直接用URL，可以取消下面的注释
    # url = "https://tushare.pro/news"
    # headers = {'User-Agent': 'Mozilla/5.0'}
    # response = requests.get(url, headers=headers)
    # html_content = response.text

    # 读取您提供的HTML
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    print("="*60)
    print("Tushare Pro News Scraper")
    print("="*60 + "\n")

    news_list = scrape_tushare_news_html(html_content)

    print(f"Successfully extracted {len(news_list)} news items\n")

    # 显示前20条
    print("-"*60)
    print("[Latest News] (First 20)")
    print("-"*60 + "\n")

    for i, news in enumerate(news_list[:20], 1):
        print(f"{i}. [{news['time']}] {news['title']}")
        print(f"    {news['content'][:100]}...")
        print()

    print("-"*60)
    print(f"Total: {len(news_list)} news items")
    print("-"*60 + "\n")

    # 按频道分类
    print("\n[Channel Analysis]")
    print("-"*60)

    # 这里可以添加更多频道的支持
    channels = ['央行', '宏观', '两会', '市场', '行业']
    for channel in channels:
        print(f"Channel: {channel}")

    return news_list


if __name__ == '__main__':
    # 先保存您的HTML到文件
    html_content = """[您提供的HTML内容]"""

    # 保存到文件
    with open('tushare_news.html', 'w', encoding='utf-8') as f:
        # 这里需要您提供的完整HTML
        pass

    test_tushare_news()
