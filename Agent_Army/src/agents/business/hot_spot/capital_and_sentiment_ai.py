"""
资金与情绪分析AI - Capital and Sentiment AI

整合功能:
1. 资金流向分析 (原CapitalFlowAI)
2. 市场情绪分析 (原MarketSentimentAI)
3. 综合市场热度评分

使用工具:
- FinancialTool (资金数据)
- NewsTool (新闻数据)
- NLPTool (情感分析)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool, NewsTool, NLPTool


class CapitalAndSentimentAI(BaseAgent, LoggerMixin):
    """
    资金与情绪分析AI - 热点捕捉军团核心成员

    整合功能:
    1. 资金流向分析 (主力资金、北向资金、融资余额)
    2. 市场情绪分析 (新闻情感、社交讨论、热度排名)
    3. 综合市场热度评分

    使用工具:
    - FinancialTool (资金数据)
    - NewsTool (新闻数据)
    - NLPTool (情感分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.financial_tool = FinancialTool()
        self.news_tool = NewsTool()
        self.nlp_tool = NLPTool()

        super().__init__(
            name="资金与情绪分析AI",
            role="分析资金流向、市场情绪，计算综合市场热度",
            capabilities=[
                AgentCapability(
                    name="capital_flow_analysis",
                    description="资金流向分析",
                    input_type="stock_code",
                    output_type="capital_flow_report"
                ),
                AgentCapability(
                    name="sentiment_analysis",
                    description="市场情绪分析",
                    input_type="stock_code",
                    output_type="sentiment_report"
                ),
                AgentCapability(
                    name="heat_score_calculation",
                    description="市场热度评分",
                    input_type="stock_code",
                    output_type="heat_score"
                ),
                AgentCapability(
                    name="comprehensive_analysis",
                    description="综合分析(资金+情绪)",
                    input_type="stock_code",
                    output_type="comprehensive_report"
                )
            ],
            tools=[
                AgentTool(
                    name="capital_tracker",
                    description="资金追踪工具",
                    tool_type="system",
                    config={}
                ),
                AgentTool(
                    name="sentiment_analyzer",
                    description="情感分析工具",
                    tool_type="system",
                    config={}
                ),
                AgentTool(
                    name="heat_calculator",
                    description="热度计算工具",
                    tool_type="system",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("资金与情绪分析AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze":
            return await self.analyze(
                kwargs.get("stock_code"),
                **kwargs
            )
        elif task == "analyze_capital_flow":
            return await self._analyze_capital_flow(
                kwargs.get("stock_code"),
                kwargs.get("time_range", "5d")
            )
        elif task == "analyze_sentiment":
            return await self._analyze_sentiment(
                kwargs.get("stock_code"),
                kwargs.get("time_range", "1d")
            )
        elif task == "get_heat_score":
            return await self._calculate_heat_score(
                kwargs.get("stock_code")
            )
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 主入口方法 ==========

    async def analyze(
        self,
        stock_code: str,
        time_range: str = "5d",
        **kwargs
    ) -> Dict[str, Any]:
        """
        综合分析 (资金 + 情绪)

        Args:
            stock_code: 股票代码
            time_range: 时间范围 (1d, 5d, 10d, 30d)

        Returns:
            综合分析报告
        """
        self.logger.info(
            f"开始综合分析",
            extra={"stock_code": stock_code, "time_range": time_range}
        )

        # ========== 1. 并行获取数据 (提升性能) ==========
        capital_data, sentiment_data = await asyncio.gather(
            self._fetch_capital_data(stock_code, time_range),
            self._fetch_sentiment_data(stock_code, time_range)
        )

        # ========== 2. 资金流向分析 (原CapitalFlowAI) ==========
        capital_flow = await self._analyze_capital_flow_internal(
            stock_code,
            capital_data
        )

        # ========== 3. 市场情绪分析 (原MarketSentimentAI) ==========
        sentiment = await self._analyze_sentiment_internal(
            stock_code,
            sentiment_data
        )

        # ========== 4. 计算综合市场热度 ==========
        heat_score = self._calculate_comprehensive_heat_score(
            capital_flow,
            sentiment
        )

        # ========== 5. 生成投资建议 ==========
        recommendation = self._generate_comprehensive_recommendation(
            capital_flow,
            sentiment,
            heat_score
        )

        # ========== 6. 构建返回结果 ==========
        result = {
            "stock_code": stock_code,
            "stock_name": kwargs.get("stock_name", stock_code),
            "analysis_type": "capital_and_sentiment",
            "timestamp": datetime.now().isoformat(),
            "time_range": time_range,

            # 资金流向 (原CapitalFlowAI)
            "capital_flow": capital_flow,

            # 市场情绪 (原MarketSentimentAI)
            "sentiment": sentiment,

            # 综合市场热度
            "heat_score": heat_score,

            # 投资建议
            "recommendation": recommendation,

            # 总结
            "summary": self._generate_summary(
                capital_flow,
                sentiment,
                heat_score,
                recommendation
            )
        }

        self.logger.info(
            f"综合分析完成",
            extra={
                "stock_code": stock_code,
                "heat_score": heat_score["total_score"]
            }
        )

        return result

    # ========== 数据获取方法 ==========

    async def _fetch_capital_data(
        self,
        stock_code: str,
        time_range: str
    ) -> Dict[str, Any]:
        """获取资金数据 (并行获取多个数据源)"""
        try:
            days = self._parse_time_range(time_range)

            # 并行获取资金数据
            flow_data, main_force_data = await asyncio.gather(
                self._fetch_capital_flow_data(stock_code, days),
                self._fetch_main_force_data(stock_code, days)
            )

            return {
                "flow_data": flow_data,
                "main_force_data": main_force_data
            }
        except Exception as e:
            self.logger.warning(f"获取资金数据失败: {e}")
            return {"flow_data": [], "main_force_data": []}

    async def _fetch_sentiment_data(
        self,
        stock_code: str,
        time_range: str
    ) -> Dict[str, Any]:
        """获取情绪数据 (并行获取多个数据源)"""
        try:
            # 并行获取新闻和社交数据
            news_data, social_data = await asyncio.gather(
                self._fetch_news_data(stock_code, time_range),
                self._fetch_social_data(stock_code, time_range)
            )

            return {
                "news_data": news_data,
                "social_data": social_data
            }
        except Exception as e:
            self.logger.warning(f"获取情绪数据失败: {e}")
            return {"news_data": [], "social_data": []}

    # ========== 资金流向分析 (原CapitalFlowAI) ==========

    async def _analyze_capital_flow(
        self,
        stock_code: str,
        time_range: str = "5d"
    ) -> Dict[str, Any]:
        """
        资金流向分析 (兼容旧API)

        Args:
            stock_code: 股票代码
            time_range: 时间范围

        Returns:
            资金流向报告
        """
        capital_data = await self._fetch_capital_data(stock_code, time_range)
        return await self._analyze_capital_flow_internal(stock_code, capital_data)

    async def _analyze_capital_flow_internal(
        self,
        stock_code: str,
        capital_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """资金流向分析 (内部方法)"""
        flow_data = capital_data.get("flow_data", [])
        main_force_data = capital_data.get("main_force_data", [])

        # 1. 分析资金流向模式
        flow_analysis = self._analyze_flow_pattern(flow_data)

        # 2. 计算资金净流入
        net_inflow = self._calculate_net_inflow(flow_data)

        # 3. 分析主力资金
        main_force_analysis = self._analyze_main_force(main_force_data)

        # 4. 资金评分 (0-100)
        capital_score = self._calculate_capital_score(
            flow_analysis,
            net_inflow,
            main_force_analysis
        )

        # 5. 资金趋势
        capital_trend = self._analyze_capital_trend(flow_data)

        return {
            "flow_pattern": flow_analysis["pattern"],
            "flow_description": flow_analysis["description"],
            "flow_strength": flow_analysis["strength"],
            "flow_ratio": flow_analysis["flow_ratio"],

            "net_inflow": net_inflow["net_amount"],
            "net_inflow_trend": net_inflow["trend"],
            "average_net_inflow": net_inflow["average_net"],

            "main_force_status": main_force_analysis["status"],
            "main_force_signal": main_force_analysis["signal"],
            "main_force_scenario": main_force_analysis["scenario"],
            "main_net_total": main_force_analysis["main_net_total"],

            "capital_score": capital_score,
            "capital_trend": capital_trend,

            "rating": self._get_capital_rating(capital_score),
            "recommendation": self._generate_capital_recommendation(flow_analysis)
        }

    # ========== 市场情绪分析 (原MarketSentimentAI) ==========

    async def _analyze_sentiment(
        self,
        stock_code: str,
        time_range: str = "1d"
    ) -> Dict[str, Any]:
        """
        市场情绪分析 (兼容旧API)

        Args:
            stock_code: 股票代码
            time_range: 时间范围

        Returns:
            情绪分析报告
        """
        sentiment_data = await self._fetch_sentiment_data(stock_code, time_range)
        return await self._analyze_sentiment_internal(stock_code, sentiment_data)

    async def _analyze_sentiment_internal(
        self,
        stock_code: str,
        sentiment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """市场情绪分析 (内部方法)"""
        news_data = sentiment_data.get("news_data", [])
        social_data = sentiment_data.get("social_data", [])

        # 1. 分析情感分数
        sentiment_scores = await self._analyze_sentiment_scores(
            news_data,
            social_data
        )

        # 2. 计算综合情绪指数
        sentiment_index = self._calculate_sentiment_index(sentiment_scores)

        # 3. 情绪趋势
        sentiment_trend = self._analyze_sentiment_trend(sentiment_scores)

        return {
            "sentiment_index": round(sentiment_index, 2),
            "sentiment_rating": self._get_sentiment_rating(sentiment_index),

            "news_sentiment": round(sentiment_scores["news_sentiment"], 2),
            "social_sentiment": round(sentiment_scores["social_sentiment"], 2),

            "news_count": len(news_data),
            "social_count": len(social_data),

            "sentiment_trend": sentiment_trend,

            "analysis": self._generate_sentiment_analysis_text(
                sentiment_index,
                sentiment_scores
            ),
            "recommendation": self._generate_sentiment_recommendation(sentiment_index)
        }

    # ========== 综合热度评分 ==========

    def _calculate_comprehensive_heat_score(
        self,
        capital_flow: Dict[str, Any],
        sentiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算综合市场热度评分

        权重分配:
        - 资金面: 60% (主力资金、资金流向)
        - 情绪面: 40% (新闻情感、社交热度)
        """
        # 资金分数 (0-100)
        capital_score = capital_flow.get("capital_score", 50)

        # 情绪分数 (0-100)
        sentiment_score = sentiment.get("sentiment_index", 50)

        # 加权平均
        total_score = (
            capital_score * 0.60 +
            sentiment_score * 0.40
        )

        # 热度等级
        if total_score >= 80:
            heat_level = "极热"
            heat_description = "市场高度关注,资金情绪双高"
        elif total_score >= 65:
            heat_level = "高热"
            heat_description = "市场关注度高,资金情绪良好"
        elif total_score >= 50:
            heat_level = "温热"
            heat_description = "市场关注度中等,资金情绪平稳"
        elif total_score >= 35:
            heat_level = "偏冷"
            heat_description = "市场关注度较低,资金情绪一般"
        else:
            heat_level = "冷门"
            heat_description = "市场关注度低,资金情绪较差"

        return {
            "total_score": round(total_score, 2),
            "heat_level": heat_level,
            "heat_description": heat_description,

            "capital_score": round(capital_score, 2),
            "capital_weight": 0.60,

            "sentiment_score": round(sentiment_score, 2),
            "sentiment_weight": 0.40,

            "components": {
                "capital": {
                    "score": round(capital_score, 2),
                    "weight": 0.60,
                    "contribution": round(capital_score * 0.60, 2)
                },
                "sentiment": {
                    "score": round(sentiment_score, 2),
                    "weight": 0.40,
                    "contribution": round(sentiment_score * 0.40, 2)
                }
            }
        }

    # ========== 投资建议生成 ==========

    def _generate_comprehensive_recommendation(
        self,
        capital_flow: Dict[str, Any],
        sentiment: Dict[str, Any],
        heat_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成综合投资建议

        使用投票机制:
        - 资金建议: 买入/持有/卖出
        - 情绪建议: 买入/持有/卖出
        - 综合建议: 投票决定
        """
        # 资金建议
        capital_rec = capital_flow.get("recommendation", "观望")

        # 情绪建议
        sentiment_rec = sentiment.get("recommendation", "观望")

        # 转换为统一格式
        def normalize_recommendation(rec: str) -> str:
            if rec in ["积极关注", "可以关注"]:
                return "BUY"
            elif rec in ["谨慎观望", "谨慎"]:
                return "HOLD"
            elif rec in ["规避风险", "规避"]:
                return "SELL"
            else:
                return "HOLD"

        capital_action = normalize_recommendation(capital_rec)
        sentiment_action = normalize_recommendation(sentiment_rec)

        # 投票机制
        votes = {
            "BUY": 0,
            "HOLD": 0,
            "SELL": 0
        }
        votes[capital_action] += 1
        votes[sentiment_action] += 1

        # 确定最终建议
        if votes["BUY"] >= 2:
            action = "BUY"
            confidence = 0.75 if votes["BUY"] == 2 else 0.90
        elif votes["SELL"] >= 2:
            action = "SELL"
            confidence = 0.75 if votes["SELL"] == 2 else 0.90
        else:
            action = "HOLD"
            confidence = 0.60

        # 生成推理说明
        reasoning = self._generate_reasoning(
            capital_flow,
            sentiment,
            heat_score,
            action
        )

        return {
            "action": action,
            "confidence": round(confidence, 2),
            "reasoning": reasoning,

            "details": {
                "capital_recommendation": capital_rec,
                "capital_action": capital_action,
                "sentiment_recommendation": sentiment_rec,
                "sentiment_action": sentiment_action
            },

            "risk_warning": self._generate_risk_warning(heat_score)
        }

    def _generate_reasoning(
        self,
        capital_flow: Dict[str, Any],
        sentiment: Dict[str, Any],
        heat_score: Dict[str, Any],
        action: str
    ) -> str:
        """生成推理说明"""
        capital_desc = capital_flow.get("flow_description", "")
        main_force = capital_flow.get("main_force_status", "")
        sentiment_desc = sentiment.get("analysis", "")
        heat_desc = heat_score.get("heat_description", "")

        reasoning = f"资金面：{capital_desc}，{main_force}。"
        reasoning += f"情绪面：{sentiment_desc}。"
        reasoning += f"综合热度：{heat_desc}（{heat_score['total_score']:.1f}分）。"

        if action == "BUY":
            reasoning += "资金和情绪均表现积极，建议关注。"
        elif action == "SELL":
            reasoning += "资金和情绪均表现较差，建议规避。"
        else:
            reasoning += "资金和情绪表现分化，建议观望。"

        return reasoning

    def _generate_risk_warning(self, heat_score: Dict[str, Any]) -> str:
        """生成风险警告"""
        level = heat_score.get("heat_level", "")

        if level == "极热":
            return "注意：市场过热，可能存在短期回调风险。"
        elif level == "高热":
            return "注意：市场关注度较高，注意控制仓位。"
        elif level == "冷门":
            return "注意：市场关注度低，流动性可能不足。"
        else:
            return "风险等级：正常"

    # ========== 辅助方法 ==========

    def _parse_time_range(self, time_range: str) -> int:
        """解析时间范围"""
        mapping = {
            "1d": 1,
            "3d": 3,
            "5d": 5,
            "7d": 7,
            "10d": 10,
            "30d": 30
        }
        return mapping.get(time_range, 5)

    async def _fetch_capital_flow_data(
        self,
        stock_code: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """获取资金流向数据 (模拟)"""
        import random

        data = []
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i-1)
            inflow = random.uniform(1000, 5000)
            outflow = random.uniform(800, 4500)

            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "inflow": round(inflow, 2),
                "outflow": round(outflow, 2),
                "net_inflow": round(inflow - outflow, 2),
                "turnover_rate": round(random.uniform(1, 5), 2)
            })

        return data

    async def _fetch_main_force_data(
        self,
        stock_code: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """获取主力资金数据 (模拟)"""
        import random

        data = []
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i-1)

            main_inflow = random.uniform(500, 3000)
            main_outflow = random.uniform(400, 2800)
            retail_inflow = random.uniform(500, 2000)
            retail_outflow = random.uniform(600, 2100)

            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "main_inflow": round(main_inflow, 2),
                "main_outflow": round(main_outflow, 2),
                "main_net": round(main_inflow - main_outflow, 2),
                "retail_inflow": round(retail_inflow, 2),
                "retail_outflow": round(retail_outflow, 2),
                "retail_net": round(retail_inflow - retail_outflow, 2)
            })

        return data

    async def _fetch_news_data(
        self,
        stock_code: str,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """获取新闻数据 (模拟)"""
        # TODO: 使用真实的NewsTool
        return [
            {
                "title": f"{stock_code}近期表现分析",
                "content": f"{stock_code}近期表现不错，市场关注度提升",
                "timestamp": datetime.now().isoformat()
            }
        ]

    async def _fetch_social_data(
        self,
        stock_code: str,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """获取社交媒体讨论数据 (模拟)"""
        return [
            {
                "platform": "雪球",
                "content": f"{stock_code}近期表现不错",
                "timestamp": datetime.now().isoformat()
            }
        ]

    def _analyze_flow_pattern(
        self,
        flow_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析资金流向模式"""
        if not flow_data:
            return {
                "pattern": "unknown",
                "strength": 0,
                "flow_ratio": 1.0,
                "description": "数据不足"
            }

        total_net_inflow = sum(d["net_inflow"] for d in flow_data)
        total_inflow = sum(d["inflow"] for d in flow_data)
        total_outflow = sum(d["outflow"] for d in flow_data)

        if total_outflow == 0:
            flow_ratio = 999
        else:
            flow_ratio = total_inflow / total_outflow

        if flow_ratio > 1.2:
            pattern = "strong_inflow"
            strength = min(100, (flow_ratio - 1) * 100)
            description = "资金持续流入，买盘强劲"
        elif flow_ratio > 1.0:
            pattern = "mild_inflow"
            strength = (flow_ratio - 1) * 50
            description = "资金小幅流入"
        elif flow_ratio > 0.8:
            pattern = "mild_outflow"
            strength = (1 - flow_ratio) * 50
            description = "资金小幅流出"
        else:
            pattern = "strong_outflow"
            strength = min(100, (1 - flow_ratio) * 100)
            description = "资金持续流出，卖盘压力大"

        return {
            "pattern": pattern,
            "strength": round(strength, 2),
            "flow_ratio": round(flow_ratio, 2),
            "description": description,
            "total_net_inflow": round(total_net_inflow, 2)
        }

    def _calculate_net_inflow(
        self,
        flow_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算资金净流入"""
        if not flow_data:
            return {"net_amount": 0, "trend": "unknown", "average_net": 0}

        total_net = sum(d["net_inflow"] for d in flow_data)
        avg_net = total_net / len(flow_data)

        if avg_net > 500:
            trend = "大幅流入"
        elif avg_net > 100:
            trend = "小幅流入"
        elif avg_net > -100:
            trend = "基本平衡"
        elif avg_net > -500:
            trend = "小幅流出"
        else:
            trend = "大幅流出"

        return {
            "net_amount": round(total_net, 2),
            "average_net": round(avg_net, 2),
            "trend": trend
        }

    def _analyze_main_force(
        self,
        main_force_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析主力资金"""
        if not main_force_data:
            return {
                "status": "unknown",
                "signal": "neutral",
                "scenario": "数据不足",
                "main_net_total": 0
            }

        main_net_total = sum(d["main_net"] for d in main_force_data)
        retail_net_total = sum(d["retail_net"] for d in main_force_data)

        if main_net_total > 1000:
            status = "主力持续买入"
            signal = "bullish"
        elif main_net_total > 0:
            status = "主力小幅买入"
            signal = "slightly_bullish"
        elif main_net_total > -1000:
            status = "主力小幅卖出"
            signal = "slightly_bearish"
        else:
            status = "主力持续卖出"
            signal = "bearish"

        if main_net_total > 0 and retail_net_total < 0:
            scenario = "主力吸筹，散户离场"
        elif main_net_total < 0 and retail_net_total > 0:
            scenario = "主力出货，散户接盘"
        elif main_net_total > 0 and retail_net_total > 0:
            scenario = "主力散户同向买入"
        else:
            scenario = "主力散户同向卖出"

        return {
            "status": status,
            "signal": signal,
            "scenario": scenario,
            "main_net_total": round(main_net_total, 2),
            "retail_net_total": round(retail_net_total, 2),
            "main_avg_net": round(main_net_total / len(main_force_data), 2)
        }

    def _calculate_capital_score(
        self,
        flow_analysis: Dict[str, Any],
        net_inflow: Dict[str, Any],
        main_force_analysis: Dict[str, Any]
    ) -> float:
        """计算资金评分 (0-100)"""
        # 基础分数 (基于流向模式)
        base_score = 50

        # 流向强度贡献 (-20 到 +20)
        if flow_analysis["pattern"] in ["strong_inflow", "mild_inflow"]:
            flow_contribution = min(20, flow_analysis["strength"] * 0.2)
        else:
            flow_contribution = -min(20, flow_analysis["strength"] * 0.2)

        # 主力资金贡献 (-15 到 +15)
        signal = main_force_analysis["signal"]
        if signal == "bullish":
            main_contribution = 15
        elif signal == "slightly_bullish":
            main_contribution = 8
        elif signal == "slightly_bearish":
            main_contribution = -8
        elif signal == "bearish":
            main_contribution = -15
        else:
            main_contribution = 0

        # 总分
        total_score = base_score + flow_contribution + main_contribution

        # 限制在 0-100 范围
        return max(0, min(100, total_score))

    def _analyze_capital_trend(
        self,
        flow_data: List[Dict[str, Any]]
    ) -> str:
        """分析资金趋势"""
        if len(flow_data) < 3:
            return "数据不足"

        # 计算最近3天 vs 之前数据
        recent = flow_data[-3:]
        earlier = flow_data[:-3] if len(flow_data) > 3 else flow_data

        recent_avg = sum(d["net_inflow"] for d in recent) / len(recent)
        earlier_avg = sum(d["net_inflow"] for d in earlier) / len(earlier)

        if earlier_avg == 0:
            change = 0
        else:
            change = ((recent_avg - earlier_avg) / abs(earlier_avg)) * 100

        if change > 20:
            return "加速流入"
        elif change > 5:
            return "持续流入"
        elif change > -5:
            return "基本稳定"
        elif change > -20:
            return "持续流出"
        else:
            return "加速流出"

    def _get_capital_rating(self, capital_score: float) -> str:
        """获取资金评级"""
        if capital_score >= 80:
            return "A"
        elif capital_score >= 65:
            return "B"
        elif capital_score >= 50:
            return "C"
        elif capital_score >= 35:
            return "D"
        else:
            return "E"

    def _generate_capital_recommendation(
        self,
        flow_analysis: Dict[str, Any]
    ) -> str:
        """生成资金面建议"""
        pattern = flow_analysis.get("pattern", "")

        if pattern == "strong_inflow":
            return "积极关注"
        elif pattern == "mild_inflow":
            return "可以关注"
        elif pattern == "mild_outflow":
            return "谨慎观望"
        else:
            return "规避风险"

    async def _analyze_sentiment_scores(
        self,
        news_data: List[Dict[str, Any]],
        social_data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """分析情感分数"""
        scores = {
            "news_sentiment": 50.0,
            "social_sentiment": 50.0
        }

        # 分析新闻情感
        if news_data:
            total_score = 0
            for news in news_data:
                sentiment = await self.nlp_tool.analyze_sentiment(
                    news.get("content", "")
                )
                total_score += sentiment.get("score", 50)

            scores["news_sentiment"] = total_score / len(news_data)

        # 分析社交媒体情感
        if social_data:
            total_score = 0
            for post in social_data:
                sentiment = await self.nlp_tool.analyze_sentiment(
                    post.get("content", "")
                )
                total_score += sentiment.get("score", 50)

            scores["social_sentiment"] = total_score / len(social_data)

        return scores

    def _calculate_sentiment_index(
        self,
        scores: Dict[str, float]
    ) -> float:
        """计算综合情绪指数"""
        return (
            scores.get("news_sentiment", 50) * 0.6 +
            scores.get("social_sentiment", 50) * 0.4
        )

    def _analyze_sentiment_trend(
        self,
        sentiment_scores: Dict[str, float]
    ) -> str:
        """分析情绪趋势"""
        index = sentiment_scores.get("news_sentiment", 50)

        if index >= 70:
            return "极度乐观"
        elif index >= 55:
            return "乐观"
        elif index >= 45:
            return "中性"
        elif index >= 30:
            return "悲观"
        else:
            return "极度悲观"

    def _get_sentiment_rating(self, sentiment_index: float) -> str:
        """获取情绪评级"""
        if sentiment_index >= 70:
            return "非常乐观"
        elif sentiment_index >= 55:
            return "乐观"
        elif sentiment_index >= 45:
            return "中性"
        elif sentiment_index >= 30:
            return "悲观"
        else:
            return "非常悲观"

    def _generate_sentiment_analysis_text(
        self,
        sentiment_index: float,
        scores: Dict[str, float]
    ) -> str:
        """生成情绪分析文本"""
        if sentiment_index >= 70:
            return f"市场情绪非常乐观（{sentiment_index:.1f}分），新闻情感{scores['news_sentiment']:.1f}分，社交媒体情感{scores['social_sentiment']:.1f}分。投资者信心较强。"
        elif sentiment_index >= 55:
            return f"市场情绪乐观（{sentiment_index:.1f}分），整体偏积极，可以关注。"
        elif sentiment_index >= 45:
            return f"市场情绪中性（{sentiment_index:.1f}分），观望为主。"
        elif sentiment_index >= 30:
            return f"市场情绪悲观（{sentiment_index:.1f}分），谨慎对待。"
        else:
            return f"市场情绪非常悲观（{sentiment_index:.1f}分），建议规避风险。"

    def _generate_sentiment_recommendation(
        self,
        sentiment_index: float
    ) -> str:
        """生成情绪面建议"""
        if sentiment_index >= 70:
            return "积极关注"
        elif sentiment_index >= 55:
            return "可以关注"
        elif sentiment_index >= 45:
            return "观望"
        elif sentiment_index >= 30:
            return "谨慎"
        else:
            return "规避"

    def _generate_summary(
        self,
        capital_flow: Dict[str, Any],
        sentiment: Dict[str, Any],
        heat_score: Dict[str, Any],
        recommendation: Dict[str, Any]
    ) -> str:
        """生成总结"""
        summary = f"资金面：{capital_flow.get('flow_description', '')}，"
        summary += f"主力资金{capital_flow.get('main_force_status', '')}，"
        summary += f"资金评分{capital_flow.get('capital_score', 0):.1f}分（{capital_flow.get('rating', '')}级）。"

        summary += f"情绪面：{sentiment.get('sentiment_rating', '')}，"
        summary += f"情绪指数{sentiment.get('sentiment_index', 0):.1f}分。"

        summary += f"综合热度：{heat_score.get('heat_level', '')}（{heat_score.get('total_score', 0):.1f}分）。"

        summary += f"投资建议：{recommendation.get('action', '')}（置信度{recommendation.get('confidence', 0)*100:.0f}%）。"

        return summary
