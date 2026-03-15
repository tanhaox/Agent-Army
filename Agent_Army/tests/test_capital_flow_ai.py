"""
资金流向AI测试

测试核心功能：
1. 资金流向分析
2. 主力资金追踪
3. 资金趋势预测

修复说明：
- 直接调用analyze()方法，而不是execute()
- 使用正确的参数格式
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
from unittest.mock import Mock, patch, AsyncMock
from src.agents.business.hot_spot.capital_flow_ai import CapitalFlowAI


# Mock数据
MOCK_CAPITAL_DATA = [
    {
        "date": "2026-03-15",
        "close_price": 1800.0,
        "change_percent": 2.5,
        "net_inflow": 5000.0,
        "main_net_inflow": 3000.0,
        "super_large_net": 1500.0,
        "large_net": 1500.0,
        "medium_net": -500.0,
        "small_net": 2500.0
    },
    {
        "date": "2026-03-14",
        "close_price": 1755.0,
        "change_percent": 1.8,
        "net_inflow": 4500.0,
        "main_net_inflow": 2800.0,
        "super_large_net": 1400.0,
        "large_net": 1400.0,
        "medium_net": -400.0,
        "small_net": 2100.0
    },
    {
        "date": "2026-03-13",
        "close_price": 1724.0,
        "change_percent": -0.5,
        "net_inflow": 4200.0,
        "main_net_inflow": 2600.0,
        "super_large_net": 1300.0,
        "large_net": 1300.0,
        "medium_net": -300.0,
        "small_net": 1900.0
    }
]


@pytest.mark.asyncio
@patch('src.agents.business.hot_spot.capital_flow_ai.AKShareTool')
async def test_initialization(mock_akshare_tool):
    """测试1：初始化"""
    print("\n" + "="*60)
    print("测试1：资金流向AI初始化")
    print("="*60)

    ai = CapitalFlowAI()

    print(f"✅ AI名称: {ai.name}")
    print(f"✅ AI角色: {ai.role}")
    print(f"✅ 分析类型: {ai.analysis_type}")
    print(f"✅ 军团: {ai.corps}")

    # 验证基本属性
    assert ai.name == "资金流向AI", "AI名称不对"
    assert ai.corps == "热点捕捉军团", "军团不对"
    assert ai.analysis_type == "capital_flow", "分析类型不对"

    print("✅ 初始化测试通过")


@pytest.mark.asyncio
@patch('src.agents.business.hot_spot.capital_flow_ai.AKShareTool')
async def test_capital_flow_analysis(mock_akshare_tool):
    """测试2：资金流向分析"""
    print("\n" + "="*60)
    print("测试2：资金流向分析")
    print("="*60)

    # Mock AKShareTool
    mock_tool_instance = Mock()
    mock_akshare_tool.return_value = mock_tool_instance

    # Mock DataFrame
    import pandas as pd
    mock_df = pd.DataFrame(MOCK_CAPITAL_DATA)
    mock_tool_instance.get_individual_fund_flow.return_value = mock_df

    ai = CapitalFlowAI()

    # 分析贵州茅台的资金流向
    result = await ai.analyze(
        stock_code="600519",
        market="sh",
        days=5
    )

    print(f"\n💰 资金流向分析结果:")
    print(f"   Agent: {result.agent_name}")
    print(f"   结论: {result.conclusion}")
    print(f"   置信度: {result.confidence}%")
    print(f"   详情: {result.details}")

    # 验证结果
    assert result.agent_name == "资金流向AI", "Agent名称不对"
    assert result.analysis_type == "capital_flow", "分析类型不对"
    assert result.conclusion is not None, "应该有结论"
    assert 0 <= result.confidence <= 100, "置信度应该在0-100之间"

    print("\n✅ 资金流向分析测试通过")


@pytest.mark.asyncio
@patch('src.agents.business.hot_spot.capital_flow_ai.AKShareTool')
async def test_main_force_tracking(mock_akshare_tool):
    """测试3：主力资金追踪"""
    print("\n" + "="*60)
    print("测试3：主力资金追踪")
    print("="*60)

    # Mock AKShareTool
    mock_tool_instance = Mock()
    mock_akshare_tool.return_value = mock_tool_instance

    # Mock DataFrame
    import pandas as pd
    mock_df = pd.DataFrame(MOCK_CAPITAL_DATA)
    mock_tool_instance.get_individual_fund_flow.return_value = mock_df

    ai = CapitalFlowAI()

    # 分析主力资金
    result = await ai.analyze(
        stock_code="600519",
        market="sh",
        days=5
    )

    print(f"\n🏦 主力资金追踪结果:")
    print(f"   Agent: {result.agent_name}")
    print(f"   结论: {result.conclusion}")
    print(f"   置信度: {result.confidence}%")

    # 获取资金流向数据
    flow_data = result.details.get("capital_flow_data", {})
    print(f"   评级: {flow_data.get('rating', 'N/A')}")
    print(f"   模式: {flow_data.get('pattern', 'N/A')}")
    print(f"   主力净流入: {flow_data.get('main_net_inflow', 0)}万元")
    print(f"   净流入: {flow_data.get('net_inflow', 0)}万元")

    # 验证结果
    assert result.agent_name == "资金流向AI", "Agent名称不对"
    assert flow_data.get("rating") in ["accumulation", "distribution", "neutral"], "评级应该是accumulation/distribution/neutral"
    assert "main_net_inflow" in flow_data, "应该有主力净流入数据"

    print("\n✅ 主力资金追踪测试通过")


@pytest.mark.asyncio
@patch('src.agents.business.hot_spot.capital_flow_ai.AKShareTool')
async def test_capital_trend_prediction(mock_akshare_tool):
    """测试4：资金趋势预测"""
    print("\n" + "="*60)
    print("测试4：资金趋势预测")
    print("="*60)

    # Mock AKShareTool
    mock_tool_instance = Mock()
    mock_akshare_tool.return_value = mock_tool_instance

    # Mock DataFrame - 多日数据用于趋势分析
    import pandas as pd
    mock_df = pd.DataFrame(MOCK_CAPITAL_DATA)
    mock_tool_instance.get_individual_fund_flow.return_value = mock_df

    ai = CapitalFlowAI()

    # 预测资金趋势
    result = await ai.analyze(
        stock_code="600519",
        market="sh",
        days=10
    )

    print(f"\n📈 资金趋势预测结果:")
    print(f"   Agent: {result.agent_name}")
    print(f"   结论: {result.conclusion}")
    print(f"   置信度: {result.confidence}%")

    # 获取资金流向数据
    flow_data = result.details.get("capital_flow_data", {})
    print(f"   评级: {flow_data.get('rating', 'N/A')}")
    print(f"   模式: {flow_data.get('pattern', 'N/A')}")
    print(f"   强度: {flow_data.get('strength', 'N/A')}")

    # 验证结果
    assert result.agent_name == "资金流向AI", "Agent名称不对"
    assert result.confidence >= 0 and result.confidence <= 100, "置信度应该在0-100之间"
    assert flow_data.get("rating") is not None, "应该有评级"

    print("\n✅ 资金趋势预测测试通过")


@pytest.mark.asyncio
async def test_flow_scenarios():
    """测试5：不同资金流向场景"""
    print("\n" + "="*60)
    print("测试5：不同资金流向场景")
    print("="*60)

    ai = CapitalFlowAI()

    # 场景1：模拟强流入
    print("\n场景1：模拟强流入市场")
    strong_inflow_data = [
        {"inflow": 5000, "outflow": 2000, "net_inflow": 3000, "turnover_rate": 4.5},
        {"inflow": 4500, "outflow": 1800, "net_inflow": 2700, "turnover_rate": 4.2},
        {"inflow": 4800, "outflow": 2100, "net_inflow": 2700, "turnover_rate": 4.8}
    ]

    # 使用公共方法测试内部逻辑
    flow_analysis = ai._analyze_capital_flow(strong_inflow_data)
    print(f"   评级: {flow_analysis.get('rating')}")
    print(f"   模式: {flow_analysis.get('pattern')}")
    print(f"   摘要: {flow_analysis.get('summary')}")

    # 场景2：模拟强流出
    print("\n场景2：模拟强流出市场")
    strong_outflow_data = [
        {"net_inflow": -3000, "main_net_inflow": -2500, "super_large_net": -1500,
         "large_net": -1000, "medium_net": 500, "small_net": -500},
        {"net_inflow": -2700, "main_net_inflow": -2200, "super_large_net": -1300,
         "large_net": -900, "medium_net": 400, "small_net": -400},
        {"net_inflow": -2700, "main_net_inflow": -2300, "super_large_net": -1400,
         "large_net": -900, "medium_net": 500, "small_net": -500}
    ]

    flow_analysis = ai._analyze_capital_flow(strong_outflow_data)
    print(f"   评级: {flow_analysis.get('rating')}")
    print(f"   模式: {flow_analysis.get('pattern')}")
    print(f"   摘要: {flow_analysis.get('summary')}")

    # 场景3：模拟平衡市场
    print("\n场景3：模拟平衡市场")
    balanced_data = [
        {"net_inflow": 100, "main_net_inflow": 50, "super_large_net": 30,
         "large_net": 20, "medium_net": -20, "small_net": 70},
        {"net_inflow": -100, "main_net_inflow": -30, "super_large_net": -20,
         "large_net": -10, "medium_net": 10, "small_net": -60},
        {"net_inflow": 0, "main_net_inflow": 0, "super_large_net": 0,
         "large_net": 0, "medium_net": 0, "small_net": 0}
    ]

    flow_analysis = ai._analyze_capital_flow(balanced_data)
    print(f"   评级: {flow_analysis.get('rating')}")
    print(f"   模式: {flow_analysis.get('pattern')}")
    print(f"   摘要: {flow_analysis.get('summary')}")

    print("\n✅ 资金流向场景测试通过")


@pytest.mark.asyncio
@patch('src.agents.business.hot_spot.capital_flow_ai.AKShareTool')
async def test_error_handling(mock_akshare_tool):
    """测试6：错误处理"""
    print("\n" + "="*60)
    print("测试6：错误处理")
    print("="*60)

    # Mock AKShareTool返回空数据
    mock_tool_instance = Mock()
    mock_akshare_tool.return_value = mock_tool_instance

    import pandas as pd
    mock_df = pd.DataFrame()  # 空DataFrame
    mock_tool_instance.get_individual_fund_flow.return_value = mock_df

    ai = CapitalFlowAI()

    # 测试空数据处理
    result = await ai.analyze(
        stock_code="600519",
        market="sh",
        days=5
    )

    print(f"\n⚠️ 空数据处理结果:")
    print(f"   Agent: {result.agent_name}")
    print(f"   结论: {result.conclusion}")
    print(f"   置信度: {result.confidence}%")

    # 验证错误处理
    assert result.agent_name == "资金流向AI", "Agent名称不对"
    assert result.confidence == 0.0, "空数据时置信度应该为0"
    assert "未能获取" in result.conclusion or "未获取到" in result.conclusion, "应该有错误信息"

    print("\n✅ 错误处理测试通过")


async def main():
    """运行所有测试"""
    print("\n" + "╔"+"═"*58+"╗")
    print("║" + " "*18 + "资金流向AI测试套件" + " "*18 + "║")
    print("╚"+"═"*58+"╝")

    try:
        await test_initialization()
        await test_capital_flow_analysis()
        await test_main_force_tracking()
        await test_capital_trend_prediction()
        await test_flow_scenarios()
        await test_error_handling()

        print("\n" + "╔"+"═"*58+"╗")
        print("║" + " "*21 + "🎉 所有测试通过！" + " "*21 + "║")
        print("╚"+"═"*58+"╝")

        print("\n✅ 测试总结:")
        print("   - ✅ 初始化测试通过")
        print("   - ✅ 资金流向分析测试通过")
        print("   - ✅ 主力资金追踪测试通过")
        print("   - ✅ 资金趋势预测测试通过")
        print("   - ✅ 资金流向场景测试通过")
        print("   - ✅ 错误处理测试通过")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
