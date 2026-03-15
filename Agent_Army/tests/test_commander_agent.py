"""
Commander Agent 测试

测试Commander的核心功能：
1. 报告汇总和质量检查
2. 报告拒绝和重试机制
3. HR升级机制（3次失败后）
4. 汇总报告生成
"""
import pytest

import sys
import os
from pathlib import Path

# Windows控制台UTF-8编码支持
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    os.system('chcp 65001 > nul 2>&1')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from datetime import datetime, timedelta
from src.agents.management.commander_agent import CommanderAgent, ReportRecord


@pytest.mark.asyncio
async def test_commander_initialization():
    """测试1：Commander初始化"""
    print("\n" + "="*60)
    print("测试1：Commander初始化")
    print("="*60)

    commander = CommanderAgent()

    print(f"✅ Commander名称: {commander.name}")
    print(f"✅ Commander角色: {commander.role}")
    print(f"✅ 能力数量: {len(commander.capabilities)}")
    print(f"✅ 工具数量: {len(commander.tools)}")

    # 检查核心能力
    capability_names = [cap.name for cap in commander.capabilities]
    assert "report_tracking" in capability_names, "缺少报告跟踪能力"
    assert "result_verification" in capability_names, "缺少结果验证能力"
    assert "accuracy_assessment" in capability_names, "缺少准确度评估能力"

    print("✅ 初始化测试通过")


@pytest.mark.asyncio
async def test_report_quality_check():
    """测试2：报告质量检查"""
    print("\n" + "="*60)
    print("测试2：报告质量检查")
    print("="*60)

    commander = CommanderAgent()

    # 模拟不同质量的报告
    reports = [
        {
            "report_id": "RPT-001",
            "agent_name": "基本面分析AI",
            "stock_code": "600519",
            "analysis": "贵州茅台基本面优秀，ROE持续保持在25%以上，品牌护城河深厚，现金流充裕。未来3年预计保持15%的稳健增长。当前估值合理，具有较高安全边际，技术面显示突破信号，成交量放大。综合判断，强烈推荐买入，目标价2200元。",  # 123字
            "recommendation": "STRONG_BUY",  # 使用标准格式
            "timestamp": datetime.now().isoformat(),
            "predictions": [
                {
                    "type": "target_price",
                    "value": 2200,
                    "timeframe": "3个月"
                }
            ]
        },
        {
            "report_id": "RPT-002",
            "agent_name": "新闻监控AI",
            "stock_code": "000858",
            "analysis": "短期利空",  # 太短
            "recommendation": "HOLD",  # 使用标准格式
            "timestamp": datetime.now().isoformat()
        },
        {
            "report_id": "RPT-003",
            "agent_name": "技术分析AI",
            "stock_code": "000001",
            # 缺少 analysis 字段
            "recommendation": "BUY",  # 使用标准格式
            "timestamp": datetime.now().isoformat()
        }
    ]

    # 汇总和检查报告
    result = await commander.execute(
        "collect_and_review_reports",
        reports=reports
    )

    print(f"\n📊 汇总结果:")
    print(f"   总报告数: {result['summary']['total_reports']}")
    print(f"   ✅ 通过质检: {len(result['summary']['approved_reports'])}份")
    print(f"   ❌ 需要重做: {len(result['summary']['rejected_reports'])}份")

    # 查看被拒绝的报告
    if result['summary']['rejected_reports']:
        print(f"\n❌ 被拒绝的报告:")
        for rejected in result['summary']['rejected_reports']:
            print(f"   - {rejected['report_id']} ({rejected['agent_name']}):")
            print(f"     问题: {', '.join(rejected['issues'])}")

    # 验证结果
    assert result['summary']['total_reports'] == 3, "报告总数不对"
    assert len(result['summary']['approved_reports']) >= 1, "应该有至少1份通过"
    assert len(result['summary']['rejected_reports']) >= 2, "应该有至少2份被拒绝"

    print("\n✅ 质量检查测试通过")


