"""
标准化估值公式库
业界公认的估值方法，绝对不允许修改
"""

from typing import Dict


class StandardValuationFormulas:
    """
    标准化估值公式 - 业界公认

    这些公式遵循CFA协会和投资界的标准方法
    不允许任何人修改，包括管理层
    """

    @staticmethod
    def dcf_simplified(data: Dict) -> float:
        """
        DCF 简化版（自由现金流折现）

        内在价值 = 自由现金流 / (折现率 - 增长率)

        业界公认公式，不可修改

        Args:
            data: {
                "free_cash_flow": 自由现金流（元）,
                "discount_rate": 折现率（如 0.1 表示 10%）,
                "growth_rate": 永续增长率（如 0.05 表示 5%）
            }

        Returns:
            内在价值（元）
        """
        free_cash_flow = data.get("free_cash_flow", 0)
        discount_rate = data.get("discount_rate", 0.1)  # 默认10%
        growth_rate = data.get("growth_rate", 0.05)  # 默认5%

        if discount_rate <= growth_rate:
            # 避免分母为0或负数
            return 0.0

        intrinsic_value = free_cash_flow / (discount_rate - growth_rate)

        return round(intrinsic_value, 2)

    @staticmethod
    def dividend_yield(data: Dict) -> float:
        """
        股息率 = 每股股息 / 股价

        业界公认公式，不可修改

        Args:
            data: {
                "dividend_per_share": 每股股息（元）,
                "stock_price": 股价（元）
            }

        Returns:
            股息率百分比
        """
        dividend_per_share = data.get("dividend_per_share", 0)
        stock_price = data.get("stock_price", 1)

        if stock_price == 0:
            return 0.0

        dividend_yield = (dividend_per_share / stock_price) * 100

        return round(dividend_yield, 2)

    @staticmethod
    def peg(data: Dict) -> float:
        """
        PEG = PE / 盈利增长率

        业界公认公式，不可修改
        PEG < 1 通常被认为低估

        Args:
            data: {
                "pe": 市盈率,
                "earnings_growth": 盈利增长率（如 15 表示 15%）
            }

        Returns:
            PEG值
        """
        pe = data.get("pe", 0)
        earnings_growth = data.get("earnings_growth", 1)  # 避免除0

        if earnings_growth == 0:
            return 0.0

        peg = pe / earnings_growth

        return round(peg, 2)

    @staticmethod
    def ev_ebitda(data: Dict) -> float:
        """
        EV/EBITDA = 企业价值 / 息税折旧摊销前利润

        业界公认公式，不可修改

        Args:
            data: {
                "enterprise_value": 企业价值（元）,
                "ebitda": EBITDA（元）
            }

        Returns:
            EV/EBITDA倍数
        """
        enterprise_value = data.get("enterprise_value", 0)
        ebitda = data.get("ebitda", 1)

        if ebitda == 0:
            return 0.0

        ev_ebitda = enterprise_value / ebitda

        return round(ev_ebitda, 2)

    @staticmethod
    def price_to_sales(data: Dict) -> float:
        """
        P/S (市销率) = 市值 / 营业收入

        业界公认公式，不可修改

        Args:
            data: {
                "market_cap": 市值（元）,
                "revenue": 营业收入（元）
            }

        Returns:
            P/S倍数
        """
        market_cap = data.get("market_cap", 0)
        revenue = data.get("revenue", 1)

        if revenue == 0:
            return 0.0

        price_to_sales = market_cap / revenue

        return round(price_to_sales, 2)

    @staticmethod
    def price_to_book(data: Dict) -> float:
        """
        P/B (市净率) = 市值 / 净资产

        业界公认公式，不可修改

        Args:
            data: {
                "market_cap": 市值（元）,
                "net_assets": 净资产（元）
            }

        Returns:
            P/B倍数
        """
        market_cap = data.get("market_cap", 0)
        net_assets = data.get("net_assets", 1)

        if net_assets == 0:
            return 0.0

        price_to_book = market_cap / net_assets

        return round(price_to_book, 2)

    @staticmethod
    def roic(data: Dict) -> float:
        """
        ROIC (投入资本回报率) = NOPAT / 投入资本

        业界公认公式，不可修改

        Args:
            data: {
                "nopat": 税后净营业利润（元）,
                "invested_capital": 投入资本（元）
            }

        Returns:
            ROIC百分比
        """
        nopat = data.get("nopat", 0)
        invested_capital = data.get("invested_capital", 1)

        if invested_capital == 0:
            return 0.0

        roic = (nopat / invested_capital) * 100

        return round(roic, 2)
