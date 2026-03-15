#!/usr/bin/env python3
"""
使用 OpenClaw CLI 正确配置
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
print('  使用 OpenClaw CLI 配置')
print('=' * 60)

# 1. 完全清理
print('\n[1] 清理环境...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw && rm -rf /root/.openclaw')
stdout.read()
time.sleep(2)
print('✓ 已清理')

# 2. 运行向导（选择默认配置）
print('\n[2] 运行初始化向导...')
# 使用环境变量自动选择默认配置
env_commands = '''
export OPENCLAW_NO_RESPAWN=1
export OPENCLAW_GATEWAY_MODE=local
export OPENCLAW_GATEWAY_BIND=lan
export OPENCLAW_GATEWAY_AUTH_MODE=token
export OPENCLAW_GATEWAY_AUTH_TOKEN=openclaw123
'''

stdin, stdout, stderr = ssh.exec_command(f'{env_commands} openclaw setup --wizard --non-interactive', get_pty=True)
time.sleep(10)
wizard_output = stdout.read().decode('utf-8', errors='ignore')
print(wizard_output[:500] if len(wizard_output) > 500 else wizard_output)

# 3. 配置模型
print('\n[3] 配置模型...')
stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.bind lan', get_pty=True)
time.sleep(1)

stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.auth.mode token', get_pty=True)
time.sleep(1)

stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.auth.token openclaw123', get_pty=True)
time.sleep(1)

stdin, stdout, stderr = ssh.exec_command('openclaw config set controlUi.allowedOrigins \'["*"]\'', get_pty=True)
time.sleep(1)

stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.trustedProxies \'["127.0.0.1", "::1"]\'', get_pty=True)
time.sleep(1)

print('✓ 配置已完成')

# 4. 手动创建 agent 配置
print('\n[4] 创建 agent 配置...')
agent_config = {"model": "zai/glm-4.7", "reasoning": True}
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

# 创建目录
stdin, stdout, stderr = ssh.exec_command('mkdir -p /root/.openclaw/agents/main/agent', get_pty=True)
time.sleep(1)

# 写入文件（使用 echo 避免编码问题）
agent_json_str = json.dumps(agent_config, indent=2).replace('"', '\\"')
stdin, stdout, stderr = ssh.exec_command(f'echo "{agent_json_str}" > /root/.openclaw/agents/main/agent/agent.json', get_pty=True)
time.sleep(1)

auth_json_str = json.dumps(auth_config, indent=2).replace('"', '\\"')
stdin, stdout, stderr = ssh.exec_command(f'echo "{auth_json_str}" > /root/.openclaw/agents/main/agent/auth-profiles.json', get_pty=True)
time.sleep(1)

print('✓ Agent 配置已创建')

# 5. 启动
print('\n[5] 启动 Gateway...')
stdin, stdout, stderr = ssh.exec_command('OPENCLAW_NO_RESPAWN=1 openclaw gateway >/tmp/openclaw-gateway.log 2>&1 &')
time.sleep(5)

# 6. 检查
print('\n[6] 检查状态...')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw')
status = stdout.read().decode('utf-8', errors='ignore')
print(status)

print('\n检查端口...')
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
port = stdout.read().decode('utf-8', errors='ignore')
print(port)

if '18789' in port:
    print('\n✓ Gateway 已启动')
    print('\n访问: https://112.126.61.223/#token=openclaw123')
else:
    print('\n⚠️  查看日志...')
    stdin, stdout, stderr = ssh.exec_command('tail -20 /tmp/openclaw-gateway.log 2>/dev/null || tail -20 /tmp/openclaw/openclaw-*.log 2>/dev/null')
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

ssh.close()
