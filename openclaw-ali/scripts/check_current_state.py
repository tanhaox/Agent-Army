#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看当前配置和日志"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_current_state():
    print("="*70)
    print(" 查看当前配置和日志")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 查看main agent配置
        print("[1] Main Agent模型配置:")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json | python3 -c "
            "'import sys, json; c=json.load(sys.stdin); "
            "print(\"Primary Model:\", c.get(\"model\", {}).get(\"primary\", \"未设置\"))'"
        )
        print(stdout.read().decode().strip())
        print()

        # 2. 查看API Key
        print("[2] API Key配置:")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/auth-profiles.json | python3 -c "
            "'import sys, json; c=json.load(sys.stdin); "
            "key = c.get(\"profiles\", {}).get(\"zai\", {}).get(\"key\", \"未设置\"); "
            "print(\"Key:\", key[:20] + \"...\" if len(key) > 20 else key)'"
        )
        print(stdout.read().decode().strip())
        print()

        # 3. 查看最新日志（所有内容）
        print("[3] 最新Gateway日志（最后50行）:")
        stdin, stdout, stderr = ssh.exec_command(
            "tail -50 /root/.openclaw/logs/gateway.log 2>/dev/null || echo '无日志'"
        )
        logs = stdout.read().decode().strip()
        print(logs)
        print()

        # 4. 测试GLM-4.7 API
        print("[4] 测试GLM-4.7 API连接:")
        test_script = '''
python3 << 'PYEOF'
import requests
import json

api_key = "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"
url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
data = {"model": "glm-4.7", "messages": [{"role": "user", "content": "你好"}]}

try:
    r = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"状态码: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        print(f"✅ 成功: {result['choices'][0]['message']['content'][:50]}...")
    else:
        print(f"❌ 失败: {r.text[:200]}")
except Exception as e:
    print(f"❌ 错误: {e}")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(test_script)
        print(stdout.read().decode().strip())
        print()

        # 5. 检查是否有多个Gateway进程
        print("[5] Gateway进程:")
        stdin, stdout, stderr = ssh.exec_command(
            "ps aux | grep -E 'openclaw.*gateway|node.*gateway' | grep -v grep"
        )
        processes = stdout.read().decode().strip()
        if processes:
            for line in processes.split('\n'):
                print(f"  {line[:100]}")
        else:
            print("  无运行进程")
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_current_state()
