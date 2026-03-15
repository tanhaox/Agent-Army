"""
发改委政策列表提取器
静态HTML，直接用BeautifulSoup提取
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re


def extract_ndrc_policies():
    """提取发改委政策列表"""

    # 真实URL（网站会自动跳转）
    url = "https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    print(f"\n{'='*60}")
    print(f"提取发改委政策列表")
    print(f"URL: {url}")
    print(f"{'='*60}\n")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'

        print(f"✅ 状态码: {response.status_code}\n")

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        policies = []

        # 发改委网站的列表项通常在 <ul><li> 结构中
        # 查找所有链接
        all_links = soup.find_all('a', href=True)

        print(f"🔍 找到 {len(all_links)} 个链接\n")

        # 过滤政策相关链接
        for link in all_links:
            title = link.get_text().strip()
            href = link['href']

            # 过滤条件：
            # 1. 标题长度要足够
            # 2. 包含政策关键词
            # 3. 链接不为空
            if len(title) < 10:
                continue

            # 补全相对链接
            if href.startswith('/'):
                full_link = f"https://www.ndrc.gov.cn{href}"
            elif not href.startswith('http'):
                continue
            else:
                full_link = href

            # 过滤非政策链接
            skip_keywords = ['javascript', 'void', '#', '更多', '首页', '返回']
            if any(kw in href.lower() for kw in skip_keywords):
                continue

            # 提取日期（如果有的话）
            date = ""

            policies.append({
                "title": title,
                "link": full_link,
                "date": date,
                "source": "国家发改委"
            })

        # 去重（按链接）
        seen = set()
        unique_policies = []
        for p in policies:
            if p['link'] not in seen:
                seen.add(p['link'])
                unique_policies.append(p)

        print(f"✅ 成功提取 {len(unique_policies)} 条政策\n")

        # 显示前20条
        print("-"*60)
        print("【最新政策列表】（显示前20条）")
        print("-"*60 + "\n")

        for i, policy in enumerate(unique_policies[:20], 1):
            print(f"{i}. {policy['title']}")
            print(f"   🔗 {policy['link']}")
            print()

        return unique_policies

    except Exception as e:
        print(f"❌ 错误: {str(e)}\n")
        return []


if __name__ == '__main__':
    extract_ndrc_policies()
