#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新OpenClaw使用glm-4-flash模型"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def update_model():
    print("="*70)
    print(" 更新OpenClaw模型配置")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 备份当前配置
        print("[1] 备份当前配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cp /root/.openclaw/agents/main/agent/agent.json "
            "/root/.openclaw/agents/main/agent/agent.json.bak"
        )
        stdout.read()
        print("  ✅ 已备份")
        print()

        # 2. 更新模型配置
        print("[2] 更新模型为 glm-4-flash...")
        update_script = '''
python3 << 'PYEOF'
import json

# 更新 main agent
agent_file = "/root/.openclaw/agents/main/agent/agent.json"
with open(agent_file, 'r') as f:
    config = json.load(f)

# 修改主模型
if 'model' in config:
    if isinstance(config['model'], dict):
        config['model']['primary'] = 'zai/glm-4-flash'
    else:
        config['model'] = {'primary': 'zai/glm-4-flash'}

# 保存
with open(agent_file, 'w') as f:
    json.dump(config, f, indent=2)

print("  ✅ 已更新 main agent")

# 更新 wangcai agent
agent_file = "/root/.openclaw/agents/wangcai/agent/agent.json"
if __import__('os').path.exists(agent_file):
    with open(agent_file, 'r') as f:
        config = json.load(f)

    if 'model' in config:
        if isinstance(config['model'], dict):
            config['model']['primary'] = 'zai/glm-4-flash'
        else:
            config['model'] = {'primary': 'zai/glm-4-flash'}

    with open(agent_file, 'w') as f:
        json.dump(config, f, indent=2)

    print("  ✅ 已更新 wangcai agent")

# 更新 openclaw.json 中的模型配置
openclaw_file = "/root/.openclaw/openclaw.json"
with open(openclaw_file, 'r') as f:
    config = json.load(f)

# 确保glm-4-flash在模型列表中
if 'models' in config and 'providers' in config['models']:
    if 'zai' in config['models']['providers']:
        models = config['models']['providers']['zai']['models']
        # 检查是否已有glm-4-flash
        has_flash = any(m.get('id') == 'glm-4-flash' for m in models)
        if not has_flash:
            models.append({
                "id": "glm-4-flash",
                "name": "GLM-4-Flash",
                "api": "openai-completions"
            })

with open(openclaw_file, 'w') as f:
    json.dump(config, f, indent=2)

print("  ✅ 已更新 openclaw.json")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(update_script)
        print(stdout.read().decode().strip())
        print()

        # 3. 验证配置
        print("[3] 验证新配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json | grep -A 3 'primary\\|model'"
        )
        new_config = stdout.read().decode().strip()
        print(new_config)
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

        # 5. 测试新模型
        print("[5] 测试新模型...")
        test_script = '''
python3 << 'PYEOF'
import requests

api_key = "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"
url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
data = {"model": "glm-4-flash", "messages": [{"role": "user", "content": "你好"}]}

try:
    r = requests.post(url, headers=headers, json=data, timeout=10)
    if r.status_code == 200:
        print("  ✅ glm-4-flash 模型测试成功！")
    else:
        print(f"  ❌ 测试失败: {r.status_code}")
except Exception as e:
    print(f"  ❌ 连接失败: {e}")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(test_script)
        print(stdout.read().decode().strip())
        print()

        ssh.close()

        print("="*70)
        print(" 更新完成！")
        print("="*70)
        print()
        print("测试方式：")
        print("  1. 网页: http://157.245.195.58:3000")
        print("  2. Telegram: 发送消息给机器人")
        print()
        print("如果还有问题，查看日志：")
        print("  tail -f /root/.openclaw/logs/gateway.log")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    update_model()
