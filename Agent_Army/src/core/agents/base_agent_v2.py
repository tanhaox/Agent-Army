"""
Agent Army - Agent基类 v2.0 (包月版)
简化版Agent基类，使用统一的model_config_v2
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import time

# 使用v2配置
from src.core.config.model_config_v2 import (
    ModelType,
    get_model_name,
    get_model_config,
    get_concurrency_limit
)


class BaseAgent(ABC):
    """Agent基类 (v2.0 简化版)"""

    # 所有24个Agent的定义
    ALL_AGENTS = {
        # 产业分析军团
        "macro_economic": {
            "name": "宏观经济AI",
            "army": "产业分析军团",
            "description": "分析宏观经济环境对股票的影响"
        },
        "industry_chain": {
            "name": "产业链分析AI",
            "army": "产业分析军团",
            "description": "分析产业链上下游关系"
        },
        "policy_impact": {
            "name": "政策影响AI",
            "army": "产业分析军团",
            "description": "分析政策对行业的影响"
        },
        "industry_cycle": {
            "name": "行业周期AI",
            "army": "产业分析军团",
            "description": "判断行业所处周期阶段"
        },
        "competitive_landscape": {
            "name": "竞争格局AI",
            "army": "产业分析军团",
            "description": "分析行业竞争格局"
        },

        # 热点捕捉军团
        "news_monitor": {
            "name": "新闻监控AI",
            "army": "热点捕捉军团",
            "description": "实时监控相关新闻"
        },
        "capital_flow": {
            "name": "资金流向AI",
            "army": "热点捕捉军团",
            "description": "分析资金流向数据"
        },
        "market_sentiment": {
            "name": "市场情绪AI",
            "army": "热点捕捉军团",
            "description": "分析市场情绪指标"
        },
        "hot_sector": {
            "name": "热点板块AI",
            "army": "热点捕捉军团",
            "description": "追踪市场热点板块"
        },

        # 个股挖掘军团
        "financial_health": {
            "name": "财务健康AI",
            "army": "个股挖掘军团",
            "description": "评估公司财务健康状况"
        },
        "growth_analysis": {
            "name": "成长性分析AI",
            "army": "个股挖掘军团",
            "description": "分析公司成长性"
        },
        "valuation_ai": {
            "name": "估值AI",
            "army": "个股挖掘军团",
            "description": "进行公司估值分析"
        },
        "technical_analysis": {
            "name": "技术分析AI",
            "army": "个股挖掘军团",
            "description": "进行技术指标分析"
        },

        # 目标预测军团
        "price_prediction": {
            "name": "价格预测AI",
            "army": "目标预测军团",
            "description": "预测股票价格走势"
        },
        "earnings_forecast": {
            "name": "业绩预测AI",
            "army": "目标预测军团",
            "description": "预测公司业绩"
        },
        "risk_assessment": {
            "name": "风险评估AI",
            "army": "目标预测军团",
            "description": "评估投资风险"
        },
        "trend_analysis": {
            "name": "趋势分析AI",
            "army": "目标预测军团",
            "description": "分析股票趋势"
        },

        # 策略执行军团
        "asset_allocation": {
            "name": "资产配置AI",
            "army": "策略执行军团",
            "description": "制定资产配置策略"
        },
        "timing_strategy": {
            "name": "择时策略AI",
            "army": "策略执行军团",
            "description": "制定择时策略"
        },
        "position_management": {
            "name": "仓位管理AI",
            "army": "策略执行军团",
            "description": "管理仓位"
        },
        "stop_loss_strategy": {
            "name": "止损策略AI",
            "army": "策略执行军团",
            "description": "制定止损策略"
        },

        # 结果验证军团
        "backtesting": {
            "name": "回测验证AI",
            "army": "结果验证军团",
            "description": "进行策略回测"
        },
        "performance_attribution": {
            "name": "业绩归因AI",
            "army": "结果验证军团",
            "description": "分析业绩来源"
        },
        "model_validator": {
            "name": "模型验证AI",
            "army": "结果验证军团",
            "description": "验证模型有效性"
        }
    }

    def __init__(self, agent_id: str):
        """
        初始化Agent

        Args:
            agent_id: Agent ID
        """
        if agent_id not in self.ALL_AGENTS:
            raise ValueError(f"Unknown agent_id: {agent_id}")

        self.agent_id = agent_id
        self.agent_info = self.ALL_AGENTS[agent_id]

        # 从v2配置获取模型信息
        self.model_name = get_model_name(agent_id)
        self.model_config = get_model_config(agent_id)
        self.concurrency_limit = get_concurrency_limit(agent_id)

        # Agent状态
        self.status = "idle"
        self.last_used = None

    @property
    def name(self) -> str:
        """Agent名称"""
        return self.agent_info["name"]

    @property
    def army(self) -> str:
        """所属军团"""
        return self.agent_info["army"]

    @property
    def description(self) -> str:
        """Agent描述"""
        return self.agent_info["description"]

    @abstractmethod
    async def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """
        执行分析（抽象方法，子类实现）

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数

        Returns:
            分析结果字典
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "army": self.army,
            "description": self.description,
            "model": self.model_name,
            "model_config": self.model_config,
            "status": self.status,
            "concurrency_limit": self.concurrency_limit
        }

    def __repr__(self) -> str:
        return f"<{self.name} ({self.agent_id})>"


class SimpleAgent(BaseAgent):
    """简单Agent实现（用于测试和演示）"""

    async def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """
        执行分析（模拟实现）

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数

        Returns:
            分析结果字典
        """
        start_time = time.time()
        self.status = "busy"

        try:
            # 模拟分析过程
            await asyncio.sleep(0.5)  # 模拟API调用

            result = {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "army": self.army,
                "stock_code": stock_code,
                "model_used": self.model_name,
                "score": 85,
                "recommendation": "买入",
                "confidence": 0.85,
                "analysis": f"基于{self.name}对{stock_code}的分析...",
                "timestamp": datetime.now().isoformat(),
                "execution_time": time.time() - start_time
            }

            self.status = "idle"
            self.last_used = datetime.now()

            return result

        except Exception as e:
            self.status = "error"
            return {
                "agent_id": self.agent_id,
                "stock_code": stock_code,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Agent工厂
def create_agent(agent_id: str) -> BaseAgent:
    """
    创建Agent实例

    Args:
        agent_id: Agent ID

    Returns:
        Agent实例
    """
    return SimpleAgent(agent_id)


# 获取所有Agent信息
def get_all_agents_info() -> Dict[str, Dict[str, Any]]:
    """获取所有Agent的信息"""
    return BaseAgent.ALL_AGENTS.copy()


# 按军团分组
def get_agents_by_army() -> Dict[str, list]:
    """按军团分组Agent"""
    armies = {}

    for agent_id, info in BaseAgent.ALL_AGENTS.items():
        army_name = info["army"]
        if army_name not in armies:
            armies[army_name] = []
        armies[army_name].append({
            "id": agent_id,
            **info
        })

    return armies


# 导入asyncio（用于SimpleAgent）
import asyncio


# 导出
__all__ = [
    'BaseAgent',
    'SimpleAgent',
    'create_agent',
    'get_all_agents_info',
    'get_agents_by_army'
]