@pytest.mark.asyncio
async def test_report_rejection_and_retry():
    """测试3：报告拒绝和重试机制"""
    print("\n" + "="*60)
    print("测试3：报告拒绝和重试机制")
    print("="*60)

    commander = CommanderAgent()

    # 模拟一份质量差的报告
    bad_report = {
        "report_id": "RPT-BAD-001",
        "agent_name": "测试AI",
        "stock_code": "600000",
        "analysis": "分析太短",
        "recommendation": "HOLD",  # 使用标准格式
        "timestamp": datetime.now().isoformat()
    }

    # 第1次拒绝
    print("\n🔄 第1次拒绝:")
    result1 = await commander.execute(
        "reject_report",
        report=bad_report,
        reason="分析内容过短，不够详细",
        retry_count=0
    )
    print(f"   动作: {result1['action']}")
    print(f"   重试次数: {result1['retry_count']}")
    print(f"   改进要求: {result1['requirements']}")

    assert result1['action'] == "reject_and_retry", "应该是拒绝并重试"
    assert result1['retry_count'] == 1, "重试次数应该是1"

    # 第2次拒绝
    print("\n🔄 第2次拒绝:")
    result2 = await commander.execute(
        "reject_report",
        report=bad_report,
        reason="分析仍然不够详细",
        retry_count=1
    )
    print(f"   重试次数: {result2['retry_count']}")
    assert result2['retry_count'] == 2, "重试次数应该是2"

    # 第3次拒绝
    print("\n🔄 第3次拒绝:")
    result3 = await commander.execute(
        "reject_report",
        report=bad_report,
        reason="质量持续不合格",
        retry_count=2
    )
    print(f"   重试次数: {result3['retry_count']}")
    assert result3['retry_count'] == 3, "重试次数应该是3"

    # 第4次拒绝（应该触发HR）
    print("\n🔄 第4次拒绝（应该触发HR）:")
    result4 = await commander.execute(
        "reject_report",
        report=bad_report,
        reason="质量持续不合格",
        retry_count=3
    )
    print(f"   动作: {result4['action']}")
    print(f"   消息: {result4.get('message', 'N/A')}")

    assert result4['action'] == "call_hr", "第4次应该叫HR"
    print("\n✅ 拒绝和重试机制测试通过")


@pytest.mark.asyncio
async def test_call_hr_for_help():
    """测试4：调用HR优化AI"""
    print("\n" + "="*60)
    print("测试4：调用HR优化AI")
    print("="*60)

    commander = CommanderAgent()

    # 模拟调用HR
    result = await commander.execute(
        "call_hr_for_help",
        agent_name="基本面分析AI",
        issue={
            "issue_type": "low_quality",
            "description": "连续3次报告质量不合格",
            "retry_count": 3
        }
    )

    print(f"\n🤖 HR调用结果:")
    print(f"   动作: {result['action']}")
    print(f"   消息: {result['message']}")
    print(f"   下一步:")
    for step in result['next_steps']:
        print(f"      - {step}")

    assert result['action'] == "call_hr", "应该是调用HR"
    assert "hr_request" in result, "应该有HR请求"
    assert "request_id" in result['hr_request'], "HR请求应该有ID"

    print(f"\n   HR请求ID: {result['hr_request']['request_id']}")
    print(f"   目标AI: {result['hr_request']['target_agent']}")
    print(f"   优先级: {result['hr_request']['priority']}")

    assert result['hr_request']['target_agent'] == "基本面分析AI", "目标AI应该是基本面分析AI"
    assert result['hr_request']['priority'] == "HIGH", "优先级应该是HIGH"

    print("\n✅ HR调用测试通过")


