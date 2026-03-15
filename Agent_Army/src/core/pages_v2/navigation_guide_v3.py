"""
Agent Army - 导航指南页面 (v3.0)
基于Phase 2设计文档，100%使用Design Tokens
"""

import streamlit as st
from pathlib import Path
import sys

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入Phase 1设计系统
from src.core.design_tokens import DesignTokens
from src.core.global_styles import apply_global_styles


def render_navigation_guide_v3():
    """渲染导航指南页面（v3.0版）"""

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
                📖 导航指南
            </h1>
            <p style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin: {DesignTokens.Spacing.M_NONE} 0 {DesignTokens.Spacing.M_SM} 0;">
                快速入门 | 功能说明 | 常见问题 | 使用技巧
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ==================== 快速开始 ====================

    st.markdown(f"""
    <h2 style="font-size: {DesignTokens.Typography.H2};
               color: {DesignTokens.Colors.TEXT_PRIMARY};
               margin-bottom: {DesignTokens.Spacing.M_MD};">
        🚀 快速开始
    </h2>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="
        background: {DesignTokens.Colors.BG_CARD};
        border-radius: {DesignTokens.Radius.LG};
        padding: {DesignTokens.Spacing.P_LG};
        margin-bottom: {DesignTokens.Spacing.M_MD};
        box-shadow: {DesignTokens.Shadow.SM};
    ">
        <h3 style="font-size: {DesignTokens.Typography.H3};
                   color: {DesignTokens.Colors.TEXT_PRIMARY};
                   margin-top: 0;
                   margin-bottom: {DesignTokens.Spacing.M_SM};">
            第一步：配置API密钥
        </h3>
        <div style="font-size: {DesignTokens.Typography.BODY};
                 color: {DesignTokens.Colors.TEXT_PRIMARY};
                 line-height: 1.6;">
            前往 <strong>⚙️ 系统配置</strong> 页面，配置以下API密钥：
            <ul style="margin-top: {DesignTokens.Spacing.M_SM};">
                <li><strong>Tushare API</strong>: 用于获取A股市场数据（<a href="https://tushare.pro/register" target="_blank" style="color: {DesignTokens.Colors.PRIMARY};">免费注册</a>）</li>
                <li><strong>OpenAI API</strong>: 用于AI分析和预测（可选）</li>
                <li><strong>Zhipu AI API</strong>: 国产大模型支持（可选）</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="
        background: {DesignTokens.Colors.BG_CARD};
        border-radius: {DesignTokens.Radius.LG};
        padding: {DesignTokens.Spacing.P_LG};
        margin-bottom: {DesignTokens.Spacing.M_MD};
        box-shadow: {DesignTokens.Shadow.SM};
    ">
        <h3 style="font-size: {DesignTokens.Typography.H3};
                   color: {DesignTokens.Colors.TEXT_PRIMARY};
                   margin-top: 0;
                   margin-bottom: {DesignTokens.Spacing.M_SM};">
            第二步：创建分析任务
        </h3>
        <div style="font-size: {DesignTokens.Typography.BODY};
                 color: {DesignTokens.Colors.TEXT_PRIMARY};
                 line-height: 1.6;">
            前往 <strong>📋 任务管理</strong> 页面，创建新的分析任务：
            <ol style="margin-top: {DesignTokens.Spacing.M_SM};">
                <li>选择任务类型（个股分析/产业分析/热点监控）</li>
                <li>输入股票代码（例如：000001）</li>
                <li>选择分析深度（快速/标准/深度）</li>
                <li>点击"▶️ 开始"执行任务</li>
            </ol>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="
        background: {DesignTokens.Colors.BG_CARD};
        border-radius: {DesignTokens.Radius.LG};
        padding: {DesignTokens.Spacing.P_LG};
        margin-bottom: {DesignTokens.Spacing.M_MD};
        box-shadow: {DesignTokens.Shadow.SM};
    ">
        <h3 style="font-size: {DesignTokens.Typography.H3};
                   color: {DesignTokens.Colors.TEXT_PRIMARY};
                   margin-top: 0;
                   margin-bottom: {DesignTokens.Spacing.M_SM};">
            第三步：查看分析报告
        </h3>
        <div style="font-size: {DesignTokens.Typography.BODY};
                 color: {DesignTokens.Colors.TEXT_PRIMARY};
                 line-height: 1.6;">
            前往 <strong>📊 分析报告</strong> 页面，查看综合分析结果：
            <ul style="margin-top: {DesignTokens.Spacing.M_SM};">
                <li><strong>6大军团分析</strong>: 产业、热点、个股、目标、策略、验证</li>
                <li><strong>雷达图</strong>: 可视化各军团评分</li>
                <li><strong>趋势图</strong>: 近30天评分趋势</li>
                <li><strong>详细数据表</strong>: 结构化数据展示</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ==================== 功能说明 ====================

    st.markdown(f"""
    <h2 style="font-size: {DesignTokens.Typography.H2};
               color: {DesignTokens.Colors.TEXT_PRIMARY};
               margin-bottom: {DesignTokens.Spacing.M_MD};
               margin-top: {DesignTokens.Spacing.M_LG};">
        💡 功能说明
    </h2>
    """, unsafe_allow_html=True)

    # 功能卡片网格
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
            box-shadow: {DesignTokens.Shadow.SM};
            border-left: 4px solid {DesignTokens.Colors.PRIMARY};
        ">
            <h4 style="font-size: {DesignTokens.Typography.H4};
                       color: {DesignTokens.Colors.PRIMARY};
                       margin-top: 0;
                       margin-bottom: {DesignTokens.Spacing.M_SM};">
                🏠 主页
            </h4>
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};">
                <strong>核心功能</strong>:
                <ul>
                    <li>系统概览和统计信息</li>
                    <li>6大军团状态监控</li>
                    <li>最近任务列表</li>
                    <li>快速操作入口</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
            box-shadow: {DesignTokens.Shadow.SM};
            border-left: 4px solid {DesignTokens.Colors.SUCCESS};
        ">
            <h4 style="font-size: {DesignTokens.Typography.H4};
                       color: {DesignTokens.Colors.SUCCESS};
                       margin-top: 0;
                       margin-bottom: {DesignTokens.Spacing.M_SM};">
                🤖 Agent状态
            </h4>
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};">
                <strong>核心功能</strong>:
                <ul>
                    <li>24个Agent实时状态</li>
                    <li>6大军团分组展示</li>
                    <li>展开/折叠详情</li>
                    <li>快速启动/停止Agent</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
            box-shadow: {DesignTokens.Shadow.SM};
            border-left: 4px solid {DesignTokens.Colors.INFO};
        ">
            <h4 style="font-size: {DesignTokens.Typography.H4};
                       color: {DesignTokens.Colors.INFO};
                       margin-top: 0;
                       margin-bottom: {DesignTokens.Spacing.M_SM};">
                📋 任务管理
            </h4>
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};">
                <strong>核心功能</strong>:
                <ul>
                    <li>创建新分析任务</li>
                    <li>任务列表和筛选</li>
                    <li>进度条可视化</li>
                    <li>批量操作</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
            box-shadow: {DesignTokens.Shadow.SM};
            border-left: 4px solid {DesignTokens.Colors.WARNING};
        ">
            <h4 style="font-size: {DesignTokens.Typography.H4};
                       color: {DesignTokens.Colors.WARNING};
                       margin-top: 0;
                       margin-bottom: {DesignTokens.Spacing.M_SM};">
                📊 分析报告
            </h4>
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};">
                <strong>核心功能</strong>:
                <ul>
                    <li>6大军团综合分析</li>
                    <li>雷达图和趋势图</li>
                    <li>详细数据表格</li>
                    <li>导出PDF/Excel</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
            box-shadow: {DesignTokens.Shadow.SM};
            border-left: 4px solid {DesignTokens.Colors.ERROR};
        ">
            <h4 style="font-size: {DesignTokens.Typography.H4};
                       color: {DesignTokens.Colors.ERROR};
                       margin-top: 0;
                       margin-bottom: {DesignTokens.Spacing.M_SM};">
                ⚙️ 系统配置
            </h4>
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};">
                <strong>核心功能</strong>:
                <ul>
                    <li>API密钥配置</li>
                    <li>Agent参数设置</li>
                    <li>系统信息查看</li>
                    <li>配置导入/导出</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
            box-shadow: {DesignTokens.Shadow.SM};
            border-left: 4px solid {DesignTokens.Colors.ARMY_INDUSTRY};
        ">
            <h4 style="font-size: {DesignTokens.Typography.H4};
                       color: {DesignTokens.Colors.ARMY_INDUSTRY};
                       margin-top: 0;
                       margin-bottom: {DesignTokens.Spacing.M_SM};">
                📖 导航指南
            </h4>
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};">
                <strong>核心功能</strong>:
                <ul>
                    <li>快速入门教程</li>
                    <li>功能说明文档</li>
                    <li>常见问题解答</li>
                    <li>使用技巧分享</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==================== 常见问题 ====================

    st.markdown(f"""
    <h2 style="font-size: {DesignTokens.Typography.H2};
               color: {DesignTokens.Colors.TEXT_PRIMARY};
               margin-bottom: {DesignTokens.Spacing.M_MD};
               margin-top: {DesignTokens.Spacing.M_LG};">
        ❓ 常见问题
    </h2>
    """, unsafe_allow_html=True)

    # FAQ展开式
    with st.expander("❓ 如何获取Tushare API密钥？", expanded=False):
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
        ">
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};
                     line-height: 1.8;">
                <strong>步骤</strong>:
                <ol>
                    <li>访问 <a href="https://tushare.pro/register" target="_blank" style="color: {DesignTokens.Colors.PRIMARY};">Tushare官网</a> 注册账号</li>
                    <li>完成手机号验证和实名认证</li>
                    <li>前往"用户中心" → "接口TOKEN"</li>
                    <li>复制API Token并粘贴到系统配置页面</li>
                </ol>
                <strong>注意</strong>: 普通用户每日可获取120次API调用额度，足够个人使用。
            </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("❓ 为什么任务执行失败？", expanded=False):
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
        ">
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};
                     line-height: 1.8;">
                <strong>常见原因</strong>:
                <ul>
                    <li><strong>API密钥未配置或已过期</strong>: 前往系统配置页面检查API密钥</li>
                    <li><strong>股票代码格式错误</strong>: 请使用6位数字代码（例如：000001）</li>
                    <li><strong>网络连接问题</strong>: 检查网络连接和代理设置</li>
                    <li><strong>API额度不足</strong>: Tushare每日有调用次数限制</li>
                </ul>
                <strong>解决方法</strong>: 点击"🔄 重试"按钮重新执行任务。
            </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("❓ 如何导出分析报告？", expanded=False):
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
        ">
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};
                     line-height: 1.8;">
                <strong>导出功能</strong>（开发中）:
                <ul>
                    <li><strong>📄 导出PDF报告</strong>: 生成完整的PDF分析报告</li>
                    <li><strong>📊 导出Excel数据</strong>: 导出原始数据到Excel文件</li>
                    <li><strong>🔗 分享报告</strong>: 生成分享链接，发送给他人</li>
                </ul>
                <strong>临时方案</strong>: 可以使用浏览器的打印功能（Ctrl+P）保存为PDF。
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==================== 使用技巧 ====================

    st.markdown(f"""
    <h2 style="font-size: {DesignTokens.Typography.H2};
               color: {DesignTokens.Colors.TEXT_PRIMARY};
               margin-bottom: {DesignTokens.Spacing.M_MD};
               margin-top: {DesignTokens.Spacing.M_LG};">
        💎 使用技巧
    </h2>
    """, unsafe_allow_html=True)

    # 技巧卡片
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            box-shadow: {DesignTokens.Shadow.SM};
            text-align: center;
        ">
            <div style="font-size: 2.5rem;
                         margin-bottom: {DesignTokens.Spacing.M_SM};">⚡</div>
            <h4 style="font-size: {DesignTokens.Typography.H4};
                       color: {DesignTokens.Colors.TEXT_PRIMARY};
                       margin-top: 0;
                       margin-bottom: {DesignTokens.Spacing.M_SM};">
                快捷操作
            </h4>
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                使用"批量操作"功能，一次性启动多个任务，提高效率
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            box-shadow: {DesignTokens.Shadow.SM};
            text-align: center;
        ">
            <div style="font-size: 2.5rem;
                         margin-bottom: {DesignTokens.Spacing.M_SM};">🔍</div>
            <h4 style="font-size: {DesignTokens.Typography.H4};
                       color: {DesignTokens.Colors.TEXT_PRIMARY};
                       margin-top: 0;
                       margin-bottom: {DesignTokens.Spacing.M_SM};">
                筛选任务
            </h4>
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                使用状态和类型筛选器，快速找到目标任务
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            box-shadow: {DesignTokens.Shadow.SM};
            text-align: center;
        ">
            <div style="font-size: 2.5rem;
                         margin-bottom: {DesignTokens.Spacing.M_SM};">📊</div>
            <h4 style="font-size: {DesignTokens.Typography.H4};
                       color: {DesignTokens.Colors.TEXT_PRIMARY};
                       margin-top: 0;
                       margin-bottom: {DesignTokens.Spacing.M_SM};">
                数据可视化
            </h4>
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                查看雷达图和趋势图，直观了解分析结果
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==================== 版本信息 ====================

    st.markdown(f"""
    <div style="
        background: {rgba(DesignTokens.Colors.PRIMARY, 0.05)};
        border-radius: {DesignTokens.Radius.LG};
        padding: {DesignTokens.Spacing.P_LG};
        margin-top: {DesignTokens.Spacing.M_LG};
        text-align: center;
    ">
        <h3 style="font-size: {DesignTokens.Typography.H3};
                   color: {DesignTokens.Colors.TEXT_PRIMARY};
                   margin-top: 0;
                   margin-bottom: {DesignTokens.Spacing.M_SM};">
            🎖️ Agent Army v2.0
        </h3>
        <div style="font-size: {DesignTokens.Typography.BODY};
                 color: {DesignTokens.Colors.TEXT_SECONDARY};">
            24个Agent | 6大军团 | 让AI价值投资更智能、更透明、更高效<br>
            Powered by omc team | 2026-03-15
        </div>
    </div>
    """, unsafe_allow_html=True)


# 如果直接运行此文件
if __name__ == "__main__":
    render_navigation_guide_v3()
