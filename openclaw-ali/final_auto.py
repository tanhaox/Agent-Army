#!/usr/bin/env python3
"""
最终自动化配置方案
"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

def create_fresh_ssh():
    """创建新的SSH连接"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=30, banner_timeout=30)
    return ssh

print('=' * 60)
print('  最终自动化配置')
print('=' * 60)

try:
    ssh = create_fresh_ssh()

    # 1. 清理
    print('\n[1] 清理环境...')
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

    # 3. 使用heredoc创建配置（避免引号转义问题）
    print('\n[3] 创建配置文件...')

    # openclaw.json
    openclaw_json = '''cat > /root/.openclaw/openclaw.json << 'EOF'
{
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
EOF
'''

    # agent.json
    agent_json = '''cat > /root/.openclaw/agents/main/agent/agent.json << 'EOF'
{
  "model": "zai/glm-4.7",
  "reasoning": true
}
EOF
'''

    # auth-profiles.json
    auth_json = '''cat > /root/.openclaw/agents/main/agent/auth-profiles.json << 'EOF'
{
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
EOF
'''

    # 执行配置创建
    for cmd in [openclaw_json, agent_json, auth_json]:
        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
        stdout.read()
        time.sleep(0.5)

    print('✓ 配置文件已创建')

    # 4. 验证配置
    print('\n[4] 验证配置...')
    stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json', get_pty=True)
    config = stdout.read().decode('utf-8', errors='ignore')
    print('openclaw.json:')
    print(config[:200])

    # 5. 启动Gateway
    print('\n[5] 启动 Gateway...')
    stdin, stdout, stderr = ssh.exec_command('OPENCLAW_NO_RESPAWN=1 openclaw gateway >/tmp/openclaw.log 2>&1 &', get_pty=True)
    time.sleep(6)

    # 6. 检查状态
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
        print('  ✓✓✓ 成功！Gateway 已启动')
        print('=' * 60)
        print('\n访问地址:')
        print('  HTTPS: https://112.126.61.223/#token=openclaw123')
        print('  HTTP:  http://112.126.61.223:18789/#token=openclaw123')
        print('\n模型: zai/glm-4.7')
        print('Token: openclaw123')
        print('\n现在可以在浏览器中访问并测试对话功能了！')
    else:
        print('\n查看日志...')
        stdin, stdout, stderr = ssh.exec_command('tail -40 /tmp/openclaw.log', get_pty=True)
        logs = stdout.read().decode('utf-8', errors='ignore')
        print(logs)

    ssh.close()

except Exception as e:
    print(f'\n❌ 错误: {e}')
    import traceback
    traceback.print_exc()
