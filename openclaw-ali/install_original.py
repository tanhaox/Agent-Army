#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理服务器上的中文版，安装原版OpenClaw"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

def execute_cmd(ssh, cmd):
    """执行SSH命令"""
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    if output.strip():
        print(output)
    if error.strip() and 'warning' not in error.lower():
        print(f"错误: {error}")
    return output

print("=" * 60)
print(" 清理中文版 + 安装原版 OpenClaw")
print("=" * 60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

# 步骤1: 清理中文版
print("\n[步骤 1/4] 清理服务器上的中文版")
print("-" * 60)
execute_cmd(ssh, "rm -rf /root/openclaw-cn")
print("✅ 已删除 /root/openclaw-cn")

execute_cmd(ssh, "npm uninstall -g openclaw-cn 2>/dev/null || echo '未安装全局包'")
print("✅ 已卸载全局 openclaw-cn")

# 步骤2: 安装原版OpenClaw
print("\n[步骤 2/4] 安装原版 OpenClaw")
print("-" * 60)
print("正在全局安装...")
execute_cmd(ssh, "npm install -g openclaw@latest")
print("✅ 安装完成")

# 步骤3: 验证安装
print("\n[步骤 3/4] 验证安装")
print("-" * 60)
execute_cmd(ssh, "openclaw --version")
execute_cmd(ssh, "openclaw --help | head -30")

# 步骤4: 检查配置目录
print("\n[步骤 4/4] 检查配置目录")
print("-" * 60)
execute_cmd(ssh, "ls -la /root/.openclaw/ 2>/dev/null || echo '配置目录尚未创建（正常，运行onboard后会创建）'")

print("\n" + "=" * 60)
print(" 安装完成！")
print("=" * 60)
print("\n下一步：运行配置向导")
print("  openclaw onboard")

ssh.close()
