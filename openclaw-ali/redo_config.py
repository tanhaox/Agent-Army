#!/usr/bin/env python3
"""
按照 DigitalOcean 成功经验重新配置
"""
import paramiko
import sys
import json
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print('=' * 60)
print('  按照 DigitalOcean 经验重新配置')
print('=' * 60)

# 1. 停止所有进程
print('\n[1] 停止所有 OpenClaw 进程...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)
print('✓ 已停止')

# 2. 设置简单的 token
print('\n[2] 设置简单 token...')
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))

# 设置简单的 token
if 'gateway' not in config:
    config['gateway'] = {}
if 'auth' not in config['gateway']:
    config['gateway']['auth'] = {}

config['gateway']['auth']['mode'] = 'token'
config['gateway']['auth']['token'] = 'openclaw123'

# 写入配置
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/openclaw.json', get_pty=True)
stdin.write(json.dumps(config, indent=2))
stdin.channel.shutdown_write()

print('✓ Token 已设置为: openclaw123')

# 3. 确保 agent.json 使用正确的模型
print('\n[3] 配置 agent 模型...')
agent_config = {
    "model": "zai/glm-4.7",
    "reasoning": True
}

stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/agents/main/agent/agent.json', get_pty=True)
stdin.write(json.dumps(agent_config, indent=2))
stdin.channel.shutdown_write()

print('✓ Agent 模型已设置为: zai/glm-4.7')

# 4. 确保 auth-profiles.json 正确
print('\n[4] 配置 zai 认证...')
auth_config = {
    "version": 1,
    "profiles": {
        "zai:default": {
            "type": "api_key",
            "provider": "zai",
            "key": "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"
        }
    },
    "lastGood": {
        "zai": "zai:default"
    }
}

stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/agents/main/agent/auth-profiles.json', get_pty=True)
stdin.write(json.dumps(auth_config, indent=2))
stdin.channel.shutdown_write()

print('✓ zai API key 已配置')

# 5. 清除所有会话
print('\n[5] 清除旧会话...')
stdin, stdout, stderr = ssh.exec_command('rm -rf /root/.openclaw/agents/main/sessions/*')
stdout.read()
print('✓ 会话已清除')

# 6. 启动 Gateway
print('\n[6] 启动 Gateway...')
stdin, stdout, stderr = ssh.exec_command('openclaw gateway >/dev/null 2>&1 &')
time.sleep(5)

# 7. 检查状态
print('\n[7] 检查状态...')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw | head -2')
status = stdout.read().decode('utf-8', errors='ignore')
print(status)

print('\n检查端口...')
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
port = stdout.read().decode('utf-8', errors='ignore')
print(port)

if '18789' in port:
    print('\n✓ Gateway 已启动')
else:
    print('\n⚠️  查看日志...')
    stdin, stdout, stderr = ssh.exec_command('tail -20 /tmp/openclaw/openclaw-*.log 2>/dev/null | tail -10')
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

ssh.close()

print('\n' + '=' * 60)
print('  配置完成')
print('=' * 60)
print('\n访问地址:')
print('  HTTPS: https://112.126.61.223/#token=openclaw123')
print('  HTTP:  http://112.126.61.223:18789/#token=openclaw123')
print('\n模型: zai/glm-4.7')
print('Token: openclaw123')
