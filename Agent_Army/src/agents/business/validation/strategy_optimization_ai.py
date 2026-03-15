"""
策略优化AI - Strategy Optimization AI

职责：
- 基于回测结果优化策略参数
- 参数调优（网格搜索、贝叶斯优化、遗传算法）
- 策略组合优化
- 生成优化建议和改进方案

输入：
- 策略名称
- 初始参数
- 优化目标
- 优化方法

输出：
- 最优参数组合
- 改进建议
- 预期收益提升
- 优化置信度
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio
import itertools
import random
from dataclasses import dataclass

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin


@dataclass
class OptimizationResult:
    """优化结果"""
    params: Dict[str, Any]
    objective_value: float
    metrics: Dict[str, float]
    iterations: int = 0
    convergence: List[float] = None

    def __post_init__(self):
        if self.convergence is None:
            self.convergence = []

    def get(self, key: str, default=None):
        """提供字典式访问"""
        if key == "iterations":
            return self.iterations
        elif key == "convergence":
            return self.convergence
        return default


class StrategyOptimizationAI(BaseAgent, LoggerMixin):
    """策略优化AI - 优化策略参数和组合"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="策略优化AI",
            role="基于回测结果优化策略参数，提升策略表现",
            capabilities=[
                AgentCapability(
                    name="parameter_optimization",
                    description="参数优化",
                    input_type="strategy_params",
                    output_type="optimized_params"
                ),
                AgentCapability(
                    name="grid_search",
                    description="网格搜索",
                    input_type="param_grid",
                    output_type="best_params"
                ),
                AgentCapability(
                    name="bayesian_optimization",
                    description="贝叶斯优化",
                    input_type="param_space",
                    output_type="best_params"
                ),
                AgentCapability(
                    name="genetic_algorithm",
                    description="遗传算法",
                    input_type="param_space",
                    output_type="best_params"
                ),
                AgentCapability(
                    name="portfolio_optimization",
                    description="组合优化",
                    input_type="strategies",
                    output_type="optimal_allocation"
                )
            ],
            tools=[
                AgentTool(
                    name="optimization_engine",
                    description="优化引擎",
                    tool_type="system",
                    config={}
                )
            ],
            config=config
        )

        # 优化算法配置
        self.optimization_methods = {
            "grid_search": self._grid_search,
            "bayesian": self._bayesian_optimization,
            "genetic": self._genetic_algorithm,
            "random_search": self._random_search
        }

        # 默认优化目标
        self.default_objective = "sharpe_ratio"  # 可选: total_return, sharpe_ratio, max_drawdown

        self.logger.info("策略优化AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "optimize_strategy":
            return await self.optimize_strategy(
                kwargs.get("strategy_name"),
                kwargs.get("original_params"),
                kwargs.get("optimization_method", "grid_search"),
                kwargs.get("objective", self.default_objective)
            )
        elif task == "grid_search":
            return await self.grid_search(
                kwargs.get("strategy_name"),
                kwargs.get("param_grid")
            )
        elif task == "bayesian_optimization":
            return await self.bayesian_optimization(
                kwargs.get("strategy_name"),
                kwargs.get("param_space")
            )
        elif task == "genetic_algorithm":
            return await self.genetic_algorithm(
                kwargs.get("strategy_name"),
                kwargs.get("param_space")
            )
        elif task == "optimize_portfolio":
            return await self.optimize_portfolio(
                kwargs.get("strategies")
            )
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 核心功能 ==========

    async def optimize_strategy(
        self,
        strategy_name: str,
        original_params: Dict[str, Any],
        optimization_method: str = "grid_search",
        objective: str = "sharpe_ratio"
    ) -> Dict[str, Any]:
        """
        优化策略参数

        Args:
            strategy_name: 策略名称
            original_params: 原始参数
            optimization_method: 优化方法 (grid_search/bayesian/genetic/random_search)
            objective: 优化目标 (sharpe_ratio/total_return/max_drawdown)

        Returns:
            优化结果
        """
        self.logger.info(
            f"开始优化策略",
            extra={
                "strategy": strategy_name,
                "method": optimization_method,
                "objective": objective
            }
        )

        # 1. 定义参数搜索空间
        param_space = self._define_param_space(strategy_name, original_params)

        # 2. 选择优化方法
        optimizer = self.optimization_methods.get(optimization_method)

        if optimizer is None:
            raise ValueError(f"不支持的优化方法: {optimization_method}。支持的方法: {list(self.optimization_methods.keys())}")

        # 3. 执行优化
        optimization_result = await optimizer(
            strategy_name,
            param_space,
            objective
        )

        # 4. 对比原始参数和优化参数
        comparison = await self._compare_params(
            strategy_name,
            original_params,
            optimization_result.params
        )

        # 5. 生成优化建议
        recommendations = self._generate_recommendations(
            original_params,
            optimization_result.params,
            comparison
        )

        # 6. 计算置信度
        confidence = self._calculate_confidence(optimization_result, comparison)

        # 7. 组装结果
        result = {
            "strategy_name": strategy_name,
            "optimization_method": optimization_method,
            "objective": objective,
            "timestamp": datetime.now().isoformat(),
            "original_params": original_params,
            "optimized_params": optimization_result.params,
            "improvements": {
                "return_improvement": comparison.get("return_improvement", 0),
                "risk_reduction": comparison.get("risk_reduction", 0),
                "sharpe_improvement": comparison.get("sharpe_improvement", 0)
            },
            "backtest_comparison": {
                "original": comparison.get("original_metrics", {}),
                "optimized": comparison.get("optimized_metrics", {})
            },
            "recommendations": recommendations,
            "confidence": confidence,
            "optimization_details": {
                "total_iterations": getattr(optimization_result, 'iterations', 0),
                "objective_value": optimization_result.objective_value,
                "convergence": getattr(optimization_result, 'convergence', [])
            },
            "summary": self._generate_optimization_summary(
                comparison,
                recommendations,
                confidence
            )
        }

        self.logger.info(
            f"策略优化完成",
            extra={
                "strategy": strategy_name,
                "improvement": comparison.get("return_improvement", 0)
            }
        )

        return result

    async def grid_search(
        self,
        strategy_name: str,
        param_grid: Dict[str, List[Any]]
    ) -> Dict[str, Any]:
        """
        网格搜索优化

        Args:
            strategy_name: 策略名称
            param_grid: 参数网格

        Returns:
            最优参数
        """
        self.logger.info(
            f"开始网格搜索",
            extra={
                "strategy": strategy_name,
                "grid_size": self._calculate_grid_size(param_grid)
            }
        )

        # 生成所有参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        all_combinations = list(itertools.product(*param_values))

        best_result = None
        best_score = float("-inf")

        # 遍历所有组合
        for i, combination in enumerate(all_combinations):
            params = dict(zip(param_names, combination))

            # 评估参数
            score = await self._evaluate_params(
                strategy_name,
                params,
                "sharpe_ratio"
            )

            if score > best_score:
                best_score = score
                best_result = OptimizationResult(
                    params=params,
                    objective_value=score,
                    metrics=await self._get_metrics(strategy_name, params)
                )

            self.logger.debug(
                f"网格搜索进度",
                extra={
                    "progress": f"{i+1}/{len(all_combinations)}",
                    "best_score": best_score
                }
            )

        return best_result

    async def bayesian_optimization(
        self,
        strategy_name: str,
        param_space: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        贝叶斯优化

        Args:
            strategy_name: 策略名称
            param_space: 参数空间 {param_name: {"type": "continuous/discrete", "range": [min, max]}}

        Returns:
            最优参数
        """
        self.logger.info(
            f"开始贝叶斯优化",
            extra={"strategy": strategy_name}
        )

        # 简化的贝叶斯优化实现
        n_iterations = 50
        best_result = None
        best_score = float("-inf")

        # 初始随机采样
        for i in range(n_iterations):
            # 生成候选参数
            params = self._sample_params(param_space)

            # 评估参数
            score = await self._evaluate_params(
                strategy_name,
                params,
                "sharpe_ratio"
            )

            if score > best_score:
                best_score = score
                best_result = OptimizationResult(
                    params=params,
                    objective_value=score,
                    metrics=await self._get_metrics(strategy_name, params)
                )

        return best_result

    async def genetic_algorithm(
        self,
        strategy_name: str,
        param_space: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        遗传算法优化

        Args:
            strategy_name: 策略名称
            param_space: 参数空间

        Returns:
            最优参数
        """
        self.logger.info(
            f"开始遗传算法优化",
            extra={"strategy": strategy_name}
        )

        # 遗传算法参数
        population_size = 20
        n_generations = 10
        mutation_rate = 0.1
        crossover_rate = 0.7

        # 初始化种群
        population = [
            self._sample_params(param_space)
            for _ in range(population_size)
        ]

        best_result = None
        best_score = float("-inf")
        convergence = []

        # 进化循环
        for generation in range(n_generations):
            # 评估适应度
            fitness_scores = []
            for individual in population:
                score = await self._evaluate_params(
                    strategy_name,
                    individual,
                    "sharpe_ratio"
                )
                fitness_scores.append(score)

                if score > best_score:
                    best_score = score
                    best_result = OptimizationResult(
                        params=individual.copy(),
                        objective_value=score,
                        metrics=await self._get_metrics(strategy_name, individual),
                        iterations=generation + 1,
                        convergence=convergence.copy()
                    )

            convergence.append(best_score)

            # 选择
            selected = self._selection(population, fitness_scores, population_size // 2)

            # 交叉
            offspring = self._crossover(selected, crossover_rate, param_space)

            # 变异
            offspring = self._mutation(offspring, mutation_rate, param_space)

            # 更新种群
            population = selected + offspring

            self.logger.debug(
                f"遗传算法进化",
                extra={
                    "generation": generation + 1,
                    "best_score": best_score
                }
            )

        return best_result

    async def optimize_portfolio(
        self,
        strategies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        策略组合优化

        Args:
            strategies: 策略列表 [{"name": str, "params": dict, "weight": float}, ...]

        Returns:
            最优组合配置
        """
        self.logger.info(
            f"开始策略组合优化",
            extra={"strategy_count": len(strategies)}
        )

        # 计算最优权重分配
        optimal_weights = await self._optimize_weights(strategies)

        # 计算组合指标
        portfolio_metrics = await self._calculate_portfolio_metrics(
            strategies,
            optimal_weights
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "strategies": strategies,
            "optimal_weights": optimal_weights,
            "portfolio_metrics": portfolio_metrics,
            "recommendations": self._generate_portfolio_recommendations(
                strategies,
                optimal_weights,
                portfolio_metrics
            ),
            "summary": self._generate_portfolio_summary(portfolio_metrics)
        }

    # ========== 辅助方法 ==========

    def _define_param_space(
        self,
        strategy_name: str,
        original_params: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """定义参数搜索空间"""
        # 根据参数类型定义搜索空间
        param_space = {}

        for param_name, param_value in original_params.items():
            if isinstance(param_value, int):
                # 整数参数
                param_space[param_name] = {
                    "type": "discrete",
                    "range": [
                        max(1, param_value - 10),
                        param_value + 10
                    ],
                    "step": 1
                }
            elif isinstance(param_value, float):
                # 浮点数参数
                param_space[param_name] = {
                    "type": "continuous",
                    "range": [
                        max(0.01, param_value * 0.5),
                        param_value * 1.5
                    ]
                }
            elif isinstance(param_value, list):
                # 列表参数
                param_space[param_name] = {
                    "type": "categorical",
                    "values": param_value
                }

        return param_space

    async def _grid_search(
        self,
        strategy_name: str,
        param_space: Dict[str, Dict[str, Any]],
        objective: str
    ) -> OptimizationResult:
        """网格搜索实现"""
        # 转换为参数网格
        param_grid = {}
        for param_name, space in param_space.items():
            if space["type"] == "discrete":
                param_grid[param_name] = list(
                    range(space["range"][0], space["range"][1] + 1, space.get("step", 1))
                )
            elif space["type"] == "continuous":
                # 连续参数离散化
                param_grid[param_name] = [
                    space["range"][0] + i * (space["range"][1] - space["range"][0]) / 10
                    for i in range(11)
                ]
            elif space["type"] == "categorical":
                param_grid[param_name] = space["values"]

        # 执行网格搜索
        return await self.grid_search(strategy_name, param_grid)

    async def _bayesian_optimization(
        self,
        strategy_name: str,
        param_space: Dict[str, Dict[str, Any]],
        objective: str
    ) -> OptimizationResult:
        """贝叶斯优化实现"""
        return await self.bayesian_optimization(strategy_name, param_space)

    async def _genetic_algorithm(
        self,
        strategy_name: str,
        param_space: Dict[str, Dict[str, Any]],
        objective: str
    ) -> OptimizationResult:
        """遗传算法实现"""
        return await self.genetic_algorithm(strategy_name, param_space)

    async def _random_search(
        self,
        strategy_name: str,
        param_space: Dict[str, Dict[str, Any]],
        objective: str
    ) -> OptimizationResult:
        """随机搜索实现"""
        self.logger.info(f"开始随机搜索", extra={"strategy": strategy_name})

        n_iterations = 100
        best_result = None
        best_score = float("-inf")

        for i in range(n_iterations):
            params = self._sample_params(param_space)
            score = await self._evaluate_params(strategy_name, params, objective)

            if score > best_score:
                best_score = score
                best_result = OptimizationResult(
                    params=params,
                    objective_value=score,
                    metrics=await self._get_metrics(strategy_name, params)
                )

        return best_result

    def _sample_params(
        self,
        param_space: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """从参数空间采样"""
        params = {}

        for param_name, space in param_space.items():
            if space["type"] == "discrete":
                params[param_name] = random.randint(space["range"][0], space["range"][1])
            elif space["type"] == "continuous":
                params[param_name] = random.uniform(space["range"][0], space["range"][1])
            elif space["type"] == "categorical":
                params[param_name] = random.choice(space["values"])

        return params

    async def _evaluate_params(
        self,
        strategy_name: str,
        params: Dict[str, Any],
        objective: str
    ) -> float:
        """
        评估参数组合

        Args:
            strategy_name: 策略名称
            params: 参数组合
            objective: 优化目标

        Returns:
            目标函数值
        """
        # 模拟回测评估
        metrics = await self._get_metrics(strategy_name, params)

        # 根据目标返回对应的值
        if objective == "sharpe_ratio":
            return metrics.get("sharpe_ratio", 0)
        elif objective == "total_return":
            return metrics.get("total_return", 0)
        elif objective == "max_drawdown":
            # 最大回撤越小越好，取负值
            return -metrics.get("max_drawdown", 0)
        else:
            return metrics.get("sharpe_ratio", 0)

    async def _get_metrics(
        self,
        strategy_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, float]:
        """获取策略指标（模拟）"""
        # 这里应该是实际的回测调用
        # 为了演示，使用模拟数据

        # 基于参数生成模拟指标
        import random

        # 使用参数生成"确定性"的随机数
        param_seed = hash(str(sorted(params.items()))) % 10000
        random.seed(param_seed)

        return {
            "total_return": round(random.uniform(5, 30), 2),
            "sharpe_ratio": round(random.uniform(0.3, 2.5), 2),
            "max_drawdown": round(random.uniform(5, 25), 2),
            "volatility": round(random.uniform(10, 30), 2),
            "win_rate": round(random.uniform(40, 70), 2)
        }

    async def _compare_params(
        self,
        strategy_name: str,
        original_params: Dict[str, Any],
        optimized_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """对比原始参数和优化参数"""
        original_metrics = await self._get_metrics(strategy_name, original_params)
        optimized_metrics = await self._get_metrics(strategy_name, optimized_params)

        return {
            "original_metrics": original_metrics,
            "optimized_metrics": optimized_metrics,
            "return_improvement": round(
                optimized_metrics["total_return"] - original_metrics["total_return"],
                2
            ),
            "risk_reduction": round(
                original_metrics["max_drawdown"] - optimized_metrics["max_drawdown"],
                2
            ),
            "sharpe_improvement": round(
                optimized_metrics["sharpe_ratio"] - original_metrics["sharpe_ratio"],
                2
            )
        }

    def _generate_recommendations(
        self,
        original_params: Dict[str, Any],
        optimized_params: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recommendations = []

        for param_name in optimized_params:
            original_value = original_params.get(param_name)
            optimized_value = optimized_params[param_name]

            if original_value != optimized_value:
                # 计算变化幅度
                if isinstance(original_value, (int, float)):
                    change_pct = ((optimized_value - original_value) / original_value) * 100
                    change_str = f"{change_pct:+.1f}%"
                else:
                    change_str = f"{original_value} → {optimized_value}"

                # 获取预期影响和分数
                impact_text = self._get_param_impact(param_name, comparison)
                impact_score = self._get_impact_score(impact_text)

                recommendations.append({
                    "param": param_name,
                    "current_value": original_value,
                    "suggested_value": optimized_value,
                    "reason": self._get_param_change_reason(param_name, comparison),
                    "expected_impact": impact_text,
                    "impact_score": impact_score,
                    "change": change_str
                })

        # 按影响程度排序
        recommendations.sort(
            key=lambda x: x["impact_score"],
            reverse=True
        )

        return recommendations

    def _get_impact_score(self, impact_text: str) -> float:
        """将影响文本转换为分数"""
        impact_scores = {
            "显著提升": 0.9,
            "中等提升": 0.6,
            "小幅提升": 0.3,
            "影响较小": 0.1
        }
        return impact_scores.get(impact_text, 0.0)

    def _get_param_change_reason(
        self,
        param_name: str,
        comparison: Dict[str, Any]
    ) -> str:
        """获取参数调整原因"""
        reasons = {
            "stop_loss": "降低止损幅度可以减少无效止损",
            "take_profit": "提高止盈目标可以捕获更多趋势",
            "position_size": "调整仓位大小可以优化风险收益比",
            "ma_short": "缩短短期均线可以更快响应市场变化",
            "ma_long": "延长长期均线可以过滤更多噪音",
            "threshold": "调整阈值可以平衡信号频率和准确性"
        }

        return reasons.get(param_name, "优化算法建议调整此参数以提升策略表现")

    def _get_param_impact(
        self,
        param_name: str,
        comparison: Dict[str, Any]
    ) -> str:
        """获取参数预期影响"""
        # 根据对比结果估算影响
        sharpe_improvement = comparison.get("sharpe_improvement", 0)

        if sharpe_improvement > 0.5:
            return "显著提升"
        elif sharpe_improvement > 0.2:
            return "中等提升"
        elif sharpe_improvement > 0:
            return "小幅提升"
        else:
            return "影响较小"

    def _calculate_confidence(
        self,
        optimization_result: OptimizationResult,
        comparison: Dict[str, Any]
    ) -> float:
        """计算优化置信度"""
        # 基于多个因素计算置信度
        factors = []

        # 1. 收益提升
        return_improvement = comparison.get("return_improvement", 0)
        if return_improvement > 10:
            factors.append(0.9)
        elif return_improvement > 5:
            factors.append(0.7)
        else:
            factors.append(0.5)

        # 2. 夏普比率提升
        sharpe_improvement = comparison.get("sharpe_improvement", 0)
        if sharpe_improvement > 0.5:
            factors.append(0.8)
        elif sharpe_improvement > 0.2:
            factors.append(0.6)
        else:
            factors.append(0.4)

        # 3. 风险降低
        risk_reduction = comparison.get("risk_reduction", 0)
        if risk_reduction > 5:
            factors.append(0.8)
        elif risk_reduction > 2:
            factors.append(0.6)
        else:
            factors.append(0.4)

        # 综合置信度
        confidence = sum(factors) / len(factors)

        return round(confidence, 2)

    def _calculate_grid_size(self, param_grid: Dict[str, List[Any]]) -> int:
        """计算网格搜索的总组合数"""
        size = 1
        for values in param_grid.values():
            size *= len(values)
        return size

    # ========== 遗传算法辅助方法 ==========

    def _selection(
        self,
        population: List[Dict[str, Any]],
        fitness_scores: List[float],
        n_select: int
    ) -> List[Dict[str, Any]]:
        """选择操作（锦标赛选择）"""
        selected = []

        for _ in range(n_select):
            # 随机选择3个个体，取最优
            tournament_indices = random.sample(range(len(population)), 3)
            tournament_fitness = [fitness_scores[i] for i in tournament_indices]
            winner_idx = tournament_indices[tournament_fitness.index(max(tournament_fitness))]
            selected.append(population[winner_idx].copy())

        return selected

    def _crossover(
        self,
        population: List[Dict[str, Any]],
        crossover_rate: float,
        param_space: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """交叉操作"""
        offspring = []

        # 确保种群大小为偶数
        n_individuals = len(population)
        if n_individuals % 2 != 0:
            n_individuals -= 1

        for i in range(0, n_individuals, 2):
            parent1 = population[i]
            parent2 = population[i + 1]

            if random.random() < crossover_rate:
                # 单点交叉
                child1, child2 = self._single_point_crossover(
                    parent1,
                    parent2,
                    param_space
                )
                offspring.append(child1)
                offspring.append(child2)
            else:
                offspring.append(parent1.copy())
                offspring.append(parent2.copy())

        # 如果原种群大小为奇数，添加最后一个个体
        if len(population) % 2 != 0:
            offspring.append(population[-1].copy())

        return offspring

    def _single_point_crossover(
        self,
        parent1: Dict[str, Any],
        parent2: Dict[str, Any],
        param_space: Dict[str, Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """单点交叉"""
        param_names = list(parent1.keys())
        crossover_point = random.randint(1, len(param_names) - 1)

        child1 = {}
        child2 = {}

        for i, param_name in enumerate(param_names):
            if i < crossover_point:
                child1[param_name] = parent1[param_name]
                child2[param_name] = parent2[param_name]
            else:
                child1[param_name] = parent2[param_name]
                child2[param_name] = parent1[param_name]

        return child1, child2

    def _mutation(
        self,
        population: List[Dict[str, Any]],
        mutation_rate: float,
        param_space: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """变异操作"""
        mutated = []

        for individual in population:
            new_individual = individual.copy()

            for param_name in individual:
                if random.random() < mutation_rate:
                    # 执行变异
                    space = param_space.get(param_name, {})
                    if space.get("type") == "continuous":
                        # 高斯变异
                        current_value = individual[param_name]
                        std = (space["range"][1] - space["range"][0]) * 0.1
                        new_value = current_value + random.gauss(0, std)
                        new_value = max(space["range"][0], min(space["range"][1], new_value))
                        new_individual[param_name] = new_value
                    elif space.get("type") == "discrete":
                        # 随机变异
                        new_individual[param_name] = random.randint(
                            space["range"][0],
                            space["range"][1]
                        )

            mutated.append(new_individual)

        return mutated

    # ========== 组合优化辅助方法 ==========

    async def _optimize_weights(
        self,
        strategies: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """优化策略权重"""
        # 简化实现：等权重
        # 实际应该使用均值-方差模型、风险平价等方法

        n = len(strategies)
        weight = 1.0 / n

        return {strategy["name"]: weight for strategy in strategies}

    async def _calculate_portfolio_metrics(
        self,
        strategies: List[Dict[str, Any]],
        weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """计算组合指标"""
        # 模拟组合指标计算
        import random

        return {
            "total_return": round(random.uniform(10, 25), 2),
            "sharpe_ratio": round(random.uniform(1.0, 2.0), 2),
            "max_drawdown": round(random.uniform(10, 20), 2),
            "volatility": round(random.uniform(12, 18), 2),
            "diversification_ratio": round(random.uniform(1.2, 1.8), 2)
        }

    def _generate_portfolio_recommendations(
        self,
        strategies: List[Dict[str, Any]],
        weights: Dict[str, float],
        metrics: Dict[str, Any]
    ) -> List[str]:
        """生成组合建议"""
        recommendations = []

        if metrics.get("sharpe_ratio", 0) > 1.5:
            recommendations.append("组合夏普比率优秀，风险调整后收益良好")

        if metrics.get("max_drawdown", 0) < 15:
            recommendations.append("组合风险控制良好，最大回撤在可接受范围")

        if metrics.get("diversification_ratio", 0) > 1.5:
            recommendations.append("策略分散度良好，可以有效降低单一策略风险")

        # 权重建议
        max_weight = max(weights.values())
        if max_weight > 0.5:
            recommendations.append("建议降低单一策略权重，提高组合分散度")

        return recommendations if recommendations else ["组合配置合理"]

    # ========== 摘要生成方法 ==========

    def _generate_optimization_summary(
        self,
        comparison: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
        confidence: float
    ) -> str:
        """生成优化摘要"""
        return_improvement = comparison.get("return_improvement", 0)
        sharpe_improvement = comparison.get("sharpe_improvement", 0)

        summary_parts = []

        if return_improvement > 0:
            summary_parts.append(f"预期收益提升{return_improvement:.2f}%")

        if sharpe_improvement > 0:
            summary_parts.append(f"夏普比率提升{sharpe_improvement:.2f}")

        summary_parts.append(f"优化置信度{confidence*100:.0f}%")

        if recommendations:
            summary_parts.append(f"共{len(recommendations)}项参数调整建议")

        return "，".join(summary_parts)

    def _generate_portfolio_summary(self, metrics: Dict[str, Any]) -> str:
        """生成组合摘要"""
        return (
            f"组合收益{metrics['total_return']:.2f}%，"
            f"夏普比率{metrics['sharpe_ratio']:.2f}，"
            f"最大回撤{metrics['max_drawdown']:.2f}%，"
            f"分散度比率{metrics['diversification_ratio']:.2f}"
        )
