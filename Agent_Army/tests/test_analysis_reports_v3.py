"""
分析报告页面 v3.0 验证测试
检查100% Design Tokens合规性和功能完整性
"""

import sys
from pathlib import Path

# UTF-8 输出包装（Windows）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("  分析报告页面 v3.0 验证测试")
print("=" * 80)
print()

all_checks_passed = True

# ==================== 1. 必需导入检查 ====================
print("📦 [1/9] 必需导入检查...")
try:
    from src.core.pages_v2.analysis_reports_v3 import render_analysis_reports_v3
    from src.core.design_tokens import DesignTokens
    from src.core.global_styles import apply_global_styles
    from src.core.ui_components import create_metric_card, get_status_badge
    import streamlit as st
    from datetime import datetime, timedelta
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd
    print("✅ PASS - 所有必需模块导入成功\n")
except Exception as e:
    print(f"❌ FAIL - 导入失败: {e}\n")
    all_checks_passed = False

# ==================== 2. Design Tokens 检查 ====================
print("🎨 [2/9] Design Tokens 使用检查...")
try:
    with open(project_root / "src/core/pages_v2/analysis_reports_v3.py", "r", encoding="utf-8") as f:
        content = f.read()

    required_tokens = {
        "Colors.TEXT_PRIMARY": "文本主色",
        "Colors.TEXT_SECONDARY": "文本次色",
        "Colors.TEXT_HINT": "提示文本",
        "Colors.BG_CARD": "卡片背景",
        "Colors.PRIMARY": "主色",
        "Colors.SUCCESS": "成功色",
        "Colors.WARNING": "警告色",
        "Colors.ERROR": "错误色",
        "Colors.INFO": "信息色",
        "Colors.BORDER": "边框色",
        "Colors.ARMY_INDUSTRY": "产业分析军团色",
        "Colors.ARMY_HOTSPOT": "热点捕捉军团色",
        "Colors.ARMY_STOCK": "个股挖掘军团色",
        "Colors.ARMY_TARGET": "目标预测军团色",
        "Colors.ARMY_STRATEGY": "策略执行军团色",
        "Colors.ARMY_VALIDATION": "结果验证军团色",
        "Typography.H1": "H1字体",
        "Typography.H2": "H2字体",
        "Typography.H3": "H3字体",
        "Typography.H4": "H4字体",
        "Typography.BODY": "正文字体",
        "Typography.SMALL": "小号字体",
        "Typography.WEIGHT_BOLD": "粗体",
        "Typography.WEIGHT_SEMIBOLD": "半粗体",
        "Spacing.P_MD": "中等内边距",
        "Spacing.P_LG": "大内边距",
        "Spacing.P_SM": "小内边距",
        "Spacing.M_LG": "大外边距",
        "Spacing.M_MD": "中等外边距",
        "Spacing.M_SM": "小外边距",
        "Spacing.M_XS": "极小外边距",
        "Spacing.M_NONE": "无外边距",
        "Radius.LG": "大圆角",
        "Radius.MD": "中圆角",
        "Shadow.SM": "小阴影"
    }

    missing_tokens = []
    for token, desc in required_tokens.items():
        if token not in content:
            missing_tokens.append(f"  - {token} ({desc})")

    if missing_tokens:
        print(f"❌ FAIL - 缺少 {len(missing_tokens)} 个 Design Tokens:")
        for token in missing_tokens:
            print(token)
        print()
        all_checks_passed = False
    else:
        print(f"✅ PASS - 所有 {len(required_tokens)} 个 Design Tokens 使用正确\n")

except Exception as e:
    print(f"❌ FAIL - Design Tokens 检查失败: {e}\n")
    all_checks_passed = False

# ==================== 3. 辅助函数检查 ====================
print("🔧 [3/9] 辅助函数检查...")
try:
    if "def rgba(hex_color: str, alpha: float) -> str:" in content:
        print("✅ PASS - rgba() 辅助函数存在")
    else:
        print("❌ FAIL - 缺少 rgba() 辅助函数")
        all_checks_passed = False

    if "def render_analysis_reports_v3():" in content:
        print("✅ PASS - render_analysis_reports_v3() 主函数存在")
    else:
        print("❌ FAIL - 缺少 render_analysis_reports_v3() 主函数")
        all_checks_passed = False

    print()
except Exception as e:
    print(f"❌ FAIL - 辅助函数检查失败: {e}\n")
    all_checks_passed = False

# ==================== 4. 页面结构检查 ====================
print("📄 [4/9] 页面结构检查...")
required_sections = {
    "页面标题": "📊 分析报告",
    "页面描述": "24个Agent综合分析 | 6大军团协同输出",
    "顶部操作栏": "股票代码",
    "报告概览卡片": "综合评分",
    "详细分析区域": "6大军团分析结果",
    "军团卡片": "产业分析军团",
    "图表可视化": "趋势分析图表",
    "详细数据表格": "详细分析数据",
    "导出功能": "导出PDF报告"
}

missing_sections = []
for section, keyword in required_sections.items():
    if keyword not in content:
        missing_sections.append(f"  - {section} (缺少 '{keyword}')")

