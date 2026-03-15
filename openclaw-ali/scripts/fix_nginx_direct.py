#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接通过Python修复nginx"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def fix_nginx_direct():
    print("="*70)
    print(" 直接修复nginx配置")
    print("="*70)
    print()

    try:
        # 连接服务器
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)
        print("[1] 已连接")

        print()

        # 读取当前配置
        print("[2] 当前nginx配置:")
        stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/sites-available/openclaw.conf")
        old_config = stdout.read().decode().strip()
        print(old_config)
        print()

        # 创建新配置
        new_config = """server {
    listen 80;
    server_name openclaw;
    location /var/www/openclaw;

    root /var/log/nginx/openclaw-access.log;
    error_log /var/log/nginx/openclaw-error.log;

    location ~ / {
        proxy_pass http://localhost:18789;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
"""
        print("[3] 写入新配置...")
        stdin, stdout, stderr = ssh.exec_command(f"echo '{new_config}' > /etc/nginx/sites-available/openclaw.conf")
        stdout.read()
        stderr.read()

        if stderr.read().decode().strip():
            print(f"  ❌ 错误: {stderr.read().decode()}")
            return

        print("  ✅ 已写入")
        print()

        # 测试配置
        print("[4] 测试nginx配置...")
        stdin, stdout, stderr = ssh.exec_command("nginx -t")
        test_result = stdout.read().decode().strip()
        print(test_result)
        print()

        # 重载nginx
        print("[5] 重载nginx...")
        stdin, stdout, stderr = ssh.exec_command("systemctl reload nginx")
        stdout.read()
        stderr.read()

        if stderr.read().decode().strip():
            print(f"  ❌ 错误: {stderr.read().decode()}")
        else:
            print("  ✅ 已重载")
        print()

        # 测试访问
        print("[6] 测试访问...")
        stdin, stdout, stderr = ssh.exec_command("curl -I http://localhost:18789")
        result = stdout.read().decode().strip()
        print(result[:200] if result else "  ✅ 成功")
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_nginx_direct()
