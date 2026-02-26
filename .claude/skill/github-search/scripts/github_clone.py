#!/usr/bin/env python3
"""
GitHub 仓库克隆工具
自动克隆 GitHub 仓库到本地
"""

import os
import sys
import subprocess
import re
from pathlib import Path

# Windows 控制台编码修复
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# 配置
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "github_downloads")
CLONE_TIMEOUT = 300  # 克隆超时时间（秒）


def is_github_repo(url):
    """
    判断是否为合法的 GitHub 仓库地址

    Args:
        url: 待验证的 URL

    Returns:
        标准化的 GitHub 仓库地址，或 None
    """
    github_pattern = r'^https?://github\.com/[\w-]+/[\w-]+'
    match = re.match(github_pattern, url.strip())
    return match.group(0) if match else None


def clone_repo(repo_url, custom_dir=None):
    """
    克隆 GitHub 仓库

    Args:
        repo_url: GitHub 仓库地址
        custom_dir: 自定义下载目录（可选）

    Returns:
        克隆结果信息
    """
    # 标准化仓库地址
    pure_url = is_github_repo(repo_url)
    if not pure_url:
        return {
            "success": False,
            "message": "❌ 无效的 GitHub 仓库地址，请检查格式！"
        }

    # 确定下载目录
    if custom_dir:
        download_dir = custom_dir
    else:
        download_dir = DOWNLOAD_DIR

    # 创建下载目录
    os.makedirs(download_dir, exist_ok=True)

    # 提取仓库名
    repo_name = pure_url.strip().split("/")[-1]
    clone_path = os.path.join(download_dir, repo_name)

    # 检查是否已存在
    if os.path.exists(clone_path) and os.path.isdir(clone_path):
        return {
            "success": False,
            "message": f"⚠️  【{repo_name}】已存在本地，无需重复下载！",
            "path": os.path.abspath(clone_path)
        }

    # 执行克隆
    print(f"\n🚀 开始下载【{repo_name}】")
    print(f"🔗 仓库地址：{pure_url}")
    print(f"📂 本地路径：{os.path.abspath(clone_path)}")
    print(f"⌛ 超时时间：{CLONE_TIMEOUT}秒，请耐心等待...")

    try:
        result = subprocess.run(
            ["git", "clone", pure_url, clone_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=CLONE_TIMEOUT
        )

        if result.returncode == 0:
            return {
                "success": True,
                "message": f"✅ 【{repo_name}】下载成功！",
                "path": os.path.abspath(clone_path),
                "url": pure_url
            }
        else:
            error_msg = result.stderr[:200].replace("\n", " ")
            return {
                "success": False,
                "message": f"❌ 【{repo_name}】下载失败！错误：{error_msg}"
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": f"❌ 下载超时！（{CLONE_TIMEOUT}秒），建议检查网络/仓库大小"
        }
    except FileNotFoundError:
        return {
            "success": False,
            "message": "❌ 未检测到 Git 环境！",
            "suggestion": "解决方案：安装 Git 并配置环境变量（https://git-scm.com/download/win）"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ 下载异常！错误：{str(e)[:100]}"
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='GitHub 仓库克隆工具')
    parser.add_argument('url', help='GitHub 仓库地址')
    parser.add_argument('--dir', '-d', help='自定义下载目录')

    args = parser.parse_args()

    result = clone_repo(args.url, args.dir)

    print(result["message"])
    if result.get("success"):
        print(f"📂 本地路径：{result['path']}")

    if "suggestion" in result:
        print(f"💡 {result['suggestion']}")


if __name__ == "__main__":
    main()
