"""
Agent Army - WebAgentAdapter
桥接Streamlit Web UI和Agent异步执行

解决Streamlit同步模型与Agent异步执行的冲突
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import get_logger
from src.core.agents.agent_manager import get_agent_manager


class WebAgentAdapter:
    """
    Web UI到Agent执行的适配器

    职责：
    1. 将Streamlit同步调用转换为async执行
    2. 提供实时进度反馈
    3. 错误处理和多级降级
    4. Session状态管理
    """

    def __init__(self):
        """初始化适配器"""
        self.logger = get_logger("web_agent_adapter")
        self.agent_manager = get_agent_manager()

        self.logger.info("WebAgentAdapter初始化完成")

    def execute_task_sync(
        self,
        task: 'AgentTask',
        progress_bar=None,
        status_text=None
    ) -> Dict[str, Any]:
        """
        同步执行Agent任务（供Streamlit调用）

        使用asyncio.run()包装async Agent.analyze()调用

        Args:
            task: AgentTask对象
            progress_bar: Streamlit进度条对象
            status_text: Streamlit状态文本对象

        Returns:
            执行结果字典
        """
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 运行async函数
            result = loop.run_until_complete(
                self._execute_task_async(task, progress_bar, status_text)
            )

            # 关闭循环
            loop.close()
            return result

        except Exception as e:
            self.logger.error(f"任务执行失败: {e}", exc_info=True)
            return self._fallback_result(task, str(e))

    async def _execute_task_async(
        self,
        task: 'AgentTask',
        progress_bar=None,
        status_text=None
    ) -> Dict[str, Any]:
        """
        异步执行任务

        Args:
            task: AgentTask对象
            progress_bar: Streamlit进度条对象
            status_text: Streamlit状态文本对象

        Returns:
            所有Agent的执行结果
        """
        # 更新任务状态
        from src.core.agents.agent_manager import TaskStatus
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        results = {}
        total_agents = len(task.agents)

        self.logger.info(f"开始执行任务 {task.task_id}")
        self.logger.info(f"股票代码: {task.stock_code}")
        self.logger.info(f"Agent数量: {total_agents}")

        for idx, agent_id in enumerate(task.agents):
            # 更新进度
            progress = (idx + 1) / total_agents
            if progress_bar:
                progress_bar.progress(progress)
            if status_text:
                status_text.text(f"正在执行 {agent_id} ({idx+1}/{total_agents})...")

            # 执行Agent
            self.logger.info(f"[{idx+1}/{total_agents}] 执行 {agent_id}")
            agent_result = await self._execute_single_agent(agent_id, task.stock_code)
            results[agent_id] = agent_result

            # 更新任务进度
            task.progress = progress * 100

        # 任务完成
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.progress = 100.0
        task.result = results

        self.logger.info(f"任务 {task.task_id} 执行完成")

        return results

    async def _execute_single_agent(
        self,
        agent_id: str,
        stock_code: str
    ) -> Dict[str, Any]:
        """
        执行单个Agent

        Args:
            agent_id: Agent ID
            stock_code: 股票代码

        Returns:
            Agent分析结果
        """
        try:
            # 获取真实Agent实例
            agent = self.agent_manager.get_agent_instance(agent_id)
            if not agent:
                self.logger.warning(f"Agent {agent_id} 未找到")
                return self._error_result(agent_id, "Agent未找到")

            # 调用Agent的analyze方法
            self.logger.info(f"调用 Agent {agent_id}.analyze({stock_code})")
            result = await agent.analyze(stock_code)

            # 转换为字典格式
            if hasattr(result, 'model_dump'):
                return result.model_dump()
            elif hasattr(result, 'dict'):
                return result.dict()
            else:
                return result

        except Exception as e:
            self.logger.error(f"Agent {agent_id} 执行失败: {e}", exc_info=True)
            return self._error_result(agent_id, str(e))

    def _error_result(self, agent_id: str, error_msg: str) -> Dict:
        """
        生成错误结果

        Args:
            agent_id: Agent ID
            error_msg: 错误消息

        Returns:
            错误结果字典
        """
        return {
            "agent_name": agent_id,
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }

    def _fallback_result(self, task: 'AgentTask', error_msg: str) -> Dict:
        """
        生成降级结果（确保用户总能看到结果）

        Args:
            task: AgentTask对象
            error_msg: 错误消息

        Returns:
            降级结果字典
        """
        return {
            "task_id": task.task_id,
            "status": "failed",
            "error": error_msg,
            "message": "分析执行失败，请稍后重试",
            "timestamp": datetime.now().isoformat()
        }


# 导出
__all__ = ['WebAgentAdapter']
