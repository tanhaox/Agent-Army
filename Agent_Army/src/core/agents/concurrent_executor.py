"""
Agent Army - 并发调度器 v2.0 (包月版)
充分利用GLM Coding Plan Max的并发额度
"""

import asyncio
from typing import Dict, List, Any, Callable
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass

from src.core.config.model_config_v2 import (
    ModelType,
    get_model_name,
    get_model_config,
    get_concurrency_limit,
    group_agents_by_model
)


@dataclass
class Task:
    """任务"""
    agent_id: str
    stock_code: str
    task_type: str
    priority: int = 0  # 0=normal, 1=high, 2=urgent
    data: Any = None


@dataclass
class TaskResult:
    """任务结果"""
    agent_id: str
    stock_code: str
    success: bool
    result: Any
    error: str = None
    execution_time: float = 0.0
    model_used: str = None


class ConcurrencyManager:
    """并发管理器"""

    def __init__(self):
        # 并发信号量
        self.semaphores = {
            ModelType.STRATEGIC: asyncio.Semaphore(10),  # GLM-5
            ModelType.PREMIUM: asyncio.Semaphore(20),    # GLM-4.7
            ModelType.CODE: asyncio.Semaphore(50)        # codegeex-4
        }

        # 使用统计
        self.usage_stats = defaultdict(lambda: {
            "total": 0,
            "active": 0,
            "completed": 0,
            "failed": 0
        })

    async def acquire(self, agent_id: str):
        """获取并发槽位"""
        from src.core.config.model_config_v2 import get_model_type
        model_type = get_model_type(agent_id)
        semaphore = self.semaphores[model_type]

        self.usage_stats[model_type]["total"] += 1
        self.usage_stats[model_type]["active"] += 1

        await semaphore.acquire()

    def release(self, agent_id: str):
        """释放并发槽位"""
        from src.core.config.model_config_v2 import get_model_type
        model_type = get_model_type(agent_id)

        self.usage_stats[model_type]["active"] -= 1
        self.usage_stats[model_type]["completed"] += 1

        self.semaphores[model_type].release()

    def get_usage_stats(self) -> Dict:
        """获取使用统计"""
        return {
            model_type.value: dict(stats)
            for model_type, stats in self.usage_stats.items()
        }


class PriorityScheduler:
    """优先级调度器"""

    def __init__(self):
        # 优先级队列
        self.queues = {
            2: [],  # urgent
            1: [],  # high
            0: []   # normal
        }

    def add_task(self, task: Task):
        """添加任务到队列"""
        self.queues[task.priority].append(task)

    def get_next_task(self) -> Task:
        """获取下一个任务（按优先级）"""
        for priority in [2, 1, 0]:  # 从高到低
            if self.queues[priority]:
                return self.queues[priority].pop(0)
        return None

    def has_tasks(self) -> bool:
        """是否还有任务"""
        return any(len(queue) > 0 for queue in self.queues.values())


