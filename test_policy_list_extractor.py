"""
政府政策列表提取器
功能：从政府网站提取政策列表（标题、链接、日期）
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from datetime import datetime


class GovPolicyListExtractor:
    """政府政策列表提取器"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

    def extract_policy_list(self, url: str, source_name: str) -> List[Dict]:
        """
        提取政策列表

        Returns:
            [
                {
                    "title": 标题,
                    "link": 链接,
                    "date": 日期,
                    "source": 来源
                }
            ]
        """
        print(f"\n{'='*60}")
        print(f"正在提取: {source_name}")
        print(f"URL: {url}")
        print(f"{'='*60}\n")

        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = response.apparent_encoding

            print(f"✅ 状态码: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ 访问失败: HTTP {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # 根据来源选择不同的解析策略
            if 'gov.cn' in url:
                policies = self._parse_gov_cn(soup, url)
            elif 'ndrc.gov.cn' in url:
                policies = self._parse_ndrc(soup, url)
            else:
                policies = self._parse_generic(soup, url)

            print(f"\n✅ 成功提取 {len(policies)} 条政策\n")
            return policies

        except Exception as e:
            print(f"❌ 错误: {str(e)}\n")
            return []

    def _parse_gov_cn(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """解析中国政府网"""
        policies = []

        # 中国政府网的列表项通常在<ul>或<div>中
        items = soup.select('ul.news_list li') or soup.select('div.list li') or soup.select('li')

        for item in items[:20]:  # 最多取20条
            # 提取标题和链接
            link_tag = item.find('a')
            if not link_tag:
                continue

            title = link_tag.get_text().strip()
            link = link_tag.get('href', '')

            # 补全相对链接
            if link and not link.startswith('http'):
                if link.startswith('/'):
                    link = 'https://www.gov.cn' + link
                else:
                    link = base_url + link

            # 提取日期（通常在span标签中）
            date_tag = item.find('span', class_='date')
            if not date_tag:
                date_tag = item.find('span')
            date = date_tag.get_text().strip() if date_tag else ''

            # 过滤无效数据
            if title and len(title) > 5 and link:
                policies.append({
                    "title": title,
                    "link": link,
                    "date": date,
                    "source": "中国政府网"
                })

        return policies

    def _parse_ndrc(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """解析发改委网站"""
        policies = []

        # 发改委网站的列表项
        items = soup.select('ul.txt-list li') or soup.select('div.list li')

        for item in items[:20]:
            link_tag = item.find('a')
            if not link_tag:
                continue

            title = link_tag.get_text().strip()
            link = link_tag.get('href', '')

            if link and not link.startswith('http'):
                if link.startswith('/'):
                    link = 'https://www.ndrc.gov.cn' + link

            date_tag = item.find('span', class_='date')
            date = date_tag.get_text().strip() if date_tag else ''

            if title and len(title) > 5 and link:
                policies.append({
                    "title": title,
                    "link": link,
                    "date": date,
                    "source": "国家发改委"
                })

        return policies

    def _parse_generic(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """通用解析器"""
        policies = []

        # 查找所有链接
        links = soup.find_all('a', href=True)

        for link_tag in links[:20]:
            title = link_tag.get_text().strip()
            link = link_tag['href']

            # 过滤：只保留政策相关链接
            keywords = ['政策', '通知', '办法', '规定', '意见', '发布']
            if not any(kw in title for kw in keywords):
                continue

            if link and not link.startswith('http'):
                if link.startswith('/'):
                    # 从base_url提取域名
                    from urllib.parse import urlparse
                    parsed = urlparse(base_url)
                    link = f"{parsed.scheme}://{parsed.netloc}{link}"

            if title and len(title) > 10 and link:
                policies.append({
                    "title": title,
                    "link": link,
                    "date": '',
                    "source": "政府网站"
                })

        return policies


def test_policy_extraction():
    """测试政策列表提取"""

    extractor = GovPolicyListExtractor()

    # 测试URL
    test_cases = [
        {
            "name": "中国政府网-最新政策",
            "url": "https://www.gov.cn/zhengce/zuixin/"
        },
    ]

    print("\n" + "="*60)
    print("政府政策列表提取测试")
    print("="*60)

    for test in test_cases:
        policies = extractor.extract_policy_list(test['url'], test['name'])

        if policies:
            print("\n" + "-"*60)
            print("【提取结果】")
            print("-"*60)

            for i, policy in enumerate(policies[:10], 1):  # 只显示前10条
                print(f"\n{i}. {policy['title']}")
                print(f"   日期: {policy['date']}")
                print(f"   链接: {policy['link'][:80]}..." if len(policy['link']) > 80 else f"   链接: {policy['link']}")

            print("-"*60)

    print("\n" + "="*60)
    print("测试完成")
    print("="*60 + "\n")


if __name__ == '__main__':
    test_policy_extraction()
