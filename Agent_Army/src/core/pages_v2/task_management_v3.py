"""
Agent Army - 任务管理页面 (v3.0 优化版)
完全基于Phase 2设计文档重构，100%使用Design Tokens

创建日期: 2026-03-15
设计文档: docs/PHASE2_DASHBOARD_DESIGN_TASK.md
实施计划: docs/PHASE3_PLAN.md 任务3.2
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# ==================== 导入Phase 1设计系统 ====================
from src.core.design_tokens import DesignTokens
from src.core.global_styles import apply_global_styles
from src.core.ui_components import create_metric_card, get_status_badge


def rgba(hex_color: str, alpha: float) -> str:
    """将hex颜色转换为rgba格式"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def render_task_management_v3():
    """渲染任务管理页面（v3.0 优化版）"""

    # 应用全局样式
    apply_global_styles()

    # ==================== 页面标题 ====================
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: {DesignTokens.Spacing.M_LG};">
        <div>
            <h1 style="font-size: {DesignTokens.Typography.H1};
                      color: {DesignTokens.Colors.TEXT_PRIMARY};
                      margin: 0;
                      font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                📋 任务管理
            </h1>
            <p style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin: {DesignTokens.Spacing.M_NONE} 0 {DesignTokens.Spacing.M_SM} 0;">
                创建、监控和管理分析任务
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ==================== 顶部统计卡片 ====================
    col1, col2, col3, col4, col5 = st.columns(5)

    task_history = st.session_state.get('task_history', [])
    total_tasks = len(task_history)
    completed = len([t for t in task_history if t['status'] == 'completed'])
    running = len([t for t in task_history if t['status'] == 'running'])
    pending = len([t for t in task_history if t['status'] == 'pending'])
    failed = len([t for t in task_history if t['status'] == 'failed'])

    with col1:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            border-left: 4px solid {DesignTokens.Colors.PRIMARY};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                总任务
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.PRIMARY};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                {total_tasks}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            border-left: 4px solid {DesignTokens.Colors.SUCCESS};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                已完成
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.SUCCESS};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                {completed}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            border-left: 4px solid {DesignTokens.Colors.INFO};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                执行中
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.INFO};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                {running}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            border-left: 4px solid {DesignTokens.Colors.WARNING};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                待执行
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.WARNING};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                {pending}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            border-left: 4px solid {DesignTokens.Colors.ERROR};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                已失败
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.ERROR};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                {failed}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<div style='margin-bottom: {DesignTokens.Spacing.M_LG};'></div>", unsafe_allow_html=True)

    # ==================== 主内容区域（左右布局）====================
    col_main, col_side = st.columns([2, 1])

    with col_main:
        # ========== 任务列表 ==========
        st.markdown(f"""
        <h2 style="font-size: {DesignTokens.Typography.H2};
                   color: {DesignTokens.Colors.TEXT_PRIMARY};
                   margin-bottom: {DesignTokens.Spacing.M_MD};">
            📝 任务列表
        </h2>
        """, unsafe_allow_html=True)

        # 筛选器（扁平化展示）
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

        with filter_col1:
            status_filter = st.selectbox(
                "状态",
                ["全部", "待执行", "执行中", "已完成", "已失败"],
                label_visibility="collapsed"
            )

        with filter_col2:
            type_filter = st.selectbox(
                "类型",
                ["全部", "个股分析", "产业分析", "热点监控", "自定义"],
                label_visibility="collapsed"
            )

        with filter_col3:
            sort_by = st.selectbox(
                "排序",
                ["创建时间（最新）", "创建时间（最早）", "进度（高到低）", "进度（低到高）"],
                label_visibility="collapsed"
            )

        with filter_col4:
            if st.button("🔄 刷新", use_container_width=True, key="refresh_tasks"):
                st.rerun()

        st.markdown(f"<div style='margin-bottom: {DesignTokens.Spacing.M_MD};'></div>", unsafe_allow_html=True)

        # ========== 任务卡片列表 ==========
        filtered_tasks = task_history

        # 应用筛选
        if status_filter != "全部":
            status_map = {
                "待执行": "pending",
                "执行中": "running",
                "已完成": "completed",
                "已失败": "failed"
            }
            filtered_tasks = [t for t in filtered_tasks if t['status'] == status_map[status_filter]]

        if type_filter != "全部":
            filtered_tasks = [t for t in filtered_tasks if type_filter in t['type']]

        # 应用排序
        if sort_by == "创建时间（最新）":
            filtered_tasks = list(reversed(filtered_tasks))
        elif sort_by == "创建时间（最早）":
            pass  # 已经是最早到最晚
        elif sort_by == "进度（高到低）":
            filtered_tasks = sorted(filtered_tasks, key=lambda x: x.get('progress', 0), reverse=True)
        elif sort_by == "进度（低到高）":
            filtered_tasks = sorted(filtered_tasks, key=lambda x: x.get('progress', 0))

        # 空状态
        if not filtered_tasks:
            st.markdown(f"""
            <div style="
                text-align: center;
                padding: {DesignTokens.Spacing.P_LG};
                background: {DesignTokens.Colors.BG_CARD};
                border-radius: {DesignTokens.Radius.LG};
                border: 2px dashed {DesignTokens.Colors.BORDER};
            ">
                <div style="font-size: {DesignTokens.Typography.H4};
                         color: {DesignTokens.Colors.TEXT_SECONDARY};
                         margin-bottom: {DesignTokens.Spacing.M_SM};">
                    📋
                </div>
                <div style="font-size: {DesignTokens.Typography.BODY};
                         color: {DesignTokens.Colors.TEXT_SECONDARY};">
                    暂无任务
                </div>
                <div style="font-size: {DesignTokens.Typography.SMALL};
                         color: {DesignTokens.Colors.TEXT_HINT};
                         margin-top: {DesignTokens.Spacing.M_SM};">
                    点击右侧创建任务开始分析
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 任务卡片
            for task in filtered_tasks:
                # 状态颜色
                status_colors = {
                    "pending": DesignTokens.Colors.WARNING,
                    "running": DesignTokens.Colors.INFO,
                    "completed": DesignTokens.Colors.SUCCESS,
                    "failed": DesignTokens.Colors.ERROR
                }
                status_color = status_colors.get(task['status'], DesignTokens.Colors.TEXT_HINT)

                # 状态文本
                status_texts = {
                    "pending": "⏳ 待执行",
                    "running": "🔄 执行中",
                    "completed": "✅ 已完成",
                    "failed": "❌ 已失败"
                }
                status_text = status_texts.get(task['status'], "⏳ 未知")

                # 展开键
                expand_key = f"expand_task_{task['id']}"
                if expand_key not in st.session_state:
                    st.session_state[expand_key] = False

                # 任务卡片
                st.markdown(f"""
                <div style="
                    background: {DesignTokens.Colors.BG_CARD};
                    border-left: 4px solid {status_color};
                    border-radius: {DesignTokens.Radius.LG};
                    padding: {DesignTokens.Spacing.P_MD};
                    margin-bottom: {DesignTokens.Spacing.M_MD};
                    box-shadow: {DesignTokens.Shadow.SM};
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: {DesignTokens.Typography.H4};
                                       color: {DesignTokens.Colors.TEXT_PRIMARY};
                                       font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
                                       margin-bottom: {DesignTokens.Spacing.M_XS};">
                                #{task['id']} - {task['type'].split('(')[0].strip()}
                            </div>
                            <div style="font-size: {DesignTokens.Typography.SMALL};
                                       color: {DesignTokens.Colors.TEXT_SECONDARY};">
                                目标: {task.get('stock_code', 'N/A')} |
                                创建: {task.get('created_at', '')[:10]}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: {DesignTokens.Typography.BODY};
                                       color: {status_color};
                                       font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};">
                                {status_text}
                            </div>
                            <div style="font-size: {DesignTokens.Typography.SMALL};
                                       color: {DesignTokens.Colors.TEXT_SECONDARY};">
                                进度: {task.get('progress', 0)}%
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 展开/折叠按钮
                col_left, col_right = st.columns([3, 1])
                with col_left:
                    if st.button(f"{'📋 详情 ▼' if not st.session_state[expand_key] else '📋 详情 ▲'}",
                               key=f"btn_{expand_key}",
                               use_container_width=True):
                        st.session_state[expand_key] = not st.session_state[expand_key]

                with col_right:
                    # 操作按钮
                    if task['status'] == "pending":
                        if st.button("▶️ 开始", key=f"start_{task['id']}", use_container_width=True):
                            task['status'] = "running"
                            st.success(f"任务 #{task['id']} 已开始执行")
                            st.rerun()
                    elif task['status'] == "completed":
                        if st.button("📊 查看", key=f"view_{task['id']}", use_container_width=True):
                            st.markdown(f"""
                            <div style="
                                background: {rgba(DesignTokens.Colors.INFO, 0.1)};
                                border-left: 4px solid {DesignTokens.Colors.INFO};
                                border-radius: {DesignTokens.Radius.MD};
                                padding: {DesignTokens.Spacing.P_SM};
                                margin-bottom: {DesignTokens.Spacing.M_SM};
                            ">
                                <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                                         font-size: {DesignTokens.Typography.SMALL};">
                                    📊 查看任务 #{task['id']} 的报告...
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    elif task['status'] == "failed":
                        if st.button("🔄 重试", key=f"retry_{task['id']}", use_container_width=True):
                            task['status'] = "pending"
                            st.success(f"任务 #{task['id']} 已重置为待执行")
                            st.rerun()

                # 展开详情
                if st.session_state[expand_key]:
                    st.markdown(f"""
                    <div style="
                        background: {rgba(DesignTokens.Colors.PRIMARY, 0.05)};
                        border-radius: {DesignTokens.Radius.MD};
                        padding: {DesignTokens.Spacing.P_MD};
                        margin-bottom: {DesignTokens.Spacing.M_MD};
                    ">
                        <div style="font-size: {DesignTokens.Typography.SMALL};
                                 color: {DesignTokens.Colors.TEXT_SECONDARY};
                                 margin-bottom: {DesignTokens.Spacing.M_SM};">
                            <strong>任务详情</strong>
                        </div>
                        <div style="font-size: {DesignTokens.Typography.BODY};
                                 color: {DesignTokens.Colors.TEXT_PRIMARY};">
                            • 任务类型: {task['type']}<br>
                            • 分析深度: {task.get('depth', '标准')}<br>
                            • 创建时间: {task.get('created_at', '')}<br>
                            • 当前状态: {status_text}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 进度条
                    progress = task.get('progress', 0)
                    st.markdown(f"""
                    <div style="margin-bottom: {DesignTokens.Spacing.M_SM};">
                        <div style="font-size: {DesignTokens.Typography.SMALL};
                                 color: {DesignTokens.Colors.TEXT_SECONDARY};
                                 margin-bottom: {DesignTokens.Spacing.M_XS};">
                            执行进度
                        </div>
                        <div style="
                            background: {rgba(DesignTokens.Colors.BORDER, 0.3)};
                            border-radius: {DesignTokens.Radius.SM};
                            height: 8px;
                            overflow: hidden;
                        ">
                            <div style="
                                background: {status_color};
                                height: 100%;
                                width: {progress}%;
                                transition: width 0.3s ease;
                            "></div>
                        </div>
                        <div style="font-size: {DesignTokens.Typography.XSMALL};
                                 color: {DesignTokens.Colors.TEXT_HINT};
                                 text-align: right;
                                 margin-top: {DesignTokens.Spacing.M_XS};">
                            {progress}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 执行日志（展开）
                    with st.expander("📝 执行日志", expanded=False):
                        st.code("""
2026-03-15 10:30:01 [INFO] 任务创建成功
2026-03-15 10:30:02 [INFO] 开始初始化Agent...
2026-03-15 10:30:03 [INFO] 启动宏观经济AI...
2026-03-15 10:30:05 [INFO] 宏观经济AI分析完成
2026-03-15 10:30:06 [INFO] 启动新闻监控AI...
2026-03-15 10:30:08 [INFO] 新闻监控AI分析完成
...
                        """, language="log")

    with col_side:
        # ========== 创建任务（侧边栏）==========
        st.markdown(f"""
        <h2 style="font-size: {DesignTokens.Typography.H2};
                   color: {DesignTokens.Colors.TEXT_PRIMARY};
                   margin-bottom: {DesignTokens.Spacing.M_MD};">
            ➕ 创建任务
        </h2>
        """, unsafe_allow_html=True)

        # 创建任务表单
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <div style="font-size: {DesignTokens.Typography.H5};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};
                     font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                任务类型
            </div>
        </div>
        """, unsafe_allow_html=True)

        task_type = st.radio(
            "",
            [
                "📊 个股完整分析",
                "🏭 产业分析",
                "🔥 热点监控",
                "⚙️ 自定义组合"
            ],
            label_visibility="collapsed"
        )

        st.markdown(f"<div style='margin-bottom: {DesignTokens.Spacing.M_SM};'></div>", unsafe_allow_html=True)

        # 股票代码
        st.markdown(f"""
        <div style="font-size: {DesignTokens.Typography.SMALL};
                 color: {DesignTokens.Colors.TEXT_SECONDARY};
                 margin-bottom: {DesignTokens.Spacing.M_XS};">
            股票代码 *
        </div>
        """, unsafe_allow_html=True)

        stock_code = st.text_input(
            "",
            placeholder="例如: 000001",
            label_visibility="collapsed",
            key="create_stock_code"
        )

        # 分析深度
        st.markdown(f"<div style='margin-top: {DesignTokens.Spacing.M_SM};'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="font-size: {DesignTokens.Typography.SMALL};
                 color: {DesignTokens.Colors.TEXT_SECONDARY};
                 margin-bottom: {DesignTokens.Spacing.M_XS};">
            分析深度
        </div>
        """, unsafe_allow_html=True)

        analysis_depth = st.selectbox(
            "",
            ["快速", "标准", "深度"],
            index=1,
            label_visibility="collapsed"
        )

        # 高级选项（展开）
        with st.expander("🔧 高级选项"):
            time_range = st.select_slider(
                "时间范围",
                options=["1月", "3月", "6月", "1年", "3年"],
                value="1年"
            )

            enable_backtest = st.checkbox("启用回测验证", value=True)
            generate_report = st.checkbox("自动生成报告", value=True)

        st.markdown(f"<div style='margin-top: {DesignTokens.Spacing.M_MD};'></div>", unsafe_allow_html=True)

        # 创建按钮
        if st.button("🚀 创建任务", type="primary", use_container_width=True):
            if not stock_code:
                st.markdown(f"""
                <div style="
                    background: {rgba(DesignTokens.Colors.ERROR, 0.1)};
                    border-left: 4px solid {DesignTokens.Colors.ERROR};
                    border-radius: {DesignTokens.Radius.MD};
                    padding: {DesignTokens.Spacing.P_SM};
                    margin-bottom: {DesignTokens.Spacing.M_SM};
                ">
                    <div style="color: {DesignTokens.Colors.ERROR};
                             font-size: {DesignTokens.Typography.SMALL};">
                        ⚠️ 请输入股票代码
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 创建任务
                task = {
                    "id": len(task_history) + 1,
                    "type": task_type,
                    "stock_code": stock_code,
                    "depth": analysis_depth,
                    "status": "pending",
                    "progress": 0,
                    "created_at": datetime.now().isoformat()
                }

                # 添加到任务历史
                if 'task_history' not in st.session_state:
                    st.session_state.task_history = []

                st.session_state.task_history.append(task)

                st.markdown(f"""
                <div style="
                    background: {rgba(DesignTokens.Colors.SUCCESS, 0.1)};
                    border-left: 4px solid {DesignTokens.Colors.SUCCESS};
                    border-radius: {DesignTokens.Radius.MD};
                    padding: {DesignTokens.Spacing.P_SM};
                    margin-bottom: {DesignTokens.Spacing.M_SM};
                ">
                    <div style="color: {DesignTokens.Colors.SUCCESS};
                             font-size: {DesignTokens.Typography.BODY};
                             font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};">
                        ✅ 任务创建成功！
                    </div>
                    <div style="color: {DesignTokens.Colors.TEXT_SECONDARY};
                             font-size: {DesignTokens.Typography.SMALL};
                             margin-top: {DesignTokens.Spacing.M_XS};">
                        任务ID: #{task['id']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.rerun()

        # 快速操作
        st.markdown(f"<div style='margin-top: {DesignTokens.Spacing.M_LG};'></div>", unsafe_allow_html=True)

        st.markdown(f"""
        <h2 style="font-size: {DesignTokens.Typography.H2};
                   color: {DesignTokens.Colors.TEXT_PRIMARY};
                   margin-bottom: {DesignTokens.Spacing.M_MD};">
            ⚡ 快速操作
        </h2>
        """, unsafe_allow_html=True)

        # 批量操作
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                批量操作
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("▶️ 开始所有待执行", use_container_width=True, key="start_all_pending"):
            count = 0
            for task in task_history:
                if task['status'] == "pending":
                    task['status'] = "running"
                    count += 1
            if count > 0:
                st.success(f"已启动 {count} 个任务")
                st.rerun()
            else:
                st.markdown(f"""
                <div style="
                    background: {rgba(DesignTokens.Colors.INFO, 0.1)};
                    border-left: 4px solid {DesignTokens.Colors.INFO};
                    border-radius: {DesignTokens.Radius.MD};
                    padding: {DesignTokens.Spacing.P_SM};
                    margin-bottom: {DesignTokens.Spacing.M_SM};
                ">
                    <div style="color: {DesignTokens.Colors.INFO};
                             font-size: {DesignTokens.Typography.SMALL};">
                        ℹ️ 没有待执行的任务
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown(f"<div style='margin-top: {DesignTokens.Spacing.M_SM};'></div>", unsafe_allow_html=True)

        if st.button("🗑️ 清理已完成", use_container_width=True, key="clear_completed"):
            original_count = len(task_history)
            st.session_state.task_history = [
                t for t in task_history
                if t['status'] not in ['completed', 'failed']
            ]
            removed = original_count - len(st.session_state.task_history)
            if removed > 0:
                st.success(f"已清理 {removed} 个任务")
                st.rerun()
            else:
                st.markdown(f"""
                <div style="
                    background: {rgba(DesignTokens.Colors.INFO, 0.1)};
                    border-left: 4px solid {DesignTokens.Colors.INFO};
                    border-radius: {DesignTokens.Radius.MD};
                    padding: {DesignTokens.Spacing.P_SM};
                    margin-bottom: {DesignTokens.Spacing.M_SM};
                ">
                    <div style="color: {DesignTokens.Colors.INFO};
                             font-size: {DesignTokens.Typography.SMALL};">
                        ℹ️ 没有已完成的任务
                    </div>
                </div>
                """, unsafe_allow_html=True)


# 如果直接运行此文件
if __name__ == "__main__":
    render_task_management_v3()
