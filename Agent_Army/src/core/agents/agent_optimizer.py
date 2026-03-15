"""
Agent Army - Agent优化器
动态模型选择、成本优化、性能监控
"""

import time
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict

from src.core.config.model_config import (
    AGENT_MODEL_CONFIG,
    ModelTier,
    ModelConfig,
    get_agent_config
)


class TaskProfile:
    """任务画像"""

    def __init__(
        self,
        task_type: str,
        complexity: str = "medium",
        urgency: str = "medium",
        budget: str = "medium",
        data_size: int = 0,
        requires_code: bool = False,
        requires_long_context: bool = False
    ):
        self.task_type = task_type
        self.complexity = complexity  # low/medium/high
        self.urgency = urgency  # low/medium/high
        self.budget = budget  # low/medium/high
        self.data_size = data_size  # 数据大小（字节）
        self.requires_code = requires_code
        self.requires_long_context = requires_long_context


class ModelSelector:
    """模型选择器"""

    @staticmethod
    def select_optimal_model(agent_id: str, task_profile: TaskProfile) -> Dict[str, Any]:
        """
        为Agent和任务选择最优模型

        Args:
            agent_id: Agent ID
            task_profile: 任务画像

        Returns:
            模型配置
        """
        # 获取Agent默认配置
        default_config = get_agent_config(agent_id)
        default_tier = default_config["tier"]

        # 根据任务特性动态调整
        optimized_tier = ModelSelector._optimize_tier(default_tier, task_profile)

        # 更新配置
        optimized_config = default_config.copy()
        optimized_config["tier"] = optimized_tier
        optimized_config["model"] = ModelConfig.get_model_name(optimized_tier)
        optimized_config["optimized"] = True
        optimized_config["optimization_reason"] = \
            ModelSelector._get_optimization_reason(default_tier, optimized_tier, task_profile)

        return optimized_config

    @staticmethod
    def _optimize_tier(default_tier: ModelTier, task_profile: TaskProfile) -> ModelTier:
        """根据任务特性优化模型等级"""

        # 1. 任务需要代码生成 → 使用codegeex-4
        if task_profile.requires_code:
            return ModelTier.SONNET_PLUS

        # 2. 任务需要长上下文 → 使用GLM-4.7
        if task_profile.requires_long_context:
            return ModelTier.OPUS

        # 3. 根据复杂度和紧急度调整
        complexity = task_profile.complexity
        urgency = task_profile.urgency

        # 高复杂度 → 使用强模型
        if complexity == "high":
            if urgency == "high":
                # 紧急且复杂 → 用Opus-（平衡）
                return ModelTier.OPUS_MINUS
            else:
                # 不紧急 → 用Opus或Opus+
                return default_tier if default_tier.value in ["opus", "opus_plus"] else ModelTier.OPUS

        # 中等复杂度 → 使用标准模型
        elif complexity == "medium":
            if urgency == "high":
                # 紧急 → 降级到Sonnet（高并发）
                return ModelTier.SONNET
            else:
                # 不紧急 → 保持默认
                return default_tier

        # 低复杂度 → 使用低成本模型
        else:  # complexity == "low"
            if urgency == "high":
                # 紧急 → 用Haiku（最快）
                return ModelTier.HAIKU
            else:
                # 不紧急 → 用Sonnet（性价比）
                return ModelTier.SONNET

    @staticmethod
    def _get_optimization_reason(
        default_tier: ModelTier,
        optimized_tier: ModelTier,
        task_profile: TaskProfile
    ) -> str:
        """获取优化原因"""
        if default_tier == optimized_tier:
            return "保持默认配置"

        reasons = []

        if task_profile.requires_code:
            reasons.append("任务需要代码生成")

        if task_profile.requires_long_context:
            reasons.append("任务需要长上下文")

        if task_profile.complexity == "high" and optimized_tier.value in ["opus", "opus_plus"]:
            reasons.append("高复杂度任务使用强模型")

        if task_profile.urgency == "high" and optimized_tier.value in ["sonnet", "haiku"]:
            reasons.append("高紧急度使用高并发模型")

        if task_profile.complexity == "low" and optimized_tier.value in ["sonnet", "haiku"]:
            reasons.append("低复杂度使用低成本模型")

        return "; ".join(reasons) if reasons else "优化配置"


