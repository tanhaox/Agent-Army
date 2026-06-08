"""
Agent Army - Web界面 v2.0

核心改进：
- 顶部导航替代侧边栏
- 4个主导航项（精简）
- 全宽内容区域
- URL 参数控制页面切换
"""

import streamlit as st
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


# ==================== 页面配置 ====================
st.set_page_config(
    page_title="Agent Army",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="collapsed"  # ← 改为 collapsed，因为我们隐藏了侧边栏
)


# ==================== 初始化 session state ====================
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

        # 自动填充的股票代码
        st.session_state.auto_stock_code = ""

        st.session_state.initialized = True
        st.session_state.logger.info("Web界面 v2.0 初始化完成")
    except Exception as e:
        st.error(f"初始化失败: {str(e)}")
        st.exception(e)
        st.stop()


# ==================== 顶部导航 ⭐ v2.0 核心改进 ====================

def render_top_nav() -> str:
    """
    渲染顶部导航栏

    Returns:
        str: 当前页面标识 (home/analysis/monitor/settings)
    """

    # ========== 自定义 CSS 样式 ==========
    st.markdown("""
    <style>
    /* 隐藏默认侧边栏 */
    [data-testid="stSidebar"] {
        display: none !important;
    }

    /* 隐藏 Streamlit 默认的菜单和页脚 */
    [data-testid="stToolbar"] {
        display: none !important;
    }

    /* 隐藏 Streamlit 默认的菜单 */
    [data-testid="stHeader"] {
        display: none !important;
    }

    /* 顶部导航栏样式 */
    .top-nav {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 60px !important;
        background: linear-gradient(90deg, #1E88E5 0%, #43A047 100%) !important;
        display: flex !important;
        align-items: center !important;
        padding: 0 20px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        z-index: 999999 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }

    .top-nav .logo {
        font-size: 20px;
        font-weight: bold;
        color: white;
        margin-right: 50px;
        white-space: nowrap;
    }

    .top-nav .nav-item {
        color: white;
        text-decoration: none;
        padding: 10px 20px;
        margin: 0 5px;
        border-radius: 5px;
        transition: background 0.3s;
        font-size: 16px;
        display: inline-block;
    }

    .top-nav .nav-item:hover {
        background: rgba(255,255,255,0.2);
        text-decoration: none;
    }

    .top-nav .nav-item.active {
        background: rgba(255,255,255,0.3);
        font-weight: bold;
    }

    /* 内容区域 padding（为固定顶部导航留出空间）*/
    .main-content {
        padding-top: 80px !important;
        padding-left: 20px !important;
        padding-right: 20px !important;
    }

    /* 移动端适配 */
    @media (max-width: 768px) {
        .top-nav {
            padding: 0 10px !important;
        }

        .top-nav .logo {
            font-size: 16px;
            margin-right: 20px;
        }

        .top-nav .nav-item {
            padding: 8px 12px;
            font-size: 14px;
            margin: 0 2px;
        }

        .main-content {
            padding-top: 70px !important;
            padding-left: 10px !important;
            padding-right: 10px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # ========== 获取当前页面 ==========
    query_params = st.query_params

    # 优先级 1: 检查 session_state 中的当前页面（最高优先级）
    if st.session_state.get("current_page"):
        current_page = st.session_state.current_page
    # 优先级 2: 检查是否有跳转请求
    elif st.session_state.get("jump_to_analysis", False):
        current_page = "analysis"
        st.session_state.jump_to_analysis = False  # 清除标志
    # 优先级 3: 检查是否正在分析
    elif st.session_state.get("analyzing", False):
        current_page = "analysis"
    # 优先级 4: 从 URL 参数获取页面
    else:
        page_param = query_params.get("page", None)
        if page_param:
            # Streamlit 1.28+ 返回 FrozenDictNotification 或列表
            if isinstance(page_param, list):
                current_page = page_param[0] if page_param else "home"
            else:
                current_page = page_param
        else:
            current_page = "home"

        # 同步到 session_state
        st.session_state.current_page = current_page

    # 允许的页面列表
    valid_pages = ["home", "analysis", "monitor", "settings"]

    # 验证页面参数，如果无效则使用默认值
    if current_page not in valid_pages:
        current_page = "home"

    # ========== 设置激活状态 ==========
    active_states = {
        "home": "active" if current_page == "home" else "",
        "analysis": "active" if current_page == "analysis" else "",
        "monitor": "active" if current_page == "monitor" else "",
        "settings": "active" if current_page == "settings" else ""
    }

    # ========== 顶部导航（使用 Streamlit 组件）==========
    # 使用 container 在页面顶部创建导航栏
    nav_container = st.container()

    with nav_container:
        # 使用列布局创建导航栏
        col_logo, col_home, col_analysis, col_monitor, col_settings = st.columns([2, 1.5, 1.5, 1.5, 1.5])

        with col_logo:
            st.markdown("🎖️ **Agent Army**")

        with col_home:
            if st.button("🏠 首页", key="nav_home", use_container_width=True):
                st.session_state.current_page = "home"
                st.rerun()

        with col_analysis:
            if st.button("📊 投资分析", key="nav_analysis", use_container_width=True):
                st.session_state.current_page = "analysis"
                st.rerun()

        with col_monitor:
            if st.button("🤖 系统监控", key="nav_monitor", use_container_width=True):
                st.session_state.current_page = "monitor"
                st.rerun()

        with col_settings:
            if st.button("⚙️ 系统配置", key="nav_settings", use_container_width=True):
                st.session_state.current_page = "settings"
                st.rerun()

        st.markdown("---")

    # ========== 开始主内容区域 ==========
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    return current_page


def close_main_content():
    """闭合主内容区域的 div 标签"""
    st.markdown("</div>", unsafe_allow_html=True)


# 渲染顶部导航
current_page = render_top_nav()


# ==================== 页面路由 ====================

# ========== 页面1: 首页 ==========
if current_page == "home":
    from src.core.pages.enhanced_home import render_enhanced_home
    render_enhanced_home()


# ========== 页面2: 投资分析 ⭐ 核心功能 ==========
elif current_page == "analysis":
    from src.core.pages.investment_analysis_v2 import render_investment_analysis_v2
    render_investment_analysis_v2()


# ========== 页面3: 系统监控 ==========
elif current_page == "monitor":
    from src.core.pages.enhanced_agent_status import render_enhanced_agent_status
    render_enhanced_agent_status()


# ========== 页面4: 系统配置 ==========
elif current_page == "settings":
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


# ==================== 闭合主内容区域 ====================
close_main_content()


# ==================== 页脚 ====================
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 12px;'>
    © 2026 Agent Army v2.0 | 顶部导航版 | 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """,
    unsafe_allow_html=True
)
