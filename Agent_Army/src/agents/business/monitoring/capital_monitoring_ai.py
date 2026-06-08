"""
资金监控AI - Capital Monitoring AI

监控部成员 (2/2)

职责：
1. 资金流向 - 监控大单资金流向和主力资金动向
2. 龙虎榜 - 分析龙虎榜数据和机构动向

合并来源：
- 资金流向AI
- 龙虎榜AI

使用工具：
- DataTool（资金数据）
- LLMTool（智能分析）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import get_logger


class CapitalMonitoringAI(BusinessAgent):
    """
    资金监控AI - 监控部成员 (2/2)

    核心能力:
    1. 资金流向 - 监控主力资金、散户资金的流入流出
    2. 龙虎榜 - 分析龙虎榜上榜原因、机构买卖行为

    使用工具:
    - DataTool (资金数据)
    - LLMTool (智能分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="资金监控AI",
            role="监控资金流向，分析龙虎榜数据",
            corps="monitoring",
            analysis_type="capital_monitoring",
            capabilities=[
                AgentCapability(
                    name="capital_flow",
                    description="资金流向监控",
                    input_type="stock_code",
                    output_type="capital_flow_data"
                ),
                AgentCapability(
                    name="dragon_tiger_analysis",
                    description="龙虎榜分析",
                    input_type="stock_code",
                    output_type="dragon_tiger_data"
                )
            ],
            tools=[
                AgentTool(
                    name="data_tool",
                    description="数据工具",
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

        self.logger.info("资金监控AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行资金监控分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - days: 监控天数（默认5天）
                - include_dragon_tiger: 是否包含龙虎榜（默认True）

        Returns:
            分析结果
        """
        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        days = kwargs.get("days", 5)
        include_dragon_tiger = kwargs.get("include_dragon_tiger", True)

        self.logger.info(
            f"开始资金监控分析",
            extra={
                "stock_code": stock_code,
                "days": days,
                "include_dragon_tiger": include_dragon_tiger
            }
        )

        # ========== 1. 资金流向监控 ==========
        capital_flow = await self._monitor_capital_flow(
            stock_code,
            days
        )

        # ========== 2. 龙虎榜分析 ==========
        dragon_tiger_data = None
        if include_dragon_tiger:
            dragon_tiger_data = await self._analyze_dragon_tiger(
                stock_code,
                days
            )

        # ========== 3. 主力动向分析 ==========
        main_force_analysis = self._analyze_main_force(
            capital_flow,
            dragon_tiger_data
        )

        # ========== 4. 风险识别 ==========
        risks = self._identify_risks(
            capital_flow,
            dragon_tiger_data,
            main_force_analysis
        )

        # ========== 5. 构建分析结果 ==========
        details = {
            "stock_code": stock_code,
            "monitoring_period": f"{days}天",

            # 资金流向
            "capital_flow": capital_flow,

            # 龙虎榜
            "dragon_tiger": dragon_tiger_data,

            # 主力分析
            "main_force_analysis": main_force_analysis,

            # 时间戳
            "timestamp": datetime.now().isoformat()
        }

        result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=self._generate_conclusion(
                capital_flow,
                dragon_tiger_data,
                main_force_analysis
            ),
            confidence=main_force_analysis["confidence"],
            details=details,
            risks=risks,
            recommendations=self._generate_recommendations(
                capital_flow,
                dragon_tiger_data,
                main_force_analysis
            )
        )

        self.logger.info(
            f"资金监控分析完成",
            extra={
                "stock_code": stock_code,
                "net_flow": capital_flow["net_flow"]["total"],
                "main_force_trend": main_force_analysis["flow_trend"],
                "on_dragon_tiger": dragon_tiger_data is not None,
                "confidence": main_force_analysis["confidence"]
            }
        )

        return result

    # ========== 资金流向监控 ==========

    async def _monitor_capital_flow(
        self,
        stock_code: str,
        days: int
    ) -> Dict[str, Any]:
        """
        监控资金流向

        Returns:
            资金流向数据
        """
        # TODO: 接入真实资金流向API
        # 模拟数据

        # 每日资金流向
        daily_flows = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            # 模拟随机波动
            import random
            random.seed(i)

            main_inflow = round(random.uniform(5000, 15000), 2)  # 主力流入（万元）
            main_outflow = round(random.uniform(3000, 12000), 2)  # 主力流出
            retail_inflow = round(random.uniform(2000, 8000), 2)  # 散户流入
            retail_outflow = round(random.uniform(1500, 7000), 2)  # 散户流出

            daily_flows.append({
                "date": date.strftime("%Y-%m-%d"),
                "main_force": {
                    "inflow": main_inflow,
                    "outflow": main_outflow,
                    "net": round(main_inflow - main_outflow, 2)
                },
                "retail": {
                    "inflow": retail_inflow,
                    "outflow": retail_outflow,
                    "net": round(retail_inflow - retail_outflow, 2)
                },
                "total_net": round(main_inflow - main_outflow + retail_inflow - retail_outflow, 2)
            })

        # 计算汇总
        main_inflow_total = sum([d["main_force"]["inflow"] for d in daily_flows])
        main_outflow_total = sum([d["main_force"]["outflow"] for d in daily_flows])
        retail_inflow_total = sum([d["retail"]["inflow"] for d in daily_flows])
        retail_outflow_total = sum([d["retail"]["outflow"] for d in daily_flows])

        net_flow = {
            "main_force": round(main_inflow_total - main_outflow_total, 2),
            "retail": round(retail_inflow_total - retail_outflow_total, 2),
            "total": round(
                (main_inflow_total - main_outflow_total) +
                (retail_inflow_total - retail_outflow_total),
                2
            )
        }

        # 资金流向趋势
        trend = self._calculate_flow_trend(daily_flows)

        # 大单分析
        large_orders = self._analyze_large_orders(stock_code, days)

        return {
            "daily_flows": daily_flows,
            "net_flow": net_flow,
            "trend": trend,
            "large_orders": large_orders,
            "summary": {
                "main_inflow_total": round(main_inflow_total, 2),
                "main_outflow_total": round(main_outflow_total, 2),
                "retail_inflow_total": round(retail_inflow_total, 2),
                "retail_outflow_total": round(retail_outflow_total, 2),
                "net_inflow_days": len([d for d in daily_flows if d["total_net"] > 0]),
                "net_outflow_days": len([d for d in daily_flows if d["total_net"] < 0])
            }
        }

    def _calculate_flow_trend(self, daily_flows: List[Dict]) -> str:
        """计算资金流向趋势"""
        if len(daily_flows) < 2:
            return "stable"

        # 最近3天 vs 前3天
        recent = daily_flows[:3]
        earlier = daily_flows[3:6] if len(daily_flows) >= 6 else []

        if not earlier:
            return "stable"

        recent_avg = sum([d["total_net"] for d in recent]) / len(recent)
        earlier_avg = sum([d["total_net"] for d in earlier]) / len(earlier)

        diff = recent_avg - earlier_avg

        if diff > 5000:  # 万元
            return "strong_inflow"  # 强势流入
        elif diff > 1000:
            return "inflow"  # 流入
        elif diff > -1000:
            return "stable"  # 稳定
        elif diff > -5000:
            return "outflow"  # 流出
        else:
            return "strong_outflow"  # 强势流出

    def _analyze_large_orders(
        self,
        stock_code: str,
        days: int
    ) -> Dict[str, Any]:
        """分析大单交易"""
        # TODO: 接入真实大单数据
        # 模拟数据
        import random
        random.seed(42)

        return {
            "large_buy_orders": random.randint(50, 200),  # 大单买入笔数
            "large_sell_orders": random.randint(30, 150),  # 大单卖出笔数
            "super_large_buy": random.randint(10, 50),  # 超大单买入
            "super_large_sell": random.randint(5, 40),  # 超大单卖出
            "block_trades": random.randint(0, 5),  # 大宗交易笔数
            "analysis": "大单以买入为主，主力资金介入迹象明显" if random.random() > 0.5 else "大单买卖均衡，资金分歧较大"
        }

    # ========== 龙虎榜分析 ==========

    async def _analyze_dragon_tiger(
        self,
        stock_code: str,
        days: int
    ) -> Optional[Dict[str, Any]]:
        """
        分析龙虎榜

        Returns:
            龙虎榜数据，如果没有上榜则返回None
        """
        # TODO: 接入真实龙虎榜API
        # 模拟数据（假设最近上榜了）

        # 随机决定是否上榜（70%概率上榜）
        import random
        if random.random() > 0.3:
            # 上榜了
            return {
                "on_list": True,
                "latest_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "reason": "日涨幅偏离值达7%",  # 上榜原因
                "close_price": 25.68,
                "change_pct": 7.85,
                "turnover_ratio": 15.6,  # 换手率

                # 买入前5名
                "buy_top5": [
                    {"name": "机构专用", "buy_amount": 5680.5, "sell_amount": 0.0},
                    {"name": "华泰证券股份有限公司总部", "buy_amount": 2340.2, "sell_amount": 120.5},
                    {"name": "中信证券股份有限公司上海分公司", "buy_amount": 1890.8, "sell_amount": 0.0},
                    {"name": "沪股通专用", "buy_amount": 1560.3, "sell_amount": 80.2},
                    {"name": "国泰君安证券股份有限公司上海分公司", "buy_amount": 1230.5, "sell_amount": 0.0}
                ],

                # 卖出前5名
                "sell_top5": [
                    {"name": "机构专用", "buy_amount": 0.0, "sell_amount": 3450.8},
                    {"name": "东方财富证券股份有限公司拉萨团结路第二证券营业部", "buy_amount": 560.2, "sell_amount": 1890.5},
                    {"name": "华鑫证券有限责任公司上海分公司", "buy_amount": 0.0, "sell_amount": 1230.6},
                    {"name": "深股通专用", "buy_amount": 320.5, "sell_amount": 980.3},
                    {"name": "招商证券股份有限公司深圳招商证券大厦证券营业部", "buy_amount": 0.0, "sell_amount": 760.4}
                ],

                # 汇总
                "total_buy": sum([item["buy_amount"] for item in [
                    {"name": "机构专用", "buy_amount": 5680.5, "sell_amount": 0.0},
                    {"name": "华泰证券股份有限公司总部", "buy_amount": 2340.2, "sell_amount": 120.5},
                    {"name": "中信证券股份有限公司上海分公司", "buy_amount": 1890.8, "sell_amount": 0.0},
                    {"name": "沪股通专用", "buy_amount": 1560.3, "sell_amount": 80.2},
                    {"name": "国泰君安证券股份有限公司上海分公司", "buy_amount": 1230.5, "sell_amount": 0.0}
                ]]),
                "total_sell": sum([item["sell_amount"] for item in [
                    {"name": "机构专用", "buy_amount": 0.0, "sell_amount": 3450.8},
                    {"name": "东方财富证券股份有限公司拉萨团结路第二证券营业部", "buy_amount": 560.2, "sell_amount": 1890.5},
                    {"name": "华鑫证券有限责任公司上海分公司", "buy_amount": 0.0, "sell_amount": 1230.6},
                    {"name": "深股通专用", "buy_amount": 320.5, "sell_amount": 980.3},
                    {"name": "招商证券股份有限公司深圳招商证券大厦证券营业部", "buy_amount": 0.0, "sell_amount": 760.4}
                ]]),

                # 机构行为分析
                "institution_analysis": {
                    "net_buy": round(5680.5 - 3450.8, 2),  # 机构净买入
                    "institution_count": 2,  # 机构席位数量
                    "hot_money_count": 3,  # 游资席位数量
                    "assessment": "机构分歧，游资活跃"
                }
            }
        else:
            # 没上榜
            return {
                "on_list": False,
                "reason": "近5日未上榜",
                "note": "未上榜可能表示波动较小，或主力资金隐蔽操作"
            }

    # ========== 主力动向分析 ==========

    def _analyze_main_force(
        self,
        capital_flow: Dict[str, Any],
        dragon_tiger_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析主力动向

        Args:
            capital_flow: 资金流向数据
            dragon_tiger_data: 龙虎榜数据

        Returns:
            主力动向分析
        """
        # 资金流向分析
        net_main = capital_flow["net_flow"]["main_force"]
        flow_trend = capital_flow["trend"]

        # 主力动向判断
        if net_main > 10000:  # 大于1亿元
            main_force_behavior = "大幅流入"
            behavior_description = "主力资金大幅流入，看好后市"
        elif net_main > 3000:
            main_force_behavior = "流入"
            behavior_description = "主力资金持续流入"
        elif net_main > -3000:
            main_force_behavior = "震荡"
            behavior_description = "主力资金进出平衡，处于观望状态"
        elif net_main > -10000:
            main_force_behavior = "流出"
            behavior_description = "主力资金持续流出"
        else:
            main_force_behavior = "大幅流出"
            behavior_description = "主力资金大幅流出，不看好后市"

        # 龙虎榜分析
        dragon_tiger_signal = "neutral"
        dragon_tiger_note = ""

        if dragon_tiger_data and dragon_tiger_data.get("on_list"):
            institution_net = dragon_tiger_data["institution_analysis"]["net_buy"]

            if institution_net > 3000:
                dragon_tiger_signal = "positive"
                dragon_tiger_note = "龙虎榜显示机构大幅净买入"
            elif institution_net > -3000:
                dragon_tiger_signal = "neutral"
                dragon_tiger_note = "龙虎榜显示机构买卖均衡"
            else:
                dragon_tiger_signal = "negative"
                dragon_tiger_note = "龙虎榜显示机构大幅净卖出"

        # 综合判断
        signals = []

        # 资金流向信号
        if net_main > 5000:
            signals.append("positive")
        elif net_main < -5000:
            signals.append("negative")
        else:
            signals.append("neutral")

        # 龙虎榜信号
        if dragon_tiger_signal:
            signals.append(dragon_tiger_signal)

        # 综合信号
        positive_count = signals.count("positive")
        negative_count = signals.count("negative")

        if positive_count >= 2:
            overall_signal = "strong_buy"
        elif positive_count == 1 and negative_count == 0:
            overall_signal = "buy"
        elif positive_count == 0 and negative_count == 0:
            overall_signal = "neutral"
        elif negative_count == 1 and positive_count == 0:
            overall_signal = "sell"
        else:
            overall_signal = "mixed"

        # 置信度
        confidence = 0.6
        if dragon_tiger_data and dragon_tiger_data.get("on_list"):
            confidence += 0.2  # 有龙虎榜数据，置信度提高
        if abs(net_main) > 5000:
            confidence += 0.1  # 资金流向明显，置信度提高
        if flow_trend in ["strong_inflow", "strong_outflow"]:
            confidence += 0.1  # 趋势明显，置信度提高

        confidence = min(confidence, 0.95)

        return {
            "main_force_behavior": main_force_behavior,
            "behavior_description": behavior_description,
            "net_main_flow": net_main,
            "flow_trend": flow_trend,
            "dragon_tiger_signal": dragon_tiger_signal,
            "dragon_tiger_note": dragon_tiger_note,
            "overall_signal": overall_signal,
            "confidence": round(confidence, 2)
        }

    # ========== 风险识别 ==========

    def _identify_risks(
        self,
        capital_flow: Dict[str, Any],
        dragon_tiger_data: Optional[Dict[str, Any]],
        main_force_analysis: Dict[str, Any]
    ) -> List[str]:
        """识别风险"""
        risks = []

        # 资金流向风险
        net_main = capital_flow["net_flow"]["main_force"]
        if net_main < -10000:
            risks.append(f"主力资金大幅流出（{net_main:.2f}万元），存在持续下跌风险")

        # 流出趋势风险
        trend = capital_flow["trend"]
        if trend == "strong_outflow":
            risks.append("资金呈现强势流出趋势，主力可能在出货")

        # 龙虎榜风险
        if dragon_tiger_data and dragon_tiger_data.get("on_list"):
            institution_net = dragon_tiger_data["institution_analysis"]["net_buy"]
            if institution_net < -3000:
                risks.append(f"龙虎榜机构净卖出{institution_net:.2f}万元，机构不看好后市")

            # 游资风险
            hot_money_count = dragon_tiger_data["institution_analysis"]["hot_money_count"]
            if hot_money_count >= 4:
                risks.append("游资席位过多，可能存在短线炒作风险")

        # 大单风险
        large_orders = capital_flow["large_orders"]
        if large_orders["large_sell_orders"] > large_orders["large_buy_orders"] * 1.5:
            risks.append("大单卖出明显多于买入，主力资金可能在撤离")

        # 综合信号风险
        if main_force_analysis["overall_signal"] in ["sell", "strong_sell"]:
            risks.append("多个指标显示卖出信号，短期风险较高")

        if not risks:
            risks.append("未发现明显资金风险")

        return risks

    # ========== 建议生成 ==========

    def _generate_recommendations(
        self,
        capital_flow: Dict[str, Any],
        dragon_tiger_data: Optional[Dict[str, Any]],
        main_force_analysis: Dict[str, Any]
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        # 基于主力行为的建议
        behavior = main_force_analysis["main_force_behavior"]
        if "大幅流入" in behavior:
            recommendations.append("主力资金大幅流入，可考虑积极跟进")
        elif "流入" in behavior:
            recommendations.append("主力资金持续流入，可考虑逢低买入")
        elif "震荡" in behavior:
            recommendations.append("主力资金进出平衡，建议观望等待")
        elif "流出" in behavior:
            recommendations.append("主力资金持续流出，建议谨慎操作")
        else:
            recommendations.append("主力资金大幅流出，建议考虑减仓")

        # 基于趋势的建议
        trend = capital_flow["trend"]
        if trend == "strong_inflow":
            recommendations.append("资金强势流入，短期可能走强")
        elif trend == "strong_outflow":
            recommendations.append("资金强势流出，短期承压较大")

        # 基于龙虎榜的建议
        if dragon_tiger_data and dragon_tiger_data.get("on_list"):
            signal = main_force_analysis["dragon_tiger_signal"]
            note = main_force_analysis["dragon_tiger_note"]
            if signal == "positive":
                recommendations.append(f"{note}，机构看好后市")
            elif signal == "negative":
                recommendations.append(f"{note}，需警惕机构做空")

        # 基于综合信号的建议
        overall = main_force_analysis["overall_signal"]
        if overall == "strong_buy":
            recommendations.append("多个指标显示买入信号，可积极布局")
        elif overall == "buy":
            recommendations.append("指标偏向买入，可适当建仓")
        elif overall == "sell":
            recommendations.append("指标偏向卖出，注意风险控制")
        elif overall == "strong_sell":
            recommendations.append("多个指标显示卖出信号，建议减仓")
        else:  # mixed
            recommendations.append("多空信号交织，建议观望")

        return recommendations

    # ========== 结论生成 ==========

    def _generate_conclusion(
        self,
        capital_flow: Dict[str, Any],
        dragon_tiger_data: Optional[Dict[str, Any]],
        main_force_analysis: Dict[str, Any]
    ) -> str:
        """生成核心结论"""
        net_flow = capital_flow["net_flow"]["total"]
        behavior = main_force_analysis["main_force_behavior"]
        signal = main_force_analysis["overall_signal"]

        dragon_info = ""
        if dragon_tiger_data and dragon_tiger_data.get("on_list"):
            dragon_info = f"，龙虎榜上榜"

        return (
            f"资金流向【{behavior}】（净{net_flow:.2f}万元）"
            f"{dragon_info}，"
            f"综合信号【{signal}】"
        )


# 便捷函数
async def analyze_capital_monitoring(
    stock_code: str,
    days: int = 5,
    include_dragon_tiger: bool = True
) -> AnalysisResult:
    """
    资金监控分析（便捷函数）

    Args:
        stock_code: 股票代码
        days: 监控天数
        include_dragon_tiger: 是否包含龙虎榜

    Returns:
        分析结果
    """
    ai = CapitalMonitoringAI()
    return await ai.analyze(
        stock_code,
        days=days,
        include_dragon_tiger=include_dragon_tiger
    )
