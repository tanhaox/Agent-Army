#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试另一个API Key"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def test_alternative_key():
    print("="*70)
    print(" 测试另一个API Key")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        print("[1] 测试第二个API Key...")
        test_script = '''
python3 << 'PYEOF'
import requests
import json

# 第二个API Key
api_key = "067666757b474d2d9cc9f5f59efb178d.Ezhq90VT2DtJXI4M"

url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "glm-4",
    "messages": [{"role": "user", "content": "你好"}]
}

try:
    response = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        print("✅ API Key有效！")
        result = response.json()
        print(f"回复: {result['choices'][0]['message']['content']}")
    else:
        print(f"❌ 错误: {response.text[:200]}")
except Exception as e:
    print(f"❌ 连接失败: {e}")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(test_script)
        result = stdout.read().decode().strip()
        print(result)

        # 如果第二个Key有效，询问是否更新
        if "✅ API Key有效" in result:
            print()
            print("="*70)
            confirm = input("第二个Key有效，是否更新OpenClaw配置？(y/n): ").strip().lower()

            if confirm == 'y':
                print()
                print("[2] 更新配置...")
                update_script = '''
python3 << 'PYEOF'
import json

new_key = "067666757b474d2d9cc9f5f59efb178d.Ezhq90VT2DtJXI4M"

# 更新main agent
auth_file = "/root/.openclaw/agents/main/agent/auth-profiles.json"
with open(auth_file, 'r') as f:
    data = json.load(f)

data['profiles']['zai']['key'] = new_key
data['profiles']['zai:default']['key'] = new_key

with open(auth_file, 'w') as f:
    json.dump(data, f, indent=2)

print("✅ 已更新 main agent")

# 更新wangcai agent
auth_file = "/root/.openclaw/agents/wangcai/agent/auth-profiles.json"
with open(auth_file, 'r') as f:
    data = json.load(f)

data['profiles']['zai']['key'] = new_key
data['profiles']['zai:default']['key'] = new_key

with open(auth_file, 'w') as f:
    json.dump(data, f, indent=2)

print("✅ 已更新 wangcai agent")
PYEOF
'''
                stdin, stdout, stderr = ssh.exec_command(update_script)
                print(stdout.read().decode().strip())

                print()
                print("[3] 重启Gateway...")
                stdin, stdout, stderr = ssh.exec_command(
                    "pkill -f openclaw-gateway && sleep 2 && nohup openclaw-gateway > /dev/null 2>&1 &"
                )
                stdout.read()
                print("✅ Gateway已重启")
                print()
                print("🎉 完成！测试: http://157.245.195.58:3000")

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_alternative_key()
