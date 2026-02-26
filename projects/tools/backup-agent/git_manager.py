#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git 管理模块 - 负责所有 Git 操作

功能：
- 初始化 Git 仓库
- 检测文件修改
- 执行备份（git add + commit）
- 获取提交历史
- 回滚到指定提交

作者：Backup Agent
创建日期：2026-02-26
"""

import os
import sys
import git
from datetime import datetime
from typing import Optional, List, Dict
from utils import should_exclude_path


class GitManager:
    """Git 管理器"""

    def __init__(self, repo_path: str, config: dict):
        """
        初始化 Git 管理器

        Args:
            repo_path: 仓库路径
            config: 配置字典
        """
        self.repo_path = repo_path
        self.config = config
        self.git_dir = os.path.join(repo_path, '.git')

        # 初始化或打开仓库
        self._init_repo()

    def _init_repo(self):
        """初始化或打开 Git 仓库"""
        try:
            # 检查是否已存在 .git 目录
            if os.path.exists(self.git_dir):
                # 尝试打开现有仓库
                try:
                    self.repo = git.Repo(self.repo_path)
                    # 验证仓库是否可用
                    self._validate_repo()
                except (git.GitCommandError, git.InvalidGitRepositoryError, ValueError) as e:
                    print(f"⚠️  现有仓库损坏: {e}")
                    print(f"🔧 尝试修复...")
                    # 仓库损坏，尝试重新初始化
                    self._reinit_repo()
            else:
                # 初始化新仓库
                if self.config.get('git', {}).get('auto_init', True):
                    self._init_new_repo()
                else:
                    raise Exception("Git 仓库不存在且 auto_init 配置为 False")
        except Exception as e:
            print(f"❌ Git 仓库初始化失败: {e}")
            raise

    def _validate_repo(self):
        """
        P1: 验证仓库是否可用（改进版）
        检查 Git 仓库的关键组件是否完好
        """
        try:
            # 检查 .git 目录是否存在
            if not os.path.exists(self.git_dir):
                raise ValueError(f".git 目录不存在: {self.git_dir}")

            # 检查 objects 目录（Git 对象存储）
            objects_dir = os.path.join(self.git_dir, 'objects')
            if not os.path.exists(objects_dir):
                raise ValueError(f"Git objects 目录不存在: {objects_dir}")

            # 检查 HEAD 文件
            head_file = os.path.join(self.git_dir, 'HEAD')
            if not os.path.exists(head_file):
                raise ValueError(f"Git HEAD 文件不存在: {head_file}")

            # 检查是否能访问 HEAD
            try:
                _ = self.repo.head
            except ValueError as e:
                if "bad object HEAD" in str(e) or "reference does not exist" in str(e):
                    # HEAD 指向的引用不存在（损坏）
                    raise ValueError(f"HEAD 损坏或引用不存在: {e}")
                raise

            # 检查是否有有效的分支
            if self.repo.heads:
                # 尝试访问第一个分支的 commit
                try:
                    _ = self.repo.heads[0].commit
                except (ValueError, git.GitCommandError) as e:
                    raise ValueError(f"分支 commit 损坏: {e}")

        except (git.GitCommandError, ValueError, IndexError, OSError) as e:
            # 仓库状态异常，需要修复
            raise

    def _init_new_repo(self):
        """初始化新的 Git 仓库"""
        print(f"🎬 正在初始化 Git 仓库: {self.repo_path}")
        self.repo = git.Repo.init(self.repo_path)

        # 配置用户信息
        git_config = self.config.get('git', {})
        user_name = git_config.get('user_name', 'Backup Agent')
        user_email = git_config.get('user_email', 'backup-agent@local')

        with self.repo.config_writer() as config:
            config.set_value('user', 'name', user_name)
            config.set_value('user', 'email', user_email)

        # 创建初始提交
        self._create_initial_commit()
        print(f"✅ Git 仓库初始化完成")

    def _reinit_repo(self):
        """重新初始化损坏的仓库"""
        import shutil
        print(f"🔄 正在重新初始化仓库...")

        # 备份旧的 .git 目录
        git_backup = self.git_dir + '.backup'
        if os.path.exists(self.git_dir):
            if os.path.exists(git_backup):
                shutil.rmtree(git_backup)
            shutil.move(self.git_dir, git_backup)
            print(f"💾 旧 .git 已备份到: {git_backup}")

        # 重新初始化
        self._init_new_repo()

    def _create_initial_commit(self):
        """创建初始提交"""
        try:
            # 添加所有文件
            self.repo.index.add(["."])

            # 创建初始提交
            commit_msg = f"🎉 初始备份 - 自动备份系统启动 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            self.repo.index.commit(commit_msg)
            print(f"💾 初始提交完成: {commit_msg}")
        except Exception as e:
            print(f"⚠️  初始提交创建失败: {e}")
            # 即使提交失败，仓库也已经初始化了
            print(f"💡 提示：仓库已初始化，下次修改时会自动创建提交")

    def has_changes(self) -> bool:
        """
        检查是否有未提交的修改

        Returns:
            bool: True 表示有修改，False 表示无修改
        """
        # 检查是否有未暂存的修改
        is_dirty = self.repo.is_dirty()

        # 检查是否有未跟踪的文件
        has_untracked = len(self.repo.untracked_files) > 0

        return is_dirty or has_untracked

    def backup(self, backup_type: str, keyword: Optional[str] = None) -> str:
        """
        执行备份

        Args:
            backup_type: 备份类型（keyword/hourly）
            keyword: 触发关键词（仅当 backup_type='keyword' 时使用）

        Returns:
            str: commit 消息
        """
        try:
            # 验证仓库状态
            try:
                _ = self.repo.head
            except (git.GitCommandError, ValueError) as e:
                print(f"⚠️  仓库状态异常，尝试修复: {e}")
                self._reinit_repo()

            # 添加有修改的文件（排除不需要备份的目录）
            added_count = self._add_changed_files()

            if added_count == 0:
                # 没有需要提交的修改
                print(f"💡 没有需要提交的修改")
                return ""

            # 生成 commit 消息
            commit_msg = self._generate_commit_message(backup_type, keyword)

            # 创建提交
            commit = self.repo.index.commit(commit_msg)

            print(f"✅ 已添加 {added_count} 个文件")
            return commit_msg

        except Exception as e:
            print(f"❌ 备份失败: {str(e)}")
            raise

    def _add_changed_files(self) -> int:
        """
        添加有修改的文件（排除不需要备份的目录）

        Returns:
            int: 成功添加的文件数量
        """
        # 排除模式（不需要备份的目录和文件）
        exclude_patterns = self.config.get('backup_compression', {}).get('exclude_patterns', [
            '.git', 'node_modules', '__pycache__', '.next', 'github_downloads'
        ])

        added_count = 0
        skipped_count = 0

        try:
            # 获取有修改的文件
            # 1. 未暂存的修改
            for item in self.repo.index.diff(None):
                filepath = item.b_path  # 修改后的文件路径
                if self._should_include(filepath, exclude_patterns):
                    success, skipped = self._try_add_file(filepath)
                    if success:
                        added_count += 1
                    if skipped:
                        skipped_count += 1
                else:
                    skipped_count += 1

            # 2. 未跟踪的文件
            for filepath in self.repo.untracked_files:
                if self._should_include(filepath, exclude_patterns):
                    success, skipped = self._try_add_file(filepath)
                    if success:
                        added_count += 1
                    if skipped:
                        skipped_count += 1
                else:
                    skipped_count += 1

            if skipped_count > 0:
                print(f"🔄 跳过 {skipped_count} 个文件（排除模式或无法访问）")

            return added_count

        except Exception as e:
            print(f"❌ 获取修改文件失败: {str(e)}")
            return 0

    def _should_include(self, filepath: str, exclude_patterns: list) -> bool:
        """
        判断文件是否应该被包含在备份中

        Args:
            filepath: 文件路径
            exclude_patterns: 排除模式列表

        Returns:
            bool: True 表示包含，False 表示排除
        """
        return not should_exclude_path(filepath, exclude_patterns)

    def _try_add_file(self, filepath: str) -> tuple:
        """
        尝试添加单个文件到 Git 索引

        Args:
            filepath: 文件路径

        Returns:
            tuple: (success: bool, skipped: bool)
        """
        try:
            self.repo.index.add([filepath])
            return True, False
        except PermissionError as e:
            # P0: Git 对象文件权限冲突
            print(f"⚠️  权限拒绝，跳过 {filepath}: {e}")
            return False, True
        except FileNotFoundError as e:
            # P0: 文件不存在（长路径或其他原因）
            print(f"⚠️  文件不存在，跳过 {filepath}: {e}")
            return False, True
        except (OSError, IOError) as e:
            # P0: 其他文件系统错误
            print(f"⚠️  无法访问 {filepath}: {type(e).__name__}: {e}")
            return False, True
        except Exception as e:
            print(f"⚠️  无法添加 {filepath}: {e}")
            return False, True

    def _generate_commit_message(self, backup_type: str, keyword: Optional[str] = None) -> str:
        """
        生成 commit 消息

        Args:
            backup_type: 备份类型（keyword/hourly）
            keyword: 触发关键词

        Returns:
            str: commit 消息
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        if backup_type == "keyword" and keyword:
            return f"💾 [关键词触发] 在检测到'{keyword}'讨论前 - {now}"
        elif backup_type == "improvement":
            return f"💾 [改进意见触发] 在创建改进意见文档前 - {now}"
        else:
            return f"💾 [整点备份] 定时备份 - {now}"

    def get_commit_history(self, hours: int = 12) -> List[Dict]:
        """
        获取最近 N 小时的提交历史

        Args:
            hours: 查询最近多少小时

        Returns:
            List[Dict]: 提交历史列表
        """
        # 检查是否是空仓库（没有提交）
        try:
            # 更健壮的检查
            if not self.repo.heads:
                return []
            # 检查 HEAD 是否有效
            _ = self.repo.head.commit
        except (git.GitCommandError, ValueError, IndexError, AttributeError) as e:
            print(f"⚠️  无法读取提交历史: {e}")
            return []

        # 计算时间范围
        from datetime import timedelta
        time_limit = datetime.now() - timedelta(hours=hours)

        commits = []
        try:
            for commit in self.repo.iter_commits():
                commit_time = datetime.fromtimestamp(commit.committed_date)

                # 只返回最近 N 小时的提交
                if commit_time < time_limit:
                    break

                commits.append({
                    'id': len(commits) + 1,
                    'hash': commit.hexsha[:7],
                    'message': commit.message.strip(),
                    'time': commit_time.strftime('%Y-%m-%d %H:%M'),
                    'author': commit.author.name
                })
        except Exception as e:
            print(f"⚠️  遍历提交历史时出错: {e}")

        return commits

    def rollback_to_commit(self, target: str) -> bool:
        """
        回滚到指定提交

        Args:
            target: 目标（可以是 commit hash、ID、或时间）

        Returns:
            bool: 是否成功
        """
        try:
            # 验证仓库状态
            try:
                if not self.repo.heads:
                    print("❌ 仓库没有任何提交，无法回滚")
                    return False
            except Exception as e:
                print(f"❌ 仓库状态异常: {e}")
                return False

            # 先创建当前状态的备份点
            current_backup_msg = self.backup("keyword", "回滚前安全备份")
            print(f"🛡️ 回滚前安全备份: {current_backup_msg}")

            # 解析目标 commit
            target_commit = self._resolve_target(target)

            if not target_commit:
                print(f"❌ 未找到目标提交: {target}")
                return False

            # 执行回滚（hard reset）
            git.reset.reset(self.repo, target_commit, index=True, working_tree=True)

            print(f"✅ 回滚成功: {target}")
            return True

        except Exception as e:
            print(f"❌ 回滚失败: {str(e)}")
            return False

    def _resolve_target(self, target: str):
        """
        解析目标为 commit 对象

        Args:
            target: 目标（hash/时间/ID）

        Returns:
            Commit 对象或 None
        """
        try:
            # 尝试作为 commit hash
            try:
                return self.repo.commit(target)
            except (git.GitCommandError, ValueError):
                pass

            # 尝试作为时间戳
            if "-" in target and ":" in target:
                # 时间格式：YYYY-MM-DD HH:MM
                try:
                    target_time = datetime.strptime(target, "%Y-%m-%d %H:%M")
                    for commit in self.repo.iter_commits():
                        commit_time = datetime.fromtimestamp(commit.committed_date)
                        # 找到最接近的 commit
                        if commit_time <= target_time:
                            return commit
                except ValueError:
                    pass

            # 尝试在 commit 消息中查找关键词
            try:
                for commit in self.repo.iter_commits():
                    if target in commit.message:
                        return commit
            except Exception:
                pass

        except Exception as e:
            print(f"⚠️  解析目标时出错: {e}")

        return None

    def get_status(self) -> dict:
        """
        获取仓库状态

        Returns:
            dict: 状态信息
        """
        # 获取分支名
        branch_name = None
        try:
            if self.repo.heads:
                branch_name = self.repo.active_branch.name
            else:
                branch_name = "master (未初始化)"
        except Exception as e:
            branch_name = f"unknown ({str(e)})"

        # 获取最新提交消息
        latest_commit = None
        try:
            if self.repo.heads and self.repo.head.commit:
                latest_commit = self.repo.head.commit.message.strip()
        except Exception as e:
            latest_commit = None

        # 获取仓库状态
        is_dirty = False
        untracked_count = 0
        try:
            is_dirty = self.repo.is_dirty()
            untracked_count = len(self.repo.untracked_files)
        except Exception:
            pass

        return {
            'repo_path': self.repo_path,
            'branch': branch_name,
            'is_dirty': is_dirty,
            'untracked_files': untracked_count,
            'latest_commit': latest_commit
        }
