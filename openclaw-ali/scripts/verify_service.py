#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证OpenClaw服务状态"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def verify_service():
    print("="*70)
    print(" 验证OpenClaw服务状态")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查Gateway进程
        print("[1] Gateway进程...")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'openclaw.*gateway' | grep -v grep")
        process = stdout.read().decode().strip()
        if process:
            print(f"  ✅ {process[:100]}...")
        else:
            print("  ❌ 未找到进程")
        print()

        # 2. 检查监听端口
        print("[2] 监听端口 (18789, 18730)...")
        stdin, stdout, stderr = ssh.exec_command(
            "ss -tlnp 2>/dev/null | grep -E '18789|18730' || "
            "netstat -tlnp 2>/dev/null | grep -E '18789|18730' || "
            "echo '未找到监听端口'"
        )
        ports = stdout.read().decode().strip()
        print(ports)
        print()

        # 3. 检查模型配置
        print("[3] 当前模型配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json | grep -A 2 'primary'"
        )
        model = stdout.read().decode().strip()
        print(model)
        print()

        # 4. 测试Web UI
        print("[4] 测试Web UI...")
        stdin, stdout, stderr = ssh.exec_command(
            "curl -s -o /dev/null -w '%{http_code}' http://localhost:18789 || echo '连接失败'"
        )
        web_status = stdout.read().decode().strip()
        if web_status == "200" or web_status.startswith("3"):
            print(f"  ✅ Web UI可访问 (HTTP {web_status})")
        else:
            print(f"  ⚠️ Web UI状态: {web_status}")
        print()

        # 5. 查看最新日志
        print("[5] Gateway最新日志...")
        stdin, stdout, stderr = ssh.exec_command(
            "tail -30 /root/.openclaw/logs/gateway.log 2>/dev/null | grep -v '^[│╰╭]' | tail -10"
        )
        logs = stdout.read().decode().strip()
        if logs:
            for line in logs.split('\n'):
                print(f"  {line}")
        else:
            print("  无日志")
        print()

        # 6. 测试GLM-4-Flash API
        print("[6] 测试GLM-4-Flash API...")
        test_script = '''
python3 << 'PYEOF'
import requests

api_key = "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"
url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
data = {
    "model": "glm-4-flash",
    "messages": [{"role": "user", "content": "测试"}]
}

try:
    r = requests.post(url, headers=headers, json=data, timeout=10)
    if r.status_code == 200:
        result = r.json()
        print("  ✅ API测试成功")
        print(f"  回复: {result['choices'][0]['message']['content'][:50]}...")
    else:
        print(f"  ❌ API错误: {r.status_code}")
except Exception as e:
    print(f"  ❌ 连接失败: {e}")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(test_script)
        print(stdout.read().decode().strip())
        print()

        ssh.close()

        print("="*70)
        print(" 验证完成")
        print("="*70)
        print()
        print("访问地址：")
        print("  http://157.245.195.58:18789")
        print("  http://157.245.195.58:3000 (如果有nginx反向代理)")
        print()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verify_service()
