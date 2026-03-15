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
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print('停止所有进程...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)

print('\n设置 allowedOrigins...')
stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.controlUi.allowedOrigins \'["*"]\'', get_pty=True)
time.sleep(3)
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

print('\n查看配置...')
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = stdout.read().decode('utf-8', errors='ignore')
print(config)

print('\n启动Gateway...')
stdin, stdout, stderr = ssh.exec_command('OPENCLAW_NO_RESPAWN=1 openclaw gateway >/tmp/origins-start.log 2>&1 &')
time.sleep(8)

print('\n检查进程:')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw')
ps = stdout.read().decode('utf-8', errors='ignore')
print(ps)

print('\n检查端口:')
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
port = stdout.read().decode('utf-8', errors='ignore')
print(port)

if '18789' in port:
    print('\n' + '=' * 60)
    print('  ✓✓✓ 成功！')
    print('=' * 60)
    print('\n访问: https://112.126.61.223/#token=openclaw123')
    print('或:    http://112.126.61.223:18789/#token=openclaw123')
else:
    print('\n查看日志...')
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/origins-start.log')
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

ssh.close()
