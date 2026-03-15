"""
Agent Army - 市场监控页面 (v2.0)
新闻监控、资金流向、市场情绪、热点追踪
"""

import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def render_market_monitor():
    """渲染市场监控页面"""

    st.title("📰 市场监控")
    st.markdown("**实时监控 | 新闻分析 | 资金流向 | 情绪追踪**")
    st.markdown("---")

    # ========== 标签页 ==========
    tab1, tab2, tab3, tab4 = st.tabs([
        "📰 新闻监控",
        "💰 资金流向",
        "📊 市场情绪",
        "🔥 热点追踪"
    ])

    # ========== 新闻监控 ==========
    with tab1:
        render_news_monitor()

    # ========== 资金流向 ==========
    with tab2:
        render_capital_flow()

    # ========== 市场情绪 ==========
    with tab3:
        render_market_sentiment()

    # ========== 热点追踪 ==========
    with tab4:
        render_hot_topics()


def render_news_monitor():
    """新闻监控"""

    st.markdown("### 📰 实时新闻监控")

    # 筛选器
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        impact_filter = st.selectbox(
            "影响筛选",
            ["全部", "正面", "负面", "中性"]
        )

    with col2:
        source_filter = st.selectbox(
            "来源筛选",
            ["全部", "财经网站", "官方公告", "研究报告"]
        )

    with col3:
        time_filter = st.selectbox(
            "时间筛选",
            ["今日", "近3日", "近7日", "近30日"]
        )

    with col4:
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # 新闻列表
    news_items = [
        {
            "time": "2026-03-14 14:30",
            "source": "央视财经",
            "title": "央行宣布降准0.5个百分点，释放长期资金约1万亿元",
            "impact": "正面",
            "impact_stocks": "平安银行、招商银行、工商银行",
            "importance": "高",
            "sentiment": 85
        },
        {
            "time": "2026-03-14 13:45",
            "source": "新华社",
            "title": "国务院常务会议：促进新能源汽车产业发展",
            "impact": "正面",
            "impact_stocks": "比亚迪、宁德时代、长城汽车",
            "importance": "高",
            "sentiment": 90
        },
        {
            "time": "2026-03-14 11:20",
            "source": "证券时报",
            "title": "科技股受资金追捧，多只个股涨停",
            "impact": "正面",
            "impact_stocks": "中兴通讯、立讯精密、歌尔股份",
            "importance": "中",
            "sentiment": 75
        },
        {
            "time": "2026-03-14 10:15",
            "source": "上海证券报",
            "title": "北向资金净流入超50亿元，连续3日净流入",
            "impact": "正面",
            "impact_stocks": "茅台、宁德时代、比亚迪",
            "importance": "中",
            "sentiment": 70
        },
        {
            "time": "2026-03-14 09:30",
            "source": "财联社",
            "title": "房地产调控政策优化，多地出台支持政策",
            "impact": "正面",
            "impact_stocks": "万科A、保利发展、招商蛇口",
            "importance": "中",
            "sentiment": 80
        }
    ]

    # 显示新闻
    for i, news in enumerate(news_items):
        with st.container():
            # 新闻头部
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

            with col1:
                impact_emoji = {
                    "正面": "🟢",
                    "负面": "🔴",
                    "中性": "🟡"
                }.get(news['impact'], "🟡")
                st.markdown(f"**{impact_emoji} {news['time']}** - {news['source']}")

            with col2:
                importance_color = "🔴" if news['importance'] == "高" else "🟡"
                st.markdown(f"**重要度**: {importance_color} {news['importance']}")

            with col3:
                st.markdown(f"**影响**: {news['impact']}")

            with col4:
                st.markdown(f"**情绪分**: {news['sentiment']}")

            # 新闻标题
            st.markdown(f"### {news['title']}")

            # 关联股票
            st.markdown(f"**关联股票**: {news['impact_stocks']}")

            # 情绪分析条
            sentiment_pct = news['sentiment']
            st.progress(sentiment_pct / 100)

            # 操作按钮
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(f"📊 详细分析", key=f"analyze_news_{i}"):
                    st.info(f"正在分析新闻影响...")

            with col2:
                if st.button(f"🔍 查看原文", key=f"source_news_{i}"):
                    st.info("原文链接功能开发中...")

            with col3:
                if st.button(f"📋 关联分析", key=f"related_news_{i}"):
                    st.info("关联分析功能开发中...")

            st.markdown("---")


