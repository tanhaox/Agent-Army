"""
Agent Army - 模型配置 v2.0 (包月版)
基于GLM Coding Plan Max，质量优先，简化配置
"""

from typing import Dict
from enum import Enum


class ModelType(str, Enum):
    """模型类型"""
    STRATEGIC = "strategic"  # GLM-5 战略级
    PREMIUM = "premium"      # GLM-4.7 旗舰
    CODE = "code"           # codegeex-4 代码专用


# ========== 模型配置（简化版）==========

# 默认模型：GLM-4.7（最强能力，包月无成本压力）
DEFAULT_MODEL = ModelType.PREMIUM

# 特殊Agent配置（仅4个需要特殊处理）
SPECIAL_AGENTS: Dict[str, ModelType] = {
    # 战略级Agent - 使用GLM-5
    "asset_allocation": ModelType.STRATEGIC,
    "backtesting": ModelType.STRATEGIC,

    # 代码Agent - 使用codegeex-4
    "technical_analysis": ModelType.CODE,
    "stop_loss_strategy": ModelType.CODE,
}

# 模型映射
MODEL_MAPPING = {
    ModelType.STRATEGIC: "glm-5",
    ModelType.PREMIUM: "glm-4.7",
    ModelType.CODE: "codegeex-4"
}

# 模型配置
MODEL_CONFIGS = {
    ModelType.STRATEGIC: {
        "model": "glm-5",
        "temperature": 0.3,
        "max_tokens": 8000,
        "timeout": 120,
        "reason": "战略级决策，需要最强推理能力"
    },
    ModelType.PREMIUM: {
        "model": "glm-4.7",
        "temperature": 0.5,
        "max_tokens": 8000,  # 1M上下文支持
        "timeout": 90,
        "reason": "主力模型，开源SOTA，能力最强"
    },
    ModelType.CODE: {
        "model": "codegeex-4",
        "temperature": 0.2,
        "max_tokens": 4000,
        "timeout": 30,
        "reason": "代码专用模型，编程精准"
    }
}

# 并发限制（基于GLM Coding Plan Max）
CONCURRENCY_LIMITS = {
    ModelType.STRATEGIC: 10,  # GLM-5 并发限制
    ModelType.PREMIUM: 20,    # GLM-4.7 并发限制
    ModelType.CODE: 50        # codegeex-4 并发限制
}


# ========== 核心函数 ==========

def get_model_type(agent_id: str) -> ModelType:
    """
    获取Agent使用的模型类型

    Args:
        agent_id: Agent ID

    Returns:
        模型类型
    """
    return SPECIAL_AGENTS.get(agent_id, DEFAULT_MODEL)


def get_model_name(agent_id: str) -> str:
    """
    获取Agent使用的模型名称

    Args:
        agent_id: Agent ID

    Returns:
        模型名称
    """
    model_type = get_model_type(agent_id)
    return MODEL_MAPPING[model_type]


def get_model_config(agent_id: str) -> Dict:
    """
    获取Agent的模型配置

    Args:
        agent_id: Agent ID

    Returns:
        模型配置字典
    """
    model_type = get_model_type(agent_id)
    return MODEL_CONFIGS[model_type].copy()


def get_concurrency_limit(agent_id: str) -> int:
    """
    获取Agent的并发限制

    Args:
        agent_id: Agent ID

    Returns:
        并发限制数
    """
    model_type = get_model_type(agent_id)
    return CONCURRENCY_LIMITS[model_type]


def get_all_agents_by_model(model_type: ModelType) -> list:
    """
    获取使用指定模型的所有Agent

    Args:
        model_type: 模型类型

    Returns:
        Agent ID列表
    """
    # 所有24个Agent
    all_agents = [
        # 产业分析军团
        "macro_economic", "industry_chain", "policy_impact",
        "industry_cycle", "competitive_landscape",

        # 热点捕捉军团
        "news_monitor", "capital_flow", "market_sentiment", "hot_sector",

        # 个股挖掘军团
        "financial_health", "growth_analysis", "valuation_ai",
        "technical_analysis",

        # 目标预测军团
        "price_prediction", "earnings_forecast", "risk_assessment",
        "trend_analysis",

        # 策略执行军团
        "asset_allocation", "timing_strategy", "position_management",
        "stop_loss_strategy",

        # 结果验证军团
        "backtesting", "performance_attribution", "model_validator"
    ]

    # 筛选使用指定模型的Agent
    return [
        agent_id for agent_id in all_agents
        if get_model_type(agent_id) == model_type
    ]


def get_statistics() -> Dict:
    """
    获取模型使用统计

    Returns:
        统计信息字典
    """
    all_agents = [
        # 产业分析军团
        "macro_economic", "industry_chain", "policy_impact",
        "industry_cycle", "competitive_landscape",

        # 热点捕捉军团
        "news_monitor", "capital_flow", "market_sentiment", "hot_sector",

        # 个股挖掘军团
        "financial_health", "growth_analysis", "valuation_ai",
        "technical_analysis",

        # 目标预测军团
        "price_prediction", "earnings_forecast", "risk_assessment",
        "trend_analysis",

        # 策略执行军团
        "asset_allocation", "timing_strategy", "position_management",
        "stop_loss_strategy",

        # 结果验证军团
        "backtesting", "performance_attribution", "model_validator"
    ]

    stats = {
        "by_model": {},
        "total": len(all_agents)
    }

    for agent_id in all_agents:
        model_type = get_model_type(agent_id)
        model_name = get_model_name(agent_id)

        if model_name not in stats["by_model"]:
            stats["by_model"][model_name] = {
                "type": model_type,
                "count": 0,
                "agents": []
            }

        stats["by_model"][model_name]["count"] += 1
        stats["by_model"][model_name]["agents"].append(agent_id)

    return stats


# ========== 批量操作 ==========

def get_model_for_agents(agent_ids: list) -> Dict[str, str]:
    """
    批量获取Agent使用的模型

    Args:
        agent_ids: Agent ID列表

    Returns:
        {agent_id: model_name} 字典
    """
    return {
        agent_id: get_model_name(agent_id)
        for agent_id in agent_ids
    }


def group_agents_by_model(agent_ids: list) -> Dict[str, list]:
    """
    按模型分组Agent

    Args:
        agent_ids: Agent ID列表

    Returns:
        {model_name: [agent_ids]} 字典
    """
    groups = {}

    for agent_id in agent_ids:
        model_name = get_model_name(agent_id)
        if model_name not in groups:
            groups[model_name] = []
        groups[model_name].append(agent_id)

    return groups


# ========== 导出 ==========

__all__ = [
    # 枚举
    'ModelType',

    # 配置
    'DEFAULT_MODEL',
    'SPECIAL_AGENTS',
    'MODEL_MAPPING',
    'MODEL_CONFIGS',
    'CONCURRENCY_LIMITS',

    # 核心函数
    'get_model_type',
    'get_model_name',
    'get_model_config',
    'get_concurrency_limit',
    'get_all_agents_by_model',
    'get_statistics',

    # 批量操作
    'get_model_for_agents',
    'group_agents_by_model'
]
