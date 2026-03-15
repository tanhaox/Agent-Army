"""
策略优化AI测试 - Strategy Optimization AI Tests
"""

import pytest
import asyncio
from datetime import datetime
from src.agents.business.validation.strategy_optimization_ai import StrategyOptimizationAI


class TestStrategyOptimizationAI:
    """策略优化AI测试类"""

    @pytest.fixture
    def optimization_ai(self):
        """创建优化AI实例"""
        return StrategyOptimizationAI()

    @pytest.fixture
    def sample_strategy_params(self):
        """示例策略参数"""
        return {
            "ma_short": 5,
            "ma_long": 20,
            "stop_loss": 0.05,
            "take_profit": 0.15,
            "position_size": 0.3
        }

    @pytest.fixture
    def sample_param_grid(self):
        """示例参数网格"""
        return {
            "ma_short": [3, 5, 7, 10],
            "ma_long": [15, 20, 25, 30],
            "stop_loss": [0.03, 0.05, 0.07],
            "take_profit": [0.10, 0.15, 0.20]
        }

    @pytest.fixture
    def sample_param_space(self):
        """示例参数空间"""
        return {
            "ma_short": {
                "type": "discrete",
                "range": [3, 15],
                "step": 1
            },
            "ma_long": {
                "type": "discrete",
                "range": [15, 35],
                "step": 1
            },
            "stop_loss": {
                "type": "continuous",
                "range": [0.02, 0.10]
            },
            "take_profit": {
                "type": "continuous",
                "range": [0.10, 0.25]
            }
        }

    @pytest.fixture
    def sample_strategies(self):
        """示例策略组合"""
        return [
            {"name": "trend_following", "params": {"ma_short": 5, "ma_long": 20}, "weight": 0.4},
            {"name": "mean_reversion", "params": {"threshold": 2.0}, "weight": 0.3},
            {"name": "momentum", "params": {"lookback": 10}, "weight": 0.3}
        ]

    # ========== 基础测试 ==========

    def test_initialization(self, optimization_ai):
        """测试初始化"""
        assert optimization_ai.name == "策略优化AI"
        assert optimization_ai.default_objective == "sharpe_ratio"
        assert "grid_search" in optimization_ai.optimization_methods
        assert "bayesian" in optimization_ai.optimization_methods
        assert "genetic" in optimization_ai.optimization_methods

    def test_capabilities(self, optimization_ai):
        """测试能力定义"""
        capabilities = optimization_ai.capabilities
        capability_names = [cap.name for cap in capabilities]

        assert "parameter_optimization" in capability_names
        assert "grid_search" in capability_names
        assert "bayesian_optimization" in capability_names
        assert "genetic_algorithm" in capability_names
        assert "portfolio_optimization" in capability_names

    # ========== 策略优化测试 ==========

    @pytest.mark.asyncio
    async def test_optimize_strategy_grid_search(
        self,
        optimization_ai,
        sample_strategy_params
    ):
        """测试网格搜索优化"""
        result = await optimization_ai.optimize_strategy(
            strategy_name="test_strategy",
            original_params=sample_strategy_params,
            optimization_method="grid_search",
            objective="sharpe_ratio"
        )

        # 验证返回结构
        assert "strategy_name" in result
        assert "optimization_method" in result
        assert "original_params" in result
        assert "optimized_params" in result
        assert "improvements" in result
        assert "backtest_comparison" in result
        assert "recommendations" in result
        assert "confidence" in result

        # 验证基本值
        assert result["strategy_name"] == "test_strategy"
        assert result["optimization_method"] == "grid_search"
        assert isinstance(result["confidence"], float)
        assert 0 <= result["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_optimize_strategy_bayesian(
        self,
        optimization_ai,
        sample_strategy_params
    ):
        """测试贝叶斯优化"""
        result = await optimization_ai.optimize_strategy(
            strategy_name="test_strategy",
            original_params=sample_strategy_params,
            optimization_method="bayesian",
            objective="sharpe_ratio"
        )

        assert result["optimization_method"] == "bayesian"
        assert "optimized_params" in result
        assert len(result["optimized_params"]) > 0

    @pytest.mark.asyncio
    async def test_optimize_strategy_genetic(
        self,
        optimization_ai,
        sample_strategy_params
    ):
        """测试遗传算法优化"""
        result = await optimization_ai.optimize_strategy(
            strategy_name="test_strategy",
            original_params=sample_strategy_params,
            optimization_method="genetic",
            objective="sharpe_ratio"
        )

        assert result["optimization_method"] == "genetic"
        assert "optimized_params" in result
        assert "optimization_details" in result

    @pytest.mark.asyncio
    async def test_optimize_strategy_random_search(
        self,
        optimization_ai,
        sample_strategy_params
    ):
        """测试随机搜索优化"""
        result = await optimization_ai.optimize_strategy(
            strategy_name="test_strategy",
            original_params=sample_strategy_params,
            optimization_method="random_search",
            objective="total_return"
        )

        assert result["optimization_method"] == "random_search"
        assert result["objective"] == "total_return"

    # ========== 优化方法测试 ==========

    @pytest.mark.asyncio
    async def test_grid_search(
        self,
        optimization_ai,
        sample_param_grid
    ):
        """测试网格搜索"""
        result = await optimization_ai.grid_search(
            strategy_name="test_strategy",
            param_grid=sample_param_grid
        )

        assert result is not None
        assert result.params is not None
        assert isinstance(result.objective_value, float)
        assert result.metrics is not None

        # 验证参数在网格范围内
        assert result.params["ma_short"] in sample_param_grid["ma_short"]
        assert result.params["ma_long"] in sample_param_grid["ma_long"]
        assert result.params["stop_loss"] in sample_param_grid["stop_loss"]

    @pytest.mark.asyncio
    async def test_bayesian_optimization(
        self,
        optimization_ai,
        sample_param_space
    ):
        """测试贝叶斯优化"""
        result = await optimization_ai.bayesian_optimization(
            strategy_name="test_strategy",
            param_space=sample_param_space
        )

        assert result is not None
        assert result.params is not None
        assert isinstance(result.objective_value, float)

        # 验证参数在范围内
        assert 3 <= result.params["ma_short"] <= 15
        assert 15 <= result.params["ma_long"] <= 35
        assert 0.02 <= result.params["stop_loss"] <= 0.10

    @pytest.mark.asyncio
    async def test_genetic_algorithm(
        self,
        optimization_ai,
        sample_param_space
    ):
        """测试遗传算法"""
        result = await optimization_ai.genetic_algorithm(
            strategy_name="test_strategy",
            param_space=sample_param_space
        )

        assert result is not None
        assert result.params is not None
        assert isinstance(result.objective_value, float)

        # 验证参数在范围内
        assert 3 <= result.params["ma_short"] <= 15
        assert 15 <= result.params["ma_long"] <= 35

    # ========== 组合优化测试 ==========

    @pytest.mark.asyncio
    async def test_optimize_portfolio(
        self,
        optimization_ai,
        sample_strategies
    ):
        """测试策略组合优化"""
        result = await optimization_ai.optimize_portfolio(sample_strategies)

        # 验证返回结构
        assert "strategies" in result
        assert "optimal_weights" in result
        assert "portfolio_metrics" in result
        assert "recommendations" in result
        assert "summary" in result

        # 验证权重
        weights = result["optimal_weights"]
        assert len(weights) == len(sample_strategies)
        assert all(isinstance(w, float) for w in weights.values())

        # 验证权重和为1
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.01

        # 验证指标
        metrics = result["portfolio_metrics"]
        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics

    # ========== 参数空间定义测试 ==========

    def test_define_param_space(self, optimization_ai, sample_strategy_params):
        """测试参数空间定义"""
        param_space = optimization_ai._define_param_space(
            "test_strategy",
            sample_strategy_params
        )

        assert isinstance(param_space, dict)
        assert len(param_space) > 0

        # 验证参数类型
        for param_name, space in param_space.items():
            assert "type" in space
            assert "range" in space

            if space["type"] == "discrete":
                assert isinstance(space["range"], list)
                assert len(space["range"]) == 2
            elif space["type"] == "continuous":
                assert isinstance(space["range"], list)
                assert len(space["range"]) == 2

    # ========== 参数采样测试 ==========

    def test_sample_params_discrete(self, optimization_ai):
        """测试离散参数采样"""
        param_space = {
            "ma_short": {
                "type": "discrete",
                "range": [3, 10],
                "step": 1
            }
        }

        params = optimization_ai._sample_params(param_space)

        assert "ma_short" in params
        assert 3 <= params["ma_short"] <= 10
        assert isinstance(params["ma_short"], int)

    def test_sample_params_continuous(self, optimization_ai):
        """测试连续参数采样"""
        param_space = {
            "stop_loss": {
                "type": "continuous",
                "range": [0.02, 0.10]
            }
        }

        params = optimization_ai._sample_params(param_space)

        assert "stop_loss" in params
        assert 0.02 <= params["stop_loss"] <= 0.10
        assert isinstance(params["stop_loss"], float)

    def test_sample_params_categorical(self, optimization_ai):
        """测试分类参数采样"""
        param_space = {
            "strategy_type": {
                "type": "categorical",
                "values": ["trend", "mean_reversion", "momentum"]
            }
        }

        params = optimization_ai._sample_params(param_space)

        assert "strategy_type" in params
        assert params["strategy_type"] in ["trend", "mean_reversion", "momentum"]

    # ========== 建议生成测试 ==========

    def test_generate_recommendations(
        self,
        optimization_ai,
        sample_strategy_params
    ):
        """测试优化建议生成"""
        optimized_params = sample_strategy_params.copy()
        optimized_params["ma_short"] = 7
        optimized_params["stop_loss"] = 0.03

        comparison = {
            "return_improvement": 5.5,
            "risk_reduction": 3.2,
            "sharpe_improvement": 0.45
        }

        recommendations = optimization_ai._generate_recommendations(
            sample_strategy_params,
            optimized_params,
            comparison
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # 验证建议结构
        for rec in recommendations:
            assert "param" in rec
            assert "current_value" in rec
            assert "suggested_value" in rec
            assert "reason" in rec
            assert "expected_impact" in rec

    # ========== 置信度计算测试 ==========

    def test_calculate_confidence_high(self, optimization_ai):
        """测试高置信度计算"""
        optimization_result = type('obj', (object,), {
            'objective_value': 1.8
        })

        comparison = {
            "return_improvement": 12.5,
            "risk_reduction": 6.3,
            "sharpe_improvement": 0.75
        }

        confidence = optimization_ai._calculate_confidence(
            optimization_result,
            comparison
        )

        assert confidence > 0.7
        assert confidence <= 1.0

    def test_calculate_confidence_medium(self, optimization_ai):
        """测试中等置信度计算"""
        optimization_result = type('obj', (object,), {
            'objective_value': 1.2
        })

        comparison = {
            "return_improvement": 6.5,
            "risk_reduction": 3.2,
            "sharpe_improvement": 0.35
        }

        confidence = optimization_ai._calculate_confidence(
            optimization_result,
            comparison
        )

        assert 0.4 <= confidence <= 0.8

    def test_calculate_confidence_low(self, optimization_ai):
        """测试低置信度计算"""
        optimization_result = type('obj', (object,), {
            'objective_value': 0.8
        })

        comparison = {
            "return_improvement": 2.5,
            "risk_reduction": 1.2,
            "sharpe_improvement": 0.15
        }

        confidence = optimization_ai._calculate_confidence(
            optimization_result,
            comparison
        )

        assert confidence < 0.6

    # ========== 网格大小计算测试 ==========

    def test_calculate_grid_size(self, optimization_ai, sample_param_grid):
        """测试网格大小计算"""
        size = optimization_ai._calculate_grid_size(sample_param_grid)

        expected_size = (
            len(sample_param_grid["ma_short"]) *
            len(sample_param_grid["ma_long"]) *
            len(sample_param_grid["stop_loss"]) *
            len(sample_param_grid["take_profit"])
        )

        assert size == expected_size

    # ========== 摘要生成测试 ==========

    def test_generate_optimization_summary(self, optimization_ai):
        """测试优化摘要生成"""
        comparison = {
            "return_improvement": 8.5,
            "sharpe_improvement": 0.55
        }

        recommendations = [
            {"param": "ma_short", "expected_impact": "显著提升"},
            {"param": "stop_loss", "expected_impact": "中等提升"}
        ]

        summary = optimization_ai._generate_optimization_summary(
            comparison,
            recommendations,
            0.75
        )

        assert isinstance(summary, str)
        assert "收益提升" in summary or "夏普比率" in summary
        assert "置信度" in summary

    # ========== 边界条件测试 ==========

    @pytest.mark.asyncio
    async def test_empty_params(self, optimization_ai):
        """测试空参数"""
        result = await optimization_ai.optimize_strategy(
            strategy_name="test_strategy",
            original_params={},
            optimization_method="random_search"
        )

        assert result is not None
        assert result["original_params"] == {}

    @pytest.mark.asyncio
    async def test_single_param(self, optimization_ai):
        """测试单一参数"""
        result = await optimization_ai.optimize_strategy(
            strategy_name="test_strategy",
            original_params={"ma_short": 5},
            optimization_method="random_search"
        )

        assert result is not None
        assert "ma_short" in result["optimized_params"]

    @pytest.mark.asyncio
    async def test_large_param_grid(self, optimization_ai):
        """测试大参数网格"""
        large_grid = {
            "param1": list(range(1, 11)),
            "param2": list(range(1, 11)),
            "param3": [0.1 * i for i in range(1, 11)]
        }

        # 使用随机搜索避免组合爆炸
        result = await optimization_ai.optimize_strategy(
            strategy_name="test_strategy",
            original_params={"param1": 5, "param2": 5, "param3": 0.5},
            optimization_method="random_search"
        )

        assert result is not None

    # ========== 遗传算法组件测试 ==========

    def test_selection(self, optimization_ai):
        """测试选择操作"""
        population = [
            {"param1": 1, "param2": 2},
            {"param1": 3, "param2": 4},
            {"param1": 5, "param2": 6}
        ]
        fitness_scores = [0.5, 0.8, 0.6]

        selected = optimization_ai._selection(population, fitness_scores, 2)

        assert len(selected) == 2
        assert all(isinstance(ind, dict) for ind in selected)

    def test_crossover(self, optimization_ai, sample_param_space):
        """测试交叉操作"""
        population = [
            {"ma_short": 5, "stop_loss": 0.05},
            {"ma_short": 7, "stop_loss": 0.03},
            {"ma_short": 9, "stop_loss": 0.07}
        ]

        offspring = optimization_ai._crossover(population, 0.7, sample_param_space)

        assert len(offspring) == len(population)
        assert all(isinstance(ind, dict) for ind in offspring)

    def test_mutation(self, optimization_ai, sample_param_space):
        """测试变异操作"""
        population = [
            {"ma_short": 5, "stop_loss": 0.05},
            {"ma_short": 7, "stop_loss": 0.03}
        ]

        mutated = optimization_ai._mutation(population, 0.1, sample_param_space)

        assert len(mutated) == len(population)
        assert all(isinstance(ind, dict) for ind in mutated)

    # ========== 组合优化组件测试 ==========

    @pytest.mark.asyncio
    async def test_optimize_weights_equal(self, optimization_ai, sample_strategies):
        """测试等权重优化"""
        weights = await optimization_ai._optimize_weights(sample_strategies)

        assert len(weights) == len(sample_strategies)
        assert all(abs(w - 1.0/len(sample_strategies)) < 0.01 for w in weights.values())

    @pytest.mark.asyncio
    async def test_calculate_portfolio_metrics(self, optimization_ai):
        """测试组合指标计算"""
        strategies = [
            {"name": "strategy1", "params": {}},
            {"name": "strategy2", "params": {}}
        ]
        weights = {"strategy1": 0.5, "strategy2": 0.5}

        metrics = await optimization_ai._calculate_portfolio_metrics(strategies, weights)

        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert all(isinstance(v, (int, float)) for v in metrics.values())

    def test_generate_portfolio_recommendations(self, optimization_ai):
        """测试组合建议生成"""
        strategies = [
            {"name": "strategy1", "params": {}},
            {"name": "strategy2", "params": {}}
        ]
        weights = {"strategy1": 0.6, "strategy2": 0.4}
        metrics = {
            "sharpe_ratio": 1.8,
            "max_drawdown": 12.5,
            "diversification_ratio": 1.6
        }

        recommendations = optimization_ai._generate_portfolio_recommendations(
            strategies,
            weights,
            metrics
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)

    # ========== 集成测试 ==========

    @pytest.mark.asyncio
    async def test_full_optimization_workflow(
        self,
        optimization_ai,
        sample_strategy_params
    ):
        """测试完整优化工作流"""
        # 1. 执行优化
        result = await optimization_ai.optimize_strategy(
            strategy_name="test_strategy",
            original_params=sample_strategy_params,
            optimization_method="random_search",
            objective="sharpe_ratio"
        )

        # 2. 验证结果完整性
        assert result["strategy_name"] == "test_strategy"
        assert "optimized_params" in result
        assert "improvements" in result
        assert "recommendations" in result

        # 3. 验证改进指标
        improvements = result["improvements"]
        assert "return_improvement" in improvements
        assert "risk_reduction" in improvements
        assert "sharpe_improvement" in improvements

        # 4. 验证建议质量
        recommendations = result["recommendations"]
        assert len(recommendations) > 0

        for rec in recommendations:
            assert "param" in rec
            assert "current_value" in rec
            assert "suggested_value" in rec
            assert "reason" in rec
            assert rec["current_value"] != rec["suggested_value"]

    # ========== 错误处理测试 ==========

    @pytest.mark.asyncio
    async def test_invalid_optimization_method(self, optimization_ai):
        """测试无效优化方法"""
        with pytest.raises(Exception):
            await optimization_ai.optimize_strategy(
                strategy_name="test_strategy",
                original_params={"param": 5},
                optimization_method="invalid_method"
            )

    @pytest.mark.asyncio
    async def test_invalid_objective(self, optimization_ai):
        """测试无效优化目标"""
        # 应该使用默认目标
        result = await optimization_ai.optimize_strategy(
            strategy_name="test_strategy",
            original_params={"param": 5},
            optimization_method="random_search",
            objective="invalid_objective"
        )

        assert result is not None