def render_capital_flow():
    """资金流向"""

    st.markdown("### 💰 资金流向监控")

    # 顶部统计
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💰 主力净流入",
            value="+15.3亿",
            delta="流入"
        )

    with col2:
        st.metric(
            label="🏦 北向资金",
            value="+58.2亿",
            delta="连续3日流入"
        )

    with col3:
        st.metric(
            label="👥 散户资金",
            value="-12.5亿",
            delta="流出"
        )

    with col4:
        st.metric(
            label="🏢 机构资金",
            value="+37.8亿",
            delta="流入"
        )

    st.markdown("---")

    # 行业资金流向
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 行业资金流向")

        industries = ["科技", "银行", "新能源", "医药", "消费", "房地产"]
        flows = [8.5, 6.2, 5.8, 3.2, 2.1, -1.5]

        fig = go.Figure(data=[
            go.Bar(
                x=industries,
                y=flows,
                marker_color=['green' if f > 0 else 'red' for f in flows]
            )
        ])

        fig.update_layout(
            height=400,
            xaxis_title="行业",
            yaxis_title="净流入（亿）"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🔥 热门流入股票")

        hot_stocks = [
            {"code": "000001", "name": "平安银行", "flow": 3.5},
            {"code": "600036", "name": "招商银行", "flow": 2.8},
            {"code": "002594", "name": "比亚迪", "flow": 2.5},
            {"code": "300750", "name": "宁德时代", "flow": 2.1},
            {"code": "600519", "name": "贵州茅台", "flow": 1.8}
        ]

        for stock in hot_stocks:
            st.markdown(
                f"**{stock['code']}** {stock['name']} - "
                f"🟢 +{stock['flow']}亿"
            )


def render_market_sentiment():
    """市场情绪"""

    st.markdown("### 📊 市场情绪分析")

    # 情绪指标
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="😊 情绪指数",
            value="72",
            delta="偏乐观"
        )

    with col2:
        st.metric(
            label="😰 恐惧贪婪指数",
            value="贪婪",
            delta="68"
        )

    with col3:
        st.metric(
            label="🌡️ 市场温度",
            value="偏热",
            delta="78"
        )

    with col4:
        st.metric(
            label="📊 成交额",
            value="1.2万亿",
            delta="活跃"
        )

    st.markdown("---")

    # 情绪仪表盘
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎭 恐惧贪婪指数")

        # 创建仪表盘
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=68,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "恐惧贪婪指数"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 25], 'color': "red"},
                    {'range': [25, 50], 'color': "orange"},
                    {'range': [50, 75], 'color': "yellow"},
                    {'range': [75, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 68
                }
            }
        ))

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 📈 情绪趋势")

        st.info("🚧 情绪趋势图开发中...")


def render_hot_topics():
    """热点追踪"""

    st.markdown("### 🔥 热点主题追踪")

    # 热点板块
    st.markdown("#### 🏆 今日热点板块")

    hot_sectors = [
        {"name": "新能源汽车", "change": "+3.5%", "leading": "比亚迪、宁德时代", "hot": True},
        {"name": "半导体", "change": "+2.8%", "leading": "中芯国际、北方华创", "hot": True},
        {"name": "医药生物", "change": "+2.2%", "leading": "恒瑞医药、药明康德", "hot": True},
        {"name": "白酒", "change": "+1.8%", "leading": "茅台、五粮液", "hot": False},
        {"name": "银行", "change": "+1.5%", "leading": "平安银行、招商银行", "hot": False}
    ]

    for sector in hot_sectors:
        col1, col2, col3, col4 = st.columns([2, 1, 3, 1])

        with col1:
            hot_badge = "🔥" if sector['hot'] else ""
            st.markdown(f"**{hot_badge} {sector['name']}**")

        with col2:
            change_color = "🟢" if float(sector['change'].replace('+', '').replace('%', '')) > 0 else "🔴"
            st.markdown(f"{change_color} {sector['change']}")

        with col3:
            st.markdown(f"龙头: {sector['leading']}")

        with col4:
            if st.button("分析", key=f"sector_{sector['name']}"):
                st.info(f"正在分析 {sector['name']} 板块...")

    st.markdown("---")

    # 热点事件
    st.markdown("#### 📰 热点事件追踪")

    events = [
        {
            "time": "14:30",
            "title": "央行降准利好银行股",
            "impact": "正面",
            "stocks": "平安银行、招商银行"
        },
        {
            "time": "13:45",
            "title": "新能源汽车销量创新高",
            "impact": "正面",
            "stocks": "比亚迪、宁德时代"
        },
        {
            "time": "11:20",
            "title": "科技股受资金追捧",
            "impact": "正面",
            "stocks": "中兴通讯、立讯精密"
        }
    ]

    for event in events:
        impact_emoji = {
            "正面": "🟢",
            "负面": "🔴",
            "中性": "🟡"
        }.get(event['impact'], "🟡")

        st.markdown(
            f"**{impact_emoji} {event['time']}** {event['title']}  \n"
            f"关联: {event['stocks']}"
        )
        st.markdown("")


# 如果直接运行此文件
if __name__ == "__main__":
    render_market_monitor()
