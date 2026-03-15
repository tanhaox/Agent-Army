"""
工具库门面层 - 统一接口

职责：
- 为分散的工具接口提供统一入口
- 自动降级和格式转换
- 简化Agent的使用复杂度

设计模式：Facade Pattern（门面模式）

根据 TOOLS_LIBRARY_INTERFACE_ANALYSIS.md 分析：
- 工具库已有23个接口，功能完整
- 主要问题：接口分散，Agent难以发现和使用
- 解决方案：创建统一门面层
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

from src.core.logger import get_logger
from src.core.tools.data_source.yahoo_tool import YahooFinanceTool
from src.core.tools.data_source.akshare_tool import AKShareTool
from src.core.tools.data_source.east_money_scraper import EastMoneyScraper
from src.core.tools.data_source.financial_tool import FinancialTool


# =============================================================================
# 门面类 1: IndustryTool - 行业分析工具
# =============================================================================

class IndustryTool:
    """
    行业分析工具 - 统一门面

    整合数据源：
    1. Yahoo Finance - 行业和板块信息
    2. AKShare - 股票基本信息
    3. EastMoneyScraper - 专门的产业链信息

    自动降级策略：
    Yahoo Finance → AKShare → EastMoney → 默认值
    """

    def __init__(self):
        self.logger = get_logger("industry_tool")

        # 初始化底层工具
        self.yahoo_tool = YahooFinanceTool()
        self.akshare_tool = AKShareTool()
        self.eastmoney_scraper = EastMoneyScraper()

        self.logger.info("行业分析工具初始化完成")

    async def get_industry_info(
        self,
        stock_code: str,
        use_chain: bool = False
    ) -> Dict[str, Any]:
        """
        获取行业信息（统一接口）

        Args:
            stock_code: 股票代码（如 "601669"）
            use_chain: 是否获取产业链信息（较慢）

        Returns:
            行业信息字典:
            {
                "stock_code": "601669",
                "stock_name": "中国电建",
                "industry": "建筑工程",
                "sector": "工业",
                "industry_code": "BK0472",
                "industry_chain": {...},  # 如果 use_chain=True
                "data_source": "Yahoo Finance"
            }
        """
        self.logger.info(f"获取行业信息: {stock_code}")

        # 方案1: 尝试 Yahoo Finance（有行业和板块信息）
        if self.yahoo_tool.is_available():
            try:
                yahoo_symbol = self._convert_to_yahoo_symbol(stock_code)
                yahoo_data = self.yahoo_tool.get_stock_info(yahoo_symbol)

                if "error" not in yahoo_data and yahoo_data.get("industry"):
                    self.logger.info(f"✅ 使用 Yahoo Finance 数据源")

                    result = {
                        "stock_code": stock_code,
                        "stock_name": yahoo_data.get("name", ""),
                        "industry": yahoo_data.get("industry", "未知"),
                        "sector": yahoo_data.get("sector", "未知"),
                        "industry_code": "",
                        "data_source": "Yahoo Finance",
                        "last_update": datetime.now().isoformat()
                    }

                    # 如果需要产业链信息，使用EastMoney补充
                    if use_chain:
                        chain_data = await self._get_industry_chain(stock_code)
                        result["industry_chain"] = chain_data

                    return result

            except Exception as e:
                self.logger.warning(f"Yahoo Finance 获取失败: {e}")

        # 方案2: 尝试 AKShare
        if self.akshare_tool.is_available():
            try:
                akshare_data = self.akshare_tool.get_stock_info(stock_code)

                if "error" not in akshare_data:
                    self.logger.info(f"✅ 使用 AKShare 数据源")

                    # 从AKShare返回的字典中提取行业信息
                    industry = "未知"
                    for key, value in akshare_data.items():
                        if "行业" in key:
                            industry = str(value)
                            break

                    result = {
                        "stock_code": stock_code,
                        "stock_name": akshare_data.get("股票简称", ""),
                        "industry": industry,
                        "sector": "未知",
                        "industry_code": "",
                        "data_source": "AKShare",
                        "last_update": datetime.now().isoformat()
                    }

                    if use_chain:
                        chain_data = await self._get_industry_chain(stock_code)
                        result["industry_chain"] = chain_data

                    return result

            except Exception as e:
                self.logger.warning(f"AKShare 获取失败: {e}")

        # 方案3: 尝试东方财富（专门的产业链信息）
        if use_chain:
            try:
                chain_data = await self.eastmoney_scraper.get_industry_info(stock_code)

                self.logger.info(f"✅ 使用 EastMoney 数据源")

                return {
                    "stock_code": stock_code,
                    "stock_name": chain_data.get("stock_name", ""),
                    "industry": chain_data.get("industry_name", "未知"),
                    "sector": "未知",
                    "industry_code": chain_data.get("industry_code", ""),
                    "industry_chain": {
                        "upstream": chain_data.get("industry_chain", {}).get("upstream", []),
                        "midstream": chain_data.get("industry_chain", {}).get("midstream", []),
                        "downstream": chain_data.get("industry_chain", {}).get("downstream", [])
                    },
                    "market_share": chain_data.get("market_share", 0.0),
                    "industry_rank": chain_data.get("industry_rank", 0),
                    "data_source": "EastMoney",
                    "last_update": chain_data.get("last_update", datetime.now().isoformat())
                }

            except Exception as e:
                self.logger.warning(f"EastMoney 获取失败: {e}")

        # 方案4: 返回默认值
        self.logger.warning("所有数据源均失败，返回默认值")
        return self._get_default_industry_data(stock_code)

    async def get_industry_stocks(
        self,
        industry_name: str,
        limit: int = 100
    ) -> List[Dict[str, str]]:
        """
        获取同行业股票列表

        Args:
            industry_name: 行业名称
            limit: 返回数量限制

        Returns:
            股票列表 [{"stock_code": "...", "stock_name": "..."}]
        """
        self.logger.info(f"获取同行业股票: {industry_name}")

        try:
            # 使用AKShare获取概念股
            df = self.akshare_tool.get_concept_stocks(industry_name)

            if not df.empty:
                stocks = []
                for _, row in df.head(limit).iterrows():
                    stocks.append({
                        "stock_code": row.get("代码", ""),
                        "stock_name": row.get("名称", ""),
                    })

                self.logger.info(f"✅ 获取到 {len(stocks)} 只股票")
                return stocks

        except Exception as e:
            self.logger.error(f"获取同行业股票失败: {e}")

        return []

    async def _get_industry_chain(self, stock_code: str) -> Dict[str, List[str]]:
        """获取产业链信息（内部方法）"""
        try:
            chain_data = await self.eastmoney_scraper.get_industry_info(stock_code)
            return chain_data.get("industry_chain", {})
        except:
            return {
                "upstream": [],
                "midstream": [],
                "downstream": []
            }

    def _convert_to_yahoo_symbol(self, stock_code: str) -> str:
        """转换股票代码为Yahoo格式"""
        if stock_code.startswith('6'):
            return f"{stock_code}.SS"  # 上海
        elif stock_code.startswith('0') or stock_code.startswith('3'):
            return f"{stock_code}.SZ"  # 深圳
        else:
            return stock_code  # 原样返回

    def _get_default_industry_data(self, stock_code: str) -> Dict[str, Any]:
        """获取默认行业数据"""
        return {
            "stock_code": stock_code,
            "stock_name": "未知",
            "industry": "其他",
            "sector": "未知",
            "industry_code": "",
            "industry_chain": {
                "upstream": [],
                "midstream": [],
                "downstream": []
            },
            "data_source": "默认值",
            "last_update": datetime.now().isoformat()
        }


# =============================================================================
# 门面类 2: TechnicalTool - 技术分析工具
# =============================================================================

class TechnicalTool:
    """
    技术分析工具 - 统一门面

    整合数据源：
    1. Yahoo Finance - K线数据（支持多种周期）
    2. AKShare - 实时行情和涨跌榜

    自动降级策略：
    Yahoo Finance → AKShare → 默认值
    """

    def __init__(self):
        self.logger = get_logger("technical_tool")

        # 初始化底层工具
        self.yahoo_tool = YahooFinanceTool()
        self.akshare_tool = AKShareTool()

        self.logger.info("技术分析工具初始化完成")

    def get_kline(
        self,
        stock_code: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        获取K线数据（统一接口）

        Args:
            stock_code: 股票代码（如 "601669"）
            period: 时间周期 ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
            interval: 数据频率 ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "5d", "1wk", "1mo", "3mo")

        Returns:
            DataFrame with OHLCV data
        """
        self.logger.info(f"获取K线数据: {stock_code}, 周期={period}, 频率={interval}")

        # 方案1: 尝试 Yahoo Finance
        if self.yahoo_tool.is_available():
            try:
                yahoo_symbol = self._convert_to_yahoo_symbol(stock_code)
                df = self.yahoo_tool.get_historical_data(yahoo_symbol, period, interval)

                if not df.empty:
                    self.logger.info(f"✅ 使用 Yahoo Finance 数据源，共 {len(df)} 条记录")
                    return df

            except Exception as e:
                self.logger.warning(f"Yahoo Finance 获取失败: {e}")

        # 方案2: 尝试 AKShare
        if self.akshare_tool.is_available():
            try:
                # AKShare的K线数据接口（示例）
                # 这里需要根据实际情况调用AKShare的K线接口
                self.logger.info(f"⚠️ AKShare K线接口待实现")

            except Exception as e:
                self.logger.warning(f"AKShare 获取失败: {e}")

        # 返回空DataFrame
        self.logger.warning("所有数据源均失败")
        return pd.DataFrame()

    def get_top_list(self, date: str = None, limit: int = 50) -> pd.DataFrame:
        """
        获取涨跌榜（统一接口）

        Args:
            date: 日期 (YYYYMMDD，默认今日)
            limit: 返回数量限制

        Returns:
            涨跌榜数据
        """
        self.logger.info(f"获取涨跌榜: {date or '今日'}")

        if self.akshare_tool.is_available():
            try:
                df = self.akshare_tool.get_top_list(date)

                if not df.empty:
                    self.logger.info(f"✅ 获取到 {len(df)} 条记录")
                    return df.head(limit)

            except Exception as e:
                self.logger.error(f"获取涨跌榜失败: {e}")

        return pd.DataFrame()

    def _convert_to_yahoo_symbol(self, stock_code: str) -> str:
        """转换股票代码为Yahoo格式"""
        if stock_code.startswith('6'):
            return f"{stock_code}.SS"  # 上海
        elif stock_code.startswith('0') or stock_code.startswith('3'):
            return f"{stock_code}.SZ"  # 深圳
        else:
            return stock_code


