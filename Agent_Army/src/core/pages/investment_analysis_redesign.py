"""
投资分析页面 - 重新设计版本

设计原则：
1. 清晰的流程：步骤1 → 步骤2 → 步骤3
2. 实时状态：当前步骤高亮，已完成步骤折叠
3. 简洁日志：只显示真实执行日志，无模拟数据
4. 友好交互：支持取消、重试
5. 错误友好：清晰的问题描述和解决建议
"""

import streamlit as st
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional


def render_step_status(
    step_num: int,
    title: str,
    status: str,  # "pending", "running", "completed", "failed"
    data: Optional[Dict[str, Any]] = None,
    logs: Optional[list] = None
):
    """渲染单个步骤的状态卡片

    Args:
        step_num: 步骤编号
        title: 步骤标题
        status: 当前状态
        data: 步骤结果数据
        logs: 执行日志列表
    """
    # 状态图标
    status_icons = {
        "pending": "⏸",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌"
    }

    # 状态颜色
    status_colors = {
        "pending": "info",
        "running": "warning",
        "completed": "success",
        "failed": "error"
    }

    icon = status_icons.get(status, "⏸")
    color = status_colors.get(status, "info")

    # 步骤卡片容器
    with st.container():
        # 步骤标题行
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            st.markdown(f"**{icon} 步骤{step_num}: {title}**")

        with col2:
            if status == "running":
                st.caption("⏳ 执行中...")
            elif status == "completed":
                elapsed = data.get("elapsed_time", 0) if data else 0
                st.caption(f"✓ 已完成 ({elapsed:.1f}秒)")
            elif status == "failed":
                st.caption("❌ 失败")
            else:
                st.caption("⏸ 等待中")

        with col3:
            if status == "completed" and data:
                score = data.get("quality_score", 0)
                st.metric("评分", f"{score}/100")

        # 内容区域（根据状态展开）
        if status == "running":
            # 显示实时日志
            if logs:
                with st.expander("📋 查看实时日志", expanded=True):
                    for log in logs[-5:]:  # 只显示最后5条
                        timestamp = log.get("timestamp", datetime.now().strftime("%H:%M:%S"))
                        message = log.get("message", "")
                        st.caption(f"{timestamp} {message}")

            # 操作按钮
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button(f"⏸ 暂停", key=f"pause_{step_num}"):
                    st.warning("⚠️ 暂停功能开发中")
            with col_btn2:
                if st.button(f"🔄 重试", key=f"retry_{step_num}"):
                    st.rerun()
            with col_btn3:
                if st.button(f"✕ 取消", key=f"cancel_{step_num}"):
                    st.error("❌ 分析已取消")
                    st.stop()

        elif status == "completed" and data:
            # 显示结果摘要
            with st.expander("✓ 查看结果摘要", expanded=False):
                if "industry_name" in data:
                    st.markdown("**产业链分析结果**:")
                    st.caption(f"• 行业：{data.get('industry_name', '')}")
                    st.caption(f"• 评分：{data.get('score', 0)}/100")
                    st.caption(f"• 周期：{data.get('industry_cycle', '')}")
                    st.caption(f"• Commander预审：{data.get('precheck_status', '')}")

                elif "composite_score" in data:
                    st.markdown("**基本面分析结果**:")
                    st.caption(f"• 综合评分：{data.get('composite_score', 0):.1f}")
                    st.caption(f"• 投资评级：{data.get('rating', '')}")
                    st.caption(f"• ROE：{data.get('roe', 0):.2f}%")
                    st.caption(f"• 营收增长：{data.get('revenue_growth', 0):.2f}%")
                    st.caption(f"• Commander预审：{data.get('precheck_status', '')}")

                elif "overall_score" in data:
                    st.markdown("**最终报告**:")
                    st.caption(f"• 综合评分：{data.get('overall_score', 0):.1f}")
                    st.caption(f"• 投资建议：{data.get('overall_rating', '')}")
                    st.caption(f"• 目标价位：¥{data.get('target_price', 0):.2f}")
                    st.caption(f"• 风险等级：{data.get('risk_level', '')}")

        elif status == "failed":
            # 显示错误信息
            st.error(f"**错误**: {data.get('error', '未知错误')}")
            if data.get("suggestions"):
                st.markdown("**建议**:")
                for suggestion in data["suggestions"]:
                    st.caption(f"• {suggestion}")

        st.markdown("")


