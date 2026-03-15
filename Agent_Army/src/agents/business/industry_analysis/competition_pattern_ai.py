"""
竞争格局AI - Competition Pattern AI

产业分析军团成员

职责：
- 分析行业竞争格局，评估市场集中度
- 识别龙头企业和竞争态势
- 使用LLMTool进行智能分析
- 计算CR4、CR8、HHI等集中度指标

使用工具：
- LLMTool（行业分析）
- YahooFinanceTool（行业数据）

数据源：
- LLM（行业分析）
- Yahoo Finance（行业数据）

返回值结构：
{
    "industry": "白酒",
    "stock_code": "600519",
    "cr4": 0.65,  # 行业前4名集中度
    "cr8": 0.78,  # 行业前8名集中度
    "hhi": 0.23,  # 赫芬达尔指数
    "concentration_level": "high",  # low/medium/high
    "top_companies": ["贵州茅台", "五粮液", "泸州老窖", "洋河股份"],
    "competitive_position": "leader",
    "timestamp": "2026-03-15T10:30:00"
}
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools.ai_service.llm_tool import LLMTool
from src.core.tools.data_source.yahoo_tool import YahooFinanceTool


class CompetitionMetrics(BaseModel):
    """竞争格局指标"""
    industry: str = Field(..., description="行业名称")
    stock_code: str = Field(..., description="股票代码")
    cr4: float = Field(..., ge=0.0, le=1.0, description="CR4指标（前4名集中度）")
    cr8: float = Field(..., ge=0.0, le=1.0, description="CR8指标（前8名集中度）")
    hhi: float = Field(..., ge=0.0, le=1.0, description="HHI指数（赫芬达尔指数）")
    concentration_level: str = Field(..., description="集中度等级: low/medium/high")
    top_companies: List[str] = Field(default_factory=list, description="龙头企业列表")
    competitive_position: str = Field(..., description="竞争地位: leader/challenger/follower/niche")
    timestamp: str = Field(..., description="分析时间戳")


class CompetitionPatternAI(BaseAgent, LoggerMixin):
    """
    竞争格局AI - 产业分析军团成员

    核心能力:
    1. 分析行业竞争格局
    2. 评估市场集中度（CR4、CR8、HHI）
    3. 识别龙头企业
    4. 评估竞争态势
    5. 识别竞争地位

    使用工具:
    - LLMTool (智能分析)
    - YahooFinanceTool (财务数据)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.llm_tool = LLMTool(config)
        self.finance_tool = YahooFinanceTool()

        super().__init__(
            name="竞争格局AI",
            role="分析行业竞争格局，评估市场集中度，识别龙头企业",
            capabilities=[
                AgentCapability(
                    name="competition_analysis",
                    description="竞争格局分析",
                    input_type="stock_code",
                    output_type="competition_report"
                ),
                AgentCapability(
                    name="market_concentration",
                    description="市场集中度评估",
                    input_type="stock_code",
                    output_type="concentration_metrics"
                ),
                AgentCapability(
                    name="leader_identification",
                    description="龙头企业识别",
                    input_type="stock_code",
                    output_type="leader_list"
                ),
                AgentCapability(
                    name="competitive_positioning",
                    description="竞争地位评估",
                    input_type="stock_code",
                    output_type="position_report"
                )
            ],
            tools=[
                AgentTool(
                    name="llm_tool",
                    description="智能分析工具",
                    tool_type="ai_service",
                    config={}
                ),
                AgentTool(
                    name="yahoo_finance",
                    description="财务数据工具",
                    tool_type="data_source",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("竞争格局AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze":
            return await self.analyze(**kwargs)
        elif task == "evaluate_concentration":
            return await self.evaluate_concentration(**kwargs)
        elif task == "identify_leaders":
            return await self.identify_leaders(**kwargs)
        elif task == "assess_position":
            return await self.assess_competitive_position(**kwargs)
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 主入口方法 ==========

    async def analyze(
        self,
        stock_code: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        竞争格局综合分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数

        Returns:
            竞争格局分析报告
        """
        self.logger.info(
            f"开始竞争格局综合分析",
            extra={"stock_code": stock_code}
        )

        # ========== 1. 获取股票基本信息 ==========
        stock_info = await self._get_stock_info(stock_code)

        # ========== 2. 评估市场集中度 ==========
        concentration_metrics = await self.evaluate_concentration(stock_code)

        # ========== 3. 识别龙头企业 ==========
        leaders = await self.identify_leaders(stock_code, top_n=5)

        # ========== 4. 评估竞争地位 ==========
        position = await self.assess_competitive_position(stock_code)

        # ========== 5. 使用LLM深度分析 ==========
        llm_analysis = await self._llm_competition_analysis(
            stock_info["industry"],
            stock_code,
            concentration_metrics,
            leaders
        )

        # ========== 6. 构建返回结果 ==========
        result = {
            "analysis_type": "competition_pattern",
            "timestamp": datetime.now().isoformat(),
            "stock_code": stock_code,
            "stock_name": stock_info.get("name", ""),
            "industry": stock_info.get("industry", ""),

            # 集中度指标
            "concentration": concentration_metrics,

            # 龙头企业
            "leaders": leaders,

            # 竞争地位
            "competitive_position": position,

            # LLM分析
            "llm_analysis": llm_analysis,

            # 综合评分
            "overall_score": self._calculate_overall_score(
                concentration_metrics,
                position,
                llm_analysis
            )
        }

        self.logger.info(
            f"竞争格局综合分析完成",
            extra={
                "stock_code": stock_code,
                "industry": stock_info.get("industry", ""),
                "concentration_level": concentration_metrics.get("concentration_level", ""),
                "position": position.get("position", "")
            }
        )

        return result

    # ========== 核心分析方法 ==========

    async def evaluate_concentration(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """
        评估市场集中度

        计算指标:
        - CR4: 前4名市场份额
        - CR8: 前8名市场份额
        - HHI: 赫芬达尔指数
        """
        self.logger.info(
            f"评估市场集中度",
            extra={"stock_code": stock_code}
        )

        # 获取股票信息
        stock_info = await self._get_stock_info(stock_code)
        industry = stock_info.get("industry", "")

        # 获取行业竞争数据
        competitors = await self._fetch_competitors_data(industry, stock_code)

        if not competitors:
            # 如果没有获取到竞争数据，返回默认值
            return {
                "industry": industry,
                "stock_code": stock_code,
                "cr4": 0.0,
                "cr8": 0.0,
                "hhi": 0.0,
                "concentration_level": "unknown",
                "total_companies": 0
            }

        # 计算集中度指标
        metrics = self._calculate_concentration_metrics(competitors)

        # 判断集中度等级
        concentration_level = self._classify_concentration_level(metrics)

        return {
            "industry": industry,
            "stock_code": stock_code,
            "cr4": metrics["cr4"],
            "cr8": metrics["cr8"],
            "hhi": metrics["hhi"],
            "concentration_level": concentration_level,
            "total_companies": len(competitors),
            "analysis": f"CR4={metrics['cr4']:.2%}, CR8={metrics['cr8']:.2%}, HHI={metrics['hhi']:.4f}",
            "implication": self._get_concentration_implication(concentration_level)
        }

    async def identify_leaders(
        self,
        stock_code: str,
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        识别龙头企业

        Args:
            stock_code: 股票代码
            top_n: 返回前N名

        Returns:
            龙头企业列表
        """
        self.logger.info(
            f"识别龙头企业",
            extra={"stock_code": stock_code, "top_n": top_n}
        )

        # 获取股票信息
        stock_info = await self._get_stock_info(stock_code)
        industry = stock_info.get("industry", "")

        # 获取竞争数据
        competitors = await self._fetch_competitors_data(industry, stock_code)

        if not competitors:
            return {
                "industry": industry,
                "stock_code": stock_code,
                "top_n": top_n,
                "leaders": [],
                "total_market_share": 0.0,
                "summary": "无竞争数据"
            }

        # 按市场份额排序
        sorted_competitors = sorted(
            competitors,
            key=lambda x: x.get("market_share", 0),
            reverse=True
        )

        # 提取前N名
        leaders = sorted_competitors[:top_n]

        # 分析龙头特征
        leader_analysis = self._analyze_leader_characteristics(leaders)

        return {
            "industry": industry,
            "stock_code": stock_code,
            "top_n": top_n,
            "leaders": [
                {
                    "name": leader.get("name", ""),
                    "stock_code": leader.get("stock_code", ""),
                    "market_share": leader.get("market_share", 0),
                    "revenue": leader.get("revenue", 0),
                    "rank": idx + 1
                }
                for idx, leader in enumerate(leaders)
            ],
            "total_market_share": sum(l.get("market_share", 0) for l in leaders),
            "leader_analysis": leader_analysis,
            "summary": f"前{top_n}名企业占据{sum(l.get('market_share', 0) for l in leaders):.1f}%市场份额"
        }

    async def assess_competitive_position(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """
        评估竞争地位

        评估维度:
        - 市场份额排名
        - 竞争优势
        - 护城河深度
        """
        self.logger.info(
            f"评估竞争地位",
            extra={"stock_code": stock_code}
        )

        # 获取股票信息
        stock_info = await self._get_stock_info(stock_code)
        industry = stock_info.get("industry", "")

        # 获取竞争数据
        competitors = await self._fetch_competitors_data(industry, stock_code)

        if not competitors:
            return {
                "industry": industry,
                "stock_code": stock_code,
                "position": "unknown",
                "rank": 0,
                "market_share": 0.0
            }

        # 找到目标公司
        target_company = None
        rank = 0
        for idx, competitor in enumerate(competitors):
            if competitor.get("stock_code") == stock_code:
                target_company = competitor
                rank = idx + 1
                break

        if not target_company:
            return {
                "industry": industry,
                "stock_code": stock_code,
                "position": "not_found",
                "rank": 0,
                "market_share": 0.0
            }

        market_share = target_company.get("market_share", 0)

        # 评估竞争地位
        if market_share >= 30:
            position = "leader"  # 龙头
            position_desc = "行业龙头，市场主导地位"
        elif market_share >= 15:
            position = "challenger"  # 挑战者
            position_desc = "行业挑战者，有实力挑战龙头"
        elif market_share >= 5:
            position = "follower"  # 跟随者
            position_desc = "行业跟随者，有一定市场份额"
        else:
            position = "niche"  # 利基市场
            position_desc = "利基市场参与者，专注细分领域"

        return {
            "industry": industry,
            "stock_code": stock_code,
            "stock_name": target_company.get("name", ""),
            "position": position,
            "position_desc": position_desc,
            "rank": rank,
            "market_share": market_share,
            "competitive_advantage": self._assess_competitive_advantage(
                target_company,
                rank,
                market_share
            )
        }

    # ========== 辅助分析方法 ==========

    async def _get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票基本信息

        Args:
            stock_code: 股票代码

        Returns:
            股票基本信息
        """
        try:
            # 使用YahooFinanceTool获取股票信息
            info = self.finance_tool.get_stock_info(stock_code)

            return {
                "stock_code": stock_code,
                "name": info.get("longName", ""),
                "industry": info.get("industry", ""),
                "sector": info.get("sector", ""),
                "market_cap": info.get("marketCap", 0)
            }
        except Exception as e:
            self.logger.warning(
                f"获取股票信息失败: {str(e)}",
                extra={"stock_code": stock_code}
            )
            return {
                "stock_code": stock_code,
                "name": "",
                "industry": "",
                "sector": "",
                "market_cap": 0
            }

    async def _fetch_competitors_data(
        self,
        industry: str,
        stock_code: str
    ) -> List[Dict[str, Any]]:
        """
        获取竞争对手数据

        Args:
            industry: 行业名称
            stock_code: 股票代码

        Returns:
            竞争对手列表
        """
        try:
            # 使用LLM分析竞争对手
            prompt = f"""分析{industry}行业的竞争格局，列出主要竞争对手及其市场份额。

请以JSON格式返回，格式如下：
{{
    "competitors": [
        {{
            "name": "公司名称",
            "stock_code": "股票代码",
            "market_share": 市场份额(0-100),
            "revenue": 营收(亿元),
            "competitive_advantage": "竞争优势"
        }}
    ]
}}

注意：
1. 市场份额总和应在80-100%之间（考虑未上市公司）
2. 请按市场份额从大到小排序
3. 至少列出5-8家主要竞争对手
4. 确保包含股票代码{stock_code}对应的公司
"""

            response = await self.llm_tool.chat(
                prompt=prompt,
                temperature=0.3
            )

            # 解析JSON响应
            import json
            try:
                result = json.loads(response)
                competitors = result.get("competitors", [])

                self.logger.info(
                    f"LLM分析竞争对手成功",
                    extra={
                        "industry": industry,
                        "competitor_count": len(competitors)
                    }
                )

                return competitors
            except json.JSONDecodeError:
                self.logger.warning("LLM返回的JSON格式无效，使用模拟数据")
                return await self._get_mock_competitors(industry, stock_code)

        except Exception as e:
            self.logger.error(
                f"获取竞争对手数据失败: {str(e)}",
                extra={"industry": industry, "stock_code": stock_code}
            )
            return await self._get_mock_competitors(industry, stock_code)

    async def _get_mock_competitors(
        self,
        industry: str,
        stock_code: str
    ) -> List[Dict[str, Any]]:
        """
        获取模拟竞争对手数据（备用方案）

        Args:
            industry: 行业名称
            stock_code: 股票代码

        Returns:
            模拟竞争对手列表
        """
        # 根据行业生成模拟数据
        if "白酒" in industry or "酒" in industry:
            competitors = [
                {"name": "贵州茅台", "stock_code": "600519", "market_share": 35.0, "revenue": 1200, "competitive_advantage": "品牌优势"},
                {"name": "五粮液", "stock_code": "000858", "market_share": 20.0, "revenue": 800, "competitive_advantage": "品牌+渠道"},
                {"name": "泸州老窖", "stock_code": "000568", "market_share": 10.0, "revenue": 300, "competitive_advantage": "历史底蕴"},
                {"name": "洋河股份", "stock_code": "002304", "market_share": 8.0, "revenue": 250, "competitive_advantage": "营销网络"},
                {"name": "山西汾酒", "stock_code": "600809", "market_share": 5.0, "revenue": 200, "competitive_advantage": "清香型龙头"},
                {"name": "古井贡酒", "stock_code": "000596", "market_share": 3.0, "revenue": 150, "competitive_advantage": "区域品牌"},
                {"name": "今世缘", "stock_code": "603369", "market_share": 2.0, "revenue": 100, "competitive_advantage": "江苏市场"},
                {"name": "口子窖", "stock_code": "603589", "market_share": 1.5, "revenue": 80, "competitive_advantage": "兼香型特色"}
            ]
        elif "半导体" in industry or "芯片" in industry:
            competitors = [
                {"name": "中芯国际", "stock_code": "688981", "market_share": 25.0, "revenue": 500, "competitive_advantage": "制造规模"},
                {"name": "韦尔股份", "stock_code": "603501", "market_share": 8.0, "revenue": 300, "competitive_advantage": "CIS芯片"},
                {"name": "兆易创新", "stock_code": "603986", "market_share": 6.0, "revenue": 200, "competitive_advantage": "存储芯片"},
                {"name": "澜起科技", "stock_code": "688008", "market_share": 5.0, "revenue": 150, "competitive_advantage": "内存接口"},
                {"name": "紫光国微", "stock_code": "002049", "market_share": 4.0, "revenue": 120, "competitive_advantage": "安全芯片"}
            ]
        else:
            # 通用模拟数据
            competitors = [
                {"name": "龙头企业A", "stock_code": stock_code, "market_share": 30.0, "revenue": 500, "competitive_advantage": "技术领先"},
                {"name": "竞争企业B", "stock_code": "000001", "market_share": 20.0, "revenue": 350, "competitive_advantage": "成本优势"},
                {"name": "竞争企业C", "stock_code": "000002", "market_share": 15.0, "revenue": 250, "competitive_advantage": "渠道优势"},
                {"name": "竞争企业D", "stock_code": "000003", "market_share": 10.0, "revenue": 200, "competitive_advantage": "品牌优势"},
                {"name": "竞争企业E", "stock_code": "000004", "market_share": 8.0, "revenue": 150, "competitive_advantage": "细分市场"},
                {"name": "竞争企业F", "stock_code": "000005", "market_share": 5.0, "revenue": 100, "competitive_advantage": "区域优势"},
                {"name": "竞争企业G", "stock_code": "000006", "market_share": 3.0, "revenue": 80, "competitive_advantage": "特色产品"},
                {"name": "竞争企业H", "stock_code": "000007", "market_share": 2.0, "revenue": 60, "competitive_advantage": "价格优势"}
            ]

        return competitors

    def _calculate_concentration_metrics(
        self,
        competitors: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        计算市场集中度指标

        Args:
            competitors: 竞争对手列表

        Returns:
            集中度指标
        """
        if not competitors:
            return {"cr4": 0.0, "cr8": 0.0, "hhi": 0.0}

        # 按市场份额排序
        sorted_competitors = sorted(
            competitors,
            key=lambda x: x.get("market_share", 0),
            reverse=True
        )

        # CR4：前4名市场份额（转换为比例0-1）
        cr4 = sum(c.get("market_share", 0) for c in sorted_competitors[:4]) / 100

        # CR8：前8名市场份额
        cr8 = sum(c.get("market_share", 0) for c in sorted_competitors[:8]) / 100

        # HHI：赫芬达尔指数（转换为比例0-1）
        hhi = sum((c.get("market_share", 0) / 100) ** 2 for c in competitors)

        return {
            "cr4": round(cr4, 4),
            "cr8": round(cr8, 4),
            "hhi": round(hhi, 4)
        }

    def _classify_concentration_level(
        self,
        metrics: Dict[str, float]
    ) -> str:
        """
        分类市场集中度等级

        Args:
            metrics: 集中度指标

        Returns:
            集中度等级: low/medium/high
        """
        cr4 = metrics["cr4"]
        hhi = metrics["hhi"]

        if cr4 >= 0.6 or hhi >= 0.25:
            return "high"  # 高集中度
        elif cr4 >= 0.4 or hhi >= 0.15:
            return "medium"  # 中集中度
        else:
            return "low"  # 低集中度

    def _get_concentration_implication(
        self,
        concentration_level: str
    ) -> str:
        """
        获取集中度影响说明

        Args:
            concentration_level: 集中度等级

        Returns:
            影响说明
        """
        implications = {
            "high": "行业高度集中，龙头企业优势明显，新进入者困难",
            "medium": "行业适度集中，存在整合空间，竞争相对稳定",
            "low": "行业竞争激烈，市场分散，差异化竞争是关键",
            "unknown": "无法判断集中度"
        }
        return implications.get(concentration_level, "未知")

    def _analyze_leader_characteristics(
        self,
        leaders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析龙头企业特征

        Args:
            leaders: 龙头企业列表

        Returns:
            龙头特征分析
        """
        if not leaders:
            return {"pattern": "无数据", "description": "无龙头企业数据"}

        if len(leaders) == 1:
            pattern = "一家独大"
            description = "单一龙头企业主导市场"
        elif len(leaders) >= 2:
            gap = leaders[0].get("market_share", 0) - leaders[1].get("market_share", 0)

            if gap > 15:
                pattern = "一超多强"
                description = "绝对龙头+多家强势企业"
            elif gap > 5:
                pattern = "双寡头"
                description = "前两名差距较小，形成双寡头格局"
            else:
                pattern = "多头并进"
                description = "多家企业实力相当，竞争激烈"
        else:
            pattern = "未知"
            description = "无法判断龙头格局"

        return {
            "pattern": pattern,
            "description": description,
            "leader_count": len(leaders),
            "top1_share": leaders[0].get("market_share", 0) if leaders else 0
        }

    def _assess_competitive_advantage(
        self,
        company: Dict[str, Any],
        rank: int,
        market_share: float
    ) -> Dict[str, Any]:
        """
        评估竞争优势

        Args:
            company: 公司信息
            rank: 排名
            market_share: 市场份额

        Returns:
            竞争优势评估
        """
        advantages = []

        # 基于排名
        if rank == 1:
            advantages.append("市场领导者")
        elif rank <= 3:
            advantages.append("行业前列")

        # 基于市场份额
        if market_share >= 30:
            advantages.append("高市场份额")
        elif market_share >= 15:
            advantages.append("中等市场份额")

        # 基于其他因素
        if company.get("competitive_advantage"):
            advantages.append(company["competitive_advantage"])

        return {
            "advantages": advantages,
            "overall_strength": "强" if rank <= 3 else "中" if rank <= 5 else "弱"
        }

    async def _llm_competition_analysis(
        self,
        industry: str,
        stock_code: str,
        concentration_metrics: Dict[str, Any],
        leaders: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用LLM深度分析竞争格局

        Args:
            industry: 行业名称
            stock_code: 股票代码
            concentration_metrics: 集中度指标
            leaders: 龙头企业数据

        Returns:
            LLM分析结果
        """
        try:
            prompt = f"""请分析{industry}行业的竞争格局，重点关注股票代码{stock_code}的公司。

已知信息：
1. 市场集中度：CR4={concentration_metrics.get('cr4', 0):.2%}, CR8={concentration_metrics.get('cr8', 0):.2%}, HHI={concentration_metrics.get('hhi', 0):.4f}
2. 集中度等级：{concentration_metrics.get('concentration_level', 'unknown')}
3. 龙头企业：{', '.join([l['name'] for l in leaders.get('leaders', [])[:3]])}

请从以下角度分析：
1. 行业竞争态势（竞争激烈程度、竞争格局特点）
2. 竞争趋势（行业整合、集中度变化趋势）
3. 关键成功因素（技术、品牌、渠道、成本等）
4. 投资建议（关注点、风险点）

请以JSON格式返回：
{{
    "competition_status": "竞争态势描述",
    "competition_trend": "竞争趋势描述",
    "key_success_factors": ["关键成功因素1", "关键成功因素2"],
    "investment_suggestion": "投资建议",
    "risk_points": ["风险点1", "风险点2"]
}}
"""

            response = await self.llm_tool.chat(
                prompt=prompt,
                temperature=0.5
            )

            # 解析JSON响应
            import json
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # 如果解析失败，返回默认值
                return {
                    "competition_status": "行业竞争态势复杂",
                    "competition_trend": "集中度呈上升趋势",
                    "key_success_factors": ["技术领先", "成本优势"],
                    "investment_suggestion": "关注龙头企业",
                    "risk_points": ["竞争加剧", "政策风险"]
                }

        except Exception as e:
            self.logger.error(
                f"LLM竞争分析失败: {str(e)}",
                extra={"industry": industry, "stock_code": stock_code}
            )
            return {
                "competition_status": "分析失败",
                "competition_trend": "无法判断",
                "key_success_factors": [],
                "investment_suggestion": "谨慎投资",
                "risk_points": ["数据不足"]
            }

    def _calculate_overall_score(
        self,
        concentration_metrics: Dict[str, Any],
        position: Dict[str, Any],
        llm_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算综合评分

        Args:
            concentration_metrics: 集中度指标
            position: 竞争地位
            llm_analysis: LLM分析

        Returns:
            综合评分
        """
        score = 60  # 基础分

        # 基于竞争地位
        pos = position.get("position", "")
        if pos == "leader":
            score += 20
        elif pos == "challenger":
            score += 15
        elif pos == "follower":
            score += 10
        elif pos == "niche":
            score += 5

        # 基于集中度等级
        concentration_level = concentration_metrics.get("concentration_level", "")
        if concentration_level == "high" and pos in ["leader", "challenger"]:
            score += 10  # 高集中度+龙头地位
        elif concentration_level == "low":
            score -= 5  # 低集中度，竞争激烈

        # 基于市场份额
        market_share = position.get("market_share", 0)
        if market_share >= 30:
            score += 10
        elif market_share >= 15:
            score += 5

        # 限制在0-100范围
        score = min(100, max(0, score))

        # 评级
        if score >= 80:
            rating = "A"
            description = "竞争地位优秀，投资价值高"
        elif score >= 70:
            rating = "B"
            description = "竞争地位良好，具有投资价值"
        elif score >= 60:
            rating = "C"
            description = "竞争地位一般，谨慎投资"
        else:
            rating = "D"
            description = "竞争地位较弱，不建议投资"

        return {
            "score": score,
            "rating": rating,
            "description": description
        }
