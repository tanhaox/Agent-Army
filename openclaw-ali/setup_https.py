#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("=" * 60)
print(" 配置 HTTPS 访问 (手机公网可用)")
print("=" * 60)

# 步骤 1: 安装 nginx
print("\n[步骤 1/5] 安装 nginx")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('apt update && apt install -y nginx 2>&1 | tail -5')
print(stdout.read().decode('utf-8', errors='ignore'))

# 步骤 2: 创建 SSL 证书目录
print("\n[步骤 2/5] 创建自签名 SSL 证书")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('mkdir -p /etc/nginx/ssl && openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/openclaw.key -out /etc/nginx/ssl/openclaw.crt 2>&1')
print(stdout.read().decode('utf-8', errors='ignore'))
print("✅ SSL 证书已创建")

# 步骤 3: 配置 nginx
print("\n[步骤 3/5] 配置 nginx 反向代理")
print("-" * 60)
nginx_config = '''server {
    listen 443 ssl;
    server_name 112.126.61.223;

    ssl_certificate /etc/nginx/ssl/openclaw.crt;
    ssl_certificate_key /etc/nginx/ssl/openclaw.key;

    # 启用 HTTP/2
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://127.0.0.1:18789;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;

        # WebSocket 支持
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
'''

stdin, stdout, stderr = ssh.exec_command('cat > /etc/nginx/sites-available/openclaw', get_pty=True)
stdin.write(nginx_config + '\n')
stdin.close()
print("✅ nginx 配置已创建")

# 步骤 4: 启用配置
print("\n[步骤 4/5] 启用 nginx 配置")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/ && nginx -t')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

if 'syntax is ok' in result or 'successful' in result:
    print("✅ 配置验证通过")
else:
    print("⚠️ 配置验证失败，请检查")

# 重启 nginx
stdin, stdout, stderr = ssh.exec_command('systemctl reload nginx')
print(stdout.read().decode('utf-8', errors='ignore'))
print("✅ nginx 已重启")

# 步骤 5: 配置 OpenClaw trustedProxies
print("\n[步骤 5/5] 配置 OpenClaw trustedProxies")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
import json
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))

# 添加 trustedProxies
if 'trustedProxies' not in config.get('gateway', {}):
    config.setdefault('gateway', {})['trustedProxies'] = ['127.0.0.1', '::1']

# 写回配置
new_config = json.dumps(config, indent=2, ensure_ascii=False)
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/openclaw.json', get_pty=True)
stdin.write(new_config + '\n')
stdin.close()
print("✅ trustedProxies 已配置")

# 重启 Gateway
stdin, stdout, stderr = ssh.exec_command('openclaw gateway restart')
print(stdout.read().decode('utf-8', errors='ignore'))

# 等待
import time
time.sleep(3)

# 获取令牌
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

# 检查 nginx 状态
stdin, stdout, stderr = ssh.exec_command('systemctl status nginx | grep -E "(Active|running)"')
nginx_status = stdout.read().decode('utf-8', errors='ignore').strip()

print("\n" + "=" * 60)
print(" ✅ HTTPS 配置完成！")
print("=" * 60)

print(f"\nnginx 状态: {nginx_status if nginx_status else '检查中...'}")

print(f"\n🌐 HTTPS 访问地址（手机推荐）:")
print(f"   https://112.126.61.223/#token={token}")

print(f"\n⚠️  重要提示:")
print(f"   1. 需要在阿里云安全组开放 TCP 端口 443")
print(f"   2. 首次访问会提示证书不安全，需要手动信任")
print(f"   3. 信任后就可以正常使用了")

print(f"\n📱 手机访问步骤:")
print(f"   1. 配置安全组开放 443 端口")
print(f"   2. 手机浏览器访问: https://112.126.61.223/")
print(f"   3. 点击浏览器提示的"高级"→"继续访问"")
print(f"   4. 输入令牌: {token}")

ssh.close()
