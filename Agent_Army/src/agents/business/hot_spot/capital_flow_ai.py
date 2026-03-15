"""
资金流向AI - Capital Flow AI

职责：
- 追踪资金流入流出，分析主力动向
- 使用AKShareTool获取资金流向数据
- 分析主力、超大单、大单、中单、小单的流向
- 生成资金评级和建议

技术要求：
1. 继承BaseBusinessAgent
2. 使用工具库：AKShareTool
3. 数据源：AKShare（个股资金流向）
4. 返回结构：Pydantic Model或Dict

作者：Agent Army
日期：2026-03-15
版本：v2.0（重构版，继承BaseBusinessAgent）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import pandas as pd

from src.agents.business.base_business_agent import (
    BusinessAgent,
    AnalysisResult
)
from src.core.tools.data_source.akshare_tool import AKShareTool
from src.core.logger import get_logger


class CapitalFlowData(BaseModel):
    """资金流向数据模型"""

    # 基本信息
    stock_code: str = Field(description="股票代码")
    timestamp: str = Field(description="时间戳")

    # 资金流向数据（元）
    net_inflow: float = Field(description="净流入（元）")
    main_net_inflow: float = Field(description="主力净流入（元）")
    super_large_net: float = Field(description="超大单净流入（元）")
    large_net: float = Field(description="大单净流入（元）")
    medium_net: float = Field(description="中单净流入（元）")
    small_net: float = Field(description="小单净流入（元）")

    # 评级
    rating: str = Field(description="资金评级：accumulation(吸筹)/distribution(派发)/neutral(中性)")

    # 额外信息
    analysis_period: str = Field(default="", description="分析周期")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")


class CapitalFlowAI(BusinessAgent):
    """
    资金流向AI - 热点捕捉军团成员

    职责：
    - 追踪资金流入流出，分析主力动向
    - 分析主力、超大单、大单、中单、小单的流向
    - 识别资金吸筹和派发信号
    - 生成资金评级和投资建议

    使用工具：
    - AKShareTool（获取个股资金流向数据）
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化资金流向AI"""
        # 初始化工具
        self.akshare_tool = AKShareTool()

        # 调用父类初始化
        super().__init__(
            name="资金流向AI",
            role="追踪资金流入流出，分析主力动向，识别资金趋势",
            corps="热点捕捉军团",
            analysis_type="capital_flow",
            capabilities=None,  # 使用默认能力
            tools=None,  # 使用默认工具
            config=config
        )

        self.logger.info(
            "资金流向AI初始化完成",
            agent=self.name,
            corps=self.corps,
            tool="AKShareTool"
        )

    async def analyze(
        self,
        stock_code: str,
        market: str = "sh",
        days: int = 5,
        **kwargs
    ) -> AnalysisResult:
        """
        分析资金流向

        Args:
            stock_code: 股票代码（如 "600519"）
            market: 市场代码（"sh" 上海，"sz" 深圳）
            days: 分析天数
            **kwargs: 其他参数

        Returns:
            AnalysisResult: 分析结果
        """
        self.logger.info(
            "开始分析资金流向",
            stock_code=stock_code,
            market=market,
            days=days
        )

        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            error_msg = f"股票代码格式错误: {stock_code}"
            self.logger.error(error_msg)
            return AnalysisResult(
                agent_name=self.name,
                analysis_type=self.analysis_type,
                conclusion=error_msg,
                confidence=0.0,
                details={},
                risks=[error_msg],
                recommendations=[]
            )

        # 获取资金流向数据
        capital_data = await self._get_capital_flow_data(
            stock_code,
            market,
            days
        )

        if not capital_data:
            error_msg = f"未能获取 {stock_code} 的资金流向数据"
            self.logger.warning(error_msg)
            return AnalysisResult(
                agent_name=self.name,
                analysis_type=self.analysis_type,
                conclusion=error_msg,
                confidence=0.0,
                details={},
                risks=[error_msg],
                recommendations=["请稍后重试或检查股票代码"]
            )

        # 分析资金流向
        flow_analysis = self._analyze_capital_flow(capital_data)

        # 生成结论
        conclusion = self._generate_conclusion(flow_analysis)

        # 生成建议
        recommendations = self._generate_recommendations(flow_analysis)

        # 风险提示
        risks = self._identify_risks(flow_analysis)

        # 构建返回结果
        result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=conclusion,
            confidence=self._calculate_confidence(flow_analysis),
            details={
                "capital_flow_data": flow_analysis,
                "raw_data": capital_data[-1] if capital_data else {}
            },
            risks=risks,
            recommendations=recommendations
        )

        self.logger.info(
            "资金流向分析完成",
            stock_code=stock_code,
            rating=flow_analysis.get("rating", "unknown"),
            net_inflow=flow_analysis.get("net_inflow", 0)
        )

        return result

    async def _get_capital_flow_data(
        self,
        stock_code: str,
        market: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """
        获取资金流向数据

        Args:
            stock_code: 股票代码
            market: 市场
            days: 天数

        Returns:
            资金流向数据列表
        """
        try:
            # 使用AKShareTool获取数据
            df = self.akshare_tool.get_individual_fund_flow(
                stock_code=stock_code,
                market=market
            )

            if df.empty:
                self.logger.warning(
                    "未获取到资金流向数据",
                    stock_code=stock_code,
                    market=market
                )
                return []

            # 取最近N天数据
            recent_data = df.head(days)

            # 转换为字典列表
            data_list = []
            for _, row in recent_data.iterrows():
                data_list.append({
                    "date": row.get("日期", ""),
                    "close_price": row.get("收盘价", 0.0),
                    "change_percent": row.get("涨跌幅", 0.0),
                    "net_inflow": row.get("主力净流入", 0.0),
                    "main_net_inflow": row.get("主力净流入", 0.0),
                    "super_large_net": row.get("超大单净流入", 0.0),
                    "large_net": row.get("大单净流入", 0.0),
                    "medium_net": row.get("中单净流入", 0.0),
                    "small_net": row.get("小单净流入", 0.0)
                })

            self.logger.info(
                "成功获取资金流向数据",
                stock_code=stock_code,
                count=len(data_list)
            )

            return data_list

        except Exception as e:
            self.logger.error(
                "获取资金流向数据失败",
                stock_code=stock_code,
                error=str(e)
            )
            return []

    def _analyze_capital_flow(
        self,
        capital_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析资金流向

        Args:
            capital_data: 资金流向数据

        Returns:
            分析结果
        """
        if not capital_data:
            return {
                "rating": "neutral",
                "net_inflow": 0.0,
                "pattern": "no_data"
            }

        # 计算累计数据（取最近一天或累计多天）
        latest = capital_data[0]  # 最新数据

        # 各类型资金净流入
        net_inflow = latest.get("net_inflow", 0.0)
        main_net_inflow = latest.get("main_net_inflow", 0.0)
        super_large_net = latest.get("super_large_net", 0.0)
        large_net = latest.get("large_net", 0.0)
        medium_net = latest.get("medium_net", 0.0)
        small_net = latest.get("small_net", 0.0)

        # 判断资金评级
        rating, pattern = self._determine_rating(
            net_inflow,
            main_net_inflow,
            super_large_net,
            large_net
        )

        # 计算资金强度（0-100）
        strength = self._calculate_strength(
            net_inflow,
            main_net_inflow
        )

        # 分析主力与散户关系
        main_retail_relation = self._analyze_main_retail_relation(
            main_net_inflow,
            medium_net,
            small_net
        )

        return {
            "stock_code": latest.get("stock_code", ""),
            "timestamp": datetime.now().isoformat(),

            # 资金流向数据
            "net_inflow": net_inflow,
            "main_net_inflow": main_net_inflow,
            "super_large_net": super_large_net,
            "large_net": large_net,
            "medium_net": medium_net,
            "small_net": small_net,

            # 评级和模式
            "rating": rating,
            "pattern": pattern,
            "strength": strength,

            # 主力与散户关系
            "main_retail_relation": main_retail_relation,

            # 分析结论
            "summary": self._generate_flow_summary(
                rating,
                pattern,
                main_retail_relation
            )
        }

    def _determine_rating(
        self,
        net_inflow: float,
        main_net_inflow: float,
        super_large_net: float,
        large_net: float
    ) -> tuple[str, str]:
        """
        确定资金评级

        Args:
            net_inflow: 净流入
            main_net_inflow: 主力净流入
            super_large_net: 超大单净流入
            large_net: 大单净流入

        Returns:
            (rating, pattern) 评级和模式
        """
        # 判断吸筹/派发信号
        if main_net_inflow > 0 and super_large_net > 0:
            # 主力净流入且超大单净流入 → 吸筹
            if main_net_inflow > 10000000:  # 1000万以上
                return "accumulation", "strong_accumulation"
            else:
                return "accumulation", "mild_accumulation"
        elif main_net_inflow < 0 and super_large_net < 0:
            # 主力净流出且超大单净流出 → 派发
            if main_net_inflow < -10000000:
                return "distribution", "strong_distribution"
            else:
                return "distribution", "mild_distribution"
        else:
            # 中性
            return "neutral", "neutral"

    def _calculate_strength(
        self,
        net_inflow: float,
        main_net_inflow: float
    ) -> float:
        """
        计算资金强度（0-100）

        Args:
            net_inflow: 净流入
            main_net_inflow: 主力净流入

        Returns:
            强度分数
        """
        # 基础分数50
        base_score = 50.0

        # 根据主力净流入调整
        # 每1000万调整1分，上限30分
        main_inflow_million = main_net_inflow / 10000000
        main_adjustment = min(30, max(-30, main_inflow_million))

        # 总分
        total_score = base_score + main_adjustment

        # 限制在0-100范围
        return max(0.0, min(100.0, total_score))

    def _analyze_main_retail_relation(
        self,
        main_net_inflow: float,
        medium_net: float,
        small_net: float
    ) -> str:
        """
        分析主力与散户关系

        Args:
            main_net_inflow: 主力净流入
            medium_net: 中单净流入（散户）
            small_net: 小单净流入（散户）

        Returns:
            关系描述
        """
        retail_net = medium_net + small_net

        if main_net_inflow > 0 and retail_net < 0:
            return "主力吸筹，散户离场（看好）"
        elif main_net_inflow < 0 and retail_net > 0:
            return "主力出货，散户接盘（警惕）"
        elif main_net_inflow > 0 and retail_net > 0:
            return "主力散户同向买入（强势）"
        elif main_net_inflow < 0 and retail_net < 0:
            return "主力散户同向卖出（弱势）"
        else:
            return "资金流向分化"

    def _generate_flow_summary(
        self,
        rating: str,
        pattern: str,
        main_retail_relation: str
    ) -> str:
        """
        生成资金流向摘要

        Args:
            rating: 评级
            pattern: 模式
            main_retail_relation: 主力散户关系

        Returns:
            摘要文本
        """
        summary = f"资金评级：{rating}，"

        if pattern == "strong_accumulation":
            summary += "主力持续大举吸筹，"
        elif pattern == "mild_accumulation":
            summary += "主力小幅吸筹，"
        elif pattern == "strong_distribution":
            summary += "主力持续大幅派发，"
        elif pattern == "mild_distribution":
            summary += "主力小幅派发，"
        else:
            summary += "资金流向中性，"

        summary += f"{main_retail_relation}。"

        return summary

    def _generate_conclusion(self, flow_analysis: Dict[str, Any]) -> str:
        """
        生成分析结论

        Args:
            flow_analysis: 资金流向分析

        Returns:
            结论文本
        """
        rating = flow_analysis.get("rating", "neutral")
        pattern = flow_analysis.get("pattern", "neutral")
        strength = flow_analysis.get("strength", 50.0)
        net_inflow = flow_analysis.get("net_inflow", 0.0)

        # 转换为万元
        net_inflow_wan = net_inflow / 10000

        conclusion = f"资金流向分析显示："

        if rating == "accumulation":
            conclusion += f"资金呈吸筹状态（{pattern}），"
            conclusion += f"主力净流入{net_inflow_wan:.2f}万元，"
            conclusion += f"资金强度{strength:.1f}分。"
        elif rating == "distribution":
            conclusion += f"资金呈派发状态（{pattern}），"
            conclusion += f"主力净流出{abs(net_inflow_wan):.2f}万元，"
            conclusion += f"资金强度{strength:.1f}分。"
        else:
            conclusion += f"资金流向中性，"
            conclusion += f"净流入{net_inflow_wan:.2f}万元，"
            conclusion += f"资金强度{strength:.1f}分。"

        return conclusion

    def _generate_recommendations(
        self,
        flow_analysis: Dict[str, Any]
    ) -> List[str]:
        """
        生成投资建议

        Args:
            flow_analysis: 资金流向分析

        Returns:
            建议列表
        """
        rating = flow_analysis.get("rating", "neutral")
        pattern = flow_analysis.get("pattern", "neutral")
        strength = flow_analysis.get("strength", 50.0)
        main_retail_relation = flow_analysis.get("main_retail_relation", "")

        recommendations = []

        if rating == "accumulation":
            if pattern == "strong_accumulation":
                recommendations.append("主力持续大举吸筹，强烈关注")
                if "主力吸筹，散户离场" in main_retail_relation:
                    recommendations.append("主力吸筹散户离场，是典型看多信号，可积极关注")
            else:
                recommendations.append("主力小幅吸筹，可以关注")
                recommendations.append("建议结合其他指标综合判断")

        elif rating == "distribution":
            if pattern == "strong_distribution":
                recommendations.append("主力持续大幅派发，建议规避")
                if "主力出货，散户接盘" in main_retail_relation:
                    recommendations.append("警惕主力出货散户接盘，风险较高")
            else:
                recommendations.append("主力小幅派发，谨慎观望")
                recommendations.append("建议等待资金流向改善")

        else:
            recommendations.append("资金流向中性，观望为主")
            recommendations.append("建议等待明确信号")

        # 根据资金强度补充建议
        if strength >= 70:
            recommendations.append("资金强度较高，市场关注度较高")
        elif strength <= 30:
            recommendations.append("资金强度较低，市场关注度较低")

        return recommendations

    def _identify_risks(self, flow_analysis: Dict[str, Any]) -> List[str]:
        """
        识别风险

        Args:
            flow_analysis: 资金流向分析

        Returns:
            风险列表
        """
        risks = []
        rating = flow_analysis.get("rating", "neutral")
        pattern = flow_analysis.get("pattern", "neutral")
        main_retail_relation = flow_analysis.get("main_retail_relation", "")

        if rating == "distribution":
            if pattern == "strong_distribution":
                risks.append("主力持续大幅派发，存在下跌风险")
            else:
                risks.append("主力小幅派发，可能面临调整压力")

        if "主力出货，散户接盘" in main_retail_relation:
            risks.append("警惕主力出货散户接盘的风险")

        if rating == "neutral":
            risks.append("资金方向不明，存在不确定性")

        return risks

    def _calculate_confidence(self, flow_analysis: Dict[str, Any]) -> float:
        """
        计算置信度

        Args:
            flow_analysis: 资金流向分析

        Returns:
            置信度（0-1）
        """
        pattern = flow_analysis.get("pattern", "neutral")
        strength = flow_analysis.get("strength", 50.0)

        # 根据模式和强度计算置信度
        if pattern in ["strong_accumulation", "strong_distribution"]:
            base_confidence = 0.85
        elif pattern in ["mild_accumulation", "mild_distribution"]:
            base_confidence = 0.70
        else:
            base_confidence = 0.50

        # 根据强度调整
        strength_bonus = (strength - 50) / 200  # -0.25 to +0.25

        confidence = base_confidence + strength_bonus

        # 限制在0-1范围
        return max(0.0, min(1.0, confidence))


