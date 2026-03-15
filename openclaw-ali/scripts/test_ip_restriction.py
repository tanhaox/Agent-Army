#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试新加坡IP访问智谱AI"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def test_ip_restriction():
    print("="*70)
    print(" 测试新加坡IP访问智谱AI")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查服务器IP
        print("[1] 服务器IP地址...")
        stdin, stdout, stderr = ssh.exec_command("curl -s ifconfig.me")
        ip = stdout.read().decode().strip()
        print(f"  IP: {ip}")
        print(f"  位置: 新加坡（DigitalOcean）")
        print()

        # 2. 测试智谱AI API（带详细错误信息）
        print("[2] 测试智谱AI API连接...")
        test_api = '''
python3 << 'PYEOF'
import requests
import json

api_key = "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"
url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

data = {
    "model": "glm-4",
    "messages": [{"role": "user", "content": "测试"}],
    "stream": False
}

print("  发送请求到智谱AI...")
try:
    r = requests.post(url, headers=headers, json=data, timeout=15)
    print(f"  状态码: {r.status_code}")
    print(f"  响应头: {dict(r.headers)}")

    if r.status_code == 200:
        print("  ✅ API连接成功")
        result = r.json()
        print(f"  回复: {result['choices'][0]['message']['content'][:50]}")
    else:
        result = r.json()
        print(f"  ❌ 错误码: {result['error']['code']}")
        print(f"  ❌ 错误信息: {result['error']['message']}")

        # 检查是否是IP限制
        if 'ip' in result['error']['message'].lower() or 'region' in result['error']['message'].lower():
            print("\n  🔴 检测到IP限制！")
            print("  新加坡IP可能被智谱AI封锁")

except requests.exceptions.Timeout:
    print("  ❌ 请求超时")
except requests.exceptions.ConnectionError as e:
    print(f"  ❌ 连接错误: {e}")
except Exception as e:
    print(f"  ❌ 其他错误: {e}")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(test_api)
        print(stdout.read().decode().strip())
        print()

        # 3. 测试DNS解析
        print("[3] 测试DNS解析...")
        stdin, stdout, stderr = ssh.exec_command("nslookup open.bigmodel.cn")
        dns = stdout.read().decode().strip()
        print(dns)
        print()

        # 4. 测试网络连通性
        print("[4] 测试网络连通性...")
        stdin, stdout, stderr = ssh.exec_command("ping -c 3 open.bigmodel.cn 2>&1 || echo 'ping失败'")
        ping = stdout.read().decode().strip()
        print(ping)
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_ip_restriction()
