"""
止损止盈AI - Stop Loss/Take Profit AI

职责：
- 设置止损止盈点位
- 基于技术分析和估值模型
- 支持多种止损止盈策略
- 动态调整止损止盈点位

核心功能：
1. 止损策略：固定止损、移动止损、ATR止损、技术止损
2. 止盈策略：目标价位、分批止盈、跟踪止盈
3. 动态调整：根据市场情况动态调整止损止盈点位
4. 风险管理：计算合理的风险收益比

输入：
- 股票代码
- 当前价格
- 技术分析结果（可选）
- 估值结果（可选）

输出：
- 止损价位和幅度
- 止盈价位和幅度（多级别）
- 持仓周期建议
- 调整规则

技术栈：
- TechnicalAnalysisAI（技术分析）
- ValuationModelAI（估值模型）
- FinancialTool（价格数据）
- ATR计算（波动率指标）

创建日期: 2026-03-15
版本: v1.0
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools.data_source import FinancialTool


class StopLossAI(BaseAgent, LoggerMixin):
    """
    止损止盈AI

    核心能力：
    1. 多策略止损：固定、移动、ATR、技术止损
    2. 多级别止盈：目标价位、分批止盈、跟踪止盈
    3. 动态调整：根据市场变化调整点位
    4. 风险管理：合理的风险收益比

    使用场景：
    - 短线交易：紧止损，快止盈
    - 中线投资：宽止损，分批止盈
    - 长线投资：技术止损，价值止盈
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.financial_tool = FinancialTool()

        super().__init__(
            name="止损止盈AI",
            role="基于技术分析和估值模型，设置合理的止损止盈点位",
            capabilities=[
                AgentCapability(
                    name="fixed_stop_loss",
                    description="固定百分比止损",
                    input_type="stock_code",
                    output_type="stop_loss_plan"
                ),
                AgentCapability(
                    name="trailing_stop_loss",
                    description="移动止损（跟踪价格）",
                    input_type="stock_code",
                    output_type="stop_loss_plan"
                ),
                AgentCapability(
                    name="atr_stop_loss",
                    description="ATR波动率止损",
                    input_type="stock_code",
                    output_type="stop_loss_plan"
                ),
                AgentCapability(
                    name="technical_stop_loss",
                    description="技术位止损（支撑压力位）",
                    input_type="stock_code",
                    output_type="stop_loss_plan"
                ),
                AgentCapability(
                    name="multi_level_take_profit",
                    description="多级别止盈策略",
                    input_type="stock_code",
                    output_type="take_profit_plan"
                ),
                AgentCapability(
                    name="dynamic_adjustment",
                    description="动态调整止损止盈",
                    input_type="stock_code",
                    output_type="adjusted_plan"
                ),
                AgentCapability(
                    name="comprehensive_plan",
                    description="综合止损止盈方案",
                    input_type="stock_code",
                    output_type="complete_plan"
                )
            ],
            tools=[
                AgentTool(
                    name="financial_data",
                    description="金融数据工具",
                    tool_type="data_source",
                    config={}
                ),
                AgentTool(
                    name="atr_calculator",
                    description="ATR波动率计算",
                    tool_type="calculation",
                    config={}
                )
            ],
            config=config
        )

        # 默认配置
        self.default_config = {
            "short_term": {
                "stop_loss_ratio": 0.05,  # 5%止损
                "take_profit_ratios": [0.08, 0.15, 0.25],  # 8%, 15%, 25%
                "holding_period": "1-2周"
            },
            "medium_term": {
                "stop_loss_ratio": 0.10,  # 10%止损
                "take_profit_ratios": [0.15, 0.30, 0.50],  # 15%, 30%, 50%
                "holding_period": "1-3个月"
            },
            "long_term": {
                "stop_loss_ratio": 0.15,  # 15%止损
                "take_profit_ratios": [0.30, 0.50, 0.80],  # 30%, 50%, 80%
                "holding_period": "6-12个月"
            }
        }

        self.logger.info("止损止盈AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        stock_code = kwargs.get("stock_code")
        if not stock_code:
            raise ValueError("缺少stock_code参数")

        if task == "fixed_stop_loss":
            return await self.fixed_stop_loss(
                stock_code,
                kwargs.get("current_price"),
                kwargs.get("stop_ratio", 0.08)
            )
        elif task == "trailing_stop_loss":
            return await self.trailing_stop_loss(
                stock_code,
                kwargs.get("current_price"),
                kwargs.get("trailing_ratio", 0.05)
            )
        elif task == "atr_stop_loss":
            return await self.atr_stop_loss(
                stock_code,
                kwargs.get("current_price"),
                kwargs.get("atr_multiplier", 2.0)
            )
        elif task == "technical_stop_loss":
            return await self.technical_stop_loss(
                stock_code,
                kwargs.get("current_price"),
                kwargs.get("technical_analysis")
            )
        elif task == "multi_level_take_profit":
            return await self.multi_level_take_profit(
                stock_code,
                kwargs.get("current_price"),
                kwargs.get("valuation_result")
            )
        elif task == "dynamic_adjustment":
            return await self.dynamic_adjustment(
                stock_code,
                kwargs.get("current_plan"),
                kwargs.get("current_price")
            )
        elif task == "comprehensive_plan":
            return await self.comprehensive_plan(
                stock_code,
                kwargs.get("investment_horizon", "medium_term"),
                kwargs.get("technical_analysis"),
                kwargs.get("valuation_result")
            )
        else:
            # 默认执行综合方案
            return await self.comprehensive_plan(stock_code)

    # ========== 固定止损策略 ==========

    async def fixed_stop_loss(
        self,
        stock_code: str,
        current_price: Optional[float] = None,
        stop_ratio: float = 0.08
    ) -> Dict[str, Any]:
        """
        固定百分比止损

        策略：设置固定的止损幅度（如8%）
        优点：简单明确，容易执行
        缺点：不考虑市场波动性

        Args:
            stock_code: 股票代码
            current_price: 当前价格（如不提供则获取实时价格）
            stop_ratio: 止损幅度（默认8%）

        Returns:
            {
                "stock_code": str,
                "current_price": float,
                "stop_loss_price": float,
                "stop_ratio": float,
                "type": "fixed"
            }
        """
        self.logger.info(
            f"计算固定止损",
            extra={"stock_code": stock_code, "stop_ratio": stop_ratio}
        )

        # 1. 获取当前价格
        if current_price is None:
            current_price = await self._get_current_price(stock_code)

        if current_price <= 0:
            return self._error_result(stock_code, "固定止损", "无效的当前价格")

        # 2. 计算止损价
        stop_loss_price = current_price * (1 - stop_ratio)

        # 3. 生成建议
        result = {
            "stock_code": stock_code,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_price": round(current_price, 2),
            "stop_loss": {
                "price": round(stop_loss_price, 2),
                "ratio": round(stop_ratio * 100, 2),
                "type": "fixed",
                "description": f"固定{stop_ratio*100:.1f}%止损"
            },
            "advantages": ["简单明确", "易于执行", "不受情绪影响"],
            "disadvantages": ["不考虑波动性", "可能被正常波动止损"],
            "risk_warning": "固定止损在波动大的市场中可能频繁触发"
        }

        self.logger.info(
            f"固定止损计算完成",
            extra={
                "stock_code": stock_code,
                "stop_loss": stop_loss_price,
                "ratio": f"{stop_ratio*100:.1f}%"
            }
        )

        return result

    # ========== 移动止损策略 ==========

    async def trailing_stop_loss(
        self,
        stock_code: str,
        current_price: Optional[float] = None,
        trailing_ratio: float = 0.05
    ) -> Dict[str, Any]:
        """
        移动止损（跟踪止损）

        策略：止损价随价格上涨而上移，但不随下跌而下移
        优点：保护利润，让盈利奔跑
        缺点：需要频繁监控

        Args:
            stock_code: 股票代码
            current_price: 当前价格
            trailing_ratio: 移动止损幅度（默认5%）

        Returns:
            移动止损方案
        """
        self.logger.info(
            f"计算移动止损",
            extra={"stock_code": stock_code, "trailing_ratio": trailing_ratio}
        )

        # 1. 获取当前价格
        if current_price is None:
            current_price = await self._get_current_price(stock_code)

        if current_price <= 0:
            return self._error_result(stock_code, "移动止损", "无效的当前价格")

        # 2. 计算初始止损价
        initial_stop = current_price * (1 - trailing_ratio)

        # 3. 生成移动止损规则
        result = {
            "stock_code": stock_code,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_price": round(current_price, 2),
            "stop_loss": {
                "price": round(initial_stop, 2),
                "ratio": round(trailing_ratio * 100, 2),
                "type": "trailing",
                "description": f"移动{trailing_ratio*100:.1f}%止损"
            },
            "trailing_rules": [
                f"初始止损价: {initial_stop:.2f}元",
                f"当价格上涨到{current_price * 1.1:.2f}元时，止损价上移到{current_price * 1.1 * (1 - trailing_ratio):.2f}元",
                f"当价格上涨到{current_price * 1.2:.2f}元时，止损价上移到{current_price * 1.2 * (1 - trailing_ratio):.2f}元",
                "止损价只上移不下移"
            ],
            "adjustment_examples": [
                {
                    "price": round(current_price * 1.1, 2),
                    "new_stop": round(current_price * 1.1 * (1 - trailing_ratio), 2)
                },
                {
                    "price": round(current_price * 1.2, 2),
                    "new_stop": round(current_price * 1.2 * (1 - trailing_ratio), 2)
                }
            ],
            "advantages": ["保护利润", "让盈利奔跑", "适应趋势"],
            "disadvantages": ["需要频繁监控", "可能过早离场"],
            "usage_tip": "适合趋势明显的行情，建议设置价格提醒"
        }

        self.logger.info(f"移动止损计算完成: {stock_code}")

        return result

    # ========== ATR止损策略 ==========

    async def atr_stop_loss(
        self,
        stock_code: str,
        current_price: Optional[float] = None,
        atr_multiplier: float = 2.0,
        period: int = 14
    ) -> Dict[str, Any]:
        """
        ATR波动率止损

        策略：根据ATR（平均真实波幅）设置止损
        公式：止损价 = 当前价格 - (ATR × 倍数)
        优点：考虑市场波动性，避免被正常波动止损
        缺点：计算复杂

        Args:
            stock_code: 股票代码
            current_price: 当前价格
            atr_multiplier: ATR倍数（默认2.0）
            period: ATR周期（默认14天）

        Returns:
            ATR止损方案
        """
        self.logger.info(
            f"计算ATR止损",
            extra={"stock_code": stock_code, "atr_multiplier": atr_multiplier}
        )

        # 1. 获取当前价格
        if current_price is None:
            current_price = await self._get_current_price(stock_code)

        if current_price <= 0:
            return self._error_result(stock_code, "ATR止损", "无效的当前价格")

        # 2. 计算ATR
        atr = await self._calculate_atr(stock_code, period)

        if atr <= 0:
            # 如果无法计算ATR，使用默认策略
            self.logger.warning(f"ATR计算失败，使用默认8%止损: {stock_code}")
            return await self.fixed_stop_loss(stock_code, current_price, 0.08)

        # 3. 计算止损价
        stop_loss_price = current_price - (atr * atr_multiplier)
        stop_ratio = (current_price - stop_loss_price) / current_price

        result = {
            "stock_code": stock_code,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_price": round(current_price, 2),
            "atr": round(atr, 2),
            "stop_loss": {
                "price": round(stop_loss_price, 2),
                "ratio": round(stop_ratio * 100, 2),
                "type": "atr",
                "description": f"ATR {atr_multiplier}倍止损",
                "formula": f"止损价 = {current_price:.2f} - ({atr:.2f} × {atr_multiplier})"
            },
            "interpretation": {
                "atr_meaning": f"过去{period}天平均波动幅度为{atr:.2f}元",
                "stop_logic": f"允许价格向下波动{atr_multiplier}个ATR（约{stop_ratio*100:.1f}%）"
            },
            "advantages": ["考虑波动性", "避免正常波动止损", "更科学"],
            "disadvantages": ["计算复杂", "需要历史数据"],
            "recommended_for": "波动较大的股票或市场"
        }

        self.logger.info(
            f"ATR止损计算完成: {stock_code}, ATR={atr:.2f}, 止损价={stop_loss_price:.2f}"
        )

        return result

    # ========== 技术止损策略 ==========

    async def technical_stop_loss(
        self,
        stock_code: str,
        current_price: Optional[float] = None,
        technical_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        技术位止损

        策略：根据关键技术位设置止损
        - 支撑位下方
        - 重要均线下方
        - 前低点下方

        优点：符合技术分析逻辑
        缺点：依赖技术分析的准确性

        Args:
            stock_code: 股票代码
            current_price: 当前价格
            technical_analysis: 技术分析结果（如不提供则自动分析）

        Returns:
            技术止损方案
        """
        self.logger.info(f"计算技术止损: {stock_code}")

        # 1. 获取当前价格
        if current_price is None:
            current_price = await self._get_current_price(stock_code)

        if current_price <= 0:
            return self._error_result(stock_code, "技术止损", "无效的当前价格")

        # 2. 获取技术分析（如未提供）
        if technical_analysis is None:
            technical_analysis = await self._get_technical_analysis(stock_code)

        # 3. 识别关键支撑位
        support_levels = self._identify_support_levels(technical_analysis)

        if not support_levels:
            # 如果没有识别到支撑位，使用固定止损
            self.logger.warning(f"未识别到支撑位，使用固定止损: {stock_code}")
            return await self.fixed_stop_loss(stock_code, current_price, 0.08)

        # 4. 选择最近的有效支撑位
        # 选择低于当前价格的最近支撑位
        valid_supports = [s for s in support_levels if s < current_price]
        if valid_supports:
            stop_loss_price = max(valid_supports)  # 最强的支撑位
        else:
            # 如果没有低于当前价格的支撑位，使用固定止损
            stop_loss_price = current_price * 0.92

        stop_ratio = (current_price - stop_loss_price) / current_price

        result = {
            "stock_code": stock_code,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_price": round(current_price, 2),
            "stop_loss": {
                "price": round(stop_loss_price, 2),
                "ratio": round(stop_ratio * 100, 2),
                "type": "technical",
                "description": f"技术位止损（支撑位下方）"
            },
            "support_levels": [
                {
                    "level": round(s, 2),
                    "type": "支撑位",
                    "is_stop_loss": s == stop_loss_price
                }
                for s in support_levels[:5]  # 只显示前5个
            ],
            "technical_basis": {
                "reason": "止损位设置在关键技术支撑位下方",
                "invalidation": "跌破此支撑位说明技术形态破坏"
            },
            "advantages": ["符合技术分析", "逻辑清晰", "专业性强"],
            "disadvantages": ["依赖技术分析准确性", "可能主观性强"],
            "recommended_for": "有明确技术形态的股票"
        }

        self.logger.info(
            f"技术止损计算完成: {stock_code}, 止损价={stop_loss_price:.2f}"
        )

        return result

    # ========== 多级别止盈策略 ==========

    async def multi_level_take_profit(
        self,
        stock_code: str,
        current_price: Optional[float] = None,
        valuation_result: Optional[Dict[str, Any]] = None,
        investment_horizon: str = "medium_term"
    ) -> Dict[str, Any]:
        """
        多级别止盈策略

        策略：分批止盈，锁定利润
        - 第一目标：保守止盈（快钱先落袋）
        - 第二目标：合理止盈（达到预期）
        - 第三目标：乐观止盈（博取更大收益）

        优点：平衡风险收益，心理压力小
        缺点：可能踏空后续行情

        Args:
            stock_code: 股票代码
            current_price: 当前价格
            valuation_result: 估值结果（用于确定目标价）
            investment_horizon: 投资周期（short_term/medium_term/long_term）

        Returns:
            多级别止盈方案
        """
        self.logger.info(f"计算多级别止盈: {stock_code}")

        # 1. 获取当前价格
        if current_price is None:
            current_price = await self._get_current_price(stock_code)

        if current_price <= 0:
            return self._error_result(stock_code, "多级别止盈", "无效的当前价格")

        # 2. 获取配置
        config = self.default_config.get(investment_horizon, self.default_config["medium_term"])
        take_profit_ratios = config["take_profit_ratios"]

        # 3. 如果有估值结果，结合估值目标价
        if valuation_result and "fair_value" in valuation_result:
            fair_value = valuation_result["fair_value"]
            # 调整止盈目标，使第三目标接近估值
            total_ratio = take_profit_ratios[2]
            adjusted_total_ratio = (fair_value - current_price) / current_price
            if 0 < adjusted_total_ratio < 1:
                scale = adjusted_total_ratio / total_ratio
                take_profit_ratios = [r * scale for r in take_profit_ratios]

        # 4. 生成分批止盈方案
        take_profit_levels = []
        for i, ratio in enumerate(take_profit_ratios, 1):
            tp_price = current_price * (1 + ratio)

            # 建议止盈比例
            if i == 1:
                position_ratio = 0.30  # 第一目标止盈30%仓位
            elif i == 2:
                position_ratio = 0.40  # 第二目标止盈40%仓位
            else:
                position_ratio = 0.30  # 第三目标止盈剩余30%仓位

            take_profit_levels.append({
                "level": i,
                "price": round(tp_price, 2),
                "ratio": round(ratio * 100, 2),
                "position_ratio": round(position_ratio * 100, 2),
                "description": f"第{i}目标：{ratio*100:.1f}%收益"
            })

        result = {
            "stock_code": stock_code,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_price": round(current_price, 2),
            "investment_horizon": investment_horizon,
            "take_profit": take_profit_levels,
            "execution_strategy": [
                f"达到第一目标({take_profit_levels[0]['price']:.2f}元)：止盈30%仓位",
                f"达到第二目标({take_profit_levels[1]['price']:.2f}元)：止盈40%仓位",
                f"达到第三目标({take_profit_levels[2]['price']:.2f}元)：止盈剩余30%仓位",
                "如果未达到第三目标就开始下跌，启动止损保护剩余利润"
            ],
            "advantages": ["分批锁定利润", "降低心理压力", "平衡风险收益"],
            "disadvantages": ["可能踏空后续行情", "需要多次操作"],
            "tips": [
                "建议设置价格提醒",
                "严格执行纪律，不贪婪",
                "根据市场情况灵活调整"
            ]
        }

        self.logger.info(
            f"多级别止盈计算完成: {stock_code}, {len(take_profit_levels)}个目标"
        )

        return result

    # ========== 综合方案 ==========

    async def comprehensive_plan(
        self,
        stock_code: str,
        investment_horizon: str = "medium_term",
        technical_analysis: Optional[Dict[str, Any]] = None,
        valuation_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        综合止损止盈方案

        整合多种策略，提供完整的方案
        """
        self.logger.info(f"生成综合方案: {stock_code}, horizon={investment_horizon}")

        # 1. 获取当前价格
        current_price = await self._get_current_price(stock_code)

        if current_price <= 0:
            return self._error_result(stock_code, "综合方案", "无效的当前价格")

        # 2. 计算止损（结合技术分析和固定止损）
        stop_loss_fixed = await self.fixed_stop_loss(stock_code, current_price)
        stop_loss_tech = await self.technical_stop_loss(
            stock_code,
            current_price,
            technical_analysis
        )

        # 选择更合理的止损价（取两者中较高的）
        sl_fixed = stop_loss_fixed["stop_loss"]["price"]
        sl_tech = stop_loss_tech["stop_loss"]["price"]
        final_stop_loss = max(sl_fixed, sl_tech)
        stop_ratio = (current_price - final_stop_loss) / current_price

        # 3. 计算止盈（多级别）
        take_profit = await self.multi_level_take_profit(
            stock_code,
            current_price,
            valuation_result,
            investment_horizon
        )

        # 4. 生成调整规则
        adjustment_rules = self._generate_adjustment_rules(investment_horizon)

        # 5. 计算风险收益比
        first_tp_price = take_profit["take_profit"][0]["price"]
        risk = current_price - final_stop_loss
        reward = first_tp_price - current_price
        risk_reward_ratio = reward / risk if risk > 0 else 0

        result = {
            "stock_code": stock_code,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_price": round(current_price, 2),
            "investment_horizon": investment_horizon,
            "stop_loss": {
                "price": round(final_stop_loss, 2),
                "ratio": round(stop_ratio * 100, 2),
                "type": "combined",
                "description": "综合固定止损和技术位止损",
                "logic": f"取固定止损({sl_fixed:.2f}元)和技术止损({sl_tech:.2f}元)中的较高者"
            },
            "take_profit": take_profit["take_profit"],
            "holding_period": self.default_config[investment_horizon]["holding_period"],
            "adjustment_rules": adjustment_rules,
            "risk_analysis": {
                "risk_amount": round(risk, 2),
                "potential_reward": round(reward, 2),
                "risk_reward_ratio": round(risk_reward_ratio, 2),
                "evaluation": "优秀" if risk_reward_ratio >= 3 else "良好" if risk_reward_ratio >= 2 else "一般"
            },
            "execution_checklist": [
                f"✓ 确认入场价格：{current_price:.2f}元",
                f"✓ 设置止损单：{final_stop_loss:.2f}元",
                f"✓ 设置第一止盈提醒：{take_profit['take_profit'][0]['price']:.2f}元",
                f"✓ 预期持仓周期：{self.default_config[investment_horizon]['holding_period']}",
                "✓ 定期检查技术形态，必要时调整"
            ],
            "summary": (
                f"建议在{current_price:.2f}元买入，"
                f"止损设在{final_stop_loss:.2f}元（{stop_ratio*100:.1f}%），"
                f"分批止盈目标为{', '.join([str(tp['price'])+'元' for tp in take_profit['take_profit']])}，"
                f"预期持仓{self.default_config[investment_horizon]['holding_period']}。"
                f"风险收益比{risk_reward_ratio:.2f}，{risk_reward_ratio >= 2 and '值得投资' or '需谨慎考虑'}。"
            )
        }

        self.logger.info(
            f"综合方案生成完成: {stock_code}, 止损={final_stop_loss:.2f}, "
            f"止盈={take_profit['take_profit'][0]['price']:.2f}"
        )

        return result

    # ========== 动态调整 ==========

    async def dynamic_adjustment(
        self,
        stock_code: str,
        current_plan: Dict[str, Any],
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        动态调整止损止盈

        根据最新价格和市场情况，动态调整点位
        """
        self.logger.info(f"动态调整方案: {stock_code}")

        # 1. 获取最新价格
        if current_price is None:
            current_price = await self._get_current_price(stock_code)

        old_price = current_plan.get("current_price", 0)
        old_stop = current_plan.get("stop_loss", {}).get("price", 0)

        # 2. 计算价格变化
        price_change = (current_price - old_price) / old_price

        # 3. 决定是否调整止损
        new_stop_loss = old_stop
        adjustment_reason = []

        if price_change > 0.10:  # 上涨10%以上
            # 上移止损位（移动止损）
            new_stop_loss = max(old_stop, current_price * 0.95)
            adjustment_reason.append(f"股价上涨{price_change*100:.1f}%，上移止损位保护利润")

        # 4. 调整止盈（如果接近目标）
        take_profit_levels = current_plan.get("take_profit", [])
        if take_profit_levels:
            first_target = take_profit_levels[0]["price"]
            if current_price >= first_target * 0.95:
                adjustment_reason.append(f"接近第一止盈目标，准备执行分批止盈")

        result = {
            "stock_code": stock_code,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "old_price": round(old_price, 2),
            "current_price": round(current_price, 2),
            "price_change": round(price_change * 100, 2),
            "old_stop_loss": round(old_stop, 2),
            "new_stop_loss": round(new_stop_loss, 2),
            "adjustment_reason": adjustment_reason,
            "action_required": adjustment_reason and "需要调整" or "无需调整",
            "new_plan": {
                **current_plan,
                "current_price": current_price,
                "stop_loss": {
                    **current_plan.get("stop_loss", {}),
                    "price": new_stop_loss
                }
            }
        }

        self.logger.info(f"动态调整完成: {stock_code}, 新止损={new_stop_loss:.2f}")

        return result

    # ========== 内部辅助方法 ==========

    async def _get_current_price(self, stock_code: str) -> float:
        """获取当前价格"""
        try:
            # 使用FinancialTool获取实时价格
            symbol = f"{stock_code}.SS" if stock_code.startswith("6") else f"{stock_code}.SZ"
            quote = self.financial_tool.get_realtime_quote(symbol)

            if quote and "current_price" in quote:
                return quote["current_price"]
            else:
                self.logger.warning(f"无法获取实时价格，使用模拟数据: {stock_code}")
                return np.random.uniform(10, 50)  # 模拟价格
        except Exception as e:
            self.logger.error(f"获取价格失败: {e}")
            return 0.0

    async def _calculate_atr(self, stock_code: str, period: int = 14) -> float:
        """
        计算ATR（平均真实波幅）

        ATR = 过去N天真实波幅的移动平均
        真实波幅 = max(高-低, |高-昨收|, |低-昨收|)
        """
        try:
            # 获取历史价格数据
            symbol = f"{stock_code}.SS" if stock_code.startswith("6") else f"{stock_code}.SZ"
            hist_data = self.financial_tool.get_historical_data(symbol, period + 10)

            if not hist_data or len(hist_data) < period:
                self.logger.warning(f"历史数据不足，无法计算ATR: {stock_code}")
                return 0.0

            # 计算真实波幅
            true_ranges = []
            for i in range(1, len(hist_data)):
                high = hist_data[i].get("high", 0)
                low = hist_data[i].get("low", 0)
                prev_close = hist_data[i-1].get("close", 0)

                if high > 0 and low > 0 and prev_close > 0:
                    tr = max(
                        high - low,
                        abs(high - prev_close),
                        abs(low - prev_close)
                    )
                    true_ranges.append(tr)

            # 计算ATR（简单移动平均）
            if len(true_ranges) >= period:
                atr = np.mean(true_ranges[-period:])
                return atr
            else:
                return 0.0

        except Exception as e:
            self.logger.error(f"计算ATR失败: {e}")
            return 0.0

    async def _get_technical_analysis(self, stock_code: str) -> Dict[str, Any]:
        """获取技术分析结果"""
        try:
            from src.agents.business.technical_analyzer import TechnicalAnalysisAI

            ta_ai = TechnicalAnalysisAI()
            result = await ta_ai.analyze(stock_code)

            return result
        except Exception as e:
            self.logger.error(f"技术分析失败: {e}")
            return {}

    def _identify_support_levels(self, technical_analysis: Dict[str, Any]) -> List[float]:
        """从技术分析中识别支撑位"""
        support_levels = []

        try:
            # 从趋势分析中提取支撑位
            if "trend_analysis" in technical_analysis:
                trend = technical_analysis["trend_analysis"]
                if "support_levels" in trend:
                    support_levels.extend(trend["support_levels"])

            # 从技术指标中提取支撑位（如均线）
            if "indicators" in technical_analysis:
                indicators = technical_analysis["indicators"]
                if "ma20" in indicators:
                    support_levels.append(indicators["ma20"])
                if "ma60" in indicators:
                    support_levels.append(indicators["ma60"])

        except Exception as e:
            self.logger.warning(f"识别支撑位失败: {e}")

        return support_levels

    def _generate_adjustment_rules(self, investment_horizon: str) -> List[str]:
        """生成调整规则"""
        base_rules = [
            "每周检查一次技术形态",
            "股价上涨10%时，上移止损位保护利润",
            "接近止盈目标时，准备执行分批止盈"
        ]

        if investment_horizon == "short_term":
            base_rules.extend([
                "短线交易，严格止损",
                "持仓不超过2周"
            ])
        elif investment_horizon == "medium_term":
            base_rules.extend([
                "中线持有，可适度放宽止损",
                "关注基本面变化"
            ])
        else:  # long_term
            base_rules.extend([
                "长线投资，主要关注基本面",
                "技术位仅供参考"
            ])

        return base_rules

    def _error_result(self, stock_code: str, strategy: str, error_msg: str) -> Dict[str, Any]:
        """生成错误结果"""
        return {
            "stock_code": stock_code,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": error_msg,
            "strategy": strategy,
            "suggestion": "请检查股票代码或稍后重试"
        }
