"""
Agent Army - 任务管理页面 (v2.0)
创建任务、监控执行、查看报告
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def render_task_management():
    """渲染任务管理页面"""

    st.title("📋 任务管理")
    st.markdown("---")

    # ========== 标签页 ==========
    tab1, tab2, tab3 = st.tabs(["➕ 创建任务", "📝 任务列表", "🔄 执行监控"])

    # ========== 创建任务标签页 ==========
    with tab1:
        st.markdown("### ➕ 创建分析任务")

        # 任务类型选择
        st.markdown("#### 任务类型")
        task_type = st.radio(
            "选择任务类型",
            [
                "个股完整分析 (24个Agent)",
                "产业分析 (产业分析军团)",
                "热点监控 (热点捕捉军团)",
                "自定义Agent组合"
            ],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # 输入区域
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 目标股票")
            stock_code = st.text_input(
                "股票代码",
                placeholder="例如：000001",
                key="task_stock_code"
            )

        with col2:
            st.markdown("#### 目标行业（可选）")
            industry_code = st.text_input(
                "行业代码",
                placeholder="例如：科技、医药",
                key="task_industry_code"
            )

        st.markdown("---")

        # Agent选择
        st.markdown("#### Agent选择")

        if "自定义Agent组合" in task_type:
            st.info("请选择要启用的Agent:")

            # 6大军团的多选
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**🏭 产业分析军团**")
                st.checkbox("宏观经济AI", value=True, key="cb_macro")
                st.checkbox("产业链分析AI", value=True, key="cb_chain")
                st.checkbox("政策影响AI", value=True, key="cb_policy")
                st.checkbox("行业周期AI", value=True, key="cb_cycle")
                st.checkbox("竞争格局AI", value=True, key="cb_competition")

            with col2:
                st.markdown("**🔥 热点捕捉军团**")
                st.checkbox("新闻监控AI", value=True, key="cb_news")
                st.checkbox("资金情绪AI", value=True, key="cb_capital")
                st.checkbox("龙虎榜AI", value=True, key="cb_dragon")
                st.checkbox("技术分析AI", value=True, key="cb_tech")

            with col3:
                st.markdown("**📈 个股挖掘军团**")
                st.checkbox("财务健康AI", value=True, key="cb_financial")
                st.checkbox("基本面分析AI", value=True, key="cb_fundamental")
                st.checkbox("成长性分析AI", value=True, key="cb_growth")
                st.checkbox("估值与建议AI", value=True, key="cb_valuation")

        else:
            st.info(f"已选择: {task_type}")

        st.markdown("---")

        # 分析深度
        st.markdown("#### 分析深度")
        analysis_depth = st.radio(
            "选择分析深度",
            ["快速 (仅核心Agent)", "标准 (推荐)", "深度 (所有Agent)"],
            index=1,
            horizontal=True,
            label_visibility="collapsed"
        )

        st.markdown("---")

        # 高级选项
        with st.expander("🔧 高级选项"):
            col1, col2 = st.columns(2)

            with col1:
                time_range = st.select_slider(
                    "时间范围",
                    options=["1个月", "3个月", "6个月", "1年", "3年", "5年"],
                    value="1年"
                )

            with col2:
                data_source = st.multiselect(
                    "数据源",
                    ["Tushare", "东方财富", "同花顺", "新浪财经"],
                    default=["Tushare"]
                )

            enable_backtest = st.checkbox("启用回测验证", value=True)
            generate_report = st.checkbox("自动生成报告", value=True)

        st.markdown("---")

        # 操作按钮
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown("")  # 占位

        with col2:
            if st.button("❌ 取消", use_container_width=True):
                st.info("已取消")

        with col3:
            if st.button("🚀 开始分析", type="primary", use_container_width=True):
                if not stock_code:
                    st.error("请输入股票代码！")
                else:
                    # 创建任务
                    task = {
                        "id": len(st.session_state.get('task_history', [])) + 1,
                        "type": task_type,
                        "stock_code": stock_code,
                        "industry_code": industry_code,
                        "depth": analysis_depth,
                        "status": "pending",
                        "progress": 0,
                        "created_at": datetime.now().isoformat()
                    }

                    # 添加到任务历史
                    if 'task_history' not in st.session_state:
                        st.session_state.task_history = []

                    st.session_state.task_history.append(task)

                    st.success(f"✅ 任务创建成功！任务ID: #{task['id']}")
                    st.info("请前往【📝 任务列表】查看任务进度")

    # ========== 任务列表标签页 ==========
    with tab2:
        st.markdown("### 📝 任务列表")

        # 筛选选项
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "状态筛选",
                ["全部", "待执行", "执行中", "已完成", "已失败"]
            )

        with col2:
            type_filter = st.selectbox(
                "类型筛选",
                ["全部", "个股分析", "产业分析", "热点监控"]
            )

        with col3:
            if st.button("🔄 刷新", use_container_width=True):
                st.rerun()

        st.markdown("---")

        # 获取任务列表
        task_history = st.session_state.get('task_history', [])

        if not task_history:
            st.info("📋 暂无任务，点击【➕ 创建任务】开始分析！")
        else:
            # 表头
            col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 1, 1, 1, 2])

            with col1:
                st.markdown("**任务ID**")
            with col2:
                st.markdown("**类型**")
            with col3:
                st.markdown("**目标**")
            with col4:
                st.markdown("**状态**")
            with col5:
                st.markdown("**进度**")
            with col6:
                st.markdown("**操作**")

            st.markdown("---")

            # 任务列表
            for task in reversed(task_history):  # 最新的在前
                col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 1, 1, 1, 2])

                with col1:
                    st.markdown(f"#{task['id']}")

                with col2:
                    st.markdown(task['type'].split('(')[0].strip())

                with col3:
                    st.markdown(task.get('stock_code', 'N/A'))

                with col4:
                    status_emoji = {
                        "pending": "⏳",
                        "running": "🔄",
                        "completed": "✅",
                        "failed": "❌"
                    }.get(task['status'], "⏳")
                    st.markdown(f"{status_emoji} {task['status']}")

                with col5:
                    progress = task.get('progress', 0)
                    st.progress(progress / 100)
                    st.caption(f"{progress}%")

                with col6:
                    # 操作按钮
                    button_col1, button_col2 = st.columns(2)

                    with button_col1:
                        if task['status'] == "completed":
                            if st.button(f"📊 查看", key=f"view_{task['id']}"):
                                st.info(f"查看任务 #{task['id']} 的报告...")

                    with button_col2:
                        if task['status'] == "pending":
                            if st.button(f"▶️ 开始", key=f"start_{task['id']}"):
                                st.info(f"开始执行任务 #{task['id']}...")

                st.markdown("---")

    # ========== 执行监控标签页 ==========
    with tab3:
        st.markdown("### 🔄 执行监控")

        # 选择要监控的任务
        task_history = st.session_state.get('task_history', [])
        running_tasks = [t for t in task_history if t['status'] == 'running']

        if not running_tasks:
            st.info("🔄 当前没有正在执行的任务")
        else:
            for task in running_tasks:
                with st.container():
                    st.markdown(f"#### 任务 #{task['id']} - {task.get('stock_code', 'N/A')}")

                    # 进度条
                    progress = task.get('progress', 0)
                    st.progress(progress / 100)
                    st.markdown(f"**进度**: {progress}%")

                    # 当前执行的Agent
                    st.markdown("**当前Agent**: 宏观经济AI 分析中...")

                    # 执行日志
                    with st.expander("📝 执行日志"):
                        st.code("""
