"""
Agent Army - Agent基类
所有Agent的基类,提供通用功能
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .logger import LoggerMixin, get_logger


class AgentState(BaseModel):
    """
    Agent状态
    """
    name: str
    role: str
    status: str = "idle"  # idle, busy, error
    current_task: Optional[str] = None
    completed_tasks: int = 0
    failed_tasks: int = 0


class AgentCapability(BaseModel):
    """
    Agent能力
    """
    name: str
    description: str
    enabled: bool = True


class AgentTool(BaseModel):
    """
    Agent工具
    """
    name: str
    description: str
    enabled: bool = True


class BaseAgent(ABC, LoggerMixin):
    """
    Agent基类
    所有Agent必须继承此类
    """

    def __init__(
        self,
        name: str,
        role: str,
        capabilities: Optional[List[AgentCapability]] = None,
        tools: Optional[List[AgentTool]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化Agent

        Args:
            name: Agent名称
            role: Agent角色
            capabilities: Agent能力列表
            tools: Agent工具列表
            config: Agent配置
        """
        self.name = name
        self.role = role
        self.capabilities = capabilities or []
        self.tools = tools or []
        self.config = config or {}

        # 初始化状态
        self.state = AgentState(
            name=name,
            role=role
        )

        self.logger.info(f"Agent初始化完成", agent=name, role=role)

    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Any:
        """
        执行任务(抽象方法,子类必须实现)

        Args:
            task: 任务描述
            **kwargs: 任务参数

        Returns:
            执行结果
        """
        pass

    async def run(self, task: str, **kwargs) -> Any:
        """
        运行Agent(带状态管理)

        Args:
            task: 任务描述
            **kwargs: 任务参数

        Returns:
            执行结果
        """
        try:
            # 更新状态为忙碌
            self.state.status = "busy"
            self.state.current_task = task

            self.logger.info(f"开始执行任务", agent=self.name, task=task)

            # 执行任务
            result = await self.execute(task, **kwargs)

            # 更新状态为空闲
            self.state.status = "idle"
            self.state.current_task = None
            self.state.completed_tasks += 1

            self.logger.info(
                f"任务执行成功",
                agent=self.name,
                task=task,
                completed=self.state.completed_tasks
            )

            return result

        except Exception as e:
            # 更新状态为错误
            self.state.status = "error"
            self.state.failed_tasks += 1

            self.logger.error(
                f"任务执行失败",
                agent=self.name,
                task=task,
                error=str(e),
                failed=self.state.failed_tasks
            )
            raise

    def get_capabilities(self) -> List[AgentCapability]:
        """
        获取Agent能力列表

        Returns:
            能力列表
        """
        return [cap for cap in self.capabilities if cap.enabled]

    def get_tools(self) -> List[AgentTool]:
        """
        获取Agent工具列表

        Returns:
            工具列表
        """
        return [tool for tool in self.tools if tool.enabled]

    def get_state(self) -> AgentState:
        """
        获取Agent状态

        Returns:
            Agent状态
        """
        return self.state

    def reset_state(self) -> None:
        """重置Agent状态"""
        self.state.status = "idle"
        self.state.current_task = None
        self.logger.info(f"Agent状态已重置", agent=self.name)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, role={self.role})>"
