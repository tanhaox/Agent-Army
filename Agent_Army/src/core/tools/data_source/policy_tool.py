"""
政策工具 - 统一管理政策和新闻数据获取
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3
import requests
from bs4 import BeautifulSoup
import re

from src.core.logger import get_logger


class PolicyTool:
    """
    政策工具

    职责：
    - 从多个数据源获取政策和新闻
    - 提供统一的搜索接口
    - 数据本地缓存和去重
    - 供 AI Agent 调用

    数据源：
    - Tushare Pro: 财经新闻（1000条）
    - 中国政府网: 政策文件（1020条）
    - 国家发改委: 政策文件（56条）
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("policy_tool")
        self.config = config or {}

        # 数据库路径
        self.db_path = self.config.get('db_path', 'C:/AI-Agent-Local/policy_news.db')

        # Tushare Cookie
        self.tushare_cookie = self.config.get(
            'tushare_cookie',
            'uid="2|1:0|10:1773285186|3:uid|12:MTAxNjY1NA==|afb938f4200448d1cf591d21cb4bd80a35bd3c3b087f4c27e041c9a3819dc8c8"; username=2|1:0|10:1773285186|8:username|12:MTM0KioqNTUy|222f214d539962e529bdf7cc055d3ed59d7ef8ad13c700aaff2fafa7bbf3ea77; session-id=f2b1682f-14f6-4f74-b5cd-16a302e0cd24'
        )

        # 初始化数据库
        self._init_db()

        self.logger.info("政策工具初始化完成")

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

    def search_policies(
        self,
        keyword: str,
        limit: int = 20,
        source: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索政策/新闻

        Args:
            keyword: 搜索关键词
            limit: 结果数量限制
            source: 数据源过滤（Tushare Pro/中国政府网/国家发改委）
            category: 分类过滤（政策/财经）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）

        Returns:
            标准化的政策列表:
            [
                {
                    "title": "政策标题",
                    "content": "内容摘要",
                    "source": "Tushare Pro",
                    "category": "财经",
                    "url": "https://...",
                    "publish_date": "2026-03-15"
                }
            ]
        """
        self.logger.info(f"搜索政策: {keyword}, 限制{limit}条")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 构建查询
        conditions = []
        params = []

        if keyword:
            conditions.append("(title LIKE ? OR content LIKE ?)")
            params.extend([f'%{keyword}%', f'%{keyword}%'])

        if source:
            conditions.append("source LIKE ?")
            params.append(f'%{source}%')

        if category:
            conditions.append("category = ?")
            params.append(category)

        if start_date:
            conditions.append("publish_date >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("publish_date <= ?")
            params.append(end_date)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f'''
            SELECT title, content, source, category, url, publish_date
            FROM policies
            WHERE {where_clause}
            ORDER BY publish_date DESC, id DESC
            LIMIT ?
        '''

        params.append(limit)

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        policies = []
        for row in results:
            policies.append({
                "title": row[0],
                "content": row[1],
                "source": row[2],
                "category": row[3],
                "url": row[4],
                "publish_date": row[5]
            })

        self.logger.info(f"找到{len(policies)}条结果")

        return policies

    def get_latest_policies(
        self,
        limit: int = 20,
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取最新政策

        Args:
            limit: 结果数量限制
            source: 数据源过滤

        Returns:
            最新的政策列表
        """
        self.logger.info(f"获取最新政策: {limit}条")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = '''
            SELECT title, content, source, category, url, publish_date
            FROM policies
        '''

        params = []

        if source:
            query += " WHERE source LIKE ?"
            params.append(f'%{source}%')

        query += " ORDER BY publish_date DESC, id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        policies = []
        for row in results:
            policies.append({
                "title": row[0],
                "content": row[1],
                "source": row[2],
                "category": row[3],
                "url": row[4],
                "publish_date": row[5]
            })

        return policies

    def get_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息

        Returns:
            {
                "total": 1919,
                "by_source": {"Tushare Pro": 843, ...},
                "by_category": {"财经": 843, ...},
                "latest_date": "2026-03-15"
            }
        """
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
            "total": total,
            "by_source": by_source,
            "by_category": by_category,
            "latest_date": latest_date
        }

    def fetch_tushare_news(self) -> List[Dict]:
        """获取Tushare Pro新闻"""
        self.logger.info("获取Tushare Pro新闻...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': self.tushare_cookie,
            'Referer': 'https://tushare.pro/'
        }

        try:
            response = requests.get('https://tushare.pro/news', headers=headers, timeout=15)

            if response.status_code != 200:
                self.logger.error(f"HTTP {response.status_code}")
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

            self.logger.info(f"获取到{len(policies)}条Tushare新闻")
            return policies

        except Exception as e:
            self.logger.error(f"获取Tushare新闻失败: {str(e)}")
            return []

    def fetch_gov_policies(self) -> List[Dict]:
        """获取中国政府网政策（JSON）"""
        self.logger.info("获取中国政府网政策...")

        try:
            response = requests.get(
                'https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json',
                timeout=15
            )

            if response.status_code != 200:
                self.logger.error(f"HTTP {response.status_code}")
                return []

            data = response.json()

            policies = []
            for item in data:
                policies.append({
                    'title': item.get('TITLE', '').strip(),
                    'content': item.get('TITLE', ''),
                    'source': '中国政府网',
                    'category': '政策',
                    'url': item.get('URL', ''),
                    'publish_date': item.get('DOCRELPUBTIME', '')
                })

            self.logger.info(f"获取到{len(policies)}条政府网政策")
            return policies

        except Exception as e:
            self.logger.error(f"获取政府网政策失败: {str(e)}")
            return []

    def fetch_ndrc_policies(self) -> List[Dict]:
        """获取发改委政策"""
        self.logger.info("获取发改委政策...")

        try:
            url = 'https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                self.logger.error(f"HTTP {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            ul_list = soup.find('ul', class_='u-list')

            if not ul_list:
                self.logger.warning("未找到新闻列表")
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

            self.logger.info(f"获取到{len(policies)}条发改委政策")
            return policies

        except Exception as e:
            self.logger.error(f"获取发改委政策失败: {str(e)}")
            return []

    def save_to_db(self, policies: List[Dict]) -> int:
        """保存到数据库（自动去重）"""
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
                self.logger.warning(f"保存失败: {policy['title'][:30]}...")

        conn.commit()
        conn.close()

        return saved_count

    def update_all_sources(self) -> Dict[str, int]:
        """
        更新所有数据源

        Returns:
            {
                "tushare": 1000,
                "gov": 1020,
                "ndrc": 56,
                "total_new": 1919
            }
        """
        self.logger.info("开始更新所有数据源...")

        all_policies = []

        # 1. Tushare Pro
        tushare_news = self.fetch_tushare_news()
        all_policies.extend(tushare_news)

        # 2. 中国政府网
        gov_policies = self.fetch_gov_policies()
        all_policies.extend(gov_policies)

        # 3. 发改委
        ndrc_policies = self.fetch_ndrc_policies()
        all_policies.extend(ndrc_policies)

        # 保存到数据库
        saved = self.save_to_db(all_policies)

        return {
            "tushare": len(tushare_news),
            "gov": len(gov_policies),
            "ndrc": len(ndrc_policies),
            "total_new": saved
        }


# ========== 便捷函数 ==========

def search_policies(keyword: str, limit: int = 20) -> List[Dict]:
    """
    搜索政策（便捷函数）

    Args:
        keyword: 搜索关键词
        limit: 结果数量限制

    Returns:
        政策列表
    """
    tool = PolicyTool()
    return tool.search_policies(keyword, limit)


def get_latest_policies(limit: int = 20) -> List[Dict]:
    """
    获取最新政策（便捷函数）

    Args:
        limit: 结果数量限制

    Returns:
        最新的政策列表
    """
    tool = PolicyTool()
    return tool.get_latest_policies(limit)


def get_policy_stats() -> Dict[str, Any]:
    """
    获取统计信息（便捷函数）

    Returns:
        统计信息
    """
    tool = PolicyTool()
    return tool.get_stats()
