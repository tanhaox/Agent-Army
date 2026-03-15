#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
板块成分股自动更新和备份脚本
定时任务：每月1号、15号 9:00 执行
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import shutil
from pathlib import Path
from datetime import datetime
import subprocess
import os

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "sector_constituents"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def backup_existing_files():
    """备份现有的CSV文件，格式：文件名.csv.backupYYYYMMDD"""
    backup_date = datetime.now().strftime('%Y%m%d')
    backup_count = 0

    for csv_file in OUTPUT_DIR.glob("*_latest.csv"):
        # 跳过今日已备份的文件
        backup_name = f"{csv_file.stem}.backup{backup_date}{csv_file.suffix}"
        backup_path = OUTPUT_DIR / backup_name

        if backup_path.exists():
            continue

        # 复制文件
        shutil.copy2(csv_file, backup_path)
        print(f"  ✓ 备份: {csv_file.name} -> {backup_name}")
        backup_count += 1

    if backup_count == 0:
        print(f"  ℹ 今日已备份或无文件")
    else:
        print(f"  ✓ 共备份 {backup_count} 个文件")

    return backup_count

def update_static_data():
    """更新静态板块数据"""
    print("  更新板块成分股数据...")

    # 运行静态数据生成脚本
    script_path = Path(__file__).parent / "create_static_sectors.py"

    if not script_path.exists():
        print(f"  ✗ 脚本不存在: {script_path}")
        return False

    try:
        result = subprocess.run(
            ['python', str(script_path)],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print("  ✓ 数据更新成功")
            return True
        else:
            print(f"  ✗ 更新失败: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ✗ 更新异常: {e}")
        return False

def cleanup_old_backups(keep_days=180):
    """清理旧备份文件（保留180天）"""
    print(f"  清理超过 {keep_days} 天的备份...")

    cutoff_date = datetime.now().timestamp() - (keep_days * 86400)
    deleted_count = 0

    for backup_file in OUTPUT_DIR.glob("*.backup*"):
        if backup_file.stat().st_mtime < cutoff_date:
            backup_file.unlink()
            deleted_count += 1

    if deleted_count > 0:
        print(f"  ✓ 删除了 {deleted_count} 个过期备份")
    else:
        print(f"  ℹ 无需清理的备份")

def send_notification(message, success=True):
    """发送通知（可选）"""
    status = "✓" if success else "✗"
    print(f"\n{status} {message}")

    # TODO: 添加邮件、微信等通知方式
    # send_email(message)
    # send_wechat(message)

def main():
    """主函数"""
    print()
    print("=" * 70)
    print("  板块成分股自动更新")
    print("=" * 70)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 步骤1：备份现有文件
    print("[步骤 1] 备份现有文件...")
    backup_count = backup_existing_files()
    print()

    # 步骤2：更新数据
    print("[步骤 2] 更新板块数据...")
    update_success = update_static_data()
    print()

    # 步骤3：清理旧备份
    print("[步骤 3] 清理旧备份...")
    cleanup_old_backups()
    print()

    # 步骤4：发送通知
    if update_success:
        send_notification("板块成分股数据更新成功", success=True)
    else:
        send_notification("板块成分股数据更新失败", success=False)

    print("=" * 70)
    print("  完成")
    print("=" * 70)
    print()

if __name__ == '__main__':
    main()
