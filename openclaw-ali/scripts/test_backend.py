#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""后台发送消息测试"""
import paramiko
import sys
import time
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def test_backend_message():
    print("="*70)
    print(" 后台发送消息测试")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 准备测试脚本
        print("[1] 准备测试脚本...")
        test_script = '''
cat > /tmp/test_openclaw.py << 'PYEOF'
import requests
import json
import time

# OpenClaw Gateway地址
BASE_URL = "http://localhost:18789"

print("测试1: 获取Agent列表")
try:
    r = requests.get(f"{BASE_URL}/api/agents", timeout=5)
    print(f"状态: {r.status_code}")
    if r.status_code == 200:
        agents = r.json()
        print(f"Agents: {json.dumps(agents, indent=2)}")
    else:
        print(f"响应: {r.text[:200]}")
except Exception as e:
    print(f"错误: {e}")

print("\n测试2: 发送消息到Agent")
# 使用正确的API端点
message_data = {
    "message": "你好",
    "userId": "test-user-123",
    "agentId": "main"  # 指定agent
}

try:
    r = requests.post(
        f"{BASE_URL}/api/message",
        json=message_data,
        timeout=30
    )
    print(f"状态: {r.status_code}")
    print(f"响应头: {dict(r.headers)}")
    print(f"响应体: {r.text[:500]}")

    if r.status_code == 200:
        result = r.json()
        print(f"\n✅ 成功")
        print(f"回复: {json.dumps(result, ensure_ascii=False, indent=2)[:300]}")
    else:
        print(f"\n❌ 失败")

except Exception as e:
    print(f"❌ 错误: {e}")

# 测试WebSocket连接
print("\n测试3: WebSocket连接")
try:
    import websocket
    ws_url = "ws://localhost:18789/ws"
    ws = websocket.create_connection(ws_url, timeout=5)
    print(f"✅ WebSocket连接成功")

    # 发送消息
    ws.send(json.dumps({
        "type": "message",
        "message": "测试",
        "userId": "test"
    }))

    # 接收响应
    result = ws.recv()
    print(f"响应: {result[:200]}")
    ws.close()

except ImportError:
    print("⚠️ websocket-client未安装")
except Exception as e:
    print(f"❌ WebSocket错误: {e}")

PYEOF

python3 /tmp/test_openclaw.py
'''
        stdin, stdout, stderr = ssh.exec_command(test_script)
        output = stdout.read().decode().strip()
        print(output)
        print()

        # 2. 查看Gateway实时日志
        print("[2] Gateway最新日志...")
        time.sleep(2)
        stdin, stdout, stderr = ssh.exec_command(
            "tail -30 /root/.openclaw/logs/gateway.log 2>/dev/null | grep -v '^[│╰╭]'"
        )
        logs = stdout.read().decode().strip()
        if logs:
            for line in logs.split('\n')[-15:]:
                if line.strip():
                    print(f"  {line[:150]}")
        else:
            print("  无日志")
        print()

        # 3. 检查最近的会话文件
        print("[3] 查看最近的会话...")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -lt /root/.openclaw/agents/main/sessions/*.jsonl 2>/dev/null | head -1 | awk '{print $NF}'"
        )
        session_file = stdout.read().decode().strip()

        if session_file:
            print(f"  会话文件: {session_file}")
            stdin, stdout, stderr = ssh.exec_command(f"tail -5 {session_file}")
            recent = stdout.read().decode().strip()
            if recent:
                print("  最新记录:")
                for line in recent.split('\n'):
                    if 'error' in line.lower() or 'rate' in line.lower():
                        print(f"    {line[:200]}")
        print()

        # 4. 直接curl测试
        print("[4] 直接curl测试...")
        curl_test = '''
curl -v -X POST http://localhost:18789/api/message \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","userId":"curl-test","agentId":"main"}' \
  2>&1 | tail -20
'''
        stdin, stdout, stderr = ssh.exec_command(curl_test)
        curl_output = stdout.read().decode().strip()
        print(curl_output)
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_backend_message()
