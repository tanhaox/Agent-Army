"""
Tushare Pro 新闻爬虫 - 改进版（带滚动）
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

def scrape_tushare_news_selenium():
    """使用Selenium爬取Tushare Pro新闻（改进版）"""

    print("="*60)
    print("Tushare Pro News Scraper (Selenium + Scroll)")
    print("="*60)
    print("\n[1/5] Initializing Chrome driver...\n")

    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    try:
        driver = webdriver.Chrome(options=chrome_options)

        print("[2/5] Loading Tushare Pro news page...")
        driver.get('https://tushare.pro/news')

        print("Waiting for initial page load...")
        time.sleep(8)  # 等待JavaScript渲染

        print("[3/5] Scrolling to load more news...")

        # 滚动页面加载更多内容
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            print(f"  Scroll {i+1}/5 completed")

        print("\n[4/5] Extracting news data...")

        # 获取页面HTML
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

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
                    'source': 'Tushare Pro'
                })

            except Exception as e:
                continue

        print(f"[5/5] Successfully extracted {len(news_list)} news items\n")

        # 显示前20条
        if len(news_list) > 0:
            print("-"*60)
            print("[Latest News] (First 20)")
            print("-"*60 + "\n")

            for i, news in enumerate(news_list[:20], 1):
                print(f"{i}. [{news['time']}] {news['title']}")
                print()

        print("-"*60)
        print(f"Total: {len(news_list)} news items")
        print("-"*60 + "\n")

        if len(news_list) > 0:
            print("[SUCCESS] Tushare Pro news scraping completed!")
        else:
            print("[WARNING] No news items found. The page structure may have changed.")

        # 关闭浏览器
        driver.quit()

        return news_list

    except Exception as e:
        print(f"\n[ERROR] {str(e)}\n")
        import traceback
        traceback.print_exc()
        return []


if __name__ == '__main__':
    scrape_tushare_news_selenium()
