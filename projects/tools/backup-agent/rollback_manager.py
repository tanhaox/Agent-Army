#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回滚管理模块 - 负责回滚命令

功能：
- 显示备份清单
- 执行回滚操作
- 支持按时间/关键词/ID 回滚

作者：Backup Agent
创建日期：2026-02-26
"""

from datetime import datetime
from git_manager import GitManager
from typing import Optional


class RollbackManager:
    """回滚管理器"""

    def __init__(self, git_manager: GitManager, config: dict):
        """
        初始化回滚管理器

        Args:
            git_manager: Git 管理器实例
            config: 配置字典
        """
        self.git_manager = git_manager
        self.config = config

    def list_backups(self, hours: int = 12):
        """
        列出最近 N 小时的备份清单

        Args:
            hours: 查询最近多少小时
        """
        # 获取提交历史
        commits = self.git_manager.get_commit_history(hours)

        if not commits:
            print(f"\n❌ 最近 {hours} 小时内没有备份记录")
            return

        # 显示备份清单
        print(f"\n{'═' * 80}")
        print(f" 📋 最近 {hours} 小时备份清单")
        print(f"{'═' * 80}")
        print(f" {'ID':<4} {'时间':<20} {'Hash':<8} {'消息'}")
        print(f"{'─' * 80}")

        for commit in commits:
            # 截断过长的消息
            message = commit['message']
            if len(message) > 40:
                message = message[:40] + '...'

            print(f" {commit['id']:<4} {commit['time']:<20} {commit['hash']:<8} {message}")

        print(f"{'═' * 80}")
        print(f"💡 提示：使用 --rollback [ID|时间|关键词] 回滚到指定备份")
        print(f"   例如：--rollback 1")
        print(f"        --rollback \"2026-02-26 14:35\"")
        print(f"        --rollback \"bug讨论前\"")

    def rollback(self, target: str) -> bool:
        """
        回滚到指定备份

        Args:
            target: 目标（ID/时间/关键词）

        Returns:
            bool: 是否成功
        """
        print(f"\n🔄 正在回滚到: {target}")

        # 确认操作
        confirm = input("⚠️ 回滚会覆盖当前代码，是否继续？(yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("❌ 已取消回滚")
            return False

        # 执行回滚
        success = self.git_manager.rollback_to_commit(target)

        if success:
            print(f"✅ 回滚完成！")
            print(f"💡 提示：如需恢复，可以使用 --rollback \"回滚前安全备份\"")
        else:
            print(f"❌ 回滚失败")

        return success

    def show_rollback_help(self):
        """显示回滚帮助信息"""
        print(f"\n{'═' * 80}")
        print(f" 📖 回滚命令帮助")
        print(f"{'═' * 80}")
        print(f"\n1️⃣  查看备份清单")
        print(f"   命令：backup-agent --list")
        print(f"   说明：显示最近 12 小时内的所有备份记录")
        print(f"\n2️⃣  按时间回滚")
        print(f"   命令：backup-agent --rollback \"2026-02-26 14:35\"")
        print(f"   说明：回滚到指定时间的备份")
        print(f"\n3️⃣  按关键词回滚")
        print(f"   命令：backup-agent --rollback \"bug讨论前\"")
        print(f"   说明：回滚到包含指定关键词的备份")
        print(f"\n4️⃣  按 ID 回滚")
        print(f"   命令：backup-agent --rollback 1")
        print(f"   说明：回滚到指定 ID 的备份（ID 从清单中获取）")
        print(f"\n5️⃣  自定义查询范围")
        print(f"   命令：backup-agent --list --hours 24")
        print(f"   说明：查询最近 24 小时的备份（默认 12 小时）")
        print(f"\n{'═' * 80}")
