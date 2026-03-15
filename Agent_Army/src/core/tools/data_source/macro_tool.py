"""
宏观经济学工具 - Macro Economic Tool

功能：
1. 获取宏观经济数据（GDP、PMI、CPI、PPI等）
2. 获取货币政策数据（利率、M2、社融等）
3. 获取财政政策数据（财政收支、赤字率等）
4. 获取汇率数据（人民币汇率、外汇储备）

数据来源：
- 国家统计局
- 中国人民银行
- 财政部
- 外汇管理局
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random


class MacroTool:
    """宏观经济学工具类"""

    def __init__(self):
        """初始化宏观经济学工具"""
        self.data_sources = {
            "economic_growth": "国家统计局",
            "monetary_policy": "中国人民银行",
            "fiscal_policy": "财政部",
            "exchange_rate": "外汇管理局"
        }

    async def fetch_economic_growth_data(
        self,
        indicators: List[str] = None,
        time_range: str = "1y"
    ) -> Dict[str, Any]:
        """
        获取经济增长数据

        Args:
            indicators: 指标列表（gdp, pmi, industrial_added_value等）
            time_range: 时间范围（1y, 5y, 10y）

        Returns:
            经济增长数据
        """
        if indicators is None:
            indicators = ["gdp", "pmi", "industrial_added_value", "fixed_asset_investment"]

        # TODO: 接入真实API
        # 当前返回模拟数据
        return self._generate_mock_economic_growth(indicators, time_range)

    async def fetch_monetary_policy_data(
        self,
        indicators: List[str] = None,
        time_range: str = "1y"
    ) -> Dict[str, Any]:
        """
        获取货币政策数据

        Args:
            indicators: 指标列表（interest_rate, m2, social_financing等）
            time_range: 时间范围

        Returns:
            货币政策数据
        """
        if indicators is None:
            indicators = ["interest_rate", "m2", "social_financing", "reserve_ratio"]

        return self._generate_mock_monetary_policy(indicators, time_range)

    async def fetch_fiscal_policy_data(
        self,
        indicators: List[str] = None,
        time_range: str = "1y"
    ) -> Dict[str, Any]:
        """
        获取财政政策数据

        Args:
            indicators: 指标列表（fiscal_revenue, fiscal_expenditure, deficit_rate等）
            time_range: 时间范围

        Returns:
            财政政策数据
        """
        if indicators is None:
            indicators = ["fiscal_revenue", "fiscal_expenditure", "deficit_rate", "tax_revenue"]

        return self._generate_mock_fiscal_policy(indicators, time_range)

    async def fetch_inflation_data(
        self,
        indicators: List[str] = None,
        time_range: str = "1y"
    ) -> Dict[str, Any]:
        """
        获取通胀数据

        Args:
            indicators: 指标列表（cpi, ppi, core_cpi等）
            time_range: 时间范围

        Returns:
            通胀数据
        """
        if indicators is None:
            indicators = ["cpi", "ppi", "core_cpi", "inflation_expectation"]

        return self._generate_mock_inflation(indicators, time_range)

    async def fetch_exchange_rate_data(
        self,
        currencies: List[str] = None,
        time_range: str = "1y"
    ) -> Dict[str, Any]:
        """
        获取汇率数据

        Args:
            currencies: 货币列表（usd_cny, eur_cny等）
            time_range: 时间范围

        Returns:
            汇率数据
        """
        if currencies is None:
            currencies = ["usd_cny", "eur_cny", "foreign_reserve"]

        return self._generate_mock_exchange_rate(currencies, time_range)

    # ========== 模拟数据生成方法 ==========

    def _generate_mock_economic_growth(
        self,
        indicators: List[str],
        time_range: str
    ) -> Dict[str, Any]:
        """生成经济增长模拟数据"""
        data = {}

        for indicator in indicators:
            if indicator == "gdp":
                data["gdp"] = {
                    "value": round(random.uniform(5.0, 7.0), 2),
                    "unit": "%",
                    "period": "2026-Q1",
                    "trend": random.choice(["上升", "平稳", "下降"]),
                    "description": "GDP同比增长率"
                }
            elif indicator == "pmi":
                data["pmi"] = {
                    "manufacturing": round(random.uniform(48.0, 52.0), 1),
                    "non_manufacturing": round(random.uniform(52.0, 56.0), 1),
                    "composite": round(random.uniform(50.0, 54.0), 1),
                    "period": "2026-02",
                    "description": "采购经理指数（PMI）"
                }
            elif indicator == "industrial_added_value":
                data["industrial_added_value"] = {
                    "value": round(random.uniform(5.0, 7.0), 2),
                    "unit": "%",
                    "period": "2026-02",
                    "trend": random.choice(["加速", "平稳", "放缓"]),
                    "description": "工业增加值同比增长率"
                }
            elif indicator == "fixed_asset_investment":
                data["fixed_asset_investment"] = {
                    "value": round(random.uniform(4.0, 6.0), 2),
                    "unit": "%",
                    "period": "2026-01-02",
                    "trend": random.choice(["回升", "持平", "回落"]),
                    "description": "固定资产投资同比增长率"
                }

        data["data_source"] = "国家统计局"
        data["update_time"] = datetime.now().isoformat()

        return data

    def _generate_mock_monetary_policy(
        self,
        indicators: List[str],
        time_range: str
    ) -> Dict[str, Any]:
        """生成货币政策模拟数据"""
        data = {}

        for indicator in indicators:
            if indicator == "interest_rate":
                data["interest_rate"] = {
                    "lpr_1y": round(random.uniform(3.0, 4.0), 2),
                    "lpr_5y": round(random.uniform(3.5, 4.5), 2),
                    "mlf": round(random.uniform(2.0, 3.0), 2),
                    "reverse_repo_7d": round(random.uniform(1.5, 2.5), 2),
                    "trend": random.choice(["降息", "持平", "加息"]),
                    "description": "关键利率水平"
                }
            elif indicator == "m2":
                data["m2"] = {
                    "value": round(random.uniform(8.0, 12.0), 2),
                    "unit": "%",
                    "period": "2026-02",
                    "trend": random.choice(["加速", "平稳", "放缓"]),
                    "description": "M2货币供应量同比增长率"
                }
            elif indicator == "social_financing":
                data["social_financing"] = {
                    "total": round(random.uniform(30000, 50000), 0),
                    "unit": "亿元",
                    "period": "2026-02",
                    "yoy_growth": round(random.uniform(8.0, 12.0), 2),
                    "description": "社会融资规模增量"
                }
            elif indicator == "reserve_ratio":
                data["reserve_ratio"] = {
                    "large_banks": round(random.uniform(10.0, 12.0), 1),
                    "medium_banks": round(random.uniform(8.0, 10.0), 1),
                    "small_banks": round(random.uniform(6.0, 8.0), 1),
                    "trend": random.choice(["降准", "持平", "升准"]),
                    "description": "存款准备金率"
                }

        data["data_source"] = "中国人民银行"
        data["update_time"] = datetime.now().isoformat()

        return data

    def _generate_mock_fiscal_policy(
        self,
        indicators: List[str],
        time_range: str
    ) -> Dict[str, Any]:
        """生成财政政策模拟数据"""
        data = {}

        for indicator in indicators:
            if indicator == "fiscal_revenue":
                data["fiscal_revenue"] = {
                    "total": round(random.uniform(20000, 30000), 0),
                    "unit": "亿元",
                    "period": "2026-02",
                    "yoy_growth": round(random.uniform(-2.0, 5.0), 2),
                    "description": "财政收入"
                }
            elif indicator == "fiscal_expenditure":
                data["fiscal_expenditure"] = {
                    "total": round(random.uniform(25000, 35000), 0),
                    "unit": "亿元",
                    "period": "2026-02",
                    "yoy_growth": round(random.uniform(3.0, 8.0), 2),
                    "description": "财政支出"
                }
            elif indicator == "deficit_rate":
                data["deficit_rate"] = {
                    "value": round(random.uniform(2.5, 3.5), 2),
                    "unit": "%",
                    "period": "2026",
                    "trend": random.choice(["扩大", "持平", "收窄"]),
                    "description": "财政赤字率"
                }
            elif indicator == "tax_revenue":
                data["tax_revenue"] = {
                    "total": round(random.uniform(15000, 25000), 0),
                    "unit": "亿元",
                    "period": "2026-02",
                    "yoy_growth": round(random.uniform(-1.0, 4.0), 2),
                    "description": "税收收入"
                }

        data["data_source"] = "财政部"
        data["update_time"] = datetime.now().isoformat()

        return data

    def _generate_mock_inflation(
        self,
        indicators: List[str],
        time_range: str
    ) -> Dict[str, Any]:
        """生成通胀模拟数据"""
        data = {}

        for indicator in indicators:
            if indicator == "cpi":
                data["cpi"] = {
                    "value": round(random.uniform(-1.0, 3.0), 2),
                    "unit": "%",
                    "period": "2026-02",
                    "trend": random.choice(["上升", "平稳", "下降"]),
                    "description": "居民消费价格指数（CPI）"
                }
            elif indicator == "ppi":
                data["ppi"] = {
                    "value": round(random.uniform(-3.0, 2.0), 2),
                    "unit": "%",
                    "period": "2026-02",
                    "trend": random.choice(["回升", "持平", "回落"]),
                    "description": "工业生产者出厂价格指数（PPI）"
                }
            elif indicator == "core_cpi":
                data["core_cpi"] = {
                    "value": round(random.uniform(0.5, 2.5), 2),
                    "unit": "%",
                    "period": "2026-02",
                    "description": "核心CPI（扣除食品和能源）"
                }
            elif indicator == "inflation_expectation":
                data["inflation_expectation"] = {
                    "value": round(random.uniform(1.5, 3.0), 2),
                    "unit": "%",
                    "period": "2026",
                    "description": "通胀预期"
                }

        data["data_source"] = "国家统计局"
        data["update_time"] = datetime.now().isoformat()

        return data

    def _generate_mock_exchange_rate(
        self,
        currencies: List[str],
        time_range: str
    ) -> Dict[str, Any]:
        """生成汇率模拟数据"""
        data = {}

        for currency in currencies:
            if currency == "usd_cny":
                data["usd_cny"] = {
                    "value": round(random.uniform(7.0, 7.3), 4),
                    "change": round(random.uniform(-0.05, 0.05), 4),
                    "change_pct": round(random.uniform(-0.7, 0.7), 2),
                    "period": "2026-03-14",
                    "trend": random.choice(["升值", "平稳", "贬值"]),
                    "description": "美元兑人民币汇率"
                }
            elif currency == "eur_cny":
                data["eur_cny"] = {
                    "value": round(random.uniform(7.5, 8.0), 4),
                    "change": round(random.uniform(-0.05, 0.05), 4),
                    "change_pct": round(random.uniform(-0.7, 0.7), 2),
                    "period": "2026-03-14",
                    "description": "欧元兑人民币汇率"
                }
            elif currency == "foreign_reserve":
                data["foreign_reserve"] = {
                    "value": round(random.uniform(31000, 33000), 0),
                    "unit": "亿美元",
                    "period": "2026-02",
                    "change": round(random.uniform(-200, 200), 0),
                    "description": "外汇储备"
                }

        data["data_source"] = "外汇管理局"
        data["update_time"] = datetime.now().isoformat()

        return data
