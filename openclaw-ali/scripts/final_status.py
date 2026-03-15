#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终状态检查"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

print("="*70)
print(" OpenClaw最终状态检查")
print("="*70)
print()

try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)
    print("✅ 已连接服务器")
    print()

    # 检查进程
    print("[1] Gateway进程:")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'openclaw.*gateway' | grep -v grep")
    process = stdout.read().decode().strip()
    if process:
        lines = process.split('\n')[:1]
        for line in lines:
            print(f"  {line[:100]}")
    else:
        print("  ❌ 未运行")
    print()

    # 检查端口
    print("[2] 监听端口:")
    stdin, stdout, stderr = ssh.exec_command("ss -tlnp 2>/dev/null | grep 18789")
    port = stdout.read().decode().strip()
    if port:
        print(f"  ✅ {port[:100]}")
    else:
        print("  ❌ 未监听")
    print()

    # 检查Web UI
    print("[3] Web UI:")
    stdin, stdout, stderr = ssh.exec_command(
        "curl -s -o /dev/null -w '%{http_code}' http://localhost:18789"
    )
    status = stdout.read().decode().strip()
    if status == "200":
        print(f"  ✅ HTTP {status}")
    else:
        print(f"  ⚠️ HTTP {status}")
    print()

    # 检查模型配置
    print("[4] 模型配置:")
    stdin, stdout, stderr = ssh.exec_command(
        "cat /root/.openclaw/agents/main/agent/agent.json | grep -A 2 'primary'"
    )
    config = stdout.read().decode().strip()
    print(f"  {config}")
    print()

    # 测试API
    print("[5] 测试GLM-4.7 API:")
    test_script = '''python3 << 'PYEOF'
import requests

api_key = "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"
url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
data = {"model": "glm-4.7", "messages": [{"role": "user", "content": "测试"}]}

try:
    r = requests.post(url, headers=headers, json=data, timeout=10)
    if r.status_code == 200:
        result = r.json()
        print(f"  ✅ 成功: {result['choices'][0]['message']['content'][:50]}...")
    else:
        print(f"  ❌ 失败: {r.status_code}")
except Exception as e:
    print(f"  ❌ 错误: {e}")
PYEOF
'''
    stdin, stdout, stderr = ssh.exec_command(test_script)
    result = stdout.read().decode().strip()
    print(result)
    print()

    ssh.close()

    print("="*70)
    print(" 检查完成")
    print("="*70)
    print()
    print("访问地址:")
    print("  http://157.245.195.58:18789")
    print()
    print("Telegram:")
    print("  发送新消息测试")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
