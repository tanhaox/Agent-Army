"""
东方财富数据爬虫 - 动态网页数据抓取

功能:
- 资金流向数据
- 龙虎榜数据
- 财务数据
- 技术指标数据

依赖:
- pip install playwright
- playwright install chromium

数据源:
- data.eastmoney.com (东方财富数据中心)
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
import re
import logging

logger = logging.getLogger(__name__)


class EastMoneyScraper:
    """
    东方财富数据爬虫工具

    使用Playwright抓取动态网页数据
    """

    def __init__(self):
        """初始化爬虫工具"""
        try:
            from playwright.async_api import async_playwright
            self.async_playwright = async_playwright
            self.available = True
            logger.info("EastMoney爬虫初始化成功")
        except ImportError:
            self.available = False
            logger.error("playwright未安装，请运行: pip install playwright && playwright install chromium")

    def is_available(self) -> bool:
        """检查工具是否可用"""
        return self.available

    def parse_money(self, s: str) -> Optional[float]:
        """
        解析金额字符串，返回亿元单位

        Args:
            s: 金额字符串（如 "12.34亿", "5678万"）

        Returns:
            金额（亿元单位）
        """
        if not s:
            return None

        s = str(s).strip()
        if s == '—' or s == '-':
            return None

        # 提取数字
        match = re.search(r'[-+]?\d+\.?\d*', s.replace(',', ''))
        if not match:
            return None

        val = float(match.group())

        # 判断单位
        if '亿' in s:
            return val
        elif '万' in s:
            return val / 10000  # 转换为亿
        else:
            return val / 100000000  # 假设是元

    async def scrape_capital_flow(
        self,
        stock_code: str,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """
        抓取资金流向数据

        Args:
            stock_code: 股票代码
            timeout: 超时时间（毫秒）

        Returns:
            资金流向数据字典
        """
        if not self.available:
            return {"error": "playwright未安装"}

        url = f"https://data.eastmoney.com/stockdata/{stock_code}.html"

        try:
            async with self.async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                logger.info(f"正在抓取 {stock_code} 资金流向数据...")
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout)

                # 等待数据加载
                import asyncio
                await asyncio.sleep(10)

                # 查找资金流向表格
                tables = await page.query_selector_all("table")

                for idx, table in enumerate(tables):
                    try:
                        headers = await table.query_selector_all("th")
                        if not headers:
                            continue

                        header_texts = []
                        for h in headers:
                            text = await h.inner_text()
                            header_texts.append(text.strip())

                        # 检查是否是资金流统计表
                        if "资金流" in str(header_texts) and "今日资金" in str(header_texts):
                            logger.info(f"找到资金流向表格 (表格 #{idx + 1})")

                            rows = await table.query_selector_all("tbody tr")
                            data = {}

                            for row in rows:
                                cols = await row.query_selector_all("td")
                                if len(cols) >= 2:
                                    label = await cols[0].inner_text()
                                    label = label.strip()

                                    if label in ["净流入额", "净占比", "主力", "超大单", "大单", "中单"]:
                                        val_today = await cols[1].inner_text()
                                        val_5d = await cols[2].inner_text() if len(cols) > 2 else ""
                                        val_10d = await cols[3].inner_text() if len(cols) > 3 else ""

                                        data[label] = {
                                            'today': self.parse_money(val_today) if label == "净流入额" else val_today.strip(),
                                            '5d': self.parse_money(val_5d) if label == "净流入额" else val_5d.strip(),
                                            '10d': self.parse_money(val_10d) if label == "净流入额" else val_10d.strip()
                                        }

                            await browser.close()

                            result = {
                                "stock_code": stock_code,
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "net_inflow": data.get('净流入额', {}).get('today'),
                                "net_inflow_5d": data.get('净流入额', {}).get('5d'),
                                "net_inflow_10d": data.get('净流入额', {}).get('10d'),
                                "main_net": self.parse_money(data.get('主力', {}).get('today', '0')),
                                "super_large_net": self.parse_money(data.get('超大单', {}).get('today', '0')),
                                "large_net": self.parse_money(data.get('大单', {}).get('today', '0')),
                                "medium_net": self.parse_money(data.get('中单', {}).get('today', '0')),
                                "timestamp": datetime.now().isoformat()
                            }

                            logger.info(f"成功抓取 {stock_code} 资金流向数据")
                            return result

                    except Exception as e:
                        logger.debug(f"表格 {idx} 处理失败: {e}")
                        continue

                await browser.close()
                return {"error": "未找到资金流向数据"}

        except Exception as e:
            logger.error(f"抓取资金流向数据失败: {e}")
            return {"error": str(e)}

    async def scrape_stock_info(
        self,
        stock_code: str,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """
        抓取股票基本信息

        Args:
            stock_code: 股票代码
            timeout: 超时时间（毫秒）

        Returns:
            股票基本信息
        """
        if not self.available:
            return {"error": "playwright未安装"}

        url = f"https://data.eastmoney.com/stockdata/{stock_code}.html"

        try:
            async with self.async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                logger.info(f"正在抓取 {stock_code} 基本信息...")
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout)

                # 等待数据加载
                import asyncio
                await asyncio.sleep(5)

                # 获取页面标题（股票名称）
                title = await page.title()
                stock_name = title.split('-')[0].strip() if '-' in title else stock_code

                # 获取关键信息
                info = {
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "timestamp": datetime.now().isoformat()
                }

                # 这里可以扩展更多字段...
                # 比如：市值、PE、PB等

                await browser.close()
                logger.info(f"成功抓取 {stock_code} 基本信息")
                return info

        except Exception as e:
            logger.error(f"抓取股票信息失败: {e}")
            return {"error": str(e)}

    async def scrape_long_hu_bang(
        self,
        date: str = None,
        timeout: int = 30000
    ) -> List[Dict[str, Any]]:
        """
        抓取龙虎榜数据

        Args:
            date: 日期 (YYYY-MM-DD，默认今日)
            timeout: 超时时间（毫秒）

        Returns:
            龙虎榜数据列表
        """
        if not self.available:
            return [{"error": "playwright未安装"}]

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        url = f"http://data.eastmoney.com/stock/tradingdata/download/{date.replace('-', '')}.xls"

        try:
            async with self.async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                logger.info(f"正在抓取 {date} 龙虎榜数据...")

                # 这里可以实现龙虎榜数据抓取
                # TODO: 实现具体逻辑

                await browser.close()
                return []

        except Exception as e:
            logger.error(f"抓取龙虎榜数据失败: {e}")
            return [{"error": str(e)}]


# 便捷函数
def get_eastmoney_scraper() -> EastMoneyScraper:
    """获取EastMoney爬虫实例"""
    return EastMoneyScraper()


# 同步包装函数
def scrape_capital_flow_sync(stock_code: str) -> Dict[str, Any]:
    """同步方式抓取资金流向数据"""
    import asyncio

    scraper = EastMoneyScraper()
    if not scraper.is_available():
        return {"error": "playwright未安装"}

    return asyncio.run(scraper.scrape_capital_flow(stock_code))


if __name__ == "__main__":
    # 测试代码
    import asyncio

    print("=" * 70)
    print("EastMoney爬虫测试")
    print("=" * 70)

    scraper = EastMoneyScraper()

    if not scraper.is_available():
        print("❌ playwright未安装")
        print("请运行: pip install playwright && playwright install chromium")
        exit(1)

    # 测试1: 抓取资金流向
    print("\n[1] 测试抓取资金流向数据: 601669 (中国电建)")
    result = asyncio.run(scraper.scrape_capital_flow("601669"))

    if "error" not in result:
        print(f"✅ 抓取成功!")
        print(f"股票代码: {result['stock_code']}")
        print(f"日期: {result['date']}")
        print(f"今日净流入: {result.get('net_inflow', 'N/A')} 亿元")
        print(f"主力净流入: {result.get('main_net', 'N/A')} 亿元")
        print(f"超大单净流入: {result.get('super_large_net', 'N/A')} 亿元")
        print(f"大单净流入: {result.get('large_net', 'N/A')} 亿元")
    else:
        print(f"❌ {result['error']}")

    print("\n" + "=" * 70)
    print("测试完成")
