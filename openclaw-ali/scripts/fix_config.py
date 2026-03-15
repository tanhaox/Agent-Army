#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复OpenClaw配置"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def fix_config():
    print("="*70)
    print(" 修复OpenClaw配置")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 移除错误的logging配置
        print("[1] 移除错误的logging配置...")
        fix_script = '''
python3 << 'PYEOF'
import json

config_file = "/root/.openclaw/openclaw.json"
with open(config_file, 'r') as f:
    config = json.load(f)

# 移除错误的logging配置
if 'logging' in config:
    del config['logging']
    print("  ✅ 已移除错误的logging配置")

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("  ✅ 配置已修复")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(fix_script)
        print(stdout.read().decode().strip())
        print()

        # 2. 验证配置
        print("[2] 验证配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/openclaw.json | python3 -m json.tool | grep -A 3 logging || echo '  logging配置已移除'"
        )
        result = stdout.read().decode().strip()
        print(result)
        print()

        # 3. 运行openclaw doctor
        print("[3] 运行openclaw doctor...")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/.openclaw && openclaw doctor --fix 2>&1 | tail -20"
        )
        doctor = stdout.read().decode().strip()
        print(doctor)
        print()

        # 4. 启动Gateway
        print("[4] 启动Gateway...")
        stdin, stdout, stderr = ssh.exec_command("pkill -f openclaw")
        stdout.read()
        time.sleep(2)

        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/.openclaw && nohup openclaw gateway start > logs/gateway.log 2>&1 &"
        )
        stdout.read()
        time.sleep(5)
        print("  已启动")
        print()

        # 5. 验证
        print("[5] 验证服务...")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'openclaw.*gateway' | grep -v grep")
        process = stdout.read().decode().strip()
        if process:
            print(f"  ✅ {process[:80]}")
        else:
            print("  ❌ 未运行")
            # 查看错误日志
            stdin, stdout, stderr = ssh.exec_command("tail -10 /root/.openclaw/logs/gateway.log")
            error = stdout.read().decode().strip()
            if error:
                print(f"\n  错误:\n{error}")
        print()

        # 6. 检查端口
        print("[6] 检查端口...")
        stdin, stdout, stderr = ssh.exec_command(
            "ss -tlnp 2>/dev/null | grep 18789 || echo '  未监听'"
        )
        port = stdout.read().decode().strip()
        print(port)
        print()

        ssh.close()

        print("="*70)
        print(" 修复完成")
        print("="*70)

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_config()
