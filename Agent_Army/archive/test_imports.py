"""
快速测试脚本 - 检查是否能正常启动
"""

import sys
from pathlib import Path

# 设置控制台编码为 UTF-8（Windows）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 60)
print("  Agent Army v2.0 - 快速测试")
print("=" * 60)
print()

# 添加当前目录到路径
current_dir = Path.cwd()
sys.path.insert(0, str(current_dir))

print(f"当前目录: {current_dir}")
print(f"Python 版本: {sys.version}")
print()

# 测试导入
print("-" * 60)
print("测试模块导入...")
print("-" * 60)

try:
    print("[1/5] 导入 streamlit...", end=" ")
    import streamlit as st
    print("[OK]")
except Exception as e:
    print(f"[FAILED]: {e}")
    input("\n按回车退出...")
    sys.exit(1)

try:
    print("[2/5] 导入 design_tokens...", end=" ")
    from src.core.design_tokens import DesignTokens
    print("[OK]")
except Exception as e:
    print(f"[FAILED]: {e}")
    input("\n按回车退出...")
    sys.exit(1)

try:
    print("[3/5] 导入 global_styles...", end=" ")
    from src.core.global_styles import apply_global_styles
    print("[OK]")
except Exception as e:
    print(f"[FAILED]: {e}")
    input("\n按回车退出...")
    sys.exit(1)

try:
    print("[4/5] 导入 ui_components...", end=" ")
    from src.core.ui_components import create_metric_card, get_status_badge
    print("[OK]")
except Exception as e:
    print(f"[FAILED]: {e}")
    input("\n按回车退出...")
    sys.exit(1)

try:
    print("[5/5] 导入 agent_status_v3...", end=" ")
    from src.core.pages_v2.agent_status_v3 import render_agent_status_v3
    print("[OK]")
except Exception as e:
    print(f"[FAILED]: {e}")
    input("\n按回车退出...")
    sys.exit(1)

print()
print("=" * 60)
print("  [SUCCESS] 所有模块导入成功")
print("=" * 60)
print()

# 测试 Design Tokens
print("测试 Design Tokens:")
print(f"  PRIMARY: {DesignTokens.Colors.PRIMARY}")
print(f"  ARMY_INDUSTRY: {DesignTokens.Colors.ARMY_INDUSTRY}")
print(f"  H1 字体: {DesignTokens.Typography.H1}")
print()

print("=" * 60)
print("  测试完成！所有检查通过。")
print("=" * 60)
print()
print("下一步:")
print("  1. 运行: streamlit run web_app_v2.py")
print("  2. 或双击: start_simple.bat")
print()

input("按回车退出...")
