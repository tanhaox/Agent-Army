#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统托盘模块 - 负责系统托盘图标和菜单

功能：
- 创建系统托盘图标
- 右键菜单功能
- 状态提示

作者：Backup Agent
创建日期：2026-02-26
"""

import os
import sys
import subprocess
import threading
from datetime import datetime

try:
    import pystray
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


class TrayIcon:
    """系统托盘图标"""

    def __init__(self, backup_agent, config: dict, logger=None):
        """
        初始化系统托盘图标

        Args:
            backup_agent: BackupAgent 实例
            config: 配置字典
            logger: 日志记录器（可选）
        """
        self.backup_agent = backup_agent
        self.config = config
        self.logger = logger
        self.icon = None
        self.running = False

        # 托盘配置
        tray_config = config.get('tray_icon', {})
        self.icon_path = tray_config.get('icon_path', 'C:\\AI-Agent-Local\\projects\\tools\\icon\\32x32.ico')

        # 加载图标
        self._load_icon()

    def _load_icon(self):
        """加载图标"""
        if not TRAY_AVAILABLE:
            print("⚠️ pystray 未安装，系统托盘功能不可用")
            print("   请运行: pip install pystray Pillow")
            return

        try:
            # 加载 ICO 文件
            self.icon_image = Image.open(self.icon_path)
            if self.logger:
                self.logger.info(f"加载托盘图标: {self.icon_path}")
        except Exception as e:
            print(f"⚠️ 加载图标失败: {str(e)}")
            self.icon_image = None

    def _show_status(self, icon=None, item=None):
        """显示状态"""
        status = self.backup_agent.git_manager.get_status()

        status_text = f"""📊 Backup Agent 状态