def render_investment_analysis_redesign():
    """渲染重新设计的投资分析页面"""

    st.markdown("### 📊 投资分析")
    st.markdown("---")

    st.success("✅ Phase 2 MVP已完成，支持完整投资分析流程！")

    # 检查是否有自动填充的股票代码
    auto_code = st.session_state.get('auto_stock_code', '')
    default_code = auto_code if auto_code else "600519"

    # 如果有自动填充的代码，显示提示
    if auto_code:
        st.info(f"💡 已自动填充股票代码: {auto_code} (来自智能任务助手)")
        if st.button("🔄 清除自动填充"):
            if 'auto_stock_code' in st.session_state:
                del st.session_state.auto_stock_code
            st.rerun()

    # 股票代码输入
    col1, col2 = st.columns([2, 1])

    with col1:
        stock_code = st.text_input(
            "股票代码",
            value=default_code,
            max_chars=6,
            help="输入6位A股代码,如 600519",
            key="stock_code_input_redesign"
        )

    with col2:
        if st.button("🔍 开始分析", type="primary", key="start_analysis_redesign"):
            if stock_code and len(stock_code) == 6:
                st.session_state.analyzing = True
                st.session_state.stock_code = stock_code
                st.session_state.analysis_start_time = time.time()
                st.rerun()

    # 如果正在分析，显示分析流程
    if st.session_state.get("analyzing", False):
        stock_code = st.session_state.get("stock_code", "")

        # 进度概览
        st.markdown("---")
        st.markdown(f"### 📊 分析进度：{stock_code}")
        st.markdown("---")

        # 整体进度条
        progress_placeholder = st.empty()
        status_placeholder = st.empty()

        # 初始化步骤状态（如果还没有）
        if "step1_status" not in st.session_state:
            st.session_state.step1_status = "pending"
            st.session_state.step2_status = "pending"
            st.session_state.step3_status = "pending"
            st.session_state.step1_data = None
            st.session_state.step2_data = None
            st.session_state.step3_data = None
            st.session_state.step1_logs = []
            st.session_state.step2_logs = []
            st.session_state.step3_logs = []

        # ========== 步骤1: 产业链分析 ==========
        if st.session_state.step1_status == "pending":
            st.session_state.step1_status = "running"

            # 更新进度
            with progress_placeholder.container():
                st.progress(10)
            with status_placeholder.container():
                st.caption("🔄 步骤1/3: 产业链分析中...")

            # 执行分析
            try:
                from src.agents.business.industry_analyzers import IndustryChainAnalyzer
                from src.agents.management.commander_agent import CommanderAgent

                # 添加日志
                st.session_state.step1_logs.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "message": f"开始分析股票 {stock_code}"
                })

                analyzer = IndustryChainAnalyzer()
                step1_start = time.time()
                result = asyncio.run(analyzer.analyze(stock_code))
                step1_elapsed = time.time() - step1_start

                st.session_state.step1_logs.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "message": f"产业链分析完成 ({step1_elapsed:.2f}秒)"
                })

                # Commander预审
                st.session_state.step1_logs.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "message": "Commander预审中..."
                })

                commander = CommanderAgent()
                precheck = asyncio.run(commander.precheck_report(
                    agent_name="产业链分析AI",
                    report_type="industry",
                    report_data=result.model_dump()
                ))

                # 保存结果
                st.session_state.step1_data = {
                    "industry_name": result.industry_name,
                    "score": result.score,
                    "industry_cycle": result.industry_cycle,
                    "market_share": result.market_share,
                    "industry_rank": result.industry_rank,
                    "elapsed_time": step1_elapsed,
                    "quality_score": precheck.get("quality_score", 0),
                    "precheck_status": "通过" if precheck.get("approved") else "未通过"
                }

                st.session_state.step1_status = "completed"
                st.rerun()

            except Exception as e:
                st.session_state.step1_status = "failed"
                st.session_state.step1_data = {
                    "error": str(e),
                    "suggestions": [
                        "检查API密钥是否有效",
                        "检查网络连接",
                        "检查股票代码是否正确"
                    ]
                }
                st.rerun()

        # ========== 步骤2: 基本面分析 ==========
        elif st.session_state.step1_status == "completed" and st.session_state.step2_status == "pending":
            st.session_state.step2_status = "running"

            # 更新进度
            with progress_placeholder.container():
                st.progress(40)
            with status_placeholder.container():
                st.caption("🔄 步骤2/3: 基本面分析中...")

            # 执行分析
            try:
                from src.agents.business.fundamental_analyzer import FundamentalAnalyzer
                from src.agents.management.commander_agent import CommanderAgent

                # 添加日志
                st.session_state.step2_logs.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "message": f"开始分析 {stock_code} 基本面"
                })

                analyzer = FundamentalAnalyzer()
                step2_start = time.time()
                result = asyncio.run(analyzer.analyze(stock_code))
                step2_elapsed = time.time() - step2_start

                st.session_state.step2_logs.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "message": f"基本面分析完成 ({step2_elapsed:.2f}秒)"
                })

                # Commander预审
                st.session_state.step2_logs.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "message": "Commander预审中..."
                })

                commander = CommanderAgent()
                precheck = asyncio.run(commander.precheck_report(
                    agent_name="基本面分析AI",
                    report_type="fundamental",
                    report_data=result  # result已经是dict，不需要model_dump()
                ))

                # 保存结果 - 从dict中正确提取字段
                st.session_state.step2_data = {
                    "composite_score": result["composite_score"],
                    "rating": result["rating"],
                    "roe": result["key_metrics"]["roe"],
                    "revenue_growth": result["key_metrics"]["revenue_growth"],
                    "profit_growth": result["key_metrics"]["profit_growth"],
                    "elapsed_time": step2_elapsed,
                    "quality_score": precheck.get("quality_score", 0),
                    "precheck_status": "通过" if precheck.get("approved") else "未通过"
                }

                st.session_state.step2_status = "completed"
                st.rerun()

            except Exception as e:
                st.session_state.step2_status = "failed"
                st.session_state.step2_data = {
                    "error": str(e),
                    "suggestions": [
                        "检查Tushare API密钥",
                        "确认股票代码正确",
                        "检查账户余额"
                    ]
                }
                st.rerun()

        # ========== 步骤3: 生成报告 ==========
        elif st.session_state.step2_status == "completed" and st.session_state.step3_status == "pending":
            st.session_state.step3_status = "running"

            # 更新进度
            with progress_placeholder.container():
                st.progress(70)
            with status_placeholder.container():
                st.caption("🔄 步骤3/3: 生成最终报告...")

            # 执行分析
            try:
                from src.workflows.investment_analysis_workflow import InvestmentAnalysisWorkflow

                # 添加日志
                st.session_state.step3_logs.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "message": "整合分析结果..."
                })

                workflow = InvestmentAnalysisWorkflow()
                step3_start = time.time()

                # 调用正确的方法名
                report = asyncio.run(workflow.analyze_stock(stock_code))
                step3_elapsed = time.time() - step3_start

                st.session_state.step3_logs.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "message": f"报告生成完成 ({step3_elapsed:.2f}秒)"
                })

                # 保存结果 - 使用正确的字段名
                st.session_state.step3_data = {
                    "overall_score": report.overall_score,
                    "overall_rating": report.overall_rating.value if hasattr(report.overall_rating, 'value') else str(report.overall_rating),
                    "target_price": report.target_price,
                    "risk_level": report.risk_level.value if hasattr(report.risk_level, 'value') else str(report.risk_level),
                    "elapsed_time": step3_elapsed
                }

                st.session_state.step3_status = "completed"
                st.session_state.analyzing = False
                st.rerun()

            except Exception as e:
                st.session_state.step3_status = "failed"
                st.session_state.step3_data = {
                    "error": str(e),
                    "suggestions": [
                        "检查所有API连接",
                        "尝试重新分析",
                        "联系技术支持"
                    ]
                }
                st.rerun()

        # ========== 渲染步骤状态 ==========
        # 步骤1
        render_step_status(
            step_num=1,
            title="产业链分析",
            status=st.session_state.step1_status,
            data=st.session_state.step1_data,
            logs=st.session_state.step1_logs
        )

        # 步骤2
        render_step_status(
            step_num=2,
            title="基本面分析",
            status=st.session_state.step2_status,
            data=st.session_state.step2_data,
            logs=st.session_state.step2_logs
        )

        # 步骤3
        render_step_status(
            step_num=3,
            title="生成投资报告",
            status=st.session_state.step3_status,
            data=st.session_state.step3_data,
            logs=st.session_state.step3_logs
        )

        # ========== 全部完成后的操作 ==========
        if st.session_state.step3_status == "completed":
            st.markdown("---")
            st.success("🎉 分析完成！")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("💾 保存报告", type="primary"):
                    st.success("✅ 报告已保存")

            with col2:
                if st.button("📊 查看详细报告"):
                    st.info("📊 跳转到报告查看页面...")

            with col3:
                if st.button("🔄 分析其他股票"):
                    # 清空session state
                    for key in ["analyzing", "stock_code", "step1_status", "step2_status", "step3_status"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

            # 显示最终结果摘要
            st.markdown("---")
            st.markdown("### 📊 分析结果摘要")

            data = st.session_state.step3_data
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("综合评分", f"{data['overall_score']:.1f}/100")
            with col2:
                st.metric("投资评级", data['overall_rating'])
            with col3:
                st.metric("目标价位", f"¥{data['target_price']:.2f}")
            with col4:
                st.metric("风险等级", data['risk_level'])


# 测试代码
if __name__ == "__main__":
    render_investment_analysis_redesign()
