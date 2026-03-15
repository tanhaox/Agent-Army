#!/usr/bin/env python3
"""
恢复备份并重启
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
print('  恢复备份并重启')
print('=' * 60)

# 查找备份文件
print('\n[1] 查找备份文件...')
stdin, stdout, stderr = ssh.exec_command('ls -lt /root/.openclaw/openclaw.json.bak* 2>/dev/null | head -3')
backups = stdout.read().decode('utf-8', errors='ignore')
print(backups)

# 恢复最新的备份
print('\n[2] 恢复备份...')
stdin, stdout, stderr = ssh.exec_command('cp /root/.openclaw/openclaw.json.bak.4 /root/.openclaw/openclaw.json 2>/dev/null && echo "已恢复 bak.4" || cp /root/.openclaw/openclaw.json.bak /root/.openclaw/openclaw.json && echo "已恢复 bak"')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

# 验证
print('\n[3] 验证配置文件...')
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json | head -20')
config_preview = stdout.read().decode('utf-8', errors='ignore')
print(config_preview)

# 重启
print('\n[4] 重启 Gateway...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)

stdin, stdout, stderr = ssh.exec_command('openclaw gateway >/dev/null 2>&1 &')
time.sleep(5)

# 检查
print('\n[5] 检查状态...')
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
        print('\n无法读取 token')
else:
    print('\n⚠️  Gateway 未启动，查看日志...')
    stdin, stdout, stderr = ssh.exec_command('tail -30 /tmp/openclaw/openclaw-*.log 2>/dev/null | tail -10')
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

ssh.close()
