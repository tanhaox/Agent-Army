"""
Agent Army - 分析报告页面 (v2.0)
股票分析、产业分析、策略建议、归因分析
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


def render_analysis_reports():
    """渲染分析报告页面"""

    st.title("📊 分析报告")
    st.markdown("**24个Agent综合分析报告 | 6大军团协同输出**")
    st.markdown("---")

    # ========== 报告类型选择 ==========
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 股票分析报告",
        "🏗️ 产业分析报告",
        "🎯 策略建议报告",
        "📋 归因分析报告"
    ])

    # ========== 股票分析报告 ==========
    with tab1:
        render_stock_analysis_report()

    # ========== 产业分析报告 ==========
    with tab2:
        render_industry_analysis_report()

    # ========== 策略建议报告 ==========
    with tab3:
        render_strategy_report()

    # ========== 归因分析报告 ==========
    with tab4:
        render_attribution_report()


def render_stock_analysis_report():
    """股票分析报告"""

    st.markdown("### 📈 股票完整分析报告")

    # 股票代码输入
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        stock_code = st.text_input(
            "股票代码",
            placeholder="例如：000001",
            key="report_stock_code"
        )

    with col2:
        report_date = st.date_input(
            "报告日期",
            value=datetime.now(),
            key="report_date"
        )

    with col3:
        if st.button("🔍 生成报告", type="primary", use_container_width=True):
            if stock_code:
                st.session_state.generate_report = True
                st.session_state.report_stock = stock_code

    st.markdown("---")

    # 检查是否生成报告
    if not st.session_state.get('generate_report', False):
        st.info("👆 请输入股票代码并点击【生成报告】")
        return

    stock = st.session_state.get('report_stock', '000001')

    # ========== 报告头部 ==========
    st.markdown(f"#### 📊 {stock} - 平安银行 综合分析报告")
    st.markdown(f"**报告日期**: {report_date} | **分析Agent**: 24个 | **报告生成**: {datetime.now().strftime('%H:%M:%S')}")

    # 投资评级卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📊 综合评分",
            value="78",
            delta="A-评级"
        )

    with col2:
        st.metric(
            label="🎯 目标价",
            value="15.8",
            delta="+12.5%"
        )

    with col3:
        st.metric(
            label="⚖️ 风险等级",
            value="中",
            delta="可控"
        )

    with col4:
        st.metric(
            label="💡 投资建议",
            value="买入",
            delta="强烈推荐"
        )

    st.markdown("---")

    # ========== 1. 宏观经济分析 ==========
    with st.expander("🌍 1. 宏观经济分析 (宏观经济AI)", expanded=True):
        st.markdown("#### 宏观经济环境")

        col1, col2 = st.columns(2)

        with col1:
            # 经济增长
            st.markdown("**📈 经济增长**")
            st.markdown("- GDP增速: 5.2% (平稳)")
            st.markdown("- PMI: 50.8 (扩张)")
            st.markdown("- 工业增加值: 6.1% (良好)")

            # 货币政策
            st.markdown("**💰 货币政策**")
            st.markdown("- LPR 1年: 3.45% (降息)")
            st.markdown("- M2增速: 9.7% (宽松)")
            st.markdown("- 社融: 35,000亿 (积极)")

        with col2:
            # 通胀分析
            st.markdown("**📊 通胀分析**")
            st.markdown("- CPI: 0.7% (温和)")
            st.markdown("- PPI: -2.5% (通缩压力)")
            st.markdown("- 核心CPI: 1.2% (稳定)")

            # 政策导向
            st.markdown("**📜 政策导向**")
            st.markdown("- 稳增长政策持续")
            st.markdown("- 降准降息空间存在")
            st.markdown("- 财政政策积极")

        # 投资环境评级
        st.success("✅ 投资环境评级: **B+ (良好)** - 宏观环境整体稳定，政策支持力度较强")

    # ========== 2. 产业分析 ==========
    with st.expander("🏭 2. 产业分析军团报告", expanded=True):
        st.markdown("#### 银行行业分析")

        # 产业链分析
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🔗 产业链位置**")
            st.markdown("- **上游**: 央行货币政策")
            st.markdown("- **中游**: 银行信贷投放")
            st.markdown("- **下游**: 企业/个人贷款")
            st.info("产业链地位: 核心中枢")

        with col2:
            st.markdown("**📊 竞争格局**")
            st.markdown("- 市场集中度CR4: 45%")
            st.markdown("- 行业排名: 前5名")
            st.markdown("- 竞争优势: 规模优势、品牌效应")
            st.info("竞争地位: 龙头企业")

        # 行业周期
        st.markdown("**🔄 行业周期**")
        st.markdown("- 当前阶段: 成熟期")
        st.markdown("- 周期位置: 60% (中后期)")
        st.markdown("- 未来走势: 稳定增长")

        # 政策影响
        st.markdown("**📜 政策影响**")
        st.markdown("- 降准降息: 正面影响 +3")
        st.markdown("- 房地产政策: 中性影响 0")
        st.markdown("- 金融监管: 正面影响 +2")

        st.success("✅ 产业评级: **A- (良好)** - 行业地位稳固，政策支持")

    # ========== 3. 公司基本面 ==========
    with st.expander("📈 3. 个股挖掘军团报告", expanded=True):
        st.markdown("#### 平安银行基本面分析")

        # 财务健康
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**💊 财务健康**")
            st.markdown("- 不良率: 1.05% (下降)")
            st.markdown("- 拨备覆盖率: 290% (充足)")
            st.markdown("- 资本充足率: 13.5% (达标)")
            st.markdown("- ROE: 11.2% (良好)")
            st.success("财务健康度: **A**")

        with col2:
            st.markdown("**📈 成长性**")
            st.markdown("- 营收增速: 8.5% (稳定)")
            st.markdown("- 利润增速: 12.3% (良好)")
            st.markdown("- CAGR 3年: 10.2%")
            st.markdown("- 增长质量: 可持续")
            st.info("成长性评分: **B+**")

        # 估值分析
        st.markdown("**💰 估值分析**")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("PE (TTM)", "5.8", "低估")

        with col2:
            st.metric("PB", "0.65", "破净")

        with col3:
            st.metric("股息率", "5.2%", "高股息")

        st.success("✅ 基本面评级: **A (优秀)** - 财务稳健，估值合理")

    # ========== 4. 技术分析 ==========
    with st.expander("📊 4. 技术分析AI报告", expanded=False):
        st.markdown("#### 技术面分析")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📈 趋势分析**")
            st.markdown("- 短期趋势: 上涨")
            st.markdown("- 中期趋势: 震荡")
            st.markdown("- 长期趋势: 上涨")

            st.markdown("**📊 技术指标**")
            st.markdown("- MA5 > MA10: 多头排列")
            st.markdown("- MACD: 金叉")
            st.markdown("- RSI: 65 (强势)")

        with col2:
            st.markdown("**💰 资金流向**")
            st.markdown("- 主力净流入: +2.5亿")
            st.markdown("- 散户净流入: -1.2亿")
            st.markdown("- 机构净流入: +3.7亿")

            st.markdown("**🔥 市场情绪**")
            st.markdown("- 情绪指数: 72 (乐观)")
            st.markdown("- 热度排名: 前10%")
            st.markdown("- 换手率: 1.5%")

        st.info("✅ 技术面评级: **B+** - 短期上涨趋势，资金流入")

    # ========== 5. 新闻监控 ==========
    with st.expander("📰 5. 新闻监控AI报告", expanded=False):
        st.markdown("#### 近期新闻事件")

        news_items = [
            {
                "time": "2026-03-14 14:30",
                "title": "央行降准0.5个百分点",
                "impact": "正面",
                "score": 85
            },
            {
                "time": "2026-03-13 10:15",
                "title": "平安银行发布年报",
                "impact": "正面",
                "score": 80
            },
            {
                "time": "2026-03-12 16:45",
                "title": "金融监管政策优化",
                "impact": "中性",
                "score": 60
            }
        ]

        for news in news_items:
            col1, col2, col3 = st.columns([2, 3, 1])

            with col1:
                st.markdown(f"**{news['time']}**")

            with col2:
                impact_emoji = "🟢" if news['impact'] == "正面" else "🟡"
                st.markdown(f"{impact_emoji} {news['title']}")

            with col3:
                st.markdown(f"影响分: {news['score']}")

        st.info("✅ 新闻影响: **正面** - 降准利好，年报业绩良好")

    # ========== 6. 综合评估 ==========
    st.markdown("---")
    st.markdown("### 🎯 综合评估")

    # 评分雷达图
    categories = ['宏观经济', '产业分析', '基本面', '技术面', '资金面', '新闻面']
    values = [75, 85, 90, 78, 82, 85]

    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        height=400
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 📊 评分明细")

        for cat, val in zip(categories, values):
            st.markdown(f"**{cat}**: {val}/100")

        st.markdown("---")
        st.markdown("#### 💡 投资建议")

        st.success("✅ **强烈推荐买入**")
        st.markdown("- 目标价: **15.8元** (+12.5%)")
        st.markdown("- 止损价: **13.2元** (-6.3%)")
        st.markdown("- 建议仓位: **15-20%**")
        st.markdown("- 持有期限: **6-12个月**")

    # ========== 导出报告 ==========
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 导出PDF报告", use_container_width=True):
            st.info("PDF导出功能开发中...")

    with col2:
        if st.button("📊 导出Excel报告", use_container_width=True):
            st.info("Excel导出功能开发中...")

    with col3:
        if st.button("📧 分享报告", use_container_width=True):
            st.info("报告分享功能开发中...")


def render_industry_analysis_report():
    """产业分析报告"""
    st.markdown("### 🏗️ 产业分析报告")
    st.info("🚧 产业分析报告页面开发中，敬请期待...")
    st.markdown("""
    将包含：
    - 产业链完整分析（上游、中游、下游）
    - 政策影响评估
    - 行业周期分析
    - 竞争格局分析
    - 投资机会识别
    """)


def render_strategy_report():
    """策略建议报告"""
    st.markdown("### 🎯 策略建议报告")
    st.info("🚧 策略建议报告页面开发中，敬请期待...")
    st.markdown("""
    将包含：
    - 买入/卖出建议
    - 仓位管理建议
    - 止盈止损策略
    - 情景分析（乐观/基准/悲观）
    - 风险提示
    """)


def render_attribution_report():
    """归因分析报告"""
    st.markdown("### 📋 归因分析报告")
    st.info("🚧 归因分析报告页面开发中，敬请期待...")
    st.markdown("""
    将包含：
    - 收益归因分析（选股、择时贡献）
    - 因子归因分析（价值、成长、质量因子）
    - 行业归因分析
    - 风格归因分析
    - Brinson归因分析
    """)


# 如果直接运行此文件
if __name__ == "__main__":
    render_analysis_reports()
