"""
发改委政策列表提取器 - 正确版本
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

        # 找到列表容器
        ul_list = soup.find('ul', class_='u-list')

        if not ul_list:
            print("❌ 未找到列表容器")
            return []

        # 提取所有列表项
        items = ul_list.find_all('li')

        print(f"🔍 找到 {len(items)} 个列表项\n")

        for item in items:
            # 查找链接
            link_tag = item.find('a', href=True)
            if not link_tag:
                continue

            title = link_tag.get_text().strip()
            href = link_tag['href']

            # 补全相对链接
            if href.startswith('./'):
                full_link = f"https://www.ndrc.gov.cn/xxgk/zcfb/fzggwl/{href[2:]}"
            elif href.startswith('../'):
                full_link = f"https://www.ndrc.gov.cn/xxgk/zcfb/{href[3:]}"
            elif href.startswith('/'):
                full_link = f"https://www.ndrc.gov.cn{href}"
            else:
                full_link = href

            # 提取日期（从文件名中，如 202602/t20260211_xxx.html）
            date_match = re.search(r'(\d{6})/t(\d{8})', href)
            if date_match:
                date_str = date_match.group(2)  # 20260211
                # 转换为 2026-02-11 格式
                date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                date = ""

            policies.append({
                "title": title,
                "link": full_link,
                "date": date,
                "source": "国家发改委"
            })

        print(f"✅ 成功提取 {len(policies)} 条政策\n")

        # 显示前20条
        print("-"*60)
        print("【最新政策列表】（显示前20条）")
        print("-"*60 + "\n")

        for i, policy in enumerate(policies[:20], 1):
            print(f"{i}. {policy['title']}")
            if policy['date']:
                print(f"   📅 {policy['date']}")
            print(f"   🔗 {policy['link']}")
            print()

        print("-"*60)
        print(f"✅ 共 {len(policies)} 条政策")
        print("-"*60 + "\n")

        return policies

    except Exception as e:
        print(f"❌ 错误: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return []


if __name__ == '__main__':
    extract_ndrc_policies()
