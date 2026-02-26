#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建桌面快捷方式（指向 VBScript）
"""

import os
import sys

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
    current_dir = r"C:\AI-Agent-Local\projects\tools\backup-agent"

    # VBScript 文件路径
    vbs_file = os.path.join(current_dir, "启动-后台运行.vbs")

    # 图标文件路径
    icon_file = r"C:\AI-Agent-Local\projects\tools\icon\32x32.ico"

    # 快捷方式路径
    shortcut_path = os.path.join(desktop_path, "Backup Agent.lnk")

    # 检查文件是否存在
    if not os.path.exists(vbs_file):
        print(f"❌ 找不到文件: {vbs_file}")
        return False

    # PowerShell 脚本创建快捷方式
    powershell_script = f'''
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
    $Shortcut.TargetPath = "{vbs_file}"
    $Shortcut.WorkingDirectory = "{current_dir}"
    $Shortcut.IconLocation = "{icon_file}"
    $Shortcut.Description = "Backup Agent - 自动备份系统"
    $Shortcut.Save()
    '''

    try:
        import subprocess
        subprocess.run(
            ['powershell', '-Command', powershell_script],
            check=True,
            capture_output=True
        )
        print(f"✅ 桌面快捷方式创建成功！")
        print(f"📍 位置: {shortcut_path}")
        return True
    except Exception as e:
        print(f"❌ 创建快捷方式失败: {str(e)}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print(" 更新桌面快捷方式")
    print("=" * 60)

    success = create_desktop_shortcut()

    if success:
        print("\n✅ 完成！")
        print("\n💡 使用方法：")
        print("   1. 双击桌面的 'Backup Agent' 图标")
        print("   2. 静默启动，无窗口弹出")
        print("   3. 系统托盘出现图标")
    else:
        print("\n❌ 创建失败")

    print("=" * 60)

    input("\n按回车键退出...")
