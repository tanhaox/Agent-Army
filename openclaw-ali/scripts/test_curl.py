#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用curl测试智谱AI API"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def test_with_curl():
    print("="*70)
    print(" 用curl测试智谱AI API")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        print("[1] 测试API Key 1 (e1797666...joophCPu5vL6oV0d)...")
        cmd1 = '''curl -s -X POST "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions" \\
  -H "Authorization: Bearer e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"glm-4","messages":[{"role":"user","content":"你好"}]}' '''
        stdin, stdout, stderr = ssh.exec_command(cmd1)
        result1 = stdout.read().decode().strip()
        print(result1[:500])
        print()

        print("[2] 测试API Key 2 (0676666...Ezhq90VT2DtJXI4M)...")
        cmd2 = '''curl -s -X POST "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions" \\
  -H "Authorization: Bearer 067666757b474d2d9cc9f5f59efb178d.Ezhq90VT2DtJXI4M" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"glm-4","messages":[{"role":"user","content":"你好"}]}' '''
        stdin, stdout, stderr = ssh.exec_command(cmd2)
        result2 = stdout.read().decode().strip()
        print(result2[:500])
        print()

        print("[3] 检查HTTP状态码...")
        cmd3 = '''curl -s -o /dev/null -w "HTTP状态码: %{http_code}\\n" -X POST "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions" \\
  -H "Authorization: Bearer e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"glm-4","messages":[{"role":"user","content":"测试"}]}' '''
        stdin, stdout, stderr = ssh.exec_command(cmd3)
        print(stdout.read().decode().strip())
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == '__main__':
    test_with_curl()