@pytest.mark.asyncio
async def test_summary_report_generation():
    """测试5：汇总报告生成"""
    print("\n" + "="*60)
    print("测试5：汇总报告生成")
    print("="*60)

    commander = CommanderAgent()

    # 模拟多个军团的报告
    reports = [
        {
            "report_id": "RPT-HOT-001",
            "agent_name": "热点捕捉-新闻监控AI",
            "stock_code": "600519",
            "corps": "热点捕捉军团",
            "analysis": "茅台股价受政策利好影响，短期看涨。市场情绪积极，资金流入明显。技术指标显示突破信号。",
            "recommendation": "BUY",
            "timestamp": datetime.now().isoformat()
        },
        {
            "report_id": "RPT-IND-001",
            "agent_name": "产业分析-行业研究AI",
            "stock_code": "600519",
            "corps": "产业分析军团",
            "analysis": "白酒行业整体景气度上升，高端白酒市场份额集中度提高。茅台作为龙头受益明显，预计未来3年保持稳健增长。",
            "recommendation": "STRONG_BUY",
            "timestamp": datetime.now().isoformat()
        },
        {
            "report_id": "RPT-STK-001",
            "agent_name": "个股挖掘-基本面分析AI",
            "stock_code": "600519",
            "corps": "个股挖掘军团",
            "analysis": "财务指标优秀：ROE 28%，净利润增长率18%，经营性现金流充裕。估值合理，安全边际较高。目标价2200元。",
            "recommendation": "STRONG_BUY",
            "timestamp": datetime.now().isoformat()
        }
    ]

    # 汇总报告
    result = await commander.execute(
        "collect_and_review_reports",
        reports=reports
    )

    print(f"\n📊 汇总报告:")
    print(result['summary_report'])

    # 验证汇总报告包含关键信息
    assert "主帅汇总报告" in result['summary_report'], "应该包含主帅汇总报告标题"
    assert "总报告数：3" in result['summary_report'], "应该显示总报告数"
    assert "热点捕捉军团" in result['summary_report'], "应该显示军团信息"

    print("\n✅ 汇总报告生成测试通过")


@pytest.mark.asyncio
async def test_accuracy_monitoring():
    """测试6：准确度监控"""
    print("\n" + "="*60)
    print("测试6：准确度监控")
    print("="*60)

    commander = CommanderAgent()

    # 注册一份带预测的报告
    report = {
        "report_id": "RPT-ACC-001",
        "agent_name": "目标定价AI",
        "stock_code": "600519",
        "analysis": "基于DCF模型和相对估值法，目标价2200元",
        "recommendation": "BUY",
        "timestamp": datetime.now().isoformat(),
        "predictions": [
            {
                "type": "target_price",
                "value": 2200,
                "timeframe": "3个月",
                "verification_date": (datetime.now() + timedelta(days=90)).isoformat()
            }
        ]
    }

    # 注册报告
    result = await commander.execute(
        "register_report",
        report=report
    )

    print(f"\n📝 报告注册:")
    print(f"   报告ID: {result['report_id']}")
    print(f"   状态: {result['status']}")
    print(f"   验证日期: {result['verification_date']}")
    print(f"   消息: {result['message']}")

    # 检查Commander的内部状态
    print(f"\n📈 Commander状态:")
    print(f"   总报告数: {len(commander.report_registry)}")
    print(f"   待验证: {len(commander.pending_verifications)}")
    print(f"   已验证: {len(commander.verification_history)}")

    # 验证报告已注册
    assert result['report_id'] in commander.report_registry, "报告应该已注册"
    assert len(commander.pending_verifications) > 0, "应该有待验证的报告"

    print("\n✅ 准确度监控测试通过")


