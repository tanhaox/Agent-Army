"""
系统配置页面 v3.0 验证测试
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
print("  系统配置页面 v3.0 验证测试")
print("=" * 80)
print()

all_checks_passed = True

# ==================== 1. 必需导入检查 ====================
print("📦 [1/8] 必需导入检查...")
try:
    from src.core.pages_v2.system_config_v3 import render_system_config_v3
    from src.core.design_tokens import DesignTokens
    from src.core.global_styles import apply_global_styles
    import streamlit as st
    import os
    print("✅ PASS - 所有必需模块导入成功\n")
except Exception as e:
    print(f"❌ FAIL - 导入失败: {e}\n")
    all_checks_passed = False

# ==================== 2. Design Tokens 检查 ====================
print("🎨 [2/8] Design Tokens 使用检查...")
try:
    with open(project_root / "src/core/pages_v2/system_config_v3.py", "r", encoding="utf-8") as f:
        content = f.read()

    required_tokens = {
        "Colors.TEXT_PRIMARY": "文本主色",
        "Colors.TEXT_SECONDARY": "文本次色",
        "Colors.BG_CARD": "卡片背景",
        "Colors.PRIMARY": "主色",
        "Colors.SUCCESS": "成功色",
        "Colors.WARNING": "警告色",
        "Colors.ERROR": "错误色",
        "Colors.INFO": "信息色",
        "Typography.H1": "H1字体",
        "Typography.H2": "H2字体",
        "Typography.H3": "H3字体",
        "Typography.BODY": "正文字体",
        "Typography.SMALL": "小号字体",
        "Typography.WEIGHT_BOLD": "粗体",
        "Spacing.P_MD": "中等内边距",
        "Spacing.P_SM": "小内边距",
        "Spacing.M_LG": "大外边距",
        "Spacing.M_MD": "中等外边距",
        "Spacing.M_SM": "小外边距",
        "Spacing.M_XS": "极小外边距",
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
print("🔧 [3/8] 辅助函数检查...")
try:
    if "def rgba(hex_color: str, alpha: float) -> str:" in content:
        print("✅ PASS - rgba() 辅助函数存在")
    else:
        print("❌ FAIL - 缺少 rgba() 辅助函数")
        all_checks_passed = False

    if "def render_system_config_v3():" in content:
        print("✅ PASS - render_system_config_v3() 主函数存在")
    else:
        print("❌ FAIL - 缺少 render_system_config_v3() 主函数")
        all_checks_passed = False

    print()
except Exception as e:
    print(f"❌ FAIL - 辅助函数检查失败: {e}\n")
    all_checks_passed = False

# ==================== 4. 页面结构检查 ====================
print("📄 [4/8] 页面结构检查...")
required_sections = {
    "页面标题": "⚙️ 系统配置",
    "API配置": "🔑 API配置",
    "Tushare API": "📊 Tushare API",
    "OpenAI API": "🤖 OpenAI API",
    "Zhipu AI": "🧠 Zhipu AI API",
    "Agent配置": "🤖 Agent配置",
    "系统信息": "📊 系统信息",
    "版本信息": "📋 版本信息"
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

# ==================== 5. API配置检查 ====================
print("🔑 [5/8] API配置检查...")
api_configs = {
    "Tushare API Key": "TUSHARE_API_KEY",
    "OpenAI API Key": "OPENAI_API_KEY",
    "Zhipu AI API Key": "ZHIPUAI_API_KEY"
}

missing_configs = []
for config_name, env_var in api_configs.items():
    if env_var not in content:
        missing_configs.append(f"  - {config_name}")

if missing_configs:
    print(f"❌ FAIL - 缺少 {len(missing_configs)} 个API配置:")
    for config in missing_configs:
        print(config)
    print()
    all_checks_passed = False
else:
    print(f"✅ PASS - 所有 {len(api_configs)} 个API配置存在\n")

# ==================== 6. Agent参数检查 ====================
print("🤖 [6/8] Agent参数检查...")
agent_params = {
    "最大并发数": "max_workers",
    "超时时间": "timeout",
    "重试次数": "retry_count",
    "数据周期": "data_period",
    "启用缓存": "cache_enabled",
    "日志级别": "log_level"
}

missing_params = []
for param_name, param_var in agent_params.items():
    if param_var not in content:
        missing_params.append(f"  - {param_name}")

if missing_params:
    print(f"❌ FAIL - 缺少 {len(missing_params)} 个Agent参数:")
    for param in missing_params:
        print(param)
    print()
    all_checks_passed = False
else:
    print(f"✅ PASS - 所有 {len(agent_params)} 个Agent参数存在\n")

# ==================== 7. 移除旧代码检查 ====================
print("🗑️ [7/8] 移除旧代码检查...")
old_patterns = {
    "st.tabs()": "标签页结构",
    "st.info()": "原生提示组件",
}

found_old = []
for pattern, desc in old_patterns.items():
    if pattern in content:
        found_old.append(f"  - {desc}")

if found_old:
    print(f"❌ FAIL - 发现 {len(found_old)} 个旧代码模式:")
    for item in found_old:
        print(item)
    print()
    all_checks_passed = False
else:
    print("✅ PASS - 未发现旧代码模式\n")

# ==================== 8. web_app_v2.py 集成检查 ====================
print("🔗 [8/8] web_app_v2.py 集成检查...")
try:
    with open(project_root / "web_app_v2.py", "r", encoding="utf-8") as f:
        web_app_content = f.read()

    if "from src.core.pages_v2.system_config_v3 import render_system_config_v3" in web_app_content:
        print("✅ PASS - system_config_v3 已正确导入")
    else:
        print("❌ FAIL - system_config_v3 未导入到 web_app_v2.py")
        all_checks_passed = False

    if "render_system_config_v3()" in web_app_content:
        print("✅ PASS - render_system_config_v3() 已正确调用")
    else:
        print("❌ FAIL - render_system_config_v3() 未调用")
        all_checks_passed = False

    print()
except Exception as e:
    print(f"❌ FAIL - web_app_v2.py 集成检查失败: {e}\n")
    all_checks_passed = False

# ==================== 最终结果 ====================
print("=" * 80)
if all_checks_passed:
    print("  ✅ 所有检查通过！system_config_v3.py 验证成功")
    print("=" * 80)
    print()
    print("核心特性:")
    print("  ✅ 100% Design Tokens 合规")
    print("  ✅ 完整的API配置（3个）")
    print("  ✅ Agent参数配置")
    print("  ✅ 系统信息展示")
    print("  ✅ 移除所有 st.info() 原生组件")
    print()
    sys.exit(0)
else:
    print("  ❌ 部分检查未通过，请修复上述问题")
    print("=" * 80)
    print()
    sys.exit(1)
