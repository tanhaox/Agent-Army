"""
环境检测脚本

自动检测当前开发环境配置，包括：
- 系统信息
- Python 版本
- 关键包版本
- 硬件配置

使用方式：
    python check_environment.py
"""

import sys
import platform
import subprocess
from pathlib import Path


def get_python_version():
    """获取 Python 版本"""
    return platform.python_version()


def get_system_info():
    """获取系统信息"""
    return {
        "系统": platform.system(),
        "版本": platform.version(),
        "架构": platform.machine(),
        "处理器": platform.processor()
    }


def get_pip_version():
    """获取 pip 版本"""
    try:
        result = subprocess.run(
            ["pip", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        return result.stdout.strip()
    except:
        return "未知"


def get_package_version(package_name):
    """获取包版本"""
    try:
        result = subprocess.run(
            ["pip", "show", package_name],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        for line in result.stdout.split("\n"):
            if line.startswith("Version:"):
                return line.split(":")[1].strip()
        return "未安装"
    except:
        return "未安装"


def get_git_version():
    """获取 Git 版本"""
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        return result.stdout.strip()
    except:
        return "未安装"


def get_node_version():
    """获取 Node.js 版本"""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        return result.stdout.strip()
    except:
        return "未安装"


def get_hardware_info():
    """获取硬件信息"""
    try:
        import psutil

        mem = psutil.virtual_memory()
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)

        return {
            "总内存": f"{mem.total // (1024**3)} GB",
            "可用内存": f"{mem.available // (1024**3)} GB",
            "CPU 物理核心": cpu_count_physical,
            "CPU 逻辑线程": cpu_count_logical
        }
    except ImportError:
        return {
            "总内存": "未知（需要 psutil）",
            "可用内存": "未知（需要 psutil）",
            "CPU 物理核心": "未知（需要 psutil）",
            "CPU 逻辑线程": "未知（需要 psutil）"
        }


def check_environment():
    """执行环境检测"""
    print("="*70)
    print("开发环境检测")
    print("="*70)

    # Python
    print("\n[Python 环境]")
    print(f"  Python 版本: {get_python_version()}")
    print(f"  pip 版本: {get_pip_version()}")

    # 系统
    print("\n[操作系统]")
    sys_info = get_system_info()
    for key, value in sys_info.items():
        print(f"  {key}: {value}")

    # 硬件
    print("\n[硬件配置]")
    hw_info = get_hardware_info()
    for key, value in hw_info.items():
        print(f"  {key}: {value}")

    # 工具链
    print("\n[工具链]")
    git_ver = get_git_version()
    node_ver = get_node_version()
    print(f"  Git: {git_ver}")
    print(f"  Node.js: {node_ver}")

    # 关键包
    print("\n[关键 Python 包]")
    packages = [
        ("flask", "Flask"),
        ("httpx", "httpx"),
        ("requests", "requests"),
        ("ollama", "ollama"),
        ("openai", "openai"),
        ("langchain-ollama", "langchain-ollama"),
        ("psutil", "psutil")
    ]

    for pkg_name, display_name in packages:
        version = get_package_version(pkg_name)
        status = "[OK]" if version != "未安装" else "[--]"
        print(f"  {status} {display_name}: {version}")

    # 项目路径
    print("\n[项目路径]")
    project_root = Path(__file__).parent.parent.parent
    print(f"  项目根目录: {project_root}")

    memory_file = Path.home() / ".claude" / "projects" / "c--AI-Agent-Local" / "memory" / "MEMORY.md"
    print(f"  记忆文件: {memory_file}")
    print(f"    存在: {'[是]' if memory_file.exists() else '[否]'}")

    print("\n" + "="*70)
    print("检测完成")
    print("="*70)


def main():
    """主函数"""
    try:
        check_environment()
    except Exception as e:
        print(f"\n[XX] 检测失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
