"""
宏观经济AI - Macro Economic AI

产业分析军团核心成员

职责：
1. 经济增长分析（GDP、PMI、工业增加值）
2. 货币政策分析（利率、流动性、M2）
3. 财政政策分析（财政收支、赤字率）
4. 通胀分析（CPI、PPI、通胀预期）
5. 汇率分析（人民币汇率、外汇储备）
6. 宏观经济综合评分
7. 投资环境评估

使用工具：
- MacroTool（宏观数据获取）
- FinancialTool（补充数据）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool
from src.core.tools.data_source.macro_tool import MacroTool


class MacroEconomicAI(BaseAgent, LoggerMixin):
    """
    宏观经济AI - 产业分析军团核心成员

    核心能力:
    1. 经济增长分析(GDP、PMI)
    2. 货币政策分析(利率、流动性)
    3. 财政政策分析(政府支出、税收)
    4. 通胀分析(CPI、PPI)
    5. 汇率分析

    使用工具:
    - MacroTool (宏观数据获取)
    - FinancialTool (补充数据)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.macro_tool = MacroTool()
        self.financial_tool = FinancialTool()

        super().__init__(
            name="宏观经济AI",
            role="分析宏观经济形势，评估投资环境",
            capabilities=[
                AgentCapability(
                    name="economic_growth_analysis",
                    description="经济增长分析",
                    input_type="time_range",
                    output_type="growth_report"
                ),
                AgentCapability(
                    name="monetary_policy_analysis",
                    description="货币政策分析",
                    input_type="time_range",
                    output_type="monetary_report"
                ),
                AgentCapability(
                    name="fiscal_policy_analysis",
                    description="财政政策分析",
                    input_type="time_range",
                    output_type="fiscal_report"
                ),
                AgentCapability(
                    name="inflation_analysis",
                    description="通胀分析",
                    input_type="time_range",
                    output_type="inflation_report"
                ),
                AgentCapability(
                    name="exchange_rate_analysis",
                    description="汇率分析",
                    input_type="time_range",
                    output_type="exchange_rate_report"
                ),
                AgentCapability(
                    name="macro_comprehensive_assessment",
                    description="宏观经济综合评估",
                    input_type="time_range",
                    output_type="macro_assessment"
                )
            ],
            tools=[
                AgentTool(
                    name="macro_tool",
                    description="宏观数据获取工具",
                    tool_type="data_source",
                    config={}
                ),
                AgentTool(
                    name="financial_tool",
                    description="财务数据补充工具",
                    tool_type="data_source",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("宏观经济AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze":
            return await self.analyze(**kwargs)
        elif task == "analyze_growth":
            return await self._analyze_economic_growth(**kwargs)
        elif task == "analyze_monetary":
            return await self._analyze_monetary_policy(**kwargs)
        elif task == "analyze_fiscal":
            return await self._analyze_fiscal_policy(**kwargs)
        elif task == "analyze_inflation":
            return await self._analyze_inflation(**kwargs)
        elif task == "analyze_exchange_rate":
            return await self._analyze_exchange_rate(**kwargs)
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 主入口方法 ==========

    async def analyze(
        self,
        time_range: str = "1y",
        **kwargs
    ) -> Dict[str, Any]:
        """
        宏观经济综合分析

        Args:
            time_range: 时间范围（1y, 5y, 10y）

        Returns:
            宏观经济综合报告
        """
        self.logger.info(
            f"开始宏观经济综合分析",
            extra={"time_range": time_range}
        )

        # ========== 1. 并行获取所有数据 ==========
        (
            economic_growth,
            monetary_policy,
            fiscal_policy,
            inflation,
            exchange_rate
        ) = await asyncio.gather(
            self._analyze_economic_growth(time_range),
            self._analyze_monetary_policy(time_range),
            self._analyze_fiscal_policy(time_range),
            self._analyze_inflation(time_range),
            self._analyze_exchange_rate(time_range)
        )

        # ========== 2. 宏观经济综合评分 ==========
        macro_score = self._calculate_macro_score(
            economic_growth,
            monetary_policy,
            fiscal_policy,
            inflation,
            exchange_rate
        )

        # ========== 3. 投资环境评估 ==========
        investment_environment = self._assess_investment_environment(macro_score)

        # ========== 4. 政策导向分析 ==========
        policy_orientation = self._analyze_policy_orientation(
            monetary_policy,
            fiscal_policy
        )

        # ========== 5. 风险预警 ==========
        risk_warnings = self._generate_risk_warnings(
            economic_growth,
            monetary_policy,
            fiscal_policy,
            inflation,
            exchange_rate
        )

        # ========== 6. 投资建议 ==========
        investment_suggestion = self._generate_investment_suggestion(
            macro_score,
            investment_environment,
            policy_orientation,
            risk_warnings
        )

        # ========== 7. 构建返回结果 ==========
        result = {
            "analysis_type": "macro_economic",
            "timestamp": datetime.now().isoformat(),
            "time_range": time_range,

            # 五大维度分析
            "economic_growth": economic_growth,
            "monetary_policy": monetary_policy,
            "fiscal_policy": fiscal_policy,
            "inflation": inflation,
            "exchange_rate": exchange_rate,

            # 综合评估
            "macro_score": macro_score,
            "investment_environment": investment_environment,
            "policy_orientation": policy_orientation,
            "risk_warnings": risk_warnings,

            # 投资建议
            "investment_suggestion": investment_suggestion
        }

        self.logger.info(
            f"宏观经济综合分析完成",
            extra={
                "macro_score": macro_score["total_score"],
                "environment": investment_environment["environment"]
            }
        )

        return result

    # ========== 五大维度分析方法 ==========

    async def _analyze_economic_growth(self, time_range: str) -> Dict[str, Any]:
        """
        经济增长分析

        分析内容:
        1. GDP增长率
        2. PMI（制造业、非制造业、综合）
        3. 工业增加值
        4. 固定资产投资
        """
        # 获取经济增长数据
        growth_data = await self.macro_tool.fetch_economic_growth_data(
            indicators=["gdp", "pmi", "industrial_added_value", "fixed_asset_investment"],
            time_range=time_range
        )

        # GDP分析
        gdp = growth_data.get("gdp", {})
        gdp_analysis = {
            "value": gdp.get("value", 0),
            "trend": gdp.get("trend", "未知"),
            "assessment": self._assess_gdp(gdp.get("value", 0)),
            "score": self._score_gdp(gdp.get("value", 0))
        }

        # PMI分析
        pmi = growth_data.get("pmi", {})
        pmi_analysis = {
            "manufacturing": pmi.get("manufacturing", 50),
            "non_manufacturing": pmi.get("non_manufacturing", 50),
            "composite": pmi.get("composite", 50),
            "assessment": self._assess_pmi(pmi.get("composite", 50)),
            "score": self._score_pmi(pmi.get("composite", 50))
        }

        # 工业增加值分析
        industrial = growth_data.get("industrial_added_value", {})
        industrial_analysis = {
            "value": industrial.get("value", 0),
            "trend": industrial.get("trend", "未知"),
            "assessment": self._assess_industrial(industrial.get("value", 0)),
            "score": self._score_industrial(industrial.get("value", 0))
        }

        # 固定资产投资分析
        investment = growth_data.get("fixed_asset_investment", {})
        investment_analysis = {
            "value": investment.get("value", 0),
            "trend": investment.get("trend", "未知"),
            "assessment": self._assess_investment(investment.get("value", 0)),
            "score": self._score_investment(investment.get("value", 0))
        }

        # 综合评分
        total_score = (
            gdp_analysis["score"] * 0.35 +
            pmi_analysis["score"] * 0.30 +
            industrial_analysis["score"] * 0.20 +
            investment_analysis["score"] * 0.15
        )

        return {
            "gdp": gdp_analysis,
            "pmi": pmi_analysis,
            "industrial_added_value": industrial_analysis,
            "fixed_asset_investment": investment_analysis,
            "total_score": round(total_score, 2),
            "overall_assessment": self._assess_overall_growth(total_score),
            "data_source": growth_data.get("data_source"),
            "update_time": growth_data.get("update_time")
        }

    async def _analyze_monetary_policy(self, time_range: str) -> Dict[str, Any]:
        """
        货币政策分析

        分析内容:
        1. 利率水平（LPR、MLF、逆回购）
        2. M2货币供应量
        3. 社会融资规模
        4. 存款准备金率
        """
        # 获取货币政策数据
        monetary_data = await self.macro_tool.fetch_monetary_policy_data(
            indicators=["interest_rate", "m2", "social_financing", "reserve_ratio"],
            time_range=time_range
        )

        # 利率分析
        interest_rate = monetary_data.get("interest_rate", {})
        interest_analysis = {
            "lpr_1y": interest_rate.get("lpr_1y", 0),
            "lpr_5y": interest_rate.get("lpr_5y", 0),
            "mlf": interest_rate.get("mlf", 0),
            "trend": interest_rate.get("trend", "未知"),
            "assessment": self._assess_interest_rate(interest_rate.get("lpr_1y", 0)),
            "score": self._score_interest_rate(interest_rate.get("trend", "未知"))
        }

        # M2分析
        m2 = monetary_data.get("m2", {})
        m2_analysis = {
            "value": m2.get("value", 0),
            "trend": m2.get("trend", "未知"),
            "assessment": self._assess_m2(m2.get("value", 0)),
            "score": self._score_m2(m2.get("value", 0))
        }

        # 社融分析
        social_financing = monetary_data.get("social_financing", {})
        financing_analysis = {
            "total": social_financing.get("total", 0),
            "yoy_growth": social_financing.get("yoy_growth", 0),
            "assessment": self._assess_financing(social_financing.get("yoy_growth", 0)),
            "score": self._score_financing(social_financing.get("yoy_growth", 0))
        }

        # 存准率分析
        reserve_ratio = monetary_data.get("reserve_ratio", {})
        reserve_analysis = {
            "large_banks": reserve_ratio.get("large_banks", 0),
            "trend": reserve_ratio.get("trend", "未知"),
            "assessment": self._assess_reserve_ratio(reserve_ratio.get("trend", "未知")),
            "score": self._score_reserve_ratio(reserve_ratio.get("trend", "未知"))
        }

        # 综合评分
        total_score = (
            interest_analysis["score"] * 0.35 +
            m2_analysis["score"] * 0.30 +
            financing_analysis["score"] * 0.20 +
            reserve_analysis["score"] * 0.15
        )

        # 货币政策立场
        policy_stance = self._determine_monetary_stance(
            interest_analysis,
            m2_analysis,
            financing_analysis
        )

        return {
            "interest_rate": interest_analysis,
            "m2": m2_analysis,
            "social_financing": financing_analysis,
            "reserve_ratio": reserve_analysis,
            "total_score": round(total_score, 2),
            "policy_stance": policy_stance,
            "data_source": monetary_data.get("data_source"),
            "update_time": monetary_data.get("update_time")
        }

    async def _analyze_fiscal_policy(self, time_range: str) -> Dict[str, Any]:
        """
        财政政策分析

        分析内容:
        1. 财政收入
        2. 财政支出
        3. 财政赤字率
        4. 税收收入
        """
        # 获取财政政策数据
        fiscal_data = await self.macro_tool.fetch_fiscal_policy_data(
            indicators=["fiscal_revenue", "fiscal_expenditure", "deficit_rate", "tax_revenue"],
            time_range=time_range
        )

        # 财政收入分析
        revenue = fiscal_data.get("fiscal_revenue", {})
        revenue_analysis = {
            "total": revenue.get("total", 0),
            "yoy_growth": revenue.get("yoy_growth", 0),
            "assessment": self._assess_fiscal_revenue(revenue.get("yoy_growth", 0)),
            "score": self._score_fiscal_revenue(revenue.get("yoy_growth", 0))
        }

        # 财政支出分析
        expenditure = fiscal_data.get("fiscal_expenditure", {})
        expenditure_analysis = {
            "total": expenditure.get("total", 0),
            "yoy_growth": expenditure.get("yoy_growth", 0),
            "assessment": self._assess_fiscal_expenditure(expenditure.get("yoy_growth", 0)),
            "score": self._score_fiscal_expenditure(expenditure.get("yoy_growth", 0))
        }

        # 赤字率分析
        deficit_rate = fiscal_data.get("deficit_rate", {})
        deficit_analysis = {
            "value": deficit_rate.get("value", 0),
            "trend": deficit_rate.get("trend", "未知"),
            "assessment": self._assess_deficit(deficit_rate.get("value", 0)),
            "score": self._score_deficit(deficit_rate.get("value", 0))
        }

        # 税收收入分析
        tax_revenue = fiscal_data.get("tax_revenue", {})
        tax_analysis = {
            "total": tax_revenue.get("total", 0),
            "yoy_growth": tax_revenue.get("yoy_growth", 0),
            "assessment": self._assess_tax(tax_revenue.get("yoy_growth", 0)),
            "score": self._score_tax(tax_revenue.get("yoy_growth", 0))
        }

        # 综合评分
        total_score = (
            revenue_analysis["score"] * 0.25 +
            expenditure_analysis["score"] * 0.25 +
            deficit_analysis["score"] * 0.30 +
            tax_analysis["score"] * 0.20
        )

        # 财政政策立场
        policy_stance = self._determine_fiscal_stance(
            expenditure_analysis,
            deficit_analysis
        )

        return {
            "fiscal_revenue": revenue_analysis,
            "fiscal_expenditure": expenditure_analysis,
            "deficit_rate": deficit_analysis,
            "tax_revenue": tax_analysis,
            "total_score": round(total_score, 2),
            "policy_stance": policy_stance,
            "data_source": fiscal_data.get("data_source"),
            "update_time": fiscal_data.get("update_time")
        }

    async def _analyze_inflation(self, time_range: str) -> Dict[str, Any]:
        """
        通胀分析

        分析内容:
        1. CPI（居民消费价格指数）
        2. PPI（工业生产者出厂价格指数）
        3. 核心CPI
        4. 通胀预期
        """
        # 获取通胀数据
        inflation_data = await self.macro_tool.fetch_inflation_data(
            indicators=["cpi", "ppi", "core_cpi", "inflation_expectation"],
            time_range=time_range
        )

        # CPI分析
        cpi = inflation_data.get("cpi", {})
        cpi_analysis = {
            "value": cpi.get("value", 0),
            "trend": cpi.get("trend", "未知"),
            "assessment": self._assess_cpi(cpi.get("value", 0)),
            "score": self._score_cpi(cpi.get("value", 0))
        }

        # PPI分析
        ppi = inflation_data.get("ppi", {})
        ppi_analysis = {
            "value": ppi.get("value", 0),
            "trend": ppi.get("trend", "未知"),
            "assessment": self._assess_ppi(ppi.get("value", 0)),
            "score": self._score_ppi(ppi.get("value", 0))
        }

        # 核心CPI分析
        core_cpi = inflation_data.get("core_cpi", {})
        core_cpi_analysis = {
            "value": core_cpi.get("value", 0),
            "assessment": self._assess_core_cpi(core_cpi.get("value", 0)),
            "score": self._score_core_cpi(core_cpi.get("value", 0))
        }

        # 通胀预期分析
        expectation = inflation_data.get("inflation_expectation", {})
        expectation_analysis = {
            "value": expectation.get("value", 0),
            "assessment": self._assess_expectation(expectation.get("value", 0)),
            "score": self._score_expectation(expectation.get("value", 0))
        }

        # 综合评分
        total_score = (
            cpi_analysis["score"] * 0.40 +
            ppi_analysis["score"] * 0.30 +
            core_cpi_analysis["score"] * 0.20 +
            expectation_analysis["score"] * 0.10
        )

        # 通胀环境
        inflation_environment = self._determine_inflation_environment(
            cpi_analysis,
            ppi_analysis,
            core_cpi_analysis
        )

        return {
            "cpi": cpi_analysis,
            "ppi": ppi_analysis,
            "core_cpi": core_cpi_analysis,
            "inflation_expectation": expectation_analysis,
            "total_score": round(total_score, 2),
            "inflation_environment": inflation_environment,
            "data_source": inflation_data.get("data_source"),
            "update_time": inflation_data.get("update_time")
        }

    async def _analyze_exchange_rate(self, time_range: str) -> Dict[str, Any]:
        """
        汇率分析

        分析内容:
        1. 美元兑人民币汇率
        2. 欧元兑人民币汇率
        3. 外汇储备
        """
        # 获取汇率数据
        exchange_data = await self.macro_tool.fetch_exchange_rate_data(
            currencies=["usd_cny", "eur_cny", "foreign_reserve"],
            time_range=time_range
        )

        # 美元汇率分析
        usd_cny = exchange_data.get("usd_cny", {})
        usd_analysis = {
            "value": usd_cny.get("value", 0),
            "change": usd_cny.get("change", 0),
            "change_pct": usd_cny.get("change_pct", 0),
            "trend": usd_cny.get("trend", "未知"),
            "assessment": self._assess_usd_rate(usd_cny.get("value", 0), usd_cny.get("trend", "未知")),
            "score": self._score_usd_rate(usd_cny.get("trend", "未知"))
        }

        # 欧元汇率分析
        eur_cny = exchange_data.get("eur_cny", {})
        eur_analysis = {
            "value": eur_cny.get("value", 0),
            "change": eur_cny.get("change", 0),
            "change_pct": eur_cny.get("change_pct", 0),
            "assessment": self._assess_eur_rate(eur_cny.get("value", 0)),
            "score": self._score_eur_rate(eur_cny.get("change_pct", 0))
        }

        # 外汇储备分析
        reserve = exchange_data.get("foreign_reserve", {})
        reserve_analysis = {
            "value": reserve.get("value", 0),
            "change": reserve.get("change", 0),
            "assessment": self._assess_reserve(reserve.get("value", 0), reserve.get("change", 0)),
            "score": self._score_reserve(reserve.get("change", 0))
        }

        # 综合评分
        total_score = (
            usd_analysis["score"] * 0.50 +
            eur_analysis["score"] * 0.20 +
            reserve_analysis["score"] * 0.30
        )

        # 汇率环境
        exchange_environment = self._determine_exchange_environment(
            usd_analysis,
            reserve_analysis
        )

        return {
            "usd_cny": usd_analysis,
            "eur_cny": eur_analysis,
            "foreign_reserve": reserve_analysis,
            "total_score": round(total_score, 2),
            "exchange_environment": exchange_environment,
            "data_source": exchange_data.get("data_source"),
            "update_time": exchange_data.get("update_time")
        }

    # ========== 综合分析方法 ==========

    def _calculate_macro_score(
        self,
        economic_growth: Dict[str, Any],
        monetary_policy: Dict[str, Any],
        fiscal_policy: Dict[str, Any],
        inflation: Dict[str, Any],
        exchange_rate: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算宏观经济综合评分

        权重分配:
        - 经济增长: 30%
        - 货币政策: 25%
        - 财政政策: 20%
        - 通胀: 15%
        - 汇率: 10%
        """
        weights = {
            "economic_growth": 0.30,
            "monetary_policy": 0.25,
            "fiscal_policy": 0.20,
            "inflation": 0.15,
            "exchange_rate": 0.10
        }

        # 加权平均
        total_score = (
            economic_growth["total_score"] * weights["economic_growth"] +
            monetary_policy["total_score"] * weights["monetary_policy"] +
            fiscal_policy["total_score"] * weights["fiscal_policy"] +
            inflation["total_score"] * weights["inflation"] +
            exchange_rate["total_score"] * weights["exchange_rate"]
        )

        # 评级
        if total_score >= 80:
            rating = "A"
            description = "宏观经济环境优秀，非常适合投资"
        elif total_score >= 70:
            rating = "B"
            description = "宏观经济环境良好，适合投资"
        elif total_score >= 60:
            rating = "C"
            description = "宏观经济环境一般，谨慎投资"
        elif total_score >= 50:
            rating = "D"
            description = "宏观经济环境较差，观望为主"
        else:
            rating = "E"
            description = "宏观经济环境恶劣，不建议投资"

        return {
            "total_score": round(total_score, 2),
            "rating": rating,
            "description": description,
            "dimension_scores": {
                "economic_growth": economic_growth["total_score"],
                "monetary_policy": monetary_policy["total_score"],
                "fiscal_policy": fiscal_policy["total_score"],
                "inflation": inflation["total_score"],
                "exchange_rate": exchange_rate["total_score"]
            },
            "weights": weights
        }

    def _assess_investment_environment(self, macro_score: Dict[str, Any]) -> Dict[str, Any]:
        """评估投资环境"""
        score = macro_score["total_score"]

        if score >= 75:
            environment = "积极"
            risk_level = "低"
            suggestion = "适合积极布局，把握投资机会"
        elif score >= 65:
            environment = "偏积极"
            risk_level = "中低"
            suggestion = "可以适度投资，注意分散风险"
        elif score >= 55:
            environment = "中性"
            risk_level = "中"
            suggestion = "谨慎投资，控制仓位"
        elif score >= 45:
            environment = "偏谨慎"
            risk_level = "中高"
            suggestion = "以观望为主，少量试探性投资"
        else:
            environment = "谨慎"
            risk_level = "高"
            suggestion = "建议观望，等待机会"

        return {
            "environment": environment,
            "risk_level": risk_level,
            "suggestion": suggestion,
            "score": score
        }

    def _analyze_policy_orientation(
        self,
        monetary_policy: Dict[str, Any],
        fiscal_policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析政策导向"""
        monetary_stance = monetary_policy.get("policy_stance", "中性")
        fiscal_stance = fiscal_policy.get("policy_stance", "中性")

        # 综合政策导向
        if "宽松" in monetary_stance and "积极" in fiscal_stance:
            orientation = "双宽松"
            impact = "利好股市、债市"
            confidence = "高"
        elif "宽松" in monetary_stance or "积极" in fiscal_stance:
            orientation = "偏宽松"
            impact = "偏利好"
            confidence = "中"
        elif "紧缩" in monetary_stance or "紧缩" in fiscal_stance:
            orientation = "偏紧缩"
            impact = "偏利空"
            confidence = "中"
        else:
            orientation = "中性"
            impact = "影响有限"
            confidence = "中"

        return {
            "orientation": orientation,
            "monetary_stance": monetary_stance,
            "fiscal_stance": fiscal_stance,
            "market_impact": impact,
            "confidence": confidence
        }

    def _generate_risk_warnings(
        self,
        economic_growth: Dict[str, Any],
        monetary_policy: Dict[str, Any],
        fiscal_policy: Dict[str, Any],
        inflation: Dict[str, Any],
        exchange_rate: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成风险预警"""
        warnings = []

        # 经济增长风险
        if economic_growth["total_score"] < 60:
            warnings.append({
                "type": "经济增长放缓",
                "level": "中",
                "description": f"经济增长评分{economic_growth['total_score']}，存在放缓风险",
                "suggestion": "关注逆周期调节政策"
            })

        # 通胀风险
        cpi_value = inflation["cpi"]["value"]
        if cpi_value > 3.0:
            warnings.append({
                "type": "通胀压力",
                "level": "中高",
                "description": f"CPI同比{cpi_value}%，存在通胀压力",
                "suggestion": "警惕货币政策收紧"
            })
        elif cpi_value < 0:
            warnings.append({
                "type": "通缩风险",
                "level": "中",
                "description": f"CPI同比{cpi_value}%，存在通缩风险",
                "suggestion": "关注刺激政策出台"
            })

        # 汇率风险
        if exchange_rate["usd_cny"]["trend"] == "贬值":
            warnings.append({
                "type": "汇率贬值",
                "level": "中",
                "description": "人民币存在贬值压力",
                "suggestion": "关注外汇储备和资本流动"
            })

        # 财政风险
        if fiscal_policy["deficit_rate"]["value"] > 3.0:
            warnings.append({
                "type": "财政赤字扩大",
                "level": "中低",
                "description": f"财政赤字率{fiscal_policy['deficit_rate']['value']}%",
                "suggestion": "关注财政可持续性"
            })

        return warnings

    def _generate_investment_suggestion(
        self,
        macro_score: Dict[str, Any],
        investment_environment: Dict[str, Any],
        policy_orientation: Dict[str, Any],
        risk_warnings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成投资建议"""
        score = macro_score["total_score"]
        environment = investment_environment["environment"]

        # 投资建议
        if score >= 75:
            action = "积极投资"
            position = "建议仓位70%-80%"
            sectors = "关注成长股、周期股"
            strategy = "逢低布局，把握机会"
        elif score >= 65:
            action = "适度投资"
            position = "建议仓位50%-70%"
            sectors = "关注优质蓝筹、价值股"
            strategy = "分批建仓，控制节奏"
        elif score >= 55:
            action = "谨慎投资"
            position = "建议仓位30%-50%"
            sectors = "关注防御性板块、消费股"
            strategy = "轻仓试探，严格止损"
        elif score >= 45:
            action = "观望为主"
            position = "建议仓位20%-30%"
            sectors = "关注现金、货币基金"
            strategy = "等待机会，不急于入场"
        else:
            action = "建议观望"
            position = "建议仓位0%-20%"
            sectors = "持币观望"
            strategy = "等待宏观环境改善"

        # 风险提示
        risk_tips = []
        if risk_warnings:
            risk_tips = [warning["description"] for warning in risk_warnings[:3]]

        return {
            "action": action,
            "position_suggestion": position,
            "sector_suggestion": sectors,
            "strategy": strategy,
            "risk_tips": risk_tips,
            "policy_benefit": policy_orientation["market_impact"],
            "confidence": policy_orientation["confidence"]
        }

    # ========== 评分和评估辅助方法 ==========

    # GDP评分
    def _assess_gdp(self, value: float) -> str:
        if value >= 6.5:
            return "经济增长强劲"
        elif value >= 5.5:
            return "经济增长平稳"
        elif value >= 4.5:
            return "经济增长放缓"
        else:
            return "经济增长乏力"

    def _score_gdp(self, value: float) -> float:
        if value >= 6.5:
            return 90
        elif value >= 5.5:
            return 75
        elif value >= 4.5:
            return 60
        else:
            return 45

    # PMI评分
    def _assess_pmi(self, value: float) -> str:
        if value >= 52:
            return "制造业景气度高"
        elif value >= 50:
            return "制造业处于扩张区间"
        else:
            return "制造业处于收缩区间"

    def _score_pmi(self, value: float) -> float:
        if value >= 52:
            return 85
        elif value >= 50:
            return 70
        else:
            return 50

    # 其他评分方法（简化版）
    def _assess_industrial(self, value: float) -> str:
        return "工业生产平稳" if value >= 5.0 else "工业生产放缓"

    def _score_industrial(self, value: float) -> float:
        return 75 if value >= 5.0 else 55

    def _assess_investment(self, value: float) -> str:
        return "投资增速平稳" if value >= 5.0 else "投资增速放缓"

    def _score_investment(self, value: float) -> float:
        return 70 if value >= 5.0 else 50

    def _assess_overall_growth(self, score: float) -> str:
        if score >= 75:
            return "经济增长强劲"
        elif score >= 65:
            return "经济增长平稳"
        else:
            return "经济增长承压"

    # 利率评分
    def _assess_interest_rate(self, value: float) -> str:
        return "利率水平适中" if 3.0 <= value <= 4.0 else "利率波动较大"

    def _score_interest_rate(self, trend: str) -> float:
        if trend == "降息":
            return 80
        elif trend == "持平":
            return 70
        else:
            return 55

    # M2评分
    def _assess_m2(self, value: float) -> str:
        return "流动性充裕" if value >= 9.0 else "流动性一般"

    def _score_m2(self, value: float) -> float:
        return 80 if value >= 9.0 else 60

    # 社融评分
    def _assess_financing(self, value: float) -> str:
        return "融资需求旺盛" if value >= 10.0 else "融资需求一般"

    def _score_financing(self, value: float) -> float:
        return 80 if value >= 10.0 else 60

    # 存准率评分
    def _assess_reserve_ratio(self, trend: str) -> str:
        return "货币政策宽松" if trend == "降准" else "货币政策稳健"

    def _score_reserve_ratio(self, trend: str) -> float:
        return 85 if trend == "降准" else 65

    # 货币政策立场
    def _determine_monetary_stance(self, interest, m2, financing) -> str:
        if interest["score"] >= 75 and m2["score"] >= 75:
            return "宽松"
        elif interest["score"] <= 55 or m2["score"] <= 55:
            return "偏紧缩"
        else:
            return "中性"

    # 财政收入评分
    def _assess_fiscal_revenue(self, value: float) -> str:
        return "财政收入增长稳定" if value >= 0 else "财政收入承压"

    def _score_fiscal_revenue(self, value: float) -> float:
        return 75 if value >= 0 else 55

    # 财政支出评分
    def _assess_fiscal_expenditure(self, value: float) -> str:
        return "财政支出力度较大" if value >= 5.0 else "财政支出平稳"

    def _score_fiscal_expenditure(self, value: float) -> float:
        return 80 if value >= 5.0 else 65

    # 赤字率评分
    def _assess_deficit(self, value: float) -> str:
        return "财政赤字可控" if value <= 3.0 else "财政赤字较高"

    def _score_deficit(self, value: float) -> float:
        return 80 if value <= 3.0 else 55

    # 税收评分
    def _assess_tax(self, value: float) -> str:
        return "税收增长稳定" if value >= 0 else "税收承压"

    def _score_tax(self, value: float) -> float:
        return 75 if value >= 0 else 55

    # 财政政策立场
    def _determine_fiscal_stance(self, expenditure, deficit) -> str:
        if expenditure["score"] >= 75:
            return "积极"
        elif deficit["score"] <= 55:
            return "紧缩"
        else:
            return "中性"

    # CPI评分
    def _assess_cpi(self, value: float) -> str:
        if 0 <= value <= 2.5:
            return "通胀温和"
        elif value > 2.5:
            return "通胀压力上升"
        else:
            return "存在通缩风险"

    def _score_cpi(self, value: float) -> float:
        if 0 <= value <= 2.5:
            return 85
        elif value > 2.5:
            return 60
        else:
            return 50

    # PPI评分
    def _assess_ppi(self, value: float) -> str:
        return "工业品价格平稳" if -1.0 <= value <= 1.0 else "工业品价格波动较大"

    def _score_ppi(self, value: float) -> float:
        return 80 if -1.0 <= value <= 1.0 else 55

    # 核心CPI评分
    def _assess_core_cpi(self, value: float) -> str:
        return "核心通胀温和" if 0 <= value <= 2.0 else "核心通胀波动"

    def _score_core_cpi(self, value: float) -> float:
        return 85 if 0 <= value <= 2.0 else 60

    # 通胀预期评分
    def _assess_expectation(self, value: float) -> str:
        return "通胀预期稳定" if 1.5 <= value <= 2.5 else "通胀预期波动"

    def _score_expectation(self, value: float) -> float:
        return 80 if 1.5 <= value <= 2.5 else 60

    # 通胀环境
    def _determine_inflation_environment(self, cpi, ppi, core_cpi) -> str:
        if cpi["score"] >= 75 and ppi["score"] >= 70:
            return "温和通胀，有利于经济增长"
        elif cpi["score"] <= 60:
            return "通胀压力或通缩风险"
        else:
            return "通胀环境中性"

    # 美元汇率评分
    def _assess_usd_rate(self, value: float, trend: str) -> str:
        if trend == "升值":
            return "人民币升值，利好进口"
        elif trend == "贬值":
            return "人民币贬值，利好出口"
        else:
            return "汇率基本稳定"

    def _score_usd_rate(self, trend: str) -> float:
        if trend == "平稳":
            return 80
        elif trend == "升值":
            return 70
        else:
            return 60

    # 欧元汇率评分
    def _assess_eur_rate(self, value: float) -> str:
        return "欧元汇率合理区间"

    def _score_eur_rate(self, change_pct: float) -> float:
        return 70

    # 外汇储备评分
    def _assess_reserve(self, value: float, change: float) -> str:
        if value >= 31000:
            return "外汇储备充足"
        else:
            return "外汇储备稳定"

    def _score_reserve(self, change: float) -> float:
        if abs(change) <= 100:
            return 85
        else:
            return 70

    # 汇率环境
    def _determine_exchange_environment(self, usd, reserve) -> str:
        if usd["score"] >= 75 and reserve["score"] >= 75:
            return "汇率环境稳定"
        else:
            return "汇率波动需关注"
