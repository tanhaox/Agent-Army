"""
估值与投资建议AI - Valuation and Investment Recommendation AI

目标预测军团核心成员 (整合版)

职责：
1. 多方法估值分析 (PE/PB/DCF)
2. 目标价格预测和上涨空间分析
3. 多维度综合评分 (基本面+技术面+资金面+情绪面)
4. 投资建议生成 (买入/持有/卖出)

整合来源：
- 估值计算AI (ValuationCalculator)
- 目标定价AI (TargetPricingAI)
- 综合评分AI (ComprehensiveScoreAI)

使用工具库：
- FinancialTool (财务数据)
- FormulaTool (估值公式)
- LLMTool (智能分析)

创建日期: 2026-03-14
版本: v2.0 (整合版)
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from src.agents.business.base_business_agent import BusinessAgent
from src.core.base_agent import AgentCapability, AgentTool
from src.core.tools.data_source import FinancialTool
from src.core.tools.calculation import FormulaTool
from src.core.tools.ai_service import LLMTool


class ValuationAndRecommendationAI(BusinessAgent):
    """
    估值与投资建议AI - 整合版

    整合功能：
    1. 多方法估值 (原估值计算AI)
    2. 目标定价 (原目标定价AI)
    3. 综合评分 (原综合评分AI)
    4. 投资建议 (整合三个AI的建议)

    优势：
    - 统一估值逻辑，避免重复计算
    - 共享财务数据，减少API调用
    - 投资建议一致性更强
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具库
        self.financial_tool = FinancialTool()
        self.formula_tool = FormulaTool()
        self.llm_tool = LLMTool()

        super().__init__(
            name="估值与投资建议AI",
            role="估值分析、目标定价、综合评分、投资建议",
            corps="target_forecast",
            analysis_type="valuation_and_recommendation",
            capabilities=[
                # 估值相关能力 (原估值计算AI)
                AgentCapability(
                    name="pe_valuation",
                    description="PE估值",
                    input_type="financial_data",
                    output_type="pe_ratio"
                ),
                AgentCapability(
                    name="pb_valuation",
                    description="PB估值",
                    input_type="financial_data",
                    output_type="pb_ratio"
                ),
                AgentCapability(
                    name="dcf_valuation",
                    description="DCF估值",
                    input_type="cash_flow_data",
                    output_type="intrinsic_value"
                ),
                AgentCapability(
                    name="safety_margin_calc",
                    description="安全边际计算",
                    input_type="intrinsic_value,current_price",
                    output_type="safety_margin"
                ),

                # 目标定价相关能力 (原目标定价AI)
                AgentCapability(
                    name="price_range_determination",
                    description="价格区间确定",
                    input_type="valuation_data",
                    output_type="price_range"
                ),
                AgentCapability(
                    name="target_price_prediction",
                    description="目标价格预测",
                    input_type="price_range",
                    output_type="target_price"
                ),
                AgentCapability(
                    name="upside_analysis",
                    description="上涨空间分析",
                    input_type="current_price,target_price",
                    output_type="upside_percentage"
                ),

                # 综合评分相关能力 (原综合评分AI)
                AgentCapability(
                    name="dimension_scoring",
                    description="维度评分",
                    input_type="stock_data",
                    output_type="dimension_scores"
                ),
                AgentCapability(
                    name="comprehensive_scoring",
                    description="综合评分",
                    input_type="dimension_scores",
                    output_type="comprehensive_score"
                ),
                AgentCapability(
                    name="investment_recommendation",
                    description="投资建议",
                    input_type="valuation,target_price,score",
                    output_type="recommendation"
                )
            ],
            tools=[
                AgentTool(
                    name="financial_tool",
                    description="财务数据工具",
                    tool_type="library",
                    config={}
                ),
                AgentTool(
                    name="formula_tool",
                    description="估值公式工具",
                    tool_type="library",
                    config={}
                ),
                AgentTool(
                    name="llm_tool",
                    description="大模型分析工具",
                    tool_type="library",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("估值与投资建议AI初始化完成（整合版）")

    async def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """
        综合分析：估值 + 目标定价 + 评分 + 建议

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - current_price: 当前价格（可选）
                - analysis_depth: 分析深度（quick/standard/deep）

        Returns:
            综合分析结果
        """
        self.logger.info(f"开始综合分析", extra={"stock_code": stock_code})

        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        # 获取当前价格（如果未提供，使用模拟价格）
        current_price = kwargs.get("current_price", 1800.0)

        # 获取分析深度
        analysis_depth = kwargs.get("analysis_depth", "standard")

        # ========== 1. 获取财务数据（共享数据，避免重复调用）==========
        financial_data = await self.financial_tool.fetch_financial_data(stock_code, years=3)
        latest = financial_data["latest"]

        # ========== 2. 估值分析（原估值计算AI）==========
        valuation = await self._analyze_valuation(stock_code, latest, current_price)

        # ========== 3. 目标定价（原目标定价AI）==========
        target = self._calculate_target_price(valuation, current_price)

        # ========== 4. 综合评分（原综合评分AI）==========
        comprehensive_score = await self._calculate_comprehensive_score(
            stock_code,
            financial_data,
            valuation,
            target
        )

        # ========== 5. 投资建议（整合三个AI的建议）==========
        recommendation = self._generate_investment_recommendation(
            valuation,
            target,
            comprehensive_score
        )

        # ========== 6. 生成综合分析结果 ==========
        result = {
            "stock_code": stock_code,
            "stock_name": financial_data["stock_name"],
            "analysis_type": "valuation_and_recommendation",
            "timestamp": datetime.now().isoformat(),
            "analysis_depth": analysis_depth,

            # 估值分析
            "valuation": {
                "pe_ratio": valuation["pe_ratio"],
                "pb_ratio": valuation["pb_ratio"],
                "intrinsic_value": valuation["intrinsic_value"],
                "valuation_level": valuation["valuation_level"],
                "safety_margin": valuation["safety_margin"],
                "valuation_methods": valuation["methods"]
            },

            # 目标定价
            "target_pricing": {
                "current_price": current_price,
                "target_price": target["target_price"],
                "price_range": target["price_range"],
                "upside_percentage": target["upside_percentage"],
                "upside_description": target["upside_description"]
            },

            # 综合评分
            "comprehensive_score": {
                "total_score": comprehensive_score["total_score"],
                "rating": comprehensive_score["rating"],
                "dimension_scores": comprehensive_score["dimension_scores"],
                "strengths": comprehensive_score["strengths"],
                "weaknesses": comprehensive_score["weaknesses"]
            },

            # 投资建议
            "recommendation": {
                "action": recommendation["action"],
                "confidence": recommendation["confidence"],
                "reasoning": recommendation["reasoning"],
                "risk_warning": recommendation["risk_warning"],
                "investment_horizon": recommendation["investment_horizon"]
            },

            # 总结
            "summary": self._generate_summary(valuation, target, comprehensive_score, recommendation)
        }

        self.logger.info(
            f"综合分析完成",
            extra={
                "stock_code": stock_code,
                "total_score": result["comprehensive_score"]["total_score"],
                "recommendation": result["recommendation"]["action"]
            }
        )

        return result

    # ========== 估值分析（原估值计算AI）==========

    async def _analyze_valuation(
        self,
        stock_code: str,
        financial_data: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """
        多方法估值分析

        Args:
            stock_code: 股票代码
            financial_data: 财务数据
            current_price: 当前价格

        Returns:
            估值分析结果
        """
        self.logger.info(f"开始估值分析", extra={"stock_code": stock_code})

        # 1. PE估值
        pe_data = {
            "stock_price": current_price,
            "earnings_per_share": financial_data.get("net_profit", 0) / 12.56  # 假设总股本
        }
        pe_ratio = self.formula_tool.calculate("pe", pe_data)

        # 2. PB估值
        pb_data = {
            "stock_price": current_price,
            "net_assets_per_share": financial_data.get("net_assets", 0) / 12.56
        }
        pb_ratio = self.formula_tool.calculate("pb", pb_data)

        # 3. DCF估值（简化版）
        intrinsic_value = self._calculate_dcf_valuation(financial_data)

        # 4. 安全边际
        safety_margin = ((intrinsic_value - current_price) / intrinsic_value) * 100

        # 5. 估值水平判断
        valuation_level = self._determine_valuation_level(pe_ratio, pb_ratio, safety_margin)

        # 6. 估值方法详情
        methods = {
            "pe_method": {
                "pe_ratio": pe_ratio,
                "fair_value_pe": financial_data.get("net_profit", 0) * 25 / 12.56,
                "assumption": "合理PE 25倍"
            },
            "pb_method": {
                "pb_ratio": pb_ratio,
                "fair_value_pb": financial_data.get("net_assets", 0) * 3 / 12.56,
                "assumption": "合理PB 3倍"
            },
            "dcf_method": {
                "intrinsic_value": intrinsic_value,
                "assumption": "未来3年增长率10%"
            }
        }

        return {
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "intrinsic_value": intrinsic_value,
            "valuation_level": valuation_level,
            "safety_margin": round(safety_margin, 2),
            "methods": methods
        }

    def _calculate_dcf_valuation(self, financial_data: Dict[str, Any]) -> float:
        """
        DCF估值（简化版）

        Args:
            financial_data: 财务数据

        Returns:
            内在价值
        """
        # 简化DCF模型
        net_profit = financial_data.get("net_profit", 0)
        growth_rate = 0.10  # 假设未来3年增长率10%
        discount_rate = 0.12  # 折现率12%

        # 未来3年现金流预测
        cash_flows = []
        for i in range(1, 4):
            future_cash_flow = net_profit * ((1 + growth_rate) ** i)
            discounted_cash_flow = future_cash_flow / ((1 + discount_rate) ** i)
            cash_flows.append(discounted_cash_flow)

        # 终值（简化计算）
        terminal_value = cash_flows[-1] * 10 / (discount_rate - growth_rate)
        discounted_terminal_value = terminal_value / ((1 + discount_rate) ** 3)

        # 总内在价值
        intrinsic_value = sum(cash_flows) + discounted_terminal_value

        # 每股价值
        total_shares = 12.56  # 假设总股本
        intrinsic_value_per_share = intrinsic_value / total_shares

        return round(intrinsic_value_per_share, 2)

    def _determine_valuation_level(
        self,
        pe_ratio: float,
        pb_ratio: float,
        safety_margin: float
    ) -> str:
        """
        判断估值水平

        Args:
            pe_ratio: PE比率
            pb_ratio: PB比率
            safety_margin: 安全边际

        Returns:
            估值水平 (严重高估/高估/合理/低估/严重低估)
        """
        # 基于PE判断
        if pe_ratio > 50:
            pe_level = "高估"
        elif pe_ratio > 30:
            pe_level = "合理偏高"
        elif pe_ratio > 15:
            pe_level = "合理"
        else:
            pe_level = "低估"

        # 基于PB判断
        if pb_ratio > 8:
            pb_level = "高估"
        elif pb_ratio > 5:
            pb_level = "合理偏高"
        elif pb_ratio > 2:
            pb_level = "合理"
        else:
            pb_level = "低估"

        # 基于安全边际判断
        if safety_margin > 30:
            margin_level = "严重低估"
        elif safety_margin > 15:
            margin_level = "低估"
        elif safety_margin > 0:
            margin_level = "合理"
        elif safety_margin > -15:
            margin_level = "高估"
        else:
            margin_level = "严重高估"

        # 综合判断（权重：安全边际50%, PE 30%, PB 20%）
        if margin_level == "严重低估" or (pe_level == "低估" and pb_level == "低估"):
            return "严重低估"
        elif margin_level == "低估" or (pe_level in ["低估", "合理"] and pb_level in ["低估", "合理"]):
            return "低估"
        elif margin_level == "合理" and pe_level == "合理" and pb_level == "合理":
            return "合理"
        elif margin_level == "高估" or (pe_level in ["高估", "合理偏高"] and pb_level in ["高估", "合理偏高"]):
            return "高估"
        else:
            return "严重高估"

    # ========== 目标定价（原目标定价AI）==========

    def _calculate_target_price(
        self,
        valuation: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """
        计算目标价格和上涨空间

        Args:
            valuation: 估值分析结果
            current_price: 当前价格

        Returns:
            目标定价结果
        """
        self.logger.info("开始计算目标价格")

        # 1. 确定价格区间（基于内在价值）
        intrinsic_value = valuation["intrinsic_value"]

        price_range = {
            "low": intrinsic_value * 0.85,   # 保守价格（15%安全边际）
            "mid": intrinsic_value,          # 合理价格
            "high": intrinsic_value * 1.15   # 乐观价格（15%溢价）
        }

        # 2. 预测目标价格（取合理价格和乐观价格的中位数）
        target_price = (price_range["mid"] + price_range["high"]) / 2

        # 3. 计算上涨空间
        upside_percentage = ((target_price - current_price) / current_price) * 100

        # 4. 上涨空间描述
        if upside_percentage >= 50:
            upside_description = "大幅上涨空间"
        elif upside_percentage >= 30:
            upside_description = "显著上涨空间"
        elif upside_percentage >= 15:
            upside_description = "温和上涨空间"
        elif upside_percentage >= 0:
            upside_description = "有限上涨空间"
        else:
            upside_description = "下跌风险"

        return {
            "target_price": round(target_price, 2),
            "price_range": {
                "low": round(price_range["low"], 2),
                "mid": round(price_range["mid"], 2),
                "high": round(price_range["high"], 2)
            },
            "upside_percentage": round(upside_percentage, 1),
            "upside_description": upside_description
        }

    # ========== 综合评分（原综合评分AI）==========

    async def _calculate_comprehensive_score(
        self,
        stock_code: str,
        financial_data: Dict[str, Any],
        valuation: Dict[str, Any],
        target: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算综合评分

        Args:
            stock_code: 股票代码
            financial_data: 财务数据
            valuation: 估值分析结果
            target: 目标定价结果

        Returns:
            综合评分结果
        """
        self.logger.info(f"开始计算综合评分", extra={"stock_code": stock_code})

        # 1. 基本面评分（40%权重）
        fundamental_score = self._score_fundamentals(financial_data)

        # 2. 技术面评分（25%权重）
        technical_score = await self._score_technical(stock_code)

        # 3. 资金面评分（20%权重）
        capital_score = await self._score_capital(stock_code)

        # 4. 情绪面评分（15%权重）
        sentiment_score = await self._score_sentiment(stock_code)

        # 5. 维度评分汇总
        dimension_scores = {
            "基本面": {
                "score": fundamental_score,
                "weight": 0.40,
                "details": {
                    "财务健康": financial_data["latest"].get("financial_health_score", 70),
                    "盈利能力": financial_data["latest"].get("profitability_score", 75),
                    "成长性": financial_data["latest"].get("growth_score", 65),
                    "估值水平": 85 if valuation["valuation_level"] in ["低估", "严重低估"] else 60
                }
            },
            "技术面": {
                "score": technical_score,
                "weight": 0.25,
                "details": {
                    "趋势强度": technical_score * 0.95,
                    "成交量": technical_score * 1.05,
                    "技术指标": technical_score
                }
            },
            "资金面": {
                "score": capital_score,
                "weight": 0.20,
                "details": {
                    "主力资金": capital_score * 1.1,
                    "北向资金": capital_score * 0.9,
                    "融资余额": capital_score
                }
            },
            "情绪面": {
                "score": sentiment_score,
                "weight": 0.15,
                "details": {
                    "市场热度": sentiment_score * 1.2,
                    "机构评级": sentiment_score * 0.9,
                    "舆情情感": sentiment_score
                }
            }
        }

        # 6. 计算综合评分
        total_score = sum(
            dim_data["score"] * dim_data["weight"]
            for dim_data in dimension_scores.values()
        )

        # 7. 评级
        rating = self._get_rating(total_score)

        # 8. 优势劣势分析
        strengths = self._identify_strengths(dimension_scores)
        weaknesses = self._identify_weaknesses(dimension_scores)

        return {
            "total_score": round(total_score, 1),
            "rating": rating,
            "dimension_scores": dimension_scores,
            "strengths": strengths,
            "weaknesses": weaknesses
        }

    def _score_fundamentals(self, financial_data: Dict[str, Any]) -> float:
        """基本面评分"""
        latest = financial_data["latest"]

        # 财务健康度
        debt_ratio = latest.get("debt_ratio", 50)
        health_score = max(0, 100 - debt_ratio)

        # 盈利能力
        roe = latest.get("roe", 10)
        profitability_score = min(100, roe * 4)

        # 成长性
        revenue_growth = latest.get("revenue_growth", 10)
        growth_score = min(100, 50 + revenue_growth * 2.5)

        # 综合评分
        return (health_score * 0.4 + profitability_score * 0.3 + growth_score * 0.3)

    async def _score_technical(self, stock_code: str) -> float:
        """技术面评分（简化版）"""
        # TODO: 集成TA-Lib进行完整技术分析
        # 当前返回模拟数据
        return 70.0

    async def _score_capital(self, stock_code: str) -> float:
        """资金面评分（简化版）"""
        # TODO: 调用资金流向AI获取数据
        return 65.0

    async def _score_sentiment(self, stock_code: str) -> float:
        """情绪面评分（简化版）"""
        # TODO: 调用市场情绪AI获取数据
        return 60.0

    def _get_rating(self, score: float) -> str:
        """获取评级"""
        if score >= 85:
            return "强烈推荐"
        elif score >= 75:
            return "推荐"
        elif score >= 65:
            return "中性"
        elif score >= 55:
            return "谨慎"
        else:
            return "不推荐"

    def _identify_strengths(self, dimension_scores: Dict[str, Any]) -> List[str]:
        """识别优势维度"""
        strengths = []
        for dim_name, dim_data in dimension_scores.items():
            if dim_data["score"] >= 75:
                strengths.append(f"{dim_name}优秀（{dim_data['score']:.1f}分）")
        return strengths if strengths else ["无明显优势"]

    def _identify_weaknesses(self, dimension_scores: Dict[str, Any]) -> List[str]:
        """识别劣势维度"""
        weaknesses = []
        for dim_name, dim_data in dimension_scores.items():
            if dim_data["score"] < 60:
                weaknesses.append(f"{dim_name}较弱（{dim_data['score']:.1f}分）")
        return weaknesses if weaknesses else ["暂无明显劣势"]

    # ========== 投资建议（整合三个AI）==========

    def _generate_investment_recommendation(
        self,
        valuation: Dict[str, Any],
        target: Dict[str, Any],
        comprehensive_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成投资建议（整合三个AI的建议）

        Args:
            valuation: 估值分析结果
            target: 目标定价结果
            comprehensive_score: 综合评分结果

        Returns:
            投资建议
        """
        self.logger.info("生成投资建议")

        # 1. 基于估值的建议
        valuation_recommendation = self._get_valuation_recommendation(valuation)

        # 2. 基于目标价格的建议
        target_recommendation = self._get_target_recommendation(target)

        # 3. 基于综合评分的建议
        score_recommendation = self._get_score_recommendation(comprehensive_score)

        # 4. 整合建议（投票机制）
        recommendations = [
            valuation_recommendation["action"],
            target_recommendation["action"],
            score_recommendation["action"]
        ]

        # 统计投票
        from collections import Counter
        vote_result = Counter(recommendations)
        final_action = vote_result.most_common(1)[0][0]

        # 5. 计算置信度
        confidence = self._calculate_confidence(
            valuation_recommendation,
            target_recommendation,
            score_recommendation
        )

        # 6. 生成推理
        reasoning = self._generate_reasoning(
            valuation,
            target,
            comprehensive_score,
            final_action
        )

        # 7. 风险警告
        risk_warning = self._generate_risk_warning(valuation, target)

        # 8. 投资期限
        investment_horizon = self._determine_investment_horizon(comprehensive_score)

        return {
            "action": final_action,
            "confidence": confidence,
            "reasoning": reasoning,
            "risk_warning": risk_warning,
            "investment_horizon": investment_horizon,
            "details": {
                "valuation_recommendation": valuation_recommendation,
                "target_recommendation": target_recommendation,
                "score_recommendation": score_recommendation
            }
        }

    def _get_valuation_recommendation(self, valuation: Dict[str, Any]) -> Dict[str, Any]:
        """基于估值的建议"""
        level = valuation["valuation_level"]

        if level in ["严重低估", "低估"]:
            return {"action": "STRONG_BUY", "confidence": 0.8, "reason": f"估值{level}"}
        elif level == "合理":
            return {"action": "BUY", "confidence": 0.6, "reason": "估值合理"}
        elif level == "高估":
            return {"action": "HOLD", "confidence": 0.7, "reason": "估值偏高"}
        else:
            return {"action": "SELL", "confidence": 0.8, "reason": "估值严重高估"}

    def _get_target_recommendation(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """基于目标价格的建议"""
        upside = target["upside_percentage"]

        if upside >= 40:
            return {"action": "STRONG_BUY", "confidence": 0.8, "reason": f"上涨空间{upside:.1f}%"}
        elif upside >= 20:
            return {"action": "BUY", "confidence": 0.7, "reason": f"上涨空间{upside:.1f}%"}
        elif upside >= 0:
            return {"action": "HOLD", "confidence": 0.6, "reason": "上涨空间有限"}
        else:
            return {"action": "SELL", "confidence": 0.7, "reason": f"下跌风险{abs(upside):.1f}%"}

    def _get_score_recommendation(self, comprehensive_score: Dict[str, Any]) -> Dict[str, Any]:
        """基于综合评分的建议"""
        rating = comprehensive_score["rating"]

        if rating == "强烈推荐":
            return {"action": "STRONG_BUY", "confidence": 0.8, "reason": f"综合评分{comprehensive_score['total_score']:.1f}分"}
        elif rating == "推荐":
            return {"action": "BUY", "confidence": 0.7, "reason": f"综合评分{comprehensive_score['total_score']:.1f}分"}
        elif rating == "中性":
            return {"action": "HOLD", "confidence": 0.6, "reason": "中性评级"}
        elif rating == "谨慎":
            return {"action": "WAIT", "confidence": 0.7, "reason": "谨慎评级"}
        else:
            return {"action": "SELL", "confidence": 0.8, "reason": "不推荐评级"}

    def _calculate_confidence(
        self,
        valuation_rec: Dict[str, Any],
        target_rec: Dict[str, Any],
        score_rec: Dict[str, Any]
    ) -> float:
        """计算置信度"""
        # 如果三个建议一致，置信度高
        actions = [valuation_rec["action"], target_rec["action"], score_rec["action"]]
        if len(set(actions)) == 1:
            return 0.85
        elif len(set(actions)) == 2:
            return 0.70
        else:
            return 0.55

    def _generate_reasoning(
        self,
        valuation: Dict[str, Any],
        target: Dict[str, Any],
        comprehensive_score: Dict[str, Any],
        action: str
    ) -> str:
        """生成推理说明"""
        parts = []

        # 估值角度
        parts.append(f"估值{valuation['valuation_level']}（安全边际{valuation['safety_margin']:.1f}%）")

        # 目标价格角度
        parts.append(f"目标价{target['target_price']:.2f}元（{target['upside_description']}）")

        # 综合评分角度
        parts.append(f"综合评分{comprehensive_score['total_score']:.1f}分（{comprehensive_score['rating']}）")

        # 行动建议
        action_map = {
            "STRONG_BUY": "强烈建议买入",
            "BUY": "建议买入",
            "HOLD": "建议持有",
            "WAIT": "建议观望",
            "SELL": "建议卖出"
        }

        return "；".join(parts) + f"。{action_map.get(action, '未知')}。"

    def _generate_risk_warning(
        self,
        valuation: Dict[str, Any],
        target: Dict[str, Any]
    ) -> str:
        """生成风险警告"""
        warnings = []

        if valuation["pe_ratio"] > 40:
            warnings.append("PE估值偏高")

        if target["upside_percentage"] < 0:
            warnings.append("存在下跌风险")

        if valuation["safety_margin"] < 0:
            warnings.append("安全边际不足")

        return "；".join(warnings) if warnings else "暂无明显风险"

    def _determine_investment_horizon(self, comprehensive_score: Dict[str, Any]) -> str:
        """确定投资期限"""
        score = comprehensive_score["total_score"]

        if score >= 80:
            return "长期持有（1年以上）"
        elif score >= 70:
            return "中期持有（6-12个月）"
        elif score >= 60:
            return "短期持有（3-6个月）"
        else:
            return "观望或短期操作"

    # ========== 总结生成 ==========

    def _generate_summary(
        self,
        valuation: Dict[str, Any],
        target: Dict[str, Any],
        comprehensive_score: Dict[str, Any],
        recommendation: Dict[str, Any]
    ) -> str:
        """生成总结"""
        parts = [
            f"估值{valuation['valuation_level']}，安全边际{valuation['safety_margin']:.1f}%",
            f"目标价{target['target_price']:.2f}元，{target['upside_description']}",
            f"综合评分{comprehensive_score['total_score']:.1f}分（{comprehensive_score['rating']}）",
            f"投资建议：{recommendation['action']}（置信度{recommendation['confidence']*100:.0f}%）"
        ]

        return "；".join(parts) + "。"


# ========== 便捷函数 ==========

async def analyze_valuation_and_recommendation(
    stock_code: str,
    current_price: float = None,
    analysis_depth: str = "standard"
) -> Dict[str, Any]:
    """
    估值与投资建议分析（便捷函数）

    Args:
        stock_code: 股票代码
        current_price: 当前价格（可选）
        analysis_depth: 分析深度（quick/standard/deep）

    Returns:
        综合分析结果
    """
    ai = ValuationAndRecommendationAI()
    kwargs = {"analysis_depth": analysis_depth}
    if current_price:
        kwargs["current_price"] = current_price
    return await ai.analyze(stock_code, **kwargs)
