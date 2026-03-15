#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复nginx配置"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def fix_nginx():
    print("="*70)
    print(" 修复nginx配置")
    print("="*70)

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 读取当前nginx配置
        print("[1] 当前配置:")
        stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/sites-available/openclaw.conf")
        config = stdout.read().decode().strip()

        if config:
            print(config)
            print()

        # 修复配置
        print("\n[2] 修复配置...")
        new_config = """server {
    listen 80;
    server_name openclaw;
    location /var/www/openclaw;

    # Primary configuration
    index_files {
        index 50x.conf;
        index index.php;
        index 3000.conf;
    }


    # Logging
    access_log /var/log/nginx/openclaw-access.log main;
    error_log /var/log/nginx/openclaw-error.log warn;

    # Custom headers
    add_header X-Forwarded-For $host;
    add_header X-Forwarded-Proto $host;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Host $host;
}


    # Proxy settings
    location / {
        proxy_pass http://localhost:18789;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Host $host;
        proxy_http_version 1.1;
    }

    # SSL settings (optional)
    # ssl_certificate /etc/nginx/ssl/openclaw.crt;
    # ssl_certificate_key /etc/nginx/ssl/openclaw.key;
}
"""
        stdin, stdout, stderr = ssh.exec_command(f"cat > /etc/nginx/sites-available/openclaw.conf << 'EOFCONFIG'\n{new_config}\nEOFCONFIG")
        stdout.read()
        stderr.read()

        # 测试配置
        print("\n[3] 测试配置...")
        stdin, stdout, stderr = ssh.exec_command("nginx -t")
        result = stdout.read().decode().strip()
        if result:
            print("  ✅ 配置有效")
        else:
            print(f"  ❌ 配置错误: {result}")
            return

        print()

        # 重启nginx
        print("\n[4] 重启nginx...")
        stdin, stdout, stderr = ssh.exec_command("nginx -s reload")
        result = stdout.read()
        stderr_out = stderr.read().decode().strip()
        if "successful" in stderr_out.lower() or "reload" not in stderr_out:
            print("  ✅ 已重启")
        else:
            print(f"  ⚠️ 重启警告: {stderr_out}")
        print()

        # 测试访问
        print("\n[5] 测试访问...")
        time.sleep(2)
        stdin, stdout, stderr = ssh.exec_command("curl -I http://localhost:18789")
        result = stdout.read()
        if "502 Bad Gateway" in result or "Cannot connect" in result:
            print("  ❌ 仍然502错误")
            print(f"  响应: {result[:200]}")
        else:
            print(f"  ✅ 正常 (状态码: {result[:9]}")

        print()

        ssh.close()

        print("\n" + "="*70)
        print(" 完成")
        print("="*70)

        print()
        if "502 Bad Gateway" in result:
            print("\n⚠️  仍然有问题!")
            print("建议:")
            print("  1. 检查OpenClaw Gateway日志")
            print("  2. 确认端口18789无防火墙阻止")
            print("  3. 查看系统资源使用情况")
        else:
            print("\n✅ nginx配置已修复!")

    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == '__main__':
    fix_nginx()