@pytest.mark.asyncio
async def test_quality_validation_scenarios():
    """测试7：各种质量验证场景"""
    print("\n" + "="*60)
    print("测试7：各种质量验证场景")
    print("="*60)

    commander = CommanderAgent()

    # 场景1：缺少必需字段
    print("\n场景1：缺少必需字段")
    report1 = {
        "report_id": "RPT-001",
        "agent_name": "测试AI",
        # 缺少 stock_code, analysis, recommendation
        "timestamp": datetime.now().isoformat()
    }

    # 场景2：分析内容过短
    print("场景2：分析内容过短")
    report2 = {
        "report_id": "RPT-002",
        "agent_name": "测试AI",
        "stock_code": "600000",
        "analysis": "太短了",  # 少于100字
        "recommendation": "BUY",
        "timestamp": datetime.now().isoformat()
    }

    # 场景3：无效建议
    print("场景3：无效建议")
    report3 = {
        "report_id": "RPT-003",
        "agent_name": "测试AI",
        "stock_code": "600000",
        "analysis": "这是一个比较详细的分析内容，长度足够，但是建议不专业。",
        "recommendation": "随便买点",  # 不专业
        "timestamp": datetime.now().isoformat()
    }

    # 场景4：完美报告
    print("场景4：完美报告")
    report4 = {
        "report_id": "RPT-004",
        "agent_name": "优秀AI",
        "stock_code": "600519",
        "analysis": "贵州茅台基本面优秀，ROE持续保持在25%以上，品牌护城河深厚，现金流充裕。未来3年预计保持15%的稳健增长。技术面显示突破信号，成交量放大，资金流入明显。综合判断，强烈推荐买入，目标价2200元，具有较高安全边际。",  # 125字
        "recommendation": "STRONG_BUY",
        "timestamp": datetime.now().isoformat()
    }

    # 汇总所有场景
    result = await commander.execute(
        "collect_and_review_reports",
        reports=[report1, report2, report3, report4]
    )

    print(f"\n📊 验证结果:")
    print(f"   总报告数: {result['summary']['total_reports']}")
    print(f"   ✅ 通过: {len(result['summary']['approved_reports'])}份")
    print(f"   ❌ 拒绝: {len(result['summary']['rejected_reports'])}份")

    # 查看被拒绝的报告
    if result['summary']['rejected_reports']:
        print(f"\n❌ 被拒绝的报告详情:")
        for rejected in result['summary']['rejected_reports']:
            print(f"   - {rejected['report_id']}:")
            print(f"     问题: {', '.join(rejected['issues'])}")

    # 查看通过的报告
    if result['summary']['approved_reports']:
        print(f"\n✅ 通过的报告详情:")
        for approved in result['summary']['approved_reports']:
            print(f"   - {approved['report_id']}: 质量分 {approved['quality_score']}")

    # 验证：应该只有场景4通过
    assert len(result['summary']['approved_reports']) >= 1, "应该有至少1份通过"
    assert len(result['summary']['rejected_reports']) >= 3, "应该有至少3份被拒绝"

    print("\n✅ 质量验证场景测试通过")


@pytest.mark.asyncio
async def test_integration_with_hr():
    """测试8：与HR Agent集成"""
    print("\n" + "="*60)
    print("测试8：与HR Agent集成")
    print("="*60)

    from src.agents.management.hr_agent import HRAgent

    commander = CommanderAgent()
    hr = HRAgent()

    # 注册一个AI到HR
    await hr.register_agent({
        "name": "基本面分析AI",
        "type": "business",
        "corps": "个股挖掘军团"
    })

    print("✅ HR已注册基本面分析AI")

    # 模拟Commander调用HR
    result = await commander.execute(
        "call_hr_for_help",
        agent_name="基本面分析AI",
        issue={
            "issue_type": "low_quality",
            "description": "连续3次报告质量不合格",
            "retry_count": 3
        }
    )

    print(f"\n🤖 Commander调用HR:")
    print(f"   请求ID: {result['hr_request']['request_id']}")
    print(f"   目标AI: {result['hr_request']['target_agent']}")
    print(f"   优先级: {result['hr_request']['priority']}")

    assert result['hr_request']['target_agent'] == "基本面分析AI", "目标AI应该是基本面分析AI"
    assert result['hr_request']['priority'] == "HIGH", "优先级应该是HIGH"

    print("\n✅ HR集成测试通过")


async def main():
    """运行所有测试"""
    print("\n" + "╔"+"═"*58+"╗")
    print("║" + " "*15 + "Commander Agent 完整测试套件" + " "*15 + "║")
    print("╚"+"═"*58+"╝")

    try:
        await test_commander_initialization()
        await test_report_quality_check()
        await test_report_rejection_and_retry()
        await test_call_hr_for_help()
        await test_summary_report_generation()
        await test_accuracy_monitoring()
        await test_quality_validation_scenarios()
        await test_integration_with_hr()

        print("\n" + "╔"+"═"*58+"╗")
        print("║" + " "*18 + "🎉 所有测试通过！" + " "*19 + "║")
        print("╚"+"═"*58+"╝")

        print("\n✅ 测试总结:")
        print("   - ✅ 初始化测试通过")
        print("   - ✅ 报告质量检查通过")
        print("   - ✅ 拒绝和重试机制通过")
        print("   - ✅ HR调用机制通过")
        print("   - ✅ 汇总报告生成通过")
        print("   - ✅ 准确度监控通过")
        print("   - ✅ 质量验证场景通过")
        print("   - ✅ HR集成测试通过")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
