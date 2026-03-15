#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新OpenClaw API Key"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def update_api_key(new_key=None):
    """更新API Key"""
    print("="*70)
    print(" 更新OpenClaw API Key")
    print("="*70)
    print()

    if not new_key:
        print("请提供新的API Key")
        print()
        print("如何获取智谱AI API Key：")
        print("1. 登录: https://open.bigmodel.cn/")
        print("2. 进入控制台 → API Keys")
        print("3. 复制API Key（格式：xxxxxxxx.xxxxxxxx）")
        print()
        print("或者检查账户状态：")
        print("- 查看是否有余额/套餐")
        print("- 检查API Key是否过期")
        print("- 确认包月套餐状态")
        return

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        print(f"[1] 更新API Key: {new_key[:20]}...")

        # 更新main agent
        update_script = f'''
python3 << 'PYEOF'
import json

# 更新main agent
auth_file = "/root/.openclaw/agents/main/agent/auth-profiles.json"
with open(auth_file, 'r') as f:
    data = json.load(f)

data['profiles']['zai']['key'] = '{new_key}'
data['profiles']['zai:default']['key'] = '{new_key}'

with open(auth_file, 'w') as f:
    json.dump(data, f, indent=2)

print("✅ 已更新 main agent")

# 更新wangcai agent
auth_file = "/root/.openclaw/agents/wangcai/agent/auth-profiles.json"
with open(auth_file, 'r') as f:
    data = json.load(f)

data['profiles']['zai']['key'] = '{new_key}'
data['profiles']['zai:default']['key'] = '{new_key}'

with open(auth_file, 'w') as f:
    json.dump(data, f, indent=2)

print("✅ 已更新 wangcai agent")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(update_script)
        print(stdout.read().decode().strip())

        # 测试新Key
        print()
        print("[2] 测试新API Key...")
        test_script = f'''
python3 << 'PYEOF'
import requests
import json

api_key = "{new_key}"
url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
headers = {{
    "Authorization": f"Bearer {{api_key}}",
    "Content-Type": "application/json"
}}

data = {{
    "model": "glm-4",
    "messages": [{{"role": "user", "content": "你好"}}]
}}

try:
    response = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"状态码: {{response.status_code}}")

    if response.status_code == 200:
        print("✅ API Key有效！")
        result = response.json()
        print(f"回复: {{result['choices'][0]['message']['content'][:50]}}...")
    else:
        print(f"❌ 错误: {{response.text[:200]}}")
except Exception as e:
    print(f"❌ 连接失败: {{e}}")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(test_script)
        print(stdout.read().decode().strip())

        # 重启Gateway
        print()
        print("[3] 重启Gateway...")
        stdin, stdout, stderr = ssh.exec_command(
            "pkill -f openclaw-gateway && sleep 2 && nohup openclaw-gateway > /dev/null 2>&1 &"
        )
        stdout.read()
        print("✅ Gateway已重启")

        print()
        print("="*70)
        print(" 更新完成！")
        print("="*70)
        print()
        print("测试方式：")
        print("1. 访问: http://157.245.195.58:3000")
        print("2. 发送消息测试")

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        update_api_key(sys.argv[1])
    else:
        update_api_key()
