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
print(" 查看详细日志")
print("=" * 60)

# 查看系统日志
print("\n[系统 journal 日志]")
stdin, stdout, stderr = ssh.exec_command('journalctl --user -u openclaw-gateway.service -n 50 --no-pager 2>/dev/null || echo "无systemd日志"')
print(stdout.read().decode('utf-8', errors='ignore'))

# 查看临时日志
print("\n[临时日志文件]")
stdin, stdout, stderr = ssh.exec_command('ls -la /tmp/openclaw/*.log 2>/dev/null | tail -5')
result = stdout.read().decode('utf-8', errors='ignore')
if result.strip():
    print(result)
    print("\n最新日志:")
    stdin, stdout, stderr = ssh.exec_command('tail -50 /tmp/openclaw/*.log 2>/dev/null | tail -50')
    print(stdout.read().decode('utf-8', errors='ignore'))
else:
    print("无日志文件")

# 检查进程状态
print("\n[进程详情]")
stdin, stdout, stderr = ssh.exec_command('ps aux | grep "[o]penclaw"')
print(stdout.read().decode('utf-8', errors='ignore'))

# 检查所有监听端口
print("\n[所有监听端口]")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep -E "(18789|18790|18791)"')
print(stdout.read().decode('utf-8', errors='ignore') or "未找到相关端口")

# 直接运行看错误
print("\n[前台运行查看错误]")
stdin, stdout, stderr = ssh.exec_command('timeout 3 openclaw gateway --bind lan 2>&1 || true')
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')
print(output)
if error.strip():
    print("STDERR:", error)

ssh.close()
