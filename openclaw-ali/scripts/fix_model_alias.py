#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查和修复模型alias配置"""
import paramiko
import sys
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_model_alias():
    print("="*70)
    print(" 检查模型alias配置")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查agent.json中的models配置
        print("[1] Agent models配置:")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json | python3 -m json.tool | grep -A 10 'models'"
        )
        models = stdout.read().decode().strip()
        print(models)
        print()

        # 2. 检查openclaw.json中的模型列表
        print("[2] 可用模型列表:")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/openclaw.json | python3 -m json.tool | grep -A 5 'glm-4'"
        )
        glm4 = stdout.read().decode().strip()
        print(glm4)
        print()

        # 3. 修复：添加glm-4的alias指向glm-4.7
        print("[3] 修复模型alias...")
        fix_script = '''
python3 << 'PYEOF'
import json

# 修改agent.json
agent_file = "/root/.openclaw/agents/main/agent/agent.json"
with open(agent_file, 'r') as f:
    config = json.load(f)

# 添加models alias
if 'models' not in config:
    config['models'] = {}

# 将zai/glm-4指向zai/glm-4.7
config['models']['zai/glm-4'] = {'alias': 'zai/glm-4.7'}
config['models']['zai/glm-4.7'] = {'alias': 'GLM-4.7'}

with open(agent_file, 'w') as f:
    json.dump(config, f, indent=2)

print("  ✅ 已添加模型alias")

# 同样修改wangcai
import os
wangcai_file = "/root/.openclaw/agents/wangcai/agent/agent.json"
if os.path.exists(wangcai_file):
    with open(wangcai_file, 'r') as f:
        config = json.load(f)

    if 'models' not in config:
        config['models'] = {}

    config['models']['zai/glm-4'] = {'alias': 'zai/glm-4.7'}
    config['models']['zai/glm-4.7'] = {'alias': 'GLM-4.7'}

    with open(wangcai_file, 'w') as f:
        json.dump(config, f, indent=2)

    print("  ✅ wangcai agent已更新")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(fix_script)
        print(stdout.read().decode().strip())
        print()

        # 4. 验证配置
        print("[4] 验证新配置:")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json | python3 -m json.tool | grep -A 5 'models'"
        )
        verify = stdout.read().decode().strip()
        print(verify)
        print()

        # 5. 重启Gateway
        print("[5] 重启Gateway...")
        stdin, stdout, stderr = ssh.exec_command("pkill -f openclaw-gateway")
        stdout.read()

        import time
        time.sleep(2)

        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/.openclaw && nohup openclaw gateway start > logs/gateway.log 2>&1 &"
        )
        stdout.read()
        time.sleep(5)

        stdin, stdout, stderr = ssh.exec_command(
            "ps aux | grep 'openclaw.*gateway' | grep -v grep"
        )
        if stdout.read().decode().strip():
            print("  ✅ Gateway已重启")
        else:
            print("  ⚠️ Gateway可能未启动")
        print()

        # 6. 清理会话缓存
        print("[6] 清理旧会话缓存...")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw/agents/main/sessions -name '*.jsonl' -mtime +1 -delete 2>/dev/null && echo '  ✅ 已清理旧会话' || echo '  无需清理'"
        )
        print(stdout.read().decode().strip())
        print()

        ssh.close()

        print("="*70)
        print(" 修复完成")
        print("="*70)
        print()
        print("现在请重新测试：")
        print("  1. 在Telegram发送新消息（不要回复旧消息）")
        print("  2. 或访问: http://157.245.195.58:18789")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_model_alias()
