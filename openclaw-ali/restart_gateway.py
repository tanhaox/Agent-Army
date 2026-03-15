#!/usr/bin/env python3
"""
重启 OpenClaw Gateway
"""
import paramiko
import sys
import time
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print('=' * 60)
print('  重启 OpenClaw Gateway')
print('=' * 60)

# 1. 停止所有 OpenClaw 进程
print('\n[1] 停止旧进程...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)
print('✓ 已停止')

# 2. 启动 Gateway
print('\n[2] 启动 Gateway...')
stdin, stdout, stderr = ssh.exec_command('openclaw gateway >/dev/null 2>&1 &', get_pty=True)
time.sleep(5)

# 3. 检查进程
print('\n[3] 检查进程状态...')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw')
status = stdout.read().decode('utf-8', errors='ignore')

if 'openclaw' in status:
    print('✓ Gateway 已启动')
    print(status)
else:
    print('⚠️  未检测到进程，查看日志...')
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/openclaw.log')
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

# 4. 检查端口
print('\n[4] 检查端口监听...')
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
port_check = stdout.read().decode('utf-8', errors='ignore')

if '18789' in port_check:
    print('✓ 端口 18789 正在监听')
else:
    print('⚠️  端口 18789 未监听')

# 5. 获取当前 token
print('\n[5] 获取访问信息...')
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print('\n' + '=' * 60)
print('  ✓ Gateway 已重启')
print('=' * 60)
print(f'\nToken: {token}')
print(f'\n访问 URL:')
print(f'  HTTPS: https://112.126.61.223/#token={token}')
print(f'  HTTP:  http://112.126.61.223:18789/#token={token}')
print('\n提示：如果仍然报错 anthropic，请在浏览器中选择 zai/glm-4.7 模型')

ssh.close()
