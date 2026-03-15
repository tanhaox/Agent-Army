"""
产业链分析AI - Industry Chain AI

产业分析军团成员

职责：
1. 上游分析（原材料、供应商）
2. 中游分析（生产制造、加工）
3. 下游分析（终端客户、销售渠道）
4. 价值分布分析（各环节利润分配）
5. 产业链地位评估
6. 投资机会识别

使用工具：
- FinancialTool（财务数据）
- LLMTool（智能分析）
- NewsTool（行业新闻）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool, LLMTool, NewsTool


class IndustryChainAI(BaseAgent, LoggerMixin):
    """
    产业链分析AI - 产业分析军团成员

    核心能力:
    1. 上游分析（原材料、供应商）
    2. 中游分析（生产制造、加工）
    3. 下游分析（终端客户、销售渠道）
    4. 价值分布分析（各环节利润分配）
    5. 产业链地位评估
    6. 投资机会识别

    使用工具:
    - FinancialTool (财务数据)
    - LLMTool (智能分析)
    - NewsTool (行业新闻)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.financial_tool = FinancialTool()
        self.llm_tool = LLMTool()
        self.news_tool = NewsTool()

        super().__init__(
            name="产业链分析AI",
            role="分析产业链结构，评估投资机会",
            capabilities=[
                AgentCapability(
                    name="upstream_analysis",
                    description="上游分析",
                    input_type="industry_code",
                    output_type="upstream_report"
                ),
                AgentCapability(
                    name="midstream_analysis",
                    description="中游分析",
                    input_type="industry_code",
                    output_type="midstream_report"
                ),
                AgentCapability(
                    name="downstream_analysis",
                    description="下游分析",
                    input_type="industry_code",
                    output_type="downstream_report"
                ),
                AgentCapability(
                    name="value_distribution_analysis",
                    description="价值分布分析",
                    input_type="industry_code",
                    output_type="value_distribution_report"
                ),
                AgentCapability(
                    name="industry_chain_assessment",
                    description="产业链综合评估",
                    input_type="industry_code",
                    output_type="assessment_report"
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
                ),
                AgentTool(
                    name="news_tool",
                    description="行业新闻工具",
                    tool_type="data_source",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("产业链分析AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze":
            return await self.analyze(**kwargs)
        elif task == "analyze_upstream":
            return await self._analyze_upstream(**kwargs)
        elif task == "analyze_midstream":
            return await self._analyze_midstream(**kwargs)
        elif task == "analyze_downstream":
            return await self._analyze_downstream(**kwargs)
        elif task == "analyze_value_distribution":
            return await self._analyze_value_distribution(**kwargs)
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 主入口方法 ==========

    async def analyze(
        self,
        industry_code: str,
        stock_code: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        产业链综合分析

        Args:
            industry_code: 行业代码
            stock_code: 股票代码（可选，用于定位产业链位置）

        Returns:
            产业链综合报告
        """
        self.logger.info(
            f"开始产业链综合分析",
            extra={"industry_code": industry_code, "stock_code": stock_code}
        )

        # ========== 1. 并行获取产业链数据 ==========
        upstream, midstream, downstream, news_data = await asyncio.gather(
            self._analyze_upstream(industry_code),
            self._analyze_midstream(industry_code),
            self._analyze_downstream(industry_code),
            self._fetch_industry_news(industry_code)
        )

        # ========== 2. 价值分布分析 ==========
        value_distribution = await self._analyze_value_distribution(
            industry_code,
            upstream,
            midstream,
            downstream
        )

        # ========== 3. 产业链地位评估 ==========
        chain_position = self._assess_chain_position(
            upstream,
            midstream,
            downstream,
            value_distribution,
            stock_code
        )

        # ========== 4. 投资机会识别 ==========
        investment_opportunities = self._identify_investment_opportunities(
            upstream,
            midstream,
            downstream,
            value_distribution,
            news_data
        )

        # ========== 5. 风险点识别 ==========
        risk_points = self._identify_risk_points(
            upstream,
            midstream,
            downstream,
            news_data
        )

        # ========== 6. 产业链评分 ==========
        chain_score = self._calculate_chain_score(
            upstream,
            midstream,
            downstream,
            value_distribution
        )

        # ========== 7. 构建返回结果 ==========
        result = {
            "analysis_type": "industry_chain",
            "timestamp": datetime.now().isoformat(),
            "industry_code": industry_code,
            "stock_code": stock_code,

            # 三大环节分析
            "upstream": upstream,
            "midstream": midstream,
            "downstream": downstream,

            # 价值分布
            "value_distribution": value_distribution,

            # 产业链地位
            "chain_position": chain_position,

            # 投资机会
            "investment_opportunities": investment_opportunities,

            # 风险点
            "risk_points": risk_points,

            # 综合评分
            "chain_score": chain_score,

            # 行业新闻
            "news_data": news_data
        }

        self.logger.info(
            f"产业链综合分析完成",
            extra={
                "industry_code": industry_code,
                "chain_score": chain_score["total_score"],
                "position": chain_position["position"]
            }
        )

        return result

    # ========== 三大环节分析方法 ==========

    async def _analyze_upstream(self, industry_code: str) -> Dict[str, Any]:
        """
        上游分析

        分析内容:
        1. 原材料供应商
        2. 成本结构
        3. 供应集中度
        4. 议价能力
        """
        # TODO: 接入真实API
        # 当前返回模拟数据

        # 上游供应商列表（模拟）
        suppliers = [
            {
                "name": "原材料供应商A",
                "market_share": 25.0,
                "cost_ratio": 40.0,
                "bargaining_power": "强",
                "stability": "稳定"
            },
            {
                "name": "原材料供应商B",
                "market_share": 20.0,
                "cost_ratio": 30.0,
                "bargaining_power": "中",
                "stability": "稳定"
            },
            {
                "name": "原材料供应商C",
                "market_share": 15.0,
                "cost_ratio": 20.0,
                "bargaining_power": "弱",
                "stability": "一般"
            }
        ]

        # 成本结构（模拟）
        cost_structure = {
            "原材料": 50.0,
            "能源": 15.0,
            "人工": 10.0,
            "设备折旧": 8.0,
            "其他": 17.0
        }

        # 供应集中度
        supplier_concentration = {
            "CR3": sum(s["market_share"] for s in suppliers[:3]),  # 前三大供应商占比
            "HHI": sum(s["market_share"]**2 for s in suppliers),  # 赫芬达尔指数
            "assessment": "中等集中" if sum(s["market_share"] for s in suppliers[:3]) < 70 else "高度集中"
        }

        # 议价能力评估
        overall_bargaining_power = self._assess_overall_bargaining_power(suppliers)

        # 上游评分
        upstream_score = self._score_upstream(
            suppliers,
            cost_structure,
            supplier_concentration,
            overall_bargaining_power
        )

        return {
            "suppliers": suppliers,
            "cost_structure": cost_structure,
            "supplier_concentration": supplier_concentration,
            "overall_bargaining_power": overall_bargaining_power,
            "score": upstream_score,
            "assessment": self._assess_upstream(upstream_score),
            "update_time": datetime.now().isoformat()
        }

    async def _analyze_midstream(self, industry_code: str) -> Dict[str, Any]:
        """
        中游分析

        分析内容:
        1. 生产制造企业
        2. 技术壁垒
        3. 产能利用率
        4. 成本优势
        """
        # 生产制造企业列表（模拟）
        manufacturers = [
            {
                "name": "制造商A",
                "market_share": 30.0,
                "capacity_utilization": 85.0,
                "tech_barrier": "高",
                "cost_advantage": "强"
            },
            {
                "name": "制造商B",
                "market_share": 25.0,
                "capacity_utilization": 80.0,
                "tech_barrier": "中",
                "cost_advantage": "中"
            },
            {
                "name": "制造商C",
                "market_share": 20.0,
                "capacity_utilization": 75.0,
                "tech_barrier": "中",
                "cost_advantage": "弱"
            }
        ]

        # 技术壁垒评估
        tech_barriers = {
            "研发投入占比": 5.5,
            "专利数量": 150,
            "技术门槛": "中高",
            "替代难度": "中等"
        }

        # 产能分析
        capacity_analysis = {
            "total_capacity": 1000,  # 总产能
            "utilization_rate": 82.0,  # 产能利用率
            "expansion_plan": "有",  # 扩产计划
            "supply_demand": "平衡"  # 供需关系
        }

        # 成本优势评估
        cost_advantage = {
            "scale_economy": "中",  # 规模经济
            "cost_structure": "优化",  # 成本结构
            "efficiency": "高",  # 生产效率
            "advantage_level": "中高"  # 优势水平
        }

        # 中游评分
        midstream_score = self._score_midstream(
            manufacturers,
            tech_barriers,
            capacity_analysis,
            cost_advantage
        )

        return {
            "manufacturers": manufacturers,
            "tech_barriers": tech_barriers,
            "capacity_analysis": capacity_analysis,
            "cost_advantage": cost_advantage,
            "score": midstream_score,
            "assessment": self._assess_midstream(midstream_score),
            "update_time": datetime.now().isoformat()
        }

    async def _analyze_downstream(self, industry_code: str) -> Dict[str, Any]:
        """
        下游分析

        分析内容:
        1. 终端客户
        2. 销售渠道
        3. 市场需求
        4. 议价能力
        """
        # 终端客户列表（模拟）
        customers = [
            {
                "segment": "个人消费者",
                "market_share": 50.0,
                "growth_rate": 8.0,
                "price_sensitivity": "高",
                "loyalty": "中"
            },
            {
                "segment": "企业客户",
                "market_share": 35.0,
                "growth_rate": 5.0,
                "price_sensitivity": "中",
                "loyalty": "高"
            },
            {
                "segment": "政府机构",
                "market_share": 15.0,
                "growth_rate": 3.0,
                "price_sensitivity": "低",
                "loyalty": "高"
            }
        ]

        # 销售渠道分析
        sales_channels = {
            "直销": 40.0,
            "经销商": 35.0,
            "电商": 20.0,
            "其他": 5.0
        }

        # 市场需求分析
        market_demand = {
            "total_market_size": 5000,  # 市场规模（亿元）
            "growth_rate": 6.5,  # 增长率
            "saturation": "中",  # 饱和度
            "potential": "中高"  # 潜力
        }

        # 客户议价能力
        customer_bargaining_power = self._assess_customer_bargaining_power(customers)

        # 下游评分
        downstream_score = self._score_downstream(
            customers,
            sales_channels,
            market_demand,
            customer_bargaining_power
        )

        return {
            "customers": customers,
            "sales_channels": sales_channels,
            "market_demand": market_demand,
            "customer_bargaining_power": customer_bargaining_power,
            "score": downstream_score,
            "assessment": self._assess_downstream(downstream_score),
            "update_time": datetime.now().isoformat()
        }

    async def _analyze_value_distribution(
        self,
        industry_code: str,
        upstream: Dict[str, Any],
        midstream: Dict[str, Any],
        downstream: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        价值分布分析

        分析内容:
        1. 各环节利润占比
        2. 价值链长度
        3. 价值创造点
        4. 价值转移趋势
        """
        # 利润分布（模拟）
        profit_distribution = {
            "上游": {
                "revenue_share": 30.0,
                "profit_share": 25.0,
                "profit_margin": 15.0,
                "value_creation": "原材料供应"
            },
            "中游": {
                "revenue_share": 45.0,
                "profit_share": 35.0,
                "profit_margin": 12.0,
                "value_creation": "生产加工"
            },
            "下游": {
                "revenue_share": 25.0,
                "profit_share": 40.0,
                "profit_margin": 25.0,
                "value_creation": "品牌营销"
            }
        }

        # 价值链分析
        value_chain = {
            "length": "长",  # 价值链长度
            "complexity": "中高",  # 复杂度
            "key_value_point": "下游",  # 关键价值点
            "value_concentration": "中"  # 价值集中度
        }

        # 价值转移趋势
        value_transfer_trend = {
            "direction": "向下游转移",  # 转移方向
            "speed": "快",  # 转移速度
            "driver": "品牌溢价",  # 驱动因素
            "impact": "利好下游企业"  # 影响
        }

        # 价值分布评分
        value_distribution_score = self._score_value_distribution(
            profit_distribution,
            value_chain,
            value_transfer_trend
        )

        return {
            "profit_distribution": profit_distribution,
            "value_chain": value_chain,
            "value_transfer_trend": value_transfer_trend,
            "score": value_distribution_score,
            "assessment": self._assess_value_distribution(value_distribution_score),
            "update_time": datetime.now().isoformat()
        }

    # ========== 辅助分析方法 ==========

    async def _fetch_industry_news(self, industry_code: str) -> Dict[str, Any]:
        """获取行业新闻"""
        # 使用NewsTool获取行业新闻
        news_list = await self.news_tool.fetch_news(
            industry_code=industry_code,
            time_range="1w"
        )

        return {
            "news_list": news_list[:10],  # 只返回前10条
            "total_count": len(news_list),
            "update_time": datetime.now().isoformat()
        }

    def _assess_chain_position(
        self,
        upstream: Dict[str, Any],
        midstream: Dict[str, Any],
        downstream: Dict[str, Any],
        value_distribution: Dict[str, Any],
        stock_code: Optional[str]
    ) -> Dict[str, Any]:
        """
        评估产业链地位

        Args:
            upstream: 上游分析结果
            midstream: 中游分析结果
            downstream: 下游分析结果
            value_distribution: 价值分布结果
            stock_code: 股票代码

        Returns:
            产业链地位评估
        """
        # 确定产业链位置（如果提供了股票代码）
        if stock_code:
            # TODO: 根据股票代码确定产业链位置
            position = "中游"
            position_score = midstream["score"]
        else:
            position = "未指定"
            position_score = 0

        # 产业链地位评估
        if position == "上游":
            bargaining_power = upstream["overall_bargaining_power"]
            profit_share = value_distribution["profit_distribution"]["上游"]["profit_share"]
        elif position == "中游":
            bargaining_power = "中"
            profit_share = value_distribution["profit_distribution"]["中游"]["profit_share"]
        elif position == "下游":
            bargaining_power = downstream["customer_bargaining_power"]
            profit_share = value_distribution["profit_distribution"]["下游"]["profit_share"]
        else:
            bargaining_power = "未知"
            profit_share = 0

        # 地位评级
        if profit_share >= 40:
            position_level = "主导"
        elif profit_share >= 30:
            position_level = "强势"
        elif profit_share >= 20:
            position_level = "中游"
        else:
            position_level = "弱势"

        return {
            "position": position,
            "position_level": position_level,
            "bargaining_power": bargaining_power,
            "profit_share": profit_share,
            "position_score": position_score,
            "update_time": datetime.now().isoformat()
        }

    def _identify_investment_opportunities(
        self,
        upstream: Dict[str, Any],
        midstream: Dict[str, Any],
        downstream: Dict[str, Any],
        value_distribution: Dict[str, Any],
        news_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        识别投资机会

        Args:
            upstream: 上游分析结果
            midstream: 中游分析结果
            downstream: 下游分析结果
            value_distribution: 价值分布结果
            news_data: 新闻数据

        Returns:
            投资机会列表
        """
        opportunities = []

        # 上游机会
        if upstream["score"] >= 70:
            opportunities.append({
                "segment": "上游",
                "opportunity": "原材料供应商",
                "reason": "上游议价能力强，利润稳定",
                "priority": "高",
                "risk": "中"
            })

        # 中游机会
        if midstream["score"] >= 70:
            if midstream["tech_barriers"]["技术门槛"] == "高":
                opportunities.append({
                    "segment": "中游",
                    "opportunity": "技术领先企业",
                    "reason": "技术壁垒高，护城河深",
                    "priority": "高",
                    "risk": "低"
                })

        # 下游机会
        if downstream["score"] >= 70:
            if downstream["market_demand"]["potential"] == "高":
                opportunities.append({
                    "segment": "下游",
                    "opportunity": "品牌渠道企业",
                    "reason": "市场需求旺盛，价值占比高",
                    "priority": "高",
                    "risk": "中"
                })

        # 价值转移机会
        if value_distribution["value_transfer_trend"]["direction"] == "向下游转移":
            opportunities.append({
                "segment": "下游",
                "opportunity": "价值转移受益者",
                "reason": "价值向下转移，下游企业受益",
                "priority": "中",
                "risk": "低"
            })

        return opportunities

    def _identify_risk_points(
        self,
        upstream: Dict[str, Any],
        midstream: Dict[str, Any],
        downstream: Dict[str, Any],
        news_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        识别风险点

        Args:
            upstream: 上游分析结果
            midstream: 中游分析结果
            downstream: 下游分析结果
            news_data: 新闻数据

        Returns:
            风险点列表
        """
        risks = []

        # 上游风险
        if upstream["supplier_concentration"]["assessment"] == "高度集中":
            risks.append({
                "segment": "上游",
                "risk": "供应商集中风险",
                "level": "高",
                "description": "供应商高度集中，议价能力弱",
                "suggestion": "寻找替代供应商，分散采购"
            })

        if upstream["overall_bargaining_power"] == "强":
            risks.append({
                "segment": "上游",
                "risk": "原材料价格波动",
                "level": "中",
                "description": "上游议价能力强，成本压力大",
                "suggestion": "建立长期合同，锁定价格"
            })

        # 中游风险
        if midstream["capacity_analysis"]["supply_demand"] == "过剩":
            risks.append({
                "segment": "中游",
                "risk": "产能过剩",
                "level": "高",
                "description": "产能利用率低，竞争激烈",
                "suggestion": "谨慎投资，关注产能出清"
            })

        if midstream["tech_barriers"]["替代难度"] == "低":
            risks.append({
                "segment": "中游",
                "risk": "技术替代风险",
                "level": "中",
                "description": "技术壁垒低，容易被替代",
                "suggestion": "关注技术升级，提升竞争力"
            })

        # 下游风险
        if downstream["market_demand"]["saturation"] == "高":
            risks.append({
                "segment": "下游",
                "risk": "市场饱和",
                "level": "中",
                "description": "市场接近饱和，增长空间有限",
                "suggestion": "寻找新市场，拓展业务"
            })

        if downstream["customer_bargaining_power"] == "强":
            risks.append({
                "segment": "下游",
                "risk": "客户议价能力强",
                "level": "中",
                "description": "客户议价能力强，利润空间受压",
                "suggestion": "提升产品差异化，增强品牌"
            })

        return risks

    def _calculate_chain_score(
        self,
        upstream: Dict[str, Any],
        midstream: Dict[str, Any],
        downstream: Dict[str, Any],
        value_distribution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算产业链综合评分

        权重分配:
        - 上游: 25%
        - 中游: 35%
        - 下游: 30%
        - 价值分布: 10%
        """
        weights = {
            "upstream": 0.25,
            "midstream": 0.35,
            "downstream": 0.30,
            "value_distribution": 0.10
        }

        # 加权平均
        total_score = (
            upstream["score"] * weights["upstream"] +
            midstream["score"] * weights["midstream"] +
            downstream["score"] * weights["downstream"] +
            value_distribution["score"] * weights["value_distribution"]
        )

        # 评级
        if total_score >= 80:
            rating = "A"
            description = "产业链结构优秀，投资价值高"
        elif total_score >= 70:
            rating = "B"
            description = "产业链结构良好，适合投资"
        elif total_score >= 60:
            rating = "C"
            description = "产业链结构一般，谨慎投资"
        elif total_score >= 50:
            rating = "D"
            description = "产业链结构较差，观望为主"
        else:
            rating = "E"
            description = "产业链结构恶劣，不建议投资"

        return {
            "total_score": round(total_score, 2),
            "rating": rating,
            "description": description,
            "dimension_scores": {
                "upstream": upstream["score"],
                "midstream": midstream["score"],
                "downstream": downstream["score"],
                "value_distribution": value_distribution["score"]
            },
            "weights": weights
        }

    # ========== 评分和评估辅助方法 ==========

    def _assess_overall_bargaining_power(self, suppliers: List[Dict[str, Any]]) -> str:
        """评估整体议价能力"""
        strong_count = sum(1 for s in suppliers if s["bargaining_power"] == "强")
        if strong_count >= 2:
            return "强"
        elif strong_count >= 1:
            return "中"
        else:
            return "弱"

    def _score_upstream(self, suppliers, cost_structure, concentration, bargaining_power) -> float:
        """评分上游"""
        score = 60

        # 供应集中度影响
        if concentration["assessment"] == "中等集中":
            score += 10
        elif concentration["assessment"] == "分散":
            score += 15

        # 议价能力影响
        if bargaining_power == "弱":
            score += 15
        elif bargaining_power == "中":
            score += 5

        return min(100, max(0, score))

    def _assess_upstream(self, score: float) -> str:
        """评估上游"""
        if score >= 75:
            return "上游供应稳定，议价能力强"
        elif score >= 60:
            return "上游供应一般，议价能力中等"
        else:
            return "上游供应风险大，议价能力弱"

    def _score_midstream(self, manufacturers, tech_barriers, capacity, cost_advantage) -> float:
        """评分中游"""
        score = 60

        # 技术壁垒影响
        if tech_barriers["技术门槛"] == "高":
            score += 15
        elif tech_barriers["技术门槛"] == "中高":
            score += 10

        # 产能利用率影响
        if capacity["utilization_rate"] >= 85:
            score += 10
        elif capacity["utilization_rate"] >= 75:
            score += 5

        # 成本优势影响
        if cost_advantage["advantage_level"] == "高":
            score += 15
        elif cost_advantage["advantage_level"] == "中高":
            score += 10

        return min(100, max(0, score))

    def _assess_midstream(self, score: float) -> str:
        """评估中游"""
        if score >= 75:
            return "中游技术领先，竞争力强"
        elif score >= 60:
            return "中游技术一般，竞争力中等"
        else:
            return "中游技术薄弱，竞争力弱"

    def _assess_customer_bargaining_power(self, customers: List[Dict[str, Any]]) -> str:
        """评估客户议价能力"""
        high_sensitivity_count = sum(1 for c in customers if c["price_sensitivity"] == "高")
        if high_sensitivity_count >= 2:
            return "强"
        elif high_sensitivity_count >= 1:
            return "中"
        else:
            return "弱"

    def _score_downstream(self, customers, channels, demand, bargaining_power) -> float:
        """评分下游"""
        score = 60

        # 市场需求影响
        if demand["potential"] == "高":
            score += 15
        elif demand["potential"] == "中高":
            score += 10

        # 增长率影响
        if demand["growth_rate"] >= 8:
            score += 10
        elif demand["growth_rate"] >= 5:
            score += 5

        # 客户议价能力影响
        if bargaining_power == "弱":
            score += 10
        elif bargaining_power == "中":
            score += 5

        return min(100, max(0, score))

    def _assess_downstream(self, score: float) -> str:
        """评估下游"""
        if score >= 75:
            return "下游需求旺盛，市场空间大"
        elif score >= 60:
            return "下游需求一般，市场空间中等"
        else:
            return "下游需求疲软，市场空间小"

    def _score_value_distribution(self, profit_dist, value_chain, transfer_trend) -> float:
        """评分价值分布"""
        score = 60

        # 价值集中度影响
        if value_chain["value_concentration"] == "高":
            score += 10
        elif value_chain["value_concentration"] == "中":
            score += 5

        # 价值转移趋势影响
        if transfer_trend["speed"] == "快":
            score += 10
        elif transfer_trend["speed"] == "中":
            score += 5

        return min(100, max(0, score))

    def _assess_value_distribution(self, score: float) -> str:
        """评估价值分布"""
        if score >= 75:
            return "价值分布清晰，关键环节明确"
        elif score >= 60:
            return "价值分布一般，关键环节中等"
        else:
            return "价值分布混乱，关键环节不明"
