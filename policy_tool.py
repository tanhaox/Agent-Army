"""
PolicyTool - 政策新闻数据采集工具
功能：从多个数据源获取政策和新闻，支持搜索、导出
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import sqlite3
import re
from typing import List, Dict, Optional
import os


class PolicyTool:
    """政策新闻数据采集工具"""

    def __init__(self, db_path: str = None):
        """初始化PolicyTool"""
        self.db_path = db_path or 'C:/AI-Agent-Local/policy_news.db'
        self.tushare_cookie = 'uid="2|1:0|10:1773285186|3:uid|12:MTAxNjY1NA==|afb938f4200448d1cf591d21cb4bd80a35bd3c3b087f4c27e041c9a3819dc8c8"; username=2|1:0|10:1773285186|8:username|12:MTM0KioqNTUy|222f214d539962e529bdf7cc055d3ed59d7ef8ad13c700aaff2fafa7bbf3ea77; session-id=f2b1682f-14f6-4f74-b5cd-16a302e0cd24'

        # 初始化数据库
        self._init_db()

        print("[SUCCESS] PolicyTool initialized")
        print(f"Database: {self.db_path}")

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                source TEXT NOT NULL,
                category TEXT,
                url TEXT,
                publish_date TEXT,
                crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(title, source, publish_date)
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON policies(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON policies(publish_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON policies(title)')

        conn.commit()
        conn.close()

    def fetch_tushare_news(self) -> List[Dict]:
        """获取Tushare Pro新闻"""
        print("\n[1/3] Fetching Tushare Pro news...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': self.tushare_cookie,
            'Referer': 'https://tushare.pro/'
        }

        try:
            response = requests.get('https://tushare.pro/news', headers=headers, timeout=15)

            if response.status_code != 200:
                print(f"ERROR: HTTP {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.find_all('div', class_='news_item')

            policies = []
            for item in news_items:
                try:
                    datetime_div = item.find('div', class_='news_datetime')
                    time_str = datetime_div.get_text().strip() if datetime_div else ''

                    content_div = item.find('div', class_='news_content')
                    content = content_div.get_text().strip() if content_div else ''

                    if not content:
                        continue

                    title_match = re.search(r'【(.+?)】', content)
                    title = title_match.group(1) if title_match else content[:50]

                    policies.append({
                        'title': title,
                        'content': content,
                        'source': 'Tushare Pro',
                        'category': '财经',
                        'url': 'https://tushare.pro/news',
                        'publish_date': datetime.now().strftime('%Y-%m-%d')
                    })

                except:
                    continue

            print(f"[SUCCESS] Fetched {len(policies)} news items")
            return policies

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return []

    def fetch_gov_policies(self) -> List[Dict]:
        """获取中国政府网政策（JSON）"""
        print("\n[2/3] Fetching Gov.cn policies...")

        try:
            response = requests.get('https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json', timeout=15)

            if response.status_code != 200:
                print(f"ERROR: HTTP {response.status_code}")
                return []

            data = response.json()

            policies = []
            for item in data:
                policies.append({
                    'title': item.get('TITLE', '').strip(),
                    'content': item.get('TITLE', ''),  # 标题作为内容
                    'source': '中国政府网',
                    'category': '政策',
                    'url': item.get('URL', ''),
                    'publish_date': item.get('DOCRELPUBTIME', '')
                })

            print(f"[SUCCESS] Fetched {len(policies)} policy items")
            return policies

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return []

    def fetch_ndrc_policies(self) -> List[Dict]:
        """获取发改委政策"""
        print("\n[3/3] Fetching NDRC policies...")

        try:
            url = 'https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                print(f"ERROR: HTTP {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            ul_list = soup.find('ul', class_='u-list')

            if not ul_list:
                print("[WARNING] News list not found")
                return []

            items = ul_list.find_all('li')
            policies = []

            for item in items:
                link_tag = item.find('a', href=True)
                if not link_tag:
                    continue

                title = link_tag.get_text().strip()
                href = link_tag['href']

                if href.startswith('./'):
                    full_link = f"https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/{href[2:]}"
                elif href.startswith('../'):
                    full_link = f"https://www.ndrc.gov.cn/xxgk/zcfb/{href[3:]}"
                else:
                    continue

                # 提取日期
                date_match = re.search(r'(\d{6})/t(\d{8})', href)
                date = f"{date_match.group(2)[:4]}-{date_match.group(2)[4:6]}-{date_match.group(2)[6:8]}" if date_match else ''

                policies.append({
                    'title': title,
                    'content': title,
                    'source': '国家发改委',
                    'category': '政策',
                    'url': full_link,
                    'publish_date': date
                })

            print(f"[SUCCESS] Fetched {len(policies)} policy items")
            return policies

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return []

    def save_to_db(self, policies: List[Dict]) -> int:
        """保存到数据库"""
        if not policies:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0

        for policy in policies:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO policies (title, content, source, category, url, publish_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    policy['title'],
                    policy.get('content', ''),
                    policy['source'],
                    policy.get('category', ''),
                    policy.get('url', ''),
                    policy.get('publish_date', '')
                ))

                if cursor.rowcount > 0:
                    saved_count += 1

            except Exception as e:
                print(f"[WARNING] Failed to save: {policy['title'][:30]}...")

        conn.commit()
        conn.close()

        return saved_count

    def search(self, keyword: str, limit: int = 50) -> List[Dict]:
        """搜索政策/新闻"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT title, content, source, category, url, publish_date
            FROM policies
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY publish_date DESC, id DESC
            LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', limit))

        results = cursor.fetchall()

        conn.close()

        policies = []
        for row in results:
            policies.append({
                'title': row[0],
                'content': row[1],
                'source': row[2],
                'category': row[3],
                'url': row[4],
                'publish_date': row[5]
            })

        return policies

    def export_to_json(self, output_file: str = 'policies_export.json'):
        """导出为JSON"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT title, content, source, category, url, publish_date
            FROM policies
            ORDER BY publish_date DESC, id DESC
        ''')

        policies = []
        for row in cursor.fetchall():
            policies.append({
                'title': row[0],
                'content': row[1],
                'source': row[2],
                'category': row[3],
                'url': row[4],
                'publish_date': row[5]
            })

        conn.close()

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(policies, f, ensure_ascii=False, indent=2)

        print(f"[SUCCESS] Exported {len(policies)} items to {output_file}")
        return len(policies)

    def get_stats(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 总数
        cursor.execute('SELECT COUNT(*) FROM policies')
        total = cursor.fetchone()[0]

        # 按来源统计
        cursor.execute('SELECT source, COUNT(*) as count FROM policies GROUP BY source')
        by_source = dict(cursor.fetchall())

        # 按分类统计
        cursor.execute('SELECT category, COUNT(*) as count FROM policies GROUP BY category')
        by_category = dict(cursor.fetchall())

        # 最新日期
        cursor.execute('SELECT MAX(publish_date) FROM policies')
        latest_date = cursor.fetchone()[0]

        conn.close()

        return {
            'total': total,
            'by_source': by_source,
            'by_category': by_category,
            'latest_date': latest_date
        }


def test_policy_tool():
    """测试PolicyTool"""

    print("="*60)
    print("PolicyTool - 政策新闻数据采集工具")
    print("="*60)

    # 初始化
    tool = PolicyTool()

    # 获取所有数据
    all_policies = []

    # 1. Tushare Pro
    tushare_news = tool.fetch_tushare_news()
    all_policies.extend(tushare_news)

    # 2. 中国政府网
    gov_policies = tool.fetch_gov_policies()
    all_policies.extend(gov_policies)

    # 3. 发改委
    ndrc_policies = tool.fetch_ndrc_policies()
    all_policies.extend(ndrc_policies)

    print("\n" + "="*60)
    print(f"Total fetched: {len(all_policies)} items")
    print("="*60 + "\n")

    # 保存到数据库
    print("Saving to database...")
    saved = tool.save_to_db(all_policies)
    print(f"Saved {saved} new items\n")

    # 显示统计
    stats = tool.get_stats()
    print("[Database Statistics]")
    print("-"*60)
    print(f"Total items: {stats['total']}")
    print(f"Latest date: {stats['latest_date']}")
    print(f"\nBy source:")
    for source, count in stats['by_source'].items():
        print(f"  {source}: {count}")
    print(f"\nBy category:")
    for category, count in stats['by_category'].items():
        print(f"  {category}: {count}")
    print("-"*60 + "\n")

    # 测试搜索
    print("[Testing Search]")
    print("-"*60)
    results = tool.search('央行', limit=5)
    print(f"Found {len(results)} items for '央行':\n")

    for i, item in enumerate(results, 1):
        print(f"{i}. {item['title']}")
        print(f"   来源: {item['source']}")
        print(f"   日期: {item['publish_date']}")
        print()

    print("="*60)
    print("[SUCCESS] PolicyTool test completed!")
    print("="*60)


if __name__ == '__main__':
    test_policy_tool()
