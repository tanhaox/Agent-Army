"""
投资分析页面 - v2.0 整合版

核心改进：
1. 单一入口完成全流程（输入→分析→查看报告）
2. 分析完成后自动展开报告详情
3. 智能输入框（支持代码/名称/拼音）
4. 全宽布局优化
5. 新手友好的引导提示
"""

import streamlit as st
import asyncio
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


def render_newbie_guide():
    """渲染新手引导提示"""
    st.info("""
    💡 **如何开始？**
    1. 输入6位股票代码（如：600519）或股票名称（如：贵州茅台）
    2. 点击"🔍 开始分析"按钮
    3. 等待2-3分钟，报告会自动展示在下方 ⬇️
    """)


def render_smart_input() -> str:
    """
    渲染智能输入框

    Returns:
        str: 用户输入的股票代码
    """
    st.markdown("#### 步骤1：输入股票代码")

    # 检查是否有自动填充的股票代码（从首页跳转）
    auto_code = st.session_state.get('auto_stock_code', '')
    default_code = auto_code if auto_code else ""

    # 显示提示信息
    if auto_code:
        st.success(f"✅ 已自动填充股票代码: {auto_code}")
        if st.button("🔄 清除", key="clear_auto_code"):
            if 'auto_stock_code' in st.session_state:
                del st.session_state.auto_stock_code
            st.rerun()

    # 智能输入框
    col1, col2 = st.columns([3, 1])

    with col1:
        user_input = st.text_input(
            "股票代码或名称",
            value=default_code,
            placeholder="支持：6位代码 / 股票名称 / 拼音缩写",
            help="示例：600519 或 贵州茅台 或 GZMT",
            key="smart_stock_input"
        )

    with col2:
        start_button = st.button("🔍 开始分析", type="primary", key="start_analysis_v2")

    # 智能识别输入类型
    if user_input:
        if user_input.isdigit() and len(user_input) == 6:
            # 6位数字 - 股票代码
            stock_code = user_input
            st.caption(f"✅ 识别为股票代码: {stock_code}")
        elif any('\u4e00' <= char <= '\u9fff' for char in user_input):
            # 包含中文 - 股票名称
            # TODO: 实现名称转代码的功能
            st.warning(f"⚠️ 识别为股票名称: {user_input}")
            st.info("💡 请输入6位股票代码（如：600519）")
            stock_code = None
        else:
            # 其他 - 可能是拼音缩写
            st.warning(f"⚠️ 无法识别: {user_input}")
            st.info("💡 请输入6位股票代码")
            stock_code = None
    else:
        stock_code = None

    # 点击开始分析
    if start_button:
        if stock_code:
            st.session_state.analyzing = True
            st.session_state.stock_code = stock_code
            st.session_state.analysis_start_time = time.time()
            st.rerun()
        else:
            st.error("❌ 请输入有效的股票代码")

    return stock_code if start_button and stock_code else None


