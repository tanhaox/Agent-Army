#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单检查当前状态"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check():
    print("="*70)
    print(" 检查当前状态")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 模型配置
        print("[1] 模型配置:")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -A 2 'primary' /root/.openclaw/agents/main/agent/agent.json"
        )
        print(stdout.read().decode().strip())
        print()

        # 2. API Key
        print("[2] API Key:")
        stdin, stdout, stderr = ssh.exec_command(
            "grep 'key' /root/.openclaw/agents/main/agent/auth-profiles.json | head -1"
        )
        print(stdout.read().decode().strip())
        print()

        # 3. Gateway日志
        print("[3] Gateway日志（最后30行）:")
        stdin, stdout, stderr = ssh.exec_command(
            "tail -30 /root/.openclaw/logs/gateway.log 2>/dev/null || echo '无日志'"
        )
        logs = stdout.read().decode().strip()
        # 只显示包含error、rate、limit的行
        error_lines = []
        for line in logs.split('\n'):
            if any(word in line.lower() for word in ['error', 'rate', 'limit', '429']):
                error_lines.append(line)

        if error_lines:
            print("  错误日志:")
            for line in error_lines[-10:]:
                print(f"  {line}")
        else:
            print("  无错误日志")
            # 显示最后5行
            last_lines = logs.split('\n')[-5:]
            for line in last_lines:
                if line.strip():
                    print(f"  {line[:150]}")
        print()

        # 4. 测试API
        print("[4] 测试GLM-4.7 API:")
        test_cmd = '''curl -s -X POST "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions" \\
  -H "Authorization: Bearer e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"glm-4.7","messages":[{"role":"user","content":"你好"}]}' \\
  | python3 -c "import sys,json; r=json.load(sys.stdin); print('✅ 成功' if 'choices' in r else f'❌ {r}')"
'''
        stdin, stdout, stderr = ssh.exec_command(test_cmd)
        print("  " + stdout.read().decode().strip())
        print()

        # 5. Gateway进程
        print("[5] Gateway进程:")
        stdin, stdout, stderr = ssh.exec_command(
            "ps aux | grep 'openclaw.*gateway' | grep -v grep | wc -l"
        )
        count = stdout.read().decode().strip()
        print(f"  运行中进程数: {count}")
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == '__main__':
    check()
