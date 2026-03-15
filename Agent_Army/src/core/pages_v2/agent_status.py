"""
Agent Army - Agent状态页面 (v2.0)
展示24个Agent和6大军团
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def render_agent_status():
    """渲染Agent状态页面"""

    st.title("🤖 Agent状态")
    st.markdown(f"**24个Agent | 6大军团 | 100%完成** | 更新时间: {datetime.now().strftime('%H:%M:%S')}")
    st.markdown("---")

    # ========== 军团选择标签页 ==========
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 总览",
        "🏭 产业分析",
        "🔥 热点捕捉",
        "📈 个股挖掘",
        "🎯 目标预测",
        "⚡ 策略执行",
        "✅ 结果验证"
    ])

    # ========== 总览标签页 ==========
    with tab1:
        st.markdown("### 📊 6大军团总览")

        # 军团统计卡片
        col1, col2, col3 = st.columns(3)

        with col1:
            st.info("🏭 **产业分析军团**\n5个Agent | 125% ⭐⭐⭐")
            st.info("🔥 **热点捕捉军团**\n4个Agent | 100% ⭐⭐")

        with col2:
            st.info("📈 **个股挖掘军团**\n4个Agent | 100% ⭐⭐")
            st.info("🎯 **目标预测军团**\n5个Agent | 125% ⭐⭐⭐")

        with col3:
            st.info("⚡ **策略执行军团**\n5个Agent | 125% ⭐⭐⭐")
            st.info("✅ **结果验证军团**\n5个Agent | 125% ⭐⭐⭐")

        st.markdown("---")

        # Agent性能监控表
        st.markdown("### 📊 Agent性能监控")

        # 表头
        col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
        with col1:
            st.markdown("**Agent名称**")
        with col2:
            st.markdown("**任务数**")
        with col3:
            st.markdown("**成功率**")
        with col4:
            st.markdown("**平均时间**")
        with col5:
            st.markdown("**评分**")
        with col6:
            st.markdown("**状态**")

        st.markdown("---")

        # 模拟Agent性能数据
        agents_performance = [
            {"name": "🤖 宏观经济AI", "tasks": 15, "success": 95, "time": "2.3s", "score": "A", "status": "idle"},
            {"name": "🤖 新闻监控AI", "tasks": 28, "success": 92, "time": "1.8s", "score": "A-", "status": "idle"},
            {"name": "🤖 产业链分析AI", "tasks": 12, "success": 100, "time": "2.5s", "score": "A+", "status": "idle"},
            {"name": "🤖 政策影响AI", "tasks": 8, "success": 88, "time": "2.0s", "score": "B+", "status": "idle"},
            {"name": "🤖 资金情绪AI", "tasks": 35, "success": 94, "time": "2.1s", "score": "A", "status": "idle"},
            {"name": "🤖 财务健康AI", "tasks": 22, "success": 91, "time": "1.9s", "score": "A-", "status": "idle"},
            {"name": "🤖 成长性分析AI", "tasks": 18, "success": 89, "time": "2.2s", "score": "B+", "status": "idle"},
            {"name": "🤖 质量评分AI", "tasks": 14, "success": 93, "time": "2.0s", "score": "A-", "status": "idle"},
            {"name": "🤖 股价预测AI", "tasks": 20, "success": 85, "time": "3.0s", "score": "B+", "status": "idle"},
            {"name": "🤖 情景分析AI", "tasks": 10, "success": 90, "time": "2.5s", "score": "A-", "status": "idle"},
        ]

        for agent in agents_performance:
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])

            with col1:
                st.markdown(agent["name"])
            with col2:
                st.markdown(str(agent["tasks"]))
            with col3:
                st.markdown(f"{agent['success']}%")
            with col4:
                st.markdown(agent["time"])
            with col5:
                # 根据评分显示不同颜色
                score = agent["score"]
                if score in ["A+", "A"]:
                    st.markdown(f"🟢 {score}")
                elif score in ["A-", "B+"]:
                    st.markdown(f"🟡 {score}")
                else:
                    st.markdown(f"🔴 {score}")
            with col6:
                status_emoji = "✅" if agent["status"] == "idle" else "🔄"
                st.markdown(f"{status_emoji} {agent['status']}")

    # ========== 产业分析军团 ==========
    with tab2:
        st.markdown("### 🏭 产业分析军团 (5个Agent) - 125% ⭐⭐⭐")

        agents = [
            {
                "name": "宏观经济AI",
                "icon": "🌍",
                "priority": "P0",
                "code": "~800行",
                "capabilities": ["经济增长分析", "货币政策分析", "财政政策分析", "通胀分析", "汇率分析"],
                "status": "idle",
                "tasks": 15,
                "score": "A"
            },
            {
                "name": "产业链分析AI",
                "icon": "🔗",
                "priority": "P1",
                "code": "~700行",
                "capabilities": ["上游分析", "中游分析", "下游分析", "价值分布", "投资机会"],
                "status": "idle",
                "tasks": 12,
                "score": "A+"
            },
            {
                "name": "政策影响AI",
                "icon": "📜",
                "priority": "P1",
                "code": "~600行",
                "capabilities": ["政策识别", "影响评估", "时间线分析", "受益/受损股", "投资建议"],
                "status": "idle",
                "tasks": 8,
                "score": "B+"
            },
            {
                "name": "行业周期AI",
                "icon": "🔄",
                "priority": "P1",
                "code": "~650行",
                "capabilities": ["周期识别", "周期位置", "周期预测", "投资建议"],
                "status": "idle",
                "tasks": 10,
                "score": "B+"
            },
            {
                "name": "竞争格局AI",
                "icon": "⚔️",
                "priority": "已有",
                "code": "~800行",
                "capabilities": ["竞争格局分析", "市场集中度", "龙头企业识别", "CR4/CR8/HHI"],
                "status": "idle",
                "tasks": 18,
                "score": "A"
            }
        ]

        # 显示Agent卡片
        for i in range(0, len(agents), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(agents):
                    agent = agents[i + j]
                    with col:
                        with st.container():
                            st.markdown(f"#### {agent['icon']} {agent['name']}")
                            st.markdown(f"**优先级**: {agent['priority']} | **代码量**: {agent['code']}")

                            # 状态和评分
                            status_emoji = "✅" if agent['status'] == "idle" else "🔄"
                            score_color = "🟢" if agent['score'] in ["A+", "A"] else "🟡"
                            st.markdown(f"**状态**: {status_emoji} {agent['status']} | **评分**: {score_color} {agent['score']}")

                            st.markdown(f"**完成任务**: {agent['tasks']}个")

                            st.markdown("**核心能力**:")
                            for cap in agent['capabilities'][:3]:
                                st.markdown(f"- {cap}")

                            if st.button(f"查看详情", key=f"detail_{agent['name']}"):
                                st.info(f"Agent详情页面开发中...")

                            st.markdown("---")

    # ========== 热点捕捉军团 ==========
    with tab3:
        st.markdown("### 🔥 热点捕捉军团 (4个Agent) - 100% ⭐⭐")

        agents = [
            {
                "name": "新闻监控AI",
                "icon": "📰",
                "priority": "P0",
                "code": "~600行",
                "capabilities": ["新闻获取", "事件提取", "影响评估", "股票关联"],
                "status": "idle",
                "tasks": 28,
                "score": "A-"
            },
            {
                "name": "资金情绪AI",
                "icon": "💰",
                "priority": "已有",
                "code": "~1100行",
                "capabilities": ["资金流向", "市场情绪", "热点识别", "趋势追踪"],
                "status": "idle",
                "tasks": 35,
                "score": "A"
            },
            {
                "name": "龙虎榜AI",
                "icon": "🐉",
                "priority": "已有",
                "code": "~900行",
                "capabilities": ["龙虎榜数据", "游资跟踪", "机构动向", "异动信号"],
                "status": "idle",
                "tasks": 22,
                "score": "A-"
            },
            {
                "name": "技术分析AI",
                "icon": "📊",
                "priority": "已有",
                "code": "~1200行",
                "capabilities": ["趋势分析", "技术指标", "形态识别", "量价分析"],
                "status": "idle",
                "tasks": 30,
                "score": "A"
            }
        ]

        # 显示Agent卡片
        for i in range(0, len(agents), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(agents):
                    agent = agents[i + j]
                    with col:
                        with st.container():
                            st.markdown(f"#### {agent['icon']} {agent['name']}")
                            st.markdown(f"**优先级**: {agent['priority']} | **代码量**: {agent['code']}")

                            status_emoji = "✅" if agent['status'] == 'idle' else "🔄"
                            score_color = "🟢" if agent['score'] in ["A+", "A"] else "🟡"
                            st.markdown(f"**状态**: {status_emoji} {agent['status']} | **评分**: {score_color} {agent['score']}")

                            st.markdown(f"**完成任务**: {agent['tasks']}个")

                            st.markdown("**核心能力**:")
                            for cap in agent['capabilities'][:3]:
                                st.markdown(f"- {cap}")

                            if st.button(f"查看详情", key=f"detail_{agent['name']}_hot"):
                                st.info(f"Agent详情页面开发中...")

                            st.markdown("---")

    # ========== 个股挖掘军团 ==========
    with tab4:
        st.markdown("### 📈 个股挖掘军团 (4个Agent) - 100% ⭐⭐")
        st.info("该军团包含：财务健康AI、基本面分析AI、成长性分析AI、估值与建议AI")

    # ========== 目标预测军团 ==========
    with tab5:
        st.markdown("### 🎯 目标预测军团 (5个Agent) - 125% ⭐⭐⭐")
        st.info("该军团包含：质量评分AI、股价预测AI、估值与建议AI、技术分析AI、成长性分析AI")

    # ========== 策略执行军团 ==========
    with tab6:
        st.markdown("### ⚡ 策略执行军团 (5个Agent) - 125% ⭐⭐⭐")
        st.info("该军团包含：风险与时机AI、情景分析AI、仓位管理AI、卖出时机AI、风险与时机AI")

    # ========== 结果验证军团 ==========
    with tab7:
        st.markdown("### ✅ 结果验证军团 (5个Agent) - 125% ⭐⭐⭐")
        st.info("该军团包含：回测分析AI、预测验证AI、业绩归因AI、风险归因AI、期权衍生品AI")

    # ========== 底部操作 ==========
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 刷新状态", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("📊 性能报告", use_container_width=True):
            st.info("性能报告页面开发中...")

    with col3:
        if st.button("⚙️ Agent配置", use_container_width=True):
            st.info("请前往【⚙️ 系统配置】页面")


# 如果直接运行此文件
if __name__ == "__main__":
    render_agent_status()
