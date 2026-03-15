"""
Agent Army - Agent集成示例
展示如何集成和调用真实Agent
"""

import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.agents.agent_manager import (
    get_agent_manager,
    TaskStatus
)


def integrate_real_agents():
    """
    集成真实Agent的示例代码

    这个文件展示了如何：
    1. 初始化Agent管理器
    2. 创建分析任务
    3. 执行任务并获取结果
    4. 显示进度和结果
    """

    st.markdown("### 🤖 Agent集成示例")

    # 获取Agent管理器
    agent_manager = get_agent_manager()

    # 显示所有Agent
    st.markdown("#### 所有Agent列表")
    all_agents = agent_manager.get_all_agents()

    for agent_id, agent_info in all_agents.items():
        with st.expander(f"{agent_info['name']} - {agent_info['army']}"):
            st.markdown(f"**ID**: {agent_id}")
            st.markdown(f"**描述**: {agent_info['description']}")
            st.markdown(f"**状态**: {agent_info['status'].value}")

    # 创建分析任务
    st.markdown("---")
    st.markdown("#### 创建分析任务")

    col1, col2 = st.columns(2)

    with col1:
        stock_code = st.text_input("股票代码", "000001", key="demo_stock_code")
        task_type = st.selectbox(
            "任务类型",
            ["full_analysis", "industry", "hot_topics", "custom"],
            key="demo_task_type"
        )

    with col2:
        # 选择参与的Agent
        available_agents = list(all_agents.keys())
        selected_agents = st.multiselect(
            "选择Agent（至少3个）",
            available_agents,
            default=available_agents[:3],
            key="demo_agents"
        )

    if st.button("创建任务", type="primary"):
        if len(selected_agents) < 3:
            st.warning("⚠️ 请至少选择3个Agent")
        else:
            # 创建任务
            task = agent_manager.create_task(
                task_type=task_type,
                stock_code=stock_code,
                agents=selected_agents
            )

            st.success(f"✅ 任务已创建: {task.task_id}")
            st.info("请在【任务管理】页面查看进度")

            # 显示任务信息
            with st.expander("📋 任务详情"):
                st.json({
                    "task_id": task.task_id,
                    "type": task.task_type,
                    "stock_code": task.stock_code,
                    "agents": task.agents,
                    "status": task.status.value,
                    "progress": f"{task.progress:.1f}%",
                    "created_at": task.created_at.isoformat()
                })

    # 显示当前任务
    st.markdown("---")
    st.markdown("#### 当前任务列表")

    tasks = agent_manager.get_all_tasks()

    if not tasks:
        st.info("暂无任务")
    else:
        for task in tasks:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

                with col1:
                    st.markdown(f"**任务ID**: {task.task_id}")

                with col2:
                    status_emoji = {
                        TaskStatus.PENDING: "⏳",
                        TaskStatus.RUNNING: "🔄",
                        TaskStatus.COMPLETED: "✅",
                        TaskStatus.FAILED: "❌"
                    }.get(task.status, "⏳")
                    st.markdown(f"**状态**: {status_emoji} {task.status.value}")

                with col3:
                    st.markdown(f"**进度**: {task.progress:.1f}%")

                with col4:
                    if task.status == TaskStatus.COMPLETED and st.button("查看", key=f"view_{task.task_id}"):
                        st.json(task.result)

                st.markdown("---")


def example_agent_analysis(stock_code: str = "000001"):
    """
    Agent分析示例

    Args:
        stock_code: 股票代码
    """
    st.markdown("### 🤖 Agent分析示例")

    agent_manager = get_agent_manager()

    # 选择关键Agent
    key_agents = [
        "macro_economic",      # 宏观经济AI
        "financial_health",    # 财务健康AI
        "valuation",           # 估值AI
        "technical_analysis",  # 技术分析AI
        "news_monitor"         # 新闻监控AI
    ]

    # 创建任务
    task = agent_manager.create_task(
        task_type="custom",
        stock_code=stock_code,
        agents=key_agents
    )

    # 执行任务（实际应用中应该是异步的）
    with st.spinner("Agent分析中..."):
        results = agent_manager.execute_task(task)

    # 显示结果
    st.success("✅ 分析完成")

    for agent_id, result in results.items():
        with st.expander(f"📊 {result['agent_name']}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**评分**: {result['score']}/100")
                st.markdown(f"**推荐**: {result['recommendation']}")
                st.markdown(f"**置信度**: {result['confidence']:.1%}")

            with col2:
                st.markdown(f"**所属军团**: {result['army']}")
                st.markdown(f"**分析时间**: {result['timestamp']}")

            st.markdown("---")
            st.markdown(f"**分析结论**: {result['analysis']}")


def example_batch_analysis(stock_codes: List[str]):
    """
    批量分析示例

    Args:
        stock_codes: 股票代码列表
    """
    st.markdown("### 📊 批量分析示例")

    agent_manager = get_agent_manager()
    tasks = []

    # 创建多个任务
    for stock_code in stock_codes:
        task = agent_manager.create_task(
            task_type="full_analysis",
            stock_code=stock_code,
            agents=["macro_economic", "financial_health", "valuation"]
        )
        tasks.append(task)

    st.info(f"已创建 {len(tasks)} 个分析任务")

    # 显示任务列表
    for task in tasks:
        st.markdown(f"- {task.task_id}: {task.stock_code} - {task.status.value}")


# 实际集成真实Agent的接口示例
class RealAgentIntegration:
    """
    真实Agent集成接口

    这个类展示了如何集成真实的Agent系统
    """

    @staticmethod
    def call_macro_economic_agent(stock_code: str) -> Dict:
        """
        调用宏观经济AI

        Args:
            stock_code: 股票代码

        Returns:
            分析结果
        """
        # TODO: 实际调用宏观经济AI
        # 示例：
        # from agents.macro_economic import MacroEconomicAgent
        # agent = MacroEconomicAgent()
        # result = agent.analyze(stock_code)
        # return result

        return {
            "gdp_growth": 5.2,
            "cpi": 2.1,
            "pmi": 51.2,
            "analysis": "宏观经济环境良好",
            "score": 85
        }

    @staticmethod
    def call_financial_health_agent(stock_code: str) -> Dict:
        """
        调用财务健康AI

        Args:
            stock_code: 股票代码

        Returns:
            分析结果
        """
        # TODO: 实际调用财务健康AI
        return {
            "revenue_growth": 15.2,
            "profit_margin": 12.5,
            "debt_ratio": 45.3,
            "analysis": "财务状况健康",
            "score": 88
        }

    @staticmethod
    def call_technical_analysis_agent(stock_code: str) -> Dict:
        """
        调用技术分析AI

        Args:
            stock_code: 股票代码

        Returns:
            分析结果
        """
        # TODO: 实际调用技术分析AI
        return {
            "ma5": 10.5,
            "ma20": 10.2,
            "macd": 0.15,
            "rsi": 65,
            "analysis": "技术指标向好",
            "score": 75
        }


# 使用示例
if __name__ == "__main__":
    # 在Streamlit页面中使用
    st.set_page_config(page_title="Agent集成示例", page_icon="🤖", layout="wide")

    tab1, tab2, tab3 = st.tabs([
        "Agent列表",
        "创建任务",
        "分析示例"
    ])

    with tab1:
        integrate_real_agents()

    with tab2:
        example_agent_analysis()

    with tab3:
        stock_codes_input = st.text_input(
            "股票代码（逗号分隔）",
            "000001,000002,600000"
        )
        if st.button("批量分析"):
            codes = [c.strip() for c in stock_codes_input.split(",")]
            example_batch_analysis(codes)
