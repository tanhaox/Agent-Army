"""
Tushare Pro 新闻聚合工具
支持10个新闻源和多个子分类
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
import sqlite3

from src.core.logger import get_logger


class TushareNewsAggregator:
    """
    Tushare Pro 新闻聚合工具

    支持10个新闻源：
    1. 雪球（7×24）
    2. 第一财经（快讯）
    3. 凤凰（全部）
    4. 同花顺（7*24小时全球直播）
    5. 金融界（7×24）
    6. 新浪财经（11个子分类）
    7. 云财经
    8. 财联社（5个子分类）
    9. 东方财富（7×24）
    10. 华尔街见闻（10个子分类）
    """

    # 新闻源配置
    NEWS_SOURCES = {
        'xq': {
            'name': '雪球',
            'url': 'https://tushare.pro/news/xq',
            'description': '7×24小时'
        },
        'yicai': {
            'name': '第一财经',
            'url': 'https://tushare.pro/news/yicai',
            'description': '快讯'
        },
        'fenghuang': {
            'name': '凤凰',
            'url': 'https://tushare.pro/news/fenghuang',
            'description': '全部'
        },
        'fenghuang10jqka': {
            'name': '同花顺',
            'url': 'https://tushare.pro/news/fenghuang10jqka',
            'description': '7*24小时全球直播'
        },
        'jinrongjie': {
            'name': '金融界',
            'url': 'https://tushare.pro/news/jinrongjie',
            'description': '7×24'
        },
        'sina': {
            'name': '新浪财经',
            'url': 'https://tushare.pro/news/sina',
            'description': '其他',
            'categories': [
                '国际', '宏观', '公司', '市场', '焦点',
                '行业', '两会', '观点', '数据', '原创', '央行'
            ]
        },
        'yuncaijing': {
            'name': '云财经',
            'url': 'https://tushare.pro/news/yuncaijing',
            'description': ''
        },
        'cls': {
            'name': '财联社',
            'url': 'https://tushare.pro/news/cls',
            'description': '',
            'categories': ['基金', '港美股', '公司', '看盘', '提醒']
        },
        'eastmoney': {
            'name': '东方财富',
            'url': 'https://tushare.pro/news/eastmoney',
            'description': '7×24'
        },
        'wallstreetcn': {
            'name': '华尔街见闻',
            'url': 'https://tushare.pro/news/wallstreetcn',
            'description': '要闻',
            'categories': [
                '要闻', 'A股', '美股', '石油', '外汇',
                '金融', '债券', '黄金', '港股', '大宗'
            ]
        }
    }

    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("tushare_news_aggregator")
        self.config = config or {}

        # Cookie
        self.cookie = self.config.get(
            'tushare_cookie',
            'uid="2|1:0|10:1773285186|3:uid|12:MTAxNjY1NA==|afb938f4200448d1cf591d21cb4bd80a35bd3c3b087f4c27e041c9a3819dc8c8"; username=2|1:0|10:1773285186|8:username|12:MTM0KioqNTUy|222f214d539962e529bdf7cc055d3ed59d7ef8ad13c700aaff2fafa7bbf3ea77; session-id=f2b1682f-14f6-4f74-b5cd-16a302e0cd24'
        )

        # 数据库路径
        self.db_path = self.config.get('db_path', 'C:/AI-Agent-Local/tushare_news.db')

        # 初始化数据库
        self._init_db()

        self.logger.info("Tushare新闻聚合工具初始化完成")

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建表（增强版，包含源和分类）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tushare_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                source TEXT NOT NULL,
                category TEXT,
                url TEXT,
                publish_time TEXT,
                crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(title, source, category, publish_time)
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON tushare_news(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON tushare_news(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_publish_time ON tushare_news(publish_time)')

        conn.commit()
        conn.close()

    def fetch_news(
        self,
        source: str = 'all',
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取新闻

        Args:
            source: 新闻源代码（如 'sina', 'cls'）或 'all'
            category: 子分类（如 '宏观', 'A股'）
            limit: 获取数量限制

        Returns:
            新闻列表
        """
        self.logger.info(f"获取新闻: source={source}, category={category}, limit={limit}")

        all_news = []

        # 获取所有源或指定源
        sources = [source] if source != 'all' else list(self.NEWS_SOURCES.keys())

        for src in sources:
            if src not in self.NEWS_SOURCES:
                self.logger.warning(f"未知的新闻源: {src}")
                continue

            # 获取该源的新闻
            news = self._fetch_from_source(src, category, limit)
            all_news.extend(news)

        self.logger.info(f"总共获取 {len(all_news)} 条新闻")

        return all_news

    def _fetch_from_source(
        self,
        source: str,
        category: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """从指定源获取新闻"""
        source_config = self.NEWS_SOURCES[source]

        # 构建URL
        url = source_config['url']
        if category and category in source_config.get('categories', []):
            url = f"{url}#{category}"

        # 发送请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': self.cookie,
            'Referer': 'https://tushare.pro/'
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                self.logger.error(f"HTTP {response.status_code}: {url}")
                return []

            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找新闻项
            news_items = soup.find_all('div', class_='news_item')

            news_list = []
            for item in news_items[:limit]:
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
                    title = title_match.group(1) if title_match else content[:50]

                    news_list.append({
                        'title': title,
                        'content': content,
                        'source': source_config['name'],
                        'category': category or '',
                        'url': url,
                        'publish_time': time_str or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })

                except Exception as e:
                    self.logger.warning(f"解析新闻项失败: {str(e)}")
                    continue

            self.logger.info(f"{source_config['name']}: 获取到 {len(news_list)} 条新闻")

            return news_list

        except Exception as e:
            self.logger.error(f"获取 {source} 新闻失败: {str(e)}")
            return []

    def search_news(
        self,
        keyword: str,
        source: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        搜索新闻

        Args:
            keyword: 搜索关键词
            source: 过滤源
            category: 过滤分类
            limit: 结果数量

        Returns:
            搜索结果
        """
        self.logger.info(f"搜索新闻: {keyword}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 构建查询
        conditions = ["(title LIKE ? OR content LIKE ?)"]
        params = [f'%{keyword}%', f'%{keyword}%']

        if source:
            conditions.append("source = ?")
            params.append(source)

        if category:
            conditions.append("category = ?")
            params.append(category)

        query = f'''
            SELECT title, content, source, category, url, publish_time
            FROM tushare_news
            WHERE {' AND '.join(conditions)}
            ORDER BY publish_time DESC, id DESC
            LIMIT ?
        '''

        params.append(limit)

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        news_list = []
        for row in results:
            news_list.append({
                'title': row[0],
                'content': row[1],
                'source': row[2],
                'category': row[3],
                'url': row[4],
                'publish_time': row[5]
            })

        self.logger.info(f"找到 {len(news_list)} 条结果")

        return news_list

    def save_to_db(self, news_list: List[Dict]) -> int:
        """保存到数据库"""
        if not news_list:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0

        for news in news_list:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO tushare_news
                    (title, content, source, category, url, publish_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    news['title'],
                    news.get('content', ''),
                    news['source'],
                    news.get('category', ''),
                    news.get('url', ''),
                    news.get('publish_time', '')
                ))

                if cursor.rowcount > 0:
                    saved_count += 1

            except Exception as e:
                self.logger.warning(f"保存失败: {news['title'][:30]}...")

        conn.commit()
        conn.close()

        return saved_count

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 总数
        cursor.execute('SELECT COUNT(*) FROM tushare_news')
        total = cursor.fetchone()[0]

        # 按源统计
        cursor.execute('SELECT source, COUNT(*) as count FROM tushare_news GROUP BY source')
        by_source = dict(cursor.fetchall())

        # 按分类统计
        cursor.execute('SELECT category, COUNT(*) as count FROM tushare_news WHERE category != "" GROUP BY category')
        by_category = dict(cursor.fetchall())

        # 最新时间
        cursor.execute('SELECT MAX(publish_time) FROM tushare_news')
        latest_time = cursor.fetchone()[0]

        conn.close()

        return {
            'total': total,
            'by_source': by_source,
            'by_category': by_category,
            'latest_time': latest_time
        }

    def get_available_sources(self) -> Dict[str, Any]:
        """获取可用的新闻源列表"""
        sources = {}

        for code, config in self.NEWS_SOURCES.items():
            sources[code] = {
                'name': config['name'],
                'description': config['description'],
                'categories': config.get('categories', []),
                'url': config['url']
            }

        return sources

    def fetch_all_sources(self, limit_per_source: int = 50) -> Dict[str, int]:
        """
        获取所有新闻源的数据

        Args:
            limit_per_source: 每个源获取的数量

        Returns:
            {源代码: 获取数量}
        """
        self.logger.info("开始获取所有新闻源...")

        results = {}
        all_news = []

        for source in self.NEWS_SOURCES.keys():
            # 获取主分类
            news = self._fetch_from_source(source, None, limit_per_source)
            all_news.extend(news)
            results[source] = len(news)

            # 获取子分类
            categories = self.NEWS_SOURCES[source].get('categories', [])
            for category in categories:
                cat_news = self._fetch_from_source(source, category, limit_per_source)
                all_news.extend(cat_news)
                results[f"{source}#{category}"] = len(cat_news)

        # 保存到数据库
        saved = self.save_to_db(all_news)

        self.logger.info(f"总共获取 {len(all_news)} 条，保存 {saved} 条新数据")

        results['total'] = len(all_news)
        results['saved'] = saved

        return results


# ========== 便捷函数 ==========

def fetch_tushare_news(source: str = 'all', limit: int = 50) -> List[Dict]:
    """
    获取Tushare新闻（便捷函数）

    Args:
        source: 新闻源（'all' 或具体源代码）
        limit: 获取数量

    Returns:
        新闻列表
    """
    aggregator = TushareNewsAggregator()
    return aggregator.fetch_news(source=source, limit=limit)


def search_tushare_news(keyword: str, limit: int = 50) -> List[Dict]:
    """
    搜索Tushare新闻（便捷函数）

    Args:
        keyword: 搜索关键词
        limit: 结果数量

    Returns:
        搜索结果
    """
    aggregator = TushareNewsAggregator()
    return aggregator.search_news(keyword, limit=limit)


def get_tushare_stats() -> Dict[str, Any]:
    """
    获取统计信息（便捷函数）

    Returns:
        统计信息
    """
    aggregator = TushareNewsAggregator()
    return aggregator.get_stats()
