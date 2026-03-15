"""
Agent Army - Agent集成管理器 v2.0
使用统一配置（model_config_v2.py）
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import time
from enum import Enum
from dataclasses import dataclass
from queue import Queue

# 导入v2配置
from src.core.config.model_config_v2 import (
    get_model_name,
    get_model_config,
    get_all_agents_by_model,
    group_agents_by_model
)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


class AgentStatus(Enum):
    """Agent状态"""
    IDLE = "idle"            # 空闲
    BUSY = "busy"            # 忙碌
    ERROR = "error"          # 错误
    OFFLINE = "offline"      # 离线


@dataclass
class AgentTask:
    """Agent任务"""
    task_id: str
    task_type: str
    stock_code: str
    agents: List[str]
    status: TaskStatus
    progress: float  # 0-100
    result: Optional[Dict] = None
    error: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class AgentManager:
    """Agent管理器 v2.0"""

    # 24个标准Agent定义
    ALL_AGENTS = {
        # 产业分析军团（5个）
        "macro_economic": {
            "name": "宏观经济AI",
            "army": "产业分析军团",
            "description": "分析GDP、CPI、PMI等宏观经济指标",
            "status": AgentStatus.IDLE
        },
        "industry_chain": {
            "name": "产业链分析AI",
            "army": "产业分析军团",
            "description": "分析产业链上下游关系",
            "status": AgentStatus.IDLE
        },
        "policy_impact": {
            "name": "政策影响AI",
            "army": "产业分析军团",
            "description": "评估政策对行业的影响",
            "status": AgentStatus.IDLE
        },
        "industry_cycle": {
            "name": "行业周期AI",
            "army": "产业分析军团",
            "description": "判断行业所处周期阶段",
            "status": AgentStatus.IDLE
        },
        "competitive_landscape": {
            "name": "竞争格局AI",
            "army": "产业分析军团",
            "description": "分析行业竞争格局",
            "status": AgentStatus.IDLE
        },

        # 热点捕捉军团（4个）
        "news_monitor": {
            "name": "新闻监控AI",
            "army": "热点捕捉军团",
            "description": "实时监控市场新闻和舆情",
            "status": AgentStatus.IDLE
        },
        "capital_flow": {
            "name": "资金流向AI",
            "army": "热点捕捉军团",
            "description": "追踪主力资金流向",
            "status": AgentStatus.IDLE
        },
        "market_sentiment": {
            "name": "市场情绪AI",
            "army": "热点捕捉军团",
            "description": "分析市场情绪和恐惧贪婪指数",
            "status": AgentStatus.IDLE
        },
        "hot_sector": {
            "name": "热点板块AI",
            "army": "热点捕捉军团",
            "description": "识别热点板块和龙头股",
            "status": AgentStatus.IDLE
        },

        # 个股挖掘军团（4个）
        "financial_health": {
            "name": "财务健康AI",
            "army": "个股挖掘军团",
            "description": "评估公司财务健康状况",
            "status": AgentStatus.IDLE
        },
        "growth_analysis": {
            "name": "成长性分析AI",
            "army": "个股挖掘军团",
            "description": "分析公司成长性",
            "status": AgentStatus.IDLE
        },
        "valuation_ai": {
            "name": "估值AI",
            "army": "个股挖掘军团",
            "description": "评估股票估值水平",
            "status": AgentStatus.IDLE
        },
        "technical_analysis": {
            "name": "技术分析AI",
            "army": "个股挖掘军团",
            "description": "技术指标分析",
            "status": AgentStatus.IDLE
        },

        # 目标预测军团（4个）
        "price_prediction": {
            "name": "价格预测AI",
            "army": "目标预测军团",
            "description": "预测股票价格走势",
            "status": AgentStatus.IDLE
        },
        "earnings_forecast": {
            "name": "业绩预测AI",
            "army": "目标预测军团",
            "description": "预测公司业绩",
            "status": AgentStatus.IDLE
        },
        "risk_assessment": {
            "name": "风险评估AI",
            "army": "目标预测军团",
            "description": "评估投资风险",
            "status": AgentStatus.IDLE
        },
        "trend_analysis": {
            "name": "趋势分析AI",
            "army": "目标预测军团",
            "description": "分析股票趋势",
            "status": AgentStatus.IDLE
        },

        # 策略执行军团（4个）
        "asset_allocation": {
            "name": "资产配置AI",
            "army": "策略执行军团",
            "description": "制定资产配置策略",
            "status": AgentStatus.IDLE
        },
        "timing_strategy": {
            "name": "择时策略AI",
            "army": "策略执行军团",
            "description": "判断最佳入场时机",
            "status": AgentStatus.IDLE
        },
        "position_management": {
            "name": "仓位管理AI",
            "army": "策略执行军团",
            "description": "管理仓位大小",
            "status": AgentStatus.IDLE
        },
        "stop_loss_strategy": {
            "name": "止损策略AI",
            "army": "策略执行军团",
            "description": "制定止损策略",
            "status": AgentStatus.IDLE
        },

        # 结果验证军团（3个）
        "backtesting": {
            "name": "回测验证AI",
            "army": "结果验证军团",
            "description": "策略回测验证",
            "status": AgentStatus.IDLE
        },
        "performance_attribution": {
            "name": "业绩归因AI",
            "army": "结果验证军团",
            "description": "分析业绩来源",
            "status": AgentStatus.IDLE
        },
        "model_validator": {
            "name": "模型验证AI",
            "army": "结果验证军团",
            "description": "验证模型有效性",
            "status": AgentStatus.IDLE
        }
    }

    def __init__(self):
        """初始化Agent管理器"""
        # 使用v2配置初始化
        self.agents = self._init_agents_with_model_config()
        self.task_queue = Queue()
        self.active_tasks: Dict[str, AgentTask] = {}

    def _init_agents_with_model_config(self) -> Dict[str, Dict]:
        """
        使用v2配置初始化24个Agent

        Returns:
            Agent字典 {agent_id: agent_info}
        """
        agents = {}

        for agent_id, base_info in self.ALL_AGENTS.items():
            # 从v2配置获取模型信息
            model_name = get_model_name(agent_id)
            model_config = get_model_config(agent_id)

            # 合并基础信息和模型配置
            agents[agent_id] = {
                **base_info,
                "model": model_name,
                "model_config": model_config,
                "agent_id": agent_id
            }

        return agents

    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """获取Agent信息（包含模型配置）"""
        return self.agents.get(agent_id)

    def get_all_agents(self) -> Dict[str, Dict]:
        """获取所有Agent（包含模型配置）"""
        return self.agents

    def get_agents_by_army(self, army_name: str) -> List[Dict]:
        """获取指定军团的Agent"""
        return [
            {"id": k, **v}
            for k, v in self.agents.items()
            if v["army"] == army_name
        ]

    def get_agents_by_model(self, model_name: str) -> List[Dict]:
        """获取使用指定模型的所有Agent"""
        return [
            {"id": k, **v}
            for k, v in self.agents.items()
            if v["model"] == model_name
        ]

    def update_agent_status(self, agent_id: str, status: AgentStatus):
        """更新Agent状态"""
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = status

    def create_task(
        self,
        task_type: str,
        stock_code: str,
        agents: List[str]
    ) -> AgentTask:
        """
        创建分析任务

        Args:
            task_type: 任务类型（full_analysis/industry/hot_topics/custom）
            stock_code: 股票代码
            agents: 参与的Agent ID列表

        Returns:
            AgentTask对象
        """
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            stock_code=stock_code,
            agents=agents,
            status=TaskStatus.PENDING,
            progress=0.0
        )

        # 添加到任务队列
        self.task_queue.put(task)
        self.active_tasks[task_id] = task

        # 保存到session state
        if 'task_history' not in st.session_state:
            st.session_state.task_history = []
        st.session_state.task_history.append({
            'task_id': task_id,
            'type': task_type,
            'stock_code': stock_code,
            'agents': agents,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        })

        return task

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """获取任务"""
        return self.active_tasks.get(task_id)

    def get_all_tasks(self) -> List[AgentTask]:
        """获取所有任务"""
        return list(self.active_tasks.values())

    def execute_task(self, task: AgentTask) -> Dict:
        """
        执行任务（模拟）

        Args:
            task: AgentTask对象

        Returns:
            分析结果
        """
        # 更新状态
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        task.progress = 0.0

        results = {}

        # 模拟执行每个Agent
        for i, agent_id in enumerate(task.agents):
            # 更新进度
            task.progress = (i + 1) / len(task.agents) * 100

            # 标记Agent为忙碌
            self.update_agent_status(agent_id, AgentStatus.BUSY)

            # 模拟Agent执行（实际应该调用真实Agent）
            agent_result = self._execute_agent(agent_id, task.stock_code)
            results[agent_id] = agent_result

            # 标记Agent为空闲
            self.update_agent_status(agent_id, AgentStatus.IDLE)

        # 任务完成
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.progress = 100.0
        task.result = results

        return results

    def _execute_agent(self, agent_id: str, stock_code: str) -> Dict:
        """
        执行单个Agent（模拟）

        Args:
            agent_id: Agent ID
            stock_code: 股票代码

        Returns:
            Agent分析结果
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return {"error": "Agent not found"}

        # 模拟耗时操作
        time.sleep(0.3)

        # 返回模拟结果（包含模型信息）
        return {
            "agent_id": agent_id,
            "agent_name": agent["name"],
            "army": agent["army"],
            "model_used": agent["model"],
            "stock_code": stock_code,
            "analysis": f"{agent['name']}对{stock_code}的分析结果（使用{agent['model']}）",
            "score": 85,
            "recommendation": "买入",
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat()
        }

    def get_model_statistics(self) -> Dict[str, Any]:
        """获取模型使用统计"""
        model_counts = {}
        for agent in self.agents.values():
            model = agent["model"]
            model_counts[model] = model_counts.get(model, 0) + 1

        return {
            "total_agents": len(self.agents),
            "model_distribution": model_counts
        }


# 全局Agent管理器实例
_agent_manager = None


def get_agent_manager() -> AgentManager:
    """获取全局Agent管理器实例"""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager


# 导出
__all__ = [
    'AgentManager',
    'AgentTask',
    'TaskStatus',
    'AgentStatus',
    'get_agent_manager'
]
