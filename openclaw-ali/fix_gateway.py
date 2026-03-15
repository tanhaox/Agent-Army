#!/usr/bin/env python3
"""
修复 OpenClaw Gateway 启动问题
"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("=" * 60)
print("  修复 OpenClaw Gateway 启动问题")
print("=" * 60)

# 1. 检查配置文件
print("\n[1] 验证 agent.json 配置...")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/agents/main/agent/agent.json')
agent_config = stdout.read().decode('utf-8', errors='ignore')
print("agent.json:")
print(agent_config)

# 2. 验证 auth-profiles.json
print("\n[2] 验证 auth-profiles.json 配置...")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/agents/main/agent/auth-profiles.json')
auth_config = stdout.read().decode('utf-8', errors='ignore')
print("auth-profiles.json:")
print(auth_config)

# 3. 尝试启动 Gateway
print("\n[3] 启动 Gateway...")
stdin, stdout, stderr = ssh.exec_command('openclaw gateway 2>&1 &', get_pty=True)
time.sleep(2)

# 4. 检查进程
print("\n[4] 检查进程状态...")
stdin, stdout, stderr = ssh.exec_command('ps aux | grep openclaw | grep -v grep')
status = stdout.read().decode('utf-8', errors='ignore')
print(status)

if 'openclaw' in status:
    print("\n✓ Gateway 启动成功！")
else:
    print("\n⚠️  Gateway 未启动，尝试前台启动查看错误...")
    stdin, stdout, stderr = ssh.exec_command('timeout 5 openclaw gateway 2>&1', get_pty=True)
    error_output = stdout.read().decode('utf-8', errors='ignore')
    print("错误信息:")
    print(error_output)

ssh.close()

print("\n" + "=" * 60)
print("  完成")
print("=" * 60)
