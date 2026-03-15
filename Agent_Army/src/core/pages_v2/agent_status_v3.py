"""
Agent Army - Agent状态页面 (v3.0 扁平化版)
完全基于Phase 2设计文档重构，100%使用Design Tokens

创建日期: 2026-03-15
设计文档: docs/PHASE2_DASHBOARD_DESIGN_TASK.md
实施计划: docs/PHASE3_PLAN.md 任务3.1
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


def render_agent_status_v3():
    """渲染Agent状态页面（v3.0 扁平化版）"""

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
                🤖 Agent状态
            </h1>
            <p style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin: {DesignTokens.Spacing.M_NONE} 0 {DesignTokens.Spacing.M_SM} 0;">
                24个Agent | 6大军团 | 100%完成 | 更新时间: {datetime.now().strftime('%H:%M:%S')}
            </p>
        </div>
        <div style="display: flex; gap: {DesignTokens.Spacing.M_SM};">
            <button onclick="parent.location.reload()"
                    style="padding: {DesignTokens.Spacing.P_SM} {DesignTokens.Spacing.P_MD};
                           background: {DesignTokens.Colors.PRIMARY};
                           color: {DesignTokens.Colors.WHITE};
                           border: none;
                           border-radius: {DesignTokens.Radius.MD};
                           cursor: pointer;
                           font-size: {DesignTokens.Typography.SMALL};">
                🔄 刷新
            </button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<hr style='border: 1px solid {DesignTokens.Colors.BORDER_DEFAULT}; margin: {DesignTokens.Spacing.M_LG} 0;'>", unsafe_allow_html=True)

    # ==================== 顶部统计卡片（扁平展示） ====================
    st.markdown(f"<h3 style='color: {DesignTokens.Colors.TEXT_PRIMARY}; margin-bottom: {DesignTokens.Spacing.M_MD};'>📊 Agent统计概览</h3>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            border-left: 4px solid {DesignTokens.Colors.PRIMARY};
            box-shadow: {DesignTokens.Shadow.SM};
            text-align: center;
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                Agent总数
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.PRIMARY};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                24
            </div>
            <div style="font-size: {DesignTokens.Typography.XSMALL};
                     color: {DesignTokens.Colors.SUCCESS};
                     font-weight: {DesignTokens.Typography.WEIGHT_MEDIUM};">
                100%在线
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
            text-align: center;
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                空闲
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.SUCCESS};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                18
            </div>
            <div style="font-size: {DesignTokens.Typography.XSMALL};
                     color: {DesignTokens.Colors.TEXT_HINT};
                     font-weight: {DesignTokens.Typography.WEIGHT_MEDIUM};">
                可接受任务
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            border-left: 4px solid {DesignTokens.Colors.WARNING};
            box-shadow: {DesignTokens.Shadow.SM};
            text-align: center;
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                忙碌
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.WARNING};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                5
            </div>
            <div style="font-size: {DesignTokens.Typography.XSMALL};
                     color: {DesignTokens.Colors.TEXT_HINT};
                     font-weight: {DesignTokens.Typography.WEIGHT_MEDIUM};">
                处理中
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            border-left: 4px solid {DesignTokens.Colors.ERROR};
            box-shadow: {DesignTokens.Shadow.SM};
            text-align: center;
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                错误
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.ERROR};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                1
            </div>
            <div style="font-size: {DesignTokens.Typography.XSMALL};
                     color: {DesignTokens.Colors.TEXT_HINT};
                     font-weight: {DesignTokens.Typography.WEIGHT_MEDIUM};">
                需要关注
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            border-left: 4px solid {DesignTokens.Colors.INFO};
            box-shadow: {DesignTokens.Shadow.SM};
            text-align: center;
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                可用率
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.INFO};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                95.8%
            </div>
            <div style="font-size: {DesignTokens.Typography.XSMALL};
                     color: {DesignTokens.Colors.SUCCESS};
                     font-weight: {DesignTokens.Typography.WEIGHT_MEDIUM};">
                优秀
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<hr style='border: 1px solid {DesignTokens.Colors.BORDER_DEFAULT}; margin: {DesignTokens.Spacing.M_LG} 0;'>", unsafe_allow_html=True)

    # ==================== 军团概览（扁平化，一行展示，可展开） ====================
    st.markdown(f"<h3 style='color: {DesignTokens.Colors.TEXT_PRIMARY}; margin-bottom: {DesignTokens.Spacing.M_MD};'>🏰 6大军团概览</h3>", unsafe_allow_html=True)

    # 6大军团数据（使用Session State管理展开/折叠状态）
    armies_data = [
        {
            "name": "产业分析军团",
            "icon": "🏭",
            "agent_count": 5,
            "color": DesignTokens.Colors.ARMY_INDUSTRY,
            "stars": "⭐⭐⭐",
            "completion": "125%",
            "agents": [
                {"name": "宏观经济AI", "icon": "🌍", "status": "idle", "tasks": 156, "score": 99},
                {"name": "产业链分析AI", "icon": "🔗", "status": "idle", "tasks": 142, "score": 98},
                {"name": "政策影响AI", "icon": "📜", "status": "busy", "tasks": 89, "score": 95},
                {"name": "行业周期AI", "icon": "🔄", "status": "idle", "tasks": 78, "score": 96},
                {"name": "竞争格局AI", "icon": "⚔️", "status": "idle", "tasks": 165, "score": 97}
            ]
        },
        {
            "name": "热点捕捉军团",
            "icon": "🔥",
            "agent_count": 4,
            "color": DesignTokens.Colors.ARMY_HOTSPOT,
            "stars": "⭐⭐",
            "completion": "100%",
            "agents": [
                {"name": "新闻监控AI", "icon": "📰", "status": "idle", "tasks": 289, "score": 95},
                {"name": "资金情绪AI", "icon": "💰", "status": "idle", "tasks": 312, "score": 96},
                {"name": "龙虎榜AI", "icon": "🐉", "status": "idle", "tasks": 198, "score": 94},
                {"name": "技术分析AI", "icon": "📊", "status": "busy", "tasks": 267, "score": 95}
            ]
        },
        {
            "name": "个股挖掘军团",
            "icon": "📈",
            "agent_count": 4,
            "color": DesignTokens.Colors.ARMY_STOCK,
            "stars": "⭐⭐",
            "completion": "100%",
            "agents": [
                {"name": "财务健康AI", "icon": "💹", "status": "idle", "tasks": 234, "score": 96},
                {"name": "成长性分析AI", "icon": "📊", "status": "idle", "tasks": 189, "score": 94},
                {"name": "估值AI", "icon": "💎", "status": "idle", "tasks": 145, "score": 95},
                {"name": "基本面分析AI", "icon": "📈", "status": "busy", "tasks": 178, "score": 97}
            ]
        },
        {
            "name": "目标预测军团",
            "icon": "🎯",
            "agent_count": 5,
            "color": DesignTokens.Colors.ARMY_TARGET,
            "stars": "⭐⭐⭐",
            "completion": "125%",
            "agents": [
                {"name": "质量评分AI", "icon": "⭐", "status": "idle", "tasks": 123, "score": 98},
                {"name": "股价预测AI", "icon": "📈", "status": "idle", "tasks": 234, "score": 93},
                {"name": "估值AI", "icon": "💎", "status": "idle", "tasks": 145, "score": 95},
                {"name": "技术分析AI", "icon": "📊", "status": "busy", "tasks": 267, "score": 95},
                {"name": "成长性分析AI", "icon": "📊", "status": "idle", "tasks": 189, "score": 94}
            ]
        },
        {
            "name": "策略执行军团",
            "icon": "⚡",
            "agent_count": 5,
            "color": DesignTokens.Colors.ARMY_STRATEGY,
            "stars": "⭐⭐⭐",
            "completion": "125%",
            "agents": [
                {"name": "买入时机AI", "icon": "🎯", "status": "idle", "tasks": 167, "score": 96},
                {"name": "卖出时机AI", "icon": "🎯", "status": "idle", "tasks": 145, "score": 95},
                {"name": "仓位管理AI", "icon": "⚖️", "status": "idle", "tasks": 98, "score": 97},
                {"name": "风险控制AI", "icon": "🛡️", "status": "error", "tasks": 87, "score": 92},
                {"name": "情景分析AI", "icon": "🔮", "status": "idle", "tasks": 134, "score": 96}
            ]
        },
        {
            "name": "结果验证军团",
            "icon": "✅",
            "agent_count": 5,
            "color": DesignTokens.Colors.ARMY_VALIDATION,
            "stars": "⭐⭐⭐",
            "completion": "125%",
            "agents": [
                {"name": "回测分析AI", "icon": "🔄", "status": "idle", "tasks": 189, "score": 97},
                {"name": "预测验证AI", "icon": "✓", "status": "idle", "tasks": 234, "score": 96},
                {"name": "业绩归因AI", "icon": "📊", "status": "idle", "tasks": 145, "score": 95},
                {"name": "风险归因AI", "icon": "📉", "status": "idle", "tasks": 123, "score": 94},
                {"name": "期权衍生品AI", "icon": "📈", "status": "busy", "tasks": 167, "score": 95}
            ]
        }
    ]

    # 第一行：3个军团
    col1, col2, col3 = st.columns(3)

    for idx, (col, army) in enumerate([(col1, armies_data[0]), (col2, armies_data[1]), (col3, armies_data[2])]):
        with col:
            # 军团卡片（使用军团主题色）
            st.markdown(f"""
            <div style="
                background: {rgba(army['color'], 0.05)};
                border-left: 4px solid {army['color']};
                border-radius: {DesignTokens.Radius.LG};
                padding: {DesignTokens.Spacing.P_MD};
                box-shadow: {DesignTokens.Shadow.SM};
                margin-bottom: {DesignTokens.Spacing.M_MD};
                transition: all 0.3s ease;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: {DesignTokens.Typography.H4};
                                     font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
                                     color: {army['color']};
                                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                            {army['icon']} {army['name']}
                        </div>
                        <div style="font-size: {DesignTokens.Typography.SMALL};
                                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                            {army['agent_count']}个Agent
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: {DesignTokens.Typography.H5};
                                     color: {army['color']};
                                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                            {army['stars']}
                        </div>
                        <div style="font-size: {DesignTokens.Typography.XSMALL};
                                     color: {DesignTokens.Colors.TEXT_HINT};">
                            {army['completion']}完成
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 展开/折叠按钮（使用Session State）
            expand_key = f"expand_army_{idx}"
            if expand_key not in st.session_state:
                st.session_state[expand_key] = False

            if st.button(f"{'展开详情 ▼' if not st.session_state[expand_key] else '收起详情 ▲'}",
                          key=f"toggle_{idx}",
                          use_container_width=True):
                st.session_state[expand_key] = not st.session_state[expand_key]

            # 展开：显示Agent网格
            if st.session_state[expand_key]:
                st.markdown(f"<div style='margin-top: {DesignTokens.Spacing.M_SM};'>", unsafe_allow_html=True)

                # Agent网格（2列布局）
                for i in range(0, len(army['agents']), 2):
                    agent_cols = st.columns(2)

                    for j, agent_col in enumerate(agent_cols):
                        if i + j < len(army['agents']):
                            agent = army['agents'][i + j]

                            with agent_col:
                                # Agent卡片
                                status_badge = get_status_badge("空闲" if agent['status'] == "idle" else
                                                                          ("忙碌" if agent['status'] == "busy" else "异常"))

                                score_color = DesignTokens.Colors.SUCCESS if agent['score'] >= 95 else DesignTokens.Colors.WARNING

                                st.markdown(f"""
                                <div style="
                                    background: {DesignTokens.Colors.BG_CARD};
                                    border: 1px solid {DesignTokens.Colors.BORDER_DEFAULT};
                                    border-radius: {DesignTokens.Radius.MD};
                                    padding: {DesignTokens.Spacing.P_MD};
                                    box-shadow: {DesignTokens.Shadow.XS};
                                    margin-bottom: {DesignTokens.Spacing.M_SM};
                                ">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <div>
                                            <div style="font-size: {DesignTokens.Typography.H5};
                                                         font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
                                                         color: {DesignTokens.Colors.TEXT_PRIMARY};
                                                         margin-bottom: {DesignTokens.Spacing.M_XS};">
                                                {agent['icon']} {agent['name']}
                                            </div>
                                            <div style="font-size: {DesignTokens.Typography.XSMALL};
                                                         color: {DesignTokens.Colors.TEXT_SECONDARY};">
                                                {status_badge}
                                            </div>
                                        </div>
                                        <div style="text-align: right;">
                                            <div style="font-size: {DesignTokens.Typography.SMALL};
                                                         color: {score_color};
                                                         font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                                                ⭐ {agent['score']}
                                            </div>
                                        </div>
                                    </div>
                                    <div style="margin-top: {DesignTokens.Spacing.M_SM};">
                                        <div style="font-size: {DesignTokens.Typography.SMALL};
                                                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                                            任务: {agent['tasks']} | 成功率: {agent['score']}%
                                        </div>
                                    </div>
                                    <div style="margin-top: {DesignTokens.Spacing.M_XS};">
                                        <button onclick="alert('Agent详情功能开发中...')"
                                                style="padding: {DesignTokens.Spacing.P_XS} {DesignTokens.Spacing.P_SM};
                                                       background: {DesignTokens.Colors.PRIMARY};
                                                       color: {DesignTokens.Colors.WHITE};
                                                       border: none;
                                                       border-radius: {DesignTokens.Radius.SM};
                                                       cursor: pointer;
                                                       font-size: {DesignTokens.Typography.XSMALL};">
                                            查看详情
                                        </button>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

    # 第二行：3个军团
    col4, col5, col6 = st.columns(3)

    for idx, (col, army) in enumerate([(col4, armies_data[3]), (col5, armies_data[4]), (col6, armies_data[5])]):
        offset_idx = idx + 3  # 继续索引

        with col:
            # 军团卡片（使用军团主题色）
            st.markdown(f"""
            <div style="
                background: {rgba(army['color'], 0.05)};
                border-left: 4px solid {army['color']};
                border-radius: {DesignTokens.Radius.LG};
                padding: {DesignTokens.Spacing.P_MD};
                box-shadow: {DesignTokens.Shadow.SM};
                margin-bottom: {DesignTokens.Spacing.M_MD};
                transition: all 0.3s ease;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: {DesignTokens.Typography.H4};
                                     font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
                                     color: {army['color']};
                                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                            {army['icon']} {army['name']}
                        </div>
                        <div style="font-size: {DesignTokens.Typography.SMALL};
                                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                            {army['agent_count']}个Agent
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: {DesignTokens.Typography.H5};
                                     color: {army['color']};
                                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                            {army['stars']}
                        </div>
                        <div style="font-size: {DesignTokens.Typography.XSMALL};
                                     color: {DesignTokens.Colors.TEXT_HINT};">
                            {army['completion']}完成
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 展开/折叠按钮
            expand_key = f"expand_army_{offset_idx}"
            if expand_key not in st.session_state:
                st.session_state[expand_key] = False

            if st.button(f"{'展开详情 ▼' if not st.session_state[expand_key] else '收起详情 ▲'}",
                          key=f"toggle_{offset_idx}",
                          use_container_width=True):
                st.session_state[expand_key] = not st.session_state[expand_key]

            # 展开：显示Agent网格
            if st.session_state[expand_key]:
                st.markdown(f"<div style='margin-top: {DesignTokens.Spacing.M_SM};'>", unsafe_allow_html=True)

                # Agent网格（2列布局）
                for i in range(0, len(army['agents']), 2):
                    agent_cols = st.columns(2)

                    for j, agent_col in enumerate(agent_cols):
                        if i + j < len(army['agents']):
                            agent = army['agents'][i + j]

                            with agent_col:
                                # Agent卡片
                                status_badge = get_status_badge("空闲" if agent['status'] == "idle" else
                                                                          ("忙碌" if agent['status'] == "busy" else "异常"))

                                score_color = DesignTokens.Colors.SUCCESS if agent['score'] >= 95 else DesignTokens.Colors.WARNING

                                st.markdown(f"""
                                <div style="
                                    background: {DesignTokens.Colors.BG_CARD};
                                    border: 1px solid {DesignTokens.Colors.BORDER_DEFAULT};
                                    border-radius: {DesignTokens.Radius.MD};
                                    padding: {DesignTokens.Spacing.P_MD};
                                    box-shadow: {DesignTokens.Shadow.XS};
                                    margin-bottom: {DesignTokens.Spacing.M_SM};
                                ">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <div>
                                            <div style="font-size: {DesignTokens.Typography.H5};
                                                         font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
                                                         color: {DesignTokens.Colors.TEXT_PRIMARY};
                                                         margin-bottom: {DesignTokens.Spacing.M_XS};">
                                                {agent['icon']} {agent['name']}
                                            </div>
                                            <div style="font-size: {DesignTokens.Typography.XSMALL};
                                                         color: {DesignTokens.Colors.TEXT_SECONDARY};">
                                                {status_badge}
                                            </div>
                                        </div>
                                        <div style="text-align: right;">
                                            <div style="font-size: {DesignTokens.Typography.SMALL};
                                                         color: {score_color};
                                                         font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                                                ⭐ {agent['score']}
                                            </div>
                                        </div>
                                    </div>
                                    <div style="margin-top: {DesignTokens.Spacing.M_SM};">
                                        <div style="font-size: {DesignTokens.Typography.SMALL};
                                                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                                            任务: {agent['tasks']} | 成功率: {agent['score']}%
                                        </div>
                                    </div>
                                    <div style="margin-top: {DesignTokens.Spacing.M_XS};">
                                        <button onclick="alert('Agent详情功能开发中...')"
                                                style="padding: {DesignTokens.Spacing.P_XS} {DesignTokens.Spacing.P_SM};
                                                       background: {DesignTokens.Colors.PRIMARY};
                                                       color: {DesignTokens.Colors.WHITE};
                                                       border: none;
                                                       border-radius: {DesignTokens.Radius.SM};
                                                       cursor: pointer;
                                                       font-size: {DesignTokens.Typography.XSMALL};">
                                            查看详情
                                        </button>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"<hr style='border: 1px solid {DesignTokens.Colors.BORDER_DEFAULT}; margin: {DesignTokens.Spacing.M_XL} 0;'>", unsafe_allow_html=True)

    # ==================== 快速筛选和操作 ====================
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 刷新状态", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("📊 性能报告", use_container_width=True):
            st.markdown(f"""
            <div style="
                background: {rgba(DesignTokens.Colors.INFO, 0.1)};
                border-left: 4px solid {DesignTokens.Colors.INFO};
                border-radius: {DesignTokens.Radius.MD};
                padding: {DesignTokens.Spacing.P_MD};
                margin: {DesignTokens.Spacing.M_SM} 0;
            ">
                <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                         font-size: {DesignTokens.Typography.SMALL};">
                    📊 性能报告页面开发中...
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        if st.button("⚙️ Agent配置", use_container_width=True):
            st.markdown(f"""
            <div style="
                background: {rgba(DesignTokens.Colors.INFO, 0.1)};
                border-left: 4px solid {DesignTokens.Colors.INFO};
                border-radius: {DesignTokens.Radius.MD};
                padding: {DesignTokens.Spacing.P_MD};
                margin: {DesignTokens.Spacing.M_SM} 0;
            ">
                <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                         font-size: {DesignTokens.Typography.SMALL};">
                    ⚙️ 请前往【⚙️ 系统配置】页面
                </div>
            </div>
            """, unsafe_allow_html=True)


# 如果直接运行此文件
if __name__ == "__main__":
    render_agent_status_v3()
