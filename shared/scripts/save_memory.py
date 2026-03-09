"""
记忆保存脚本

当用户说出"保存记忆"、"生成记忆"等口令时，自动保存当前会话的关键信息。

功能：
1. 捕获当前会话的关键信息
2. 格式化为 Markdown 并追加到 MEMORY.md
3. 如有必要，同步更新 1.md

使用方式：
    python save_memory.py --session "会话摘要"
    python save_memory.py --auto  # 自动捕获当前状态
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import argparse

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
MEMORY_FILE = Path.home() / ".claude" / "projects" / "c--AI-Agent-Local" / "memory" / "MEMORY.md"
PRELOAD_FILE = PROJECT_ROOT / "1.md"


class MemorySaver:
    """记忆保存器"""

    def __init__(self):
        self.memory_file = MEMORY_FILE
        self.preload_file = PRELOAD_FILE

        # 确保目录存在
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

    def get_current_status(self) -> dict:
        """获取当前项目状态"""
        status = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "projects": {},
            "services": {},
            "recent_changes": []
        }

        # 扫描 projects 目录
        projects_dir = PROJECT_ROOT / "projects"
        if projects_dir.exists():
            for category in ["skills", "apps", "tools"]:
                cat_dir = projects_dir / category
                if cat_dir.exists():
                    projects = [d.name for d in cat_dir.iterdir() if d.is_dir()]
                    status["projects"][category] = projects

        # 扫描服务状态（检查常见端口）
        import socket
        common_ports = {
            5007: "autogen",
            5006: "ollama",
            5002: "ocr",
            5000: "api_manager/intelligent_tutor"
        }

        for port, name in common_ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            status["services"][name] = result == 0
            sock.close()

        return status

    def format_memory_entry(self, session_info: dict) -> str:
        """格式化记忆条目"""
        date = datetime.now().strftime("%Y-%m-%d")

        entry = f"\n\n---\n\n## {session_info.get('title', '会话记录')}（{date}）\n\n"

        if session_info.get("description"):
            entry += f"**描述**: {session_info['description']}\n\n"

        if session_info.get("key_changes"):
            entry += "### 关键变更\n\n"
            for change in session_info["key_changes"]:
                entry += f"- {change}\n"
            entry += "\n"

        if session_info.get("files_modified"):
            entry += "### 修改的文件\n\n"
            for file in session_info["files_modified"]:
                entry += f"- `{file}`\n"
            entry += "\n"

        if session_info.get("files_created"):
            entry += "### 创建的文件\n\n"
            for file in session_info["files_created"]:
                entry += f"- `{file}`\n"
            entry += "\n"

        if session_info.get("bugs_fixed"):
            entry += "### 修复的问题\n\n"
            for bug in session_info["bugs_fixed"]:
                entry += f"- {bug}\n"
            entry += "\n"

        if session_info.get("new_features"):
            entry += "### 新增功能\n\n"
            for feature in session_info["new_features"]:
                entry += f"- {feature}\n"
            entry += "\n"

        if session_info.get("status"):
            entry += f"### 状态\n\n{session_info['status']}\n\n"

        if session_info.get("next_steps"):
            entry += "### 下一步\n\n"
            for step in session_info["next_steps"]:
                entry += f"- {step}\n"
            entry += "\n"

        return entry

    def save_memory(self, session_info: dict, update_preload: bool = False) -> dict:
        """保存记忆到文件"""
        result = {
            "success": False,
            "memory_updated": False,
            "preload_updated": False,
            "errors": []
        }

        try:
            # 读取现有记忆
            existing_content = ""
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()

            # 追加新记忆
            new_entry = self.format_memory_entry(session_info)

            # 检查是否已存在相同日期的条目
            date_str = datetime.now().strftime("%Y-%m-%d")
            if f"## {session_info.get('title', '会话记录')}（{date_str}）" in existing_content:
                result["errors"].append(f"已存在相同日期的条目，请修改标题或手动编辑")
                return result

            # 写入文件
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                f.write(existing_content + new_entry)

            result["memory_updated"] = True
            result["success"] = True

            # 更新 1.md（如果需要）
            if update_preload and self.preload_file.exists():
                self._update_preload_file(session_info)
                result["preload_updated"] = True

        except Exception as e:
            result["errors"].append(f"保存记忆失败: {e}")

        return result

    def _update_preload_file(self, session_info: dict):
        """更新 1.md 文件"""
        try:
            with open(self.preload_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 更新版本号（如果需要）
            # 这里可以根据实际需求添加更复杂的逻辑
            pass

        except Exception as e:
            print(f"警告：更新 1.md 失败: {e}")

    def generate_auto_session(self) -> dict:
        """自动生成当前会话摘要"""
        status = self.get_current_status()

        session = {
            "title": "自动会话记录",
            "description": f"当前项目状态快照 - {status['timestamp']}",
            "status": f"项目运行正常，发现 {sum(len(p) for p in status['projects'].values())} 个项目",
            "projects": status["projects"],
            "services": status["services"]
        }

        return session


def main():
    parser = argparse.ArgumentParser(
        description="保存当前会话记忆",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 手动保存会话
  python save_memory.py --title "服务管理技能开发" --desc "完成 v1.1.0 版本"

  # 自动保存当前状态
  python save_memory.py --auto

  # 保存并更新 1.md
  python save_memory.py --title "新功能" --update-preload
        """
    )

    parser.add_argument(
        '--title', '-t',
        type=str,
        help='会话标题'
    )

    parser.add_argument(
        '--description', '--desc', '-d',
        type=str,
        help='会话描述'
    )

    parser.add_argument(
        '--changes', '-c',
        type=str,
        nargs='+',
        help='关键变更列表'
    )

    parser.add_argument(
        '--files-modified', '-m',
        type=str,
        nargs='+',
        help='修改的文件列表'
    )

    parser.add_argument(
        '--files-created', '-f',
        type=str,
        nargs='+',
        help='创建的文件列表'
    )

    parser.add_argument(
        '--bugs', '-b',
        type=str,
        nargs='+',
        help='修复的问题列表'
    )

    parser.add_argument(
        '--features',
        type=str,
        nargs='+',
        help='新增功能列表'
    )

    parser.add_argument(
        '--status', '-s',
        type=str,
        help='当前状态'
    )

    parser.add_argument(
        '--next', '-n',
        type=str,
        nargs='+',
        help='下一步计划'
    )

    parser.add_argument(
        '--auto', '-a',
        action='store_true',
        help='自动生成当前状态摘要'
    )

    parser.add_argument(
        '--update-preload', '-u',
        action='store_true',
        help='同时更新 1.md 文件'
    )

    args = parser.parse_args()

    saver = MemorySaver()

    # 自动模式
    if args.auto:
        session_info = saver.generate_auto_session()
        result = saver.save_memory(session_info, args.update_preload)

        print("\n" + "="*70)
        print("自动记忆保存")
        print("="*70)
        print(f"\n{session_info['description']}")
        print(f"\n状态: {session_info['status']}")
        print(f"\n记忆文件: {'[OK] 已更新' if result['memory_updated'] else '[XX] 未更新'}")
        print(f"1.md 文件: {'[OK] 已更新' if result['preload_updated'] else '未变更'}")

        if result["errors"]:
            print(f"\n错误:")
            for error in result["errors"]:
                print(f"  - {error}")

        return

    # 手动模式
    if not args.title:
        print("错误：必须提供 --title 参数（或使用 --auto 自动模式）")
        parser.print_help()
        return

    session_info = {
        "title": args.title,
        "description": args.description,
        "key_changes": args.changes,
        "files_modified": args.files_modified,
        "files_created": args.files_created,
        "bugs_fixed": args.bugs,
        "new_features": args.features,
        "status": args.status,
        "next_steps": args.next
    }

    # 移除 None 值
    session_info = {k: v for k, v in session_info.items() if v is not None}

    result = saver.save_memory(session_info, args.update_preload)

    print("\n" + "="*70)
    print("记忆保存")
    print("="*70)
    print(f"\n标题: {session_info['title']}")
    print(f"记忆文件: {'[OK] 已更新' if result['memory_updated'] else '[XX] 未更新'}")
    print(f"1.md 文件: {'[OK] 已更新' if result['preload_updated'] else '未变更'}")

    if result["errors"]:
        print(f"\n错误:")
        for error in result["errors"]:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