# 便捷函数
async def analyze_capital_flow(
    stock_code: str,
    market: str = "sh",
    days: int = 5
) -> CapitalFlowData:
    """
    分析资金流向（便捷函数）

    Args:
        stock_code: 股票代码
        market: 市场
        days: 天数

    Returns:
        CapitalFlowData: 资金流向数据
    """
    agent = CapitalFlowAI()
    result = await agent.analyze(stock_code, market, days)

    # 提取详细信息
    details = result.details.get("capital_flow_data", {})

    return CapitalFlowData(
        stock_code=stock_code,
        timestamp=details.get("timestamp", datetime.now().isoformat()),
        net_inflow=details.get("net_inflow", 0.0),
        main_net_inflow=details.get("main_net_inflow", 0.0),
        super_large_net=details.get("super_large_net", 0.0),
        large_net=details.get("large_net", 0.0),
        medium_net=details.get("medium_net", 0.0),
        small_net=details.get("small_net", 0.0),
        rating=details.get("rating", "neutral"),
        analysis_period=f"{days}天",
        details=details
    )


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test():
        print("=" * 70)
        print("资金流向AI测试")
        print("=" * 70)

        agent = CapitalFlowAI()

        # 测试分析
        result = await agent.analyze(
            stock_code="600519",
            market="sh",
            days=5
        )

        print("\n分析结果:")
        print(f"Agent: {result.agent_name}")
        print(f"结论: {result.conclusion}")
        print(f"置信度: {result.confidence:.2f}")
        print(f"\n建议:")
        for rec in result.recommendations:
            print(f"  - {rec}")
        print(f"\n风险:")
        for risk in result.risks:
            print(f"  - {risk}")

        # 测试便捷函数
        print("\n" + "=" * 70)
        print("测试便捷函数")
        print("=" * 70)

        capital_data = await analyze_capital_flow("600519", "sh", 5)

        print(f"\n股票代码: {capital_data.stock_code}")
        print(f"净流入: {capital_data.net_inflow:.2f} 元")
        print(f"主力净流入: {capital_data.main_net_inflow:.2f} 元")
        print(f"超大单净流入: {capital_data.super_large_net:.2f} 元")
        print(f"大单净流入: {capital_data.large_net:.2f} 元")
        print(f"中单净流入: {capital_data.medium_net:.2f} 元")
        print(f"小单净流入: {capital_data.small_net:.2f} 元")
        print(f"评级: {capital_data.rating}")

        print("\n" + "=" * 70)
        print("测试完成")
        print("=" * 70)

    asyncio.run(test())