2026-03-14 14:30:01 [INFO] 开始执行任务 #1
2026-03-14 14:30:02 [INFO] 启动宏观经济AI...
2026-03-14 14:30:04 [INFO] 宏观经济AI分析完成
2026-03-14 14:30:05 [INFO] 启动新闻监控AI...
2026-03-14 14:30:07 [INFO] 新闻监控AI分析完成
...
                        """, language="log")

                    # 操作按钮
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(f"⏸️ 暂停", key=f"pause_{task['id']}"):
                            st.info(f"任务 #{task['id']} 已暂停")

                    with col2:
                        if st.button(f"❌ 取消", key=f"cancel_{task['id']}"):
                            st.info(f"任务 #{task['id']} 已取消")

                    st.markdown("---")

    # ========== 底部统计 ==========
    st.markdown("---")
    st.markdown("### 📊 任务统计")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_tasks = len(st.session_state.get('task_history', []))
        st.metric("总任务数", total_tasks)

    with col2:
        completed = len([t for t in st.session_state.get('task_history', []) if t['status'] == 'completed'])
        st.metric("已完成", completed)

    with col3:
        running = len([t for t in st.session_state.get('task_history', []) if t['status'] == 'running'])
        st.metric("执行中", running)

    with col4:
        pending = len([t for t in st.session_state.get('task_history', []) if t['status'] == 'pending'])
        st.metric("待执行", pending)


# 如果直接运行此文件
if __name__ == "__main__":
    render_task_management()
