"""
AKShare工具 - 中国金融数据接口

功能:
- 个股资金流向数据
- 实时行情数据
- 财务数据
- 宏观经济数据

依赖:
- pip install akshare

数据源:
- 东方财富网
- 新浪财经
- 同花顺
- 网易财经
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class AKShareTool:
    """
    AKShare工具类

    专门获取中国A股市场数据
    """

    def __init__(self):
        """初始化AKShare工具"""
        try:
            import akshare as ak
            self.ak = ak
            self.available = True
            logger.info("AKShare工具初始化成功")
        except ImportError:
            self.available = False
            logger.error("akshare未安装，请运行: pip install akshare")

    def is_available(self) -> bool:
        """检查工具是否可用"""
        return self.available

    def get_individual_fund_flow(
        self,
        stock_code: str,
        market: str = "sh"
    ) -> pd.DataFrame:
        """
        获取个股资金流向数据

        Args:
            stock_code: 股票代码（如 "601669"）
            market: 市场代码 ("sh" 上海, "sz" 深圳)

        Returns:
            DataFrame with columns:
            - 日期: 交易日期
            - 收盘价: 当日收盘价
            - 涨跌幅: 涨跌幅度
            - 主力净流入: 主力资金净流入
            - 超大单净流入: 超大单净流入
            - 大单净流入: 大单净流入
            - 中单净流入: 中单净流入
            - 小单净流入: 小单净流入
        """
        if not self.available:
            logger.error("AKShare未安装")
            return pd.DataFrame()

        try:
            df = self.ak.stock_individual_fund_flow(
                stock=stock_code,
                market=market
            )

            logger.info(f"成功获取 {stock_code} 资金流向数据，共 {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"获取资金流向数据失败: {e}")
            return pd.DataFrame()

    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取实时行情数据

        Args:
            symbol: 股票代码（如 "sh601669" 或 "sz000001"）

        Returns:
            实时行情数据
        """
        if not self.available:
            return {"error": "akshare未安装"}

        try:
            # 沪深京实时行情
            df = self.ak.stock_zh_a_spot_em()

            # 过滤指定股票
            stock_data = df[df['代码'] == symbol]

            if stock_data.empty:
                return {"error": f"未找到股票 {symbol}"}

            row = stock_data.iloc[0]

            result = {
                "symbol": symbol,
                "name": row.get('名称', ''),
                "current_price": row.get('最新价', 0),
                "change": row.get('涨跌额', 0),
                "change_percent": row.get('涨跌幅', 0),
                "open": row.get('今开', 0),
                "high": row.get('最高', 0),
                "low": row.get('最低', 0),
                "volume": row.get('成交量', 0),
                "amount": row.get('成交额', 0),
                "amplitude": row.get('振幅', 0),
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"成功获取 {symbol} 实时行情")
            return result

        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return {"error": str(e)}

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取个股基本信息

        Args:
            symbol: 股票代码

        Returns:
            股票基本信息
        """
        if not self.available:
            return {"error": "akshare未安装"}

        try:
            # 获取A股个股信息
            df = self.ak.stock_individual_info_em(symbol=symbol)

            # 转换为字典
            info = {}
            if not df.empty:
                for _, row in df.iterrows():
                    key = row.get('item', '')
                    value = row.get('value', '')
                    info[key] = value

            logger.info(f"成功获取 {symbol} 基本信息")
            return info

        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return {"error": str(e)}

    def get_history_capital_flow(
        self,
        stock_code: str,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        获取历史资金流向数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            历史资金流向数据
        """
        if not self.available:
            return pd.DataFrame()

        try:
            # 默认最近3个月
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")

            df = self.ak.stock_individual_fund_flow_rank(
                symbol=stock_code,
                date=start_date
            )

            logger.info(f"成功获取 {stock_code} 历史资金流向数据")
            return df

        except Exception as e:
            logger.error(f"获取历史资金流向失败: {e}")
            return pd.DataFrame()

    def get_margin_trading(self, symbol: str) -> Dict[str, Any]:
        """
        获取融资融券数据

        Args:
            symbol: 股票代码

        Returns:
            融资融券数据
        """
        if not self.available:
            return {"error": "akshare未安装"}

        try:
            df = self.ak.stock_margin_detail_sz(symbol=symbol)

            result = {
                "symbol": symbol,
                "data": df.to_dict('records')[:10] if not df.empty else [],
                "columns": df.columns.tolist() if not df.empty else [],
                "count": len(df) if not df.empty else 0
            }

            logger.info(f"成功获取 {symbol} 融资融券数据")
            return result

        except Exception as e:
            logger.error(f"获取融资融券数据失败: {e}")
            return {"error": str(e)}

    def get_top_list(self, date: str = None) -> pd.DataFrame:
        """
        获取龙虎榜数据（每日汇总）

        Args:
            date: 日期 (YYYYMMDD，默认今日)

        Returns:
            龙虎榜数据
        """
        if not self.available:
            return pd.DataFrame()

        try:
            if not date:
                date = datetime.now().strftime("%Y%m%d")

            # 使用新浪的每日龙虎榜数据
            df = self.ak.stock_lhb_detail_daily_sina(date=date)

            logger.info(f"成功获取 {date} 龙虎榜数据")
            return df

        except Exception as e:
            logger.error(f"获取龙虎榜数据失败: {e}")
            return pd.DataFrame()

    def get_stock_dragon_tiger_detail(
        self,
        symbol: str,
        date: str
    ) -> pd.DataFrame:
        """
        获取指定股票的龙虎榜详情

        Args:
            symbol: 股票代码（如 "600519"）
            date: 日期 (YYYYMMDD)

        Returns:
            该股票在指定日期的龙虎榜详情
        """
        if not self.available:
            return pd.DataFrame()

        try:
            # 先获取该股票有数据的日期列表
            date_df = self.ak.stock_lhb_stock_detail_date_em(symbol=symbol)

            if date_df.empty:
                logger.warning(f"股票 {symbol} 无龙虎榜数据")
                return pd.DataFrame()

            # 检查指定日期是否在列表中
            if date not in date_df['date'].values:
                logger.warning(f"股票 {symbol} 在 {date} 无龙虎榜数据")
                return pd.DataFrame()

            # 获取详细数据
            df = self.ak.stock_lhb_stock_detail_em(
                symbol=symbol,
                date=date
            )

            logger.info(f"成功获取 {symbol} 在 {date} 的龙虎榜详情")
            return df

        except Exception as e:
            logger.error(f"获取股票龙虎榜详情失败: {e}")
            return pd.DataFrame()

    def get_stock_dragon_tiger_dates(self, symbol: str) -> pd.DataFrame:
        """
        获取指定股票的龙虎榜日期列表

        Args:
            symbol: 股票代码

        Returns:
            包含日期的DataFrame
        """
        if not self.available:
            return pd.DataFrame()

        try:
            df = self.ak.stock_lhb_stock_detail_date_em(symbol=symbol)
            logger.info(f"成功获取 {symbol} 的龙虎榜日期列表")
            return df

        except Exception as e:
            logger.error(f"获取龙虎榜日期列表失败: {e}")
            return pd.DataFrame()

    def get_concept_stocks(self, concept_name: str) -> pd.DataFrame:
        """
        获取概念板块成分股

        Args:
            concept_name: 概念名称

        Returns:
            概念成分股列表
        """
        if not self.available:
            return pd.DataFrame()

        try:
            df = self.ak.stock_board_concept_name_em()

            # 过滤指定概念
            concept_data = df[df['板块名称'] == concept_name]

            logger.info(f"成功获取 {concept_name} 概念成分股")
            return concept_data

        except Exception as e:
            logger.error(f"获取概念成分股失败: {e}")
            return pd.DataFrame()


# 便捷函数
def get_akshare_tool() -> AKShareTool:
    """获取AKShare工具实例"""
    return AKShareTool()


if __name__ == "__main__":
    # 测试代码
    print("=" * 70)
    print("AKShare工具测试")
    print("=" * 70)

    tool = AKShareTool()

    if not tool.is_available():
        print("❌ akshare未安装")
        print("请运行: pip install akshare")
        exit(1)

    # 测试1: 获取资金流向
    print("\n[1] 测试获取资金流向数据: 601669 (中国电建)")
    df = tool.get_individual_fund_flow("601669", "sh")
    if not df.empty:
        print(f"获取到 {len(df)} 条记录")
        print(df.head())
    else:
        print("❌ 未获取到数据")

    # 测试2: 获取实时行情
    print("\n[2] 测试获取实时行情")
    quote = tool.get_realtime_quote("601669")
    if "error" not in quote:
        print(f"股票名称: {quote.get('name')}")
        print(f"当前价格: {quote.get('current_price')}")
        print(f"涨跌幅: {quote.get('change_percent'):.2f}%")
    else:
        print(f"❌ {quote['error']}")

    print("\n" + "=" * 70)
    print("测试完成")
