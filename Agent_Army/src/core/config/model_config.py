"""
Agent Army - 模型配置管理
为24个Agent分配智谱AI模型
"""

from typing import Dict, Any
from enum import Enum


class ModelTier(str, Enum):
    """模型等级"""
    OPUS_PLUS = "opus_plus"      # GLM-5
    OPUS = "opus"                # GLM-4.7
    OPUS_MINUS = "opus_minus"    # glm-4-plus
    SONNET_PLUS = "sonnet_plus"  # codegeex-4
    SONNET = "sonnet"            # glm-4-air
    HAIKU = "haiku"              # glm-4-flash


class ModelConfig:
    """模型配置"""

    # 模型映射
    MODEL_MAPPING = {
        ModelTier.OPUS_PLUS: "glm-5",
        ModelTier.OPUS: "glm-4.7",
        ModelTier.OPUS_MINUS: "glm-4-plus",
        ModelTier.SONNET_PLUS: "codegeex-4",
        ModelTier.SONNET: "glm-4-air",
        ModelTier.HAIKU: "glm-4-flash"
    }

    # 并发限制
    CONCURRENCY_LIMITS = {
        ModelTier.OPUS_PLUS: 1,
        ModelTier.OPUS: 2,
        ModelTier.OPUS_MINUS: 5,
        ModelTier.SONNET_PLUS: 10,
        ModelTier.SONNET: 100,
        ModelTier.HAIKU: 200
    }

    # 成本权重（相对于glm-4-flash）
    COST_WEIGHTS = {
        ModelTier.OPUS_PLUS: 50.0,    # 50倍
        ModelTier.OPUS: 30.0,         # 30倍
        ModelTier.OPUS_MINUS: 10.0,   # 10倍
        ModelTier.SONNET_PLUS: 5.0,   # 5倍
        ModelTier.SONNET: 2.0,        # 2倍
        ModelTier.HAIKU: 1.0          # 基准
    }

    @staticmethod
    def get_model_name(tier: ModelTier) -> str:
        """获取模型名称"""
        return ModelConfig.MODEL_MAPPING[tier]

    @staticmethod
    def get_concurrency_limit(tier: ModelTier) -> int:
        """获取并发限制"""
        return ModelConfig.CONCURRENCY_LIMITS[tier]

    @staticmethod
    def get_cost_weight(tier: ModelTier) -> float:
        """获取成本权重"""
        return ModelConfig.COST_WEIGHTS[tier]


# ========== 24个Agent的模型配置 ==========

