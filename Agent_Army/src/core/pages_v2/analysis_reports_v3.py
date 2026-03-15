"""
Agent Army - 分析报告页面 (v3.0 优化版)
完全基于Phase 2设计文档重构，100%使用Design Tokens
"""

import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys
import pandas as pd

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入Phase 1设计系统
from src.core.design_tokens import DesignTokens
from src.core.global_styles import apply_global_styles
from src.core.ui_components import create_metric_card, get_status_badge


def rgba(hex_color: str, alpha: float) -> str:
    """将hex颜色转换为rgba格式"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def render_analysis_reports_v3():
    """渲染分析报告页面（v3.0 优化版）"""

    # 应用全局样式
    apply_global_styles()

    # 页面标题
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: {DesignTokens.Spacing.M_LG};">
        <div>
            <h1 style="font-size: {DesignTokens.Typography.H1};
                      color: {DesignTokens.Colors.TEXT_PRIMARY};
                      margin: 0;
                      font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                📊 分析报告
            </h1>
            <p style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin: {DesignTokens.Spacing.M_NONE} 0 {DesignTokens.Spacing.M_SM} 0;">
                24个Agent综合分析 | 6大军团协同输出
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 顶部操作栏
    col1, col2, col3, col4 = st.columns(4)

    with col2:
        report_type = st.selectbox(
            "报告类型",
            ["📈 股票分析", "🏗️ 产业分析", "🎯 策略建议", "📋 归因分析"],
            label_visibility="collapsed"
        )

    # 根据报告类型显示不同的输入框
    with col1:
        if report_type == "📈 股票分析":
            # 股票分析需要股票代码
            from src.core.utils.stock_code_resolver import resolve_stock_code, get_stock_name

            stock_input = st.text_input(
                "股票代码/名称",
                placeholder="例如: 600519 或 贵州茅台",
                label_visibility="collapsed"
            )

            # 实时解析
            if stock_input:
                resolved_code = resolve_stock_code(stock_input)
                if resolved_code:
                    stock_name = get_stock_name(resolved_code)
                    st.success(f"✅ {resolved_code} - {stock_name or '已知股票'}")
                    target_input = resolved_code
                else:
                    target_input = stock_input

        elif report_type == "🏗️ 产业分析":
            # 产业分析需要行业名称
            target_input = st.text_input(
                "行业名称",
                placeholder="例如: 新能源汽车、半导体、白酒",
                label_visibility="collapsed"
            )

        elif report_type == "🎯 策略建议":
            # 策略建议可以留空（分析整体市场）
            target_input = st.text_input(
                "关注领域（可选）",
                placeholder="例如: 科技股、消费股、或留空分析整体",
                label_visibility="collapsed"
            )

        elif report_type == "📋 归因分析":
            # 归因分析需要报告ID或股票代码
            target_input = st.text_input(
                "报告ID或股票代码",
                placeholder="例如: RPT-001 或 600519",
                label_visibility="collapsed"
            )

    with col3:
        date_range = st.selectbox(
            "时间范围",
            ["1个月", "3个月", "6个月", "1年"],
            index=2,
            label_visibility="collapsed"
        )

    with col4:
        if st.button("🔍 生成报告", type="primary", use_container_width=True):
            # 根据报告类型验证输入
            if report_type == "📈 股票分析":
                if target_input:
                    st.success(f"✅ 正在生成 {target_input} 的股票分析报告...")
                else:
                    st.error("❌ 请输入股票代码或名称")

            elif report_type == "🏗️ 产业分析":
                if target_input:
                    st.success(f"✅ 正在生成「{target_input}」的产业分析报告...")
                else:
                    st.error("❌ 请输入行业名称")

            elif report_type == "🎯 策略建议":
                if target_input:
                    st.success(f"✅ 正在生成「{target_input}」的策略建议报告...")
                else:
                    st.success("✅ 正在生成整体市场策略建议报告...")

            elif report_type == "📋 归因分析":
                if target_input:
                    st.success(f"✅ 正在生成 {target_input} 的归因分析...")
                else:
                    st.error("❌ 请输入报告ID或股票代码")

    st.markdown(f"<div style='margin-bottom: {DesignTokens.Spacing.M_LG};'></div>", unsafe_allow_html=True)

    # ==================== 报告类型卡片（扁平化展示） ====================

    # 股票分析报告
    st.markdown(f"""
    <h2 style="font-size: {DesignTokens.Typography.H2};
               color: {DesignTokens.Colors.TEXT_PRIMARY};
               margin-bottom: {DesignTokens.Spacing.M_MD};">
        📈 股票分析报告
    </h2>
    """, unsafe_allow_html=True)

    # 报告概览卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
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
                综合评分
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.SUCCESS};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                78
            </div>
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_HINT};
                     margin-top: {DesignTokens.Spacing.M_XS};">
                A-评级
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
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
                技术面
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.INFO};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                82
            </div>
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_HINT};
                     margin-top: {DesignTokens.Spacing.M_XS};">
                强烈买入
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
                基本面
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.WARNING};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                75
            </div>
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_HINT};
                     margin-top: {DesignTokens.Spacing.M_XS};">
                买入
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
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
                风险评估
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.PRIMARY};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                中等
            </div>
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_HINT};
                     margin-top: {DesignTokens.Spacing.M_XS};">
                风险可控
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<div style='margin-bottom: {DesignTokens.Spacing.M_LG};'></div>", unsafe_allow_html=True)

    # 详细分析区域（展开式）
    expand_details = st.expander("📋 详细分析", expanded=False)

    with expand_details:
        # 军团分析卡片
        st.markdown(f"""
        <h3 style="font-size: {DesignTokens.Typography.H3};
                   color: {DesignTokens.Colors.TEXT_PRIMARY};
                   margin-bottom: {DesignTokens.Spacing.M_SM};">
            6大军团分析结果
        </h3>
        """, unsafe_allow_html=True)

        # 产业分析军团
        st.markdown(f"""
        <div style="
            background: {rgba(DesignTokens.Colors.ARMY_INDUSTRY, 0.05)};
            border-left: 4px solid {DesignTokens.Colors.ARMY_INDUSTRY};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <div style="font-size: {DesignTokens.Typography.H4};
                     color: {DesignTokens.Colors.ARMY_INDUSTRY};
                     font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                🏭 产业分析军团
            </div>
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                <strong>宏观环境</strong>: 经济政策利好，行业发展稳定<br>
                <strong>行业地位</strong>: 行业龙头，市场份额领先<br>
                <strong>建议</strong>: <span style="color: {DesignTokens.Colors.SUCCESS};">✅ 增持持有</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 热点捕捉军团
        st.markdown(f"""
        <div style="
            background: {rgba(DesignTokens.Colors.ARMY_HOTSPOT, 0.05)};
            border-left: 4px solid {DesignTokens.Colors.ARMY_HOTSPOT};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <div style="font-size: {DesignTokens.Typography.H4};
                     color: {DesignTokens.Colors.ARMY_HOTSPOT};
                     font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                🔥 热点捕捉军团
            </div>
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                <strong>市场情绪</strong>: 当前市场热度较高<br>
                <strong>资金流向</strong>: 主力资金持续流入<br>
                <strong>建议</strong>: <span style="color: {DesignTokens.Colors.WARNING};">⚠️ 注意回调风险</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 个股挖掘军团
        st.markdown(f"""
        <div style="
            background: {rgba(DesignTokens.Colors.ARMY_STOCK, 0.05)};
            border-left: 4px solid {DesignTokens.Colors.ARMY_STOCK};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <div style="font-size: {DesignTokens.Typography.H4};
                     color: {DesignTokens.Colors.ARMY_STOCK};
                     font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                📈 个股挖掘军团
            </div>
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                <strong>财务健康</strong>: 财务状况优秀<br>
                <strong>成长性</strong>: 营收稳定增长<br>
                <strong>建议</strong>: <span style="color: {DesignTokens.Colors.SUCCESS};">✅ 买入持有</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 目标预测军团
        st.markdown(f"""
        <div style="
            background: {rgba(DesignTokens.Colors.ARMY_TARGET, 0.05)};
            border-left: 4px solid {DesignTokens.Colors.ARMY_TARGET};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <div style="font-size: {DesignTokens.Typography.H4};
                     color: {DesignTokens.Colors.ARMY_TARGET};
                     font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                🎯 目标预测军团
            </div>
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                <strong>目标价位</strong>: 预测涨幅 15-25%<br>
                <strong>时间周期</strong>: 3-6个月<br>
                <strong>建议</strong>: <span style="color: {DesignTokens.Colors.SUCCESS};">✅ 分批建仓</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 策略执行军团
        st.markdown(f"""
        <div style="
            background: {rgba(DesignTokens.Colors.ARMY_STRATEGY, 0.05)};
            border-left: 4px solid {DesignTokens.Colors.ARMY_STRATEGY};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <div style="font-size: {DesignTokens.Typography.H4};
                     color: {DesignTokens.Colors.ARMY_STRATEGY};
                     font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                ⚔️ 策略执行军团
            </div>
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                <strong>执行策略</strong>: 价值投资+波段操作<br>
                <strong>仓位管理</strong>: 建议仓位 30-50%<br>
                <strong>建议</strong>: <span style="color: {DesignTokens.Colors.INFO};">ℹ️ 严格执行纪律</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 结果验证军团
        st.markdown(f"""
        <div style="
            background: {rgba(DesignTokens.Colors.ARMY_VALIDATION, 0.05)};
            border-left: 4px solid {DesignTokens.Colors.ARMY_VALIDATION};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <div style="font-size: {DesignTokens.Typography.H4};
                     color: {DesignTokens.Colors.ARMY_VALIDATION};
                     font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                ✅ 结果验证军团
            </div>
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                <strong>历史准确率</strong>: 78%<br>
                <strong>风险收益比</strong>: 1:3.5<br>
                <strong>建议</strong>: <span style="color: {DesignTokens.Colors.SUCCESS};">✅ 信号可靠</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 图表可视化区域
        st.markdown(f"""
        <h3 style="font-size: {DesignTokens.Typography.H3};
                   color: {DesignTokens.Colors.TEXT_PRIMARY};
                   margin-top: {DesignTokens.Spacing.M_LG};
                   margin-bottom: {DesignTokens.Spacing.M_SM};">
            📊 趋势分析图表
        </h3>
        """, unsafe_allow_html=True)

        # 评分雷达图和趋势图
        col1, col2 = st.columns(2)

        with col1:
            # 创建雷达图数据
            categories = ['产业分析', '热点捕捉', '个股挖掘', '目标预测', '策略执行', '结果验证']
            values = [82, 75, 88, 80, 78, 85]

            # 转换PRIMARY颜色为RGB
            primary_rgb = tuple(int(DesignTokens.Colors.PRIMARY[i:i+2], 16) for i in (1, 3, 5))

            fig_radar = go.Figure(data=go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                line_color=DesignTokens.Colors.PRIMARY,
                fillcolor=f"rgba({primary_rgb[0]}, {primary_rgb[1]}, {primary_rgb[2]}, 0.2)"
            ))

            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=False,
                height=400,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(
                    family="Microsoft YaHei, SimHei, Arial",
                    size=12,
                    color=DesignTokens.Colors.TEXT_PRIMARY
                )
            )

            st.plotly_chart(fig_radar, use_container_width=True)

        with col2:
            # 创建趋势图数据
            dates = pd.date_range(end=datetime.now(), periods=30)
            trend_scores = [65 + i * 0.5 + (i % 3) * 2 for i in range(30)]

            fig_trend = go.Figure()

            fig_trend.add_trace(go.Scatter(
                x=dates,
                y=trend_scores,
                mode='lines+markers',
                name='综合评分',
                line=dict(color=DesignTokens.Colors.PRIMARY, width=2),
                marker=dict(size=6)
            ))

            # 转换BORDER颜色为RGB
            border_rgb = tuple(int(DesignTokens.Colors.BORDER_DEFAULT[i:i+2], 16) for i in (1, 3, 5))

            fig_trend.update_layout(
                title='近30天评分趋势',
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor=DesignTokens.Colors.BG_CARD,
                font=dict(
                    family="Microsoft YaHei, SimHei, Arial",
                    size=12,
                    color=DesignTokens.Colors.TEXT_PRIMARY
                ),
                xaxis=dict(
                    showgrid=True,
                    gridcolor=f"rgba({border_rgb[0]}, {border_rgb[1]}, {border_rgb[2]}, 0.2)",
                    color=DesignTokens.Colors.TEXT_SECONDARY
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=f"rgba({border_rgb[0]}, {border_rgb[1]}, {border_rgb[2]}, 0.2)",
                    color=DesignTokens.Colors.TEXT_SECONDARY,
                    range=[60, 90]
                )
            )

            st.plotly_chart(fig_trend, use_container_width=True)

        # 详细数据表格
        st.markdown(f"""
        <h3 style="font-size: {DesignTokens.Typography.H3};
                   color: {DesignTokens.Colors.TEXT_PRIMARY};
                   margin-top: {DesignTokens.Spacing.M_LG};
                   margin-bottom: {DesignTokens.Spacing.M_SM};">
            📋 详细分析数据
        </h3>
        """, unsafe_allow_html=True)

        # 创建详细数据表格
        detail_data = {
            '军团': ['产业分析', '热点捕捉', '个股挖掘', '目标预测', '策略执行', '结果验证'],
            '评分': [82, 75, 88, 80, 78, 85],
            '评级': ['A', 'B+', 'A+', 'A', 'B+', 'A'],
            '关键指标': ['政策利好', '资金流入', '财务优秀', '涨幅15-25%', '仓位30-50%', '准确率78%'],
            '操作建议': ['增持持有', '注意回调', '买入持有', '分批建仓', '严格执行', '信号可靠']
        }

        df = pd.DataFrame(detail_data)

        # 自定义表格样式
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            box-shadow: {DesignTokens.Shadow.SM};
            overflow-x: auto;
        ">
        """, unsafe_allow_html=True)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                '军团': st.column_config.TextColumn('军团', width='medium'),
                '评分': st.column_config.ProgressColumn('评分', format='%d', min_value=0, max_value=100),
                '评级': st.column_config.TextColumn('评级', width='small'),
                '关键指标': st.column_config.TextColumn('关键指标', width='large'),
                '操作建议': st.column_config.TextColumn('操作建议', width='medium')
            }
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # 导出功能
    st.markdown(f"<div style='margin-top: {DesignTokens.Spacing.M_LG};'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 导出PDF报告", use_container_width=True):
            st.markdown(f"""
            <div style="
                background: {rgba(DesignTokens.Colors.PRIMARY, 0.1)};
                border-left: 4px solid {DesignTokens.Colors.PRIMARY};
                border-radius: {DesignTokens.Radius.MD};
                padding: {DesignTokens.Spacing.P_SM};
                margin-bottom: {DesignTokens.Spacing.M_SM};
            ">
                <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                         font-size: {DesignTokens.Typography.SMALL};">
                    📄 PDF报告导出功能开发中...
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        if st.button("📊 导出Excel数据", use_container_width=True):
            st.markdown(f"""
            <div style="
                background: {rgba(DesignTokens.Colors.SUCCESS, 0.1)};
                border-left: 4px solid {DesignTokens.Colors.SUCCESS};
                border-radius: {DesignTokens.Radius.MD};
                padding: {DesignTokens.Spacing.P_SM};
                margin-bottom: {DesignTokens.Spacing.M_SM};
            ">
                <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                         font-size: {DesignTokens.Typography.SMALL};">
                    📊 Excel导出功能开发中...
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        if st.button("🔗 分享报告", use_container_width=True):
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
                    🔗 分享链接功能开发中...
                </div>
            </div>
            """, unsafe_allow_html=True)

