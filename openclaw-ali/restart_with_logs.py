#!/usr/bin/env python3
"""
重新启动并查看实时日志
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

print('杀掉所有openclaw进程...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)

print('\n删除旧日志...')
stdin, stdout, stderr = ssh.exec_command('rm -f /tmp/openclaw*.log /tmp/final.log')
stdout.read()
time.sleep(1)

print('\n启动Gateway（前台模式，5秒后超时）...')
# 使用timeout命令让进程在5秒后自动停止，这样我们可以看到启动日志
stdin, stdout, stderr = ssh.exec_command('timeout 5 openclaw gateway 2>&1 || true', get_pty=True)
time.sleep(6)

output = stdout.read().decode('utf-8', errors='ignore')
error_output = stderr.read().decode('utf-8', errors='ignore')

print('启动输出:')
print(output)
if error_output:
    print('错误输出:')
    print(error_output)

print('\n后台启动Gateway...')
stdin, stdout, stderr = ssh.exec_command('OPENCLAW_NO_RESPAWN=1 openclaw gateway >/tmp/openclaw-new.log 2>&1 &')
time.sleep(6)

print('\n检查新日志:')
stdin, stdout, stderr = ssh.exec_command('cat /tmp/openclaw-new.log')
logs = stdout.read().decode('utf-8', errors='ignore')
print(logs)

print('\n检查进程:')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw')
ps = stdout.read().decode('utf-8', errors='ignore')
print(ps)

print('\n检查端口:')
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
port = stdout.read().decode('utf-8', errors='ignore')
print(port)

ssh.close()
