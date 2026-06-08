"""
状态机模块 - 任务生命周期管理

版本: 2.0 (8部门制)
方案: Plan B - 自己实现，不依赖OpenClaw
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import uuid
import time


# 状态机配置（从配置文件加载）
STATE_MACHINE = {
    'Pending': {
        'name': '待处理',
        'next_state': 'Commander',
        'timeout': None
    },
    'Commander': {
        'name': '总司令识别',
        'next_state': 'Research',
        'timeout': 10
    },
    'Research': {
        'name': '研究部分析',
        'next_state': 'Analysis',
        'timeout': 60
    },
    'Analysis': {
        'name': '分析部分析',
        'next_state': 'Review',
        'timeout': 90
    },
    'Review': {
        'name': '质量审核',
        'next_state': 'Prediction',
        'next_state_reject': 'Research',
        'timeout': 15
    },
    'Prediction': {
        'name': '预测部计算',
        'next_state': 'Strategy',
        'timeout': 60
    },
    'Strategy': {
        'name': '策略部分析',
        'next_state': 'Validation',
        'timeout': 60
    },
    'Validation': {
        'name': '验证部验证',
        'next_state': 'Report',
        'timeout': 45
    },
    'Report': {
        'name': '生成报告',
        'next_state': 'Done',
        'timeout': 20
    },
    'Done': {
        'name': '完成',
        'next_state': None,
        'timeout': None
    }
}


@dataclass
class Task:
    """
    投资分析任务

    管理单个投资分析任务的完整生命周期，从创建到完成。
    """

    # 基本信息
    task_id: str
    stock_code: str
    stock_name: Optional[str] = None

    # 状态信息
    current_state: str = 'Pending'
    previous_state: Optional[str] = None
    state_history: List[Dict] = field(default_factory=list)

    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    state_transitions: Dict[str, datetime] = field(default_factory=dict)

    # 部门执行结果
    department_results: Dict = field(default_factory=lambda: {
        'Research': None,
        'Analysis': None,
        'Prediction': None,
        'Strategy': None,
        'Validation': None
    })

    # 质量评分
    quality_scores: Dict = field(default_factory=lambda: {
        'Research': 0,
        'Analysis': 0
    })

    # 最终报告
    final_report: Optional[Dict] = None

    # 错误信息
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def transition_to(self, new_state: str) -> None:
        """
        状态转换

        Args:
            new_state: 新状态名称
        """
        # 记录历史
        self.previous_state = self.current_state
        self.current_state = new_state

        # 添加到历史记录
        self.state_history.append({
            'from': self.previous_state,
            'to': new_state,
            'timestamp': datetime.now().isoformat()
        })

        # 记录转换时间
        self.state_transitions[new_state] = datetime.now()

        # 记录开始时间
        if new_state != 'Pending' and self.started_at is None:
            self.started_at = datetime.now()

        # 记录完成时间
        if new_state == 'Done':
            self.completed_at = datetime.now()

    def is_complete(self) -> bool:
        """
        检查任务是否完成

        Returns:
            True 如果任务已完成
        """
        return self.current_state == 'Done'

    def get_duration(self) -> timedelta:
        """
        获取任务耗时

        Returns:
            任务持续时间
        """
        if self.completed_at:
            return self.completed_at - (self.started_at or self.created_at)
        elif self.started_at:
            return datetime.now() - self.started_at
        else:
            return timedelta(0)

    def add_error(self, error: str) -> None:
        """
        添加错误信息

        Args:
            error: 错误描述
        """
        self.errors.append(f"[{datetime.now().isoformat()}] {error}")

    def add_warning(self, warning: str) -> None:
        """
        添加警告信息

        Args:
            warning: 警告描述
        """
        self.warnings.append(f"[{datetime.now().isoformat()}] {warning}")

    def to_dict(self) -> Dict:
        """
        转换为字典格式

        Returns:
            任务信息的字典表示
        """
        return {
            'task_id': self.task_id,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'current_state': self.current_state,
            'previous_state': self.previous_state,
            'state_history': self.state_history,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': str(self.get_duration()),
            'department_results': self.department_results,
            'quality_scores': self.quality_scores,
            'final_report': self.final_report,
            'errors': self.errors,
            'warnings': self.warnings
        }

    def to_json(self) -> str:
        """
        转换为JSON字符串

        Returns:
            JSON格式的任务信息
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def create_task(stock_code: str, task_id: Optional[str] = None) -> Task:
    """
    创建新任务的工厂函数

    Args:
        stock_code: 股票代码
        task_id: 可选的任务ID（不提供则自动生成）

    Returns:
        新创建的任务对象
    """
    if task_id is None:
        timestamp = int(datetime.now().timestamp())
        task_id = f"ANALYSIS-{stock_code}-{timestamp}"

    return Task(task_id=task_id, stock_code=stock_code)


