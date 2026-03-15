#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在服务器上安装OpenClaw - 使用镜像和重试"""
import paramiko
import sys

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
print(" 服务器 OpenClaw 安装脚本 (镜像版)")
print("=" * 60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

# 步骤1: 配置Git使用镜像
print("\n[步骤 1/6] 配置 Git 镜像加速")
print("=" * 60)
execute_cmd(ssh, "git config --global http.postBuffer 524288000", "增大Git缓存")
execute_cmd(ssh, "git config --global http.lowSpeedLimit 0", "禁用低速限制")
execute_cmd(ssh, "git config --global http.lowSpeedTime 999999", "延长超时")

# 步骤2: 尝试克隆（使用ghproxy镜像）
print("\n[步骤 2/6] 克隆 OpenClaw-CN 仓库 (使用镜像)")
print("=" * 60)

# 尝试多种镜像源
mirrors = [
    "https://mirror.ghproxy.com/https://github.com/OpenClaw-CN/openclaw-digitalocean.git",
    "https://ghproxy.net/https://github.com/OpenClaw-CN/openclaw-digitalocean.git",
    "https://github.com/OpenClaw-CN/openclaw-digitalocean.git"
]

cloned = False
for mirror in mirrors:
    print(f"\n尝试镜像: {mirror}")
    output = execute_cmd(ssh, f"cd /root && rm -rf openclaw-digitalocean && git clone {mirror} openclaw-digitalocean", "克隆仓库")
    if 'done' in output.lower() or 'received' in output.lower():
        cloned = True
        print("\n✅ 克隆成功！")
        break
    else:
        print(f"❌ 此镜像失败，尝试下一个...")

if not cloned:
    print("\n⚠️ 所有镜像都失败了，尝试手动下载...")
    # 手动下载方式
    execute_cmd(ssh, "cd /root && rm -rf openclaw-digitalocean openclaw-digitalocean.zip", "清理旧文件")
    execute_cmd(ssh, 'cd /root && wget https://github.com/OpenClaw-CN/openclaw-digitalocean/archive/refs/heads/main.zip -O openclaw-digitalocean.zip --timeout=30', "下载ZIP压缩包")
    execute_cmd(ssh, "cd /root && unzip -o openclaw-digitalocean.zip && mv openclaw-digitalocean-main openclaw-digitalocean", "解压并重命名")
    execute_cmd(ssh, "cd /root && rm -f openclaw-digitalocean.zip", "清理ZIP文件")

# 步骤3: 验证克隆结果
print("\n[步骤 3/6] 验证克隆结果")
print("=" * 60)
execute_cmd(ssh, "ls -la /root/openclaw-digitalocean/", "列出项目目录")

# 步骤4: 检查package.json
print("\n[步骤 4/6] 检查项目配置")
print("=" * 60)
execute_cmd(ssh, "test -f /root/openclaw-digitalocean/package.json && echo '✅ package.json 存在' || echo '❌ package.json 不存在'", "验证package.json")

# 步骤5: 安装依赖
print("\n[步骤 5/6] 安装项目依赖")
print("=" * 60)
execute_cmd(ssh, "cd /root/openclaw-digitalocean && pnpm install", "安装依赖 (可能需要几分钟)")

# 步骤6: 配置环境
print("\n[步骤 6/6] 配置环境")
print("=" * 60)
execute_cmd(ssh, "cd /root/openclaw-digitalocean && cp .env.example .env 2>/dev/null || echo '没有.env.example文件'", "复制配置文件")

print("\n" + "=" * 60)
print(" 安装完成！")
print("=" * 60)
print("\n项目位置: /root/openclaw-digitalocean")

# 检查setup脚本
execute_cmd(ssh, "cat /root/openclaw-digitalocean/package.json | grep -A 2 '\"setup\"' || cat /root/openclaw-digitalocean/package.json | grep -A 2 'scripts'", "显示setup脚本")

print("\n下一步: 运行 setup 初始化配置")
print("命令: cd /root/openclaw-digitalocean && pnpm run setup")

ssh.close()
