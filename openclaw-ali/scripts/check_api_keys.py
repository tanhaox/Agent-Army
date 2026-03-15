#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查API Key配置"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_api_keys():
    print("="*70)
    print(" 检查API Key配置")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查所有auth-profiles配置
        print("[1] 所有Agent的API Key配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw/agents -name 'auth-profiles.json' -exec echo '=== {} ===' \\; -exec cat {} \\;"
        )
        auth_configs = stdout.read().decode().strip()
        print(auth_configs)
        print()

        # 2. 测试auth-profiles中的API Key
        print("[2] 测试实际配置的API Key...")
        test_actual = '''
python3 << 'PYEOF'
import requests
import json

# 实际配置的API Key
api_key = "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"

url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "glm-4",
    "messages": [{"role": "user", "content": "测试"}]
}

try:
    response = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"状态码: {response.status_code}")
    result = response.json()
    if response.status_code == 200:
        print("✅ API Key有效")
        print(f"回复: {result['choices'][0]['message']['content'][:50]}...")
    else:
        print(f"❌ 错误: {json.dumps(result, ensure_ascii=False, indent=2)}")
except Exception as e:
    print(f"❌ 连接失败: {e}")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(test_actual)
        print(stdout.read().decode().strip())
        print()

        # 3. 检查智谱AI账户信息（如果API支持）
        print("[3] 检查账户余额...")
        check_balance = '''
python3 << 'PYEOF'
import requests

api_key = "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"

# 尝试获取账户信息
headers = {"Authorization": f"Bearer {api_key}"}

# GLM的账户信息接口
try:
    response = requests.get(
        "https://open.bigmodel.cn/api/paas/v4/account/info",
        headers=headers,
        timeout=10
    )
    print(f"状态码: {response.status_code}")
    print(response.text[:500])
except Exception as e:
    print(f"无法获取账户信息: {e}")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(check_balance)
        print(stdout.read().decode().strip())
        print()

        # 4. 检查Gateway日志（最近的所有日志）
        print("[4] Gateway最新日志（查看实际错误）...")
        stdin, stdout, stderr = ssh.exec_command(
            "tail -100 /root/.openclaw/logs/gateway.log"
        )
        gateway_log = stdout.read().decode().strip()
        # 只显示包含error或failed的行
        error_lines = [line for line in gateway_log.split('\n')
                      if 'error' in line.lower() or 'failed' in line.lower() or '429' in line]
        if error_lines:
            for line in error_lines[-10:]:
                print(line)
        else:
            print("  无错误日志")
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_api_keys()
