#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("=" * 60)
print(" 原版 OpenClaw 安装验证")
print("=" * 60)

# 检查openclaw命令
print("\n[1] openclaw 命令位置")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('which openclaw')
result = stdout.read().decode('utf-8', errors='ignore').strip()
if result:
    print(f"✅ 已安装: {result}")
else:
    print("❌ 未找到")

# 检查版本
print("\n[2] 版本信息")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('openclaw --version 2>&1')
print(stdout.read().decode('utf-8', errors='ignore'))

# 查看帮助
print("\n[3] 帮助信息")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('openclaw --help 2>&1 | head -40')
print(stdout.read().decode('utf-8', errors='ignore'))

# 检查配置目录
print("\n[4] 配置目录")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('ls -la /root/.openclaw/ 2>/dev/null || echo "配置目录尚未创建"')
print(stdout.read().decode('utf-8', errors='ignore'))

print("\n" + "=" * 60)
print(" 验证完成！")
print("=" * 60)

print("\n🚀 下一步：运行配置向导")
print("   ssh root@112.126.61.223")
print("   openclaw onboard")

ssh.close()
