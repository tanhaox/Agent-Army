#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

print("="*70)
print(" 检查OpenClaw状态")
print("="*70)

try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

    print("\n[1] 进程:")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep openclaw | grep -v grep")
    print(stdout.read().decode().strip()[:200] or "未运行")
    print()

    print("[2] 端口:")
    stdin, stdout, stderr = ssh.exec_command("ss -tlnp | grep 18789 || echo '未监听'")
    print(stdout.read().decode().strip()[:100] or "未监听")
    print()

    print("[3] Web UI:")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:18789")
    print(f"  HTTP {stdout.read().decode().strip()}")
    print()

    print("[4] 测试GLM-4.7:")
    stdin, stdout, stderr = ssh.exec_command('''
python3 -c "import requests; r=requests.post('https://open.bigmodel.cn/api/coding/paas/v4/chat/completions',
headers={'Authorization': 'Bearer e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d'},
json={'model': 'glm-4.7', 'messages': [{'role': 'user', 'content': '你好'}]},
timeout=10)
print('✅ 成功' if r.status_code == 200 else f'❌ {r.status_code}')" 2>&1
''')
    print(stdout.read().decode().strip())
    print()

    ssh.close()

    print("\n访问: http://157.245.195.58:18789")
except Exception as e:
    print(f"[ERROR] {e}")
