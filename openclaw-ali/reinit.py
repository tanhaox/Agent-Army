#!/usr/bin/env python3
"""
完全重新初始化 OpenClaw
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
print('  完全重新初始化 OpenClaw')
print('=' * 60)

# 1. 停止所有进程
print('\n[1] 停止所有 OpenClaw 进程...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)
print('✓ 已停止')

# 2. 备份当前配置
print('\n[2] 备份当前配置...')
stdin, stdout, stderr = ssh.exec_command('mv /root/.openclaw /root/.openclaw.backup.$(date +%s) 2>/dev/null || echo "无需备份"')
stdout.read()
print('✓ 已备份')

# 3. 重新初始化
print('\n[3] 重新初始化配置...')
# 使用 Python json 模块生成配置
import json

gateway_config = {
    "gateway": {
        "bind": "lan",
        "auth": {
            "mode": "token",
            "token": "openclaw123"
        },
        "trustedProxies": ["127.0.0.1", "::1"]
    },
    "controlUi": {
        "allowedOrigins": ["*"]
    }
}

stdin, stdout, stderr = ssh.exec_command('mkdir -p /root/.openclaw', get_pty=True)
stdout.read()

stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/openclaw.json', get_pty=True)
stdin.write(json.dumps(gateway_config, indent=2))
stdin.channel.shutdown_write()

print('✓ 配置文件已创建')

# 4. 创建 agent 配置
print('\n[4] 创建 agent 配置...')
import json

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

stdin, stdout, stderr = ssh.exec_command('mkdir -p /root/.openclaw/agents/main/agent', get_pty=True)
stdout.read()

stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/agents/main/agent/agent.json', get_pty=True)
stdin.write(json.dumps(agent_config, indent=2))
stdin.channel.shutdown_write()

stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/agents/main/agent/auth-profiles.json', get_pty=True)
stdin.write(json.dumps(auth_config, indent=2))
stdin.channel.shutdown_write()

print('✓ Agent 配置已创建')

# 5. 启动
print('\n[5] 启动 Gateway...')
stdin, stdout, stderr = ssh.exec_command('openclaw gateway >/dev/null 2>&1 &')
time.sleep(5)

# 6. 检查
print('\n[6] 检查状态...')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw | head -2')
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
    stdin, stdout, stderr = ssh.exec_command('tail -30 /tmp/openclaw/openclaw-*.log 2>/dev/null | tail -15')
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

ssh.close()
