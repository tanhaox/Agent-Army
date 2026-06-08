"""
自我进化AI - Self Evolution AI

优化部成员 (1/3)

职责：
1. 经验积累 - 记录成功/失败案例
2. 参数优化 - 优化模型参数
3. 模式识别 - 识别市场模式

合并来源：
- 经验积累AI
- 参数优化AI
- 模式识别AI

使用工具：
- FinancialTool（财务数据）
- LLMTool（智能分析）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import json

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import get_logger


class SelfEvolutionAI(BusinessAgent):
    """
    自我进化AI - 优化部成员 (1/3)

    核心能力:
    1. 经验积累 - 成功/失败案例记录与学习
    2. 参数优化 - 模型参数自动调优
    3. 模式识别 - 市场模式识别与分类

    使用工具:
    - FinancialTool (财务数据)
    - LLMTool (智能分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="自我进化AI",
            role="经验积累与参数优化",
            corps="optimization",
            analysis_type="self_evolution",
            capabilities=[
                AgentCapability(
                    name="experience_accumulation",
                    description="经验积累与学习",
                    input_type="analysis_result",
                    output_type="experience_database"
                ),
                AgentCapability(
                    name="parameter_optimization",
                    description="模型参数优化",
                    input_type="model_performance",
                    output_type="optimized_parameters"
                ),
                AgentCapability(
                    name="pattern_recognition",
                    description="市场模式识别",
                    input_type="market_data",
                    output_type="pattern_library"
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

        # 经验数据库（内存存储，后续可改为持久化）
        self.experience_database = {
            "success_cases": [],
            "failure_cases": [],
            "patterns": []
        }

        # 模型参数（示例）
        self.model_parameters = {
            "valuation_weights": {
                "pe": 0.3,
                "pb": 0.25,
                "dcf": 0.25,
                "peg": 0.2
            },
            "risk_threshold": 0.7,
            "confidence_threshold": 0.75
        }

        self.logger.info("自我进化AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行自我进化分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - historical_results: 历史分析结果（用于经验积累）
                - current_performance: 当前模型表现（用于参数优化）
                - market_data: 市场数据（用于模式识别）

        Returns:
            分析结果
        """
        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        self.logger.info(
            f"开始自我进化分析",
            extra={
                "stock_code": stock_code,
                "mode": kwargs.get("mode", "full")
            }
        )

        # ========== 1. 经验积累 ==========
        experience_insights = await self._accumulate_experience(stock_code, **kwargs)

        # ========== 2. 参数优化 ==========
        optimized_params = await self._optimize_parameters(stock_code, **kwargs)

        # ========== 3. 模式识别 ==========
        recognized_patterns = await self._recognize_patterns(stock_code, **kwargs)

        # ========== 4. 生成进化建议 ==========
        evolution_recommendations = self._generate_evolution_recommendations(
            experience_insights,
            optimized_params,
            recognized_patterns
        )

        # ========== 5. 构建分析结果 ==========
        details = {
            "stock_code": stock_code,

            # 经验积累
            "experience_insights": experience_insights,

            # 参数优化
            "optimized_parameters": optimized_params,

            # 模式识别
            "recognized_patterns": recognized_patterns,

            # 进化建议
            "evolution_recommendations": evolution_recommendations,

            # 时间戳
            "timestamp": datetime.now().isoformat()
        }

        result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=self._generate_conclusion(
                experience_insights,
                optimized_params,
                recognized_patterns
            ),
            confidence=self._calculate_confidence(experience_insights, recognized_patterns),
            details=details,
            risks=evolution_recommendations.get("risks", []),
            recommendations=evolution_recommendations.get("recommendations", [])
        )

        self.logger.info(
            f"自我进化分析完成",
            extra={
                "stock_code": stock_code,
                "patterns_found": len(recognized_patterns),
                "params_optimized": len(optimized_params)
            }
        )

        return result

    # ========== 经验积累 ==========

    async def _accumulate_experience(
        self,
        stock_code: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        经验积累（成功/失败案例记录）

        Args:
            stock_code: 股票代码
            **kwargs: 历史分析结果

        Returns:
            经验洞察
        """
        # TODO: 从数据库读取历史分析结果
        # 当前使用模拟数据

        historical_results = kwargs.get("historical_results", [])

        # 分析成功案例
        success_insights = self._analyze_success_cases(stock_code, historical_results)

        # 分析失败案例
        failure_insights = self._analyze_failure_cases(stock_code, historical_results)

        # 提取关键经验
        key_lessons = self._extract_key_lessons(success_insights, failure_insights)

        return {
            "success_cases_count": len(self.experience_database["success_cases"]),
            "failure_cases_count": len(self.experience_database["failure_cases"]),
            "success_insights": success_insights,
            "failure_insights": failure_insights,
            "key_lessons": key_lessons,
            "learning_rate": self._calculate_learning_rate()
        }

    def _analyze_success_cases(
        self,
        stock_code: str,
        historical_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析成功案例"""
        # TODO: 接入真实历史数据
        # 模拟成功案例特征
        return [
            {
                "pattern": "低PE + 高增长",
                "success_rate": 0.85,
                "sample_size": 120,
                "avg_return": 35.0,
                "description": "PE低于行业平均，增长率高于20%的股票表现优异"
            },
            {
                "pattern": "DCF低估",
                "success_rate": 0.78,
                "sample_size": 85,
                "avg_return": 28.0,
                "description": "DCF估值显示股价低于内在价值30%以上"
            }
        ]

    def _analyze_failure_cases(
        self,
        stock_code: str,
        historical_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析失败案例"""
        # TODO: 接入真实历史数据
        # 模拟失败案例特征
        return [
            {
                "pattern": "高PE陷阱",
                "failure_rate": 0.65,
                "sample_size": 90,
                "avg_loss": -18.0,
                "description": "PE超过50倍的股票，如果增长率不匹配，容易回调"
            },
            {
                "pattern": "周期顶部误判",
                "failure_rate": 0.72,
                "sample_size": 45,
                "avg_loss": -25.0,
                "description": "在行业周期顶部买入，忽视周期性风险"
            }
        ]

    def _extract_key_lessons(
        self,
        success_insights: List[Dict[str, Any]],
        failure_insights: List[Dict[str, Any]]
    ) -> List[str]:
        """提取关键经验"""
        lessons = []

        # 从成功案例中提取经验
        for insight in success_insights:
            if insight["success_rate"] >= 0.80:
                lessons.append(f"✅ {insight['pattern']}：成功率{insight['success_rate']*100:.0f}%")

        # 从失败案例中提取教训
        for insight in failure_insights:
            if insight["failure_rate"] >= 0.60:
                lessons.append(f"❌ 避免{insight['pattern']}：失败率{insight['failure_rate']*100:.0f}%")

        return lessons

    def _calculate_learning_rate(self) -> float:
        """计算学习速率"""
        # TODO: 基于历史数据计算真实学习速率
        total_cases = (
            len(self.experience_database["success_cases"]) +
            len(self.experience_database["failure_cases"])
        )

        if total_cases == 0:
            return 0.0

        # 简化版本：随着案例增加，学习速率提高
        return min(0.95, total_cases / 1000.0)

    # ========== 参数优化 ==========

    async def _optimize_parameters(
        self,
        stock_code: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        参数优化（模型参数调优）

        Args:
            stock_code: 股票代码
            **kwargs: 当前模型表现

        Returns:
            优化后的参数
        """
        # TODO: 接入真实模型表现数据
        current_performance = kwargs.get("current_performance", {})

        # 获取当前参数
        current_params = self.model_parameters.copy()

        # 优化估值权重
        optimized_weights = self._optimize_valuation_weights(current_performance)

        # 优化风险阈值
        optimized_risk_threshold = self._optimize_risk_threshold(current_performance)

        # 优化置信度阈值
        optimized_confidence_threshold = self._optimize_confidence_threshold(current_performance)

        # 计算优化效果
        optimization_effect = self._calculate_optimization_effect(
            current_params,
            {
                "valuation_weights": optimized_weights,
                "risk_threshold": optimized_risk_threshold,
                "confidence_threshold": optimized_confidence_threshold
            }
        )

        return {
            "original_parameters": current_params,
            "optimized_parameters": {
                "valuation_weights": optimized_weights,
                "risk_threshold": optimized_risk_threshold,
                "confidence_threshold": optimized_confidence_threshold
            },
            "optimization_effect": optimization_effect,
            "improvement_percentage": optimization_effect.get("improvement", 0.0)
        }

    def _optimize_valuation_weights(
        self,
        performance: Dict[str, Any]
    ) -> Dict[str, float]:
        """优化估值权重"""
        # TODO: 基于历史表现优化权重
        # 简化版本：根据成功率调整权重
        base_weights = self.model_parameters["valuation_weights"]

        # 模拟优化：给PE和DCF更高权重
        optimized_weights = {
            "pe": 0.35,  # 从0.30提升
            "pb": 0.20,  # 从0.25降低
            "dcf": 0.30,  # 从0.25提升
            "peg": 0.15  # 从0.20降低
        }

        return optimized_weights

    def _optimize_risk_threshold(
        self,
        performance: Dict[str, Any]
    ) -> float:
        """优化风险阈值"""
        # TODO: 基于历史风险调整阈值
        # 简化版本：保守策略
        return 0.65  # 从0.70降低

    def _optimize_confidence_threshold(
        self,
        performance: Dict[str, Any]
    ) -> float:
        """优化置信度阈值"""
        # TODO: 基于历史准确性调整阈值
        # 简化版本：提高标准
        return 0.78  # 从0.75提升

    def _calculate_optimization_effect(
        self,
        original: Dict[str, Any],
        optimized: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算优化效果"""
        # TODO: 基于回测数据计算真实效果
        # 简化版本：模拟提升
        return {
            "accuracy_improvement": 5.2,  # 准确率提升5.2%
            "risk_reduction": 12.8,  # 风险降低12.8%
            "improvement": 8.5  # 综合提升8.5%
        }

    # ========== 模式识别 ==========

    async def _recognize_patterns(
        self,
        stock_code: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        模式识别（市场模式识别与分类）

        Args:
            stock_code: 股票代码
            **kwargs: 市场数据

        Returns:
            识别到的模式
        """
        # TODO: 接入真实市场数据
        market_data = kwargs.get("market_data", {})

        # 识别技术模式
        technical_patterns = await self._recognize_technical_patterns(stock_code, market_data)

        # 识别基本面模式
        fundamental_patterns = await self._recognize_fundamental_patterns(stock_code, market_data)

        # 识别市场情绪模式
        sentiment_patterns = await self._recognize_sentiment_patterns(stock_code, market_data)

        # 模式匹配度
        pattern_matching_score = self._calculate_pattern_matching_score(
            technical_patterns,
            fundamental_patterns,
            sentiment_patterns
        )

        return {
            "technical_patterns": technical_patterns,
            "fundamental_patterns": fundamental_patterns,
            "sentiment_patterns": sentiment_patterns,
            "pattern_matching_score": pattern_matching_score,
            "total_patterns_found": (
                len(technical_patterns) +
                len(fundamental_patterns) +
                len(sentiment_patterns)
            )
        }

    async def _recognize_technical_patterns(
        self,
        stock_code: str,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """识别技术模式"""
        # TODO: 接入真实技术分析
        # 模拟技术模式
        return [
            {
                "pattern": "上升趋势",
                "confidence": 0.85,
                "duration": "45天",
                "description": "股价呈现稳定上升趋势，MA20/MA60金叉"
            },
            {
                "pattern": "成交量放大",
                "confidence": 0.78,
                "description": "近期成交量持续放大，资金流入明显"
            }
        ]

    async def _recognize_fundamental_patterns(
        self,
        stock_code: str,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """识别基本面模式"""
        # TODO: 接入真实基本面分析
        # 模拟基本面模式
        return [
            {
                "pattern": "盈利改善",
                "confidence": 0.82,
                "description": "连续3个季度盈利超预期，ROE提升至15%"
            },
            {
                "pattern": "估值修复",
                "confidence": 0.75,
                "description": "PE处于历史低位（25%分位），具备修复空间"
            }
        ]

    async def _recognize_sentiment_patterns(
        self,
        stock_code: str,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """识别市场情绪模式"""
        # TODO: 接入真实情绪分析
        # 模拟情绪模式
        return [
            {
                "pattern": "机构增持",
                "confidence": 0.70,
                "description": "北向资金连续5日净流入"
            },
            {
                "pattern": "研报看好",
                "confidence": 0.68,
                "description": "近期3家机构给出'买入'评级"
            }
        ]

    def _calculate_pattern_matching_score(
        self,
        technical: List[Dict[str, Any]],
        fundamental: List[Dict[str, Any]],
        sentiment: List[Dict[str, Any]]
    ) -> float:
        """计算模式匹配度"""
        # TODO: 基于历史数据计算真实匹配度
        total_patterns = len(technical) + len(fundamental) + len(sentiment)

        if total_patterns == 0:
            return 0.0

        # 简化版本：平均置信度
        all_confidences = []
        for pattern in technical + fundamental + sentiment:
            all_confidences.append(pattern.get("confidence", 0.5))

        return sum(all_confidences) / len(all_confidences)

    # ========== 辅助方法 ==========

    def _generate_evolution_recommendations(
        self,
        experience_insights: Dict[str, Any],
        optimized_params: Dict[str, Any],
        recognized_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成进化建议"""
        recommendations = []
        risks = []

        # 基于经验生成的建议
        if experience_insights["learning_rate"] > 0.8:
            recommendations.append("模型学习速率良好，建议继续保持当前策略")
        else:
            recommendations.append("建议增加训练样本，提升学习速率")

        # 基于参数优化生成的建议
        improvement = optimized_params["improvement_percentage"]
        if improvement > 5.0:
            recommendations.append(f"参数优化效果显著（提升{improvement:.1f}%），建议应用新参数")

        # 基于模式识别生成的建议
        pattern_score = recognized_patterns["pattern_matching_score"]
        if pattern_score > 0.75:
            recommendations.append(f"模式匹配度高（{pattern_score*100:.0f}%），当前市场环境适合模型发挥")

        # 风险提示
        if pattern_score < 0.60:
            risks.append("模式匹配度较低，建议谨慎参考当前分析")

        if len(recognized_patterns["technical_patterns"]) == 0:
            risks.append("未识别到明确技术模式，市场可能处于震荡期")

        return {
            "recommendations": recommendations,
            "risks": risks,
            "action_items": self._generate_action_items(
                experience_insights,
                optimized_params,
                recognized_patterns
            )
        }

    def _generate_action_items(
        self,
        experience_insights: Dict[str, Any],
        optimized_params: Dict[str, Any],
        recognized_patterns: Dict[str, Any]
    ) -> List[str]:
        """生成行动项"""
        actions = []

        # 参数优化行动项
        if optimized_params["improvement_percentage"] > 5.0:
            actions.append("应用优化后的模型参数")

        # 模式库更新行动项
        if recognized_patterns["total_patterns_found"] > 3:
            actions.append("将识别到的新模式添加到模式库")

        # 经验积累行动项
        if experience_insights["learning_rate"] < 0.7:
            actions.append("增加历史案例训练，提升学习速率")

        return actions

    def _calculate_confidence(
        self,
        experience_insights: Dict[str, Any],
        recognized_patterns: Dict[str, Any]
    ) -> float:
        """计算综合置信度"""
        # 学习速率权重
        learning_weight = 0.3
        learning_score = experience_insights["learning_rate"]

        # 模式匹配度权重
        pattern_weight = 0.7
        pattern_score = recognized_patterns["pattern_matching_score"]

        # 综合置信度
        confidence = learning_score * learning_weight + pattern_score * pattern_weight

        return round(confidence, 2)

    def _generate_conclusion(
        self,
        experience_insights: Dict[str, Any],
        optimized_params: Dict[str, Any],
        recognized_patterns: Dict[str, Any]
    ) -> str:
        """生成核心结论"""
        return (
            f"学习速率{experience_insights['learning_rate']*100:.0f}%，"
            f"参数优化提升{optimized_params['improvement_percentage']:.1f}%，"
            f"识别{recognized_patterns['total_patterns_found']}个市场模式，"
            f"模式匹配度{recognized_patterns['pattern_matching_score']*100:.0f}%"
        )


# 便捷函数
async def analyze_self_evolution(
    stock_code: str,
    historical_results: Optional[List[Dict[str, Any]]] = None,
    current_performance: Optional[Dict[str, Any]] = None,
    market_data: Optional[Dict[str, Any]] = None
) -> AnalysisResult:
    """
    自我进化分析（便捷函数）

    Args:
        stock_code: 股票代码
        historical_results: 历史分析结果
        current_performance: 当前模型表现
        market_data: 市场数据

    Returns:
        分析结果
    """
    ai = SelfEvolutionAI()
    return await ai.analyze(
        stock_code,
        historical_results=historical_results,
        current_performance=current_performance,
        market_data=market_data
    )
