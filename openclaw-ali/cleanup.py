#!/usr/bin/env python3
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=15)

print('停止残留进程...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)

print('\n验证...')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw || echo "✓ 无残留进程"')
print(stdout.read().decode('utf-8', errors='ignore').strip())

stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789 || echo "✓ 端口已释放"')
print(stdout.read().decode('utf-8', errors='ignore').strip())

ssh.close()
