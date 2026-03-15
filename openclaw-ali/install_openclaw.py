#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在服务器上安装OpenClaw"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

def execute_cmd(ssh, cmd, description=""):
    """执行SSH命令并显示输出"""
    if description:
        print(f"\n[执行] {description}")
    print(f"命令: {cmd}")
    print("-" * 60)

    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')

    if output.strip():
        print(output)
    if error.strip() and 'warning' not in error.lower():
        print(f"错误: {error}")

    return output

print("=" * 60)
print(" 服务器 OpenClaw 安装脚本")
print("=" * 60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

# 步骤1: 克隆仓库
print("\n[步骤 1/5] 克隆 OpenClaw-CN 仓库")
print("=" * 60)

# 先检查是否已存在
execute_cmd(ssh, "ls -la /root/ | grep claw", "检查现有OpenClaw目录")

# 克隆仓库 (使用 OpenClaw-CN，中文友好版本)
cmd = "cd /root && git clone https://github.com/OpenClaw-CN/openclaw-digitalocean.git"
output = execute_cmd(ssh, cmd, "克隆 OpenClaw-CN 仓库")

# 步骤2: 安装 pnpm
print("\n[步骤 2/5] 安装 pnpm")
print("=" * 60)
execute_cmd(ssh, "npm install -g pnpm", "全局安装 pnpm")

# 验证安装
execute_cmd(ssh, "pnpm --version", "验证 pnpm 版本")

# 步骤3: 安装依赖
print("\n[步骤 3/5] 安装项目依赖")
print("=" * 60)
execute_cmd(ssh, "cd /root/openclaw-digitalocean && pnpm install", "安装依赖 (可能需要几分钟)")

# 步骤4: 复制配置文件
print("\n[步骤 4/5] 配置环境变量")
print("=" * 60)
execute_cmd(ssh, "cd /root/openclaw-digitalocean && cp .env.example .env", "复制配置文件")

# 步骤5: 显示目录结构
print("\n[步骤 5/5] 检查安装结果")
print("=" * 60)
execute_cmd(ssh, "ls -la /root/openclaw-digitalocean/", "列出项目目录")

execute_cmd(ssh, "cat /root/openclaw-digitalocean/package.json | grep -A 5 'scripts'", "显示可用脚本")

print("\n" + "=" * 60)
print(" 安装完成！")
print("=" * 60)
print("\n项目位置: /root/openclaw-digitalocean")
print("\n下一步: 运行 setup 初始化配置")
print("命令: cd /root/openclaw-digitalocean && pnpm run setup")

ssh.close()
