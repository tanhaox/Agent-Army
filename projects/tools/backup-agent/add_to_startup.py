#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动添加到 Windows 启动项
"""

import os
import sys
import shutil

# 设置 Windows 控制台 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def add_to_startup():
    """添加 Backup Agent 到 Windows 启动项"""

    # 获取启动文件夹路径
    startup_folder = os.path.join(
        os.getenv('APPDATA'),
        r'Microsoft\Windows\Start Menu\Programs\Startup'
    )

    # 当前脚本目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 批处理文件路径
    bat_file = os.path.join(current_dir, 'start_backup_agent.bat')

    # 快捷方式路径
    shortcut_path = os.path.join(startup_folder, 'Backup Agent.lnk')

    # 检查批处理文件是否存在
    if not os.path.exists(bat_file):
        print(f"❌ 找不到批处理文件: {bat_file}")
        return False

    # 检查是否已经存在
    if os.path.exists(shortcut_path):
        print(f"⚠️ 启动项已存在: {shortcut_path}")
        return True

    # 使用 PowerShell 创建快捷方式
    import subprocess
    powershell_script = f'''
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
    $Shortcut.TargetPath = "{bat_file}"
    $Shortcut.WorkingDirectory = "{current_dir}"
    $Shortcut.Description = "Backup Agent - 自动备份系统"
    $Shortcut.Save()
    '''

    try:
        subprocess.run(
            ['powershell', '-Command', powershell_script],
            check=True,
            capture_output=True
        )
        print(f"✅ 已添加到启动项: {shortcut_path}")
        print(f"📁 启动文件夹: {startup_folder}")
        return True
    except Exception as e:
        print(f"❌ 添加启动项失败: {str(e)}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print(" 添加 Backup Agent 到 Windows 启动项")
    print("=" * 60)

    success = add_to_startup()

    if success:
        print("\n✅ Backup Agent 将在下次登录时自动启动")
        print("\n💡 提示：如果需要立即启动，请双击 start_backup_agent.bat")
    else:
        print("\n❌ 添加失败，请手动添加")

    print("=" * 60)

    input("\n按回车键退出...")
