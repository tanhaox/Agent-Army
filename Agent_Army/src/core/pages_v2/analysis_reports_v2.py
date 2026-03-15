"""
Agent Army - 分析报告页 (v2.1 优化版)
集成导出功能
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import sys
from typing import Dict, List

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入导出工具
from src.core.utils.exporters import (
    PDFExporter,
    ExcelExporter,
    ShareLinkGenerator
)

# 导入Agent管理器
from src.core.agents.agent_manager import get_agent_manager


@st.cache_data(ttl=300)
def load_analysis_result(stock_code: str) -> Dict:
    """
    加载分析结果（带缓存）
    """
    agent_manager = get_agent_manager()

    # 模拟分析结果
    analysis_result = {}

    # 24个Agent的分析结果
    all_agents = agent_manager.get_all_agents()

    for agent_id, agent_info in all_agents.items():
        analysis_result[agent_id] = {
            'agent_name': agent_info['name'],
            'army': agent_info['army'],
            'score': 85,
            'recommendation': '买入',
            'confidence': 0.85,
            'analysis': f"基于{agent_info['name']}的综合分析...",
            'timestamp': datetime.now().isoformat()
        }

    return analysis_result


def render_analysis_reports_v2():
    """渲染优化版分析报告页面"""

    st.title("📄 分析报告")
    st.markdown("**查看和导出Agent分析报告**")
    st.markdown("---")

    # ========== 查询区域 ==========
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        stock_code = st.text_input(
            "股票代码",
            value="000001",
            placeholder="输入股票代码",
            key="report_stock_code"
        )

    with col2:
        report_type = st.selectbox(
            "报告类型",
            options=["股票分析报告", "产业分析报告", "策略报告", "归因分析报告"],
            key="report_type"
        )

    with col3:
        st.write("")
        st.write("")
        if st.button("📄 生成报告", type="primary", use_container_width=True):
            st.rerun()

    if not stock_code:
        st.info("💡 请输入股票代码生成报告")
        return

    st.markdown("---")

    # 加载分析结果
    with st.spinner(f"正在生成 {stock_code} 的分析报告..."):
        analysis_result = load_analysis_result(stock_code)

    # ========== 导出功能区 ==========
    st.markdown("### 📥 导出报告")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📄 导出PDF", use_container_width=True, key="export_pdf"):
            export_pdf_report(stock_code, analysis_result)

    with col2:
        if st.button("📊 导出Excel", use_container_width=True, key="export_excel"):
            export_excel_report(stock_code, analysis_result)

    with col3:
        if st.button("🔗 分享链接", use_container_width=True, key="share_link"):
            generate_share_link(stock_code)

    with col4:
        if st.button("🖨️ 打印报告", use_container_width=True, key="print_report"):
            st.info("💡 请使用浏览器打印功能 (Ctrl+P)")

    st.markdown("---")

    # ========== 报告内容区 ==========
    if report_type == "股票分析报告":
        render_stock_report(stock_code, analysis_result)
    elif report_type == "产业分析报告":
        render_industry_report(stock_code)
    elif report_type == "策略报告":
        render_strategy_report(stock_code)
    elif report_type == "归因分析报告":
        render_attribution_report(stock_code)


def export_pdf_report(stock_code: str, analysis_result: Dict):
    """导出PDF报告"""
    if not PDFExporter.is_available():
        st.warning("⚠️ PDF功能需要安装: pip install reportlab")
        return

    with st.spinner("正在生成PDF..."):
        pdf_bytes = PDFExporter.export_stock_analysis_report(
            stock_code=stock_code,
            analysis_result=analysis_result
        )

        if pdf_bytes:
            # 创建下载链接
            filename = f"analysis_report_{stock_code}_{datetime.now().strftime('%Y%m%d')}.pdf"
            download_link = PDFExporter.create_download_link(pdf_bytes, filename)

            st.markdown(download_link, unsafe_allow_html=True)
            st.success(f"✅ PDF报告已生成: {filename}")


def export_excel_report(stock_code: str, analysis_result: Dict):
    """导出Excel报告"""
    with st.spinner("正在生成Excel..."):
        excel_bytes = ExcelExporter.export_analysis_data(
            stock_code=stock_code,
            analysis_result=analysis_result
        )

        if excel_bytes:
            # 创建下载链接
            filename = f"analysis_data_{stock_code}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            download_link = ExcelExporter.create_download_link(excel_bytes, filename)

            st.markdown(download_link, unsafe_allow_html=True)
            st.success(f"✅ Excel数据已生成: {filename}")


def generate_share_link(stock_code: str):
    """生成分享链接"""
    report_id = f"{stock_code}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    share_link = ShareLinkGenerator.generate_report_link(report_id)

    st.code(share_link, language="text")

    st.info("💡 链接有效期为30天")


def render_stock_report(stock_code: str, analysis_result: Dict):
    """渲染股票分析报告"""

    st.markdown(f"## 📊 股票分析报告 - {stock_code}")
    st.markdown(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    # ========== 投资评级 ==========
    st.markdown("### ⭐ 投资评级")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("综合评分", "85/100", "+5")

    with col2:
        st.metric("推荐评级", "买入", "强烈推荐")

    with col3:
        st.metric("目标价位", "¥15.50", "+18%")

    with col4:
        st.metric("止损价位", "¥12.00", "-8%")

    st.markdown("---")

    # ========== Agent分析结果 ==========
    st.markdown("### 🤖 Agent分析结果")

    # 按军团分组
    armies = {}
    for agent_id, result in analysis_result.items():
        army_name = result['army']
        if army_name not in armies:
            armies[army_name] = []
        armies[army_name].append(result)

    # 评分雷达图
    st.markdown("#### 📈 综合评分雷达图")

    army_names = list(armies.keys())
    army_scores = [85] * len(army_names)  # 模拟数据

    fig_radar = go.Figure(data=go.Scatterpolar(
        r=army_scores,
        theta=army_names,
        fill='toself'
    ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        height=400
    )

    st.plotly_chart(fig_radar, use_container_width=True)

    # 详细分析
    for army_name, results in armies.items():
        with st.expander(f"**{army_name}** 分析"):
            for result in results[:3]:  # 只显示前3个
                st.markdown(f"##### {result['agent_name']}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("评分", f"{result['score']}/100")

                with col2:
                    st.metric("推荐", result['recommendation'])

                with col3:
                    st.metric("置信度", f"{result['confidence']:.1%}")

                st.markdown(f"**分析结论**: {result['analysis']}")
                st.markdown("---")


def render_industry_report(stock_code: str):
    """渲染产业分析报告"""
    st.markdown(f"## 🏭 产业分析报告 - {stock_code}")
    st.info("💡 产业分析报告开发中...")


def render_strategy_report(stock_code: str):
    """渲染策略报告"""
    st.markdown(f"## ♟️ 策略报告 - {stock_code}")
    st.info("💡 策略报告开发中...")


def render_attribution_report(stock_code: str):
    """渲染归因分析报告"""
    st.markdown(f"## 📊 归因分析报告 - {stock_code}")
    st.info("💡 归因分析报告开发中...")


# 如果直接运行此文件
if __name__ == "__main__":
    render_analysis_reports_v2()
