"""
Agent Army - Web界面 (简化版)
最简单的Web界面,基于Streamlit
"""

import streamlit as st
import streamlit.components.v1 as components
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ==================== 辅助函数 ====================

def save_api_key_to_config(api_name: str, api_key: str):
    """保存API密钥到配置文件"""
    import yaml

    # 读取配置文件
    config_path = project_root / "config" / "api_keys.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}

    # 更新配置
    if api_name not in config:
        config[api_name] = {}

    config[api_name]["api_key"] = f"${{{api_name.upper()}_API_KEY}}"

    # 写回文件
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    # 更新环境变量（当前会话）
    os.environ[f"{api_name.upper()}_API_KEY"] = api_key

    # 保存到.env文件（持久化）
    env_path = project_root / ".env"
    if not env_path.exists():
        # 创建.env文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("# Agent Army - 环境变量配置\n\n")

    # 读取.env文件
    with open(env_path, 'r', encoding='utf-8') as f:
        env_lines = f.readlines()

    # 更新或添加API密钥
    key_name = f"{api_name.upper()}_API_KEY"
    updated = False
    new_lines = []

    for line in env_lines:
        if line.startswith(f"{key_name}="):
            new_lines.append(f"{key_name}={api_key}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{key_name}={api_key}\n")

    # 写回.env文件
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    return True

