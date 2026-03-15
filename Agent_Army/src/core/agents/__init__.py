"""
Agent Army - Agents
Agent集成模块

默认使用 v2.0 (包月版) - 质量优先，简化配置
"""

# 默认使用v2版本
from .agent_manager_v2 import (
    AgentManager,
    AgentTask,
    TaskStatus,
    AgentStatus,
    get_agent_manager
)

# 如果需要使用v1版本，请显式导入：
# from .agent_manager import ...

__all__ = [
    'AgentManager',
    'AgentTask',
    'TaskStatus',
    'AgentStatus',
    'get_agent_manager'
]
