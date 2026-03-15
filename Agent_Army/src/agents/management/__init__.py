"""
管理层Agent（简化版）

只保留2个核心管理层Agent：
- HRAgent: 人力资源Agent（agent优化、配置管理）
- CommanderAgent: 主帅Agent（报告准确度、专业度、结果验证）

删除的角色（过度设计）：
- Strategist（战略官）→ 职责由用户和Commander承担
- Coordinator（协调官）→ 职责由Commander承担
"""

from .hr_agent import HRAgent
from .commander_agent import CommanderAgent

__all__ = [
    "HRAgent",
    "CommanderAgent",
]