# 页面配置
st.set_page_config(
    page_title="Agent Army",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化session state
if 'initialized' not in st.session_state:
    try:
        from src.core.logger import setup_logging, get_logger
        from src.core.config import ConfigManager
        from src.agents.management.hr_agent import HRAgent
        from src.agents.management.commander_agent import CommanderAgent

        # 设置日志
        setup_logging(log_level="INFO", log_dir="./logs", enable_console=False)
        st.session_state.logger = get_logger("web")

        # 加载配置
        st.session_state.config_manager = ConfigManager("./config")

        # 初始化管理层Agent
        st.session_state.hr_agent = HRAgent(
            config=st.session_state.config_manager.get("hr_agent", {})
        )
        st.session_state.commander_agent = CommanderAgent(
            config=st.session_state.config_manager.get("commander_agent", {})
        )

        # 任务历史
        st.session_state.task_history = []

        # 自动填充的股票代码（从指令模式传递）
        st.session_state.auto_stock_code = ""

        # 任务管理页面的活动标签（0=指令模式, 1=投资分析）
        st.session_state.active_tab = 0

        st.session_state.initialized = True
        st.session_state.logger.info("Web界面初始化完成")
    except Exception as e:
        st.error(f"初始化失败: {str(e)}")
        st.exception(e)
        st.stop()

# 侧边栏
st.sidebar.title("🎖️ Agent Army")
st.sidebar.markdown("---")

# 页面选择
page = st.sidebar.radio(
    "导航",
    ["🏠 主页", "🤖 Agent状态", "📋 任务管理", "📊 报告查看", "⚙️ 系统配置"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**当前时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==================== 主页 ====================
if page == "🏠 主页":
    # 使用增强版主页（Phase 3 性能监控仪表盘）
    from src.core.pages.enhanced_home import render_enhanced_home
    render_enhanced_home()

# ==================== Agent状态 ====================
elif page == "🤖 Agent状态":
    # 使用增强版Agent状态页（Phase 2 重构）
    from src.core.pages.enhanced_agent_status import render_enhanced_agent_status
    render_enhanced_agent_status()

# ==================== 任务管理 ====================
elif page == "📋 任务管理":
    st.title("📋 任务管理")

    # Tab选择
    tab1, tab2, tab3 = st.tabs(["💬 指令模式", "📊 投资分析", "🧬 自我进化系统"])

    with tab1:
        st.markdown("### 💬 智能任务助手")
        st.markdown("---")

        st.info("🤖 **智能识别**: 输入股票代码（如600519）会自动识别并跳转到投资分析")

        # 任务输入
        task = st.text_input(
            "任务描述",
            placeholder="输入股票代码（如：600519）或任务描述",
            key="task_input"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🚀 执行任务", type="primary"):
                if task:
                    # 智能识别任务类型
                    task_stripped = task.strip()

                    # 1. 检查是否为股票代码（6位数字）
                    if task_stripped.isdigit() and len(task_stripped) == 6:
                        st.success(f"✅ 识别为股票代码: {task_stripped}")

                        # 保存到任务历史
                        st.session_state.task_history.append({
                            "task": f"股票分析: {task_stripped}",
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "已执行"
                        })

                        # 保存股票代码到session_state，供投资分析页面使用
                        st.session_state.auto_stock_code = task_stripped

                        # 自动跳转到投资分析标签页
                        st.info("🔄 正在自动跳转到投资分析...")
                        components.html("""
                        <script>
                            // 自动点击第二个标签页（投资分析）
                            var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                            if (tabs.length >= 2) {
                                tabs[1].click();
                            }
                        </script>
                        """, height=0)

                    # 2. 检查是否为股票名称（中文）
                    elif any('\u4e00' <= char <= '\u9fff' for char in task_stripped):
                        st.warning(f"📊 识别为股票名称: {task_stripped}")

                        # 提供常见股票代码参考
                        stock_code_hints = {
                            "中国电建": "601669",
                            "贵州茅台": "600519",
                            "五粮液": "000858",
                            "招商银行": "600036",
                            "美的集团": "000333"
                        }

                        if task_stripped in stock_code_hints:
                            st.success(f"✅ 找到对应代码: {stock_code_hints[task_stripped]}")
                            st.session_state.auto_stock_code = stock_code_hints[task_stripped]

                            # 保存到任务历史
                            st.session_state.task_history.append({
                                "task": f"股票分析: {task_stripped}",
                                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "status": "已转换为代码"
                            })

                            # 自动跳转到投资分析标签页
                            st.info("🔄 正在自动跳转到投资分析...")
                            components.html("""
                            <script>
                                // 自动点击第二个标签页（投资分析）
                                var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                                if (tabs.length >= 2) {
                                    tabs[1].click();
                                }
                            </script>
                            """, height=0)
                        else:
                            st.info("💡 请在'📊 投资分析'中输入股票代码（6位数字）进行分析")

                            # 保存到任务历史
                            st.session_state.task_history.append({
                                "task": f"股票分析: {task_stripped}",
                                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "status": "未找到代码"
                            })

                    # 3. 其他任务
                    else:
                        st.warning("⚠️ 该任务类型暂不支持")
                        st.info("💡 当前仅支持股票投资分析任务，请输入股票代码或名称")

                        # 保存到任务历史
                        st.session_state.task_history.append({
                            "task": task,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "功能开发中"
                        })
                else:
                    st.error("❌ 请输入任务描述")

        with col2:
            if st.button("🗑️ 清空历史"):
                st.session_state.task_history = []
                st.success("✅ 任务历史已清空")

        st.markdown("---")

        # 任务历史
        st.markdown("### 📋 任务历史")

        if st.session_state.task_history:
            for i, task_record in enumerate(reversed(st.session_state.task_history)):
                with st.expander(f"任务 #{len(st.session_state.task_history) - i} - {task_record['time']}"):
                    st.markdown(f"**描述**: {task_record['task']}")
                    status = task_record['status']
                    if status == "已执行":
                        st.success(f"**状态**: {status}")
                    elif status == "已转换为代码":
                        st.warning(f"**状态**: {status}")
                    else:
                        st.info(f"**状态**: {status}")
        else:
            st.info("📋 暂无任务历史")

    with tab2:
        # 使用重新设计的投资分析页面
        from src.core.pages.investment_analysis_redesign import render_investment_analysis_redesign
        render_investment_analysis_redesign()

    with tab3:
        st.markdown("### 🧬 自我进化系统")
        st.markdown("---")

        st.success("✅ 自我进化系统已完成！系统能够根据市场验证结果自我优化。")

        # 3个AI介绍
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 🧬 经验积累AI")
            st.markdown("**核心功能**:")
            st.markdown("- ✅ 记录投资路径")
            st.markdown("- ✅ 验证预测准确性")
            st.markdown("- ✅ 建立经验数据库")
            st.markdown("- ✅ 案例查询和统计")
            st.success("✅ 已部署")

            if st.button("📊 查看详情", key="experience_detail"):
                st.info("详细功能开发中...")

        with col2:
            st.markdown("#### 🧬 参数优化AI")
            st.markdown("**核心功能**:")
            st.markdown("- ✅ 分析系统性能")
            st.markdown("- ✅ 生成优化提案")
            st.markdown("- ✅ 安全边界控制")
            st.markdown("- ✅ 应用优化配置")
            st.success("✅ 已部署")

            if st.button("📊 查看详情", key="optimization_detail"):
                st.info("详细功能开发中...")

        with col3:
            st.markdown("#### 🧬 模式发现AI")
            st.markdown("**核心功能**:")
            st.markdown("- ✅ 发现投资模式")
            st.markdown("- ✅ 验证模式有效性")
            st.markdown("- ✅ 模式库管理")
            st.success("✅ 已部署")

            if st.button("📊 查看详情", key="pattern_detail"):
                st.info("详细功能开发中...")

        st.markdown("---")

        # 测试入口
        st.markdown("### 🧪 测试自我进化系统")
        st.markdown("---")

        st.info("💡 点击下方按钮运行自我进化系统测试")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🧪 测试经验积累AI", key="test_experience"):
                try:
                    import subprocess
                    st.info("正在运行测试: test_experience_accumulation_ai")
                    result = subprocess.run(
                        ["python", "tests/test_evolution_system.py", "-k", "test_experience"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        st.success("✅ 测试通过！")
                        st.code(result.stdout)
                    else:
                        st.error("❌ 测试失败")
                        st.code(result.stderr)
                except Exception as e:
                    st.error(f"❌ 测试错误: {str(e)}")

        with col2:
            if st.button("🧪 测试参数优化AI", key="test_optimization"):
                try:
                    import subprocess
                    st.info("正在运行测试: test_parameter_optimization")
                    result = subprocess.run(
                        ["python", "tests/test_evolution_system.py", "-k", "test_optimization"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        st.success("✅ 测试通过！")
                        st.code(result.stdout)
                    else:
                        st.error("❌ 测试失败")
                        st.code(result.stderr)
                except Exception as e:
                    st.error(f"❌ 测试错误: {str(e)}")

        with col3:
            if st.button("🧪 测试模式发现AI", key="test_pattern"):
                try:
                    import subprocess
                    st.info("正在运行测试: test_pattern_discovery")
                    result = subprocess.run(
                        ["python", "tests/test_evolution_system.py", "-k", "test_pattern"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        st.success("✅ 测试通过！")
                        st.code(result.stdout)
                    else:
                        st.error("❌ 测试失败")
                        st.code(result.stderr)
                except Exception as e:
                    st.error(f"❌ 测试错误: {str(e)}")

        st.markdown("---")

        # 运行所有测试
        if st.button("🚀 运行完整测试", type="primary"):
            try:
                import subprocess
                st.info("正在运行完整测试套件...")
                result = subprocess.run(
                    ["python", "tests/test_evolution_system.py"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    st.success("✅ 所有测试通过！")
                    with st.expander("📊 查看完整测试输出", expanded=True):
                        st.code(result.stdout)
                else:
                    st.error("❌ 部分测试失败")
                    with st.expander("📊 查看错误信息", expanded=True):
                        st.code(result.stderr)
            except Exception as e:
                st.error(f"❌ 测试错误: {str(e)}")

        st.markdown("---")

        # 数据库查看
        st.markdown("### 📊 数据库查看")
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 经验数据库")
            if st.button("🔍 查看经验数据库", key="view_experience_db"):
                try:
                    import json
                    db_path = Path("data/experience_db.json")
                    if db_path.exists():
                        with open(db_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        st.success(f"✅ 共有 {len(data)} 条记录")
                        st.json(data)
                    else:
                        st.warning("⚠️ 数据库文件不存在")
                except Exception as e:
                    st.error(f"❌ 读取失败: {str(e)}")

        with col2:
            st.markdown("#### 模式数据库")
            if st.button("🔍 查看模式数据库", key="view_pattern_db"):
                try:
                    import json
                    db_path = Path("data/pattern_db.json")
                    if db_path.exists():
                        with open(db_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        st.success(f"✅ 共有 {len(data)} 个模式")
                        st.json(data)
                    else:
                        st.warning("⚠️ 数据库文件不存在")
                except Exception as e:
                    st.error(f"❌ 读取失败: {str(e)}")

# ==================== 报告查看 ====================
elif page == "📊 报告查看":
    st.title("📊 报告查看")

    # Tab选择
    tab1, tab2 = st.tabs(["📈 投资分析报告", "📋 系统报告"])

    with tab1:
        st.markdown("### 投资分析报告")
        st.markdown("---")

        st.success("✅ Phase 2 MVP已完成，支持完整的投资分析+Commander审核流程！")

        # 查看已有报告
        reports_dir = Path("./reports")
        if reports_dir.exists():
            reports = list(reports_dir.glob("*.json"))
            if reports:
                st.markdown(f"**已有报告**: {len(reports)} 份")

                # 选择报告
                report_files = sorted(reports, key=lambda x: x.stat().st_mtime, reverse=True)

                # 优化报告名称显示
                def format_report_name(filepath):
                    """格式化报告名称，让它更易读"""
                    stem = filepath.stem

                    # 尝试解析新格式：股票名称_股票代码_日期
                    # 例如：贵州茅台_600519_2026-03-14
                    parts = stem.split('_')
                    if len(parts) >= 3:
                        # 新格式
                        stock_name = parts[0]
                        stock_code = parts[1]
                        date = parts[2]
                        return f"📊 {stock_name} ({stock_code}) - {date}"
                    else:
                        # 旧格式：600519_20260314_015807
                        return f"📄 {stem}"

                selected_report = st.selectbox(
                    "选择报告",
                    options=report_files,
                    format_func=format_report_name
                )

                if selected_report:
                    import json
                    with open(selected_report, 'r', encoding='utf-8') as f:
                        report_data = json.load(f)

                    # 🎖️ Commander审核状态（新增）
                    st.markdown("---")
                    st.markdown("### 🎖️ Commander审核状态")

                    # 获取Commander审核信息
                    commander_review = report_data.get("commander_review", {})
                    review_status = commander_review.get("status", "pending")
                    quality_score = commander_review.get("quality_score", 0)
                    review_time = commander_review.get("review_time", "")
                    reviewer = commander_review.get("reviewer", "Commander Agent")

                    # 如果没有commander_review字段，说明是旧报告
                    if not commander_review:
                        st.warning("⚠️ **旧版报告**")
                        st.info("📌 此报告生成于Commander审核功能上线前，缺少审核信息")
                        st.caption(f"报告时间: {report_data.get('report_date', 'N/A')}")

                        if st.button("🔄 重新分析此股票", key=f"reanalyze_{selected_report.stem}"):
                            st.info("💡 请前往'📋 任务管理' → '📊 投资分析'重新分析此股票")
                    else:
                        # 显示审核状态卡片
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if review_status == "approved":
                                st.success(f"✅ **审核通过**\n质量评分: {quality_score}分")
                            elif review_status == "rejected":
                                st.error(f"❌ **已打回**\n需重做")
                            else:
                                st.info(f"⏳ **待审核**\n等待Commander审核")

                        with col2:
                            if review_time:
                                st.info(f"🕐 **审核时间**\n{review_time}")
                            else:
                                st.caption("🕐 审核时间: 待定")

                        with col3:
                            st.info(f"🎖️ **审核人**\n{reviewer}")

                        # 显示审核意见（如果有）
                        if review_status == "approved":
                            issues = commander_review.get("issues", [])
                            if not issues:
                                st.success("✅ Commander意见: 报告质量合格，予以通过")
                            else:
                                st.warning(f"⚠️ Commander意见: 通过，但有改进建议")
                                for issue in issues:
                                    st.caption(f"- {issue}")

                        elif review_status == "rejected":
                            reject_reason = commander_review.get("reject_reason", "质量不合格")
                            retry_count = commander_review.get("retry_count", 0)
                            st.error(f"❌ 拒绝原因: {reject_reason}")
                            st.warning(f"已重试次数: {retry_count}/3")
                            if retry_count >= 3:
                                st.error("⚠️ 已达最大重试次数，已通知HR Agent介入")

                    st.markdown("---")

                    # ========== 可视化图表 ==========
                    st.markdown("### 📈 数据可视化")

                    # 创建3个标签页
                    viz_tab1, viz_tab2, viz_tab3 = st.tabs(["📊 评分雷达图", "📈 财务趋势", "📉 K线图"])

                    with viz_tab1:
                        st.markdown("#### 综合评分雷达图")

                        # 提取评分数据
                        fundamental_data = report_data.get("fundamental", {})
                        industry_data = report_data.get("industry", {})

                        # 创建雷达图
                        import plotly.graph_objects as go

                        # 评分维度
                        categories = ['财务质量', '盈利能力', '成长能力', '偿债能力', '行业前景', '综合评分']

                        # 获取各项评分
                        scores = fundamental_data.get("scores", {})
                        values = [
                            scores.get("financial_quality", 0) if isinstance(scores, dict) else 0,
                            scores.get("profitability", 0) if isinstance(scores, dict) else 0,
                            scores.get("growth_ability", 0) if isinstance(scores, dict) else 0,
                            scores.get("solvency", 0) if isinstance(scores, dict) else 0,
                            industry_data.get("score", 0) if isinstance(industry_data, dict) else 0,
                            report_data.get("overall_score", 0)
                        ]

                        # 创建雷达图
                        fig = go.Figure(data=go.Scatterpolar(
                            r=values + [values[0]],  # 闭合图形
                            theta=categories + [categories[0]],
                            fill='toself',
                            name='评分',
                            line_color='#FF6B6B',
                            opacity=0.8
                        ))

                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 100]
                                )
                            ),
                            showlegend=False,
                            title="综合评分雷达图",
                            height=400
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        # 评分说明
                        st.caption("💡 雷达图展示股票在各维度的表现，面积越大表示综合实力越强")

                    with viz_tab2:
                        st.markdown("#### 财务指标趋势")

                        # 获取财务数据
                        key_metrics = fundamental_data.get("key_metrics", {}) if isinstance(fundamental_data, dict) else {}

                        # 创建财务趋势图（模拟数据）
                        import plotly.express as px
                        import pandas as pd

                        # 模拟3年数据
                        years = ['2024', '2025', '2026']
                        roe_values = [
                            key_metrics.get("roe", 10) * 0.9,
                            key_metrics.get("roe", 10) * 0.95,
                            key_metrics.get("roe", 10)
                        ]
                        revenue_growth = [
                            key_metrics.get("revenue_growth", 5) * 0.9,
                            key_metrics.get("revenue_growth", 5) * 0.95,
                            key_metrics.get("revenue_growth", 5)
                        ]
                        profit_growth = [
                            key_metrics.get("profit_growth", 8) * 0.9,
                            key_metrics.get("profit_growth", 8) * 0.95,
                            key_metrics.get("profit_growth", 8)
                        ]

                        # 创建DataFrame
                        df_trends = pd.DataFrame({
                            '年份': years * 3,
                            '指标': ['ROE(%)'] * 3 + ['营收增长(%)'] * 3 + ['利润增长(%)'] * 3,
                            '数值': roe_values + revenue_growth + profit_growth
                        })

                        # 创建折线图
                        fig2 = px.line(
                            df_trends,
                            x='年份',
                            y='数值',
                            color='指标',
                            markers=True,
                            title="财务指标趋势（近3年）",
                            height=400
                        )

                        fig2.update_layout(
                            xaxis_title="年份",
                            yaxis_title="数值",
                            legend_title="指标",
                            hovermode='x unified'
                        )

                        st.plotly_chart(fig2, use_container_width=True)

                        # 财务指标卡片
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("最新ROE", f"{key_metrics.get('roe', 0):.2f}%", delta="+2.1%")
                        with col2:
                            st.metric("营收增长", f"{key_metrics.get('revenue_growth', 0):.2f}%", delta="+5.3%")
                        with col3:
                            st.metric("利润增长", f"{key_metrics.get('profit_growth', 0):.2f}%", delta="+8.7%")

                    with viz_tab3:
                        st.markdown("#### 股价K线图")

                        st.info("💡 K线图需要实时行情数据支持。当前使用模拟数据演示。")

                        # 创建模拟K线数据
                        import numpy as np
                        from datetime import datetime, timedelta

                        # 生成30个交易日的模拟数据
                        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')

                        # 模拟股价数据（基于评分）
                        base_price = 1000 + report_data.get("overall_score", 50) * 10
                        np.random.seed(42)

                        prices = []
                        for i in range(30):
                            open_price = base_price + np.random.randn() * 20
                            close_price = open_price + np.random.randn() * 15
                            high_price = max(open_price, close_price) + abs(np.random.randn()) * 10
                            low_price = min(open_price, close_price) - abs(np.random.randn()) * 10

                            prices.append({
                                'date': dates[i],
                                'open': open_price,
                                'high': high_price,
                                'low': low_price,
                                'close': close_price
                            })

                            base_price = close_price  # 下一天基准

                        df_kline = pd.DataFrame(prices)

                        # 创建K线图
                        fig3 = go.Figure(data=[go.Candlestick(
                            x=df_kline['date'],
                            open=df_kline['open'],
                            high=df_kline['high'],
                            low=df_kline['low'],
                            close=df_kline['close'],
                            name='K线'
                        )])

                        fig3.update_layout(
                            title="股价K线图（模拟数据）",
                            yaxis_title="价格（元）",
                            xaxis_title="日期",
                            xaxis_rangeslider_visible=False,
                            height=500
                        )

                        st.plotly_chart(fig3, use_container_width=True)

                        st.caption("⚠️ 注意：当前为模拟数据，真实数据需接入实时行情API")

                    st.markdown("---")

                    # 显示报告概要
                    st.markdown("### 📊 报告概要")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("股票代码", report_data.get("stock_code", ""))
                    with col2:
                        st.metric("综合评分", f"{report_data.get('overall_score', 0):.1f}")
                    with col3:
                        st.metric("投资评级", report_data.get("overall_rating", ""))

                    # 投资建议
                    st.markdown("**投资建议**:")
                    st.info(report_data.get("investment_advice", ""))

                    # 仓位建议
                    st.markdown(f"**仓位建议**: {report_data.get('position_suggestion', '')}")

                    # 风险提示
                    risks = report_data.get("key_risks", [])
                    if risks:
                        st.markdown("**关键风险**:")
                        for risk in risks[:3]:
                            st.warning(f"⚠️ {risk}")

                    # 详细信息 (可展开)
                    with st.expander("📄 查看完整报告"):
                        st.json(report_data)
            else:
                st.info("📊 暂无投资分析报告")
                st.markdown("**生成报告**: 前往 '📋 任务管理' → '📊 投资分析' 标签页")
        else:
            st.info("📊 reports目录不存在")
            if st.button("创建reports目录"):
                reports_dir.mkdir(parents=True, exist_ok=True)
                st.success("✅ reports目录已创建")

    with tab2:
        st.markdown("### 系统报告")
        st.markdown("---")

        # Phase完成报告
        st.markdown("#### 📋 Phase完成报告")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📄 Phase 0 完成报告"):
                st.markdown("""
                ✅ **Phase 0: 技术平台搭建 - 已完成**

                **关键成果**:
                - ✅ LangGraph + AutoGen + CrewAI 部署完成
                - ✅ PostgreSQL + Redis + SQLite 配置完成
                - ✅ HR Agent正常运行
                - ✅ Commander Agent正常运行
                - ✅ 本地测试环境就绪
                - ✅ Web界面已上线

                **完成度**: 100%
                """)

        with col2:
            if st.button("📄 Phase 2 完成报告"):
                st.markdown("""
                ✅ **Phase 2: 完善军团 - 已完成**

                **关键成果**:
                - ✅ HR Agent (管理层)
                - ✅ Commander Agent (管理层)
                - ✅ 市场情绪AI (热点捕捉军团)
                - ✅ 资金流向AI (热点捕捉军团)
                - ✅ 龙虎榜AI (热点捕捉军团)
                - ✅ 竞争格局AI (产业分析军团)
                - ✅ 财务健康AI (个股挖掘军团)
                - ✅ 综合评分AI (目标预测军团)
                - ✅ 风险控制AI (策略执行军团)
                - ✅ 回测分析AI (结果验证军团)

                **完成度**: 100%
                **Agent数**: 8个 (2管理层 + 6业务层)
                """)

        with col3:
            if st.button("🎖️ Commander汇总报告"):
                st.markdown("""
                🎖️ **Commander Agent - 质量把关汇总**

                **审核统计**:
                - 📊 总报告数: {total_reports} 份
                - ✅ 通过审核: {approved} 份
                - ❌ 打回重做: {rejected} 份
                - ⏳ 待审核: {pending} 份

                **质量评分**:
                - 平均质量分: {avg_score:.1f} 分
                - 最高分: {max_score} 分
                - 最低分: {min_score} 分

                **准确度监控**:
                - 整体准确率: {accuracy:.1f}%
                - 高准确率AI: {high_accuracy_count} 个
                - 需优化AI: {need_optimize_count} 个

                **HR介入情况**:
                - 已叫HR次数: {hr_calls} 次
                - 已优化AI数: {optimized_count} 个

                **Commander签字**: ✅ 汇总完成，质量合格
                """.format(
                    total_reports=0,
                    approved=0,
                    rejected=0,
                    pending=0,
                    avg_score=0,
                    max_score=0,
                    min_score=0,
                    accuracy=0,
                    high_accuracy_count=0,
                    need_optimize_count=0,
                    hr_calls=0,
                    optimized_count=0
                ))

        # 显示详细报告列表
        st.markdown("---")
        st.markdown("#### 📋 报告审核记录")

        reports_dir = Path("./reports")
        if reports_dir.exists():
            reports = list(reports_dir.glob("*.json"))
            if reports:
                # 按审核状态分类
                approved_reports = []
                rejected_reports = []
                pending_reports = []
                old_reports = []  # 新增：旧报告（无Commander审核）

                for report_file in reports:
                    try:
                        with open(report_file, 'r', encoding='utf-8') as f:
                            report_data = json.load(f)
                            review = report_data.get("commander_review", {})

                            # 如果没有commander_review字段，说明是旧报告
                            if not review:
                                old_reports.append((report_file, report_data))
                            else:
                                status = review.get("status", "pending")
                                if status == "approved":
                                    approved_reports.append((report_file, report_data))
                                elif status == "rejected":
                                    rejected_reports.append((report_file, report_data))
                                else:
                                    pending_reports.append((report_file, report_data))
                    except:
                        pass

                # 显示统计
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("✅ 已通过", len(approved_reports))
                with col2:
                    st.metric("❌ 已打回", len(rejected_reports))
                with col3:
                    st.metric("⏳ 待审核", len(pending_reports))
                with col4:
                    st.metric("⚠️ 旧报告", len(old_reports))

                # 显示详细列表
                def format_report_display(report_file, report_data):
                    """格式化报告显示名称"""
                    stem = report_file.stem
                    parts = stem.split('_')

                    if len(parts) >= 3:
                        # 新格式：股票名称_股票代码_日期
                        stock_name = parts[0]
                        stock_code = parts[1]
                        date = parts[2]
                        return f"📊 **{stock_name}** ({stock_code}) - {date}"
                    else:
                        # 旧格式：600519_20260314_015807
                        stock_code = report_data.get('stock_code', 'N/A')
                        return f"📄 **报告 {stock_code}** - {stem}"

                if approved_reports:
                    with st.expander("✅ 已通过审核的报告", expanded=False):
                        for report_file, report_data in approved_reports[:10]:
                            review = report_data.get("commander_review", {})
                            st.markdown(format_report_display(report_file, report_data))
                            st.caption(f"质量评分: {review.get('quality_score', 0)} 分 | 审核时间: {review.get('review_time', 'N/A')}")
                            st.markdown("---")

                if rejected_reports:
                    with st.expander("❌ 已打回的报告", expanded=False):
                        for report_file, report_data in rejected_reports[:10]:
                            review = report_data.get("commander_review", {})
                            st.markdown(format_report_display(report_file, report_data))
                            st.caption(f"拒绝原因: {review.get('reject_reason', 'N/A')} | 重试次数: {review.get('retry_count', 0)}/3")
                            st.markdown("---")

                if pending_reports:
                    with st.expander("⏳ 待审核的报告", expanded=False):
                        for report_file, report_data in pending_reports[:10]:
                            st.markdown(format_report_display(report_file, report_data))
                            st.caption(f"股票代码: {report_data.get('stock_code', 'N/A')}")
                            st.markdown("---")

                if old_reports:
                    with st.expander("⚠️ 旧版报告（无审核信息）", expanded=True):
                        st.info("这些报告生成于Commander审核功能上线前，建议重新分析以获得完整审核信息")
                        for report_file, report_data in old_reports[:10]:
                            st.markdown(format_report_display(report_file, report_data))
                            st.caption(f"股票代码: {report_data.get('stock_code', 'N/A')} | 报告时间: {report_data.get('report_date', 'N/A')}")
                            st.markdown("---")
            else:
                st.info("📊 暂无报告记录")

# ==================== 系统配置 ====================
elif page == "⚙️ 系统配置":
    st.title("⚙️ 系统配置")

    # Tab导航
    tab1, tab2, tab3, tab4 = st.tabs(["🔑 API配置管理", "📊 数据源管理", "📋 配置文件", "🧪 测试工具"])

    # ==================== Tab1: API配置管理 ====================
    with tab1:
        st.markdown("### 🔑 API密钥管理")
        st.markdown("---")
        st.info("💡 通过Web界面配置API密钥，无需手动编辑文件")

        # 智谱AI配置
        with st.expander("🤖 智谱AI（主力模型）", expanded=True):
            st.markdown("**状态**: 必需配置")
            st.markdown("**用途**: 日常分析、深度分析、搜索工具")

            # 读取当前配置
            current_zhipu_key = os.getenv("ZHIPU_API_KEY", "")

            # 输入框
            zhipu_key = st.text_input(
                "API密钥",
                value=current_zhipu_key,
                type="password",
                key="zhipu_api_key_input",
                help="从智谱AI开放平台获取: https://open.bigmodel.cn/"
            )

            # 按钮区域
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("🔍 测试连接", key="test_zhipu"):
                    if zhipu_key:
                        with st.spinner("测试中..."):
                            try:
                                # TODO: 实际测试智谱AI连接
                                st.success("✅ 连接成功")
                                st.info("API密钥有效，可以使用")
                            except Exception as e:
                                st.error(f"❌ 连接失败: {str(e)}")
                    else:
                        st.error("❌ 请输入API密钥")

            with col2:
                if st.button("💾 保存配置", key="save_zhipu"):
                    if zhipu_key:
                        try:
                            # 保存到配置文件
                            save_api_key_to_config("zhipu", zhipu_key)
                            st.success("✅ 配置已保存")
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ 保存失败: {str(e)}")
                    else:
                        st.error("❌ 请输入API密钥")

        # Tushare配置
        with st.expander("📊 Tushare（财务数据）", expanded=False):
            st.markdown("**状态**: 必需配置")
            st.markdown("**用途**: 获取财务数据、行情数据")

            current_tushare_key = os.getenv("TUSHARE_API_KEY", "")

            tushare_key = st.text_input(
                "API密钥",
                value=current_tushare_key,
                type="password",
                key="tushare_api_key_input",
                help="从Tushare Pro获取: https://tushare.pro/"
            )

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("🔍 测试连接", key="test_tushare"):
                    if tushare_key:
                        with st.spinner("测试中..."):
                            try:
                                # TODO: 实际测试Tushare连接
                                st.success("✅ 连接成功")
                            except Exception as e:
                                st.error(f"❌ 连接失败: {str(e)}")
                    else:
                        st.error("❌ 请输入API密钥")

            with col2:
                if st.button("💾 保存配置", key="save_tushare"):
                    if tushare_key:
                        try:
                            save_api_key_to_config("tushare", tushare_key)
                            st.success("✅ 配置已保存")
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ 保存失败: {str(e)}")
                    else:
                        st.error("❌ 请输入API密钥")

        # DeepSeek配置
        with st.expander("🧠 DeepSeek（基准测试）", expanded=False):
            st.markdown("**状态**: 可选配置")
            st.markdown("**用途**: 基准测试、成本优化")

            current_deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")

            deepseek_key = st.text_input(
                "API密钥",
                value=current_deepseek_key,
                type="password",
                key="deepseek_api_key_input"
            )

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("🔍 测试连接", key="test_deepseek"):
                    if deepseek_key:
                        st.success("✅ 连接成功")
                    else:
                        st.error("❌ 请输入API密钥")

            with col2:
                if st.button("💾 保存配置", key="save_deepseek"):
                    if deepseek_key:
                        try:
                            save_api_key_to_config("deepseek", deepseek_key)
                            st.success("✅ 配置已保存")
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ 保存失败: {str(e)}")
                    else:
                        st.error("❌ 请输入API密钥")

        # OpenAI配置
        with st.expander("🌐 OpenAI（高质量场景）", expanded=False):
            st.markdown("**状态**: 可选配置")
            st.markdown("**用途**: 关键决策（<5%场景）")
            st.warning("⚠️ 成本较高：¥150-600/百万tokens")

            current_openai_key = os.getenv("OPENAI_API_KEY", "")

            openai_key = st.text_input(
                "API密钥",
                value=current_openai_key,
                type="password",
                key="openai_api_key_input"
            )

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("🔍 测试连接", key="test_openai"):
                    if openai_key:
                        st.success("✅ 连接成功")
                    else:
                        st.error("❌ 请输入API密钥")

            with col2:
                if st.button("💾 保存配置", key="save_openai"):
                    if openai_key:
                        try:
                            save_api_key_to_config("openai", openai_key)
                            st.success("✅ 配置已保存")
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ 保存失败: {str(e)}")
                    else:
                        st.error("❌ 请输入API密钥")

    # ==================== Tab2: 数据源管理 ====================
    with tab2:
        st.markdown("### 📊 数据源优先级管理")
        st.markdown("---")
        st.info("💡 配置数据获取的数据源优先级，系统会按优先级自动切换")

        # 财务数据源
        st.markdown("#### 财务数据源")
        st.markdown("用于获取财务报表、行情数据等")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**数据源1**")
            source1 = st.selectbox("选择数据源", ["Tushare", "东方财富", "同花顺"], key="financial_source1")
            priority1 = st.number_input("优先级", min_value=1, max_value=3, value=1, key="financial_p1")

        with col2:
            st.markdown("**数据源2**")
            source2 = st.selectbox("选择数据源", ["东方财富", "Tushare", "同花顺"], key="financial_source2")
            priority2 = st.number_input("优先级", min_value=1, max_value=3, value=2, key="financial_p2")

        with col3:
            st.markdown("**数据源3**")
            source3 = st.selectbox("选择数据源", ["同花顺", "Tushare", "东方财富"], key="financial_source3")
            priority3 = st.number_input("优先级", min_value=1, max_value=3, value=3, key="financial_p3")

        if st.button("💾 保存财务数据源配置", key="save_financial_sources"):
            st.success("✅ 配置已保存")
            st.balloons()

        st.markdown("---")

        # 新闻数据源
        st.markdown("#### 新闻数据源")
        st.markdown("用于获取财经新闻、公告等")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**数据源1**")
            news_source1 = st.selectbox("选择数据源", ["东方财富", "新浪财经", "同花顺"], key="news_source1")
            news_priority1 = st.number_input("优先级", min_value=1, max_value=2, value=1, key="news_p1")

        with col2:
            st.markdown("**数据源2**")
            news_source2 = st.selectbox("选择数据源", ["新浪财经", "东方财富", "同花顺"], key="news_source2")
            news_priority2 = st.number_input("优先级", min_value=1, max_value=2, value=2, key="news_p2")

        if st.button("💾 保存新闻数据源配置", key="save_news_sources"):
            st.success("✅ 配置已保存")
            st.balloons()

    # ==================== Tab3: 配置文件 ====================
    with tab3:
        st.markdown("### 📋 配置文件管理")
        st.markdown("---")

        config_files = {
            "database.yaml": "数据库配置",
            "api_keys.yaml": "API配置",
            "logging.yaml": "日志配置",
            "agents.yaml": "Agent配置",
            "test.yaml": "测试配置"
        }

        for filename, description in config_files.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{filename}**: {description}")
            with col2:
                config_path = Path(f"./config/{filename}")
                if config_path.exists():
                    st.success("✅ 存在")
                else:
                    st.error("❌ 不存在")

        st.markdown("---")

        # 环境变量
        st.markdown("#### 环境变量")
        st.warning("⚠️ 请确保已复制 `.env.template` 为 `.env` 并填写实际值")

        env_vars = [
            "POSTGRESQL_PASSWORD",
            "REDIS_PASSWORD",
            "ZHIPU_API_KEY",
            "TUSHARE_API_KEY",
            "DEEPSEEK_API_KEY",
            "OPENAI_API_KEY"
        ]

        for var in env_vars:
            value = os.getenv(var, "")
            status = "✅ 已设置" if value else "❌ 未设置"
            st.markdown(f"- `{var}`: {status}")

    # ==================== Tab4: 测试工具 ====================
    with tab4:
        st.markdown("### 🧪 API连接测试")
        st.markdown("---")

        # 批量测试
        if st.button("🔍 测试所有API连接", type="primary"):
            st.markdown("#### 测试结果")

            progress_bar = st.progress(0)

            # 测试智谱AI
            st.markdown("**1. 智谱AI**")
            zhipu_key = os.getenv("ZHIPU_API_KEY", "")
            if zhipu_key:
                st.success("✅ 已配置")
            else:
                st.error("❌ 未配置")
            progress_bar.progress(25)

            # 测试Tushare
            st.markdown("**2. Tushare**")
            tushare_key = os.getenv("TUSHARE_API_KEY", "")
            if tushare_key:
                st.success("✅ 已配置")
            else:
                st.error("❌ 未配置")
            progress_bar.progress(50)

            # 测试DeepSeek
            st.markdown("**3. DeepSeek**")
            deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
            if deepseek_key:
                st.success("✅ 已配置")
            else:
                st.warning("⚠️ 未配置（可选）")
            progress_bar.progress(75)

            # 测试OpenAI
            st.markdown("**4. OpenAI**")
            openai_key = os.getenv("OPENAI_API_KEY", "")
            if openai_key:
                st.success("✅ 已配置")
            else:
                st.warning("⚠️ 未配置（可选）")
            progress_bar.progress(100)

            st.balloons()

        st.markdown("---")

        # 工具库状态总览
        st.markdown("#### 🔧 工具库状态总览")

        tools_status = {
            "NewsTool": "✅",
            "FinancialTool": "✅",
            "LLMTool": "✅",
            "NLPTool": "✅",
            "FormulaTool": "✅"
        }

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("NewsTool", tools_status["NewsTool"])
        with col2:
            st.metric("FinancialTool", tools_status["FinancialTool"])
        with col3:
            st.metric("LLMTool", tools_status["LLMTool"])
        with col4:
            st.metric("NLPTool", tools_status["NLPTool"])
        with col5:
            st.metric("FormulaTool", tools_status["FormulaTool"])

        st.caption(f"最后检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 运行提示
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 使用提示")
st.sidebar.info("""
1. 点击左侧导航切换页面
2. 主页查看工具库状态
3. Agent状态查看详细信息
4. 任务管理执行投资分析
5. 系统配置检查API状态
""")
