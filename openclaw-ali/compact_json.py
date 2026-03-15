#!/usr/bin/env python3
"""
使用紧凑JSON格式（无缩进）避免截断问题
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
print('  使用紧凑JSON格式（最终方案）')
print('=' * 60)

# 1. 清理
print('\n[1] 清理...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw', get_pty=True)
stdout.read()
time.sleep(2)
stdin, stdout, stderr = ssh.exec_command('rm -rf /root/.openclaw /root/.openclaw-*', get_pty=True)
stdout.read()
time.sleep(1)
print('✓ 已清理')

# 2. 创建目录
print('\n[2] 创建目录...')
stdin, stdout, stderr = ssh.exec_command('mkdir -p /root/.openclaw/agents/main/agent', get_pty=True)
stdout.read()
print('✓ 目录已创建')

# 3. 写入紧凑JSON（无缩进，避免截断）
print('\n[3] 写入配置（紧凑格式）...')

# openclaw.json（紧凑格式，无缩进）
gateway_config = '{"gateway":{"bind":"lan","auth":{"mode":"token","token":"openclaw123"},"trustedProxies":["127.0.0.1","::1"]},"controlUi":{"allowedOrigins":["*"]}}'

# agent.json
agent_config = '{"model":"zai/glm-4.7","reasoning":true}'

# auth-profiles.json
auth_config = '{"version":1,"profiles":{"zai:default":{"type":"api_key","provider":"zai","key":"e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"}},"lastGood":{"zai":"zai:default"}}'

# 写入
stdin, stdout, stderr = ssh.exec_command(f'echo \'{gateway_config}\' > /root/.openclaw/openclaw.json', get_pty=True)
stdout.read()
time.sleep(0.5)

stdin, stdout, stderr = ssh.exec_command(f'echo \'{agent_config}\' > /root/.openclaw/agents/main/agent/agent.json', get_pty=True)
stdout.read()
time.sleep(0.5)

stdin, stdout, stderr = ssh.exec_command(f'echo \'{auth_config}\' > /root/.openclaw/agents/main/agent/auth-profiles.json', get_pty=True)
stdout.read()
time.sleep(0.5)

print('✓ 配置已写入')

# 4. 验证
print('\n[4] 验证配置...')
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json', get_pty=True)
config = stdout.read().decode('utf-8', errors='ignore')
print('openclaw.json:')
print(config)
print(f'\n配置长度: {len(config)} 字符')

# 5. 启动
print('\n[5] 启动 Gateway...')
stdin, stdout, stderr = ssh.exec_command('OPENCLAW_NO_RESPAWN=1 openclaw gateway >/tmp/final.log 2>&1 &', get_pty=True)
time.sleep(6)

# 6. 检查
print('\n[6] 检查状态...')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw | head -2', get_pty=True)
status = stdout.read().decode('utf-8', errors='ignore')
print(status)

print('\n检查端口...')
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789', get_pty=True)
port = stdout.read().decode('utf-8', errors='ignore')
print(port)

if '18789' in port:
    print('\n' + '=' * 60)
    print('  ✓✓✓✓✓ 成功！Gateway 已启动')
    print('=' * 60)
    print('\n🌐 访问地址:')
    print('  HTTPS: https://112.126.61.223/#token=openclaw123')
    print('  HTTP:  http://112.126.61.223:18789/#token=openclaw123')
    print('\n🤖 模型: zai/glm-4.7')
    print('🔑 Token: openclaw123')
    print('\n现在可以在浏览器中访问并测试对话功能了！')
else:
    print('\n查看日志:')
    stdin, stdout, stderr = ssh.exec_command('tail -50 /tmp/final.log', get_pty=True)
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

ssh.close()
