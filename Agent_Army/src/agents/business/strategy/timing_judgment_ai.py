"""
时机判断AI - Timing Judgment AI

策略部成员 (1/4)

职责：
1. 买入时机判断 - 识别最佳买入时机
2. 卖出时机判断 - 识别最佳卖出时机

合并来源：
- 买入时机AI
- 卖出时机AI

使用工具：
- TechnicalTool（技术指标）
- MarketTool（市场数据）
- LLMTool（智能分析）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import get_logger


class TimingJudgmentAI(BusinessAgent):
    """
    时机判断AI - 策略部成员 (1/4)

    核心能力:
    1. 买入时机判断 - 技术面+基本面+市场面
    2. 卖出时机判断 - 止盈+止损+趋势反转

    使用工具:
    - TechnicalTool (技术指标)
    - MarketTool (市场数据)
    - LLMTool (智能分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="时机判断AI",
            role="判断最佳买卖时机",
            corps="strategy",
            analysis_type="timing_judgment",
            capabilities=[
                AgentCapability(
                    name="buy_timing",
                    description="买入时机判断",
                    input_type="stock_code",
                    output_type="buy_signal"
                ),
                AgentCapability(
                    name="sell_timing",
                    description="卖出时机判断",
                    input_type="stock_code",
                    output_type="sell_signal"
                )
            ],
            tools=[
                AgentTool(
                    name="technical_tool",
                    description="技术指标工具",
                    tool_type="data_source",
                    config={}
                ),
                AgentTool(
                    name="market_tool",
                    description="市场数据工具",
                    tool_type="data_source",
                    config={}
                ),
                AgentTool(
                    name="llm_tool",
                    description="智能分析工具",
                    tool_type="ai_service",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("时机判断AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行时机判断分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - current_price: 当前股价（必需）
                - position_cost: 持仓成本（可选）

        Returns:
            分析结果
        """
        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        current_price = kwargs.get("current_price")
        if not current_price:
            raise ValueError("缺少current_price参数")

        position_cost = kwargs.get("position_cost")

        self.logger.info(
            f"开始时机判断分析",
            extra={
                "stock_code": stock_code,
                "current_price": current_price,
                "position_cost": position_cost
            }
        )

        # ========== 1. 买入时机判断 ==========
        buy_timing = await self._analyze_buy_timing(
            stock_code,
            current_price
        )

        # ========== 2. 卖出时机判断 ==========
        sell_timing = await self._analyze_sell_timing(
            stock_code,
            current_price,
            position_cost
        )

        # ========== 3. 综合时机评分 ==========
        timing_score = self._calculate_timing_score(buy_timing, sell_timing)

        # ========== 4. 操作建议 ==========
        action_suggestion = self._generate_action_suggestion(
            buy_timing,
            sell_timing,
            timing_score
        )

        # ========== 5. 风险提示 ==========
        risks = self._identify_risks(buy_timing, sell_timing)

        # ========== 6. 建议 ==========
        recommendations = self._generate_recommendations(
            buy_timing,
            sell_timing,
            action_suggestion
        )

        # ========== 7. 构建分析结果 ==========
        details = {
            "current_price": current_price,
            "position_cost": position_cost,

            # 买入时机
            "buy_timing": buy_timing,

            # 卖出时机
            "sell_timing": sell_timing,

            # 综合评分
            "timing_score": timing_score,

            # 操作建议
            "action_suggestion": action_suggestion,

            # 时间戳
            "timestamp": datetime.now().isoformat()
        }

        result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=self._generate_conclusion(action_suggestion, timing_score),
            confidence=timing_score["confidence"],
            details=details,
            risks=risks,
            recommendations=recommendations
        )

        self.logger.info(
            f"时机判断分析完成",
            extra={
                "stock_code": stock_code,
                "action": action_suggestion["action"],
                "score": timing_score["overall_score"]
            }
        )

        return result

    # ========== 买入时机判断 ==========

    async def _analyze_buy_timing(
        self,
        stock_code: str,
        current_price: float
    ) -> Dict[str, Any]:
        """
        买入时机判断

        Args:
            stock_code: 股票代码
            current_price: 当前股价

        Returns:
            买入时机分析
        """
        # TODO: 接入真实数据
        # 当前使用模拟数据

        # 1. 技术面买入信号
        technical_signal = self._analyze_buy_technical(current_price)

        # 2. 基本面买入信号
        fundamental_signal = self._analyze_buy_fundamental()

        # 3. 市场面买入信号
        market_signal = self._analyze_buy_market()

        # 4. 综合买入信号
        buy_signal = self._combine_buy_signals(
            technical_signal,
            fundamental_signal,
            market_signal
        )

        return {
            "signal": buy_signal["signal"],
            "strength": buy_signal["strength"],
            "confidence": buy_signal["confidence"],
            "technical": technical_signal,
            "fundamental": fundamental_signal,
            "market": market_signal,
            "entry_points": buy_signal["entry_points"],
            "description": buy_signal["description"]
        }

    def _analyze_buy_technical(self, current_price: float) -> Dict[str, Any]:
        """技术面买入信号"""
        # TODO: 接入真实技术指标
        # 模拟数据

        # 假设技术指标
        ma5 = current_price * 0.98
        ma10 = current_price * 0.96
        ma20 = current_price * 0.94

        # 均线多头排列
        is_bullish_alignment = ma5 > ma10 > ma20

        # RSI指标
        rsi = 45.0  # 中性偏低，未超买

        # MACD指标
        macd_signal = "金叉"

        # 综合技术评分
        score = 0
        if is_bullish_alignment:
            score += 30
        if 30 <= rsi <= 50:  # RSI中性偏弱，有上涨空间
            score += 25
        if macd_signal == "金叉":
            score += 25

        return {
            "score": score,
            "indicators": {
                "ma_alignment": "多头排列" if is_bullish_alignment else "非多头",
                "rsi": rsi,
                "macd": macd_signal
            },
            "support_level": round(current_price * 0.95, 2),
            "resistance_level": round(current_price * 1.10, 2),
            "description": "技术面出现买入信号" if score >= 50 else "技术面观望"
        }

    def _analyze_buy_fundamental(self) -> Dict[str, Any]:
        """基本面买入信号"""
        # TODO: 接入真实基本面数据
        # 模拟数据

        # 假设基本面指标
        pe_ratio = 15.0
        industry_pe = 18.0
        peg_ratio = 0.8
        roe = 18.0

        # 综合评分
        score = 0
        if pe_ratio < industry_pe:
            score += 25
        if peg_ratio < 1.0:
            score += 25
        if roe > 15:
            score += 25

        return {
            "score": score,
            "valuation": {
                "pe_ratio": pe_ratio,
                "industry_pe": industry_pe,
                "peg_ratio": peg_ratio
            },
            "profitability": {
                "roe": roe
            },
            "description": "基本面估值合理，具备投资价值" if score >= 50 else "基本面一般"
        }

    def _analyze_buy_market(self) -> Dict[str, Any]:
        """市场面买入信号"""
        # TODO: 接入真实市场数据
        # 模拟数据

        # 假设市场指标
        market_trend = "震荡上行"
        capital_flow = "主力流入"
        market_sentiment = 65.0  # 市场情绪

        # 综合评分
        score = 0
        if market_trend in ["上涨", "震荡上行"]:
            score += 20
        if capital_flow == "主力流入":
            score += 25
        if market_sentiment > 60:
            score += 20

        return {
            "score": score,
            "market_trend": market_trend,
            "capital_flow": capital_flow,
            "market_sentiment": market_sentiment,
            "description": "市场环境向好" if score >= 40 else "市场环境一般"
        }

    def _combine_buy_signals(
        self,
        technical: Dict[str, Any],
        fundamental: Dict[str, Any],
        market: Dict[str, Any]
    ) -> Dict[str, Any]:
        """综合买入信号"""
        # 权重分配
        weights = {
            "technical": 0.40,
            "fundamental": 0.40,
            "market": 0.20
        }

        # 加权评分
        total_score = (
            technical["score"] * weights["technical"] +
            fundamental["score"] * weights["fundamental"] +
            market["score"] * weights["market"]
        )

        # 生成信号
        if total_score >= 70:
            signal = "强烈买入"
            strength = "强"
            entry_points = ["突破阻力位", "回调支撑位"]
        elif total_score >= 50:
            signal = "买入"
            strength = "中"
            entry_points = ["回调买入", "分批建仓"]
        elif total_score >= 30:
            signal = "观望"
            strength = "弱"
            entry_points = ["等待更明确信号"]
        else:
            signal = "不买入"
            strength = "无"
            entry_points = []

        # 置信度
        confidence = min(0.9, total_score / 100)

        return {
            "signal": signal,
            "strength": strength,
            "confidence": round(confidence, 2),
            "entry_points": entry_points,
            "description": f"买入信号{signal}，综合评分{total_score:.1f}分"
        }

    # ========== 卖出时机判断 ==========

    async def _analyze_sell_timing(
        self,
        stock_code: str,
        current_price: float,
        position_cost: Optional[float]
    ) -> Dict[str, Any]:
        """
        卖出时机判断

        Args:
            stock_code: 股票代码
            current_price: 当前股价
            position_cost: 持仓成本

        Returns:
            卖出时机分析
        """
        # 1. 技术面卖出信号
        technical_signal = self._analyze_sell_technical(current_price)

        # 2. 止盈信号
        take_profit_signal = self._analyze_take_profit(
            current_price,
            position_cost
        )

        # 3. 止损信号
        stop_loss_signal = self._analyze_stop_loss(
            current_price,
            position_cost
        )

        # 4. 综合卖出信号
        sell_signal = self._combine_sell_signals(
            technical_signal,
            take_profit_signal,
            stop_loss_signal
        )

        return {
            "signal": sell_signal["signal"],
            "strength": sell_signal["strength"],
            "confidence": sell_signal["confidence"],
            "technical": technical_signal,
            "take_profit": take_profit_signal,
            "stop_loss": stop_loss_signal,
            "exit_points": sell_signal["exit_points"],
            "description": sell_signal["description"]
        }

    def _analyze_sell_technical(self, current_price: float) -> Dict[str, Any]:
        """技术面卖出信号"""
        # TODO: 接入真实技术指标
        # 模拟数据

        # 假设技术指标
        rsi = 65.0  # 接近超买
        macd_signal = "死叉迹象"

        # 综合评分
        score = 0
        if rsi > 70:
            score += 30
        elif rsi > 60:
            score += 15

        if macd_signal == "死叉":
            score += 25
        elif macd_signal == "死叉迹象":
            score += 15

        return {
            "score": score,
            "indicators": {
                "rsi": rsi,
                "macd": macd_signal
            },
            "resistance_level": round(current_price * 1.15, 2),
            "description": "技术面出现卖出信号" if score >= 30 else "技术面未出现卖出信号"
        }

    def _analyze_take_profit(
        self,
        current_price: float,
        position_cost: Optional[float]
    ) -> Dict[str, Any]:
        """止盈信号分析"""
        if not position_cost:
            return {
                "score": 0,
                "profit_rate": 0,
                "description": "无持仓，不考虑止盈"
            }

        # 计算盈利比例
        profit_rate = ((current_price - position_cost) / position_cost) * 100

        # 止盈评分
        score = 0
        if profit_rate >= 50:
            score = 50
            description = "盈利超过50%，建议止盈"
        elif profit_rate >= 30:
            score = 40
            description = "盈利超过30%，考虑止盈"
        elif profit_rate >= 20:
            score = 20
            description = "盈利超过20%，可部分止盈"
        else:
            score = 0
            description = "盈利空间有限，暂不止盈"

        return {
            "score": score,
            "profit_rate": round(profit_rate, 2),
            "description": description
        }

    def _analyze_stop_loss(
        self,
        current_price: float,
        position_cost: Optional[float]
    ) -> Dict[str, Any]:
        """止损信号分析"""
        if not position_cost:
            return {
                "score": 0,
                "loss_rate": 0,
                "description": "无持仓，不考虑止损"
            }

        # 计算亏损比例
        loss_rate = ((position_cost - current_price) / position_cost) * 100

        # 止损评分
        score = 0
        if loss_rate >= 15:
            score = 50
            description = "亏损超过15%，建议止损"
        elif loss_rate >= 10:
            score = 40
            description = "亏损超过10%，考虑止损"
        elif loss_rate >= 7:
            score = 20
            description = "亏损超过7%，警惕风险"
        else:
            score = 0
            description = "亏损可控，暂不止损"

        return {
            "score": score,
            "loss_rate": round(loss_rate, 2),
            "description": description
        }

    def _combine_sell_signals(
        self,
        technical: Dict[str, Any],
        take_profit: Dict[str, Any],
        stop_loss: Dict[str, Any]
    ) -> Dict[str, Any]:
        """综合卖出信号"""
        # 最高评分
        max_score = max(
            technical["score"],
            take_profit["score"],
            stop_loss["score"]
        )

        # 生成信号
        if max_score >= 50:
            signal = "强烈卖出"
            strength = "强"
            exit_points = ["立即卖出", "分批减仓"]
        elif max_score >= 30:
            signal = "卖出"
            strength = "中"
            exit_points = ["考虑减仓", "设置止损"]
        elif max_score >= 15:
            signal = "观望"
            strength = "弱"
            exit_points = ["密切关注"]
        else:
            signal = "持有"
            strength = "无"
            exit_points = []

        # 置信度
        confidence = min(0.9, max_score / 100)

        return {
            "signal": signal,
            "strength": strength,
            "confidence": round(confidence, 2),
            "exit_points": exit_points,
            "description": f"卖出信号{signal}，最高评分{max_score:.1f}分"
        }

    # ========== 综合评分 ==========

    def _calculate_timing_score(
        self,
        buy_timing: Dict[str, Any],
        sell_timing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算综合时机评分"""
        buy_signal = buy_timing["signal"]
        sell_signal = sell_timing["signal"]

        # 综合评分逻辑
        if buy_signal in ["强烈买入", "买入"] and sell_signal == "持有":
            overall_score = 85
            action = "买入"
        elif buy_signal == "观望" and sell_signal == "持有":
            overall_score = 60
            action = "观望"
        elif sell_signal in ["强烈卖出", "卖出"]:
            overall_score = 30
            action = "卖出"
        else:
            overall_score = 50
            action = "观望"

        # 置信度（买入和卖出置信度的平均）
        confidence = (buy_timing["confidence"] + sell_timing["confidence"]) / 2

        return {
            "overall_score": overall_score,
            "action": action,
            "confidence": round(confidence, 2)
        }

    def _generate_action_suggestion(
        self,
        buy_timing: Dict[str, Any],
        sell_timing: Dict[str, Any],
        timing_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成操作建议"""
        action = timing_score["action"]

        if action == "买入":
            return {
                "action": "买入",
                "timing": "良好",
                "entry_strategy": buy_timing["entry_points"],
                "position_suggestion": "可分批建仓",
                "risk_control": "设置止损位"
            }
        elif action == "卖出":
            return {
                "action": "卖出",
                "timing": "合适",
                "exit_strategy": sell_timing["exit_points"],
                "position_suggestion": "分批减仓",
                "risk_control": "及时止损"
            }
        else:
            return {
                "action": "观望",
                "timing": "等待",
                "entry_strategy": ["等待更明确信号"],
                "position_suggestion": "保持观察",
                "risk_control": "控制仓位"
            }

    # ========== 风险识别 ==========

    def _identify_risks(
        self,
        buy_timing: Dict[str, Any],
        sell_timing: Dict[str, Any]
    ) -> List[str]:
        """识别风险"""
        risks = []

        # 买入风险
        if buy_timing["signal"] in ["强烈买入", "买入"]:
            if buy_timing["confidence"] < 0.7:
                risks.append("买入信号置信度较低，存在误判风险")

        # 卖出风险
        if sell_timing["signal"] in ["强烈卖出", "卖出"]:
            if sell_timing["technical"]["score"] > 30:
                risks.append("技术面出现卖出信号，注意风险")

        # 止损风险
        if sell_timing["stop_loss"]["score"] >= 20:
            risks.append(f"持仓亏损{sell_timing['stop_loss']['loss_rate']:.1f}%，注意止损")

        if not risks:
            risks.append("时机判断相对明确，风险可控")

        return risks

    # ========== 建议生成 ==========

    def _generate_recommendations(
        self,
        buy_timing: Dict[str, Any],
        sell_timing: Dict[str, Any],
        action_suggestion: Dict[str, Any]
    ) -> List[str]:
        """生成投资建议"""
        recommendations = []

        action = action_suggestion["action"]

        if action == "买入":
            recommendations.append(f"当前为买入时机，{buy_timing['description']}")
            for entry_point in action_suggestion["entry_strategy"][:2]:
                recommendations.append(f"建议{entry_point}")
        elif action == "卖出":
            recommendations.append(f"当前为卖出时机，{sell_timing['description']}")
            for exit_point in action_suggestion["exit_strategy"][:2]:
                recommendations.append(f"建议{exit_point}")
        else:
            recommendations.append("当前观望为主，等待更明确信号")
            recommendations.append("可关注后续技术面和基本面变化")

        return recommendations

    # ========== 辅助方法 ==========

    def _generate_conclusion(
        self,
        action_suggestion: Dict[str, Any],
        timing_score: Dict[str, Any]
    ) -> str:
        """生成核心结论"""
        return (
            f"操作建议【{action_suggestion['action']}】，"
            f"时机评分{timing_score['overall_score']}分，"
            f"置信度{timing_score['confidence'] * 100:.0f}%"
        )


# 便捷函数
async def analyze_timing_judgment(
    stock_code: str,
    current_price: float,
    position_cost: Optional[float] = None
) -> AnalysisResult:
    """
    时机判断分析（便捷函数）

    Args:
        stock_code: 股票代码
        current_price: 当前股价
        position_cost: 持仓成本

    Returns:
        分析结果
    """
    ai = TimingJudgmentAI()
    return await ai.analyze(
        stock_code,
        current_price=current_price,
        position_cost=position_cost
    )