AGENT_MODEL_CONFIG: Dict[str, Dict[str, Any]] = {
    # ========== Opus+ (GLM-5) - 战略级任务 ==========

    "asset_allocation": {
        "tier": ModelTier.OPUS_PLUS,
        "model": "glm-5",
        "temperature": 0.3,
        "max_tokens": 4000,
        "timeout": 120,
        "reason": "资产配置需要全局视野和战略决策，使用最强模型"
    },

    "backtesting": {
        "tier": ModelTier.OPUS_PLUS,
        "model": "glm-5",
        "temperature": 0.2,
        "max_tokens": 8000,
        "timeout": 180,
        "reason": "回测验证需要复杂的架构级分析，使用最强模型"
    },

    # ========== Opus (GLM-4.7) - 深度分析 ==========

    "macro_economic": {
        "tier": ModelTier.OPUS,
        "model": "glm-4.7",
        "temperature": 0.5,
        "max_tokens": 8000,
        "timeout": 90,
        "reason": "宏观经济需要处理大量长文本数据，利用1M上下文"
    },

    "price_prediction": {
        "tier": ModelTier.OPUS,
        "model": "glm-4.7",
        "temperature": 0.4,
        "max_tokens": 6000,
        "timeout": 60,
        "reason": "价格预测需要深度学习和复杂推理"
    },

    "risk_assessment": {
        "tier": ModelTier.OPUS,
        "model": "glm-4.7",
        "temperature": 0.3,
        "max_tokens": 4000,
        "timeout": 60,
        "reason": "风险评估需要综合多个风险因子，复杂计算"
    },

    "performance_attribution": {
        "tier": ModelTier.OPUS,
        "model": "glm-4.7",
        "temperature": 0.4,
        "max_tokens": 6000,
        "timeout": 90,
        "reason": "业绩归因需要深入分析，多维度推理"
    },

    # ========== Opus- (glm-4-plus) - 主力模型 ==========

    "industry_chain": {
        "tier": ModelTier.OPUS_MINUS,
        "model": "glm-4-plus",
        "temperature": 0.5,
        "max_tokens": 3000,
        "timeout": 45,
        "reason": "产业链分析是标准任务，glm-4-plus足够"
    },

    "policy_impact": {
        "tier": ModelTier.OPUS_MINUS,
        "model": "glm-4-plus",
        "temperature": 0.4,
        "max_tokens": 3000,
        "timeout": 45,
        "reason": "政策解读需要准确性，glm-4-plus稳定可靠"
    },

    "competitive_landscape": {
        "tier": ModelTier.OPUS_MINUS,
        "model": "glm-4-plus",
        "temperature": 0.5,
        "max_tokens": 3000,
        "timeout": 45,
        "reason": "竞争分析需要深度推理，glm-4-plus足够"
    },

    "financial_health": {
        "tier": ModelTier.OPUS_MINUS,
        "model": "glm-4-plus",
        "temperature": 0.3,
        "max_tokens": 3000,
        "timeout": 45,
        "reason": "财务分析是核心任务，需要稳定性"
    },

    "growth_analysis": {
        "tier": ModelTier.OPUS_MINUS,
        "model": "glm-4-plus",
        "temperature": 0.4,
        "max_tokens": 3000,
        "timeout": 45,
        "reason": "成长性分析是关键决策指标"
    },

    "earnings_forecast": {
        "tier": ModelTier.OPUS_MINUS,
        "model": "glm-4-plus",
        "temperature": 0.3,
        "max_tokens": 3000,
        "timeout": 45,
        "reason": "业绩预测需要准确性和稳定性"
    },

    "timing_strategy": {
        "tier": ModelTier.OPUS_MINUS,
        "model": "glm-4-plus",
        "temperature": 0.4,
        "max_tokens": 3000,
        "timeout": 45,
        "reason": "择时是核心策略，需要可靠性"
    },

    "position_management": {
        "tier": ModelTier.OPUS_MINUS,
        "model": "glm-4-plus",
        "temperature": 0.3,
        "max_tokens": 3000,
        "timeout": 45,
        "reason": "仓位管理需要风险控制，高可靠性"
    },

    # ========== Sonnet+ (codegeex-4) - 代码专用 ==========

    "technical_analysis": {
        "tier": ModelTier.SONNET_PLUS,
        "model": "codegeex-4",
        "temperature": 0.2,
        "max_tokens": 4000,
        "timeout": 30,
        "reason": "技术分析需要计算技术指标，代码专用模型"
    },

    "stop_loss_strategy": {
        "tier": ModelTier.SONNET_PLUS,
        "model": "codegeex-4",
        "temperature": 0.2,
        "max_tokens": 4000,
        "timeout": 30,
        "reason": "止损策略需要编写脚本和算法"
    },

    # ========== Sonnet (glm-4-air) - 高并发主力 ==========

    "news_monitor": {
        "tier": ModelTier.SONNET,
        "model": "glm-4-air",
        "temperature": 0.5,
        "max_tokens": 2000,
        "timeout": 15,
        "reason": "新闻监控需要实时性，高并发100"
    },

    "capital_flow": {
        "tier": ModelTier.SONNET,
        "model": "glm-4-air",
        "temperature": 0.4,
        "max_tokens": 2000,
        "timeout": 15,
        "reason": "资金流向监控，高频更新"
    },

    "market_sentiment": {
        "tier": ModelTier.SONNET,
        "model": "glm-4-air",
        "temperature": 0.5,
        "max_tokens": 2000,
        "timeout": 15,
        "reason": "情绪分析需要实时性，批量处理"
    },

    "hot_sector": {
        "tier": ModelTier.SONNET,
        "model": "glm-4-air",
        "temperature": 0.5,
        "max_tokens": 2000,
        "timeout": 15,
        "reason": "热点追踪需要高并发，快速响应"
    },

    "industry_cycle": {
        "tier": ModelTier.SONNET,
        "model": "glm-4-air",
        "temperature": 0.4,
        "max_tokens": 2000,
        "timeout": 15,
        "reason": "周期分析相对简单，性价比优先"
    },

    "valuation_ai": {
        "tier": ModelTier.SONNET,
        "model": "glm-4-air",
        "temperature": 0.3,
        "max_tokens": 2000,
        "timeout": 15,
        "reason": "估值计算相对标准，性价比优先"
    },

    # ========== Haiku (glm-4-flash) - 超低成本 ==========

    "trend_analysis": {
        "tier": ModelTier.HAIKU,
        "model": "glm-4-flash",
        "temperature": 0.5,
        "max_tokens": 1500,
        "timeout": 10,
        "reason": "趋势判断相对简单，快速响应优先"
    },

    "model_validator": {
        "tier": ModelTier.HAIKU,
        "model": "glm-4-flash",
        "temperature": 0.2,
        "max_tokens": 1500,
        "timeout": 10,
        "reason": "模型验证是标准化检查，不需要复杂推理"
    },
}


# ========== 统计信息 ==========

def get_model_stats():
    """获取模型使用统计"""
    stats = {
        "by_tier": {},
        "by_model": {},
        "cost_distribution": {}
    }

    for agent_id, config in AGENT_MODEL_CONFIG.items():
        tier = config["tier"]
        model = config["model"]
        cost_weight = ModelConfig.get_cost_weight(tier)

        # 按等级统计
        stats["by_tier"][tier.value] = stats["by_tier"].get(tier.value, 0) + 1

        # 按模型统计
        stats["by_model"][model] = stats["by_model"].get(model, 0) + 1

        # 成本分布
        stats["cost_distribution"][tier.value] = \
            stats["cost_distribution"].get(tier.value, 0) + cost_weight

    return stats


def get_agent_config(agent_id: str) -> Dict[str, Any]:
    """获取Agent配置"""
    if agent_id not in AGENT_MODEL_CONFIG:
        raise ValueError(f"Unknown agent: {agent_id}")
    return AGENT_MODEL_CONFIG[agent_id]


def recommend_model(task_complexity: str, urgency: str, budget: str) -> str:
    """
    根据任务特性推荐模型

    Args:
        task_complexity: 任务复杂度 (low/medium/high)
        urgency: 紧急度 (low/medium/high)
        budget: 预算 (low/medium/high)

    Returns:
        推荐的模型名称
    """
    # 决策树
    if task_complexity == "high":
        if urgency == "low" and budget == "high":
            return "glm-5"  # 复杂任务，用最强模型
        else:
            return "glm-4.7"  # 平衡速度和质量
    elif task_complexity == "medium":
        if urgency == "high":
            return "glm-4-air"  # 快速响应
        else:
            return "glm-4-plus"  # 标准任务
    else:  # low complexity
        if budget == "low":
            return "glm-4-flash"  # 最低成本
        else:
            return "glm-4-air"  # 性价比


# 导出
__all__ = [
    'ModelTier',
    'ModelConfig',
    'AGENT_MODEL_CONFIG',
    'get_model_stats',
    'get_agent_config',
    'recommend_model'
]
