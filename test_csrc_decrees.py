"""
证监会令提取器
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re


def extract_csrc_decrees():
    """提取证监会令列表"""

    url = "https://www.csrc.gov.cn/csrc/c101953/zfxxgk_zdgk.shtml"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    print(f"\n{'='*60}")
    print(f"提取证监会令列表")
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

        # 查找所有链接
        all_links = soup.find_all('a', href=True)

        print(f"🔍 找到 {len(all_links)} 个链接\n")

        # 过滤证监会令相关链接
        for link in all_links:
            title = link.get_text().strip()
            href = link['href']

            # 过滤条件：
            # 1. 标题包含"令"字（如【第233号令】）
            # 2. 或者标题长度足够且包含关键词
            if '令' not in title and len(title) < 10:
                continue

            # 跳过导航链接
            skip_keywords = ['首页', '返回', '更多', '下一页', '上一页', '版权', '联系我们']
            if any(kw in title for kw in skip_keywords):
                continue

            # 补全相对链接
            if href.startswith('/'):
                full_link = f"https://www.csrc.gov.cn{href}"
            elif not href.startswith('http'):
                continue
            else:
                full_link = href

            # 提取令号（如【第233号令】）
            decree_match = re.search(r'【第(\d+)号令】', title)
            if decree_match:
                decree_num = decree_match.group(1)
                # 重新格式化标题
                title = title.replace('【', '【第').replace('】', '号令】')
            else:
                decree_num = ""

            # 提取发布日期（从链接中）
            # 例如：/csrc/c101953/c7616837/content.shtml
            # 从内容页面的URL中获取日期
            date = ""

            policies.append({
                "title": title,
                "link": full_link,
                "date": date,
                "source": "中国证监会",
                "type": "证监会令"
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
        print("【证监会令列表】（显示前20条）")
        print("-"*60 + "\n")

        for i, policy in enumerate(unique_policies[:20], 1):
            print(f"{i}. {policy['title']}")
            print(f"   🔗 {policy['link']}")
            print()

        if len(unique_policies) > 20:
            print(f"... 还有 {len(unique_policies) - 20} 条\n")

        print("-"*60)
        print(f"✅ 共 {len(unique_policies)} 条证监会令")
        print("-"*60 + "\n")

        return unique_policies

    except Exception as e:
        print(f"❌ 错误: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return []


if __name__ == '__main__':
    extract_csrc_decrees()
