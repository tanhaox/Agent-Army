"""
配置部 - Configuration Department

配置部包含2个AI Agent:
1. 资产配置AI (AssetAllocationAI) - 资产配置策略
2. 机会筛选AI (OpportunityScreeningAI) - 投资机会筛选

精简说明：
- 原有3个Agent精简为2个Agent（-33%）
- 资产配置AI = 保留独立
- 机会筛选AI = 保留独立
"""

from src.agents.business.configuration.asset_allocation_ai import (
    AssetAllocationAI,
    analyze_asset_allocation
)
from src.agents.business.configuration.opportunity_screening_ai import (
    OpportunityScreeningAI,
    analyze_opportunity_screening
)

__all__ = [
    # Agent类
    "AssetAllocationAI",
    "OpportunityScreeningAI",

    # 便捷函数
    "analyze_asset_allocation",
    "analyze_opportunity_screening"
]
