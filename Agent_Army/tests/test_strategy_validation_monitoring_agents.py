"""
策略部、验证部、监控部Agent综合单元测试

测试覆盖：
1. 策略部（4个Agent）
2. 验证部（2个Agent）
3. 监控部（2个Agent）
"""

import pytest
from datetime import datetime

# 策略部导入
from src.agents.business.strategy import (
    TimingJudgmentAI,
    PositionManagementAI,
    RiskControlAI,
    StrategyEvaluationAI
)

# 验证部导入
from src.agents.business.validation import (
    ValidationBacktestAI,
    AttributionOptionAI
)

# 监控部导入
from src.agents.business.monitoring import (
    InformationMonitoringAI,
    CapitalMonitoringAI
)


# ========== 策略部测试 ==========

class TestTimingJudgmentAI:
    """时机判断AI测试类"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        return TimingJudgmentAI()

    @pytest.mark.asyncio
    async def test_analyze_basic(self, agent):
        """测试基本分析功能"""
        result = await agent.analyze(
            stock_code="600519",
            current_price=50.0
        )

        # 验证返回结构
        assert result.agent_name == "时机判断AI"
        assert result.analysis_type == "timing_judgment"
        assert result.confidence > 0
        assert len(result.details) > 0

        # 验证核心字段
        assert "buy_timing" in result.details
        assert "sell_timing" in result.details
        assert "timing_score" in result.details
        assert "action_suggestion" in result.details

    @pytest.mark.asyncio
    async def test_buy_timing_analysis(self, agent):
        """测试买入时机分析"""
        result = await agent.analyze(
            stock_code="600519",
            current_price=50.0
        )

        buy_timing = result.details["buy_timing"]
        assert "signal" in buy_timing
        assert "strength" in buy_timing
        assert "confidence" in buy_timing
        assert "entry_points" in buy_timing

    @pytest.mark.asyncio
    async def test_with_position(self, agent):
        """测试有持仓的情况"""
        result = await agent.analyze(
            stock_code="600519",
            current_price=50.0,
            position_cost=45.0
        )

        sell_timing = result.details["sell_timing"]
        assert "take_profit" in sell_timing
        assert "stop_loss" in sell_timing


class TestPositionManagementAI:
    """仓位管理AI测试类"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        return PositionManagementAI()

    @pytest.mark.asyncio
    async def test_analyze_basic(self, agent):
        """测试基本分析功能"""
        result = await agent.analyze(
            stock_code="600519",
            current_price=50.0,
            total_capital=100000,
            risk_tolerance=3
        )

        # 验证返回结构
        assert result.agent_name == "仓位管理AI"
        assert result.analysis_type == "position_management"
        assert result.confidence > 0

        # 验证核心字段
        assert "position_size" in result.details
        assert "allocation_strategy" in result.details

    @pytest.mark.asyncio
    async def test_different_risk_tolerance(self, agent):
        """测试不同风险偏好"""
        for risk_level in [1, 3, 5]:
            result = await agent.analyze(
                stock_code="600519",
                current_price=50.0,
                total_capital=100000,
                risk_tolerance=risk_level
            )

            assert result.details["risk_assessment"]["risk_level"] == risk_level


class TestRiskControlAI:
    """风控AI测试类"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        return RiskControlAI()

    @pytest.mark.asyncio
    async def test_analyze_basic(self, agent):
        """测试基本分析功能"""
        result = await agent.analyze(
            stock_code="600519",
            current_price=50.0
        )

        # 验证返回结构
        assert result.agent_name == "风控AI"
        assert result.analysis_type == "risk_control"
        assert result.confidence > 0

        # 验证核心字段
        assert "risk_assessment" in result.details
        assert "stop_loss_strategy" in result.details
        assert "risk_control_plan" in result.details

    @pytest.mark.asyncio
    async def test_stop_loss_calculation(self, agent):
        """测试止损计算"""
        result = await agent.analyze(
            stock_code="600519",
            current_price=50.0,
            intended_buy_price=50.0
        )

        stop_loss = result.details["stop_loss_strategy"]
        assert "stop_loss_price" in stop_loss
        assert stop_loss["stop_loss_price"] < 50.0


class TestStrategyEvaluationAI:
    """策略评估AI测试类"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        return StrategyEvaluationAI()

    @pytest.mark.asyncio
    async def test_analyze_basic(self, agent):
        """测试基本分析功能"""
        result = await agent.analyze(
            stock_code="600519",
            current_price=50.0,
            investment_horizon="中期"
        )

        # 验证返回结构
        assert result.agent_name == "策略评估AI"
        assert result.analysis_type == "strategy_evaluation"
        assert result.confidence > 0

        # 验证核心字段
        assert "scenario_analysis" in result.details
        assert "timing_assessment" in result.details
        assert "performance_prediction" in result.details

    @pytest.mark.asyncio
    async def test_scenario_analysis(self, agent):
        """测试情景分析"""
        result = await agent.analyze(
            stock_code="600519",
            current_price=50.0
        )

        scenario_analysis = result.details["scenario_analysis"]
        assert "scenarios" in scenario_analysis
        assert "current_scenario" in scenario_analysis


