#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完全重启服务器和OpenClaw"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def full_restart():
    print("="*70)
    print(" 完全重启OpenClaw")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 停止所有OpenClaw进程
        print("[1] 停止所有OpenClaw进程...")
        stdin, stdout, stderr = ssh.exec_command("pkill -9 -f openclaw")
        stdout.read()
        time.sleep(2)
        print("  ✅ 已停止")
        print()

        # 2. 清理所有日志
        print("[2] 清理日志...")
        stdin, stdout, stderr = ssh.exec_command(
            "truncate -s 0 /root/.openclaw/logs/*.log 2>/dev/null || true"
        )
        stdout.read()
        print("  ✅ 已清理")
        print()

        # 3. 验证配置文件
        print("[3] 验证配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json | python3 -m json.tool | grep -A 5 'primary\\|models'"
        )
        config = stdout.read().decode().strip()
        print(config)
        print()

        # 4. 启动OpenClaw Gateway
        print("[4] 启动OpenClaw Gateway...")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/.openclaw && nohup openclaw gateway start > logs/gateway.log 2>&1 &"
        )
        stdout.read()
        time.sleep(8)
        print("  已启动")
        print()

        # 5. 验证进程
        print("[5] 验证进程状态...")
        stdin, stdout, stderr = ssh.exec_command(
            "ps aux | grep -E 'openclaw|node.*gateway' | grep -v grep"
        )
        processes = stdout.read().decode().strip()
        if processes:
            for line in processes.split('\n')[:2]:
                print(f"  {line[:100]}")
        else:
            print("  ❌ 未找到进程")
            # 查看错误
            stdin, stdout, stderr = ssh.exec_command("tail -20 /root/.openclaw/logs/gateway.log")
            error = stdout.read().decode().strip()
            if error:
                print(f"\n  错误日志:\n{error[:500]}")
        print()

        # 6. 检查端口
        print("[6] 检查端口...")
        stdin, stdout, stderr = ssh.exec_command(
            "ss -tlnp 2>/dev/null | grep 18789 || echo '  未监听'"
        )
        port = stdout.read().decode().strip()
        print(port)
        print()

        # 7. 测试Web UI
        print("[7] 测试Web UI...")
        stdin, stdout, stderr = ssh.exec_command(
            "curl -s -o /dev/null -w '%{http_code}' http://localhost:18789"
        )
        status = stdout.read().decode().strip()
        if status == "200":
            print(f"  ✅ 可访问 (HTTP {status})")
        else:
            print(f"  ⚠️ 状态: {status}")
        print()

        # 8. 测试API
        print("[8] 测试GLM-4.7 API...")
        test_script = '''
python3 << 'PYEOF'
import requests

api_key = "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"
url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
data = {"model": "glm-4.7", "messages": [{"role": "user", "content": "测试"}]}

try:
    r = requests.post(url, headers=headers, json=data, timeout=10)
    if r.status_code == 200:
        result = r.json()
        print("  ✅ GLM-4.7 API测试成功")
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

        # 9. 查看启动日志
        print("[9] Gateway启动日志（最后10行）:")
        stdin, stdout, stderr = ssh.exec_command(
            "tail -10 /root/.openclaw/logs/gateway.log 2>/dev/null | grep -v '^[│╰╭]' || echo '  无日志'"
        )
        logs = stdout.read().decode().strip()
        for line in logs.split('\n'):
            if line.strip():
                print(f"  {line[:150]}")
        print()

        ssh.close()

        print("="*70)
        print(" 重启完成")
        print("="*70)
        print()
        print("访问地址:")
        print("  http://157.245.195.58:18789")
        print()
        print("Telegram:")
        print("  发送新消息测试（不要回复旧消息）")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    full_restart()
