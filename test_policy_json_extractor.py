"""
政府政策JSON数据提取器
功能：直接获取政府网站的JSON数据文件
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
from typing import List, Dict


class GovPolicyJSONExtractor:
    """政府政策JSON提取器"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'https://www.gov.cn/zhengce/zuixin/',
        }

    def extract_from_json(self, json_url: str, source_name: str = "中国政府网") -> List[Dict]:
        """
        从JSON文件提取政策列表

        Args:
            json_url: JSON文件的完整URL
            source_name: 数据源名称

        Returns:
            [
                {
                    "title": 标题,
                    "link": 链接,
                    "date": 发布日期,
                    "source": 来源
                }
        ]
        """
        print(f"\n{'='*60}")
        print(f"正在获取: {source_name}")
        print(f"JSON URL: {json_url}")
        print(f"{'='*60}\n")

        try:
            response = requests.get(json_url, headers=self.headers, timeout=15)

            print(f"✅ 状态码: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ 获取失败: HTTP {response.status_code}")
                return []

            # 解析JSON
            data = response.json()

            # 转换为标准格式
            policies = []
            for item in data:
                policy = {
                    "title": item.get("TITLE", "").strip(),
                    "link": item.get("URL", "").strip(),
                    "date": item.get("DOCRELPUBTIME", "").strip(),
                    "source": source_name
                }

                # 过滤无效数据
                if policy["title"] and policy["link"]:
                    policies.append(policy)

            print(f"✅ 成功提取 {len(policies)} 条政策\n")

            return policies

        except Exception as e:
            print(f"❌ 错误: {str(e)}\n")
            return []

    def auto_discover_json(self, page_url: str) -> List[Dict]:
        """
        自动发现并获取JSON数据

        Args:
            page_url: 政策列表页面的URL

        Returns:
            政策列表
        """
        print(f"\n{'='*60}")
        print(f"自动发现JSON数据源")
        print(f"页面URL: {page_url}")
        print(f"{'='*60}\n")

        # 常见的JSON文件路径
        possible_json_paths = [
            "./ZUIXINZHENGCE.json",
            "./zhengce.json",
            "./policy.json",
            "./data.json",
        ]

        # 从页面URL推导基础URL
        if "zuixin" in page_url:
            base_url = "https://www.gov.cn/zhengce/zuixin/"
            json_url = "https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json"
        elif "zhengceku" in page_url:
            base_url = "https://www.gov.cn/zhengce/zhengceku/"
            json_url = "https://www.gov.cn/zhengce/zhengceku/ZHENGCEKU.json"
        else:
            print("⚠️ 未知的页面类型")
            return []

        print(f"🔍 推测JSON URL: {json_url}\n")

        return self.extract_from_json(json_url, "中国政府网")


def test_json_extraction():
    """测试JSON提取"""

    extractor = GovPolicyJSONExtractor()

    # 测试URL
    json_url = "https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json"

    print("\n" + "="*60)
    print("政府政策JSON提取测试")
    print("="*60)

    policies = extractor.extract_from_json(json_url)

    if policies:
        print("\n" + "-"*60)
        print("【最新政策列表】（显示前20条）")
        print("-"*60 + "\n")

        for i, policy in enumerate(policies[:20], 1):
            print(f"{i}. {policy['title']}")
            print(f"   📅 {policy['date']}")
            print(f"   🔗 {policy['link']}")
            print()

        print("-"*60)
        print(f"✅ 共 {len(policies)} 条政策")
        print("-"*60)

    print("\n" + "="*60)
    print("测试完成")
    print("="*60 + "\n")


if __name__ == '__main__':
    test_json_extraction()