def render_analysis_progress(stock_code: str):
    """
    渲染分析进度

    Args:
        stock_code: 股票代码
    """
    st.markdown("---")
    st.markdown(f"#### 步骤2：分析进度 - {stock_code}")
    st.markdown("---")

    # 初始化步骤状态
    if "step1_status" not in st.session_state:
        st.session_state.step1_status = "pending"
        st.session_state.step2_status = "pending"
        st.session_state.step3_status = "pending"
        st.session_state.step1_data = None
        st.session_state.step2_data = None
        st.session_state.step3_data = None

    # 步骤1：产业链分析
    if st.session_state.step1_status == "pending":
        st.session_state.step1_status = "running"
        st.rerun()

    if st.session_state.step1_status == "running":
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown("**🔄 步骤1: 产业链分析**")
            with col2:
                st.caption("⏳ 执行中...")

        # 执行分析
        try:
            from src.agents.business.industry_analyzers import IndustryChainAnalyzer
            from src.core.config import ConfigManager

            config_manager = ConfigManager("./config")
            analyzer = IndustryChainAnalyzer(config=config_manager.get("industry_analyzer", {}))

            start_time = time.time()
            result = analyzer.analyze(stock_code)
            elapsed_time = time.time() - start_time

            # Commander 预审
            if st.session_state.get("commander_agent"):
                commander = st.session_state.commander_agent
                precheck = commander.precheck_report(
                    agent="产业链分析AI",
                    report_data=result,
                    report_type="industry_analysis"
                )
                result["precheck_status"] = precheck.get("status", "pending")
                result["quality_score"] = precheck.get("quality_score", 0)
            else:
                result["precheck_status"] = "skipped"
                result["quality_score"] = 0

            result["elapsed_time"] = elapsed_time
            st.session_state.step1_data = result
            st.session_state.step1_status = "completed"
            st.rerun()

        except Exception as e:
            st.session_state.step1_status = "failed"
            st.session_state.step1_data = {
                "error": str(e),
                "suggestions": [
                    "检查网络连接",
                    "确认 Tushare API 密钥已配置",
                    "查看日志了解详细错误"
                ]
            }
            st.rerun()

    # 显示步骤1结果
    if st.session_state.step1_status == "completed":
        data = st.session_state.step1_data
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown("**✅ 步骤1: 产业链分析**")
            with col2:
                st.caption(f"✓ 已完成 ({data.get('elapsed_time', 0):.1f}秒)")
            with col3:
                st.metric("评分", f"{data.get('quality_score', 0)}/100")

        # 步骤2：基本面分析
        st.markdown("")
        if st.session_state.step2_status == "pending":
            st.session_state.step2_status = "running"
            st.rerun()

    elif st.session_state.step1_status == "failed":
        data = st.session_state.step1_data
        st.error(f"**❌ 步骤1失败**: {data.get('error', '未知错误')}")
        if data.get("suggestions"):
            st.markdown("**建议**:")
            for suggestion in data["suggestions"]:
                st.caption(f"• {suggestion}")

        # 停止分析
        if st.button("🔄 重试", key="retry_step1"):
            st.session_state.step1_status = "pending"
            st.rerun()
        return

    # 步骤2：基本面分析
    if st.session_state.step2_status == "running":
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown("**🔄 步骤2: 基本面分析**")
            with col2:
                st.caption("⏳ 执行中...")

        # 执行分析
        try:
            from src.agents.business.fundamental_analyzer import FundamentalAnalyzer
            from src.core.config import ConfigManager

            config_manager = ConfigManager("./config")
            analyzer = FundamentalAnalyzer(config=config_manager.get("fundamental_analyzer", {}))

            start_time = time.time()
            result = analyzer.analyze(stock_code)
            elapsed_time = time.time() - start_time

            # Commander 预审
            if st.session_state.get("commander_agent"):
                commander = st.session_state.commander_agent
                precheck = commander.precheck_report(
                    agent="基本面分析AI",
                    report_data=result,
                    report_type="fundamental_analysis"
                )
                result["precheck_status"] = precheck.get("status", "pending")
                result["quality_score"] = precheck.get("quality_score", 0)
            else:
                result["precheck_status"] = "skipped"
                result["quality_score"] = 0

            result["elapsed_time"] = elapsed_time
            st.session_state.step2_data = result
            st.session_state.step2_status = "completed"
            st.rerun()

        except Exception as e:
            st.session_state.step2_status = "failed"
            st.session_state.step2_data = {
                "error": str(e),
                "suggestions": [
                    "检查网络连接",
                    "确认 Tushare API 密钥已配置",
                    "查看日志了解详细错误"
                ]
            }
            st.rerun()

    # 显示步骤2结果
    if st.session_state.step2_status == "completed":
        data = st.session_state.step2_data
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown("**✅ 步骤2: 基本面分析**")
            with col2:
                st.caption(f"✓ 已完成 ({data.get('elapsed_time', 0):.1f}秒)")
            with col3:
                st.metric("评分", f"{data.get('quality_score', 0)}/100")

        # 步骤3：生成报告
        st.markdown("")
        if st.session_state.step3_status == "pending":
            st.session_state.step3_status = "running"
            st.rerun()

    elif st.session_state.step2_status == "failed":
        data = st.session_state.step2_data
        st.error(f"**❌ 步骤2失败**: {data.get('error', '未知错误')}")
        if data.get("suggestions"):
            st.markdown("**建议**:")
            for suggestion in data["suggestions"]:
                st.caption(f"• {suggestion}")

        # 停止分析
        if st.button("🔄 重试", key="retry_step2"):
            st.session_state.step2_status = "pending"
            st.rerun()
        return

    # 步骤3：生成最终报告
    if st.session_state.step3_status == "running":
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown("**🔄 步骤3: 生成最终报告**")
            with col2:
                st.caption("⏳ 执行中...")

        # 执行报告生成
        try:
            from src.workflows.investment_analysis_workflow import InvestmentAnalysisWorkflow
            from src.core.config import ConfigManager

            config_manager = ConfigManager("./config")

            # 整合步骤1和步骤2的结果
            step1_result = st.session_state.step1_data
            step2_result = st.session_state.step2_data

            workflow = InvestmentAnalysisWorkflow(config=config_manager.get("workflow", {}))

            start_time = time.time()

            # 生成最终报告
            final_report = {
                "stock_code": stock_code,
                "stock_name": step2_result.get("stock_name", ""),
                "industry": step1_result.get("industry_name", ""),
                "industry_score": step1_result.get("score", 0),
                "fundamental": step2_result,
                "overall_score": (step1_result.get("score", 0) + step2_result.get("composite_score", 0)) / 2,
                "overall_rating": _calculate_rating(
                    (step1_result.get("score", 0) + step2_result.get("composite_score", 0)) / 2
                ),
                "investment_advice": _generate_advice(
                    (step1_result.get("score", 0) + step2_result.get("composite_score", 0)) / 2
                ),
                "target_price": step2_result.get("target_price", 0),
                "risk_level": step2_result.get("risk_level", "中等"),
                "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "commander_review": {
                    "status": "pending",
                    "reviewer": "Commander Agent"
                }
            }

            elapsed_time = time.time() - start_time
            final_report["elapsed_time"] = elapsed_time

            st.session_state.step3_data = final_report
            st.session_state.step3_status = "completed"
            st.session_state.analyzing = False  # 分析完成
            st.rerun()

        except Exception as e:
            st.session_state.step3_status = "failed"
            st.session_state.step3_data = {
                "error": str(e),
                "suggestions": [
                    "检查数据是否完整",
                    "查看日志了解详细错误",
                    "尝试重新分析"
                ]
            }
            st.session_state.analyzing = False
            st.rerun()


