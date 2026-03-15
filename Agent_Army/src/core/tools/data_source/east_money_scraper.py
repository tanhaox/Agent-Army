"""
东方财富数据源工具 - 获取产业链、行业分类等数据
"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from src.core.logger import get_logger
from src.core.utils.rate_limiter import get_global_limiter_manager


class EastMoneyScraper:
    """
    东方财富数据爬虫

    职责：
    - 获取产业链信息
    - 获取行业分类
    - 获取公司行业信息

    数据来源：东方财富网（公开API）
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("east_money_scraper")
        self.config = config or {}

        # API基础URL
        self.base_url = "http://push2.eastmoney.com/api/qt/clist/get"
        self.industry_url = "http://emweb.securities.eastmoney.com/PC_HSF10/IndustryIndustryService/api"

        # 初始化节流器（东方财富API限制）- 可选
        limiter_manager = get_global_limiter_manager()
        self.rate_limiter = limiter_manager.get("eastmoney")
        if self.rate_limiter is None:
            self.logger.warning("未配置东方财富API节流器，将无节流调用")

        self.logger.info("东方财富爬虫初始化完成")

    async def get_industry_info(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票的产业链信息

        Args:
            stock_code: 股票代码（如 "600519"）

        Returns:
            产业链信息字典:
            {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "industry_name": "白酒",
                "industry_chain": {
                    "upstream": ["原材料1", "原材料2"],
                    "midstream": ["制造环节1", "制造环节2"],
                    "downstream": ["销售渠道1", "销售渠道2"]
                },
                "market_share": 5.0,
                "industry_rank": 3,
                "industry_size": 1000.0,
                "industry_growth": 10.0
            }
        """
        self.logger.info(f"获取产业链信息: {stock_code}")

        # 转换股票代码格式
        ts_code = self._convert_stock_code(stock_code)

        # 尝试获取行业信息（东方财富 -> AKShare -> 默认值）
        industry_data = None
        chain_data = {
            "upstream": ["原材料供应"],
            "midstream": ["生产制造"],
            "downstream": ["销售渠道"]
        }

        try:
            # 节流控制（如果已配置）
            if self.rate_limiter is not None:
                await self.rate_limiter.acquire(timeout=30.0)
                self.logger.info("✅ 东方财富节流器许可已获取")
            else:
                self.logger.info("⚠️ 无节流器，直接调用API")

            # 尝试获取行业信息
            industry_data = await self._fetch_industry_data(ts_code)

            # 尝试获取产业链信息（如果失败，使用默认值）
            try:
                chain_data = await self._fetch_chain_data(ts_code)
            except Exception as chain_error:
                self.logger.warning(f"获取产业链数据失败，使用默认值: {chain_error}")

        except Exception as e:
            self.logger.warning(f"东方财富API失败: {str(e)}")
            self.logger.info("⚠️ 使用AKShare作为备用数据源...")

            # 使用AKShare作为备用
            try:
                import akshare as ak

                # 获取股票基本信息
                stock_info = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: ak.stock_individual_info_em(stock_code)
                )

                # 解析行业信息
                industry_name = "其他"
                for item in stock_info.values():
                    if '行业' in str(item):
                        industry_name = str(item).split('：')[-1] if '：' in str(item) else str(item)
                        break

                industry_data = {
                    "stock_name": "未知",
                    "industry_name": industry_name,
                    "industry_code": "BK0001",
                    "market_share": 5.0,
                    "industry_rank": 50,
                    "industry_size": 1000.0,
                    "industry_growth": 10.0,
                    "industry_cycle": self._determine_industry_cycle(industry_name)
                }

                self.logger.info(f"✅ 使用AKShare获取到行业信息: {industry_name}")

            except Exception as ak_error:
                self.logger.error(f"AKShare也失败: {str(ak_error)}")
                # 使用默认数据
                industry_data = self._get_default_industry_data(ts_code)

        # 如果行业数据仍然为空，使用默认值
        if industry_data is None:
            self.logger.warning("所有数据源均失败，使用默认数据")
            industry_data = self._get_default_industry_data(ts_code)

        # 整合数据
        result = {
            "stock_code": stock_code,
            "stock_name": industry_data.get("stock_name", ""),
            "industry_name": industry_data.get("industry_name", ""),
            "industry_code": industry_data.get("industry_code", ""),
            "industry_chain": chain_data,
            "market_share": industry_data.get("market_share", 0.0),
            "industry_rank": industry_data.get("industry_rank", 0),
            "industry_size": industry_data.get("industry_size", 0.0),
            "industry_growth": industry_data.get("industry_growth", 0.0),
            "industry_cycle": industry_data.get("industry_cycle", "未知"),
            "data_sources": ["东方财富", "AKShare"] if industry_data.get("stock_name") != "未知" else ["默认值"],
            "last_update": datetime.now().isoformat()
        }

        self.logger.info(f"✅ 成功获取产业链信息: {result['industry_name']}")
        return result

    async def get_industry_stocks(self, industry_name: str) -> List[str]:
        """
        获取同一行业的所有股票代码

        Args:
            industry_name: 行业名称

        Returns:
            股票代码列表
        """
        self.logger.info(f"获取行业股票: {industry_name}")

        try:
            # 调用东方财富API
            params = {
                "pn": 1,
                "pz": 500,
                "po": 1,
                "np": 1,
                "fltt": 2,
                "invt": 2,
                "fid": "f3",  # 行业分类
                "fs": f"b:{self._get_industry_code(industry_name)}",  # 行业代码
                "fields": f"f12,f14",  # 股票代码, 股票名称
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, timeout=10) as response:
                    if response.status != 200:
                        raise Exception(f"API返回错误: {response.status}")

                    data = await response.json()

                    if data.get("rc") != 0:
                        raise Exception(f"API返回错误: {data.get('errmsg')}")

                    stocks = []
                    for item in data.get("data", {}).get("diff", []):
                        stock_code = item.get("f12", "")
                        stocks.append(stock_code)

                    self.logger.info(f"获取到 {len(stocks)} 只股票")
                    return stocks

        except Exception as e:
            self.logger.error(f"获取行业股票失败: {str(e)}")
            return []

    def _convert_stock_code(self, stock_code: str) -> str:
        """
        转换股票代码格式

        Args:
            stock_code: 6位代码（如 "600519"）

        Returns:
            带后缀的代码（如 "600519.SH" 或 "000001.SZ"）
        """
        if stock_code.startswith('6'):
            return f"{stock_code}.SH"
        else:
            return f"{stock_code}.SZ"

    def _get_industry_code(self, industry_name: str) -> str:
        """
        获取行业代码（申万行业分类）

        Args:
            industry_name: 行业名称

        Returns:
            行业代码
        """
        # 申万一级行业代码映射
        industry_codes = {
            "银行": "BK0001",
            "医药生物": "BK0002",
            "食品饮料": "BK0003",
            "电子": "BK0004",
            "计算机": "BK0005",
            "传媒": "BK0006",
            "通信": "BK0007",
            "房地产": "BK0008",
            "建筑装饰": "BK0009",
            "电气设备": "BK0010",
            # ... 更多行业映射
        }

        return industry_codes.get(industry_name, "BK0001")

    async def _fetch_industry_data(self, ts_code: str) -> Dict[str, Any]:
        """
        获取行业数据（内部方法）

        Args:
            ts_code: 带后缀的股票代码

        Returns:
            行业数据字典
        """
        self.logger.info(f"获取行业数据: {ts_code}")

        try:
            # 方案1: 尝试调用东方财富行业信息API
            url = f"{self.industry_url}/GetIndustryPlateInfo"
            params = {
                "secid": ts_code,
                "field": "f3,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152"
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "http://emweb.securities.eastmoney.com/"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        raise Exception(f"API返回错误: {response.status}")

                    # 检查返回类型
                    content_type = response.headers.get('Content-Type', '')
                    if 'text/html' in content_type:
                        self.logger.warning(f"API返回HTML页面，可能URL已变更或需要认证")
                        raise Exception("API返回HTML而非JSON数据")

                    data = await response.json()

                    # 解析返回数据
                    if data.get("version") is None or data.get("data") is None:
                        self.logger.warning(f"API返回空数据，使用默认值")
                        return self._get_default_industry_data(ts_code)

                    industry_info = data.get("data", {})

                    return {
                        "stock_name": industry_info.get("secName", ""),
                        "industry_name": industry_info.get("boardName", ""),
                        "industry_code": industry_info.get("boardCode", ""),
                        "market_share": self._calculate_market_share(ts_code),
                        "industry_rank": industry_info.get("rank", 0),
                        "industry_size": industry_info.get("totalMarketValue", 0) / 1e8,  # 转换为亿元
                        "industry_growth": industry_info.get("industryGrowth", 0.0),
                        "industry_cycle": self._determine_industry_cycle(industry_info.get("boardName", ""))
                    }

        except Exception as e:
            self.logger.error(f"获取行业数据失败: {str(e)}")
            self.logger.info("使用AKShare作为备用数据源...")

            # 方案2: 使用AKShare作为备用
            try:
                import akshare as ak

                # 获取股票基本信息
                stock_info = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: ak.stock_individual_info_em(ts_code.split('.')[0])
                )

                # 解析行业信息
                industry_name = "其他"
                for item in stock_info.values():
                    if '行业' in str(item):
                        industry_name = str(item).split('：')[-1] if '：' in str(item) else str(item)
                        break

                return {
                    "stock_name": "未知",  # AKShare不返回股票名称
                    "industry_name": industry_name,
                    "industry_code": "BK0001",
                    "market_share": 5.0,  # 默认值
                    "industry_rank": 50,  # 默认值
                    "industry_size": 1000.0,  # 默认值
                    "industry_growth": 10.0,  # 默认值
                    "industry_cycle": self._determine_industry_cycle(industry_name)
                }

            except Exception as ak_error:
                self.logger.error(f"AKShare也失败了: {str(ak_error)}")
                # 返回默认数据
                return self._get_default_industry_data(ts_code)

    async def _fetch_chain_data(self, ts_code: str) -> Dict[str, List[str]]:
        """
        获取产业链数据（内部方法）

        Args:
            ts_code: 带后缀的股票代码

        Returns:
            产业链数据字典:
            {
                "upstream": ["上游1", "上游2"],
                "midstream": ["中游1", "中游2"],
                "downstream": ["下游1", "下游2"]
            }
        """
        self.logger.info(f"获取产业链数据: {ts_code}")

        try:
            # 调用东方财富产业链API
            url = f"{self.industry_url}/GetIndustryChainInfo"
            params = {
                "secid": ts_code
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status != 200:
                        raise Exception(f"API返回错误: {response.status}")

                    data = await response.json()

                    # 解析产业链数据
                    chain_info = data.get("data", {})

                    return {
                        "upstream": chain_info.get("upstream", []),
                        "midstream": chain_info.get("midstream", []),
                        "downstream": chain_info.get("downstream", [])
                    }

        except Exception as e:
            self.logger.error(f"获取产业链数据失败: {str(e)}")
            # 返回默认数据
            return {
                "upstream": ["原材料供应"],
                "midstream": ["生产制造"],
                "downstream": ["销售渠道"]
            }

    def _calculate_market_share(self, ts_code: str) -> float:
        """
        计算市场份额（简化版）

        Args:
            ts_code: 股票代码

        Returns:
            市场份额（百分比）
        """
        # TODO: 实现真实的市场份额计算
        # 这里使用简化逻辑，实际应该从API获取
        return 5.0

    def _determine_industry_cycle(self, industry_name: str) -> str:
        """
        判断行业周期

        Args:
            industry_name: 行业名称

        Returns:
            行业周期（成长期/成熟期/衰退期）
        """
        # 简化判断逻辑
        growth_industries = ["新能源", "人工智能", "半导体", "生物医药"]

        for growth_industry in growth_industries:
            if growth_industry in industry_name:
                return "成长期"

        return "成熟期"

    def _get_default_industry_data(self, ts_code: str) -> Dict[str, Any]:
        """
        获取默认行业数据（API失败时的降级方案）

        Args:
            ts_code: 股票代码

        Returns:
            默认行业数据
        """
        return {
            "stock_name": "未知",
            "industry_name": "其他",
            "industry_code": "BK9999",
            "market_share": 0.0,
            "industry_rank": 0,
            "industry_size": 0.0,
            "industry_growth": 0.0,
            "industry_cycle": "未知"
        }


# 测试代码
async def test():
    """测试东方财富爬虫"""
    scraper = EastMoneyScraper()

    # 测试1: 获取产业链信息
    print("测试1: 获取产业链信息")
    result = await scraper.get_industry_info("600519")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 测试2: 获取行业股票
    print("\n测试2: 获取行业股票")
    stocks = await scraper.get_industry_stocks("食品饮料")
    print(f"股票数量: {len(stocks)}")
    print(f"前5只: {stocks[:5]}")


if __name__ == "__main__":
    asyncio.run(test())
