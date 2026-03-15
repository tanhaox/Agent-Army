"""
历史节点分析AI - Historical Node Analysis AI

职责：
- 整合事件周期性 + K线共性 + 资金常客
- 生成历史节点分析报告
- 预测未来关键时间窗口

这是"AI投资外脑"最核心的Agent，整合了3个子AI的分析结果。

输入：
- 股票代码
- 历史年数（默认3年）

输出：
- 事件周期性分析
- K线共性识别
- 资金常客识别
- 关键时间窗口预测
- 综合评分和投资建议
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool

# 导入子AI
from src.agents.business.stock.historical_cycle_ai import HistoricalCycleAI
from src.agents.business.stock.kline_pattern_ai import KlinePatternAI
from src.agents.business.stock.capital_regular_ai import CapitalRegularAI


class HistoricalNodeAI(BaseAgent, LoggerMixin):
    """
    历史节点分析AI - AI投资外脑的核心

    核心功能：
    1. 整合3个子AI的分析结果
       - HistoricalCycleAI：事件周期性
       - KlinePatternAI：K线共性
       - CapitalRegularAI：资金常客

    2. 生成关键时间窗口预测
       - 政策发布窗口
       - 财报发布窗口
       - 主升浪时间窗口

    3. 综合评分和投资建议
       - 综合评分（0-100）
       - 投资建议（买入/持有/卖出）
       - 风险提示

    这是Deep-Interview中用户最核心的需求：
    "识别股票历史节点规律，预测关键时间窗口"
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.financial_tool = FinancialTool()

        # 初始化3个子AI
        self.cycle_ai = HistoricalCycleAI(config)
        self.pattern_ai = KlinePatternAI(config)
        self.capital_ai = CapitalRegularAI(config)

        super().__init__(
            name="历史节点分析AI",
            role="分析股票历史节点规律，预测关键时间窗口，综合评估投资价值",
            capabilities=[
                AgentCapability(
                    name="historical_node_analysis",
                    description="历史节点综合分析",
                    input_type="stock_code",
                    output_type="comprehensive_report"
                ),
                AgentCapability(
                    name="key_time_window_prediction",
                    description="关键时间窗口预测",
                    input_type="stock_code",
                    output_type="time_window_report"
                ),
                AgentCapability(
                    name="investment_advice",
                    description="投资建议生成",
                    input_type="stock_code",
                    output_type="investment_report"
                )
            ],
            tools=[
                AgentTool(
                    name="cycle_analysis",
                    description="事件周期性分析",
                    tool_type="agent",
                    config={}
                ),
                AgentTool(
                    name="pattern_analysis",
                    description="K线共性分析",
                    tool_type="agent",
                    config={}
                ),
                AgentTool(
                    name="capital_analysis",
                    description="资金常客分析",
                    tool_type="agent",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("历史节点分析AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze":
            return await self.analyze(
                kwargs.get("stock_code"),
                kwargs.get("years", 3)
            )
        elif task == "predict_key_windows":
            return await self.predict_key_windows(
                kwargs.get("stock_code"),
                kwargs.get("years", 3)
            )
        elif task == "generate_investment_advice":
            return await self.generate_investment_advice(
                kwargs.get("stock_code"),
                kwargs.get("years", 3)
            )
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 核心功能 ==========

    async def analyze(
        self,
        stock_code: str,
        years: int = 3
    ) -> Dict[str, Any]:
        """
        综合分析历史节点

        整合3个子AI的分析结果，生成完整的历史节点分析报告

        Args:
            stock_code: 股票代码
            years: 分析历史年数

        Returns:
            {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "analysis_date": "2026-03-15",
                "event_cycles": {...},  # 来自cycle_ai
                "kline_patterns": {...},  # 来自pattern_ai
                "regular_capital": {...},  # 来自capital_ai
                "key_nodes": [
                    {
                        "time_window": "2026-06",
                        "event_type": "政策发布",
                        "confidence": 0.85,
                        "action": "关注政策窗口"
                    },
                    {
                        "time_window": "2026-07-08",
                        "event_type": "主升浪",
                        "confidence": 0.78,
                        "action": "北向资金流入，预期上涨"
                    }
                ],
                "overall_score": 82,
                "rating": "A",
                "investment_advice": "...",
                "risk_alerts": [...],
                "summary": "..."
            }
        """
        self.logger.info(
            f"开始历史节点综合分析",
            extra={"stock_code": stock_code, "years": years}
        )

        # 1. 并发调用3个子AI（提高性能）
        cycle_task = self.cycle_ai.analyze_event_cycles(stock_code, years)
        pattern_task = self.pattern_ai.analyze_kline_patterns(stock_code, years)
        capital_task = self.capital_ai.identify_regular_capital(stock_code, years)

        # 等待所有分析完成
        event_cycles, kline_patterns, regular_capital = await asyncio.gather(
            cycle_task,
            pattern_task,
            capital_task,
            return_exceptions=True
        )

        # 处理异常
        if isinstance(event_cycles, Exception):
            self.logger.error(f"事件周期分析失败: {event_cycles}")
            event_cycles = {"error": str(event_cycles)}

        if isinstance(kline_patterns, Exception):
            self.logger.error(f"K线共性分析失败: {kline_patterns}")
            kline_patterns = {"error": str(kline_patterns)}

        if isinstance(regular_capital, Exception):
            self.logger.error(f"资金常客分析失败: {regular_capital}")
            regular_capital = {"error": str(regular_capital)}

        # 2. 生成关键时间节点
        key_nodes = self._generate_key_nodes(
            event_cycles,
            kline_patterns,
            regular_capital
        )

        # 3. 计算综合评分
        overall_score = self._calculate_overall_score(
            event_cycles,
            kline_patterns,
            regular_capital,
            key_nodes
        )

        # 4. 生成投资建议
        investment_advice = self._generate_investment_advice(
            overall_score,
            key_nodes,
            kline_patterns,
            regular_capital
        )

        # 5. 生成风险提示
        risk_alerts = self._generate_risk_alerts(
            event_cycles,
            kline_patterns,
            regular_capital
        )

        # 6. 生成摘要
        summary = self._generate_summary(
            event_cycles,
            kline_patterns,
            regular_capital,
            key_nodes,
            overall_score
        )

        # 7. 构建最终报告
        report = {
            "stock_code": stock_code,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "event_cycles": event_cycles,
            "kline_patterns": kline_patterns,
            "regular_capital": regular_capital,
            "key_nodes": key_nodes,
            "overall_score": overall_score,
            "rating": self._score_to_rating(overall_score),
            "investment_advice": investment_advice,
            "risk_alerts": risk_alerts,
            "summary": summary
        }

        self.logger.info(
            f"历史节点综合分析完成",
            extra={
                "stock_code": stock_code,
                "overall_score": overall_score,
                "key_nodes_count": len(key_nodes)
            }
        )

        return report

    async def predict_key_windows(
        self,
        stock_code: str,
        years: int = 3
    ) -> List[Dict[str, Any]]:
        """
        预测关键时间窗口

        只返回关键时间窗口，不包含完整分析

        Returns:
            [
                {
                    "time_window": "2026-06",
                    "event_type": "政策发布",
                    "confidence": 0.85,
                    "importance": "高",
                    "action": "关注政策窗口"
                }
            ]
        """
        self.logger.info(f"预测关键时间窗口: {stock_code}")

        # 1. 获取分析报告
        full_report = await self.analyze(stock_code, years)

        # 2. 提取关键节点
        return full_report.get("key_nodes", [])

    # ========== 内部方法 ==========

    def _generate_key_nodes(
        self,
        event_cycles: Dict[str, Any],
        kline_patterns: Dict[str, Any],
        regular_capital: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        生成关键时间节点

        整合3个子AI的结果，识别未来关键时间窗口

        关键时间窗口类型：
        1. 政策发布窗口
        2. 财报发布窗口
        3. 主升浪时间窗口（资金流入+价格突破）
        """
        key_nodes = []

        # 1. 从事件周期中提取
        if not event_cycles.get("error"):
            # 财报窗口
            earnings_cycles = event_cycles.get("earnings_cycles", {})
            if earnings_cycles.get("detected"):
                next_earnings = earnings_cycles.get("next_event", "")
                confidence = earnings_cycles.get("confidence", 0.0)

                key_nodes.append({
                    "time_window": next_earnings,
                    "event_type": "财报发布",
                    "confidence": confidence,
                    "importance": "高" if confidence > 0.8 else "中",
                    "action": "关注财报数据，验证业绩预期",
                    "source": "event_cycles"
                })

            # 政策窗口
            policy_cycles = event_cycles.get("policy_cycles", {})
            if policy_cycles.get("detected"):
                next_policy = policy_cycles.get("next_event", "")
                confidence = policy_cycles.get("confidence", 0.0)

                key_nodes.append({
                    "time_window": next_policy,
                    "event_type": "政策发布",
                    "confidence": confidence,
                    "importance": "中" if confidence > 0.7 else "低",
                    "action": "关注政策动向，评估政策影响",
                    "source": "event_cycles"
                })

        # 2. 从资金常客中提取（主升浪预测）
        if not regular_capital.get("error"):
            prediction = regular_capital.get("prediction", "")
            regular_funds = regular_capital.get("regular_funds", [])

            if regular_funds and prediction:
                # 找到置信度最高的常客资金
                best_fund = max(regular_funds, key=lambda x: x.get("confidence", 0.0))

                # 预测主升浪时间窗口
                if best_fund.get("confidence", 0.0) > 0.7:
                    key_nodes.append({
                        "time_window": "未来1-2个月",  # 根据资金流向预测
                        "event_type": "主升浪",
                        "confidence": best_fund.get("confidence", 0.0),
                        "importance": "高",
                        "action": f"{best_fund['name']}预计流入，关注买入时机",
                        "source": "regular_capital"
                    })

        # 3. 从K线共性中提取（突破时间窗口）
        if not kline_patterns.get("error"):
            resistance_levels = kline_patterns.get("resistance_levels", [])
            seasonal_patterns = kline_patterns.get("seasonal_patterns", {})

            if resistance_levels and seasonal_patterns:
                best_quarter = seasonal_patterns.get("best_quarter", "")
                if best_quarter == "Q1":
                    key_nodes.append({
                        "time_window": f"次年Q1",
                        "event_type": "季节性上涨",
                        "confidence": seasonal_patterns.get("seasonal_strength", 0.0) + 0.5,
                        "importance": "中",
                        "action": f"{best_quarter}历史表现最佳，提前布局",
                        "source": "kline_patterns"
                    })

        # 4. 按时间排序
        key_nodes.sort(key=lambda x: x["time_window"])

        # 5. 去重（合并相似窗口）
        key_nodes = self._merge_similar_nodes(key_nodes)

        return key_nodes

    def _calculate_overall_score(
        self,
        event_cycles: Dict[str, Any],
        kline_patterns: Dict[str, Any],
        regular_capital: Dict[str, Any],
        key_nodes: List[Dict[str, Any]]
    ) -> int:
        """
        计算综合评分（0-100）

        评分维度：
        1. 周期性清晰度（25分）
        2. K线共性强度（25分）
        3. 资金常客质量（25分）
        4. 关键节点确定性（25分）
        """
        score = 0

        # 1. 周期性清晰度（25分）
        if not event_cycles.get("error"):
            earnings_detected = event_cycles.get("earnings_cycles", {}).get("detected", False)
            policy_detected = event_cycles.get("policy_cycles", {}).get("detected", False)

            if earnings_detected and policy_detected:
                score += 25
            elif earnings_detected or policy_detected:
                score += 15

        # 2. K线共性强度（25分）
        if not kline_patterns.get("error"):
            support_levels = kline_patterns.get("support_levels", [])
            resistance_levels = kline_patterns.get("resistance_levels", [])

            if len(support_levels) >= 2 and len(resistance_levels) >= 2:
                score += 25
            elif len(support_levels) >= 1 or len(resistance_levels) >= 1:
                score += 15

        # 3. 资金常客质量（25分）
        if not regular_capital.get("error"):
            regular_funds = regular_capital.get("regular_funds", [])

            if regular_funds:
                # 计算平均置信度
                avg_confidence = sum(
                    f.get("confidence", 0.0) for f in regular_funds
                ) / len(regular_funds)

                if avg_confidence > 0.8:
                    score += 25
                elif avg_confidence > 0.6:
                    score += 15
                else:
                    score += 10

        # 4. 关键节点确定性（25分）
        if key_nodes:
            high_confidence_count = sum(
                1 for node in key_nodes
                if node.get("confidence", 0.0) > 0.7
            )

            if high_confidence_count >= 2:
                score += 25
            elif high_confidence_count >= 1:
                score += 15
            else:
                score += 10

        return round(score)

    def _score_to_rating(self, score: int) -> str:
        """评分转评级"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C"
        else:
            return "D"

    def _generate_investment_advice(
        self,
        overall_score: int,
        key_nodes: List[Dict[str, Any]],
        kline_patterns: Dict[str, Any],
        regular_capital: Dict[str, Any]
    ) -> str:
        """
        生成投资建议

        基于综合评分和关键节点，给出具体的投资建议
        """
        if overall_score >= 80:
            # 高分：建议关注
            advice_parts = []

            # 1. 关键时间窗口
            if key_nodes:
                high_importance_nodes = [
                    node for node in key_nodes
                    if node.get("importance") == "高"
                ]

                if high_importance_nodes:
                    node = high_importance_nodes[0]
                    advice_parts.append(
                        f"重点关注{node['time_window']}的{node['event_type']}窗口"
                    )
                    advice_parts.append(node.get("action", ""))

            # 2. 资金建议
            if not regular_capital.get("error"):
                prediction = regular_capital.get("prediction", "")
                if prediction:
                    advice_parts.append(f"{prediction}，可考虑提前布局")

            return "；".join(advice_parts) if advice_parts else "综合评分优秀，建议关注投资机会"

        elif overall_score >= 60:
            # 中等分：谨慎关注
            return "综合评分中等，历史节点规律尚可，建议谨慎关注，注意风险控制"

        else:
            # 低分：观望
            return "综合评分较低，历史节点规律不明显，建议观望或等待更好的时机"

    def _generate_risk_alerts(
        self,
        event_cycles: Dict[str, Any],
        kline_patterns: Dict[str, Any],
        regular_capital: Dict[str, Any]
    ) -> List[str]:
        """生成风险提示"""
        alerts = []

        # 1. 周期性风险
        if event_cycles.get("error") or \
           not event_cycles.get("earnings_cycles", {}).get("detected") and \
           not event_cycles.get("policy_cycles", {}).get("detected"):
            alerts.append("⚠️ 未检测到明显的事件周期性，预测可能不准确")

        # 2. K线风险
        if not kline_patterns.get("error"):
            current_price = kline_patterns.get("current_price", 0)
            nearest_support = kline_patterns.get("nearest_support")
            nearest_resistance = kline_patterns.get("nearest_resistance")

            if nearest_support and current_price:
                distance = (current_price - nearest_support) / current_price
                if distance < 0.05:  # 距离支撑位<5%
                    alerts.append(f"⚠️ 当前价格{current_price:.2f}元接近支撑位{nearest_support:.2f}元，注意止损")

        # 3. 资金风险
        if not regular_capital.get("error"):
            prediction = regular_capital.get("prediction", "")
            if "流出" in prediction:
                alerts.append("⚠️ 预测资金净流出，建议谨慎")

        # 4. 综合风险
        if not alerts:
            alerts.append("✅ 暂无明显风险，但仍需持续监控")

        return alerts

    def _generate_summary(
        self,
        event_cycles: Dict[str, Any],
        kline_patterns: Dict[str, Any],
        regular_capital: Dict[str, Any],
        key_nodes: List[Dict[str, Any]],
        overall_score: int
    ) -> str:
        """生成分析摘要"""
        summary_parts = []

        # 1. 周期性摘要
        if not event_cycles.get("error"):
            summary_parts.append(event_cycles.get("summary", ""))

        # 2. K线摘要
        if not kline_patterns.get("error"):
            summary_parts.append(kline_patterns.get("summary", ""))

        # 3. 资金摘要
        if not regular_capital.get("error"):
            summary_parts.append(regular_capital.get("summary", ""))

        # 4. 关键节点摘要
        if key_nodes:
            node_descriptions = [
                f"{node['time_window']}的{node['event_type']}"
                for node in key_nodes[:3]  # 最多3个
            ]
            summary_parts.append(f"关键时间窗口：{', '.join(node_descriptions)}")

        # 5. 综合评分
        summary_parts.append(f"综合评分：{overall_score}分（{self._score_to_rating(overall_score)}）")

        # 合并（去除空字符串）
        summary_parts = [p for p in summary_parts if p]

        return "；".join(summary_parts) + "。"

    def _merge_similar_nodes(
        self,
        key_nodes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        合并相似的时间节点

        例如：同一个月的政策和财报窗口可以合并
        """
        if len(key_nodes) <= 1:
            return key_nodes

        merged = []
        used_indices = set()

        for i, node1 in enumerate(key_nodes):
            if i in used_indices:
                continue

            merged_node = node1.copy()
            used_indices.add(i)

            # 查找相似节点
            for j, node2 in enumerate(key_nodes[i+1:], start=i+1):
                if j in used_indices:
                    continue

                # 简单判断：如果事件类型相同且时间窗口相似
                if (node1["event_type"] == node2["event_type"] and
                    node1["time_window"] == node2["time_window"]):

                    # 合并置信度（取最大值）
                    merged_node["confidence"] = max(
                        node1["confidence"],
                        node2["confidence"]
                    )

                    # 合并action
                    actions = [node1["action"], node2["action"]]
                    merged_node["action"] = "；".join(actions)

                    used_indices.add(j)

            merged.append(merged_node)

        return merged