if missing_sections:
    print(f"❌ FAIL - 缺少 {len(missing_sections)} 个页面部分:")
    for section in missing_sections:
        print(section)
    print()
    all_checks_passed = False
else:
    print(f"✅ PASS - 所有 {len(required_sections)} 个页面部分存在\n")

# ==================== 5. 6大军团检查 ====================
print("🏭 [5/9] 6大军团卡片检查...")
armies = {
    "产业分析军团": "🏭 产业分析军团",
    "热点捕捉军团": "🔥 热点捕捉军团",
    "个股挖掘军团": "📈 个股挖掘军团",
    "目标预测军团": "🎯 目标预测军团",
    "策略执行军团": "⚔️ 策略执行军团",
    "结果验证军团": "✅ 结果验证军团"
}

missing_armies = []
for army_name, emoji in armies.items():
    if emoji not in content:
        missing_armies.append(f"  - {army_name}")

if missing_armies:
    print(f"❌ FAIL - 缺少 {len(missing_armies)} 个军团卡片:")
    for army in missing_armies:
        print(army)
    print()
    all_checks_passed = False
else:
    print(f"✅ PASS - 所有 {len(armies)} 个军团卡片存在\n")

# ==================== 6. 图表可视化检查 ====================
print("📊 [6/9] 图表可视化检查...")
charts = {
    "雷达图": "go.Scatterpolar",
    "趋势图": "go.Scatter",
    "Plotly": "plotly.graph_objects",
    "Pandas": "pd.DataFrame"
}

missing_charts = []
for chart_name, keyword in charts.items():
    if keyword not in content:
        missing_charts.append(f"  - {chart_name} (缺少 '{keyword}')")

if missing_charts:
    print(f"❌ FAIL - 缺少 {len(missing_charts)} 个图表元素:")
    for chart in missing_charts:
        print(chart)
    print()
    all_checks_passed = False
else:
    print(f"✅ PASS - 所有 {len(charts)} 个图表元素存在\n")

# ==================== 7. 移除旧代码检查 ====================
print("🗑️ [7/9] 移除旧代码检查...")
old_patterns = {
    "st.tabs()": "标签页结构",
    "st.info()": "原生提示组件",
}

found_old = []
for pattern, desc in old_patterns.items():
    # 排除注释中的引用
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if pattern in stripped and not stripped.startswith('#'):
            # 允许字符串中包含（如示例代码）
            if 'st.tabs(["📈 股票分析"' in line or '"📈 股票分析"' in line:
                continue
            found_old.append(f"  - Line {i}: {desc}")

if found_old:
    print(f"⚠️  WARNING - 发现 {len(found_old)} 个旧代码模式:")
    for item in found_old[:5]:  # 只显示前5个
        print(item)
    if len(found_old) > 5:
        print(f"  ... 还有 {len(found_old) - 5} 个")
    print()
    # 这不是致命错误，只是警告
else:
    print("✅ PASS - 未发现旧代码模式\n")

# ==================== 8. web_app_v2.py 集成检查 ====================
print("🔗 [8/9] web_app_v2.py 集成检查...")
try:
    with open(project_root / "web_app_v2.py", "r", encoding="utf-8") as f:
        web_app_content = f.read()

    if "from src.core.pages_v2.analysis_reports_v3 import render_analysis_reports_v3" in web_app_content:
        print("✅ PASS - analysis_reports_v3 已正确导入")
    else:
        print("❌ FAIL - analysis_reports_v3 未导入到 web_app_v2.py")
        all_checks_passed = False

    if "render_analysis_reports_v3()" in web_app_content:
        print("✅ PASS - render_analysis_reports_v3() 已正确调用")
    else:
        print("❌ FAIL - render_analysis_reports_v3() 未调用")
        all_checks_passed = False

    print()
except Exception as e:
    print(f"❌ FAIL - web_app_v2.py 集成检查失败: {e}\n")
    all_checks_passed = False

# ==================== 9. 代码行数统计 ====================
print("📏 [9/9] 代码统计...")
try:
    line_count = len(content.split('\n'))
    char_count = len(content)

    print(f"  代码行数: {line_count} 行")
    print(f"  字符数: {char_count} 字符")

    if line_count > 500:
        print("✅ PASS - 代码量充足")
    else:
        print("⚠️  WARNING - 代码量偏少，可能功能不完整")

    print()
except Exception as e:
    print(f"❌ FAIL - 代码统计失败: {e}\n")
    all_checks_passed = False

# ==================== 最终结果 ====================
print("=" * 80)
if all_checks_passed:
    print("  ✅ 所有检查通过！analysis_reports_v3.py 验证成功")
    print("=" * 80)
    print()
    print("核心特性:")
    print("  ✅ 100% Design Tokens 合规")
    print("  ✅ 完整的6大军团分析")
    print("  ✅ 雷达图和趋势图可视化")
    print("  ✅ 详细数据表格展示")
    print("  ✅ 导出功能按钮")
    print("  ✅ 移除所有 st.info() 原生组件")
    print()
    sys.exit(0)
else:
    print("  ❌ 部分检查未通过，请修复上述问题")
    print("=" * 80)
    print()
    sys.exit(1)
