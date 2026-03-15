"""
政府网站内容提取器 - 测试脚本
功能：从政府网站提取政策正文内容，去除广告和无关标签
"""

import sys
import io

# 修复Windows控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup
import html2text
from typing import Dict, Optional
import re


class GovContentExtractor:
    """政府网站内容提取器"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.body_width = 0  # 不换行

    def extract_content(self, url: str) -> Dict[str, str]:
        """
        提取网页正文内容

        Args:
            url: 网页URL

        Returns:
            {
                "title": 标题,
                "content": Markdown格式正文,
                "date": 发布日期,
                "source": 来源,
                "success": 是否成功
            }
        """
        print(f"\n{'='*60}")
        print(f"正在提取: {url}")
        print(f"{'='*60}\n")

        try:
            # 1. 获取网页
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = response.apparent_encoding
            print(f"✅ 状态码: {response.status_code}")

            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}

            # 2. 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 3. 提取标题
            title = self._extract_title(soup)
            print(f"📌 标题: {title}")

            # 4. 提取正文
            content_div = self._find_content_div(soup)
            if not content_div:
                return {"success": False, "error": "未找到正文内容"}

            # 5. 转换为Markdown
            markdown_content = self.h2t.handle(str(content_div))
            print(f"📝 内容长度: {len(markdown_content)} 字符")

            # 6. 提取发布日期
            date = self._extract_date(soup)
            print(f"📅 日期: {date}")

            # 7. 提取来源
            source = self._extract_source(soup, url)
            print(f"🏢 来源: {source}")

            print(f"\n✅ 提取成功！\n")

            return {
                "success": True,
                "title": title,
                "content": markdown_content,
                "date": date,
                "source": source,
                "url": url
            }

        except Exception as e:
            print(f"❌ 错误: {str(e)}\n")
            return {"success": False, "error": str(e)}

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        # 优先级：h1 > title属性 > meta title
        title_tag = soup.find('h1')
        if title_tag:
            return title_tag.get_text().strip()

        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()

        return "未知标题"

    def _find_content_div(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """
        查找正文内容区域

        政府网站的常见正文容器：
        - class="content" / "article-content" / "main-content"
        - id="content" / "article" / "main"
        """
        # 先移除不需要的标签
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            tag.decompose()

        # 常见的政府网站正文容器（按优先级排序）
        content_selectors = [
            'article',  # HTML5语义化标签
            'div.pages_txt',  # 中国政府网专用
            'div.TRS_Editor',  # 政府网站常见
            'div.article-body',
            'div.main-content',
            'div.text',
            'div.detail',
            'div.article-content',
            'div#content',
            'div.content',
            'div.content-area',
        ]

        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                text_length = len(content_div.get_text().strip())
                print(f"🔍 找到容器: {selector} (文本长度: {text_length})")
                # 至少200字符才算有效正文
                if text_length > 200:
                    return content_div

        # 如果以上都没找到，尝试找最大的文本块
        print("⚠️ 未找到常见容器，尝试自动检测...")
        all_divs = soup.find_all('div')
        valid_divs = [d for d in all_divs if len(d.get_text().strip()) > 200]

        if valid_divs:
            max_text_div = max(valid_divs, key=lambda d: len(d.get_text()))
            print(f"🔍 自动检测到最大文本块 (长度: {len(max_text_div.get_text())})")
            return max_text_div

        return None

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """提取发布日期"""
        # 常见的日期选择器
        date_selectors = [
            'span.date',
            'span.pub-date',
            'span.publish-date',
            'time',
            'p.date',
            'div.date',
        ]

        for selector in date_selectors:
            date_tag = soup.select_one(selector)
            if date_tag:
                date_text = date_tag.get_text().strip()
                # 简单的日期格式验证
                if re.search(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}', date_text):
                    return date_text

        return "未知日期"

    def _extract_source(self, soup: BeautifulSoup, url: str) -> str:
        """提取来源"""
        # 从URL推断来源
        if 'gov.cn' in url:
            if 'www.gov.cn' in url:
                return "中国政府网"
            elif 'ndrc.gov.cn' in url:
                return "国家发改委"
            elif 'pbc.gov.cn' in url:
                return "中国人民银行"
            elif 'csrc.gov.cn' in url:
                return "中国证监会"
            else:
                return "政府网站"
        return "未知来源"


def test_gov_websites():
    """测试政府网站内容提取"""

    extractor = GovContentExtractor()

    # 测试URL列表（使用实际存在的政策文件）
    test_urls = [
        {
            "name": "中国政府网-最新政策",
            "url": "https://www.gov.cn/zhengce/zuixin/"
        },
        {
            "name": "中国政府网-政策文件库",
            "url": "https://www.gov.cn/zhengce/zhengceku/"
        },
        {
            "name": "发改委-政策发布",
            "url": "https://www.ndrc.gov.cn/xxgk/zcfb/"
        },
    ]

    print("\n" + "="*60)
    print("政府网站内容提取测试")
    print("="*60)

    for test in test_urls:
        print(f"\n测试: {test['name']}")
        print(f"URL: {test['url']}")

        result = extractor.extract_content(test['url'])

        if result['success']:
            print("\n" + "-"*60)
            print("【标题】")
            print(result['title'])
            print("\n【正文预览】（前500字符）")
            print(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
            print("\n【日期】")
            print(result['date'])
            print("\n【来源】")
            print(result['source'])
            print("-"*60)
        else:
            print(f"❌ 提取失败: {result.get('error', '未知错误')}")

    print("\n" + "="*60)
    print("测试完成")
    print("="*60 + "\n")


if __name__ == '__main__':
    test_gov_websites()