📁 监控路径: {status['repo_path']}
🌿 当前分支: {status['branch']}
📝 是否有修改: {'是' if status['is_dirty'] else '否'}
📄 未跟踪文件: {status['untracked_files']} 个
💾 最新提交: {status['latest_commit'] or '无'}"""

        # 使用 tkinter 显示消息框
        self._show_message_box("Backup Agent 状态", status_text)

    def _show_backups(self, icon=None, item=None):
        """显示备份清单"""
        commits = self.backup_agent.git_manager.get_commit_history(hours=12)

        if not commits:
            backup_text = "❌ 最近 12 小时内没有备份记录"
        else:
            lines = ["📋 最近 12 小时备份清单", "=" * 60]
            for commit in commits:
                lines.append(f"ID {commit['id']} | {commit['time']} | {commit['message'][:40]}")
            backup_text = "\n".join(lines)

        # 使用 tkinter 显示消息框
        self._show_message_box("备份清单", backup_text)

    def _show_message_box(self, title, message):
        """
        显示消息框（线程安全）

        Args:
            title: 标题
            message: 消息内容
        """
        import threading

        def show_box():
            try:
                import tkinter as tk
                from tkinter import messagebox

                # 创建隐藏的主窗口
                root = tk.Tk()
                root.withdraw()  # 隐藏主窗口
                root.attributes('-topmost', True)  # 置顶

                # 显示消息框
                messagebox.showinfo(title, message)

                # 销毁窗口
                root.destroy()
            except Exception as e:
                # 如果 tkinter 失败，使用控制台输出
                print(f"\n{title}")
                print("=" * 60)
                print(message)
                print("=" * 60)

        # 在新线程中显示消息框（避免阻塞托盘线程）
        thread = threading.Thread(target=show_box, daemon=True)
        thread.start()

    def _open_logs_dir(self, icon=None, item=None):
        """打开日志目录"""
        logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
        if os.path.exists(logs_dir):
            os.startfile(logs_dir)
        else:
            print(f"❌ 日志目录不存在: {logs_dir}")

    def _open_backups_dir(self, icon=None, item=None):
        """打开压缩包目录"""
        backups_dir = os.path.join(os.path.dirname(__file__), 'backups')
        if os.path.exists(backups_dir):
            os.startfile(backups_dir)
        else:
            print(f"❌ 压缩包目录不存在: {backups_dir}")

    def _manual_backup(self, icon=None, item=None):
        """手动触发备份"""
        try:
            # 执行备份
            commit_id = self.backup_agent.git_manager.backup("手动触发备份")

            # 触发压缩（如果启用）
            if self.backup_agent.compressor:
                self.backup_agent.compressor.create_backup()

            # 显示成功消息
            message = f"✅ 备份成功！\n\nCommit ID: {commit_id[:8]}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self._show_message_box("备份成功", message)

            if self.logger:
                self.logger.info(f"手动备份成功: {commit_id}")
        except Exception as e:
            # 显示失败消息
            message = f"❌ 备份失败！\n\n错误: {str(e)}"
            self._show_message_box("备份失败", message)

            if self.logger:
                self.logger.error(f"手动备份失败: {str(e)}")

    def _toggle_service(self, icon=None, item=None):
        """切换服务状态"""
        if self.backup_agent.scheduler and self.backup_agent.scheduler.running:
            self.backup_agent.stop()
            self.update_tooltip("Backup Agent - 已停止")
        else:
            # 重新启动服务
            self.backup_agent.start_daemon()
            self.update_tooltip("Backup Agent - 运行中")

    def _exit_app(self, icon=None, item=None):
        """退出应用"""
        self.backup_agent.stop()
        if self.icon:
            self.icon.stop()

    def update_tooltip(self, text: str):
        """更新托盘图标提示"""
        if self.icon:
            self.icon.title = text

    def start(self):
        """启动托盘图标"""
        if not TRAY_AVAILABLE or not self.icon_image:
            if self.logger:
                self.logger.error("pystray 不可用或图标加载失败")
            return False

        if self.running:
            if self.logger:
                self.logger.warning("托盘已经在运行")
            return False

        try:
            if self.logger:
                self.logger.info("正在创建托盘菜单...")

            # 创建菜单项列表
            menu_items = [
                pystray.MenuItem("查看状态", self._show_status),
                pystray.MenuItem("查看备份清单", self._show_backups),
                pystray.MenuItem("立即备份", self._manual_backup),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("打开日志目录", self._open_logs_dir),
                pystray.MenuItem("打开压缩包目录", self._open_backups_dir),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("停止服务", self._toggle_service),
                pystray.MenuItem("退出", self._exit_app)
            ]

            if self.logger:
                self.logger.info("正在创建托盘图标对象...")

            # 创建托盘图标
            self.icon = pystray.Icon(
                "backup_agent",
                self.icon_image,
                "Backup Agent - 启动中",
                pystray.Menu(*menu_items)
            )

            self.running = True

            if self.logger:
                self.logger.info("正在启动托盘线程...")

            # 在新线程中运行托盘（非 daemon，确保程序持续运行）
            icon_thread = threading.Thread(target=self._run_icon, daemon=False)
            icon_thread.start()

            if self.logger:
                self.logger.info(f"系统托盘已启动（running={self.running}）")

            return True

        except Exception as e:
            print(f"❌ 启动系统托盘失败: {str(e)}")
            if self.logger:
                self.logger.error(f"启动系统托盘失败: {str(e)}", exc_info=True)
            return False

    def _run_icon(self):
        """在独立线程中运行托盘图标"""
        try:
            if self.logger:
                self.logger.info("托盘图标线程开始运行")
            self.icon.run()
            if self.logger:
                self.logger.info("托盘图标线程已退出")
        except Exception as e:
            if self.logger:
                self.logger.error(f"托盘图标线程异常: {str(e)}", exc_info=True)
            print(f"❌ 托盘图标线程异常: {str(e)}")
        finally:
            self.running = False

    def stop(self):
        """停止托盘图标"""
        if self.icon:
            self.icon.stop()
        self.running = False
