"""
AI-Agent-Local 子代理框架
基于 SADD (Subagent-Driven Development) 模式

核心原则：
- Fresh subagent per task - 上下文隔离
- Quality gates - 任务间代码审查
- Parallel execution - 并行处理独立任务
- Fast iteration - 快速迭代

Version: 1.0.0
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import json
import sys

# 导入代码审查器
from reviewer import CodeReviewer, create_reviewer

logger = logging.getLogger(__name__)


# ==================== 数据类 ====================

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEWING = "reviewing"
    BLOCKED = "blocked"


class Severity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"  # 必须立即修复
    IMPORTANT = "important"  # 下个任务前修复
    MINOR = "minor"        # 记录即可


@dataclass
class Task:
    """任务定义"""
    id: str
    name: str
    description: str
    requirements: str
    directory: Optional[str] = None
    files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 2  # 0=critical, 1=high, 2=medium, 3=low, 4=backlog
    complexity: str = "medium"  # low, medium, high
    task_type: str = "development"  # development, testing, review, docs
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubAgentResult:
    """子代理执行结果"""
    task_id: str
    agent_id: str
    status: TaskStatus
    output: str
    files_changed: List[str] = field(default_factory=list)
    tests_run: List[str] = field(default_factory=list)
    commit_hash: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeReviewIssue:
    """代码审查问题"""
    severity: Severity
    category: str  # bug, security, performance, style, architecture
    description: str
    location: Optional[str] = None  # file:line
    suggestion: Optional[str] = None


@dataclass
class CodeReview:
    """代码审查结果"""
    task_id: str
    overall_assessment: str  # excellent, good, needs_work, poor
    strengths: List[str] = field(default_factory=list)
    issues: List[CodeReviewIssue] = field(default_factory=list)
    score: float = 0.0  # 0.0-10.0
    recommendations: List[str] = field(default_factory=list)


# ==================== 模型选择策略 ====================

class ModelSelector:
    """模型选择器"""

    # 根据任务类型选择基础模型
    MODEL_BY_TASK_TYPE = {
        "architecture": "opus",      # 架构设计
        "design": "sonnet",           # 设计
        "coding": "sonnet",            # 编码
        "testing": "haiku",           # 测试
        "documentation": "haiku",     # 文档
        "review": "opus",             # 审查
        "analysis": "sonnet",          # 分析
        "refactoring": "sonnet",       # 重构
    }

    # 复杂度调整
    COMPLEXITY_UPGRADE = {
        ("low", "sonnet"): "sonnet",
        ("low", "haiku"): "sonnet",
        ("medium", "sonnet"): "opus",
        ("medium", "haiku"): "sonnet",
        ("high", "sonnet"): "opus",
        ("high", "haiku"): "sonnet",
    }

    @classmethod
    def select_model(
        cls,
        task_type: str,
        complexity: str = "medium",
        explicit_model: Optional[str] = None
    ) -> str:
        """
        选择合适的模型

        Args:
            task_type: 任务类型
            complexity: 复杂度
            explicit_model: 强制指定模型

        Returns:
            模型名称
        """
        if explicit_model:
            return explicit_model

        base_model = cls.MODEL_BY_TASK_TYPE.get(task_type, "sonnet")
        return cls.COMPLEXITY_UPGRADE.get((complexity, base_model), base_model)

    @classmethod
    def get_agent_for_task(
        cls,
        task: Task,
        explicit_agent: Optional[str] = None
    ) -> str:
        """为任务选择代理类型"""
        if explicit_agent:
            return explicit_agent

        # 简化的代理类型映射
        AGENT_MAPPING = {
            "architecture": "software-architect",
            "design": "developer",
            "coding": "developer",
            "testing": "qa-engineer",
            "documentation": "tech-writer",
            "review": "code-reviewer",
            "analysis": "analyst",
        }

        return AGENT_MAPPING.get(task.task_type, "developer")


# ==================== 子代理基类 ====================

class SubAgent(ABC):
    """子代理基类"""

    def __init__(self, agent_id: str, model: str = "sonnet"):
        self.agent_id = agent_id
        self.model = model
        self.logger = logging.getLogger(f"subagent.{agent_id}")

    @abstractmethod
    async def execute(self, task: Task) -> SubAgentResult:
        """执行任务"""
        pass

    def _create_prompt(self, task: Task) -> str:
        """创建执行提示"""
        return f"""