def _calculate_rating(score: float) -> str:
    """根据评分计算投资评级"""
    if score >= 80:
        return "A (强烈推荐)"
    elif score >= 70:
        return "B (推荐)"
    elif score >= 60:
        return "C (观望)"
    elif score >= 50:
        return "D (谨慎)"
    else:
        return "E (回避)"


def _generate_advice(score: float) -> str:
    """根据评分生成投资建议"""
    if score >= 80:
        return "该公司基本面优秀，行业前景良好，建议重点配置。"
    elif score >= 70:
        return "该公司表现良好，可以考虑适度配置。"
    elif score >= 60:
        return "该公司表现一般，建议谨慎观察。"
    else:
        return "该公司存在风险，建议暂时回避。"


def render_final_report(stock_code: str):
    """
    渲染最终报告 ⭐ 核心改进：自动展开

    Args:
        stock_code: 股票代码
    """
    st.markdown("---")
    st.markdown("#### 步骤3：分析报告")
    st.markdown("---")

    # 成功提示
    st.success("🎉 分析完成！报告已自动展示在下方 ⬇️")

    # 获取报告数据
    report_data = st.session_state.step3_data

    # ========== 关键改进：自动展开报告 ==========
    with st.expander("📊 查看完整分析报告", expanded=True):  # ← expanded=True
        # 报告概要卡片
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("股票代码", report_data.get("stock_code", ""))

        with col2:
            st.metric("综合评分", f"{report_data.get('overall_score', 0):.1f}")

        with col3:
            st.metric("投资评级", report_data.get("overall_rating", ""))

        with col4:
            target_price = report_data.get("target_price", 0)
            st.metric("目标价位", f"¥{target_price:.2f}" if target_price else "N/A")

        st.markdown("---")

        # 投资建议
        st.markdown("### 💡 投资建议")
        st.info(report_data.get("investment_advice", ""))

        st.markdown("---")

        # 详细指标
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📈 产业链分析")
            industry_data = report_data.get("fundamental", {})
            if isinstance(industry_data, dict):
                st.caption(f"• 行业：{report_data.get('industry', 'N/A')}")
                st.caption(f"• 评分：{report_data.get('industry_score', 0)}/100")
                st.caption(f"• 周期：{industry_data.get('industry_cycle', 'N/A')}")

        with col2:
            st.markdown("#### 💰 基本面分析")
            if isinstance(industry_data, dict):
                key_metrics = industry_data.get("key_metrics", {})
                st.caption(f"• ROE：{key_metrics.get('roe', 0):.2f}%")
                st.caption(f"• 营收增长：{key_metrics.get('revenue_growth', 0):.2f}%")
                st.caption(f"• 利润增长：{key_metrics.get('profit_growth', 0):.2f}%")

        st.markdown("---")

        # 风险提示
        risks = report_data.get("key_risks", [])
        if risks:
            st.markdown("### ⚠️ 风险提示")
            for risk in risks[:3]:
                st.warning(f"• {risk}")

    st.markdown("---")

    # 操作按钮
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 保存报告", type="primary", key="save_report_v2"):
            try:
                # 保存报告到文件
                reports_dir = Path("./reports")
                reports_dir.mkdir(exist_ok=True)

                stock_name = report_data.get("stock_name", stock_code)
                date_str = datetime.now().strftime("%Y-%m-%d")
                filename = f"{stock_name}_{stock_code}_{date_str}.json"
                filepath = reports_dir / filename

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)

                st.success(f"✅ 报告已保存: {filename}")
            except Exception as e:
                st.error(f"❌ 保存失败: {str(e)}")

    with col2:
        if st.button("📊 查看历史报告", key="view_history"):
            st.info("💡 点击顶部导航的'📊 投资分析'查看历史报告（功能开发中）")

    with col3:
        if st.button("🔄 分析其他股票", key="analyze_other"):
            # 清除分析状态
            for key in ["analyzing", "stock_code", "step1_status", "step2_status", "step3_status",
                       "step1_data", "step2_data", "step3_data"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


def render_investment_analysis_v2():
    """渲染投资分析页面 v2.0 - 整合版"""

    st.markdown("# 📊 投资分析")
    st.markdown("---")

    st.success("✅ Agent Army v2.0 - 全流程整合版")

    # 新手引导（首次访问显示）
    if "visited_analysis" not in st.session_state:
        render_newbie_guide()
        st.session_state.visited_analysis = True

    # 步骤1：输入股票代码
    stock_code = render_smart_input()

    # 步骤2+3：分析进度 + 报告展示
    if st.session_state.get("analyzing", False):
        stock_code = st.session_state.get("stock_code", "")
        render_analysis_progress(stock_code)

    # 步骤3：显示最终报告（分析完成后）
    if st.session_state.get("step3_status") == "completed":
        stock_code = st.session_state.get("stock_code", "")
        render_final_report(stock_code)
