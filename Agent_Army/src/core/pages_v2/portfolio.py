"""
Agent Army - 投资组合页面 (v2.0)
组合管理、风险分析、业绩归因
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


def render_portfolio():
    """渲染投资组合页面"""

    st.title("💹 投资组合")
    st.markdown("**组合管理 | 风险分析 | 业绩归因 | 优化建议**")
    st.markdown("---")

    # ========== 标签页 ==========
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 组合概览",
        "📈 持仓管理",
        "⚖️ 风险分析",
        "📊 业绩归因",
        "🔄 组合优化"
    ])

    # ========== 组合概览 ==========
    with tab1:
        render_portfolio_overview()

    # ========== 持仓管理 ==========
    with tab2:
        render_holdings_management()

    # ========== 风险分析 ==========
    with tab3:
        render_risk_analysis()

    # ========== 业绩归因 ==========
    with tab4:
        render_performance_attribution()

    # ========== 组合优化 ==========
    with tab5:
        render_portfolio_optimization()


def render_portfolio_overview():
    """组合概览"""

    st.markdown("### 📊 组合概览")

    # 顶部统计卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💰 总市值",
            value="¥1,250,000",
            delta="+5.2%"
        )

    with col2:
        st.metric(
            label="📈 今日盈亏",
            value="+¥12,500",
            delta="+1.0%"
        )

    with col3:
        st.metric(
            label="📊 累计盈亏",
            value="+¥125,000",
            delta="+10.0%"
        )

    with col4:
        st.metric(
            label="🎯 夏普比率",
            value="1.5",
            delta="优秀"
        )

    st.markdown("---")

    # 组合收益曲线
    st.markdown("#### 📈 组合收益曲线")

    # 生成模拟数据
    dates = pd.date_range(start='2025-01-01', end='2026-03-14', freq='D')
    portfolio_values = [1000000]
    for i in range(len(dates) - 1):
        change = portfolio_values[-1] * (0.0005 + 0.002 * (2 * (i % 10) / 10 - 1))
        portfolio_values.append(portfolio_values[-1] + change)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=portfolio_values,
        mode='lines',
        name='组合价值',
        line=dict(color='#1E88E5', width=2)
    ))

    fig.update_layout(
        height=400,
        xaxis_title="日期",
        yaxis_title="组合价值",
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

    # 资产配置
    st.markdown("#### 🥧 资产配置")

    col1, col2 = st.columns(2)

    with col1:
        # 行业分布饼图
        industries = ['银行', '科技', '医药', '消费', '新能源', '其他']
        weights = [25, 20, 15, 15, 15, 10]

        fig = go.Figure(data=[go.Pie(
            labels=industries,
            values=weights,
            hole=0.4
        )])

        fig.update_layout(
            title="行业分布",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 持仓集中度
        st.markdown("**📊 持仓集中度**")
        st.markdown("- 前5大持仓: 65%")
        st.markdown("- 前10大持仓: 85%")
        st.markdown("- HHI指数: 0.15 (分散度良好)")

        st.markdown("")
        st.markdown("**⚖️ 风险指标**")
        st.markdown("- 组合波动率: 18.5%")
        st.markdown("- Beta: 0.95")
        st.markdown("- 最大回撤: -8.2%")
        st.markdown("- VaR (95%): -2.3%")

    # 快速操作
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("➕ 添加持仓", use_container_width=True):
            st.info("请前往【持仓管理】页面添加")

    with col2:
        if st.button("⚖️ 风险检查", use_container_width=True):
            st.info("请前往【风险分析】页面查看")

    with col3:
        if st.button("🔄 优化建议", use_container_width=True):
            st.info("请前往【组合优化】页面查看")


def render_holdings_management():
    """持仓管理"""

    st.markdown("### 📈 持仓管理")

    # 操作按钮
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search = st.text_input("搜索股票", placeholder="输入股票代码或名称", label_visibility="collapsed")

    with col2:
        if st.button("➕ 添加持仓", type="primary", use_container_width=True):
            st.session_state.show_add_holding = True

    with col3:
        if st.button("📊 批量分析", use_container_width=True):
            st.info("批量分析功能开发中...")

    st.markdown("---")

    # 持仓列表
    holdings = [
        {
            "code": "000001",
            "name": "平安银行",
            "shares": 10000,
            "cost": 12.5,
            "current": 14.05,
            "market_value": 140500,
            "weight": 11.2,
            "profit": 15500,
            "profit_pct": 12.4,
            "rating": "A",
            "risk": "中"
        },
        {
            "code": "600036",
            "name": "招商银行",
            "shares": 8000,
            "cost": 35.0,
            "current": 33.5,
            "market_value": 268000,
            "weight": 21.4,
            "profit": -12000,
            "profit_pct": -4.3,
            "rating": "A+",
            "risk": "中"
        },
        {
            "code": "002594",
            "name": "比亚迪",
            "shares": 5000,
            "cost": 250.0,
            "current": 285.0,
            "market_value": 142500,
            "weight": 11.4,
            "profit": 17500,
            "profit_pct": 14.0,
            "rating": "A",
            "risk": "中高"
        },
        {
            "code": "300750",
            "name": "宁德时代",
            "shares": 4000,
            "cost": 180.0,
            "current": 195.0,
            "market_value": 78000,
            "weight": 6.2,
            "profit": 6000,
            "profit_pct": 8.3,
            "rating": "B+",
            "risk": "高"
        }
    ]

    # 表头
    col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 1, 1, 1, 1, 1])

    with col1:
        st.markdown("**股票**")
    with col2:
        st.markdown("**市值**")
    with col3:
        st.markdown("**权重**")
    with col4:
        st.markdown("**盈亏**")
    with col5:
        st.markdown("**评级**")
    with col6:
        st.markdown("**风险**")
    with col7:
        st.markdown("**操作**")

    st.markdown("---")

    # 持仓列表
    total_profit = 0

    for holding in holdings:
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 1, 1, 1, 1, 1])

        with col1:
            st.markdown(f"**{holding['code']}**")
            st.caption(holding['name'])

        with col2:
            st.markdown(f"¥{holding['market_value']:,.0f}")

        with col3:
            st.markdown(f"{holding['weight']}%")

        with col4:
            profit_emoji = "🟢" if holding['profit'] > 0 else "🔴"
            st.markdown(f"{profit_emoji} ¥{holding['profit']:,.0f}")
            st.caption(f"{holding['profit_pct']:+.1f}%")

        with col5:
            rating_color = "🟢" if holding['rating'] in ["A+", "A"] else "🟡"
            st.markdown(f"{rating_color} {holding['rating']}")

        with col6:
            risk_color = {
                "低": "🟢",
                "中": "🟡",
                "中高": "🟠",
                "高": "🔴"
            }.get(holding['risk'], "🟡")
            st.markdown(f"{risk_color} {holding['risk']}")

        with col7:
            if st.button("📊", key=f"analyze_{holding['code']}", help="详细分析"):
                st.info(f"正在分析 {holding['code']}...")

        total_profit += holding['profit']

    # 总计
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("持仓数量", "10只")

    with col2:
        total_value = sum(h['market_value'] for h in holdings)
        st.metric("总市值", f"¥{total_value:,.0f}")

    with col3:
        st.metric("总盈亏", f"¥{total_profit:,.0f}")

    with col4:
        st.metric("平均评级", "A-")


def render_risk_analysis():
    """风险分析"""

    st.markdown("### ⚖️ 风险分析")

    # 风险指标卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📊 组合波动率",
            value="18.5%",
            delta="中等风险"
        )

    with col2:
        st.metric(
            label="β Beta系数",
            value="0.95",
            delta="略低于市场"
        )

    with col3:
        st.metric(
            label="📉 最大回撤",
            value="-8.2%",
            delta="控制良好"
        )

    with col4:
        st.metric(
            label="⚠️ VaR (95%)",
            value="-2.3%",
            delta="可接受"
        )

    st.markdown("---")

    # 风险分解
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎯 风险归因")

        # 风险来源饼图
        risk_sources = ['市场风险', '行业风险', '个股风险', '流动性风险']
        risk_values = [45, 25, 20, 10]

        fig = go.Figure(data=[go.Pie(
            labels=risk_sources,
            values=risk_values,
            hole=0.4
        )])

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 📊 风险指标明细")

        risk_metrics = [
            ("市场风险", "45%", "系统性风险", "中"),
            ("行业风险", "25%", "行业集中度", "中"),
            ("个股风险", "20%", "个股波动", "中高"),
            ("流动性风险", "10%", "变现能力", "低")
        ]

        for metric, value, desc, level in risk_metrics:
            level_color = {
                "低": "🟢",
                "中": "🟡",
                "中高": "🟠",
                "高": "🔴"
            }.get(level, "🟡")

            st.markdown(f"**{metric}**: {value} - {desc} {level_color}")

    # 风险提示
    st.markdown("---")
    st.markdown("#### ⚠️ 风险提示")

    st.warning("""
    1. **集中度风险**: 前5大持仓占比65%，建议适度分散
    2. **行业风险**: 银行股占比25%，受降息影响较大
    3. **个股风险**: 宁德时代Beta较高，波动性大
    """)

    if st.button("📋 生成风险报告", type="primary"):
        st.info("风险报告生成功能开发中...")


def render_performance_attribution():
    """业绩归因"""

    st.markdown("### 📊 业绩归因分析")

    st.info("🚧 业绩归因分析页面开发中...")
    st.markdown("""
    将包含：
    - **收益归因**: 选股贡献 vs 择时贡献
    - **因子归因**: 价值、成长、质量、动量因子
    - **行业归因**: 行业配置贡献
    - **风格归因**: 大盘/小盘、成长/价值
    - **Brinson归因**: 配置效应 + 选择效应
    """)


def render_portfolio_optimization():
    """组合优化"""

    st.markdown("### 🔄 组合优化建议")

    st.info("🚧 组合优化页面开发中...")
    st.markdown("""
    将包含：
    - **再平衡建议**: 偏离目标权重的持仓
    - **风险优化**: 降低组合风险的调整方案
    - **收益优化**: 提升预期收益的调整方案
    - **成本优化**: 降低交易成本的调整策略
    """)


# 如果直接运行此文件
if __name__ == "__main__":
    render_portfolio()
