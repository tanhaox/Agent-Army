#!/usr/bin/env python3
"""
清除会话并重启
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
print('  清除会话并重启')
print('=' * 60)

# 清除会话
print('\n[1] 清除旧会话...')
stdin, stdout, stderr = ssh.exec_command('rm -rf /root/.openclaw/agents/main/sessions/*')
stdout.read()
print('✓ 已清除')

# 确保 agent.json 正确
print('\n[2] 确保 agent.json 正确...')
agent_config = {"model": "zai/glm-4.7", "reasoning": True}
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/agents/main/agent/agent.json', get_pty=True)
stdin.write(json.dumps(agent_config, indent=2))
stdin.channel.shutdown_write()
print('✓ 已更新')

# 重启
print('\n[3] 重启 Gateway...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)

stdin, stdout, stderr = ssh.exec_command('openclaw gateway >/dev/null 2>&1 &')
time.sleep(5)

# 检查日志
print('\n[4] 检查日志...')
stdin, stdout, stderr = ssh.exec_command('tail -30 /tmp/openclaw/openclaw-*.log 2>/dev/null | grep -i model')
logs = stdout.read().decode('utf-8', errors='ignore')
print(logs if logs else '(没有找到模型日志)')

# 获取 token
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print('\n' + '=' * 60)
print('  完成')
print('=' * 60)
print(f'\n访问: https://112.126.61.223/#token={token}')
print('\n在浏览器控制台执行以下代码清除缓存:')
print("  localStorage.clear();")
print("  location.reload();")

ssh.close()
