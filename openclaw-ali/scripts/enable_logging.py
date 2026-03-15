#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启用详细日志并重启"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def enable_verbose_logging():
    print("="*70)
    print(" 启用详细日志并重启")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查日志配置
        print("[1] 检查日志配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/openclaw.json | python3 -m json.tool | grep -A 10 'logging\\|logs'"
        )
        log_config = stdout.read().decode().strip()
        print(log_config)
        print()

        # 2. 添加详细日志配置
        print("[2] 启用详细日志...")
        update_script = '''
python3 << 'PYEOF'
import json

config_file = "/root/.openclaw/openclaw.json"
with open(config_file, 'r') as f:
    config = json.load(f)

# 启用详细日志
config['logging'] = {
    "level": "debug",
    "file": "/root/.openclaw/logs/gateway.log",
    "console": True
}

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("  ✅ 已启用详细日志")
PYEOF
'''
        stdin, stdout, stderr = ssh.exec_command(update_script)
        print(stdout.read().decode().strip())
        print()

        # 3. 停止Gateway
        print("[3] 停止Gateway...")
        stdin, stdout, stderr = ssh.exec_command("pkill -9 -f openclaw-gateway")
        stdout.read()
        time.sleep(2)
        print("  已停止")
        print()

        # 4. 清空日志文件
        print("[4] 清空日志文件...")
        stdin, stdout, stderr = ssh.exec_command(
            "truncate -s 0 /root/.openclaw/logs/gateway.log 2>/dev/null || "
            "echo '' > /root/.openclaw/logs/gateway.log"
        )
        stdout.read()
        print("  已清空")
        print()

        # 5. 启动Gateway（前台运行以查看输出）
        print("[5] 启动Gateway...")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/.openclaw && nohup openclaw-gateway > /root/.openclaw/logs/gateway.log 2>&1 &"
        )
        stdout.read()
        time.sleep(5)
        print("  已启动")
        print()

        # 6. 查看启动日志
        print("[6] 启动日志...")
        stdin, stdout, stderr = ssh.exec_command(
            "tail -50 /root/.openclaw/logs/gateway.log"
        )
        startup_log = stdout.read().decode().strip()
        print(startup_log if startup_log else "  无日志")
        print()

        # 7. 验证进程
        print("[7] 验证进程...")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep openclaw-gateway | grep -v grep")
        process = stdout.read().decode().strip()
        if process:
            print(f"  ✅ {process[:80]}")
        else:
            print("  ❌ 未运行")
        print()

        ssh.close()

        print("="*70)
        print(" 日志已启用")
        print("="*70)
        print()
        print("现在：")
        print("  1. 在Telegram发送消息测试")
        print("  2. 运行: python check_telegram.py 查看日志")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    enable_verbose_logging()