class BatchExecutor:
    """批量执行器"""

    def __init__(self):
        self.concurrency_manager = ConcurrencyManager()
        self.scheduler = PriorityScheduler()

    async def execute_task(
        self,
        task: Task,
        execute_func: Callable
    ) -> TaskResult:
        """
        执行单个任务

        Args:
            task: 任务
            execute_func: 执行函数

        Returns:
            任务结果
        """
        start_time = datetime.now()
        model_used = get_model_name(task.agent_id)

        try:
            # 获取并发槽位
            await self.concurrency_manager.acquire(task.agent_id)

            # 执行任务
            result = await execute_func(task)

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            return TaskResult(
                agent_id=task.agent_id,
                stock_code=task.stock_code,
                success=True,
                result=result,
                execution_time=execution_time,
                model_used=model_used
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            return TaskResult(
                agent_id=task.agent_id,
                stock_code=task.stock_code,
                success=False,
                error=str(e),
                execution_time=execution_time,
                model_used=model_used
            )

        finally:
            # 释放并发槽位
            self.concurrency_manager.release(task.agent_id)

    async def execute_batch(
        self,
        tasks: List[Task],
        execute_func: Callable
    ) -> List[TaskResult]:
        """
        批量执行任务

        Args:
            tasks: 任务列表
            execute_func: 执行函数

        Returns:
            结果列表
        """
        # 按模型分组（优化并发）
        groups = group_agents_by_model([task.agent_id for task in tasks])

        # 为每个模型创建任务组
        task_groups = []
        for model_name, agent_ids in groups.items():
            model_tasks = [t for t in tasks if t.agent_id in agent_ids]
            task_groups.append((model_name, model_tasks))

        # 并发执行所有任务
        results = await asyncio.gather(*[
            self.execute_task(task, execute_func)
            for task in tasks
        ])

        return results

    async def execute_batch_optimized(
        self,
        tasks: List[Task],
        execute_func: Callable
    ) -> List[TaskResult]:
        """
        优化的批量执行（按模型分组）

        Args:
            tasks: 任务列表
            execute_func: 执行函数

        Returns:
            结果列表
        """
        # 按模型分组
        groups = defaultdict(list)
        for task in tasks:
            model_name = get_model_name(task.agent_id)
            groups[model_name].append(task)

        # 为每个模型并发执行任务
        all_results = []

        for model_name, model_tasks in groups.items():
            # 并发执行同一模型的所有任务
            model_results = await asyncio.gather(*[
                self.execute_task(task, execute_func)
                for task in model_tasks
            ])

            all_results.extend(model_results)

        return all_results


class AgentExecutor:
    """Agent执行器（主入口）"""

    def __init__(self):
        self.batch_executor = BatchExecutor()
        self.execution_history = []

    async def execute_agents(
        self,
        agent_ids: List[str],
        stock_codes: List[str],
        execute_func: Callable,
        priority: int = 0
    ) -> List[TaskResult]:
        """
        执行多个Agent

        Args:
            agent_ids: Agent ID列表
            stock_codes: 股票代码列表
            execute_func: 执行函数
            priority: 优先级

        Returns:
            结果列表
        """
        # 创建任务
        tasks = []
        for agent_id in agent_ids:
            for stock_code in stock_codes:
                task = Task(
                    agent_id=agent_id,
                    stock_code=stock_code,
                    task_type="analysis",
                    priority=priority
                )
                tasks.append(task)

        # 批量执行
        results = await self.batch_executor.execute_batch_optimized(
            tasks,
            execute_func
        )

        # 记录历史
        self.execution_history.extend(results)

        return results

    async def execute_single_agent(
        self,
        agent_id: str,
        stock_codes: List[str],
        execute_func: Callable
    ) -> List[TaskResult]:
        """
        执行单个Agent（多股票）

        Args:
            agent_id: Agent ID
            stock_codes: 股票代码列表
            execute_func: 执行函数

        Returns:
            结果列表
        """
        return await self.execute_agents(
            [agent_id],
            stock_codes,
            execute_func
        )

    async def execute_full_analysis(
        self,
        stock_code: str,
        execute_func: Callable
    ) -> Dict[str, TaskResult]:
        """
        执行全量分析（24个Agent）

        Args:
            stock_code: 股票代码
            execute_func: 执行函数

        Returns:
            {agent_id: TaskResult} 字典
        """
        # 所有24个Agent
        all_agents = [
            "macro_economic", "industry_chain", "policy_impact",
            "industry_cycle", "competitive_landscape",
            "news_monitor", "capital_flow", "market_sentiment", "hot_sector",
            "financial_health", "growth_analysis", "valuation_ai",
            "technical_analysis",
            "price_prediction", "earnings_forecast", "risk_assessment",
            "trend_analysis",
            "asset_allocation", "timing_strategy", "position_management",
            "stop_loss_strategy",
            "backtesting", "performance_attribution", "model_validator"
        ]

        # 执行所有Agent
        results = await self.execute_agents(
            all_agents,
            [stock_code],
            execute_func,
            priority=1  # 全量分析使用高优先级
        )

        # 转换为字典
        return {
            result.agent_id: result
            for result in results
        }

    def get_execution_stats(self) -> Dict:
        """获取执行统计"""
        if not self.execution_history:
            return {}

        total = len(self.execution_history)
        success = sum(1 for r in self.execution_history if r.success)
        failed = total - success

        avg_time = sum(r.execution_time for r in self.execution_history) / total

        by_model = defaultdict(lambda: {"count": 0, "success": 0, "avg_time": 0})
        for result in self.execution_history:
            model = result.model_used
            by_model[model]["count"] += 1
            if result.success:
                by_model[model]["success"] += 1
            by_model[model]["avg_time"] += result.execution_time

        # 计算平均时间
        for model in by_model:
            by_model[model]["avg_time"] /= by_model[model]["count"]

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": success / total if total > 0 else 0,
            "avg_execution_time": avg_time,
            "by_model": dict(by_model)
        }


# ========== 示例使用 ==========

async def example_usage():
    """示例用法"""

    # 执行器
    executor = AgentExecutor()

    # 模拟执行函数
    async def mock_execute_func(task: Task):
        # 模拟API调用
        await asyncio.sleep(1)
        return f"Analysis result for {task.stock_code}"

    # 示例1: 执行单个Agent（多股票）
    print("示例1: 执行单个Agent")
    results1 = await executor.execute_single_agent(
        "macro_economic",
        ["000001", "000002", "000003"],
        mock_execute_func
    )
    print(f"完成 {len(results1)} 个任务")

    # 示例2: 执行多个Agent（单股票）
    print("\n示例2: 执行多个Agent")
    results2 = await executor.execute_agents(
        ["macro_economic", "financial_health", "technical_analysis"],
        ["000001"],
        mock_execute_func
    )
    print(f"完成 {len(results2)} 个任务")

    # 示例3: 执行全量分析（24个Agent）
    print("\n示例3: 执行全量分析")
    results3 = await executor.execute_full_analysis(
        "000001",
        mock_execute_func
    )
    print(f"完成 {len(results3)} 个Agent")

    # 统计
    stats = executor.get_execution_stats()
    print(f"\n统计: {stats}")


# ========== 导出 ==========

__all__ = [
    'Task',
    'TaskResult',
    'ConcurrencyManager',
    'PriorityScheduler',
    'BatchExecutor',
    'AgentExecutor'
]
