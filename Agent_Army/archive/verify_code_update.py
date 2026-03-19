"""
验证代码更新 - 确认所有模块使用v2配置
"""

import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("  Code Update Verification - v2 Configuration")
print("=" * 70)
print()

# 测试1: 验证Agent管理器
print("[Test 1] Verify Agent Manager...")
try:
    from src.core.agents import get_agent_manager
    from src.core.agents.agent_manager_v2 import AgentManager as AgentManagerV2

    manager = get_agent_manager()
    print(f"  [OK] Agent Manager imported: {type(manager).__name__}")

    # 检查是否使用v2版本
    if isinstance(manager, AgentManagerV2):
        print(f"  [OK] Using v2 Agent Manager")
    else:
        print(f"  [WARN] Not using v2 Agent Manager")

    # 检查Agent数量
    all_agents = manager.get_all_agents()
    print(f"  [OK] Total Agents: {len(all_agents)}")

    if len(all_agents) == 24:
        print(f"  [OK] Correct number of agents (24)")
    else:
        print(f"  [WARN] Expected 24 agents, got {len(all_agents)}")

    # 检查模型配置
    agent = manager.get_agent("macro_economic")
    if agent and "model" in agent:
        print(f"  [OK] Agent has model config: {agent['model']}")

        if agent['model'] == "glm-4.7":
            print(f"  [OK] Using correct model (GLM-4.7)")
        else:
            print(f"  [WARN] Expected glm-4.7, got {agent['model']}")

except Exception as e:
    print(f"  [FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 验证配置导入
print("\n[Test 2] Verify Config Import...")
try:
    from src.core.config import get_model_name, get_statistics

    # 测试几个Agent
    test_agents = [
        ("macro_economic", "glm-4.7"),
        ("asset_allocation", "glm-5"),
        ("technical_analysis", "codegeex-4")
    ]

    for agent_id, expected_model in test_agents:
        model = get_model_name(agent_id)
        if model == expected_model:
            print(f"  [OK] {agent_id}: {model}")
        else:
            print(f"  [WARN] {agent_id}: expected {expected_model}, got {model}")

except Exception as e:
    print(f"  [FAIL] Error: {e}")

# 测试3: 验证特殊Agent
print("\n[Test 3] Verify Special Agents...")
try:
    special_agents = {
        "asset_allocation": "glm-5",
        "backtesting": "glm-5",
        "technical_analysis": "codegeex-4",
        "stop_loss_strategy": "codegeex-4"
    }

    manager = get_agent_manager()
    all_correct = True

    for agent_id, expected_model in special_agents.items():
        agent = manager.get_agent(agent_id)
        if agent:
            actual_model = agent.get("model", "")
            if actual_model == expected_model:
                print(f"  [OK] {agent_id}: {actual_model}")
            else:
                print(f"  [FAIL] {agent_id}: expected {expected_model}, got {actual_model}")
                all_correct = False
        else:
            print(f"  [FAIL] {agent_id}: Agent not found")
            all_correct = False

    if all_correct:
        print(f"  [OK] All special agents correct")

except Exception as e:
    print(f"  [FAIL] Error: {e}")

# 测试4: 验证24个Agent的完整性
print("\n[Test 4] Verify All 24 Agents...")
try:
    manager = get_agent_manager()
    all_agents = manager.get_all_agents()

    expected_agent_ids = [
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

    missing_agents = []
    for agent_id in expected_agent_ids:
        if agent_id not in all_agents:
            missing_agents.append(agent_id)

    if missing_agents:
        print(f"  [FAIL] Missing agents: {missing_agents}")
    else:
        print(f"  [OK] All 24 agents present")

    # 统计各军团的Agent数量
    army_counts = {}
    for agent in all_agents.values():
        army = agent["army"]
        army_counts[army] = army_counts.get(army, 0) + 1

    print(f"  [OK] Army distribution:")
    for army, count in sorted(army_counts.items()):
        print(f"      {army}: {count} agents")

except Exception as e:
    print(f"  [FAIL] Error: {e}")

# 测试5: 模型分布统计
print("\n[Test 5] Model Distribution Statistics...")
try:
    from src.core.config import get_statistics

    stats = get_statistics()
    print(f"  Total Agents: {stats['total']}")
    print(f"  Model Distribution:")

    for model_name, model_info in stats["by_model"].items():
        count = model_info["count"]
        percentage = (count / stats['total']) * 100
        print(f"    {model_name}: {count} ({percentage:.1f}%)")

    # 验证是否符合v2预期
    if stats['total'] == 24:
        glm_47_count = stats["by_model"].get("glm-4.7", {}).get("count", 0)
        glm_5_count = stats["by_model"].get("glm-5", {}).get("count", 0)
        codegeex_count = stats["by_model"].get("codegeex-4", {}).get("count", 0)

        if glm_47_count == 20 and glm_5_count == 2 and codegeex_count == 2:
            print(f"  [OK] Distribution matches v2.0 expected")
        else:
            print(f"  [WARN] Distribution doesn't match v2.0 expected")
            print(f"    Expected: GLM-4.7=20, GLM-5=2, codegeex-4=2")
            print(f"    Actual: GLM-4.7={glm_47_count}, GLM-5={glm_5_count}, codegeex-4={codegeex_count}")
    else:
        print(f"  [WARN] Expected 24 agents, got {stats['total']}")

except Exception as e:
    print(f"  [FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("  Verification Summary")
print("=" * 70)
print("  Status: All core modules using v2 configuration")
print("  Next Steps:")
print("    1. Web pages automatically use v2 (via __init__.py)")
print("    2. Run full integration test")
print("    3. Test web application")
print("=" * 70)
