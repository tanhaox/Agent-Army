#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重启服务器并启动OpenClaw"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def reboot_and_start():
    print("="*70)
    print(" 重启服务器并启动OpenClaw")
    print("="*70)
    print()

    try:
        # 1. 连接服务器
        print("[1] 连接服务器...")
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)
        print("  ✅ 已连接")
        print()

        # 2. 发送重启命令
        print("[2] 发送重启命令...")
        stdin, stdout, stderr = ssh.exec_command("reboot")
        stdout.read()
        print("  ✅ 服务器正在重启...")
        print()
        ssh.close()

        # 3. 等待服务器重启
        print("[3] 等待服务器重启完成（60秒）...")
        for i in range(60, 0, -1):
            print(f"\r  倒计时: {i}秒  ", end='', flush=True)
            time.sleep(1)
        print("\n")

        # 4. 等待SSH可用
        print("[4] 等待SSH服务...")
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=10)
                print(f"  ✅ SSH已恢复（尝试 {attempt + 1}/{max_attempts}）")
                break
            except:
                if attempt < max_attempts - 1:
                    print(f"\r  尝试 {attempt + 1}/{max_attempts}...", end='', flush=True)
                    time.sleep(2)
                else:
                    print("\n  ❌ SSH连接失败")
                    return
        print()
        print()

        # 5. 启动OpenClaw
        print("[5] 启动OpenClaw Gateway...")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/.openclaw && nohup openclaw gateway start > logs/gateway.log 2>&1 &"
        )
        stdout.read()
        time.sleep(8)
        print("  已启动")
        print()

        # 6. 验证进程
        print("[6] 验证进程...")
        stdin, stdout, stderr = ssh.exec_command(
            "ps aux | grep 'openclaw.*gateway' | grep -v grep"
        )
        process = stdout.read().decode().strip()
        if process:
            print(f"  ✅ {process[:80]}")
        else:
            print("  ❌ 未找到进程")
            # 查看错误日志
            stdin, stdout, stderr = ssh.exec_command("tail -20 /root/.openclaw/logs/gateway.log")
            error = stdout.read().decode().strip()
            if error:
                print(f"\n  错误日志:\n{error[:500]}")
        print()

        # 7. 检查端口
        print("[7] 检查端口...")
        time.sleep(5)
        stdin, stdout, stderr = ssh.exec_command(
            "ss -tlnp 2>/dev/null | grep 18789 || echo '  未监听'"
        )
        port = stdout.read().decode().strip()
        print(port)
        print()

        # 8. 测试Web UI
        print("[8] 测试Web UI...")
        stdin, stdout, stderr = ssh.exec_command(
            "curl -s -o /dev/null -w '%{http_code}' http://localhost:18789"
        )
        status = stdout.read().decode().strip()
        if status == "200":
            print(f"  ✅ 可访问 (HTTP {status})")
        else:
            print(f"  ⚠️ 状态: {status}")
        print()

        # 9. 验证模型配置
        print("[9] 模型配置:")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json | grep -A 5 'primary'"
        )
        config = stdout.read().decode().strip()
        print(config)
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
        print("  发送新消息测试")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    reboot_and_start()