class CostOptimizer:
    """成本优化器"""

    def __init__(self):
        self.usage_stats = defaultdict(lambda: {
            "count": 0,
            "total_cost": 0.0,
            "total_time": 0.0
        })

    def record_usage(self, agent_id: str, model_tier: ModelTier, execution_time: float):
        """记录使用情况"""
        stats = self.usage_stats[agent_id]
        stats["count"] += 1
        stats["total_cost"] += ModelConfig.get_cost_weight(model_tier)
        stats["total_time"] += execution_time

    def get_cost_report(self) -> Dict[str, Any]:
        """获取成本报告"""
        total_cost = sum(
            stats["total_cost"]
            for stats in self.usage_stats.values()
        )

        report = {
            "total_cost": total_cost,
            "by_agent": {},
            "by_tier": defaultdict(lambda: {"count": 0, "cost": 0.0})
        }

        for agent_id, stats in self.usage_stats.items():
            report["by_agent"][agent_id] = {
                "count": stats["count"],
                "total_cost": stats["total_cost"],
                "avg_cost": stats["total_cost"] / stats["count"] if stats["count"] > 0 else 0,
                "avg_time": stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
            }

        return report

    def suggest_optimization(self) -> List[str]:
        """建议优化措施"""
        suggestions = []

        # 找出成本最高的Agent
        cost_report = self.get_cost_report()
        by_agent = cost_report["by_agent"]

        if by_agent:
            most_expensive = max(by_agent.items(), key=lambda x: x[1]["total_cost"])
            avg_cost = by_agent[most_expensive[0]]["avg_cost"]

            if avg_cost > 20:  # 成本阈值
                suggestions.append(
                    f"Agent '{most_expensive[0]}' 平均成本较高 (¥{avg_cost:.2f})，"
                    f"考虑降低模型等级或增加缓存"
                )

        # 找出执行时间最长的Agent
        slowest = max(
            by_agent.items(),
            key=lambda x: x[1]["avg_time"],
            default=(None, {"avg_time": 0})
        )

        if slowest[1]["avg_time"] > 10:  # 时间阈值（秒）
            suggestions.append(
                f"Agent '{slowest[0]}' 平均执行时间较长 ({slowest[1]['avg_time']:.1f}s)，"
                f"考虑优化prompt或使用更快的模型"
            )

        return suggestions


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics = defaultdict(lambda: {
            "calls": 0,
            "total_time": 0.0,
            "success": 0,
            "failure": 0,
            "cache_hits": 0
        })

    def record_call(self, agent_id: str, execution_time: float, success: bool, cache_hit: bool):
        """记录调用"""
        metrics = self.metrics[agent_id]
        metrics["calls"] += 1
        metrics["total_time"] += execution_time
        if success:
            metrics["success"] += 1
        else:
            metrics["failure"] += 1
        if cache_hit:
            metrics["cache_hits"] += 1

    def get_metrics(self, agent_id: str = None) -> Dict[str, Any]:
        """获取性能指标"""
        if agent_id:
            return dict(self.metrics[agent_id])
        else:
            return {k: dict(v) for k, v in self.metrics.items()}

    def get_slowest_agents(self, top_n: int = 5) -> List[tuple]:
        """获取最慢的Agent"""
        agent_times = [
            (agent_id, metrics["total_time"] / metrics["calls"] if metrics["calls"] > 0 else 0)
            for agent_id, metrics in self.metrics.items()
        ]
        return sorted(agent_times, key=lambda x: x[1], reverse=True)[:top_n]

    def get_success_rate(self, agent_id: str) -> float:
        """获取成功率"""
        metrics = self.metrics[agent_id]
        total = metrics["success"] + metrics["failure"]
        return metrics["success"] / total if total > 0 else 0.0

    def get_cache_hit_rate(self, agent_id: str) -> float:
        """获取缓存命中率"""
        metrics = self.metrics[agent_id]
        return metrics["cache_hits"] / metrics["calls"] if metrics["calls"] > 0 else 0.0


class AgentOptimizer:
    """Agent优化器（主入口）"""

    def __init__(self):
        self.model_selector = ModelSelector()
        self.cost_optimizer = CostOptimizer()
        self.performance_monitor = PerformanceMonitor()

    def optimize_and_execute(
        self,
        agent_id: str,
        task_profile: TaskProfile,
        execute_func: callable
    ) -> Any:
        """
        优化并执行Agent任务

        Args:
            agent_id: Agent ID
            task_profile: 任务画像
            execute_func: 执行函数

        Returns:
            执行结果
        """
        # 1. 选择最优模型
        model_config = self.model_selector.select_optimal_model(agent_id, task_profile)

        # 2. 记录开始时间
        start_time = time.time()

        # 3. 执行任务
        try:
            result = execute_func(model_config)
            success = True
        except Exception as e:
            result = e
            success = False

        # 4. 记录执行时间
        execution_time = time.time() - start_time

        # 5. 更新统计
        model_tier = model_config["tier"]
        self.cost_optimizer.record_usage(agent_id, model_tier, execution_time)
        self.performance_monitor.record_call(
            agent_id,
            execution_time,
            success,
            cache_hit=False  # TODO: 实现缓存检测
        )

        # 6. 返回结果
        return {
            "result": result,
            "model_config": model_config,
            "execution_time": execution_time,
            "success": success
        }

    def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告"""
        return {
            "cost_report": self.cost_optimizer.get_cost_report(),
            "performance_metrics": self.performance_monitor.get_metrics(),
            "optimization_suggestions": self.cost_optimizer.suggest_optimization(),
            "slowest_agents": self.performance_monitor.get_slowest_agents(5)
        }


# ========== 全局优化器实例 ==========

_global_optimizer = None


def get_agent_optimizer() -> AgentOptimizer:
    """获取全局Agent优化器实例"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = AgentOptimizer()
    return _global_optimizer


# 导出
__all__ = [
    'TaskProfile',
    'ModelSelector',
    'CostOptimizer',
    'PerformanceMonitor',
    'AgentOptimizer',
    'get_agent_optimizer'
]
