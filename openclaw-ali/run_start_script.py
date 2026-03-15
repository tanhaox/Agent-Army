#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("=" * 60)
print(" 执行启动脚本")
print("=" * 60)

# 执行启动脚本
print("\n[执行] /root/start-gateway.sh")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('/root/start-gateway.sh', get_pty=True)
time.sleep(5)  # 等待启动

# 读取输出
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

# 再次检查端口
print("\n[最终检查] 端口监听")
print("-" * 60)
time.sleep(2)
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')
if result.strip():
    print("✅ 成功监听:")
    print(result)
    print("\n🌐 访问 URL: http://112.126.61.223:18789/")
    print("🔑 令牌: b65090c779a6fb8d11b4f39db2028fb8ec893d5b04f65359")
    print("🔐 完整: http://112.126.61.223:18789/#token=b65090c779a6fb8d11b4f39db2028fb8ec893d5b04f65359")
else:
    print("❌ 端口仍未监听，请手动检查")

ssh.close()
