#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建桌面快捷方式
"""

import os
import sys
import subprocess

# 设置 Windows 控制台 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def create_desktop_shortcut():
    """创建桌面快捷方式"""

    # 获取桌面路径
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    # 当前脚本目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 批处理文件路径
    bat_file = os.path.join(current_dir, "启动 Backup Agent.bat")

    # 图标文件路径
    icon_file = r"C:\AI-Agent-Local\projects\tools\icon\32x32.ico"

    # 快捷方式路径
    shortcut_path = os.path.join(desktop_path, "Backup Agent.lnk")

    # 检查批处理文件是否存在
    if not os.path.exists(bat_file):
        print(f"❌ 找不到批处理文件: {bat_file}")
        return False

    # 检查图标文件是否存在
    if not os.path.exists(icon_file):
        print(f"❌ 找不到图标文件: {icon_file}")
        return False

    # PowerShell 脚本创建快捷方式
    powershell_script = f'''
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
    $Shortcut.TargetPath = "{bat_file}"
    $Shortcut.WorkingDirectory = "{current_dir}"
    $Shortcut.IconLocation = "{icon_file}"
    $Shortcut.Description = "Backup Agent - 自动备份系统"
    $Shortcut.Save()
    '''

    try:
        subprocess.run(
            ['powershell', '-Command', powershell_script],
            check=True,
            capture_output=True
        )
        print(f"✅ 桌面快捷方式创建成功！")
        print(f"📍 位置: {shortcut_path}")
        print(f"🎨 图标: {icon_file}")
        return True
    except Exception as e:
        print(f"❌ 创建快捷方式失败: {str(e)}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print(" 创建 Backup Agent 桌面快捷方式")
    print("=" * 60)

    success = create_desktop_shortcut()

    if success:
        print("\n✅ 完成！")
        print("\n💡 提示：")
        print("   - 桌面上会出现 'Backup Agent' 图标")
        print("   - 双击即可启动 Backup Agent")
        print("   - 图标与系统托盘图标一致")
    else:
        print("\n❌ 创建失败，请手动创建快捷方式")

    print("=" * 60)

    input("\n按回车键退出...")
