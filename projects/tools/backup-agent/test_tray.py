#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试系统托盘图标
"""

import sys
import os

# 设置 Windows 控制台 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    import pystray
    from PIL import Image

    def on_clicked(icon, item):
        print("托盘图标被点击了！")
        icon.stop()

    # 加载图标
    icon_path = r"C:\AI-Agent-Local\projects\tools\icon\32x32.ico"
    icon_image = Image.open(icon_path)

    # 创建托盘图标
    icon = pystray.Icon(
        "test_icon",
        icon_image,
        "测试托盘图标 - 如果看到这个说明工作正常！",
        pystray.MenuItem("退出", on_clicked)
    )

    print("=" * 60)
    print(" 托盘图标测试")
    print("=" * 60)
    print("\n✅ 托盘图标应该已经出现在系统托盘")
    print("🔍 请检查任务栏右下角（可能需要点击 ^ 图标查看隐藏图标）")
    print("\n💡 提示：")
    print("   - 鼠标悬停在图标上应该看到提示文字")
    print("   - 右键图标应该看到'退出'菜单")
    print("   - 或者按 Ctrl+C 停止此程序")
    print("\n" + "=" * 60)

    # 运行托盘图标
    icon.run()

except ImportError:
    print("❌ pystray 或 Pillow 未安装")
    print("   请运行: pip install pystray Pillow")
except Exception as e:
    print(f"❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()

input("\n按回车键退出...")
