#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试并更新到glm-4.7模型"""
import requests
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def test_and_update_glm47():
    print("="*70)
    print(" 测试并更新到GLM-4.7模型")
    print("="*70)
    print()

    # 1. 本地测试glm-4.7
    print("[1] 本地测试GLM-4.7模型...")
    api_key = "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"
    url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "glm-4.7",
        "messages": [{"role": "user", "content": "你好"}]
    }

    try:
        r = requests.post(url, headers=headers, json=data, timeout=15)
        print(f"  状态码: {r.status_code}")

        if r.status_code == 200:
            result = r.json()
            print("  ✅ GLM-4.7模型可用！")
            print(f"  回复: {result['choices'][0]['message']['content'][:80]}...")
        else:
            result = r.json()
            print(f"  ❌ 失败: {result['error']['message']}")
            print("\n  尝试 glm-4.7-reasoning...")
            data['model'] = 'glm-4.7-reasoning'
            r2 = requests.post(url, headers=headers, json=data, timeout=15)
            if r2.status_code == 200:
                print("  ✅ glm-4.7-reasoning 可用！")
            else:
                print(f"  ❌ 也失败: {r2.json()['error']['message']}")
                return

    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return

    print()

    # 2. 更新服务器配置
    print("[2] 更新OpenClaw配置...")
    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        update_script = '''
python3 << 'PYEOF'
import json

# 更新 main agent
agent_file = "/root/.openclaw/agents/main/agent/agent.json"
with open(agent_file, 'r') as f:
    config = json.load(f)

# 修改主模型为 glm-4.7
if 'model' in config:
    if isinstance(config['model'], dict):
        config['model']['primary'] = 'zai/glm-4.7'
    else:
        config['model'] = {'primary': 'zai/glm-4.7'}

with open(agent_file, 'w') as f:
    json.dump(config, f, indent=2)

print("  ✅ 已更新 main agent")

# 更新 wangcai agent
agent_file = "/root/.openclaw/agents/wangcai/agent/agent.json"
import os
if os.path.exists(agent_file):
    with open(agent_file, 'r') as f:
        config = json.load(f)

    if 'model' in config:
        if isinstance(config['model'], dict):
            config['model']['primary'] = 'zai/glm-4.7'
        else:
            config['model'] = {'primary': 'zai/glm-4.7'}

    with open(agent_file, 'w') as f:
        json.dump(config, f, indent=2)

    print("  ✅ 已更新 wangcai agent")

# 更新 openclaw.json 中的模型配置
openclaw_file = "/root/.openclaw/openclaw.json"
with open(openclaw_file, 'r') as f:
    config = json.load(f)

# 确保glm-4.7在模型列表中
if 'models' in config and 'providers' in config['models']:
    if 'zai' in config['models']['providers']:
        models = config['models']['providers']['zai']['models']
        has_47 = any(m.get('id') == 'glm-4.7' for m in models)
        if not has_47:
            models.append({
                "id": "glm-4.7",
                "name": "GLM-4.7",
                "api": "openai-completions",
                "reasoning": True
            })
            print("  ✅ 已添加 glm-4.7 到模型列表")

with open(openclaw_file, 'w') as f:
    json.dump(config, f, indent=2)

PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(update_script)
        print(stdout.read().decode().strip())
        print()

        # 3. 验证配置
        print("[3] 验证配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json | grep -A 2 'primary'"
        )
        print(stdout.read().decode().strip())
        print()

        # 4. 重启Gateway
        print("[4] 重启Gateway...")
        stdin, stdout, stderr = ssh.exec_command("pkill -f openclaw-gateway")
        stdout.read()
        time.sleep(2)

        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/.openclaw && nohup openclaw-gateway > /dev/null 2>&1 &"
        )
        stdout.read()
        time.sleep(3)

        stdin, stdout, stderr = ssh.exec_command("ps aux | grep openclaw-gateway | grep -v grep")
        if stdout.read().decode().strip():
            print("  ✅ Gateway已重启")
        else:
            print("  ⚠️ Gateway可能未启动")
        print()

        # 5. 最终验证
        print("[5] 最终验证...")
        test_script = '''
python3 << 'PYEOF'
import requests

api_key = "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"
url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
data = {"model": "glm-4.7", "messages": [{"role": "user", "content": "你好，请简短回复"}]}

try:
    r = requests.post(url, headers=headers, json=data, timeout=10)
    if r.status_code == 200:
        result = r.json()
        print("  ✅ GLM-4.7 模型测试成功！")
        content = result['choices'][0]['message']['content']
        print(f"  回复: {content[:100]}...")
    else:
        print(f"  ❌ 测试失败: {r.status_code} - {r.text[:100]}")
except Exception as e:
    print(f"  ❌ 错误: {e}")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(test_script)
        print(stdout.read().decode().strip())

        ssh.close()

        print()
        print("="*70)
        print(" 更新完成！")
        print("="*70)
        print()
        print("测试：http://157.245.195.58:18789")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_and_update_glm47()
