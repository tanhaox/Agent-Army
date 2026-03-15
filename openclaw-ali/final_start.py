#!/usr/bin/env python3
"""
最终清理并启动
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
print('  最终启动')
print('=' * 60)

# 1. 杀掉所有进程
print('\n[1] 杀掉所有openclaw进程...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(3)
print('✓ 已停止')

# 2. 停止systemd服务
print('\n[2] 停止systemd服务...')
stdin, stdout, stderr = ssh.exec_command('systemctl stop openclaw-gateway.service 2>/dev/null || true')
stdout.read()
time.sleep(2)
print('✓ 已停止')

# 3. 检查配置文件
print('\n[3] 检查配置文件...')
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = stdout.read().decode('utf-8', errors='ignore')
print('当前配置:')
print(config)

# 4. 创建agent配置
print('\n[4] 创建agent配置...')
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

agent_json = json.dumps(agent_config, separators=(',', ':'))
auth_json = json.dumps(auth_config, separators=(',', ':'))

stdin, stdout, stderr = ssh.exec_command(f'printf "{agent_json}" > /root/.openclaw/agents/main/agent/agent.json')
time.sleep(1)

stdin, stdout, stderr = ssh.exec_command(f'printf "{auth_json}" > /root/.openclaw/agents/main/agent/auth-profiles.json')
time.sleep(1)

print('✓ Agent配置已创建')

# 5. 启动Gateway
print('\n[5] 启动Gateway...')
stdin, stdout, stderr = ssh.exec_command('OPENCLAW_NO_RESPAWN=1 openclaw gateway >/tmp/final-start.log 2>&1 &')
time.sleep(8)

# 6. 检查状态
print('\n[6] 检查状态...')
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
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/final-start.log')
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

ssh.close()
