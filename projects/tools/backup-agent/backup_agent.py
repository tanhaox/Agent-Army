#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backup Agent - 自动备份系统

功能：
- 实时监控对话内容，检测到改进意见文档创建时立即备份
- 每小时整点自动备份
- 简单回滚机制，支持按时间/关键词/ID 回滚
- 全自动运行，用户无感知

使用方法：
    # 启动后台服务
    python backup_agent.py --daemon

    # 查看备份清单
    python backup_agent.py --list

    # 回滚到指定备份
    python backup_agent.py --rollback 1

作者：Backup Agent
创建日期：2026-02-26
版本：v1.0.0
"""

import sys
import os
import argparse
import signal
from datetime import datetime

# 设置 Windows 控制台 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from config import Config
from git_manager import GitManager
from scheduler import Scheduler
from conversation_monitor import ConversationMonitor
from rollback_manager import RollbackManager
from logger import Logger
from backup_compressor import BackupCompressor
from tray_icon import TrayIcon


class BackupAgent:
    """备份 Agent 主程序"""

    def __init__(self):
        """初始化 Backup Agent"""
        # 加载配置
        print("📋 正在加载配置...")
        self.config_manager = Config()
        self.config = self.config_manager.get_config()

        # 初始化日志
        log_dir = os.path.join(current_dir, 'logs')
        self.logger = Logger(log_dir)
        self.logger.info("Backup Agent 正在启动...")

        # 初始化 Git 管理器
        print("🔧 正在初始化 Git 管理器...")
        monitor_path = self.config.get('monitor_path', current_dir)
        self.git_manager = GitManager(monitor_path, self.config)
        self.logger.info(f"监控路径: {monitor_path}")

        # 初始化各个模块
        self.scheduler = None
        self.monitor = None
        self.rollback_manager = RollbackManager(self.git_manager, self.config)
        self.compressor = BackupCompressor(monitor_path, self.config, self.logger)
        self.tray_icon = None

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """
        信号处理器

        Args:
            signum: 信号编号
            frame: 当前栈帧
        """
        print(f"\n🛑 收到退出信号，正在关闭...")
        self.stop()
        sys.exit(0)

    def start_daemon(self, enable_tray=False):
        """启动后台服务

        Args:
            enable_tray: 是否启用系统托盘
        """
        print("\n" + "=" * 60)
        print(" 🤖 Backup Agent 后台服务启动")
        print("=" * 60)

        # 启动定时任务（传递压缩器）
        self.scheduler = Scheduler(self.git_manager, self.config, self.logger, self.compressor)
        self.scheduler.start()
        self.logger.info("定时任务已启动")

        # 启动对话监控
        self.monitor = ConversationMonitor(self.git_manager, self.config, self.logger)
        self.monitor.start()
        self.logger.info("对话监控已启动")

        # 显示启动信息
        print(f"\n✅ Backup Agent 已启动！")
        print(f"📁 监控路径: {self.config.get('monitor_path')}")
        print(f"📝 监控目录: docs/improvements/")
        print(f"🕐 整点备份: 每小时")
        print(f"📦 压缩备份: {'启用' if self.compressor.enabled else '禁用'}")
        print(f"🖥️ 系统托盘: {'启用' if enable_tray else '禁用'}")
        print(f"📄 日志文件: {self.logger.get_log_path()}")
        print(f"\n💡 后台运行中，关闭此窗口不会影响服务")
        print("=" * 60 + "\n")

        # 运行监控循环
        try:
            import threading

            # 定时任务线程
            scheduler_thread = threading.Thread(target=self.scheduler.run, daemon=False)
            scheduler_thread.start()

            # 对话监控线程
            monitor_thread = threading.Thread(target=self.monitor.run, daemon=False)
            monitor_thread.start()

            # 如果启用托盘，等待托盘线程
            if enable_tray:
                self.tray_icon = TrayIcon(self, self.config, self.logger)
                tray_started = self.tray_icon.start()

                if not tray_started:
                    self.logger.error("系统托盘启动失败，程序将继续运行但无托盘图标")
                    print("⚠️  系统托盘启动失败，程序继续运行...")

                # 无论托盘是否成功启动，主线程都要保持运行
                if tray_started and self.tray_icon.running:
                    # 等待托盘线程
                    while self.tray_icon.running:
                        import time
                        time.sleep(1)
                    self.logger.info("托盘线程已结束")
                else:
                    # 托盘失败，简单保持运行
                    print("💡 程序正在后台运行（无托盘图标）")
                    while True:
                        import time
                        time.sleep(1)
            else:
                # 没有托盘，主线程等待工作线程
                while True:
                    import time
                    time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n🛑 正在停止服务...")
            self.stop()

    def stop(self):
        """停止后台服务"""
        self.logger.info("Backup Agent 正在关闭...")

        if self.scheduler:
            self.scheduler.stop()

        if self.monitor:
            self.monitor.stop()

        if self.tray_icon:
            self.tray_icon.stop()

        print("✅ Backup Agent 已关闭")
        self.logger.info("Backup Agent 已关闭")

    def list_backups(self, hours: int = 12):
        """
        列出备份清单

        Args:
            hours: 查询最近多少小时
        """
        self.rollback_manager.list_backups(hours)

    def rollback(self, target: str):
        """
        回滚到指定备份

        Args:
            target: 目标（ID/时间/关键词）
        """
        self.rollback_manager.rollback(target)

    def show_status(self):
        """显示当前状态"""
        status = self.git_manager.get_status()

        print(f"\n{'═' * 60}")
        print(f" 📊 Backup Agent 状态")
        print(f"{'═' * 60}")
        print(f" 📁 监控路径: {status['repo_path']}")
        print(f" 🌿 当前分支: {status['branch']}")
        print(f" 📝 是否有修改: {'是' if status['is_dirty'] else '否'}")
        print(f" 📄 未跟踪文件: {status['untracked_files']} 个")
        print(f" 💾 最新提交: {status['latest_commit']}")
        print(f"{'═' * 60}\n")

    def show_help(self):
        """显示帮助信息"""
        print(f"\n{'═' * 60}")
        print(f" 📖 Backup Agent 帮助")
        print(f"{'═' * 60}")
        print(f"\n🚀 启动服务")
        print(f"   命令：python backup_agent.py --daemon")
        print(f"   说明：启动后台备份服务")
        print(f"\n📋 查看备份清单")
        print(f"   命令：python backup_agent.py --list")
        print(f"   说明：显示最近 12 小时内的所有备份")
        print(f"\n📊 查看状态")
        print(f"   命令：python backup_agent.py --status")
        print(f"   说明：显示当前仓库状态")
        print(f"\n🔄 回滚操作")
        print(f"   命令：python backup_agent.py --rollback <目标>")
        print(f"   说明：回滚到指定备份")
        print(f"   例如：--rollback 1")
        print(f"        --rollback \"2026-02-26 14:35\"")
        print(f"        --rollback \"bug讨论前\"")
        print(f"\n📖 回滚帮助")
        print(f"   命令：python backup_agent.py --rollback-help")
        print(f"   说明：显示详细的回滚命令帮助")
        print(f"\n{'═' * 60}\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Backup Agent - 自动备份系统',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--daemon', action='store_true',
                        help='启动后台服务')
    parser.add_argument('--tray', action='store_true',
                        help='启用系统托盘（需配合 --daemon 使用）')
    parser.add_argument('--list', action='store_true',
                        help='查看备份清单')
    parser.add_argument('--rollback', metavar='TARGET',
                        help='回滚到指定备份')
    parser.add_argument('--rollback-help', action='store_true',
                        help='显示回滚帮助')
    parser.add_argument('--status', action='store_true',
                        help='显示当前状态')
    parser.add_argument('--hours', type=int, default=12,
                        help='查询最近多少小时的备份（默认12小时）')

    # GitHub远程仓库管理（新增）
    parser.add_argument('--github-push', action='store_true',
                        help='推送代码到GitHub远程仓库')
    parser.add_argument('--github-status', action='store_true',
                        help='显示GitHub远程仓库状态')
    parser.add_argument('--github-setup', metavar='URL',
                        help='设置GitHub远程仓库（URL格式：https://github.com/user/repo.git 或 git@github.com:user/repo.git）')
    parser.add_argument('--github-test', action='store_true',
                        help='测试GitHub连接')

    args = parser.parse_args()

    # 创建 Backup Agent 实例
    agent = BackupAgent()

    # 根据参数执行相应操作
    if args.daemon:
        # 启动后台服务
        agent.start_daemon(enable_tray=args.tray)

    elif args.list:
        # 查看备份清单
        agent.list_backups(args.hours)

    elif args.rollback:
        # 回滚操作
        agent.rollback(args.rollback)

    elif args.rollback_help:
        # 显示回滚帮助
        agent.rollback_manager.show_rollback_help()

    elif args.status:
        # 显示状态
        agent.show_status()

    elif args.github_push:
        # 推送到GitHub
        success, message = agent.git_manager.push_to_github()
        print(message)
        if not success:
            sys.exit(1)

    elif args.github_status:
        # 显示GitHub状态
        status = agent.git_manager.get_github_status()
        print(f"\n{'═' * 60}")
        print(f" 🌐 GitHub 远程仓库状态")
        print(f"{'═' * 60}")
        if status['has_remote']:
            print(f" ✅ 远程仓库: {status['remote_name']}")
            print(f" 📡 远程URL: {status['remote_url']}")
            print(f" 🌿 当前分支: {status['branch']}")
            if status['needs_push']:
                print(f" ⚠️  状态: 本地有未推送的提交")
                print(f" 📊 领先: {status['ahead_count']} 个提交")
                if status['behind_count'] > 0:
                    print(f" 📊 落后: {status['behind_count']} 个提交")
            else:
                print(f" ✅ 状态: 已同步")
                if status['behind_count'] > 0:
                    print(f" ⚠️  落后: {status['behind_count']} 个提交")
        else:
            print(f" ❌ 未配置远程仓库")
            print(f" 💡 使用 --github-setup <URL> 配置远程仓库")
        print(f"{'═' * 60}\n")

    elif args.github_setup:
        # 设置GitHub远程仓库
        success, message = agent.git_manager.setup_github_remote(args.github_setup)
        print(message)
        if not success:
            sys.exit(1)

    elif args.github_test:
        # 测试GitHub连接
        success, message = agent.git_manager.test_github_connection()
        print(message)
        if not success:
            sys.exit(1)

    else:
        # 显示帮助
        agent.show_help()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        from datetime import datetime
        error_msg = f"FATAL ERROR: {str(e)}\n{traceback.format_exc()}"
        print(error_msg, flush=True)
        # 尝试写入崩溃日志
        try:
            with open('C:\\AI-Agent-Local\\projects\\tools\\backup-agent\\logs\\crash.log', 'a') as f:
                f.write(f"\n[{datetime.now()}] {error_msg}\n")
        except:
            pass
