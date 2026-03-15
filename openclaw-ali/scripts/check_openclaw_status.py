#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw运行状态"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

print("=" * 70)
print("  检查OpenClaw运行状态")
print("=" * 70)
print()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=15)

# 1. 检查进程
print("[1] 检查OpenClaw进程...")
stdin, stdout, stderr = ssh.exec_command('ps aux | grep -E "(openclaw|claw)" | grep -v grep')
output = stdout.read().decode('utf-8', errors='ignore')
if output.strip():
    print(f"   ✅ 找到进程:\n{output}")
else:
    print("   ⚠️  未找到OpenClaw进程")
print()

# 2. 检查pm2
print("[2] 检查PM2进程...")
stdin, stdout, stderr = ssh.exec_command('pm2 list 2>/dev/null || echo "PM2未安装或未运行"')
output = stdout.read().decode('utf-8', errors='ignore')
print(f"   {output}")
print()

# 3. 检查systemd服务
print("[3] 检查Systemd服务...")
stdin, stdout, stderr = ssh.exec_command('systemctl list-units --all | grep -i claw || echo "无相关服务"')
output = stdout.read().decode('utf-8', errors='ignore')
if output.strip() and "无相关服务" not in output:
    print(f"   ✅ 找到服务:\n{output}")
else:
    print("   ⚠️  未找到Systemd服务")
print()

# 4. 检查OpenClaw安装位置
print("[4] 检查OpenClaw安装...")
stdin, stdout, stderr = ssh.exec_command('which openclaw || npm list -g | grep -i claw || ls -la ~/.openclaw/ 2>/dev/null || echo "未找到安装"')
output = stdout.read().decode('utf-8', errors='ignore')
print(f"   {output}")
print()

# 5. 检查skill目录
print("[5] 检查已安装的Skills...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/skills/ 2>/dev/null || echo "Skills目录不存在"')
output = stdout.read().decode('utf-8', errors='ignore')
print(f"   {output}")
print()

# 6. 检查OpenClaw配置
print("[6] 检查OpenClaw配置...")
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/config.yaml 2>/dev/null || cat ~/.openclaw/config.json 2>/dev/null || echo "未找到配置文件"')
output = stdout.read().decode('utf-8', errors='ignore')
if "未找到配置文件" not in output:
    print(f"   ✅ 配置文件存在")
else:
    print(f"   {output}")
print()

# 7. 检查端口监听
print("[7] 检查端口监听...")
stdin, stdout, stderr = ssh.exec_command('netstat -tlnp 2>/dev/null | grep -E "(3000|8080|8888)" || ss -tlnp 2>/dev/null | grep -E "(3000|8080|8888)" || echo "未找到常见端口"')
output = stdout.read().decode('utf-8', errors='ignore')
if output.strip() and "未找到常见端口" not in output:
    print(f"   ✅ 找到监听端口:\n{output}")
else:
    print("   ⚠️  未找到常见OpenClaw端口")
print()

print("=" * 70)
ssh.close()
