"""
快速验证模型配置
"""

import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("  Agent Army - 模型配置快速验证")
print("=" * 70)
print()

# 导入配置
from src.core.config.model_config import (
    AGENT_MODEL_CONFIG,
    ModelTier,
    ModelConfig,
    get_model_stats
)

# 统计信息
stats = get_model_stats()

print("[模型等级分布]")
for tier, count in sorted(stats["by_tier"].items(), key=lambda x: x[1], reverse=True):
    print(f"  {tier:20} : {count:2}个Agent")

print()
print("[模型使用统计]")
for model, count in sorted(stats["by_model"].items(), key=lambda x: x[1], reverse=True):
    print(f"  {model:20} : {count:2}个Agent")

print()
print("[成本分布]")
total_cost = sum(stats["cost_distribution"].values())
for tier, cost in sorted(stats["cost_distribution"].items(), key=lambda x: x[1], reverse=True):
    percentage = (cost / total_cost) * 100
    print(f"  {tier:20} : {cost:6.1f} ({percentage:5.1f}%)")

print()
print("[24个Agent配置清单]")
print("=" * 70)

# 按等级分组
by_tier = {
    ModelTier.OPUS_PLUS: [],
    ModelTier.OPUS: [],
    ModelTier.OPUS_MINUS: [],
    ModelTier.SONNET_PLUS: [],
    ModelTier.SONNET: [],
    ModelTier.HAIKU: []
}

for agent_id, config in AGENT_MODEL_CONFIG.items():
    by_tier[config["tier"]].append(agent_id)

tier_names = {
    ModelTier.OPUS_PLUS: "Opus+ (GLM-5)",
    ModelTier.OPUS: "Opus (GLM-4.7)",
    ModelTier.OPUS_MINUS: "Opus- (glm-4-plus)",
    ModelTier.SONNET_PLUS: "Sonnet+ (codegeex-4)",
    ModelTier.SONNET: "Sonnet (glm-4-air)",
    ModelTier.HAIKU: "Haiku (glm-4-flash)"
}

for tier in [ModelTier.OPUS_PLUS, ModelTier.OPUS, ModelTier.OPUS_MINUS,
             ModelTier.SONNET_PLUS, ModelTier.SONNET, ModelTier.HAIKU]:
    agents = by_tier[tier]
    print(f"\n{tier_names[tier]} - {len(agents)} Agents")
    for agent_id in agents:
        config = AGENT_MODEL_CONFIG[agent_id]
        reason = config.get("reason", "")
        print(f"  - {agent_id:25} : {reason}")

print()
print("=" * 70)
print("  [OK] Configuration verification completed!")
print("=" * 70)
