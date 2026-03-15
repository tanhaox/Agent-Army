#!/usr/bin/env python3
"""
使用CLI命令正确配置（让OpenClaw自己生成配置）
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
print('  使用CLI命令正确配置')
print('=' * 60)

# 1. 完全清理
print('\n[1] 清理环境...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw && rm -rf /root/.openclaw')
stdout.read()
time.sleep(2)
print('✓ 已清理')

# 2. 启动一次让OpenClaw生成默认配置
print('\n[2] 首次启动（生成默认配置）...')
stdin, stdout, stderr = ssh.exec_command('timeout 10 openclaw gateway 2>&1 || true')
time.sleep(12)
output = stdout.read().decode('utf-8', errors='ignore')
print('启动输出（前500字符）:')
print(output[:500] if len(output) > 500 else output)

# 3. 检查生成的配置文件
print('\n[3] 查看生成的配置...')
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json 2>/dev/null || echo "文件不存在"')
config = stdout.read().decode('utf-8', errors='ignore')
print('原始配置:')
print(config)

# 4. 使用openclaw config命令修改配置
print('\n[4] 使用CLI修改配置...')

# 设置bind模式为lan
print('  - 设置 gateway.bind = lan')
stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.bind lan', get_pty=True)
time.sleep(1)
result = stdout.read().decode('utf-8', errors='ignore')
print(f'    {result.strip()}')

# 设置token
print('  - 设置 gateway.auth.token = openclaw123')
stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.auth.token openclaw123', get_pty=True)
time.sleep(1)
result = stdout.read().decode('utf-8', errors='ignore')
print(f'    {result.strip()}')

# 设置trustedProxies
print('  - 设置 trustedProxies')
stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.trustedProxies \'["127.0.0.1", "::1"]\'', get_pty=True)
time.sleep(1)
result = stdout.read().decode('utf-8', errors='ignore')
print(f'    {result.strip()}')

# 5. 再次查看配置
print('\n[5] 验证修改后的配置...')
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = stdout.read().decode('utf-8', errors='ignore')
print('修改后的配置:')
print(config)

# 6. 创建agent配置
print('\n[6] 创建agent配置...')
stdin, stdout, stderr = ssh.exec_command('mkdir -p /root/.openclaw/agents/main/agent')
time.sleep(1)

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

# 使用printf避免echo的换行问题
agent_json = json.dumps(agent_config, separators=(',', ':'))
auth_json = json.dumps(auth_config, separators=(',', ':'))

stdin, stdout, stderr = ssh.exec_command(f'printf "{agent_json}" > /root/.openclaw/agents/main/agent/agent.json')
time.sleep(1)

stdin, stdout, stderr = ssh.exec_command(f'printf "{auth_json}" > /root/.openclaw/agents/main/agent/auth-profiles.json')
time.sleep(1)

print('✓ Agent配置已创建')

# 7. 启动Gateway
print('\n[7] 启动Gateway...')
stdin, stdout, stderr = ssh.exec_command('OPENCLAW_NO_RESPAWN=1 openclaw gateway >/tmp/cli-start.log 2>&1 &')
time.sleep(6)

# 8. 检查状态
print('\n[8] 检查状态...')
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
else:
    print('\n查看日志...')
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/cli-start.log')
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

ssh.close()
