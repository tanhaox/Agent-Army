#!/usr/bin/env python3
"""
最简单的方法：让 OpenClaw 自己生成配置
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
print('  让 OpenClaw 自己生成配置')
print('=' * 60)

# 1. 完全清理
print('\n[1] 清理环境...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw && rm -rf /root/.openclaw')
stdout.read()
time.sleep(2)
print('✓ 已清理')

# 2. 直接启动（让 OpenClaw 自动生成配置）
print('\n[2] 启动 OpenClaw（自动生成配置）...')
stdin, stdout, stderr = ssh.exec_command('OPENCLAW_NO_RESPAWN=1 openclaw gateway >/tmp/openclaw-start.log 2>&1 &')
time.sleep(5)

# 3. 等待配置文件生成
print('\n[3] 等待配置生成...')
stdin, stdout, stderr = ssh.exec_command('ls -la /root/.openclaw/openclaw.json 2>/dev/null && echo "配置已生成" || echo "等待中..."')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

# 4. 使用 dashboard 设置 token
print('\n[4] 生成 token...')
stdin, stdout, stderr = ssh.exec_command('sleep 3 && openclaw dashboard --no-open', get_pty=True)
time.sleep(5)
dashboard = stdout.read().decode('utf-8', errors='ignore')
print(dashboard)

# 获取 token
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json 2>/dev/null | grep -oP \'token[^,]*"[^"]*"\' || cat /root/.openclaw/openclaw.json 2>/dev/null')
try:
    import json
    config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
    token = config.get('gateway', {}).get('auth', {}).get('token', '')
    print(f'Token: {token}')
except:
    print('无法读取 token')

# 5. 配置 agent
print('\n[5] 配置 agent...')
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

# 使用 heredoc 避免引号问题
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/agents/main/agent/agent.json <<\'EOF\'\n' + json.dumps(agent_config, indent=2) + '\nEOF', get_pty=True)
time.sleep(1)

stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/agents/main/agent/auth-profiles.json <<\'EOF\'\n' + json.dumps(auth_config, indent=2) + '\nEOF', get_pty=True)
time.sleep(1)

print('✓ Agent 配置已创建')

# 6. 重启
print('\n[6] 重启 Gateway...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw && sleep 2 && OPENCLAW_NO_RESPAWN=1 openclaw gateway >/tmp/openclaw-final.log 2>&1 &')
time.sleep(5)

# 7. 检查
print('\n[7] 检查状态...')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw | head -2')
status = stdout.read().decode('utf-8', errors='ignore')
print(status)

print('\n检查端口...')
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
port = stdout.read().decode('utf-8', errors='ignore')
print(port)

if '18789' in port:
    print('\n✓✓✓ 成功！Gateway 已启动')

    # 获取最终 token
    stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
    config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
    token = config.get('gateway', {}).get('auth', {}).get('token', '')

    print(f'\n访问地址:')
    print(f'  HTTPS: https://112.126.61.223/#token={token}')
    print(f'  HTTP:  http://112.126.61.223:18789/#token={token}')
    print(f'\n模型: zai/glm-4.7')
else:
    print('\n⚠️  查看日志...')
    stdin, stdout, stderr = ssh.exec_command('tail -30 /tmp/openclaw-final.log 2>/dev/null | tail -15')
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

ssh.close()
