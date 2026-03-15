#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw完整状态"""
import paramiko
import sys
import json
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

print("="*70)
print(" 检查OpenClaw完整状态")
print("="*70)
print()

try:
    # 连接服务器
    key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)
    print("✅ 已连接服务器")
    print()

    # 1. 检查进程
    print("[1] 进程状态:")
    stdin, stdout, stderr = ssh.exec_command(
        "ps aux | grep -E 'openclaw|gateway|node' | grep -v grep"
    )
    processes = stdout.read().decode().strip()
    if processes:
        print(f"  ✅ 找到 {len(processes.split(chr'))} 个进程")
        print(f"    PID: {fields[1]}")
        print(f"    Command: {' '.join(fields[10:15])}")
    else:
        print("  ❌ 没有运行OpenClaw进程")
    print()

    # 2. 检查端口
    print("[2] 端口监听:")
    stdin, stdout, stderr = ssh.exec_command(
        "ss -tlnp 2>/dev/null | grep 18789 || echo '端口未监听'"
    )
    ports = stdout.read().decode().strip()
    if ports:
        print(f"  ✅ {ports}")
    else:
        print("  ❌ 端口未监听")
    print()

    # 3. 检查配置
    print("[3] 模型配置:")
    stdin, stdout, stderr = ssh.exec_command(
        "cat /root/.openclaw/agents/main/agent/agent.json | python3 -c "
        "'import sys, json; c=json.load(sys.stdin); "
        "print(f\"Primary: {c.get(\\\"model\\\", {}).get(\\\"primary\\\", \\\"未设置\\\")); "
        "'"
    )
    config = json.loads(config_str)
    print(config)
    print()

    # 4. 检查日志
    print("[4] Gateway日志 (最后20行):")
    stdin, stdout, stderr = ssh.exec_command(
        "tail -20 /root/.openclaw/logs/gateway.log 2>/dev/null || echo '无日志'"
    )
    logs = stdout.read().decode().strip()
    if logs:
        print(logs)
    else:
        print("  无日志文件")
    print()

    # 5. 测试Web UI
    print("[5] 测试Web UI:")
    stdin, stdout, stderr = ssh.exec_command(
        "curl -s -o /dev/null -w '%{http_code}' http://localhost:18789"
    )
    status = stdout.read().decode().strip()
    print(f"  HTTP状态: {status}")
    print()

    # 6. 测试API
    print("[6] 测试GLM-4.7 API:")
    test_script = '''
python3 << 'PYEOF'
import requests

api_key = "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"
url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
data = {"model": "glm-4.7", "messages": [{"role": "user", "content": "你好"}]}

try:
    r = requests.post(url, headers=headers, json=data, timeout=10)
    if r.status_code == 200:
        result = r.json()
        print(f"  ✅ 成功")
        print(f"  回复: {result['choices'][0]['message']['content'][:50]}...")
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
    print("  网页: http://157.245.195.58:18789")
    print()
    print("Telegram:")
    print("  发送新消息测试")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
