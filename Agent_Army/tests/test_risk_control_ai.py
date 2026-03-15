"""
风险控制AI测试 - Risk Control AI Tests
测试风险控制AI的各项功能
"""

import pytest
import asyncio
from datetime import datetime
from src.agents.business.strategy.risk_control_ai import (
    RiskControlAI,
    RiskAssessment,
    RiskIndicators,
    RiskLimits,
    RiskControlResult
)


class TestRiskControlAI:
    """风险控制AI测试类"""

    @pytest.fixture
    def risk_ai(self):
        """创建RiskControlAI实例"""
        return RiskControlAI()

    @pytest.fixture
    def sample_price_data(self):
        """示例价格数据"""
        return [
            100.0, 102.5, 101.3, 103.8, 105.2,
            104.1, 106.5, 107.8, 106.2, 108.5,
            109.3, 107.5, 108.8, 110.2, 109.5,
            111.3, 112.5, 111.8, 113.2, 114.5
        ]

    @pytest.fixture
    def sample_market_data(self):
        """示例市场数据"""
        return [
            3000.0, 3020.0, 3010.0, 3030.0, 3045.0,
            3035.0, 3050.0, 3060.0, 3055.0, 3070.0,
            3080.0, 3070.0, 3085.0, 3095.0, 3090.0,
            3100.0, 3110.0, 3105.0, 3120.0, 3130.0
        ]

    @pytest.fixture
    def sample_portfolio_data(self):
        """示例组合数据"""
        return {
            "concentration": 0.25,  # 单股占比25%
            "liquidity_ratio": 0.75,  # 流动性比率75%
            "industry_concentration": 0.45  # 行业集中度45%
        }

    # ========== 基础功能测试 ==========

    def test_initialization(self, risk_ai):
        """测试初始化"""
        assert risk_ai.name == "风险控制AI"
        assert risk_ai.role == "风险控制专家"
        assert risk_ai.corps == "战略军团"
        assert risk_ai.analysis_type == "风险控制"
        assert risk_ai.risk_free_rate == 0.03
        assert risk_ai.confidence_level == 0.95

    def test_validate_stock_code_valid(self, risk_ai):
        """测试有效股票代码验证"""
        assert risk_ai.validate_stock_code("600519") is True
        assert risk_ai.validate_stock_code("000858") is True
        assert risk_ai.validate_stock_code("300001") is True

    def test_validate_stock_code_invalid(self, risk_ai):
        """测试无效股票代码验证"""
        assert risk_ai.validate_stock_code("12345") is False
        assert risk_ai.validate_stock_code("abcdef") is False
        assert risk_ai.validate_stock_code("6005190") is False

    # ========== 风险评估测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_with_valid_data(self, risk_ai, sample_price_data, sample_market_data, sample_portfolio_data):
        """测试完整分析功能"""
        result = await risk_ai.analyze(
            stock_code="600519",
            price_data=sample_price_data,
            market_data=sample_market_data,
            portfolio_data=sample_portfolio_data,
            current_position=0.15
        )

        # 验证基本结构
        assert result.agent_name == "风险控制AI"
        assert result.analysis_type == "风险控制"
        assert result.confidence > 0

        # 验证详细数据
        assert "stock_code" in result.details
        assert "risk_assessment" in result.details
        assert "risk_indicators" in result.details
        assert "risk_limits" in result.details
        assert "suggestions" in result.details

    @pytest.mark.asyncio
    async def test_analyze_with_invalid_stock_code(self, risk_ai):
        """测试无效股票代码"""
        result = await risk_ai.analyze(
            stock_code="12345",
            price_data=[100.0, 101.0]
        )

        assert "无效的股票代码" in result.conclusion
        assert result.confidence == 0.0
        assert len(result.risks) > 0

    @pytest.mark.asyncio
    async def test_risk_assessment_with_price_data(self, risk_ai, sample_price_data):
        """测试基于价格数据的风险评估"""
        risk_assessment = await risk_ai._assess_risk(
            price_data=sample_price_data,
            portfolio_data={}
        )

        assert isinstance(risk_assessment, RiskAssessment)
        assert 0 <= risk_assessment.risk_score <= 100
        assert 1 <= risk_assessment.risk_level <= 5
        assert risk_assessment.overall_risk in ["低", "中低", "中", "中高", "高"]

    @pytest.mark.asyncio
    async def test_risk_assessment_with_portfolio_data(self, risk_ai, sample_portfolio_data):
        """测试基于组合数据的风险评估"""
        risk_assessment = await risk_ai._assess_risk(
            price_data=[],
            portfolio_data=sample_portfolio_data
        )

        assert isinstance(risk_assessment, RiskAssessment)
        assert 0 <= risk_assessment.risk_score <= 100

    @pytest.mark.asyncio
    async def test_risk_assessment_high_concentration(self, risk_ai):
        """测试高集中度风险评估"""
        portfolio_data = {
            "concentration": 0.35,  # 高集中度
            "liquidity_ratio": 0.8,
            "industry_concentration": 0.75
        }

        risk_assessment = await risk_ai._assess_risk(
            price_data=[],
            portfolio_data=portfolio_data
        )

        # 高集中度应该导致较高的风险等级
        assert risk_assessment.risk_level >= 3

    @pytest.mark.asyncio
    async def test_risk_assessment_low_liquidity(self, risk_ai):
        """测试低流动性风险评估"""
        portfolio_data = {
            "concentration": 0.2,
            "liquidity_ratio": 0.25,  # 低流动性
            "industry_concentration": 0.5
        }

        risk_assessment = await risk_ai._assess_risk(
            price_data=[],
            portfolio_data=portfolio_data
        )

        # 低流动性应该增加风险评分
        assert risk_assessment.risk_score > 0

    # ========== 风险指标计算测试 ==========

    @pytest.mark.asyncio
    async def test_calculate_indicators_with_price_data(self, risk_ai, sample_price_data):
        """测试风险指标计算"""
        indicators = await risk_ai._calculate_indicators(
            price_data=sample_price_data,
            market_data=[]
        )

        assert isinstance(indicators, RiskIndicators)
        # 应该能计算出波动率、VaR、最大回撤
        assert indicators.volatility is not None
        assert indicators.var_95 is not None
        assert indicators.max_drawdown is not None

    @pytest.mark.asyncio
    async def test_calculate_indicators_with_market_data(self, risk_ai, sample_price_data, sample_market_data):
        """测试包含市场数据的指标计算"""
        indicators = await risk_ai._calculate_indicators(
            price_data=sample_price_data,
            market_data=sample_market_data
        )

        # 应该能计算出Beta
        assert indicators.beta is not None

    @pytest.mark.asyncio
    async def test_calculate_indicators_insufficient_data(self, risk_ai):
        """测试数据不足的情况"""
        indicators = await risk_ai._calculate_indicators(
            price_data=[100.0],
            market_data=[]
        )

        # 数据不足时，指标应该为None
        assert indicators.volatility is None
        assert indicators.var_95 is None

    def test_calculate_returns(self, risk_ai, sample_price_data):
        """测试收益率计算"""
        returns = risk_ai._calculate_returns(sample_price_data)

        assert len(returns) == len(sample_price_data) - 1
        assert all(isinstance(r, float) for r in returns)

    def test_calculate_returns_empty_data(self, risk_ai):
        """测试空数据的收益率计算"""
        returns = risk_ai._calculate_returns([])
        assert returns == []

    def test_calculate_returns_single_price(self, risk_ai):
        """测试单个价格点的收益率计算"""
        returns = risk_ai._calculate_returns([100.0])
        assert returns == []

    def test_calculate_max_drawdown(self, risk_ai):
        """测试最大回撤计算"""
        import numpy as np
        prices = np.array([100.0, 110.0, 105.0, 95.0, 100.0])
        max_dd = risk_ai._calculate_max_drawdown(prices)

        # 最大回撤应该是从110降到95，约13.6%
        assert max_dd > 0
        assert max_dd < 0.2

    # ========== 风险限额测试 ==========

    @pytest.mark.asyncio
    async def test_set_risk_limits_high_risk(self, risk_ai):
        """测试高风险限额设置"""
        risk_assessment = RiskAssessment(
            overall_risk="高",
            risk_score=75.0,
            risk_level=5
        )

        limits = await risk_ai._set_risk_limits(
            risk_assessment=risk_assessment,
            current_position=0.3
        )

        assert limits.single_stock_max == 0.05  # 5%
        assert limits.single_industry_max == 0.15  # 15%
        assert limits.total_max_position == 0.40  # 40%
        assert limits.cash_min_ratio == 0.30  # 30%

    @pytest.mark.asyncio
    async def test_set_risk_limits_low_risk(self, risk_ai):
        """测试低风险限额设置"""
        risk_assessment = RiskAssessment(
            overall_risk="低",
            risk_score=10.0,
            risk_level=1
        )

        limits = await risk_ai._set_risk_limits(
            risk_assessment=risk_assessment,
            current_position=0.1
        )

        assert limits.single_stock_max == 0.15  # 15%
        assert limits.single_industry_max == 0.35  # 35%
        assert limits.total_max_position == 0.80  # 80%
        assert limits.cash_min_ratio == 0.10  # 10%

    @pytest.mark.asyncio
    async def test_set_risk_limits_medium_risk(self, risk_ai):
        """测试中等风险限额设置"""
        risk_assessment = RiskAssessment(
            overall_risk="中",
            risk_score=40.0,
            risk_level=3
        )

        limits = await risk_ai._set_risk_limits(
            risk_assessment=risk_assessment,
            current_position=0.2
        )

        assert limits.single_stock_max == 0.10  # 10%
        assert limits.single_industry_max == 0.25  # 25%
        assert limits.total_max_position == 0.60  # 60%
        assert limits.cash_min_ratio == 0.20  # 20%

    # ========== 风险建议测试 ==========

    @pytest.mark.asyncio
    async def test_generate_suggestions_high_risk(self, risk_ai):
        """测试高风险建议生成"""
        risk_assessment = RiskAssessment(
            overall_risk="高",
            risk_score=75.0,
            risk_level=5
        )

        risk_indicators = RiskIndicators(
            var_95=-0.35,
            max_drawdown=0.25,
            volatility=0.45,
            beta=1.6,
            sharpe_ratio=0.4
        )

        risk_limits = RiskLimits(
            single_stock_max=0.05,
            single_industry_max=0.15,
            total_max_position=0.40,
            cash_min_ratio=0.30
        )

        suggestions = await risk_ai._generate_suggestions(
            risk_assessment=risk_assessment,
            risk_indicators=risk_indicators,
            risk_limits=risk_limits
        )

        assert len(suggestions) > 0
        assert any("降低仓位" in s for s in suggestions)
        assert any("止损" in s for s in suggestions)

    @pytest.mark.asyncio
    async def test_generate_suggestions_low_risk(self, risk_ai):
        """测试低风险建议生成"""
        risk_assessment = RiskAssessment(
            overall_risk="低",
            risk_score=10.0,
            risk_level=1
        )

        risk_indicators = RiskIndicators(
            var_95=-0.10,
            max_drawdown=0.08,
            volatility=0.15,
            beta=0.8,
            sharpe_ratio=1.8
        )

        risk_limits = RiskLimits(
            single_stock_max=0.15,
            single_industry_max=0.35,
            total_max_position=0.80,
            cash_min_ratio=0.10
        )

        suggestions = await risk_ai._generate_suggestions(
            risk_assessment=risk_assessment,
            risk_indicators=risk_indicators,
            risk_limits=risk_limits
        )

        assert len(suggestions) > 0
        assert any("夏普比率较高" in s for s in suggestions)

    @pytest.mark.asyncio
    async def test_generate_suggestions_high_volatility(self, risk_ai):
        """测试高波动率建议"""
        risk_indicators = RiskIndicators(
            volatility=0.50,  # 高波动率
            beta=1.2,
            sharpe_ratio=0.8
        )

        suggestions = await risk_ai._generate_suggestions(
            risk_assessment=RiskAssessment(overall_risk="中", risk_score=50.0, risk_level=3),
            risk_indicators=risk_indicators,
            risk_limits=RiskLimits(
                single_stock_max=0.10,
                single_industry_max=0.25,
                total_max_position=0.60,
                cash_min_ratio=0.20
            )
        )

        assert any("波动率较高" in s for s in suggestions)
        assert any("分批建仓" in s for s in suggestions)

    # ========== 综合功能测试 ==========

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, risk_ai, sample_price_data, sample_market_data, sample_portfolio_data):
        """测试完整分析流程"""
        result = await risk_ai.analyze(
            stock_code="600519",
            price_data=sample_price_data,
            market_data=sample_market_data,
            portfolio_data=sample_portfolio_data,
            current_position=0.15
        )

        # 验证返回结构
        assert result.agent_name == "风险控制AI"
        assert result.analysis_type == "风险控制"
        assert result.conclusion is not None
        assert result.confidence > 0
        assert len(result.details) > 0
        assert len(result.recommendations) > 0

        # 验证风险评估
        risk_assessment = result.details["risk_assessment"]
        assert "overall_risk" in risk_assessment
        assert "risk_score" in risk_assessment
        assert "risk_level" in risk_assessment

        # 验证风险指标
        risk_indicators = result.details["risk_indicators"]
        assert "volatility" in risk_indicators
        assert "var_95" in risk_indicators

        # 验证风险限额
        risk_limits = result.details["risk_limits"]
        assert "single_stock_max" in risk_limits
        assert "total_max_position" in risk_limits

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, risk_ai):
        """测试置信度计算"""
        # 创建完整的风险结果
        risk_result = RiskControlResult(
            stock_code="600519",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_assessment=RiskAssessment(
                overall_risk="中",
                risk_score=50.0,
                risk_level=3
            ),
            risk_indicators=RiskIndicators(
                volatility=0.25,
                var_95=-0.15,
                max_drawdown=0.12
            ),
            risk_limits=RiskLimits(
                single_stock_max=0.10,
                single_industry_max=0.25,
                total_max_position=0.60,
                cash_min_ratio=0.20
            )
        )

        confidence = risk_ai._calculate_confidence(risk_result)
        assert 0.3 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_confidence_calculation_missing_indicators(self, risk_ai):
        """测试缺失指标时的置信度计算"""
        # 创建不完整的风险结果
        risk_result = RiskControlResult(
            stock_code="600519",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_assessment=RiskAssessment(
                overall_risk="中",
                risk_score=50.0,
                risk_level=3
            ),
            risk_indicators=RiskIndicators(
                volatility=None,
                var_95=None,
                max_drawdown=None
            ),
            risk_limits=RiskLimits(
                single_stock_max=0.10,
                single_industry_max=0.25,
                total_max_position=0.60,
                cash_min_ratio=0.20
            )
        )

        confidence = risk_ai._calculate_confidence(risk_result)
        # 缺失关键指标应该降低置信度
        assert confidence < 0.8
        assert confidence >= 0.3

    # ========== 边界情况测试 ==========

    @pytest.mark.asyncio
    async def test_empty_price_data(self, risk_ai):
        """测试空价格数据"""
        result = await risk_ai.analyze(
            stock_code="600519",
            price_data=[],
            market_data=[],
            portfolio_data={}
        )

        # 应该能处理空数据，但不应该有具体指标
        assert result.details["risk_indicators"]["volatility"] is None
        assert result.details["risk_indicators"]["var_95"] is None

    @pytest.mark.asyncio
    async def test_single_price_point(self, risk_ai):
        """测试单个价格点"""
        result = await risk_ai.analyze(
            stock_code="600519",
            price_data=[100.0],
            market_data=[],
            portfolio_data={}
        )

        # 单个价格点无法计算指标
        assert result.details["risk_indicators"]["volatility"] is None

    @pytest.mark.asyncio
    async def test_extreme_volatility(self, risk_ai):
        """测试极端波动率"""
        extreme_prices = [
            100.0, 150.0, 80.0, 180.0, 70.0,
            200.0, 60.0, 220.0, 50.0, 250.0
        ]

        result = await risk_ai.analyze(
            stock_code="600519",
            price_data=extreme_prices,
            market_data=[],
            portfolio_data={}
        )

        # 极端波动应该导致高风险
        risk_level = result.details["risk_assessment"]["risk_level"]
        assert risk_level >= 4

    @pytest.mark.asyncio
    async def test_stable_prices(self, risk_ai):
        """测试稳定价格"""
        stable_prices = [100.0 + i * 0.1 for i in range(20)]  # 非常稳定的价格

        result = await risk_ai.analyze(
            stock_code="600519",
            price_data=stable_prices,
            market_data=[],
            portfolio_data={
                "concentration": 0.1,  # 低集中度
                "liquidity_ratio": 0.9,  # 高流动性
                "industry_concentration": 0.3  # 低行业集中度
            }
        )

        # 稳定价格+低集中度应该导致低到中等风险
        risk_level = result.details["risk_assessment"]["risk_level"]
        assert risk_level <= 3

    # ========== 错误处理测试 ==========

    @pytest.mark.asyncio
    async def test_handle_zero_prices(self, risk_ai):
        """测试处理零价格"""
        zero_prices = [100.0, 0.0, 105.0, 110.0]

        result = await risk_ai.analyze(
            stock_code="600519",
            price_data=zero_prices,
            market_data=[],
            portfolio_data={}
        )

        # 应该能处理零价格而不崩溃
        assert result is not None

    @pytest.mark.asyncio
    async def test_handle_negative_prices(self, risk_ai):
        """测试处理负价格"""
        negative_prices = [100.0, -50.0, 105.0, 110.0]

        result = await risk_ai.analyze(
            stock_code="600519",
            price_data=negative_prices,
            market_data=[],
            portfolio_data={}
        )

        # 应该能处理负价格而不崩溃
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src/agents/business/strategy/risk_control_ai", "--cov-report=html"])
