"""
Tushare Pro 新闻爬虫 - 使用Selenium自动获取
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import time

def scrape_tushare_news_selenium():
    """使用Selenium爬取Tushare Pro新闻"""

    print("="*60)
    print("Tushare Pro News Scraper (Selenium)")
    print("="*60)
    print("\n[1/4] Initializing Chrome driver...\n")

    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    try:
        # 启动Chrome
        driver = webdriver.Chrome(options=chrome_options)

        print("[2/4] Loading Tushare Pro news page...")
        driver.get('https://tushare.pro/news')

        # 等待页面加载
        print("Waiting for page to load...")
        time.sleep(5)  # 等待JavaScript渲染

        # 等待新闻内容加载
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'news_item'))
            )
            print("Page loaded successfully!\n")
        except:
            print("Warning: News items not found, but continuing...\n")

        print("[3/4] Extracting news data...")

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

                # 提取标题（内容可能被【】括起来）
                import re
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

        print("[SUCCESS] Tushare Pro news scraping completed!")

        # 关闭浏览器
        driver.quit()

        return news_list

    except Exception as e:
        print(f"\n[ERROR] {str(e)}\n")
        print("\nPossible solutions:")
        print("1. Install Chrome browser")
        print("2. Install ChromeDriver")
        print("3. Or use requests + BeautifulSoup (see alternative method)")
        return []


if __name__ == '__main__':
    scrape_tushare_news_selenium()
