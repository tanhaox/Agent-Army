#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装板块成分股自动更新定时任务
Cron表达式：每月1号、15号 9:00 执行
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.absolute()
UPDATE_SCRIPT = SCRIPT_DIR / "auto_update_sectors.py"

def install_crontab():
    """安装crontab定时任务"""
    print("=" * 70)
    print("  安装板块成分股自动更新定时任务")
    print("=" * 70)
    print()

    # 检查更新脚本是否存在
    if not UPDATE_SCRIPT.exists():
        print(f"✗ 更新脚本不存在: {UPDATE_SCRIPT}")
        return False

    # 定时任务配置
    # 每月1号、15号 9:00 执行
    cron_schedule = "0 9 1,15 * *"
    cron_command = f"cd {SCRIPT_DIR} && /usr/bin/python3 {UPDATE_SCRIPT} >> {SCRIPT_DIR}/auto_update.log 2>&1"

    print(f"定时任务配置:")
    print(f"  执行时间: 每月1号、15号 9:00")
    print(f"  执行命令: {cron_command}")
    print()

    # 获取当前crontab
    try:
        result = subprocess.run(
            ['crontab', '-l'],
            capture_output=True,
            text=True
        )
        current_cron = result.stdout if result.returncode == 0 else ""
    except Exception as e:
        current_cron = ""

    # 检查是否已存在相同的任务
    if 'auto_update_sectors.py' in current_cron:
        print("⚠ 检测到已存在板块成分股更新任务")
        print()
        choice = input("是否覆盖？(y/n): ").strip().lower()
        if choice != 'y':
            print("✗ 取消安装")
            return False

        # 删除旧任务
        lines = current_cron.split('\n')
        lines = [line for line in lines if 'auto_update_sectors.py' not in line]
        current_cron = '\n'.join(lines)

    # 添加新任务
    new_cron_entry = f"{cron_schedule} {cron_command}  # 板块成分股自动更新"
    new_cron = current_cron.rstrip('\n') + '\n' + new_cron_entry + '\n'

    # 写入临时文件
    temp_cron_file = Path('/tmp/crontab_temp')
    with open(temp_cron_file, 'w') as f:
        f.write(new_cron)

    # 安装新的crontab
    try:
        subprocess.run(['crontab', str(temp_cron_file)], check=True)
        print("✓ 定时任务安装成功!")
        print()
        print("当前定时任务列表:")
        print("-" * 70)
        subprocess.run(['crontab', '-l'])
        print("-" * 70)
        print()
        print("说明:")
        print("  - 任务将在每月1号、15号 9:00 自动执行")
        print("  - 日志文件: {}/auto_update.log".format(SCRIPT_DIR))
        print("  - 可以使用 'crontab -l' 查看所有定时任务")
        print("  - 可以使用 'crontab -r' 删除所有定时任务（谨慎使用）")
        print()

        # 清理临时文件
        temp_cron_file.unlink()

        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ 安装失败: {e}")
        temp_cron_file.unlink()
        return False

def uninstall_crontab():
    """卸载定时任务"""
    print("=" * 70)
    print("  卸载板块成分股自动更新定时任务")
    print("=" * 70)
    print()

    # 获取当前crontab
    try:
        result = subprocess.run(
            ['crontab', '-l'],
            capture_output=True,
            text=True
        )
        current_cron = result.stdout if result.returncode == 0 else ""
    except Exception as e:
        print(f"✗ 获取crontab失败: {e}")
        return False

    if 'auto_update_sectors.py' not in current_cron:
        print("ℹ 未找到板块成分股更新任务")
        return True

    # 删除相关任务
    lines = current_cron.split('\n')
    lines = [line for line in lines if 'auto_update_sectors.py' not in line]
    new_cron = '\n'.join(lines)

    # 写入临时文件
    temp_cron_file = Path('/tmp/crontab_temp')
    with open(temp_cron_file, 'w') as f:
        f.write(new_cron)

    # 安装新的crontab
    try:
        subprocess.run(['crontab', str(temp_cron_file)], check=True)
        print("✓ 定时任务已卸载")
        temp_cron_file.unlink()
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 卸载失败: {e}")
        temp_cron_file.unlink()
        return False

def test_run():
    """测试运行"""
    print("=" * 70)
    print("  测试运行板块成分股更新")
    print("=" * 70)
    print()

    try:
        subprocess.run(['python3', str(UPDATE_SCRIPT)], check=True)
        print("✓ 测试运行成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 测试运行失败: {e}")
        return False

def main():
    """主函数"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'install':
            install_crontab()
        elif command == 'uninstall':
            uninstall_crontab()
        elif command == 'test':
            test_run()
        elif command == 'status':
            # 查看定时任务状态
            print("当前定时任务:")
            print("-" * 70)
            subprocess.run(['crontab', '-l'])
            print("-" * 70)
        else:
            print(f"未知命令: {command}")
            print("可用命令: install, uninstall, test, status")
    else:
        # 默认：安装
        install_crontab()

if __name__ == '__main__':
    main()
