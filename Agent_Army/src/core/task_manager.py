"""
任务管理器模块 - 统一任务管理接口

版本: 2.0 (8部门制)
方案: Plan B - 自己实现，不依赖OpenClaw
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from src.core.state_machine import StateMachineEngine, Task
from src.core.permission_matrix import PermissionChecker, PermissionError


class TaskManager:
    """
    任务管理器

    整合状态机和权限矩阵，提供统一的任务管理接口。
    """

    def __init__(
        self,
        state_machine_config: Optional[str] = None,
        permission_config: Optional[str] = None,
        max_concurrent_tasks: int = 10
    ):
        """
        初始化任务管理器

        Args:
            state_machine_config: 状态机配置文件路径
            permission_config: 权限矩阵配置文件路径
            max_concurrent_tasks: 最大并发任务数
        """
        self.state_machine = StateMachineEngine(state_machine_config)
        self.permission_checker = PermissionChecker(permission_config)
        self.max_concurrent_tasks = max_concurrent_tasks

        # 任务队列
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.running_tasks: Dict[str, asyncio.Task] = {}

        # 启动任务处理器
        self._processor_started = False

    async def create_analysis_task(
        self,
        stock_code: str,
        mode: str = "standard",
        caller: str = "investor"
    ) -> str:
        """
        创建投资分析任务

        Args:
            stock_code: 股票代码
            mode: 分析模式（standard | quick）
            caller: 调用者身份

        Returns:
            任务ID

        Raises:
            PermissionError: 如果调用者没有权限
        """
        # 检查权限
        if not self.permission_checker.can_call(caller, 'commander'):
            raise PermissionError(
                f"{caller} 没有权限创建分析任务"
            )

        # 创建任务
        task_id = await self.state_machine.create_task(stock_code)

        # 根据模式设置任务属性
        task = self.state_machine.tasks[task_id]
        task.mode = mode

        # 添加到队列
        await self.task_queue.put(task_id)

        # 启动任务处理器（如果未启动）
        if not self._processor_started:
            asyncio.create_task(self._process_queue())
            self._processor_started = True

        return task_id

    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        return self.state_machine.get_task_status(task_id)

    async def list_tasks(
        self,
        include_completed: bool = False,
        caller: str = "investor"
    ) -> List[Dict]:
        """
        列出任务

        Args:
            include_completed: 是否包含已完成的任务
            caller: 调用者身份

        Returns:
            任务列表
        """
        # 投资者只能查看自己的任务（简化版，实际应该有用户关联）
        tasks = self.state_machine.list_tasks(include_completed)
        return tasks

    async def cancel_task(
        self,
        task_id: str,
        caller: str = "investor"
    ) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID
            caller: 调用者身份

        Returns:
            True 如果取消成功
        """
        # 检查权限（只有创建者或管理员可以取消）
        # 简化版：允许任何人取消

        # 如果任务正在运行，先取消asyncio任务
        if task_id in self.running_tasks:
            asyncio_task = self.running_tasks[task_id]
            asyncio_task.cancel()
            del self.running_tasks[task_id]

        # 在状态机中标记为取消
        return self.state_machine.cancel_task(task_id)

    async def _process_queue(self):
        """
        处理任务队列

        从队列中取出任务并执行，控制并发数量。
        """
        while True:
            try:
                # 检查并发数量
                while len(self.running_tasks) >= self.max_concurrent_tasks:
                    # 等待有任务完成
                    await asyncio.sleep(0.5)

                # 从队列中获取任务
                task_id = await self.task_queue.get()

                # 启动任务
                asyncio_task = asyncio.create_task(
                    self._run_task_with_cleanup(task_id)
                )
                self.running_tasks[task_id] = asyncio_task

            except Exception as e:
                print(f"Error processing queue: {e}")
                await asyncio.sleep(1)

    async def _run_task_with_cleanup(self, task_id: str):
        """
        运行任务并在完成后清理

        Args:
            task_id: 任务ID
        """
        try:
            # 运行任务
            await self.state_machine.run_task(task_id)
        except Exception as e:
            print(f"Task {task_id} failed: {e}")
        finally:
            # 清理
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    def get_queue_size(self) -> int:
        """
        获取队列大小

        Returns:
            队列中的任务数量
        """
        return self.task_queue.qsize()

    def get_running_count(self) -> int:
        """
        获取正在运行的任务数量

        Returns:
            正在运行的任务数量
        """
        return len(self.running_tasks)

    async def wait_for_completion(
        self,
        task_id: str,
        timeout: Optional[float] = None
    ) -> bool:
        """
        等待任务完成

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）

        Returns:
            True 如果任务完成，False 如果超时
        """
        start_time = datetime.now()

        while True:
            # 检查任务是否存在
            task = self.state_machine.tasks.get(task_id)
            if not task:
                return False

            # 检查任务是否完成
            if task.is_complete():
                return True

            # 检查超时
            if timeout:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout:
                    return False

            # 等待一段时间
            await asyncio.sleep(0.5)

    async def get_task_result(self, task_id: str) -> Optional[Dict]:
        """
        获取任务结果

        Args:
            task_id: 任务ID

        Returns:
            任务结果（如果任务已完成）
        """
        task = self.state_machine.tasks.get(task_id)
        if not task or not task.is_complete():
            return None

        return {
            'task_id': task.task_id,
            'stock_code': task.stock_code,
            'stock_name': task.stock_name,
            'final_report': task.final_report,
            'duration': str(task.get_duration()),
            'errors': task.errors,
            'warnings': task.warnings,
            'quality_scores': task.quality_scores
        }

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        total_tasks = len(self.state_machine.tasks)
        active_tasks = self.state_machine.get_active_count()
        completed_tasks = sum(
            1 for task in self.state_machine.tasks.values()
            if task.is_complete()
        )

        return {
            'total_tasks': total_tasks,
            'active_tasks': active_tasks,
            'completed_tasks': completed_tasks,
            'queued_tasks': self.get_queue_size(),
            'running_tasks': self.get_running_count(),
            'max_concurrent_tasks': self.max_concurrent_tasks
        }
