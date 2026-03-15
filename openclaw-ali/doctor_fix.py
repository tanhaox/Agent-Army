#!/usr/bin/env python3
"""
使用 openclaw doctor 修复配置
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
print('  修复 OpenClaw 配置')
print('=' * 60)

# 运行 doctor
print('\n[1] 运行 openclaw doctor --fix...')
stdin, stdout, stderr = ssh.exec_command('openclaw doctor --fix', get_pty=True)
time.sleep(10)
doctor_output = stdout.read().decode('utf-8', errors='ignore')
print(doctor_output)

# 检查配置
print('\n[2] 检查配置文件...')
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json | head -30')
config = stdout.read().decode('utf-8', errors='ignore')
print(config)

# 重启
print('\n[3] 重启 Gateway...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)

stdin, stdout, stderr = ssh.exec_command('openclaw gateway >/dev/null 2>&1 &')
time.sleep(5)

# 检查
print('\n[4] 检查状态...')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw | head -2')
status = stdout.read().decode('utf-8', errors='ignore')
print(status)

print('\n检查端口...')
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
port = stdout.read().decode('utf-8', errors='ignore')
print(port)

if '18789' in port:
    print('\n✓ Gateway 已启动')
    # 获取 token
    stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
    try:
        config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
        token = config.get('gateway', {}).get('auth', {}).get('token', '')
        print(f'\n访问: https://112.126.61.223/#token={token}')
    except:
        pass
else:
    print('\n⚠️  仍未启动，查看日志...')
    stdin, stdout, stderr = ssh.exec_command('tail -20 /tmp/openclaw/openclaw-*.log 2>/dev/null | tail -10')
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

ssh.close()
