"""
Yahoo Finance工具 - 国际标准股票数据源

功能:
- 实时行情数据
- 历史K线数据
- 财务报表
- 股票基本信息
- 资金流向数据（部分支持）

依赖:
- pip install yfinance

数据源:
- Yahoo Finance API（免费，无需注册）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class YahooFinanceTool:
    """
    Yahoo Finance工具类

    提供全球股票市场数据的访问能力
    """

    def __init__(self):
        """初始化Yahoo Finance工具"""
        try:
            import yfinance as yf
            self.yf = yf
            self.available = True
            logger.info("Yahoo Finance工具初始化成功")
        except ImportError:
            self.available = False
            logger.error("yfinance未安装，请运行: pip install yfinance")

    def is_available(self) -> bool:
        """检查工具是否可用"""
        return self.available

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        股票基本信息

        Args:
            symbol: 股票代码（如 "601669.SS" 代表A股）

        Returns:
            股票信息字典，包含名称、市值、行业等
        """
        if not self.available:
            return {"error": "yfinance未安装"}

        try:
            ticker = self.yf.Ticker(symbol)
            info = ticker.info

            # 提取关键信息
            result = {
                "symbol": symbol,
                "name": info.get("longName", "未知"),
                "market_cap": info.get("marketCap", 0),
                "previous_close": info.get("previousClose", 0),
                "open": info.get("open", 0),
                "high": info.get("dayHigh", 0),
                "low": info.get("dayLow", 0),
                "volume": info.get("volume", 0),
                "52_week_change": info.get("52WeekChange", 0),
                "industry": info.get("industry", "未知"),
                "sector": info.get("sector", "未知"),
                "website": info.get("website", ""),
                "business_summary": info.get("longBusinessSummary", ""),
                "employees": info.get("fullTimeEmployees", 0),
                "city": info.get("city", ""),
                "country": info.get("country", "China")
            }

            logger.info(f"成功获取 {symbol} 的基本信息")
            return result

        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return {"error": str(e)}

    def get_historical_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        获取历史K线数据

        Args:
            symbol: 股票代码
            period: 时间周期 ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
            interval: 数据频率 ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "5d", "1wk", "1mo", "3mo")

        Returns:
            DataFrame with OHLCV data
        """
        if not self.available:
            return pd.DataFrame()

        try:
            ticker = self.yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)

            logger.info(f"成功获取 {symbol} 历史数据，共 {len(hist)} 条记录")
            return hist

        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return pd.DataFrame()

    def get_financial_statements(
        self,
        symbol: str
    ) -> Dict[str, Any]:
        """
        获取财务报表数据

        Args:
            symbol: 股票代码

        Returns:
            包含利润表、资产负债表、现金流量表的字典
        """
        if not self.available:
            return {"error": "yfinance未安装"}

        try:
            ticker = self.yf.Ticker(symbol)

            # 获取财务报表
            financials = ticker.financials
            income_statement = ticker.income_stmt
            balance_sheet = ticker.balance_sheet
            cash_flow = ticker.cashflow

            result = {
                "symbol": symbol,
                "income_statement": self._process_dataframe(income_statement) if income_statement is not None else None,
                "balance_sheet": self._process_dataframe(balance_sheet) if balance_sheet is not None else None,
                "cash_flow": self._process_dataframe(cash_flow) if cash_flow is not None else None,
            }

            logger.info(f"成功获取 {symbol} 财务报表")
            return result

        except Exception as e:
            logger.error(f"获取财务报表失败: {e}")
            return {"error": str(e)}

    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取实时行情

        Args:
            symbol: 股票代码（多个代码用空格分隔）

        Returns:
            实时行情数据
        """
        if not self.available:
            return {"error": "yfinance未安装"}

        try:
            ticker = self.yf.Ticker(symbol)
            info = ticker.info

            result = {
                "symbol": symbol,
                "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "change": info.get("regularMarketChange", 0),
                "change_percent": info.get("regularMarketChangePercent", 0),
                "previous_close": info.get("previousClose", 0),
                "open": info.get("regularMarketOpen", 0),
                "high": info.get("regularMarketDayHigh", 0),
                "low": info.get("regularMarketDayLow", 0),
                "volume": info.get("regularMarketVolume", 0),
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"成功获取 {symbol} 实时行情")
            return result

        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return {"error": str(e)}

    def _process_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """处理DataFrame，转换为字典格式"""
        if df is None or df.empty:
            return None

        try:
            return {
                "data": df.to_dict('records')[:10],  # 前10行
                "columns": df.columns.tolist(),
                "shape": df.shape
            }
        except:
            return {"error": "数据处理失败"}

    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取公司详细信息

        Args:
            symbol: 股票代码

        Returns:
            公司信息字典
        """
        if not self.available:
            return {"error": "yfinance未安装"}

        try:
            ticker = self.yf.Ticker(symbol)
            info = ticker.info

            result = {
                "company_name": info.get("longName", ""),
                "legal_name": info.get("underlyingSymbol", ""),
                "industry": info.get("industry", ""),
                "sector": info.get("sector", ""),
                "business_summary": info.get("longBusinessSummary", ""),
                "website": info.get("website", ""),
                "employees": info.get("fullTimeEmployees", 0),
                "city": info.get("city", ""),
                "zip": info.get("zip", ""),
                "country": info.get("country", ""),
                "currency": info.get("currency", "CNY"),
                "exchange": info.get("exchange", ""),
                "market": info.get("market", ""),
                "market_cap": info.get("marketCap", 0),
                "shares_outstanding": info.get("sharesOutstanding", 0),
                "shares_float": info.get("sharesFloat", 0),
                "shares_short": info.get("sharesShort", 0),
                "short_ratio": info.get("shortRatio", 0),
                "trailing_pe": info.get("trailingPE", 0),
                "forward_pe": info.get("forwardPE", 0),
                "peg_ratio": info.get("pegRatio", 0),
                "price_to_book": info.get("priceToBook", 0),
                "enterprise_value": info.get("enterpriseValue", 0),
                "profit_margin": info.get("profitMargins", 0),
                "operating_margin": info.get("operatingMargins", 0),
            }

            logger.info(f"成功获取 {symbol} 公司详细信息")
            return result

        except Exception as e:
            logger.error(f"获取公司信息失败: {e}")
            return {"error": str(e)}


# 便捷函数
def get_yahoo_tool() -> YahooFinanceTool:
    """获取YahooFinance工具实例"""
    return YahooFinanceTool()


if __name__ == "__main__":
    # 测试代码
    print("=" * 70)
    print("Yahoo Finance工具测试")
    print("=" * 70)

    tool = YahooFinanceTool()

    if not tool.is_available():
        print("❌ yfinance未安装")
        print("请运行: pip install yfinance")
        exit(1)

    # 测试1: 获取股票信息
    print("\n[1] 测试获取股票信息: 601669.SS (中国电建)")
    info = tool.get_stock_info("601669.SS")
    print(f"公司名称: {info.get('name')}")
    print(f"市值: {info.get('market_cap')}")
    print(f"行业: {info.get('industry')}")

    # 测试2: 获取实时行情
    print("\n[2] 测试获取实时行情")
    quote = tool.get_realtime_quote("601669.SS")
    print(f"当前价格: {quote.get('current_price')}")
    print(f"涨跌幅: {quote.get('change_percent'):.2f}%")

    print("\n" + "=" * 70)
    print("测试完成")
