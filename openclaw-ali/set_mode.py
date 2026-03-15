#!/usr/bin/env python3
"""
设置gateway.mode并启动
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

print('=' * 60)
print('  设置gateway.mode')
print('=' * 60)

# 1. 停止进程
print('\n[1] 停止所有进程...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)
print('✓ 已停止')

# 2. 设置gateway.mode
print('\n[2] 设置 gateway.mode = local...')
stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.mode local', get_pty=True)
time.sleep(3)
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

# 3. 查看配置
print('\n[3] 查看配置...')
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json | grep -A 20 gateway')
config = stdout.read().decode('utf-8', errors='ignore')
print(config)

# 4. 启动Gateway
print('\n[4] 启动Gateway...')
stdin, stdout, stderr = ssh.exec_command('OPENCLAW_NO_RESPAWN=1 openclaw gateway >/tmp/mode-start.log 2>&1 &')
time.sleep(8)

# 5. 检查状态
print('\n[5] 检查状态...')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw')
ps = stdout.read().decode('utf-8', errors='ignore')
print(ps)

print('\n检查端口...')
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
port = stdout.read().decode('utf-8', errors='ignore')
print(port)

if '18789' in port:
    print('\n' + '=' * 60)
    print('  ✓✓✓ 成功！Gateway 已启动')
    print('=' * 60)
    print('\n🌐 访问地址:')
    print('  HTTPS: https://112.126.61.223/#token=openclaw123')
    print('  HTTP:  http://112.126.61.223:18789/#token=openclaw123')
    print('\n🤖 模型: zai/glm-4.7')
    print('🔑 Token: openclaw123')
    print('\n现在可以在浏览器中测试对话功能了！')
else:
    print('\n查看日志...')
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/mode-start.log')
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

ssh.close()
