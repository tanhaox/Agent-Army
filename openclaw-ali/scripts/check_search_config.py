#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw的搜索和聊天配置"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_search_config():
    print("="*70)
    print(" 检查OpenClaw搜索和聊天配置")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查main agent配置
        print("[1] Main Agent配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json | grep -A 10 'model\\|search'"
        )
        config = stdout.read().decode().strip()
        print(config)
        print()

        # 2. 检查技能配置
        print("[2] 检查技能配置（web-search等）...")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw/agents/main/skills -name '*.json' -exec echo '=== {} ===' \\; -exec cat {} \\; 2>/dev/null | head -100"
        )
        skills = stdout.read().decode().strip()
        print(skills)
        print()

        # 3. 检查模型配置
        print("[3] 模型提供商配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/openclaw.json | python3 -m json.tool | grep -A 20 'zai\\|search'"
        )
        models = stdout.read().decode().strip()
        print(models)
        print()

        # 4. 测试两个Key
        print("[4] 测试两个API Key...")
        print()
        print("Key 1: e1797666...joophCPu5vL6oV0d")
        test_key1 = '''
python3 << 'PYEOF'
import requests

api_key = "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"
url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
data = {"model": "glm-4", "messages": [{"role": "user", "content": "你好"}]}

try:
    r = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"  状态: {r.status_code}")
    if r.status_code == 200:
        print("  ✅ 有效（AI聊天Key）")
    else:
        print(f"  ❌ {r.json()['error']['message'][:50]}")
except Exception as e:
    print(f"  ❌ {e}")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(test_key1)
        print(stdout.read().decode().strip())

        print()
        print("Key 2: 0676666...Ezhq90VT2DtJXI4M")
        test_key2 = '''
python3 << 'PYEOF'
import requests

api_key = "067666757b474d2d9cc9f5f59efb178d.Ezhq90VT2DtJXI4M"
url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
data = {"model": "glm-4", "messages": [{"role": "user", "content": "你好"}]}

try:
    r = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"  状态: {r.status_code}")
    if r.status_code == 200:
        print("  ✅ 有效（搜索Key？）")
    else:
        print(f"  ❌ {r.json()['error']['message'][:50]}")
except Exception as e:
    print(f"  ❌ {e}")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(test_key2)
        print(stdout.read().decode().strip())

        print()
        print("="*70)
        print(" 请告诉我：")
        print("  1. 哪个是AI聊天Key？（用于对话）")
        print("  2. 哪个是搜索专用Key？（用于web-search）")
        print("="*70)

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_search_config()
