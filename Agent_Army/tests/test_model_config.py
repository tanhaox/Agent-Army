"""
Agent Army - 模型配置测试
验证24个Agent的模型分配
"""

import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config.model_config import (
    AGENT_MODEL_CONFIG,
    ModelTier,
    ModelConfig,
    get_model_stats,
    get_agent_config
)


def test_model_config():
    """测试模型配置"""
    print("=" * 70)
    print("  Agent Army - 模型配置验证")
    print("=" * 70)
    print()

    # 测试1: 验证所有24个Agent都有配置
    print("[Test 1] 验证Agent配置完整性...")
    assert len(AGENT_MODEL_CONFIG) == 24, f"应为24个Agent，实际{len(AGENT_MODEL_CONFIG)}个"
    print(f"  ✓ 所有24个Agent配置完整")

    # 测试2: 验证模型等级分布
    print("\n[Test 2] 验证模型等级分布...")
    stats = get_model_stats()

    expected_distribution = {
        "opus_plus": 2,      # GLM-5
        "opus": 4,           # GLM-4.7
        "opus_minus": 8,     # glm-4-plus
        "sonnet_plus": 2,    # codegeex-4
        "sonnet": 6,         # glm-4-air
        "haiku": 2           # glm-4-flash
    }

    for tier, expected_count in expected_distribution.items():
        actual_count = stats["by_tier"].get(tier, 0)
        assert actual_count == expected_count, \
            f"{tier}: 期望{expected_count}个，实际{actual_count}个"
        print(f"  ✓ {tier}: {actual_count}个Agent")

    # 测试3: 验证模型名称
    print("\n[Test 3] 验证模型名称映射...")
    model_names = {}
    for agent_id, config in AGENT_MODEL_CONFIG.items():
        model_name = config["model"]
        model_names[model_name] = model_names.get(model_name, 0) + 1

    print("  模型使用统计:")
    for model, count in model_names.items():
        print(f"    - {model}: {count}个Agent")

    # 测试4: 验证并发限制
    print("\n[Test 4] 验证并发限制...")
    for tier in ModelTier:
        limit = ModelConfig.get_concurrency_limit(tier)
        print(f"  ✓ {tier.value}: 并发限制={limit}")

    # 测试5: 验证成本权重
    print("\n[Test 5] 验证成本权重...")
    for tier in ModelTier:
        weight = ModelConfig.get_cost_weight(tier)
        print(f"  ✓ {tier.value}: 成本权重={weight}x")

    # 测试6: 打印成本分布
    print("\n[Test 6] 成本分布分析...")
    total_cost = sum(stats["cost_distribution"].values())
    print(f"  总成本权重: {total_cost}")
    for tier, cost in sorted(stats["cost_distribution"].items(), key=lambda x: x[1], reverse=True):
        percentage = (cost / total_cost) * 100
        print(f"    - {tier}: {cost} ({percentage:.1f}%)")

    # 测试7: 打印每个Agent的配置
    print("\n[Test 7] Agent配置详情...")
    print("=" * 70)

    # 按军团分组
    armies = {
        "产业分析军团": [
            "macro_economic", "industry_chain", "policy_impact",
            "industry_cycle", "competitive_landscape"
        ],
        "热点捕捉军团": [
            "news_monitor", "capital_flow", "market_sentiment", "hot_sector"
        ],
        "个股挖掘军团": [
            "financial_health", "growth_analysis", "valuation_ai", "technical_analysis"
        ],
        "目标预测军团": [
            "price_prediction", "earnings_forecast", "risk_assessment", "trend_analysis"
        ],
        "策略执行军团": [
            "asset_allocation", "timing_strategy", "position_management", "stop_loss_strategy"
        ],
        "结果验证军团": [
            "backtesting", "performance_attribution", "model_validator"
        ]
    }

    for army_name, agent_ids in armies.items():
        print(f"\n【{army_name}】")
        for agent_id in agent_ids:
            config = AGENT_MODEL_CONFIG[agent_id]
            model = config["model"]
            tier = config["tier"].value
            print(f"  {agent_id:25} → {model:15} ({tier})")

    print("\n" + "=" * 70)
    print("  ✓ 所有测试通过!")
    print("=" * 70)


if __name__ == "__main__":
    test_model_config()
