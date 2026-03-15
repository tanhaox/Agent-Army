"""
标准化财务公式库
业界公认的计算方法，绝对不允许修改
"""

from typing import Dict


class StandardFinancialFormulas:
    """
    标准化财务公式 - 业界公认

    这些公式遵循国际会计准则和中国会计准则
    不允许任何人修改，包括管理层
    """

    @staticmethod
    def roe(data: Dict) -> float:
        """
        ROE (净资产收益率) = 净利润 / 净资产

        业界公认公式，不可修改

        Args:
            data: {
                "net_profit": 净利润（元）,
                "net_assets": 净资产（元）
            }

        Returns:
            ROE百分比（如 15.2 表示 15.2%）
        """
        net_profit = data.get("net_profit", 0)
        net_assets = data.get("net_assets", 1)  # 避免除0

        if net_assets == 0:
            return 0.0

        roe = (net_profit / net_assets) * 100

        return round(roe, 2)

    @staticmethod
    def pe(data: Dict) -> float:
        """
        PE (市盈率) = 股价 / 每股收益

        业界公认公式，不可修改

        Args:
            data: {
                "stock_price": 股价（元）,
                "eps": 每股收益（元）
            }

        Returns:
            PE倍数
        """
        stock_price = data.get("stock_price", 0)
        eps = data.get("eps", 1)  # 避免除0

        if eps == 0:
            return 0.0

        pe = stock_price / eps

        return round(pe, 2)

    @staticmethod
    def pb(data: Dict) -> float:
        """
        PB (市净率) = 股价 / 每股净资产

        业界公认公式，不可修改

        Args:
            data: {
                "stock_price": 股价（元）,
                "net_assets_per_share": 每股净资产（元）
            }

        Returns:
            PB倍数
        """
        stock_price = data.get("stock_price", 0)
        net_assets_per_share = data.get("net_assets_per_share", 1)

        if net_assets_per_share == 0:
            return 0.0

        pb = stock_price / net_assets_per_share

        return round(pb, 2)

    @staticmethod
    def debt_ratio(data: Dict) -> float:
        """
        资产负债率 = 总负债 / 总资产

        业界公认公式，不可修改

        Args:
            data: {
                "total_liabilities": 总负债（元）,
                "total_assets": 总资产（元）
            }

        Returns:
            负债率百分比（如 40.5 表示 40.5%）
        """
        total_liabilities = data.get("total_liabilities", 0)
        total_assets = data.get("total_assets", 1)

        if total_assets == 0:
            return 0.0

        debt_ratio = (total_liabilities / total_assets) * 100

        return round(debt_ratio, 2)

    @staticmethod
    def gross_margin(data: Dict) -> float:
        """
        毛利率 = (营业收入 - 营业成本) / 营业收入

        业界公认公式，不可修改

        Args:
            data: {
                "revenue": 营业收入（元）,
                "cost": 营业成本（元）
            }

        Returns:
            毛利率百分比
        """
        revenue = data.get("revenue", 0)
        cost = data.get("cost", 0)

        if revenue == 0:
            return 0.0

        gross_margin = ((revenue - cost) / revenue) * 100

        return round(gross_margin, 2)

    @staticmethod
    def net_margin(data: Dict) -> float:
        """
        净利率 = 净利润 / 营业收入

        业界公认公式，不可修改

        Args:
            data: {
                "net_profit": 净利润（元）,
                "revenue": 营业收入（元）
            }

        Returns:
            净利率百分比
        """
        net_profit = data.get("net_profit", 0)
        revenue = data.get("revenue", 0)

        if revenue == 0:
            return 0.0

        net_margin = (net_profit / revenue) * 100

        return round(net_margin, 2)

    @staticmethod
    def current_ratio(data: Dict) -> float:
        """
        流动比率 = 流动资产 / 流动负债

        业界公认公式，不可修改

        Args:
            data: {
                "current_assets": 流动资产（元）,
                "current_liabilities": 流动负债（元）
            }

        Returns:
            流动比率
        """
        current_assets = data.get("current_assets", 0)
        current_liabilities = data.get("current_liabilities", 1)

        if current_liabilities == 0:
            return 0.0

        current_ratio = current_assets / current_liabilities

        return round(current_ratio, 2)

    @staticmethod
    def quick_ratio(data: Dict) -> float:
        """
        速动比率 = (流动资产 - 存货) / 流动负债

        业界公认公式，不可修改

        Args:
            data: {
                "current_assets": 流动资产（元）,
                "inventory": 存货（元）,
                "current_liabilities": 流动负债（元）
            }

        Returns:
            速动比率
        """
        current_assets = data.get("current_assets", 0)
        inventory = data.get("inventory", 0)
        current_liabilities = data.get("current_liabilities", 1)

        if current_liabilities == 0:
            return 0.0

        quick_ratio = (current_assets - inventory) / current_liabilities

        return round(quick_ratio, 2)

    @staticmethod
    def eps(data: Dict) -> float:
        """
        EPS (每股收益) = 净利润 / 总股本

        业界公认公式，不可修改

        Args:
            data: {
                "net_profit": 净利润（元）,
                "total_shares": 总股本（股）
            }

        Returns:
            每股收益（元）
        """
        net_profit = data.get("net_profit", 0)
        total_shares = data.get("total_shares", 1)

        if total_shares == 0:
            return 0.0

        eps = net_profit / total_shares

        return round(eps, 2)

    @staticmethod
    def revenue_growth(data: Dict) -> float:
        """
        营收增长率 = (本期营收 - 上期营收) / 上期营收

        业界公认公式，不可修改

        Args:
            data: {
                "revenue": 本期营收（元）,
                "revenue_last": 上期营收（元）
            }

        Returns:
            增长率百分比
        """
        revenue = data.get("revenue", 0)
        revenue_last = data.get("revenue_last", 1)

        if revenue_last == 0:
            return 0.0

        growth = ((revenue - revenue_last) / revenue_last) * 100

        return round(growth, 2)

    @staticmethod
    def profit_growth(data: Dict) -> float:
        """
        净利润增长率 = (本期净利润 - 上期净利润) / 上期净利润

        业界公认公式，不可修改

        Args:
            data: {
                "net_profit": 本期净利润（元）,
                "net_profit_last": 上期净利润（元）
            }

        Returns:
            增长率百分比
        """
        net_profit = data.get("net_profit", 0)
        net_profit_last = data.get("net_profit_last", 1)

        if net_profit_last == 0:
            return 0.0

        growth = ((net_profit - net_profit_last) / net_profit_last) * 100

        return round(growth, 2)
