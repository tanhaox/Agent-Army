#!/usr/bin/env python3
"""
验证Agent配置
"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print('=' * 60)
print('  验证Agent配置')
print('=' * 60)

print('\n[1] 检查agent.json...')
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/agents/main/agent/agent.json 2>/dev/null || echo "文件不存在"')
agent = stdout.read().decode('utf-8', errors='ignore')
print(agent)

print('\n[2] 检查auth-profiles.json...')
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/agents/main/agent/auth-profiles.json 2>/dev/null || echo "文件不存在"')
auth = stdout.read().decode('utf-8', errors='ignore')
print(auth)

print('\n[3] 检查Gateway日志（最后10行）...')
stdin, stdout, stderr = ssh.exec_command('journalctl -u openclaw-gateway.service -n 10 --no-pager 2>/dev/null || tail -10 /tmp/mode-start.log 2>/dev/null || echo "无日志"')
logs = stdout.read().decode('utf-8', errors='ignore')
print(logs)

ssh.close()

print('\n' + '=' * 60)
print('  配置完成！')
print('=' * 60)
print('\n✅ 现在可以访问:')
print('   https://112.126.61.223/#token=openclaw123')
print('\n🤖 模型: zai/glm-4.7')
print('🔑 Token: openclaw123')