class StateMachineEngine:
    """
    状态机引擎

    管理所有任务的状态转换和执行流程。
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化状态机引擎

        Args:
            config_path: 配置文件路径（可选）
        """
        self.tasks: Dict[str, Task] = {}
        self.active_tasks: Set[str] = set()
        self.state_machine = STATE_MACHINE

        # 如果提供了配置文件，加载配置
        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str) -> None:
        """
        从配置文件加载状态机定义

        Args:
            config_path: 配置文件路径
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.state_machine = config.get('state_machine', STATE_MACHINE)
        except Exception as e:
            # 加载失败，使用默认配置
            print(f"Warning: Failed to load config from {config_path}: {e}")

    async def create_task(self, stock_code: str) -> str:
        """
        创建新任务

        Args:
            stock_code: 股票代码

        Returns:
            任务ID
        """
        task = create_task(stock_code)
        self.tasks[task.task_id] = task
        self.active_tasks.add(task.task_id)
        return task.task_id

    async def run_task(self, task_id: str) -> bool:
        """
        运行任务（状态循环）

        Args:
            task_id: 任务ID

        Returns:
            True 如果任务成功完成
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        try:
            # 状态循环
            while not task.is_complete():
                current_state = task.current_state

                # 检查超时
                if self._is_timeout(task, current_state):
                    timeout_error = f"State {current_state} timeout after {self.state_machine[current_state]['timeout']}s"
                    task.add_error(timeout_error)
                    # 可以选择继续或停止
                    # 这里选择继续到下一个状态
                    task.add_warning(f"Timeout handled: continuing to next state")

                # 获取下一个状态
                state_config = self.state_machine.get(current_state)
                if not state_config:
                    task.add_error(f"Unknown state: {current_state}")
                    break

                next_state = state_config.get('next_state')
                if not next_state:
                    # 没有下一个状态，结束
                    break

                # 状态转换（实际执行逻辑由外部实现）
                # 这里只负责状态管理
                task.transition_to(next_state)

                # 模拟异步执行（实际项目中这里会调用对应的Agent）
                await asyncio.sleep(0.1)

            # 标记任务完成
            if task.is_complete():
                self.active_tasks.discard(task_id)
                return True
            else:
                return False

        except Exception as e:
            task.add_error(f"Task execution failed: {e}")
            self.active_tasks.discard(task_id)
            return False

    def _is_timeout(self, task: Task, state: str) -> bool:
        """
        检查状态是否超时

        Args:
            task: 任务对象
            state: 状态名称

        Returns:
            True 如果超时
        """
        state_config = self.state_machine.get(state)
        if not state_config:
            return False

        timeout = state_config.get('timeout')
        if timeout is None:
            return False

        # 获取进入该状态的时间
        state_enter_time = task.state_transitions.get(state)
        if not state_enter_time:
            return False

        # 计算持续时间
        duration = (datetime.now() - state_enter_time).total_seconds()
        return duration > timeout

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        return {
            'task_id': task.task_id,
            'stock_code': task.stock_code,
            'stock_name': task.stock_name,
            'current_state': task.current_state,
            'state_name': self.state_machine.get(task.current_state, {}).get('name', 'Unknown'),
            'progress': self._calculate_progress(task),
            'duration': str(task.get_duration()),
            'errors': task.errors,
            'warnings': task.warnings,
            'is_complete': task.is_complete()
        }

    def _calculate_progress(self, task: Task) -> float:
        """
        计算任务进度百分比

        Args:
            task: 任务对象

        Returns:
            进度百分比（0-100）
        """
        total_states = len(self.state_machine) - 1  # 排除Done
        current_index = list(self.state_machine.keys()).index(task.current_state)
        return (current_index / total_states) * 100

    def list_tasks(self, include_completed: bool = False) -> List[Dict]:
        """
        列出所有任务

        Args:
            include_completed: 是否包含已完成的任务

        Returns:
            任务列表
        """
        tasks = []
        for task_id, task in self.tasks.items():
            if include_completed or not task.is_complete():
                tasks.append(self.get_task_status(task_id))
        return tasks

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            True 如果取消成功
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.add_warning("Task cancelled by user")
        task.transition_to('Done')
        self.active_tasks.discard(task_id)
        return True

    def get_active_count(self) -> int:
        """
        获取活跃任务数量

        Returns:
            活跃任务数量
        """
        return len(self.active_tasks)

    def clear_completed_tasks(self) -> int:
        """
        清理已完成的任务

        Returns:
            清理的任务数量
        """
        completed_ids = [
            task_id for task_id, task in self.tasks.items()
            if task.is_complete()
        ]
        for task_id in completed_ids:
            del self.tasks[task_id]
        return len(completed_ids)
