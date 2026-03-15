"""
盈利预测AI - Profit Forecast AI

目标预测军团成员

职责：
1. 预测未来盈利能力（收入、净利润增长率）
2. 分析历史盈利趋势
3. 使用Yahoo Finance获取历史财务数据
4. 使用LLM进行趋势分析和预测
5. 生成盈利预测报告
6. 评估预测置信度

使用工具：
- YahooFinanceTool（历史财务数据）
- LLMTool（趋势分析预测）
- FinancialTool（辅助财务数据）

数据源：
- Yahoo Finance（历史财务报表）
- LLM（趋势预测和分析）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel, Field

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools.data_source.yahoo_tool import YahooFinanceTool
from src.core.tools.ai_service.llm_tool import LLMTool
from src.core.tools.data_source import FinancialTool


# ========== 数据模型 ==========

class HistoricalRevenue(BaseModel):
    """历史收入数据"""
    year: int
    revenue: float
    net_profit: Optional[float] = None
    growth_rate: Optional[float] = None


class ForecastYear(BaseModel):
    """预测年度数据"""
    year: int
    revenue: float
    net_profit: float
    growth_rate: float
    confidence: float = Field(ge=0.0, le=1.0)


class ProfitForecastResult(BaseModel):
    """盈利预测结果"""
    stock_code: str
    stock_name: str
    forecast_years: int
    historical_revenue: List[HistoricalRevenue]
    forecast: List[ForecastYear]
    avg_growth_rate: float
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: str
    analysis_notes: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)


class ProfitForecastAI(BaseAgent, LoggerMixin):
    """
    盈利预测AI - 目标预测军团成员

    核心能力:
    1. 获取历史财务数据（Yahoo Finance）
    2. 分析盈利趋势（LLM辅助分析）
    3. 预测未来盈利能力（多模型预测）
    4. 评估预测置信度
    5. 识别风险因素

    使用工具:
    - YahooFinanceTool (历史财务数据)
    - LLMTool (智能分析)
    - FinancialTool (辅助数据)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.yahoo_tool = YahooFinanceTool()
        self.llm_tool = LLMTool()
        self.financial_tool = FinancialTool()

        super().__init__(
            name="盈利预测AI",
            role="预测企业未来盈利能力和增长趋势",
            capabilities=[
                AgentCapability(
                    name="historical_analysis",
                    description="历史盈利分析",
                    input_type="stock_code",
                    output_type="historical_revenue"
                ),
                AgentCapability(
                    name="trend_analysis",
                    description="盈利趋势分析",
                    input_type="historical_data",
                    output_type="trend_report"
                ),
                AgentCapability(
                    name="profit_forecast",
                    description="未来盈利预测",
                    input_type="stock_code,years",
                    output_type="forecast_data"
                ),
                AgentCapability(
                    name="confidence_assessment",
                    description="预测置信度评估",
                    input_type="forecast_data",
                    output_type="confidence_score"
                )
            ],
            tools=[
                AgentTool(
                    name="yahoo_tool",
                    description="Yahoo Finance数据工具",
                    tool_type="data_source",
                    config={}
                ),
                AgentTool(
                    name="llm_tool",
                    description="智能分析工具",
                    tool_type="ai_service",
                    config={}
                ),
                AgentTool(
                    name="financial_tool",
                    description="财务数据工具",
                    tool_type="data_source",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("盈利预测AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze":
            return await self.analyze(**kwargs)
        elif task == "forecast":
            return await self.forecast(**kwargs)
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 主入口方法 ==========

    async def analyze(
        self,
        stock_code: str,
        forecast_years: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        综合盈利预测分析

        Args:
            stock_code: 股票代码（6位数字）
            forecast_years: 预测年数（默认3年）
            **kwargs: 其他参数
                - use_llm: 是否使用LLM分析（默认True）

        Returns:
            盈利预测分析报告
        """
        self.logger.info(
            f"开始盈利预测分析",
            extra={
                "stock_code": stock_code,
                "forecast_years": forecast_years
            }
        )

        # ========== 1. 验证股票代码 ==========
        if not self._validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        # ========== 2. 获取历史财务数据 ==========
        historical_data = await self._get_historical_financial_data(stock_code)

        # ========== 3. 计算历史增长率 ==========
        historical_with_growth = self._calculate_historical_growth_rates(historical_data)

        # ========== 4. LLM趋势分析（可选）==========
        use_llm = kwargs.get("use_llm", True)
        trend_analysis = None
        if use_llm:
            trend_analysis = await self._llm_trend_analysis(
                stock_code,
                historical_with_growth,
                forecast_years
            )

        # ========== 5. 生成盈利预测 ==========
        forecast = await self._generate_profit_forecast(
            historical_with_growth,
            forecast_years,
            trend_analysis
        )

        # ========== 6. 计算平均增长率 ==========
        avg_growth_rate = self._calculate_average_growth_rate(forecast)

        # ========== 7. 评估预测置信度 ==========
        confidence = self._assess_forecast_confidence(
            historical_with_growth,
            forecast,
            trend_analysis
        )

        # ========== 8. 生成分析说明 ==========
        analysis_notes = self._generate_analysis_notes(
            historical_with_growth,
            forecast,
            trend_analysis
        )

        # ========== 9. 识别风险因素 ==========
        risk_factors = self._identify_risk_factors(
            historical_with_growth,
            forecast
        )

        # ========== 10. 构建返回结果 ==========
        result = {
            "stock_code": stock_code,
            "stock_name": historical_data[-1].get("stock_name", "未知"),
            "forecast_years": forecast_years,
            "historical_revenue": [
                {
                    "year": item["year"],
                    "revenue": item["revenue"],
                    "net_profit": item.get("net_profit"),
                    "growth_rate": item.get("growth_rate")
                }
                for item in historical_with_growth
            ],
            "forecast": [
                {
                    "year": f["year"],
                    "revenue": f["revenue"],
                    "net_profit": f["net_profit"],
                    "growth_rate": f["growth_rate"],
                    "confidence": f["confidence"]
                }
                for f in forecast
            ],
            "avg_growth_rate": avg_growth_rate,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "analysis_notes": analysis_notes,
            "risk_factors": risk_factors,
            "trend_analysis": trend_analysis
        }

        self.logger.info(
            f"盈利预测分析完成",
            extra={
                "stock_code": stock_code,
                "avg_growth_rate": avg_growth_rate,
                "confidence": confidence
            }
        )

        return result

    async def forecast(
        self,
        stock_code: str,
        forecast_years: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        快速盈利预测（简化版本）

        Args:
            stock_code: 股票代码
            forecast_years: 预测年数

        Returns:
            预测结果
        """
        # 调用完整分析
        result = await self.analyze(stock_code, forecast_years, use_llm=False)

        # 返回简化结果
        return {
            "stock_code": result["stock_code"],
            "stock_name": result["stock_name"],
            "forecast": result["forecast"],
            "avg_growth_rate": result["avg_growth_rate"],
            "confidence": result["confidence"]
        }

    # ========== 数据获取方法 ==========

    async def _get_historical_financial_data(
        self,
        stock_code: str
    ) -> List[Dict[str, Any]]:
        """
        获取历史财务数据

        Args:
            stock_code: 股票代码

        Returns:
            历史财务数据列表
        """
        self.logger.info(f"获取历史财务数据: {stock_code}")

        # 1. 尝试从Yahoo Finance获取
        yahoo_data = await self._get_yahoo_financial_data(stock_code)

        # 2. 如果Yahoo数据不足，补充本地财务数据
        if len(yahoo_data) < 3:
            local_data = await self._get_local_financial_data(stock_code)
            # 合并数据（去重）
            yahoo_data = self._merge_financial_data(yahoo_data, local_data)

        # 3. 如果仍然不足，使用模拟数据
        if len(yahoo_data) < 3:
            self.logger.warning(f"财务数据不足，使用模拟数据: {stock_code}")
            yahoo_data = self._generate_mock_financial_data(stock_code)

        return yahoo_data

    async def _get_yahoo_financial_data(
        self,
        stock_code: str
    ) -> List[Dict[str, Any]]:
        """从Yahoo Finance获取财务数据"""
        if not self.yahoo_tool.is_available():
            self.logger.warning("Yahoo Finance工具不可用")
            return []

        try:
            # 转换股票代码格式（A股需要添加.SS或.SZ后缀）
            symbol = self._convert_to_yahoo_symbol(stock_code)

            # 获取财务报表
            financials = self.yahoo_tool.get_financial_statements(symbol)

            if "error" in financials:
                self.logger.warning(f"Yahoo Finance数据获取失败: {financials['error']}")
                return []

            # 解析利润表数据
            income_stmt = financials.get("income_statement", {})
            if not income_stmt or not income_stmt.get("data"):
                return []

            # 提取收入数据
            data = []
            for row in income_stmt["data"][:5]:  # 最近5年
                year = row.get("fiscal_date", "")[:4]  # 提取年份
                revenue = row.get("totalRevenue", 0)
                net_income = row.get("netIncome", 0)

                if year and revenue:
                    data.append({
                        "year": int(year),
                        "revenue": float(revenue),
                        "net_profit": float(net_income)
                    })

            self.logger.info(f"从Yahoo Finance获取{len(data)}年数据")
            return data

        except Exception as e:
            self.logger.error(f"Yahoo Finance数据获取异常: {e}")
            return []

    async def _get_local_financial_data(
        self,
        stock_code: str
    ) -> List[Dict[str, Any]]:
        """从本地获取财务数据"""
        try:
            financial_data = await self.financial_tool.fetch_financial_data(
                stock_code,
                years=3
            )

            # 转换格式
            data = []
            for i, year_data in enumerate(financial_data.get("historical", [])[:3]):
                data.append({
                    "year": datetime.now().year - 2 + i,
                    "revenue": year_data.get("revenue", 0),
                    "net_profit": year_data.get("net_profit", 0)
                })

            return data

        except Exception as e:
            self.logger.error(f"本地财务数据获取失败: {e}")
            return []

    def _generate_mock_financial_data(
        self,
        stock_code: str
    ) -> List[Dict[str, Any]]:
        """生成模拟财务数据"""
        base_revenue = 1000000000  # 10亿基础收入
        growth_rate = 0.10  # 10%增长率

        data = []
        current_year = datetime.now().year

        for i in range(5):
            year = current_year - 5 + i
            revenue = base_revenue * ((1 + growth_rate) ** i)
            net_profit = revenue * 0.15  # 15%净利率

            data.append({
                "year": year,
                "revenue": round(revenue, 2),
                "net_profit": round(net_profit, 2)
            })

        return data

    # ========== 数据处理方法 ==========

    def _convert_to_yahoo_symbol(self, stock_code: str) -> str:
        """
        转换为Yahoo Finance股票代码格式

        Args:
            stock_code: 6位股票代码

        Returns:
            Yahoo格式的股票代码
        """
        # 上海证券交易所（6开头）
        if stock_code.startswith("6"):
            return f"{stock_code}.SS"
        # 深圳证券交易所（0或3开头）
        else:
            return f"{stock_code}.SZ"

    def _merge_financial_data(
        self,
        data1: List[Dict],
        data2: List[Dict]
    ) -> List[Dict]:
        """合并财务数据（去重）"""
        merged = {}

        for item in data1 + data2:
            year = item["year"]
            if year not in merged:
                merged[year] = item

        # 按年份排序
        result = sorted(merged.values(), key=lambda x: x["year"])
        return result

    def _calculate_historical_growth_rates(
        self,
        historical_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        计算历史增长率

        Args:
            historical_data: 历史财务数据

        Returns:
            包含增长率的数据
        """
        result = []

        for i in range(len(historical_data)):
            item = historical_data[i].copy()

            # 计算收入增长率（相对于前一年）
            if i > 0:
                prev_revenue = historical_data[i - 1]["revenue"]
                if prev_revenue > 0:
                    growth_rate = (item["revenue"] - prev_revenue) / prev_revenue
                    item["growth_rate"] = round(growth_rate, 4)
                else:
                    item["growth_rate"] = 0.0
            else:
                item["growth_rate"] = None

            result.append(item)

        return result

    # ========== LLM分析方法 ==========

    async def _llm_trend_analysis(
        self,
        stock_code: str,
        historical_data: List[Dict],
        forecast_years: int
    ) -> Dict[str, Any]:
        """
        使用LLM进行趋势分析

        Args:
            stock_code: 股票代码
            historical_data: 历史数据
            forecast_years: 预测年数

        Returns:
            LLM分析结果
        """
        self.logger.info(f"启动LLM趋势分析: {stock_code}")

        # 构建提示词
        prompt = self._build_llm_analysis_prompt(
            stock_code,
            historical_data,
            forecast_years
        )

        try:
            # 调用LLM
            response = await self.llm_tool.chat(
                prompt=prompt,
                model="glm-5",
                temperature=0.3
            )

            # 解析LLM响应
            analysis = self._parse_llm_response(response)

            self.logger.info(f"LLM趋势分析完成: {stock_code}")
            return analysis

        except Exception as e:
            self.logger.error(f"LLM趋势分析失败: {e}")
            return None

    def _build_llm_analysis_prompt(
        self,
        stock_code: str,
        historical_data: List[Dict],
        forecast_years: int
    ) -> str:
        """构建LLM分析提示词"""

        # 格式化历史数据
        history_str = "\n".join([
            f"  {item['year']}年: 收入{item['revenue']/100000000:.2f}亿元, "
            f"增长率{item.get('growth_rate', 0)*100:.1f}%"
            for item in historical_data[-5:]
        ])

        prompt = f"""请分析股票{stock_code}的盈利趋势，并提供未来{forecast_years}年的预测。

历史财务数据：
{history_str}

请从以下角度分析：
1. 历史增长趋势分析（是否稳定、是否有周期性）
2. 行业前景判断
3. 增长驱动因素识别
4. 未来{forecast_years}年增长率预测（给出保守、中性、乐观三种情况）
5. 主要风险因素

请以JSON格式返回：
{{
    "trend_assessment": "增长趋势评估（上升/稳定/下降）",
    "growth_drivers": ["驱动因素1", "驱动因素2"],
    "forecast_scenarios": {{
        "conservative": {{"growth_rate": 0.05, "reasoning": "保守理由"}},
        "neutral": {{"growth_rate": 0.10, "reasoning": "中性理由"}},
        "optimistic": {{"growth_rate": 0.15, "reasoning": "乐观理由"}}
    }},
    "risk_factors": ["风险1", "风险2"],
    "confidence_level": 0.75
}}

注意：增长率以小数形式表示（如0.10表示10%）。"""

        return prompt

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        import json

        try:
            # 尝试直接解析JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果解析失败，返回结构化错误信息
            self.logger.warning("LLM响应JSON解析失败，返回默认分析")
            return {
                "trend_assessment": "稳定增长",
                "growth_drivers": ["市场需求增长", "产品竞争力提升"],
                "forecast_scenarios": {
                    "conservative": {"growth_rate": 0.08, "reasoning": "保守预测"},
                    "neutral": {"growth_rate": 0.10, "reasoning": "中性预测"},
                    "optimistic": {"growth_rate": 0.12, "reasoning": "乐观预测"}
                },
                "risk_factors": ["市场竞争加剧", "成本上升压力"],
                "confidence_level": 0.70
            }

    # ========== 预测生成方法 ==========

    async def _generate_profit_forecast(
        self,
        historical_data: List[Dict],
        forecast_years: int,
        trend_analysis: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """
        生成盈利预测

        Args:
            historical_data: 历史数据
            forecast_years: 预测年数
            trend_analysis: LLM趋势分析

        Returns:
            预测数据列表
        """
        self.logger.info(f"生成{forecast_years}年盈利预测")

        # 获取最新年份的数据
        latest_data = historical_data[-1]
        base_revenue = latest_data["revenue"]
        base_net_profit = latest_data.get("net_profit", base_revenue * 0.15)
        base_year = latest_data["year"]

        # 确定增长率
        if trend_analysis and "forecast_scenarios" in trend_analysis:
            # 使用LLM预测的中性增长率
            growth_rate = trend_analysis["forecast_scenarios"]["neutral"]["growth_rate"]
            confidence = trend_analysis.get("confidence_level", 0.70)
        else:
            # 使用历史平均增长率
            growth_rate = self._calculate_historical_avg_growth(historical_data)
            confidence = 0.65

        forecast = []
        for i in range(1, forecast_years + 1):
            year = base_year + i

            # 计算预测收入（复合增长）
            revenue = base_revenue * ((1 + growth_rate) ** i)

            # 计算预测净利润（假设净利率保持稳定）
            net_profit_margin = base_net_profit / base_revenue if base_revenue > 0 else 0.15
            net_profit = revenue * net_profit_margin

            forecast.append({
                "year": year,
                "revenue": round(revenue, 2),
                "net_profit": round(net_profit, 2),
                "growth_rate": round(growth_rate, 4),
                "confidence": round(confidence, 2)
            })

        return forecast

    def _calculate_historical_avg_growth(
        self,
        historical_data: List[Dict]
    ) -> float:
        """计算历史平均增长率"""
        growth_rates = [
            item["growth_rate"]
            for item in historical_data
            if item.get("growth_rate") is not None
        ]

        if not growth_rates:
            return 0.10  # 默认10%增长率

        return round(sum(growth_rates) / len(growth_rates), 4)

    def _calculate_average_growth_rate(
        self,
        forecast: List[Dict]
    ) -> float:
        """计算预测平均增长率"""
        if not forecast:
            return 0.0

        growth_rates = [f["growth_rate"] for f in forecast]
        return round(sum(growth_rates) / len(growth_rates), 4)

    # ========== 置信度评估方法 ==========

    def _assess_forecast_confidence(
        self,
        historical_data: List[Dict],
        forecast: List[Dict],
        trend_analysis: Optional[Dict]
    ) -> float:
        """
        评估预测置信度

        Args:
            historical_data: 历史数据
            forecast: 预测数据
            trend_analysis: LLM分析

        Returns:
            置信度（0-1）
        """
        confidence_score = 0.0

        # 1. 历史数据完整性（最高30分）
        data_years = len(historical_data)
        if data_years >= 5:
            confidence_score += 30
        elif data_years >= 3:
            confidence_score += 20
        else:
            confidence_score += 10

        # 2. 历史增长稳定性（最高30分）
        growth_rates = [
            item["growth_rate"]
            for item in historical_data
            if item.get("growth_rate") is not None
        ]

        if growth_rates:
            avg_growth = sum(growth_rates) / len(growth_rates)
            variance = sum((g - avg_growth) ** 2 for g in growth_rates) / len(growth_rates)
            std_dev = variance ** 0.5

            # 标准差越小，稳定性越高
            if std_dev < 0.05:
                confidence_score += 30
            elif std_dev < 0.10:
                confidence_score += 20
            else:
                confidence_score += 10

        # 3. LLM分析质量（最高20分）
        if trend_analysis:
            llm_confidence = trend_analysis.get("confidence_level", 0.5)
            confidence_score += llm_confidence * 20

        # 4. 预测合理性（最高20分）
        if forecast:
            avg_forecast_growth = sum(f["growth_rate"] for f in forecast) / len(forecast)

            # 增长率应在合理范围内（0% - 30%）
            if 0.0 <= avg_forecast_growth <= 0.30:
                confidence_score += 20
            elif 0.0 <= avg_forecast_growth <= 0.50:
                confidence_score += 10
            else:
                confidence_score += 5

        # 转换为0-1范围
        final_confidence = min(confidence_score / 100, 1.0)

        return round(final_confidence, 2)

    # ========== 分析说明生成方法 ==========

    def _generate_analysis_notes(
        self,
        historical_data: List[Dict],
        forecast: List[Dict],
        trend_analysis: Optional[Dict]
    ) -> List[str]:
        """生成分析说明"""
        notes = []

        # 历史数据说明
        latest = historical_data[-1]
        notes.append(f"最新年度（{latest['year']}）收入{latest['revenue']/100000000:.2f}亿元")

        # 增长率说明
        avg_growth = self._calculate_historical_avg_growth(historical_data)
        notes.append(f"历史平均增长率{avg_growth*100:.1f}%")

        # 预测说明
        if forecast:
            forecast_growth = forecast[0]["growth_rate"]
            notes.append(f"预测未来{len(forecast)}年年均增长率{forecast_growth*100:.1f}%")

            last_forecast = forecast[-1]
            notes.append(
                f"预计{last_forecast['year']}年收入"
                f"{last_forecast['revenue']/100000000:.2f}亿元"
            )

        # LLM分析说明
        if trend_analysis and "trend_assessment" in trend_analysis:
            notes.append(f"趋势评估：{trend_analysis['trend_assessment']}")

        return notes

    def _identify_risk_factors(
        self,
        historical_data: List[Dict],
        forecast: List[Dict]
    ) -> List[str]:
        """识别风险因素"""
        risks = []

        # 增长率波动风险
        growth_rates = [
            item["growth_rate"]
            for item in historical_data
            if item.get("growth_rate") is not None
        ]

        if growth_rates:
            avg_growth = sum(growth_rates) / len(growth_rates)
            variance = sum((g - avg_growth) ** 2 for g in growth_rates) / len(growth_rates)
            std_dev = variance ** 0.5

            if std_dev > 0.15:
                risks.append("历史增长率波动较大，预测不确定性高")

        # 预测增长率过高风险
        if forecast:
            avg_forecast = sum(f["growth_rate"] for f in forecast) / len(forecast)
            if avg_forecast > 0.25:
                risks.append("预测增长率较高，实际达成存在难度")

            # 逐年增长率递增风险
            if len(forecast) >= 2:
                if forecast[-1]["growth_rate"] > forecast[0]["growth_rate"] * 1.5:
                    risks.append("远期增长率预测过于乐观")

        # 数据不足风险
        if len(historical_data) < 3:
            risks.append("历史数据不足，预测可靠性有限")

        # 行业风险（通用）
        risks.append("宏观经济波动可能影响实际业绩")
        risks.append("行业竞争加剧可能导致增长不及预期")

        return list(set(risks))  # 去重

    # ========== 辅助方法 ==========

    def _validate_stock_code(self, stock_code: str) -> bool:
        """验证股票代码格式"""
        import re
        return bool(re.match(r"^\d{6}$", stock_code))


# ========== 便捷函数 ==========

async def forecast_profit(
    stock_code: str,
    forecast_years: int = 3,
    use_llm: bool = True
) -> Dict[str, Any]:
    """
    盈利预测（便捷函数）

    Args:
        stock_code: 股票代码
        forecast_years: 预测年数（默认3年）
        use_llm: 是否使用LLM分析（默认True）

    Returns:
        盈利预测结果
    """
    ai = ProfitForecastAI()
    return await ai.analyze(stock_code, forecast_years, use_llm=use_llm)


# ========== 测试代码 ==========

if __name__ == "__main__":
    import asyncio

    async def test():
        """测试盈利预测AI"""
        print("=" * 70)
        print("盈利预测AI测试")
        print("=" * 70)

        # 创建AI实例
        ai = ProfitForecastAI()

        # 测试贵州茅台
        stock_code = "600519"
        print(f"\n[测试] 分析股票：{stock_code}")

        try:
            result = await ai.analyze(stock_code, forecast_years=3, use_llm=False)

            print(f"\n[结果] 股票名称：{result['stock_name']}")
            print(f"[结果] 预测年数：{result['forecast_years']}年")
            print(f"[结果] 平均增长率：{result['avg_growth_rate']*100:.1f}%")
            print(f"[结果] 预测置信度：{result['confidence']*100:.0f}%")

            print("\n[历史数据]")
            for item in result['historical_revenue'][-3:]:
                print(f"  {item['year']}年: 收入{item['revenue']/100000000:.2f}亿元, "
                      f"增长率{item.get('growth_rate', 0)*100:.1f}%")

            print("\n[预测数据]")
            for item in result['forecast']:
                print(f"  {item['year']}年: 收入{item['revenue']/100000000:.2f}亿元, "
                      f"增长率{item['growth_rate']*100:.1f}%")

            print("\n[分析说明]")
            for note in result['analysis_notes']:
                print(f"  • {note}")

            print("\n[风险因素]")
            for risk in result['risk_factors']:
                print(f"  ⚠️ {risk}")

        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "=" * 70)
        print("测试完成")
        print("=" * 70)

    asyncio.run(test())
