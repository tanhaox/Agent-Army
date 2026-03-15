#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

print("=" * 60)
print(" 在服务器上手动启动 Gateway")
print("=" * 60)
print("\n请手动 SSH 连接服务器执行以下命令：")
print("\n1. 连接服务器:")
print("   ssh root@112.126.61.223")
print("\n2. 清理旧进程:")
print("   pkill -9 -f openclaw")
print("\n3. 手动启动 Gateway (前台运行，可看到输出):")
print("   openclaw gateway")
print("\n4. 如果成功，你应该看到类似:")
print("   Gateway listening on port 18789")
print("\n5. 然后按 Ctrl+Z，bg 放入后台")
print("\n" + "=" * 60)
print("\n或者使用一键启动脚本:")

# 创建一键启动脚本
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

# 创建启动脚本
start_script = '''#!/bin/bash
echo "Starting OpenClaw Gateway..."
pkill -9 -f openclaw
sleep 1
cd /root
nohup openclaw gateway > /tmp/gateway.log 2>&1 &
sleep 3
echo "Checking status..."
ps aux | grep "[o]penclaw"
ss -tlnp | grep 18789
echo ""
echo "Logs:"
tail -20 /tmp/gateway.log
'''

stdin, stdout, stderr = ssh.exec_command('cat > /root/start-gateway.sh', get_pty=True)
stdin.write(start_script)
stdin.close()

stdin, stdout, stderr = ssh.exec_command('chmod +x /root/start-gateway.sh')
stdout.read()

print("\n已创建启动脚本 /root/start-gateway.sh")
print("SSH 登录后执行: /root/start-gateway.sh")

ssh.close()
