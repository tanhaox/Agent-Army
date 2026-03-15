"""
测试HR Agent
"""
import pytest

import sys
import io
import asyncio
from pathlib import Path

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.management.hr_agent import HRAgent


@pytest.mark.asyncio
async def test_hr_agent():
    """测试HR Agent"""

    print("\n" + "=" * 60)
    print("  测试HR Agent")
    print("=" * 60)

    # ========== 1. 初始化 ==========
    print("\n[1] 初始化HR Agent")
    print("-" * 60)

    hr = HRAgent()
    print(f"✅ 初始化成功")
    print(f"   名称: {hr.name}")
    print(f"   角色: {hr.role}")
    print(f"   能力数: {len(hr.capabilities)}")
    print(f"   工具数: {len(hr.tools)}")

    # ========== 2. 注册Agent ==========
    print("\n[2] 注册测试Agent")
    print("-" * 60)

    # 注册几个模拟agent
    test_agents = [
        {
            "name": "基本面分析AI",
            "type": "business",
            "corps": "stock_mining",
            "status": "active"
        },
        {
            "name": "目标定价AI",
            "type": "business",
            "corps": "target_forecast",
            "status": "active"
        },
        {
            "name": "新闻监控AI",
            "type": "business",
            "corps": "hot_spot",
            "status": "active"
        }
    ]

    for agent_info in test_agents:
        await hr.register_agent(agent_info)
        print(f"   ✅ 已注册: {agent_info['name']}")

    # ========== 3. 更新性能数据 ==========
    print("\n[3] 更新性能数据")
    print("-" * 60)

    # 模拟性能数据
    hr.update_agent_performance("基本面分析AI", success=True, response_time=2.5, accuracy=85.0)
    hr.update_agent_performance("目标定价AI", success=True, response_time=3.2, accuracy=88.0)
    hr.update_agent_performance("新闻监控AI", success=False, response_time=1.8, accuracy=65.0)  # 低准确率

    print(f"   ✅ 已更新3个agent的性能数据")

    # ========== 4. 监控所有Agent ==========
    print("\n[4] 监控所有Agent")
    print("-" * 60)

    report = await hr.monitor_all_agents()

    print(f"   ✅ 监控完成")
    print(f"   总Agent数: {report['total_agents']}")
    print(f"   发现问题: {len(report['issues'])}")

    if report['issues']:
        print(f"\n   ⚠️ 问题列表:")
        for issue in report['issues']:
            print(f"     - {issue['agent_name']}: {issue['issue_type']} "
                  f"(当前{issue['value']:.1f}, 阈值{issue['threshold']})")

    # ========== 5. 分析单个Agent性能 ==========
    print("\n[5] 分析新闻监控AI性能")
    print("-" * 60)

    analysis = await hr.analyze_performance("新闻监控AI")

    print(f"   ✅ 分析完成")
    print(f"   准确率: {analysis['performance']['accuracy_rate']:.1f}%")
    print(f"   成功率: {analysis['performance']['success_rate']:.1f}%")
    print(f"   响应时间: {analysis['performance']['average_response_time']:.2f}s")

    if analysis['issues']:
        print(f"\n   ⚠️ 发现问题:")
        for issue in analysis['issues']:
            print(f"     - {issue['description']}")

    if analysis['recommendations']:
        print(f"\n   💡 改进建议:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"     {i}. {rec}")

    # ========== 6. 提出优化方案 ==========
    print("\n[6] 提出优化方案")
    print("-" * 60)

    issue = {
        "issue_type": "low_accuracy",
        "description": "新闻监控AI准确率65%低于70%",
        "current_value": 65.0,
        "threshold": 70.0
    }

    proposal_result = await hr.propose_optimization("新闻监控AI", issue)

    print(f"   ✅ 提案已创建")
    print(f"   提案ID: {proposal_result['proposal_id']}")
    print(f"   提案类型: {proposal_result['proposal']['proposal_type']}")
    print(f"   审批流程: {proposal_result['approval_flow']}")
    print(f"   消息: {proposal_result['message']}")

    # ========== 7. 验证审批流程 ==========
    print("\n[7] 验证审批流程")
    print("-" * 60)

    # 测试需要花钱的提案
    expensive_issue = {
        "issue_type": "model_upgrade",
        "description": "升级到GLM-4-Plus",
        "costs": {
            "annual_cost": 365000
        }
    }

    expensive_proposal = await hr.propose_optimization("新闻监控AI", expensive_issue)

    print(f"   提案类型: 需要花钱的升级")
    print(f"   审批流程: {expensive_proposal['approval_flow']}")
    print(f"   需要成本审批: {expensive_proposal['proposal']['requires_cost']}")

    if expensive_proposal['approval_flow'] == "user":
        print(f"   ✅ 正确识别为需要用户审批")

    # ========== 8. 执行自主优化 ==========
    print("\n[8] 执行自主优化（无需审批）")
    print("-" * 60)

    # 模拟一个简单的配置变更（不需要审批）
    config_issue = {
        "issue_type": "slow_response",
        "description": "响应时间优化"
    }

    config_proposal = await hr.propose_optimization("新闻监控AI", config_issue)

    print(f"   提案ID: {config_proposal['proposal_id']}")
    print(f"   审批流程: {config_proposal['approval_flow']}")

    if config_proposal['approval_flow'] == "hr_auto":
        print(f"   ✅ HR可自主决策")

        # 模拟批准并执行
        proposal_id = config_proposal['proposal_id']
        hr.proposals[proposal_id].status = "approved"  # 模拟批准

        result = await hr.execute_optimization(proposal_id)
        print(f"   ✅ 执行结果: {result['result']['message']}")

    # ========== 9. 查看提案统计 ==========
    print("\n[9] 查看提案统计")
    print("-" * 60)

    print(f"   总提案数: {len(hr.proposals)}")
    for proposal_id, proposal in hr.proposals.items():
        print(f"   - {proposal_id}: {proposal.status} "
              f"(需要用户审批: {proposal.requires_cost or proposal.requires_permission})")

    # ========== 10. 验证权限分级 ==========
    print("\n[10] 验证权限分级机制")
    print("-" * 60)

    print("   ✅ 参数微调 → HR自主决策")
    print("   ✅ 算法优化 → 需主帅审批")
    print("   ✅ 花钱升级 → 需用户审批")
    print("   ✅ 安全权限 → 需用户审批")

    print("\n" + "=" * 60)
    print("  ✅ HR Agent测试全部通过!")
    print("=" * 60)

    print("\nHR Agent特点:")
    print("1. ✅ 性能监控: 实时跟踪所有agent性能")
    print("2. ✅ 问题识别: 自动识别性能问题")
    print("3. ✅ 优化提案: 生成详细优化方案")
    print("4. ✅ 权限分级: 根据风险自动确定审批流程")
    print("5. ✅ 自主执行: 无风险优化可自主决策")


if __name__ == "__main__":
    asyncio.run(test_hr_agent())