# ========== 验证部测试 ==========

class TestValidationBacktestAI:
    """验证回测AI测试类"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        return ValidationBacktestAI()

    @pytest.mark.asyncio
    async def test_analyze_basic(self, agent):
        """测试基本分析功能"""
        # 模拟预测和实际数据
        predictions = [
            {"date": "2025-01-01", "predicted": 52.0},
            {"date": "2025-01-02", "predicted": 53.0}
        ]
        actual_prices = [
            {"date": "2025-01-01", "actual": 51.5},
            {"date": "2025-01-02", "actual": 52.8}
        ]

        result = await agent.analyze(
            stock_code="600519",
            predictions=predictions,
            actual_prices=actual_prices
        )

        # 验证返回结构
        assert result.agent_name == "验证回测AI"
        assert result.analysis_type == "validation_backtest"
        assert result.confidence > 0

        # 验证核心字段
        assert "validation_metrics" in result.details
        assert "backtest_results" in result.details


class TestAttributionOptionAI:
    """归因期权AI测试类"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        return AttributionOptionAI()

    @pytest.mark.asyncio
    async def test_analyze_basic(self, agent):
        """测试基本分析功能"""
        result = await agent.analyze(
            stock_code="600519",
            current_price=50.0
        )

        # 验证返回结构
        assert result.agent_name == "归因期权AI"
        assert result.analysis_type == "attribution_option"
        assert result.confidence > 0

        # 验证核心字段
        assert "return_attribution" in result.details
        assert "option_analysis" in result.details

    @pytest.mark.asyncio
    async def test_option_pricing(self, agent):
        """测试期权定价"""
        result = await agent.analyze(
            stock_code="600519",
            current_price=50.0,
            strike_price=55.0,
            time_to_maturity=0.25
        )

        option_analysis = result.details["option_analysis"]
        assert "option_price" in option_analysis
        assert "greeks" in option_analysis


# ========== 监控部测试 ==========

class TestInformationMonitoringAI:
    """信息监控AI测试类"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        return InformationMonitoringAI()

    @pytest.mark.asyncio
    async def test_analyze_basic(self, agent):
        """测试基本分析功能"""
        result = await agent.analyze(
            stock_code="600519",
            days=7
        )

        # 验证返回结构
        assert result.agent_name == "信息监控AI"
        assert result.analysis_type == "information_monitoring"
        assert result.confidence > 0

        # 验证核心字段
        assert "news_events" in result.details
        assert "sentiment_analysis" in result.details

    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, agent):
        """测试情绪分析"""
        result = await agent.analyze(
            stock_code="600519",
            days=7
        )

        sentiment = result.details["sentiment_analysis"]
        assert "overall_sentiment" in sentiment
        assert "sentiment_trend" in sentiment


class TestCapitalMonitoringAI:
    """资金监控AI测试类"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        return CapitalMonitoringAI()

    @pytest.mark.asyncio
    async def test_analyze_basic(self, agent):
        """测试基本分析功能"""
        result = await agent.analyze(
            stock_code="600519",
            days=5
        )

        # 验证返回结构
        assert result.agent_name == "资金监控AI"
        assert result.analysis_type == "capital_monitoring"
        assert result.confidence > 0

        # 验证核心字段
        assert "capital_flow" in result.details
        assert "dragon_tiger" in result.details

    @pytest.mark.asyncio
    async def test_capital_flow_trend(self, agent):
        """测试资金流向趋势"""
        result = await agent.analyze(
            stock_code="600519",
            days=5
        )

        capital_flow = result.details["capital_flow"]
        assert "net_flow" in capital_flow
        assert "trend" in capital_flow


# ========== 运行测试 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
