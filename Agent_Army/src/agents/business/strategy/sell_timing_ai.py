"""
卖出时机AI - Sell Timing AI

策略执行军团成员

职责：
1. 技术面卖出信号（趋势反转、形态破位）
2. 基本面卖出信号（业绩恶化、估值过高）
3. 市场面卖出信号（资金流出、市场情绪恶化）
4. 风险控制卖出信号（触发止损、风险过大）
5. 止盈卖出信号（达到目标价、收益兑现）
6. 综合卖出建议

使用工具：
- FinancialTool（财务数据）
- LLMTool（智能分析）
- TechnicalTool（技术指标）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool, LLMTool


class SellTimingAI(BaseAgent, LoggerMixin):
    """
    卖出时机AI - 策略执行军团成员

    核心能力:
    1. 技术面卖出信号（趋势反转、形态破位）
    2. 基本面卖出信号（业绩恶化、估值过高）
    3. 市场面卖出信号（资金流出、市场情绪恶化）
    4. 风险控制卖出信号（触发止损、风险过大）
    5. 止盈卖出信号（达到目标价、收益兑现）
    6. 综合卖出建议

    使用工具:
    - FinancialTool (财务数据)
    - LLMTool (智能分析)
    - TechnicalTool (技术指标)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.financial_tool = FinancialTool()
        self.llm_tool = LLMTool()

        super().__init__(
            name="卖出时机AI",
            role="识别最佳卖出时机，优化卖出策略",
            capabilities=[
                AgentCapability(
                    name="technical_sell_signal",
                    description="技术面卖出信号",
                    input_type="stock_code",
                    output_type="technical_signals"
                ),
                AgentCapability(
                    name="fundamental_sell_signal",
                    description="基本面卖出信号",
                    input_type="stock_code",
                    output_type="fundamental_signals"
                ),
                AgentCapability(
                    name="market_sell_signal",
                    description="市场面卖出信号",
                    input_type="stock_code",
                    output_type="market_signals"
                ),
                AgentCapability(
                    name="sell_timing_decision",
                    description="综合卖出决策",
                    input_type="stock_code",
                    output_type="sell_decision"
                )
            ],
            tools=[
                AgentTool(
                    name="financial_tool",
                    description="财务数据工具",
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

        self.logger.info("卖出时机AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze":
            return await self.analyze(**kwargs)
        elif task == "technical_signals":
            return await self._analyze_technical_signals(**kwargs)
        elif task == "fundamental_signals":
            return await self._analyze_fundamental_signals(**kwargs)
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 主入口方法 ==========

    async def analyze(
        self,
        stock_code: str,
        current_price: float,
        buy_price: float,
        position_value: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        综合卖出时机分析

        Args:
            stock_code: 股票代码
            current_price: 当前股价
            buy_price: 买入价格
            position_value: 持仓市值

        Returns:
            综合卖出时机建议
        """
        self.logger.info(
            f"开始综合卖出时机分析",
            extra={
                "stock_code": stock_code,
                "current_price": current_price,
                "buy_price": buy_price
            }
        )

        # ========== 1. 技术面卖出信号 ==========
        technical_signals = await self._analyze_technical_signals(stock_code, current_price)

        # ========== 2. 基本面卖出信号 ==========
        fundamental_signals = await self._analyze_fundamental_signals(stock_code, current_price)

        # ========== 3. 市场面卖出信号 ==========
        market_signals = await self._analyze_market_signals(stock_code)

        # ========== 4. 风险控制卖出信号 ==========
        risk_signals = self._analyze_risk_signals(current_price, buy_price)

        # ========== 5. 止盈卖出信号 ==========
        profit_signals = self._analyze_profit_signals(current_price, buy_price)

        # ========== 6. 综合卖出决策 ==========
        sell_decision = self._make_sell_decision(
            technical_signals,
            fundamental_signals,
            market_signals,
            risk_signals,
            profit_signals,
            current_price,
            buy_price
        )

        # ========== 7. 构建返回结果 ==========
        result = {
            "analysis_type": "sell_timing",
            "timestamp": datetime.now().isoformat(),
            "stock_code": stock_code,
            "current_price": current_price,
            "buy_price": buy_price,
            "position_value": position_value,
            "profit_loss": round((current_price - buy_price) / buy_price * 100, 2),

            # 技术面信号
            "technical_signals": technical_signals,

            # 基本面信号
            "fundamental_signals": fundamental_signals,

            # 市场面信号
            "market_signals": market_signals,

            # 风险信号
            "risk_signals": risk_signals,

            # 止盈信号
            "profit_signals": profit_signals,

            # 综合决策
            "sell_decision": sell_decision
        }

        self.logger.info(
            f"综合卖出时机分析完成",
            extra={
                "stock_code": stock_code,
                "action": sell_decision["action"],
                "urgency": sell_decision["urgency"]
            }
        )

        return result

    # ========== 核心分析方法 ==========

    async def _analyze_technical_signals(
        self,
        stock_code: str,
        current_price: float
    ) -> Dict[str, Any]:
        """
        技术面卖出信号分析

        Args:
            stock_code: 股票代码
            current_price: 当前股价

        Returns:
            技术面卖出信号
        """
        # TODO: 接入真实技术指标数据
        signals = []

        # 1. 趋势反转信号
        trend_reversal = self._detect_trend_reversal(current_price)
        if trend_reversal["detected"]:
            signals.append({
                "type": "趋势反转",
                "strength": trend_reversal["strength"],
                "description": trend_reversal["description"],
                "priority": "高" if trend_reversal["strength"] >= 0.7 else "中"
            })

        # 2. 形态破位信号
        pattern_breakdown = self._detect_pattern_breakdown(current_price)
        if pattern_breakdown["detected"]:
            signals.append({
                "type": "形态破位",
                "strength": pattern_breakdown["strength"],
                "description": pattern_breakdown["description"],
                "priority": "高"
            })

        # 3. 均线死叉信号
        ma_cross = self._detect_ma_death_cross(current_price)
        if ma_cross["detected"]:
            signals.append({
                "type": "均线死叉",
                "strength": ma_cross["strength"],
                "description": ma_cross["description"],
                "priority": "中"
            })

        # 4. 超买信号
        overbought = self._detect_overbought(current_price)
        if overbought["detected"]:
            signals.append({
                "type": "超买",
                "strength": overbought["strength"],
                "description": overbought["description"],
                "priority": "低"
            })

        # 计算技术面综合卖出强度
        if signals:
            total_strength = sum(s["strength"] for s in signals) / len(signals)
        else:
            total_strength = 0.0

        return {
            "signals": signals,
            "signal_count": len(signals),
            "total_strength": round(total_strength, 2),
            "update_time": datetime.now().isoformat()
        }

    async def _analyze_fundamental_signals(
        self,
        stock_code: str,
        current_price: float
    ) -> Dict[str, Any]:
        """
        基本面卖出信号分析

        Args:
            stock_code: 股票代码
            current_price: 当前股价

        Returns:
            基本面卖出信号
        """
        # 获取财务数据
        financial_data = await self.financial_tool.fetch_financial_data(stock_code)

        signals = []

        # 1. 业绩恶化信号
        performance_decline = self._detect_performance_decline(financial_data)
        if performance_decline["detected"]:
            signals.append({
                "type": "业绩恶化",
                "severity": performance_decline["severity"],
                "description": performance_decline["description"],
                "priority": "高"
            })

        # 2. 估值过高信号
        overvaluation = self._detect_overvaluation(current_price, financial_data)
        if overvaluation["detected"]:
            signals.append({
                "type": "估值过高",
                "severity": overvaluation["severity"],
                "description": overvaluation["description"],
                "priority": "中"
            })

        # 3. 行业景气度下行
        industry_downturn = self._detect_industry_downturn(financial_data)
        if industry_downturn["detected"]:
            signals.append({
                "type": "行业下行",
                "severity": industry_downturn["severity"],
                "description": industry_downturn["description"],
                "priority": "中"
            })

        # 4. 竞争力下降
        competitiveness_decline = self._detect_competitiveness_decline(financial_data)
        if competitiveness_decline["detected"]:
            signals.append({
                "type": "竞争力下降",
                "severity": competitiveness_decline["severity"],
                "description": competitiveness_decline["description"],
                "priority": "中"
            })

        # 计算基本面综合卖出强度
        if signals:
            severity_map = {"高": 1.0, "中": 0.6, "低": 0.3}
            total_severity = sum(severity_map.get(s.get("priority", "低"), 0.3) for s in signals) / len(signals)
        else:
            total_severity = 0.0

        return {
            "signals": signals,
            "signal_count": len(signals),
            "total_severity": round(total_severity, 2),
            "update_time": datetime.now().isoformat()
        }

    async def _analyze_market_signals(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """
        市场面卖出信号分析

        Args:
            stock_code: 股票代码

        Returns:
            市场面卖出信号
        """
        signals = []

        # 1. 资金流出信号
        capital_outflow = self._detect_capital_outflow()
        if capital_outflow["detected"]:
            signals.append({
                "type": "资金流出",
                "intensity": capital_outflow["intensity"],
                "description": capital_outflow["description"],
                "priority": "高"
            })

        # 2. 市场情绪恶化
        sentiment_deterioration = self._detect_sentiment_deterioration()
        if sentiment_deterioration["detected"]:
            signals.append({
                "type": "情绪恶化",
                "intensity": sentiment_deterioration["intensity"],
                "description": sentiment_deterioration["description"],
                "priority": "中"
            })

        # 3. 机构减仓
        institution_selling = self._detect_institution_selling()
        if institution_selling["detected"]:
            signals.append({
                "type": "机构减仓",
                "intensity": institution_selling["intensity"],
                "description": institution_selling["description"],
                "priority": "高"
            })

        # 计算市场面综合卖出强度
        if signals:
            intensity_map = {"高": 1.0, "中": 0.6, "低": 0.3}
            total_intensity = sum(intensity_map.get(s.get("priority", "低"), 0.3) for s in signals) / len(signals)
        else:
            total_intensity = 0.0

        return {
            "signals": signals,
            "signal_count": len(signals),
            "total_intensity": round(total_intensity, 2),
            "update_time": datetime.now().isoformat()
        }

    def _analyze_risk_signals(
        self,
        current_price: float,
        buy_price: float
    ) -> Dict[str, Any]:
        """
        风险控制卖出信号分析

        Args:
            current_price: 当前股价
            buy_price: 买入价格

        Returns:
            风险控制卖出信号
        """
        signals = []

        # 计算盈亏
        loss_pct = ((current_price - buy_price) / buy_price) * 100

        # 1. 止损触发
        if loss_pct <= -8.0:
            signals.append({
                "type": "止损触发",
                "loss_pct": round(loss_pct, 2),
                "description": f"亏损{abs(loss_pct):.2f}%，触发止损",
                "priority": "紧急",
                "action": "立即卖出"
            })
        elif loss_pct <= -5.0:
            signals.append({
                "type": "接近止损",
                "loss_pct": round(loss_pct, 2),
                "description": f"亏损{abs(loss_pct):.2f}%，接近止损线",
                "priority": "高",
                "action": "考虑卖出"
            })

        # 2. 回撤过大
        if -8.0 < loss_pct < -3.0:
            signals.append({
                "type": "回撤较大",
                "loss_pct": round(loss_pct, 2),
                "description": f"回撤{abs(loss_pct):.2f}%，需要关注",
                "priority": "中",
                "action": "密切关注"
            })

        return {
            "signals": signals,
            "signal_count": len(signals),
            "loss_pct": round(loss_pct, 2),
            "update_time": datetime.now().isoformat()
        }

    def _analyze_profit_signals(
        self,
        current_price: float,
        buy_price: float
    ) -> Dict[str, Any]:
        """
        止盈卖出信号分析

        Args:
            current_price: 当前股价
            buy_price: 买入价格

        Returns:
            止盈卖出信号
        """
        signals = []

        # 计算盈利
        profit_pct = ((current_price - buy_price) / buy_price) * 100

        # 1. 达到目标价
        if profit_pct >= 35.0:
            signals.append({
                "type": "大幅盈利",
                "profit_pct": round(profit_pct, 2),
                "description": f"盈利{profit_pct:.2f}%，建议止盈",
                "priority": "高",
                "action": "分批止盈"
            })
        elif profit_pct >= 25.0:
            signals.append({
                "type": "显著盈利",
                "profit_pct": round(profit_pct, 2),
                "description": f"盈利{profit_pct:.2f}%，可考虑止盈",
                "priority": "中",
                "action": "适度止盈"
            })
        elif profit_pct >= 15.0:
            signals.append({
                "type": "适度盈利",
                "profit_pct": round(profit_pct, 2),
                "description": f"盈利{profit_pct:.2f}%，建议跟踪止盈",
                "priority": "低",
                "action": "跟踪止盈"
            })

        return {
            "signals": signals,
            "signal_count": len(signals),
            "profit_pct": round(profit_pct, 2),
            "update_time": datetime.now().isoformat()
        }

    # ========== 综合卖出决策 ==========

    def _make_sell_decision(
        self,
        technical: Dict[str, Any],
        fundamental: Dict[str, Any],
        market: Dict[str, Any],
        risk: Dict[str, Any],
        profit: Dict[str, Any],
        current_price: float,
        buy_price: float
    ) -> Dict[str, Any]:
        """
        综合卖出决策

        Args:
            technical: 技术面信号
            fundamental: 基本面信号
            market: 市场面信号
            risk: 风险信号
            profit: 止盈信号
            current_price: 当前股价
            buy_price: 买入价格

        Returns:
            综合卖出决策
        """
        # 计算总卖出信号强度
        sell_score = (
            technical["total_strength"] * 0.25 +
            fundamental["total_severity"] * 0.30 +
            market["total_intensity"] * 0.25 +
            len(risk["signals"]) * 0.1 +
            len(profit["signals"]) * 0.1
        )

        # 确定卖出动作
        if sell_score >= 0.7:
            action = "强烈建议卖出"
            urgency = "紧急"
            sell_percentage = "80-100%"
        elif sell_score >= 0.5:
            action = "建议卖出"
            urgency = "高"
            sell_percentage = "50-80%"
        elif sell_score >= 0.3:
            action = "考虑减仓"
            urgency = "中"
            sell_percentage = "30-50%"
        else:
            action = "持有观察"
            urgency = "低"
            sell_percentage = "0%"

        # 生成卖出建议
        sell_reasons = []
        if technical["signal_count"] > 0:
            sell_reasons.append(f"技术面{technical['signal_count']}个卖出信号")
        if fundamental["signal_count"] > 0:
            sell_reasons.append(f"基本面{fundamental['signal_count']}个卖出信号")
        if market["signal_count"] > 0:
            sell_reasons.append(f"市场面{market['signal_count']}个卖出信号")
        if risk["signal_count"] > 0:
            sell_reasons.append(f"风险控制{risk['signal_count']}个信号")
        if profit["signal_count"] > 0:
            sell_reasons.append(f"止盈信号{profit['signal_count']}个")

        return {
            "action": action,
            "urgency": urgency,
            "sell_percentage": sell_percentage,
            "sell_score": round(sell_score, 2),
            "sell_reasons": sell_reasons,
            "profit_loss": round((current_price - buy_price) / buy_price * 100, 2),
            "update_time": datetime.now().isoformat()
        }

    # ========== 辅助检测方法 ==========

    def _detect_trend_reversal(self, price: float) -> Dict[str, Any]:
        """检测趋势反转"""
        # TODO: 实现真实检测逻辑
        return {"detected": False, "strength": 0.0, "description": ""}

    def _detect_pattern_breakdown(self, price: float) -> Dict[str, Any]:
        """检测形态破位"""
        return {"detected": False, "strength": 0.0, "description": ""}

    def _detect_ma_death_cross(self, price: float) -> Dict[str, Any]:
        """检测均线死叉"""
        return {"detected": False, "strength": 0.0, "description": ""}

    def _detect_overbought(self, price: float) -> Dict[str, Any]:
        """检测超买"""
        return {"detected": False, "strength": 0.0, "description": ""}

    def _detect_performance_decline(self, data: Dict) -> Dict[str, Any]:
        """检测业绩恶化"""
        return {"detected": False, "severity": 0.0, "description": ""}

    def _detect_overvaluation(self, price: float, data: Dict) -> Dict[str, Any]:
        """检测估值过高"""
        return {"detected": False, "severity": 0.0, "description": ""}

    def _detect_industry_downturn(self, data: Dict) -> Dict[str, Any]:
        """检测行业下行"""
        return {"detected": False, "severity": 0.0, "description": ""}

    def _detect_competitiveness_decline(self, data: Dict) -> Dict[str, Any]:
        """检测竞争力下降"""
        return {"detected": False, "severity": 0.0, "description": ""}

    def _detect_capital_outflow(self) -> Dict[str, Any]:
        """检测资金流出"""
        return {"detected": False, "intensity": 0.0, "description": ""}

    def _detect_sentiment_deterioration(self) -> Dict[str, Any]:
        """检测情绪恶化"""
        return {"detected": False, "intensity": 0.0, "description": ""}

    def _detect_institution_selling(self) -> Dict[str, Any]:
        """检测机构减仓"""
        return {"detected": False, "intensity": 0.0, "description": ""}
