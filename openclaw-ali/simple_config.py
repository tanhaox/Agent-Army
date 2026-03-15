#!/usr/bin/env python3
"""
从成功的 DigitalOcean 复制配置
"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

aliyun = paramiko.SSHClient()
aliyun.set_missing_host_key_policy(paramiko.AutoAddPolicy())
aliyun.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print('=' * 60)
print('  从 DigitalOcean 复制配置到阿里云')
print('=' * 60)

# DigitalOcean 服务器信息
DO_HOST = '157.245.195.58'
DO_PASSWORD = 'your-digitalocean-password'  # 需要用户提供

print('\n⚠️  需要连接到 DigitalOcean 服务器')
print('请提供 DigitalOcean 的 root 密码，或者按 Ctrl+C 取消')
# do_pass = input('DigitalOcean root 密码: ')

# 先清理阿里云
print('\n[1] 清理阿里云环境...')
stdin, stdout, stderr = aliyun.exec_command('pkill -9 -f openclaw && rm -rf /root/.openclaw')
stdout.read()
time.sleep(2)
print('✓ 已清理')

# 创建基础目录
print('\n[2] 创建目录...')
stdin, stdout, stderr = aliyun.exec_command('mkdir -p /root/.openclaw/agents/main/agent')
stdout.read()
print('✓ 目录已创建')

# 手动创建最简配置（避免JSON问题）
print('\n[3] 创建配置文件...')

# 使用printf避免引号问题
config_commands = [
    'cat > /root/.openclaw/openclaw.json << \'OEOF\'',
    '{',
    '  "gateway": {',
    '    "bind": "lan",',
    '    "auth": {',
    '      "mode": "token",',
    '      "token": "openclaw123"',
    '    }',
    '  }',
    '}',
    'OEOF',
    '',
    'cat > /root/.openclaw/agents/main/agent/agent.json << \'OEOF\'',
    '{',
    '  "model": "zai/glm-4.7",',
    '  "reasoning": true',
    '}',
    'OEOF',
    '',
    'cat > /root/.openclaw/agents/main/agent/auth-profiles.json << \'OEOF\'',
    '{',
    '  "version": 1,',
    '  "profiles": {',
    '    "zai:default": {',
    '      "type": "api_key",',
    '      "provider": "zai",',
    '      "key": "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"',
    '    }',
    '  },',
    '  "lastGood": {',
    '    "zai": "zai:default"',
    '  }',
    '}',
    'OEOF',
]

cmd = '\n'.join(config_commands)
stdin, stdout, stderr = aliyun.exec_command(cmd, get_pty=True)
time.sleep(3)

print('✓ 配置已创建')

# 验证
print('\n[4] 验证配置...')
stdin, stdout, stderr = aliyun.exec_command('cat /root/.openclaw/openclaw.json')
config = stdout.read().decode('utf-8', errors='ignore')
print('openclaw.json:')
print(config)

# 启动
print('\n[5] 启动 Gateway...')
stdin, stdout, stderr = aliyun.exec_command('OPENCLAW_NO_RESPAWN=1 openclaw gateway >/tmp/openclaw.log 2>&1 &')
time.sleep(5)

# 检查
print('\n[6] 检查状态...')
stdin, stdout, stderr = aliyun.exec_command('ps aux | grep [o]penclaw | head -2')
status = stdout.read().decode('utf-8', errors='ignore')
print(status)

print('\n检查端口...')
stdin, stdout, stderr = aliyun.exec_command('ss -tlnp | grep 18789')
port = stdout.read().decode('utf-8', errors='ignore')
print(port)

if '18789' in port:
    print('\n✓✓✓ 成功！')
    print('\n访问: https://112.126.61.223/#token=openclaw123')
else:
    print('\n查看日志...')
    stdin, stdout, stderr = aliyun.exec_command('tail -30 /tmp/openclaw.log 2>/dev/null')
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

aliyun.close()