你是一个专业的开发者，正在执行以下任务：

任务名称：{task.name}
任务描述：{task.description}
要求：
{task.requirements}

工作目录：{task.directory or '当前目录'}}
相关文件：{', '.join(task.files) if task.files else '无'}

请：
1. 仔细理解任务要求
2. 实现指定的功能
3. 编写必要的测试（如果适用）
4. 验证实现正确性
5. 提交工作（如果使用 Git）

完成后，请提供：
- 实现说明
- 测试结果
- 文件变更列表
- 任何问题或建议

请立即开始执行，不要询问任何问题。
"""


# ==================== 调度器基类 ====================

class ExecutionStrategy(ABC):
    """执行策略基类"""

    @abstractmethod
    async def execute(self, tasks: List[Task], dispatcher: 'Dispatcher') -> List[SubAgentResult]:
        """执行任务列表"""
        pass


class SequentialStrategy(ExecutionStrategy):
    """顺序执行策略"""

    async def execute(
        self,
        tasks: List[Task],
        dispatcher: 'Dispatcher'
    ) -> List[SubAgentResult]:
        """顺序执行任务，每个任务后进行审查"""
        results = []

        for task in tasks:
            dispatcher.logger.info(f"[顺序执行] 开始任务: {task.name}")

            # 执行任务
            result = await dispatcher._execute_single_task(task)
            results.append(result)

            # 代码审查
            if result.status == TaskStatus.COMPLETED:
                dispatcher.logger.info(f"[顺序执行] 审查任务: {task.name}")
                review = await dispatcher._review_result(result, task)

                # 应用审查反馈
                if review and review.issues:
                    critical_issues = [i for i in review.issues if i.severity == Severity.CRITICAL]
                    if critical_issues:
                        dispatcher.logger.warning(f"[顺序执行] 发现 {len(critical_issues)} 个关键问题，修复中...")
                        # 修复关键问题
                        result = await dispatcher._fix_issues(result, critical_issues, task)

            dispatcher.logger.info(f"[顺序执行] 任务完成: {task.name}")

        return results


class ParallelStrategy(ExecutionStrategy):
    """并行执行策略"""

    async def execute(
        self,
        tasks: List[Task],
        dispatcher: 'Dispatcher'
    ) -> List[SubAgentResult]:
        """并行执行独立任务，最后统一审查"""
        dispatcher.logger.info(f"[并行执行] 启动 {len(tasks)} 个子代理")

        # 启动所有子代理
        tasks_and_agents = []
        for task in tasks:
            agent_future = asyncio.create_task(
                dispatcher._execute_single_task(task)
            )
            tasks_and_agents.append((task, agent_future))

        # 等待所有任务完成
        results = []
        for task, future in tasks_and_agents:
            try:
                result = await asyncio.wait_for(future, timeout=300)  # 5分钟超时
                results.append(result)
            except asyncio.TimeoutError:
                dispatcher.logger.error(f"[并行执行] 任务超时: {task.name}")
                results.append(SubAgentResult(
                    task_id=task.id,
                    agent_id=f"timeout-{task.id}",
                    status=TaskStatus.FAILED,
                    output="执行超时"
                ))

        # 批量审查
        dispatcher.logger.info(f"[并行执行] 批量审查 {len(results)} 个结果")
        review = await dispatcher._batch_review(results, tasks)

        return results


# ==================== 调度器 ====================

class Dispatcher:
    """子代理调度器"""

    def __init__(
        self,
        model_selector: Optional[ModelSelector] = None,
        reviewer: Optional['CodeReviewer'] = None,
        strategy: ExecutionStrategy = None,
        enable_review: bool = True
    ):
        self.model_selector = model_selector or ModelSelector()
        self.reviewer = reviewer or (create_reviewer() if enable_review else None)
        self.strategy = strategy or SequentialStrategy()
        self.enable_review = enable_review
        self.logger = logging.getLogger("dispatcher")

    async def execute(
        self,
        tasks: List[Task],
        mode: str = "sequential"  # sequential or parallel
    ) -> List[SubAgentResult]:
        """
        执行任务列表

        Args:
            tasks: 任务列表
            mode: 执行模式

        Returns:
            执行结果列表
        """
        self.logger.info(f"[调度器] 开始执行 {len(tasks)} 个任务，模式: {mode}")

        # 按优先级和依赖排序
        sorted_tasks = self._sort_tasks(tasks)

        # 选择策略
        if mode == "parallel":
            strategy = ParallelStrategy()
        else:
            strategy = SequentialStrategy()

        # 执行
        results = await strategy.execute(sorted_tasks, self)

        self.logger.info(f"[调度器] 执行完成: {len(results)} 个结果")
        return results

    async def _execute_single_task(self, task: Task) -> SubAgentResult:
        """执行单个任务"""
        start_time = datetime.now()

        # 选择模型和代理
        model = self.model_selector.select_model(
            task.task_type,
            task.complexity
        )
        agent_type = self.model_selector.get_agent_for_task(task)

        self.logger.info(
            f"[任务 {task.id}] 模型: {model}, 代理: {agent_type}"
        )

        # 更新任务状态
        task.status = TaskStatus.IN_PROGRESS

        # TODO: 实际调用子代理
        # 这里需要集成到实际的 LLM 调用
        result = SubAgentResult(
            task_id=task.id,
            agent_id=f"{agent_type}-{task.id}",
            status=TaskStatus.COMPLETED,
            output=f"任务 {task.name} 已完成",
            execution_time=(datetime.now() - start_time).total_seconds()
        )

        task.status = TaskStatus.COMPLETED
        task.result = result

        return result

    async def _review_result(
        self,
        result: SubAgentResult,
        task: Task
    ) -> Optional['CodeReview']:
        """审查单个结果"""
        if not self.reviewer:
            return None

        self.logger.info(f"[审查] 审查任务: {task.name}")

        # 读取变更的文件
        code_to_review = ""
        for file_path in result.files_changed:
            try:
                full_path = Path(task.directory) / file_path if task.directory else Path(file_path)
                if full_path.exists():
                    code_to_review += f"\n# --- {file_path} ---\n"
                    code_to_review += full_path.read_text(encoding='utf-8')
            except Exception as e:
                self.logger.warning(f"[审查] 无法读取文件 {file_path}: {e}")

        # 如果没有代码，审查输出
        if not code_to_review:
            code_to_review = result.output

        # 执行审查
        review = await self.reviewer.review(
            code=code_to_review,
            file_path=task.files[0] if task.files else "",
            task_id=task.id
        )

        return review

    async def _batch_review(
        self,
        results: List[SubAgentResult],
        tasks: List[Task]
    ) -> Optional['CodeReview']:
        """批量审查结果"""
        if not self.reviewer:
            return None

        self.logger.info(f"[批量审查] 审查 {len(results)} 个结果")

        # 准备批量审查的代码
        code_items = []
        for result, task in zip(results, tasks):
            code_to_review = ""

            # 读取变更的文件
            for file_path in result.files_changed:
                try:
                    full_path = Path(task.directory) / file_path if task.directory else Path(file_path)
                    if full_path.exists():
                        code_to_review += f"\n# --- {file_path} ---\n"
                        code_to_review += full_path.read_text(encoding='utf-8')
                except Exception as e:
                    self.logger.warning(f"[批量审查] 无法读取文件 {file_path}: {e}")

            # 如果没有代码，使用输出
            if not code_to_review:
                code_to_review = result.output

            code_items.append({
                "code": code_to_review,
                "file_path": task.files[0] if task.files else "",
                "task_id": task.id
            })

        # 执行批量审查
        reviews = await self.reviewer.review_batch(code_items)

        # 合并审查结果
        if reviews:
            merged_review = reviews[0]
            for review in reviews[1:]:
                merged_review.issues.extend(review.issues)
                merged_review.strengths.extend(review.strengths)
            return merged_review

        return None

    async def _fix_issues(
        self,
        result: SubAgentResult,
        issues: List[CodeReviewIssue],
        task: Task
    ) -> SubAgentResult:
        """修复关键问题"""
        self.logger.info(f"[修复] 修复 {len(issues)} 个关键问题")

        # TODO: 实现修复逻辑
        return result

    def _sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """排序任务（优先级和依赖）"""
        # 按优先级排序
        priority_sorted = sorted(tasks, key=lambda t: t.priority)

        # 简单的依赖处理
        sorted_tasks = []
        processed = set()

        for task in priority_sorted:
            if task.id in processed:
                continue

            # 检查依赖
            can_add = all(dep in processed for dep in task.dependencies)
            if can_add:
                sorted_tasks.append(task)
                processed.add(task.id)

        return sorted_tasks


# ==================== 工厂函数 ====================

def create_dispatcher(
    mode: str = "sequential",
    model_selector: Optional[ModelSelector] = None
) -> Dispatcher:
    """
    创建调度器

    Args:
        mode: 执行模式 (sequential/parallel)
        model_selector: 模型选择器

    Returns:
        Dispatcher 实例
    """
    strategy = SequentialStrategy() if mode == "sequential" else ParallelStrategy()
    return Dispatcher(model_selector=model_selector, strategy=strategy)


def create_task(
    task_id: str,
    name: str,
    description: str,
    requirements: str,
    **kwargs
) -> Task:
    """便捷创建任务"""
    return Task(
        id=task_id,
        name=name,
        description=description,
        requirements=requirements,
        **kwargs
    )


# ==================== 示例使用 ====================

if __name__ == "__main__":
    import asyncio

    async def main():
        # 创建任务列表
        tasks = [
            create_task(
                task_id="task-1",
                name="实现用户认证功能",
                description="使用 JWT 实现用户登录和注册",
                requirements="""
                1. 实现 /auth/login 端点
                2. 实现 /auth/register 端点
                3. 使用 JWT token 机制
                4. 添加密码加密
                """,
                directory="src/auth",
                files=["auth.py", "models.py"],
                priority=1,
                complexity="high",
                task_type="development"
            ),
            create_task(
                task_id="task-2",
                name="编写用户认证测试",
                description="为认证功能编写单元测试",
                requirements="""
                1. 测试登录接口
                2. 测试注册接口
                3. 测试 JWT 验证
                4. 测试错误处理
                """,
                directory="tests/test_auth.py",
                files=["test_auth.py"],
                priority=2,
                complexity="medium",
                task_type="testing",
                dependencies=["task-1"]  # 依赖任务 1
            ),
            create_task(
                task_id="task-3",
                name="编写 API 文档",
                description="为认证 API 编写文档",
                requirements="""
                1. 使用 Swagger 格式
                2. 包含请求/响应示例
                3. 添加认证说明
                """,
                directory="docs/api",
                files=["auth_api.md"],
                priority=3,
                complexity="low",
                task_type="documentation"
            ),
        ]

        # 创建调度器
        dispatcher = create_dispatcher(mode="sequential")

        # 执行任务
        results = await dispatcher.execute(tasks, mode="sequential")

        # 输出结果
        print("\n=== 执行结果 ===")
        for result in results:
            print(f"\n任务 {result.task_id}:")
            print(f"  状态: {result.status.value}")
            print(f"  输出: {result.output[:100]}...")
            print(f"  执行时间: {result.execution_time:.2f}秒")

    # 运行示例
    asyncio.run(main())
