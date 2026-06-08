"""
预测部Agent单元测试

测试覆盖：
1. 估值定价AI
2. 综合评估AI
3. 预测AI
"""

import pytest
import asyncio
from src.agents.business.prediction import (
    ValuationPricingAI,
    ComprehensiveEvaluationAI,
    PriceForecastAI,
    analyze_valuation_pricing,
    analyze_comprehensive_evaluation,
    analyze_price_forecast
)


# ========== 估值定价AI测试 ==========

class TestValuationPricingAI:
    """估值定价AI测试类"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        return ValuationPricingAI()

    @pytest.mark.asyncio
    async def test_analyze_basic(self, agent):
        """测试基本分析功能"""
        result = await agent.analyze(
            stock_code="600519",
            current_price=50.0
        )

        # 验证返回结构
        assert result.agent_name == "估值定价AI"
        assert result.analysis_type == "valuation_pricing"
        assert result.confidence > 0
        assert len(result.details) > 0

        # 验证核心字段
        assert "valuation_models" in result.details
        assert "target_pricing" in result.details
        assert "valuation_advice" in result.details

        # 验证估值模型
        valuation_models = result.details["valuation_models"]
        assert "pe" in valuation_models
        assert "pb" in valuation_models
        assert "dcf" in valuation_models
        assert "peg" in valuation_models

        # 验证目标定价
        target_pricing = result.details["target_pricing"]
        assert "target_price" in target_pricing
        assert "upside" in target_pricing
        assert "confidence" in target_pricing
        assert "price_range" in target_pricing

    @pytest.mark.asyncio
    async def test_invalid_stock_code(self, agent):
        """测试无效股票代码"""
        with pytest.raises(ValueError, match="无效的股票代码"):
            await agent.analyze(
                stock_code="invalid",
                current_price=50.0
            )

    @pytest.mark.asyncio
    async def test_missing_current_price(self, agent):
        """测试缺少当前价格"""
        with pytest.raises(ValueError, match="缺少current_price参数"):
            await agent.analyze(stock_code="600519")

    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """测试便捷函数"""
        result = await analyze_valuation_pricing(
            stock_code="600519",
            current_price=50.0,
            prediction_period="6m"
        )

        assert result.analysis_type == "valuation_pricing"


# ========== 综合评估AI测试 ==========

class TestComprehensiveEvaluationAI:
    """综合评估AI测试类"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        return ComprehensiveEvaluationAI()

    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return {
            "research_data": {"industry": "白酒"},
            "analysis_data": {"fundamental": "good"},
            "prediction_data": {"target_price": 60.0}
        }

    @pytest.mark.asyncio
    async def test_analyze_basic(self, agent, sample_data):
        """测试基本分析功能"""
        result = await agent.analyze(
            stock_code="600519",
            **sample_data
        )

        # 验证返回结构
        assert result.agent_name == "综合评估AI"
        assert result.analysis_type == "comprehensive_evaluation"
        assert result.confidence > 0
        assert len(result.details) > 0

        # 验证核心字段
        assert "dimension_scores" in result.details
        assert "comprehensive_score" in result.details
        assert "quality_assessment" in result.details
        assert "investment_rating" in result.details

        # 验证维度评分
        dimension_scores = result.details["dimension_scores"]
        assert "fundamental" in dimension_scores
        assert "growth" in dimension_scores
        assert "valuation" in dimension_scores
        assert "technical" in dimension_scores
        assert "sentiment" in dimension_scores

        # 验证综合评分范围
        comprehensive_score = result.details["comprehensive_score"]
        assert 0 <= comprehensive_score <= 100

    @pytest.mark.asyncio
    async def test_investment_rating(self, agent, sample_data):
        """测试投资评级"""
        result = await agent.analyze(
            stock_code="600519",
            **sample_data
        )

        investment_rating = result.details["investment_rating"]

        # 验证评级字段
        assert "rating" in investment_rating
        assert "action" in investment_rating
        assert "risk_level" in investment_rating

        # 验证评级值
        assert investment_rating["rating"] in [
            "强烈推荐", "推荐", "中性", "谨慎", "不推荐"
        ]

    @pytest.mark.asyncio
    async def test_convenience_function(self, sample_data):
        """测试便捷函数"""
        result = await analyze_comprehensive_evaluation(
            stock_code="600519",
            **sample_data
        )

        assert result.analysis_type == "comprehensive_evaluation"


# ========== 预测AI测试 ==========

class TestPriceForecastAI:
    """预测AI测试类"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        return PriceForecastAI()

    @pytest.mark.asyncio
    async def test_analyze_basic(self, agent):
        """测试基本分析功能"""
        result = await agent.analyze(
            stock_code="600519",
            current_price=50.0,
            forecast_period="12m"
        )

        # 验证返回结构
        assert result.agent_name == "预测AI"
        assert result.analysis_type == "price_forecast"
        assert result.confidence > 0
        assert len(result.details) > 0

        # 验证核心字段
        assert "price_forecast" in result.details
        assert "profit_forecast" in result.details
        assert "trend_forecast" in result.details
        assert "scenario_analysis" in result.details

        # 验证价格预测
        price_forecast = result.details["price_forecast"]
        assert "forecast_price" in price_forecast
        assert "upside" in price_forecast
        assert "trend" in price_forecast
        assert "confidence" in price_forecast

        # 验证利润预测
        profit_forecast = result.details["profit_forecast"]
        assert "forecast_profit" in profit_forecast
        assert "profit_growth" in profit_forecast
        assert "forecast_eps" in profit_forecast

    @pytest.mark.asyncio
    async def test_different_forecast_periods(self, agent):
        """测试不同预测周期"""
        periods = ["3m", "6m", "12m"]

        for period in periods:
            result = await agent.analyze(
                stock_code="600519",
                current_price=50.0,
                forecast_period=period
            )

            assert result.details["forecast_period"] == period
            assert result.details["price_forecast"]["forecast_period"] == period

    @pytest.mark.asyncio
    async def test_scenario_analysis(self, agent):
        """测试情景分析"""
        result = await agent.analyze(
            stock_code="600519",
            current_price=50.0
        )

        scenario_analysis = result.details["scenario_analysis"]

        # 验证三种情景
        assert "optimistic" in scenario_analysis
        assert "neutral" in scenario_analysis
        assert "pessimistic" in scenario_analysis
        assert "expected_value" in scenario_analysis

        # 验证情景概率
        assert scenario_analysis["optimistic"]["probability"] == 0.30
        assert scenario_analysis["neutral"]["probability"] == 0.50
        assert scenario_analysis["pessimistic"]["probability"] == 0.20

    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """测试便捷函数"""
        result = await analyze_price_forecast(
            stock_code="600519",
            current_price=50.0,
            forecast_period="6m"
        )

        assert result.analysis_type == "price_forecast"


# ========== 运行测试 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