# =============================================================================
# 门面类 3: CapitalFlowTool - 资金流向工具
# =============================================================================

class CapitalFlowTool:
    """
    资金流向工具 - 统一门面

    整合数据源：
    1. FinancialTool (Tushare) - 资金流向数据
    2. AKShare - 个股资金流向

    自动降级策略：
    FinancialTool → AKShare → 模拟数据
    """

    def __init__(self):
        self.logger = get_logger("capital_flow_tool")

        # 初始化底层工具
        self.financial_tool = FinancialTool()
        self.akshare_tool = AKShareTool()

        self.logger.info("资金流向工具初始化完成")

    async def get_capital_flow(
        self,
        stock_code: str,
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """
        获取资金流向数据（统一接口）

        Args:
            stock_code: 股票代码（如 "600519"）
            start_date: 开始日期（YYYYMMDD格式）
            end_date: 结束日期（YYYYMMDD格式）

        Returns:
            资金流向数据:
            {
                "stock_code": "600519",
                "data": [
                    {
                        "trade_date": "2026-03-15",
                        "net_vol_main": 200000,  # 主力净流入
                        "net_vol_xl": 150000,     # 大单净流入
                        "net_mf_vol": 50000,      # 中单净流入
                        "net_lg_vol": -30000      # 小单净流入
                    }
                ],
                "summary": {...}
            }
        """
        self.logger.info(f"获取资金流向数据: {stock_code}")

        # 方案1: 尝试 FinancialTool (Tushare)
        try:
            tushare_data = await self.financial_tool.get_moneyflow(
                stock_code, start_date, end_date
            )

            if tushare_data.get("data"):
                self.logger.info(f"✅ 使用 Tushare 数据源，共 {len(tushare_data['data'])} 条记录")
                return tushare_data

        except Exception as e:
            self.logger.warning(f"Tushare 获取失败: {e}")

        # 方案2: 尝试 AKShare
        if self.akshare_tool.is_available():
            try:
                market = "sh" if stock_code.startswith('6') else "sz"
                df = self.akshare_tool.get_individual_fund_flow(stock_code, market)

                if not df.empty:
                    self.logger.info(f"✅ 使用 AKShare 数据源，共 {len(df)} 条记录")

                    # 转换为统一格式
                    data_list = []
                    for _, row in df.iterrows():
                        data_list.append({
                            "trade_date": str(row.get("日期", "")),
                            "net_vol_main": float(row.get("主力净流入", 0)),
                            "net_vol_xl": float(row.get("超大单净流入", 0)),
                            "net_mf_vol": float(row.get("中单净流入", 0)),
                            "net_lg_vol": float(row.get("小单净流入", 0))
                        })

                    total_net_inflow = sum(d.get("net_vol_main", 0) for d in data_list)

                    return {
                        "stock_code": stock_code,
                        "data": data_list,
                        "summary": {
                            "total_net_inflow": float(total_net_inflow),
                            "avg_daily_inflow": float(total_net_inflow / len(data_list)) if data_list else 0,
                            "record_count": len(data_list)
                        },
                        "data_source": "AKShare"
                    }

            except Exception as e:
                self.logger.warning(f"AKShare 获取失败: {e}")

        # 方案3: 返回模拟数据
        self.logger.warning("所有数据源均失败，返回空数据")
        return {
            "stock_code": stock_code,
            "data": [],
            "summary": {
                "total_net_inflow": 0,
                "avg_daily_inflow": 0,
                "record_count": 0
            },
            "data_source": "无"
        }

    async def get_dragon_tiger(
        self,
        stock_code: str = None,
        date: str = None
    ) -> Dict[str, Any]:
        """
        获取龙虎榜数据（统一接口）

        Args:
            stock_code: 股票代码（可选）
            date: 日期 (YYYYMMDD格式)

        Returns:
            龙虎榜数据
        """
        self.logger.info(f"获取龙虎榜数据: {stock_code or '全部'}")

        # 使用 FinancialTool 的龙虎榜接口
        try:
            data = await self.financial_tool.get_top_list(stock_code, date)
            self.logger.info(f"✅ 获取到 {len(data.get('data', []))} 条记录")
            return data

        except Exception as e:
            self.logger.error(f"获取龙虎榜失败: {e}")
            return {
                "stock_code": stock_code,
                "data": [],
                "summary": {"total_count": 0},
                "data_source": "无"
            }


# =============================================================================
# 工厂函数
# =============================================================================

def get_industry_tool() -> IndustryTool:
    """获取行业分析工具实例"""
    return IndustryTool()


def get_technical_tool() -> TechnicalTool:
    """获取技术分析工具实例"""
    return TechnicalTool()


def get_capital_flow_tool() -> CapitalFlowTool:
    """获取资金流向工具实例"""
    return CapitalFlowTool()


# =============================================================================
# 导出列表
# =============================================================================

__all__ = [
    "IndustryTool",
    "TechnicalTool",
    "CapitalFlowTool",
    "get_industry_tool",
    "get_technical_tool",
    "get_capital_flow_tool"
]
