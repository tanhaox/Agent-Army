"""
仓位管理AI - Position Management AI

策略执行军团成员

职责：
1. 仓位配置建议（初始仓位、加仓、减仓）
2. 风险预算管理（单股风险、总风险控制）
3. 动态仓位调整（市场环境、个股表现）
4. 分批建仓策略（分批买入、卖出）
5. 止盈止损策略（动态止盈、止损）
6. 仓位优化建议

使用工具：
- FinancialTool（财务数据）
- LLMTool（智能分析）
- FormulaTool（财务指标计算）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool, LLMTool


class PositionManagementAI(BaseAgent, LoggerMixin):
    """
    仓位管理AI - 策略执行军团成员

    核心能力:
    1. 仓位配置建议（初始仓位、加仓、减仓）
    2. 风险预算管理（单股风险、总风险控制）
    3. 动态仓位调整（市场环境、个股表现）
    4. 分批建仓策略（分批买入、卖出）
    5. 止盈止损策略（动态止盈、止损）
    6. 仓位优化建议

    使用工具:
    - FinancialTool (财务数据)
    - LLMTool (智能分析)
    - FormulaTool (财务指标计算)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.financial_tool = FinancialTool()
        self.llm_tool = LLMTool()

        super().__init__(
            name="仓位管理AI",
            role="优化仓位配置，控制投资风险",
            capabilities=[
                AgentCapability(
                    name="position_sizing",
                    description="仓位配置",
                    input_type="stock_code",
                    output_type="position_size"
                ),
                AgentCapability(
                    name="risk_budgeting",
                    description="风险预算管理",
                    input_type="stock_code",
                    output_type="risk_budget"
                ),
                AgentCapability(
                    name="dynamic_adjustment",
                    description="动态仓位调整",
                    input_type="stock_code",
                    output_type="position_adjustment"
                ),
                AgentCapability(
                    name="stop_loss_take_profit",
                    description="止盈止损策略",
                    input_type="stock_code",
                    output_type="stop_strategy"
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

        self.logger.info("仓位管理AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze":
            return await self.analyze(**kwargs)
        elif task == "position_sizing":
            return await self._position_sizing(**kwargs)
        elif task == "risk_budgeting":
            return await self._risk_budgeting(**kwargs)
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 主入口方法 ==========

    async def analyze(
        self,
        stock_code: str,
        current_price: float,
        total_capital: float,
        risk_tolerance: str = "中等",
        **kwargs
    ) -> Dict[str, Any]:
        """
        仓位管理综合分析

        Args:
            stock_code: 股票代码
            current_price: 当前股价
            total_capital: 总资金
            risk_tolerance: 风险偏好（保守/中等/激进）

        Returns:
            仓位管理综合建议
        """
        self.logger.info(
            f"开始仓位管理综合分析",
            extra={
                "stock_code": stock_code,
                "current_price": current_price,
                "total_capital": total_capital,
                "risk_tolerance": risk_tolerance
            }
        )

        # ========== 1. 仓位配置建议 ==========
        position_sizing = await self._position_sizing(
            stock_code,
            current_price,
            total_capital,
            risk_tolerance
        )

        # ========== 2. 风险预算管理 ==========
        risk_budgeting = await self._risk_budgeting(
            stock_code,
            current_price,
            total_capital,
            risk_tolerance
        )

        # ========== 3. 动态仓位调整 ==========
        dynamic_adjustment = await self._dynamic_adjustment(
            stock_code,
            current_price,
            position_sizing,
            risk_tolerance
        )

        # ========== 4. 分批建仓策略 ==========
        batch_strategy = self._generate_batch_strategy(
            position_sizing,
            current_price
        )

        # ========== 5. 止盈止损策略 ==========
        stop_strategy = self._generate_stop_strategy(
            current_price,
            risk_budgeting
        )

        # ========== 6. 仓位优化建议 ==========
        optimization_suggestion = self._generate_optimization_suggestion(
            position_sizing,
            risk_budgeting,
            dynamic_adjustment
        )

        # ========== 7. 构建返回结果 ==========
        result = {
            "analysis_type": "position_management",
            "timestamp": datetime.now().isoformat(),
            "stock_code": stock_code,
            "current_price": current_price,
            "total_capital": total_capital,
            "risk_tolerance": risk_tolerance,

            # 仓位配置
            "position_sizing": position_sizing,

            # 风险预算
            "risk_budgeting": risk_budgeting,

            # 动态调整
            "dynamic_adjustment": dynamic_adjustment,

            # 分批建仓
            "batch_strategy": batch_strategy,

            # 止盈止损
            "stop_strategy": stop_strategy,

            # 优化建议
            "optimization_suggestion": optimization_suggestion
        }

        self.logger.info(
            f"仓位管理综合分析完成",
            extra={
                "stock_code": stock_code,
                "recommended_position": position_sizing["position_percentage"],
                "position_value": position_sizing["position_value"]
            }
        )

        return result

    # ========== 核心分析方法 ==========

    async def _position_sizing(
        self,
        stock_code: str,
        current_price: float,
        total_capital: float,
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """
        仓位配置建议

        Args:
            stock_code: 股票代码
            current_price: 当前股价
            total_capital: 总资金
            risk_tolerance: 风险偏好

        Returns:
            仓位配置建议
        """
        # 获取财务数据
        financial_data = await self.financial_tool.fetch_financial_data(stock_code)

        # 评估股票质量
        quality_score = self._assess_stock_quality(financial_data)

        # 评估股票波动性
        volatility_score = self._assess_stock_volatility(financial_data)

        # 根据风险偏好确定基础仓位
        risk_adjustments = {
            "保守": 0.5,   # 保守型：降低仓位
            "中等": 1.0,   # 中等型：标准仓位
            "激进": 1.5    # 激进型：提高仓位
        }

        risk_multiplier = risk_adjustments.get(risk_tolerance, 1.0)

        # 计算基础仓位（质量分数越高，仓位越大）
        base_position = (quality_score / 100) * 0.20  # 最高20%

        # 根据波动性调整（波动性越大，仓位越小）
        volatility_adjustment = 1 - (volatility_score / 100) * 0.3  # 最多降低30%

        # 最终仓位
        position_percentage = base_position * volatility_adjustment * risk_multiplier
        position_percentage = min(position_percentage, 0.25)  # 单股最高25%

        # 计算仓位价值
        position_value = total_capital * position_percentage

        # 计算股数
        shares = int(position_value / current_price)

        return {
            "position_percentage": round(position_percentage * 100, 2),
            "position_value": round(position_value, 2),
            "shares": shares,
            "quality_score": quality_score,
            "volatility_score": volatility_score,
            "risk_multiplier": risk_multiplier,
            "description": self._generate_position_description(position_percentage, risk_tolerance),
            "update_time": datetime.now().isoformat()
        }

    async def _risk_budgeting(
        self,
        stock_code: str,
        current_price: float,
        total_capital: float,
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """
        风险预算管理

        Args:
            stock_code: 股票代码
            current_price: 当前股价
            total_capital: 总资金
            risk_tolerance: 风险偏好

        Returns:
            风险预算管理建议
        """
        # 单股最大风险（占总资本的比例）
        max_single_risk = {
            "保守": 0.02,   # 保守型：2%
            "中等": 0.03,   # 中等型：3%
            "激进": 0.05    # 激进型：5%
        }

        single_risk_limit = max_single_risk.get(risk_tolerance, 0.03)

        # 计算最大可接受损失
        max_acceptable_loss = total_capital * single_risk_limit

        # 计算止损价格
        # 假设买入后，最大损失为single_risk_limit
        stop_loss_percentage = 0.08  # 止损8%
        stop_loss_price = current_price * (1 - stop_loss_percentage)

        # 计算可买入股数（基于风险预算）
        risk_based_shares = int(max_acceptable_loss / (current_price - stop_loss_price))

        # 计算风险预算对应的价值
        risk_based_value = risk_based_shares * current_price

        # 总风险预算（假设持有10只股票）
        total_risk_budget = single_risk_limit * 10

        return {
            "single_risk_limit": round(single_risk_limit * 100, 2),
            "max_acceptable_loss": round(max_acceptable_loss, 2),
            "stop_loss_price": round(stop_loss_price, 2),
            "stop_loss_percentage": round(stop_loss_percentage * 100, 2),
            "risk_based_shares": risk_based_shares,
            "risk_based_value": round(risk_based_value, 2),
            "total_risk_budget": round(total_risk_budget * 100, 2),
            "description": f"单股最大风险{single_risk_limit*100}%，总风险预算{total_risk_budget*100}%",
            "update_time": datetime.now().isoformat()
        }

    async def _dynamic_adjustment(
        self,
        stock_code: str,
        current_price: float,
        position_sizing: Dict[str, Any],
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """
        动态仓位调整

        Args:
            stock_code: 股票代码
            current_price: 当前股价
            position_sizing: 仓位配置
            risk_tolerance: 风险偏好

        Returns:
            动态仓位调整建议
        """
        # TODO: 接入真实市场环境数据
        # 当前返回模拟数据

        # 市场环境评估
        market_environment = self._assess_market_environment()

        # 个股表现评估
        stock_performance = self._assess_stock_performance()

        # 调整规则
        adjustments = []

        # 基于市场环境调整
        if market_environment["condition"] == "牛市":
            adjustments.append({
                "factor": "市场环境",
                "action": "加仓",
                "percentage": 2.0,
                "reason": "市场环境向好，适度加仓"
            })
        elif market_environment["condition"] == "熊市":
            adjustments.append({
                "factor": "市场环境",
                "action": "减仓",
                "percentage": -2.0,
                "reason": "市场环境不佳，适度减仓"
            })

        # 基于个股表现调整
        if stock_performance["trend"] == "上涨":
            adjustments.append({
                "factor": "个股表现",
                "action": "持有或加仓",
                "percentage": 1.0,
                "reason": "个股表现良好，可适度加仓"
            })
        elif stock_performance["trend"] == "下跌":
            adjustments.append({
                "factor": "个股表现",
                "action": "减仓或止损",
                "percentage": -1.5,
                "reason": "个股表现不佳，建议减仓"
            })

        # 计算总调整幅度
        total_adjustment = sum(adj["percentage"] for adj in adjustments)

        # 调整后的仓位
        adjusted_position = position_sizing["position_percentage"] + total_adjustment
        adjusted_position = max(0, min(25, adjusted_position))  # 限制在0-25%之间

        return {
            "market_environment": market_environment,
            "stock_performance": stock_performance,
            "adjustments": adjustments,
            "total_adjustment": round(total_adjustment, 2),
            "adjusted_position": round(adjusted_position, 2),
            "update_time": datetime.now().isoformat()
        }

    # ========== 分批建仓策略 ==========

    def _generate_batch_strategy(
        self,
        position_sizing: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """
        生成分批建仓策略

        Args:
            position_sizing: 仓位配置
            current_price: 当前股价

        Returns:
            分批建仓策略
        """
        total_shares = position_sizing["shares"]

        # 分批买入策略（3批）
        buy_strategy = {
            "batch_count": 3,
            "batches": [
                {
                    "batch": 1,
                    "shares": int(total_shares * 0.4),  # 第一批40%
                    "price": current_price,
                    "timing": "立即买入"
                },
                {
                    "batch": 2,
                    "shares": int(total_shares * 0.3),  # 第二批30%
                    "price": round(current_price * 0.97, 2),  # 回调3%时买入
                    "timing": "股价回调3%时"
                },
                {
                    "batch": 3,
                    "shares": int(total_shares * 0.3),  # 第三批30%
                    "price": round(current_price * 0.95, 2),  # 回调5%时买入
                    "timing": "股价回调5%时"
                }
            ],
            "description": "分3批建仓，降低平均成本"
        }

        # 分批卖出策略（3批）
        sell_strategy = {
            "batch_count": 3,
            "batches": [
                {
                    "batch": 1,
                    "shares": int(total_shares * 0.3),  # 第一批30%
                    "price": round(current_price * 1.15, 2),  # 上涨15%时卖出
                    "timing": "股价上涨15%时"
                },
                {
                    "batch": 2,
                    "shares": int(total_shares * 0.3),  # 第二批30%
                    "price": round(current_price * 1.25, 2),  # 上涨25%时卖出
                    "timing": "股价上涨25%时"
                },
                {
                    "batch": 3,
                    "shares": int(total_shares * 0.4),  # 第三批40%
                    "price": round(current_price * 1.35, 2),  # 上涨35%时卖出
                    "timing": "股价上涨35%时"
                }
            ],
            "description": "分3批止盈，锁定收益"
        }

        return {
            "buy_strategy": buy_strategy,
            "sell_strategy": sell_strategy,
            "update_time": datetime.now().isoformat()
        }

    # ========== 止盈止损策略 ==========

    def _generate_stop_strategy(
        self,
        current_price: float,
        risk_budgeting: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成止盈止损策略

        Args:
            current_price: 当前股价
            risk_budgeting: 风险预算

        Returns:
            止盈止损策略
        """
        # 止损策略
        stop_loss = {
            "price": risk_budgeting["stop_loss_price"],
            "percentage": risk_budgeting["stop_loss_percentage"],
            "type": "固定止损",
            "description": f"跌破{risk_budgeting['stop_loss_percentage']}%时止损"
        }

        # 动态止盈策略（跟踪止盈）
        take_profit = {
            "levels": [
                {
                    "level": 1,
                    "price": round(current_price * 1.15, 2),
                    "percentage": 15.0,
                    "action": "止盈30%仓位"
                },
                {
                    "level": 2,
                    "price": round(current_price * 1.25, 2),
                    "percentage": 25.0,
                    "action": "止盈30%仓位"
                },
                {
                    "level": 3,
                    "price": round(current_price * 1.35, 2),
                    "percentage": 35.0,
                    "action": "止盈40%仓位"
                }
            ],
            "trailing_stop": {
                "activation": round(current_price * 1.20, 2),  # 上涨20%后激活
                "trail_percentage": 8.0,  # 回撤8%止盈
                "description": "上涨20%后启动跟踪止盈，回撤8%止盈"
            }
        }

        return {
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "update_time": datetime.now().isoformat()
        }

    # ========== 优化建议生成 ==========

    def _generate_optimization_suggestion(
        self,
        position_sizing: Dict[str, Any],
        risk_budgeting: Dict[str, Any],
        dynamic_adjustment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成仓位优化建议

        Args:
            position_sizing: 仓位配置
            risk_budgeting: 风险预算
            dynamic_adjustment: 动态调整

        Returns:
            仓位优化建议
        """
        suggestions = []

        # 仓位大小建议
        position_pct = position_sizing["position_percentage"]
        if position_pct < 5:
            suggestions.append("仓位较小，可考虑适度加仓至5-10%")
        elif position_pct > 20:
            suggestions.append("仓位较大，注意分散风险，建议不超过20%")

        # 风险控制建议
        if risk_budgeting["single_risk_limit"] > 4:
            suggestions.append("单股风险偏高，建议控制在3%以内")

        # 动态调整建议
        if dynamic_adjustment["total_adjustment"] > 0:
            suggestions.append("当前市场环境和个股表现良好，可适度加仓")
        elif dynamic_adjustment["total_adjustment"] < 0:
            suggestions.append("当前市场环境或个股表现不佳，建议减仓或观望")

        # 分散化建议
        suggestions.append("建议持有8-12只股票，实现适度分散")

        # 定期调整建议
        suggestions.append("建议每月review一次仓位配置，根据市场变化调整")

        return {
            "suggestions": suggestions,
            "priority": "中",
            "update_time": datetime.now().isoformat()
        }

    # ========== 辅助评估方法 ==========

    def _assess_stock_quality(self, data: Dict[str, Any]) -> float:
        """评估股票质量"""
        # TODO: 接入真实数据
        return 75.0  # 质量分数（0-100）

    def _assess_stock_volatility(self, data: Dict[str, Any]) -> float:
        """评估股票波动性"""
        return 40.0  # 波动性分数（0-100）

    def _assess_market_environment(self) -> Dict[str, Any]:
        """评估市场环境"""
        return {
            "condition": "震荡市",
            "trend": "横盘",
            "confidence": 0.65
        }

    def _assess_stock_performance(self) -> Dict[str, Any]:
        """评估个股表现"""
        return {
            "trend": "上涨",
            "momentum": "较强",
            "relative_strength": 0.75
        }

    def _generate_position_description(self, position_pct: float, risk_tolerance: str) -> str:
        """生成仓位描述"""
        if position_pct < 5:
            return f"建议轻仓配置（{position_pct:.1f}%），适合{risk_tolerance}型投资者"
        elif position_pct < 10:
            return f"建议适度配置（{position_pct:.1f}%），适合{risk_tolerance}型投资者"
        elif position_pct < 15:
            return f"建议标准配置（{position_pct:.1f}%），适合{risk_tolerance}型投资者"
        else:
            return f"建议较大配置（{position_pct:.1f}%），注意风险控制"
